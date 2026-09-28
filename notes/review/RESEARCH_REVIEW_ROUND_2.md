# Research review — round 2 (verify fixes)

You reviewed this project in round 1 (`notes/review/codex_review_round1.md`). The authors responded; the change log with status is in `notes/review/2026-09-26-research-review.md` (Chinese; the table "评审发现的实现与表述错误，及处理状态"). Please verify the fixes against the artifacts, not the change log:

1. Certified frontier: `prototypes/theory.py` (`Disc(mode='relax')`, `tau_lower`, `frontier_steps`, `phi_at`), `prototypes/frontier.py`, results `prototypes/output/frontier.json` (now includes per-frame Corollary-1 checks `corollary_violations`). Is the plotted curve now a certified lower bound of the continuous problem (Prop. 5′ in `paper/proofs_zh.md` / `paper/proofs.tex`)? Any remaining direction error?
2. DP bracket and rounding fixes (`dp_tau`, `rhalf`).
3. New relaxation policy "threshold + prune" (`prototypes/relax_hierarchy.py::relax_frame_threshold`, default in `run`): does it fix the plateau failure (ERA5 frame 9) and unresolved frames? Is the description in `paper/draft_zh.md` §6.4 accurate (κ controls which nodes are flattened; final d_top reported; no approximation guarantee)?
4. Misreading re-analysis (`prototypes/misreading.py`): harmonised normalisation (occupied anchor range for all methods), threshold relaxation, paired 8-frame temporal-block bootstrap of differences (`paired` in `prototypes/output/replicate_*.json`). Are the draft's §7.3 statements (k = 2 windows, proxy sign disagreement, permutation null, missed rates) now correct and appropriately scoped?
5. Proof qualifications (pseudo-polynomial, degree-exponential, tolerance, conventions for Prop. 6, Theorem 2 without extremum assumption, Corollary 1 necessary-not-attainable).
6. Framing in `paper/draft_zh.md` v0.3: three contributions, scope table in §4, claims boundaries. Anything still over-claimed?

Then give: (a) a mock PacificVis review (summary, strengths, weaknesses, score 1–5 with confidence), (b) the three highest-lift remaining actions for the next four weeks, (c) whether the verdict changes from round 1.

=== SCOPE LIMITS (these bound what you PROPOSE, never what you look for) ===
Report anything that is actually wrong here — including a rare-looking case, if
this repo actually produces it. Then keep the fix in scope:
1. This is a RESEARCH-WORKFLOW tool, not a security paper. Verification is
   welcome; over-defense is not. Assume a cooperating operator on their own
   machine — a malicious local user is NOT in the threat model.
2. Do NOT propose SHA / hash / content-fingerprint / digest-binding schemes.
   Reporting a real defect in hashing code that already exists is fine.
3. NO speculative machinery: do not add feature flags, migration frameworks,
   compat layers, wrappers, pins, or similar mechanisms unless evidence shows
   a current repo defect they fix or an explicit existing invariant they must
   preserve. "Load-bearing", "compatibility", and "not scaffolding" are labels,
   not evidence. Point to the failing path/artifact or invariant, and check the
   proposal's factual premises, such as whether a named package version exists.
4. NO corner-case obsession: exotic encodings, symlink races, RTL text and
   millisecond races are out of scope unless you can show the case arises here.
5. Where a rubric or checklist is genuinely needed, do not over-mechanize
   judgement. A clear sentence a human reads beats a scored table nobody
   maintains.
Exception: code that runs remote commands, starts a network service, or installs
an MCP server runs on the user's machine with their credentials — trust-boundary
findings there are in scope and the default is strict.
Say plainly when something is correct. Do not manufacture findings.
