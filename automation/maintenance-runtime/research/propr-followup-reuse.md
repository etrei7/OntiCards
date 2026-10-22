# 原生续办、PR26审查与仅日报运行

2026-10-22。只读核实ProPR 0.9.0 / commit `42931b1502eb03ac299f14e306811736fab51eb4`，并区分本地维护政策补丁。未发评论、标签、任务或模型请求。

## 选择及新增适配原因

| 场景 | 已有实现 | 本次选择与边界 |
|---|---|---|
| Issue25失败重试 | `POST /api/tasks/:taskId/followup`；`taskIssueFollowup.ts:396,421` | 不用于认领PR26。失败task无pr_number时继续Issue25，target=pull_request也不能指定新的PR号码；自由文本不是可靠绑定 |
| PR26单次审查 | Task API所用 `prepareApiFollowup` + App原生issue-comment POST + `dispatchPostedFollowup`；worker原生 `/review` 分支 | 选用受信宿主一次性调用相同链，固定PR26/head/base/draft，先跑原生assignment gate；不开放新MCP endpoint。只补调用参数、预检、一次性证据/未知提交恢复，不编写Agent循环 |
| 克隆不稳定时审查 | `pr_review_context_enabled` 原生设置；GitHub diff/files上下文 | 无每次review独立覆写字段；本次不改全局scout设置。现有bootstrap和真实origin fetch已验；scout若失败，上游会继续确定性diff/files审查 |
| PR分支复用 | `PullRequestPublication` 从PR实际head定位；`createPullRequestHeadWorktree` | PR26同仓codex/fix-pdf-current-main满足维护政策，通常续办会更新原分支。选择/review则不进入正常实现/提交/推送路径 |
| 无权写分支 | 上游 `prContinuation.ts` 持久reservation、固定continuation分支、marker及GitHub head唯一性 | 这会创建另一continuation PR，不能承诺所有实现续办均“不新建PR”；本次审查前确认无待恢复handoff，避免先恢复旧发布 |
| 普通首次AI标签失败循环 | 初次issue-only投递无持久消费receipt；30秒dedup、active/waiting与BullMQ jobId仅短期去重 | 现有3 attempts不是跨轮询总预算。失败移除processing而保留AI；child removeOnFail=true可在下一轮重新创建。此缺口必须保留 |
| 已有失败Issue受控重试 | `issue_retry_request_states` + 原生followup route + queue receipt | 人工明确重试已有失败任务时复用此路径，可消费对应label事件、避免重复轮询。同一方案尚未覆盖无request的第一次普通label |
| 立即抑制Issue25重复实施 | 现有仓库enabled=false；或移除AI、已有AI-cancelled终止标记 | 本次保持仓库监控关闭，仅直接触发PR26审查。不可改成AI-done伪称成功；普通入口全局三轮总预算仍需后续窄适配 |

## PR26内部入口

编译后可精确导入：

```js
import { prepareApiFollowup, dispatchPostedFollowup } from './packages/core/dist/webhook/commentEventHandler.js';
import { commentAuthorMayFollowUp } from './packages/core/dist/webhook/followupAssignmentGate.js';
```

`prepareApiFollowup(redis,{owner:'stepll2026',repo:'OntiCards',prNumber:26},body)`在POST前注册真实marker，避免App评论被轮询/回调抢走。真实POST成功后，把真实comment id/time/author和原始正文传给`dispatchPostedFollowup`；`userId='318866723'`代表已由维护者授权的调用者，不冒充App评论作者。原生atomic claim为`pr-comment-processed:stepll2026:OntiCards:26:<comment-id>`；未知结果不能重新POST。失败/超时应根据已注册的完整marker查真实评论，再只dispatch该评论；原生claim已存在时返回unknown并人工查收据，不强删锁。

准确正文第一行：`/review opencode-bailian/qwen3.8-max-0902`，随后中文AI标识、审查范围和证据限制。PR必须仍open、draft=true、head=`3105b7b61469c6b2945357f2eefa8fcb2e3aaee5`、base=`c8e3dfee68d398a37842fc332f73af40a56f02a7`，head仓库同源、branch=`codex/fix-pdf-current-main`。这些是投稿前条件，不是锁定远端；完成时仍须核对实际reviewedHead与当前head。

