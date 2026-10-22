# OntiCards 维护系统运行说明

本说明对应2026-10-23的policy13测试部署。API、worker、daemon运行于10.66.66.5，镜像只在kol-stage2构建。单仓库stepll2026/OntiCards已启用监控，修复与证据通过草稿PR交付，最终合并由维护者操作。各验收项的通过范围和剩余问题见[验收审计](../../research/acceptance-gap-audit.md)，运行版本见[manifest](manifest.json)。早期运行说明原文保存在[evidence历史目录](../../evidence/pre-policy11-document-history/)，不要将其暂停状态和旧镜像当成当前配置。

## 使用入口

- [管理界面](http://10.66.66.5:18123/)：使用已配置的GitHub OAuth登录；查看Tasks、Agent reports、Repository和Schedule。
- [事实日报](http://10.66.66.5:18123/onticards-reports/)：上一上海自然日的JSON与中文Markdown，含源Issue/PR、Checks和原生任务链接。
- [PR33并发导出证据](http://10.66.66.5:18123/onticards-reports/acceptance/pr33-fdd3/)：精确head/base、测试、截图与下载包；该结果只证明并发转换修复。
- [PR26产品预览](http://10.66.66.5:18111)：独立测试数据；手动验收与持续CI分别记录。
- [配置PR30](https://github.com/stepll2026/OntiCards/pull/30)、[版式修复PR26](https://github.com/stepll2026/OntiCards/pull/26)、[原生自动修复PR33](https://github.com/stepll2026/OntiCards/pull/33)均为草稿，不自动批准或合并。

## 复用组件与版本

ProPR0.9.0固定上游commit42931b1502eb03ac299f14e306811736fab51eb4，OpenCode1.18.31负责模型工具执行，原生队列、任务、PR审查和修复流程继续使用。n8n2.42.7承担普通咨询和持续CI，systemd负责日界快照、确定性事实采集、锁和30天清理。GitHub App、Checks、Git Data及PR界面承担身份、版本与审核，不另建认证/合并平台。

当前app镜像为`registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy13@sha256:3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879`。完整补丁[propr-maintenance-policy13.patch](../propr-maintenance-policy13.patch)只应用到固定上游一次；SHA256为91c2d151fd95ff6fcd634fc73d553a6fcc84674f481b3a7ce7b48eb11ea0273b，得到tree 0af2178f1461819a893d6705a0e23dcad6330595。94文件含54生产文件和40测试/fixture；逐组原因、现有扩展点和升级方法见[补丁映射](../../research/propr-patch-map.md)。不要叠加历史全量补丁。

kol-stage2编译通过，679项既有分组、20项原生只读/版本/权限边界和265项相关审查/恢复/取消/MCP回归共964通过、0跳过。此数不代表OntiCards全业务通过。[部署回执](../../evidence/propr-policy13-deployment.json)核对三服务镜像、部署前后空队列和健康状态；5机没有构建镜像。

API18122、静态UI18125、Redis18124仅监听loopback；Nginx18123同源代理。Compose文件为[compose.yaml](compose.yaml)。模型alias为onticards-qwen，复用OpenAI-compatible适配器接百炼qwen3.8-max-0902。修复每次24步、每次execute/analyze600秒、并发1、最多3轮；多个阶段累计可超过600秒。原生provider replacement为0。实际tokens有记录，供应商USD费用未知，不能把未知写0。

## 身份和隔离

专用GitHub App5422414、installation174029282仅安装OntiCards。宿主持有私钥，受控写操作由可信发布端完成；编码Agent使用降权只读token，无App PEM、宿主Docker socket或生产数据库。Agent容器UID1000、4GiB/2CPU、network none；主管服务仍是受信root进程，并非VM隔离。

用户选择内网HTTP。只有精确origin`http://10.66.66.5:18123`启用原生session的内部HTTP适配；OAuth、HttpOnly、SameSite及认证检查保留，未启demo/development免认证。凭据在服务器secrets受限文件，交付包不含.env/PEM/数据库。新增凭据应直接填服务器文件，不能写进Issue或PR。

不可信产品测试使用两机UID1001 rootless Docker、强制命令与SFTP边界，构建在kol-stage2，运行在5机。预览模型使用NewAPI短时、IP/模型/额度受限token；不向PR容器提供长期供应商key。具体负向测试及限额见持续CI运行说明，不能将rootless称作VM。Mihomo复用已有服务及任务专用listener17891；订阅凭据不进入公开文件。缓存后的原生fetch已实际验证，历史无缓存clone失败仍保留。

## 日报、知识与普通讨论

systemd在上海00:00采Star/Fork快照，09:00产生上一自然日事实报告；ProPR原生Schedule在09:05归纳，配置详见[DAILY-PRODUCTION.md](DAILY-PRODUCTION.md)。完整state=all分页列表同时计算窗口变化和当前待办，与仓库开放总数交叉核对。Commit statuses和Check runs分别采集。原生任务仅导出安全列，再由低权限采集器读快照；不导出提示、凭据或原始任务payload。Linux37项测试通过。首次缺日界基线显示未知，不补造历史Star变化。

知识主路径为版本化Agent规则、仓库事实文档、精确commit的原生Git与n8n不可变blob读取；主分支变化必须解析新commit和tree后刷新受影响blob。全仓语义摘要为可选加速层：本次60个文件摘要、0目录摘要，预算失败后已关闭summary并停止indexing worker，不能称完整索引。policy11将旧自动重试在模型前拒绝，真实恢复记录20条LLM日志前后不增、旧job为failed，见[indexing-settle-after.json](../../evidence/indexing-settle-after.json)。不得通过清空队列或预算重新开始掩盖失败。

普通讨论使用已有n8n五分钟轮询、HTTP、模型、条件和Data Table。AI标签修复交ProPR，普通人类讨论交n8n，机器人输入不互相触发。每线程最多3次回复/6次模型调用，独立复核通过且当前源版本、正文、标签均未变化才发布；POST未知仅GET确认。Issue31已达到停止条件并转人工，不因新部署重置预算。当前自动回复事实以[n8n运行说明](../n8n/RUNBOOK-current.md)和真实回执为准。

普通 AI 标签首次分发先创建真实原生 Task 并读回 SQLite task/pending；无法持久化就不入队。父分发失败或终态写入未知时，后续 poll、改模型/base、队列清理都不恢复预算；认证 Follow Up 仍沿原生一次性请求/accepted tombstone。首投递证据不参加普通存储清理，不能通过删Task/数据库重置规避。初次分发 completed 只表示 child 已入队，不代表代码修复成功。详见[边界复用与红绿](../../research/pure-label-admission-reuse.md)。

## PR证据及已知失败

Issue32通过原生任务生成PR33，后续反馈仍更新同一PR。最终head fdd3f291e8d4a51c31610f13d87670ab3288a6e9/base c8e3dfee68d398a37842fc332f73af40a56f02a7，实际LibreOffice测试9/9、竞态10/10、并发真实PDF2/2；最终Check仅覆盖进程profile隔离。PR26 head3105…是另一个版式范围，不能复用PR33结果证明其并发行为。前端lint/tsc基线失败和缺three_way_check导致的迁移跳过分别保留。

真实持续CI r3的提取、问数聚合值250、治理和四格式导出及API7/7通过，随后r4在原账户剩余额度内完成API7/7、浏览器3/3、0跳过；r2限流和r3配额失败保留，最新结果见PR26 rootless门户与Check119988255661。SQL R18三次不安全候选被独立审查拒绝，尚未修复。原生PR26模型审查曾有事实错误，纠正评论及无效输出失败记录均保留。任务状态completed不等于内容质量或业务验收成功。

## 暂停、恢复和升级

在`/opt/onticards-maintenance/propr`查看`docker compose ps`。停止新调度用`docker compose stop daemon`，停止消费用`docker compose stop worker`；停止daemon不会取消已运行任务。仅暂停日报优先在UI该Agent definition将Schedule设Off并Save；恢复UTC cron `5 1 * * *`并核对下一次时间。仓库Monitor与日报Schedule独立，当前Monitor已启用。不要再运行历史全量init或一次性enable脚本。

恢复前检查任务、队列、镜像和单仓范围，保留SQLite/Redis及失败证据，不用`down -v`或reset。一般咨询的启停/未知发布恢复使用其现有RUNBOOK；不要手工把posting_unknown改回可发布。索引当前应保持关闭，未来显式恢复需新预算、固定main、原生取消状态清理与新job，不得复活旧attempts。

升级在kol-stage2对新上游逐项检查补丁是否仍必要，运行受影响测试，再构建固定digest；5机仅pull、核对、按空队列窗口切换。回退须考虑HTTP、状态和日志TTL兼容，不把整库历史备份直接覆盖现状。

日志复用Redis Lua/AOF，2592000秒为最后成功写入后的空闲TTL，64MiB上限会裁剪早期输出。30天TTL刷新已用真实Redis验证，但尚未经过30天自然运行。公开产物使用白名单和到期时间，不公开原始trace/HAR、数据库、凭据或完整Agent运行文本。

ProPR为Apache-2.0，OpenCode为MIT；n8n为Sustainable Use License，运行Redis7.4.10为RSALv2/SSPLv1，不能统称全部为OSI开源。原始许可和声明保留。完整候选来源与新增适配依据见[复用矩阵](../../research/reuse-matrix.md)。

10/22最终原生AI日报仍有两处语义错误，已明确保留quality=false；交付的显式复核修正版10/10通过。未来日报用独立onticards-daily-qwen alias、revision13及空全局instructions，配置和事实读取已无模型验证；未冒称新alias模型验收通过。

补充真实本地 Git/fork 验证50/50通过，但其中语义负例明确证明 clean merge 后仍可出现运行失败；它不是语义正确证明。文本冲突回滚转人工，语义与业务继续由精确版本测试/人工审查负责，见[边界](../../research/conflict-fork-validation-boundaries.md)。OpenHands Canvas候选已可逆停止，数据保留；当前主链路只有ProPR/OpenCode。

## 自动 CI 与语义审查的当前接线

完整 intake 已自然派发到CI，批次余额只观察一次、旧成功/人工/预算不足保持sticky；剩余15445低于45000，0新租约/供应商请求，原429未知证据不抹去。语义review是另一个原生子workflow：六PR自然只读握手已验，单仓read/review、loopback TLS和固定受限SSH，模型调用为0。policy13三服务已部署，其原生lease内只读恢复、可信owner无标签review和实际head/base发布门禁已通过fixture。当前host policy=false、child dry_run；最终PR30发布后才对完整当前snapshot登记baseline再启未来tuple，不回放旧PR。实际是否启用以交付旁的mcp-review-activation.json为准，不以posted当审查完成。安装/回滚与严格边界见[CI接入说明](../n8n-preview-ci/README.md#自动语义审查接线)。

当前timer实测：onticards-snapshot.timer下一次2026-10-24 00:00上海，onticards-report.timer下一次2026-10-23 09:00；原生AI09:05保持。未来结果不提前验收。
