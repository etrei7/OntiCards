# ProPR 内网 HTTP 会话接入复用核对

2026-10-22。用户明确选择内网 `http://10.66.66.5:18123`；本次只读研究，不修改源码、镜像、OAuth设置或运行服务。目的为复用现成登录能力，定位必要的小适配，不切换NODE_ENV、不启用demo或免认证。

## 已有能力、版本与来源

ProPR源码 `42931b1502eb03ac299f14e306811736fab51eb4`（policy3基础）。package-lock实锁Express5.2.1、express-session1.18.2、connect-redis9.0.0、passport-github2 0.1.12。当前Express网页文档已标1.19.0，因此同时核对[express-session v1.18.2原文](https://github.com/expressjs/session/blob/v1.18.2/README.md)，不能把新版新增接口当成本镜像已有能力。

| 原生模块 | 已核实行为 | 此环境接入 |
|---|---|---|
| `packages/api/authRedirect.ts` | `AUTH_ALLOW_HTTP_REDIRECT=true`允许非loopback HTTP；仍检查允许hostname，但注释明确该主机所有端口都接受 | 复用开关；本次opt-in应额外限制精确origin，不能把同IP其他端口扩大为合法重定向 |
| `packages/api/corsValidation.ts` | `FRONTEND_URL`经canonical helper解析；对该origin精确比较，已支持HTTP；另有既存loopback/COOKIE_DOMAIN逻辑 | 设置明确FRONTEND_URL，不新增宽泛CORS、不设置COOKIE_DOMAIN |
| `packages/api/authSession.ts` | `shouldUseSecureSessionCookie`在production下只对canonical HTTP loopback返回false；未发现非loopback受限HTTP会话配置 | 唯一必要的会话配置缺口；AUTH_ALLOW_HTTP_REDIRECT并不能关闭Secure cookie |
| `packages/api/auth.ts` | 原生Redis session、HttpOnly、SameSite=Lax、30天maxAge，GitHub OAuth strategy使用state；现有会话/白名单完成流程 | 全部复用，不引入新认证或绕过 |
| `packages/api/requestRateLimits.ts` | `PROPR_TRUSTED_PROXY_PEERS`可限制即时反代peer；未配时trust proxy=false | 原Nginx→127.0.0.1 API可用明确loopback peers；不使用trust proxy=true或整个内网段 |
| `clearSessionCookie` | 与创建cookie共用`shouldUseSecureSessionCookie`，保留HttpOnly/Lax属性 | 必须共用新增opt-in判定，避免登录/注销属性不一致 |

[Express官方会话说明](https://expressjs.com/en/resources/middleware/session/)与锁定1.18.2文档说明：Secure cookie在HTTP下不能按正常会话往返；库已有`secure:false`和`secure:'auto'`配置。此处应复用静态false的严格opt-in，不全局切auto，因为目标只批准一个精确内网origin。只影响这个配置条件，不降低其他HTTPS/生产部署默认值。

[Express官方反代说明](https://expressjs.com/en/guide/behind-proxies/)支持按IP限定可信peer，并要求可信反代正确处理转发头。已有Nginx显式写`Host`、`X-Forwarded-Proto`、`X-Forwarded-For`，API仅loopback；配置可信peer不应依赖客户端自己提供的转发头决定是否降为不安全cookie。

## 建议的最小适配（尚未实施）

1. 新增独立明确opt-in：`AUTH_INSECURE_SESSION_ORIGIN=http://10.66.66.5:18123`。复用`canonicalProprHttpUrlOrigin(..., {allowInsecureHttp:true})`；要求输入本身是canonical origin（无用户名/密码、path/query/hash、空白/别名端口），HTTP、IPv4且位于RFC1918；本次只配置此精确值。
2. 只有`API_PUBLIC_URL`及`FRONTEND_URL`都与该origin完全一致，且`COOKIE_DOMAIN`未设置时，`shouldUseSecureSessionCookie`才返回false。未启用/不合法/不一致/公共IP/HTTPS/cookieDomain等情况保持原有安全默认。由可信服务环境配置，不能从Issue、repo文件或请求头更改。
3. 复用`AUTH_ALLOW_HTTP_REDIRECT=true`，同时在这个opt-in模式下把HTTP重定向收紧到该精确origin；保留路径跳转，但拒绝同host其他port、其他host、userinfo及非canonical输入。原生hostname白名单不能作为该精确边界的替代。
4. 不改GitHub OAuth/state、HttpOnly、SameSite=Lax、白名单、Redis store、过期时间、会话注销及原有CSRF检查；不改NODE_ENV=production，不启用demo。已有CSRF实现有路由范围：`createSessionCsrfProtection`主要保护扩展管理路径，另有MCP表单及OAuth state。不要泛称已验证整个REST的全局CSRF。
5. 使用原生`PROPR_TRUSTED_PROXY_PEERS=127.0.0.1,::1`等与实际反代peer相符的最窄设置，保持API loopback监听。HTTP cookie本身没有端口隔离属性；精确origin重定向/CORS并不使浏览器cookie获得端口隔离，报告应准确描述这点。

建议复用现有`sessionCookie.test.ts`、`githubAuthCallback.test.ts`、`oauthState.test.ts`、`extensionCsrfScope.test.ts`及CORS/重定向测试，补实际有价值的边界：opt-in缺失仍Secure；唯一正确组合不含Secure但仍HttpOnly/Lax；public IP、同IP错端口、FRONTEND/API不一致、COOKIE_DOMAIN、URL混淆全部拒绝降级；HTTP回调state错误仍拒绝；未登录仍401；适用CSRF路径仍403；注销cookie匹配。构建仅打包机，实际OAuth浏览器往返在10.66.66.5验证。

## 另一个已证实的配置优先级事实

`packages/core/src/daemon/configLoader.ts:208–215`中，在没有CONFIG_REPO且`GITHUB_REPOS_TO_MONITOR`非空时，直接返回环境变量repo列表；只有使用持久配置时才经`configManager.ts:178–181`过滤enabled。早期DB enabled=false不能证明daemon停止监控，日志也曾明确读取环境变量。主流程17:22已移除该覆盖并启用唯一持久repo；`evidence/issue25/task-progress.json`保存实际“Successfully loaded monitored repositories from persisted configuration”日志。此处只纠正文档，不新增配置加载器。
