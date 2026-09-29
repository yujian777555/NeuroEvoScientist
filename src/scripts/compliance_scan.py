"""Submission compliance scan (Blocker 8, plans/submission_hardening_plan.md).

Scans paper-facing files for prohibited wording. For each match, classifies:
- historical/development-only (docs/phases, plans) -> safe
- paper-facing (paper/) -> must be fixed

Exit 0 when paper-facing files are clean.
"""

import os
import re
import sys

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")

PROHIBITED = [
    (r"ENSS.{0,40}(outperform|beat|better than|superior).{0,40}random",
     "ENSS > random search"),
    (r"[Mm]amba.{0,40}(improve|boost|better).{0,30}performance",
     "Mamba improves performance"),
    (r"first[- ]ever|first to (show|demonstrate|propose|introduce|present)|"
     r"the first (to|method|work|approach|system)|首个|首次提出",
     "unsupported 'first' claim"),
    (r"full neural architecture self[- ]evolution",
     "full neural architecture self-evolution"),
    (r"[Ll]o[Rr]A|QLoRA", "LoRA/QLoRA wording (allowed only as adapter tech "
     "in related work / legacy-tagged docs)"),
    (r"universal(ly)?.{0,40}(superior|better|optimal)",
     "universal superiority"),
    (r"capability collapse", "QASPER capability collapse wording"),
    (r"backbone[- ]independent", "backbone-independent task preference"),
]

PAPER_FACING = ["paper/"]
SAFE_PREFIXES = ["docs/", "plans/", "issues/"]  # development history
SAFE_FILES = ["CHANGELOG.md", "README.md", "status.json",
              "paper/submission_checklist.md",  # lists the red lines itself
              "paper/title_candidates.md",      # contains a red-line self-check
              "paper/references.bib",           # citations, not prose claims
              ]


def classify(path):
    base = os.path.basename(path)
    if any(path.startswith(p) for p in PAPER_FACING) \
            and path not in SAFE_FILES and base not in SAFE_FILES:
        return "PAPER-FACING"
    return "development-history"


def main():
    hits = []
    for root, _, files in os.walk(_REPO):
        if ".git" in root or "__pycache__" in root or "node_modules" in root:
            continue
        for fn in files:
            if not fn.endswith((".md", ".bib", ".txt")):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, _REPO).replace("\\", "/")
            with open(path, encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    for pattern, label in PROHIBITED:
                        if re.search(pattern, line, re.IGNORECASE):
                            hits.append((rel, lineno, label,
                                         classify(rel), line.strip()[:100]))

    paper_hits = [h for h in hits if h[3] == "PAPER-FACING"]
    dev_hits = [h for h in hits if h[3] != "PAPER-FACING"]

    print("== paper-facing matches (must be zero) ==")
    for h in paper_hits:
        print("  %s:%d [%s] %s" % h[:4])
    print("== development-history matches (safe, for audit) ==")
    for h in dev_hits:
        print("  %s:%d [%s]" % h[:3])
    print("\nsummary: %d paper-facing, %d development-history"
          % (len(paper_hits), len(dev_hits)))

    sys.exit(1 if paper_hits else 0)


if __name__ == "__main__":
    main()
