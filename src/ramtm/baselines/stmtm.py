"""Spatiotemporal Merge Tree Maps (Diaz et al., 2026 preprint).

This module reproduces the algorithmic pipeline described in Sections 4.1
and 4.2 of *Spatiotemporal Merge Tree Maps: A Topology and Geometry Aware
Visualization for Temporal Scalar Data*.

The paper uses TTK for merge-tree construction and simplification.  To keep
that boundary explicit, this file consumes already constructed *binary
augmented merge trees*.  It then implements the paper's contribution:

1. hierarchy-constrained optimal leaf ordering (OLO);
2. optional temporal concordance and thresholded reordering;
3. Eq. (1), the distance-aware 1-D projection with temporal anchors;
4. Eq. (2), proportional leaf-interval allocation;
5. global scaling, padding, discretization, and temporal assembly;
6. leaf filling followed by the four hierarchy-aware filling cases in Fig. 5;
7. the SNS, trustworthiness, and temporal-displacement metrics from Sec. 5.2.

No scalar dataset is read or processed on import.  The JSON input format is
documented in README_复现说明.md and in ``load_frames_json``.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy.cluster.hierarchy import leaves_list, optimal_leaf_ordering
from scipy.optimize import linear_sum_assignment, minimize
from scipy.spatial.distance import pdist, squareform


WeightMode = Literal["uniform", "inverse"]
RunMode = Literal["base", "temporal"]


@dataclass(frozen=True)
class PaperPreset:
    """Parameters reported in Tables 1 and 2 of the paper.

    ``persistence_threshold`` is the normalized value printed as p_opt in
    Table 1. A per-frame percentage interpretation is a reproduction assumption;
    matching the feature count does not verify the simplification procedure.

    Alpha in Eq. (2) and delta in Eq. (1) are not included in Table 2.  The
    implementation exposes both separately instead of presenting invented
    dataset-specific values as paper parameters.
    """

    dimensions: Tuple[int, int]
    timesteps: int
    feature_count: str
    persistence_threshold: float
    weights: WeightMode
    total_leaf_extent_k: float
    reorder_threshold_r: float
    temporal_lambda: float
    layout_length: int
    start_timestep: int


PAPER_PRESETS: Dict[str, PaperPreset] = {
    "gaussian": PaperPreset(
        (128, 128), 64, "3", 0.001, "uniform", 65.0, 0.95, 1.5, 4096, 1
    ),
    "ring": PaperPreset(
        (14, 14), 40, "1-7", 0.001, "uniform", 1.0, 0.95, 1.5, 196, 0
    ),
    "wildfires": PaperPreset(
        (64, 64), 32, "2-34", 0.15, "uniform", 10.0, 0.85, 0.5, 4096, 5
    ),
    "storms": PaperPreset(
        (281, 181), 744, "1-8", 0.105, "inverse", 135.0, 0.65, 0.05, 4096, 40
    ),
}


@dataclass
class TreeArc:
    """One augmented merge-tree arc, directed from child toward the root.

    ``regular_vertices`` must be ordered from ``child`` to ``parent``.  The
    endpoints are critical vertices and are not repeated in that array.
    """

    id: int
    child: int
    parent: int
    regular_vertices: np.ndarray = field(
        default_factory=lambda: np.empty(0, dtype=np.int64)
    )


@dataclass
class AugmentedMergeTreeFrame:
    """A binary augmented merge tree and its original spatial geometry."""

    timestep: int
    root: int
    children: Dict[int, Tuple[int, ...]]
    arcs: Dict[int, TreeArc]
    values: np.ndarray
    coordinates: np.ndarray
    domain_min: np.ndarray
    domain_max: np.ndarray
    sample_ids: Optional[np.ndarray] = None
    _arc_for_child: Dict[int, TreeArc] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        # Preserve float32 scalar fields during full temporal runs.  Numerical
        # optimization promotes the small feature-level arrays to float64, so
        # retaining the source dtype here avoids duplicating hundreds of full
        # ERA5 grids without changing the layout computation.
        self.values = np.asarray(self.values)
        self.coordinates = np.asarray(self.coordinates, dtype=float)
        self.domain_min = np.asarray(self.domain_min, dtype=float)
        self.domain_max = np.asarray(self.domain_max, dtype=float)
        if self.sample_ids is None:
            self.sample_ids = np.arange(self.values.size, dtype=np.int64)
        else:
            self.sample_ids = np.asarray(self.sample_ids, dtype=np.int64)
        self.children = {
            int(node): tuple(int(c) for c in child_ids)
            for node, child_ids in self.children.items()
        }
        self.arcs = {int(k): v for k, v in self.arcs.items()}
        self._arc_for_child = {arc.child: arc for arc in self.arcs.values()}
        self.validate()

    def validate(self) -> None:
        n = self.values.size
        if not n or not np.isfinite(self.values).all() or not np.isfinite(self.coordinates).all():
            raise ValueError("finite nonempty scalar values and coordinates are required")
        if self.coordinates.ndim != 2 or self.coordinates.shape[0] != n:
            raise ValueError("coordinates must have shape (sample_count, spatial_dimension)")
        if self.sample_ids is None or self.sample_ids.shape != (n,):
            raise ValueError("sample_ids must contain one stable spatial id per sample")
        if self.root < 0 or self.root >= n:
            raise ValueError("root is outside the sample array")
        if self.domain_min.shape != (self.coordinates.shape[1],):
            raise ValueError("domain_min has the wrong spatial dimension")
        if self.domain_max.shape != self.domain_min.shape:
            raise ValueError("domain_max has the wrong spatial dimension")
        for node, child_ids in self.children.items():
            # A merge-tree root may have a single outgoing superarc; all
            # non-root branching supernodes are binary as assumed by the paper.
            allowed = (0, 1, 2) if node == self.root else (0, 2)
            if len(child_ids) not in allowed:
                raise ValueError(
                    f"node {node} has {len(child_ids)} children; the paper assumes a binary tree"
                )
            for child in child_ids:
                arc = self._arc_for_child.get(child)
                if arc is None or arc.parent != node:
                    raise ValueError(f"missing or inconsistent arc for child {child} of node {node}")
        for arc in self.arcs.values():
            if np.any(arc.regular_vertices < 0) or np.any(arc.regular_vertices >= n):
                raise ValueError(f"arc {arc.id} contains an invalid regular vertex")
        seen = set()
        def visit(node):
            if node in seen or node not in self.children or not 0 <= node < n:
                raise ValueError("tree must be connected, acyclic, and singly parented")
            seen.add(node)
            for child in self.children[node]:
                visit(child)
        visit(self.root)
        if seen != set(self.children) or set(self._arc_for_child) != seen - {self.root}:
            raise ValueError("tree nodes and arcs do not form a rooted tree")
        if len(self.arcs) != len(seen)-1:
            raise ValueError("each non-root node must have exactly one incoming arc")
        owned = list(seen) + [int(v) for a in self.arcs.values() for v in a.regular_vertices]
        if sorted(owned) != list(range(n)):
            raise ValueError("augmented tree must own each sample exactly once")
        if len(set(self.sample_ids.tolist())) != n:
            raise ValueError("sample_ids must be unique within a frame")
        root_value=self.values[self.root]
        if root_value==np.max(self.values):direction=1
        elif root_value==np.min(self.values):direction=-1
        else:raise ValueError("merge-tree root must be a global scalar extremum")
        for arc in self.arcs.values():
            path=np.r_[arc.child,arc.regular_vertices,arc.parent].astype(int)
            if np.any(direction*np.diff(self.values[path]) < 0):
                raise ValueError("regular vertices must be monotone from child toward parent")

    @property
    def leaves(self) -> Tuple[int, ...]:
        return tuple(sorted(node for node, c in self.children.items() if len(c) == 0))

    def parent(self, node: int) -> Optional[int]:
        arc = self._arc_for_child.get(int(node))
        return None if arc is None else int(arc.parent)

    def arc_for_child(self, child: int) -> TreeArc:
        return self._arc_for_child[int(child)]

    def leaf_feature_vertices(self, leaf: int) -> np.ndarray:
        """Samples of a leaf feature: extremum plus its leaf-arc regular nodes."""

        arc = self.arc_for_child(leaf)
        return np.concatenate((np.array([leaf], dtype=np.int64), arc.regular_vertices))

    def leaf_centroid(self, leaf: int) -> np.ndarray:
        return np.mean(self.coordinates[self.leaf_feature_vertices(leaf)], axis=0)

    def leaf_size(self, leaf: int) -> int:
        return int(self.leaf_feature_vertices(leaf).size)

    def lca(self, first: int, second: int) -> int:
        ancestors = set()
        node: Optional[int] = int(first)
        while node is not None:
            ancestors.add(node)
            node = self.parent(node)
        node = int(second)
        while node not in ancestors:
            parent = self.parent(node)
            if parent is None:
                raise ValueError("tree is disconnected")
            node = parent
        return node

    def nonleaf_path_to_ancestor(self, leaf: int, ancestor: int) -> List[TreeArc]:
        """Arcs above the already-filled leaf arc, ordered leaf -> ancestor."""

        result: List[TreeArc] = []
        node = self.parent(leaf)
        while node is not None and node != ancestor:
            arc = self.arc_for_child(node)
            result.append(arc)
            node = arc.parent
        if node != ancestor:
            raise ValueError(f"{ancestor} is not an ancestor of leaf {leaf}")
        return result


@dataclass(frozen=True)
class LayoutParameters:
    weights: WeightMode
    total_leaf_extent_k: float
    reorder_threshold_r: float
    temporal_lambda: float
    layout_length: int
    start_timestep: int
    mode: RunMode = "temporal"
    alpha: float = 1.0
    min_spacing_delta: float = 1e-3
    optimizer_tolerance: float = 1e-9
    optimizer_max_iterations: int = 2000

    @classmethod
    def from_preset(cls, name: str, *, mode: RunMode = "temporal") -> "LayoutParameters":
        p = PAPER_PRESETS[name.lower()]
        return cls(
            weights=p.weights,
            total_leaf_extent_k=p.total_leaf_extent_k,
            reorder_threshold_r=p.reorder_threshold_r,
            temporal_lambda=p.temporal_lambda,
            layout_length=p.layout_length,
            start_timestep=p.start_timestep,
            mode=mode,
        )

    def validate(self, frame_count: int) -> None:
        if not np.isfinite([self.total_leaf_extent_k, self.temporal_lambda, self.alpha,
                            self.min_spacing_delta, self.optimizer_tolerance]).all():
            raise ValueError("parameters must be finite")
        if self.temporal_lambda < 0 or self.optimizer_tolerance <= 0 or self.optimizer_max_iterations < 1:
            raise ValueError("lambda must be nonnegative and solver settings positive")
        if self.weights not in ("uniform", "inverse"):
            raise ValueError("weights must be 'uniform' or 'inverse'")
        if self.mode not in ("base", "temporal"):
            raise ValueError("mode must be 'base' or 'temporal'")
        if not 0.0 <= self.reorder_threshold_r <= 1.0:
            raise ValueError("r must lie in [0, 1]")
        if self.total_leaf_extent_k <= 0 or self.layout_length <= 0:
            raise ValueError("K and layout length must be positive")
        if self.alpha <= 0 or self.min_spacing_delta <= 0:
            raise ValueError("alpha and delta must be positive")
        if not 0 <= self.start_timestep < frame_count:
            raise ValueError("start_timestep is outside the sequence")


@dataclass
class ContinuousSkeleton:
    ordering: Tuple[int, ...]
    anchors: np.ndarray
    starts: np.ndarray
    ends: np.ndarray


@dataclass
class DiscreteSkeleton:
    ordering: Tuple[int, ...]
    anchors: np.ndarray
    starts: np.ndarray
    ends: np.ndarray


@dataclass
class STMTMResult:
    parameters: LayoutParameters
    continuous: List[ContinuousSkeleton]
    discrete: List[DiscreteSkeleton]
    leaf_matches: List[Dict[int, int]]
    linearized_values: np.ndarray
    padding: int


def _leaf_distance_matrix(frame: AugmentedMergeTreeFrame, leaves: Sequence[int]) -> np.ndarray:
    if len(leaves) <= 1:
        return np.zeros((len(leaves), len(leaves)), dtype=float)
    centroids = np.vstack([frame.leaf_centroid(leaf) for leaf in leaves])
    return squareform(pdist(centroids, metric="euclidean"))


def ordering_cost(frame: AugmentedMergeTreeFrame, ordering: Sequence[int]) -> float:
    """Paper Sec. 4.1.1: sum of distances between adjacent centroids."""

    if len(ordering) < 2:
        return 0.0
    centroids = {leaf: frame.leaf_centroid(leaf) for leaf in ordering}
    return float(
        sum(
            np.linalg.norm(centroids[a] - centroids[b])
            for a, b in zip(ordering[:-1], ordering[1:])
        )
    )


def _tree_linkage(frame: AugmentedMergeTreeFrame, leaves: Sequence[int]) -> np.ndarray:
    """Encode the binary merge-tree hierarchy as a SciPy linkage matrix."""

    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    rows: List[List[float]] = []
    counts: Dict[int, int] = {i: 1 for i in range(len(leaves))}

    def visit(node: int) -> int:
        child_ids = frame.children[node]
        if not child_ids:
            return leaf_index[node]
        if len(child_ids) == 1:
            return visit(child_ids[0])
        if len(child_ids) != 2:
            raise ValueError("OLO requires the binary hierarchy assumed by the paper")
        a = visit(child_ids[0])
        b = visit(child_ids[1])
        cluster_id = len(leaves) + len(rows)
        count = counts[a] + counts[b]
        # OLO only needs the hierarchy.  A monotone topological level is used
        # as linkage height and has no role in the centroid-distance objective.
        height = float(len(rows) + 1)
        rows.append([float(a), float(b), height, float(count)])
        counts[cluster_id] = count
        return cluster_id

    root_cluster = visit(frame.root)
    expected_root = 2 * len(leaves) - 2
    if len(leaves) > 1 and root_cluster != expected_root:
        raise ValueError("tree contains nodes not represented by the leaf hierarchy")
    return np.asarray(rows, dtype=float)


def optimal_hierarchical_leaf_order(frame: AugmentedMergeTreeFrame) -> Tuple[int, ...]:
    """Compute SciPy OLO using centroid distances, as in Sec. 4.1.1."""

    leaves = frame.leaves
    if len(leaves) <= 1:
        return leaves
    distances = _leaf_distance_matrix(frame, leaves)
    linkage = _tree_linkage(frame, leaves)
    ordered_linkage = optimal_leaf_ordering(linkage, squareform(distances, checks=False))
    return tuple(leaves[int(i)] for i in leaves_list(ordered_linkage))


def match_leaves_by_overlap(
    reference: AugmentedMergeTreeFrame,
    current: AugmentedMergeTreeFrame,
) -> Dict[int, int]:
    """Simple one-to-one overlap matching used for temporal mode.

    The paper specifies an overlap-based strategy but not its tie handling.
    We maximize intersection counts globally with the Hungarian algorithm and
    discard zero-overlap pairs.  Stable ``sample_ids`` are therefore required.
    """

    previous = reference.leaves
    now = current.leaves
    if not previous or not now:
        return {}
    previous_sets = [set(reference.sample_ids[reference.leaf_feature_vertices(x)]) for x in previous]
    current_sets = [set(current.sample_ids[current.leaf_feature_vertices(x)]) for x in now]
    overlap = np.zeros((len(now), len(previous)), dtype=float)
    for i, a in enumerate(current_sets):
        for j, b in enumerate(previous_sets):
            overlap[i, j] = len(a.intersection(b))
    rows, cols = linear_sum_assignment(-overlap)
    return {
        now[int(i)]: previous[int(j)]
        for i, j in zip(rows, cols)
        if overlap[int(i), int(j)] > 0
    }


def _concordance(
    left: Sequence[int],
    right: Sequence[int],
    matches: Mapping[int, int],
    previous_rank: Mapping[int, int],
) -> int:
    score = 0
    for a in left:
        ma = matches.get(a)
        if ma is None:
            continue
        for b in right:
            mb = matches.get(b)
            if mb is not None and previous_rank[ma] < previous_rank[mb]:
                score += 1
    return score


def temporally_concordant_order(
    frame: AugmentedMergeTreeFrame,
    previous_order: Sequence[int],
    matches: Mapping[int, int],
) -> Tuple[int, ...]:
    """Bottom-up AB/BA selection using the paper's concordance score."""

    previous_rank = {leaf: i for i, leaf in enumerate(previous_order)}

    def visit(node: int) -> Tuple[int, ...]:
        child_ids = frame.children[node]
        if not child_ids:
            return (node,)
        # The global merge-tree root can have one outgoing superarc.  It adds
        # no AB/BA decision and therefore transparently forwards its subtree.
        if len(child_ids) == 1:
            return visit(child_ids[0])
        a = visit(child_ids[0])
        b = visit(child_ids[1])
        score_ab = _concordance(a, b, matches, previous_rank)
        score_ba = _concordance(b, a, matches, previous_rank)
        ab = a + b
        ba = b + a
        if score_ab > score_ba:
            return ab
        if score_ba > score_ab:
            return ba
        # The paper resolves unmatched leaves and matched-pair ties by Cost.
        cost_ab = ordering_cost(frame, ab)
        cost_ba = ordering_cost(frame, ba)
        return ba if cost_ba < cost_ab else ab

    return visit(frame.root)


