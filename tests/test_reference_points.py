import unittest
from types import SimpleNamespace
import numpy as np
from ramtm.reference_points import reference_points_from_frames,reconstruct_xy

class ReferencePointTests(unittest.TestCase):
    def test_qp_certificate_polish_regression(self):
        import json
        from pathlib import Path
        from ramtm.error_budget import solve_frame,Parameters
        f=json.loads((Path(__file__).parent/'fixtures/qp_polish.json').read_text())
        f.pop('source');f['p']=Parameters(**f.pop('parameters'))
        row=solve_frame(**f)
        self.assertLess(row['global_gap_bound'],.01)
        self.assertGreaterEqual(row['min_constraint_slack'],-1e-6)
        self.assertLessEqual(np.max(abs(row['x']-row['reference'])),row['budget']+1e-6)

    def test_explicit_semantics_and_row_identity(self):
        f=SimpleNamespace(leaves=[1,3],coordinates=np.array([[0,0],[20,30],[50,50],[80,90]]),
                          leaf_centroid=lambda i: np.array([50+i,50-i]))
        np.testing.assert_array_equal(reference_points_from_frames([f],[[3,1]],kind='extremum')[0],[[80,90],[20,30]])
        np.testing.assert_array_equal(reference_points_from_frames([f],[[3,1]],kind='centroid')[0],[[53,47],[51,49]])
        for ids in [[1,1],[1],[1,2]]:
            with self.assertRaises(ValueError):reference_points_from_frames([f],[ids],kind='extremum')
        with self.assertRaises(ValueError):reference_points_from_frames([f],[[1,3]],kind='guess')

    def test_reconstruction_rejects_time_identity_and_shape_mismatch(self):
        x=[dict(feature_ids=['a','b'],x=[10,20])];y=[dict(feature_ids=['a','b'],x=[30,40])]
        np.testing.assert_array_equal(reconstruct_xy(x,y)[0],[[10,30],[20,40]])
        for bad in [[],y+y,[dict(feature_ids=['b','a'],x=[30,40])],
                    [dict(feature_ids=['a','b'],x=[30])],[dict(feature_ids=['a','b'],x=[30,np.nan])]]:
            with self.assertRaises(ValueError):reconstruct_xy(x,bad)
if __name__=='__main__':unittest.main()
