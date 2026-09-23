"""Exact feature-level controls complement grid-quantized full scalar evidence."""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from ramtm.error_budget import Parameters,solve_dual_reference_sequence
from ramtm.dual_evaluation import position_motion_metrics
from ramtm.baselines.stmtm import LayoutParameters,project_leaf_anchors
from types import SimpleNamespace
OUT=ROOT/'results/dual_reference/records'

def main():
    records=[];p=Parameters(width_scale=.012)
    for name,v in [('pure_x',(0.6,0)),('pure_y',(0,.6)),('diagonal',(.6,.4)),('zero',(0,0))]:
        c=np.array([[25.,25.],[55.,40.],[80.,80.]])[None,:,:]+np.arange(21)[:,None,None]*np.array(v)
        a=np.full((21,3),200.);dual=solve_dual_reference_sequence(c,a,[((0,1),2)]*21,p)
        d=np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)
        assert np.max(abs(d-d[0]))<1e-12
        previous=None;anchors=[]
        for t in range(21):
            frame=SimpleNamespace(timestep=t,leaf_centroid=lambda i,t=t:c[t,i])
            pars=LayoutParameters('uniform',7.2,.95,.5,2048,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
            x=project_leaf_anchors(frame,(0,1,2),pars,previous)
            previous=dict(enumerate(x));anchors.append(x)
        assert np.max(abs(np.array(anchors)-anchors[0]))<1e-5
        m=position_motion_metrics(c,dual['positions'])
        assert m['motion_2d_nmae']<1e-7
        records.append(dict(case=name,pairwise_max_change=float(np.max(abs(d-d[0]))),
            stmtm_anchor_max_change=float(np.max(abs(np.array(anchors)-anchors[0]))),**m))
    for axis in [0,1]:
        c=np.array([[50.,20.],[50.,80.]])
        if axis:c=c[:,::-1]
        result=solve_dual_reference_sequence([c,c],[[200,200]]*2,[(0,1)]*2,p)
        rows=[result['x_view'][0],result['y_view'][0]]
        assert abs(rows[axis]['reference'][0]-rows[axis]['reference'][1])<1e-12
        assert rows[axis]['tau']>0 and rows[1-axis]['tau']<1e-9
        records.append(dict(case='same_y' if axis else 'same_x',tau_x=rows[0]['tau'],tau_y=rows[1]['tau']))
    (OUT/'exact_mechanisms.json').write_text(json.dumps(records,indent=2,allow_nan=False))
    print('PASS exact translations, ST invariance, zero motion, complementary crowding')
if __name__=='__main__':main()