def _orientation_agreement(
    ordering: Sequence[int],
    previous_order: Sequence[int],
    matches: Mapping[int, int],
) -> int:
    rank = {leaf: i for i, leaf in enumerate(previous_order)}
    score = 0
    for i in range(len(ordering)):
        mi = matches.get(ordering[i])
        if mi is None:
            continue
        for j in range(i + 1, len(ordering)):
            mj = matches.get(ordering[j])
            if mj is not None and rank[mi] < rank[mj]:
                score += 1
    return score


def choose_temporal_order(
    frame: AugmentedMergeTreeFrame,
    previous_order: Sequence[int],
    matches: Mapping[int, int],
    r: float,
) -> Tuple[int, ...]:
    """Thresholded choice between concordant ordering and OLO."""

    current = temporally_concordant_order(frame, previous_order, matches)
    olo = optimal_hierarchical_leaf_order(frame)
    reversed_olo = tuple(reversed(olo))
    if _orientation_agreement(reversed_olo, previous_order, matches) > _orientation_agreement(
        olo, previous_order, matches
    ):
        olo = reversed_olo
    current_cost = ordering_cost(frame, current)
    olo_cost = ordering_cost(frame, olo)
    # 0/0 is unspecified in the paper: retain the concordant order on this tie.
    ratio = 1.0 if current_cost == 0.0 and olo_cost == 0.0 else (
        math.inf if current_cost == 0.0 else olo_cost / current_cost
    )
    return olo if ratio <= r else current


