# Abstract v1（Phase-19 Task 8；只用可辩护 claim）

LLM agents are typically deployed with a fixed, manually designed cognitive
architecture. We ask whether the per-task configuration of an agent's
episodic memory policy, reasoning strategy, and context policy can be
discovered automatically, above a frozen backbone, under multiple
capability–cost objectives.

We present NeuroEvoScientist, a task-conditioned cognitive architecture
co-design framework that evolutionary searches a 48-configuration space of
real, activated genes — four episodic memory policies (including a trainable
Mamba-2 substrate), four reasoning strategies, and three context policies —
with leakage-safe calibration splits, raw multi-objective logging, and a
pre-registered holdout protocol.

On GSM8K, automatically discovered configurations substantially outperform
simple fixed baselines on untouched held-out items (e.g., +33.8 percentage
points over the strongest fixed baseline at 1.5B scale; paired bootstrap and
McNemar confirm significance). On PubMedQA, discovered configurations yield
competitive capability–cost tradeoffs rather than universal capability
superiority; we report this asymmetry explicitly. The two tasks favor
different gene distributions across seeds, and own-task configurations occupy
better positions on the held-out capability–cost frontier (e.g., −41% prompt
tokens at equal-or-better capability on GSM8K). These preferences transfer
directionally to a 4.7× larger backbone without re-searching.

Equally important are the audit findings: within this compact space,
equal-budget evolutionary search does not outperform random search
(20 seeds × 4 budgets), and a real Mamba-2 memory substrate, though valid and
trainable, is not selected by evolution — we keep both as negative results.
Removing episodic memory degrades held-out capability by up to 11 points,
with the degradation growing on the larger backbone.

Our artifacts — complete architecture landscapes, per-item predictions,
paired statistics, and a claim-by-claim audit — are released to make
agent-architecture research reproducible and falsifiable.

（合规自查：摘要未声称 ENSS 优于随机搜索；未声称 Mamba 收益；
数字均可溯源至 results/phase19_*、results/phase18_*。）
