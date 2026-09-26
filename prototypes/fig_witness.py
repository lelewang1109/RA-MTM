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
W0, W1, KAPPA = 100, 118, .2


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
    tz = max(W, key=lambda t: W[t][0] / max(log[t]['tau_hier'], 1e-9) + (H[t] / L))   # clear, explained conflict

    plt.rcParams.update({'axes.titlesize': 9, 'font.size': 8})
    fig = plt.figure(figsize=(12, 3.6))
    g = fig.add_gridspec(2, 3, height_ratios=[1, 3], width_ratios=[1.25, .8, 1.25], hspace=.08, wspace=.18,
                         left=.035, right=.97, top=.9, bottom=.13)
    ext = [W0 - .5, W1 - .5, p.canvas_origin, p.canvas_origin + L]; tt = np.arange(W0, W1)
    # (a)
    ax = fig.add_subplot(g[1, 0]); ax.imshow(mapsA[:, W0:W1], origin='lower', aspect='auto', extent=ext, cmap='magma', vmin=lo, vmax=hi)
    for t, (b, (i, j, k)) in W.items():
        u = rowsA[t]['x']; ax.plot([t, t], [u[i], u[j]], color='#56b4e9', lw=2.2, alpha=.9, solid_capstyle='round')
        ax.plot(t, u[k], 'o', mfc='none', mec='#e69f00', mew=1.6, ms=6)
    ax.axvline(tz, color='w', ls=':', lw=.9); ax.set(xlabel='time step', yticks=[], ylabel='1-D position')
    top = fig.add_subplot(g[0, 0], sharex=ax)
    F = np.array([d['tau_free'] for d in log])
    top.bar(tt, H[W0:W1] / L * 100, color='#d55e00', width=.85, label='hierarchy cost H')
    top.bar(tt, [W[t][0] / L * 100 if t in W else 0 for t in tt], color='#56b4e9', width=.4, label='witness bound')
    top.axhline(theta / L * 100, color='k', ls=':', lw=.8); top.tick_params(labelbottom=False); top.set_ylabel('% axis')
    top.legend(fontsize=6.5, loc='upper left', ncol=2, framealpha=.8)
    top.set_title('(a) merge tree kept: certificate and witness triples')
    # (b)
    ax = fig.add_subplot(g[:, 1]); q = np.asarray(ref['qs'][tz]); u = rowsA[tz]['x']; b, (i, j, k) = W[tz]
    for m in range(len(q)):
        c = '#56b4e9' if m in (i, j) else '#e69f00' if m == k else '#aaaaaa'; lw = 1.6 if m in (i, j, k) else .8
        ax.plot([q[m], u[m]], [1, 0], color=c, lw=lw); ax.plot(q[m], 1, 'v', color=c, ms=6); ax.plot(u[m], 0, 'o', color=c, ms=6, mec='k', mew=.4)
    ax.plot([p.canvas_origin, p.canvas_origin + L], [1, 1], 'k', lw=.6); ax.plot([p.canvas_origin, p.canvas_origin + L], [0, 0], 'k', lw=.6)
    ax.text(p.canvas_origin, 1.07, 'reference q', fontsize=7); ax.text(p.canvas_origin, -.13, 'anchor u (merge tree kept)', fontsize=7)
    ax.set_ylim(-.25, 1.2); ax.set_yticks([]); ax.set_xticks([])
    ax.set_title(f'(b) step {tz}: witness bound {b/L:.0%}, τ* = {log[tz]["tau_hier"]/L:.0%}\nblue: one subtree; orange: lies between them in q')
    # (c)
    ax = fig.add_subplot(g[1, 2]); ax.imshow(optR[:, W0:W1], origin='lower', aspect='auto', extent=ext, cmap='magma', vmin=lo, vmax=hi)
    for t in range(W0, W1):
        if R['frame_log'][t]['relaxed_nodes']: ax.plot(t, p.canvas_origin + .975 * L, 'v', color='#009e73', ms=4)
    ax.axvline(tz, color='w', ls=':', lw=.9); ax.set(xlabel='time step', yticks=[])
    top = fig.add_subplot(g[0, 2], sharex=ax, sharey=fig.axes[1])
    top.bar(tt, [np.max(abs(r['x'] - r['reference'])) / L * 100 for r in rowsR[W0:W1]], color='#009e73', width=.85, label='max position error')
    tw = top.twinx(); dd = np.array(dst[W0:W1]); m = dd > 1e-9
    tw.plot(tt[m], dd[m], 'o', color='#0072b2', ms=3, label='δ* (hPa, right)'); tw.tick_params(labelsize=7, colors='#0072b2')
    h1, l1 = top.get_legend_handles_labels(); h2, l2 = tw.get_legend_handles_labels()
    top.legend(h1 + h2, l1 + l2, fontsize=6.5, loc='upper left', ncol=2, framealpha=.8); top.tick_params(labelbottom=False, labelleft=False)
    top.set_title(f'(c) relaxed (κ = {int(KAPPA*100)}%), optimal filling; ▼ relaxed steps')
    fig.savefig(OUT / 'fig_witness.png', dpi=220); fig.savefig(OUT / 'fig_witness.pdf'); plt.close(fig)
    print('zoom step', tz, 'witness', b / L, 'tau*', log[tz]['tau_hier'] / L, 'H', H[tz] / L, 'triple', (i, j, k),
          'values', [float(sc['frames'][tz].values[sc['ids'][tz][x]]) for x in (i, j, k)], 'delta*', dst[tz],
          'R err', np.max(abs(rowsR[tz]['x'] - rowsR[tz]['reference'])) / L)


if __name__ == '__main__':
    main()
