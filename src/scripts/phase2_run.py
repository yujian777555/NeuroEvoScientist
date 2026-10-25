"""Phase-2 pilot command-line entry point.

Examples (VM):
  PYTHONPATH=src python src/scripts/phase2_run.py preflight --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py infer-stage1 --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py infer-stage2 --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py analyze --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py null-smoke --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py null-full --repo . --out phase2/pilot
  PYTHONPATH=src python src/scripts/phase2_run.py combine --repo . --out phase2/pilot
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phase2 import runner  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=[
        "preflight", "infer-stage1", "select", "infer-stage2", "analyze",
        "null-smoke", "null-full", "combine"])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1000)
    parser.add_argument("--timeout-sec", type=float, default=14400)
    args = parser.parse_args()
    repo = os.path.abspath(args.repo)
    out = os.path.abspath(args.out)

    if args.command == "preflight":
        result = runner.run_preflight(repo, out)
    elif args.command == "infer-stage1":
        result = runner.run_inference(repo, out, "stage1")
        result = {"status": result.status,
                  "feature_set": result.feature_set,
                  "manifest": result.manifest}
    elif args.command == "select":
        result = runner.select_frozen(repo, out)
        result = {"status": result.status,
                  "feature_set": result.feature_set}
    elif args.command == "infer-stage2":
        result = runner.run_inference(repo, out, "leval")
        result = {"status": result.status,
                  "feature_set": result.feature_set,
                  "manifest": result.manifest}
    elif args.command == "analyze":
        result = runner.run_analysis(repo, out)
        result = {"status": result.get("status")}
    elif args.command == "null-smoke":
        result = runner.run_null(repo, out, start=args.start,
                                 end=args.end if args.end != 1000 else 2,
                                 smoke=True, timeout_sec=args.timeout_sec)
    elif args.command == "null-full":
        result = runner.run_null(repo, out, start=args.start, end=args.end,
                                 smoke=False, timeout_sec=args.timeout_sec)
    else:
        result = runner.combine_final(out)
        result = {"status": result.get("status")}
    print("PHASE2_RESULT", result.get("status"))
    print("OUT", out)


if __name__ == "__main__":
    main()
