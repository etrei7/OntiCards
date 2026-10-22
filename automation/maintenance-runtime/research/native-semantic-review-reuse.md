# 普通咨询自动语义门禁：实施前复用判断

2026-10-22 23:55 CST。现有 n8n 2.42.7 已有 Schedule / Execute Workflow / If / Edit Fields / Crypto / HTTP Request / DataTable，真实 Issue29 两次 App 回复已成功；通用发布候选39节点已有11项原生fixture断言，但尚未真实生产发布。当前缺口是原通用草稿只有结构检查后等待人工，不能称普通咨询已持续自动回复。

继续复用 [n8n HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)、[DataTable](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.datatable/)、既有单仓App节点与 [百炼严格结构化输出](https://help.aliyun.com/en/model-studio/qwen-structured-output)。严格schema约束格式，不能替代事实与来源审核，因此增加独立审核请求是具体缺口适配；不引入新Agent、调度器、状态服务或HTTP客户端。

拟增加原生审核子流程：只选择咨询/缺信息的原始结构合格草稿；对来源hash/正文hash/线程预算核对；先Insert不可重复审核意图，再将同线程模型预算加一，再调用已有无重试HTTP模型节点。审核只判断、不改写，输出逐项引用与支持源码原文、来源范围、缺资料最小性和禁止操作判定。代码确定性验证引文确在草稿、依据确在对应源码片段或已审事实、字段来自当前人类事件；任何未知/不支持/不完整转人工。审核调用也计入总预算3，不另开账外调用。

通过门禁后在原生DataTable写入精确正文/source/event/hash批准，通用发布器复用既有39节点fresh GET→sticky intent→单POST→GET核对→会话增量，不另造发布器。普通草稿至少保留一个审核额度；不足两次额度时不自动消耗最后一次生成无法审核的回复。自动批准仅用于普通咨询与必要补资料，疑似代码缺陷和大改继续转人工。源变化在发布前重新拒绝；模型和POST均不自动重试。单实例原生并发1，不声称跨实例事务幂等。

Issue31已明确封顶：attempt1/execution42结果未知；attempt2/execution411真实响应把源码镜像误记成人类运行事实，结构门禁正确拒绝；attempt3/execution464失败输出无法区分HTTP/传输/非JSON，预算3，0发布，关闭入口。不得用新Issue规避其预算。后续配置只做0模型fixture，真实启用需根流程检查配置和证据；不会把fixture中的审核结果冒充新模型结果。

额外诊断缺口：原规范化节点丢失了失败HTTP响应；执行不保存敏感payload后无法回溯attempt3细节。必要适配是在HTTP后只保存安全状态/category、有限已脱敏助手文本/错误摘要，不保存请求headers、token或任意原错误对象。现有失败仍记unknown，不补写成已知。

## 2026-10-23 配置校正与原生验证

上文“普通线程总预算3”是当时的配置误解，把修复 Agent 的三轮限制套到了普通咨询。根流程审阅后纠正：普通会话最多三次 App 回复，每轮一次草稿及一次独立审核，共最多六次模型调用；ProPR 修复仍三轮，未改。没有提高任何已封存故障线程预算：Issue31 的历史三次和失败记录原样保留，并在草稿/审核配置中显式 `manual_handoff_threads=[31]`；其他失败线程继续由既有 pending event 与原始模型意图阻止后续自动调用。

具体适配仅复用已有配置、DataTable 预算字段及 If/Set 表达式：普通草稿开始前必须剩余两次额度；审核前先 Insert 意图并消耗一次；发布只保留模型计数、将同线程回复增一。没有新预算服务。新增原生 fixture 直接复制四个实际生产表达式，冻结外部模型/确认传输，并用独立 DataTable 跨重启验证 2→4→6、三回复、第四回复/旧真人事件拒绝、31的新事件拒绝、其他失败线程保留和单剩余额度拒绝。证据 `evidence/n8n/conversation-budget-native-probe.json`，9/9；`conversation-budget-probe-provenance.json` 记录表达式哈希。

独立审核的完整原生图在新版本 fixture 表中验证12/12，包括6次上限、31保持3次、引用不存在/源码当运行事实/已知字段重复请求拒绝、来源前移在模型前落人工记录，以及 Issue29 两条旧已发布正文的冻结兼容。证据 `evidence/n8n/semantic-native-budget6-probe.json`；没有新模型调用，不用此结果宣称模型普遍语义准确。

发布前接管缺口：原已有 fresh GET 会检查 source/head，但未在草稿产生后重新检查新增 AI 标签。现补在 sticky unknown/published 优先分支之后、任何新 POST 之前：fresh 标签含 AI 转 `native_repair_route`；已经转交的事件不自动返回咨询发布。该最小路由适配防止 n8n 和 ProPR 同线程重复处理，不重写原生 ProPR入口。

部署仍复用现有 loopback18128、官方 n8n2.42.7 镜像、单实例生产并发1及已有凭据。候选45节点草稿、37节点审核、48节点发布；截至本段撰写尚未启用。管理工具复用 n8n 源码已核实的 owner REST create/PATCH/activate，新增工作流先inactive，以原生 checksum 防止覆盖并发编辑；不直接写 SQLite，不创建新凭据，不新建服务。启用时仅接纳启用时间之后的人类新事件，Issue31永久显式人工封存，不重新处理历史未知请求。

后续实际进展：00:47:42 CST 已按上述根审查条件启用三流程，激活后首次00:50原生定时周期已运行；draft788在新鲜水位上无候选，0模型/0评论，31仍3。`ordinary-pipeline-enabled.json`与`ordinary-pipeline-runtime.json`为实际部署/首周期证据。不是新模型质量通过证据；真实新事件尚需继续验收。

## 01:00 真实新事件遗漏：复用已有日报修正

真人评论6346376385已于00:57提交，但poll826返回Issues增量0/讨论50/inline0/PR19，目标只有19个PR；事件投影按目标过滤，导致新增普通Issue评论被丢掉，却错误提交水位。HTTP空数组的根因仍未知，不能称GitHub确定故障；我们已确认的是工作流自身依赖不完整目标集合且没有独立完整性核对。红证据 `issue29-final-intake-completeness-red.json`、`issue29-final-intake-red.json`保留。

根流程同日已在日报发现同类问题，`repo/automation/onticards/report.py`已复用PyGithub完整 `state=all,sort=updated,direction=desc` 分页，再本地选择窗口，并以repository.open_issues_count独立核对。n8n采用同一策略：移除since，保留已有原生HTTP分页；复用现有 `/installation/repositories` 返回的单仓metadata中的open_issues_count核对完整Issue+PR open数。不是增加新的客户端/订阅/服务。

另一个明确缺口是完整讨论列表可引用列表未包含的已关闭Issue。最小配置适配把评论issue_url解析为固定仓数字ID补集，在原生单线程Loop中使用已有HTTP GET节点模式读取缺失Issue元数据；GET失败或无法确认类型时整轮partial，不推进水位。成功时将补充的当前Issue元数据传入既有timeline/评论/事件投影。预算、admission、模型和发布流程均不改；先前错误前移的水位不回退、不清账，新完整列表仍可自然接纳00:57事件。

完整原生loop fixture新增6项全部通过：正常Issue/PR投影；空Issue列表与非零open数冲突拒绝；评论引用缺失closed Issue补抓并保留真人事件；补GET失败拒绝；open数不符拒绝。证据 `intake-completeness-native-probe.json`，0模型/0GitHub。01:13:05仅通过原生owner API更新采集为59节点并读回，没触发手动poll，等待下一5分钟周期；实机结果尚未在本段预判。


### 2026-10-23 01:21 CST：原生源码缓存汇总缺口（实施前依据）

实际41节点 reader 在同一次选择中同时命中缓存和未缓存文件时，两个 If 分支分别到达 Require all blob hashes；它按当前分支项目数与完整路径数比较，导致已验证文件仍被判断不完整。受控原生 fixture 冻结1 cached + 1 fresh，旧图实测只汇总1/2并拒绝；不是 GitHub 凭据或模型质量结论。

复用 n8n 2.42.7 内置 Loop Over Items（splitInBatches，batchSize=1）：每个文件仍走既有缓存选择、原生 HTTP、Git blob SHA1 校验；循环 done 后统一汇总，再执行原来的 DataTable 缓存和令牌撤销。仅新增1个配置节点及连线，没有新增源码客户端或缓存平台。官方原生能力来源：https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/ 。

证据 evidence/n8n/source-cache-loop-native-probe.json：保留旧图混合缓存失败，42节点 cached/fresh/mixed 均通过，错误 blob hash 仍拒绝，共5/5；0模型、0GitHub请求。此证据只覆盖冻结原生路由，真实定时周期结果另记，不能据此宣称 Issue29 已回复。


### 2026-10-23 01:30 CST：真实知识读取发现上下文优先级缺口

独立 agent 调用原生 source Webhook 的8abe真实记录 `evidence/n8n/knowledge-main-refresh-native-red.json` 显示：12文件已校验，但24k字符先被6个通用文件占满，用户显式询问的 ext_migrate.py / models/__init__.py 等未返回，而旧 complete=true。这里是现有 Set 模板投影问题，不是知识文件缺失或网络失败。

最小配置调整仍复用原生 Set、同一完整 Git tree、既有 DataTable/blob校验：显式现存路径优先，然后topic相关路径，最后optional core；品牌 OntiCards 不再触发泛化 card 模式。保留12文件/24k字符/每文件180行及6k字符的既有上限。明确存在但不允许读取的路径、超过12个的显式目标，或者片段预算遗漏必需目标，均complete=false并列出具体遗漏；optional core截断不导致虚假失败。没有引入额外检索服务或扩大上下文预算。

实际生产 Set 表达式冻结输入验证 `source-relevance-expression-probe.json` 10/10，保留旧表达式遗漏目标的red，覆盖相关目标优先、品牌误匹配、unsafe显式路径、文件/字符超限以及可选core截断。它是表达式验证，不冒称真实HTTP验证；随后独立agent会继续原生8abe→c8e→main三版本读取。Issue29已发生的草稿源快照与调用预算完全保留，本配置不会回写历史或自动重试模型。


### 2026-10-23 01:34 CST：真实草稿的版本元数据转录缺口（候选，未部署）

Issue29真人评论6346376385经正常定时draft998及semantic1022实际执行。草稿调用19195tokens，审核19318tokens；审核questions_minimal=false及不匹配的逐字来源引用被既有gate拒绝，0发布，累计预算4/回复2，不覆盖原稿。证据 `issue29-final-native-rejected.json`、`issue29-final-original-draft.md`、`issue29-final-original-review.json`。另人工发现草稿将实际c8e3dfee68d398...错录为68d598...，独立模型未明确指出此错误。

最小候选仍复用现有 Strict bounded draft request / Validate structure Set：提示模型只写source_id，不自行复制40位SHA/链接；当前commit行和链接由可信source context渲染。正文若仍包含不在受信source context/trusted facts中的40位commit/blob值，结构gate拒绝。没有改变语义gate逐字引用要求，不自动重试、不改本轮原文。该候选须冻结响应回放、审查后再部署；Issue29剩余预算并不构成自动恢复授权。
