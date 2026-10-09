# Gate 3 Executor Report — V2 Paper Finalization (2026-10-09)

Executor: Kimi. Evidence commits: forensic `dff357b`; paper package commit
see status.json (`v2_fasttrack.f3_commit`).
This is the Executor's Gate-3 report; the GO/NO-GO decision belongs to the
Planner. **Nothing has been submitted anywhere.**

## Scope compliance

- NO new GPU experiments (F3 total GPU usage: 0).
- V1 frozen artifacts untouched (`paper/arr2026/main.pdf` SHA-256 verified
  unchanged by the forensic verifier).
- No result cherry-picking: every number in the paper traces to an
  immutable committed source (see `v2_quality/paper/submission_manifest.md`
  source-to-claim map); `paper/phase21_tables.md` was not used.
- The B1 cost/accuracy result is presented prominently (Table 2, Figure 1b,
  abstract, §6): B1 equals REF observed SVAMP accuracy with 1.75× fewer
  total tokens; REF has no demonstrated accuracy or cost superiority over
  B1 in F2.

## Step 1 — forensic F2 provenance (F3-A): PASS

`v2_quality/fasttrack/verify_f2_integrity.py` (read-only, CI-guarded by
`tests/test_v2_f2_forensic.py`) verified byte-for-byte: SVAMP test/train
full-file SHA-256 vs pre-inference lock and manifest; 300 ordered IDs
(count/unique/order/hash); 3×300 prediction rows (locked ID order, no
duplicates, non-empty full completions, binary scores, adapter-score
alignment, per-row genome, phenotype SHA vs manifest, recomputed
accuracies 211/215/211); paired stats recomputed (23/27 p=0.671811
CI[−6.0,+3.33]; 34/34 p=1.0 CI[−5.33,+5.33]; 33/29 p=0.703537) matching
committed values exactly; runner commit in history; V1 PDF hash unchanged.
Two PARTIAL annotations documented honestly in
`v2_quality/fasttrack/f2_provenance_forensic.md`: (1) the run-time loader
checked ordered IDs+count, not full file bytes (now closed post-hoc);
(2) the on-VM model-revision observation is not itself a committed
artifact. No BLOCKED condition; no dataset SHA mismatch.

## Step 2 — paper package (F3-B/C): COMPLETE

`v2_quality/paper/`: `manuscript.md`, `main.tex` (acl.sty review mode),
`references.bib` (22 entries, all cited, incl. MaAS / AgentSquare /
Evo-Memory / ADAS), `figures/` (fig1 capability-vs-token panels from
F1/F2 immutable CSV/JSON; fig2 paired-difference CIs marked as
non-equivalence), `main.pdf` (7 pages), `anonymous_supplementary.zip`
(106 files, scrubbed of VM paths/URLs/user paths; no dataset payloads),
`submission_manifest.md`, `audit_report.md`, build/audit scripts.

Content guards honored: three evidence tiers separated; Tier-1 headline
scoped as vs Direct-only fixed baselines (not search's isolated
contribution); Phase-18 evolution≈random and Mamba-2 negatives kept;
F1 exploratory labels (p=0.087 exploratory; p=0.041/0.043 secondary
unadjusted); F2 primary/secondary exact numbers; non-transfer worded as
"dev point estimate not replicated cross-benchmark" — not a formal
interaction, not equivalence, not universal non-transfer; QASPER labeled
paired sign test with extraction limitations; QA-style single-agent scope
stated in Introduction, Setting, and Limitations.

## Step 3 — verification

- Full test suite: 105/105 PASS (103 prior + 2 new forensic tests).
- Paper audit: 18/18 PASS (anonymity incl. PDF metadata; 22/22 citations;
  statistics vs locked sources; V1 holdout recomputed from frozen CSV:
  0.5185/0.8597 vs 0.2289/0.6932; review format; page count).
- PDF rendered and visually inspected page-by-page (7/7). Three layout
  defects found during inspection (title orphan line, figure label
  overlap, unbreakable reference URL) were fixed and re-verified.
- Supplementary rebuild verified free of forbidden patterns.

## Candidate venue (verified live 2026-10-09, https://aclrollingreview.org/dates)

- **ARR October 2026 cycle: submission deadline 2026-10-12** — final cycle
  for **NAACL 2027 / COLING 2027** (commitment 2026-12-23).
- ACL 2027: final ARR submission January 2027 (CFP: 2027-01-04).
- ARR requires reviewer registration by ALL authors at submission.
The owner decides target and performs any OpenReview upload; the Executor
recommends the 2026-10-12 cycle if the Planner's Gate-3 review completes
in time, otherwise the January 2027 cycle for ACL 2027.

## Remaining scientific risks (unchanged, disclosed in paper)

Public-benchmark contamination (SVAMP); single model family; cross-
benchmark rather than i.i.d. confirmation; Tier-2 exploratory with partial
provenance; QASPER extraction sensitivity; ±~5pp CI resolution at n=300.

## Gate-3 recommendation

**GO for submission** (owner action; Executor does not submit).
Package: `v2_quality/paper/main.pdf` + `anonymous_supplementary.zip`.
STOP point reached — awaiting Planner Gate-3 review.
