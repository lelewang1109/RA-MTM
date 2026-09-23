"""Fixed-reference, absolute-measure, hierarchy-constrained error-budget layout.
Generalizes the existing fig2_fig7_controlled prototype, without proxy baselines.
Only leaf intervals are produced: no claim of full scalar-field reconstruction.
"""
from dataclasses import dataclass, asdict
from itertools import product, permutations, combinations
import numpy as np
from scipy.optimize import linprog, minimize
from scipy.linalg import null_space
from types import SimpleNamespace

@dataclass(frozen=True)
class Parameters:
    canvas: float = 120.0
    width_scale: float = 0.06
    gap: float = 0.5
    rho: float = 0.5
    extra_budget: float = 1.0
    motion_weight: float = 0.5
    eccentricity_weight: float = 0.1
    reference_weight: float = 4.0
    geometry_weight: float = 1.0
    normalize_terms: bool = True
    temporal_mode: str = 'residual'
    canvas_origin: float = 0.0

class InfeasibleLayout(ValueError):
    pass

def reference_unit_direction(dimension, reference_direction=None, reference_axis=None):
    """Normalize a finite nonzero direction; default is the first Cartesian axis.

    Scale of the supplied vector has no effect. Axis accepts an index or x/y/z.
    Directions are fixed across time. Canvas origin/extent must be specified in
    projected world units by the caller, never estimated from frame centroids.
    """
    if reference_direction is not None and reference_axis is not None:
        raise ValueError('specify a direction or an axis, not both')
    if reference_direction is None:
        axis = 0 if reference_axis is None else reference_axis
        if isinstance(axis, str):
            if axis not in ('x', 'y', 'z'):
                raise ValueError('unknown reference axis')
            axis = ('x', 'y', 'z').index(axis)
        if not isinstance(axis, (int, np.integer)) or not 0 <= axis < dimension:
            raise ValueError('reference axis outside spatial dimension')
        direction = np.eye(dimension)[axis]
    else:
        direction = np.asarray(reference_direction, float)
    if direction.shape != (dimension,) or not np.isfinite(direction).all():
        raise ValueError('reference direction must be finite with one entry per dimension')
    scale = np.max(abs(direction))
    if scale == 0:
        raise ValueError('reference direction must be nonzero')
    direction = direction / scale
    return direction / np.linalg.norm(direction)


def project_reference(centers, reference_direction=None, *, reference_axis=None):
    """q = C @ unit(a), preserving projected world coordinates and units."""
    c = np.asarray(centers, float)
    if c.ndim < 2 or c.shape[-1] == 0 or not np.isfinite(c).all():
        raise ValueError('finite centers with a spatial dimension required')
    return c @ reference_unit_direction(c.shape[-1], reference_direction, reference_axis)


def leaf_orders(tree):
    if isinstance(tree, (int, np.integer)):
        return [(int(tree),)]
    result = []
    for children in product(*(leaf_orders(c) for c in tree)):
        for perm in permutations(children):
            result.append(sum(perm, ()))
    return sorted(set(result))

def constraints(width, order, p):
    n = len(width)
    if np.any(width <= 0) or not np.isfinite(width).all():
        raise ValueError('positive finite absolute measures are required')
    if width.sum() + (n-1)*p.gap > p.canvas + 1e-9:
        raise InfeasibleLayout('absolute widths and gaps exceed the canvas')
    rows, rhs = [], []
    for a,b in zip(order[:-1], order[1:]):
        r = np.zeros(2*n); r[n+b]=1; r[n+a]=-1
        rows.append(r); rhs.append((width[a]+width[b])/2+p.gap)
    for i in range(n):
        r = np.zeros(2*n); r[i]=1; r[n+i]=-1
        cap=p.rho*width[i]/2
        rows.extend([r,-r]); rhs.extend([-cap,-cap])
    return np.array(rows), np.array(rhs), [(p.canvas_origin,p.canvas_origin+p.canvas)]*n+[(p.canvas_origin+w/2,p.canvas_origin+p.canvas-w/2) for w in width]

def checked_lp(c, A, b, bounds):
    r=linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    if r.status==2:
        return None
    if not r.success:
        raise RuntimeError('LP numerical failure (not classified infeasible): '+r.message)
    return r

