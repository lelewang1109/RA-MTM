"""Witness figure: where the certificate comes from, and what relaxation changes, on an ERA5 excerpt.

(a) Merge-tree-preserving anchored map (A) with the certificate strip. In every conflict step the best witness
    triple (i, j in one subtree v, k outside, q_i < q_k < q_j) is drawn: a line joins u_i and u_j (same subtree),
    a ring marks u_k, whose reference lies between them but whose anchor cannot.
(b) Zoom on one step: references (top) vs. anchors (bottom) of the witness triple and the rest.
(c) Relaxed map (R, optimal filling) of the same excerpt with the topological-cost strip; relaxed steps marked.
Output: prototypes/output/fig_witness.png (+ .pdf).  Run: .venv/bin/python -W ignore prototypes/fig_witness.py
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, replicate as rp, task_reference as tr, filling as fl, theory as th

OUT = tr.OUT; plt = tr.plt
W0, W1, KAPPA = 38, 57, .2
TZ = 48
if len(sys.argv) == 4: W0, W1, TZ = map(int, sys.argv[1:4])   # run: fig_witness.py W0 W1 tz


def witness(fr, ids, q):
    s0 = rh.node_tree(fr, ids); nodes, _ = th.struct_nodes(s0); best, arg = 0., None
    for v, par, leaves in nodes:
        if par is None: continue
        S = set(leaves)
        for i in leaves:
            for j in leaves:
                if q[i] >= q[j]: continue
                for k in range(len(ids)):
                    if k in S or not q[i] < q[k] < q[j]: continue
                    b = min(q[k] - q[i], q[j] - q[k]) / 2
                    if b > best: best, arg = b, (i, j, k)
    return best, arg


def main():
    ds = rp.LOADERS['era5'](); sc = ds['sc']; kind = sc['trees'][0].kind
    base = rh.run(ds, 0., make_figure=False, return_internal=True); I0 = base['_internal']; p = I0['p']; ref = I0['ref']
    L = p.canvas; theta = base['theta']; lo, hi = np.quantile(sc['fields'], [0, 1])
    R = rh.run(ds, KAPPA, make_figure=False, return_internal=True); IR = R['_internal']
    rowsA = I0['results']['A_full_hierarchy']['_rows']; mapsA = I0['results']['A_full_hierarchy']['_maps']
    rowsR = IR['results']['R_relaxed']['_rows']; mapsR, dskR, _ = rh.render(sc, rowsR, p, ds['nominal'])
    optR = mapsR.astype(float).copy(); dst = []
    for t, (f_, sk) in enumerate(zip(sc['frames'], dskR)):
        optR[:, t], d = fl.optimal_fill(mapsR[:, t], list(sk.ordering), sk.anchors, f_, kind); dst.append(d)
    log = base['frame_log']; H = np.array([d['tau_hier'] - d['tau_free'] for d in log])
    W = {t: witness(sc['frames'][t], sc['ids'][t], np.asarray(ref['qs'][t])) for t in range(W0, W1) if H[t] > theta}
    tz = TZ   # conflict step whose witness triple lies in the domain interior (see prototypes/boundary.py)

    import figstyle as fs; fs.apply()
    fig = plt.figure(figsize=(fs.TEXT_W, 2.5))
    g = fig.add_gridspec(3, 4, height_ratios=[.5, .5, 2.2], width_ratios=[1.2, .85, .7, 1.2], hspace=.12, wspace=.12,
                         left=.035, right=.995, top=.9, bottom=.13)
    ext = [W0 - .5, W1 - .5, p.canvas_origin, p.canvas_origin + L]; tt = np.arange(W0, W1)
    # (a)
    ax = fig.add_subplot(g[2, 0]); ax.imshow(mapsA[:, W0:W1], origin='lower', aspect='auto', extent=ext, cmap='magma', vmin=lo, vmax=hi)
    for t, (b, (i, j, k)) in W.items():
        u = rowsA[t]['x']; ax.plot([t, t], [u[i], u[j]], color='#56b4e9', lw=1.6, alpha=.95, solid_capstyle='round')
        ax.plot(t, u[k], 'o', mfc='none', mec='#e69f00', mew=1.1, ms=4)
    ax.axvline(tz, color='w', ls=':', lw=.7); ax.set(xlabel='time step', yticks=[], ylabel='1-D position')
    top = fig.add_subplot(g[0:2, 0], sharex=ax)
    top.bar(tt, H[W0:W1] / L * 100, color='#d55e00', width=.85, label='hierarchy cost $H$')
    top.bar(tt, [W[t][0] / L * 100 if t in W else 0 for t in tt], color='#56b4e9', width=.4, label='witness bound')
    top.axhline(theta / L * 100, color='k', ls=':', lw=.6); top.tick_params(labelbottom=False); top.set_ylabel('% axis')
    top.legend(loc='upper left', ncol=2, framealpha=.8, handlelength=1)
    top.set_title('(a) merge tree kept: $H$ and witness triples'); top.set_ylim(0, 48)
    # (b) the 2-D field at the zoomed step with the witness triple and the reference direction
    import geo
    G = geo.Era5Geo(sc.get('window', Path(__file__).resolve().parents[1] / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc'), sc['coords'])
    ax = fig.add_subplot(g[:, 1]); ax.imshow(sc.get('fields_smooth', sc['fields'])[tz], origin='lower', extent=G.extent, cmap='magma', vmin=lo, vmax=hi)
    G.graticule(ax); G.coastlines(ax, Path(__file__).resolve().parents[1] / 'data/geo/ne_110m_coastline.geojson')
    b, (i, j, k) = W[tz]; ids = sc['ids'][tz]; Pw = np.array([sc['frames'][tz].coordinates[x] for x in ids])
    dvec = np.asarray(ref['candidates']['direction']['a']); c0 = np.array([np.mean(G.extent[:2]), np.mean(G.extent[2:])])
    ax.annotate('', c0 + 38 * dvec, c0 - 38 * dvec, arrowprops=dict(arrowstyle='->', color='w', lw=1))
    for m in range(len(ids)):
        c = '#56b4e9' if m in (i, j) else '#e69f00' if m == k else '#dddddd'
        foot = c0 + ((Pw[m] - c0) @ dvec) * dvec
        if m in (i, j, k): ax.plot([Pw[m, 0], foot[0]], [Pw[m, 1], foot[1]], ':', color=c, lw=.9)
        ax.plot(*Pw[m], 'o', color=c, ms=5 if m in (i, j, k) else 3.5, mec='k', mew=.4)
        if m in (i, j, k):
            ax.text(Pw[m, 0] + 2.5, Pw[m, 1] - 1, f'{float(sc["frames"][tz].values[ids[m]]):.0f}', color='w', fontsize=6, fontweight='bold')
    ax.set(xlim=G.extent[:2], ylim=G.extent[2:], xticks=[], yticks=[], aspect='equal')
    ax.set_xlabel(f'(b) step {tz}: pressure field (hPa)', fontsize=7.5)
    # (c)
    ax = fig.add_subplot(g[:, 2]); q = np.asarray(ref['qs'][tz]); u = rowsA[tz]['x']
    for m in range(len(q)):
        c = '#56b4e9' if m in (i, j) else '#e69f00' if m == k else '#aaaaaa'; lw = 1.3 if m in (i, j, k) else .6
        ax.plot([q[m], u[m]], [1, 0], color=c, lw=lw); ax.plot(q[m], 1, 'v', color=c, ms=4.5); ax.plot(u[m], 0, 'o', color=c, ms=4.5, mec='k', mew=.3)
    ax.plot([p.canvas_origin, p.canvas_origin + L], [1, 1], 'k', lw=.5); ax.plot([p.canvas_origin, p.canvas_origin + L], [0, 0], 'k', lw=.5)
    ax.text(p.canvas_origin, 1.08, 'reference $q$', fontsize=6.5); ax.text(p.canvas_origin, -.16, 'anchor $u$ (tree kept)', fontsize=6.5)
    ax.set_ylim(-.28, 1.22); ax.set_yticks([]); ax.set_xticks([])
    for sp in ['left', 'bottom']: ax.spines[sp].set_visible(False)
    ax.set_title(f'(c) witness {b/L:.0%}, $\\tau^*$ {log[tz]["tau_hier"]/L:.0%}')
    # (c)
    ax = fig.add_subplot(g[2, 3]); ax.imshow(optR[:, W0:W1], origin='lower', aspect='auto', extent=ext, cmap='magma', vmin=lo, vmax=hi)
    for t in range(W0, W1):
        if R['frame_log'][t]['relaxed_nodes']: ax.plot(t, p.canvas_origin + .975 * L, 'v', color='#009e73', ms=3)
    ax.axvline(tz, color='w', ls=':', lw=.7); ax.set(xlabel='time step', yticks=[])
    top = fig.add_subplot(g[0, 3], sharex=ax); top.set_ylim(0, 24)
    top.bar(tt, [np.max(abs(r['x'] - r['reference'])) / L * 100 for r in rowsR[W0:W1]], color='#009e73', width=.85)
    top.tick_params(labelbottom=False, labelleft=False); top.set_title(f'(d) relaxed ($\\kappa$ = {int(KAPPA*100)}%), optimal filling')
    top.text(.01, .95, 'max position error', transform=top.transAxes, ha='left', va='top', fontsize=6.5, color='#009e73')
    bot = fig.add_subplot(g[1, 3], sharex=ax); bot.bar(tt, dst[W0:W1], color='#0072b2', width=.85); bot.tick_params(labelbottom=False, labelleft=False)
    bot.text(.3, .95, f'$\\delta^*$ (max {max(dst[W0:W1]):.0f} hPa)', transform=bot.transAxes, ha='left', va='top', fontsize=6.5, color='#0072b2')
    from matplotlib.ticker import MaxNLocator
    for a_ in fig.axes: a_.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.axes[2].set_xticks([]); fig.axes[3].set_xticks([])
    fig.savefig(OUT / 'fig_witness.png', dpi=300); fig.savefig(OUT / 'fig_witness.pdf'); plt.close(fig)
    print('zoom step', tz, 'witness', b / L, 'tau*', log[tz]['tau_hier'] / L, 'H', H[tz] / L, 'triple', (i, j, k),
          'values', [float(sc['frames'][tz].values[sc['ids'][tz][x]]) for x in (i, j, k)], 'delta*', dst[tz],
          'R err', np.max(abs(rowsR[tz]['x'] - rowsR[tz]['reference'])) / L)


if __name__ == '__main__':
    main()
