# Current Plan — Submission Phase (non-experimental)

实验已全部冻结（Phase-21 Stop Rule）。当前为非实验投稿准备阶段。

## Done（本阶段已完成）

- [x] 终版图表 6 张（`paper/figures/`，可由 `render_figures.py` 复现）
- [x] 参考文献 `paper/references.bib`（仅真实文献）
- [x] 可复现性附录 `paper/reproducibility_appendix.md`
- [x] 投稿清单与 venue 建议 `paper/submission_checklist.md`
- [x] Planner submission 提交核对一致

## Remaining（需 Planner/人工）

- [ ] manuscript 语言润色（母语级英文）
- [ ] LaTeX 排版（ARR acl.cls 或 TMLR 模板）
- [ ] 仓库公开就绪（README 更新、LICENSE）
- [ ] 内审 + 匿名化检查 + 提交

## 合规红线（全程有效）

无 ENSS>random、无 Mamba 收益、无 LoRA/QLoRA-as-context、无全主干 NAS、
QASPER-7B = backbone–prompt/extraction interaction、dev/holdout 结果分区、
记忆因果仅限同基因受控消融。
