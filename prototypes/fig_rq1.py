"""RQ1 figure: per-time-step space cost and hierarchy cost on the three real datasets (from replicate_*.json).
Output: prototypes/output/fig_rq1.png (+ .pdf).  Run: .venv/bin/python -W ignore prototypes/fig_rq1.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr

OUT = tr.OUT; plt = tr.plt
NAMES = [('era5', 'ERA5 1999/2000'), ('era5_2014', 'ERA5 2013/14'), ('wildfire', 'Wildfire 2019')]
plt.rcParams.update({'axes.titlesize': 8.5, 'font.size': 7.5})
fig, axs = plt.subplots(1, 3, figsize=(12, 2.1), layout='constrained', gridspec_kw=dict(width_ratios=[118, 124, 75]))
for ax, (n, label) in zip(axs, NAMES):
    c = json.loads((OUT / f'replicate_{n}.json').read_text())['certificate']
    H = np.array(c['H_per_frame']) * 100; F = np.array(c['F_per_frame']) * 100; t = np.arange(len(H))
    ax.bar(t, F, color='#999999', width=.9, label='space cost $\\tau_{\\rm free}$')
    ax.bar(t, H, bottom=F, color='#d55e00', width=.9, label='hierarchy cost $H$')
    ax.axhline(2, color='k', ls=':', lw=.8, label='$\\theta$ = 2%')
    ax.set(title=f"{label}: {c['conflict_frames']}/{c['frames']} steps with $H>\\theta$", xlabel='time step', xlim=(-1, len(H)))
axs[0].set_ylabel('% of axis'); axs[0].legend(fontsize=6.5, loc='upper left', framealpha=.8)
fig.savefig(OUT / 'fig_rq1.png', dpi=220); fig.savefig(OUT / 'fig_rq1.pdf'); plt.close(fig)
