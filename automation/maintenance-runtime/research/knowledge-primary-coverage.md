# 知识目标的主路径与可选语义摘要

最终状态（2026-10-23）：下表“尚需”是验证前清单，现已完成零模型三ref真实读取、69项独立Git/cache/自然事件source hash检查和当前运行说明；PDF专题定位另7项通过。当前可复制PR30资料在 `deploy/propr/knowledge-current-pr30/`，来源manifest明确冻结10c与实际main c8e不同。policy11已部署，旧索引无新模型收尾failed/队列空；语义索引仍可选/停用/部分历史产物，不冒称全仓完成。详见 `knowledge-native-refresh.md` 最终主路径节与 `evidence/knowledge-main-refresh-independent.json`、`knowledge-source-binding-exact.json`。

任务书第七节要求读取并核实代码/文档/部署/测试，形成产品边界、模块地图、操作说明、已知故障、处理规则和版本时间六类内容；执行任务读取实际代码版本，main 更新后增量刷新受影响内容。原文没有要求全仓逐文件模型摘要，也明确优先现有文档、Agent 指令与底座上下文，禁止无证实缺口新建知识平台。

因此全仓语义摘要可作为可选加速层；停止其付费循环不会删除功能目标，但必须让下列主路径真正可用。60 条局部摘要不是全仓完成，也不能代替事实档案。

| 目标 | 现成主路径及已有证据 | 尚需最小验证 |
|---|---|---|
| 初始化事实与边界 | PR30 `AGENTS.md`、`docs/maintenance/repository-context.md`、response-policy；初始8abe、现main c8e、PDF3105及并发fdd3有独立构建/测试。版本包10c6862有blob/SHA manifest。 | 版本文档的早期运行状态须保留日期；在当前交付说明链接新的PR33、日报App及政策版本，避免把历史“未验证”当当前结论。 |
| 任务代码版本上下文 | ProPR真实checkout/worktree；OpenCode原生AGENTS和instructions；Issue32→PR33真实任务记录。instructions包是额外知识，实际checkout为最终代码事实。 | 任务记录持续列head/base，分清PR30文档SHA与业务代码SHA；PR30合并后改原生相对路径，避免长期同时载入旧副本。 |
| 事件的即时事实读取 | n8n现成GitHub Contents/Trees、Crypto SHA1、DataTable。每次先fresh resolve main/full SHA，再按同一commit验证blob；缓存键含commit/path/blob，最多12文件/24000字符，未命中/截断/请求失败不冒充完整。`repository-context-independent-verification.json`真实核6个核心文件与本地Git一致。 | 用真实历史8abe→c8e通过同一入口验证受影响入口或迁移SOP变更及未变文件；不能只测同SHA缓存命中。零模型、零GitHub写即可。 |
| main变化后增量刷新 | 原生Git fetch和n8n新commit/tree/cache自然产生新版本，不必重新摘要406文件。现有日报记录main SHA及近期提交。 | 确认实际未来事件或现有poll链会调用fresh reader，并把受影响源/版本/时间保留在现成source DataTable；仅一个手动probe不证明未来运行。若要求无事件时也刷新，应接现有Schedule原生节点，不能另造调度器。 |
| 可审阅知识产物 | 项目Markdown事实档案 + exact Git链接 + source cache的commit/tree/blob + SHA绑定运行报告。原生代码/文档是知识内容，模型摘要不是唯一格式。 | 汇总一次新旧版本对照清单和当前sources入口；未知、未测试、历史失败继续明确显示。 |

现成 n8n reader 的路径/文本预算是上下文边界，不能称检索全仓。范围之外的问题应沿原有完整tree选择必要文件并读取，或者明确待核实；没有证据时不得让模型凭摘要猜测。部署状态变化也不能仅由Git SHA推导，仍以真实运行manifest和报告为准。

可选索引历史：policy9真实预算耗尽后BullMQ重试重开预算，另因baseBranch缺失重复HEAD；HEAD部分失败又误显示completed。原证据保留，summary状态为partial。policy11复用原生attempts/UnrecoverableError/status完成修复，478测试通过且仅构建推送；主流程负责旧任务无模型settle。默认不恢复付费索引，不把修复代码通过当语义索引验收完成。

最低收口不需要新增模型调用或知识服务：一组真实Git历史变更对照、一组现成source reader跨SHA读取/缓存检查、现有长期入口调用关系与当前事实文档版本说明。完成这些后，可将“实际版本上下文与增量事实读取”列为主能力，将全仓语义索引标为可选、停用、部分历史产物。
