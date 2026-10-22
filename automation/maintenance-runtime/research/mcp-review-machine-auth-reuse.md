# 原生 PR 审查机器接入：复用与边界审查

初始审查基线：ProPR 0.9.0，上游 `42931b1502eb03ac299f14e306811736fab51eb4`；policy12 tree `b3dd9a914e431b15b41febbf97211d736e6428fd`。以下保留初始只读研究与当时缺口，文末记录 policy13 修复；实际部署状态以对应 deployment receipt 为准。初始独立研究未调用模型、发送 GitHub 评论或签发凭据。后续受限机器接线的真实无模型验证由 CI 交付清单中的 receipt 单独记录。

## 已有能力与实际缺口

| 需求 | 已有实现与位置 | 验证结论 |
|---|---|---|
| 固定 PR 审查 | `packages/api/mcp/toolsPullRequests.ts:226` 的 `review_pull_request` | scope 为 review；支持 expectedHead、原生 mutation idempotencyKey；复用 `/review` 评论与现有 intake/worker，未另建 Agent |
| 可撤销机器委托 | `mcp/oauth.ts:95` 的 issueDelegatedGrant、`:186` 的 revokeGrant | 支持受信 first-party 短期 grant；只授 read/review 和单仓，不返回 GitHub token。它没有 refresh token，不能当长期 OAuth credential |
| 当前用户鉴权 | `mcp/agentRunGrants.ts:82`、`githubUserGrantService.ts`、`mcp/policy.ts:33` | 可复用已存在的 active GitHub user grant；每次 MCP 调用重新核 GitHub 身份、实例权限与仓库权限，不能伪造用户 consent 或伪 AgentRun |
| 标准长期 OAuth | `mcp/oauth.ts:19,56,147,155` | code 60秒、access 15分钟、grant 30天；refresh 轮换，重放撤销 grant。此路径原生可用，但仍需真实浏览器 consent |
| n8n OAuth 客户端 | 现场已安装 n8n 2.42.7 的 `McpOAuth2Api.credentials.js`、`oauth.service.js:583–767`、`oauth2-credential.controller.js:50–96` | 原生 MCP OAuth2 credential 支持 DCR、S256 PKCE、resource 在授权/兑换/刷新间保留并加密存储，无需自写 token broker |
| 用户既有 HTTP 管理入口 | `mcp/browser.ts:156–169` | GET consent 可复用 session，但 POST 要求 Origin 严格等于 MCP HTTPS canonical origin。HTTP18123 页面不能向 HTTPS127 listener 完成真实同源 consent；不得伪 Origin 或绕 CA 警告 |
| 现成内部 system-task 入口 | `routes/agentRunInternalRoutes.ts:19,27,100–119` | 仅真实 running/acting AgentRun 可申请对应 phase grant；report 只有 read、action 只有 read/plan/execute。没有独立 review 入口；不得为此伪造 run 或扩大 phase scopes |

用户选择 HTTP，当前桌面不信任已有 CA，本轮不以改变桌面全局信任或绕证书警告作为接入前提；长期浏览器 OAuth 保留为可选安装方式。本轮缺口是**既有可信 n8n 到原生 first-party review 动作之间的机器接线**，不是缺少审查、调度、授权或令牌服务。

父任务选择的最小部署适配是已有 OpenSSH `restrict`/固定 ForceCommand 模式：仅可信 n8n 持专用 key；它只能向受信宿主提交一个固定 review 请求。宿主在现有 ProPR 上下文内解析 active user grant、签发短委托、调用原生 MCP、finally 撤销。n8n、PR 与 Agent 都不获得 ProPR DB、Docker socket、PEM 或 MCP bearer。此方案使用已有宿主信任边界，不能描述成无特权运行。

## 必须沿用的持久幂等边界

`mcp/operations.ts:125–150` 的唯一身份是 `(owner_id, grant_id, idempotency_key)`。短委托每次创建新 grant，**相同字符串 key 并不足以跨 grant 去重**。

固定宿主动作必须先持有原生 flock，再按受信固定 owner/repository/tool 和确定性 key 读取已有 `mcp_operations`，用原生 `canonical`/`digest` 比较完整 tool+args 的 payload hash。已有 accepted、unknown、posted、failed、completed 等任何记录都应返回既有安全状态或转人工，不再创建评论；参数改变同 key 必须拒绝。只有确实没有旧 operation 才可调用原生 mutation。当前候选为复用原生身份及仓库鉴权，会先签短 grant、只读核验，再查询跨 grant operation；无论是否已有记录都 finally 撤销。原生 operation insert 在 GitHub POST 之前，进程在 POST 后丢响应仍保留 unknown/accepted 证据，不通过删除记录恢复预算。

