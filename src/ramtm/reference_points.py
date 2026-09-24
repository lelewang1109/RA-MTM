"""Explicit landmark semantics for fixed-world reference projections.

Extremum = actual leaf vertex (minimum for a join tree, maximum for a split
 tree). Centroid = unweighted leaf-arc support centroid. Neither is a basin
 center or a tracked physical object. Geometry always uses support centroids.
"""
import numpy as np


def reference_points_from_frames(frames, leaf_ids, *, kind):
    """Return landmarks in the exact leaf-row order; never infer correspondence."""
    if kind not in ('extremum', 'centroid'):
        raise ValueError('reference kind must explicitly be extremum or centroid')
    if not frames or len(frames) != len(leaf_ids):
        raise ValueError('nonempty matching frames and leaf ID lists required')
    result = []
    for frame, ids in zip(frames, leaf_ids):
        if len(ids) != len(set(ids)) or set(ids) != set(frame.leaves):
            raise ValueError('reference IDs must identify every frame leaf exactly once')
        points = (frame.coordinates[list(ids)] if kind == 'extremum' else
                  np.array([frame.leaf_centroid(i) for i in ids]))
        if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
            raise ValueError('finite 2-D reference points required')
        result.append(points.copy())
    return result


def reconstruct_xy(x_view, y_view):
    """Pair anchors only by identical ordered persistent IDs, with no silent zip."""
    if not x_view or len(x_view) != len(y_view):
        raise ValueError('nonempty time-aligned X/Y views required')
    result = []
    for x, y in zip(x_view, y_view):
        ids = x['feature_ids']
        if ids != y['feature_ids'] or len(set(ids)) != len(ids):
            raise ValueError('X/Y persistent identities must match exactly')
        xx, yy = np.asarray(x['x']), np.asarray(y['x'])
        if xx.shape != (len(ids),) or yy.shape != xx.shape or not np.isfinite([xx, yy]).all():
            raise ValueError('finite anchors must match feature identities')
        result.append(np.column_stack((xx, yy)))
    return result
