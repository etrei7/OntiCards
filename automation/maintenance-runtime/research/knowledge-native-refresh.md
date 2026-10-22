# 原生知识增量与固定版本验收（2026-10-22）

当前状态更新（2026-10-23 北京时间）：知识主路径已完成零模型真实跨版本验收：现成 n8n reader 读取 8abe → c8e → main，22 段实际返回上下文、29 条原生缓存记录和真实事件绑定经独立 Git 对照，69/69 通过。PR30 精确 10c6862 文档包保持原样，实际任务 checkout 为最终代码依据；当前入口、版本及历史边界见 `deploy/propr/KNOWLEDGE-CURRENT.md`。主流程已于 2026-10-22T17:15:40Z 部署 policy11；旧索引任务随后无新模型日志地进入 failed，队列为空、summarization=false。全仓语义索引仅为停用的可选部分产物，不能称全仓完成。

下文至末节前保留选型、候选和失败历史，早期“尚未部署/仓库空”不代表当前运行状态。最新实际部署、478 项政策回归和完整补丁分组分别见 `evidence/propr-policy11-deployment.json`、`evidence/propr-policy11-build-validation.json`、`research/propr-patch-map.md`。

复用底座固定 ProPR `42931b1502eb03ac299f14e306811736fab51eb4`（实例 policy7）及 OpenCode 1.18.31，不增加向量库、知识服务或自制调度器。上游功能说明：[Repository Knowledge](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/docs/docs/features/repository-knowledge.md)。

