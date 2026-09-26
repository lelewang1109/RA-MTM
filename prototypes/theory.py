"""Theory made computable: exact certificate at display resolution, topological price of
non-contiguity, and the position-topology lower frontier.

(1) dp_tau: exact min-max reference deviation for a hierarchy (any arity) at pixel resolution.
    For a subtree S, E_S(x) = earliest possible "next free start" after placing S's leaves greedily
    with no leaf starting before x (minimised over S's legal orders). E_S is monotone in x and
      leaf:        E(x) = s + W + G, s = max(x, lo) if s <= hi else INF
      binary node: E_S = min(E_B o E_A, E_A o E_B)
      m-ary node:  subset DP  F[mask] = min_c E_c o F[mask \\ c]
    Root feasible iff E_root(0) < INF. Bisection on tau. Cost O(n N) per test (binary), O(2^m m N) per m-ary node.
(2) violated_nodes / price check: for any 1-D map, d_top >= (f(parent(v)) - f(v)) / 2 for every node v whose
    leaf set is not contiguous in the map's leaf order (Theorem 2).
(3) frontier: Phi(delta) = tau*(flatten T at all nodes with persistence gap <= 2 delta)  (Corollary).
"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ------------------------------------------------------------------ (1) DP
class Disc:
    """Pixel discretisation of a continuous layout problem (canvas [a, a+L] -> N pixels)."""
    def __init__(self, w, q, p, N):
        self.N = N; self.dx = p.canvas / N
        self.W = np.maximum(1, np.rint(np.asarray(w) / self.dx)).astype(int)
        self.G = int(np.rint(p.gap / self.dx))
        self.h = p.rho * self.W / 2.                     # anchor slack in pixels
        self.q = (np.asarray(q) - p.canvas_origin) / self.dx
        self.M = N + self.G + 2; self.INF = self.M - 1


def _leaf_E(d, i, tau):
    x = np.arange(d.M)
    lo = max(0, int(np.ceil(d.q[i] - tau - d.h[i] - d.W[i] / 2 - 1e-9)))
    hi = min(d.N - d.W[i], int(np.floor(d.q[i] + tau + d.h[i] - d.W[i] / 2 + 1e-9)))
    s = np.maximum(x, lo)
    E = np.where((s <= hi) & (x < d.INF), s + d.W[i] + d.G, d.INF)
    return np.minimum(E, d.INF)


def _node_E(d, tree, tau):
    if isinstance(tree, (int, np.integer)): return _leaf_E(d, int(tree), tau)
    kids = [_node_E(d, c, tau) for c in tree]
    m = len(kids)
    if m == 1: return kids[0]
    if m == 2:
        A, B = kids
        return np.minimum(B[A], A[B])
    F = {0: np.arange(d.M)}
    for mask in range(1, 1 << m):
        best = None
        for c in range(m):
            if mask >> c & 1:
                cand = kids[c][F[mask ^ (1 << c)]]
                best = cand if best is None else np.minimum(best, cand)
        F[mask] = best
    return F[(1 << m) - 1]


def dp_feasible(d, tree, tau):
    return _node_E(d, tree, tau)[0] < d.INF


def dp_tau(w, q, tree, p, N, tol=1e-3):
    """Exact tau* (world units) of the pixel-discretised problem; inf if infeasible at any tau."""
    d = Disc(w, q, p, N)
    hi = float(N)
    if not dp_feasible(d, tree, hi): return np.inf
    lo = 0.
    if dp_feasible(d, tree, 0.): return 0.
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if dp_feasible(d, tree, mid): hi = mid
        else: lo = mid
    return hi * d.dx


# ----------------------------------------------------- tree / persistence tools
def struct_nodes(s, parent=None, out=None):
    """(node_id, parent_id, leaves) for every branching node of rh.node_tree structure."""
    out = [] if out is None else out
    if isinstance(s, int): return out, [s]
    leaves = []
    for c in s[1]:
        _, lv = struct_nodes(c, s[0], out); leaves += lv
    out.append((s[0], parent, leaves))
    return out, leaves


def violated_nodes(struct, order):
    """Non-root nodes whose leaf set is not contiguous in `order` (tuple of leaf ranks)."""
    pos = {leaf: k for k, leaf in enumerate(order)}
    nodes, _ = struct_nodes(struct)
    bad = []
    for v, parent, leaves in nodes:
        if parent is None: continue
        ps = sorted(pos[l] for l in leaves)
        if ps[-1] - ps[0] + 1 != len(ps): bad.append((v, parent))
    return bad


def flatten_set(struct, nodes):
    import relax_hierarchy as rh
    for v in nodes: struct = rh.flatten(struct, v)
    return struct


def to_tree(struct):
    return struct if isinstance(struct, int) else [to_tree(c) for c in struct[1]]


def gaps(fr, struct):
    """Persistence gap |f(parent) - f(v)| for every non-root branching node."""
    nodes, _ = struct_nodes(struct)
    return {v: abs(float(fr.values[v] - fr.values[par])) for v, par, _ in nodes if par is not None}


def frontier_frame(fr, struct, w, q, p, N, deltas):
    """Phi(delta) for one frame: tau* after flattening every node with gap <= 2 delta."""
    g = gaps(fr, struct); out = []
    for dlt in deltas:
        W_ = [v for v, gv in sorted(g.items(), key=lambda kv: kv[1]) if gv <= 2 * dlt + 1e-12]
        s = flatten_set(struct, W_)
        out.append(dp_tau(w, q, to_tree(s), p, N))
    return out
