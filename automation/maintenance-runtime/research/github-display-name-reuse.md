# policy6 管理页显示名兼容：实施前复用记录

2026-10-22。主流程已真实观察 `/api/auth/user` 返回登录用户 stepll2026、admin及四项权限，但 displayName:null 导致现有 UI `proprApi.ts::isCurrentUserResponse` 拒绝整个用户对象，表现为 read-only/no repos。身份与权限已正确，不能通过扩大权限或要求用户改GitHub个人资料修复。

先核实官方：GitHub REST [Users文档](https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28) 与 [官方OpenAPI描述](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json)。2026-10-22实际下载后仅保存schema摘要和文档SHA256，`private-user`/`public-user` 的 `name` 均为 `string, nullable:true`，`login`为string。证据 `evidence/github-user-nullable-name-schema.json`，不依赖搜索摘要猜测。

现有ProPR42931b1 `packages/api/authBearer.ts:86` 已使用 `profile.name || profile.login`，`packages/api/auth.ts:118` OAuth入口却直接取 `profile.displayName`；`authorization.ts:135` 响应又直接透传旧session的空值。UI要求displayName string的校验保留。

采用现成fallback，最小只改上述两个现有函数：新OAuth用户缺显示名时回退username；`authenticatedUserResponse`对既有session的null/空displayName回退login，不要求重新登录，不改session权限、role、permissions、authorizationSource、令牌或授权解析。空字符串与null同样回退，正常姓名保持原样；不新增认证层/接口/schema宽松分支。

验证复用既有 `githubAuthCallback.test.ts` 的真实Passport策略、OAuth state、session序列化和HTTP `/api/auth/user`，仅stub外部GitHub transport；再以 `instanceAuthorization.test.ts` 覆盖旧session输出投影、admin/member权限不变和无凭据泄露。先跑null回归红例，再修两行、跑相关认证/授权测试。此记录是policy6候选，未构建或部署。

## 隔离验证结果

2026-10-22在kol-stage2复用policy5测试镜像，禁网、仅只读挂载4个变更文件。新增5个实质用例先红4失败/1通过，原因均为null/空串未回退；两行修复后两个完整原生测试文件34/34，另外6个认证/会话/重定向/权限回归文件44/44，合计78独立用例全部通过、0跳过。`npm run build`和显式`npx tsc --noEmit`通过。旧session同cookie访问、无二次token交换，admin/member权限/来源/身份完全不变；未放松UI schema、未添加权限、未暴露OAuth凭据。

精确文件SHA、计数和日志见 `evidence/policy6-displayname-validation.json`。这只是policy6候选，未构建镜像、未部署，也未将隔离测试计作真实浏览器修复通过。
