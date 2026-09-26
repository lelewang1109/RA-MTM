# Project: RA-MTM (paper collaboration)

Reference-Anchored Merge Tree Maps: lay out the merge-tree features of a 2D time-varying scalar field along fixed world X and Y axes, producing two time-aligned 1D maps whose paired anchors recover each feature's 2D position and motion. Compared against TMTM (paper 1) and ST-MTM (paper 2).

The code and research docs come from the collaborator (lelewang1109). The user (GitHub: ydvislab) is co-authoring the paper and works in this private copy first; it will be merged back into the collaborator's repo later.

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
  - `notes/2026-09-26-innovation-directions.md` → `notes/novelty/2026-09-26-novelty-report.md` → `notes/2026-09-26-prototype.md` is the current line of thinking: move from dual X/Y maps to one task-referenced map (radial / focus-distance / along-path reference) with the τ* certificate; novelty check verdict PROCEED 7/10.
- `prototypes/` — our own exploratory scripts (do not modify the collaborator's `src/`); `task_reference.py` reuses `solve_frame(reference=q)`.
- `.aris/traces/` — cross-model (Codex) review traces from ARIS skills.

## Not in git (per machine)

- Reference paper PDFs: put in `references/pdf/` (git-ignored). Hashes are in `references/provenance.json`; paper 1 = TMTM (Wiebke/TemporalMergeTreeMaps), paper 2 = ST-MTM preprint (no official code; reimplemented from §4.1–4.3).
- ERA5 input `data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc` — keep in cloud storage and symlink `data/real`. Must match the SHA-256 in `results/era5/protocol.json`. Ring data is generated, needs nothing.
- For prototypes, a 12-hourly equivalent (118 frames, 11.5 MB) is fetched anonymously from the public ARCO-ERA5 mirror by `prototypes/era5_arco.py` (needs `pip install xarray zarr gcsfs` in `.venv`). It reproduces the collaborator's tracks/hierarchies/extrema exactly but is not byte-identical to the CDS file; load it with `ep.SOURCE = <file>; ep.extract(step=1)`.
- User requirement (2026-09-26): improvements must be general — no per-dataset parameters or hand-picked references. See `notes/2026-09-26-general-method.md`.
- `.venv/`: `python3 -m venv .venv && .venv/bin/python -m pip install -e .`

## Conventions

- The user writes in Chinese; notes/docs in Chinese, code and paper text in English.
- Do not change the collaborator's code, protocol parameters, or published results without discussing it first; they are hash-audited (`scripts/verify_results.py`, `results/manifest.json`).
- Keep claims honest: the docs deliberately list limitations (see `notes/2026-09-26-initial-review.md`). Don't overstate superiority.
