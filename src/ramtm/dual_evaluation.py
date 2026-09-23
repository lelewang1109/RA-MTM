"""Feature-level 2-D fidelity, fixed-domain normalization, explicit ID matching."""
import numpy as np


def position_motion_metrics(centers, positions, feature_ids=None, domain_extent=(120.,120.),
                            minimum_motion=0.12):
    """RMSE of Euclidean position / fixed diagonal; angular errors in radians.

    Trajectories start at track birth. Direction excludes true speed <= threshold.
    A stationary predicted vector for a moving truth gets pi (maximum penalty),
    and is counted explicitly; it is never treated as an accurate direction.
    IDs that disappear and reappear start a new trajectory segment.
    """
    extent=np.asarray(domain_extent,float)
    if extent.shape!=(2,) or not np.isfinite(extent).all() or np.any(extent<=0):
        raise ValueError('two positive finite fixed domain extents required')
    if not np.isfinite(minimum_motion) or minimum_motion<0:
        raise ValueError('minimum_motion must be finite and nonnegative')
    if not len(centers) or len(centers)!=len(positions):raise ValueError('equal nonempty sequences required')
    if feature_ids is None:
        n=len(centers[0])
        if any(len(c)!=n for c in centers):raise ValueError('variable counts require IDs')
        feature_ids=[list(range(n)) for _ in centers]
    if len(feature_ids)!=len(centers):raise ValueError('one ID list per frame required')
    errors=[];steps=[];magnitudes=[];trajectories=[];angles=[];zero_predictions=0
    previous={};birth={}
    for c,h,ids in zip(centers,positions,feature_ids):
        c,h=np.asarray(c,float),np.asarray(h,float)
        if c.shape!=h.shape or c.ndim!=2 or c.shape[1]!=2 or not len(c) or not np.isfinite([c,h]).all():
            raise ValueError('finite matching (features,2) arrays required')
        if len(ids)!=len(c) or len(set(ids))!=len(ids):raise ValueError('unique aligned feature IDs required')
        current={}
        for truth,pred,key in zip(c,h,ids):
            e=pred-truth;errors.append(e);current[key]=(truth,pred)
            if key not in previous:birth[key]=e
            else:
                vc=truth-previous[key][0];vh=pred-previous[key][1]
                steps.append(np.linalg.norm(vh-vc));magnitudes.append(abs(np.linalg.norm(vh)-np.linalg.norm(vc)))
                trajectories.append(np.linalg.norm(e-birth[key]))
                if np.linalg.norm(vc)>minimum_motion:
                    if np.linalg.norm(vh)<=1e-10:
                        angles.append(np.pi);zero_predictions+=1
                    else:
                        diff=np.arctan2(vh[1],vh[0])-np.arctan2(vc[1],vc[0])
                        angles.append(abs(np.arctan2(np.sin(diff),np.cos(diff))))
        previous=current
    e=np.array(errors);diag=np.linalg.norm(extent)
    avg=lambda a:float(np.mean(a)) if len(a) else None
    return dict(position_2d_nrmse=float(np.sqrt(np.mean(np.sum(e*e,axis=1)))/diag),
        position_2d_nmae=float(np.mean(np.linalg.norm(e,axis=1))/diag),
        reference_x_nmae=float(np.mean(abs(e[:,0]))/extent[0]),
        reference_y_nmae=float(np.mean(abs(e[:,1]))/extent[1]),
        reference_x_p95=float(np.quantile(abs(e[:,0]),.95)/extent[0]),
        reference_y_p95=float(np.quantile(abs(e[:,1]),.95)/extent[1]),
        motion_2d_nmae=avg(np.asarray(steps)/diag),
        motion_magnitude_2d_nmae=avg(np.asarray(magnitudes)/diag),
        trajectory_2d_nmae=avg(np.asarray(trajectories)/diag),
        direction_error_radians=avg(angles),direction_count=len(angles),
        direction_zero_predictions=zero_predictions,matched_steps=len(steps),
        minimum_motion=float(minimum_motion))
