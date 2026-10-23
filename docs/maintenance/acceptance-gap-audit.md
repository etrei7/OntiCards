# OntiCards 验收缺口独立审计

> 历史审计：下文沿用旧任务书AC-01至AC-13，记录当时ProPR/n8n与人工最终合并策略；该策略已被2026-10-23的新目标取代。下文“当前/最终人工/已通过”仅描述原版本，不证明新系统或后台ON/OFF功能通过。当前实施选择及缺口见[复用矩阵](reuse-matrix.md)首节，行为规则见[回复策略](response-policy.md)。完整新任务书保留23项验收，自动合并、旧入口迁移与新整合业务闭环均尚未验收。

按附件全部功能与 AC-01～AC-14 核对，快照为 **2026-10-23 03:50（上海）**。配置、候选、部署、受控实跑和持续成功分别计证；主流程尚在实施，不能整体结项。21:02旧快照完整保存在 `evidence/audit-history/acceptance-gap-audit-20261022-2102.md`，原始失败证据不删除。

ProPR API/worker/daemon当前已于19:45:28Z实部署 **policy13**，digest `3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879`；964项（679既有分组+20原生只读/版本/权限边界+265相关回归）无跳过，编译通过；部署前后队列0、runtime.env未改、health200。policy12在child/模型/仓库准备前复用原生Task原子持久登记，补上此前无Task父失败跨poll重新获得预算的缺口；存储不可写则拒绝派发。policy13只读review恢复、无AI标签可信owner门禁及实际收集head/base发布检查已部署；新接线未追加付费模型验收。原语义索引partial停、indexworker关闭，未宣称完整索引成功。

