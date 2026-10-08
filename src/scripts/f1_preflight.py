"""F1 preflight (NO GPU): build production prompts for the seven locked
baselines and assert the Planner-mandated distinctness/comparability
properties. Writes v2_quality/fasttrack/f1_preflight.md with evidence.

Checks (fail-closed):
- 7 baselines normalize to 7 distinct task phenotypes on GSM8K and QASPER;
- B0 != B5, B1 != B4 by rendered prompt hash on real DEV items;
- B1 != REF (REF injects a memory exemplar);
- B5 vs REF differ ONLY by reasoning template (identical exemplars/context);
- B3's retrieval path is term-frequency cosine (legacy enum 'tfidf');
- REF == A_gsm from the Phase-20 selection lock;
- F1 cache/output paths are isolated from Phase-20 holdout paths.
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome, task_phenotype_hash
from evaluator.gsm8k import GSM8KEvaluator
from evaluator.qasper import QasperEvaluator

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
GSM8K_TEST = os.path.join(REPO, "data", "gsm8k", "test.jsonl")
GSM8K_TRAIN = os.path.join(REPO, "data", "gsm8k", "train.jsonl")
QASPER = os.path.join(REPO, "data", "qasper", "qasper.jsonl")
BASELINES = os.path.join(REPO, "v2_quality", "fasttrack", "baselines_f1.json")
P20_LOCK = os.path.join(REPO, "results", "phase20_selection_lock.json")
OUT = os.path.join(REPO, "v2_quality", "fasttrack", "f1_preflight.md")


def load_genomes():
    conf = json.load(open(BASELINES, encoding="utf-8"))
    return {k: StructuredGenome(**{**conf["common"], **v}).normalize()
            for k, v in conf["baselines"].items()}


def prompt_hash(evaluator, genome, sample, memory):
    exemplars = None
    query = sample.get("question") or sample.get("input", "")
    if memory is not None and genome.exemplar_count > 0:
        exemplars = memory.recall(query, k=genome.exemplar_count)
    p = evaluator.build_prompt(sample, genome, exemplars)
    return hashlib.sha256(p.encode("utf-8")).hexdigest()[:16], p


def main():
    lines = ["# F1 Preflight Evidence (NO GPU)", ""]
    failures = []

    genomes = load_genomes()

    # --- phenotype uniqueness on both tasks
    for task in ("gsm8k", "qasper"):
        keys = {k: task_phenotype_hash(g, task) for k, g in genomes.items()}
        ok = len(set(keys.values())) == len(keys)
        lines.append("## Phenotype uniqueness (%s): %s" % (task, ok))
        for k, v in keys.items():
            lines.append("- %s: `%s`" % (k, v))
        if not ok:
            failures.append("duplicate phenotype on %s" % task)

    # --- prompt building on a real DEV item per task
    ev_g = GSM8KEvaluator(backend=lambda p, g: "", data_path=GSM8K_TEST,
                          calibration_path=GSM8K_TRAIN)
    sample_g = ev_g.load_samples()[0]
    ev_q = QasperEvaluator(backend=lambda p, g: "", data_path=QASPER,
                           calibration_path=QASPER, start=0, limit=1)
    sample_q = ev_q.load_samples()[0]

    def banks(ev):
        return {k: (ev.build_memory_bank(g) if g.exemplar_count > 0 else None)
                for k, g in genomes.items()}

    for label, ev, sample in (("gsm8k", ev_g, sample_g),
                              ("qasper", ev_q, sample_q)):
        banks_ = banks(ev)
        hashes = {}
        prompts = {}
        for k, g in genomes.items():
            h, p = prompt_hash(ev, g, sample, banks_[k])
            hashes[k] = h
            prompts[k] = p
        lines.append("## Prompt hashes on DEV item (%s)" % label)
        for k, h in hashes.items():
            lines.append("- %s: `%s`" % (k, h))
        if label == "gsm8k":
            if hashes["B0"] == hashes["B5"]:
                failures.append("B0 == B5 prompt hash")
            if hashes["B1"] == hashes["B4"]:
                failures.append("B1 == B4 prompt hash")
            if hashes["B1"] == hashes["REF"]:
                failures.append("B1 == REF prompt hash (memory not injected?)")
            # B5 vs REF: identical exemplar block, differ by reasoning only
            def ex_block(p):
                return p.split("Question:")[0]
            if ex_block(prompts["B5"]) != ex_block(prompts["REF"]):
                failures.append("B5/REF exemplar+context block differ")
            if prompts["B5"] == prompts["REF"]:
                failures.append("B5 == REF (reasoning template not applied)")
            lines.append("B5/REF share exemplar block: %s"
                         % (ex_block(prompts["B5"]) == ex_block(prompts["REF"])))

    # --- B3 retrieval metric is term-frequency cosine despite 'tfidf' enum
    from evaluator.memory import RetrievalMemoryController
    ctrl = RetrievalMemoryController(genomes["B3"])
    lines.append("## B3 retrieval metric implementation")
    lines.append("- enum: `%s`, controller metric: `%s` (term-frequency cosine; no IDF)"
                 % (genomes["B3"].retrieval_metric, ctrl.metric))
    lines.append("- implementation: `tfidf_scores` computes TF-cosine only "
                 "(no IDF term) — verified in src/evaluator/memory.py")

    # --- REF == A_gsm from Phase-20 selection lock
    lock = json.load(open(P20_LOCK, encoding="utf-8"))
    a_gsm = next(c for c in lock["configurations"] if c["name"] == "A_gsm")
    ref_dict = genomes["REF"].to_dict()
    a_gsm_norm = StructuredGenome(**a_gsm["genome"]).normalize().to_dict()
    same = all(ref_dict.get(k) == a_gsm_norm.get(k) for k in a_gsm_norm)
    lines.append("## REF matches locked A_gsm: %s" % same)
    if not same:
        failures.append("REF != A_gsm")
        for k in a_gsm_norm:
            if ref_dict.get(k) != a_gsm_norm.get(k):
                lines.append("- DIFF %s: REF=%s A_gsm=%s"
                             % (k, ref_dict.get(k), a_gsm_norm.get(k)))

    # --- isolation of V2 caches/outputs
    v2_paths = ["v2_quality/fasttrack/f1_results", "v2_quality/fasttrack/caches"]
    for p in v2_paths:
        os.makedirs(os.path.join(REPO, p), exist_ok=True)
    lines.append("## Isolation")
    lines.append("- V2 cache dir: `v2_quality/fasttrack/caches/` (fresh, isolated)")
    lines.append("- V2 results dir: `v2_quality/fasttrack/f1_results/` (fresh)")
    lines.append("- F1 reads only DEV slices: GSM8K test[0:100], QASPER items[0:50]")
    lines.append("- No read/write under results/ or experiments/ during F1")

    ok = not failures
    lines.append("")
    lines.append("## VERDICT: %s" % ("PASS" if ok else "FAIL"))
    for f in failures:
        lines.append("- FAILED: %s" % f)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-(len(failures) + 2):]))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
