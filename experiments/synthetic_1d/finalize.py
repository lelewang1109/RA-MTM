"""Validate complete artifact linkage and write a final SHA-256 manifest."""
from pathlib import Path
import hashlib,json,csv
from datasets import ROOT
from run_experiments import OUT, DATA, FIGURES, TABLES, RECORDS, save_json, write_csv
ver=json.loads((RECORDS/'verification.json').read_text())
assert all(r['status']=='pass' for r in ver['checks'])
assert ver['stmtm_topology_equal']==ver['topology_frames']
required_figures=['comparison.png','diagnostics.png','geometry.png']
required_tables=['metrics.csv','trajectories.csv','applicability.csv','lp_lower_bounds.csv',
                 'topology_checks.csv','ablation.csv','sensitivity.csv','centroid_perturbation.csv']
assert all((FIGURES/f).exists() for f in required_figures)
assert all((TABLES/f).exists() for f in required_tables)
certificates=[]
for p in RECORDS.glob('*_budget_certificates.json'):
    records=json.loads(p.read_text())
    for r in records:
        assert r['min_constraint_slack']>=-1e-6
        assert r['global_gap_bound']<.01
        assert r['qp_gap_bound']<.01,(p,r['qp_gap_bound'])
        certificates.append(r)
boundary=[
 dict(case='coincident_centroids_inverse',TMTM='not evaluated in this formula probe',ST_MTM='inverse 1/d undefined; uniform remains defined',RA_MTM='finite feasible layout',scope='Eq1 boundary, not full STMTM failure'),
 dict(case='discrete_capacity_4_leaves_5_pixels',TMTM='not evaluated in this probe',ST_MTM='one gap per consecutive interval impossible',RA_MTM='not evaluated in this pixel probe',scope='minimum 7 pixels for four singleton intervals'),
 dict(case='absolute_width_capacity',TMTM='not evaluated in this probe',ST_MTM='not evaluated in this probe',RA_MTM='explicit LP/capacity infeasible; never rescales absolute measure',scope='two widths 6 plus gap .5 cannot fit canvas 5')]
write_csv(TABLES/'boundary_checks.csv',boundary)
save_json(RECORDS/'validation_summary.json',dict(formula_regressions=len(ver['checks']),scalar_topology_frames=ver['topology_frames'],
    budget_frames=len(certificates),max_qp_gap_bound=max(r['qp_gap_bound'] for r in certificates),
    min_constraint_slack=min(r['min_constraint_slack'] for r in certificates)))
print('validated synthetic outputs;',len(certificates),'certified frames')
