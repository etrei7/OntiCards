# 原生跨轮询重试停止能力与 policy5 局部扩展

2026-10-22。固定上游 ProPR `42931b1502eb03ac299f14e306811736fab51eb4`。前半保留 policy4 阶段的只读调查；文末 policy5 段记录随后明确授权的局部实现与隔离验证。生产只改 dispatcher 与现有失败评论，未操作实际 GitHub 标签/评论或生产队列；构建部署由主流程统一完成，本记录不构成生产原生续办端到端通过。

## policy4 阶段的历史结论

**当前 Issue25 的受控续跑可优先复用原生 Follow-up，不需要再写调度或重试计数器。** 网络恢复后，经真实认证入口对已经 failed、没有待执行子任务的原任务发送一条普通 follow-up，走现有请求/触发回执机制。它会写真实 Issue 评论并重贴 trigger，属于新的有记录请求；不能假装只是本地 dry-run。是否现在执行由主流程按当前网络与用户授权决定，本次未调用。

**这不能自动修复所有外部首次贴 AI 标签的循环接单。** 没有 task submission、没有 retry request/accepted receipt 的普通首次事件，仍没有持久“这个触发已执行过”的记录。当前没有查到一个配置项可让所有外部首次事件自动采用 submission 回执；不能把既有重试机制有能力写成默认已经生效。

## 实际入口与机制

| 已有能力 | 源码位置（相对于 research/propr-src） | 能解决什么、限制是什么 |
|---|---|---|
| 共享发现入口 | `src/daemon/issueDetection.ts` 仅 re-export core；`packages/core/src/daemon/issueDetection.ts:107,233,304` | 实际 daemon/webhook 复用 core。仅排除 trigger-processing/done/cancelled；Redis NX 去重只有30秒；父job attempts=3且完成/失败后可删除，因此不是跨poll持久幂等。不要误改另一个legacy `src/polling/issuePolling.ts` 或依赖其环境变量。 |
| 普通失败行为 | `src/jobs/errorHandlers.ts:368–381` | 发布失败评论并移除 processing，保留原AI trigger；评论承诺自动重试。与没有持久回执的普通Issue结合，队列清理后下次poll可再次接单。 |
| 原生 task submission | `packages/api/routeRegistry.ts:216–218`、`packages/api/routes/taskSubmissionRoutes.ts:366–396`、`packages/core/src/services/taskSubmissionService.ts:138–173` | 创建持久 submission，CAS处理Issue创建与不确定响应，保存已有dispatch。`POST /api/task-submissions`是创建新Issue的入口，不是无副作用地收编Issue25；不能为了回执创建重复Issue或直接伪造数据库记录。 |
| Submission的trigger回执 | `packages/core/src/services/taskSubmissionRetry.ts:28–98`、`src/jobs/issueJobDispatcher.ts:379–386,443–474` | dispatch_complete后没有新、可排序的trigger便跳过；终态后新trigger可重跑。子job在持久dispatch回执前保留。既有 `taskSubmissionService.test.ts:96–119` 实质覆盖队列清理后迟到投递跳过、新label才重跑。此次未重新执行该组。 |
| 已失败Issue原生Follow-up | `packages/api/routeRegistry.ts:284`、`packages/api/routes/taskFollowupRoutes.ts:149–155`、`packages/api/routes/taskIssueFollowup.ts:398–445` | `POST /api/tasks/:taskId/followup`走现有认证/任务入口；没有PR时直接续办原Issue。要求该任务最新history为failed、队列无active/waiting/delayed对应任务、Issue open且不是PR；done/cancelled标记会拒绝。这里应使用普通请求文本，PR slash command会拒绝。 |
| 请求保留/发布/不确定结果恢复 | `packages/api/routes/taskIssueFollowup.ts:211–247,314–325,363–392`、`packages/core/src/services/issueRetryRequest.ts` | 先reserve，再post评论、读取label baseline、begin publication、重贴trigger和记录结果；结果不明时保留义务，不随意再发相同请求。直接复用，不写新补偿轮询。 |
| 队列原子accepted回执 | `packages/core/src/services/issueRetryRun.ts:6–19,33` | 同一Redis事务记录接受的children和trigger，记录无到期；消费后retire保留tombstone。即使原job删掉，迟到dispatch也不能重新接受同一个请求。 |
| 无submission的Issue续办也受回执保护 | `packages/core/src/services/issueRetryRequest.ts:650–652,719–773`、`src/jobs/issueJobDispatcher.ts:335–345` | 无任何request/consumed receipt时直接返回request:null，解释首次普通Issue缺口；已有accepted/consumed请求后，同trigger返回trigger:null，dispatcher直接skip。这是Issue25优先使用原生Follow-up的依据。 |

