# GitHub App 接入与权限

以下权限与policy13记录描述旧部署的实际基线。新目标采用仓库级持久AI自动合并设置，替代永久人工最终合并；当前新Gateway尚未上线。任何新权限必须先核已有安装与具体接口需要，不把本文权限表当授权扩大范围。OpenHands普通设置页已经存在，但读取接口未接入时显示“状态未知”，不代表GitHub端请求已取消。

2026-10-23：后台 App 与管理 UI OAuth 均已真实接通。App 5422414、installation 174029282、slug `onticards-maintainer-stepll2026`、bot ID 346235449；selected 仅 `stepll2026/OntiCards`。当前 policy13（964项回归通过）运行 API/worker/daemon，仓库监控已启用。日报独立 alias 只读事实，Schedule 为上海 09:05。详细版本见交付目录 `automation/maintenance-runtime/deploy/propr/manifest.json` 及 RUNBOOK；早期暂停快照不是当前状态。

|仓库权限|级别|用途|
|---|---|---|
|Contents|读写|可信宿主发布受控 codex 分支|
|Issues|读写|授权范围内分类与回复|
|Pull requests|读写|草稿 PR、反馈与审查|
|Checks|读写|版本绑定的窄范围验收及失效|
|Actions|只读|采集工作流记录|
|Metadata|只读|单仓范围与身份核对|

没有 Administration、Secrets、Workflows 写入、Actions 写入或组织权限。Webhook 关闭；ProPR 与 n8n 分工轮询：AI 标签编码/PR 反馈由 ProPR 负责，普通咨询由 n8n 负责。机器人评论不触发循环。子操作使用最小权限短 token，结束撤销；编码容器只读，无 App 私钥。

私钥位于测试机 `/opt/onticards-maintenance/propr/secrets/github-app.pem`，0600、受限目录。实际 github.env、oauth.env、模型 key 及数据库不进入交付包。已有 key 可用时不要重生成或撤销其他 key。[GitHub 私钥管理说明](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps)。

用户选择内网 HTTP，OAuth 回调精确为 `http://10.66.66.5:18123/api/auth/github/callback`。该 origin 复用原生 OAuth/Redis session 的受限 HTTP 适配，保留认证、HttpOnly、SameSite 检查，没有 demo 免认证。49 项认证测试与真实 Edge 登录分别留证。部署到其他域名时应配置相应可信 HTTPS 入口。

原生 Issue32→PR33 及同 PR 反馈更新已运行，PR26/30/33 均为 Draft；Checks 仅描述各自实际覆盖范围。五分钟 n8n Check watch 按 head/base 验证旧证据，真实 synthetic base 失配探针已变 action_required，真实 PR 未被修改。

Contents写权限本身不能限制合并。旧policy13仍拒绝自动合并、MCP合并、回退合并和main发布；迁移必须逐入口接入新的服务端设置和版本门禁，不能简单关掉全局策略。新模式OFF继续AI工作并撤销本系统未完成Auto-merge；ON仅允许受信入口在真实测试、独立审查和仓库规则满足后合并。编码或测试进程不得借其他凭据绕过该设置。已知模型错误、预算停止、索引partial和历史失败继续保留，不因API成功或Task completed而认定业务合格。

自动语义评审复用原生MCP review_pull_request。用户管理入口仍为HTTP；MCP仅在127.0.0.1:18135通过现有可信CA提供TLS，HTTP入口返回404。可信n8n通过专用受限OpenSSH固定命令调用宿主：读取已有active用户授权，签发仅read/review、仅OntiCards、5分钟的原生委托，操作后撤销并核验；不把用户令牌、DB密钥、PEM或Docker socket交给n8n/PR/Agent。受限命令仍属于可信root边界，不称无特权服务。

白名单实际仅stepll2026。普通对话将原生/review、/fix、/ultrafix命令归入context_only，避免重复消耗；命令文字本身不授予修复权限。源码封存时评审接线已自然干跑但未派发模型。正式启用须在最终PR30发布后记录当前所有开放PR的head/base基线；后续新版本才接单，启用回执随完整交付包提供，历史失败/unknown预算不清除。
