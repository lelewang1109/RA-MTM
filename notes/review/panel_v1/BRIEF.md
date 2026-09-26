# Panel review brief (ARS academic-paper-reviewer, full mode) — PacificVis 2027 Conference Paper Track

Venue: IEEE PacificVis 2027, Conference Paper Track (IEEE VGTC conference format, 9 pages body + 2 pages refs,
double-blind). Decision scale for the final report: Accept / Minor Revision / Major Revision / Reject, and a
PacificVis-style score 1 (strong reject) .. 5 (strong accept) with confidence 1..5.

Materials (read them yourself; do not trust summaries):
- Compiled PDF (what reviewers see; body ~7 pages): /private/tmp/claude-501/ramtm/paper_v1.pdf
  (use the Read tool with pages "1-8"; it renders page images)
- LaTeX source (slightly newer than the PDF: notation fix — pixel size is now lambda, error budget beta; new
  Sec. 3.2 "Tasks and the role of the reference"; theta sensitivity sentence): /Users/yudong/Research/RA-MTM/paper/pacificvis2027/main.tex
- References: /Users/yudong/Research/RA-MTM/paper/pacificvis2027/refs.bib
- Supplement proofs: /Users/yudong/Research/RA-MTM/paper/proofs.tex
- Evidence notes (Chinese): /Users/yudong/Research/RA-MTM/notes/2026-09-26-exact-frontier.md, /Users/yudong/Research/RA-MTM/notes/2026-09-26-replication.md
- Code that produced every number: /Users/yudong/Research/RA-MTM/prototypes/ (theory.py, attainable.py, filling.py,
  pointcert.py, relax_hierarchy.py, replicate.py, misreading.py, quality.py) and outputs in prototypes/output/*.json

Rules (IRON RULES of the panel):
1. Review INDEPENDENTLY. Do not read other reviewers' reports in /Users/yudong/Research/RA-MTM/notes/review/panel_v1/.
2. READ-ONLY: never modify the manuscript or any repository file except your own report file.
3. Every criticism must say what is wrong, where (section / page / equation / figure), and a concrete minimal fix.
4. Balance: 3-5 specific strengths with locations.
5. No sycophantic inflation; no manufactured issues. Say plainly when something is correct.
6. Write in English.

Report structure (markdown):
- Reviewer role and identity (given in your prompt); review focus (2-3 sentences)
- Recommendation (Accept / Minor / Major / Reject), PacificVis score 1-5, confidence 1-5
- Summary assessment (150-250 words)
- Strengths S1..S5 (with locations)
- Weaknesses W1..Wn ranked by impact on acceptance, each tagged CRITICAL / MAJOR / MINOR, with location and minimal fix
- Detailed comments by section (only where relevant to your focus)
- Questions to authors
- What would raise your score by one point
