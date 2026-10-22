# 日报补采与静态报告 ACL 复用核查（2026-10-22，实施前）

## 第三次局部审查：AI 评论身份（19:24，实施前）

现有 G01 采集只按正文 `<!-- onticards-ai:` 计数，漏掉 ProPR 原生未带该标记的 Issue/PR 讨论评论，且普通用户可复制标记。复用既有 PyGithub 2.10.0 `Repository.get_issues_comments` 的分页及 `IssueComment.user`，不增加评论系统、HTTP 客户端或调度器。GitHub 官方 [仓库 Issue comments API](https://docs.github.com/en/rest/issues/comments#list-issue-comments-for-a-repository) 已返回 user.id/type/login、issue_url、created_at 与 html_url；`since` 按更新时间筛选，因此仍需以 created_at 做原有北京时间自然日左闭右开过滤。此接口涵盖 Issue 和 PR 的讨论评论，不代表 PR 行内 review comments 的完整数量。

固定使用本次已核实的 App bot ID `346235449` 且 `type=Bot` 识别本系统，login 仅展示，正文标记仅作为辅助数据。新 payload 保存身份判定来源、评论链接、时间、Issue/PR 编号和作者；评论数量不等于执行成功数量。将分页及可能触发补全请求的属性访问一并置于既有 safe 边界，失败为未获取及脱敏错误，不能误报为零。版本依据为 [PyGithub 2.10.0 IssueComment](https://pygithub.readthedocs.io/en/stable/github_objects/IssueComment.html) 及本地同版本源码。

兼容边界：仅带新 `ai_comment_identity` 的新 payload 使用新口径和评论链接。旧 payload 保留原有 marker 口径文字和输出字节；repair 不因软件升级重写旧日报，不把历史标记统计伪装为新身份口径。先验证无标记原生评论、伪造标记、其他 bot、专用日报排除、窗口边界、分页/属性 API 失败及冻结旧 Markdown 哈希，再部署至同一 flock 下；保留真实已完整日报内容和权限。

### 第三次修复与部署结果

旧实现新增5例中3失败、2兼容检查通过，原生无marker漏计、伪造marker误计、空正文异常和作者API失败未记未知均有失败证据；冻结旧renderer哈希在源码改动前取得。新实现本地20/20通过，`evidence/reporting-bot-identity-red.log`、`reporting-bot-identity-green.log/xml`、`reporting-bot-identity-validation.json` 保留过程。新增生产代码只在已有report.py，复用safe与PyGithub分页；无依赖变更。

19:27确认服务器仍为前一版源SHA `4337f2f44daaec0825fdaa7f38d8c2b9d58850fa5f1d1c59d840e0ce89f780a1`，在现有flock下备份 `/opt/onticards-maintenance/reporting-review-backups/20261022T112719Z` 后替换为 `fe83e8a8f1c746de305065f20d5ae9344cbab23b622fafb2a0db8624bbf0625b`。沿用生产Python3.12.3与前轮独立测试依赖，Linux20/20通过2.23秒，未向生产venv安装pytest。随后实际低权限catch-up exit0，原完整日报数据库payload及JSON SHA `a6bc9910d4f6c3ca3d48caacbfb789e98f78cbfae1cc7e203d61bf6679665eb5`、MD SHA `b6cb7065a6e66d302194b2a0382413efd5a13e4dfb46b47c46f5eacb7bc95027` 均保持；权限、两timer、tmpfiles及门户GET200/PUT403/DB404不变。证据 `evidence/reporting-bot-identity-deployment.json`、`reporting-bot-identity-linux.log/xml`。没有重采旧日或宣称未来定时触发已经成功。

审查基线为配置提交 `3b2443a`。复用现有 `automation/onticards/report.py`、SQLite reports 表、pytest9.1.1、已部署 systemd255.4 与 tmpfiles，不另建调度器或权限服务。本次属于 G02 已有持久恢复与报告交付的具体遗漏。

## 已确认缺口与最小改动

1. `report.py:320` 的 catch-up 只枚举最近7天。`evidence/reporting-review-stale-catchup.json` 证实已知2026-10-10 partial在最后7天均complete时永不重试，运行却complete。将当前 repository 的数据库已知未complete日期并入候选，限定不晚于requested day；继续使用现有collect/save_report/唯一键与排他flock。不追补未知的更早日期、不重采已complete窗口。先用现有main入口及真实SQLite建立跨lookback失败测试，再改最小候选集合。
2. 宿主只读getfacl核实 `/var/lib/onticards-report` 为0700，reports目录有UID101及既有UID1000的access/default只读ACL；报告文件两者只读。Nginx容器仅bind mount reports只读，worker UID101；API未挂该目录。交付tmpfiles的`d ...reports 0700`会重设mask而不包含恢复ACL的操作。使用原生`a+`声明UID101只读/目录遍历和default ACL，显式mask，恢复在`d`之后执行的ACL。只新增必要101条目；保留已有1000条目但不为新环境创建1000权限。状态父目录和SQLite仍0700，仅reports bind mount可读；不授予父目录遍历、不扩大挂载或写权限。

## 官方能力与版本

[systemd v255 tmpfiles.d 源文档](https://github.com/systemd/systemd/blob/v255/man/tmpfiles.d.xml)（LGPL-2.1-or-later）支持`a+`追加POSIX ACL、显式mask及default ACL；多种操作使用固定次序，目录创建/模式调整后再应用ACL。该能力始于v219，当前255已有，无需新依赖。[systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html) 说明StateDirectoryMode会调整指定的最内层状态目录；当前unit只指定父目录，因此保留其0700不影响reports默认ACL。

验证计划：在5机新建独立临时fixture，复用真实systemd-tmpfiles、getfacl、setpriv与已有UID进行冷创建、重复--create、default继承、只读/不可写及父目录隔离验证；不对实际报告目录执行试验。保留旧配置导致mask失效的失败结果。源码测试使用既有本地venv中的PyGithub/pytest，GitHub请求边界替身，不访问真实仓库。

当前文档是实施前依据；测试结果另见后续证据，不预先认定通过。

## 实施后验证

新增主入口测试在旧源码真实得到`collected=[]`、run complete，重现历史partial被遗漏；最小5行SQLite候选合并后旧10+新1共11/11通过。新例同时验证更早已知partial完成、future partial不动、7个complete窗口不重采、没有生成未知历史。证据：`evidence/reporting-stale-catchup-red.log`、`reporting-stale-catchup-green.log`、`reporting-recovery-final.xml`。

systemd255.4实际临时fixture `/tmp/onticards-report-acl-4c5yo_0a`：旧配置把named ACL mask清为---，101读取失败；新配置两次`--create`后101可读、不可写文件/不可新建文件，UMask0077写入的新文件继承只读ACL。现有1000条目保留；干净安装1000不能读且无其ACL。状态父目录0700，101无法列出。证据：`evidence/reporting-tmpfiles-acl-verification.json`。生产目录、service/timer均未修改。两份tmpfiles配置保持一致。

## 第二次独立审查：采集前失败与精确 PR head（本轮实施前依据）

已有 partial 恢复没有覆盖采集入口失败：`get_repo` TimeoutError 之后 runs 不含请求 day、reports 无该日记录，超过 lookback 后无法再补。实际 main() 无网络复现见 `evidence/reporting-review-infrastructure-gap.json`。复用现有 reports 的 `(repository,day)` 主键，在网络前确定日期并持久登记 pending；使用 SQLite 官方 [UPSERT / ON CONFLICT DO NOTHING](https://sqlite.org/lang_upsert.html) 保留原 complete/payload，repair 跳过空 payload。继续合并 pending/partial 与近期日期，不新增 scheduler/queue。

GitHub 官方 [List commits on a pull request](https://docs.github.com/en/rest/pulls/pulls#list-commits-on-a-pull-request) 明确最多返回250条；旧实现会把第250条 success 写在第251条实际 failure 的 head 上且无错误，复现见 `evidence/reporting-review-pr-head-status.json`。改用已有 [PyGithub 2.10 Repository.get_commit(sha)](https://pygithub.readthedocs.io/en/stable/github_objects/Repository.html#github.Repository.Repository.get_commit) 直接读取 pr.head.sha；失败沿用现有 safe 未知/错误处理。

先补回归红灯，再做最小修复：API入口失败、真实子进程终止后超lookback恢复、complete记录和文件不变、future不误补、未知更早历史不抓；精确head和查询403不冒充成功。源码范围为 report.py、tests、README；本轮不提交、不部署，不重复已核验的 systemd255 ACL/生产门户权限试验。

## 第二次审查的修复验证

新增4个实际case在旧实现全部失败：入口失败窗口未登记、独立子进程实际终止后窗口丢失、精确head未查询（成功和403两种结果）。`reporting-pending-head-red.log` 保存4 failed/11 deselected。局部修复后全部15项通过（0 skipped），日志与JUnit分别为 `evidence/reporting-pending-head-green.log`、`reporting-pending-head-green.xml`。

子进程试验在本地 Windows Python 环境执行，使用真正 `Popen.kill()`，不是只写一个 synthetic running 行；网络入口由替身阻塞，不接外部GitHub。恢复后旧run变interrupted，10/10窗口补成complete，而指定lookback之外未知日没有被补造。不能把这个结果称为新增Linux SIGKILL部署验收。本轮源码/README尚未commit或部署，原18:39部署仍是下面的历史阶段。

## 第二次修复的生产部署

2026-10-22 19:17，先确认线上旧源 SHA256 `0e903234d1ff08431490e789cb1d906cda7375cc2e42f218df5c6111b4942b98`，在现有collector.lock下备份至 `/opt/onticards-maintenance/reporting-review-backups/20261022T111700Z` 后原子替换。新源 `4337f2f44daaec0825fdaa7f38d8c2b9d58850fa5f1d1c59d840e0ce89f780a1`；mode0640/root:985、tmpfiles与ACL、两timer均保持。

现有生产venv解释器 Python3.12.3，pytest9.1.1及其测试依赖仅置于任务临时目录，未装入生产venv。线上新源码全部15项测试2.22秒通过，包含Linux真实终止子进程的pending恢复；状态全部在独立fixture。随后以实际低权限服务用户和现有环境执行只覆盖已完整日的真实catch-up，exit0；原日报唯一记录/payload/MD/JSON SHA均不变。门户GET200、PUT403、私有DB404。证据 `evidence/reporting-pending-head-deployment.json`、`reporting-pending-head-linux.log`、`reporting-pending-head-linux.xml`。未新建镜像、未修改GitHub或ProPR审查。

## 首次审阅批准后的部署（历史）

18:39 在已有collector.lock下备份并替换实际report.py与tmpfiles，连续应用配置两次；未改service/timer/凭据或其他ProPR配置。备份目录 `reporting-review-backups/20261022T103932Z`。原生catch-up指定已有complete日期，exit0且唯一日报record/payload/文件SHA不变。现有facts和PR26门户GET200、PUT403、私有DB404；父目录0700，timer仍active/enabled。完整证据 `evidence/reporting-reviewed-deployment.json`。本节是上述独立fixture之后的真实部署阶段，不覆盖之前失败证据。
