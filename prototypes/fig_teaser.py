"""Teaser: the same ERA5 winter as (a) ST-MTM, (b) reference-anchored layout keeping the merge tree, with the
per-frame certificate strip, and (c) certificate-driven relaxation rendered with the optimal barrier filling,
with the per-frame topological cost strip.
Output: prototypes/output/fig_teaser.png (+ .pdf)
Run: .venv/bin/python -W ignore prototypes/fig_teaser.py
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, replicate as rp, task_reference as tr, filling as fl, pointcert as pc, misreading as mr
from experiments import era5 as ep

OUT = tr.OUT; plt = tr.plt
KAPPA = .2


def tracks(ax, sc, U, color='white'):
    T = len(U)
    for k in sorted(set(k for fr in sc['tracks'] for k in fr)):
        tt = [t for t in range(T) if k in sc['tracks'][t]]
        if len(tt) < 3: continue
        ax.plot(tt, [U[t][sc['tracks'][t].index(k)] for t in tt], '-', color=color, lw=.7)


def main():
    ds = rp.LOADERS['era5'](); sc = ds['sc']; kind = sc['trees'][0].kind; T = len(sc['ids'])
    lo, hi = np.quantile(sc['fields'], [0, 1])
    base = rh.run(ds, 0., make_figure=False, return_internal=True); I0 = base['_internal']; p = I0['p']; ref = I0['ref']
    L = p.canvas; theta = base['theta']
    R = rh.run(ds, KAPPA, make_figure=False, return_internal=True)
    rowsA = I0['results']['A_full_hierarchy']['_rows']; mapsA = I0['results']['A_full_hierarchy']['_maps']
    rowsR = R['_internal']['results']['R_relaxed']['_rows']
    mapsR, dskR, _ = rh.render(sc, rowsR, p, ds['nominal'])
    optR = mapsR.astype(float).copy(); dstar = []
    for t, (fr, sk) in enumerate(zip(sc['frames'], dskR)):
        optR[:, t], d = fl.optimal_fill(mapsR[:, t], list(sk.ordering), sk.anchors, fr, kind); dstar.append(d)
    # ST-MTM in its own model
    span = ds['native_span']
    px = rh.gm.Parameters(canvas=span, canvas_origin=float(min(ds['lo'][0], 0.)), width_scale=.5 * span / ds['domain_area'],
                          gap=span / 240, extra_budget=span / 120, rho=.5)
    st = ep.run_method(sc, 'ST-MTM', px, canvas=span, length=ds['nominal'], refine_raster=False, strict_checks=False)
    Ust = [np.asarray(r['pixel_x'], float) for r in st['rows']]
    cert_pt = []; st_pt = []
    for t in range(T):
        q = np.asarray(ref['qs'][t])
        cert_pt.append(float(pc.tau_pt(rh.leaf_orders(sc['hier'][t]), q).min()))
        st_pt.append(float(pc.tau_pt([np.argsort(Ust[t], kind='stable')], q)[0]))
    log = base['frame_log']
    H = np.array([d['tau_hier'] - d['tau_free'] for d in log]); F = np.array([d['tau_free'] for d in log])
    errR = np.array([np.max(abs(r['x'] - r['reference'])) for r in rowsR])

    fig = plt.figure(figsize=(13, 3.9))
    plt.rcParams['axes.titlesize'] = 9
    g = fig.add_gridspec(2, 3, height_ratios=[1, 2.6], hspace=.08, wspace=.12, left=.045, right=.965, top=.9, bottom=.12)
    t = np.arange(T)
    # (a)
    ax = fig.add_subplot(g[1, 0]); ext = [min(u.min() for u in Ust), max(u.max() for u in Ust)]
    ax.imshow(st['maps'], origin='lower', aspect='auto', extent=[-.5, T - .5, ext[0], ext[1]], vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, Ust); ax.set(xlabel='time step', yticks=[]); ax.set_ylabel('1-D position')
    top = fig.add_subplot(g[0, 0], sharex=ax)
    top.bar(t, np.array(cert_pt) / L * 100, color='#555555', width=.9, label='unavoidable (width-free certificate)')
    top.bar(t, (np.array(st_pt) - np.array(cert_pt)) / L * 100, bottom=np.array(cert_pt) / L * 100, color='#bbbbbb', width=.9, label='avoidable')
    top.set(title='(a) ST-MTM: order vs. reference', ylabel='% axis'); top.tick_params(labelbottom=False)
    top.legend(fontsize=6.5, loc='upper left', ncol=2, framealpha=.7)
    # (b)
    ax = fig.add_subplot(g[1, 1]); ax.imshow(mapsA, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + L],
                                             vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, [r['x'] for r in rowsA]); ax.set(xlabel='time step', yticks=[])
    top = fig.add_subplot(g[0, 1], sharex=ax, sharey=fig.axes[1])
    top.bar(t, F / L * 100, color='#999999', width=.9, label='space cost')
    top.bar(t, H / L * 100, bottom=F / L * 100, color='#d55e00', width=.9, label='hierarchy cost H')
    top.axhline(theta / L * 100, color='k', ls=':', lw=.8)
    top.set(title='(b) Anchored, merge tree kept: certificate τ*'); top.tick_params(labelbottom=False, labelleft=False)
    top.legend(fontsize=6.5, loc='upper left', ncol=2, framealpha=.7)
    # (c)
    ax = fig.add_subplot(g[1, 2]); ax.imshow(optR, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + L],
                                             vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, [r['x'] for r in rowsR]); ax.set(xlabel='time step', yticks=[])
    top = fig.add_subplot(g[0, 2], sharex=ax, sharey=fig.axes[1])
    top.bar(t, errR / L * 100, color='#009e73', width=.9, label='max position error')
    top.set(title=f'(c) Relaxed (κ = {int(KAPPA*100)}%), optimal filling'); top.tick_params(labelbottom=False, labelleft=False)
    tw = top.twinx(); dd = np.array(dstar); m = dd > 1e-9
    tw.plot(t[m], dd[m], 'o', color='#0072b2', ms=2.2, label='topological cost δ* (hPa, right)')
    tw.set_ylabel('hPa', color='#0072b2', fontsize=8); tw.tick_params(labelsize=7, colors='#0072b2')
    h1, l1 = top.get_legend_handles_labels(); h2, l2 = tw.get_legend_handles_labels()
    top.legend(h1 + h2, l1 + l2, fontsize=6.5, loc='upper left', ncol=2, framealpha=.7)
    for a in fig.axes: a.tick_params(labelsize=7)
    fig.savefig(OUT / 'fig_teaser.png', dpi=220); fig.savefig(OUT / 'fig_teaser.pdf'); plt.close(fig)
    print('mean max error A %.3f R %.3f of axis; mean delta* %.2f hPa, max %.2f' %
          (np.mean([np.max(abs(r['x'] - r['reference'])) for r in rowsA]) / L, errR.mean() / L, np.mean(dstar), np.max(dstar)))


if __name__ == '__main__':
    main()
