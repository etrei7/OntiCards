# 固定版本的原生 n8n / OpenSSH / Rootless Docker 验证接入

2026-10-23 03:19 当前事实：完整仓库采集已通过既有五分钟 Schedule 接入18132原生CI准入。03:11自然周期只有1个 receiver、6个PR子准入；PR26保留旧成功，PR28/27/22保持人工范围，PR30/33保持预算不足。该周期没有 CI main、SSH、模型、令牌mint或重复余额登录；这证明接线及持久门禁，不表示新PR业务测试已通过。

原02:37/02:38两条 `budget_unverifiable` 的直接服务日志为登录HTTP429，历史detail保留。经一次明确批准的只读运行状态核对，原生余额15445小于45000，两条记录追加观察并记 `budget_exhausted`，未重置余额或重投。现有原生节点已调整为完整可信批次最多一次余额观察，绑定watermark、时间≤300秒；已消费/人工/dry-run批次跳过登录，子准入不登录，真正发lease前仍复用原fresh额度检查。52表达式、20原生fixture和7自然周期断言通过，见 `research/ci-batch-budget-reuse.md` 与 `evidence/rootless-runtime/batch-budget-*.json`。

PR26固定head3105/basec8e已由原生n8n执行70完成真实rootless业务验收：API7/7、Playwright3/3、9PNG、实际schema/card/query250/基础治理/四格式导出。只kol构建，精确registry digest到5机测试；37文件只读门户及Check119988255661已发布并登记5min失效watch。r2网关429/r3预扣不足保留；r4使用40406原生单位/token12撤销，账户总100k未重置，余额15445，USD未知。fresh安装/真实host reboot、磁盘硬配额未验；同head/base重跑仍需人工审核归档，不具备产品化恢复按钮。最终合并人工。

01:50历史状态：当时“普通采集的新PR自动派发尚未接通”和元数据匿名限额问题属于接入前记录，现以上述03:11完整自然周期及实际App门禁为准；不将历史成功当作未来版本或完整额度下的新运行。

## 复用边界与新增原因

| 需求 | 复用能力 | 必要适配 |
|---|---|---|
| 既有PR触发 | 已有n8n采集；原生Webhook/子workflow/DataTable | 接收repo固定、PR/head/base固定输入；无需新scheduler/runner |
| 安全SSH | 镜像已有OpenSSH/SFTP；原生Execute Command | 原SSH node缺hostkey校验，固定命令入口调用OpenSSH pinned known_hosts；不复制SSH客户端 |
| 构建 | Git fetch/checkout/fsck、Docker BuildKit | 拒fork/非codex/新head或base；只kol的专用rootless daemon |
| 传产物 | Docker save/load + Skopeo1.13.3 + 既有ACR；小证据仍原生SFTP | 可信publisher私有snapshot后hash、固定repository/tag、精确digest回读/拉取；测试机不build；两个可信账号持单registry auth entry，UID1001不可读；现凭据不是repo最小权限 |
| 测试 | 原pytest7、原Playwright1.64.1三项、官方浏览器镜像/seccomp、现有Compose服务参数 | root控制Compose，无PR脚本宿主执行，无长期模型/GitHub/SSH秘密；非模型与显式test-model分别留receipt，后者复用真实模型产品流程及原model_config API |
| 并发/状态 | n8n单并发/DataTable、flock、确定性目录 | 相同head/base已有running/failed/complete receipt均不静默重跑；没有新增任务队列 |
| 超时/清理 | Linux进程组、native user systemd、Compose down | 终止客户端整个进程组；构建失败重启仅专用daemon，测试失败清理仅对应project并读回 |

`controller.py`、`dispatch.mjs` 是固定能力间的边界适配。测试脚本从已实跑的部署材料复用；`test_entry.py`复用原始账号轮换API，增加严格报告数量/退出码校验。它们均放在root管理目录，不能由PR改写。

## 自动语义审查接线