def project_leaf_anchors(
    frame: AugmentedMergeTreeFrame,
    ordering: Sequence[int],
    parameters: LayoutParameters,
    temporal_positions: Optional[Mapping[int, float]] = None,
) -> np.ndarray:
    """Solve Eq. (1) with SLSQP."""

    count = len(ordering)
    if count == 0:
        return np.empty(0, dtype=float)
    if count == 1:
        if temporal_positions and ordering[0] in temporal_positions:
            return np.array([temporal_positions[ordering[0]]], dtype=float)
        return np.zeros(1, dtype=float)

    distances = _leaf_distance_matrix(frame, ordering)
    if parameters.weights == "uniform":
        weights = np.ones_like(distances)
    else:
        if np.any(distances[np.triu_indices(count, 1)] == 0):
            raise ValueError("Eq. (1) inverse weights are undefined for coincident centroids")
        weights = np.divide(
            1.0,
            distances,
            out=np.zeros_like(distances),
            where=distances > 0,
        )

    matched = []
    if temporal_positions:
        matched = [(i, temporal_positions[leaf]) for i, leaf in enumerate(ordering) if leaf in temporal_positions]
    lam = parameters.temporal_lambda if parameters.mode == "temporal" else 0.0

    adjacent = np.maximum(np.diag(distances, 1), parameters.min_spacing_delta)
    initial = np.concatenate(([0.0], np.cumsum(adjacent)))
    target_mean = float(np.mean([p for _, p in matched])) if matched else 0.0
    initial += target_mean - float(np.mean(initial))

    def objective(x: np.ndarray) -> float:
        value = 0.0
        for i in range(count):
            for j in range(i + 1, count):
                residual = (x[j] - x[i]) - distances[i, j]
                value += weights[i, j] * residual * residual
        if lam > 0.0:
            value += lam * sum((x[i] - p) ** 2 for i, p in matched)
        return float(value)

    def gradient(x: np.ndarray) -> np.ndarray:
        g = np.zeros(count)
        for i in range(count):
            for j in range(i + 1, count):
                v = 2 * weights[i, j] * (x[j] - x[i] - distances[i, j])
                g[j] += v
                g[i] -= v
        if lam > 0:
            for i, p in matched:
                g[i] += 2 * lam * (x[i] - p)
        return g

    constraints = [
        {
            "type": "ineq",
            "fun": lambda x, i=i: x[i + 1] - x[i] - parameters.min_spacing_delta,
        }
        for i in range(count - 1)
    ]
    # Eq. (1) is translation-invariant when lambda=0.  This equality merely
    # fixes that free gauge and does not change any optimized distance.
    if not matched or lam == 0.0:
        constraints.append({"type": "eq", "fun": lambda x: float(np.mean(x))})

    result = minimize(
        objective,
        initial,
        jac=gradient,
        method="SLSQP",
        constraints=constraints,
        options={
            "ftol": parameters.optimizer_tolerance,
            "maxiter": parameters.optimizer_max_iterations,
            "disp": False,
        },
    )
    if not result.success:
        raise RuntimeError(f"Eq. (1) SLSQP failed at t={frame.timestep}: {result.message}")
    if np.min(np.diff(result.x)) < parameters.min_spacing_delta - 1e-7:
        raise RuntimeError("Eq. (1) returned violated spacing constraints")
    return np.asarray(result.x, dtype=float)


