# 当前普通会话流程部署与恢复

适用已验收的测试机10.66.66.5，不适用于覆盖共享n8n。所有镜像构建仍只在打包机；这里复用已存在官方n8n2.42.7镜像digest。目录 `/opt/onticards-maintenance/n8n/persistent`，独立项目/容器 `onticards-maintenance-triage`，loopback18128，host-network访问既有loopback17891代理，生产并发1。源配置为 `persistent-compose.yml`。

## 当前流程与再生成

按以下顺序再生成配置：`build_persistent_polling.py` → `build_bounded_get.py`（输出实际部署的 `persistent-readonly-serial.workflow.json` 与 GET child）→ `build_repository_context.py` → `build_persistent_drafts.py` → `build_semantic_review.py` → `build_persistent_publication.py`。生成器都只写本地JSON；默认模型、审核、发布开关关闭。

`build_event_replay.py` 仅作为已有Builder类定义的编译期来源；当前生成器只读取该类代码段，不运行其中历史回放入口。`triage-issue29-v1.workflow.json`仅作为已验证原生HTTP模型节点的编译期模板，不重新导入其历史测试工作流。生成草稿所需的公开历史来源最小依赖为 `evidence/n8n/issue29-followup-source-snapshot.json`；这里只迁入缺失的Issue29会话，不覆盖已有状态。完整运行必须导入原生App JWT与模型HeaderAuth凭据，JSON内只有credential ID引用，不包含密钥。

现有实例更新使用 `manage_ordinary_conversation_pipeline.py`：先stage并读回inactive，审查后显式 `--enable`。它只使用服务器已有owner凭据调用n8n原生create/PATCH/activate，检查checksum、目标无未完成执行、Issue31入口inactive且历史预算为3。它是本部署的受控更新器，不能用于在空库中虚构Issue31历史或通用初始化。启用设置新的admission时间，不回放旧事件；不要因更新而重置会话或未知请求账本。

## 已有实例恢复

1. 保留 `persistent/state` 与 `persistent/secrets`；备份按服务器内部秘密处理，不进Git或公开证据。数据库备份必须保持SQLite一致性（原生备份或维护窗口停止独立容器后复制）；加密密钥与数据库必须对应，不能换新密钥导致既有Credential失效。
2. 仅检查/启动本独立项目：`docker compose --project-directory /opt/onticards-maintenance/n8n/persistent -f /opt/onticards-maintenance/n8n/persistent/compose.yml config --quiet`，随后 `up -d --no-build --pull never`。不构建镜像，不修改共享n8n或ProPR。
3. 用 `snapshot_ordinary_pipeline.py` / `snapshot_persistent_polling.py` 检查active、实际开关、水位、预算与回执。soft-deleted执行壳的status可能仍为running；只有deletedAt为空且status为new/running/waiting才作为未完成执行。
4. 若需要暂停模型/发布，在本实例原生管理UI停用对应draft/review/publisher工作流；不要清除DataTable、改变已发comment ID或通过marker归零。故障源采集可单独停止而保留状态。不要通过重放Webhook追赶未知模型或POST。
5. `posting_unknown`只允许原生GET对账；找不到结果也不自动第二次POST。模型未知或审核失败保留已消耗预算并转人工。Issue31手工恢复入口已封存，任何部署不得重新启用。短token撤销未知就记录未知/等待自然到期，不声称撤销成功。

## 有效验证

262表达式语法检查：`node validate_persistent_expressions.mjs`（含历史配置只做解析，不执行模型）。主要行为测试是独立18127、官方同digest镜像、原生DataTable/Webhook上的预算、语义、发布、安全诊断fixture；运行器仅对loopback，模型/GitHub网络均替换，测试后停止容器。`build_*_probe.py`先生成相应JSON，再将JSON和 `run_*_probe.py` 放到测试机目录执行。不要在常驻18128导入fixture。fixture DataTable按版本隔离，保留旧结果；同一测试重复运行可能读到已消耗的状态，不可删除历史后宣称首次通过。

