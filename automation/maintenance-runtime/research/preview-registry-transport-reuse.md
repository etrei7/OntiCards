# CI 镜像传输复用记录（2026-10-22）

固定 PR26/head 3105b7b6/base c8e3dfee 已由打包机原生 rootless Docker 构建。原生 SFTP 正向认证成功，但 4.9 GiB 归档在约十分钟只传 10.9 MiB，保留不完整文件与失败记录；不能把工作站中转作为常驻链。

复用两机原生 Skopeo 1.13.3、已有阿里云 ACR registry 和现有 OpenSSH ForceCommand。官方来源：[Skopeo copy](https://github.com/containers/skopeo/blob/v1.13.3/docs/skopeo-copy.1.md)、[containers/image transports](https://github.com/containers/image/blob/v5.29.2/docs/containers-transports.5.md)。Skopeo 原生支持 docker-archive ↔ docker registry、authfile、digestfile 和按 digest 拉取；不执行镜像，不需要 Docker socket，不新增镜像服务。

唯一必要适配：固定本仓库、PR/head/base/run ID，验证现有构建 manifest；打包机可信 publisher UID1003 将 UID1001 输出复制到自己 0700 目录的独占 0600 snapshot，拒绝最终路径 symlink，复制后校验完整 SHA256，才调用 Skopeo。仅发布 api/web 到固定专用 repo/tag，并回读精确 manifest digest。测试机可信 fetch UID1004 按精确 digest 下载到固定 inbox，UID1001 只加载并重新核对镜像 config/layers；数据库、浏览器等依赖复用已验证可信锁定镜像。

凭据边界：只复制既有 Docker config 中目标 registry 的一个 entry 到可信账号私有 authfile；不复制其他 registry、不放到 rootless UID1001、不挂载 PR 容器。现有凭据不是 repository 最小权限短期凭据；没有证据证明可直接签发更小 ACR scope，因此记录限制，不声称最小权限已达成。固定命令、单 registry/repo 与 UID 文件隔离限制这次调用范围。

故障状态持久化，不自动重试同 head/base；可信操作员需保留原 receipt/partial 后明确恢复。原有构建成功可幂等复用，不重建 PR。所有结果仍需真实测试机 API/Playwright 和模型链分别验证；发布成功不代表测试通过。

实测更新：15:29:40Z API/Web 已发布并按 digest 回读。5 机显式代理下载首层很慢；同一 manifest 直连 0.84 秒，代理 12.84 秒。15:35:08Z 终止精确 UID1004 Skopeo 进程，完整保存 failed receipt 和 partial inbox，再由操作员恢复一次直连下载；不改共享 Mihomo 或系统路由。原生 SFTP partial 也保留。25 项固定输入/归档边界/私有复制/短租约验证通过，不能替代业务测试。

模型阶段复用原有真实 `exercise-product-flow.py`、API7 和 Playwright3，用固定测试脚本只读挂载到既有可信浏览器镜像，无需新测试框架或重新构建镜像。新增 `test-model` 为显式独立阶段 receipt，固定相同 identity 和已下载 manifest；不会覆盖非模型阶段证据。NewAPI 原生同一短 token 仅 chat+embedding 两个已验证 alias、900 秒、原生 20000 测试预算、源 IP 10.66.66.5；只经 SSH stdin 传入，≤4KiB，控制器核 identity/expiry/alias/base URL。通过现成产品 model_config API 配置，不修改产品代码。租约最后撤销并读回；完整模型运行尚待实测，既有 rerank 多表场景限制仍保留。


## 2026-10-23 00:16 的原生读取配额缺口

首轮独立 n8n 执行 ID1 在匿名 GitHub PR GET 返回403（共享出口60/h配额耗尽），未消费CI receipt，未发行模型租约。已有18128实例已经实际验证原生JWT RS256→HTTP installation token→scope回读→DELETE撤销；直接复用这一子工作流模式，新增18132专属加密JWT credential和12节点只读子工作流，仅 pull_requests/metadata read、repositories=[OntiCards]。每个版本检查独立签发并撤销，避免构建/下载期间token过期；PR/SSH容器从不接收此token。凭据临时文件0600，CLI import后两端删除；子工作流禁用成功/失败正文保存。主workflow只接收脱敏 current/head/base/token_revoked 结果，在派发前、模型前、结果发布前再次检查；缺token、scope不符、撤销未知均fail closed。来源是本交付已有 build_repository_context.py/install_persistent_polling.py，未新增token broker。

非模型真实运行16:03—16:05Z：7 API + 2 Playwright均通过，6 PNG由Playwright原生成功附件html/data输出。首次收集门禁误查test-results，保留旧receipt后仅修正收集路径，不重复成功测试。最终证据包SHA256=37be0676b5ee68d1312b4289eb6d3c4443caa2aa48550be8616f4cf3a41063ca。截图包含登录、工作空间等页面，部分导航瞬间截图仍为loading状态；这只证明对应smoke断言，不当作完整业务数据已显示的证据。
