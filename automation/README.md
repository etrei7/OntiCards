# OntiCards 事实日报

复用 PyGithub、SQLite、systemd、flock 和 tmpfiles，为 `stepll2026/OntiCards` 补充北京时间自然日统计与文件恢复。具体复用缺口见 [复用矩阵](../docs/maintenance/reuse-matrix.md) 的 R01、R02、R03、G01、G02。此目录负责确定性统计；模型归纳、原生维护任务及其状态不由本采集器替代。

运行要求：Python 3.12+。生产依赖固定在 `requirements.txt`，实际测试机依赖快照在 `deploy/requirements.lock.txt`。以下命令从仓库根目录执行：

```sh
python3 -m venv automation/.venv
automation/.venv/bin/python -m pip install -r automation/requirements.txt
PYTHONPATH=automation automation/.venv/bin/python -m onticards.report report --state automation/state
```

公开仓库可匿名读取；如需要提高额度，只向此进程提供独立只读 `GITHUB_TOKEN`。不要提供 App 私钥或复用修复发布所用的写令牌。输出为 `state/reports/YYYY-MM-DD.md`、同名 JSON 和 SQLite 运行台账；首次没有日界快照时，净变化显示“基线建立中”。`snapshot` 采当前快照；`catch-up --lookback-days 7` 补缺失窗口；`report --day YYYY-MM-DD` 更新同一逻辑日报。调用恢复选项 `--recover-interrupted` 时必须持有部署使用的排他 flock。

本次已验证 10 项统计/恢复用例，以及测试机上的重复触发、受控 timer、进程中断恢复、文件重建与 30 天样本清理。单元测试使用 pytest：

```sh
automation/.venv/bin/python -m pip install pytest==9.1.1
PYTHONPATH=automation automation/.venv/bin/python -m pytest automation/tests -q
```

## 已部署实例

测试机 `10.66.66.5` 的固定目录为 `/opt/onticards-maintenance/reporting`，服务用户 `onticards-report`，状态目录 `/var/lib/onticards-report`。已启用的原生 timer：`onticards-snapshot.timer` 在北京时间 00:00 采样，`onticards-report.timer` 在 09:00 补报；均使用 Persistent。运行记录使用实际采集时间，不能用补采值伪造过去日界值。报告入口为内部 HTTP 服务的 `/onticards-reports/`。

`deploy/` 保存实际使用的 unit、timer、tmpfiles 和安装配置。安装脚本需要预先放置源码包 `/opt/onticards-maintenance/reporting-source.tar.gz`（包含本目录的 `onticards/` 和 `requirements.txt`）、本目录部署文件至 `reporting-deploy/`，以及受限 `proxy.env`。这是指定主机的部署配置，执行前核对目录和已存在服务。脚本不启用 timer；验证成功后使用 systemd 原生入口：

```sh
systemctl start onticards-collector@catch-up.service
systemctl enable --now onticards-snapshot.timer onticards-report.timer
systemctl list-timers 'onticards-*'
journalctl -u onticards-collector@catch-up.service
```

暂停定时采集用 `systemctl stop onticards-snapshot.timer onticards-report.timer`，恢复用 `systemctl start`。使用 `systemctl start onticards-collector@report.service` 手工重跑上一日报；不会创建第二个 repository/day 逻辑记录。

报告文件过期时间为生成后 30 天；修复文件不会刷新其保留期。SQLite 台账与报告文件具有不同保留边界。AI 模型费用、未经调用的接口、当前 PR 全部检查是否通过均不能从缺失数据推算；JSON 保留 API 错误，Markdown 不把未获取统计填成 0。
