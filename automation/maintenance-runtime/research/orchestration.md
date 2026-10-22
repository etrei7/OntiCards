# 历史选型记录与当前入口

本文保留2026-10-22分阶段候选比较；下文“当前policy4/daemon停止/日报disabled”等描述属于当时快照。当前实际版本、启用状态与验收结论以 `../deploy/propr/manifest.json`、`reuse-matrix.md` 和 `acceptance-gap-audit.md` 为准，不可按历史段落恢复服务。

OpenHands Canvas候选已完成比较并退出选型；2026-10-23停用本任务专用 `onticards-openhands-canvas` 容器，退出码0，镜像/配置/历史保留，未删除数据。当前编码与日报继续使用ProPR/OpenCode；普通讨论和测试派发复用n8n。

---

# OntiCards 编排、审查、修复组件复用核实

检索与实测日期：2026-10-22（Asia/Shanghai）。本文保留阶段 0 候选证据，并以本节当前结论及末尾部署证据为准。源码核实不等于端到端实测；本子任务没有向 GitHub 写评论、推送或创建 PR。

## 当前结论

最终采用 **ProPR 0.9.0 固定源码 + OpenCode 1.18.31**，现用百炼 `qwen3.8-max-0902`；早期 `qwen3-coder-flash` 的质量失败证据保留，不启用付费 Connect。OpenHands Canvas 1.30.0 已完成真实 nonce/Python 工具探针，但其 Automation preset 会向 terminal 注入 GitHub secret；因此没有锁定该框架，改用 ProPR 原生只读 agent token 与宿主发布流程。已确认的例外入口由 G05 最小政策补丁硬拒绝；当前 policy4 的测试和准确 digest 以主部署 manifest 为准。

所有镜像都在 `kol-stage2` 构建、通过已有私有 registry 分发，在 `10.66.66.5` 测试。GitHub App 已实际接入；API/worker 运行 policy4，daemon 停止。原生 Issue25 接单后失败于 clone/refresh，不能算自动 Issue→PR 已完成；另行可信宿主发布的 Draft PR26 也不能替代该链路。已有 systemd 00:00/09:00 事实采集被复用，不新增 n8n 重复调度。原生 ProPR 日报 cron 配为 09:05，当前仍 disabled。

官方 OpenCode CLI 已完成真实 nonce 工具验证。中文日报后来通过 ProPR 原生 trigger→worker→OpenCode→report 实跑：首次 completed 但质量失败，第二次 120 秒 provider 请求超时；复用原生 timeout=300000、模型 enable_thinking=false、精简只读输入后，第三次 run `2957780b-64f9-4a13-a21b-a03ba5d609dc` 在 31.854 秒完成，事实核对通过，未发布外部日报。详见 `daily-timeout-reuse.md` 和 `evidence/native-daily-attempt3-quality.json`。普通未打 AI 标签的 Issue 入口使用已有 n8n 原生节点，真实 HTTP+DataTable 顺序去重/人工兜底已通过，自动回复质量及全事件恢复未通过，继续 dry-run，详见 `issue-triage-reuse.md`。当前入口、镜像 digest、安全边界和停止/恢复见 `../deploy/propr/RUNBOOK.md` 与 `manifest.json`；下面矩阵保留选型过程，不能把候选能力当成已经验收。

## 版本与来源

完整 GitHub API 元数据保存在同目录 `component-versions.json`，包含检索时间、主分支 SHA、最近推送、发布信息与许可证。全部候选仓库未归档，最近均有 2026-10-21/22 推送；这是维护活动证据，不代表稳定性保证。

