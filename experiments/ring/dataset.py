"""Ring adapter: parameters read from the locally archived author generator.

No upstream projection/layout implementation is imported or executed.
"""
from pathlib import Path
import ast
import hashlib
import xml.etree.ElementTree as ET
import numpy as np

SOURCE = Path(__file__).parent / 'source'
COMMIT = '2c75a10ed2cd55177a25ff751e0c0a8261200717'


def generate():
    script = SOURCE / 'SpreadingRingGeneration.py'
    workspace = SOURCE / 'dataset_spreading_ring.processor.xml'
    properties = {}
    for node in ast.walk(ast.parse(script.read_text())):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            target = node.targets[0]
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                properties[target.attr] = node.value.args
    literal = ast.literal_eval
    shape = tuple(literal(v) for v in properties['volSize'][2].args)
    bounds = [[literal(v) for v in properties[key][2:4]] for key in ('rangeX', 'rangeY')]
    center = [literal(v) for v in properties['epicenter'][2].args]
    names = ['peak0', 'peakChange', 'mu0', 'muChange', 'omega0', 'omegaChange']
    declared = {name: literal(properties[name][2]) for name in names}
    # Inviwo FloatProperty and vec2 store single-precision values.
    actual = {key: float(np.float32(v)) for key, v in declared.items()}
    actual_center = np.asarray(center, dtype=np.float32).astype(float)
    steps = int(ET.parse(workspace).find(".//Property[@identifier='steps']/value").get('content'))
    x, y = np.mgrid[bounds[0][0]:bounds[0][1]:shape[0]*1j,
                    bounds[1][0]:bounds[1][1]:shape[1]*1j]
    pos = np.dstack((x, y))
    distance = np.sqrt(np.sum((pos-actual_center)**2, axis=2))
    fields = []
    for t in range(steps):
        peak = actual['peak0'] + t*actual['peakChange']
        radius = actual['mu0'] + t*actual['muChange']
        sigma = actual['omega0'] + t*actual['omegaChange']
        field = peak*np.exp(-.5*((distance-radius)/sigma)**2)
        # Source arrays index x,y; pipeline arrays index y,x. This is an axis
        # transpose, not a resampling or an Inviwo memory-layout permutation.
        fields.append(field.T.astype(np.float32))
    fields = np.asarray(fields)
    coordinates = np.c_[x.T.ravel(), y.T.ravel()]
    assert fields.shape == (40, 14, 14) and np.isfinite(fields).all()
    metadata = dict(
        conceptual_origin='Franke et al., Visual Analysis of Spatio-temporal Phenomena with 1D Projections (2021)',
        original_repository='https://github.com/UniStuttgart-VISUS/spatiotemporal1d',
        actual_source='Existing project archive/paper1_author_reference.zip, TMTM author Ring generator and workspace',
        author_repository='https://github.com/Wiebke/TemporalMergeTreeMaps', author_commit=COMMIT,
        generator_path='modules/mergetreemaps/python/processors/SpreadingRingGeneration.py',
        workspace_path='modules/mergetreemaps/data/workspaces/dataset_spreading_ring.inv',
        source_files_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (script, workspace)},
        external_download_used=False,
        external_access_note='Original repository landing page inspected; direct clone/raw archive unavailable due to DNS. Existing archived author source supplied the actual data parameters.',
        declared_parameters=dict(shape_xy=shape, bounds_xy=bounds, center=center, time_steps=steps, **declared),
        actual_float32_property_values=dict(center=actual_center.tolist(), **actual),
        equation='f(x,y,t)=(peak0+t*peakChange)*exp(-0.5*((distance((x,y),center)-(mu0+t*muChange))/(omega0+t*omegaChange))**2)',
        sampling='14 endpoint-inclusive samples per axis on [0,210], np.mgrid; no interpolation, smoothing, noise, or random seed',
        array_order='time,y,x; transpose of source x,y fields; Inviwo-only memory repacking omitted',
        dtype=str(fields.dtype), shape_tyx=list(fields.shape), nonfinite_count=int((~np.isfinite(fields)).sum()),
        sha256_tyx=hashlib.sha256(fields.tobytes()).hexdigest(),
        radius_start=actual['mu0'], radius_end=actual['mu0']+39*actual['muChange'])
    return fields, coordinates, metadata


def persistence_audit(trees, fraction=.001):
    """Elder-rule split-tree pair audit; fail if cancellation would be needed.

    For this input p=.001 is a certified no-op. Merely attaching p to a tree
    would not apply simplification; this explicit audit makes that distinction.
    """
    rows = []
    for t, tree in enumerate(trees):
        pairs = []
        def visit(k):
            children = [tree.arcs[a].child for a in tree.nodes[k].child_arcs]
            if not children:
                return k
            peaks = [visit(c) for c in children]
            elder = max(peaks, key=lambda v: (tree.values[v], -v))
            pairs.extend((v, k, float(tree.values[v]-tree.values[k])) for v in peaks if v != elder)
            return elder
        visit(tree.root)
        threshold = fraction*float(np.ptp(tree.values))
        canceled = [v for v in pairs if v[2] < threshold]
        rows.append(dict(t=t, features=sum(not n.child_arcs for n in tree.nodes.values()),
                         supernodes=len(tree.nodes), finite_pairs=len(pairs),
                         persistence_threshold=threshold,
                         minimum_finite_persistence=min((v[2] for v in pairs), default=None),
                         canceled_features=len(canceled)))
        if canceled:
            raise ValueError(f'Frame {t}: p={fraction} requires cancellation; cannot silently use unsimplified fields')
    return rows
