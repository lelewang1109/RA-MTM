"""Share of the certificate explained by the best witness triple in conflict frames (Sec. 4.1).
Output: prototypes/output/witness.json.  Run: .venv/bin/python -W ignore prototypes/witness_stats.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, replicate as rp, task_reference as tr
from fig_witness import witness

res = {}
for name in ['era5', 'era5_2014', 'wildfire']:
    ds = rp.LOADERS[name](); sc = ds['sc']
    o = rh.run(ds, 0., make_figure=False, return_internal=True); ref = o['_internal']['ref']; theta = o['theta']
    r = []
    for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
        lg = o['frame_log'][t]
        if lg['tau_hier'] - lg['tau_free'] > theta:
            r.append(witness(fr, ids, np.asarray(ref['qs'][t]))[0] / lg['tau_hier'])
    r = np.array(r); res[name] = dict(conflict_frames=len(r), median=float(np.median(r)), share_at_least_half=float(np.mean(r >= .5)), min=float(r.min()))
    print(name, res[name], flush=True)
(tr.OUT / 'witness.json').write_text(json.dumps(res, indent=1))
