# 原生修复 PR 发布的两个实证缺口

2026-10-22，固定 ProPR 0.9.0 / 42931b1502eb03ac299f14e306811736fab51eb4，Apache-2.0；当前 policy7。

真实 Issue32 原生任务已产生 PR33（head 86fda6805385a5bcfb9e09e3e0139a83aa184ac2，base c8e3dfee68d398a37842fc332f73af40a56f02a7）。GitHub GET 发现 draft=false，描述把缺失价格时的内部零值显示为 API cost $0.00。Agent 没有 pytest/pip，不能把任务 completed 当测试通过。

已检查原生 `createPullRequest`、`generateCompletionCommentParts`、`prFormatters` 和 `.propr/pr-template.md` 扩展点，并核对 [GitHub 官方创建 PR 参数](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request)、[固定上游模板实现](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/packages/core/src/workflow/prTemplate.ts)。模板能调整正文，不能改变硬编码 draft=false；将模板写入 main 也不符合人工最终合并约定。上游成本模板把缺失值转为零，必须保留未知而非包装成账单。

最小扩展：复用已有受信 `humanMergeOnly()` 部署策略，原生创建参数改为 Draft；在此策略下只有已提供的正数成本可显示，缺失/内部默认零改为 null/unknown，禁用 OpenRouter 估价冒充本供应商实报；现有模板接受 null。非维护模式保留原行为。无需新发布器、认证或计费服务。

验收：直接调用现有生产创建函数捕获 Draft API 参数；真实生产正文/模板函数覆盖未知、默认零、正数费用及维护模式开关。完整编译、现有相关测试在 kol-stage2 执行。真实 PR33 已用原生 App 转 Draft 并改正说明，旧 body 仅留服务器受限档案、原 SHA 留回执。此记录不是新补丁已经部署的证明。