2026-10-23 03:50 状态：同一完整 intake 已分支到原生 `onticardsReviewAdmissionV1`，与 CI 的运行范围、预算和结果分开。自然 poll1782→handoff1808→receiver425→review432–437 对六个当前 PR 完成 HTTPS/MCP 原生 read-only 验证：真实 owner/单仓/read+review、显式维护模型 alias、tools/list 与 finally 撤销均通过；0 `tools/call`、0模型、0GitHub写入。policy13三服务已部署，964/964和13后TLS/SSH12项通过。当前 child 为 dry_run，host policy.enabled=false；**不是六次代码语义审查完成**。原始19:21回执保留，后补整数执行ID元数据见 `mcp-review-natural-intake-metadata-correction.json`，不把原生软删除行的 running 状态当仍在运行。

新部署按下列顺序；这是复用现有 ProPR、n8n、OpenSSH 的固定接线，没有新授权代理、Agent 或队列。

1. 先依 ProPR `DEPLOY-CURRENT.md` 部署独立验证的 immutable policy image。自动模式必须 API、worker、daemon 三个 running image 全部通过 `activate_review_admission.py` 的精确版本 allowlist；policy13 worker 的只读恢复、无 AI 标签可信owner和实际收集head/base门禁已有20项新原生fixture与265项相关回归；旧policy12探针另保留，不反写成13验证。
2. 受信宿主 `/opt/onticards-maintenance/propr/review-stage` 放入 `deploy/propr/review-service` 中 `mcp_review.mjs`、`receipt.mjs`、`ssh_gate.py`、`configure_native.mjs`、`probe_service.py` 及 `deploy/propr/mcp-tls.conf`、`mcp.env.template`。安装器 `review-service/install_service.py` 读取并备份当前 Compose/Nginx，再最小追加 API helper/CA 只读挂载和 loopback TLS；不能用旧整份配置覆盖已有证据门户。它生成仅服务器内的 key、固定 hostpin 和原生 MCP 设置，保留 policy=false。证书复用当前服务器已验证的 local CA/SAN127.0.0.1，其他环境先准备正确证书，不跳过 TLS。原 HTTP `/api/mcp` 和子路径显式404，用户 HTTP UI 保持可用。
3. 专用 root key 仅允许 `from=127.0.0.1`，restrict/no-user-rc/禁转发/PTY，固定 `env -i` Python wrapper；不解释 SSH_ORIGINAL_COMMAND。n8n没有 ProPR DB、PEM、root Docker socket或可选宿主命令。输入≤4KiB且5秒读入上限；grant只在宿主内存中，5分钟、单仓 read/review，finally撤销。wrapper 210/225秒边界与 lost-response 的 unknown 状态必须保留。
4. 将 `dispatch_review.mjs`、`review-admission.workflow.json`、`read_review_baseline.py`、`activate_review_admission.py` 复制到现有可信 `/opt/onticards-maintenance/preview-ci/bundle`。先运行 `install_review_probe.py` 的单次固定只读原生探针，再运行 `connect_review_intake.py` 向现有 receiver 追加一个 Execute Workflow 分支；它断言批次预算节点存在且尚未接线，不覆盖已部署 budget 修复。所有模板默认 inactive/dry_run，输入无法选择真实 review。
5. `probe_review_baseline.py` 在独立命名 DataTable、synthetic PR 上实测六项首次 baseline+重复不派发12/12；SSH节点替换为必失败的拒绝哨兵，0SSH/模型。正式 baseline 必须等待最后配置 PR30 commit 发布并进入现成完整采集水位后，执行 `activate_review_admission.py --config-head <最终40位SHA>` 先只读准备，再由受信维护者同参数 `--apply`。它停止 receiver、再次确认有效原生执行为0，固定 mode=baseline 登记所有当前版本且不调用 SSH，再切 review 和 host policy，读回两处状态。失败回滚保持 disabled/dry_run，保留旧 baseline/预算，安全回执始终落盘且退出2。不得靠删除旧行“恢复”。