## 为什么不能只启用 failed-label helper

`packages/core/src/utils/errorHandler.ts:195–258` 的 helper 只删 processing、加 `AI-failed-<category>`并发表评论，没有移除AI trigger；实际 core 发现入口也不排除failed标签，因此不能停止下一轮。`handleError(...issueRef...)` 在170–177行以未await的异步方式调用它，不能作为可靠持久终态边界。helper评论说进入Dead Letter Queue，但这个函数没有入DLQ操作，且直接拼originalError.message；未经调用链、实际队列和脱敏复核，不应照搬这段评论作为已转人工证据。当前Issue处理走另一个 `src/jobs/errorHandlers.ts` 路径，不能因为找到同名helper就认定它已覆盖。

## 全部外部事件仍缺的最小衔接

优先使经授权的首批任务从既有 task-submission 入口创建，并使用原生 Follow-up 续办；这是现成流程接入选择，不能声称已解决任意已有Issue首次标签入口。针对已存在Issue，若长期要求所有首次AI标签事件在失败后默认等待人工，需要在共享core admission/dispatcher处补一处持久触发衔接：复用现有 task_history、GitHub labeled事件顺序及 submission/accepted receipt 语义，只在新、授权、可排序的trigger到来后放行。不能新增第二套job计数器/调度器，也不能自动给外部正文授予submission的扩展权限。

可审阅扩展点是 `processDetectedIssue` 与 `handleDispatchWithDeps` 的进入边界，或在原生submission创建服务增加经身份验证的existing-issue绑定；后者必须验证归属、禁止重复Issue、禁止凭文本生成扩展授权。二者是需要另行设计/实测的局部适配，不是已存在的开关。不要仅把失败label加入exclude：还需定义失败后人工重试如何清除标记、同秒label顺序、GitHub结果不确定、重启与并发，以及从哪个终态时刻开始阻断；更不能把失败改成done来抑制轮询。

下一轮验收应复用现有 dispatcher/followup/receipt 测试：同一label失败后连续poll不再执行、删children和重启仍不重复、真实人工新follow-up恰好一次、旧/乱序/同秒label fail closed、暂态API失败不丢请求、普通未启用维护政策的实例行为保持原状。当前政策252项测试不包含这些流程的全部上游测试，本次仅核查源码与既有测试，不补写通过数字。

## 补查：只配置BullMQ保留job能否替代新回执（2026-10-22）

该现成能力可以挡住**仍被Redis保留、同agent/model/base组合的同ID再次执行**，但仅把首次child和failed parent设`removeOnComplete/removeOnFail=false`不能作为当前共享队列的长期边界。此次未改源码或运行配置。

