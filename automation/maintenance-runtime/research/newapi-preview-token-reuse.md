# 测试 API 的短期模型凭据复用核实

2026-10-22。对应 AC06/09：不可信 PR 测试容器不能持有长期模型密钥，但自然语言查询验收需要真实模型。

已有：10.66.66.5 的 New API v1.0.0-rc.22 可通过原生管理 API 访问；19个已配置模型不含本任务指定的 qwen3.8-max-0902，未替换维护模型。只读结果在 evidence/newapi-existing-capabilities.json。项目 API 已支持 OpenAI 兼容地址和测试配置。

复用来源：QuantumNous/new-api，v1.0.0-rc.22，AGPL-3.0；原生 Token 的过期时间、额度、模型白名单、IP 白名单以及普通用户/分组隔离，不自建凭据代理或额度系统。

- https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/controller/token.go
- https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/model/token.go
- https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/middleware/auth.go
- https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/service/group.go
- https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.22/controller/channel.go
- https://docs.newapi.ai/en/docs/guide/feature-guide/user/token

已确认的边界：管理员所有的推理 token 可通过后缀指定渠道，故不能把管理员 token 给 PR 容器；需要专用普通用户的短期推理 token。专用 channel 必须只属于专用 group，该 group 不加入全站 UserUsableGroups 或 AutoGroups，避免其他用户消耗本任务的 DashScope key。后台账号认证与推理 token 是不同凭据。

拟接入：原生管理 API 配置专用普通测试账号/私有 group/唯一模型入口；每次受信测试流程创建有限额度、有限时长、限定模型和来源的推理 token，并在结束时禁用。长期 provider key 留在现有 New API 服务，后台用户凭据只留受信端。网络入口复用现有 nginx，仅代理精确 chat/completions 路径，关闭其他路径并设置限流/并发/请求大小；rootless 子网只开该确切端口。

新增代码仅是这些原生 API 的部署/取证适配及任务配置，必须保留 token_id/run_id、有效期及撤销结果；不包含通用 scheduler、token 服务或模型代理。尚未创建账号、channel、token，也未开放网络或调用模型。下一步先读取当前 group/ratio 的安全字段并验证不覆盖已有配置，再完成原生配置和拒绝测试。计量单位不能伪装成供应商实际费用。

22:09 CST 实施更新：已通过原生 API 创建 user2（普通role1）、专用group和channel3（disabled）。逐字段读回quota=100000、固定供应商URL、模型mapping、max_tokens=1024及enable_thinking=false。全局可用分组/auto分组未变。原生option API整体写map无CAS，本轮串行读回和私有备份不能称为原子更新。

8/8真实原生拒绝探针通过：普通账号不能管理渠道、错模型、错IP、渠道后缀绕过、停用渠道、撤销token、过期token、零额度token。测试token2/3/4全部禁用并读回，供应商调用0。尚未启用渠道或开放网络；这些拒绝检查不能当作成功推理。证据：newapi-preview-configuration.json、newapi-preview-token-denial.json。

22:21 CST：现有 nginx 已增加专用18134精确POST推理入口，覆盖来源地址、防止客户端伪造X-Forwarded-For；GET405、其他路径404、query400、无token401实测，旧管理入口仍200。渠道仍disabled，未调用供应商。`deploy/propr/nginx.conf`及`evidence/newapi-preview-route-deployment.json`可核对。

后续凭据传递复用可信n8n的Execute Command与已有OpenSSH stdin。新增`deploy/newapi-preview/lease.mjs`只把原生login/create/readback/disable连到现有CI run；普通账号留在可信凭据挂载，短token仅内存传给固定SSH命令。每run独占intent文件，900秒过期、20000测试额度、唯一模型和10.66.66.5来源限制；结果未知不重新签发。撤销读回及原生used_quota写入无密钥收据。该候选尚待真实rootless路线验证，不表示模型业务测试已经通过。

保留配置失败记录：首次创建普通账号因原生Password/DisplayName max20限制拒绝，确认用户名不存在后修正为20字符随机密码及短显示名，旧intent保留服务器0600文件；第二次发现原生UpdateUser忽略quota，读回0触发停止，随后使用官方ManageUser/add_quota/override API设置并读回100000。无重复账号、无通过数据库直接修改配额。该quota和alias ratio仅用于测试消费上限，供应商实际美元账单未知。


## 完整产品链补充：2026-10-22 23:18

既有产品 extract-schema/governance/query 需要真实 embedding；早期只允许 chat 的短租约不能覆盖这条目标。复用 New API v1.0.0-rc.22 原生 /v1/embeddings、普通用户模型白名单/配额/IP/到期能力，单独配置同组 embedding channel，避免 chat 参数覆盖影响向量请求；现有账号预算不重置。仅在现有 Nginx18134 增加精确 POST /v1/embeddings，禁止管理路由/查询参数，沿用地址/大小/并发/限速控制。

已核对项目 embedding_api.py 的 OpenAI 兼容格式和[阿里云官方 embedding 文档](https://www.alibabacloud.com/help/en/model-studio/embedding)、[qwen3.7-text-embedding-flash 模型页](https://help.aliyun.com/en/model-studio/qwen3-7-text-embedding-flash)。模型实际输出维数和 New API 透传能力仍须真实短租约验证；不写新模型代理。单表fixture原生跳过候选≤1的rerank，不等于多表rerank已覆盖；其nested/flat协议适配尚在核实。
