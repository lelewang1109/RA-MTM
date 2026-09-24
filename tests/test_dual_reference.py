"""Independent invariants and counterexamples (stdlib unittest)."""
import unittest
from dataclasses import replace
import numpy as np
from scipy.optimize import linprog
from ramtm.error_budget import (Parameters,project_reference,solve_frame,solve_sequence,
                               solve_dual_reference_sequence,leaf_orders,InfeasibleLayout)
from ramtm.dual_evaluation import position_motion_metrics

class DualReferenceTests(unittest.TestCase):
    def test_projection(self):
        c=np.array([[2.,3.],[4.,7.]])
        np.testing.assert_array_equal(project_reference(c,(1,0)),c[:,0])
        np.testing.assert_array_equal(project_reference(c,reference_axis='y'),c[:,1])
        np.testing.assert_allclose(project_reference(c,(3,4)),c@np.array([.6,.8]))
        np.testing.assert_allclose(project_reference(c,(3e300,4e300)),c@np.array([.6,.8]))
        for a in [(0,0),(np.nan,1),(np.inf,0),(1,2,3)]:
            with self.assertRaises(ValueError):project_reference(c,a)
        with self.assertRaises(ValueError):project_reference(c,(1,0),reference_axis='y')

    def test_tau_independent_lp(self):
        # Independently use interval LEFT endpoints l (solver uses centers z).
        c=np.array([[20.,20.],[90.,30.],[40.,80.],[70.,90.]])
        p=Parameters(width_scale=1.,extra_budget=0.);w=np.array([7.,8.,9.,6.]);h=((0,1),(2,3))
        for axis in [0,1]:
            q=c[:,axis];taus=[];n=len(w)
            for order in leaf_orders(h):
                rows=[];rhs=[]
                def add(parts,b):
                    r=np.zeros(2*n+1)
                    for i,v in parts:r[i]=v
                    rows.append(r);rhs.append(b)
                for i in range(n):
                    add([(i,1),(2*n,-1)],q[i]);add([(i,-1),(2*n,-1)],-q[i])
                    add([(i,1),(n+i,-1)],(1+p.rho)*w[i]/2)
                    add([(i,-1),(n+i,1)],-(1-p.rho)*w[i]/2)
                for i,j in zip(order[:-1],order[1:]):add([(n+i,1),(n+j,-1)],-w[i]-p.gap)
                lp=linprog(np.r_[np.zeros(2*n),1],A_ub=rows,b_ub=rhs,
                           bounds=[(0,120)]*n+[(0,120-v) for v in w]+[(0,None)],method='highs')
                self.assertTrue(lp.success);taus.append(lp.fun)
            r=solve_frame(c,w,h,p=p,reference_axis=axis)
            self.assertAlmostEqual(r['tau'],min(taus),places=7)
            self.assertEqual(len(r['lp_orders']),len(taus))

    def test_identity_permutation_birth_death(self):
        c=[np.array([[30.,30.],[80.,75.]]),np.array([[81.,76.],[31.,31.],[55.,50.]]),np.array([[32.,32.]])]
        ids=[['a','b'],['b','a','c'],['a']];a=[[20,20],[20,20,20],[20]];h=[(0,1),((0,2),1),0]
        d=solve_dual_reference_sequence(c,a,h,feature_ids=ids)
        for t in range(3):
            self.assertEqual(d['x_view'][t]['feature_ids'],ids[t])
            np.testing.assert_array_equal(d['positions'][t][:,0],d['x_view'][t]['x'])
            np.testing.assert_array_equal(d['positions'][t][:,1],d['y_view'][t]['x'])
        m=position_motion_metrics(c,d['positions'],ids)
        self.assertEqual(m['matched_steps'],3)
        with self.assertRaises(ValueError):solve_dual_reference_sequence(c,a,h,feature_ids=[['a','a'],ids[1],ids[2]])
        with self.assertRaises(ValueError):solve_sequence(c,a,h)

    def test_landmark_reference_keeps_centroid_geometry_and_identity(self):
        centers=[np.array([[104.,104.],[150.,160.]]),np.array([[151.,161.],[105.,105.]])]
        landmarks=[np.array([[32.,48.],[170.,180.]]),np.array([[171.,182.],[34.,49.]])]
        ids=[['a','b'],['b','a']];areas=[[20.,20.]]*2;hier=[(0,1)]*2;p=Parameters(canvas=210.)
        result=solve_dual_reference_sequence(centers,areas,hier,p,feature_ids=ids,reference_points=landmarks)
        for axis,key in enumerate(['x_view','y_view']):
            for t,row in enumerate(result[key]):
                np.testing.assert_array_equal(row['reference'],landmarks[t][:,axis])
                self.assertEqual(row['feature_ids'],ids[t])
            expected=solve_frame(centers[1],areas[1],hier[1],
                previous=result[key][0]['x'][::-1],previous_q=landmarks[0][::-1,axis],
                p=p,matched=[True,True],reference=landmarks[1][:,axis])
            np.testing.assert_allclose(result[key][1]['x'],expected['x'],atol=1e-8)
        default=solve_dual_reference_sequence(centers,areas,hier,p,feature_ids=ids)
        explicit=solve_dual_reference_sequence(centers,areas,hier,p,feature_ids=ids,reference_points=centers)
        for a,b in zip(default['positions'],explicit['positions']):np.testing.assert_array_equal(a,b)
        for bad in [landmarks[:1],[landmarks[0],np.array([[np.nan,2],[3,4]])],[landmarks[0],np.ones((1,2))]]:
            with self.assertRaises(ValueError):
                solve_dual_reference_sequence(centers,areas,hier,p,feature_ids=ids,reference_points=bad)

    def test_zero_motion_and_direction_wrap(self):
        c=np.tile([[30.,30.],[80.,80.]],(3,1,1));m=position_motion_metrics(c,c)
        self.assertIsNone(m['direction_error_radians']);self.assertEqual(m['position_2d_nrmse'],0)
        c=np.array([[[0.,0.]],[[-1.,.001]]]);h=np.array([[[0.,0.]],[[-1.,-.001]]])
        self.assertLess(position_motion_metrics(c,h)['direction_error_radians'],.003)
        z=np.zeros_like(c);self.assertAlmostEqual(position_motion_metrics(c,z)['direction_error_radians'],np.pi)

    def test_translation_equivariance_and_capacity(self):
        c=np.array([[[30.,30.],[65.,80.]],[[30.,35.],[65.,85.]]]);a=np.full((2,2),20.);h=[(0,1)]*2
        with self.assertRaises(ValueError):
            solve_dual_reference_sequence(c,a,h,y_parameters=Parameters(width_scale=.03))
        d=solve_dual_reference_sequence(c,a,h)
        np.testing.assert_allclose(d['positions'][1]-d['positions'][0],[[0,5],[0,5]],atol=2e-5)
        with self.assertRaises(InfeasibleLayout):solve_frame(c[0],[2000,2000],h[0])
        np.testing.assert_allclose(solve_sequence(c,a,h)[0]['x'],d['x_view'][0]['x'])

    def test_fixed_world_renderer_and_identity_guard(self):
        from ramtm.baselines import tmtm as b1, stmtm as b2
        from ramtm.reference_anchored import render_dual_reference_sequence
        tr=b1.build_augmented_merge_tree(np.array([9.,0.,3.,1.,6.,2.,8.]))
        coords=np.c_[np.linspace(20,100,7),np.linspace(100,20,7)]
        children={k:tuple(tr.arcs[a].child for a in n.child_arcs) for k,n in tr.nodes.items()}
        arcs={a:b2.TreeArc(a,e.child,e.parent,np.array(e.regular_vertices[::-1],int)) for a,e in tr.arcs.items()}
        f=b2.AugmentedMergeTreeFrame(0,tr.root,children,arcs,tr.values,coords,[0,0],[120,120])
        ids=list(f.leaves);rank={v:i for i,v in enumerate(ids)}
        def h(k):
            ch=children[k]
            if not ch:return rank[k]
            return h(ch[0]) if len(ch)==1 else tuple(h(v) for v in ch)
        c=np.array([f.leaf_centroid(v) for v in ids]);a=[f.leaf_size(v) for v in ids]
        dual=solve_dual_reference_sequence([c,c],[a,a],[h(tr.root)]*2)
        result=render_dual_reference_sequence([f,f],[ids,ids],dual,length=8192)
        for key in ['x_view','y_view']:
            for t in range(2):
                row=dual[key][t];sk=result[key]['skeletons'][t]
                np.testing.assert_array_equal(sk.anchors,np.rint(row['x'][list(row['order'])]*(8191/120)))
                self.assertLessEqual(result[key]['raster_errors'][t]['anchor_error'],120/8191/2+1e-12)
        dual['y_view'][0]['feature_ids']=list(reversed(dual['y_view'][0]['feature_ids']))
        with self.assertRaises(ValueError):render_dual_reference_sequence([f,f],[ids,ids],dual)

    def test_signed_axis_fixed_origin(self):
        p=Parameters(canvas_origin=-120.)
        c=np.array([[30.,30.],[80.,70.]])
        r=solve_frame(c,[20,20],(0,1),p=p,reference_direction=(-1,0))
        self.assertTrue(np.all(r['x']<0));np.testing.assert_array_equal(r['reference'],[-30,-80])
        for bad in [np.nan,np.inf]:
            with self.assertRaises(ValueError):solve_frame(c,[20,20],(0,1),p=replace(p,canvas_origin=bad))

if __name__=='__main__':unittest.main()
