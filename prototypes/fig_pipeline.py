"""Pipeline figure (Fig. 2): one ERA5 time step through the method.

(1) field, extrema, automatic reference direction; (2) merge tree; (3) certificate: best merge-tree-preserving
layout vs. references (tau*, tau_free, H); (4) relaxation: flatten weak merges (crossing edges = broken
contiguity); (5) relaxed layout rendered with the optimal barrier filling (vs. LCA filling); (6) resulting map
with per-frame strips.
Output: prototypes/output/fig_pipeline.png (+ .pdf)
Run: .venv/bin/python -W ignore prototypes/fig_pipeline.py [t]
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, replicate as rp, task_reference as tr, filling as fl, theory as th
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = tr.OUT; plt = tr.plt
KAPPA = .2
T0 = int(sys.argv[1]) if len(sys.argv) > 1 else 114
COL = ['#0072b2', '#d55e00', '#009e73', '#cc79a7', '#e69f00', '#56b4e9', '#999999', '#f0e442']


def branch_nodes(fr, k):
    """Skip unary chains: return the next branching node or leaf below k."""
    while len(fr.children[k]) == 1: k = fr.children[k][0]
    return k


def draw_tree(ax, fr, xpos, flat=(), lw=1.2):
    """Elbow dendrogram with y = merge value; internal x = mean of leaf x; flattened nodes dashed red."""
    def rec(k):
        k = branch_nodes(fr, k)
        ch = fr.children[k]
        if not ch: return xpos[k], [xpos[k]]
        xs = []; pts = []
        for c in ch:
            cx, lx = rec(c); c2 = branch_nodes(fr, c); pts.append((cx, float(fr.values[c2]))); xs += lx
        x = float(np.mean(xs)); y = float(fr.values[k]); style = dict(color='#c0392b', ls='--') if k in flat else dict(color='k')
        for cx, cy in pts: ax.plot([cx, cx], [cy, y], color='k', lw=lw)
        ax.plot([min(p[0] for p in pts), max(p[0] for p in pts)], [y, y], lw=lw, **style)
        if k in flat: ax.text(x, y, ' γ', color='#c0392b', fontsize=7, va='bottom')
        return x, xs
    rec(fr.root)


def layout_row(ax, row, q, y, cols, L, origin):
    for i in range(len(q)):
        z, w, u = row['z'][i], row['w'][i], row['x'][i]
        ax.add_patch(Rectangle((z - w / 2, y - .12), w, .24, color=cols[i], alpha=.55, lw=0))
        ax.plot(u, y, 'o', color=cols[i], ms=3.5, mec='k', mew=.4)
        ax.plot([u, q[i]], [y + .12, 1 - .05], color=cols[i], lw=.8)
        ax.plot(q[i], 1, 'v', color=cols[i], ms=4)
    ax.plot([origin, origin + L], [1, 1], color='k', lw=.6); ax.plot([origin, origin + L], [y, y], color='#bbbbbb', lw=.4)
    ax.set_xlim(origin - .02 * L, origin + 1.02 * L); ax.set_ylim(-.35, 1.35); ax.set_yticks([])
    ax.text(origin, 1.12, 'reference q', fontsize=6.5); ax.text(origin, y - .32, '1-D layout', fontsize=6.5)


def main():
    ds = rp.LOADERS['era5'](); sc = ds['sc']; kind = sc['trees'][0].kind
    base = rh.run(ds, 0., make_figure=False, return_internal=True); I0 = base['_internal']; p = I0['p']; ref = I0['ref']; L = p.canvas
    R = rh.run(ds, KAPPA, make_figure=False, return_internal=True); IR = R['_internal']
    t = T0; fr = sc['frames'][t]; ids = sc['ids'][t]; q = np.asarray(ref['qs'][t]); n = len(ids)
    lg0 = base['frame_log'][t]; lgR = R['frame_log'][t]
    rowA = I0['results']['A_full_hierarchy']['_rows'][t]; rowR = IR['results']['R_relaxed']['_rows'][t]
    cols = {i: COL[r] for r, i in enumerate(np.argsort(q))}                           # colour by reference rank
    cl = [cols[i] for i in range(n)]
    flat = [s['node'] for s in lgR['steps']]
    rowsR = IR['results']['R_relaxed']['_rows']
    maps, dsk, npx = rh.render(sc, rowsR, p, ds['nominal'])
    opt = maps.astype(float).copy(); dst = []
    for tt, (f_, sk) in enumerate(zip(sc['frames'], dsk)):
        opt[:, tt], d = fl.optimal_fill(maps[:, tt], list(sk.ordering), sk.anchors, f_, kind); dst.append(d)

    import figstyle as fs; fs.apply()
    fig = plt.figure(figsize=(fs.TEXT_W, 3.1))
    gg = fig.add_gridspec(2, 3, wspace=.3, hspace=.62, left=.06, right=.995, top=.9, bottom=.1)
    axs = [fig.add_subplot(gg[i // 3, i % 3]) for i in range(6)]
    # (1) field
    ax = axs[0]; C = np.asarray(sc['coords']); lo, hi = C.min(0), C.max(0)
    import geo; G = geo.Era5Geo(sc['window'], C) if 'window' in sc else None
    ax.imshow(sc.get('fields_smooth', sc['fields'])[t], origin='lower', extent=G.extent if G else [lo[0], hi[0], lo[1], hi[1]], cmap='magma')
    if G: G.graticule(ax); G.coastlines(ax, Path(__file__).resolve().parents[1] / 'data/geo/ne_110m_coastline.geojson'); ax.set(xlim=G.extent[:2], ylim=G.extent[2:])
    P = np.array([fr.coordinates[k] for k in ids])
    for i in range(n): ax.plot(P[i, 0], P[i, 1], 'o', color=cl[i], ms=4, mec='w', mew=.5)
    a = np.asarray(ref['candidates']['direction']['a']); c0 = (lo + hi) / 2; s = .38 * (hi - lo).min()
    ax.annotate('', c0 + s * a, c0 - s * a, arrowprops=dict(arrowstyle='->', color='w', lw=1.4))
    ax.set(title='① field, extrema, reference direction', xticks=[], yticks=[])
    # (2) merge tree, legal order of layout A
    ax = axs[1]; oA = list(rowA['order'])
    draw_tree(ax, fr, {ids[i]: k for k, i in enumerate(oA)})
    for k, i in enumerate(oA): ax.plot(k, fr.values[ids[i]], 'o', color=cl[i], ms=3.5, mec='k', mew=.3)
    ax.set(title='② merge tree $T_t$ (join tree, hPa)', xticks=[])
    # (3) certificate
    ax = axs[2]; layout_row(ax, rowA, q, 0, cl, L, p.canvas_origin)
    ax.set(title=f'③ certificate $\\tau^*$ = {lg0["tau_hier"]/L:.0%}, $\\tau_{{free}}$ = {lg0["tau_free"]/L:.0%}', xticks=[])
    # (4) relaxation
    ax = axs[3]; oR = list(rowR['order'])
    draw_tree(ax, fr, {ids[i]: k for k, i in enumerate(oR)}, flat=set(flat))
    for k, i in enumerate(oR): ax.plot(k, fr.values[ids[i]], 'o', color=cl[i], ms=3.5, mec='k', mew=.3)
    ax.set(title=f'④ relax: flatten {len(flat)} weak merge (dashed)', xticks=[])
    # (5) relaxed layout + optimal filling
    me_lca = float(rh.merge_errors(sc, maps, dsk, kind)[t].max())
    ax = axs[4]; y = np.linspace(p.canvas_origin, p.canvas_origin + L, maps.shape[0], endpoint=False) + L / maps.shape[0] / 2
    v = maps[:, t].astype(float); vo = opt[:, t]; vmin, vmax = v.min(), v.max()
    ax.plot(y, (v - vmin) / (vmax - vmin), color='#999999', lw=.8, ls='--', label='LCA filling')
    ax.plot(y, (vo - vmin) / (vmax - vmin), color='#0072b2', lw=1.0, label='optimal filling')
    for i in range(n):
        z, w, u = rowR['z'][i], rowR['w'][i], rowR['x'][i]
        ax.add_patch(Rectangle((z - w / 2, -.28), w, .12, color=cl[i], alpha=.55, lw=0)); ax.plot(u, -.22, 'o', color=cl[i], ms=3.5, mec='k', mew=.4)
        ax.plot(q[i], -.02, 'v', color=cl[i], ms=4)
    ax.set_ylim(-.34, 1.08); ax.set_yticks([]); ax.set_xticks([]); ax.legend(loc='upper left', framealpha=.7, handlelength=1.2)
    ax.set(title=f'⑤ error {np.max(abs(rowR["x"]-q))/L:.1%}; $\\delta^*$ = {dst[t]:.1f} hPa (LCA {me_lca:.1f})')
    # (6) map excerpt with strips
    ax = axs[5]; w0, w1 = max(0, t - 18), min(len(rowsR), t + 4)
    ax.imshow(opt[:, w0:w1], origin='lower', aspect='auto', extent=[w0 - .5, w1 - .5, p.canvas_origin, p.canvas_origin + L], cmap='magma',
              vmin=np.min(sc['fields']), vmax=np.max(sc['fields']))
    ax.axvline(t, color='w', lw=.8, ls=':')
    top = ax.inset_axes([0, 1.03, 1, .25]); tt_ = np.arange(w0, w1)
    top.bar(tt_, [np.max(abs(r['x'] - r['reference'])) / L * 100 for r in rowsR[w0:w1]], color='#009e73', width=.8)
    
    top.set_xlim(w0 - .5, w1 - .5); top.set_xticks([]); top.set_yticks([])
    ax.set_yticks([]); ax.set_xlabel('time step'); top.set_title('⑥ map with error strip')
    fig.savefig(OUT / 'fig_pipeline.png', dpi=300); fig.savefig(OUT / 'fig_pipeline.pdf'); plt.close(fig)
    print('t', t, 'n', n, 'H', (lg0['tau_hier'] - lg0['tau_free']) / L, 'flattened', flat, 'delta*', dst[t])


if __name__ == '__main__':
    main()