重要实证为 `conversation-budget-native-probe.json` 9项、`semantic-native-budget6-probe.json`12项、`publication-native-ai-gate-probe.json`13项、`policy-boundary-native-probe.json`10项。冻结模型响应只能验证门禁/状态机，不证明模型质量。真实自动回复验收必须关联真人评论ID、source SHA、模型usage、独立review原文及App永久评论URL；`snapshot_issue29_final.py`只读取已授权真人事件6346376385，不触发执行。

## 权限与范围

只有单仓 `stepll2026/OntiCards`；机器事件不生成新普通草稿。AI标签由ProPR负责，发布前新添AI也转交。普通咨询与必要缺资料经过一次draft+一次独立review，最多3回复/6调用；大改、疑似缺陷、不确定来源或失败转人工。n8n不构建、SSH部署、合并或关闭Issue。最后合并由维护者操作。

实际00:47启用及00:50首周期状态见 `ordinary-pipeline-enabled.json`、`ordinary-pipeline-runtime.json`。真实Issue29第三条回复是否完成须看最终独立证据，不能以开关=true替代E2E。


2026-10-23 01:24 当前采集为59节点，源码读取为42节点。采集复用全量分页 state=all（不加 since）与 installation repository 元数据的 open_issues_count 做一致性校验，补齐评论指向但全量列表未含的线程元数据；失败不推进水位。源码的每个缓存/未缓存文件走原生 Loop Over Items，done 后统一 SHA 汇总和令牌撤销。对应更新器 `update_intake_completeness.py` 和 `update_source_cache_loop.py` 只更新现有原生工作流，不清账、不触发模型。

`intake-completeness-native-probe.json` 6/6覆盖原生完整循环、空列表与独立计数不符、评论补集及元数据失败；`source-cache-loop-native-probe.json` 5/5保留旧混合缓存失败，验证缓存/新读取/混合聚合以及坏hash拒绝。两者均0模型。真实01:20自然采集完整29线程264事件、令牌撤销成功，不能将此采集通过等同于回复链路通过。


01:35当前source仍42节点，显式目标与相关文件优先；required片段未覆盖时明确complete=false，合法空文件带size=0/empty=true/已验证blob返回。11项实际Set表达式验证已过，真实三ref验证由独立agent执行，尚未以其未返回结果标为通过。

01:31真实普通回复轮次已拒绝：真人Issue29事件6346376385自然draft998（19195tokens）→独立review1022（19318tokens），questions_minimal=false且exact quote不匹配，0发布；预算2→4，回复保持2。原文、来源、审核和失败均在bounded证据中。当前Set可信SHA渲染/错误SHA拦截属于本地候选，未部署；冻结回放6/6不代表新的模型质量通过。任何同事件有限恢复都需要明确运维批准，不能自动清除原失败或归零预算。


## 2026-10-23 02:21 最终状态（前述时间点为历史）

01:42 已部署可信 source SHA 模板及精确 metadata quote 门禁；此前“本地候选”仅描述01:31。source 42节点最终版本4776d717（模板SHA29595c00…），实际相关源码覆盖已由独立检查通过：三ref 8abe/c8e/main共69/69；PDF helper→entry实际871–1012同6000字符7/7。证据为 evidence/knowledge-main-refresh-independent.json、knowledge-pdf-source-independent.json；不等于语义质量通过。

01:57 唯一获批的 Issue29 同真人事件最终恢复执行1220，实际18444 tokens（17549+895）。真实输出把当前c8e提交中的68d398错写68d598，精确SHA门禁拒绝 needs_structure_review；第6次独立审核没有调用，没有第3条App评论。总模型预算5、已发布回复2，原998/1022原文和行保留。02:00:51专用恢复入口停用、manual_enabled=false，常驻draft/review manual_handoff_threads=[29,31]。Issue31仍3次历史预算封存；29/31不再模型或公开尝试。普通自动回复新链路真实语义E2E未通过，不能用此前两次人工审核发布替代。最终证据：issue29-final-recovery-result.json、issue29-final-recovery-sealed.json、ordinary-pipeline-runtime-final.json。

