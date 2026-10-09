"""Build the V2 anonymous supplementary ZIP (scrubbed staging copy).

Includes: evaluation source, V2 protocols/configs/locks/results, tests,
figure scripts, manuscript. Excludes: .git, dataset payloads (license
review not done — hashes are recorded in the lock), VM logs, V1 artifacts.

Scrubbing: local VM paths (/202532803004), any github.com URLs, Windows
user paths are replaced before zipping. The build FAILS if post-scrub grep
still finds identifying patterns.
"""

import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
STAGE = os.path.join(HERE, "_supp_stage")
ZIP = os.path.join(HERE, "anonymous_supplementary.zip")

INCLUDE = [
    ("src/genome", "src/genome"),
    ("src/evaluator", "src/evaluator"),
    ("src/evolution", "src/evolution"),
    ("src/models", "src/models"),
    ("src/scripts/f1_run.py", "src/scripts/f1_run.py"),
    ("src/scripts/f1_preflight.py", "src/scripts/f1_preflight.py"),
    ("src/scripts/f2_run.py", "src/scripts/f2_run.py"),
    ("src/scripts/f2_freeze_lock.py", "src/scripts/f2_freeze_lock.py"),
    ("src/scripts/f2_statistics.py", "src/scripts/f2_statistics.py"),
    ("v2_quality/svamp_adapter.py", "v2_quality/svamp_adapter.py"),
    ("v2_quality/fasttrack", "v2_quality/fasttrack"),
    ("tests", "tests"),
    ("v2_quality/paper/manuscript.md", "v2_quality/paper/manuscript.md"),
    ("v2_quality/paper/make_figures.py", "v2_quality/paper/make_figures.py"),
    ("v2_quality/paper/figures", "v2_quality/paper/figures"),
]

EXCLUDE_DIRS = {"__pycache__", ".git", "data", "f1_results_caches"}
EXCLUDE_FILES = {"svamp_test.json", "svamp_train.json"}  # dataset payloads

SCRUB_PATTERNS = [
    (re.compile(r"/202532803004[^\s'\"`)']*"), "<ANON_VM_PATH>"),
    (re.compile(r"https?://github\.com/[^\s)'\"\]]+"), "<ANON_REPO_URL>"),
    (re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s'\"`)']+"), "<ANON_USER_PATH>"),
    (re.compile(r"[A-Za-z]:/Users/[^\s'\"`)']+"), "<ANON_USER_PATH>"),
]

FORBIDDEN = ["/202532803004", "github.com", "yujian", "于舰",
             "codex_mere", "10.10.24.107"]


def copy_tree():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    for src, dst in INCLUDE:
        s = os.path.join(REPO, src)
        d = os.path.join(STAGE, dst)
        if os.path.isdir(s):
            for root, dirs, files in os.walk(s):
                dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
                for f in files:
                    if f in EXCLUDE_FILES or f.endswith((".pyc", ".log")):
                        continue
                    sp = os.path.join(root, f)
                    rel = os.path.relpath(sp, s)
                    dp = os.path.join(d, rel)
                    os.makedirs(os.path.dirname(dp), exist_ok=True)
                    shutil.copy2(sp, dp)
        elif os.path.isfile(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
        else:
            print("MISSING:", src)


def scrub():
    n = 0
    for root, _, files in os.walk(STAGE):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith((".png", ".zip", ".pyc")):
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            orig = text
            for rx, rep in SCRUB_PATTERNS:
                text = rx.sub(rep, text)
            if text != orig:
                open(p, "w", encoding="utf-8").write(text)
                n += 1
    print("scrubbed files:", n)


def verify():
    bad = []
    for root, _, files in os.walk(STAGE):
        for f in files:
            if f.endswith((".png", ".zip", ".pyc")):
                continue
            p = os.path.join(root, f)
            try:
                text = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for pat in FORBIDDEN:
                if pat in text:
                    bad.append((os.path.relpath(p, STAGE), pat))
    return bad


def make_zip():
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(STAGE):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, STAGE))
    print("zip:", ZIP, os.path.getsize(ZIP), "bytes")


if __name__ == "__main__":
    copy_tree()
    scrub()
    bad = verify()
    if bad:
        print("FORBIDDEN CONTENT FOUND:")
        for rel, pat in bad[:20]:
            print(" ", rel, "->", pat)
        sys.exit(2)
    make_zip()
    shutil.rmtree(STAGE)
    print("OK")
