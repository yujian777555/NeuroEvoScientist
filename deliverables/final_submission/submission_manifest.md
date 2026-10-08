# ARR 2026 Submission Manifest

## Package

- **Main PDF**: `paper/arr2026/main.pdf`
  - SHA-256: `e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d`
  - Pages: 8（含 references；ARR 长文正文 8 页上限内，references 不计）
  - 构建源 commit：`8fa8945`（paper-only hotfix；含统计命名、QASPER-7B 措辞降级、
    TF-IDF 命名修正、pre-specified/commit-locked 措辞、GSM8K 种子稳定性修正、
    Figure 2 caption、MaAS + Evo-Memory 相关工作、目标精确定义、章节顺序调整）
  - 变更链：`9f91fbd` → `d1bfb55`（caption 澄清）→ 本次（paper-only hotfix）
- **Anonymous supplementary**: `paper/arr2026/anonymous_supplementary.zip`
  - 116 文件；身份泄漏扫描（编程验证）：零

## Gate 核验（全部通过）

- [x] 干净环境编译（tectonic，acl.sty review 模式）
- [x] 逐页目检（8/8 页）：无裁切、无 ??、无溢出
- [x] 引用核对（24/24 引用键均在 BibTeX 中有匹配条目；编译通过）
- [x] 正文无内部仓库路径
- [x] PDF 属性无作者身份元数据
- [x] LaTeX 源匿名 grep：零命中
- [x] 合规扫描（`src/scripts/compliance_scan.py`）：paper-facing 0 命中
- [x] 实验冻结（无进行中 GPU 任务）

## 待办（提交前人工项）

1. **OpenReview 档案**：每位作者完整档案 + ORCID + 冲突 + ACL Anthology 链接
2. **ARR 服务贡献者**：满足 2026 年 10 月可持续评审政策（行政性桌拒风险）
3. **LICENSE**：公开仓库前由 owner 选择（Apache-2.0 或 MIT）
4. 截止日前复查 ARR 官方日期页（防日期修正）

## 固定日期

- ARR 提交截止：2026-10-12
- 评审/服务注册截止：2026-10-14
- 作者回应：2026-11-24 至 11-30
- Meta-review：2026-12-17
- NAACL 2027 / COLING 2027 commitment：2026-12-23
