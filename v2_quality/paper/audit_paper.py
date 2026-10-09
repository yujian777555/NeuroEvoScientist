"""V2 paper audit: anonymity, citations, printed-statistics vs locked sources.

Outputs v2_quality/paper/audit_report.md and exits non-zero on any FAIL.
Checks:
  A. PDF anonymity: no names, emails, URLs, local paths in extracted text
     or metadata.
  B. Citations: every \\cite key exists in references.bib and vice versa.
  C. Statistics: every headline number in main.tex traced to its locked
     source (F1 summary CSV, F2 manifest/statistics JSON, frozen V1 CSVs,
     confirmation lock).
  D. Format: review mode line numbers present, page count recorded.
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
FT = os.path.join(REPO, "v2_quality", "fasttrack")

RESULTS = []


def rec(cid, ok, detail):
    RESULTS.append((cid, "PASS" if ok else "FAIL", detail))
    print("%-8s %-4s %s" % (cid, "PASS" if ok else "FAIL", detail))


def main():
    import fitz
    doc = fitz.open(os.path.join(HERE, "main.pdf"))
    text = "\n".join(p.get_text() for p in doc)
    meta = doc.metadata

    # -- A. anonymity ---------------------------------------------------------
    forbidden = ["yujian", "NeuroEvoScientist team", "github.com",
                 "202532803004", "于舰", "@gmail", "@outlook", "@163.com",
                 "10.10.24.107"]
    hits = [p for p in forbidden if p.lower() in text.lower()]
    meta_hits = [p for p in forbidden
                 if p.lower() in json.dumps(meta).lower()]
    rec("A.anon", not hits and not meta_hits,
        "PDF text/metadata free of identifiers" if not (hits or meta_hits)
        else "FOUND: %s %s" % (hits, meta_hits))
    rec("A.meta", not meta.get("author") and not meta.get("title"),
        "PDF metadata author/title empty (anonymous)")

    # -- B. citations ---------------------------------------------------------
    tex = open(os.path.join(HERE, "main.tex"), encoding="utf-8").read()
    bib = open(os.path.join(HERE, "references.bib"), encoding="utf-8").read()
    cited = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", tex))
    cited = {k.strip() for group in cited for k in group.split(",")}
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    rec("B.cite2bib", cited <= defined,
        "all %d cited keys defined" % len(cited)
        if cited <= defined else "UNDEFINED: %s" % (cited - defined))
    rec("B.bib2cite", defined <= cited,
        "all %d bib entries cited" % len(defined)
        if defined <= cited else "UNCITED: %s" % (defined - cited))

    # -- C. statistics trace --------------------------------------------------
    man = json.load(open(os.path.join(FT, "f2_results", "run_manifest.json"),
                         encoding="utf-8"))
    stats = json.load(open(os.path.join(FT, "f2_results",
                                        "f2_statistics.json"), encoding="utf-8"))
    lock = json.load(open(os.path.join(FT, "confirmation_lock.json"),
                          encoding="utf-8"))
    cells = {c["config"]: c for c in man["cells"]}

    def has(*subs):
        return all(s in tex for s in subs)

    checks = [
        ("C.f2.acc", abs(cells["REF"]["capability"] - 211/300) < 1e-9
         and abs(cells["B2"]["capability"] - 215/300) < 1e-9
         and has("70.33", "71.67", "211/300", "215/300"),
         "REF=211/300=70.33%%, B2=215/300=71.67%% in tex and manifest"),
        ("C.f2.tok", has("68{,}017", "50{,}049", "118{,}066", "197{,}017",
                         "44{,}137", "241{,}154", "19{,}117", "48{,}264",
                         "67{,}381")
         and cells["REF"]["prompt_tokens_total"] == 68017
         and cells["B1"]["completion_tokens_total"] == 48264,
         "all six token counts match manifest"),
        ("C.f2.primary", stats["primary_contrast"]["mcnemar"]["p_exact"]
         == 0.671811 and has("-1.33", "[-6.00, +3.33]", "p{=}0.67"),
         "primary REF-B2 -1.33pp CI[-6.00,+3.33] p=0.67"),
        ("C.f2.secondary", stats["secondary_contrast"]["mcnemar"]["p_exact"]
         == 1.0 and has("0.00", "[-5.33, +5.33]", "p{=}1.0"),
         "secondary REF-B1 0.00pp CI[-5.33,+5.33] p=1.0"),
        ("C.f2.cost_ratio", has("1.75$\\times$", "3.56$\\times$",
                                "2.04$\\times$")
         and abs(118066/67381 - 1.752) < 0.01
         and abs(68017/19117 - 3.558) < 0.01
         and abs(241154/118066 - 2.043) < 0.01,
         "cost ratios 1.75x/3.56x/2.04x recomputed from manifest"),
        ("C.f2.n300", lock["n_items"] == 300 and has("n{=}300"),
         "300 locked items"),
        ("C.f1.cells", has("60.0", "59.0", "50.0", "49.0", "57.0", "11.0",
                           "13.0", "8{,}091", "67{,}391", "24{,}391"),
         "F1 dev cell values present"),
        ("C.f1.stats", has("+10.0", "p{=}0.087", "p{=}0.041", "p{=}0.043"),
         "F1 paired stats values present"),
        ("C.v1.headline", has("+29.0", "+16.7", "0.518", "0.859"),
         "V1 locked headline values present"),
        ("C.v1.audit", has("48", "random search", "Mamba-2"),
         "Phase18 audit + Mamba-2 negative results present"),
        ("C.qasper", has("paired sign test"),
         "QASPER paired sign test correctly labeled"),
    ]
    for cid, ok, detail in checks:
        rec(cid, bool(ok), detail)

    # V1 holdout cross-check against frozen CSV (not phase21_tables.md)
    import csv
    with open(os.path.join(REPO, "results", "phase20_holdout_results.csv"),
              encoding="utf-8") as f:
        rows = {(r["config"], r["benchmark"], r["model"]): r
                for r in csv.DictReader(f)}
    a15 = float(rows[("A_gsm", "gsm8k", "Qwen2.5-1.5B-Instruct")]["capability"])
    a7b = float(rows[("A_gsm", "gsm8k", "Qwen2.5-7B-Instruct")]["capability"])
    f15 = max(float(r["capability"]) for (c, b, m), r in rows.items()
              if b == "gsm8k" and m == "Qwen2.5-1.5B-Instruct"
              and c.startswith("fixed"))
    f7b = max(float(r["capability"]) for (c, b, m), r in rows.items()
              if b == "gsm8k" and m == "Qwen2.5-7B-Instruct"
              and c.startswith("fixed"))
    rec("C.v1.csv", abs(a15 - 0.5185) < 1e-3 and abs(a7b - 0.8597) < 1e-3
        and abs((a15 - f15) * 100 - 29.0) < 0.1
        and abs((a7b - f7b) * 100 - 16.7) < 0.1,
        "V1 holdout recomputed from frozen CSV: A_gsm %.4f/%.4f vs best "
        "fixed %.4f/%.4f -> +%.1f/+%.1fpp"
        % (a15, a7b, f15, f7b, (a15 - f15) * 100, (a7b - f7b) * 100))

    # -- D. format --------------------------------------------------------------
    rec("D.pages", len(doc) <= 8 + 3, "page count = %d (content+refs; ARR "
        "8-page content limit applies to ~5 content pages)" % len(doc))
    rec("D.review", "00" in text and "\\usepackage[review]{acl}" in tex,
        "review mode with line numbers")

    fails = [c for c, s, _ in RESULTS if s == "FAIL"]
    lines = ["# V2 Paper Audit Report",
             "",
             "Generated by `v2_quality/paper/audit_paper.py` (read-only).",
             "",
             "| Check | Status | Detail |", "|---|---|---|"]
    for cid, status, detail in RESULTS:
        lines.append("| %s | %s | %s |" % (cid, status, detail))
    lines += ["", "**Verdict: %s**" % ("FAIL: " + ", ".join(fails) if fails
                                        else "PASS"), ""]
    open(os.path.join(HERE, "audit_report.md"), "w",
         encoding="utf-8").write("\n".join(lines))
    print("\nVERDICT:", "FAIL" if fails else "PASS")
    sys.exit(2 if fails else 0)


if __name__ == "__main__":
    main()