def solve_frame(centers, measure, hierarchy, previous=None, previous_q=None, p=Parameters(), matched=None,
                reference=None, temporal_confidence=None, *, reference_direction=None, reference_axis=None):
    c=np.asarray(centers,float)
    if c.ndim != 2 or not len(c):raise ValueError("centers must be a nonempty matrix")
    n=len(c)
    direction=reference_unit_direction(c.shape[1],reference_direction,reference_axis)
    # Geometry describes leaf supports; a world reference need not be their
    # centroid. In particular, a support can change abruptly at a saddle event
    # while its extremum stays at exactly the same spatial sample.
    q=project_reference(c,direction) if reference is None else np.asarray(reference,float)
    if reference is not None and (reference_direction is not None or reference_axis is not None):
        raise ValueError("explicit reference cannot be combined with a direction")
    if q.shape!=(n,) or not np.isfinite(q).all():raise ValueError('invalid reference positions')
    w=p.width_scale*np.asarray(measure,float)
    if w.shape != (n,):raise ValueError("measure must have one entry per leaf")
    # Dynamic sequences supply previous positions in current-leaf order. Births
    # have no temporal target; do not turn their missing history into a penalty.
    mask=np.ones(n,dtype=bool) if matched is None else np.asarray(matched,dtype=bool)
    if mask.shape!=(n,):raise ValueError('matched must have one entry per current leaf')
    confidence=np.ones(n) if temporal_confidence is None else np.asarray(temporal_confidence,float)
    if confidence.shape!=(n,) or not np.isfinite(confidence).all() or np.any((confidence<0)|(confidence>1)):
        raise ValueError('temporal confidence must be finite and in [0,1]')
    if previous is not None:
        previous=np.asarray(previous,float)
        previous_q=np.asarray(previous_q,float) if previous_q is not None else None
        if previous.shape!=(n,) or not np.isfinite(previous[mask]).all():
            raise ValueError('invalid matched previous positions')
        if p.temporal_mode=='residual' and (previous_q is None or previous_q.shape!=(n,) or not np.isfinite(previous_q[mask]).all()):
            raise ValueError('invalid matched previous references')
    weights=[p.reference_weight,p.geometry_weight,p.motion_weight,p.eccentricity_weight]
    if (not np.isfinite(c).all() or not 0<=p.rho<=1 or p.extra_budget<0
            or not np.isfinite(weights).all() or min(weights)<0
            or not np.isfinite([p.canvas,p.canvas_origin,p.width_scale,p.gap,p.extra_budget,p.rho]).all()
            or p.canvas<=0 or p.width_scale<=0 or p.gap<0):
        raise ValueError('invalid geometry or parameters')
    legal=leaf_orders(hierarchy)
    if any(sorted(o)!=list(range(n)) for o in legal):
        raise ValueError('hierarchy must contain every leaf exactly once')
    candidates=[]; records=[]
    for order in legal:
        A,b,bounds=constraints(w,order,p)
        L=np.c_[-A,np.zeros(len(A))]; rhs=-b
        E=np.c_[np.eye(n),np.zeros((n,n)),-np.ones(n)]
        F=np.c_[-np.eye(n),np.zeros((n,n)),-np.ones(n)]
        lp=checked_lp(np.r_[np.zeros(2*n),1.], np.vstack([L,E,F]),np.r_[rhs,q,-q],bounds+[(0,None)])
        records.append(dict(order=list(order),tau=None if lp is None else float(lp.fun)))
        if lp is not None:candidates.append((order,A,b,bounds,lp))
    if not candidates:raise InfeasibleLayout('no legal hierarchy order can fit')
    tau=min(r[-1].fun for r in candidates); budget=tau+p.extra_budget
    best=None;qp_records=[]
    for order,A,b,bounds,lp in candidates:
        if lp.fun>budget+1e-8:continue
        R=np.c_[np.eye(n),np.zeros((n,n))]
        A=np.vstack([A,R,-R]); b=np.r_[b,q-budget,-q-budget]
        start=checked_lp(np.zeros(2*n),-A,-b,bounds)
        if start is None:continue
        pairs=list(combinations(order,2)); B=np.zeros((len(pairs),2*n))
        d=np.array([np.linalg.norm(c[i]-c[j]) for i,j in pairs])
        for k,(i,j) in enumerate(pairs):B[k,j]=1; B[k,i]=-1
        D=np.c_[-np.eye(n),np.eye(n)]
        if p.temporal_mode not in ('residual','stationary'):
            raise ValueError('temporal_mode must be residual or stationary')
        goal=None if previous is None or not mask.any() else (previous[mask]+q[mask]-previous_q[mask] if p.temporal_mode=='residual' else previous[mask])
        # Means keep the balance independent of the number of leaves/pairs.
        # Every residual is a length; dividing the whole objective by canvas^2
        # would only change solver units, not its minimizer.
        gw=p.geometry_weight/(max(1,len(pairs)) if p.normalize_terms else 1)
        rw=p.reference_weight/(n if p.normalize_terms else 1)
        ew=p.eccentricity_weight/(n if p.normalize_terms else 1)
        tw=p.motion_weight/(max(1,int(mask.sum())) if p.normalize_terms else 1)
        def fun(v):
            ans=gw*np.sum((B@v-d)**2)+ew*np.sum((D@v)**2)+rw*np.sum((v[:n]-q)**2)
            if goal is not None:ans+=tw*np.sum(confidence[mask]*(v[:n][mask]-goal)**2)
            return float(ans)
        def jac(v):
            g=2*gw*B.T@(B@v-d)+2*ew*D.T@(D@v)
            g[:n]+=2*rw*(v[:n]-q)
            if goal is not None:g[:n][mask]+=2*tw*confidence[mask]*(v[:n][mask]-goal)
            return g
        # Eliminate z=x when rho=0; opposite active inequalities otherwise make
        # SLSQP falsely report incompatible constraints on a feasible LP face.
        transform=np.vstack([np.eye(n),np.eye(n)]) if p.rho==0 else np.eye(2*n)
        Aa=A@transform
        keep=np.max(abs(Aa),axis=1)>1e-12
        Aa,bb=Aa[keep],b[keep]
        qb=bounds[n:] if p.rho==0 else bounds
        initial=start.x[:n] if p.rho==0 else start.x
        opt=minimize(lambda v:fun(transform@v)/1000,initial,jac=lambda v:transform.T@jac(transform@v)/1000,
                     method='SLSQP',bounds=qb,constraints={'type':'ineq','fun':lambda v:Aa@v-bb,'jac':lambda v:Aa},
                     options={'ftol':1e-13,'maxiter':2000})
        if not opt.success:
            # tau=tau* can leave a lower-dimensional feasible face. Find its
            # universally tight constraints by LP, then solve in its affine hull.
            # This changes coordinates, not the budget or objective.
            dim=len(initial)
            fullA=np.vstack([Aa,np.eye(dim),-np.eye(dim)])
            fullb=np.r_[bb,[lo for lo,hi in qb],[-hi for lo,hi in qb]]
            tight=[]
            for row,limit in zip(fullA,fullb):
                probe=checked_lp(-row,-fullA,-fullb,[(None,None)]*dim)
                if probe is None:raise RuntimeError('QP face unexpectedly infeasible')
                if row@probe.x-limit<1e-8:tight.append(row)
            N=null_space(np.array(tight).reshape(-1,dim)) if tight else np.eye(dim)
            origin=initial.copy()
            if N.shape[1]==0:
                opt=SimpleNamespace(success=True,x=origin,message='zero-dimensional certified LP face')
            else:
                G=fullA@N;h=fullb-fullA@origin;active=np.max(abs(G),axis=1)>1e-10
                G,h=G[active],h[active]
                rr=minimize(lambda y:fun(transform@(origin+N@y))/1000,np.zeros(N.shape[1]),
                    jac=lambda y:N.T@transform.T@jac(transform@(origin+N@y))/1000,
                    method='SLSQP',constraints={'type':'ineq','fun':lambda y:G@y-h,'jac':lambda y:G},
                    options={'ftol':1e-13,'maxiter':2000})
                opt=SimpleNamespace(success=rr.success,x=origin+N@rr.x,message=rr.message)
        if not opt.success:raise RuntimeError('QP numerical failure: '+opt.message)
        opt.x=transform@opt.x
        if not np.isfinite(opt.x).all():raise RuntimeError('QP returned nonfinite coordinates')
        if p.reference_weight == 0 and (goal is None or p.motion_weight == 0):
            # The first-frame objective is translation invariant. Fix its free
            # gauge by the closest feasible mean reference, without changing
            # stress, eccentricity, or the LP error budget.
            low=max(float(np.max(q-budget-opt.x[:n])),float(np.max(p.canvas_origin+w/2-opt.x[n:])))
            high=min(float(np.min(q+budget-opt.x[:n])),float(np.min(p.canvas_origin+p.canvas-w/2-opt.x[n:])))
            if low <= high + 1e-8:
                opt.x += np.clip(float(np.mean(q-opt.x[:n])),low,max(low,high))
        slack=float(np.min(A@opt.x-b))
        if not np.isfinite(slack) or slack < -1e-6:raise RuntimeError('QP returned an invalid layout')
        val=fun(opt.x)
        if not np.isfinite(val):raise RuntimeError('QP returned nonfinite objective')
        oracle=checked_lp(jac(opt.x),-A,-b,bounds)
        if oracle is None:raise RuntimeError('no feasible optimality oracle')
        gap_bound=max(0.,float(jac(opt.x)@(opt.x-oracle.x)))
        qp_records.append(dict(order=list(order),objective=val,gap_bound=gap_bound))
        if best is None or val<best['objective']-1e-9:
            best=dict(x=opt.x[:n],z=opt.x[n:],w=w,order=order,tau=float(tau),budget=float(budget),
                      objective=val,min_constraint_slack=slack,qp_gap_bound=gap_bound,lp_orders=records)
    if best is None:raise RuntimeError('no QP solution after a feasible LP')
    best['qp_orders']=qp_records
    best['global_gap_bound']=max(0.,best['objective']-min(v['objective']-v['gap_bound'] for v in qp_records))
    best['reference']=q.copy()
    best['reference_direction']=None if reference is not None else direction.copy()
    best['temporal_confidence']=np.where(mask,confidence,0.)
    return best

