# Venue 建议与投稿清单（Phase-21 后非实验阶段）

## 论文定位（已定）

任务条件化认知架构协同设计：受控研究 + 多目标审计 + 负结果报告。
强项：协议严谨性、负结果的科学价值、机制诊断（QASPER-7B）。
弱项（诚实）：单模型家族、紧凑空间、进化未胜随机。

## Venue 候选（按匹配度）

1. **ACL Rolling Review（ARR）/ ACL 主会** — agent 架构、prompt 策略、
   实证分析型论文的默认选项；负结果与审计协议在 ARR 评审中通常受认可。
2. **EMNLP Findings** — 对"严谨实证 + 负结果"友好；规模匹配。
3. **NeurIPS (main)** — 若强调搜索/优化视角与 Pareto 分析；竞争激烈，
   负结果叙事需要写得非常扎实。
4. **TMLR** — 滚动评审、允许方法学与审计型贡献；时间灵活。

建议路径：先 ARR 一轮；若时间不紧，TMLR 作为并行备选（两者政策允许时）。

## 投稿清单

### 内容完备性
- [x] manuscript_v2 骨架（`paper/manuscript_v2.md`）
- [x] abstract_v2（Planner 已校准数字与措辞）
- [x] limitations.md
- [x] 终版表格（`paper/phase21_tables.md`）
- [x] 终版图（`paper/figures/` 6 张，数据可复现渲染）
- [x] 参考文献（`paper/references.bib`，仅真实可查证文献）
- [x] 可复现性附录（`paper/reproducibility_appendix.md`）
- [x] claim 审计（`docs/claim_audit.md` + `docs/phase21_final_audit.md`）
- [ ] manuscript 语言润色（母语级英文，Planner 或人工）
- [ ] venue 模板排版（LaTeX，ARR acl.cls / TMLR style）

### 合规红线（提交前自查）
- [ ] 无 "ENSS 优于随机搜索" 措辞
- [ ] 无 "Mamba 提升性能" 措辞
- [ ] 无 LoRA/QLoRA-as-context 表述
- [ ] 无 "全主干神经架构自进化" 表述
- [ ] QASPER-7B 写为 backbone–prompt/extraction interaction
- [ ] dev 结果与 holdout 结果明确分区
- [ ] 记忆因果主张仅限同基因受控消融处

### 工程就绪
- [x] 实验冻结（无进行中 GPU 任务）
- [x] 全部测试通过（79+）
- [x] 证据-claim 映射完整
- [ ] 仓库公开可读性检查（README 更新、LICENSE）

### 时间线建议
- T+0–3 天：语言润色 + LaTeX 排版
- T+4–5 天：内审（对照本清单）+ 匿名化检查
- T+6–7 天：提交
