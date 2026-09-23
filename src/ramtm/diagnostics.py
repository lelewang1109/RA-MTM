"""Independent feasibility diagnostics, never used to tune or repair layouts."""
import numpy as np
from .error_budget import leaf_orders, constraints, checked_lp


def hierarchy_signature(hierarchy):
    """Unordered internal leaf clusters; sibling orientation is not topology."""
    clusters=[]
    def walk(h):
        if isinstance(h,(int,np.integer)):return (int(h),)
        members=tuple(sorted(i for child in h for i in walk(child)))
        clusters.append(members)
        return members
    walk(hierarchy)
    return tuple(sorted(clusters))


def target_error_lower_bound(centers,measure,hierarchy,budget,target,p):
    """Exact min max_i |x_i-target_i| in the CURRENT budgeted feasible set.

    target=q_t+e_(t-1) gives unavoidable step-motion error conditional on the
    previous layout; target=q_t+e_0 gives unavoidable cumulative-motion error
    conditional on the first layout. Neither is a lower bound on mean error.
    """
    q=np.asarray(centers)[:,0];target=np.asarray(target);n=len(q)
    width=p.width_scale*np.asarray(measure)
    values=[]
    for order in leaf_orders(hierarchy):
        A,b,bounds=constraints(width,order,p)
        R=np.c_[np.eye(n),np.zeros((n,n))]
        A=np.vstack([A,R,-R]);b=np.r_[b,q-budget,-q-budget]
        E=np.c_[R,-np.ones(n)];F=np.c_[-R,-np.ones(n)]
        result=checked_lp(np.r_[np.zeros(2*n),1.],np.vstack([np.c_[-A,np.zeros(len(A))],E,F]),
                          np.r_[-b,target,-target],bounds+[(0,None)])
        if result is not None:values.append(float(result.fun))
    if not values:raise RuntimeError('diagnostic found an empty budgeted feasible set')
    return min(values)


def geometry_diagnostics(centers,budget):
    """Exact-projection distortion and a necessary box-budget geometry bound.

    d_ij >= |q_i-q_j| and |x_i-x_j| <= |q_i-q_j|+2B. Thus the positive
    residual beyond that upper bound is unavoidable. Hierarchy/width constraints
    can increase the bound. This does NOT assert that direct projection is legal.
    """
    c=np.asarray(centers);q=c[:,0]
    d=np.linalg.norm(c[:,None,:]-c[None,:,:],axis=-1)
    dq=abs(q[:,None]-q[None,:]);den=np.sum(d*d)
    if den==0:return 0.,0.
    return (float(np.sqrt(np.sum((d-dq)**2)/den)),
            float(np.sqrt(np.sum(np.maximum(d-dq-2*budget,0.)**2)/den)))


def project_reference(centers,angle_degrees,domain_side=120.):
    """Rigid basis rotation, with a fixed origin from the ORIGINAL square.

    No per-frame fitting or axis selection. Euclidean distances and areas stay
    unchanged; the canvas is the projection of the full square, not the data.
    """
    theta=np.deg2rad(angle_degrees)
    axis=np.array([np.cos(theta),np.sin(theta)])
    normal=np.array([-axis[1],axis[0]])
    corners=domain_side*np.array([[0,0],[0,1],[1,0],[1,1]])
    bounds=corners@axis
    transformed=np.asarray(centers)@np.stack([axis,normal],axis=1)
    transformed[...,0]-=bounds.min()
    return transformed,float(np.ptp(bounds))
