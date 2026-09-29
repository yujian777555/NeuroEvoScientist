# Current Plan — Submission Hardening (final gate)

依据 `plans/submission_hardening_plan.md` 执行。

## Blockers 状态

- [x] 1. manuscript_v3.md 完整英文论文稿
- [x] 2. related_work.md 真实引用重写（无 first 声明）
- [x] 3. method/experiments 双层协议同步
- [x] 4. fig2 真实 seed 分布 + fig6 紧凑空间标注
- [x] 5. 精确模型/数据/环境版本入附录
- [x] 6. README 重写为锁定定位
- [ ] 7. LICENSE —— **需仓库 owner 决定**（Executor 不擅自选择）
- [x] 8. 合规扫描（paper-facing 0 命中，`compliance_scan.py` 门禁可用）
- [ ] 9. venue 排版 + 投稿 PDF —— **需 Planner 选定 venue**（ARR acl.cls / TMLR）

## Final Gate 自查

- 实验冻结 ✓
- paper-facing 违禁措辞 0 ✓
- 测试 79 passed / 11 skipped ✓

## Next

等 owner 选 LICENSE、Planner 选 venue。其余就绪。
