# PR26 原生上下文预算离线验证

2026-10-22；未调用模型、未访问 GitHub、未修改生产配置。实际输入是上一次 execution 3 的 93,531 字符提示，SHA256 `fc10a86b674992eccb67aaf3a4d62fb21370e935b05be7982e3419e250adef64`。通过原生 `buildReviewPrompt` 的占位模板提取各 section，逐字重建完全相等后，才进行预算比较；不是另写提示压缩器。

## 结论

否决 12,000：虽然输出 22,058 字符，却整段删除 `libreoffice_exporter.py` 的实际变更，原生明确标记 partial。

16,000 是下一次受控审查的可行配置候选：生成 32,129 字符、原生估计 15,277 输入 token，完整保留三个文件的全部 diff、原始需求、当前 operator 格式补充及固定输出合同。历史评论被去除，完整文件副本缩短。此结果不能证明模型下一次必定遵循格式或作出正确判断。

| 配置（均关闭 scout） | 字符 | 原生估算 token | 三文件完整 diff | 具体删减 |
| --- | ---: | ---: | --- | --- |
| 无绝对 cap | 82,926 | 42,133 | 是 | 仅不再加入 scout context |
| 12,000 cap | 22,058 | 10,056 | 否 | 评论及整文件副本删掉，生产 exporter diff 也删掉 |
| 16,000 cap | 32,129 | 15,277 | 是 | 评论删掉；整文件副本从估算 27,270 缩至 1,541 token |

原输入 section 长度：comments 1,199、originalTaskSpec 1,248、checks 164、diff 11,772、full fileContents 52,659、related scout context 10,161、combinedCommentBody 0、operator prompt 1,862 字符。单独关闭 scout 不能消除重复整文件。

## 原生入口与生效范围

配置 payload 已准备在 `deploy/propr/review-context-candidate.json`。通过已认证原生 `POST /api/config/settings`，正文为该文件，或现有 MCP `update_execution_settings` 的 settings 字段；复用其设置锁、验证、合并和发布机制，不覆盖完整 settings。无需新增网络端点或服务。实施前由主流程记录原三个字段，待 Issue32 终态、原生队列空闲后再应用并读回；本次没有执行这些写操作。

```json
{
  "settings": {
    "pr_review_context_enabled": false,
    "pr_review_max_context_tokens": 16000,
    "pr_review_context_budget_percent": 100
  }
}
```

源码（锁定上游 42931b1502eb03ac299f14e306811736fab51eb4，加已部署 policy6）：

- `src/jobs/reviewRuntimeSettings.ts:16–36`：每次 review 读取原生 settings，无本函数缓存；context_enabled false 只控制 scout。
- `src/jobs/prCommentReviewJob.ts:224–236,314–345,363–367`：在本次 review 开始加载设置；false 跳过 scout，将 max cap/percent 传给 reviewer。进行中的 Issue32 implementation 没有读取这些三个 review-only 字段；不会因此重启/取消其 Agent。仍等其结束后修改，以便清楚归属验收。
- `packages/shared/src/reviewContextBudget.ts:222–259`：对当前 OpenCode/qwen 路由采用保守未知模型容量，safe input 148,000、generic-calibrated tokenizer；100% 与 cap 取较小值，16k 生效。容量为 ProPR 本地回退估算，不是供应商已核实窗口/账单。
- `src/jobs/reviewPromptBuilder.ts:255–265,376–405,428–464`：依次裁剪 scout、comments、full files、diff、原需求、授权后续需求、review request、额外指令、operator prompt。提供 preparedDiff 时按完整文件选择；遗漏会记录文件与 partial。固定合同无法容纳则抛错，不静默越界。
- `src/jobs/prReviewRunner.ts:94–135`：预算包含原生 analysis safety suffix；日志记录 section token/遗漏原因。没有给 scout 增加第二层模型循环。
- `packages/api/mcp/toolsManagement.ts:65–69`、`packages/api/routes/configRoutes.ts:292–330`：原生读/更新入口与权限；`configRoutesSettings.ts:215–245` 验证字段。

16k 是全实例后续 review 设置，不仅 PR26；将来更大的 diff 仍可能 partial，必须按各次日志/结果判断，不能把本次三文件完整当作通用保证。关闭 scout 减少一次模型阶段，仍不把预算宣称为整体任务 600 秒或美元上限。

## 三个文件的一致性

以下 SHA256 是实际 prompt 中的整文件 diff section（含路径/统计头、diff fence）；16k 输出逐字包含相同整段，因而原文与保留段 hash 相同。不是仅检查文件名或 diff 摘要。

| 文件 | 原始和 16k 保留段 SHA256 |
| --- | --- |
| OntiCards_Api/Dockerfile | 99b8197f8336c2e326af69261b0e2ccb4bedf7287ccf0144f2d76f0909a23694 |
| OntiCards_Api/tests/test_governance_pdf_export.py | dad10f3cef18ef36df46129c22a9e1186915af5e1fddee7e06943fa9848be559 |
| OntiCards_Api/controllers/governance/libreoffice_exporter.py | ae732183b6810e9ad98da6feedf450b31f460cbdee58efaae70abce395662f00 |

证据：`evidence/pr26-review-context-offline.json`；可复验工具 `deploy/propr/probe_review_context_budget.mjs`。原始完整提示只留在服务器专用 data 文件（0600），不进入交付包/日志。工具只输出统计与 hash。首次辅助进程因 barrel import 打开 DB 句柄，完成计算后停止的是该独立辅助 PID；改用现成纯 suffix 模块后无模型复跑自然退出 0，结果一致。