def solve_sequence(centers,measure,hierarchies,p=Parameters(), *,
                   reference_direction=None, reference_axis=None, feature_ids=None):
    """Solve fixed-axis views, optionally matching persistent IDs across frames.

    Without IDs the legacy contract is a fixed feature count and row identity.
    With IDs births/deaths and row permutations are supported; IDs must be unique
    in each frame and represent tracks, not transient scalar-grid vertex IDs.
    """
    if not len(centers) or not len(centers)==len(measure)==len(hierarchies):
        raise ValueError('nonempty equal-length sequences required')
    if feature_ids is None:
        n=len(centers[0])
        if any(len(c)!=n for c in centers):raise ValueError('variable counts require feature_ids')
        feature_ids=[list(range(n)) for _ in centers]
    if len(feature_ids)!=len(centers):raise ValueError('one ID list per frame required')
    out=[]
    for t,(c,a,h,ids) in enumerate(zip(centers,measure,hierarchies,feature_ids)):
        if len(ids)!=len(c) or len(set(ids))!=len(ids):
            raise ValueError('unique feature IDs required for every row')
        previous=previous_q=mask=None
        if t:
            lookup={key:i for i,key in enumerate(feature_ids[t-1])}
            mask=np.array([key in lookup for key in ids])
            previous=np.zeros(len(ids));previous_q=np.zeros(len(ids))
            for i,key in enumerate(ids):
                if mask[i]:
                    j=lookup[key];previous[i]=out[-1]['x'][j];previous_q[i]=out[-1]['reference'][j]
        row=solve_frame(c,a,h,previous,previous_q,p,mask,
                        reference_direction=reference_direction,reference_axis=reference_axis)
        row['feature_ids']=list(ids)
        out.append(row)
    return out


def solve_dual_reference_sequence(centers,measure,hierarchies,p=Parameters(), *,
                                  feature_ids=None, y_parameters=None):
    """Complementary Cartesian views with shared identity, not a 2-D field inverse."""
    if any(np.asarray(c).ndim!=2 or np.asarray(c).shape[1]!=2 for c in centers):
        raise ValueError('dual Cartesian reconstruction requires 2-D centroids')
    if y_parameters is not None and y_parameters.width_scale != p.width_scale:
        raise ValueError('dual views must share the same absolute measure-to-width scale')
    x=solve_sequence(centers,measure,hierarchies,p,reference_axis='x',feature_ids=feature_ids)
    y=solve_sequence(centers,measure,hierarchies,p if y_parameters is None else y_parameters,
                     reference_axis='y',feature_ids=feature_ids)
    positions=[]
    for xv,yv in zip(x,y):
        if xv['feature_ids']!=yv['feature_ids']:raise ValueError('view identity mismatch')
        positions.append(np.column_stack((xv['x'],yv['x'])))
    return dict(x_view=x,y_view=y,positions=positions,feature_ids=[r['feature_ids'] for r in x])