[Draft PR26](https://github.com/stepll2026/OntiCards/pull/26) head3105/basec8e 是已有PDF版式修复；[Draft PR33](https://github.com/stepll2026/OntiCards/pull/33) head `fdd3f291e8d4a51c31610f13d87670ab3288a6e9` / basec8e 是 **Issue32 原生自动修复及同PR两次反馈更新**，最终9/9、真实并发PDF2/2、竞态10/10通过。PR33公开Check119950685976仅证明并发范围，不能扩成整仓通过。[Draft PR30](https://github.com/stepll2026/OntiCards/pull/30)为配置交付；最新交付提交由主流程统一发布，本轮本地文档不冒充已发布版本。所有最终合并仍由维护者执行。

00:00 systemd真实日界快照已成功：487 Stars/9 Forks；10/22新事实日报 run5da38704 complete/errors[]，含13个nativeTasks、PR33 Checks1/PR26 Checks2；37项Linux回归通过。新10/22三次原生AI均未通过质量审查；第三次f879已完成模型但含全局R18污染及空Checks误写未知，两处语义错误保留，显式复核修正版独立QA 10/10通过，保留公开原文，不叫native通过。未来日报采用原生独立alias、instructions=[]/helper READY/只读bind已无模型验证，definition revision13与09:05 schedule保持；事实09:00。

独立原生n8n→受限OpenSSH→rootless流水线已在kol真实构建PR26，经既有registry精确digest到5机，最终 **r4真实模型业务API7/7、Playwright3/3、9原生PNG、四格式导出及query250通过**，0 skip；native执行70于17:35:11Z成功持久化。r2网关429、r3原生预扣不足均保留；本轮40406原生配额、token12禁用读回、总账户100k未重置/余15445、美元未知，无后续供应商调用。基础治理仅单表三列空值检测，不扩成规则库/关系全覆盖。

37文件只读门户及Check119988255661已真实发布，固定head3105/basec8e发布前后不变、Draft保持；5个最小scope token全部撤销。复用n8n 5min持续版本失效，PR26/PR33均登记watching，PR33自然trigger17:45:36核验current；故意synthetic base的neutral Check119966580036已真实PATCH并独立回读action_required，0测试/模型/ref写。首次PATCH/Code输出错误保留。新PR/更新已复用同一完整intake→原生CI准入，自然03:11一批6PR完成：PR26旧成功跳过，PR30/33在保留原unknown事实后受控核余额改为budget_exhausted，随后sticky保持；0新login/SSH/model。新tuple可再准入，但余额15445低于45000，必须先人工补配并显式恢复，不跨poll自动重发租约。fork/非codex/main进入人工，PR33失效只action_required不冒充自动复跑专项。

知识主路径独立69/69：真实8abe→c8e→main，22上下文/29缓存/4改增文件，0模型；语义索引仍partial停止。普通咨询完整分页已自然poll966验证29线程/264事件/短token撤销，新Issue29真人事件已发现并进入两模型，但19195+19318tokens后质量gate拒绝、0POST，最后有限恢复draft1220再用18444tokens仍写错SHA，被gate拒绝且0POST；最终总5次模型/2条旧回复，未用第6次review，29/31已封存人工。原生slash命令（含MCP /review）排除普通draft路由9/9实际fixture通过，避免同一维护命令被咨询管道双消费。

自动语义审查与CI分开：复用MCP原生read+review、显式编码alias、持久operation及既有原生review，不新建Agent。TLS仅loopback18135，HTTP /api/mcp及子路径404；受限SSH12/12负向与真实native只读握手通过，n8n子workflow已真dry-run且0model。跨grant旧operation隔离SQLite16/16、envelope13/13、SSH未知结果6/6通过。已有pending publication恢复、无AI标签worker拒绝及发布前head/base检查的实际缺口已由policy13局部原生修复，20新+265相关fixture和旧679通过，13后的TLS/SSH12项再次通过；自动review仍disabled/dry_run；最后PR30发布后完整snapshot baseline才允许未来版本，不回放旧PR。这不算语义审查业务通过。

## 逐项验收

| AC及完整目标 | 当前结论 | 真实证据 | 尚缺且保留 |
|---|---|---|---|
| AC-01 目标与基线 | 基线和知识主路径通过；语义索引部分 | 单仓/kol构建/5机测试、精确SHA；App单仓六权限；独立knowledge-main-refresh-independent.json 69/69，8abe→c8e→main/0模型 | 语义索引partial停；默认分支模板待人工合并。 |
| AC-02 真实完整日报 | 事实完整；新原生AI质量未通过 | 00:00 487/9；facts run5da38704 errors[]/13nativeTasks/Checks分列；Linux37；第三AI原文与两语义错误保留 | 主流程显式审核修正版10/10通过，原生第三次质量失败仍保留；独立daily alias rev13只证明配置/helper，未来定时质量未验，不以旧10/21通过替代。 |
| AC-03 定时、幂等、恢复 | 事实采集与原生受控恢复通过；整体部分 | systemd Persistent/flock/pending跨lookback/catch-up、重复完整报告SHA不变、受控中断/重启；n8n常驻定时、重启及sticky未知发布 | 宿主真实reboot、所有任务中断恢复未全验；首投递持久门禁policy12已补；CI失败需显式审阅归档恢复，未产品化一键重跑。 |
| AC-04 有据回复、去重、续办 | Issue29既有两答通过；新常驻补充质量拒绝 | 6339994362/6340579230真实App/重复同ID；自然intake966 29线程264事件完整发现新真人；draft998/review1022两调用38313tokens被gate拦截，0POST | 新真人事件最后恢复已失败并人工封存，常驻自动draft→review→publish成功闭环尚未完成；Issue31未知封存。全事件投影/关闭重开/多线程15+预算批20+并发8原生fixture通过，但不当真实模型全E2E。 |
| AC-05 自动隔离修复、PR及独立审查 | 有真实成功案例；部分通用路径未验 | Issue32→原生受限Agent→PR33→测试失败反馈同PR更新→最终fdd3；9/9、2PDF并发、10竞态；main未改。原Issue25失败与PR26独立发布仍保留 | SQL三轮候选均被独立审查拒绝，仍未修；真实fork无权continuation、可解/语义冲突分流尚未端到端。新PR自动语义review仅干跑接线，policy13门禁已部署，正式baseline待，不把CI当代码审查。 |
| AC-06 真构建/部署/API/PW/截图 | 固定PR26完整列出业务通过；非整仓 | rootless r4 API7/PW3/0skip/9PNG，真实schema/card/query250/基础治理/四格式；native执行70；PR33独立9+2+10；kol构建5机测试 | r2/r3失败保留；迁移5pass1skip、three_way_check缺失、原lint/typecheck基线未修；PR26本身未含PR33并发修复。 |
| AC-07 SHA追溯与旧证据失效 | 固定证据与原生5min失效实证通过 | PR26 Check119988255661/37文件HTTP哈希与只读拒绝；PR33 Check119950685976；synthetic neutral119966580036→action_required/独立回读；20 Code断言，natural trigger复查current | 5min窗口内存在观察延迟；断网不能保证即时更新；不自动重新运行PR33；30天持续访问未验。 |
| AC-08 失败限制、停止转人工 | 多类真实停止；边界未全覆盖 | failed child跨poll无新预算，unknown POST不重发，原生Git子进程停止；CI r2/r3失败存档、显式r4后停止；旧索引failed、模型记录20→20/停止结算通过 | policy12首投递持久Task堵已定位父失败/failed未写回重预算，9+192相关测试通过；物理隐藏模型请求不能以逻辑6次泛称封顶；金额未知不是费用cap。 |
| AC-09 fork与凭据隔离 | 单仓App/真实受限执行边界通过；fork部分 | PR33/PR26专属Agent边界；rootless UID/subUID/cgroup、宿主/内网/metadata负向拒绝；SSH pinned/from/ForceCommand、只可信publisher持registry凭据；PR只获原生短模型token | 共享kernel不是VM；外部fork拒绝进入此CI，真实原生fork continuation/作者归属仍未端到端；registry既有凭据非repo最小权限，已限制可信单entry。 |
| AC-10 人工合并与真实入口 | 当前边界通过 | Draft PR26/30/33、证据门户和Checks；native merge/noncodex/main禁止策略，main未写、无auto-approve/保护弱化 | 只有当前版本及必要检查满足才可审核；专项success不等于全仓可合并。最终Merge及默认分支模板启用由维护者操作。 |
| AC-11 查看/暂停/恢复/取消/重试 | 日报UI、NewTask、部分取消/反馈实测；整体部分 | OAuth空姓名fallback、HTTP uuid原生库修复；原生UI Issue32/PR33反馈与终态；准备阶段Abort/deadline、日报暂停恢复；native receipts可追踪 | 原生pending无job Stop/Redis/SQLite 25/25已验，准备期真实Git子进程取消/超时原51项相关回归通过；本地continuation49+语义负例1共50项另计；历史PR26 history_id空但liveDetails有token；CI同head/base人工恢复尚为受信操作流程，不能称完整管理闭环。 |
| AC-12 可复现交付 | 已有运行链与严格allowlist；非全新安装验收 | policy13 digest/patch、systemd/ACL、n8n默认inactive模板、rootless/SSH/registry、原生测试及Check证据；最终源码依赖/hash清单 | 自动PR发现→CI已自然派发且不足余额永久拒绝；fresh build控制器匿名读可能限流并failclosed；维护者独立安装、宿主reboot/磁盘硬quota/30天持续未验。 |
| AC-13 逐功能复用 | R01～R19与具体gap有来源/方式/状态 | ProPR/n8n/GitHub/systemd/PyGithub/Compose/Rootless/OpenSSH/Skopeo/PW/原生NewAPI等实证及许可 | 原生节点配置成功不替代真实业务；历史失败版本单独保留，不反写当时结论。 |
| AC-14 新代码对应缺口、不减目标 | 当前新增范围明确；目标全部保留 | 已有Task/history/Redis Lua/Express/parser/simple-git/索引预算最小扩展；n8n节点/固定可信边界适配，未新造scheduler/Agent/发布器/日志/认证平台 | 真实模型全事件、fork/冲突、管理恢复、索引与新版本持续CI验收未完成仍列出；不为工具适配删除SQL、模型、浏览器、证据及人工合并目标。 |

## 附件其余目标及阶段

阶段0盘点/联网逐功能复用/基线已有证据。阶段1事实采集已跨真实日界，最新AI质量尚未过。阶段2Issue29早期人工审核发布两答通过，新常驻补充最后失败封存；普通语义完整闭环仍缺。阶段3已有Issue32→PR33及反馈同PR真实成功；审查通用有效产物与fork/冲突部分未验。阶段4既有PR26产品和PR33专项通过，固定PR26原生rootless模型CI已通过列出业务，自动新PR派发已自然接通，后续完整模型验收受剩余额度阻止。阶段5运行/定时/恢复多项实证，不能整体结项。

- 七项业务目标、第五节七类规则：咨询不授予修复权限；小问题最小修复、大改/缺信息转人工；自己事件/机器人防循环和每线程3回复/6模型调用目标保留。普通新事件全自动语义质量和全部事件类别尚未实证。
- 第六节默认参数：上海时区、事实09:00/日界00:00、AI09:05、并发1、5分钟、3轮、30天；实际费用未知；原生索引6分析/600秒及Git准备120秒已局部扩展，但整任务所有隐藏请求和重入不得无证称封顶。
- 第七节知识六项：文档、模块/接口/数据流、部署测试、已知问题、规则、repo/branch/SHA/时间均有；原生摘要pinning、fetch失败停止、deadline、预算/重复入口修复有证据，完整新知识产出未宣称成功。
- 第八节日报A–F：当前事实包含概况/事件/PR、commit statuses与Checks、native任务/AI活动、待办、质量；旧完整报告保留旧口径和SHA；新摘要不得把不同日、不同计数或未知当已证事实。
- 第九节九项代码规则：隔离branch/head/base、复现/最小修复/测试/独立审阅/反馈同PR已由PR33实证；fork权属、冲突分流、未来变更再验仍保留；用户最终合并。
- 第十节证据：机器断言与截图分别记录，真模型/fixture不混；PR26/PDF/PR33门户固定allowlist，raw trace不公开。新CI失败含边界和阶段、未执行不当通过；预览销毁后证据仍保留，实际30天持续访问未验。
- 第十一节管理：复用ProPR/GitHub/Nginx，无新后台；普通PR链接不冒充合并按钮。prequeue取消25/25已验；历史UI日志关联和全故障恢复仍有明确边界。

## 当前具体剩余项

1. 新自然日三次原生AI摘要质量未过，显式复核修正版10/10已过；09:00/09:05未来定时不能预先通过；daily专用alias配置成功不是新模型质量成功。
2. 常驻完整分页已真定时发现真人；新补充及最后有限恢复均被质量gate拒绝、0POST，最终5调用/2旧回复已人工封存。全事件类别/并发与Issue31未知仍保留。
3. rootless固定PR26完整真实模型CI通过；新PR自动发现→派发已接通，PR metadata复用App只读短token；新版本完整模型预算不足（15445<45000）持久拒绝、不会自动重置或重发，CI人工恢复仍是受信归档流程，不称AC11全部完成。
4. Check失效已真证，但5min观察延迟与网络失败存在；旧证据不删除，失效不自动重跑专项。30天持续访问未到期验。
5. 版本化知识主路径69/69通过，语义索引partial停；无Task parent/failed未落盘已定位边界由policy12原子首投递门禁补足，数据库不可写时拒绝。
6. 真fork无权continuation、作者归属/原PR保持、语义冲突停止/确定冲突续办；prequeue原生Stop25/25已验，全部任务恢复未全验。
7. SQL扫描未修；PR26并发问题在独立PR33修复，不能反写PR26已修；迁移缺脚本与前端静态基线失败保留。
8. 自动语义审查的policy13门禁已验证部署，最后PR30后完整snapshot baseline尚待；当前真实只读传输/准入配置通过，正式启用见外置activation回执；不额外付费重跑旧审查。
9. 最终严格allowlist及镜像/源码hash主流程统一交付；维护者fresh install、宿主reboot、磁盘硬配额未验。全部最终合并人工执行。

## 历史解释与保留

历史21:02完整快照及原始失败保留在 `evidence/audit-history/`。Issue25 clone/ownership、PR26无效review误completed、模型token8/9会话401、token10网关429、原生Check PATCH未知、SQL候选拒绝均不得重写成成功。Git native shallow bootstrap复用本任务已有代码，之后origin小fetch成功，不冒充公网完整clone成功；新网络结果按实际探针区分。
