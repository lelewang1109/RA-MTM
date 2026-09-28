"""Figures and statistics for the paper draft that are not produced by other prototypes.

Outputs (prototypes/output/):
  paper_stats.json            dataset statistics for Table 1
  fig_conflict_timeline.png   per-frame space cost tau_free and hierarchy cost H (RQ1)
  fig_toy_conflict.png        three-leaf conflict example (Section 4)
Run: .venv/bin/python -W ignore prototypes/paper_figs.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, relax_hierarchy as rh, task_reference as tr
from ramtm.error_budget import leaf_orders

OUT = tr.OUT; plt = tr.plt
relax = json.loads((OUT / 'relax_metrics.json').read_text())

stats = {}
fig, axs = plt.subplots(3, 1, figsize=(10, 6.4), layout='constrained')
for ax, (make, name) in zip(axs, [(gm.era5, 'era5'), (gm.ring, 'ring'), (gm.gaussians, 'gaussians')]):
    ds = make(); sc = ds['sc']; r = relax[name]; log = r['frame_log']
    theta = r['theta']; L = r['canvas']
    H = np.array([d['tau_hier'] - d['tau_free'] for d in log]); F = np.array([d['tau_free'] for d in log])
    n_orders = [len(leaf_orders(h)) for h in sc['hier']]
    stats[name] = dict(frames=len(log), leaves_min=int(min(map(len, sc['ids']))), leaves_max=int(max(map(len, sc['ids']))),
                       legal_orders_max=int(max(n_orders)), legal_orders_median=float(np.median(n_orders)),
                       tracks=int(len(set(k for fr in sc['tracks'] for k in fr))), axis_length=L, theta=theta,
                       conflict_frames=int(np.sum(H > theta)), conflict_share=float(np.mean(H > theta)),
                       H_max=float(H.max()), H_max_share_of_axis=float(H.max() / L),
                       H_median_in_conflict=float(np.median(H[H > theta])) if np.any(H > theta) else 0.,
                       space_cost_max=float(F.max()), space_cost_frames_over_theta=int(np.sum(F > theta)),
                       tau_free_exact_frames=int(sum(n <= 6 for n in map(len, sc['ids']))),
                       field_range=r['field_range'], reference=r['reference'])
    t = np.arange(len(log))
    ax.bar(t, F / L * 100, color='#999999', width=.9, label='space cost τ_free')
    ax.bar(t, H / L * 100, bottom=F / L * 100, color='#d55e00', width=.9, label='hierarchy cost H = τ* − τ_free')
    ax.axhline(theta / L * 100, color='k', ls=':', lw=.9, label='θ (2% of axis)')
    ax.set(ylabel='% of axis', title=f"{name}: {stats[name]['conflict_frames']}/{len(log)} frames with H > θ")
    if name == 'era5': ax.legend(loc='upper right', fontsize=8, ncol=3)
axs[-1].set_xlabel('time step')
fig.savefig(OUT / 'fig_conflict_timeline.png', dpi=170); plt.close(fig)

# three-leaf example: tree ((A,B),C), references qA < qC < qB
fig, axs = plt.subplots(1, 3, figsize=(11, 2.8), layout='constrained')
q = dict(A=20, C=50, B=80); col = dict(A='#0072b2', B='#56b4e9', C='#d55e00')
def draw(ax, pos, title, err=None):
    ax.set_xlim(0, 100); ax.set_ylim(-1.2, 1.6); ax.axhline(0, color='k', lw=.6)
    for k, x in q.items():
        ax.plot([x, x], [0, .9], ':', color=col[k]); ax.text(x, 1.0, f'q_{k}', ha='center', color=col[k], fontsize=9)
    for k, x in pos.items():
        ax.add_patch(plt.Rectangle((x - 6, -.25), 12, .5, color=col[k], alpha=.8)); ax.text(x, -.7, k, ha='center', fontsize=10)
    ax.set_title(title, fontsize=9.5); ax.set_yticks([]); ax.set_xlabel('reference coordinate')
draw(axs[0], dict(A=20, C=50, B=80), 'reference order A–C–B\n(violates subtree {A,B})')
draw(axs[1], dict(A=20, B=35, C=50), 'legal order A–B–C: B moved by 45')
draw(axs[2], dict(A=20, B=59, C=71), 'optimal legal layout: max error = τ* = 21\n= (q_B − q_C + w)/2, split between B and C')
fig.savefig(OUT / 'fig_toy_conflict.png', dpi=170); plt.close(fig)

(OUT / 'paper_stats.json').write_text(json.dumps(stats, indent=1))
print(json.dumps(stats, indent=1))