| 组件 | 已核实版本 / commit | 许可 | 官方来源、部署与边界 |
|---|---|---|---|
| gh-aw | 发布 `v0.93.0`；检索时 main `f5092b615d369ee1869619ca7871fb583fd40d6c` | MIT | [仓库](https://github.com/github/gh-aw)、[发布](https://github.com/github/gh-aw/releases/tag/v0.93.0)。GitHub CLI 扩展把 Markdown 编译成 Actions lock workflow；不能把编译成功当作模型运行成功。 |
| agentics 模板 | `b4e175bab6674279e0fe158f7dc877b77bc9d92f`；无 release | MIT | [repo-status](https://github.com/githubnext/agentics/blob/b4e175bab6674279e0fe158f7dc877b77bc9d92f/workflows/repo-status.md)、[repo-assist](https://github.com/githubnext/agentics/blob/b4e175bab6674279e0fe158f7dc877b77bc9d92f/workflows/repo-assist.md)。已下载原文件并检查 frontmatter 与任务规则。 |
| OpenHands Automation | `1.23.2` = `77dd60e53659c4daf27a9dbc20fa0f96cd135533` | MIT | [源码](https://github.com/OpenHands/automation/tree/1.23.2)。已浅克隆对应 tag；Python ≥3.12，SDK/workspace 固定为 `1.57.0`，SQLite 或 PostgreSQL。README 标明 beta。 |
| OpenHands Agent Canvas | 发布 `v1.30.0`；检索时 main `fcc15b45b9dae3765c745a7647ff63fc26a4a14c` | MIT | [源码](https://github.com/OpenHands/OpenHands)、[自托管安装](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/vm)。npm 包 `@openhands/agent-canvas`，可只运行 backend。版本间兼容以包的实际依赖为准。 |
| ProPR | README 声明 `0.9.0`；核查源码 `42931b1502eb03ac299f14e306811736fab51eb4` | Apache-2.0 | [源码](https://github.com/integry/propr/tree/42931b1502eb03ac299f14e306811736fab51eb4)、[安装](https://docs.propr.dev/docs/tutorials/setup)。API 的“最近 release”是 desktop preview，不当作 server 稳定版；运行版应锁 CLI 和 image digest。自托管免费，Connect 中继/托管 UI 有套餐边界，可用自己的 GitHub App 避开中继。 |
| PR-Agent | 发布 `v0.48.0`；main `6c6da246af071bade2a9c13ade03d84d78f0c065` | MIT | [源码](https://github.com/The-PR-Agent/pr-agent)、[安装](https://docs.pr-agent.ai/installation/github/)。现项目是社区维护 PR-Agent，不能把 Qodo 商业功能算到此开源组件；新镜像命名空间 `pragent/pr-agent`。 |
| 已有 n8n | 主代理环境实测 `2.42.7` | Sustainable Use License / Enterprise License；不是 OSI 开源许可 | [许可](https://docs.n8n.io/sustainable-use-license/)、[版本功能区别](https://docs.n8n.io/hosting/community-edition-features/)。本任务优先复用已有自托管内部用途；不假设已购 Enterprise。 |

## 逐功能复用矩阵（编排相关）

状态：**S** = 官方文档与源码已核实；**E** = 环境已由主代理盘点；**R** = 目标端到端实测。这里没有把 S 写为 R。

| 需求 / 验收 | 已检查现成能力与采用建议 | 接入方式 / 已覆盖 | 具体缺口、验证与新增边界 |
|---|---|---|---|
| 调度、手动触发、历史、恢复 / AC-03、11 | n8n Schedule Trigger、执行记录与重试；同时比较 gh-aw Actions schedule/dispatch、OpenHands scheduler/dispatcher | E：n8n 已存在；S：[Schedule Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)。配置 `Asia/Shanghai`，日界与09:00两个触发。 | 需要实测重启后的缺失日期补跑，不能假设 cron 自动补齐每一个自然日。只允许“计算未完成日报窗口并逐日补跑”的薄适配；调度器不自研。 |
| GitHub 采集、中文日报 / AC-02、03 | n8n GitHub + HTTP Request；gh-aw repo-status；OpenHands GitHub Repository Monitor | [n8n GitHub](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.github/)原生读 repository、issues、PR、review、workflow；未暴露 endpoint 用其既有 HTTP Request。repo-status 只借格式和提示模板。 | 已证实 repo-status 默认模型收集“近期”活动、每天创建新 Issue 并关闭旧报告；没有日界 Star 快照、固定统计窗口、失败/null口径、持续日报单记录。需要项目统计规则 Code 节点或薄模块，不得重写客户端；每窗口唯一键 `repository/date`，失败不填0。 |
| 状态存储与日报幂等 / AC-02、03 | n8n Data Tables；OpenHands KV store、run history；gh-aw repo-memory | [Data Tables](https://docs.n8n.io/data/data-tables/)明示跨 workflow 持久数据、重复运行标记和 API。配置 snapshot/report 数据表；任务运行状态由编排底座持有。 | 并发 upsert / 发布后二阶段失败的恢复需实测；对账键而非“已看过”提示词。不得另建数据库平台或第二套任务队列。 |
| Issue 分类、信息追问、后续评论 / AC-04 | OpenHands Repository Monitor + prompt/plugin preset；repo-assist issue memory、awaiting_clarification | [Monitor](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt/github-repo-monitor)；Automation `schemas.py` 支持 `destination=continue_conversation`、`subject_key_expr`，按 `repo#number`续同一会话。配置中文、范围、AI身份规则。 | 未验证部署后工具权限和模型能力；新评论去重、自己/其他机器人过滤需配置并回放验证。不能因为中文需求重写事件系统。 |
| Issue→隔离分支→PR / AC-05 | OpenHands Issue-to-PR；ProPR三阶段流水线；repo-assist draft PR | [OpenHands模板](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt/issue-to-pr)已有 clone、修复、测试、PR、回写。ProPR由宿主编排进行 commit/push；Agent只改文件。 | OpenHands模板的 GitHub MCP 写令牌若进入执行不可信代码的容器，就不满足任务书 AC-09；需要独立写工具/可信发布阶段或改用 ProPR，而不是用提示词声称隔离。首次公开写入必须测试Issue/PR；机器凭据当前待配置。 |
| PR审查 / AC-05、06 | OpenHands PR Review；ProPR `/review`；PR-Agent `/review`、`/improve`、`/ask` | [OpenHands审查](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt/github-pr-review)与修复使用独立 conversation；PR-Agent适合作可选独立审查器，支持LiteLLM。 | PR-Agent不是完整Issue修复/部署平台，不单独作为主底座；先选一个审查责任组件，不能多机器人重复回应。静态审查不替代真实构建/API/浏览器测试。 |
| 反馈修复、失败停止、冲突 / AC-05、08 | repo-assist Task5更新自己的PR；ProPR `/fix`、`/merge`、`/ultrafix max=3` | repo-assist 已指示同PR更新、基础设施失败只评论；ProPR支持有界review/fix循环、CI等待超时、循环恢复。 | OpenHands普通prompt的“最多3轮”不是独立可核验的业务修复轮计数；先检查上游hooks/KV配置，不能用无限循环。ProPR `/merge`含义是base合入PR分支，但另有auto-merge标签与合并入口；必须关闭所有自动最终合并策略。 |
| Fork PR与凭据隔离 / AC-09、10 | gh-aw safe outputs；ProPR read-only installation token；OpenHands每会话Docker | [gh-aw安全](https://github.github.com/gh-aw/introduction/architecture/)、[ProPR隔离](https://docs.propr.dev/docs/features/execution-safety)、[OpenHands Docker](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/docker-execution)。 | Fork无推送权限的受控关联分支需实测；不得把容器=凭据隔离。ProPR源码/文档有只读任务令牌和可信finalization；OpenHands需核实MCP和测试进程的凭据边界。 |
| 上下文、知识档案 / AC-01、12 | 目标现有README/文档、AGENTS；OpenHands skills/agent profile；gh-aw repo-memory | 模板/指令配置 + 版本化项目事实文档，按实际SHA加载；无需向量服务。repo-assist memory有schema验证、完成动作键、issues/fixes游标。 | repo-assist memory只保留有限条目，不能替代长期审计；事实档案仍须主代理读取真实源码形成。 |
| 部署、构建、API、浏览器、证据 / AC-06、07、12 | 原项目Compose、测试框架，Playwright，GitHub artifacts/Checks；ProPR有preview模块 | 只需目标环境配置与业务测试；Agent编排调用现成测试入口。构建镜像必须在用户指定打包机，运行先10.66.66.5。 | 本研究未审计项目具体测试入口；必须由主实施填。head/base/tested checkout、镜像版本、成功截图、30天留存和过期时间是必要元数据适配；不能由旧报告给新SHA通过状态。 |
| 管理入口、暂停/恢复/取消/重试 / AC-10、11 | n8n执行UI、Canvas automations/runs、GitHub PR/Checks；ProPR UI | 配置链接和摘要即可，不新建后台或认证。GitHub Merge保留给人工。 | 用真实服务进程/运行状态检验UI；不能把计划状态当运行中。模型费用读不到标未知。 |

## 候选细节与未采用原因

### gh-aw / repo-assist

`repo-assist.md` 的源码包含 repo-memory schema、去重记录、待信息状态、自己的 PR CI 修复与冲突处理、AI 身份和反垃圾规则；这些是可复用配置。其默认任务包含主动功能建议、依赖改造、关闭旧活动 Issue、轮流选择三项工作，超出 OntiCards 首期规则；需要收窄模板，不应直接原样启用。

gh-aw 提供明确的读写分离、safe outputs、staged mode 和 Actions 审计，可作为后续 GitHub 原生路径。当前缺口是部署前置：默认分支尚无workflow，计划需维护者合并后生效；模型机密必须配置在能执行的环境；不能用当前交互式 connector 凭据冒充无人值守令牌。[Codex引擎文档](https://github.github.com/gh-aw/engines/codex/)说明自定义 `OPENAI_BASE_URL` 需 Responses 兼容，不能直接假设 DeepSeek Chat Completions 可接。其他引擎可评估，但不为适配而写新的Agent循环。

### OpenHands

Automation 1.23.2 已检查本地 `config.py`、`backends/local.py`、`presets/prompt/sdk_main.py`、`schemas.py`：设置 `AUTOMATION_AGENT_SERVER_URL` 启用本地模式，支持 SQLite、独立本地Bearer key，复用本地 Agent Server 的模型、仓库、MCP和secret设置；不是只有Cloud可用。local backend每run隔离目录；目录隔离本身不是容器/令牌隔离。`continue_conversation`可将后续事件送回同主题会话；自定义webhook delivery header支持去重。

其 scheduler 已有 cron、timezone、原子待运行记录、Postgres行锁；SQLite假设单进程。已有 n8n 时不让两个定时器同时发日报。初期可由 n8n 控制日报与固定调用，OpenHands拥有Agent运行状态；或者只让OpenHands负责GitHub事件，职责必须明确。自动化模板的可用性与模型质量还需现场试跑。

### ProPR

已浅克隆完整源码并检查 `docker-compose.yml`、`.env.example`、`docs/docs/features/execution-safety.md`、`pr-commands.md` 和 `operations/github-auth.md`。系统是Linux amd64、Node 22/24、Docker，包含Redis、daemon、worker、API、UI及可选辅助worker，依赖多于OpenHands本地最小路径；但分支/推送、PR命令、轮数/超时、队列恢复和只读agent令牌更明确，减少安全适配风险。

DeepSeek需通过它已支持的OpenCode provider配置，而不是把DeepSeek key塞给Codex。ProPR已有 [OpenCode集成](https://docs.propr.dev/docs/architecture/opencode-integration)，应验证该条实际协议路径。使用自己的GitHub App可避免Connect relay；目前机器凭据缺失仍会阻塞真实自动处理。不要为了安装方便启用第三方中继。

### PR-Agent

可自托管CLI、Docker或Actions，LiteLLM覆盖DeepSeek及兼容接口；适合独立review，不负责完整Issue→隔离执行→部署。若OpenHands/ProPR已足够审查，首期不叠加它，避免重复评论与模型费用。若现有底座审查不合格，再以具体失败证据启用。

## 已做验证与下一步闸门

已执行：GitHub REST仓库/commit/release/license查询；下载固定commit repo-status/repo-assist；浅克隆Automation tag 1.23.2和ProPR源码；阅读上表列出的源文件/官方文档。结果为 S，没有伪造模型或GitHub写入跑通。

最小验证顺序：安装锁定版本的现成服务 → API健康/认证 → 现有模型一次真实tool call并校验工具结果 → 只读仓库访问 → 隔离测试进程/挂载/令牌权限检查 → dry-run动作计划 → 明确测试Issue/PR真实写入 → 同事件重放与人类追问续办 → 最多3轮失败退出 → 真实PR构建/API/浏览器与SHA证据 → 重启与定时运行记录。缺凭据继续做前面不依赖的项目，不得标通过或自行重写替代。

升级：统一锁版本或SHA/digest，先在10.66.66.5重新执行上述最小验证后更新；未维护任何业务fork。下载到research的上游仓库仅用于检查，不属于要交付的新增功能代码。

## 包级核实补充

实际下载并运行Canvas 1.30.0包内`--info`/`--help`后，确认上游默认完整组合为Agent Server/SDK **1.56.0** + Automation **1.22.0**，而非各组件独立最新版；1.22.0源码亦有主题续办。ProPR README产品版本0.9.0与当前npm CLI版本不同：`propr-cli@0.9.0`实际404，registry latest **0.8.15**。这属于部署版本需要核实的差异，不能写成ProPR不可用。完整可执行探针路径、模型/凭据边界及未验证项见同目录`deployment-probe.md`。

另外，DeepSeek当前官方文档已列出Responses/Anthropic兼容接口，所以gh-aw不能因供应商品牌排除；仍需验证用户实际网关/模型是否覆盖gh-aw Codex要求的Responses工具调用。已有Chat Completions接口最直接的候选是OpenHands/LiteLLM。
# 实施阶段安全边界补充（2026-10-22）

自动 Issue→修复 PR 的主底座建议采用 **ProPR + OpenCode**。OpenHands Canvas 仍完成受控安装能力验证，但不能因已下载镜像就将它锁定为生产编排。

- 已复核匹配 Canvas1.30.0 的 Automation **1.22.0** `presets/prompt/sdk_main.py`：先 `workspace.get_secrets()`，随后 `conversation.update_secrets(secrets)`，源码明确这些 secret 会自动导出为 bash 环境变量。未找到现成的“沙箱只读 GitHub、宿主独立发布 PR”实现。工具白名单本身不能约束一个已经拿到写 token 的 terminal。来源：[锁定版本的官方 preset](https://github.com/OpenHands/automation/blob/1.22.0/openhands/automation/presets/prompt/sdk_main.py)。仓库 origin 与相关源码已在本地检查。
- ProPR 锁定 `42931b1502eb03ac299f14e306811736fab51eb4` 的 [`agentGitAccess.ts`](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/packages/core/src/agents/agentGitAccess.ts) 实现实际 GitHub App 子令牌权限收缩：contents/issues/pull_requests/metadata 全为 read，校验返回权限不符立即拒绝启动；任务 `.git` 与共享 clone 挂只读。普通 Issue、修复和review使用该路径。**例外**：`executionMode=goal` 且 `PROPR_GOAL_LAUNCH_STRATEGY=orchestrate` 时允许代理写Git，因此本任务不得启用该模式。
- ProPR [`autoMergePolicy.ts`](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/packages/core/src/workflow/autoMergePolicy.ts) 中 `auto_merge.enabled: false` 明确返回 `skipped_disabled`；策略读取 base 分支。这是代码约束，不能用提示词替代。仍需要仓库规则保护主分支、App不拥有绕过权，以及实际拒绝合并测试；本轮不把源码检查标记成线上验证通过。
- ProPR `.env.example` 的默认 `routing_websocket` 依赖托管 ProPR App/relay，本次必须显式 `GITHUB_EVENT_INTAKE_MODE=polling` 与 `GH_AUTH_MODE=app`，使用用户自己的 GitHub App；不设置 UI tunnel token，不引入付费订阅。

