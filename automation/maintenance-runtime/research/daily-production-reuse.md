# 长期日报配置：实施前复用与缺口

2026-10-22。不得启用 schedule，不新增付费运行，历史验收原文不改。

| 所需能力 | 已有实现及选择 | 本次配置 / 具体缺口 |
|---|---|---|
| 真实触发时间和 Run ID | ProPR 0.9.0 固定 commit `42931b1502eb03ac299f14e306811736fab51eb4` 的 `src/jobs/agentRuns/reportPrompt.ts`：`taskSection` 使用 `run.createdAt` 输出 UTC ISO，Run ID 在同一行 | 直接使用原生 Task 字段；没有 `{{yesterday}}` 或日期模板运算，不引入模板框架 |
| 每日北京时间 09:05 | 原生 `agentDefinitionStore.ts` 固定 UTC；`5 1 * * *`；`src/agentRunScheduler.ts` + daemon sweep | 更新既有 definition，保持 scheduleEnabled=false；不增加另一个 timer 或常驻进程 |
| 上一上海自然日与输入校验 | Python 标准库 `datetime` / `zoneinfo`；已有 `automation/onticards/report.py::window` 用作独立测试对照 | 最小只读输入适配：从原生触发时间计算日期，验证对应 JSON 的 repo/day/window/status/errors 与 Markdown 同一次 run；只投影元数据/PR字段，避免读两份完整数据。这是原生自由文本报告缺少的确定性校验，不实现采集、模型调用、调度或循环 |
| 事实目录持续更新 | 现有 systemd bind mount `/var/lib/onticards-report/reports` → OpenCode `report-inputs`，ro | 实机两个路径 inode 相同。保留直接挂载，不复制每日固定文件 |
| 模型与超时 | 已验证 OpenCode 1.18.31 原生 `provider.options.timeout` 和 `model.options.enable_thinking` | 初装默认对齐 qwen3.8-max-0902 / 300000ms / false；总体600s、24步不变。本次只改本地初装模板，不远端全量运行 |
| 缺日报与错窗口 | 原生报告是自由文本，ProPR 不解析业务成功状态 | 输入适配返回 `WAITING_FOR_FACTS` 或 `INPUT_INVALID`，正式prompt要求只输出失败/等待声明，不能改用其他日期。这样的文字报告可能仍被底座标记 completed，不能宣称原生 failed 自动路由已存在 |

来源：固定上游 [reportPrompt.ts](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/src/jobs/agentRuns/reportPrompt.ts)、[agentRunScheduler.ts](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/src/agentRunScheduler.ts)、[Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html)。原生 scheduler 用最新到期 slot 的 idempotency key；宕机后不会为每个遗漏自然日都新建 AI 摘要。原生 Task 只包含实际 run.createdAt，未将幂等键内计划 slot 单独交给模型；本配置明确以触发时的上海日期减一天为目标。

来源澄清：`reporting-first-2026-10-21.*` 是首次 run `673621a8-9e01-4c3e-8d19-8ca5830d95d2`，06:57:13Z 完成；后来重采集的当前文件为 `8cd49268-5bd1-41c3-b63c-8a014d428539`，06:59:33Z。Agent 第三次验收读取后者。2026-10-22现场核对两个直接挂载路径 inode 都为11534663，内容一致；没有用固定验收拷贝代替现行目录。

## 已落地及无模型验证

既有 definition `e6a4ce1d-0068-4c3a-832c-ff911c791a1c` 已通过上游 `updateAgentDefinition` 更新到 revision 7：`modelName=opencode-bailian/qwen3.8-max-0902`、`scheduleCron=5 1 * * *`、`scheduleTimezone=UTC`、`scheduleEnabled=false`、`nextRunAt=null`、`includePreviousReports=false`。保持 `dry_run`、repositories/capabilities 为空。备份为测试机 data/daily-before-production-definition.json；没有触发新 AgentRun。

- 输入契约26项检查通过，独立对照现有采集器 `window()`，覆盖上海日界、09:05前后、跨月/年、闰日、缺失/错日/错仓库/错误状态/过期/未生成数据及JSON-MD不一致。证据：`evidence/daily-input-contract-validation.json`。
- 上游 `nextCronOccurrence` 和 `buildAgentReportPrompt` 的7项纯函数检查通过，确认UTC cron映射上海09:05及原生Task传入实际UTC createdAt。证据：`evidence/daily-native-schedule-validation.json`。
- 在已有官方Agent镜像中以1000:1000、禁网、drop-all、no-new-privileges，仅读only helper与真实事实目录：指定2026-10-22触发时间返回10月21日 `READY`、事实run `8cd49268…`；指定次日触发时间返回10月22日 `WAITING_FOR_FACTS`。没有挂模型配置、GitHub凭据、Docker socket，没有模型调用。证据：`daily-production-input-runtime-ready.json` / `daily-production-input-runtime-waiting.json`。这验证Python输入适配，不冒称正式prompt已经过第四次模型验收。
- 实机现有日报 timer active/enabled，下一次为2026-10-23 09:00 CST，`Persistent=true`；readonly bind mount enabled。daemon状态 exited，worker运行中。未启用长期schedule，未改首次/二次/三次的原始验收产物。

## 启用剩余条件与明确限制

1. 由主流程核对下一次09:00采集产出上一自然日完整JSON/MD；09:05前准备好时正式输入契约才能返回READY。测试机现有采集/挂载无需新增服务。
2. 原生日报scheduler运行在daemon中。启动daemon也会恢复其其他intake；应先用原生仓库设置明确Issue自动处理开关、核对队列与失败任务，再按维护者意图启动。不能把仅日报enable说成隔离启动。
3. 当前正式prompt与原生配置已就绪，但下一自然日首次真实scheduled run仍需核对日期、工具调用、输入来源与A—F质量。不得将本轮零模型测试等同于该项验收；不再付费重跑同窗口第四次。
4. 缺事实时有确定性的等待/失败输入与明确文字输出；上游自由文本AgentRun可能仍记completed，尚无独立的业务失败告警/自动补摘要路由。原生宕机恢复只排最新到期slot，不补每个遗漏AI摘要。确定性日报采集的补报与AI摘要补跑是不同能力。
5. 原生限制保持600秒、24步、单并发。供应商返回费用未知；这些是执行上限，不代表已实现货币预算或免费调用。

部署/回退操作与文件边界见 `deploy/propr/DAILY-PRODUCTION.md`。本次新增生产代码仅 `daily_input_contract.py`：选择指定自然日、校验文件配对、投影已有事实。全部调度、队列、模型工具执行、报告保存沿用上游实现。

后续启用准备（尚未执行）：复用 `configManager.saveMonitoredRepos` 和 `agentDefinitionStore.updateAgentDefinition`，仅把已有仓库enabled置false、已有日报scheduleEnabled置true。准备一个默认只读、须显式 `--apply` 的一次性配置脚本；它检查环境仓库覆盖、队列和恢复义务并保存回退快照，不含定时器/触发器/模型调用。原生 `agentRunTrigger.ts:266` 仅对非空repositories检查启用仓库，故现有空repositories日报不受仓库禁用影响。