本次源码检索未发现 `mcp_operations` 的周期性 30天删除入口；普通 Task 清理不是这张表。持久化仍以 DB 未被管理员删除/重置为前提。n8n 既有 DataTable 准入历史同样保留。身份为 `(repository, PR, head, base)`：新 head 或 base 是新版本，可有独立验收；原版本的 failed/unknown 不因过期、grant、队列清理或 model 改变重新消费预算。

## 撤销与后续执行

`revokeGrant` 只写 grant.revoked=true，不删除评论或取消 job。`review_pull_request` 返回 posted 只证明 GitHub 评论已创建；原生 `prCommentPolling.ts:291` 以 commentID 去重并检查 assignment，`processPullRequestCommentJob.ts:187` 重新使用安装身份的 getAuthenticatedOctokit。后续 review 不依赖已撤销的 MCP bearer，因此在原生 mutation 返回后 finally revoke 不妨碍已授权的评论接单。

policy12 上游执行仍要求 repo enabled、所需 AI 标签、允许的评论者和活动的 daemon/worker；policy13 对明确获授权的纯审查提供下述严格无标签例外，普通修复仍受标签限制。不能将 posted 当作 queued 或 completed。撤销后的 token 不能继续调用 get_operation；状态可由受信宿主投影既有安全 operation/task 字段，或由已有 n8n 跟踪流程读取，不得为查询状态重新发布 review。

原生 strict schema 支持 expectedHead，不接受 expectedBase。宿主须在调用前独立读取当前 base SHA；持续 CI/Check 发布前再核 live head/base。原生单模型默认路径中的 PR read 和评论 POST 并非 GitHub 原子事务，不能承诺两 SHA 被锁定，也不能把异步 worker 读取的后续 head 混称为请求中的 head。

## 独立审查发现的恢复写入边界

普通 polling 生成的 review job 没有 `ultrafixMeta`；`prCommentReviewJob.ts:129` 在无该字段时直接跳过 Ultrafix continuation，`processPullRequestCommentJob.ts:452` 的 review 分支本身不进入代码执行及推送。然而同函数 `:415` 先执行 `gatePredecessorHandoff`，`:442` 先执行 `recoverPendingPublication`。前者会通过 `followupHandoffRecovery.ts:261` 恢复旧 worktree，后者通过 `prPublicationRecovery.ts:100` 的 `publication.prepare` 恢复旧 publication；两者都可能在新 review 开始前发布先前实施任务的代码。

因此初始 policy12 审查发现一项明确缺口：须在持有原生 PR lease 的位置、两项恢复之前拒绝或跳过写入型恢复。固定 helper 的只读预检不能排除评论排队后新增 checkpoint 的竞争。此项随后获授权以 policy13 的局部原生入口修复，不把提示词“不修改代码”算作技术保证。

独立无模型验证：固定 policy12 测试镜像在 `--network none`、无凭据挂载下运行原生 OAuth、operations、agentRunGrants 三文件 **52/52、0 skip**；当前适配 receipt 测试 **13/13、0 skip**，覆盖嵌套原生 envelope、未知提交、撤销未知及错误不假称成功。安全记录：`evidence/mcp-native-independent-review.json`。这些不是新接线已部署或真实自动审查成功的证明。

## 无模型验收点

1. SSH 正确固定命令可达；任意 shell、额外参数、forward、PTY、user rc、危险环境注入拒绝。输入有界且仅允许固定单仓、整数 PR、40hex head/base、固定模式；用户输入不拼接 shell。
2. wrong repo/head/base/未知键/超4KiB/非法类型均在签发 grant 或写 GitHub 前拒绝。用真实 live read 核当前 head/base，不能把输入中的 SHA 自证为真。
3. 两个相同请求并发时只一次进入原生 mutation；restart 后旧 accepted/unknown/failed/posted 同样不重发；新 grant 不使旧 key 复活；改变 payload 用同 key 拒绝。
4. 用原生 fixture mock transport 检验 POST 后丢响应→unknown→再次请求不 POST；不要用公开评论制造故障。
5. 成功、预条件失败、MCP transport timeout 都 finally revoke；中途 SIGKILL 时短 TTL 是后备，不能宣称 finally 一定运行。revocation 失败必须作为失败状态报告。
6. 原生短 grant 在 read/review 范围内，execute/merge/deploy/manage 被拒；不把 secret、token、完整环境或原始上游错误写入 n8n execution 或公开证据。

