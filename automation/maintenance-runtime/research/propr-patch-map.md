# ProPR 完整补丁分组映射（冻结 policy13）

基线 ProPR 0.9.0 / Apache-2.0，固定上游 `42931b1502eb03ac299f14e306811736fab51eb4`。完整补丁 SHA256 `91c2d151fd95ff6fcd634fc73d553a6fcc84674f481b3a7ce7b48eb11ea0273b`，Git tree `0af2178f1461819a893d6705a0e23dcad6330595`。本表只描述冻结源码，不能替代当前部署 manifest。policy13 构建、回归和 registry digest 见 evidence/propr-policy13-validation.json；运行状态另见 deployment receipt，不能用源码冻结代表部署完成。

共 94 文件，54 生产文件、40 测试/fixture。行数是相对上游 Git diff 的实际新增/删除行，不是文件总长或测试覆盖率。一个文件只计一次；共享入口的其他原因在组说明中明确。没有修改上游依赖版本。

## 逐组原因与文件

### 内网 HTTP 会话与现有管理员授权

真实私网 HTTP 登录 cookie/redirect 不兼容，以及已登录 GitHub displayName 与实际 username 授权回退错配。

继续用原 OAuth、session、CSRF 和授权配置；仅在显式开关、完全相同 canonical RFC1918 origin 且无 COOKIE_DOMAIN 时允许 HTTP cookie，既有 GitHub login 优先于 displayName。未另建身份服务。

