"""Theory figure: the price of topology, the optimal filling, and the trade-off, on the concept example ((A,B),C).

(a) Merge tree kept (order A B C): every merge level is read correctly (d_top = 0), but the positions deviate by tau*.
(b) Order A C B (positions exact): with the LCA-path filling the A-B merge is read at the root: error gamma.
(c) Same order, barrier filling: barriers at s_AB + gamma/2 split the error: d_top = gamma/2 (Theorem 7 is tight;
    Proposition 8).
(d) The trade-off for this example: certified lower frontier Phi (step at gamma/2) and the three maps.
Output: prototypes/output/fig_topo_price.png/.pdf.  Run: .venv/bin/python -W ignore prototypes/fig_topo_price.py
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr, figstyle as fs, fig_concept as fc

OUT = tr.OUT; plt = tr.plt
fs.apply()
COL = fc.COL


def profile(order, pos, vals, bars, top, xx):
    pts = [(0., top)]
    for a_, b_ in zip(order[:-1], order[1:]):
        pts += [(pos[a_], vals[a_]), ((pos[a_] + pos[b_]) / 2, bars[(a_, b_)])]
    pts += [(pos[order[-1]], vals[order[-1]]), (10., top)]
    px = np.array([p[0] for p in pts]); py = np.array([p[1] for p in pts]); prof = np.empty_like(xx)
    for m in range(len(pts) - 1):
        sel = (xx >= px[m]) & (xx <= px[m + 1]); t_ = (xx[sel] - px[m]) / (px[m + 1] - px[m])
        prof[sel] = py[m] + (py[m + 1] - py[m]) * (1 - np.cos(np.pi * t_)) / 2
    return prof


def main():
    g, X, Y, f = fc.field(); vals, merges, idx = fc.merge_values(g, f)
    sAB = [m for m in merges if m[1] | m[2] == frozenset('AB')][0][0]; sR = max(m[0] for m in merges); gam = sR - sAB
    q = {k: g[idx[k][1]] for k in fc.P}; w, gap = 1.0, .2; tau = (w + gap + q['B'] - q['C']) / 2
    uA = dict(A=q['A'], B=q['B'] - tau, C=q['C'] + tau)
    xx = np.linspace(0, 10, 800); top = sR + .12; lo = min(vals.values()) - .12
    cases = [('(a) tree kept: A B C', ['A', 'B', 'C'], uA, {('A', 'B'): sAB, ('B', 'C'): sR}, 0., tau),
             ('(b) A C B, LCA filling', ['A', 'C', 'B'], q, {('A', 'C'): sR, ('C', 'B'): sR}, gam, 0.),
             ('(c) A C B, optimal filling', ['A', 'C', 'B'], q, {('A', 'C'): sAB + gam / 2, ('C', 'B'): sAB + gam / 2}, gam / 2, 0.)]
    fig = plt.figure(figsize=(fs.TEXT_W, 1.95))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, .95], wspace=.18, left=.03, right=.99, top=.86, bottom=.17)
    for c, (title, order, pos, bars, dtop, err) in enumerate(cases):
        ax = fig.add_subplot(gs[c]); prof = profile(order, pos, vals, bars, top, xx)
        ax.plot(xx, prof, color='k', lw=.8)
        for k in order:
            m = abs(xx - pos[k]) < .35; ax.plot(xx[m], prof[m], color=COL[k], lw=2)
            ax.plot(pos[k], vals[k], 'o', color=COL[k], ms=4, mec='k', mew=.4); ax.text(pos[k], vals[k] - .07, k, ha='center', va='top', fontsize=7, fontweight='bold')
            ax.plot(q[k], lo - .02, '^', color=COL[k], ms=4, clip_on=False)
        ax.axhline(sAB, color='#0072b2', lw=.6, ls='--'); ax.axhline(sR, color='#d55e00', lw=.6, ls='--')
        if c == 0:
            ax.text(9.95, sAB + .02, 'true A–B merge', fontsize=6, color='#0072b2', va='bottom', ha='right')
            ax.text(9.95, sR + .02, 'true root', fontsize=6, color='#d55e00', va='bottom', ha='right')
        # read A-B merge level on the map: max of profile between A and B
        a_, b_ = sorted([pos['A'], pos['B']]); readAB = prof[(xx >= a_) & (xx <= b_)].max()
        if abs(readAB - sAB) > 1e-3:
            xm = (a_ + b_) / 2 + (.9 if c == 1 else -1.6)
            ax.annotate('', (xm, readAB), (xm, sAB), arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=.8))
            ax.text(xm + .15, (readAB + sAB) / 2, 'A–B: ' + (r'$\gamma_v$' if c == 1 else r'$\gamma_v/2$'), color='#c0392b', fontsize=6.5, va='center',
                    bbox=dict(facecolor='white', edgecolor='none', pad=.5, alpha=.85))
        if c == 2:
            aC = prof[(xx >= pos['A']) & (xx <= pos['C'])].max(); xm = pos['C'] + .9
            ax.annotate('', (xm, sR), (xm, aC), arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=.8))
            ax.text(xm + .15, (sR + aC) / 2, r'A–C: $\gamma_v/2$', color='#c0392b', fontsize=6.5, va='center',
                    bbox=dict(facecolor='white', edgecolor='none', pad=.5, alpha=.85))
        ax.set(xlim=(0, 10), ylim=(lo - .05, top + .08), xticks=[], yticks=[])
        ax.set_title(title)
        ax.text(5, lo - .2, f'position error {err:.2f}   $d_{{top}}$ = ' + ('0' if dtop == 0 else (r'$\gamma_v$' if c == 1 else r'$\gamma_v/2$')),
                ha='center', va='top', fontsize=6.5)
    # (d) trade-off
    ax = fig.add_subplot(gs[3])
    ax.step([0, gam / 2, gam * 1.25], [tau, 0, 0], where='post', color='k', lw=1, ls='--', label='certified bound $\\Phi$')
    for (lab, x, y, mk) in [('(a)', 0, tau, 'o'), ('(b)', gam, 0, 's'), ('(c)', gam / 2, 0, 'o')]:
        ax.plot(x, y, mk, color='#009e73' if lab != '(b)' else '#999999', ms=5, mec='k', mew=.4)
        ax.text(x + .015, y + .1, lab, fontsize=6.5)
    ax.fill_between([0, gam / 2], 0, tau, color='#dddddd', alpha=.6, lw=0); ax.text(gam * .1, tau * .35, 'impossible', fontsize=6, color='#666666')
    ax.set(xlim=(-.02, gam * 1.25), ylim=(-.15, tau * 1.25), xticks=[0, gam / 2, gam], xticklabels=['0', r'$\gamma_v/2$', r'$\gamma_v$'])
    ax.set_xlabel('$d_{top}$', labelpad=1); ax.set_ylabel('position error', labelpad=1); ax.set_title('(d) trade-off')
    ax.legend(loc='upper right', fontsize=6, handlelength=1.5, frameon=False)
    fig.savefig(OUT / 'fig_topo_price.png', dpi=300); fig.savefig(OUT / 'fig_topo_price.pdf'); plt.close(fig)
    print('gamma', gam, 'tau', tau)


if __name__ == '__main__':
    main()
