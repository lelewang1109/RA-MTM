"""Controlled scalar fields on a sampled line or a fixed embedded polyline.
Adjacency is always (i,i+1). Trees are extracted from values, never prescribed
independently of the field. Feature sizes are actual augmented leaf-arc counts.
"""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from baselines import temporal_merge_tree_maps as b1
from baselines import spatiotemporal_merge_tree_maps as b2

S=np.linspace(0,120,601)

def field3(shift=0):
    return np.interp(S,[0,10+shift,20+shift,30+shift,40+shift,50+shift,60+shift,70+shift,120],
                     [10,7,0,4,.5,6,1,7,9])

def field4(t=0,change=False):
    return np.interp(S,[0,10,20,30,40,50,60,70,80,90,120],
                     [10,8,0,4+(.3*t if change else 0),.5,6,1,4.5,1.5,8,9])

def make_scene(name,values,coords,summary_only=False):
    trees=[b1.build_augmented_merge_tree(v,'join') for v in values]
    frames=[]; ids=[]; centers=[]; areas=[]; hs=[]
    for t,tree in enumerate(trees):
        leaves=sorted(k for k,node in tree.nodes.items() if not node.child_arcs)
        ids.append(leaves)
        children={k:tuple(tree.arcs[a].child for a in node.child_arcs) for k,node in tree.nodes.items()}
        arcs={a:b2.TreeArc(a,e.child,e.parent,np.array(e.regular_vertices[::-1],int)) for a,e in tree.arcs.items()}
        f=b2.AugmentedMergeTreeFrame(t,tree.root,children,arcs,tree.values,coords,np.min(coords,axis=0),np.max(coords,axis=0))
        frames.append(f)
        centers.append([f.leaf_centroid(k) for k in leaves]);areas.append([f.leaf_size(k) for k in leaves])
        rank={k:i for i,k in enumerate(leaves)}
        def hierarchy(k):
            ch=children[k]
            if not ch:return rank[k]
            if len(ch)==1:return hierarchy(ch[0])
            return tuple(hierarchy(c) for c in ch)
        hs.append(hierarchy(tree.root))
    assert len(set(map(len,ids)))==1, 'this suite holds feature identity count fixed'
    return dict(name=name,values=np.array(values),coords=coords,trees=trees,frames=frames,ids=ids,
                centers=np.array(centers),area=np.array(areas),hierarchies=hs,summary_only=summary_only)

def datasets():
    straight=np.c_[S,np.zeros_like(S)]
    # A fixed polyline folds in x; y=S makes the spatial embedding injective.
    folded=np.c_[np.interp(S,[0,20,40,60,80,120],[0,20,65,40,90,120]),S*.35]
    scenes=[make_scene('static',[field3() for _ in range(13)],straight),
            make_scene('translation',[field3(t) for t in range(13)],straight)]
    # Change only the right outer shoulder; left leaf and separating saddle stay fixed.
    growth=[np.interp(S,[0,15,25,55,85,90+2*t,120],[10,7,0,6,.5,7,9]) for t in range(11)]
    scenes.append(make_scene('growth',growth,straight))
    # Expand all central template coordinates about s=40; the fixed outer
    # domain absorbs the change. Leaf measures grow together, with only grid
    # rounding deviations from proportionality. Translation adds a second,
    # independent control in the combined case.
    for name,translation in [('collective_growth',False),('translation_growth',True)]:
        sequence=[]
        for t in range(11):
            knots=40+(1+.03*t)*(np.array([10,20,30,40,50,60,70])-40)+(t if translation else 0)
            sequence.append(np.interp(S,np.r_[0,knots,120],[10,7,0,4,.5,6,1,7,9]))
        scenes.append(make_scene(name,sequence,straight))
    scenes.append(make_scene('hierarchy_conflict',[field4() for _ in range(11)],folded))
    scenes.append(make_scene('topology_change',[field4(t,True) for t in range(11)],folded))
    crowded=[]
    for t in range(11):
        a,b=25+t,95-t
        crowded.append(np.interp(S,[0,a,60,b,120],[10,0,6,.5,9]))
    scenes.append(make_scene('crowding',crowded,np.c_[55+S/12,S*.4]))
    scenes.append(make_scene('summary_only',[field4(t,True) for t in range(11)],folded,True))
    return scenes

if __name__=='__main__':
    for s in datasets():print(s['name'],s['area'].shape,s['area'][0],s['area'][-1],s['hierarchies'][0],s['hierarchies'][-1])
