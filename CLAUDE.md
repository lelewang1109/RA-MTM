# Project: RA-MTM (paper collaboration)

Reference-Anchored Merge Tree Maps: lay out the merge-tree features of a 2D time-varying scalar field along fixed world X and Y axes, producing two time-aligned 1D maps whose paired anchors recover each feature's 2D position and motion. Compared against TMTM (paper 1) and ST-MTM (paper 2).

The code and research docs come from the collaborator (lelewang1109). The user (GitHub: ydvislab) is co-authoring the paper and works in this private copy first; it will be merged back into the collaborator's repo later.

## Target venue

PacificVis 2027 **Conference Paper Track** (Busan, Apr 19–22 2027) — **decided 2026-09-26** (TVCG journal track deadline Sep 8 has passed; VIS 2027 considered and declined). Plan: `notes/2026-09-26-submission-plan.md`. Abstract **Nov 2, 2026**, full paper **Nov 9, 2026** (verify time zone on https://pacificvis2027.github.io/), 9 pages + 2 pages refs/acks. First-round notification Dec 16, 2026. Paper framing under discussion: see `notes/2026-09-26-paper-framing.md`.

## Remotes and sync

- `origin` = `ydvislab/RA-MTM` (private). All commits and pushes go here.
- `upstream` = `lelewang1109/RA-MTM` (collaborator, public). Fetch/merge only; push is disabled on purpose. Never push or open PRs there unless the user asks.
- Pull collaborator updates: `git fetch upstream && git merge upstream/main`.
- The user works from several machines (office, home, laptops). Everything needed to resume work must live in tracked files, not chat history or local Claude memory. When a session produces a decision or result, record it in `notes/` and commit + push before ending.

## Where things are

- `README.md`, `docs/` — collaborator's method, solver derivation, reproduction guide and results (Chinese). `docs/solver.md` has the section-by-section comparison against papers 1 and 2.
- `src/ramtm/` — algorithm. `error_budget.py` is the core LP/QP solver; baselines in `src/ramtm/baselines/`.
- `experiments/`, `scripts/run_experiments.py` — experiment protocol and entry point.
- `results/{ring,era5}/` — published evidence; `metrics.csv` is the main table.
- `notes/` — the user's own analysis, decisions and review-risk tracking (ours, not the collaborator's). Decide at merge time whether it goes upstream.
  - Line of thinking (history): `2026-09-26-innovation-directions.md` → `novelty/` → `2026-09-26-prototype.md` → `conflict-strategies` → `general-method` → `local-relaxation` → `paper-framing` → `misreading-pilot` → `replication`. Decisions are summarized in `notes/decisions.md`.
  - **Current paper framing** (after ARIS/Codex review round 1, innovation 7/10, GO): "How faithful can a hierarchy-constrained 1-D layout be?" — (1) positional certificate τ* + exact DP, (2) filling-independent topological price γ/2 + certified position–topology frontier, (3) cross-domain characterization (ERA5 ×2, wildfire, Ring, Gaussians) + dendrogram-display use. Claim limits: `notes/review/2026-09-26-research-review.md`. Status and remaining tasks: `notes/2026-09-26-submission-plan.md`.
- `paper/` — **`paper/pacificvis2027/` is the submission source** (VGTC template, `main.tex` + `refs.bib` + `figures/`; compile on Overleaf via `paper/pacificvis2027_overleaf.zip`, no local LaTeX). `paper/proofs.tex` = supplement (full proofs); `paper/draft_zh.md` / `proofs_zh.md` = Chinese versions; `paper/main.tex` = earlier generic-class English draft (superseded). Figures come from `prototypes/paper_figs.py`; every number from `prototypes/paper_numbers.py`.
- `prototypes/` — our own scripts (do not modify the collaborator's `src/`): `theory.py` (certificate, DP, certified lower bound, frontier), `relax_hierarchy.py` (threshold+prune relaxation), `general_method.py` (automatic defaults), `replicate.py` / `frontier.py` / `misreading*.py` / `robustness.py` / `generality.py` (experiments), outputs in `prototypes/output/`.
- `.aris/traces/` — cross-model (Codex) review traces from ARIS skills.

## Not in git (per machine)

- Reference paper PDFs: put in `references/pdf/` (git-ignored). Hashes are in `references/provenance.json`; paper 1 = TMTM (Wiebke/TemporalMergeTreeMaps), paper 2 = ST-MTM preprint (no official code; reimplemented from §4.1–4.3).
- ERA5 input `data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc` — keep in cloud storage and symlink `data/real`. Must match the SHA-256 in `results/era5/protocol.json`. Ring data is generated, needs nothing.
- For prototypes, a 12-hourly equivalent (118 frames, 11.5 MB) is fetched anonymously from the public ARCO-ERA5 mirror by `prototypes/era5_arco.py` (needs `pip install xarray zarr gcsfs` in `.venv`). It reproduces the collaborator's tracks/hierarchies/extrema exactly but is not byte-identical to the CDS file; load it with `ep.SOURCE = <file>; ep.extract(step=1)`.
- Extra real datasets (2026-09-26): wildfire FRP `data/real/wildfire/wildfire.json` (Zenodo 11234747, CC-BY 4.0) and ERA5 winter 2013–14 (`prototypes/era5_arco.py 2013-12-01T00 2014-02-01T00 <out>`); loaders in `prototypes/datasets_extra.py`. Full evidence chain on all datasets: `prototypes/replicate.py` → `notes/2026-09-26-replication.md`.
- User requirement (2026-09-26): improvements must be general — no per-dataset parameters or hand-picked references. See `notes/2026-09-26-general-method.md`.
- `.venv/`: `python3 -m venv .venv && .venv/bin/python -m pip install -e .`

## Conventions

- The user writes in Chinese; notes/docs in Chinese, code and paper text in English.
- Do not change the collaborator's code, protocol parameters, or published results without discussing it first; they are hash-audited (`scripts/verify_results.py`, `results/manifest.json`).
- Keep claims honest: the docs deliberately list limitations (see `notes/2026-09-26-initial-review.md`). Don't overstate superiority.