正式启用后，只接目标仓库 main 上 open PR 的新 `(repo,PR,head,base)`；普通分支/fork允许原生只读审查，取不到源码转人工。原生维护模式 review worker 仍验证真实可信 owner 与 assignment，不加 AI 编码标签，不给 execute/fix/merge scope。先登记永久 admission，任何 failed/unknown/posted/队列清理都不跨 poll 重申请。跨 grant 再核原生 `mcp_operations` 的 owner/repo/tool/key/payload；16项真实隔离 SQLite 与13项 envelope、6项 SSH未知投影测试通过。新 base 是新版本，不能将该策略描述为同head永远只有一次。

`posted` 只表示原生带 AI 归属说明的 `/review` 命令已发布，后续接单/模型/有效解析/版本再核是原生任务独立结果。传输或解析未知返回 model_started=null，旧已消费记录也不冒称从未调用过模型；grant撤销未知必须人工处理。当前只读探针证明接线，最终 `evidence/mcp-review-activation.json` 才记录实际未来事件启用；尚无新的自动语义审查模型验收。

## 现有安装顺序与复现边界

1. 两机已有`onticards-preview` UID1001、独立rootless systemd及UID网络拒绝规则。先读回cgroup/rootless/DNS/16项负向记录。不要改root Docker或系统限制。
2. `export_existing_dependencies.py`只在5机save已有amd64 PostgreSQL15/nginx1.27，不构建。kol原同tag缓存实际arm64，已被架构门禁拒绝，保留原tag。把归档及metadata送到kol受限候选目录。
3. 仅kol运行`bootstrap_trusted_images.py`：load既有amd64依赖、复用kol Weaviate1.36.0、用`Dockerfile.tests`构建固定可信测试镜像。生成`trusted-images.json`。真实rootless Chromium sandbox已通过：仅可信tests容器增加官方seccomp所需SYS_CHROOT，CapEff=0/NoNewPrivs=1；API/PR不增加cap，不关闭sandbox。
4. 在5机受信目录`/opt/onticards-maintenance/preview-ci/secrets`生成专用command/transfer两把ed25519私钥，0600/宿主UID1003，只挂可信CI容器；公钥可传两机。`known_hosts`由现有受信SSH读取各机host public key生成；不使用accept-new/关校验。
5. 两机用同一可信镜像锁执行`install_controller.py --role build|test --source-ip <实测可信n8n出口单IP> --command-public-key <公钥文件> --transfer-public-key <公钥文件> --trusted-images <锁文件>`先review-only，再`--apply`。固定machine-id哈希阻止角色装反。真实kol sshd确认可信CI源121.12.5.44；测试机源10.66.66.5。原先仅TCP连通推测123.88.32.135不可靠，已纠正。专用UID1003仅该目标TCP22走main，绕开既有TUN的错误接管；无新隧道、不改其他UID或全局Mihomo规则。不能填0.0.0.0/0。
6. 安装器只建专用transfer用户、root-owned ForceCommand/authorized_keys与internal-sftp chroot，无sudo/docker组，无forward/pty。`sshd -t`成功后reload，并读回sshd -T。验证任意命令拒绝、错hostkey拒绝、SFTP越界/写outbox拒绝。失败不投PR。
7. 可信CI以专用UID1003复用现成n8n2.42.7镜像，只读挂载原镜像passwd/group加该账户以及UID专属缓存tmpfs，`compose.ci.yml`独立持久库/encryption key，127.0.0.1:18132、broker18133、单并发；部署前检查端口未用。只此实例显式启用Execute Command。与主n8n和18128咨询工作流分开。
8. 原生DataTable `onticards_ci_receipts_v1`列：`receipt_key/head/base/state/detail` string、`pr` number。导入默认inactive的`preview.workflow.json`，配置原生HTTP Header Auth `onticards-preview-trigger`。来自已有采集workflow的原生HTTP Request POST到loopback `/webhook/onticards-fixed-preview-v1`，body仅`{pr,head,base}`，凭据不由PR提供。跨实例用native webhook，不声称Execute Workflow能跨实例。
9. 先固定head/base单次安全验收，再接原生采集中的PR新head触发。先后两次读GitHub；后置变动/不可读必须stale。版本检查每次复用原生App JWT→单仓pull_requests/metadata read→核scope→GET→DELETE撤销，发生在派发前、model前和结果后；凭据不传shell/PR。另有独立18+8+8节点 Check观察/登记/5分钟失效工作流，仅Check动作短token使用checks write+metadata read，不扩大App权限。当前Check创建/证据发布仍通过现有可信发布入口；无合并。

