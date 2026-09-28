"""Three-leaf conflict (Fig. 3) at column width: tree ((A,B),C), references q_A < q_C < q_B, equal widths, g = rho = 0.
Output: prototypes/output/fig_toy_conflict.png (+ .pdf).  Run: .venv/bin/python -W ignore prototypes/fig_toy.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr, figstyle as fs

OUT = tr.OUT; plt = tr.plt
fs.apply()
q = dict(A=20, C=50, B=80); col = dict(A='#0072b2', B='#56b4e9', C='#d55e00')
fig, axs = plt.subplots(3, 1, figsize=(fs.COL_W, 2.5), layout='constrained', sharex=True)
def draw(ax, pos, title):
    ax.set_xlim(0, 100); ax.set_ylim(-.8, 1.6); ax.axhline(0, color='k', lw=.5)
    for k, x in q.items():
        ax.plot([x, x], [0, .75], ':', color=col[k], lw=.8); ax.text(x, .82, f'$q_{k}$', ha='center', color=col[k], fontsize=6.5)
    for k, x in pos.items():
        ax.add_patch(plt.Rectangle((x - 6, -.22), 12, .44, color=col[k], alpha=.85)); ax.text(x, -.72, k, ha='center', fontsize=6.5)
    ax.set_yticks([]); ax.text(100, 1.25, title, fontsize=6.5, ha='right', va='bottom')
    for sp in ['left', 'top', 'right']: ax.spines[sp].set_visible(False)
draw(axs[0], dict(A=20, C=50, B=80), 'reference order: splits {A,B}')
draw(axs[1], dict(A=20, B=35, C=50), 'legal, poor: B moved by 45')
draw(axs[2], dict(A=20, B=59, C=71), 'optimal legal: $\\tau^*=21$')
axs[-1].set_xlabel('reference coordinate')
fig.savefig(OUT / 'fig_toy_conflict.png', dpi=300); fig.savefig(OUT / 'fig_toy_conflict.pdf'); plt.close(fig)
