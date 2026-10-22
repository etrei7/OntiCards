# OntiCards 逐功能复用矩阵

当前快照 **2026-10-23 03:50（上海）**。ProPR API/worker/daemon已于19:45:28Z部署policy13，digest `3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879`，964/964（679既有分组+20原生只读/版本/权限边界+265相关回归）0skip/编译通过；运行配置不变、队列前后0、health200。policy10未单独部署。知识主路径69/69、真实8abe→c8e→main、0模型；完整语义索引partial停、旧任务failed后模型20→20，未造完整索引成功。

[Draft PR33](https://github.com/stepll2026/OntiCards/pull/33)是Issue32原生自动修复及两次同PR反馈更新，fdd3/basec8e，9/9+真实并发PDF2/2+竞态10/10；Check119950685976仅并发范围。[PR26](https://github.com/stepll2026/OntiCards/pull/26)3105/basec8e最终rootless r4真实业务API7/PW3/9PNG/四格式与问数250通过；37文件门户和Check119988255661已发布，不能扩为lint/迁移全验或PR33并发修复。[Draft PR30](https://github.com/stepll2026/OntiCards/pull/30)由主流程统一追加，本地文档不冒充已发布提交。main未写、最终Merge人工。

00:00真实487Stars/9Forks；10/22facts run5da38704 complete/errors[]，nativeTasks13、PR33Checks1/PR26Checks2（采集当时），Linux37。新三次原生AI质量均未通过，第三次两语义错误保留；显式复核修正版独立QA 10/10通过，不叫native通过。未来daily专用alias rev13/instructions空/helperREADY只读bind已无模型验证，同09:05Schedule保持，事实09:00。

原生n8n2.42.7→OpenSSH pinned/ForceCommand→rootless→现有registry/Skopeo→5机测试已实际贯通。r2网关429、r3预扣不足保留；r4为第三次实际供应商验收，使用40406原生单位/短token12已禁用，总100k未重置/余15445，USD未知，无更多供应商调用。新PR/更新已复用完整intake→原生CI准入；03:11自然1receiver/6PR，旧成功/人工/预算不足均保持sticky，0新增SSH/模型，不将固定受控成功宣称所有PR持续通过。

App版本检查与Checks写scope分离，PR26/33登记watch；native5min自然trigger17:45:36检查PR33 current，synthetic neutral119966580036已真实PATCH/回读action_required，不是产品tests。首次失败保留。普通intake966全量分页29线程/264事件成功；新Issue29真人事件两模型38313tokens被质量gate拒绝；最后有限恢复18444tokens仍错SHA，0POST，总5调用/2旧回复，29/31已封存人工。普通native slash命令排除咨询路由9/9已部署。全部AC目标保留，旧21:02/01:20快照在evidence/audit-history。

## 组件来源和版本

|代号|来源和锁定候选|许可与维护|当前验证|
|---|---|---|---|
|OC|[OntiCards](https://github.com/stepll2026/OntiCards/tree/8abe9e20d58df2605b8a66c3a4296d3dcfe325a2)|AGPL-3.0；现有Flask2.3.3、Next14.1.3、Yarn锁文件、Compose|已克隆、148个Python文件语法检查通过；扫描器4个探针2失败|
|OH|[OpenHands Canvas v1.30.0](https://github.com/OpenHands/OpenHands/releases/tag/v1.30.0)，实际官方镜像内Automation1.22.0/SDK1.56.0；另查Automation1.23.2/SDK1.57.0源码|MIT；本地模式源码及镜像已核实|测试机真实模型+4次工具动作完成随机nonce/计算探针；显式配置OH_SESSION_API_KEYS_0后未认证401。高权限写凭据会进入Agent环境，未找到现成宿主发布边界，因此不作为自动修复主底座|
|GA|[gh-aw v0.93.0](https://github.com/github/gh-aw/releases/tag/v0.93.0)、[agentics b4e175b](https://github.com/githubnext/agentics/tree/b4e175bab6674279e0fe158f7dc877b77bc9d92f)|MIT；近期维护|已查repo-status/repo-assist源文件；默认分支暂无workflow，不能宣称定时已生效|
|PP|[ProPR 42931b1](https://github.com/integry/propr/tree/42931b1502eb03ac299f14e306811736fab51eb4)|Apache-2.0；源码0.9.0，npmCLI0.8.15|policy13已部署，digest3bef8bde；964/964无skip/编译通过；Issue32→PR33及反馈实证；新原生review门禁已部署，无新增模型审查验收|
|PA|[PR-Agent v0.48.0](https://github.com/The-PR-Agent/pr-agent/releases/tag/v0.48.0)|MIT；2026-10-16发布|审查候选；不单独覆盖修复部署和日报，不与主底座重复消费相同PR|
|N8|[n8n](https://github.com/n8n-io/n8n)、[Schedule Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)|现有2.42.7/Sustainable Use License，非MIT/OSI；镜像有已有本地修改|18128自然全分页已通过，新补充质量被拒；18132固定PR26完整模型CI执行70成功，5min Checks失效真证；同一完整intake已接动态PR准入，03:11自然六PR预算/旧状态保持，0新增模型|
|GH|[GitHub REST](https://docs.github.com/en/rest)、[Actions](https://docs.github.com/en/actions)、Issues/PR/Review/Merge|平台原生服务；REST版本2022-11-28|App5422414单仓六权限live；PR26/30/33真实Draft，精确Git Data/双回读；PR33 Check119950685976仅并发success，App最小短token撤销；main未改，Merge人工|
|PYGH|[PyGithub 2.10.0](https://github.com/PyGithub/PyGithub/releases/tag/v2.10.0)|LGPL-3.0；Python3.12.3|事实采集37项Linux测试与锁下部署；网络前pending、跨lookback补报、精确PR head、固定App bot身份识别，旧完整payload/文件不重写|
|PW|[Playwright 1.64.1](https://github.com/microsoft/playwright/tree/cfe490d941f992655948eee8fd4fd94e1c4234bf)|Apache-2.0；Chromium1248|旧f553/Web8abe3/3及9截图；当前3105/basec8e真实3/3、0失败0跳过、截图manifest绑定新head/base，Draft PR26；未来SHA变化仍需新验|
|PT|[pytest 9.1.1](https://github.com/pytest-dev/pytest/tree/cf470ec0bf7eb89cd97dd56df4859eae5db46447)|MIT|本机版本核实；采用JUnit/参数化断言，不写测试运行器|
|ART|[upload-artifact 7.0.2](https://github.com/actions/upload-artifact/tree/cf430e030ddbb5b0abf93d22962f4752f3646cd9)|MIT；2026-10-07发布|Actions长期产物候选；本轮先私有报告目录，不能把本地目录称为已上传artifact|
|DC|[Docker Compose](https://docs.docker.com/compose/)|Apache-2.0；采用打包机2.40.3/测试机5.0.0已有安装|Docker/Compose实测可用；不为追新升级|
|SD|[systemd timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)|系统已有255；LGPL-2.1-or-later|已启用00:00快照/09:00补报，Asia/Shanghai、Persistent、flock、15分钟超时、低权限用户；受控timer和重启实测成功，tmpfiles清理31天样本成功|
|QM|[百炼工具调用](https://help.aliyun.com/zh/model-studio/qwen-function-calling)、[代码模型](https://help.aliyun.com/zh/model-studio/qwen-coder)|用户提供现有API；非本项目开源组件|实际/models存在qwen3-coder-flash，两轮工具调用通过（455tokens）；产品问数、1024维qwen3.7-text-embedding-flash、qwen3.7-text-rerank请求均200。qwen3-coder-plus实际404未采用；金额未知|
|MH|[Mihomo 1.19.23](https://github.com/MetaCubeX/mihomo)|已有部署，GPL-3.0|既有1.19.23 native fileprovider/专用17891成功API；公网完整clone600.098秒超时。本地浅mirror用原生ensureRepoCloned/worktree及后续真实origin fetch9.994秒成功；浅cache不登记清理，未伪造marker|

## 逐功能决策

|ID与验收|现有实现及比较|采用模块和接入方式|覆盖与具体缺口|验证与新增范围|
|---|---|---|---|---|
|R01 仓库与权限 AC01/09|OC代码/远端、GH连接；服务器Codeup是另一版本|GH只读API、git SHA；配置固定repository，白名单分支codex/|App5422414单仓六权限live；PR26/33源、镜像、basec8e分别验证；原生Git准备abort/deadline已部署，旧网络失败保留|GH原生JWT/短token精确scope回读与撤销；无新GitHub客户端；真实外部fork仍未端到端|
|R02 定时/重试/恢复 AC03/11|N8、SD、GA、OH、PP原生调度比较|事实SD，Agent PP/BullMQ，普通事件N8|事实00:00已真实运行487/9，09:00/AI09:05仍启用；N8两独立5min；policy12原子Task首投递阻父/child跨poll预算，CIreceipt不自动重跑|systemd/原生BullMQ/DataTable/flock；37项事实回归、9+192首投递相关；无Task父失败门禁已补，全任务reboot恢复仍未完整覆盖|
|R03 日报统计 AC02|GA repo-status、OH monitor、PYGH/GH|PYGH API分页/SQLite/既有中文模板适配|10/22 facts run5da38704 complete/errors[]；nativeTasks13、Checks与commit statuses分列；未知基线不造0|G01新增复用GH Checks API与原生TaskDB只读快照，37项Linux/低权限LoadCredential；原生App自动短token无匿名fallback；旧完整payload不重写|
|R04 日报交付 AC02/03|GH运营Issue、OH产物、PP原生run/report|事实报告+原生独立daily alias/只读挂载|10/22三次nativeAI质量均未过；显式审核修正版10/10通过，非原生生成质量通过；rev13 instructions空/helperREADY无模型证据，同09:05Schedule|G02复用原provider/definition；不把配置/任务completed当内容正确，不把费用NULL写0|
|R05 询问/分类/回复 AC04|PP标签入口不足普通咨询；GA/OH/N8比较|N8 HTTP/DataTable/模型/原生App发布|Issue29既有两真实App回复；新真人已发现，draft998/review1022共38313tokens被gate拒绝/0POST，最后恢复18444tokens仍错SHA拒绝0POST，总5调用/2旧回复，29/31已人工封存|G03原生节点；3回复/6调用目标保留；Issue31未知封存，不以重试绕预算|
|R06 事件/防循环 AC03/04|PP polling/BullMQ、N8原生Schedule/HTTP/DataTable|独立18128全量分页+open_count一致性门禁，原7workflow不动|自然poll966 complete，29线程264事件，29issues/50comments/0inline/19PR；短token撤销、sticky未知跨重启；原since漏评论已修并实证|原生close/reopen/全部PR评论投影/多线程15、预算批20、并发8fixture通过；不把fixture当所有真实模型事件E2E，新语义回复质量与发现成功分开|
|R07 PR审查 AC05/08|PP原生MCP review_pull_request、OAuth短grant、既有review parser/formatter/publisher；N8原生子workflow/DataTable|复用同一完整intake，单仓read+review、明确编码alias、CA验证loopback TLS、固定受限SSH；同tuple持久准入及跨grant原生operation查重|TLS/SSH12、自然六PR真实只读链、baseline12、envelope13/SSH未知6/隔离SQLite16、上游OAuth52通过；0模型。policy13无标签可信owner worker/只读恢复/实际head+base检查已部署，20新+265相关fixture；最终baseline前disabled|新薄适配只接原生权限/入口/receipt，不新造Agent。普通分支/fork只读允许、不可读转人工；posted不等完成，unknown不重发，历史无效review仍失败|
|R08 修复/反馈/冲突 AC05/08|PP ultrafix/worktree/宿主发布，比较OH/GA|PP+OpenCode单并发3轮，原生Follow Up与持久history|Issue32原生修复产生PR33，同PR真实反馈续办到fdd3，最终9/9+PDF2/2+竞态10/10；Issue25失败和SQL三轮拒绝仍保留|G03/G05原生worktree/host发布/Follow Up；真实fork/语义冲突出口未全验；policy12复用原生Task原子首投递先于child/模型，补父失败跨poll预算；9+192相关测试|
|R09 外部fork/权限 AC09/10|GH metadata、PP只读Agent/宿主finalization|原生continuation+实例merge禁用/codex前缀/测试机禁build|PR33/PR26专属Agent边界，rootless实际镜像/UID/subUID/cgroup/网络/socket/caps负向；外部fork拒入此CI|App/privatekey/SSH/registry只可信host或CI，PR仅短模型token；原生fork continuation/作者归属/原PR不关闭端到端待验|
|R10 仓库知识 AC01/12|OC文档、OHcontexts/GAmemory、PP原summary|版本化AGENTS/.propr/知识模板、原summary/git/AsyncLocalStorage/BullMQ|policy11知识主路径69/69，真实8abe→c8e→main、22上下文/29缓存/4改增文件、0模型；全语义索引partial停|G-K01至G-K04 pinning/deadline/6分析600秒/重入预算局部修复；不造新知识库、不把主路径通过当全仓语义索引成功|
|R11 隔离部署 AC06/09|OC原Dockerfile/Compose/healthcheck，DC|既有override/独立网络/卷，测试机pull --no-build；当前新预览18111|现成Compose独立18111产品验证、5机rootless严格网络与cgroup；可信SSH/native registry固定digest已实接，PR26真kol构建/5机测试|G04：ForceCommand/source-IP/hostpin、SFTP证据、Skopeo1.13.3单entry可信publisher/fetch；PR不拿root socket/SSH，测试机不build|
|R12 前后端/API/迁移 AC06|OC yarn/Flask/Alembic/pytest|原命令与业务用例，独立合成数据|PR26rootless r4 API7/7、真实四格式导出，PR33专项9+2+10；原migration5pass1skip|G04复用测试/Compose，three_way_check缺失与原lint/tsc基线仍未修，不以业务success覆盖它们|
|R13 浏览器关键业务 AC06|PW原生runner/APIRequestContext/PNG/JSON/JUnit|登录权限、schema、卡片、真实chat/embedding问数、治理导出|PR26rootless r4 PW3/3零skip、9原生PNG，query250/基础空值治理；r2限流/r3预扣失败保留；无stub/跳过|G04复用原业务spec，固定trustedbundle；同秒JWT精度通过无模型红绿probe后fixture跨秒重登，未放松401断言|
|R14 证据与版本 AC07|PW reporters、GH Checks、PP Redis Lua/AOF、现有Nginx|原生JSON/JUnit/PNG/manifest、Nginx只读allowlist、n8n5min失效|PR26rootless37文件HTTP哈希、POST403，Check119988255661；PR33专属Check；synthetic neutral→action_required独立回读，20边界fixture，真实schedule复查|G07复用JWT/HTTP/DataTable/Schedule；只读PRtoken与Checks写token分离撤销，保留旧证据/失效不重跑；30天持续与网络中断即时性未验|
|R15 状态/队列/预算 AC08/11|PP UI/BullMQ/ultrafix/Express session/OAuth|原生认证/私网HTTP opt-in、已有Follow Up；GitHub官方name nullable，复用authBearer回退|OAuth空姓名和HTTP uuid原生fallback已部署、NewTask/PR33反馈真实；Git准备abort/deadline实际子进程停止；索引预算/重入policy11已部署|G05/G-K复用原状态/AbortController/simple-git/native预算；prequeue原生Stop/真实Redis/SQLite25/25及本地Git continuation/语义负例50/50已验；历史history_id缺失、CI人工重跑尚为受信操作流程|
|R16 人工合并 AC10|GH原生Review/Checks/Merge|仅提供真实PR与证据链接，由维护者操作GitHub Merge|Draft PR26/30/33、真实报告和Check入口；机器人不merge/main写/autoapprove/弱化保护|采用GitHub原生Merge由维护者；当前Check必须精确SHA，专项success不扩成全仓可合并|
|R17 持续运行/升级 AC03/12|DC restart、SD原生服务/备份|固定image digest，空队列升级，专用用户及原生ACL|policy13 API/worker/daemon已部署3bef8bde；事实timer跨日真实成功，Linux37；n8n独立持久/重启，rootlessuser daemon/ACL配置已实证|G04原生systemd/Compose；indexworker暂停/summary关；宿主真reboot、磁盘硬quota、30天持续留存仍未验|
|R18 SQL扫描缺陷（首个修复尝试） AC05/14|OC sql_from_guard；检索SQLGlot/sqlparse，实际探针sqlparse0.6.0 BSD-3-Clause|本轮不采用生产候选；保留共享接口及现有源码，未引入解析器|3轮SQL候选独立拒绝，数组/dollar字符串漏真实表风险；生产未改、未发修复PR|G08明确未修，保留sqlparse/lexer/调用方/PG证据，不用安全退化换个例通过|
|R19 治理PDF可用性 AC06/14|OC既有DOCX构建、python-docx与soffice；先研究后改|三文件修复复用于main c8e，保留7个main变更blob|PR26版式串行3/API7/PW3；其并发1/2失败由原生Issue32→独立PR33解决，最终fdd3的9/9、并发2/2、竞态10/10通过|G09复用LibreOffice独立UserInstallation临时profile、原PDF路径/测试；PR33专项证据单独，不回写PR26旧版本|

## 当前新增代码边界与复用增量

- G-Review：上游无自动新PR/更新审查开关，HTTP入口又无法直接原生OAuth同源consent。复用OpenSSH固定服务能力、原生MCP短grant/operation/read+review、N8既有intake/DataTable；HTTP MCP关闭、18135仅loopback/CA验证。新代码精确对应跨grant幂等、严格原生回执投影、≤4KiB输入与状态未知边界、首次baseline，不造auth broker。policy13原生worker门禁已在真实Redis/SQLite fixture及964项镜像回归通过后部署；新接线尚无模型审查成功，等最终PR30后baseline启未来版本。
- R14最终交付：依据`research/final-delivery-reuse.md`复用zipfile/Gitleaks/现有Nginx publisher/精确Git blob和公开产物hash；三allowlist映射与HTML索引只是薄适配，无新网站或认证服务。

- G-CI intake：已部署复用18128完整分页/水位/DataTable→18132原生准入；自然03:11一批6PR、0login/SSH/model，同tuple永久消费。PR30/33原unknown保留并受控reconcile为budget_exhausted；余额15445<45000，不自动重置或重发。新head/base新增tuple，fork/非codex/main人工。52表达式+20原生预算批fixture通过；不新增Schedule/采集器/队列。依据`research/preview-intake-dispatch-reuse.md`、`research/ci-batch-budget-reuse.md`。

- G01/G02：PyGithub原生分页/Checks API、SQLite既有reports事务主键、systemd LoadCredential/App installation自动短token、原生TaskDB只读投影；37项实机回归。完整旧payload/文件SHA保持，未造broker/scheduler。
- G03：n8n原生Schedule/DataTable/HTTP/JWT/模型节点及有限表达式；普通咨询全分页已真实定时、slash命令排重9/9；最终语义补充失败人工封存，不新建事件队列或Agent。
- G04：RootlessKit/Docker/systemd/UID firewall/OpenSSH pinned ForceCommand/SFTP/Skopeo/现成registry/Compose/pytest/PW的固定边界适配。官方SSH节点缺hostpin采用镜像已有OpenSSH；全部构建kol，5机load/test。现有registry凭据非repo最小，限定可信单entry不可给PR。
- G05：截至policy13复用既有Task/history/continuation/mergegate/Redis Lua/Express/parser/metrics/AbortController/simple-git，保留非维护与原内部Ultrafix行为；964/964分组测试及精确patch/digest。首投递原子Task门禁已补无Task父失败，数据库不可写拒绝派发；不泛称所有外部隐含模型请求费用已封顶。
- G06/G-K：版本化知识模板及原生summary pinning、fetch失败停止、准备deadline、6分析/600秒共享预算、BullMQattempt与HEAD/main去重复；首次真实索引失败保留，policy11知识主路径69/69无模型通过，未完整付费重验，不造新知识系统。
- G07：原生Nginx/HTML/JSON/JUnit、SHA manifest、n8n原生App版本门禁与Checks注册/5min失效；Check写token与PR只读token分离。首次PATCH未知/Code格式失败保留；20 Code断言、真实neutral→action_required与自然5min当前版本复核已通过。
- G08：SQL仍未修，三轮不安全候选不发布。G09：PR26已有DOCX/soffice版式复用；PR33进一步复用LibreOffice独立profile/临时目录，真实自动续办与专项并发通过。
- G-CI模型：原生NewAPI普通私有group+短token（双alias/IP/900s/额度/撤销），专用Nginx exact chat/embedding端点；实际r2 429/r3预扣失败后仅显式调整既有rate/burst/原生额度，r4真实业务通过，之后停止，模型/公开DNS不扩大到其它内网。产品JWT同秒精度缺陷以真实无模型探针确认，fixture等待1.05秒再登录，仍保持401断言。

## 历史新增代码边界（21:02原文，不作为当前部署状态）


- G01：自然日统计、日界快照、精确PR head和固定App身份适配；复用PYGH客户端/分页，不实现HTTP库。20项测试覆盖失败/窗口/重复/伪造评论，不把unknown当0。
- G02：复用SQLite原reports主键/事务，网络前登记pending、catch-up union已知pending/partial，完整payload保留，旧文件内容及mtime可恢复但不重写新口径；30天tmpfiles/原生ACL已实证。来源research/report-recovery-acl-reuse.md；不另建scheduler/queue。
- G03：模板、仓库规则、现成Agent和事件配置；不实现新的Agent循环。
- G04：OntiCards专有Compose覆盖、测试spec和部署命令；使用已有runner/构建器。
- G05：复用PP原生只读Agent/宿主发布/continuation/merge gate；最小禁止merge、非codex发布及测试机build。policy4原Redis Lua/AOF TTL环境配置（默认3600、部署2592000、整数60～31536000）两key/刷新实测，保留64MiB；原Express/session仅RFC1918精确origin HTTP opt-in，认证/HttpOnly/Lax/CSRF保留。policy5复用task/history/原native请求阻已有failed child跨poll重预算，原config私有副本ownership、analyze时限、错误投影及未知usage修正，统一287测试。policy6复用authBearer显示名fallback（78认证/权限测试）及原严格parser发布前拒绝无效review（31分组测试）；最终49文件patch可精确应用上游，tree efa47fa828a5032ebcc6c67e7e3f75276ad34048。已部署digest91d40150；新实际有效审查/浏览器仍待验。没有新日志/认证/Agent/发布/任务系统。
- G06：事实与运维文档。
- G07：证据manifest/当前SHA核对/清单脱敏薄适配；复用Nginx attachment交付原生Playwright自包含HTML，保留sandbox，下载本地打开已验；原生GitHub Check一次neutral发布，不自研截图/HTML报告/认证或长期监控。
- G08：已复现SQL缺陷；3次候选经独立审查拒绝，未修改生产源码、未发布修复PR。后续方言接口需要明确设计，本轮保持未修复。
- G09：实际API与PDF渲染暴露的导出故障；复用项目已有DOCX构建及LibreOffice转换，仅补缺失依赖和版式设置，不新建导出器。

## 原选型理由与历史状态（来源保留，当前状态以上表为准）

GA安全输出有价值，但此仓库无默认分支workflow，用户保留最终合并，日程不能提前生效；模型引擎兼容也必须验证。PP因实际凭据边界成为主底座，不继续补造OH发布流程。PA仅负责审查，主底座覆盖后不重复启用。N8复用正常server/DataTable实现Issue29受控双回复，并已启用独立只读5min采集；长期自动写尚未启用，旧草稿失败保留。OH已真实通过本地模型/工具探针，但缺所需现成写凭据隔离边界；仅保留测试记录。

历史组件比较和原始失败仍见research/environment.md、repository.md、testing.md、orchestration.md及各阶段evidence；不将后来的修复/部署回写成历史通过。

最新证据：`propr-policy6-deployment.json`、`propr-policy6-patch-validation.json`、`pr26-policy5-native-review.json`、`pr26-policy5-invalid-review-response.json`、`n8n/persistent-polling-first-schedule-summary.json`、`maintenance-draft-pr.json`、`rootless-runtime/summary.json`。完整未覆盖目标见`research/acceptance-gap-audit.md`；旧末段18:57陈述仅属历史阶段，不覆盖本页首段/逐功能表。

## 历史阶段记录（以下不作为当前状态）

### 17:26 新增原生配置复用证据（实施前）

用户选择内网HTTP。`research/propr-intranet-http-reuse.md`核对锁定Express5.2.1 / express-session1.18.2 / connect-redis9.0.0 / passport-github2 0.1.12及官方文档。复用`AUTH_ALLOW_HTTP_REDIRECT=true`、现有精确FRONTEND_URL CORS、`PROPR_TRUSTED_PROXY_PEERS`与GitHub OAuth/Redis session；缺口仅为production非loopback cookie强制Secure以及HTTP redirect原先只匹配host全端口。G05登记必要局部配置适配：独立`AUTH_INSECURE_SESSION_ORIGIN`，仅canonical RFC1918 IPv4且与API_PUBLIC_URL/FRONTEND_URL精确同origin、无cookieDomain才允许该HTTP会话；此模式重定向也限制同origin，保留HttpOnly/Lax/OAuth state及原生CSRF，其他默认Secure。尚未改源码或部署，不使用development/demo/免认证，不新造认证系统。来源：[express-session锁定版本](https://github.com/expressjs/session/blob/v1.18.2/README.md)、[Express反代配置](https://expressjs.com/en/guide/behind-proxies/)。

配置优先级另已核实：`configLoader.ts:208–215`的非空GITHUB_REPOS_TO_MONITOR在无CONFIG_REPO时优先于DB enabled。早期DB false仅是存储值，实际daemon读取env且当时AI项为0；17:22主流程移除覆盖并从持久配置读取唯一enabled仓库。Issue25已进入同一原生task，首次clone与重试失败证据见`evidence/issue25/`。当前模型已由主流程切换为qwen3.8-max-0902，工具探针2次动作返回nonce/sum99；旧qwen3-coder-flash业务/日报结果仍按历史模型记录。

### 17:37 状态补充（历史）

Issue25实际出现三个correlation的原生轮询执行，均失败在clone/refresh基础设施，未进入Agent；最早一轮的TLS失败与attempts2/3 ownership保护已分别保留。主流程17:34停止daemon/worker，17:36只读inspect确认exited，API仍running。原生AI标签未撤销时，processing标签在失败后移除且普通child job被删除，下一轮可再接单；单job3次不限制跨轮次。17:37原parent/child job均不存在，队列waiting/active/failed为0。恢复研究与证据见`research/issue25-native-recovery.md`及`evidence/issue25/`；不能将此计为自动成功或成功恢复。

G05新增TTL与精确内网HTTP的最小配置适配现已实现到候选源码，构建前分组复验252政策、110日志、49认证测试全部通过且0 skip，证据`evidence/propr-policy4-{policy,live-output,auth}-tests.log`；日志默认TTL33项另通过。此时尚未确认policy4生产镜像部署，当前运行镜像仍以manifest的policy3为准。HTTP研究原文为实施前快照；OAuth浏览器完整往返及30天持续访问验收未完成。历史“尚未改源码”描述仅适用于17:26阶段，不代表本补充时状态。

18:57运行补证：原生UI暂停/恢复均保存成功，definition revision10、next=2026-10-23T01:05Z，daemon heartbeat真实存在，3条既有日报run未增加，队列0。原生缓存复用既有浅mirror建立，worktree及真实GitHub origin fetch9.994s通过；公网完整clone600秒失败仍保留，浅缓存registry拒绝自动清理且未伪造标记。见daily-native-ui-management.json、native-git-bootstrap.json；均不替代Issue25编码/发布成功。


### 19:34 验证增量（不覆盖历史失败）

- G01/G02事实日报：网络前pending登记、精确PR head状态查询、按已核实App bot ID/type识别原生评论已部署。Linux20/20，完整旧日报payload/MD/JSON及权限/timer不变。对应入口失败漏补报、PR commits250上限、marker漏计/伪造三个具体缺口，见reporting-pending-head-deployment.json与reporting-bot-identity-deployment.json；实现commit15423d32。
- AC04：Issue25原150字预期无附件依据、否定句regex两项误报，原红证据保留，逐句复核无实质事实错。已有10条本App评论，不再发第11条冒充限额验证；新明确咨询验收Issue29由已授权Edge人类账号创建（连接器创建403），尚待真实后台初答与补充续办。
- AC05原生PR26审查：短token issue-write/PR-read添标签403，使用已有PR-write后成功，只发表comment6339444121一次。脚本缺原生依赖初始化导致dispatch前失败，核空队列/无task后恢复同评论；真实job随后因worker缺标签配置skipped/missing_required_label，0模型/0Agent。已用原生PRIMARY_PROCESSING_LABELS=AI修正并仅重建空闲worker，不声称审查已完成。
- PDF并发：3105现有镜像同时导出2份，一份成功一份RuntimeError，串行3/API7/PW3仍为各自通过。仅探针加入LibreOffice原生UserInstallation临时profile参数后2/2成功；业务源码未改，不能冒称已修复。复用依据pdf-concurrency-reuse.md，原失败pdf-concurrency-probe.json与参数验证pdf-concurrency-native-parameter.json分别保留。

### policy6 新缺口登记（实施前，AC09/11/14）

原生OAuth及旧session响应直接传GitHub可为null的姓名，UI严格string guard使已认证admin误显示只读。官方GitHub public/private-user schema已实取核实nullable，现有authBearer已有name→login回退。G05最小复用该fallback到新OAuth和旧session响应；不放宽UI/权限schema、不改用户资料、不新增认证。拟两处字段映射及原生OAuth/session/权限测试，依据 `research/github-display-name-reuse.md`；policy6尚未部署。

### G04/G07 原生执行环境补充（实施前）

Actions缺隔离runner，保留原候选并比较现有n8n SSH节点：复用其命令/传文件能力，以及两机已有Docker rootless安装器、systemd/cgroup2/RootlessKit。缺口是uidmap与专用非root身份/UID网络隔离、固定head/base可信控制bundle和自动验收关联；先仅补运行时、拒绝宿主/内网/metadata负向探针，不创建SSH授权、不build或部署PR。来源和实际版本见`research/n8n-rootless-preview-reuse.md`；不新建调度/runner管理/代理，不扩大App权限。
