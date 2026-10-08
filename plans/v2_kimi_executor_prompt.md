# Kimi Code — NeuroEvoScientist V2 论文质量强化执行提示词

你是 NeuroEvoScientist 的 Executor（Kimi）。GPT 是 Planner。请立即接管 GitHub 项目，不需要我重复历史。

仓库：https://github.com/yujian777555/NeuroEvoScientist
分支：main

## 一、任务变更

用户明确表示“不着急投稿”。不要继续以 2026-10-12 ARR 截止日为工作目标。
从现在开始转入 V2 SCIENTIFIC QUALITY UPGRADE；目标是提高论文的公平性、可解释性、可验证性和潜在 CCF-B 投稿质量，而不是寻找能让结果好看的方法。
权威计划：plans/v2_quality_upgrade_plan.md。先完整阅读这个文件。
V1 已冻结：原 PDF 的 SHA-256 是 e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d。禁止覆盖 paper/arr2026/、deliverables/final_submission/、历史 results/、experiments/、锁定 configs/。
V1 的 +29.0pp / +16.7pp 只能表述为对当时四组 Direct+Full 固定基线的比较，绝不能把它解释成搜索算法本身的净贡献。

## 二、现在执行的唯一阶段：V2-0

1. git fetch origin && git checkout main && git pull --ff-only origin main；检查 HEAD、git status、status.json、v2 plan。
2. 从实际代码和锁定实验输出核对：
   - results/phase20_selection_lock.json
   - results/phase20_holdout_results.csv
   - results/phase20_statistics.json
   - configs/phase20_protocol.yaml
   - configs/phase20_structured_search_space.yaml
   - src/evaluator/ 与 src/evolution/
   - Phase-18 random-vs-evolution audit 真实文件
   - paper/phase21_tables.md 是否为错误遗留表格，以及它是否进入匿名 supplementary
3. 将所有已存在固定基线展开为 reasoning/memory/context/exemplar/cost 对照表；突出搜索配置 CoT vs fixed Direct 的混杂。核对 GSM8K 1.5B 的 A_gsm=0.5185、memory disabled=0.5193、best fixed=0.2289；7B A_gsm=0.8597、memory disabled=0.7342、best fixed=0.6932。若源文件不同，优先采用实际数据并解释。
4. 创建（不存在才新建）：
   - v2_quality/audit_baseline_fairness.md
   - v2_quality/protocol_v2.md
   - v2_quality/dataset_registry.json
   - v2_quality/run_matrix.csv
   - v2_quality/compute_budget.md
   - v2_quality/archival_discrepancies.md
   - v2_quality/gates/gate0_decision.md
5. Protocol 必须先规定假设、强 CoT-matched baselines、实际 prompt/output token 计费、配对统计、任务/模型及其精确版本、数据重复/泄漏检查、dev 和全新 independent confirmation 的分离、预先锁定的候选集合，以及最大 GPU 预算/停止条件。原来反复查看过的 Phase-20 holdout 不允许再次冒充 untouched confirm。若找不到独立确认集，则 V2 只能称 exploratory。
6. 将论文质量提升分成门禁：
   P0 strong fixed CoT and cost-matched baselines；
   P1 Memory×Reasoning×Context 受控交互；
   P2 structured-space ENSS vs budget-matched Random；
   P3 non-Qwen 家族的 zero-research transfer + independent confirmation；
   P4 V2 新论文、图、统计和合规终审。
   后续阶段必须遵守 plans/v2_quality_upgrade_plan.md 的门禁，不能预先开展。
7. 补最少量的 unit/integration tests 检查数据拆分、重复、版本、配置身份与缓存一致性；这一步不运行 GPU、不跑新 holdout、不重算历史实验。
8. 单独提交 V2-0 的新文档和必要测试。将 status.json 更新为 V2-0 GATE REVIEW（保留明确的 V1 FROZEN / ready-but-not-submitted 元数据），提交并 push origin/main。任何并发变化请先 fetch 检查，不覆盖 Planner 更新。

## 三、完成门槛

本轮只允许完成 V2-0。不要自动启动 V2-1 或 GPU 队列！
Gate 0 GO 条件：所有强基线定义明确且可实现；有可审计的独立确认集方案；新旧结果版本隔离；预算上限、统计和停止规则明确；必要测试通过。
如果任一条件不满足，给 NO-GO 和具体阻塞项，不要假装已完成。

## 四、固定报告格式

V2-0 AUDIT COMPLETE / BLOCKED
HEAD / origin-main SHA：
工作区：
新建/修改文件：
核实的基线表：
关键发现：
新的独立确认集是否可行（及来源/锁定证据）：
测试命令与结果：
实验重跑：NO
GPU 消耗：0
历史结果有无修改：NO
Gate0：GO / NO-GO
阻塞风险：
下一步建议：
GitHub commit 和文件链接：

最后停在 Gate 0，把报告发给我和 Planner 审核，再由 Planner 授权下一阶段。