def allocate_leaf_intervals(
    frame: AugmentedMergeTreeFrame,
    ordering: Sequence[int],
    anchors: np.ndarray,
    parameters: LayoutParameters,
) -> Tuple[np.ndarray, np.ndarray]:
    """Solve Eq. (2), including proportional target widths."""

    count = len(ordering)
    if count == 0:
        return np.empty(0), np.empty(0)
    sizes = np.asarray([frame.leaf_size(leaf) for leaf in ordering], dtype=float)
    powered = sizes ** parameters.alpha
    target = parameters.total_leaf_extent_k * powered / float(np.sum(powered))
    eps = max(parameters.min_spacing_delta * 0.1, 1e-9)

    # Strict inequalities use an explicit numerical margin (reproduction assumption).
    # Adapt it downward for small K rather than inventing infeasibility.
    eps = min(eps, parameters.total_leaf_extent_k / (8 * count), float(np.min(target)) / 4)
    if count > 1:
        if np.any(np.diff(anchors) <= 0):
            raise ValueError("anchors must be strictly ordered")
        eps = min(eps, float(np.min(np.diff(anchors))) / 8)
    # A feasible construction: tiny inner halves; put leftover mass outside.
    starts = anchors - eps
    ends = anchors + eps
    remaining = parameters.total_leaf_extent_k - 2 * count * eps
    starts[0] -= remaining / 2
    ends[-1] += remaining / 2
    centered = np.r_[anchors - target / 2, anchors + target / 2]
    if count == 1 or np.all(centered[:count][1:] - centered[count:][:-1] >= eps):
        starts, ends = centered[:count], centered[count:]
    initial = np.concatenate((starts, ends))

    def unpack(z: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return z[:count], z[count:]

    def objective(z: np.ndarray) -> float:
        s, e = unpack(z)
        return float(np.sum(((e - s - target) / target) ** 2))

    def gradient(z):
        ss, ee = unpack(z)
        r = 2 * (ee - ss - target) / target ** 2
        return np.r_[-r, r]

    constraints = []
    for i in range(count):
        constraints.extend(
            [
                {"type": "ineq", "fun": lambda z, i=i: anchors[i] - z[i] - eps},
                {
                    "type": "ineq",
                    "fun": lambda z, i=i: z[count + i] - anchors[i] - eps,
                },
            ]
        )
    for i in range(count - 1):
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda z, i=i: z[i + 1] - z[count + i] - eps,
            }
        )
    constraints.append(
        {
            "type": "eq",
            "fun": lambda z: float(np.sum(z[count:] - z[:count]))
            - parameters.total_leaf_extent_k,
        }
    )
    result = minimize(
        objective,
        initial,
        jac=gradient,
        method="SLSQP",
        constraints=constraints,
        options={
            "ftol": parameters.optimizer_tolerance,
            "maxiter": parameters.optimizer_max_iterations,
            "disp": False,
        },
    )
    if not result.success:
        raise RuntimeError(f"Eq. (2) SLSQP failed at t={frame.timestep}: {result.message}")
    ss, ee = unpack(result.x)
    if (np.any(ss >= anchors) or np.any(ee <= anchors)
            or np.any(ee[:-1] >= ss[1:])
            or abs(np.sum(ee-ss)-parameters.total_leaf_extent_k) > 1e-6):
        raise RuntimeError("Eq. (2) returned violated interval constraints")
    return unpack(np.asarray(result.x, dtype=float))


