# 日报 Checks 与原生任务事实适配

2026-10-23。真实第二次模型日报把 `commit_status_count=0` 错写为“0 checks”，且旧采集器固定文字“未执行本系统测试”无法区分未采集与未执行。已有 PR33 成功 Check、PR26 neutral Check 和 ProPR 修复任务，因此必须补足事实输入，不能仅让模型猜测或隐藏相关需求。

复用 [PyGithub 2.10.0 Commit.get_check_runs](https://pygithub.readthedocs.io/en/stable/github_objects/Commit.html)、[GitHub Checks REST](https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference)，继续按 PR 精确 head 获取分页数据；权限沿用已有 App checks:read。Commit status、Checks、Actions 和本地业务验收分别表示，不从空列表推导全项通过。

AI 处理事实复用 ProPR 0.9.0 已有 SQLite `tasks` / `task_history`，仅导出白名单元数据和管理入口链接，不导出 prompts、initial_job_data、config、日志正文或凭据。原生 HTTP Tasks 入口需要交互式会话；不为一次读取新建账号、认证或重复任务数据库。通过现有 systemd collector 的 ExecStartPre 运行受信只读导出，再由低权限采集器读取选定快照。复用 [systemd ExecStartPre](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#ExecStart=)，不添加第二个定时器。

必要新增范围：Checks 字段映射、固定列的原生任务快照及按自然日过滤、现有 Markdown/AI 输入显示。导出失败写明确错误，陈旧/缺失快照不当零记录；历史报告未带新字段时保持原渲染。验收包括状态与 Checks 分离、真实分页、读取失败、跨日任务、只导出目标仓库、密钥字段不进入快照，以及实际 GitHub Check/任务 ID 对照。
