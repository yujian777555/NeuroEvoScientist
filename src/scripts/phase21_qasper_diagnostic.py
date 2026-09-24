"""Phase-21 Task 3: QASPER-7B collapse diagnosis (diagnostic-only).

Frozen protocol: fixed small QASPER item set (items[50:62], holdout slice),
representative configs x 2 backbones. No tuning, no prompt changes.

Per item we persist:
- raw generated text (truncated), extracted final answer;
- marker (####) compliance; output token length (word proxy);
- empty/degenerate-output flag;
- LongBench-compatible normalized F1 on extracted answer;
- normalized F1 on whole continuation (diagnostic only);
- prompt length (words), exemplar count, input context budget.

Failure-mode classification per config/backbone:
1. answer-extraction/formatting mismatch;
2. exemplar overload / context distraction;
3. generation degeneration;
4. genuine answer-quality degradation;
5. mixed/unclear.

Writes results/phase21_qasper7b_diagnostic.json.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome
from models.builder import build_agent
from evaluator.qasper import QasperEvaluator, qa_f1

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
LOCK = os.path.join(_REPO, "results", "phase20_selection_lock.json")
OUT = os.path.join(_REPO, "results", "phase21_qasper7b_diagnostic.json")

DIAG_CONFIGS = ["A_qasper", "A_gsm", "no_memory", "fixed_retrieval"]
DIAG_ITEMS = list(range(50, 62))  # fixed QASPER holdout items


def classify(rows):
    """Failure mode per (config, backbone) group of item rows."""
    n = len(rows)
    if not n:
        return "unknown"
    no_marker = sum(1 for r in rows if not r["marker_present"])
    empty = sum(1 for r in rows if r["empty_output"])
    whole_better = sum(
        1 for r in rows if r["f1_whole"] > r["f1_extracted"] + 0.15)
    if empty / n > 0.5:
        return "generation_degeneration"
    if no_marker / n > 0.5:
        return "answer_extraction_mismatch"
    if whole_better / n > 0.5:
        return "extraction_loss_or_distraction"
    mean_f1 = sum(r["f1_extracted"] for r in rows) / n
    if mean_f1 < 0.05:
        return "genuine_quality_degradation_or_mixed"
    return "mostly_functional"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--data-path", required=True)
    args = parser.parse_args()

    lock = json.load(open(LOCK))
    cfgs = {c["name"]: c for c in lock["configurations"]
            if c["name"] in DIAG_CONFIGS}

    from evaluator.backends import QwenBackend, HFTransformersBackend
    if "qwen" in args.model.lower():
        backend = QwenBackend(args.model, device=args.device,
                              batch_size=args.batch_size)
    else:
        backend = HFTransformersBackend(args.model, device=args.device,
                                        batch_size=args.batch_size)

    evaluator = QasperEvaluator(
        backend=backend, start=50, limit=12, data_path=args.data_path,
        cache_path=None,  # diagnostic: always fresh inference
    )
    samples = evaluator.load_samples()
    model_tag = os.path.basename(str(args.model))

    report = {"model": model_tag, "configs": {}, "items": []}
    for name in DIAG_CONFIGS:
        cfg = cfgs[name]
        genome = StructuredGenome(**cfg["genome"]).normalize()
        disable_memory = cfg.get("disable_memory", False)
        evaluator.disable_memory = disable_memory

        memory = None
        if not disable_memory:
            memory = evaluator.build_memory_bank(genome)
        k = genome.exemplar_count
        prompts = []
        for s in samples:
            ex = None if (memory is None or k == 0) else memory.recall(
                s["input"], k=k)
            prompts.append(evaluator.build_prompt(s, genome, ex))

        outputs = backend.batch_generate(prompts, genome)
        rows = []
        for i, (sample, prompt, output) in enumerate(
                zip(samples, prompts, outputs)):
            gold = sample["answers"][0] if sample["answers"] else ""
            marker = "####" in output
            extracted = output.split("####")[-1].strip() if marker \
                else output.strip()
            row = {
                "item_index": DIAG_ITEMS[i],
                "raw_output": output[:600],
                "extracted_answer": extracted[:200],
                "marker_present": marker,
                "output_words": len(output.split()),
                "empty_output": len(output.strip()) < 3,
                "f1_extracted": round(qa_f1(extracted, gold), 4),
                "f1_whole": round(qa_f1(output, gold), 4),
                "prompt_words": len(prompt.split()),
                "exemplar_count": k,
                "input_context_budget": genome.input_context_budget,
            }
            rows.append(row)
            report["items"].append({"config": name, **row})
        report["configs"][name] = {
            "n_items": len(rows),
            "failure_mode": classify(rows),
            "mean_f1_extracted": round(
                sum(r["f1_extracted"] for r in rows) / max(1, len(rows)), 4),
            "mean_f1_whole": round(
                sum(r["f1_whole"] for r in rows) / max(1, len(rows)), 4),
            "marker_compliance": round(
                sum(r["marker_present"] for r in rows) / max(1, len(rows)), 3),
            "mean_output_words": round(
                sum(r["output_words"] for r in rows) / max(1, len(rows)), 1),
            "mean_prompt_words": round(
                sum(r["prompt_words"] for r in rows) / max(1, len(rows)), 1),
        }
        print("diag done:", name, report["configs"][name]["failure_mode"])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("DIAG_DONE ->", OUT)


if __name__ == "__main__":
    main()