官方来源：n8n [MCP credentials](https://docs.n8n.io/integrations/builtin/credentials/mcp)、[HTTP OAuth2 credentials](https://docs.n8n.io/integrations/builtin/credentials/httprequest/#using-oauth2)；OpenSSH [ForceCommand 配置](https://man.openbsd.org/sshd_config#ForceCommand)、[authorized_keys 限制](https://man.openbsd.org/sshd#AUTHORIZED_KEYS_FILE_FORMAT)。精确行为以本次锁定 ProPR 源码和现场 n8n 2.42.7 安装文件读取为准。

## policy13 原生入口的最小修复

改动仅涉及 5 个生产文件与 5 个测试文件，完整补丁及逐文件 SHA 见 `evidence/propr-policy13-patch-validation.json`。没有增加依赖、数据表、队列、模型循环或新认证体系。

- 复用现有 PR lease、`humanMergeOnly` 和 typed `commandMode`：维护模式中不含内部 `ultrafixMeta` 的纯 review 跳过 predecessor handoff、pending publication 和旧循环停止入口。保留旧记录、worktree 与预算；原生内部 Ultrafix review、普通 fix 和未启维护模式保持原行为。正文 JSON 不能生成内部 meta。
- 无标签例外同时要求非空白名单、GitHub 实时评论的精确 login、原生作者过滤、原生 assignment/权限 gate、明确 `/review` 及最初入队命令一致。复用 `parseSlashCommand`/`buildCommandMeta`；原生首行被剥离的 payload 由 `commandCommentId` 绑定对应 typed metadata。对照原始队列正文，防止既有校验刷新 edited body 后形成自授权。白名单 `user` 不隐式授权 `user[bot]`。不增加 AI 标签，不放开 fix，不以 PR 正文或可伪造 marker 授权。
- 收集上下文末尾与发布 findings 前复用现有 GitHub GET，要求实际 head/base 两个完整 SHA 均未变化，且 PR 未关闭。实际收集的 base 同 head 写入原生 review marker/Task history。变化或读取失败沿原生错误通知和 Task FAILED 出口，保留已发生的 raw response、tokens、耗时与 session，不自动补跑、不产生伪 findings。

真实 Redis lease 与真实 SQLite 的无模型 fixture 核对旧 handoff/continuation 每个字段及预算不变、竞争任务无法跨 lease、内部 Ultrafix 兼容、无标签可信命令可达、未授权/编辑/错误 commentId 拒绝。真实 runner 与现有 Task finalizer fixture 核对 head/base 变化均 FAILED，原用量仍被记录。独立审查保留了 `[bot]` 归一化和 edited-body 两个红证据，后续修复与完整镜像验证分开记录，不能把 fixture 说成新 PR 已真实审查成功。

最终源码已于打包机完成完整编译及 **964/964、0 skip** 测试执行：既有 679、新只读授权/lease 20、相关 review/handoff/cancel/MCP 265。完整 tree 为 `0af2178f1461819a893d6705a0e23dcad6330595`，full patch SHA256 `91c2d151fd95ff6fcd634fc73d553a6fcc84674f481b3a7ce7b48eb11ea0273b`，registry digest `sha256:3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879`。安全计数、初始红证据与日志哈希见 `evidence/propr-policy13-validation.json`；独立审阅见 `evidence/policy13-independent-review.json`。构建镜像不等于已切换线上，后者由 `evidence/propr-policy13-deployment.json` 单独证明。

10.66.66.5 已于 `2026-10-22T19:45:28Z` 完成该 digest 的 API/worker/daemon 切换，队列前后为 0、runtime.env 未改；同名 deployment receipt 保留了实际读回。机器 review 自动接线的启用与基线登记仍由其独立 activation receipt 证明，不能由本次无模型镜像升级推定已经审查任何新增 PR。

GitHub GET→POST 仍不是原子事务；在 GET 返回与评论 POST 之间存在极小竞态。排队前的请求 base 不是执行时锁定的 base，本修复明确记录并校验实际收集的 revision。短授权撤销不取消已创建评论，但不能据 posted 状态声称模型或发布成功。