**必须给PR26加现有AI标签**：`processPullRequestCommentJob.ts:137`在review共用校验中要求primary processing label；不加会skip。仅保留其他label并追加AI，不动Issue25。任务终态前不可撤掉标签。repo DB disabled确保此标签本身不开放全仓polling。

`processPullRequestCommentJob.ts:453`对review提前分支，不进入`executeProcessing`发布路径；`prReviewRunner.ts:142`调用`agent.analyze`，`OpenCodeAgent.ts:148`创建readonly分析workspace。可选scout在`prCommentReviewJob.ts:316`以后尝试clone，失败可回到确定性上下文；`reviewRuntimeSettings.ts:29`读全局`settings.pr_review_context_enabled`。本次“后台PR审查成功”仍不能算Issue25“自动Issue→修复PR成功”。

一次性脚本 `deploy/propr/review_pr26_once.mjs` 默认只读。`--apply`才有标签/评论/队列副作用；`--resume`只恢复同一已注册、作者为已验证App bot的唯一评论，要求Redis原生registration精确匹配，绝不再次POST。投稿所用App专属短令牌限定单仓，pull_requests write、contents/issues/metadata read；不授予contents write，不传给模型；finally撤销。`--resume`和默认预检仅mint read令牌。仓库公开元数据用无凭据Octokit读取，GET /app使用App JWT。全局scout保持不变。默认模式若已存在PR26绑定task会拒绝，因为native assignment gate会刷新其assignee投影，不能把这称为纯读。无待恢复PR发布记录且队列空才允许投稿，daemon可继续仅日报调度。以上为调用现成链所必需的部署适配，不是新服务。

### PR26 prepared阶段权限修正及验证

