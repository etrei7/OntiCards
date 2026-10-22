# OntiCards 逐功能复用矩阵

当前状态截至2026-10-22 18:57：API/worker/daemon运行policy4，仓库接单disabled；事实日报00:00/09:00定时启用，原生AI日报revision10 schedule on（下次10月23日09:05）且未触发，n8n inactive。第三次受控原生日报31.854秒完成、quality=true，输入14104/输出1650/缓存11264，USD未知；OAuth完整往返及受保护原生日报UI已实测。保留首次质量失败、第二次超时，不能把一次验收当长期运行。

当前产品head3105/basec8e已在kol-stage2构建、5机18111验证：转换3/API7/PW3，9截图/6页PDF视觉；迁移5通过1跳过。[Draft PR26](https://github.com/stepll2026/OntiCards/pull/26)及[证据门户](http://10.66.66.5:18123/onticards-reports/acceptance/pdf-3105/)可读，原生Check119778059245为neutral、绑定精确head/base且main未改。HTML受同源sandbox限制，采用现有Nginx附件下载，本地原生详情/嵌入图验证通过；不放宽sandbox、不造localStorage shim。此PR是独立复用既有修复并受信发布，Issue25自动链仍未成功。

新提供Mihomo配置已复用原生file provider及任务专用17891/ONTICARDS-PROVIDED，delay/API200，共享selectors/DNS/rules保留；最新600.098秒完整clone探针已ETIMEDOUT，未记为通过。旧订阅403与其他失败保留。事实日报新增5行SQLite known partial候选恢复、tmpfiles原生ACL，11项测试及18:39锁下部署通过；最终合并仍由维护者操作。

首版矩阵已先交付；后续每项状态按真实证据更新。R19的实施前复用候选最初写于测试报告，后归并本矩阵，不倒称该行先于记录。源码/文档核实、可启动、端到端通过是不同状态。未执行项目不会写成通过；功能目标保持任务书全部范围。早期connector创建Issue的403、缺App时后台拒绝启动、PDF500/五页破版及旧208项政策测试均保留为历史阶段证据。

## 组件来源和版本

|代号|来源和锁定候选|许可与维护|当前验证|
|---|---|---|---|
|OC|[OntiCards](https://github.com/stepll2026/OntiCards/tree/8abe9e20d58df2605b8a66c3a4296d3dcfe325a2)|AGPL-3.0；现有Flask2.3.3、Next14.1.3、Yarn锁文件、Compose|已克隆、148个Python文件语法检查通过；扫描器4个探针2失败|
|OH|[OpenHands Canvas v1.30.0](https://github.com/OpenHands/OpenHands/releases/tag/v1.30.0)，实际官方镜像内Automation1.22.0/SDK1.56.0；另查Automation1.23.2/SDK1.57.0源码|MIT；本地模式源码及镜像已核实|测试机真实模型+4次工具动作完成随机nonce/计算探针；显式配置OH_SESSION_API_KEYS_0后未认证401。高权限写凭据会进入Agent环境，未找到现成宿主发布边界，因此不作为自动修复主底座|
|GA|[gh-aw v0.93.0](https://github.com/github/gh-aw/releases/tag/v0.93.0)、[agentics b4e175b](https://github.com/githubnext/agentics/tree/b4e175bab6674279e0fe158f7dc877b77bc9d92f)|MIT；近期维护|已查repo-status/repo-assist源文件；默认分支暂无workflow，不能宣称定时已生效|
|PP|[ProPR 42931b1](https://github.com/integry/propr/tree/42931b1502eb03ac299f14e306811736fab51eb4)|Apache-2.0；源码0.9.0，npmCLI0.8.15|policy4 digest5c6342f9，完整TS/252政策/49认证/110日志通过；OAuth原生UI实测。日报第三次quality=true，revision10 schedule on（下次10月23日09:05）；Issue→PR未验|
|PA|[PR-Agent v0.48.0](https://github.com/The-PR-Agent/pr-agent/releases/tag/v0.48.0)|MIT；2026-10-16发布|审查候选；不单独覆盖修复部署和日报，不与主底座重复消费相同PR|
|N8|[n8n](https://github.com/n8n-io/n8n)、[Schedule Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)|现有2.42.7；Sustainable Use License，非MIT/OSI开源；现有镜像有本地修改|新增原生HTTP/JWT/Data Table/条件节点配置补充未打AI标签咨询入口；全部inactive。CLI读取#19–24并调用真实模型6次/7302tokens，草稿quality=false；无网重放能拦截不合格输出。正常server Data Table/幂等、持久事件水位、长期代理及真实回复仍缺；不是已启用自动回复|
|GH|[GitHub REST](https://docs.github.com/en/rest)、[Actions](https://docs.github.com/en/actions)、Issues/PR/Review/Merge|平台原生服务；REST版本2022-11-28|App5422414单仓六权限live验证通过；Git Data API原生发布精确PDF候选，8对象SHA与双回读一致；PR26一次neutral Check119778059245已发布，短期token撤销、main未改。早期connector create_issue403仍保留；真实Issue→PR未验|
|PYGH|[PyGithub 2.10.0](https://github.com/PyGithub/PyGithub/releases/tag/v2.10.0)|LGPL-3.0；Python3.12.3|真实事实采集、11项统计恢复测试；跨lookback已知partial和原生ACL修复已部署，完整窗口record/文件哈希不变|
|PW|[Playwright 1.64.1](https://github.com/microsoft/playwright/tree/cfe490d941f992655948eee8fd4fd94e1c4234bf)|Apache-2.0；Chromium1248|旧f553/Web8abe3/3及9截图；当前3105/basec8e真实3/3、0失败0跳过、截图manifest绑定新head/base，Draft PR26；未来SHA变化仍需新验|
|PT|[pytest 9.1.1](https://github.com/pytest-dev/pytest/tree/cf470ec0bf7eb89cd97dd56df4859eae5db46447)|MIT|本机版本核实；采用JUnit/参数化断言，不写测试运行器|
|ART|[upload-artifact 7.0.2](https://github.com/actions/upload-artifact/tree/cf430e030ddbb5b0abf93d22962f4752f3646cd9)|MIT；2026-10-07发布|Actions长期产物候选；本轮先私有报告目录，不能把本地目录称为已上传artifact|
|DC|[Docker Compose](https://docs.docker.com/compose/)|Apache-2.0；采用打包机2.40.3/测试机5.0.0已有安装|Docker/Compose实测可用；不为追新升级|
|SD|[systemd timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)|系统已有255；LGPL-2.1-or-later|已启用00:00快照/09:00补报，Asia/Shanghai、Persistent、flock、15分钟超时、低权限用户；受控timer和重启实测成功，tmpfiles清理31天样本成功|
|QM|[百炼工具调用](https://help.aliyun.com/zh/model-studio/qwen-function-calling)、[代码模型](https://help.aliyun.com/zh/model-studio/qwen-coder)|用户提供现有API；非本项目开源组件|实际/models存在qwen3-coder-flash，两轮工具调用通过（455tokens）；产品问数、1024维qwen3.7-text-embedding-flash、qwen3.7-text-rerank请求均200。qwen3-coder-plus实际404未采用；金额未知|
|MH|[Mihomo 1.19.23](https://github.com/MetaCubeX/mihomo)|已有部署，GPL-3.0|用户提供配置下载200，原生file provider/专用17891切ONTICARDS-PROVIDED，delay362ms/API200；共享selectors/DNS/rules保留；完整clone在600.098秒超时，旧403/150秒超时与探针错误分别保留|

## 逐功能决策

|ID与验收|现有实现及比较|采用模块和接入方式|覆盖与具体缺口|验证与新增范围|
|---|---|---|---|---|
|R01 仓库与权限 AC01/09|OC代码/远端、GH连接；服务器Codeup是另一版本|GH只读API、git SHA；配置固定repository，白名单分支codex/|App身份/精确权限/单仓live通过；宿主HTTP/1.1匿名clone小探针成功，但Issue25实际worker clone TLS EOF、后续ownership拒绝，保留不同环境结果|`evidence/github-app-live-verification.json`、`github-app-backend-configuration.json`；不新增GitHub客户端|
|R02 定时/重试/恢复 AC03/11|N8、SD、GA、OH、PP原生调度均比较|事实SD，Agent PP polling/BullMQ；不另造调度|事实00:00/09:00启用；AI revision10 schedule on（下次10月23日09:05），cron原生计算09:05已验但未触发；Issue25跨poll停止仍缺|11统计恢复测试；known partial跨lookback修复、18:39锁下真实部署/不重采complete；不将此算Agent恢复|
|R03 日报统计 AC02|GA repo-status、OH repo monitor、PYGH/GH|PYGH采集+SQLite持久快照+现成中文报告模板调整|模板未覆盖自然日边界、日界快照、closed/reopened事件、Issue/PR分离、初始未知值|G01确定性统计适配：API分页复用，事件ID去重，窗口唯一，失败写null；必须边界/失败/重复测试|
|R04 日报交付 AC02/03|GH运营Issue、OH任务产物、PP原生报告|事实报告+PP原生run/report，revision10实时只读挂载|第三次run2957780b质量true、31.854s、14104输入/1650输出/11264缓存、USD未知，OAuth UI可读；正式schedule已配置启用、下次2026-10-23 09:05；daemon已运行；此前两失败保留|G02窗口唯一/动态输入合同；quality.json/production-provenance.json，禁止把受控验收冒充定时日更|
|R05 询问/分类/回复 AC04|OC Issue表单；GA repo-assist；OH monitor/events；PP标签入口未覆盖普通咨询；已检索N8原生节点|N8 2.42.7 HTTP读取开放Issue/PR及讨论，现有模型中文草稿、条件校验、Data Table；JWT/安装token/评论节点只配置未连线|已读#19–24、模型6次，quality=false；#23缺AI标识、#20缺字段、无代码依据仍全判可修复。无公开回复；分类不构成修复授权|G03工作流配置；`research/issue-triage-reuse.md`、`evidence/n8n/quality-review.json`；校验重放全转人工核实，不另造Agent循环|
|R06 事件/防循环 AC03/04|PP原生polling/BullMQ；N8原生Trigger/HTTP/Data Table/条件节点|PP 5分钟标签修复入口；N8补充一般咨询事件，inactive；不接托管relay或新增公网webhook|N8正常server Data Table未验（CLI旁路），关闭/重开持久水位、机器人防循环、每线程上限、POST不确定回读、人类续办、长期代理仍缺|G03复用配置；无网重放仅证明不合格输出被拦，不能计幂等/长期事件验收；未发GitHub消息或任务|
|R07 PR审查 AC05/08|OH PR Review、PA、PP、GA|一个主审查组件，独立上下文读diff与测试结果|真实构建/浏览器不是LLM审查自带结果|模板G03与测试调用G04；按位置/依据评论；不得自动approve|
|R08 修复/反馈/冲突 AC05/08|OH Issue-to-PR、GA repo-assist、PP ultrafix|PP+OpenCode+已有worktree/容器，单并发、最多3轮|Issue25原生接单后clone TLS失败及ownership重试拒绝，未进入Agent；daemon停。PDF复用不冒称首次生成；SQL3轮拒绝|G03配置；已有候选API发布不是Issue→PR成功；policy4未重新编写Agent/分支管理器|
|R09 外部fork/权限 AC09/10|GH fork metadata、PP宿主finalization；OH写凭据进入Agent环境|PP只读Agent token与宿主发布；fork受控关联分支|G05实例禁止合并/codex前缀/测试机禁build，复用原生same-repo非codex continuation|policy4完整TS编译、252政策测试与生产dist验证通过；真实无权fork/提交归属和Agent边界仍待验|
|R10 仓库知识 AC01/12|OC README/CONTRIBUTING/SECURITY与模块；OH contexts/GA memory|版本化知识文件，使用实际task SHA上下文|已有AGENTS/运维知识草稿与实际SHA事实档案；默认分支未合并，真实main变更后增量刷新仍待验|文档G06；已出repository.md；不建向量知识系统|
|R11 隔离部署 AC06/09|OC原Dockerfile/Compose/healthcheck，DC|既有override/独立网络/卷，测试机pull --no-build；当前新预览18111|API3105/basec8e，Web复用相同tree；真实服务启动、迁移5通过1跳过；Draft PR26。旧18110与原服务隔离|G04仅打包机构建，`deploy/evidence-pdf-current-main/runtime/runtime-manifest.json`；不碰既有生产服务|
|R12 前后端/API/迁移 AC06|OC yarn命令、Flask接口、Alembic、pytest|原命令及业务用例、独立合成数据|3105/basec8e API7/7、soffice3/3；原生migration5pass/1skip，缺three_way_check不计通过；旧lint/typecheck失败保留|G04项目spec与数据；当前main7路径blob原样保留，不把空库/升级迁移/完整schema校验混同|
|R13 浏览器关键业务 AC06|PW原生runner、APIRequestContext、截图/trace|登录权限、元数据、卡片、真实模型问数、治理导出|3105/basec8e PW3/3、0skip，真实查询250及成功截图，Draft PR26；业务API各步200，截图manifest绑定新组合、6页PDF视觉完成|G04业务测试；公开发布清单排除全部trace，HTML内嵌步骤凭据已脱敏；旧f553证据保留，新head/base后仍须重新验|
|R14 证据与版本 AC07|PW reporters、GH Checks/artifacts、PP Redis Lua/AOF、现有Nginx|原生HTML/JSON/JUnit/manifest；Nginx只读门户与HTML attachment；G05原生日志TTL配置|PR26门户GET200/PUT403/DB404，HTML实际下载SHA一致、本地详情/图正常；Check119778059245 neutral精确head/base。Redis2592000及刷新已验；长期30天/自动版本失效/Actions待验|G07薄关联/清单脱敏，G05 TTL；不造报告/存储/认证系统，不使用localStorage shim；raw trace不发布|
|R15 状态/队列/预算 AC08/11|PP原生UI/BullMQ/ultrafix，Express session/Redis/OAuth|原生认证+精确HTTP opt-in和已有任务管理入口|49认证测试、OAuth完整往返及原生日报受保护UI通过；Activity Overview temporarily unavailable，取消/恢复/预算出口未验，USD未知|G03配置/G05局部扩展；API/worker/daemon运行，仓库接单disabled；不启用demo/development/免认证|
|R16 人工合并 AC10|GH原生Review/Checks/Merge|仅提供真实PR与证据链接，由维护者操作GitHub Merge|PP合并入口由G05实例策略关闭，不变保护规则；当前head变化重新检查|没有新增执行合并代码；新增的是拒绝执行的策略检查|
|R17 持续运行/升级 AC03/12|DC restart、SD服务、现有管理|固定版本、原生暂停恢复、备份状态|report.py/tmpfiles18:39锁下备份部署、apply2次、facts/portal200，PUT403、DB404，timer仍active/enabled；完整Agent升级恢复待验|G04现有配置；备份reporting-review-backups/20261022T103932Z，deployment.json；无不必要fork|
|R18 SQL扫描缺陷（首个修复尝试） AC05/14|OC sql_from_guard；检索SQLGlot/sqlparse，实际探针sqlparse0.6.0 BSD-3-Clause|本轮不采用生产候选；保留共享接口及现有源码，未引入解析器|3次模型尝试后独立审查拒绝：数组/dollar字符串新增漏真实表；完整调用方及PG15.18只读实测证实风险。默认sqlparse也有跨方言歧义|G08未修复；`research/sql-candidate-review.md`保留13组scanner/8组调用方/14组lexer及PG证据；停止换循环重试，不能用安全退化换个例通过|
|R19 治理PDF可用性 AC06/14|OC已有_build_docx_with_python、python-docx与soffice；实施前候选在testing-report，后归并矩阵|原3文件修复复用于main c8e，7个main变化blob保持一致|当前3105组合转换3/API7/PW3、9截图与6页视觉通过，migration5/1skip，受信创建[Draft PR26](https://github.com/stepll2026/OntiCards/pull/26)；非Issue25自动成功。旧f553完整证据保留|G09仅依赖和版式，`deploy/evidence-pdf-current-main/`与`evidence/pdf-current-main-pr.json`；主分支未写、未合并，soffice并发待验|

## 新增代码边界

- G01：自然日统计与快照适配，源于R03模板口径不覆盖；使用PYGH，不实现HTTP客户端/分页库。
- G02：repo/window唯一日报、补采、首次基线与到期元数据；SQLite原生事务/唯一约束。审查后5行合并已知未complete日期、不超过requested day、不回填未知历史；复用systemd255 a+恢复UID101/default ACL，保留既有1000但新环境不新增1000，父目录0700。11测试与18:39实机通过，来源research/report-recovery-acl-reuse.md；不实现数据库/调度/权限平台。
- G03：模板、仓库规则、现成Agent和事件配置；不实现新的Agent循环。
- G04：OntiCards专有Compose覆盖、测试spec和部署命令；使用已有runner/构建器。
- G05：复用 PP 只读 Agent token、宿主发布、原生 continuation；最小实例政策拒绝合并、非 codex 分支发布、测试机 Docker build。policy4 再复用现有 Redis Lua/AOF，仅将硬编码 TTL 扩展为 `PROPR_LIVE_OUTPUT_TTL_SECONDS`（整数60～31536000，默认3600，部署2592000），保留64MiB裁剪；真实 Redis 两键同TTL/写入刷新已验。复用原生 Express/OAuth/Redis session，仅补 `AUTH_INSECURE_SESSION_ORIGIN` 的精确 RFC1918 origin opt-in 与 redirect 收紧，保留认证/HttpOnly/Lax/原适用CSRF。完整补丁 `deploy/propr-maintenance-policy.patch` 共30文件，可应用固定上游并匹配全部源码；252政策/49认证/110日志测试0跳过，API/worker policy4实测。OAuth真实往返/原生日报UI已验；容量截断、全任务脱敏与长期访问仍待验；没有新日志系统/认证/沙箱/发布流程。
- G06：事实与运维文档。
- G07：证据manifest/当前SHA核对/清单脱敏薄适配；复用Nginx attachment交付原生Playwright自包含HTML，保留sandbox，下载本地打开已验；原生GitHub Check一次neutral发布，不自研截图/HTML报告/认证或长期监控。
- G08：已复现SQL缺陷；3次候选经独立审查拒绝，未修改生产源码、未发布修复PR。后续方言接口需要明确设计，本轮保持未修复。
- G09：实际API与PDF渲染暴露的导出故障；复用项目已有DOCX构建及LibreOffice转换，仅补缺失依赖和版式设置，不新建导出器。

## 尚未最终采用的理由

GA安全输出有价值，但此仓库无默认分支workflow，用户保留最终合并，日程不能提前生效；模型引擎兼容也必须验证。PP因实际凭据边界成为主底座，不继续补造OH发布流程。PA仅负责审查，主底座覆盖后不重复启用。N8已采用原生模块补一般咨询入口，限inactive草稿/重放，质量与长期运行缺口未解决前不启用。OH已真实通过本地模型/工具探针，但缺所需现成写凭据隔离边界；仅保留测试记录。

原始证据见 `research/environment.md`、`repository.md`、`testing.md`、`orchestration.md`、`independent-review.md`、组件版本JSON和 `baseline-results.json`；最新状态另见 `evidence/github-app-live-verification.json`、`pdf-branch-publication-api.json`、`propr-native-daily-quality.json`、`n8n/quality-review.json`、`propr-policy4-validation.json`、`propr-policy4-runtime-status.json` 与 `propr-policy4-patch-validation.json`。App、候选发布、policy4测试及API/worker运行有证；当前main组合已有PR26和3/7/3证据；OAuth已验；单次日报质量与PR26门户/HTML下载/neutral Check已验。正式AI schedule已配置启用且daemon已运行，30天持续访问、真实自动Issue→PR、全事件咨询与自动head/base失效仍待验。

最新补充证据：`evidence/github-oauth-configuration.json`、`propr-oauth-native-daily.png`、`native-daily-attempt3-quality.json`、`daily-production-configuration.json`、`daily-production-provenance.json`、`mihomo-provided-config-validation.json`、`reporting-reviewed-deployment.json`、`pdf26-evidence-ui.json`、`pdf26-evidence-serving.json`、`pdf26-native-check-publication.json`。

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
