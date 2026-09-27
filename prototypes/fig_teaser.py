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
ROOT_NC = Path(__file__).resolve().parents[1] / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc'
COAST = Path(__file__).resolve().parents[1] / 'data/geo/ne_110m_coastline.geojson'


def tracks(ax, sc, U, color='white'):
    T = len(U)
    for k in sorted(set(k for fr in sc['tracks'] for k in fr)):
        tt = [t for t in range(T) if k in sc['tracks'][t]]
        if len(tt) < 3: continue
        ax.plot(tt, [U[t][sc['tracks'][t].index(k)] for t in tt], '-', color=color, lw=.45)


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

    import figstyle as fs; fs.apply()
    fig = plt.figure(figsize=(fs.TEXT_W, 4.1))
    gout = fig.add_gridspec(2, 1, height_ratios=[3.35, 1.45], hspace=.17, left=.05, right=.995, top=.95, bottom=.015)
    g = gout[0].subgridspec(3, 3, height_ratios=[.5, .5, 2.4], hspace=.12, wspace=.08)
    t = np.arange(T); ymax = max(np.max(st_pt), np.max(H + F)) / L * 105
    def strip(gs, **kw):
        a = fig.add_subplot(gs, **kw); a.tick_params(labelbottom=False); a.set_xlim(-.5, T - .5); return a
    # (a)
    ax = fig.add_subplot(g[2, 0]); ext = [min(u.min() for u in Ust), max(u.max() for u in Ust)]
    ax.imshow(st['maps'], origin='lower', aspect='auto', extent=[-.5, T - .5, ext[0], ext[1]], vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, Ust); ax.set(xlabel='time step', yticks=[]); ax.set_ylabel(f'position along {ref["label"].split()[-1]}')
    top = strip(g[0:2, 0])
    top.bar(t, np.array(cert_pt) / L * 100, color='#555555', width=.9, label='unavoidable')
    top.bar(t, (np.array(st_pt) - np.array(cert_pt)) / L * 100, bottom=np.array(cert_pt) / L * 100, color='#bbbbbb', width=.9, label='avoidable')
    top.set(title='(a) ST-MTM: deviation of its order', ylabel='% axis', ylim=(0, ymax))
    top.legend(loc='upper left', ncol=2, framealpha=.7, handlelength=1)
    # (b)
    ax = fig.add_subplot(g[2, 1]); ax.imshow(mapsA, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + L],
                                             vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, [r['x'] for r in rowsA]); ax.set(xlabel='time step', yticks=[])
    top = strip(g[0:2, 1]); top.set_ylim(0, ymax); top.tick_params(labelleft=False)
    top.bar(t, F / L * 100, color='#999999', width=.9, label='space cost')
    top.bar(t, H / L * 100, bottom=F / L * 100, color='#d55e00', width=.9, label='hierarchy cost $H$')
    top.axhline(theta / L * 100, color='k', ls=':', lw=.6)
    top.set(title='(b) Merge tree kept: certificate $\\tau^*$'); top.legend(loc='upper left', ncol=2, framealpha=.7, handlelength=1)
    # (c)
    ax = fig.add_subplot(g[2, 2]); ax.imshow(optR, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + L],
                                             vmin=lo, vmax=hi, cmap='magma')
    tracks(ax, sc, [r['x'] for r in rowsR]); ax.set(xlabel='time step', yticks=[])
    top = strip(g[0, 2]); top.bar(t, errR / L * 100, color='#009e73', width=.9); top.set_ylim(0, ymax / 2)
    top.set_title(f'(c) Relaxed ($\\kappa$ = {int(KAPPA*100)}%), optimal filling'); top.tick_params(labelleft=False)
    top.text(.99, .9, 'max position error', transform=top.transAxes, ha='right', va='top', fontsize=6.5, color='#009e73')
    bot = strip(g[1, 2]); bot.bar(t, dstar, color='#0072b2', width=.9); bot.tick_params(labelleft=False)
    bot.text(.99, .9, f'topological cost $\\delta^*$ (max {max(dstar):.0f} hPa)', transform=bot.transAxes, ha='right', va='top', fontsize=6.5, color='#0072b2')
    # geographic snapshots (bottom row), linked to time steps in all three maps
    import geo, matplotlib.patheffects as pe
    G = geo.Era5Geo(sc.get('window', ROOT_NC), sc['coords'])
    SN = [5, 26, 48, 62, 108]
    maps_axes = [a for a in fig.axes if a.images and a.get_xlabel() == 'time step']
    for a in maps_axes:
        for k, tt_ in enumerate(SN):
            a.axvline(tt_, color='w', lw=.6, ls=':')
            a.text(tt_, a.get_ylim()[1], f'{k + 1}', color='w', fontsize=6, ha='center', va='top', fontweight='bold',
                   path_effects=[pe.withStroke(linewidth=1.2, foreground='k')])
    for a in maps_axes: a.set_xlabel('')
    sub = gout[1].subgridspec(1, len(SN), wspace=.05)
    for k, tt_ in enumerate(SN):
        a = fig.add_subplot(sub[k]); a.imshow(sc.get('fields_smooth', sc['fields'])[tt_], origin='lower', extent=G.extent, cmap='magma', vmin=lo, vmax=hi)
        G.graticule(a); G.coastlines(a, COAST)
        P_ = np.array([sc['frames'][tt_].coordinates[i] for i in sc['ids'][tt_]])
        a.plot(P_[:, 0], P_[:, 1], 'o', mfc='none', mec='w', mew=.8, ms=4)
        if k == 0:
            dvec = np.asarray(ref['candidates']['direction']['a']); c0 = np.array([np.mean(G.extent[:2]), np.mean(G.extent[2:])])
            a.annotate('', c0 + 25 * dvec, c0 - 25 * dvec, arrowprops=dict(arrowstyle='->', color='#56b4e9', lw=1.2))
        a.set(xlim=G.extent[:2], ylim=G.extent[2:], xticks=[], yticks=[], aspect='equal')
        a.set_title(f'{k + 1}: {sc["dates"][tt_][5:13]}h, $H$ = {H[tt_] / L:.0%}', fontsize=6.5, pad=2)
    fig.savefig(OUT / 'fig_teaser.png', dpi=300); fig.savefig(OUT / 'fig_teaser.pdf'); plt.close(fig)
    print('mean max error A %.3f R %.3f of axis; mean delta* %.2f hPa, max %.2f' %
          (np.mean([np.max(abs(r['x'] - r['reference'])) for r in rowsA]) / L, errR.mean() / L, np.mean(dstar), np.max(dstar)))


if __name__ == '__main__':
    main()
