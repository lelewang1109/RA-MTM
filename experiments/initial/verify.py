"""Independent formula, invariance, topology and invalid-input regression checks."""
from pathlib import Path
import sys, json, itertools, dataclasses, importlib.util, zipfile
import numpy as np
from datasets import datasets, ROOT, S
sys.path.insert(0,str(ROOT))
from baselines import temporal_merge_tree_maps as b1
from baselines import spatiotemporal_merge_tree_maps as b2
from methods.error_budget import solve_frame, Parameters, InfeasibleLayout, leaf_orders
from run_initial import run_b1,run_b2,save_json,write_csv,OUT

records=[]
def check(name,condition,details=''):
    assert condition,(name,details)
    records.append(dict(check=name,status='pass',details=details))

def clusters(tree):
    """Branch membership using distinct leaf scalar values; ignores root gauge."""
    out=[]
    def visit(k):
        arcs=tree.nodes[k].child_arcs
        if not arcs:return (round(float(tree.values[k]),7),)
        leaves=tuple(sorted(v for a in arcs for v in visit(tree.arcs[a].child)))
        if len(arcs)>1:out.append((round(float(tree.values[k]),7),leaves))
        return leaves
    leaves=visit(tree.root)
    return sorted(out),sorted(leaves)

scenes=datasets();topology=[]
for sc in [s for s in scenes if not s['summary_only']]:
    r1=run_b1(sc);r2=run_b2(sc)
    for t,tree in enumerate(sc['trees']):
        c1=clusters(b1.build_augmented_merge_tree(r1['scalar_map'][:,t]))
        # Repeated sampled values form flat zones. Compare the quotient of
        # consecutive equal values, not SoS-induced zero-persistence extrema.
        v=r2['scalar_map'][:,t]
        v=v[np.r_[True,np.abs(np.diff(v))>1e-10]]
        c2=clusters(b1.build_augmented_merge_tree(v))
        truth=clusters(tree)
        check('TMTM scalar topology '+sc['name']+'/'+str(t),c1==truth)
        # No fabricated claim: report the actual reduced scalar topology check.
        topology.append(dict(scene=sc['name'],t=t,tmtm_equal=c1==truth,stmtm_equal=c2==truth,
                              source_leaves=len(truth[1]),stmtm_leaves=len(c2[1])))
    # Independently enumerate legal leaf orders to verify SciPy OLO costs.
    f=sc['frames'][0];ids=sc['ids'][0]
    exact=min(b2.ordering_cost(f,[ids[i] for i in o]) for o in leaf_orders(sc['hierarchies'][0]))
    got=b2.ordering_cost(f,b2.optimal_hierarchical_leaf_order(f))
    check('OLO exact cost '+sc['name'],abs(exact-got)<1e-8)
write_csv(OUT/'topology_checks.csv',topology)

# Literal Algorithm 1 known seven-sample case: root 0, branching vertices 2,4.
t=b1.build_augmented_merge_tree(np.array([9.,0.,3.,1.,6.,2.,8.]))
l=b1.linearize_tree(t)
check('Algorithm 1 hand-computed sample permutation',np.array_equal(l.position_of_vertex,np.arange(7)))
check('inclusive overlap equation 4',b1.interval_overlap((2,5),(5,8))==1)
# Original-space overlap matrix independently counted from membership indicators.
sc=scenes[1];a,b=sc['trees'][:2]
M=b1.spatial_overlap_matrix(a,b)
check('all subtree overlap counts',all(v==sum(int(i in a.subtree_vertices(x) and i in b.subtree_vertices(y)) for i in range(len(S))) for (x,y),v in M.items()))