02:19 已复用完整intake接入既有CI：生成顺序在 build_bounded_get.py 之后追加 build_intake_ci_handoff.py，生成9节点child与60节点 persistent-readonly-ci.workflow.json；不新增Schedule。child仅在完整水位已持久化、原读token撤销true、watermark/poll_id一致、线程数完整且10分钟内时投递公开PR元信息。最多20个open PR；18132既有fresh guard再次核head/base/repository。只有专用HeaderAuth credential ID进入配置，真实key沿用服务器0600文件。当前trusted mode=dry_run，是否实际CI收到需看单独native receipt，不将启用当成功。install_intake_ci_handoff.py 是一次既有59节点实例的校验升级器，不适用于空库或覆盖任意配置。

新增无模型实际原生边界验证：intake-lifecycle-ci-native-probe.json 13/13（全PR评论/review、close/reopen、机器身份和CI投影）；ordinary-concurrency-native-probe.json 8/8。后者只在隔离18127复用同镜像/同DB、设置与生产相同N8N_CONCURRENCY_PRODUCTION_LIMIT=1，两个同时Webhook进入时间02:20:32.990与02:20:35.635，第一完成02:20:35.570，实际DataTable只增加一次2调用预算/1模拟回复，第二为already_answered_verified。没有真实模型或GitHub POST，原隔离容器已恢复并停止；这验证单实例串行边界，不宣称多实例CAS或真实语义回复。


02:35 CI接入更新：首次真实dry-run发现DataTable多行导致逐item重复投批次，已用n8n原生executeOnce配置修复。原失败29份、27个尚未运行的重复接收被原生停止，全部0SSH/0模型。修后自然25分仅1receiver，三个受控PR通过既有validation_only。原生多row+HTTP计数回归最终15/15（已替代此前单row13项覆盖），实际published定义与文件hash一致；并发8/8另保留。隔离CLI测试必须等待启动依赖索引完成、显式publish版本并回读workflow_published_version，防止旧版本响应混为新测。

02:35:24 consumer已切正常dispatch模式，专用child版本3f0f3196，父60节点仍同五分钟Schedule。没有手动补跑；具体PR26重复跳过与PR30/33预算结果由18132原生admission收据记录。新模型CI当前预算不足不能声称构建通过；不会通过降低既定45000预留或增加余额绕过预算。


## 2026-10-23 03:19 当前收尾（前述时间点保留为历史）

CI已连接正常dispatch。03:11自然周期1receiver/6child，PR26旧成功跳过、三个PR转人工、PR30/33预算不足保持；0 CI main/SSH/模型/令牌mint。原02:37/02:38预算未知的登录HTTP429证据保留，经明确批准只读核对后追加余额15445<45000，不重置或重投。余额读取现为完整批次至多一次，旧回执/人工/dry-run跳过；时间≤300秒、watermark绑定、实际lease前仍fresh校验。原生生命周期及批次fixture现20/20，另52表达式与自然周期7断言，不把旧13/15的覆盖数作为最终值。

03:19常驻draft只更新既有routing Set。按照ProPR原生首行、大小写及参数规则，PR discussion/inline中的 `/review`、`/fix`、`/merge`、`/switch`、`/use`、`/ultrafix` 标记context-only，避免真实owner发出的MCP命令再消费普通咨询模型；marker不是授权。已有pending、预算与29/31封存保持；官方formatter离线捕获+原生fixture9/9，0模型/公开发帖。准确版本与源表达式hash见 `native-slash-routing-deployment.json`。部署器 `update_native_command_route.py` 仅适用于该已存在且无未完成draft的实例，不是全新安装器。

Issue29仍5calls/2replies、Issue31仍3calls并人工封存，不再模型。可信SHA门禁已部署，知识69/69及PDF7/7仍为实际来源验证；真实普通自动语义回复未通过的结论不变。
