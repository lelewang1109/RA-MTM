"""Task metrics with common ground truth and a fixed, method-independent scale.

No per-frame alignment, fitted scales, outcome-dependent thresholds, or aggregate
winner score. Position/trajectory errors use the domain span, never signal size.
Widths use growth relative to the first frame; log errors treat expansion and
contraction symmetrically. These are encoding fidelity, not user-study accuracy.
"""
import numpy as np


def task_metrics(centers, measure, anchors, widths, domain_span):
    c,a,x,w=map(lambda v: np.asarray(v,float),(centers,measure,anchors,widths))
    q=c[:,:,0]
    if q.shape != x.shape or a.shape != w.shape or a.shape != x.shape:
        raise ValueError('same frames/features required for truth and all outputs')
    if len(x)<2 or domain_span<=0 or not all(np.isfinite(v).all() for v in (c,a,x,w)) or np.any(a<=0) or np.any(w<=0):
        raise ValueError('finite positive measures/widths, span and at least two frames required')
    e=x-q
    trajectory=(x-x[0])-(q-q[0])
    loggrowth=np.log(w/w[0])-np.log(a/a[0])
    total=np.log(w.sum(1)/w[0].sum())-np.log(a.sum(1)/a[0].sum())
    stable=np.ptp(a,axis=0)<1e-9
    return dict(
        reference_nmae=float(np.mean(abs(e))/domain_span),
        reference_p95=float(np.quantile(abs(e),.95)/domain_span),
        trajectory_nmae=float(np.mean(abs(trajectory[1:]))/domain_span),
        common_motion_nmae=float(np.mean(abs(trajectory[1:].mean(1)))/domain_span),
        motion_step_nmae=float(np.mean(abs(np.diff(e,axis=0)))/domain_span),
        growth_log_mae=float(np.mean(abs(loggrowth[1:]))),
        total_growth_log_mae=float(np.mean(abs(total[1:]))),
        unchanged_size_log_drift=float(np.max(abs(np.log(w[:,stable]/w[0,stable])))) if stable.any() else None,
    )


def orient_once(scene, result):
    """Resolve only a reflection/translation gauge from the first frame.

    Baseline native layouts are retained. No scale fitting or later truth is used.
    Applying this to the output cannot change distances, widths or topology.
    """
    r=result;q=scene['centers'][0,:,0];x=r['x'][0]
    sign=1 if np.dot(x-x.mean(),q-q.mean())>=0 else -1
    shift=float(q.mean()-sign*x.mean())
    r['x']=sign*r['x']+shift;r['z']=sign*r['z']+shift
    if 'pixel_x' in r:
        r['pixel_x']=sign*r['pixel_x']+shift;r['pixel_z']=sign*r['pixel_z']+shift
    if sign<0:
        r['order']=[tuple(reversed(o)) for o in r['order']]
        if 'scalar_map' in r:r['scalar_map']=r['scalar_map'][::-1]
        if 'sample_positions' in r:r['sample_positions']=r['scalar_map'].shape[0]-1-r['sample_positions']
    r['display_reflection']=sign;r['display_translation']=shift
    return r
