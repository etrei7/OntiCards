# 常驻咨询发布候选：原生节点与审阅边界

2026-10-22；候选文件 `persistent-publication.workflow.json`，生成器 `build_persistent_publication.py`，39 个原生节点。当前没有导入、没有激活，`publication_enabled=false`、`approval=null`，未执行 GitHub 写入。

复用 n8n 2.42.7 Schedule、Webhook、DataTable、If、Set、Crypto、JWT 和 HTTP Request。App JWT/短期安装 token 的轮换使用原生节点；不新建调度器、API 客户端或状态服务。既有 Issue29 的两次实际发布与顺序 sticky 回放仅证明原有受控路径，不能冒称这个39节点候选已完成真实发布或并发验收。

## 可审阅流程

1. 原生五分钟 Schedule 与 loopback Webhook 进入同一条链。Webhook 请求内容不形成批准；仅使用部署者提供的可信批准配置，固定单仓库。
2. 从已有草稿和会话 DataTable 读取原模型结果与来源。Crypto 重算 source/body SHA256；批准必须精确绑定 event key、source hash、body hash、人工 reviewed 标记和正文 marker，原草稿仍须 `awaiting_semantic_review`。
3. JWT 用已有受限 App 凭据签名，申请仅单仓库 `issues:write`、`pull_requests:read`、`contents:read`、`metadata:read` 短期 token；原生 GET 核实实际仓库与权限严格相等。
4. 原生 HTTP 完整读取 Issue、评论、PR head/base、inline/reviews 与当前源码 commit。所有分页必须200数组且末页无next；评论中此前所有本App回复均计数（不按marker归零），最多三条。
5. 已有 `posting_unknown` 或 `published*` 状态及其原始 body/hash/source hash 优先保持；读失败、marker冲突、新批准或来源变化都不能将其恢复为可POST。未知请求只能GET对账；已发布评论被删除也不会自动补发。
6. 仅全量来源仍与批准时一致、预算和会话预约相符时，先将 `posting_unknown` 原生 Upsert 到持久表，再执行唯一评论 POST。POST没有重试；随后的GET核对完整正文、marker、App数字ID、login和Bot类型。网络异常保留unknown。
7. 只有GET确认且本次批准hash与已发布意图一致，才合并人工审过的 observed_fields、已问字段和已答人类ID；publication ID 去重，重复对账不会重复应用旧会话增量。原model_calls不归零。根审查发现原先从模型 `missing_evidence` 写入已问字段可能与人工修订后的正文不同，现改为批准对象的 `asked_fields`，必须显式 `asked_fields_reviewed=true`、字段在允许表内、不是已知/本次已提供字段，并与最终body hash共同绑定；原模型文本保留。
8. Scope拒绝/无POST/POST各分支均汇入原生DELETE撤销安装token和最小回执。执行被强制终止时不保证撤销；须诚实标未知并等待自然到期，不能把原生设计目标当实测成功。

## 当前还需验证

- 独立审阅这39节点的完整连接和 sticky 分支；现有局部表达式解析通过不等于原生运行通过。
- 通过原生本地 HTTP fixture 做未知POST→GET失败→恢复、旧批准变化、重复对账和预算上限；不调用真实GitHub POST，不消耗模型。
- Issue31需先按 `issue31-manual-resume-review.md` 明确人工恢复，取得真实草稿并逐句审阅；当前首次模型结果未知，无可发布正文。
- 生产并发限制1仅约束该独立实例生产入口；不声称DataTable跨实例事务或并发恰好一次。不能同时启动第二个发布器写同一事件。
- 目前配置仍以精确批准驱动。全仓普通会话的持续无人值守语义质量审核策略尚未验收，不能将一次审核发布称全部长期目标完成。

下一阶段语义质量门禁候选：复用已经接通的原生 HTTP 模型节点、严格 JSON schema 和实际 SHA 源码上下文，独立审核 draft 中逐项事实引用、缺资料最小性、已知字段与问题一致性、普通咨询范围；错误/不确定转待人工。审核请求也先预留并计入原总模型预算，不能把审核调用放在账外。当前线程模型调用上限3；若剩余预算不足以完成草稿和独立审核，就不得自动发布，也不自动提高上限。此方案尚未实施、未额外调用模型，先完成已明确批准的Issue31人工恢复及审核发布。

## 当前工作流状态（22:35 CST 快照）

| 工作流 ID | 状态/角色 |
|---|---|
| `onticardsPersistentReadOnlyV1` | active，46节点串行读取；新配置真实轮询验证中 |
| `onticardsBoundedGetV1` | active 子流程，4节点；无Schedule；原生四场景GET有界重试已通过 |
| `onticardsRepositoryContextV1` | active 子流程，33节点；无Schedule；实际main/tree/blob校验已通过 |
| `onticardsPersistentDraftsV1` | inactive，model_enabled=false；Issue31已预留1次、结果未知 |
| `onticardsMigrationGuardProbeV1` | active fixture Webhook，无Schedule/无GitHub/无模型 |
| `onticardsPersistentPublicationV1` | 仅本地候选，未导入、未激活、批准为空 |

