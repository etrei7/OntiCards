# 日报结果与原生任务状态

2026-10-22，检查了 ProPR 0.9.0 固定 commit 42931b1502eb03ac299f14e306811736fab51eb4 的 `processAgentRunJob`、`reportFromResult`、原生 Agent definition 模板和现有失败/重投状态机，并在线核对[上游实现](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/src/jobs/processAgentRunJob.ts)。

原生流程对成功返回的任意非空文本保存 report_ready，然后 dry_run 转 completed。现有日报输入 helper 已能拒绝缺数据和错误窗口，但 Agent 按提示输出“日报等待事实数据/输入校验失败”时，界面仍可能显示 completed。只改提示不能修改这个持久状态。

必要局部扩展：仅维护模式、且可信部署环境精确指定的正式日报 definition，识别已约定的失败输出；拒绝缺目标日期、run ID 或 A—F 的不完整报告。复用原生 failed 状态和 report 字段保留原输出，复用原生重投协调与 cleanup，不增加调度器、任务系统、采集器或模型调用。成功结构校验不表示事实/语义已经完全正确；真实日报仍有独立内容验收。

验证使用现有 processor 的状态机测试 harness：等待事实/输入无效/不完整报告落 failed 且保存报告，重投不重复模型，正常日报和其他 definition 行为保持。随后在 kol-stage2 编译并纳入 policy8；本文件不是部署成功证明。
