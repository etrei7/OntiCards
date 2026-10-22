# 原生日报生产配置与事实口径

2026-10-23：ProPR policy12的API/worker/daemon已运行；原生definition `e6a4ce1d-0068-4c3a-832c-ff911c791a1c`为revision13、scheduleEnabled=true、UTC cron `5 1 * * *`（上海09:05）。dry_run、repositories/capabilities为空、includePreviousReports=false。它只产出报告，不能触发仓库写入。单仓Monitor独立启用，不能沿用历史“仓库intake disabled”的描述。

## 调度与输入

现成systemd日界00:00快照、09:00事实采集、Persistent/锁/30天清理保持；ProPR09:05做AI归纳。真实10/23日界快照已产生，首次缺10/22起点，所以10/22Star净变化未知。下一日界建立后才能计算下一窗口净变化。定时AI摘要的未来09:05自然运行仍待观察，不把手动验收写成已发生的定时运行。

事实源`/var/lib/onticards-report/reports`通过原生systemd只读bind映射到`/opt/onticards-maintenance/propr/opencode/report-inputs`，Agent内为`/home/node/.config/opencode/report-inputs`。helper按Task.createdAt计算上一上海自然日，核对JSON/MD日期、窗口、run_id、生成时间、过期时间、complete/errors；缺数据明确等待，禁止换成latest或旧日报。helper本身在上游可写配置目录，因此事实权限边界依赖独立只读bind，不能只凭helper0444声称隔离。

`daily_input_contract.py`只进行选定文件读取及结构化投影，不做网络、调度或模型调用。当前28项输入测试通过；沿用7项原生cron/Task检查。prompt由原生get/update服务保存，revision12只变更事实解释，不改变Schedule、授权和模型。不要重新执行全量`init_runtime.py`或历史启用脚本。

## 采集和质量

10/22最新事实run `5da38704-a3ef-49b3-9c18-2bf3a88d28b1`为complete、errors=[]：当前开放12项（6 Issue/6 PR），窗口Issue变化4/PR变化5/关闭事件1。当前待办和统计窗口分列，不混算。原生任务历史安全快照覆盖13项；每个PR分别附commit statuses和Check runs，0 commit status不表示0 Checks。PR33的成功Check只覆盖并发PDF范围，PR26的失效探针不作业务验收。

采集器复用PyGithub完整分页，state=all列表一次获取后区分窗口变化与当前开放，并与仓库元数据开放总数核对。缺失、接口失败或不一致记partial/unknown，不能填0。原生任务通过systemd ExecStartPre读取SQLite安全列，独占随机临时文件及原子替换导出；低权限采集器只读取JSON，不获得ProPR数据库权限。Linux37/37、0跳过；Windows36通过/1跳过是其独立平台结果。

10/21第三次手动摘要run2957780b…通过独立质量检查，前两次错误和超时保留。10/22第一次5ea7dc61…因不完整源数据及历史环境污染失败；第二次c7b531ca…虽列全6 Issue/6 PR，仍把commit statuses误写成Checks，所以quality=false。源数据和prompt修正后最终第三次手动run为`f879dedc-7a00-464f-8e94-6b0b7d234353`，独立复核仍未通过：4个成功空Checks被写成未知，并引入历史SQL待办。原文保留，显式复核修正版10/10通过，不能称原生质量通过。同一事实日仍是一个逻辑日报；补采更新同一日期文件，历史代次作为验收证据冻结保存。

## 暂停、恢复、追查

UI的Agent definition Schedule设Off并Save暂停；恢复填UTC cron `5 1 * * *`并Save，核对nextRunAt与pendingScheduleSlot。该操作已真实验过。daemon调度、worker消费；停止daemon不取消进行中的worker。原生只补最新到期slot，不能承诺宕机期间每一天AI摘要都自动补齐；确定性事实采集的补采与AI摘要调度分别验收。

报告完成后核对A—F与结构化事实，特别是时间窗口、未知基线、PR/Issue区分、Checks范围和AI任务状态。保留原文、模型用量和错误；供应商USD金额未知。不要通过同日无限重跑获得绿结果。当前每日手动验收最多三次，原生定时任务继续按正常窗口运行。

证据：[最新事实与历史代次](../../evidence/daily-2026-10-22/)、[输入部署](../../evidence/daily-native-facts-20261023/deployment.json)、[采集器部署](../../evidence/report-collector-source-fix/deployment.json)。报告读取入口为[事实日报](http://10.66.66.5:18123/onticards-reports/)，原生AI报告从管理UI对应Task打开。

当前revision13仅将原生agentAlias改为onticards-daily-qwen，独立最小config的instructions=[]。同镜像真实debug config及只读helper READY已无模型验证，native agents_update有3个subscriber；编码alias、prompt、Schedule及模型不变。新alias未来模型质量尚未验，不做第四次同日验收。见daily-isolated-alias.json与reviewed/independent-quality-review.json。
