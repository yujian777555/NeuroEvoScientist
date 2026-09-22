"""Reasoning-gene prompt construction (Phase-17/20 shared helper).

The reasoning gene changes the instruction template; Phase-20 sub-genes
change it further for real:
- reasoning_depth (cot/planner): explicit step count instruction;
- verifier_passes (verify): number of verification passes requested.
"""

_TEMPLATES = {
    "direct": "Question: {q}\n{hint}",
    "cot": "Question: {q}\nLet's think step by step{depth}. {hint}",
    "verify": ("Question: {q}\nSolve it, then verify your solution"
               "{passes}. {hint}"),
    "planner": ("Question: {q}\nFirst write a short solution plan{depth}, "
                "then execute it. {hint}"),
}


def reasoning_prompt(genome, question, answer_hint):
    strategy = getattr(genome, "reasoning", "direct")
    template = _TEMPLATES.get(strategy, _TEMPLATES["direct"])

    depth = getattr(genome, "reasoning_depth", None)
    if strategy in ("cot", "planner") and depth:
        depth_txt = " in exactly %d short steps" % depth
    else:
        depth_txt = ""

    passes = getattr(genome, "verifier_passes", None)
    if strategy == "verify" and passes:
        passes_txt = " %d times" % passes
    else:
        passes_txt = " step by step"

    return template.format(q=question, hint=answer_hint,
                           depth=depth_txt, passes=passes_txt)