独立实例 `onticards-maintenance-triage` 使用已存在官方镜像digest与独立持久库，未在测试机构建。旧18127探针已停止；共享n8n与ProPR未由本候选修改。

## 2026-10-23 00:47 CST 当前版本（取代上文历史未实施状态）

根流程审核了普通咨询范围、源码与人类事实分离、精确批准和sticky发布链；要求补充发布前新增AI标签转交，以及纠正普通对话预算。两项已完成原生验证后，本次以既有owner REST API安装并启用三个5分钟工作流，未新建实例或凭据，未直接写SQLite：

| 文件/工作流 | 节点 | 当前开关 | 审阅定位（生成器） |
|---|---:|---|---|
| `persistent-drafts.workflow.json` / `onticardsPersistentDraftsV1` |45|model与全仓普通新事件=true|`build_persistent_drafts.py:25` 配置；36–75人类事件/AI分流/历史与失败预算；90–94先预留；111–126结构与人类原文字段校验|
| `persistent-semantic-review.workflow.json` / `onticardsPersistentSemanticReviewV1` |37|review=true|`build_semantic_review.py:23`咨询/缺信息+已预约+历史失败/31排除；26–38fresh SHA与持久预算；47源码quote、人类字段、已知字段门禁；50精确批准|
| `persistent-publication.workflow.json` / `onticardsPersistentPublicationV1` |48|publication与automatic=true|`build_persistent_publication.py:53–77`fresh来源及sticky优先，70–71 AI接管；80–89写前意图、单POST、GET确认与一次会话增量；101原生批准选择|

普通线程最多3回复、每轮草稿+独立审核最多6调用；每次工作流只处理1候选，模型/POST无自动重试。Issue31已封存，不因普通预算变6而获得第四次：草稿/审核配置均含 `manual_handoff_threads=[31]`，人工恢复工作流inactive且manual_enabled=false，真实账本model_calls=3及原pending状态保留。其他失败线程继续由原生pending和历史意图阻止新模型。疑似代码缺陷/大改转人工；AI标签由ProPR原生路径接管，n8n不自行创建Agent或重复修复。

激活只接纳 `2026-10-22T16:47:39.252594Z` 之后的新真人文本，历史事件保留上下文。`ordinary-pipeline-staged.json`与`ordinary-pipeline-enabled.json`保存native checksum/version/文件SHA及读回开关。管理动作本身0模型/0GitHub请求；真实模型和GitHub发布需之后符合条件的新事件。不能把配置已启用称为这条新独立审核链已经真实自动发帖。

新证据（均在 `evidence/n8n/`）：

- `conversation-budget-native-probe.json`：9/9，使用4条未修改的生产状态表达式与原生DataTable，跨重启2→4→6、第三回复后第四拒绝、旧真人事件拒绝、31旧/新事件仍3、其他失败线程保留、剩余1次不足以做pair。没有模型或GitHub调用。
- `semantic-native-budget6-probe.json`：12/12，完整37节点审核链用冻结源/模型响应替换网络；来源变化、引用错误、运行事实混淆、字段冲突、非法JSON、6次上限及31封存均验证。Issue29旧两条正文兼容只使用历史批准冻结结果，不声称新的模型语义实测。
- `publication-native-ai-gate-probe.json`：13/13，完整发布链连接本机原生HTTP fixture；新增AI零POST、unknown之后加AI仍保持unknown，仅GET；此前未知POST→GET失败→恢复、正文/来源/次数/已问字段与一次会话增量仍通过。真实GitHub请求0。
- `policy-boundary-native-probe.json`：原生安全诊断与批准选择10项；`persistent-expression-validation.json`：252表达式语法校验。它们不替代真实服务端执行或模型质量测试。

新增配置/表达式理由与官方复用来源见 `research/native-semantic-review-reuse.md`。保留上文旧39节点/3模型预算及Issue31第一次未知的历史阶段描述；不能据上文历史段推断当前仍未启用，也不能把Issue31的三次失败改写成成功。

00:52 首个真实定时周期：原生review771、draft788、publisher789已触发并离开执行队列；draft788于00:52:07落盘 `dry_run_no_model`，水位00:50:05、fresh=true、candidate=null、model_enabled=true、调用0。review/publication新表仍空；29预算2/回复2、31预算3/回复0保持。证据 `ordinary-pipeline-runtime.json`。`saveData*=none` 的旧执行壳可能仍显示running但已带deletedAt，应按原生soft-delete语义解释，不能据此宣称仍有模型正在跑。此轮没有合格新事件，不属于模型→审核→实际发帖E2E。


### 2026-10-23 01:36 实际拒绝回执

Issue29真人事件6346376385由原生定时流程完成draft998+review1022，两次实际模型共38513tokens，原文未更改。独立review自身decision=approve但questions_minimal=false；既有全布尔/精确quote gate拒绝，status=needs_human_review，无GitHub POST。累计model_calls=4，reply_count=2。人工另发现完整SHA转录错误，已准备可信Set渲染/冲突拦截候选与冻结原响应6项验证，不以人工改文伪装模型成功。证据 issue29-final-native-rejected.json / issue29-final-original-draft.md / issue29-final-original-review.json。后续是否允许剩余预算内明确运维恢复由root审查；没有自动重试。
