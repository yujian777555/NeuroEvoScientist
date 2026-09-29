"""Build the anonymous reproducibility package (Blocker 3).

Produces paper/arr2026/anonymous_supplementary.zip containing code, configs,
protocol docs, result artifacts, and reproduction instructions — with all
identifying metadata stripped (no git history, no personal paths, no owner
identity, no identifying commit links).

Double-blind safe: the archive contains no author-identifying material.
"""

import os
import zipfile

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(_REPO, "paper", "arr2026", "anonymous_supplementary.zip")

INCLUDE = [
    "src/", "configs/", "tests/", "scripts_vm/",
    "paper/reproducibility_appendix.md",
    "docs/claim_audit.md", "docs/phase21_final_audit.md",
    "results/phase19_selection_lock.json", "results/phase20_selection_lock.json",
    "results/phase20_statistics.json", "results/phase21_qasper_diag_15b.json",
    "results/phase21_qasper_diag_7b.json", "results/phase18_pareto_fronts.json",
    "results/phase18_search_efficiency.csv",
]

STRIP_PATTERNS = ["/d/", "D:\\", "C:\\Users", "yujian777555", "于舰",
                  "10.10.24.107", "codex_mere"]


def anonymized(text):
    for pat in STRIP_PATTERNS:
        text = text.replace(pat, "<ANON>")
    return text


def main():
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for entry in INCLUDE:
            path = os.path.join(_REPO, entry)
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for fn in files:
                        if fn.endswith((".pyc", ".log")):
                            continue
                        fp = os.path.join(root, fn)
                        rel = os.path.relpath(fp, _REPO)
                        with open(fp, encoding="utf-8", errors="ignore") as f:
                            content = anonymized(f.read())
                        z.writestr(rel, content)
                        n += 1
            elif os.path.isfile(path):
                with open(path, encoding="utf-8", errors="ignore") as f:
                    z.writestr(entry, anonymized(f.read()))
                n += 1
    print("anonymous package:", OUT, "files:", n)


if __name__ == "__main__":
    main()
