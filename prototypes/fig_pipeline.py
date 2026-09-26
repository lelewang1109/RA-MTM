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
        ax.plot(q[i], 1, 'v', color=cols[i], ms=5)
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

    plt.rcParams.update({'axes.titlesize': 8, 'font.size': 7})
    fig, axs = plt.subplots(1, 6, figsize=(14, 3.0), gridspec_kw=dict(width_ratios=[1, 1.05, 1.25, 1.05, 1.25, 1.15], wspace=.4,
                                                                       left=.01, right=.995, top=.74, bottom=.12))
    # (1) field
    ax = axs[0]; C = np.asarray(sc['coords']); lo, hi = C.min(0), C.max(0)
    ax.imshow(sc['fields'][t], origin='lower', extent=[lo[0], hi[0], lo[1], hi[1]], cmap='magma')
    P = np.array([fr.coordinates[k] for k in ids])
    for i in range(n): ax.plot(P[i, 0], P[i, 1], 'o', color=cl[i], ms=5, mec='w', mew=.7)
    a = np.asarray(ref['candidates']['direction']['a']); c0 = (lo + hi) / 2; s = .38 * (hi - lo).min()
    ax.annotate('', c0 + s * a, c0 - s * a, arrowprops=dict(arrowstyle='->', color='w', lw=1.4))
    ax.set(title='① field, extrema,\nauto reference direction', xticks=[], yticks=[])
    # (2) merge tree, legal order of layout A
    ax = axs[1]; oA = list(rowA['order'])
    draw_tree(ax, fr, {ids[i]: k for k, i in enumerate(oA)})
    for k, i in enumerate(oA): ax.plot(k, fr.values[ids[i]], 'o', color=cl[i], ms=5, mec='k', mew=.4)
    ax.set(title='② merge tree $T_t$\n(join tree of minima)', xticks=[]); ax.text(0, 1.01, 'hPa', transform=ax.transAxes, fontsize=6.5)
    # (3) certificate
    ax = axs[2]; layout_row(ax, rowA, q, 0, cl, L, p.canvas_origin)
    ax.set(title=f'③ certificate: τ* = {lg0["tau_hier"]/L:.0%}, τ_free = {lg0["tau_free"]/L:.1%}\nhierarchy cost H = {(lg0["tau_hier"]-lg0["tau_free"])/L:.0%} > θ = 2%', xticks=[])
    # (4) relaxation
    ax = axs[3]; oR = list(rowR['order'])
    draw_tree(ax, fr, {ids[i]: k for k, i in enumerate(oR)}, flat=set(flat))
    for k, i in enumerate(oR): ax.plot(k, fr.values[ids[i]], 'o', color=cl[i], ms=5, mec='k', mew=.4)
    ax.set(title=f'④ relax: flatten weak merges\n(κ = {int(KAPPA*100)}%: {len(flat)} node{"s" if len(flat) > 1 else ""}, dashed)', xticks=[])
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
    ax.set_ylim(-.34, 1.08); ax.set_yticks([]); ax.set_xticks([]); ax.legend(fontsize=6, loc='upper left', framealpha=.7)
    ax.set(title=f'⑤ layout + optimal filling: max error {np.max(abs(rowR["x"]-q))/L:.1%},\ntopological cost δ* = {dst[t]:.1f} hPa (LCA filling: {me_lca:.1f})')
    # (6) map excerpt with strips
    ax = axs[5]; w0, w1 = max(0, t - 18), min(len(rowsR), t + 4)
    ax.imshow(opt[:, w0:w1], origin='lower', aspect='auto', extent=[w0 - .5, w1 - .5, p.canvas_origin, p.canvas_origin + L], cmap='magma',
              vmin=np.min(sc['fields']), vmax=np.max(sc['fields']))
    ax.axvline(t, color='w', lw=.8, ls=':')
    top = ax.inset_axes([0, 1.02, 1, .22]); tt_ = np.arange(w0, w1)
    top.bar(tt_, [np.max(abs(r['x'] - r['reference'])) / L * 100 for r in rowsR[w0:w1]], color='#009e73', width=.8)
    tw = top.twinx(); dd = np.array(dst[w0:w1]); m = dd > 1e-9; tw.plot(tt_[m], dd[m], 'o', color='#0072b2', ms=2); tw.set_yticks([])
    top.set_xlim(w0 - .5, w1 - .5); top.set_xticks([]); top.set_yticks([])
    ax.set_yticks([]); ax.set_xlabel('time step'); top.set_title('⑥ map with per-frame strips\n(max error, δ*)')
    for a_, b_ in zip(axs[:-1], axs[1:]):
        fig.add_artist(FancyArrowPatch((a_.get_position().x1 + .002, .47), (b_.get_position().x0 - (.03 if b_ in (axs[1], axs[3]) else .003), .47), transform=fig.transFigure,
                                       arrowstyle='-|>', mutation_scale=9, color='#555555'))
    fig.savefig(OUT / 'fig_pipeline.png', dpi=220); fig.savefig(OUT / 'fig_pipeline.pdf'); plt.close(fig)
    print('t', t, 'n', n, 'H', (lg0['tau_hier'] - lg0['tau_free']) / L, 'flattened', flat, 'delta*', dst[t])


if __name__ == '__main__':
    main()