主流程真实首次`--apply`在追加AI标签时收到403 `Resource not accessible by integration`；原scoped token为issues write、pull_requests read。收据仍prepared、labelAdded=false、comment/jobId为空，未发表评论/dispatch且令牌已撤销。此处记录主流程已核验的现场结果，不把本子任务无网mock当GitHub实测。[官方标签接口](https://docs.github.com/en/rest/issues/labels#add-labels-to-an-issue)与[评论接口](https://docs.github.com/en/rest/issues/comments#create-an-issue-comment)列出Issues write或Pull requests write能力。本次固定PR26改为后者，仍在现有App安装权限内，不调整App权限或仓库授权。

`--resume-prepared`只接受原prepared、目标/branch/正文完全一致、没有comment/job/outcome/commentPostAttemptedAt/resumePreparedAttemptedAt，且原生Redis marker仍精确匹配的收据。全量分页评论中一旦已有同正文或marker即拒绝；通过后先exclusive-create保存`.before-resume-prepared.json`，再记录这一次恢复尝试。随后才可追加AI并仅POST一次；写前存comment_post_attempted及时间。POSTattempted/unknown状态绝不能走此模式，已有评论仅用`--resume`原生claim恢复。原receipt快照和403失败记录不得删除；一次prepared恢复再失败则人工复核，不自动重复。

无网络、无凭据、无模型校验`node deploy/propr/verify_review_pr26_adapter.mjs`真实执行适配脚本正文，注入内存FS/SQLite/Redis和假HTTP，共11项通过：只读零发布、label403保留prepared、保存原收据后恰好一次评论/dispatch、未知POST/已attempt/目标或正文变化/marker过期/已有同marker/重复prepared恢复拒绝、已发评论恢复只读不POST。结果`evidence/pr26-review-adapter-validation.json`；这不证明修改权限后真实GitHub调用已成功，须主流程审阅后显式执行。

### 已发布评论后的原生依赖注入修正

主流程`--resume-prepared`已成功追加AI并发布唯一评论6339444121；dispatch在`loadUltrafixDeps()`报未初始化而中断，原收据为dispatch_unknown。错误原文独立保存在`pr26-review-dispatch-bootstrap-failure.json`，不回填假装旧收据本来记录过异常。

源码顺序为`dispatchPostedFollowup:815`取得claim→`handleSlashCommand:301`→`fenceManualCommand:247`在调用invalidateAutomaticWork之前load抛错；getExistingPRCommentJobs、batch及enqueue均在之后。API原生`ultrafixInit.ts`的前两步是createUltrafixDeps()+setUltrafixDeps；整个initializeUltrafix另含立即sweep及interval，因此适配只复用前两步。已在实际policy4 API容器只读导入并set，得到invalidateAutomaticWork=function，无sweep/模型/GitHub动作。

11:21:59Z独立SSH快照`pr26-review-claim-readonly.json`：原claim=1792667888534，TTL86169240ms，PR26任务/各状态匹配job/待评论/loop/epoch/deferred/ci-wait/rearm/manual-takeover均空，repo disabled。原收据真实字节另存`pr26-review-receipt-before-bootstrap.json`，SHA256 aa854c184754ed15d6366dfd379b1b6358ba0383c91d63ec1f248d213b355d5f。

新增显式`--resume-bootstrap`仅匹配此精确comment、job、原收据SHA和claim值；原生registration和GitHub唯一真实Bot评论仍须匹配。再次核DB/所有job状态/Redis义务为空，exclusive保存原收据和claim/TTL证据；Lua原子比较原claim并再次检查待处理键及queue长度后才DEL这一key，随后同一进程原生dispatch一次。任何不同claim、旧收据变化或pending工作都拒绝，无通用unknown解锁、不重发评论、不伪造任务。CAS后如进程中断，不自动重复；固定快照/attempt标记将阻止再次使用此专用模式。今后dispatch异常原文按实际发生时间保存在收据dispatchError中。

隔离适配校验增至16项，追加精确bootstrap恢复一次/只读token/不POST，以及claim变化、pending工作、原收据变化、CAS竞争拒绝。旧11项结果保留pre-bootstrap文件。mock不验证GitHub或Redis服务实际入队；真正恢复仍由主流程审阅并显式执行。

## 普通Issue咨询/缺信息

`webhookHandler.ts:271`只将带pull_request的issue_comment送入PR评论处理；普通Issue评论返回not_pull_request_comment。`slashCommandParser.ts:8`只支持review/fix/merge/switch/use/ultrafix，没有ask/discuss。Planner refinement有answered/clarifying，但服务对象为规划草稿，不能冒充对普通Issue自动答疑。原生Automation可读材料并产出triage报告，但没有已核实的“普通Issue回复+评论水位+跨轮预算”链。

因此已验证n8n原生Schedule/HTTP/结构字段/DataTable较适合补普通Issue分类和回复；仍须把已列明的完整事件水位、原子去重、三轮上限、POST未知恢复与App发布闭环作为缺口。不能用ProPR的PR实现续办替代咨询回复，也无需再创造一个通用事件平台。

## 仅日报daemon及恢复检查

`configManager.ts:178`仅加载enabled仓库；`configLoader.ts:208`在无环境GITHUB_REPOS_TO_MONITOR覆盖时用DB。`agentRunTrigger.ts:266`只对definition.repositories非空验证仓库，因此现有repos=[]日报不受仓库disabled影响。daemon.ts:293仍独立启动AgentRun sweep；249处明确零仓库也保持运行。

daemon全局恢复：ultrafix resume、epic merge-progress重试、plan auto-merge、AgentRun deferred/stuck/grant清理；draft context/rescue bundle为TTL清理，diagnostics为元数据盘点。Issue intent reconciliation在taskIntent.ts:448/465按传入repos过滤。goals/任务replacement/CI/handoff恢复位于已运行worker的worker.ts:398，非daemon新入口，但启用前也查空。

已准备的enable_daily_only.mjs检查队列、pending_schedule_slot、非终态AgentRuns、所有PR恢复表、goals、plan_issues、task_submissions、issue_retry_request_states、task_drafts、replacement_request，以及ultrafix state/deferred/ci-wait/rearm-retry/index和epic:merge-progress-retry；不删除记录，非空即停。它用原生服务同事务禁用仓库、启用definition，并强制nextRunAt等于调用者传入的未来UTC时刻。root另行执行，脚本不启动daemon。

10:42Z/10:48Z只读现场：无环境仓库覆盖；4个PR恢复表和上述6个附加SQL计数均0。说明不是原生调度实跑证据。调度启用/启动的结果由root独立记录。