补充传输安装：两机 `install_artifact_registry.py --role publish|fetch --source-ip <已核源IP>`先review再apply。kol可信publisher UID1003，5可信fetch UID1004，均无sudo/docker组，固定ForceCommand。同一command公钥但不同专用账户及命令范围。只复制既有目标registry一项到各自0700 home/0600 authfile。5 inbox归fetch UID1004、group1001，PR运行账号只读；不再用SFTP上传大归档。已有SFTP slow partial与首次代理fetch failure归档，不静默重试。

## 结果及失败语义

远端`receipt.json`记录起止时间、每阶段退出码/timeout、是否真正启动测试、清理读回和模型状态。非模型成功必须有API7零fail的XML、PW2零fail/skip的JSON/XML与截图；模型成功另需PW3及真实extract-schema/query250/governance/四格式导出机器证据。缺失不得通过。固定命令不打印原始build日志，原日志限服务器受信目录。只打包明确机器报告、PNG和模型阶段固定产品证据，不自动公开任意trace/HTML。

同head/base的running/failed receipt不自动清空，跨n8n重启不会得到新预算。当前**没有产品化人工重跑/恢复**：需维护者检查原阶段和资源，再显式审核重置仅该run的n8n receipt与隔离目录（先归档原证据）。本轮不实现新retry controller，不据此宣称AC11完成。中断恢复、真实host reboot和磁盘硬配额仍未验。

`test-model`为显式独立阶段，相同镜像/manifest，结果目录加`-model`，不覆盖非模型证据。NewAPI普通账户原生租约仅chat+embedding两个固定alias、源IP限制、900秒、45000原生测试额度（不是USD；实际剩余额度不足时failclosed），不重置既有账户用量。stdin≤4KiB，只可信tests与产品API可见短token；finally撤销，撤销未知仍取脱敏证据并明确`revocation_unknown`，禁止重发。900秒包括load/startup，过期失败保留事实。GitHub派发前及结果后核head/base；变更/不可读为stale。固定单表真实模型业务r4已通过，多表rerank兼容缺口保留。共享kernel/rootless不是VM；外部fork拒绝；不放宽宿主网络/秘密边界。


## 22:57 网络与短租约实证

5机UID1001/subUID专用链仅放行10.66.66.5:18134/TCP，原公网RETURN改为REJECT；仅API接第二个原生model-egress网络，其他服务internal:true。原有拒绝项全部保留。真实短token合成请求200/精确模型回复，allow_ips=10.66.66.5得到验证，token6撤销；这不是PR产品模型链。普通NewAPI账号仅可信CI受限目录，PR不接触长期密钥。后续租约通过固定SSH stdin≤4KiB绑定run/head/base/expiry/SHA，当前首轮非模型CI尚不传租约。

PR26首轮在BuildKit auth客户端DNS阶段失败，tests_started=false；现已复用同一nsenter使原生docker build CLI也用专属public DNS，受信维护者归档旧receipt/log后重跑一次。自动相同run拒绝机制未更改。真实原生BuildKit超时/重启专用daemon/零残留已经证明。


## 2026-10-23 00:49 状态与恢复边界

