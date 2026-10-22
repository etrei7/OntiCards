# 新 PR / 更新的语义审查入口复用核查

2026-10-23 02:34 上海，只读核查，0 模型调用、0 GitHub 写入。

## 已有实现和真实状态

核查时 ProPR policy11；当前部署 policy12，历史原始值保留。单仓配置 enabled=true；autoFollowupOnFailedCi=false、autoAssignPullRequests=false、autoAssignRequestReview=false、autoResolveMergeConflicts=true。证据 `evidence/semantic-review-trigger-audit.json`。autoAssignRequestReview 是请求 GitHub 人工 reviewer，不是 AI 自动语义审查。

上游 `packages/core/src/daemon/issueDetection.ts` 排除 pull_request；`src/polling/prCommentPolling.ts` 处理显式评论、触发标签和 ultrafix 的既有续办。`webhookHandler.ts` 的 PR 事件处理计划/冲突/旧验证取消等；未发现新 PR 或 synchronize 自动发起通用语义审查的配置开关。模型和审查提示设置只选实现，不创建触发器。CI 的 API/PW 与 Checkwatch 不替代这项目标。

## 优先复用的两个原生入口

1. `POST /api/tasks/:taskId/review`：原生鉴权、用户仓库访问/assignment、7天 Redis sourceTask 幂等、原生命令分发、队列、parser 和发布器。限制是必须有旧 Task，且同 sourceTask 只允许一次；无法直接覆盖全新人工 PR 或同 Task 的新 head/base。不能伪造 Task 或拿旧 Task receipt 当新版本已审查。
2. 原生 MCP `review_pull_request`：支持任意开放 PR、expectedHead、durable idempotencyKey、read/review scope 和单仓 grant；复用原生 review 模型、命令、parser/发布器，不需新 Agent。入口会通过已认证 principal 的 GitHub 身份发布可追溯命令，不伪造评论作者。需要真实原生 OAuth grant。

现有 MCP 原生配置要求 HTTPS origin（`mcp/config.ts`、`configResolver.ts`、`routes/adminMcpRoutes.ts`）；当前 HTTP 内网部署不能仅打开开关。不能删除 HTTPS 约束或借用人工浏览器 cookie 作为永久服务凭据。需要准备受信 HTTPS 与原生最小 read/review、仅 OntiCards 的 OAuth 接入配置。

## 候选集成边界

复用已经完整分页、提交水位并撤销 token 的 18128 intake，经既有 HTTP/Execute Workflow 到独立 review admission。与 CI 状态分开，使用原生 DataTable 持久键 `(repository, PR, head, base)`；初始完整快照只登记 baseline，不回放 PR26/30/33。仅后续新 PR 或版本变化进入 fresh scope 检查；目标仓库 main 上所有 open PR（含普通分支/fork）允许只读审查；不可读源码或旧发布恢复冲突转人工。CI 执行仍单独限制同仓 codex 分支；先持久登记 submitting，再调用原生 review；任何 unknown/failed 不跨 poll 自动重预算。语义结果必须来自原生 parser/Task 终态，受理或评论已发不计成功。

本次只允许配置与 native dry-run/未来事件 admission 验证，不允许额外模型验收调用。本段是接入前快照；现已实施下述原生 intake→dry-run 接线，正式模型派发仍未启用，不把 CI 或 TLS 接通写成语义审查完成。

来源：上游 ProPR 本地精确源码（research/propr-src 对应交付政策基线）；既有 [n8n 子工作流](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow/) 与 [MCP 授权](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)。新增范围若实施仅是原生节点配置、版本准入和最小可信接线。

## 已选最小集成（2026-10-23 03:20 上海，候选未武装）

原生 OAuth consent 要求浏览器同 canonical HTTPS origin；现有 HTTP 用户入口不满足，不能伪造 Origin 或令用户忽略证书。复用原生短期 `issueDelegatedGrant` 与现有 OpenSSH 固定能力，而不新增 OAuth broker、队列或认证框架：可信 n8n 只持 from=127.0.0.1、restrict/no-user-rc/禁转发/PTY 的专用固定动作 key；宿主固定 argv/env 的 wrapper 通过既有 API 容器原生持久 membership 与真实 GitHub 身份检查，颁发仅 OntiCards/read+review 的 5 分钟 grant，验证现有本地 CA 的 HTTPS MCP，finally 撤销并读回。n8n 没有 Docker socket、ProPR DB、PEM 或普通 shell 能力。

原生 McpOperations 幂等包含 grant_id；新增适配的唯一持久查询是跨 grant 查原表 owner/repo/tool/idempotency_key + 原生 payload_hash；任何 accepted/unknown/failed/posted 等旧记录禁止重发。原生 DataTable 在 SSH 前登记版本，失败、未知、重启和队列清理均不释放预算。输入 tuple 含 base，新 base 视为新版本，不伪称同 head 永久一次。

`structuredContent.data` 是原生 operation 投影，comment 位于 result。适配保留 posted/failed/unknown/lifecycle，不把 posted 当 review 完成；请求后传输失败是 submission_outcome_unknown/model_started=null。撤销 unknown 转 credential_cleanup_unknown。使用明确 alias `onticards-qwen:opencode-bailian/qwen3.8-max-0902`，不误选同模型日报 alias。13 项本地 envelope/不确定状态测试通过；peer 52 项原生 OAuth/operations/grants 禁网测试通过，均无模型。

新发现仍需处理：原生 review worker early branch 前可能恢复此前 pending publication/Ultrafix；仅 prompt 不构成全面只读保证。正式自动 review 继续 disabled，等待原生 lease 内最小 gate 审查；不以 TLS 配置或 dry-run 代替实际语义审查验收。最后 PR30 commit 发布后才取完整当前 snapshot 建 baseline 并启未来事件，旧 PR 不回放。

## 03:50 实际收口

policy13三服务于19:45:28Z部署精确digest3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879，964/964无skip；真实Redis/SQLite workerfixture验证只读恢复、可信owner无标签及实际收集head/base变化失败出口。13后TLS/SSH12项再次全部通过、0模型。自动接线仍dry_run/hostfalse，六PR自然只读回执与12项baseline去重证明传输和准入，不是语义审查成功。最终PR30发布后由activate_review_admission.py读取完整新水位、登记全部旧版本baseline、三服务精确版本和双配置读回后才启未来事件；失败receipt始终落盘并exit2。外置mcp-review-activation.json记录真实启用，不产生源码head循环。
