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
    temporal_mode: str = 'residual'

class InfeasibleLayout(ValueError):
    pass

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
    return np.array(rows), np.array(rhs), [(0,p.canvas)]*n+[(w/2,p.canvas-w/2) for w in width]

def checked_lp(c, A, b, bounds):
    r=linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    if r.status==2:
        return None
    if not r.success:
        raise RuntimeError('LP numerical failure (not classified infeasible): '+r.message)
    return r

def solve_frame(centers, measure, hierarchy, previous=None, previous_q=None, p=Parameters()):
    c=np.asarray(centers,float); q=c[:,0]; w=p.width_scale*np.asarray(measure,float); n=len(q)
    if not np.isfinite(c).all() or not 0<=p.rho<=1 or p.extra_budget<0:
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
    best=None
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
        goal=None if previous is None else (previous+q-previous_q if p.temporal_mode=='residual' else previous)
        def fun(v):
            ans=np.sum((B@v-d)**2)+p.eccentricity_weight*np.sum((D@v)**2)
            if goal is not None:ans+=p.motion_weight*np.sum((v[:n]-goal)**2)
            return float(ans)
        def jac(v):
            g=2*B.T@(B@v-d)+2*p.eccentricity_weight*D.T@(D@v)
            if goal is not None:g[:n]+=2*p.motion_weight*(v[:n]-goal)
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
        if goal is None or p.motion_weight == 0:
            # The first-frame objective is translation invariant. Fix its free
            # gauge by the closest feasible mean reference, without changing
            # stress, eccentricity, or the LP error budget.
            low=max(float(np.max(q-budget-opt.x[:n])),float(np.max(w/2-opt.x[n:])))
            high=min(float(np.min(q+budget-opt.x[:n])),float(np.min(p.canvas-w/2-opt.x[n:])))
            if low <= high + 1e-8:
                opt.x += np.clip(float(np.mean(q-opt.x[:n])),low,max(low,high))
        slack=float(np.min(A@opt.x-b))
        if slack < -1e-6:raise RuntimeError('QP returned an invalid layout')
        val=fun(opt.x)
        oracle=checked_lp(jac(opt.x),-A,-b,bounds)
        if oracle is None:raise RuntimeError('no feasible optimality oracle')
        gap_bound=max(0.,float(jac(opt.x)@(opt.x-oracle.x)))
        if best is None or val<best['objective']-1e-9:
            best=dict(x=opt.x[:n],z=opt.x[n:],w=w,order=order,tau=float(tau),budget=float(budget),
                      objective=val,min_constraint_slack=slack,qp_gap_bound=gap_bound,lp_orders=records)
    if best is None:raise RuntimeError('no QP solution after a feasible LP')
    return best

def solve_sequence(centers,measure,hierarchies,p=Parameters()):
    out=[]
    for t in range(len(centers)):
        out.append(solve_frame(centers[t],measure[t],hierarchies[t],None if not t else out[-1]['x'],
                               None if not t else centers[t-1,:,0],p))
    return out
