"""Temporal Merge Tree Maps (Koepp and Weinkauf, IEEE VIS 2022).

This module is a readable, self-contained Python reproduction of the method in
Sections 3.1--3.3 of the paper:

1. build an augmented join/split tree for every scalar-field time step;
2. linearize every spatial domain with Algorithm 1;
3. greedily choose the binary child order using Equations (1)--(4);
4. assemble the optimized one-dimensional fields into a static image.

The authors' implementation delegates tree extraction and persistence
simplification to TTK.  This file contains a deterministic regular-grid tree
builder so that the paper algorithm can also be studied without Inviwo/TTK.
For figure-level reproduction, feed fields already simplified with TTK using
the persistence thresholds in PAPER_PRESETS below.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Literal, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

import numpy as np


TreeKind = Literal["join", "split"]


@dataclass(frozen=True)
class PaperPreset:
    """Parameters reported in Table 1 and Section 5 of the paper.

    Persistence values are percentages of the complete scalar range, exactly
    as reported by the authors.  ``None`` means that no simplification
    threshold was reported for that data set.
    """

    spatial_shape_xyz: Tuple[int, int, int]
    time_steps: Optional[int]
    persistence_percent: Optional[float]
    tree_kind: TreeKind
    scalar_restriction: Optional[Tuple[float, Optional[float]]] = None
    note: str = ""


PAPER_PRESETS: Dict[str, PaperPreset] = {
    "nucleon": PaperPreset((64, 64, 1), None, None, "split"),
    "ring": PaperPreset((14, 14, 1), 40, None, "split"),
    "benzene": PaperPreset((61, 61, 1), 21, 0.05, "join"),
    "storms": PaperPreset(
        (282, 181, 1),
        744,
        0.015,
        "join",
        note="1-hourly sea-level-pressure anomaly; the paper subtracts an 8-day mean and applies light Gaussian smoothing.",
    ),
    "cylinder": PaperPreset(
        (135, 64, 48),
        508,
        2.0,
        "split",
        scalar_restriction=(0.04, None),
        note="Okubo-Weiss criterion Q; Section 5 displays Q > 0.04.",
    ),
    "tangaroa-0.15": PaperPreset((300, 180, 120), 201, 0.15, "split"),
    "tangaroa-0.5": PaperPreset((300, 180, 120), 201, 0.5, "split"),
    "tangaroa-2": PaperPreset((300, 180, 120), 201, 2.0, "split"),
    "tangaroa-10": PaperPreset((300, 180, 120), 201, 10.0, "split"),
}


@dataclass
class SuperNode:
    """A critical sample and the superarcs leaving it toward the leaves."""

    vertex: int
    child_arcs: List[int] = field(default_factory=list)


@dataclass
class SuperArc:
    """An augmented merge-tree arc.

    ``regular_vertices`` are stored from the parent critical point toward the
    child critical point, i.e. in the order required by Algorithm 1.
    """

    id: int
    parent: int
    child: int
    regular_vertices: List[int]


@dataclass
class AugmentedMergeTree:
    """A binary augmented merge tree over one flattened scalar field."""

    values: np.ndarray
    spatial_shape: Tuple[int, ...]
    kind: TreeKind
    root: int
    nodes: Dict[int, SuperNode]
    arcs: Dict[int, SuperArc]
    vertex_to_arc: np.ndarray
    persistence_percent: Optional[float] = None
    _subtree_cache: Dict[int, frozenset[int]] = field(default_factory=dict, init=False, repr=False)

    @property
    def sample_count(self) -> int:
        return int(self.values.size)

    @property
    def root_arcs(self) -> List[int]:
        return list(self.nodes[self.root].child_arcs)

    @property
    def non_root_arcs(self) -> List[int]:
        root_arc_ids = set(self.root_arcs)
        return [arc_id for arc_id in self.arcs if arc_id not in root_arc_ids]

    def subtree_vertices(self, arc_id: int) -> frozenset[int]:
        """Return the sample set represented by the subtree below ``arc_id``."""

        cached = self._subtree_cache.get(arc_id)
        if cached is not None:
            return cached
        arc = self.arcs[arc_id]
        result: Set[int] = set(arc.regular_vertices)
        result.add(arc.child)
        for child_arc_id in self.nodes[arc.child].child_arcs:
            result.update(self.subtree_vertices(child_arc_id))
        if arc.parent == self.root:
            result.add(self.root)
        frozen = frozenset(result)
        self._subtree_cache[arc_id] = frozen
        return frozen

    def subtree_size(self, arc_id: int) -> int:
        return len(self.subtree_vertices(arc_id))

    def internal_nodes_preorder(self, decisions: Mapping[int, bool]) -> Iterator[int]:
        """Yield non-root branching nodes in the current traversal order."""

        def visit(node_id: int) -> Iterator[int]:
            child_arcs = _ordered_child_arcs(self, node_id, decisions)
            if len(child_arcs) >= 2:
                yield node_id
            for arc_id in child_arcs:
                yield from visit(self.arcs[arc_id].child)

        for arc_id in _ordered_child_arcs(self, self.root, decisions):
            yield from visit(self.arcs[arc_id].child)


@dataclass
class Linearization:
    """The mapping g: original vertex id -> integer position in one dimension."""

    position_of_vertex: np.ndarray
    vertex_at_position: np.ndarray
    subtree_intervals: Dict[int, Tuple[int, int]]


@dataclass
class TemporalMergeTreeMapResult:
    trees: List[AugmentedMergeTree]
    decisions: List[Dict[int, bool]]
    linearizations: List[Linearization]
    pair_objectives: np.ndarray
    linearized_values: np.ndarray


@dataclass(frozen=True)
class ImageParameters:
    """Section 3.3 parameters.

    The paper uses the hardware texture limit of 4096 along linearized space.
    Time receives its own horizontal dimension.  ``time_step_width=1`` gives
    one column per time step; larger widths either repeat or linearly
    interpolate the temporal samples, matching the two modes in the authors'
    implementation.
    """

    max_linearized_pixels: int = 4096
    time_step_width: int = 1
    time_interpolation: Literal["repeat", "linear"] = "repeat"
    cmap: str = "RdBu_r"
    value_range: Optional[Tuple[float, float]] = None


@dataclass
class _ActiveBranch:
    top_node: int
    regular_vertices_ascending: List[int]


class _SweepComponents:
    """Union-find used by the regular-grid merge-tree sweep."""

    def __init__(self, size: int) -> None:
        self.parent = np.full(size, -1, dtype=np.int64)
        self.branch: Dict[int, _ActiveBranch] = {}

    def active(self, vertex: int) -> bool:
        return self.parent[vertex] >= 0

    def find(self, vertex: int) -> int:
        parent = int(self.parent[vertex])
        if parent == vertex:
            return vertex
        root = self.find(parent)
        self.parent[vertex] = root
        return root

    def start(self, vertex: int, branch: _ActiveBranch) -> None:
        self.parent[vertex] = vertex
        self.branch[vertex] = branch

    def attach_regular(self, vertex: int, representative: int) -> int:
        representative = self.find(representative)
        self.parent[vertex] = representative
        self.branch[representative].regular_vertices_ascending.append(vertex)
        return representative

    def merge_at(self, vertex: int, representatives: Sequence[int], branch: _ActiveBranch) -> int:
        roots = sorted({self.find(rep) for rep in representatives})
        self.parent[vertex] = vertex
        for root in roots:
            self.parent[root] = vertex
            self.branch.pop(root, None)
        self.branch[vertex] = branch
        return vertex


def _freudenthal_neighbor_offsets(ndim: int) -> List[Tuple[int, ...]]:
    """TTK-like regular-grid adjacency for a Freudenthal triangulation.

    Two offsets share a simplex when all nonzero components have the same sign.
    This produces 6 neighbors in 2-D and 14 neighbors in 3-D away from borders.
    """

    offsets: List[Tuple[int, ...]] = []
    for encoded in np.ndindex(*(3,) * ndim):
        offset = tuple(component - 1 for component in encoded)
        if all(component == 0 for component in offset):
            continue
        nonzero = [component for component in offset if component]
        if all(component > 0 for component in nonzero) or all(component < 0 for component in nonzero):
            offsets.append(offset)
    return offsets


def _neighbor_vertices(vertex: int, shape: Tuple[int, ...], offsets: Sequence[Tuple[int, ...]]) -> Iterator[int]:
    coordinate = np.unravel_index(vertex, shape)
    for offset in offsets:
        candidate = tuple(index + delta for index, delta in zip(coordinate, offset))
        if all(0 <= index < limit for index, limit in zip(candidate, shape)):
            yield int(np.ravel_multi_index(candidate, shape))


def build_augmented_merge_tree(
    scalar_field: np.ndarray,
    kind: TreeKind = "join",
    *,
    persistence_percent: Optional[float] = None,
) -> AugmentedMergeTree:
    """Build an augmented merge tree on a 1-D/2-D/3-D regular grid.

    The sweep uses simulation of simplicity: equal scalar values are ordered by
    flattened vertex id.  For a join tree values are inserted increasingly; a
    split tree is obtained by sweeping ``-scalar_field`` increasingly.

    The paper assumes binary trees.  Generic-position Freudenthal grids satisfy
    this in the usual case.  If a discrete multi-saddle remains, it is retained
    as an n-ary node. :func:`linearize_tree` rejects it until explicit binary
    preprocessing has been performed, since the identity proof is binary.

    ``persistence_percent`` is stored as provenance.  The authors used TTK for
    persistence simplification before this stage; therefore inputs should be
    TTK-simplified when exact paper presets are required.
    """

    field_array = np.asarray(scalar_field)
    if kind not in ("join", "split"):
        raise ValueError("kind must be join or split")
    if field_array.size == 0 or not np.isfinite(field_array).all():
        raise ValueError("a nonempty finite scalar field is required")
    if field_array.ndim < 1 or field_array.ndim > 3:
        raise ValueError("A time step must be a 1-D, 2-D, or 3-D scalar field.")
    values = np.asarray(field_array, dtype=np.float64).reshape(-1)
    shape = tuple(int(v) for v in field_array.shape)
    work_values = values if kind == "join" else -values
    vertex_ids = np.arange(values.size, dtype=np.int64)
    order = np.lexsort((vertex_ids, work_values))
    last_vertex = int(order[-1])

    components = _SweepComponents(values.size)
    offsets = _freudenthal_neighbor_offsets(field_array.ndim)
    nodes: Dict[int, SuperNode] = {}
    arcs: Dict[int, SuperArc] = {}
    vertex_to_arc = np.full(values.size, -1, dtype=np.int64)
    next_arc_id = 0

    def add_arc(parent: int, child_branch: _ActiveBranch) -> int:
        nonlocal next_arc_id
        regular = list(reversed(child_branch.regular_vertices_ascending))
        arc = SuperArc(next_arc_id, parent, child_branch.top_node, regular)
        arcs[next_arc_id] = arc
        nodes[parent].child_arcs.append(next_arc_id)
        for vertex in regular:
            vertex_to_arc[vertex] = next_arc_id
        vertex_to_arc[child_branch.top_node] = next_arc_id
        next_arc_id += 1
        return arc.id

    for vertex_raw in order:
        vertex = int(vertex_raw)
        lower_components = sorted(
            {
                components.find(neighbor)
                for neighbor in _neighbor_vertices(vertex, shape, offsets)
                if components.active(neighbor)
            }
        )

        if vertex == last_vertex:
            nodes[vertex] = SuperNode(vertex)
            for representative in lower_components:
                add_arc(vertex, components.branch[representative])
            components.merge_at(vertex, lower_components, _ActiveBranch(vertex, []))
            root = vertex
            break

        if not lower_components:
            nodes[vertex] = SuperNode(vertex)
            components.start(vertex, _ActiveBranch(vertex, []))
        elif len(lower_components) == 1:
            components.attach_regular(vertex, lower_components[0])
        else:
            nodes[vertex] = SuperNode(vertex)
            for representative in lower_components:
                add_arc(vertex, components.branch[representative])
            components.merge_at(vertex, lower_components, _ActiveBranch(vertex, []))
    else:  # pragma: no cover - the loop always reaches its last vertex
        raise RuntimeError("Merge-tree sweep did not create a root.")

    if arcs:
        for root_arc_id in nodes[root].child_arcs:
            vertex_to_arc[root] = root_arc_id
            break
    else:
        vertex_to_arc[root] = 0

    return AugmentedMergeTree(
        values=values,
        spatial_shape=shape,
        kind=kind,
        root=root,
        nodes=nodes,
        arcs=arcs,
        vertex_to_arc=vertex_to_arc,
        persistence_percent=persistence_percent,
    )


def _ordered_child_arcs(
    tree: AugmentedMergeTree, node_id: int, decisions: Mapping[int, bool]
) -> List[int]:
    child_arcs = list(tree.nodes[node_id].child_arcs)
    if decisions.get(node_id, False):
        child_arcs.reverse()
    return child_arcs


def linearize_tree(
    tree: AugmentedMergeTree,
    decisions: Optional[Mapping[int, bool]] = None,
) -> Linearization:
    """Apply Algorithm 1 and return the feature-preserving 1-D mapping."""

    decisions = decisions or {}
    if tree.sample_count > 1 and len(tree.root_arcs) != 1:
        raise ValueError("Algorithm 1 requires one root arc; preprocess the tree explicitly")
    if any(len(node.child_arcs) not in (0, 2) for key, node in tree.nodes.items() if key != tree.root):
        raise ValueError("Algorithm 1 requires binary branching; apply documented multi-saddle preprocessing")
    sample_count = tree.sample_count
    position_of_vertex = np.full(sample_count, -1, dtype=np.int64)
    vertex_at_position = np.full(sample_count, -1, dtype=np.int64)

    def place(vertex: int, position: int) -> None:
        if position_of_vertex[vertex] >= 0 or vertex_at_position[position] >= 0:
            raise RuntimeError("A sample or output position was assigned twice.")
        position_of_vertex[vertex] = position
        vertex_at_position[position] = vertex

    def process_arc(arc_id: int, left: int, right: int) -> Tuple[int, int]:
        arc = tree.arcs[arc_id]
        place_left = False  # Algorithm 1 starts on the right.
        for vertex in arc.regular_vertices:
            if place_left:
                place(vertex, left)
                left += 1
            else:
                place(vertex, right)
                right -= 1
            place_left = not place_left
        return left, right

    def process_node(node_id: int, left: int, right: int) -> None:
        child_arcs = _ordered_child_arcs(tree, node_id, decisions)
        if not child_arcs:
            place(node_id, left)
            return

        first_arc = child_arcs[0]
        first_size = tree.subtree_size(first_arc)
        center = left + first_size
        place(node_id, center)

        block_left = left
        block_right = center - 1
        next_left, next_right = process_arc(first_arc, block_left, block_right)
        process_node(tree.arcs[first_arc].child, next_left, next_right)

        block_left = center + 1
        for arc_id in child_arcs[1:]:
            block_right = block_left + tree.subtree_size(arc_id) - 1
            next_left, next_right = process_arc(arc_id, block_left, block_right)
            process_node(tree.arcs[arc_id].child, next_left, next_right)
            block_left = block_right + 1

    place(tree.root, 0)
    root_child_arcs = _ordered_child_arcs(tree, tree.root, decisions)
    next_block_left = 1
    for arc_id in root_child_arcs:
        block_right = next_block_left + tree.subtree_size(arc_id) - 1
        # The root itself is included in the root-subtree set but already lives
        # at x=0, so only m-1 positions are passed to the child arc.
        if tree.root in tree.subtree_vertices(arc_id):
            block_right -= 1
        next_left, next_right = process_arc(arc_id, next_block_left, block_right)
        process_node(tree.arcs[arc_id].child, next_left, next_right)
        next_block_left = block_right + 1

    if np.any(position_of_vertex < 0) or np.any(vertex_at_position < 0):
        missing = np.flatnonzero(position_of_vertex < 0)
        raise RuntimeError(f"Linearization left {missing.size} samples unassigned.")

    intervals: Dict[int, Tuple[int, int]] = {}
    for arc_id in tree.arcs:
        positions = position_of_vertex[np.fromiter(tree.subtree_vertices(arc_id), dtype=np.int64)]
        intervals[arc_id] = (int(positions.min()), int(positions.max()))
    return Linearization(position_of_vertex, vertex_at_position, intervals)


def interval_overlap(first: Tuple[int, int], second: Tuple[int, int]) -> int:
    """Equation (4): overlap of two inclusive one-dimensional intervals."""

    minimum = max(first[0], second[0])
    maximum = min(first[1], second[1])
    return max(0, maximum - minimum + 1)


def spatial_overlap_matrix(
    first: AugmentedMergeTree,
    second: AugmentedMergeTree,
) -> Dict[Tuple[int, int], int]:
    """Equation (1), computed once in the original n-D sample domain."""

    overlap: Dict[Tuple[int, int], int] = {}
    for first_arc_id in first.non_root_arcs:
        first_vertices = first.subtree_vertices(first_arc_id)
        for second_arc_id in second.non_root_arcs:
            overlap[(first_arc_id, second_arc_id)] = len(
                first_vertices.intersection(second.subtree_vertices(second_arc_id))
            )
    return overlap


def objective_between(
    first: AugmentedMergeTree,
    first_layout: Linearization,
    second: AugmentedMergeTree,
    second_layout: Linearization,
    overlap_nd: Optional[Mapping[Tuple[int, int], int]] = None,
) -> float:
    """Equations (2)--(3) for one pair of consecutive time steps."""

    overlap_nd = overlap_nd or spatial_overlap_matrix(first, second)
    objective = 0.0
    for first_arc_id in first.non_root_arcs:
        for second_arc_id in second.non_root_arcs:
            original = overlap_nd[(first_arc_id, second_arc_id)]
            mapped = interval_overlap(
                first_layout.subtree_intervals[first_arc_id],
                second_layout.subtree_intervals[second_arc_id],
            )
            objective += float(original - mapped) ** 2
    return objective


def _greedy_align_one_tree(
    fixed_tree: AugmentedMergeTree,
    fixed_layout: Linearization,
    target_tree: AugmentedMergeTree,
) -> Tuple[Dict[int, bool], Linearization, float]:
    """Section 3.2.2: top-down binary decisions for one adjacent tree."""

    overlap_nd = spatial_overlap_matrix(fixed_tree, target_tree)
    decisions: Dict[int, bool] = {}

    def local_contribution(layout: Linearization, child_arcs: Sequence[int]) -> float:
        value = 0.0
        for fixed_arc_id in fixed_tree.non_root_arcs:
            fixed_interval = fixed_layout.subtree_intervals[fixed_arc_id]
            for target_arc_id in child_arcs:
                if target_arc_id in target_tree.root_arcs:
                    continue
                original = overlap_nd.get((fixed_arc_id, target_arc_id), 0)
                mapped = interval_overlap(fixed_interval, layout.subtree_intervals[target_arc_id])
                value += float(original - mapped) ** 2
        return value

    def decide_subtree(node_id: int) -> None:
        child_arcs = target_tree.nodes[node_id].child_arcs
        if len(child_arcs) >= 2:
            decisions[node_id] = False
            normal_layout = linearize_tree(target_tree, decisions)
            normal_cost = local_contribution(normal_layout, child_arcs)

            decisions[node_id] = True
            reversed_layout = linearize_tree(target_tree, decisions)
            reversed_cost = local_contribution(reversed_layout, child_arcs)

            # The authors' implementation keeps the original order on ties.
            decisions[node_id] = reversed_cost < normal_cost

        for child_arc_id in _ordered_child_arcs(target_tree, node_id, decisions):
            decide_subtree(target_tree.arcs[child_arc_id].child)

    for root_arc_id in _ordered_child_arcs(target_tree, target_tree.root, decisions):
        decide_subtree(target_tree.arcs[root_arc_id].child)

    layout = linearize_tree(target_tree, decisions)
    objective = objective_between(fixed_tree, fixed_layout, target_tree, layout, overlap_nd)
    return decisions, layout, objective


def optimize_temporal_order(
    trees: Sequence[AugmentedMergeTree],
    *,
    focus_timestep: int = 0,
) -> Tuple[List[Dict[int, bool]], List[Linearization], np.ndarray]:
    """Greedily propagate traversal orders forward and backward in time.

    The focus tree has the fixed, un-reversed traversal used by default in the
    authors' implementation.  The root subtree (the full domain) is omitted
    from every objective because it contributes zero, as stated in Section
    3.2.2.
    """

    if not trees:
        return [], [], np.empty(0, dtype=np.float64)
    if not 0 <= focus_timestep < len(trees):
        raise ValueError("focus_timestep is outside the sequence")
    if any(t.spatial_shape != trees[0].spatial_shape for t in trees):
        raise ValueError("TMTM overlap requires a common sampled spatial domain")
    decisions: List[Dict[int, bool]] = [dict() for _ in trees]
    layouts: List[Optional[Linearization]] = [None for _ in trees]
    pair_objectives = np.zeros(max(0, len(trees) - 1), dtype=np.float64)

    layouts[focus_timestep] = linearize_tree(trees[focus_timestep], decisions[focus_timestep])

    for time in range(focus_timestep, len(trees) - 1):
        fixed_layout = layouts[time]
        assert fixed_layout is not None
        decision, layout, objective = _greedy_align_one_tree(
            trees[time], fixed_layout, trees[time + 1]
        )
        decisions[time + 1] = decision
        layouts[time + 1] = layout
        pair_objectives[time] = objective

    for time in range(focus_timestep, 0, -1):
        fixed_layout = layouts[time]
        assert fixed_layout is not None
        decision, layout, _ = _greedy_align_one_tree(
            trees[time], fixed_layout, trees[time - 1]
        )
        decisions[time - 1] = decision
        layouts[time - 1] = layout
        # Re-evaluate in chronological orientation for Equation (3).
        overlap = spatial_overlap_matrix(trees[time - 1], trees[time])
        pair_objectives[time - 1] = objective_between(
            trees[time - 1], layout, trees[time], fixed_layout, overlap
        )

    return decisions, [layout for layout in layouts if layout is not None], pair_objectives


def linearized_scalar_matrix(
    fields: np.ndarray,
    layouts: Sequence[Linearization],
    *,
    max_linearized_pixels: int = 4096,
) -> np.ndarray:
    """Stack f(x,t)=s(g^-1(x),t), then apply paper-style subsampling."""

    time_steps = int(fields.shape[0])
    flattened = np.asarray(fields, dtype=np.float64).reshape(time_steps, -1)
    columns = [
        flattened[time, layouts[time].vertex_at_position]
        for time in range(time_steps)
    ]
    full = np.column_stack(columns)
    factor = max(1, math.ceil(full.shape[0] / max_linearized_pixels))
    return full[::factor, :]


def _expand_time(values: np.ndarray, width: int, mode: str) -> np.ndarray:
    if width <= 1:
        return values
    if mode == "repeat" or values.shape[1] == 1:
        return np.repeat(values, width, axis=1)

    source = np.arange(values.shape[1], dtype=np.float64)
    target = np.linspace(0.0, values.shape[1] - 1.0, values.shape[1] * width)
    expanded = np.empty((values.shape[0], target.size), dtype=np.float64)
    for row in range(values.shape[0]):
        expanded[row] = np.interp(target, source, values[row])
    return expanded


def save_temporal_merge_tree_map(
    scalar_matrix: np.ndarray,
    output_path: Path | str,
    parameters: ImageParameters = ImageParameters(),
) -> None:
    """Color-code a scalar matrix and save the temporal merge tree map."""

    import matplotlib.pyplot as plt

    image_values = _expand_time(
        np.asarray(scalar_matrix), parameters.time_step_width, parameters.time_interpolation
    )
    value_min, value_max = (
        parameters.value_range
        if parameters.value_range is not None
        else (float(np.nanmin(image_values)), float(np.nanmax(image_values)))
    )
    plt.imsave(
        Path(output_path),
        image_values,
        cmap=parameters.cmap,
        vmin=value_min,
        vmax=value_max,
        origin="upper",
    )


def compute_temporal_merge_tree_map(
    fields: np.ndarray,
    *,
    kind: TreeKind = "join",
    persistence_percent: Optional[float] = None,
    focus_timestep: int = 0,
    max_linearized_pixels: int = 4096,
) -> TemporalMergeTreeMapResult:
    """Run the full paper pipeline on an array shaped ``(time, *space)``."""

    data = np.asarray(fields)
    trees = [
        build_augmented_merge_tree(
            data[time], kind=kind, persistence_percent=persistence_percent
        )
        for time in range(data.shape[0])
    ]
    decisions, layouts, pair_objectives = optimize_temporal_order(
        trees, focus_timestep=focus_timestep
    )
    values = linearized_scalar_matrix(
        data, layouts, max_linearized_pixels=max_linearized_pixels
    )
    return TemporalMergeTreeMapResult(
        trees=trees,
        decisions=decisions,
        linearizations=layouts,
        pair_objectives=pair_objectives,
        linearized_values=values,
    )


def _write_metadata(
    path: Path,
    result: TemporalMergeTreeMapResult,
    preset_name: Optional[str],
    kind: TreeKind,
    persistence_percent: Optional[float],
    focus_timestep: int,
    image_parameters: ImageParameters,
) -> None:
    metadata = {
        "paper": "Koepp and Weinkauf (2022), Temporal Merge Tree Maps",
        "preset": preset_name,
        "preset_parameters": asdict(PAPER_PRESETS[preset_name]) if preset_name else None,
        "tree_kind": kind,
        "persistence_percent_of_data_range": persistence_percent,
        "focus_timestep": focus_timestep,
        "image_parameters": asdict(image_parameters),
        "objective_equation_3": float(result.pair_objectives.sum()),
        "pair_objectives": result.pair_objectives.tolist(),
        "supernodes_per_timestep": [len(tree.nodes) for tree in result.trees],
        "decisions": [
            {str(node): bool(reverse) for node, reverse in decision.items()}
            for decision in result.decisions
        ],
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help=".npy array shaped (time, *spatial dimensions)")
    parser.add_argument("output", type=Path, help="output PNG path")
    parser.add_argument("--preset", choices=sorted(PAPER_PRESETS))
    parser.add_argument("--tree", choices=("join", "split"), default=None)
    parser.add_argument("--persistence-percent", type=float, default=None)
    parser.add_argument("--focus-timestep", type=int, default=0)
    parser.add_argument("--max-linearized-pixels", type=int, default=4096)
    parser.add_argument("--time-step-width", type=int, default=1)
    parser.add_argument("--time-interpolation", choices=("repeat", "linear"), default="repeat")
    parser.add_argument("--cmap", default="RdBu_r")
    parser.add_argument("--value-min", type=float)
    parser.add_argument("--value-max", type=float)
    parser.add_argument("--metadata", type=Path)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    preset = PAPER_PRESETS.get(args.preset) if args.preset else None
    kind: TreeKind = args.tree or (preset.tree_kind if preset else "join")
    persistence_percent = (
        args.persistence_percent
        if args.persistence_percent is not None
        else (preset.persistence_percent if preset else None)
    )
    value_range = None
    if args.value_min is not None and args.value_max is not None:
        value_range = (args.value_min, args.value_max)

    image_parameters = ImageParameters(
        max_linearized_pixels=args.max_linearized_pixels,
        time_step_width=args.time_step_width,
        time_interpolation=args.time_interpolation,
        cmap=args.cmap,
        value_range=value_range,
    )
    fields = np.load(args.input)
    result = compute_temporal_merge_tree_map(
        fields,
        kind=kind,
        persistence_percent=persistence_percent,
        focus_timestep=args.focus_timestep,
        max_linearized_pixels=image_parameters.max_linearized_pixels,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_temporal_merge_tree_map(result.linearized_values, args.output, image_parameters)
    metadata_path = args.metadata or args.output.with_suffix(".json")
    _write_metadata(
        metadata_path,
        result,
        args.preset,
        kind,
        persistence_percent,
        args.focus_timestep,
        image_parameters,
    )


if __name__ == "__main__":
    main()
