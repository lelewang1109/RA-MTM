# Round 2 (partial — usage limit hit before final report; resumes 19:22)

I’ll read the brief and my round-1 review, then check each claimed fix against the artifacts. I’ll state plainly which fixes hold, which are incomplete, and which claims lack evidence.

---

I’m using the academic paper reviewer skill to structure the mock review. The artifact audit will come first, especially the frontier’s bound direction, the plateau case, and the revised proxy analysis.

---

The frontier code now uses the right approach: it relaxes the continuous problem before discretizing and evaluates actual breakpoints. I’m checking that argument independently. The new relaxation also avoids requiring each individual flattening to help, though its logged certificate appears to describe the hierarchy before pruning.

---

The saved proxy tables match the revised headline numbers, including wildfire’s higher missed-change rate. The draft is still inconsistent: its abstract retains unrestricted polynomial-time and interleaving-distance claims, and Figure 3 still calls the permutation null “chance.” I’m now rerunning the numerical paths to check the saved results.

---

ERA5 frame 9 is fixed: the new policy flattens nodes 121 and 1403 together and reaches τ* = 0. The full ERA5 rerun also confirms zero unresolved frames at unlimited κ and exactly reproduces the saved frontier. I found a plotting defect, though: the line joining Gaussian results crosses below the certified bound. Only the measured points represent achieved layouts.

## Reviewer's own numerical checks (from the log)
- Dendrogram exact tau* (candidate search) 688.905 rows vs DP 689.004 (excess 0.1 px); OLO max 88.2%, median 14.5%.
- Green line segments below certified bound: 0 for ERA5, ERA5-2014, wildfire, Ring; 2 for Gaussian (line interpolation artefact; points above bound) -> fixed by plotting points only.