| 需求 | 现成实现与接入 | 验证/具体缺口 |
|---|---|---|
| 任务读取本次代码知识 | OpenCode 自动读取工作区 AGENTS.md；原生 `instructions` 可载入已有文档；[官方 Rules](https://opencode.ai/docs/rules/) | PR30 未合并，main 尚无这些文件。部署的临时全局副本没有来源 manifest，AGENTS/context 仍是旧版。准备 exact PR30 SHA 包，不能冒称已经更新运行环境。 |
| main 变化后增量摘要 | `src/indexing_worker.ts:294` 原生 5 分钟扫描；`:125` 比较 origin 分支 SHA；`summaryMinerStaleness.ts` 按 branch+path+blob hash 识别新增/修改/删除 | 真实 Git+SQLite 探针已过，重复处理 0；删除仅本分支。模型摘要质量及线上扫描尚未执行。 |
| 手动更新/停用/恢复 | 原生 `POST /api/config/repos/trigger-indexing`，payload 在 knowledge-native-config.json；原生 stop-indexing；UI Reindex；失败重跑保留成功文件摘要 | `summarization.enabled=false`、无 indexing worker、repositories 索引表空，为实际状态。候选 compose profile 默认不启动。 |
| 知识版本及新鲜度 | 原生 `repositories.last_indexed_hash`、file_summaries blob hash、MCP get_repository_context freshness；read_repository_file 支持 exact ref | 已复现 G-K01：metadata 取 origin/main=B，但 scanGitFiles 读 checkout A 的 index，批处理读可变工作树。原生 fetch checkout/reset 异常仅 warning，甚至 fetch 失败也仍入队。必须修复再声称固定版本更新。 |
| 与 Issue intake 分离 | 原生手动 triggerIndexing 可指定仓库；定时扫描只看 repos_to_monitor.enabled | 原生没有独立 index-only repository enabled；不要为知识刷新开启所有 Issue intake。当前单仓 enabled 由 root 管理。 |

## 新增适配原因先行记录：G-K01

136 项无模型隔离验收来自现成 policy7 测试镜像，含新增实际导入 scanGitFiles、identifyStaleFiles、deleteFileSummaries 的 Git+SQLite 探针。`evidence/native-knowledge-and-pr-tests.log` SHA256 `c1717edbaa03e27489d49cc8f54bc8b78354c01c361bd05a532b1159b6f6fc1a`。其中“pinning hazard reproduced”是缺陷证明，不是该能力通过。上游 summaryMiner.test.ts 复制私有逻辑，未把它作为集成实证。

已先检查原生 createWorktreeFromExistingBranch；它操作可写 branch/共享 tracking，不适合索引临时只读快照。已实现最小候选，复用 Git 原生 [detached worktree](https://git-scm.com/docs/git-worktree)、createHooklessGit、repositoryStorageLifecycle.use：一次捕获分支 commit，临时 detached checkout 全程读同一 SHA，完成/失败后仅清理该工作树；metadata/message 同样从捕获 SHA 读取。手动、批量、周期三个原生入队分支 fetch 失败均拒绝入队。复用原有状态/SQLite/批处理/取消/调度，不新增服务。候选尚未构建部署，线上能力不能标为闭环。

## G-K02 与修复验收

实际 Git 快照仍可包含指向宿主文件的符号链接。原生过滤器使用 statSync 跟随链接，因此仅固定 SHA 不足以证明内容来自该 SHA。复用已有 isFile 判断，将 statSync 改为 lstatSync，拒绝符号链接，不引入新的文件系统解析器。

四个生产文件、三个测试文件已冻结。真实 Git+SQLite 测试证明：共享 checkout/ref 在批处理期间变化时仍读取捕获的 B 提交；路径、blob、元数据一致；缺 ref 提前失败；成功和 provider 异常均清理仅本次快照；原始工作树和未跟踪文件保留；禁用时不建快照；hook 未执行。原生三条入队路径在 fetch 失败时均不入队。测试中模型和 Redis 边界被替换，不是线上模型索引验收。

policy7 基线 red：固定版本 3 失败/1 通过，fetch 3 失败/2 通过，符号链接 1 失败/4 通过。候选 core/root TypeScript 编译成功；七个测试文件 146/146 通过、0 skip。已有 fallback 测试在禁网时输出 Redis/价格查询警告，其断言通过；不得称为 Redis 集成成功。

补丁 `deploy/propr-indexing-pinning.patch` SHA256 `d66ad85fcc4ee5067159fa5840faa78ae9b51731b982d35bda6234fc2677533b`，相对 policy7 tree `3df474a18c69018a47b1389506bad38c65e9abb8`；独立临时 index apply 后 tree `41e314ba1ff2b052ffedc5a9d7dd4c2ff8a590ae`。只含上述七文件，排除并行 PR33 发布修复。文件哈希见 `evidence/indexing-pinning-candidate-files.json`；日志见 `evidence/indexing-pinning/`；构建机复验脚本 `deploy/propr/run-indexing-pinned-tests.sh`。

## 已准备且未应用的配置

- `deploy/propr/knowledge-indexing.compose.yaml`：extends 现有 worker，固定 policy7 镜像，原生 indexing_worker，profile knowledge，扫描 300000ms/重检 86400000ms。Compose 2.40.3 使用空 runtime.env 做静态解析成功，未启动服务。
- `deploy/propr/knowledge-native-config.json`：原生 summarization 字段，默认 enabled=false；固定现有 agent/model，无 fallback 扩张。不能整份当 API payload；只提交相应字段。
- `deploy/propr/knowledge/10c6862d4c7325c85618f86455aacf9d10c088b5/`：三个文件严格来自 PR30 commit，含 tree/blob/SHA256 manifest 和原生 instructions fragment。`package_knowledge_snapshot.py` 只允许这三个 Git 路径、full SHA，目标已有就拒绝，不读工作区秘密、不覆盖历史。这是补临时副本缺少版本来源的部署适配。
- PR30 合并后，改用原生相对路径 instructions + 自动发现 AGENTS.md，读取每个实际任务 checkout 的同版本文档；停止同时载入旧全局副本。每次 main 变化仍核实际代码，不能把历史测试结论外推到新 head。

正式启用还需：G-K01 修复通过、镜像在 kol 构建并由 root 部署；确认 main/文档来源和现有 intake 设置；一次真实有限索引验证 usage/产物/实际 SHA；确定原生批次模型调用的整体用量边界。当前 24 steps/单次 600s 不等于整个仓库索引的总预算；不得无上限开启重复全仓付费。

## G-K03 单次索引预算（先记录复用与缺口）

原生 `SUMMARIZATION_MAX_BATCH_TOKENS/MAX_BATCH_FILES` 和目录对应配置只限制每批，文件及目录解析各自最多三次重试；原生 `indexRepo` 没有路径 include 或全 run 总上限，failed 状态还会每 5 分钟重排。不能把“关索引”当完成 main 变化后增量刷新。

已授权最小候选：在现有 indexingCancellation 中使用 Node 原生 AsyncLocalStorage 传递每次 indexRepo 独立预算，文件/目录实际 analyze 前（含原生格式重试）共同最多 6 次，600 秒总分析窗口；把剩余毫秒传给现成 AnalyzeOptions.timeoutMs，沿现成 Docker timeout 终止机制。预算触顶复用 indexRepo 的 failed 状态、保留已保存 summaries；维护模式 failed 不自动重新排队，原生手动 trigger 可恢复，completed 仍按 main SHA 增量刷新。无新调度、receipt 表或 Agent 循环。原生模型内部工具步骤仍另外受现有 24 steps，analysis 数不等于供应商 HTTP 尝试数，USD 继续未知。

主流程已实际部署 PR30 精确 SHA 三文档包及原生 instructions，provider 配置 hash 未改变；receipt 为服务器 `evidence/versioned-knowledge-deployment.json`。前文“未应用”描述属于准备历史；索引 worker 和预算候选尚未部署，不把知识文件部署等同全仓索引完成。

预算上下文使用 Node 官方稳定的 [AsyncLocalStorage](https://nodejs.org/api/async_context.html#class-asynclocalstorage)，以原生 Promise/async 生命周期隔离并发 run，没有新数据库状态层。候选目前隔离保存在 `research/indexing-budget-candidate/`，未覆盖 policy8 冻结源码。首次 core/root 编译与 82 项测试通过，包含真实 Node 子进程超时退出（不仅 Promise 返回）、真实 Git+SQLite failed/保留摘要/快照清理、跨 poll failed 零入队、原生手动续办及 completed 新 SHA 入队。使用禁网 fake provider；不冒称付费索引已验收。

约束精确定义：6 次是原生分析入口调用，包含格式重试、文件及目录调用与显式 fallback，不等于模型内工具轮次或供应商 HTTP 重试次数。当前选用 direct OpenCode/Qwen，仍须保持单步数/供应商请求 timeout；未来换 Synthetic 路由不能外推成 6 次物理 provider 请求。取消标志在每次分析前检查；进行中的分析仍沿原生 timeout 终止，不宣称人工取消能即时中断正在运行的 indexing 容器。Git 准备与清理仍可能增加总体墙钟时间；这不是整个索引任务 600 秒的墙钟 SLA。

### G-K03 最终截止检查及 policy9 候选

2026-10-22T16:16Z：在原生 OpenCode `resolveAnalysisTimeout` 再次读取同一绝对截止，位置在配置快照和 scoped Git access 准备之后、现成 Docker executor 启动之前。未过期则只传剩余毫秒；已经过期则抛原有预算异常，不启动执行器，仍经原有 finally 清理快照。预算异常保留到 indexRepo 的原生 failed 状态，不被转换成普通空响应。没有添加新的 timer、子进程管理器或重试服务。

两项新增用例在旧 OpenCode 实现 2/2 失败；候选完整 core/root 编译和 8 个文件 98/98 通过、0 skip。准备耗时 250ms 时 1000ms 窗口只剩 750ms；准备耗时 1001ms 时 executor 调用数为零，两个分支都清理快照。原有真实 Node 子进程 400ms 超时及进程不存在验证仍通过。日志为 `evidence/indexing-budget/indexing-budget-deadline-{red,final}.log`。原先 82 项与 19 项的历史日志保留，不相加宣称一次完整测试。

冻结 policy8 已由主流程部署（见 `evidence/propr-policy8-deployment.json`）；索引预算候选仅叠加到独立 policy9。policy8 tree `7d3af65f3e0fc702ed89103291e2dcc7101f4fdd` 加 6 个生产文件、5 个测试文件，得到候选 tree `555f1a7d4c24192e108503be371ec0c05faf2ec6`；独立全补丁 `deploy/propr-maintenance-policy9.patch`，原 policy8 补丁不改。`evidence/propr-policy9-patch-validation.json` 保存完整文件清单与 apply 后 tree，构建完成后仍须主流程部署及一次有限真实索引验收。

2026-10-22T16:21:21Z，kol 完成 policy9 官方生产镜像构建与推送，合并后的 460/460 回归通过、24 suites、0 skip。镜像固定为 `registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy9@sha256:60ad76755bb04c593e82a0debe02becb8ba99f66e355f0271dd671c9b9bb444b`；构建 config ID `sha256:afed0f6d05339bae0d2576ef35f3491079adea07e88282c4fcfa41b6539f488b`。`evidence/propr-policy9-build-validation.json` 及 `evidence/policy9/` 为无模型构建证据。原 policy8 全补丁 SHA256 仍为 `7d585dd8ffd379cb3908f65e7f34dc909e03aecfd74adb10645fe89ab36b2fa5`。候选知识 profile 已固定 policy9 digest 和 6 次/600000ms；部署与真实索引由主流程另行记录。

## G-K04 知识入队前 Git 准备未受期限保护

真实首次索引在 API `queueIndexingJob` 的 ensureRepoCloned 卡住，尚未 queue.add。复查发现 API 缺少既有 host Git 缓存 bind，主流程按现成 Compose 配置修正；另有独立源码缺口：手动、批量、周期三个知识准备入口直接调用 ensureRepoCloned/fetchLatestChanges，未使用 policy7 已有的 withGitPreparation。createHooklessGit 只继承已有执行信号，分析阶段 6 次/600 秒预算也尚未开始，故不能终止该准备过程。

先记录后实施的最小 policy10 候选：仅复用现成 withGitPreparation、simple-git 原生 AbortSignal、createExecutionDeadline，维护模式下每个仓库一次 clone + fresh fetch 合并受 120 秒期限保护，超时等待真实 Git 子进程终止后沿原有返回/日志路径失败、零入队。正常及 fetch 失败语义保持，非维护模式默认行为不变。没有新 clone、调度器、Task/receipt 表或自制进程管理器。使用本地 HTTP stall 的真实 Git child 验证 red/green，不能只测 Promise race。现有 Stop Indexing 仅操作已有 queue job，不把 prequeue 调用宣称为可由 UI Stop 取消；此候选先关闭明确的无限准备时限缺口。

2026-10-22T16:52Z：两个生产文件和两个测试文件已形成独立 policy10 delta。真实测试分别经过三个原生入口 × clone/fetch：基线 6/6 red 均先观察到真实 git-remote HTTP 子进程，再因未受 deadline 终止而失败；候选通过，子进程及其 HTTP children 均退出、零入队。同一 wrapper 参数断言为 120000ms，fixture 只把期限压到 700ms；fetch 前先消耗 200ms，验证两阶段共享期限。与旧取消/入队测试合计 22/22、0 skip，root TypeScript 编译成功。首版 fixture 的单参数 fetch overload 未发请求，已修为真实 `git fetch` 后重新 red/green，旧日志保留且不作为六项红测证据。

候选 tree `34be674fa6c23301594a7304934c1fd0a361fd43`，完整补丁 `deploy/propr-maintenance-policy10.patch` SHA256 `d29d0a40af595d9dd3cf595dd3d386a3422e0425df19740de63b20f5442cab4d`；仅四文件 delta 为 `deploy/propr-policy10-delta.patch`。来源为冻结 policy9 tree，未从共享工作树整包。`evidence/indexing-preparation/` 保存 red/green，`propr-policy10-patch-validation.json` 保存 SHA/apply/tree。预队列 Git 失败仍遵循现成周期扫描的下轮重试语义；未新增 persistent failed row 或预队列 UI 取消能力。Git deadline 不声称同时取消 Octokit 的鉴权 HTTP 请求。
# G-K05: native retry and completion projection gaps (observed 2026-10-22 16:55 UTC)

Before the following adaptation, live policy9 produced a bounded-analysis failure for `main`, but BullMQ's existing queue default (`attempts: 3`) automatically reopened the same job with a fresh per-run allowance. A separately queued `HEAD` job processed 20 files and failed another 20 (`failedBatches=1`, `stopProcessing=true`); `summaryMiner.finalizeIndexing` persisted `failed` then returned normally, while `processIndexingJob` unconditionally reported completed. Evidence: `evidence/indexing-before-budget-stop.json`, `indexing-outcome-events.json`, and the operator's stop receipt. Neither job demonstrates a complete index.

Reuse first: BullMQ 5.81.3 already provides [attempt limits](https://docs.bullmq.io/guide/retrying-failing-jobs) and [UnrecoverableError](https://docs.bullmq.io/patterns/stop-retrying-jobs); ProPR already persists branch-specific indexing state and accepts an explicit monitored `baseBranch`. Use those mechanisms: maintenance queue attempts=1; reject attemptsMade>0 or attemptsStarted>1 before `indexRepo` (including existing attempts=3 and stalled jobs); convert maintenance failures to native UnrecoverableError; verify the native repository status after indexRepo before returning completed. Failed/unknown results must fail, cancellation/cooldown idle must remain an explicit skip. No second budget, retry scheduler, receipt store, or model loop is introduced. Ordinary non-maintenance behavior remains unchanged.

The duplicate `HEAD` admission is a configuration gap: the deployed monitored repository now explicitly uses `baseBranch: main`. Existing branch-aware native queue deduplication can then match manual/main and periodic/main. Do not hardcode `main` for other repositories or reinterpret arbitrary refs. Validate configured deduplication without model calls.

已完成 policy11 候选：2 个生产文件和 2 个测试文件，精确叠加 policy10 tree，完整 tree `c5ace8247411ee8c33802a62169fd02e54d0378b`。真实隔离 Redis/BullMQ 基线 11 项中 7 red、4 pass；修复后 19 项（含原生 main 去重和原入队回归）全绿。旧 attempts=3 的预算失败只执行一次，已失败旧 job 第二次投递零 indexRepo 调用，原生 failed 状态不会发布 completed。stalled/redelivery 分支另用持久计数字段边界测试，不冒称该单例跑过宿主崩溃。非维护默认行为不变，取消/cooldown idle 明确返回 skipped 而不是完成的知识库。

kol 最终官方生产构建和 core/root 编译通过，原回归 467/467、独立 Redis 11/11，共 478/478、0 skip。镜像 `registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy11@sha256:d07dc0c1f50566ac6913206059faab112ce8c0db96e44bc24ba1786f921bf21d`；完整补丁 `deploy/propr-maintenance-policy11.patch` SHA256 `bcf33d2adc53582de662aafa7da114c1a211ab3f0dd9064712630a446be3ac4f`，87 文件按原因分类，不是本轮新增87文件。policy9/10 历史 patch 保留。真实模型索引恢复尚未执行。

## 最终主路径验收：版本文档 + 实际 checkout + 原生增量源读取

任务书要求初始化阅读并验证代码、文档、部署和测试，持续维护带版本/时间的事实档案；没有要求逐文件调用模型完成全部语义摘要。沿现成 Markdown、OpenCode instructions、ProPR checkout、n8n GitHub/Crypto/DataTable 实现这些目标，不再引入知识服务。

2026-10-22T17:38Z 前完成三个真实只读请求，经已有 `onticardsRepositoryContextV1` Webhook 串行运行：

| 请求 | 实际 commit/tree | 原生核验文件数 | 结果 |
|---|---|---:|---|
| 历史 8abe | `8abe9e20d58df2605b8a66c3a4296d3dcfe325a2` / `696e08b3526a0aae36bfee8813ebdcc3415d1174` | 8 | complete，令牌已撤销 |
| 当前 c8e | `c8e3dfee68d398a37842fc332f73af40a56f02a7` / `99f6c09c69ae8553c62fe223d3eaf6ed650e1955` | 10 | complete，令牌已撤销 |
| main | 现场重新解析为同一 c8e/tree | 10 | complete，令牌已撤销 |

三个响应实际返回 22 段有界上下文，其中保留合法空文件；可选核心内容受 24000 字符预算截断，因此核验文件数不等于返回摘录数。独立读取本地相同 Git 对象核每段 blob、SHA256、行起点与摘录；29 条缓存的 `commit:path`、内容 hash 与 Git blob 全部一致；`ext_migrate.py`、`models/__init__.py` 的变更和两个新增迁移文件均匹配。69 项检查全绿，模型调用与仓库写入均为零。原生 DataTable 是按 commit/path 的不可变缓存；observed_at 表示最近读取/保存时间，不能冒充每个缓存文件都重新联网获取。

保留两个 red：最初核心文件耗尽预算却 complete=true；显式相关路径优先后，真实历史空 `models/__init__.py` 被错误当缺失。复用现有 Select/Verified Set 表达式修复相关性与 empty 元数据，必需非空文件因预算丢失仍 fail closed，不增加 12 文件/24000 字符上限。原生 Loop 已由另一任务完成混合缓存汇总修复。这些是现成工作流配置调整，没有自制检索器、事件轮询器或模型循环。

长期入口实读为 active：`onticardsPersistentDraftsV1` 每 5 分钟处理符合条件的新事件，Issue 每次 fresh resolve main，PR 使用事件 head，经 source complete + token_revoked 门禁后把 repository_context 存入原有事件 source_snapshot，并用原生 Crypto SHA256 绑定。现存 Issue29 自然事件确实绑定 c8e 和 source hash，但该历史运行早于相关性修复且回答审查被拒绝、零新评论，不能称咨询回答端到端通过。没有事件时此 source reader 不额外轮询；实际 ProPR 任务 fetch 与现有每日日报另记录当前 main。无需重复建设空闲时知识调度器。

证据：`evidence/knowledge-main-refresh-{native-red,empty-file-red,native-green-v2,independent}.json`、`knowledge-main-historical-diff.json`、`knowledge-source-pipeline-readonly.json`、`knowledge-runtime-current.json`。复验脚本为 `deploy/n8n/verify_knowledge_main_refresh.py` 和 `deploy/verify-knowledge-main-refresh.py`；前者拒绝覆盖既有验收输出，不能原样反复执行。新验收须显式新文件名并先检查现有请求状态。

原生语义索引维持可选/停用：main 与 HEAD 均 failed、last_indexed_hash=null，60 条历史文件摘要不等于完整覆盖。policy11 旧任务收尾证明零新增模型日志和空队列，见 `evidence/indexing-settle-after.json`。这不妨碍任务读取实际 checkout 和有界源上下文，但超范围问题仍须读取相应代码，不能凭摘要猜测。

