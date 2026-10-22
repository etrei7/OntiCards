# 现有 CI 批次余额观察复用

2026-10-23。先核现有实现、实际失败与 New API 官方源码，沿用既有 n8n/普通账号，不新增额度或凭据服务。

已确认根因：原 `build_intake_admission.py` 将 `readModelBudget()` 的 Execute Command 放在每个 PR 子流程内，最多20个 PR 逐个登录。真实 02:37:28.043、02:38:03.841（北京时间）`POST /api/user/login` 返回429，分别早于 PR30/33 原生回执预算检查时间29/27ms；两行记 `budget_unverifiable`。现有服务日志只投影时间、路径、状态，见 `evidence/rootless-runtime/budget-existing-log-status.json`。这证明该次登录被限流，不证明累计请求来自哪个具体流程；不会将其他失败一概归网络或限流。

New API v1.0.0-rc.22 官方 [api-router.go](https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/router/api-router.go) 将 login 置于 CriticalRateLimit，/user/self 使用 UserAuth；[user.go](https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/controller/user.go) 提供原生 access_token/access_expires_at/session。当前专用账号受限文件只存 username/password/user_id，没有现成缓存会话。当前 `lease.mjs` 已验证普通账号id2/role1/group及读取余额，并在真正签发测试租约前再做新鲜额度检查。

选用现成 n8n Execute Command、Code、If、DataTable、Execute Workflow 调整节点位置：完整可信批次最多调用一次现有 readModelBudget；仅把无秘密余额 JSON 绑定该批 watermark/observed_at，传给其 PR 子流程。子流程校验年龄不超过300秒、不得来自其他批次、额度类型/原生零调用字段，然后保留既有 fresh PR scope 与 sticky receipt 流程。所有候选均已有回执或 dry-run 时，直接沿原生分流跳过余额读取。没有新调度、客户端、跨批缓存、token存储、refresh循环、配额重置或限流改动。

新增/改动代码均对应具体缺口：`build_intake_admission.py` 只移动原节点并绑定新鲜批次观察；既有 `test_intake_admission.mjs` 增加 stale/crossbatch/六项投影/全部consumed拒绝；已有隔离 `build_serial_loop_probe.py`/`run_serial_loop_probe.py` 复用原生localhost HTTP+DataTable计数器验证多item只发生一次传输，并复制生产Code/If门禁。模拟运输不冒充真实 NewAPI 请求或模型验收；真实自然poll单独取证。

历史恢复是独立运维动作：root 明确授权只核对已存在 PR30/33 两条 admission；`reconcile_budget_observation_once.py` 复用原生 DataTable/Execute Command，原state/detail完整保留并追加操作者“AI maintenance operation”及新余额观察，state变为 budget_exhausted，不伪装真人点击，不执行CI/模型、不签发测试token、不清预算。原独立余额probe定义恢复inactive。因原生模板入口及多item夹具曾失败，没有数据改变的失败记录保留服务器；成功回执 `budget-native-reconciliation.json` 是状态核对，不是新CI执行通过。


03:19 收尾：03:08仅更新既有 receiver/admission，父intake未变、无新Schedule。52项实际表达式验证、20项原生节点fixture通过（其中5项覆盖多PR只读1次、全旧回执0次、dry-run0次、过期/跨批次拒绝）。03:11自然receiver381及子382–387只有一批6PR，0 CI main/SSH/模型，0新登录；两条已核对的预算状态及原始429 detail不变。证据为 `batch-budget-expression-tests.json`、`batch-budget-deployment.json`、`batch-budget-natural-poll.json` 及 `evidence/n8n/intake-lifecycle-ci-native-probe.json`。状态核对原始前后值见 `budget-native-reconciliation.json`。执行壳soft-deleted且status仍running不是实际仍在执行，deletedAt也不当作完成时间。