f=scenes[0]['frames'][0];ids=scenes[0]['ids'][0];order=tuple(ids)
p=b2.LayoutParameters('uniform',15.,.95,.5,2048,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
q=np.array([f.leaf_centroid(i)[0] for i in order]);x=b2.project_leaf_anchors(f,order,p)
check('Eq1 collinear analytical solution',np.max(abs(x-(q-q.mean())))<1e-6)
start,end=b2.allocate_leaf_intervals(f,order,x,p)
target=p.total_leaf_extent_k*np.array([f.leaf_size(k) for k in order])/sum(f.leaf_size(k) for k in order)
check('Eq2 analytical target widths',np.max(abs(end-start-target))<1e-7)
small=dataclasses.replace(p,total_leaf_extent_k=1e-8)
s,e=b2.allocate_leaf_intervals(f,order,x,small)
check('Eq2 small K feasible (no false infeasibility)',abs(sum(e-s)-small.total_leaf_extent_k)<1e-12)

# Centroids can coincide for separate disjoint supports; inverse 1/d is undefined.
coincident=dataclasses.replace(f,coordinates=np.zeros_like(f.coordinates))
try:b2.project_leaf_anchors(coincident,order,dataclasses.replace(p,weights='inverse'))
except ValueError:rejected=True
else:rejected=False
check('zero-distance inverse variant is rejected',rejected)
xu=b2.project_leaf_anchors(coincident,order,p)
check('zero-distance uniform variant remains defined',np.all(np.diff(xu)>.009999))
ours=solve_frame(np.zeros((3,2))+60,[20,20,20],((0,1),2))
check('coincident centroids budget remains finite',np.isfinite(ours['x']).all())

# Strictly insufficient canvas is infeasible for our method, not secretly rescaled.
try:solve_frame(np.array([[1.,0],[2.,0]]),[100,100],(0,1),p=Parameters(canvas=5))
except InfeasibleLayout:rejected=True
else:rejected=False
check('absolute-width capacity failure is explicit',rejected)
# Known lower bound for inverted B/C forced by ((A,C),(B,D)).
centers=np.c_[[20,40,60,80],np.zeros(4)]
r=solve_frame(centers,np.full(4,100/3),((0,2),(1,3)),p=Parameters(extra_budget=0))
check('LP inverse-order analytical lower bound',abs(r['tau']-10.75)<1e-8,str(r['tau']))
check('zero extra budget respected',np.max(abs(r['x']-centers[:,0]))<=10.750001)

# Replay the old rounding bug without changing the paper objective.
# Three zero-width rounded intervals: repairing the third could break the first gap.
with zipfile.ZipFile(ROOT/'archive/pre_initial_snapshot.zip') as z:
    oldsrc=z.read('论文-2/spatiotemporal_merge_tree_maps.py').decode()
oldpath=ROOT/'tmp/old_stmtm_audit.py';oldpath.write_text(oldsrc)
spec=importlib.util.spec_from_file_location('old_stmtm_audit',oldpath);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
old_inverse=old.project_leaf_anchors(coincident,order,dataclasses.replace(p,weights='inverse'))
check('old inverse silently dropped zero-distance pairs',np.isfinite(old_inverse).all())
old_sample=old._uniform_resample(np.array([0.,10.]),3)
check('sampling fix removes invented scalar values',np.array_equal(b2._uniform_resample(np.array([0.,10.]),3),[0,0,10]) and old_sample[1]==5)
# deterministic search for the previously missed pairwise overlap, over rounding cases
found=None
for count in [3,4]:
    for length in range(5,18):
        for step in [.01,.1,.3,.6,1.]:
            anchors=np.arange(count)*step
            ss=anchors-.003;ee=anchors+.003
            sk=old.ContinuousSkeleton(tuple(range(count)),anchors,ss,ee)
            # Isolate discretization from padding; full span available.
            old.compute_padding=lambda frames,L:0
            saved=b2.compute_padding;b2.compute_padding=lambda frames,L:0
            try:
                d,_=old.discretize_skeletons([f],[sk],length);d=d[0]
                bad=np.any(d.starts[1:]-d.ends[:-1]<2)
                if bad:
                    try:
                        new,_=b2.discretize_skeletons([f],[sk],length)
                        fixed=np.all(new[0].starts[1:]-new[0].ends[:-1]>=2)
                        newstatus='valid'
                    except RuntimeError:fixed=True;newstatus='explicit insufficient capacity'
                    found=dict(count=count,length=length,step=step,old_starts=d.starts.tolist(),old_ends=d.ends.tolist(),new_status=newstatus)
                    check('discrete repair regression',fixed,found)
            except RuntimeError:pass
            finally:b2.compute_padding=saved
            if found:break
        if found:break
    if found:break
# Target a clustered middle of a larger global range, if uniform samples did not expose it.
if not found:
    old.compute_padding=lambda frames,L:0
    saved=b2.compute_padding;b2.compute_padding=lambda frames,L:0
    for length in range(7,30):
        sk=old.ContinuousSkeleton((0,1,2,3),np.array([0,5,5.01,5.02]),np.array([-.01,4.99,5,5.01]),np.array([.01,5.001,5.011,5.021]))
        extra=old.ContinuousSkeleton((0,),np.array([10.]),np.array([9.99]),np.array([10.01]))
        try:
            d=old.discretize_skeletons([f],[sk,extra],length)[0][0]
            if np.any(d.starts[1:]-d.ends[:-1]<2):
                new=b2.discretize_skeletons([f],[sk,extra],length)[0][0]
                found=dict(length=length,old_starts=d.starts.tolist(),old_ends=d.ends.tolist(),new_starts=new.starts.tolist(),new_ends=new.ends.tolist())
                check('discrete repair regression',np.all(new.starts[1:]-new.ends[:-1]>=2),found);break
        except RuntimeError:pass
    b2.compute_padding=saved
check('rounding bug has a concrete counterexample',found is not None)

# Original n-ary handling made a layout despite lacking the binary identity guarantee.
root=b1.SuperNode(0,[0]);nodes={0:root,1:b1.SuperNode(1,[1,2,3]),2:b1.SuperNode(2),3:b1.SuperNode(3),4:b1.SuperNode(4)}
arcs={0:b1.SuperArc(0,0,1,[]),1:b1.SuperArc(1,1,2,[]),2:b1.SuperArc(2,1,3,[]),3:b1.SuperArc(3,1,4,[])}
nonbinary=b1.AugmentedMergeTree(np.array([9,5,0,1,2.]),(5,),'join',0,nodes,arcs,np.zeros(5,int))
try:b1.linearize_tree(nonbinary)
except ValueError:rejected=True
else:rejected=False
check('unprocessed nonbinary tree never masquerades as paper identity',rejected)
save_json(OUT/'verification.json',dict(checks=records,rounding_counterexample=found,
    topology_frames=len(topology),stmtm_topology_equal=sum(r['stmtm_equal'] for r in topology)))
print('PASS',len(records),'checks;',sum(r['stmtm_equal'] for r in topology),'/',len(topology),'STMTM scalar topology checks')
