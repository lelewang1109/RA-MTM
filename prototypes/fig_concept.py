"""Concept figure: from a 2-D scalar field to a merge tree map, and why hierarchy and space conflict.

(a) Analytic field with three minima A, B, C; A and B share a trough and merge first, C lies between them along
    the reference direction (x). Dashed lines project the minima onto the reference axis (q_A < q_C < q_B).
(b) Its join tree, computed by a union-find sweep of the grid; heights are merge values; gamma = gap between the
    A-B merge and the root.
(c) 1-D layouts on the reference axis: sorting by reference splits subtree {A,B}; the best layout that keeps
    {A,B} contiguous must deviate by tau* (arrows q -> u).
(d) The resulting merge-tree-map column (value profile along the 1-D axis, colour strip below): merge levels read
    from the column equal those of the tree.
Output: prototypes/output/fig_concept.png/.pdf.  Run: .venv/bin/python -W ignore prototypes/fig_concept.py
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr, figstyle as fs
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = tr.OUT; plt = tr.plt
fs.apply()
COL = dict(A='#0072b2', B='#56b4e9', C='#d55e00')
P = dict(A=(2.2, 5.6), B=(7.8, 5.9), C=(5.0, 2.4))


def field(n=161):
    g = np.linspace(0, 10, n); X, Y = np.meshgrid(g, g)
    G = lambda c, s: np.exp(-((X - c[0]) ** 2 + (Y - c[1]) ** 2) / (2 * s ** 2))
    f = -1.00 * G(P['A'], 1.05) - 0.92 * G(P['B'], 1.05) - 0.98 * G(P['C'], 0.95)
    # trough joining A and B along an arc to the north
    arc_y = 5.75 + 1.9 * np.sin(np.pi * np.clip((X - 2.2) / 5.6, 0, 1))
    inside = (X > 2.2) & (X < 7.8)
    f += -0.62 * np.exp(-((Y - arc_y) ** 2) / (2 * .42 ** 2)) * inside * np.sin(np.pi * np.clip((X - 2.2) / 5.6, 0, 1)) ** .35
    f += 0.012 * ((X - 5) ** 2 + (Y - 5) ** 2) / 25          # gentle bowl so the root merge is inside the domain
    return g, X, Y, f


def merge_values(g, f):
    """Union-find sweep (8-neighbourhood): merge value of the components containing the labelled minima."""
    n = len(g); idx = {k: (int(np.argmin(abs(g - p[1]))), int(np.argmin(abs(g - p[0])))) for k, p in P.items()}
    for k, (i, j) in idx.items():                           # snap to the local minimum
        for _ in range(50):
            win = f[max(0, i - 1):i + 2, max(0, j - 1):j + 2]; di, dj = np.unravel_index(np.argmin(win), win.shape)
            ni, nj = max(0, i - 1) + di, max(0, j - 1) + dj
            if (ni, nj) == (i, j): break
            i, j = ni, nj
        idx[k] = (i, j)
    parent = -np.ones(n * n, int); order = np.argsort(f.ravel(), kind='stable'); lab = {}
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    merges = []; seen = {i * n + j: k for k, (i, j) in idx.items()}
    comp = {}
    for v in order:
        parent[v] = v; i, j = divmod(v, n); comp[v] = {seen[v]} if v in seen else set()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                a, b = i + di, j + dj
                if (di or dj) and 0 <= a < n and 0 <= b < n and parent[a * n + b] >= 0:
                    r1, r2 = find(v), find(a * n + b)
                    if r1 != r2:
                        s1, s2 = comp[r1], comp[r2]
                        if s1 and s2: merges.append((float(f.ravel()[v]), frozenset(s1), frozenset(s2)))
                        parent[r2] = r1; comp[r1] = s1 | s2
    vals = {k: float(f[idx[k]]) for k in P}
    return vals, merges[:2], idx


def main():
    g, X, Y, f = field(); vals, merges, idx = merge_values(g, f)
    sAB = [m for m in merges if m[1] | m[2] == frozenset('AB')]
    sAB = sAB[0][0] if sAB else merges[0][0]; sRoot = max(m[0] for m in merges)
    gamma = sRoot - sAB
    fig = plt.figure(figsize=(fs.TEXT_W, 2.05))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.0, .95, 1.25, 1.25], wspace=.38, left=.025, right=.99, top=.86, bottom=.15)
    # (a) field
    ax = fig.add_subplot(gs[0]); ax.imshow(f, origin='lower', extent=[0, 10, 0, 10], cmap='RdBu_r', vmin=-1.1, vmax=1.1)
    ax.contour(g, g, f, levels=np.linspace(f.min(), f.max(), 13), colors='k', linewidths=.25, alpha=.5)
    for k, (x, y) in P.items():
        i, j = idx[k]; x, y = g[j], g[i]
        ax.plot(x, y, 'o', color=COL[k], ms=6, mec='w', mew=.8); ax.text(x + .35, y + .35, k, color='k', fontsize=8, fontweight='bold')
        ax.plot([x, x], [y, -.9], ':', color=COL[k], lw=.8, clip_on=False)
        ax.plot(x, -.9, 'v', color=COL[k], ms=4, clip_on=False)
    ax.annotate('', (9.7, -.9), (.3, -.9), arrowprops=dict(arrowstyle='->', lw=.8), annotation_clip=False)
    ax.text(5, -1.8, 'reference coordinate $q$', ha='center', fontsize=6.5)
    ax.set(xlim=(0, 10), ylim=(0, 10), xticks=[], yticks=[], aspect='auto'); ax.set_title('(a) field: A, B share a trough')
    # (b) join tree
    ax = fig.add_subplot(gs[1]); xs = dict(A=0, B=1, C=2); xAB = .5
    for k in 'AB': ax.plot([xs[k], xs[k]], [vals[k], sAB], color=COL[k], lw=2)
    ax.plot([0, 1], [sAB, sAB], color='k', lw=1); ax.plot([xAB, xAB], [sAB, sRoot], color='#0072b2', lw=2, alpha=.6)
    ax.plot([xs['C'], xs['C']], [vals['C'], sRoot], color=COL['C'], lw=2); ax.plot([xAB, 2], [sRoot, sRoot], color='k', lw=1)
    ax.plot([1.25, 1.25], [sRoot, sRoot + .12], color='k', lw=1)
    for k in P: ax.plot(xs[k], vals[k], 'o', color=COL[k], ms=5, mec='k', mew=.4); ax.text(xs[k], vals[k] - .09, k, ha='center', va='top', fontsize=7, fontweight='bold')
    ax.plot(xAB, sAB, 's', color='k', ms=3.5); ax.plot(1.25, sRoot, 's', color='k', ms=3.5)
    ax.annotate('', (1.62, sRoot), (1.62, sAB), arrowprops=dict(arrowstyle='<->', lw=.7, color='#c0392b'))
    ax.text(1.68, (sAB + sRoot) / 2, r'$\gamma_v$', color='#c0392b', fontsize=7.5, va='center')
    ax.text(-.15, sAB + .03, 'A–B merge', fontsize=6, va='bottom'); ax.text(.55, sRoot + .03, 'root', fontsize=6, va='bottom')
    ax.set(xlim=(-.4, 2.4), ylim=(min(vals.values()) - .3, sRoot + .3), xticks=[]); ax.set_ylabel('value', labelpad=1)
    ax.set_title('(b) merge tree $((A,B),C)$')
    # (c) layouts on the reference axis
    ax = fig.add_subplot(gs[2]); q = {k: g[idx[k][1]] for k in P}; w, gap = 1.0, .2
    tau = (w + gap + q['B'] - q['C']) / 2; u = dict(A=q['A'], B=q['B'] - tau, C=q['C'] + tau)
    yq, y1, y2 = 2.6, 1.55, .35
    ax.plot([0, 10], [yq, yq], color='k', lw=.5); ax.text(0, yq + .22, 'reference $q$', fontsize=6.3)
    for y0, pos, lab in [(y1, q, 'sorted by $q$: A C B, splits {A,B}'), (y2, u, 'best order keeping {A,B}: A B C')]:
        ax.plot([0, 10], [y0, y0], color='#bbbbbb', lw=.5); ax.text(0, y0 + .24, lab, fontsize=6.3)
        for k, x in pos.items():
            ax.add_patch(Rectangle((x - w / 2, y0 - .15), w, .3, color=COL[k], alpha=.85, lw=0))
            ax.text(x, y0, k, ha='center', va='center', color='w', fontsize=7, fontweight='bold')
    for k in P:
        ax.plot(q[k], yq, 'v', color=COL[k], ms=4.5)
        ax.plot([q[k], q[k]], [yq, y2 + .17], ':', color=COL[k], lw=.7)
        if abs(u[k] - q[k]) > .05:
            yy = y2 - (.26 if k == 'B' else .4); ax.add_artist(FancyArrowPatch((q[k], yy), (u[k], yy), arrowstyle='->', mutation_scale=7, color=COL[k], lw=1.1))
    ax.text(5, y2 - .72, f'max deviation $\\tau^*$ = {tau:.2f}, shared by B and C', ha='center', fontsize=6.3)
    ax.set(xlim=(-.2, 10.2), ylim=(-.45, 3.0), xticks=[], yticks=[]); [ax.spines[s_].set_visible(False) for s_ in ['left', 'bottom']]
    ax.set_title('(c) hierarchy vs. space')
    # (d) the column of the merge tree map: leaf values at anchors, barriers at merge values between them
    ax = fig.add_subplot(gs[3]); order = sorted(P, key=lambda k: u[k]); xx = np.linspace(0, 10, 800)
    knots_x = [0.] + [u[k] for k in order] + [10.]; top = sRoot + .12
    bars = {('A', 'B'): sAB, ('B', 'C'): sRoot}
    prof = np.empty_like(xx); owner = np.empty(len(xx), object)
    pts = [(0., top, None)]
    for a_, b_ in zip(order[:-1], order[1:]):
        pts += [(u[a_], vals[a_], a_), ((u[a_] + u[b_]) / 2, bars.get((a_, b_), bars.get((b_, a_))), None)]
    pts += [(u[order[-1]], vals[order[-1]], order[-1]), (10., top, None)]
    px = np.array([p[0] for p in pts]); py = np.array([p[1] for p in pts])
    for m in range(len(pts) - 1):
        sel = (xx >= px[m]) & (xx <= px[m + 1]); t_ = (xx[sel] - px[m]) / (px[m + 1] - px[m])
        prof[sel] = py[m] + (py[m + 1] - py[m]) * (1 - np.cos(np.pi * t_)) / 2
    for k in P:
        m = abs(xx - u[k]) < .3; ax.plot(xx[m], prof[m], color=COL[k], lw=1.8)
    ax.plot(xx, prof, color='k', lw=.5, alpha=.6)
    for k in P: ax.plot(u[k], vals[k], 'o', color=COL[k], ms=4, mec='k', mew=.4)
    ax.axhline(sAB, color='#888888', lw=.5, ls='--'); ax.axhline(sRoot, color='#888888', lw=.5, ls='--')
    ax.text(10.1, sAB, 'A–B', fontsize=6, va='center'); ax.text(10.1, sRoot, 'root', fontsize=6, va='center')
    lo = min(vals.values()) - .2
    ax.imshow(prof[None, :], extent=[0, 10, lo - .25, lo - .05], aspect='auto', cmap='RdBu_r', vmin=-1.1, vmax=1.1)
    ax.set(xlim=(0, 11.2), ylim=(lo - .28, top + .1), xticks=[], yticks=[]); ax.set_xlabel('1-D position (one map column)')
    ax.set_title('(d) merge tree map column')
    fig.savefig(OUT / 'fig_concept.png', dpi=300); fig.savefig(OUT / 'fig_concept.pdf'); plt.close(fig)
    print('values', vals, 'sAB', sAB, 'root', sRoot, 'gamma', gamma, 'tau*', tau, 'merges', [(round(m[0], 3), sorted(m[1]), sorted(m[2])) for m in merges])


if __name__ == '__main__':
    main()