def _temporal_positions(
    ordering: Sequence[int],
    matches: Mapping[int, int],
    reference: ContinuousSkeleton,
) -> Dict[int, float]:
    ref_position = {leaf: float(reference.anchors[i]) for i, leaf in enumerate(reference.ordering)}
    return {
        leaf: ref_position[previous]
        for leaf in ordering
        if (previous := matches.get(leaf)) in ref_position
    }


def construct_continuous_skeletons(
    frames: Sequence[AugmentedMergeTreeFrame],
    parameters: LayoutParameters,
) -> Tuple[List[ContinuousSkeleton], List[Dict[int, int]]]:
    """Paper Sec. 4.1, propagated from Start forward and backward."""

    parameters.validate(len(frames))
    count = len(frames)
    skeletons: List[Optional[ContinuousSkeleton]] = [None] * count
    matches_by_frame: List[Dict[int, int]] = [{} for _ in frames]
    start = parameters.start_timestep

    def solve(index: int, reference_index: Optional[int]) -> None:
        frame = frames[index]
        if reference_index is None or parameters.mode == "base":
            ordering = optimal_hierarchical_leaf_order(frame)
            matches: Dict[int, int] = {}
            temporal = None
        else:
            reference_frame = frames[reference_index]
            reference_skeleton = skeletons[reference_index]
            assert reference_skeleton is not None
            matches = match_leaves_by_overlap(reference_frame, frame)
            ordering = choose_temporal_order(
                frame, reference_skeleton.ordering, matches, parameters.reorder_threshold_r
            )
            temporal = _temporal_positions(ordering, matches, reference_skeleton)
        anchors = project_leaf_anchors(frame, ordering, parameters, temporal)
        starts, ends = allocate_leaf_intervals(frame, ordering, anchors, parameters)
        skeletons[index] = ContinuousSkeleton(tuple(ordering), anchors, starts, ends)
        matches_by_frame[index] = matches

    solve(start, None)
    for index in range(start + 1, count):
        solve(index, index - 1)
    for index in range(start - 1, -1, -1):
        solve(index, index + 1)
    return [s for s in skeletons if s is not None], matches_by_frame


def compute_padding(frames: Sequence[AugmentedMergeTreeFrame], layout_length: int) -> int:
    """Sec. 4.1.3: unoccupied fraction from centroid/domain diagonals."""

    centroids = np.vstack(
        [frame.leaf_centroid(leaf) for frame in frames for leaf in frame.leaves]
    )
    feature_diagonal = float(np.linalg.norm(np.max(centroids, axis=0) - np.min(centroids, axis=0)))
    domain_min = np.min(np.vstack([f.domain_min for f in frames]), axis=0)
    domain_max = np.max(np.vstack([f.domain_max for f in frames]), axis=0)
    domain_diagonal = float(np.linalg.norm(domain_max - domain_min))
    occupied = 1.0 if domain_diagonal == 0.0 else np.clip(feature_diagonal / domain_diagonal, 0.0, 1.0)
    return int(round(layout_length * (1.0 - occupied)))


