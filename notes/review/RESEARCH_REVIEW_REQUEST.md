# Research review request (round 1)

Read `/Users/yudong/Research/RA-MTM/notes/review/RESEARCH_SUMMARY.md` first, then verify against the primary artifacts it cites:
- proofs: `paper/proofs_zh.md` (Chinese; notation in §0, Lemma 1–5, Prop 1–6, Theorem 1–2, Corollary 1)
- implementation: `prototypes/theory.py` (DP), `prototypes/relax_hierarchy.py` (closed form `tau_orders`, relaxation, `merge_errors`), `prototypes/misreading.py`, `prototypes/replicate.py`, `prototypes/frontier.py`, `prototypes/generality.py`, collaborator solver `src/ramtm/error_budget.py`
- raw results: `prototypes/output/replicate_*.json`, `misreading*.json`, `frontier.json`, `generality.json`, `relax_tradeoff.json`
- context: `notes/related-work-map.md`, `notes/novelty/2026-09-26-novelty-report-v2.md`, current draft `paper/draft_zh.md` (v0.1, to be rewritten), the two reference papers in `references/pdf/` (TMTM `koepp22.pdf`, ST-MTM `ssrn-6604235.pdf`).

Venue: IEEE PacificVis 2027 conference track (visualization; technique + analysis paper). Judge by visualization-venue standards (TVCG/EuroVis/PacificVis), not ML standards.

Please act as a senior visualization reviewer. Start from the assumption that the work is broken somewhere. Answer:
1. Is this publishable at PacificVis 2027 conference track? How strong is the innovation (score 1–10 with justification)? Is the author right that it "feels like a small problem in a small field"?
2. How should the framing be widened so that the contribution reads as general (hierarchy-constrained 1-D layouts: merge tree maps, dendrogram-ordered dense pixel displays / clustered heatmaps, geophylogenies, storylines with location axes)? Is the generality experiment (1024-leaf dendrograms) the right evidence, or what else?
3. Check the theory: are Prop 1 (closed form), Theorem 1 (earliest-next-start DP; optimal substructure; complexity), Prop 5 (≤ δ/2 discretisation), Theorem 2 (d_top ≥ gap/2 for ANY filling), Prop 6 (ℓ∞-cophenetic = labeled interleaving; label conventions of Munch & Stefanou), Corollary 1 (frontier) correct? Which are substantive vs. trivial? Any hidden assumption that breaks them (ties, plateaus, unary chains, multi-saddles, the anchor = extremum assumption, split vs join)?
4. Is the reader-proxy misreading analysis convincing? Threats to validity (dependence, thresholds, 2-D truth from extrema, chance model)? What would a reviewer demand (user study? another task?).
5. Missing baselines / comparisons / experiments (e.g., certificate under TMTM's and ST-MTM's own width models; Li–Wang for τ_free; optimal (not greedy) relaxation; a "midpoint" filling that attains the gap/2 bound; OLO/seriation baselines for dendrograms).
6. Give a concrete GO / NO-GO and a prioritized 5-week plan (highest acceptance lift per effort), and a results-to-claims matrix: which claims are allowed now, which need which evidence.

Be brutally honest; say plainly what is correct.

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
