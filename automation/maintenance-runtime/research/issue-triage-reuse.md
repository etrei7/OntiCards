# 普通 Issue / PR 分类与后续评论：复用决策（实施前）

记录时间：2026-10-22 Asia/Shanghai。目标仓库固定 `stepll2026/OntiCards`。本文件补充 R05/R06，不改变原有功能目标。当前 GitHub App 私钥及 ID 尚未接入，因此所有分类流程默认 dry-run，不发送评论、标签或修复任务。

## 已确认缺口

ProPR 源码固定于 [`42931b1502eb03ac299f14e306811736fab51eb4`](https://github.com/integry/propr/tree/42931b1502eb03ac299f14e306811736fab51eb4)，产品版本 0.9.0。`packages/core/src/daemon/issueDetection.ts` 的轮询在 365–370 行逐个使用 primary label 过滤 GitHub Issue；约 186 行再次检查 trigger admission，约 198 行检查触发标签的操作人白名单。当前配置仅 `AI` 标签及维护者 `stepll2026`。因此普通新 Issue 不会自动进入分类/回复流程。此结论来自源码，不以 UI 的 triage 文案推断覆盖。

ProPR 已入队任务的 continuation 可复用，但不等于监视全部未打标签 Issue/PR 的后续评论。直接扩大修复标签/移除操作人白名单会扩大代码执行授权，不能补这个缺口。现成 OpenCode 单次运行也不提供可靠的持久去重与全部事件接入。

## 逐功能复用选择

测试机已有 n8n **2.42.7**，容器 `n8n`，镜像 `registry-intl.cn-hongkong.aliyuncs.com/shallopcr/n8n:2.42.7-zh-community-r2a-20261014`，本地 image ID `sha256:b5b32a81eba912458faf4638b54641d249c959567519a2030a803711d7639663`。复用现有实例，不安装另一套编排服务，不新增轮询程序。

| 功能 | 采用的现成能力与来源 | 接入方式 | 已验证 / 剩余缺口 |
|---|---|---|---|
| 每 5 分钟普通 Issue/PR 接入 | n8n Schedule Trigger、HTTP Request、GitHub REST | 固定仓库，不设 AI label 过滤；列表与评论分页；第一次回填只读 | 原生节点存在；执行实测后追加证据。不能用只读 Events API 的有限历史代替可靠长期接入 |
| GitHub App 认证 | n8n JWT v1 原生 Sign + HTTP Request | jwtAuth 的 PEM 私钥、RS256；JWT `iat=now-60`、`exp=now+540`、真实 `iss`；POST 固定 installation 174029282 的 access_tokens，限定 OntiCards 及 issues/pull_requests 权限 | 已查运行镜像 Jwt.node.js / JwtAuth.credentials.js，PEM/RS256/JSON claims 均原生支持。AppID/PEM 缺失，GitHub 验签尚未实测 |
| 获取 Issue、正文、评论、PR/review | 原生 HTTP Request / GitHub REST | 使用原生分页；固定 API host/repo，不能由模型提供 URL | GitHub 节点支持 Issue 评论与 PR review，但内置凭据为 PAT/OAuth，未发现自动 App installation token 生命周期；故 App 短期 token 走 HTTP Request，避免额外开发 credential plugin |
| 中文分类与回复草稿 | 原生 HTTP Request 调百炼 OpenAI-compatible Chat Completions | 仅传公开正文/评论及固定中文规则，不附工具；模型凭据为单独加密 Header Auth；四类加“不足以判断/需代码核实”，模型不能写 GitHub | 复用已验证 `qwen3-coder-flash`；将执行真实公共读 + 模型 dry-run |
| 跨运行去重、限次与恢复 | n8n Data Table v1.1 的 get/rowNotExists/upsert | 以 repo + item/event ID + updated_at 的稳定键，保存状态/评论 ID/回复次数；仅确认 GitHub 写入成功后标记已发布；灰区先查 marker 评论，禁止盲目重发 | 已检查运行镜像 DataTable.node.js 与 upsert.operation.js。原生 upsert 存在，但不把它宣称为事务锁或 exactly-once；并发、失败中断恢复和限次仍需真实验收 |
| 防机器人循环 | n8n Filter / IF / Edit Fields + 稳定评论 marker | bot 身份及 `[AI辅助]`/marker 跳过；人工新评论或更新才触发；维持次数/时间窗口 | GitHub App bot ID 尚未确认；不能假定身份或加入 ProPR 白名单 |
| 受控发布评论/标签 | 可信 n8n HTTP Request 节点 | 固定 POST comments、labels；使用短期 token，输出正文只能作为 body，不控制方法/URL/仓库；默认写入节点断开且禁用 | 未提供 GitHub 凭据，所以未启用。模型不可调用该节点；后续发布测试需记录真实评论 ID |
| 修复任务交接 | ProPR 原生 AI 标签轮询与白名单 | 确认 App bot ID 后才允许其触发；可修复缺陷需代码证据/授权，其他类只回复/待人工 | 现有安全边界保留；不得把模型分类等同于可自动修改代码的授权 |
| 避免保存短期 token | n8n workflow settings | 成功/失败 execution 保存均 none，manual/progress false；运行时最小字段投影后才进模型；人工测试原始日志先过滤凭据再留证据 | 配置将在可导入 JSON 中锁定；设置不能阻止授权的 n8n 管理员查看运行时数据，不把它宣称成跨租户安全隔离 |

## 选择结论与实施范围

选择现有 n8n 的原生节点补充入口、认证、分类和去重，继续使用 ProPR 执行已授权的修复任务。先交付并执行 inactive/dry-run 的公开仓库读取和中文分类流程；不包含 GitHub 写凭据。再准备独立未启用的 App JWT/安装 token/发布节点模板与 Data Table 去重配置。只有缺少节点间的确定性字段映射、输出校验时才写简短表达式，不创建新的 agent loop、调度器、GitHub SDK 或队列。

尚未覆盖的验收点必须保持明确：真实 App token 签发及权限、全部新增/编辑/评论/review 事件分页和恢复、跨运行幂等与失败恢复、实际中文回复、确认 bot 身份后的 ProPR 交接，以及 Issue→修复 PR 全链路。dry-run 不计为这些验收点通过。

## 实测增量（2026-10-22 16:43）

可导入配置位于 `../deploy/n8n/`。原生 HTTP 公共读取与 6 次百炼模型调用实际完成，7302 tokens，GitHub 写入 0；当前项目新增 #23/#24 来自其他真实作者，并非本任务创建。原生校验拒绝了不合格草稿（漏字段、漏 AI 标识、无代码证据仍全部判断可修复），完整原文保留 `../evidence/n8n/public-triage-results.json`。无模型重放通过，把全部未核实修复结论置为 `needs_human_review`；不计为成功自动回复。

实测发现两个环境缺口：n8n 2.42.7 `execute` CLI 未初始化 Data Table module；已导入全版本保留该原生节点，CLI 副本明确旁路，不宣称幂等验证通过。常驻 bridge 容器无法使用宿主 loopback GitHub 代理；同一已部署镜像的一次性 host-network CLI 读取成功，常驻流程仍需配置现有代理可达入口。没有更改共享实例网络，也没有增加调度服务。

选择后新增内容仅为原生节点 JSON、字段投影/校验表达式及安装/证据提取脚本。没有新增 agent、token 签发实现或轮询实现。真实 App 已由主流程验证，本站 n8n 模板仍未绑定该凭据，等待主流程统一启用。

## 官方资料

- [JWT 原生节点](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.jwt/) 与 [PEM/RS256 凭据](https://docs.n8n.io/integrations/builtin/credentials/jwt/)。运行镜像中对应 `dist/nodes/Jwt/Jwt.node.js`、`dist/credentials/JwtAuth.credentials.js` 已核查。
- [GitHub App JWT claims](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app) 与 [installation token REST](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app)。
- [GitHub 节点](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.github/) 与 [GitHub credential](https://docs.n8n.io/integrations/builtin/credentials/github/)。
- [HTTP Request 节点](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) 与 [Data Table 节点](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.datatable/)。
- [工作流保存、超时和时区设置](https://docs.n8n.io/workflows/settings/)。
- [n8n Sustainable Use License](https://docs.n8n.io/sustainable-use-license/)：已有实例用于内部业务自动化，不称其为 OSI 开源；未新购商业授权，价格/许可条款以官方文本为准。

## 2026-10-22 第二阶段实施前复用决策：结构化模型与原生去重

现有证据 `evidence/model-list-probe.json` 的 178 个可用 ID 含 `qwen3.8-max-0902`、`qwen3.8-max`、`qwen3.7-plus-2026-05-26`、`qwen3.7-plus`。优先比较两个明确快照各一次，样本固定为已失败的公开 PR #23；不重跑全部六条，不修改 ProPR 模型或种子配置。

| 缺口 | 复用选择与来源 | 接入与验证计划 | 新增内容的理由 |
|---|---|---|---|
| Coder Flash JSON Object 缺字段、错误类型与过度修复结论 | 百炼现成 `response_format: json_schema` + `strict:true`，当前文档列 Qwen3.8-Max/Qwen3.7-Plus 系列支持。https://help.aliyun.com/zh/model-studio/qwen-structured-output | HTTP Request 原生节点传 JSON Schema；两个模型各一请求，记录返回 ID、tokens、HTTP/finish reason、事实/结构质量。模型能力需实际验证，不以列表代替调用成功。 | 仅配置 schema 和一次性测试脚本，无模型/Agent 循环。 |
| 身份/权限字段不能让模型推断 | n8n 2.42.7 Edit Fields、IF/Switch、Crypto 原生节点 | `kind`/repo/number 来自可信投影；AI前缀与 `auto_repair=false` 确定性设置；模型只产建议文字。 | 字段映射配置防止模型把 PR 当 Issue，或把分类变成修复授权。 |
| CLI 未初始化 DataTable，去重尚未验证 | n8n 同一已安装镜像正常 `start`、DataTable create/rowNotExists/upsert；https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.datatable/ | 临时 loopback 独立 SQLite server，仅一个受控 Webhook，无 Schedule，无 GitHub 凭据；先同一事件两次，再修改事件与错误草稿路由。正常 server 验证后停止，旧七个工作流及主库不变。 | 一次性部署/核验脚本只调用原生 CLI/REST，非新服务或调度器。此测试不等于主实例正式接入。 |

n8n 的 [Structured Output Parser](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.outputparserstructured/) 也可按 schema 校验，但子节点表达式绑定第一条输入；本轮先复用供应商严格 schema + 原生逐条字段/路由，避免再引入 LangChain 模型适配和自动重试。事实正确性仍独立审核，schema 不能保证事实。

### 第二阶段已得实证

两个固定快照各一调用均 HTTP200 且 strict schema/PR 类型通过：`qwen3.8-max-0902` 8.276秒、737tokens；`qwen3.7-plus-2026-05-26` 7.230秒、719tokens。原文仍含条件式合并建议，因此自动发布质量均未通过。优先保留 Max 供受控后续验证，因为它明确要求独立 diff 核验；单一样本不足以证明一般准确率或代码工具能力。详见 `evidence/n8n/structured-model-quality.json`。

正常 server 的 DataTable/IF/Edit Fields/Respond to Webhook 已真实执行，6次请求形成3行持久账本，重复来源不再次进入处理分支，缺字段及合并建议转人工复核，bot样本忽略。合格分支用明确 synthetic 样本测试，不伪称模型已达到自动发布标准。旧主实例工作流哈希不变，临时 loopback 实例已停止。上述节点均为上游原生能力；新增 Python 仅生成配置、限定启动、调用原生 CLI/HTTP 和导出测试证据。

后续端到端验证仍复用同一临时 server 的 HTTP Request + Credential + strict schema + DataTable，只允许一个真实公开样本模型调用，然后重复同事件验证模型节点被跳过；另存证据，不把冻结响应重放冒充真实模型节点执行。生产自动发布依然关闭。执行存储实测是空 runData 的 soft-delete 初始壳，而非物理立即零行。

端到端现已实际完成，证据 `evidence/n8n/native-server-live-model-probe.json`：原生 HTTP 第一次调用 `qwen3.8-max-0902`，430 输入/240 输出/670 总 tokens，10.806 秒；自由文本包含合并建议，进入人工复核并持久化。同样事件第二次 0.297 秒，原生 DataTable 在模型节点之前返回 duplicate，模型调用 0。没有 GitHub 凭据、写入或 Schedule，原主实例工作流完整哈希不变，临时实例已停止。这证明有限的原生模型节点→确定性校验→持久化→顺序去重路径，不证明自动中文发布质量、并发抢占或完整事件恢复。
