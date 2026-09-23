"""Seven declared field mechanisms. Truth is extracted support centroids/areas.

Gaussian peaks identify features by a shared construction correspondence. These
are not independent tracking benchmarks. No baseline-specific input changes.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from ramtm.baselines import tmtm as b1, stmtm as b2

CASES=['pure_x','pure_y','diagonal','same_x','same_y','hierarchy_conflict','motion_growth']

def make_mechanism(name, frames=21, grid=65):
    axis=np.linspace(0,120,grid);X,Y=np.meshgrid(axis,axis);coords=np.c_[X.ravel(),Y.ravel()]
    base=np.array([[28.,32.],[58.,45.],[82.,76.]])
    if name=='same_x':base=np.array([[50.,25.],[50.,80.]])
    if name=='same_y':base=np.array([[25.,50.],[80.,50.]])
    if name=='hierarchy_conflict':base=np.array([[25.,25.],[85.,28.],[40.,85.],[70.,90.]])
    amp=np.array([1.,.83,.67,.52])[:len(base)]
    values=[];trees=[];fs=[];ids=[];centers=[];area=[];hierarchies=[]
    for t in range(frames):
        velocity={'pure_x':(.6,0),'pure_y':(0,.6),'diagonal':(.6,.4),'motion_growth':(.4,.3)}.get(name,(0,0))
        mu=base+t*np.array(velocity);sig=np.full(len(base),6.)
        if name=='motion_growth':sig*=np.linspace(1+.015*t,1-.008*t,len(base))
        field=np.max([a*np.exp(-((X-x)**2+(Y-y)**2)/(2*s*s)) for a,(x,y),s in zip(amp,mu,sig)],axis=0)
        tr=b1.build_augmented_merge_tree(field,'split')
        leaves=[k for k,n in tr.nodes.items() if not n.child_arcs]
        if len(leaves)!=len(base):raise RuntimeError('unexpected feature count')
        rr,cc=linear_sum_assignment(np.linalg.norm(mu[:,None]-coords[leaves][None,:],axis=-1))
        leaves=[leaves[cc[list(rr).index(i)]] for i in range(len(base))]
        children={k:tuple(tr.arcs[a].child for a in n.child_arcs) for k,n in tr.nodes.items()}
        arcs={a:b2.TreeArc(a,e.child,e.parent,np.array(e.regular_vertices[::-1],int)) for a,e in tr.arcs.items()}
        f=b2.AugmentedMergeTreeFrame(t,tr.root,children,arcs,tr.values,coords,coords.min(0),coords.max(0))
        rank={k:i for i,k in enumerate(leaves)}
        def h(k):
            ch=children[k]
            if not ch:return rank[k]
            if len(ch)==1:return h(ch[0])
            return tuple(h(v) for v in ch)
        values.append(field);trees.append(tr);fs.append(f);ids.append(leaves)
        centers.append([f.leaf_centroid(k) for k in leaves]);area.append([f.leaf_size(k)*(120/(grid-1))**2 for k in leaves]);hierarchies.append(h(tr.root))
    return dict(name=name,values=np.array(values),coords=coords,trees=trees,frames=fs,ids=ids,
        centers=np.array(centers),area=np.array(area),hierarchies=hierarchies,summary_only=False)
