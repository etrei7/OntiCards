# GitHub App 接入

截至2026-10-22 18:57（北京时间），后台 App 已真实接通：App ID `5422414`，slug `onticards-maintainer-stepll2026`，installation ID `174029282`，账号 `stepll2026`，selected 仅 `stepll2026/OntiCards`。bot 为 `onticards-maintainer-stepll2026[bot]`（ID346235449）。安装编号不是 App ID。文档不含私钥、模型密钥或 token。

## 现有权限

|仓库权限|级别|用途|
|---|---|---|
|Contents|读写|受控修复分支与提交|
|Issues|读写|按授权规则评论和分类|
|Pull requests|读写|创建/更新修复 PR 与审查反馈|
|Checks|读写|发布绑定 head 的测试结果|
|Actions|只读|读取 CI 结果和产物|
|Metadata|只读|身份及仓库信息|

没有申请 Administration、Secrets、Workflows 写入、Actions 写入或组织权限。Webhook 关闭；事件入口复用 ProPR polling。仓库轮询目前暂停，不能因持久仓库配置 enabled 就声称正在接单。

## 凭据与验证

GitHub 当前菜单为开发者设置 → GitHub Apps → App 旁 Edit → Credentials → Key pairs → New key。[官方私钥说明](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps)。已有可用密钥无需重复生成，也不要擅自撤销其他密钥。

PEM 位于测试机 `/opt/onticards-maintenance/propr/secrets/github-app.pem`，目录0700、文件0600，只交给受信 API/daemon/worker。App ID 和 installation ID 在独立 `github.env` 中。私钥不进 Git、构建上下文、Agent、n8n、截图或日报。交付包 verifier 复用 PyGithub 2.10.0；真实验证已确认 App 身份、账号、精确单仓、六项权限集合，并用降为只读的短期令牌读取仓库。离线校验另有7测试/17场景。

真实写入包括测试 Issue #25、受控 PDF 分支及[草稿 PR #26](https://github.com/stepll2026/OntiCards/pull/26)。分支发布复用 Git Data API，逐个匹配原始 blob/tree/commit SHA 后才创建 ref，未更新 main，短期令牌在操作后撤销。PR26 的 head3105/basec8e 已独立完成 PDF3/API7/浏览器3验证；迁移5通过1跳过。它不代表后台原生 Issue→PR 链路成功：Issue25 在 clone/refresh 网络阶段失败，未运行编码 Agent。AI 触发标签已移除，失败记录保留。

## 管理网页登录

后台安装令牌与浏览器OAuth是不同流程。原生回调已保存为 `http://10.66.66.5:18123/api/auth/github/callback`，client secret已接入仅API读取的0600 `oauth.env`，不写本文或仓库。主流程完成GitHub授权往返，账号stepll2026已登录并查看受保护的第三次日报任务正文；证据 `evidence/github-oauth-configuration.json`（browser_round_trip_verified=true）与 `propr-oauth-native-daily.png`。早期保存超时/未接入是历史状态，已经解决。

policy4复用原生OAuth、Express session和Redis，仅对用户选择的精确RFC1918 HTTP origin opt-in；49认证测试和真实登录分别计证，没有开启demo/development/免认证。Dashboard Activity Overview观测temporarily unavailable；登录/日报可读不等于所有管理操作已通过。

PR26证据已追加到描述，并创建原生Check119778059245，conclusion为neutral。发布前后精确回读head3105/basec8e，main未变、没有ref writes/merge、token已撤销；详见 `evidence/pdf26-native-check-publication.json`。这是单次受信发布，尚无持续head/base变化失效监控，不能标成全部合并条件满足。

## 当前运行边界

API/worker/daemon 均运行 policy4；仓库接单配置disabled。AI 日报 schedule 已启用：首轮内容质量失败、第二轮 provider 请求超时，第三轮受控配置修正后在31.854秒完成且质量核对通过，run `2957780b-64f9-4a13-a21b-a03ba5d609dc`。输入14104、输出1650、缓存读取11264 tokens，USD未知；三轮原始证据全部保留，第三轮没有GitHub写入。正式日报定义revision10已接实时只读输入，原生cron对应北京时间09:05，nextRunAt=2026-10-23T01:05:00Z；原生UI暂停/恢复保存、daemon心跳、空队列及仍仅3条历史run已核对；尚无下一自然日定时执行结果。确定性事实日报的 systemd 00:00/09:00 timer 已启用。原生工具日志配置为30天，真实 Redis data/meta 两键刷新已验证，仍有64MiB容量截断边界。

早期订阅403保留为历史。用户新提供的配置已下载200，复用Mihomo原生file provider并把任务专用17891切到ONTICARDS-PROVIDED；共享selectors/DNS/rules保留。delay/API200已验，最新完整Git clone在600.098秒超时，未宣称稳定成功；详见evidence/mihomo-provided-config-validation.json。仍须完成自动咨询回复、事件续办/去重、防循环、跨轮次失败停止、fork路径和原生Issue→PR验收。

Contents 写权限本身没有单独的禁止合并开关；本实例在 ProPR 策略层关闭自动合并、显式 MCP 合并与回退合并，只允许受控 `codex/` 分支。最终合并由维护者操作，既有保护规则没有削弱。

原生Git缓存恢复已实测：复用已有浅mirror，通过原生ensureRepoCloned建立缓存并创建隔离worktree，再移除临时映射后真实origin fetch通过（9.994秒）。对象fsck、HEAD c8e及clean通过；浅缓存registry未登记、自动清理保留，不伪造marker，不等于公网完整clone稳定。原partial目录保留。证据 `evidence/native-git-bootstrap.json`。
