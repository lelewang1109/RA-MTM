"""Trade-off: position fidelity vs merge-level (topology) fidelity under local relaxation.
Sweeps the cap on the merge-level change a single relaxation may cause (fraction of the
field's value range). cap=0 is the full-hierarchy method; cap=inf is unrestricted relaxation.
Run: .venv/bin/python -W ignore prototypes/relax_tradeoff.py
"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, general_method as gm
CAPS = [0., .01, .02, .05, .10, .20, .50, np.inf]
rows = []
for make in (gm.era5, gm.ring, gm.gaussians):
    ds = make()
    for cap in CAPS:
        r = rh.run(ds, cap, make_figure=False); R = r['results']['R_relaxed']
        rows.append(dict(dataset=ds['name'], cap=cap, frames_relaxed=r['frames_relaxed'], ref_err_mean=R['ref_err_mean'],
                         ref_err_p95=R['ref_err_p95'], ref_err_max=R['ref_err_max'], frames_err_over_theta=R['frames_err_over_theta'],
                         pairs_changed_frac=R['pairs_merge_changed'] / R['pairs'], merge_err_max=R['merge_err_max'],
                         merge_err_mean_changed=R['merge_err_mean_changed'], field_range=r['field_range'],
                         topology_exact_frames=R['topology_exact_frames'], frames=r['frames']))
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
(rh.OUT / 'relax_tradeoff.json').write_text(json.dumps(rows, indent=1, default=float))
plt = rh.plt
fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), layout='constrained')
for ax, name in zip(axs, ['era5', 'ring', 'gaussians']):
    R = [r for r in rows if r['dataset'] == name]
    x = [r['merge_err_max'] / r['field_range'] * 100 for r in R]; y = [r['ref_err_mean'] for r in R]
    ax.plot(x, y, 'o-', color='#0072b2')
    for r, xx, yy in zip(R, x, y):
        ax.annotate('cap ' + ('∞' if r['cap'] == np.inf else f"{r['cap']:.0%}"), (xx, yy), fontsize=7, xytext=(4, 3), textcoords='offset points')
    ax.set(title=name, xlabel='max merge-level change (% of value range)', ylabel='mean position error |u−q|')
fig.suptitle('Position fidelity vs topology fidelity under certificate-driven local relaxation', fontsize=11)
fig.savefig(rh.OUT / 'relax_tradeoff.png', dpi=150)
