# 既有完整 PR intake 接入原生 CI（实施前登记）

2026-10-23 02:08。缺口：固定 PR26 已从 n8n→受限 SSH→rootless→真实业务通过，但新 PR/新 head/base 尚未从现有事件采集进入 CI。已有 Checkwatch 只使旧证据失效，不能代替新版本验证。

复用现有18128 `onticardsPersistentReadOnlyV1` 的完整分页、水位、`onticards_intake_threads_v1` 和原生 Execute Workflow/HTTP Request；在成功提交完整水位且 installation token 撤销后投递安全 PR snapshot。18132复用现有 Header Auth、原生 DataTable `onticards_ci_receipts_v1`、`onticardsPreviewRevisionV1` 与 `onticardsFixedPreviewV1`。不新建 Schedule、GitHub列表采集器、队列或runner。

18132只接受单仓完整snapshot，并再次用既有App只读子流程核同仓codex分支/main及精确head/base。外部fork、策略范围外版本转人工。已批准`preview-v1`是固定API7/真实模型PW3与合成单表业务，不冒充PR33并发专项或lint/迁移全验。旧Checks仍由原生5minwatch按原head/base失效；新head/base有新的原生receipt身份，需要自己的验证，不能继承success。

幂等复用同一DataTable：现有CI主receipt保持原键；派发admission用有明确前缀的同一版本键，在外部调用前记录。running/failed/complete/unknown不自动重预算；余额不足记录`budget_exhausted`。这不是新的调度队列：没有后台重试器、任务执行循环或独立时钟。人工配置额度后仍需审阅并显式恢复旧受阻版本；新版本自然进入新准入判断。

当前普通NewAPI账户剩15445，低于45000；复用原生普通账户login/self仅读余额，0 token mint/0 provider。此次验收只允许真实只读发现、原生dry-run、去重与余额拒绝，不再次调用供应商。原生实例只导入专用HeaderAuth凭据，原值从受信文件导入，不打印/入PR/传PR容器。HeaderAuth只使可信intake能提交版本候选，不授予它GitHub写权限。

来源：已验证的n8n2.42.7原生DataTable/Execute Workflow/HTTP节点（`deploy/n8n/build_persistent_polling.py`）；[n8n子工作流](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow/)、[DataTable](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.datatable/)、[NewAPI原生token管理](https://doc.newapi.pro/en/api/fei-token-management/)。本文件只登记方案；后续实证单列，不将候选当部署成功。
