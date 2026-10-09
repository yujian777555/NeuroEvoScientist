"""READ-ONLY forensic integrity verifier for the F2 SVAMP confirmation.

Gate-2/F3 requirement: independently re-hash every committed F2 artifact and
compare against the pre-inference lock and the runner manifest. This script
NEVER modifies any file (except writing its own report on request) and never
re-runs inference.

Checks
------
A. Dataset bytes: SHA-256 of svamp_test.json / svamp_train.json full bytes
   vs confirmation_lock.json AND f2_results/run_manifest.json.
B. Ordered 300 test IDs recomputed from the dataset file vs lock
   (count, uniqueness, order, IDs hash).
C. Prediction files (REF/B2/B1): exactly the locked 300 IDs in locked order,
   no duplicates, non-empty full completion output, binary `correct`,
   `adapter_score` == `correct` per row, recomputed accuracy vs manifest,
   per-row genome vs baselines_f1.json, recomputed phenotype SHA-256 vs
   manifest.
D. Paired statistics recomputed from predictions (win/loss counts, exact
   two-sided McNemar, paired bootstrap CI with the same fixed seed) vs
   committed f2_statistics.json.
E. Provenance annotations: model/source revision evidence that is NOT
   independently committed (marked PARTIAL, never silently PASS), and the
   documented limitation that the original run-time loader checked only
   ordered ID hash + count, not full file bytes.
F. V1 frozen PDF hash unchanged.
G. Runner commit exists in repository history.

Exit code: 0 = no FAIL; 2 = at least one FAIL (hard blocker).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from math import comb

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
FT = os.path.join(REPO, "v2_quality", "fasttrack")
RESULTS = os.path.join(FT, "f2_results")

V1_PDF = os.path.join(REPO, "paper", "arr2026", "main.pdf")
V1_PDF_SHA = ("e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d")

BOOT_N = 10000
BOOT_SEED = 20260923

CHECKS = []  # (id, status, detail)


def record(cid, status, detail):
    CHECKS.append((cid, status, detail))
    print("%-4s %-7s %s" % (cid, status, detail))


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mcnemar_p(aw, bw):
    n = aw + bw
    if n == 0:
        return 1.0
    k = min(aw, bw)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n))


def bootstrap_ci(diffs, n=BOOT_N, seed=BOOT_SEED):
    import random
    rng = random.Random(seed)
    means = sorted(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) /
                   len(diffs) for _ in range(n))
    return (round(100 * means[int(0.025 * n)], 2),
            round(100 * means[int(0.975 * n)], 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-report", action="store_true",
                    help="write v2_quality/fasttrack/f2_provenance_forensic.md")
    args = ap.parse_args()

    lock = load_json(os.path.join(FT, "confirmation_lock.json"))
    manifest = load_json(os.path.join(RESULTS, "run_manifest.json"))
    stats = load_json(os.path.join(RESULTS, "f2_statistics.json"))
    baselines = load_json(os.path.join(FT, "baselines_f1.json"))
    fails = 0

    # -- A. dataset full-byte hashes -----------------------------------------
    for fname in ("svamp_test.json", "svamp_train.json"):
        key = fname.replace("svamp_", "")  # test.json / train.json
        actual = sha256_file(os.path.join(FT, "data", fname))
        want_lock = lock["files"][key]
        want_man = manifest["dataset_files_sha256"][key]
        ok = actual == want_lock == want_man
        fails += not ok
        record("A.%s" % key, "PASS" if ok else "FAIL",
               "%s full-byte sha256 %s… (lock %s, manifest %s)"
               % (fname, actual[:12],
                  "match" if actual == want_lock else "MISMATCH",
                  "match" if actual == want_man else "MISMATCH"))

    # -- B. ordered IDs recomputation ----------------------------------------
    rows = load_json(os.path.join(FT, "data", "svamp_test.json"))
    ids = [str(r["ID"]) for r in rows]
    ids_hash = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    ok = (len(ids) == 300 and len(set(ids)) == 300
          and ids == lock["test_ids"] and ids_hash == lock["test_ids_sha256"])
    fails += not ok
    record("B.ids", "PASS" if ok else "FAIL",
           "300 ordered IDs recomputed: count=%d unique=%d order=%s hash=%s"
           % (len(ids), len(set(ids)),
              "match" if ids == lock["test_ids"] else "MISMATCH",
              "match" if ids_hash == lock["test_ids_sha256"] else "MISMATCH"))

    # -- C. prediction files --------------------------------------------------
    sys.path.insert(0, os.path.join(REPO, "src"))
    from genome.structured import StructuredGenome
    from evaluator.memory import _effective_to_dict

    preds = {}
    for cfg in ("REF", "B2", "B1"):
        path = os.path.join(RESULTS, "predictions_f2_%s.jsonl" % cfg)
        recs = [json.loads(l) for l in open(path, encoding="utf-8")]
        preds[cfg] = recs
        cell = next(c for c in manifest["cells"] if c["config"] == cfg)

        pids = [r["svamp_id"] for r in recs]
        genome = StructuredGenome(**{**baselines["common"],
                                     **baselines["baselines"][cfg]}).normalize()
        eff = _effective_to_dict(genome, "svamp_confirm")
        pheno = hashlib.sha256(json.dumps(eff, sort_keys=True)
                               .encode()).hexdigest()
        checks = {
            "n_rows=300": len(recs) == 300,
            "ids_order": pids == lock["test_ids"],
            "ids_unique": len(set(pids)) == 300,
            "output_full": all(isinstance(r["output"], str)
                               and len(r["output"]) > 0 for r in recs),
            "binary_correct": all(r["correct"] in (0.0, 1.0) for r in recs),
            "adapter_align": all(abs(r["adapter_score"] - r["correct"]) < 1e-9
                                 for r in recs),
            "genome_rows": all(r["genome"] == eff for r in recs),
            "phenotype_sha": pheno == cell["phenotype_sha256"],
        }
        acc = sum(r["correct"] for r in recs)
        checks["accuracy_vs_manifest"] = (
            abs(acc / 300.0 - cell["capability"]) < 1e-9)
        bad = [k for k, v in checks.items() if not v]
        fails += bool(bad)
        record("C.%s" % cfg, "PASS" if not bad else "FAIL",
               "%d rows, accuracy %d/300=%.4f; %s"
               % (len(recs), acc, acc / 300.0,
                  "all row checks ok" if not bad else "FAILED: %s" % bad))

    # -- D. paired statistics recomputation -----------------------------------
    def pair(a, b):
        wa = sum(1 for x, y in zip(preds[a], preds[b]) if x["correct"] > y["correct"])
        wb = sum(1 for x, y in zip(preds[a], preds[b]) if x["correct"] < y["correct"])
        diffs = [x["correct"] - y["correct"] for x, y in zip(preds[a], preds[b])]
        lo, hi = bootstrap_ci(diffs)
        return wa, wb, round(mcnemar_p(wa, wb), 6), lo, hi

    for label, a, b, key in (("REFvsB2", "REF", "B2", "primary_contrast"),
                             ("REFvsB1", "REF", "B1", "secondary_contrast"),
                             ("B2vsB1", "B2", "B1", "descriptive_B2_vs_B1")):
        wa, wb, p, lo, hi = pair(a, b)
        committed = stats[key]
        ok = (wa == committed["mcnemar"]["a_wins"]
              and wb == committed["mcnemar"]["b_wins"]
              and abs(p - committed["mcnemar"]["p_exact"]) < 1e-6
              and lo == committed["bootstrap"]["ci95_lo_pp"]
              and hi == committed["bootstrap"]["ci95_hi_pp"])
        fails += not ok
        record("D.%s" % label, "PASS" if ok else "FAIL",
               "wins %d/%d p=%.6f CI[%s,%s] %s committed"
               % (wa, wb, p, lo, hi, "==" if ok else "!="))

    # -- E. provenance annotations (honest PARTIAL, never silent PASS) --------
    record("E.loader", "PARTIAL",
           "run-time loader load_locked_test_rows() verified ONLY item count "
           "and ordered-ID hash at inference time; full dataset bytes were "
           "recorded but not runtime-verified. This verifier closes the gap "
           "post-hoc (checks A/B above).")
    model_ok = manifest["model_revision"] == lock["model_revision"]
    record("E.model_rev", "PARTIAL" if model_ok else "FAIL",
           "model revision %s consistent between lock and manifest; the on-VM "
           "offline-cache snapshot name was observed at launch (2026-10-09) "
           "but that observation is not itself a committed artifact — no "
           "independent committed proof of weight identity exists."
           % manifest["model_revision"][:12])
    fails += not model_ok

    # -- F. V1 frozen PDF ------------------------------------------------------
    if os.path.exists(V1_PDF):
        actual = sha256_file(V1_PDF)
        ok = actual == V1_PDF_SHA
        fails += not ok
        record("F.v1_pdf", "PASS" if ok else "FAIL",
               "paper/arr2026/main.pdf sha256 %s… %s frozen value"
               % (actual[:12], "==" if ok else "!="))
    else:
        record("F.v1_pdf", "FAIL", "paper/arr2026/main.pdf missing")
        fails += 1

    # -- G. runner commit in history -------------------------------------------
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", manifest["git_sha"] + "^{commit}"],
            cwd=REPO, stderr=subprocess.DEVNULL)
        record("G.commit", "PASS",
               "runner commit %s exists in repository history"
               % manifest["git_sha"][:12])
    except subprocess.CalledProcessError:
        record("G.commit", "FAIL",
               "runner commit %s NOT in repository" % manifest["git_sha"])
        fails += 1

    verdict = "FAIL" if fails else (
        "PASS (with documented PARTIAL provenance annotations)"
        if any(s == "PARTIAL" for _, s, _ in CHECKS) else "PASS")
    print("\nVERDICT: %s" % verdict)

    if args.write_report:
        lines = ["# F2 Provenance Forensic Audit (post-hoc, read-only)",
                 "",
                 "Date: 2026-10-09. Generated by "
                 "`v2_quality/fasttrack/verify_f2_integrity.py` "
                 "(read-only; no file modified, no inference re-run).",
                 "",
                 "Scope: Gate-2 mandated post-hoc closure of the run-time "
                 "verification gap. The original `load_locked_test_rows()` "
                 "validated **only item count and the ordered-ID hash** at "
                 "inference time; it did **not** SHA-256-verify full dataset "
                 "file bytes or model/source revisions at run time. Full-byte "
                 "dataset hashes were recorded in the pre-inference lock and "
                 "the runner manifest; this audit now verifies them against "
                 "the committed artifacts byte-for-byte.",
                 "",
                 "| Check | Status | Detail |",
                 "|---|---|---|"]
        for cid, status, detail in CHECKS:
            lines.append("| %s | %s | %s |" % (cid, status, detail))
        lines += ["",
                  "**Verdict: %s**" % verdict,
                  "",
                  "PARTIAL annotations are honest provenance limitations, not "
                  "failures: (1) the model weight revision is consistent "
                  "between the pre-inference lock and the manifest, and the "
                  "on-VM snapshot name was observed at launch, but that "
                  "observation is not itself a committed artifact; "
                  "(2) the run-time loader gap is disclosed and is now closed "
                  "post-hoc by checks A/B for all future readers.",
                  ""]
        with open(os.path.join(FT, "f2_provenance_forensic.md"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("report written: v2_quality/fasttrack/f2_provenance_forensic.md")

    sys.exit(2 if fails else 0)


if __name__ == "__main__":
    main()
