# GitHub App 接入

截至2026-10-22 18:15（北京时间），后台 App 已真实接通：App ID `5422414`，slug `onticards-maintainer-stepll2026`，installation ID `174029282`，账号 `stepll2026`，selected 仅 `stepll2026/OntiCards`。bot 为 `onticards-maintainer-stepll2026[bot]`（ID346235449）。安装编号不是 App ID。文档不含私钥、模型密钥或 token。

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

后台安装令牌不需要 OAuth client secret；浏览器登录是另一条原生认证流程。用户选择内网 HTTP，已授权把回调设为 `http://10.66.66.5:18123/api/auth/github/callback` 并生成一个 OAuth client secret，但网页保存时连接超时，保存结果未知，secret 尚未生成接入。恢复访问后应先读取设置核实，再完成一次保存和生成，不能把授权当作配置成功。

policy4 已运行于 API/worker，复用原生 OAuth、Express session 和 Redis，仅配置精确 RFC1918 origin 的 HTTP opt-in；49认证测试通过，但完整浏览器 OAuth 往返仍未验。没有开启 demo、development 或免认证模式。此配置仅用于用户选择的内部入口。

## 当前运行边界

API/worker 运行 policy4；daemon 停止。AI 日报 schedule 关闭：首轮内容质量失败、第二轮 provider 请求超时，第三轮受控配置修正后在31.854秒完成且质量核对通过，run `2957780b-64f9-4a13-a21b-a03ba5d609dc`。三轮原始证据全部保留，第三轮没有 GitHub 写入。确定性事实日报的 systemd 00:00/09:00 timer 已启用。原生工具日志配置为30天，真实 Redis data/meta 两键刷新已验证，仍有64MiB容量截断边界。

现有 Mihomo 任务 listener 17891 仍为 DIRECT，新旧订阅均返回403；GitHub API 可用于已验证操作，但完整 Git clone 和浏览器连接不稳定。未改变共享代理选路。网络恢复后仍须完成自动咨询回复、事件续办/去重、防循环、跨轮次失败停止、fork 路径和原生 Issue→PR 验收。

Contents 写权限本身没有单独的禁止合并开关；本实例在 ProPR 策略层关闭自动合并、显式 MCP 合并与回退合并，只允许受控 `codex/` 分支。最终合并由维护者操作，既有保护规则没有削弱。