| 核查点 | 精确实现与结论 |
|---|---|
| 普通parent | core `daemon/issueDetection.ts:298–310`固定`issue-owner-repo-number`，3 attempts，complete/fail均true。父dispatcher只是手动添加child，不是等待child完成的BullMQ Flow；parent可以先completed，child后failed。 |
| 普通child | `src/jobs/issueJobDispatcher.ts:442–448`固定Issue/agent/model/baseBranch组合ID，当前remove= !submission。保留false会使BullMQ后续同ID add不执行新child；改变默认model或baseBranch则是另一ID，仍不能表达整个Issue总3轮。 |
| 人工新Follow-up | `childRunSuffix:285–287`有request时追加`-request-<request.id>-<commentId>`，所以保留首次child不妨碍新request child。现有request持久accepted/tombstone继续生效，无须另造receipt。 |
| Parent保留与重试 | `packages/api/routes/planIssueHelpers.ts:56–85`的nativeFollow-up enqueue也使用同一parent ID，并直接queue.add，没有检测已failed后job.retry或移除。若保留failed parent，新请求可能返回queued而被旧ID挡住；parent在建task之前失败时，TaskFollowup本身还缺任务身份。不能只改retain后声称人工续办仍正常。 |
| 现成手动retry入口 | BullMQ库有`Job.retry('failed')`；本项目已用在agentImagePreparationQueue.ts:151。当前API routeRegistry仅queue stats/activity/metrics，没有通用failed Issue parent retry端点；CLI/API检索未找到这一入口。受信运维直接调用原生Job.retry可作为明确一次人工操作，但不等同已有UI功能，也必须保留原parent请求身份、核失败态及无child/活动工作。 |
| 其他job的清理会影响保留 | 固定BullMQ **5.81.3**（package-lock.json:4919）`moveToFinished-14.lua:166–171`按当前完成job的age/count清理整个completed/failed集合；`removeJobsByMaxAge.lua:9–11`、`removeJobsByMaxCount.lua:9–11`不读取被删除job的removeOn选项。只给目标job设false不免疫共享队列其他job的年龄/数量清理。 |
| 当前队列默认 | `packages/core/src/queue/taskQueue.ts:102–108`completed保留24h/1000，failed保留7d。AgentRun/其他任务复用该issueQueue，保留的首次child仍可能被后续job清理；不是等待7d一定到时执行清理，而是在后续完成事件惰性触发。 |
| Redis与显式清理 | Compose已AOF+独立卷，能让尚存job跨正常重启保留；不保护被age/count清理、删卷/reset或人工remove的job。taskCancellation仅移除待执行项，不是终态清理的普遍保证；源码未见额外全局queue.clean定时器，但BullMQ原生惰性清理已足以构成缺口。 |

如要采用retain作为单仓低负担临时策略，必须同时证明**共享issueQueue全部产生者**均不再用age/count裁剪这些终态job、Redis容量与保留运维可接受、failed parent有显式原生retry操作、模型/base变更不绕过总任务限次。仅改变queue默认值仍会被各producer显式options覆盖；把整个队列永久保留也影响日报/PR任务的容量策略。故推荐先保留既有停止intake+原生人工Follow-up边界；若继续实现，应优先评审“原生持久触发衔接”与“统一队列retain+failed-parent native retry”的实际总改动，不把后者误认为两行配置即可完整解决。

