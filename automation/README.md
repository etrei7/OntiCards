# OntiCards 事实日报

复用 PyGithub、SQLite、systemd、flock 和 tmpfiles，为 `stepll2026/OntiCards` 补充北京时间自然日统计与文件恢复。具体复用缺口见 [复用矩阵](../docs/maintenance/reuse-matrix.md) 的 R01、R02、R03、G01、G02。此目录负责确定性统计；模型归纳、原生维护任务及其状态不由本采集器替代。

运行要求：Python 3.12+。生产依赖固定在 `requirements.txt`，实际测试机依赖快照在 `deploy/requirements.lock.txt`。以下命令从仓库根目录执行：

```sh
python3 -m venv automation/.venv
automation/.venv/bin/python -m pip install -r automation/requirements.txt
PYTHONPATH=automation automation/.venv/bin/python -m onticards.report report --state automation/state
```

公开仓库可匿名读取；如需要提高额度，只向此进程提供独立只读 `GITHUB_TOKEN`。不要提供 App 私钥或复用修复发布所用的写令牌。输出为 `state/reports/YYYY-MM-DD.md`、同名 JSON 和 SQLite 运行台账；首次没有日界快照时，净变化显示“基线建立中”。`snapshot` 采当前快照；`catch-up --lookback-days 7` 补最近缺失窗口，同时恢复数据库已知的更早未完成日报，均不晚于 `--day`，不会回填未知的更早历史或重采已完成窗口；`report --day YYYY-MM-DD` 更新同一逻辑日报。调用恢复选项 `--recover-interrupted` 时必须持有部署使用的排他 flock。

采集器在发出 HTTP 前用同一 reports 主键登记 pending 日期；入口超时或进程中断后，超过 lookback 的这些已知窗口仍可补跑。pending 没有报告 payload，不会被恢复为虚构日报；预登记不覆盖已有 complete 报告。PR commit status 直接查询记录的 head SHA，不依赖最多250条的 PR commits 列表末端；接口失败保持未获取和错误记录。

新采集的 AI 评论按已核实的 App bot ID `346235449` 且 `type=Bot` 识别，复用 GitHub 的评论作者字段；正文标记和登录名不作为身份凭据。JSON 保留作者、Issue/PR编号、评论时间和链接，Markdown提供逐条追溯。这里只统计 Issue/PR 讨论评论，不是 PR 行内 review comments 的完整清单；评论数量不代表执行成功。专用日报Issue仍按 `REPORT_ISSUES` 排除。旧payload保留原marker口径及原输出，不在修复文件时改写历史。

本次已验证 20 项统计/恢复用例，包括跨 lookback 的 partial/pending 恢复、API入口失败、实际终止独立子进程、complete文件不变、超过250提交的精确head状态、App身份/伪造标记/窗口排除/评论API失败及旧日报冻结输出。此前测试机上的重复触发、受控 timer、进程中断恢复、文件重建与 30 天样本清理证据另行保留。单元测试使用 pytest：

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

静态日报复用现有 Nginx 对 reports 子目录的只读 bind mount，worker 数字 UID 为101。tmpfiles 原生 `a+` 在目录模式调整后恢复 UID101 的读取/遍历及默认 ACL，新文件继承只读权限。数据库父目录仍0700，不授予 Nginx 父目录遍历或写权限。`a+`保留已有管理员ACL；当前主机既有UID1000条目不由本配置新增，干净安装只新增101。换主机必须核对实际Nginx UID和挂载，不能照抄宿主用户名。配置基于 [systemd v255 原生 ACL](https://github.com/systemd/systemd/blob/v255/man/tmpfiles.d.xml)，已在独立临时目录用真实systemd255重复创建验证，未把临时验证写入实际状态目录。

2026-10-22 18:39 实际部署已备份旧源码/配置并在现有flock下替换。重复应用tmpfiles后，日报/证据门户GET200、PUT403、私有数据库路径404；指定已有complete日期的原生catch-up运行exit0，日报唯一记录与文件哈希不变。timer、数据与凭据保留。完整部署证据在交付包 `evidence/reporting-reviewed-deployment.json`，备份位于测试机 `reporting-review-backups/20261022T103932Z`。

19:17，pending窗口与精确head修复部署至同一路径，现有Python3.12.3解释器运行全部15项测试通过，测试依赖只存独立验证目录，未写入生产venv；真实低权限catch-up保持完整日报payload/文件不变。证据 `evidence/reporting-pending-head-deployment.json`，备份 `reporting-review-backups/20261022T111700Z`。

19:27，AI评论身份扩展在同一flock下原子部署，服务器20/20测试通过，真实低权限catch-up exit0；10/21完整日报数据库payload和MD/JSON SHA均不变，源0640/root:985、ACL、tmpfiles、timer与门户权限保持。旧源码备份 `reporting-review-backups/20261022T112719Z`，新源SHA256 `fe83e8a8f1c746de305065f20d5ae9344cbab23b622fafb2a0db8624bbf0625b`。证据 `evidence/reporting-bot-identity-deployment.json`、`reporting-bot-identity-linux.xml`。这验证升级与历史兼容，不声称明日09:00的定时触发已发生。