def discretize_skeletons(
    frames: Sequence[AugmentedMergeTreeFrame],
    skeletons: Sequence[ContinuousSkeleton],
    layout_length: int,
) -> Tuple[List[DiscreteSkeleton], int]:
    """Shared global scaling, centering padding, and overlap postprocessing."""

    padding = compute_padding(frames, layout_length)
    inner = max(layout_length - padding, 1)
    global_min = min(float(np.min(s.starts)) for s in skeletons)
    global_max = max(float(np.max(s.ends)) for s in skeletons)
    span = global_max - global_min
    offset = int(math.ceil(padding / 2.0))

    def scale(values: np.ndarray) -> np.ndarray:
        if span == 0.0:
            return np.full(values.shape, offset + (inner - 1) // 2, dtype=np.int64)
        return np.rint((inner - 1) * (values - global_min) / span).astype(np.int64) + offset

    result: List[DiscreteSkeleton] = []
    for skeleton in skeletons:
        x = scale(skeleton.anchors)
        s = scale(skeleton.starts)
        e = scale(skeleton.ends)
        s = np.minimum(s, x)
        e = np.maximum(e, x)
        # Reproduction assumption for the paper's underspecified +/-1 repair:
        # preserve each rounded interval length, pack forward, then backward if
        # needed. Unlike pairwise repair, this cannot break an earlier gap.
        lengths = e - s
        if int(np.sum(lengths) + 2 * max(0, len(s) - 1)) > inner - 1:
            raise RuntimeError("rounded intervals plus gaps exceed the padded canvas")
        new_s = s.copy()
        for i in range(1, len(s)):
            new_s[i] = max(new_s[i], new_s[i - 1] + lengths[i - 1] + 2)
        if new_s[-1] + lengths[-1] > offset + inner - 1:
            new_s[-1] = offset + inner - 1 - lengths[-1]
            for i in range(len(s) - 2, -1, -1):
                new_s[i] = min(new_s[i], new_s[i + 1] - lengths[i] - 2)
        shift = new_s - s
        s, e, x = s + shift, e + shift, x + shift
        if np.any(s > x) or np.any(x > e) or s[0] < offset or e[-1] >= layout_length:
            raise RuntimeError("invalid discretized skeleton")
        if np.any(s[1:] - e[:-1] < 2):
            raise RuntimeError("discrete interval gap invariant violated")
        result.append(DiscreteSkeleton(skeleton.ordering, x, s, e))
    return result, padding


def _uniform_resample(values: np.ndarray, count: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if count <= 0:
        return np.empty(0, dtype=float)
    if values.size == 0:
        return np.full(count, np.nan)
    if values.size == 1:
        return np.full(count, values[0])
    locations = np.linspace(0.0, values.size - 1.0, count)
    # Uniform sampling of existing nodes; tie-to-even rounding is our assumption.
    return values[np.rint(locations).astype(int)]


def _arc_values(frame: AugmentedMergeTreeFrame, arc: TreeArc, upward: bool) -> np.ndarray:
    vertices = arc.regular_vertices if upward else arc.regular_vertices[::-1]
    return frame.values[vertices]


def _sample_path(
    frame: AugmentedMergeTreeFrame,
    arcs: Sequence[TreeArc],
    count: int,
    *,
    upward: bool,
    fallback_start: float,
    fallback_end: float,
) -> np.ndarray:
    if count <= 0:
        return np.empty(0, dtype=float)
    ordered_arcs = list(arcs if upward else reversed(arcs))
    sizes = np.asarray([max(len(a.regular_vertices), 1) for a in ordered_arcs], dtype=float)
    if not ordered_arcs:
        return np.linspace(fallback_start, fallback_end, count + 2)[1:-1]
    exact = count * sizes / np.sum(sizes)
    allocations = np.floor(exact).astype(int)
    remainder = count - int(np.sum(allocations))
    if remainder:
        priority = np.argsort(-(exact - allocations), kind="stable")
        allocations[priority[:remainder]] += 1
    chunks = []
    for arc, allocation in zip(ordered_arcs, allocations):
        if allocation:
            samples = _arc_values(frame, arc, upward)
            if samples.size == 0:
                # An empty augmented arc still has its own scalar bounds.
                # Interpolation over the entire multi-arc path can jump past
                # the next arc and create a spurious extremum.
                start, end = (arc.child, arc.parent) if upward else (arc.parent, arc.child)
                samples = np.linspace(frame.values[start], frame.values[end], int(allocation)+2)[1:-1]
            else:
                samples = _uniform_resample(samples, int(allocation))
            chunks.append(samples)
    values = np.concatenate(chunks) if chunks else np.empty(0)
    if not np.isfinite(values).all():
        raise ValueError('nonfinite scalar path samples')
    return values


def _alternating_positions(anchor: int, start: int, end: int) -> List[int]:
    result: List[int] = []
    radius = 1
    while len(result) < end - start:
        left = anchor - radius
        right = anchor + radius
        if left >= start:
            result.append(left)
        if right <= end:
            result.append(right)
        radius += 1
    return result


def fill_leaf_intervals(
    frame: AugmentedMergeTreeFrame,
    skeleton: DiscreteSkeleton,
    output: np.ndarray,
) -> None:
    """Fig. 4: place extrema, then alternate regular samples left/right."""

    for i, leaf in enumerate(skeleton.ordering):
        anchor = int(skeleton.anchors[i])
        start = int(skeleton.starts[i])
        end = int(skeleton.ends[i])
        output[anchor] = frame.values[leaf]
        positions = _alternating_positions(anchor, start, end)
        arc = frame.arc_for_child(leaf)
        samples = _uniform_resample(frame.values[arc.regular_vertices], len(positions))
        if np.any(np.isnan(samples)):
            samples = np.linspace(frame.values[leaf], frame.values[arc.parent], len(positions) + 2)[1:-1]
        for position, value in zip(positions, samples):
            output[position] = value


def _quadratic_bridge(start_value: float, end_value: float, count: int) -> np.ndarray:
    """Quadratic easing toward the outer endpoint described in Sec. 4.2.2."""

    if count <= 0:
        return np.empty(0)
    t = np.linspace(0.0, 1.0, count + 2)[1:-1]
    return start_value + (end_value - start_value) * t * t


def fill_internal_gap(
    frame: AugmentedMergeTreeFrame,
    left_leaf: int,
    right_leaf: int,
    left_end: int,
    right_start: int,
    output: np.ndarray,
) -> None:
    """Implement Fig. 5A-C for one pair of consecutive leaves."""

    positions = np.arange(left_end + 1, right_start, dtype=np.int64)
    if positions.size == 0:
        return
    lca = frame.lca(left_leaf, right_leaf)
    left_path = frame.nonleaf_path_to_ancestor(left_leaf, lca)
    right_path = frame.nonleaf_path_to_ancestor(right_leaf, lca)
    lca_value = float(frame.values[lca])
    left_value = float(output[left_end])
    right_value = float(output[right_start])

    if not left_path and not right_path:  # sibling leaves, Fig. 5A
        middle = positions.size // 2
        lca_position = int(positions[middle])
        output[lca_position] = lca_value
        left_positions = positions[:middle]
        right_positions = positions[middle + 1 :]
        output[left_positions] = _quadratic_bridge(left_value, lca_value, len(left_positions))
        output[right_positions] = _quadratic_bridge(right_value, lca_value, len(right_positions))[::-1]
        return

    if not left_path:  # direct-deep, Fig. 5B
        output[positions[0]] = lca_value
        rest = positions[1:]
        output[rest] = _sample_path(
            frame,
            right_path,
            len(rest),
            upward=False,
            fallback_start=lca_value,
            fallback_end=right_value,
        )
        return
    if not right_path:
        output[positions[-1]] = lca_value
        rest = positions[:-1]
        output[rest] = _sample_path(
            frame,
            left_path,
            len(rest),
            upward=True,
            fallback_start=left_value,
            fallback_end=lca_value,
        )
        return

    # Deep-deep, Fig. 5C: split proportionally to total path sizes.
    left_size = sum(max(len(a.regular_vertices), 1) for a in left_path)
    right_size = sum(max(len(a.regular_vertices), 1) for a in right_path)
    non_lca = max(int(positions.size) - 1, 0)
    left_count = int(round(non_lca * left_size / (left_size + right_size)))
    left_count = min(max(left_count, 0), non_lca)
    lca_index = left_count
    output[positions[lca_index]] = lca_value
    left_positions = positions[:lca_index]
    right_positions = positions[lca_index + 1 :]
    output[left_positions] = _sample_path(
        frame,
        left_path,
        len(left_positions),
        upward=True,
        fallback_start=left_value,
        fallback_end=lca_value,
    )
    output[right_positions] = _sample_path(
        frame,
        right_path,
        len(right_positions),
        upward=False,
        fallback_start=lca_value,
        fallback_end=right_value,
    )


def fill_boundaries(
    frame: AugmentedMergeTreeFrame,
    skeleton: DiscreteSkeleton,
    output: np.ndarray,
) -> None:
    """Fig. 5D: fill both borders along root-to-extreme-leaf paths."""

    if not skeleton.ordering:
        return
    left_leaf = skeleton.ordering[0]
    right_leaf = skeleton.ordering[-1]
    left_positions = np.arange(0, int(skeleton.starts[0]), dtype=np.int64)
    right_positions = np.arange(int(skeleton.ends[-1]) + 1, output.size, dtype=np.int64)
    left_path = frame.nonleaf_path_to_ancestor(left_leaf, frame.root)
    right_path = frame.nonleaf_path_to_ancestor(right_leaf, frame.root)
    if left_positions.size:
        output[left_positions] = _sample_path(
            frame,
            left_path,
            len(left_positions),
            upward=False,
            fallback_start=float(frame.values[frame.root]),
            fallback_end=float(output[int(skeleton.starts[0])]),
        )
    if right_positions.size:
        output[right_positions] = _sample_path(
            frame,
            right_path,
            len(right_positions),
            upward=True,
            fallback_start=float(output[int(skeleton.ends[-1])]),
            fallback_end=float(frame.values[frame.root]),
        )


def fill_frame(
    frame: AugmentedMergeTreeFrame,
    skeleton: DiscreteSkeleton,
    layout_length: int,
) -> np.ndarray:
    """Paper Sec. 4.2: leaf filling, hierarchical gaps, then borders."""

    output = np.full(layout_length, np.nan, dtype=float)
    fill_leaf_intervals(frame, skeleton, output)
    for i in range(len(skeleton.ordering) - 1):
        fill_internal_gap(
            frame,
            skeleton.ordering[i],
            skeleton.ordering[i + 1],
            int(skeleton.ends[i]),
            int(skeleton.starts[i + 1]),
            output,
        )
    fill_boundaries(frame, skeleton, output)
    if not np.isfinite(output).all():
        raise RuntimeError(f"incomplete or nonfinite hierarchical filling at t={frame.timestep}")
    return output


def compute_spatiotemporal_merge_tree_map(
    frames: Sequence[AugmentedMergeTreeFrame],
    parameters: LayoutParameters,
) -> STMTMResult:
    """Run the complete paper pipeline on precomputed augmented trees."""

    if not frames:
        raise ValueError("at least one frame is required")
    continuous, matches = construct_continuous_skeletons(frames, parameters)
    discrete, padding = discretize_skeletons(frames, continuous, parameters.layout_length)
    rows = [fill_frame(f, s, parameters.layout_length) for f, s in zip(frames, discrete)]
    # Each 1-D slice is rotated and time is horizontal: (linear position, time).
    image = np.column_stack(rows)
    return STMTMResult(parameters, continuous, discrete, matches, image, padding)


def scale_normalized_stress(original_distances: np.ndarray, embedded: np.ndarray) -> float:
    """Scale-Normalized Stress (SNS), Sec. 5.2."""

    d = np.asarray(original_distances, dtype=float)
    x = np.asarray(embedded, dtype=float)
    projected = squareform(pdist(x.reshape(-1, 1)))
    denominator_alpha = float(np.sum(projected * projected))
    alpha = 0.0 if denominator_alpha == 0.0 else float(np.sum(d * projected) / denominator_alpha)
    denominator = float(np.sum(d * d))
    return 0.0 if denominator == 0.0 else float(np.sum((d - alpha * projected) ** 2) / denominator)


def trustworthiness(original: np.ndarray, embedded: np.ndarray, neighbors: int) -> float:
    """Trustworthiness formula used in Sec. 5.2."""

    original = np.asarray(original, dtype=float)
    embedded = np.asarray(embedded, dtype=float).reshape(-1, 1)
    n = original.shape[0]
    k = int(neighbors)
    if not 0 < k < n / 2:
        raise ValueError("trustworthiness requires 0 < k < N/2")
    d0 = squareform(pdist(original))
    d1 = squareform(pdist(embedded))
    np.fill_diagonal(d0, -np.inf)
    np.fill_diagonal(d1, -np.inf)
    order0 = np.argsort(d0, axis=1, kind="stable")
    order1 = np.argsort(d1, axis=1, kind="stable")
    ranks = np.empty_like(order0)
    for i in range(n):
        ranks[i, order0[i]] = np.arange(n)
    penalty = 0
    for i in range(n):
        original_neighbors = set(order0[i, 1 : k + 1])
        projected_neighbors = set(order1[i, 1 : k + 1])
        penalty += sum(int(ranks[i, j]) - k for j in projected_neighbors - original_neighbors)
    return float(1.0 - 2.0 * penalty / (n * k * (2 * n - 3 * k - 1)))


def temporal_displacement(
    skeletons: Sequence[ContinuousSkeleton],
    matches_by_frame: Sequence[Mapping[int, int]],
) -> float:
    """TD from Sec. 5.2, for a forward-propagated sequence."""

    total = 0.0
    for t in range(1, len(skeletons)):
        previous = {
            leaf: float(skeletons[t - 1].anchors[i])
            for i, leaf in enumerate(skeletons[t - 1].ordering)
        }
        current = {
            leaf: float(skeletons[t].anchors[i])
            for i, leaf in enumerate(skeletons[t].ordering)
        }
        for leaf, previous_leaf in matches_by_frame[t].items():
            if leaf in current and previous_leaf in previous:
                total += abs(current[leaf] - previous[previous_leaf])
    return float(total)


def load_frames_json(path: str | Path) -> List[AugmentedMergeTreeFrame]:
    """Load TTK-exported augmented trees from the documented neutral JSON schema."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    records = raw["frames"] if isinstance(raw, dict) else raw
    frames = []
    for record in records:
        arcs = {
            int(a["id"]): TreeArc(
                int(a["id"]),
                int(a["child"]),
                int(a["parent"]),
                np.asarray(a.get("regular_vertices", []), dtype=np.int64),
            )
            for a in record["arcs"]
        }
        children = {int(k): tuple(v) for k, v in record["children"].items()}
        frames.append(
            AugmentedMergeTreeFrame(
                timestep=int(record["timestep"]),
                root=int(record["root"]),
                children=children,
                arcs=arcs,
                values=np.asarray(record["values"], dtype=float),
                coordinates=np.asarray(record["coordinates"], dtype=float),
                domain_min=np.asarray(record["domain_min"], dtype=float),
                domain_max=np.asarray(record["domain_max"], dtype=float),
                sample_ids=np.asarray(record.get("sample_ids", np.arange(len(record["values"]))), dtype=np.int64),
            )
        )
    frames.sort(key=lambda f: f.timestep)
    return frames


def save_result(result: STMTMResult, output_prefix: str | Path, *, cmap: str = "RdBu_r") -> None:
    """Save NumPy values, layout metadata, and a static map image."""

    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    np.save(prefix.with_suffix(".npy"), result.linearized_values)
    metadata = {
        "parameters": asdict(result.parameters),
        "padding": result.padding,
        "shape": list(result.linearized_values.shape),
        "frames": [
            {
                "ordering": list(s.ordering),
                "anchors": s.anchors.tolist(),
                "starts": s.starts.tolist(),
                "ends": s.ends.tolist(),
                "matches": {str(k): int(v) for k, v in result.leaf_matches[i].items()},
            }
            for i, s in enumerate(result.discrete)
        ],
    }
    prefix.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    import matplotlib.pyplot as plt

    plt.imsave(prefix.with_suffix(".png"), result.linearized_values, cmap=cmap, origin="lower")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trees_json", type=Path, help="TTK-exported augmented-tree sequence")
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--preset", choices=sorted(PAPER_PRESETS), required=True)
    parser.add_argument("--mode", choices=("base", "temporal"), default="temporal")
    parser.add_argument("--alpha", type=float, default=1.0, help="Eq. (2); Table 2 does not report it")
    parser.add_argument("--delta", type=float, default=1e-3, help="Eq. (1); Table 2 does not report it")
    parser.add_argument("--cmap", default="RdBu_r")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    frames = load_frames_json(args.trees_json)
    base = LayoutParameters.from_preset(args.preset, mode=args.mode)
    parameters = LayoutParameters(
        **{**asdict(base), "alpha": args.alpha, "min_spacing_delta": args.delta}
    )
    result = compute_spatiotemporal_merge_tree_map(frames, parameters)
    save_result(result, args.output_prefix, cmap=args.cmap)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