官方锁定源码：[moveToFinished](https://github.com/taskforcesh/bullmq/blob/v5.81.3/src/commands/moveToFinished-14.lua)、[age清理](https://github.com/taskforcesh/bullmq/blob/v5.81.3/src/commands/includes/removeJobsByMaxAge.lua)、[count清理](https://github.com/taskforcesh/bullmq/blob/v5.81.3/src/commands/includes/removeJobsByMaxCount.lua)。[官方auto-removal说明](https://docs.bullmq.io/guide/queues/auto-removal-of-jobs)明确job移除后同jobId不再提供去重；这里额外核对了共享集合的实际Lua实现。

## policy5：纯标签失败停止的局部衔接（实施前登记）

2026-10-22 20:00左右。新增证据 `evidence/issue25-poll-receipt-readonly.json` 与 `issue25-label-timeline-readonly.json`：同一最初 AI 标签下有三条不同 correlation 的 failed task；期间没有新的 AI labeled 事件，task submission 和 retry request 均为零。任务状态与 GitHub 事件共同证明跨 poll 重新执行，不能以单 job attempts=3 宣称整个任务最多三轮。

选型继续复用固定上游 ProPR 的 `tasks`/`task_history`、认证 Follow-up、`selectRetryRun`、`enqueueIssueRetryRun` 和无到期 accepted receipt，不加新表、计数器、scheduler 或永久保留 BullMQ jobs。只在 `ONTICARDS_MAINTENANCE_MODE=1` 的 dispatcher 读取该 repo/issue、类型 issue 的持久失败终态；没有 submission 且没有原生 owed retry request 的投递进入等待人工。更换模型/base 或重新贴普通 label 不恢复预算。已有 child 的当前重试和限流恢复不经这个 parent admission gate，不改其既定 attempts。

恢复使用原生已认证任务详情 Follow-up（`POST /api/tasks/:taskId/followup`）创建真实请求/评论/触发；请求身份和 accepted tombstone 仍由原生服务核验与消费，仅准一次。维护模式现有失败评论将指向此入口，保留 failed，不伪装 done；普通模式文案和行为不变。父任务在任何 task 持久化之前失败，或实际 SQLite 写入失败导致根本没有持久终态，不能由此读取门禁补造事实；作为明确边界保留。

待验收：真实 SQLite 关闭/重开、queue 清理后多次 poll；repo/issue/type 隔离；更换 model/base 不绕过；数据库故障不放行；原生 request 的真实 SQLite/Redis accepted receipt 经清理/重启仍一次；旧/缺失顺序历史不放行；维护模式之外不受影响。构建由主流程在打包机统一进行，当前未部署，不提前标成功。

## policy5 已完成的源码和隔离验证

最终只改生产 `src/jobs/issueJobDispatcher.ts`、`src/jobs/errorHandlers.ts` 两个现有文件，新增单一测试文件 `test/maintenancePureLabelFailure.test.ts`。复用模式开关 `humanMergeOnly()`（读取受信宿主 `ONTICARDS_MAINTENANCE_MODE=1`），不新增配置开关。dispatcher 在原生 request/submission 解析后，只有无两种身份时读取 task 的最新 history；repo 忽略大小写、issue number 与 task_type=issue 精确过滤。正在进行/已恢复的历史 failed 行不会被当作当前失败，数据库读取异常不放行。已有失败终态保持不变，内部返回可追踪 taskId 和 Follow-up endpoint；现有 GitHub 失败评论只提示登录后“task details → Follow Up”，不泄露产品无关的 API 实现提示。

维护模式文案按实际 job opts/attemptsMade 区分：1/3 不宣称耗尽，仅说明既有 job 的剩余重试；3/3 才提示等待人工。非维护模式保留原有行为与原文。child processor、当前 attempts、限流 handoff、BullMQ cleanup 和原生请求状态机均未改。

验证来源 `evidence/policy5-pure-label-validation.json`，完整命令 `deploy/run-policy5-pure-label-tests.sh`。全部在打包机复用已有 policy4 测试镜像，临时文件 SQLite + 隔离真实 Redis，无互联网/凭据/生产数据：

| 验证 | 实测 |
|---|---|
| 改前旧源码 | 1条红例：failed持久化后重开数据库，纯label投递仍dispatched |
| 新增回归 | 5/5通过，0跳过；包含新Node进程读取同一SQLite失败记录、多poll/换model/base、repo/issue/type和最新状态、DB故障、1/3与3/3文案 |
| 人工恢复的实质路径 | 调用原生reserve/begin/record/select/consume；真实enqueueIssueRetryRun + Redis accepted tombstone；删除实际child、重连队列/SQLite后3次重复投递均skip，缺失触发事件历史defer，普通新relabel仍不能再生预算 |
| 既有dispatcher/submission/intake/receipt/usage-limit/provider来源回归 | 145/145通过，0跳过；此前无Redis的143+2skip日志按历史保留，最终必需Redis组已覆盖两项 |
| TypeScript整包编译、镜像和生产 | 主流程统一policy5执行，此文不提前声称完成 |

### 尚未覆盖的精确边界

门禁读取已有 `tasks/task_history`，**不覆盖 dispatcher 在 child 创建 Task 前自身终态失败**。这个路径 `handleDispatch` 不创建 Task；catch 的 `recordDispatchFailure` 只适用于已有原生 submission。无 submission 的纯标签父 job 如果在 GitHub 认证/label读取/目标选择阶段反复失败，清理后下一轮仍可能再次创建父 job。当前代码没有可直接配置、又不伪造 authenticated submission 的持久首投递回执；此次没有扩大成第二套任务系统。即使已有子任务失败，发现入口仍可能每poll加入一个立即skip的父job；本补丁停止的是新的child/模型执行预算，不假称完全关闭发现事件。

生产Issue25既有失败证据能被此门禁利用，但并未为证明补丁而重启intake、贴label、发Follow-up或触发模型。没有将隔离fixture中的认证请求视为生产用户操作的端到端验收。
