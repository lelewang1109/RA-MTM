"""Hidden costs of relaxation? Temporal stability and non-positional quality measures for every method.

Per method (TMTM, ST-MTM, fixed-X anchored, ours A, ours R) and dataset:
  spurious_flip_rate  consecutive time steps: share of tracked pairs whose vertical order flips on the map while their
                      reference order does not flip (order instability not explained by motion along the reference)
  motion_residual     mean |du' - dq| / L of tracked features between consecutive steps, where u' is the map axis after
                      the best affine calibration onto the reference (fit over all steps; fair to maps with other axes)
  stress              per frame Kruskal stress-1 between 1-D anchor distances (optimal scale) and 2-D extremum distances
  spearman            per frame rank correlation between 1-D and 2-D pairwise distances (n >= 4)
  nn_preservation     per frame share of features whose 2-D nearest neighbour is also their 1-D nearest neighbour (n >= 3)
Output: prototypes/output/quality.json.  Run: .venv/bin/python -W ignore prototypes/quality.py
"""
from pathlib import Path
import sys, json
from itertools import combinations
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import replicate as rp, misreading as mr, task_reference as tr

OUT = tr.OUT
DATASETS = ['era5', 'era5_2014', 'wildfire', 'ring']


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else np.nan


def analyse(name):
    ds = rp.LOADERS[name](); sc = ds['sc']; tracks = sc['tracks']
    M, ext, conflict, ref = mr.method_positions(ds)
    qs = [np.asarray(q, float) for q in ref['qs']]; L = ref['extent']
    out = {}
    for m, D in M.items():
        U = [np.asarray(u, float) for u in D['u']]
        uu = np.concatenate(U); qq = np.concatenate(qs)
        A = np.c_[uu, np.ones_like(uu)]; a, b = np.linalg.lstsq(A, qq, rcond=None)[0]     # affine calibration onto the reference
        Uc = [a * u + b for u in U]
        flips = tot = 0; res = []
        for t in range(1, len(U)):
            prev = {k: i for i, k in enumerate(tracks[t - 1])}
            common = [(prev[k], i) for i, k in enumerate(tracks[t]) if k in prev]
            for (p1, c1), (p2, c2) in combinations(common, 2):
                su0 = np.sign(Uc[t - 1][p1] - Uc[t - 1][p2]); su1 = np.sign(Uc[t][c1] - Uc[t][c2])
                sq0 = np.sign(qs[t - 1][p1] - qs[t - 1][p2]); sq1 = np.sign(qs[t][c1] - qs[t][c2])
                tot += 1; flips += int(su0 != su1 and sq0 == sq1)
            for p, c in common: res.append(abs((Uc[t][c] - Uc[t - 1][p]) - (qs[t][c] - qs[t - 1][p])) / L)
        st, sp, nn = [], [], []
        for t, u in enumerate(U):
            P = np.asarray(ext[t], float); n = len(u)
            if n < 3: continue
            pr = list(combinations(range(n), 2))
            d1 = np.array([abs(u[i] - u[j]) for i, j in pr]); d2 = np.array([np.linalg.norm(P[i] - P[j]) for i, j in pr])
            s = (d1 @ d2) / max(d1 @ d1, 1e-12); st.append(float(np.sqrt(np.sum((s * d1 - d2) ** 2) / np.sum(d2 ** 2))))
            if n >= 4: sp.append(spearman(d1, d2))
            D1 = np.abs(u[:, None] - u[None]); D2 = np.linalg.norm(P[:, None] - P[None], axis=2)
            np.fill_diagonal(D1, np.inf); np.fill_diagonal(D2, np.inf)
            nn.append(float(np.mean(D1.argmin(1) == D2.argmin(1))))
        out[m] = dict(spurious_flip_rate=flips / max(tot, 1), pairs=tot, motion_residual=float(np.mean(res)),
                      stress=float(np.mean(st)), spearman=float(np.nanmean(sp)), nn_preservation=float(np.mean(nn)))
    return out


def main():
    res = {}
    for n in DATASETS:
        res[n] = analyse(n)
        print(n)
        for m, x in res[n].items():
            print(f"   {m:22s} flips {x['spurious_flip_rate']:.3f}  motion res {x['motion_residual']:.4f}  stress {x['stress']:.3f}  "
                  f"spearman {x['spearman']:.3f}  NN {x['nn_preservation']:.3f}", flush=True)
    (OUT / 'quality.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