证据：[propr-intranet-http-reuse.md](../research/propr-intranet-http-reuse.md)、[github-display-name-reuse.md](../research/github-display-name-reuse.md)、[propr-policy6-validation.json](../evidence/propr-policy6-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/api/auth.ts` | production | extended | +1 / −1 |
| `packages/api/authInternalHttp.ts` | production | new | +21 / −0 |
| `packages/api/authRedirect.ts` | production | extended | +5 / −0 |
| `packages/api/authSession.ts` | production | extended | +2 / −0 |
| `packages/api/authorization.ts` | production | extended | +1 / −1 |
| `packages/api/test/authInternalHttp.test.ts` | test | new | +92 / −0 |
| `packages/api/test/githubAuthCallback.test.ts` | test | extended | +43 / −1 |
| `packages/api/test/instanceAuthorization.test.ts` | test | extended | +15 / −0 |

### G05 人工合并、宿主发布与 Agent 只读凭据

仅关闭界面 autoMerge 仍有 REST/MCP/continuation/rescue/goal 入口可写或合并；已有普通分支并非 codex/。

复用原生 central merge gate、权限拒绝码、continuation PR、host push、read-only scoped token；在最后写入口拒绝合并、非 codex/ refspec、writable Agent token 和 goal/orchestrate。原生 continuation 继续工作，未创建发布系统。

证据：[orchestration.md](../research/orchestration.md)、[propr-followup-reuse.md](../research/propr-followup-reuse.md)、[propr-policy4-validation.json](../evidence/propr-policy4-validation.json)、[propr-policy5-validation.json](../evidence/propr-policy5-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/api/mcp/toolsPullRequests.ts` | production | extended | +2 / −1 |
| `packages/api/test/mcpMergePreconditions.test.ts` | test | extended | +14 / −0 |
| `packages/core/src/agents/agentGitAccess.ts` | production | extended | +3 / −0 |
| `packages/core/src/git/pushSalvage.ts` | production | extended | +2 / −0 |
| `packages/core/src/git/repoBranching.ts` | production | extended | +3 / −0 |
| `packages/core/src/index.ts` | production | extended | +2 / −1 |
| `packages/core/src/services/autoMergeGate.ts` | production | extended | +6 / −0 |
| `packages/core/src/webhook/checkRunHelpers.ts` | production | extended | +3 / −0 |
| `packages/core/src/workflow/maintenancePolicy.ts` | production | new | +15 / −0 |
| `packages/core/test/autoMergeGate.test.ts` | test | extended | +18 / −0 |
| `packages/core/test/maintenanceBranchPolicy.test.ts` | test | new | +14 / −0 |
| `src/github/autoMergeOperations.ts` | production | extended | +3 / −1 |
| `src/jobs/prContinuation.ts` | production | extended | +2 / −1 |
| `src/jobs/prPublication.ts` | production | extended | +12 / −1 |
| `src/jobs/prPublicationGit.ts` | production | extended | +4 / −1 |
| `src/jobs/processSystemTaskJob.ts` | production | extended | +2 / −1 |
| `test/agentGitAccess.test.ts` | test | extended | +15 / −0 |
| `test/autoMergeOperations.test.ts` | test | extended | +12 / −0 |
| `test/checkRunHandler.test.ts` | test | extended | +10 / −0 |
| `test/prContinuation.test.ts` | test | extended | +55 / −0 |
| `test/workflowPreviewPublication.test.ts` | test | extended | +3 / −1 |

### G05 测试机禁止镜像构建

上游 Agent image 自动准备会在测试机执行 docker build，违反两机职责。

复用既有 image inspect/缓存与 Docker executor，只在维护模式实际 build 之前拒绝；镜像须由打包机准备，现成镜像照常运行。

证据：[orchestration.md](../research/orchestration.md)、[propr-policy4-validation.json](../evidence/propr-policy4-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/claude/docker/dockerExecutor.ts` | production | extended | +4 / −0 |
| `test/maintenanceDockerBuildPolicy.test.ts` | test | new | +49 / −0 |

### 30 天运行日志保留配置

原生 live output 的固定 TTL 不能表达附件要求的 30 天，不能只改外部文档。

在原 Redis 日志写入路径加入受信 TTL 配置和界限验证；沿用原生键、续期、读取与清理，无新增日志服务。

证据：[acceptance-gap-audit.md](../research/acceptance-gap-audit.md)、[propr-policy5-validation.json](../evidence/propr-policy5-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/agents/impl/utils/liveOutputLog.ts` | production | extended | +12 / −1 |
| `test/liveOutputLog.integration.test.ts` | test | extended | +29 / −1 |
| `test/liveOutputTtlConfiguration.test.ts` | test | new | +42 / −0 |

### 审查执行、产物有效性与未知 token

实际 review 配置副本只有根目录改 UID，子文件不可读；原 analyze 默认 30 分钟超出部署上限；provider 失败/结构无效仍被记为 passed，缺 token 被强制变成 0。

沿用原 snapshot、UID1000、执行 timeout、effectiveReviewScore 严格 parser、Task FAILED 和数据库 NULL；无效原文/usage 保留，不生成伪 findings，不放宽 schema。policy13 复用原生 GitHub GET 在发布前验证实际收集的 head/base，失效走 FAILED 并保留 raw/usage/time。OpenCodeAgent 还共享知识预算的 remaining deadline，避免复制 snapshot 后重开时间窗。

证据：[pr26-policy5-review-validation-gap.md](../research/pr26-policy5-review-validation-gap.md)、[pr26-policy6-review-quality.md](../research/pr26-policy6-review-quality.md)、[pr26-policy6-review-validation-tests.json](../evidence/pr26-policy6-review-validation-tests.json)、[knowledge-native-refresh.md](../research/knowledge-native-refresh.md)、[mcp-review-machine-auth-reuse.md](../research/mcp-review-machine-auth-reuse.md)、[propr-policy13-validation.json](../evidence/propr-policy13-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/agents/impl/OpenCodeAgent.ts` | production | extended | +20 / −2 |
| `packages/core/src/utils/llmMetrics.ts` | production | extended | +14 / −3 |
| `src/jobs/prCommentReviewJob.ts` | production | extended | +11 / −4 |
| `src/jobs/prReviewRunner.ts` | production | extended | +13 / −5 |
| `src/jobs/reviewResultMetrics.ts` | production | extended | +1 / −1 |
| `test/analysisGitAccess.test.ts` | test | extended | +103 / −3 |
| `test/fixtures/pr26-invalid-review.json` | test | new | +8 / −0 |
| `test/llmMetricsRecording.test.ts` | test | extended | +29 / −0 |
| `test/prCommentReviewFollowupScope.test.ts` | test | extended | +55 / −4 |
| `test/prReviewRunnerBudget.test.ts` | test | extended | +3 / −2 |
| `test/prReviewValidation.test.ts` | test | new | +112 / −0 |
| `test/reviewResultMetrics.test.ts` | test | new | +21 / −0 |

### 纯审查禁止恢复旧写入、可信无标签授权及两 SHA 一致性

上游纯 /review 仍先恢复旧 handoff/publication，可能发布代码；worker 无标签必跳过；上下文仅 head 校验且发布前没有 head/base 校验。

复用 native PR lease、humanMergeOnly、typed commandMode/内部 Ultrafix meta 区分、作者白名单及权限 gate、live GitHub comments、原 parseSlashCommand/buildCommandMeta。纯 review 不碰旧恢复或预算；无标签例外绑定最初入队正文与 commentId，拒绝编辑及隐式 bot 名匹配，fix 仍需标签。复用现有 GitHub GET 和 Task FAILED，保留实际 reviewed base。共享 runner/history 文件归 analysis-and-review 组。没有新服务/表/队列；GET→POST 仍非原子。

证据：[mcp-review-machine-auth-reuse.md](../research/mcp-review-machine-auth-reuse.md)、[propr-policy13-validation.json](../evidence/propr-policy13-validation.json)、[policy13-independent-review.json](../evidence/policy13-independent-review.json)、[policy13-author-filter-independent.json](../evidence/policy13-author-filter-independent.json)、[policy13-queued-body-independent.json](../evidence/policy13-queued-body-independent.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `src/jobs/processPullRequestCommentJob.ts` | production | extended | +38 / −7 |
| `src/jobs/reviewCommentFormatter.ts` | production | extended | +4 / −2 |
| `src/jobs/reviewContextHelpers.ts` | production | extended | +19 / −5 |
| `test/maintenanceReadOnlyReview.test.ts` | test | new | +261 / −0 |
| `test/reviewContextHelpers.test.ts` | test | extended | +6 / −2 |

### 首次 AI 标签 Issue 跨轮询失败停止

原 BullMQ child 清理后下一次 poll 可重生；父分发失败没有 Task，或 SQLite failed 终态写入丢失时，旧 failed-only 门禁也会漏过。

复用原生 WorkerStateManager/Redis NX 和现有 tasks/history：纯标签首次先建真实分发 Task 并读回 SQLite task+pending，再允许入队；已存在任何同 Issue 实现记录均不因普通 poll、队列清理或模型/base 变化再获预算。父失败复用 UnrecoverableError；未知终态仍封闭。原存储清理保护这条首投递证据，已认证 Follow Up 仍先解析并沿原 accepted tombstone 一次执行。无新表、计数器或receipt平台。

证据：[cross-poll-retry-reuse.md](../research/cross-poll-retry-reuse.md)、[pure-label-admission-reuse.md](../research/pure-label-admission-reuse.md)、[policy5-pure-label-validation.json](../evidence/policy5-pure-label-validation.json)、[propr-policy12-admission-validation.json](../evidence/propr-policy12-admission-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/storage/taskHistoryControl.ts` | production | extended | +3 / −0 |
| `src/jobs/errorHandlers.ts` | production | extended | +19 / −3 |
| `src/jobs/issueJobDispatcher.ts` | production | extended | +65 / −2 |
| `test/maintenanceLabelAdmission.test.ts` | test | new | +174 / −0 |
| `test/maintenancePureLabelFailure.test.ts` | test | new | +173 / −0 |

### Git 准备有界与取消

Issue32 原生 Stop 已持久 cancelled，但 clone 子树仍运行；Agent 600 秒不覆盖 Git 准备。

复用 simple-git 4.0.2 原生 AbortSignal/timeout、现有 Redis abort checker 和 monotonic deadline，作用于现有 hookless Git/clone/worktree；不加通用进程管理器。Git 准备期限不等于包含所有 HTTP/模型/发布的整任务期限。

证据：[issue32-git-preparation-gap.md](../research/issue32-git-preparation-gap.md)、[issue32-operator-git-cleanup.json](../evidence/issue32-operator-git-cleanup.json)、[propr-policy7-validation.json](../evidence/propr-policy7-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/claude/docker/dockerAbortController.ts` | production | extended | +25 / −14 |
| `packages/core/src/git/hooklessGit.ts` | production | extended | +36 / −0 |
| `packages/core/src/git/repoManager.ts` | production | extended | +3 / −1 |
| `packages/core/test/dockerAbortController.test.ts` | test | extended | +1 / −1 |
| `src/jobs/issueJob/types.ts` | production | extended | +2 / −0 |
| `src/jobs/issueJob/worktree.ts` | production | extended | +7 / −6 |
| `src/jobs/processGitHubIssueJob.ts` | production | extended | +4 / −3 |
| `test/nativeGitPreparation.test.ts` | test | new | +128 / −0 |
| `test/taskSubmissionLifecycle.test.ts` | test | extended | +2 / −0 |

### 知识 SHA 一致性、预算、准备期限与失败投影

G-K01 origin SHA 与可变 checkout 内容不一致；G-K02 跟随 symlink；G-K03 无总分析额度；G-K04 三个入队准备入口可能无限 clone；G-K05 BullMQ attempts3 重开额度且部分失败被记 completed。

复用 Git detached worktree、lstat、原 native file/blob 增量、SQLite、AsyncLocalStorage、OpenCode deadline、withGitPreparation、BullMQ attempts=1/UnrecoverableError 和 branch 状态。6 analysis/600秒共享预算；clone+freshfetch共120秒；失败保留 partial，原生显式新 job 可恢复。默认分支重复使用已有 baseBranch=main 配置修正，不造新分支映射器。

证据：[knowledge-native-refresh.md](../research/knowledge-native-refresh.md)、[indexing-before-budget-stop.json](../evidence/indexing-before-budget-stop.json)、[indexing-outcome-events.json](../evidence/indexing-outcome-events.json)、[propr-policy9-build-validation.json](../evidence/propr-policy9-build-validation.json)、[propr-policy12-patch-validation.json](../evidence/propr-policy12-patch-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/api/routes/indexingQueueHelpers.ts` | production | extended | +24 / −14 |
| `packages/core/src/queue/taskQueue.ts` | production | extended | +2 / −1 |
| `packages/core/src/services/relevance/indexingCancellation.ts` | production | extended | +42 / −0 |
| `packages/core/src/services/relevance/summaryFileFilter.ts` | production | extended | +1 / −1 |
| `packages/core/src/services/relevance/summaryMiner.ts` | production | extended | +42 / −18 |
| `packages/core/src/services/relevance/summaryMinerBatch.ts` | production | extended | +5 / −0 |
| `packages/core/src/services/relevance/summaryMinerDirectoryBatch.ts` | production | extended | +6 / −0 |
| `src/indexing_worker.ts` | production | extended | +39 / −19 |
| `test/indexingDeadlineProcess.test.ts` | test | new | +31 / −0 |
| `test/indexingFreshFetch.test.ts` | test | new | +90 / −0 |
| `test/indexingPinnedRevision.test.ts` | test | new | +145 / −0 |
| `test/indexingPreparationDeadline.test.ts` | test | new | +123 / −0 |
| `test/indexingQueueBudgetIntegration.test.ts` | test | new | +128 / −0 |
| `test/indexingRunBudget.test.ts` | test | new | +109 / −0 |
| `test/summaryFileFilter.test.ts` | test | extended | +12 / −0 |

### 冲突确定性合并与人工分流

原生任何冲突都交模型，残留 conflict marker 仅 warning；无法从文字冲突判断业务语义正确。

复用 Git clean merge、unresolved 检查、rollback、既有 failed/human history；维护模式真正未解决冲突停止在模型前。覆盖文本/二进制冲突，不声称判断所有语义冲突。

证据：[native-semantic-review-reuse.md](../research/native-semantic-review-reuse.md)、[conflict-human-gate-candidate-files.json](../evidence/conflict-human-gate-candidate-files.json)、[propr-policy8-validation.json](../evidence/propr-policy8-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/git/conflictResolution.ts` | production | extended | +7 / −1 |
| `packages/core/test/conflictResolution.test.ts` | test | extended | +77 / −0 |
| `src/jobs/mergeConflictAgentRunner.ts` | production | extended | +20 / −13 |
| `src/jobs/mergeConflictHelpers.ts` | production | extended | +8 / −2 |
| `test/mergeConflictHelpers.test.ts` | test | extended | +11 / −0 |
| `test/processMergeConflictJob.test.ts` | test | extended | +44 / −0 |

### 真实 PR33 Draft 与未知费用发布

原生 Issue→PR 创建写死 draft=false；供应商未给价格却公开 $0.00。

使用现成 GitHub draft 字段和原模板 nullable cost；不新建 PR 发布器，也不把未知金额推定免费。

证据：[pr33-publication-reuse-gap.md](../research/pr33-publication-reuse-gap.md)、[propr-publication-fix-validation.json](../evidence/propr-publication-fix-validation.json)、[pr33-publication-correction.json](../evidence/pr33-publication-correction.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `packages/core/src/utils/github/logFiles.ts` | production | extended | +7 / −3 |
| `packages/core/src/workflow/prTemplate.ts` | production | extended | +2 / −2 |
| `src/github/prFormatters.ts` | production | extended | +6 / −4 |
| `src/jobs/issueJobHelpers.ts` | production | extended | +2 / −1 |
| `test/maintenancePublication.test.ts` | test | new | +70 / −0 |

### 原生日报事实缺失的终态

原 dry-run 报告自由文本 WAITING_FOR_FACTS/INPUT_INVALID 也被记 completed，不能形成原生失败待办。

在既有 AgentRun result-state 入口识别部署输入契约失败，复用原 Task/AgentRun 失败路径，不另建日报调度器；这不替代自然语言质量人工审查。

证据：[daily-result-state-reuse-gap.md](../research/daily-result-state-reuse-gap.md)、[propr-policy8-validation.json](../evidence/propr-policy8-validation.json)。

| 文件 | 类型 | 新增/扩展 | +行 / −行 |
|---|---|---|---|
| `src/jobs/agentRuns/dailyReportContract.ts` | production | new | +25 / −0 |
| `src/jobs/processAgentRunJob.ts` | production | extended | +9 / −0 |
| `test/processAgentRunJob.test.ts` | test | extended | +64 / −0 |

## 单独的 HTTP UI 补丁

API/app 完整补丁不包含 UI。`deploy/propr-ui-http-compat.patch` SHA256 `6e578fcc8ab923ecc53b463cdabe63fe96436cdf50a957a8002e1cbeed4ec236`，4文件：NewTaskPage.tsx、NewTaskPage.test.tsx、propr-ui/package.json、package-lock.json。复用已有 uuid 14.0.1（MIT）的 WebCrypto getRandomValues；ID 生成纳入原 try/finally，同 key 恢复逻辑保留。没有 Math.random 降级。HTTP 浏览器 2/2、页面22/22；完整 UI typecheck 仍有与基线相同的既有诊断，不能声称全仓通过。见 [复用原因](propr-intranet-new-task-reuse.md) 与 [验证](../evidence/new-task-http-validation.json)。

## 精确应用、升级与回滚

1. 从上游固定 commit 的干净源码开始。核完整补丁 SHA；执行 `git apply --check` 后 apply，再核 manifest 中每个 blob。完整补丁不能叠加在旧 policy 的修改工作树上；只能从指定基线使用对应 delta。
2. `export-propr-policy13.py` 从冻结 policy12 tree 只叠加10个允许文件并导出完整补丁；临时 index 从固定上游 apply 完整补丁得到同一 tree。交付重建使用 `prepare-propr-policy13-source.py`：固定上游 Git 对象 + 完整补丁 + validation manifest，无旧 policy 私有 tar/修改工作树依赖。
3. 仅 kol-stage2 执行 `build-propr-policy13.sh`：官方构建阶段编译、原回归和真实独立 Redis 测试，再按 registry digest 交部署审阅。升级不能跳过真实旧 attempts3 和 partial-failed 投影测试。默认配置变化不会改写旧 Redis job opts，必须保留入口 guard。
4. 生产切换前停止并核清旧索引运行/容器，保留 partial 与历史，不直接重试未知旧 job。通过原生明确新 job 恢复；同名索引 branch 使用现成 baseBranch。数据库及队列不是补丁内容，不能用源码回滚假定回滚运行状态。
5. 上游升级需重新检查每组扩展点是否已被原生覆盖，能删除的适配优先删除；禁止盲目 fuzzy apply。镜像可回退已记录 digest，但索引应维持 disabled 直到旧队列/状态边界复核，不能回退后自动重开预算。

## 历史补丁哈希

以下是历史冻结记录；同名旧交付路径可能后来用于 policy8，不能将历史哈希解释为该路径的当前字节。policy9/10/11/12/13 独立文件均保留。

| Policy | 文件数 | tree | 完整 patch SHA256 |
|---|---:|---|---|
| 4 | 30 | `4c7600d867a56f794128f3b12af49611690fae13` | `8232c76b8ccd7bd1bce6b6a1a23dfa1c695bcfd13f246c69b5ab7a0e3b0b6306` |
| 5 | 41 | `a11d7f3cb0df0f0b6254e3d1a8d05e9d3adacd96` | `07f050f9ffe0f38b37e1b46a5a9df2e125f9e02578e9ebdaba8834a9e89a443f` |
| 6 | 49 | `efa47fa828a5032ebcc6c67e7e3f75276ad34048` | `750690b89497cd8e66ac52226cdece9d62dac64c5c5e6ad6328c04338fb643c0` |
| 7 | 58 | `3df474a18c69018a47b1389506bad38c65e9abb8` | `79dac6d988109d0cf0e97d1cb1d7a5090f309689d94e0d3418165733520c5f70` |
| 8 | 79 | `7d3af65f3e0fc702ed89103291e2dcc7101f4fdd` | `7d585dd8ffd379cb3908f65e7f34dc909e03aecfd74adb10645fe89ab36b2fa5` |
| 9 | 84 | `555f1a7d4c24192e108503be371ec0c05faf2ec6` | `eb62d0af8a1240f7bf75a94a1f526edaf696eea3890fd70481fe878a33b52ff8` |
| 10 | 85 | `34be674fa6c23301594a7304934c1fd0a361fd43` | `d29d0a40af595d9dd3cf595dd3d386a3422e0425df19740de63b20f5442cab4d` |
| 11 | 87 | `c5ace8247411ee8c33802a62169fd02e54d0378b` | `bcf33d2adc53582de662aafa7da114c1a211ab3f0dd9064712630a446be3ac4f` |
| 12 | 89 | `b3dd9a914e431b15b41febbf97211d736e6428fd` | `6faa1328f318ceff10c018271222a5f3a7828c022f30417167246b9f111ca2a7` |
| 13 | 94 | `0af2178f1461819a893d6705a0e23dcad6330595` | `91c2d151fd95ff6fcd634fc73d553a6fcc84674f481b3a7ce7b48eb11ea0273b` |
