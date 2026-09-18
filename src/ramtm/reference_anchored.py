"""RA-MTM: Reference-Anchored Merge Tree Maps (working research name).

The layout optimizer is error_budget.py. This module adds a fixed-world pixel
mapping and reuses the audited ST-MTM scalar/path filling as a shared renderer.
That renderer is an explicit borrowed component, not a new contribution and not
the ST-MTM layout algorithm. A map is a tree-based summary, not a reconstructed
2-D field. Absolute widths refer to continuous intervals; raster error is saved.
"""
import numpy as np
from ramtm.error_budget import Parameters, solve_sequence, solve_frame
from ramtm.baselines.stmtm import DiscreteSkeleton, fill_frame

NAME = 'RA-MTM'
FULL_NAME = 'Reference-Anchored Merge Tree Maps'

def render_sequence(frames, feature_ids, layouts, canvas=120., length=2048):
    """Map world [0,canvas] to [0,length-1], identically for every frame.

    No per-frame normalization or silent repair. Insufficient raster capacity
    raises an error; the user can increase length without changing the layout.
    """
    if canvas <= 0 or length < 2:
        raise ValueError('positive canvas and at least two pixels required')
    if not (len(frames)==len(feature_ids)==len(layouts)) or not len(frames):
        raise ValueError('nonempty equal-length input sequences required')
    scale=(length-1)/canvas
    maps=[]; skeletons=[]; errors=[]
    for frame,ids,row in zip(frames,feature_ids,layouts):
        order=np.asarray(row['order'],int)
        x=np.asarray(row['x'])[order];z=np.asarray(row['z'])[order];w=np.asarray(row['w'])[order]
        starts=np.rint((z-w/2)*scale).astype(int)
        ends=np.rint((z+w/2)*scale).astype(int)
        anchors=np.rint(x*scale).astype(int)
        if (np.any(starts<0) or np.any(ends>=length) or np.any(anchors<starts)
                or np.any(anchors>ends) or np.any(starts[1:]-ends[:-1]<2)):
            raise ValueError('fixed-reference raster cannot represent these intervals; increase resolution')
        sk=DiscreteSkeleton(tuple(ids[i] for i in order),anchors,starts,ends)
        values=fill_frame(frame,sk,length)
        if not np.isfinite(values).all():raise RuntimeError('nonfinite scalar rendering')
        maps.append(values);skeletons.append(sk)
        errors.append(dict(anchor_error=float(np.max(abs(anchors/scale-x))),
            interval_extent_error=float(np.max(abs((ends-starts)/scale-w)))))
    return np.column_stack(maps),skeletons,errors