- 非模型真实运行16:03—16:05Z，7 API + 2 PW通过；6 PNG采用原生html/data成功附件路径。收集路径修正仅重打包，未重复已成功测试；旧收集失败receipt保留。
- 第一次模型阶段使用token8，在密码轮换后沿用旧登录token，原应用401拒绝model_config，尚未进入推理。NewAPI原生读回used_quota=0/remain20000/status disabled，不能把发租约等于模型已执行。
- 现成Compose只清活跃profile会遗漏tests专属结果volume，已补--profile tests及容器/volume双读回。模型project加-model独立后缀；测试入口拒绝非空结果目录并在轮换后重新登录。两个根因都有红/绿，合计29测试通过。真实恢复前两个project容器/volume全0，旧run/outbox/lease/原n8n行归档。
- 一次批准恢复的令牌名54字节被NewAPI原生50字节门禁拒绝，原生GET两名均不存在后才缩为-r1并继续同一批准恢复；无新token或供应商调用。无自动重发逻辑。
- n8n子workflow execution正文none时SQLite旧实体可显示running；真实是否执行应读取原生/rest/executions concurrentExecutionsCount，不能直接把这些已返回的无正文子workflow行计为当前任务。

Check观察注册仅接受受信Header Auth固定仓库身份，核App5422414/head/name/external_id，head或base漂移/不可核实时将原Check置action_required，保留原证据，不自动重跑PR33。20个Code边界fixture通过；真实登记、synthetic失效与自然schedule已回读。历史段落保留当时状态。


## 当前证据、失效及部署材料

- `evidence/rootless-runtime/pr26-r4-native-workflow.json`：native执行70起止17:30:07–17:35:11Z；前/模型前/结果后三次head/base current且各token撤销。
- `pr26-model-r4-{receipt,lease,phase}.json`及实际产物目录：API7/PW3、项目容器/卷均0，短token用量/撤销；r2/r3原失败不覆盖。
- `pr26-rootless-check-publication.json`：Check119988255661，发布前后精确head/base、Draft不变，5最小token撤销；`check-watch-latest.json`含原生trigger和登记表，`check-invalidation-verified.json`证明真实neutral→action_required。
- [公开只读证据](http://10.66.66.5:18123/onticards-reports/acceptance/pr26-rootless-3105/)37文件，Gitleaks8.30.1零命中、PDF/Office成员扫描、每HTTP文件哈希一致/POST403。不含raw DB/trace/凭据。`package_pr26_evidence.py`为这次已完成产物的严格白名单封存，需现有Python/PyMuPDF；不执行测试。两个publish脚本复用既有Nginx/PyGithub模式，只可在受信host按固定receipt一次执行，POST不确定只读恢复。
- `install_revision_guard.py`仅新实例首次导入使用，要求空执行表；运行实例中的none保存子执行可能留running实体，升级时用原生REST concurrentExecutionsCount判断，不以旧SQLite行强行清理。`install_check_watch.py`复用REST activate导入，无需停模型任务。
- 原生模型lease有期、普通账户、双alias/IP限制；900秒包含startup。总账户不自动补额。当前余15445小于固定45000，下一次模型验收会显式拒绝，不能静默循环mint。历史r1-r4恢复入口只对应本次run和已批准receipt，不提供任意预算重置。
- CI final allowlist保持`deploy/research/evidence`相对目录；源脚本依赖的可信测试入口/flow脚本已纳入安装器。live Nginx最终从服务器回读，保留pdf-3105、pr33-fdd3、pr26-rootless-3105及精确模型路由，绝不能用早期local整份覆盖。

预算admission当前显式投影为`budget_exhausted`：原生GET账户余额不足45000时0 token POST/0 provider，phase记录`not_started/not_issued`并指向受信维护者分配；不自动reset/reissue。无网络5项回归及17:57Z部署/备份哈希见`budget-admission-deployment.json`。非模型CI不受此模型门禁影响。
