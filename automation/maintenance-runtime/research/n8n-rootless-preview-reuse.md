# 当前实施事实（2026-10-23 01:50）

下文按时间保留先研究再实施的原始记录。已授权并实际完成两机rootless、专用UID和网络拒绝、OpenSSH固定命令/hostpin、可信registry发布/精确digest拉取、固定PR26原生n8n完整真实模型业务API7/PW3/9PNG/四格式，以及37文件门户/Check/5min版本失效。复用来源和最小适配均在原记录；当前详细边界见deploy/n8n-preview-ci/README.md。初期“尚未授权/尚未实现”仅当时状态。

当前剩余：外部fork拒入此CI；共享内核不是VM；磁盘硬quota/hostreboot/fresh安装未验；新PR自动派发未接；fresh build匿名元数据限流failclosed；模型账户余15445低于固定45000，不能自动后续调用。固定验收通过不包含lint/迁移全验/PR33并发专项。

## 原始研究与阶段记录

# 原生 n8n / OpenSSH / Rootless Docker 预览执行环境

## 当前可审阅状态（2026-10-22 22:57 CST）

已部署两机专用 rootless 运行时及固定命令/SFTP边界，尚未宣称完整 CI 或 AC06/07/09 完成。可信测试镜像只在 kol 构建，5机经 save/load 验证配置与层一致；真实 Chromium sandbox 在非 root/NoNewPrivs 下通过。官方 seccomp 要求受信浏览器容器单独声明 SYS_CHROOT（实际 CapEff=0），API/PR容器仍 cap_drop ALL。没有禁用 sandbox、SYS_ADMIN 或宿主 AppArmor/sysctl 变更。

| 能力 | 真实验证 | 当前缺口 |
|---|---|---|
| 隔离网络 | 5机仅 UID1001/subUID 的 TCP 10.66.66.5:18134 精确允许，其他公网也拒绝；8个负向目标、internal-only拒绝、401及TCP正向对照通过 | 尚需实际PR API负载时再取边界 |
| 短模型租约 | 复用 New API 原生 user2/group/900秒/model/IP/quota；rootless合成调用200，18输入+3输出，token6立即禁用读回 | 合成探针不是完整产品模型链；embedding/rerank业务目标未删，不能假定单chat路由覆盖 |
| SSH | 原镜像现成OpenSSH/SFTP，固定 known_hosts；两机11项任意命令/越界/写outbox/symlink/错误hostkey拒绝通过 | 自动PR事件入口未接 |
| 可信CI出口 | 独立UID1003，只有101.47.177.55/32 TCP22经原生policy routing main；其他UID/路由不变；真实kol源121.12.5.44，公钥from精确限定 | 专用服务开机恢复未通过真实宿主重启验收 |
| 超时 | 原生进程组真实杀子进程；真实BuildKit sleep超时，重启仅专用user daemon，sleep和容器零残留 | 复杂产品测试失败后的完整Compose清理仍待本轮实际运行 |
| PR26固定构建 | head3105b7b6/basec8e，GitHub PR/精确refs/fetch/fsck通过；首轮DNS基础设施失败已完整保留，经人工审核归档后修复namespace；新API镜像已构建，Web构建中 | 传输、5机API7/PW2、原生n8n整轮结果尚未完成 |
| n8n | 现成2.42.7独立18132实例，14个原生节点配置；独立数据库/密钥/UID1003/loopback/单并发 | 正在初始化，配置默认inactive，尚未连持续采集 |

新增适配仅绑定固定repo/PR/head/base、原生SSH/SFTP、BuildKit/Compose/既有测试之间的输入和结果，不造调度器或runner管理器。相同head/base receipt仍持久消耗，不自动重试；环境修复后的人工恢复有原始receipt/log及原因，不能称产品化AC11已完成。外部fork仍拒绝，最终合并仍由维护者完成。共享内核不是VM，磁盘硬配额尚未实现。

构建客户端使用原生 util-linux nsenter 进入既有 RootlessKit mount/network namespace，是因为 BuildKit registry auth 在CLI进程解析DNS，单改daemon DNS不够；没有开放CGNAT DNS。复用依据：[RootlessKit network/copy-up](https://github.com/rootless-containers/rootlesskit/blob/master/docs/network.md)、[OpenSSH固定命令与chroot](https://man.openbsd.org/sshd_config)、[Linux ip-rule](https://man7.org/linux/man-pages/man8/ip-rule.8.html)。n8n原生SSH节点2.42.7缺hostkey验证，故选已有Execute Command调用现成OpenSSH/SFTP，非新SSH实现。

关键证据：`evidence/rootless-runtime/{trusted-tests-bootstrap,trusted-tests-loaded,model-egress-configuration,model-egress-probe,model-short-lease-probe,restricted-ssh-probe,trusted-ssh-route,trusted-build-timeout,ci-process-timeout}.json`；sandbox red/green日志同目录。精确配置：`deploy/n8n-preview-ci/`。首轮PR失败及恢复证据在远端recovery，待同步脱敏记录。

## 历史实施记录（以下旧状态不代表当前）


2026-10-22，实施前核对。目标对应 R11/R12/R13/R14、G04/G07、AC06/07/09/12；原 Actions 模板保留，因缺隔离 runner 和默认分支配置，尚不能提供长期验证。改用现有 n8n 调度和 SSH 节点衔接固定可信命令，不另写调度器、runner 管理器或放宽 GitHub App 权限。

## 已有能力与选择

- [n8n SSH 官方节点](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.ssh/)原生支持命令、上传和下载。复用现有 2.42.7 镜像；本阶段不创建 SSH 授权或启用构建流程。
- [Docker rootless 官方安装](https://docs.docker.com/engine/security/rootless/)支持独立非 root daemon/user namespace、systemd user unit、linger。已有 root Docker 保留，安装器原生 `--force` 仅允许两者并存，不改变原 daemon。
- [官方运行说明](https://docs.docker.com/engine/security/rootless/tips/)确定独立 socket/data 路径；资源限制依赖 cgroup v2/systemd。两机均已有 cgroup2，必须实测 driver/controller，未验证前不称资源限制有效。
- [Ubuntu 官方 rootless 排错说明](https://docs.docker.com/engine/security/rootless/troubleshoot/)要求已有 AppArmor rootlesskit profile。两机当前 `/etc/apparmor.d/rootlesskit` 已加载，userns sysctl=1，保持 AppArmor 限制及所有 sysctl 不变。
- [RootlessKit 原生网络](https://github.com/rootless-containers/rootlesskit/blob/master/docs/network.md)采用 slirp4netns，保留 `--disable-host-loopback`。另外复用宿主 [iptables owner/addrtype](https://man7.org/linux/man-pages/man8/iptables-extensions.8.html)，仅专用 UID/子 UID 范围附加独立链，拒绝宿主、RFC1918、CGNAT、link-local/metadata 和 IPv6 本地范围；不改既有规则/默认策略。规则是配置，不是自造网络代理。

## 真实前置与具体缺口

只读确认无 `onticards-preview` 同名用户。kol-stage2 为 Ubuntu24.04、Docker28.5.1、RootlessKit2.3.4；10.66.66.5 为 Ubuntu24.04.3、Docker29.1.3、RootlessKit2.3.5；两机 slirp4netns1.2.1。已有 rootless 安装脚本，但 `newuidmap/newgidmap` 均缺，subuid/subgid 只有原用户100000:65536。

采用 Ubuntu 软件源 `uidmap` 与必要 `libsubid4`。APT 模拟显示打包机还需同源 `login/passwd` 依赖更新，测试机仅新增两包；不安装新 Docker，不运行系统批量升级或 autoremove。建立独立锁密码用户及不重叠65536映射，不加 sudo/docker 组。只安装本用户 systemd/rootless，负向探针前不接收任何 PR 代码。

尚未实现：固定 head/base/tree 的可信控制 bundle、只读源码输入、构建只在 kol、产物不可变身份、5机独立 Compose/API/PW、结果 allowlist 和新 head/base 失效。SSH 必须采用固定命令/受限凭据；不能让 PR 修改的 Compose、脚本或工作流获得宿主命令、SSH 私钥、Docker socket、生产秘密。外部 fork 仍不投放共享宿主。Rootless 缩小权限边界，不等同虚拟机隔离或所有资源/网络限制已通过。

本阶段只配置运行时并做正负向探针；不注册 runner、不授权 SSH 公钥、不 build、不部署 PR。若原生前置失败，记录并停止该路径，不放宽 AppArmor/sysctl。

## 20:55 实测

两机均成功建立 `onticards-preview`，UID/GID1001，唯一同名组，锁密码，无 sudo/docker 组和 SSH 授权；自动分配165536:65536子UID/GID，与原映射不重叠。原生 systemd user daemon、linger、独立 `/run/user/1001/docker.sock`、用户数据目录均正常，Docker明确报告 rootless/systemd/cgroup2。仅该用户 slice 设置4GiB/CPU200%/4096 tasks，原 root Docker PID、AppArmor哈希和sysctl前后相同。

现成 `busybox:latest` / `redis:7-alpine` 从各机已有镜像save/load，逐层身份一致，未 build。仅探针容器设read-only、cap-drop ALL/no-new-privileges、无宿主秘密/Socket挂载，实际cgroup memory=64MiB/pids=64/cpu=0.5，CapEff=0/NoNewPrivs=1。宿主新UID与容器各8个网络负向目标全部拒绝，含真实已监听loopback对照、RFC1918、Docker桥、link-local/CGNAT metadata、打包机公网地址及RootlessKit宿主gateway；IPv6此身份全拒绝。宿主UID读取本任务App私钥/根SSH目录与连接root Docker socket均拒绝。无探针容器残留。

公网正向仅kol的1.1.1.1:443 TCP连接通过；5机未通，不能声称registry/包管理/DNS可用。5机现有Mihomo TUN路由保留，UID过滤命中拒绝计数；不为通过正向探针改全局代理或放开loopback。5机部署可先采用可信传输的镜像save/load，测试对模型/外网的依赖需另行明确。完整记录见 `evidence/rootless-runtime/{kol-stage2,server-183}/runtime-{installed,probe}.json`。

## 下一步可信执行合同（尚未实施）

1. 复用 n8n 原生调度/SSH 执行，凭据只在受信 n8n；远端 authorized_keys 固定命令、禁forward/pty、限制来源，由维护者审查后配置。本阶段没有创建任何密钥或授权。
2. 可信控制 bundle 固定版本/哈希，与PR源码分开。复用已通过的Compose覆盖/API/PW测试，运行脚本只能接受固定仓库、PR号、精确40位head/base以及限定工作目录，不执行PR提供的工作流/Compose/宿主shell。动态PR Dockerfile只能在kol的rootless构建边界执行，无凭据/宿主socket/SSH挂载。
3. 使用Git原生归档/bundle与精确SHA校验交付源码，构建产物通过Docker save/load和SHA256送到5机rootless；不把registry推送凭据给不可信代码。5机不build。固定端口/网络/卷/命令由可信bundle决定，禁止PR任意声明宿主bind、privileged或host网络。
4. 结果复用原生JUnit/Playwright HTML/截图；manifest绑定repo/PR/task/run/head/base/tree/image/命令/退出码，发布只选固定allowlist。新的head/base必须使旧报告不再代表当前结果。尚未接通这条执行合同，不能将运行时探针称为长期CI验收。

共享内核仍是边界，rootless不是VM。未来若出现需要放宽sysctl/AppArmor、开放宿主代理/秘密、裸宿主运行PR脚本等条件，本方案必须拒绝，不能以测试需求扩大权限。

## 21:30 具体接入选择（候选，未授权密钥/未执行 PR）

原生 SSH 节点 2.42.7 的实际 `Ssh.node.js` 只向 node-ssh 传 host、port、username、privateKey/passphrase，未提供 hostVerifier/known_hosts 选项。不能把“能 SSH”当作已核验服务器身份。复用同镜像已有 `/usr/bin/ssh`、`/usr/bin/sftp` 及 [n8n Execute Command 原生节点](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand/)，固定 root 管理的入口脚本，使用 [OpenSSH](https://man.openbsd.org/ssh_config) `StrictHostKeyChecking=yes` 与独立 known_hosts。该节点默认禁用，仅拟在专用可信 CI 实例显式启用；不改变共享/咨询实例。不得将任意 PR 文本插入 shell 命令。

两机专用 rootless namespace 使用 util-linux [nsenter](https://man7.org/linux/man-pages/man1/nsenter.1.html) 设置自己的 public DNS；未放行 CGNAT DNS，也未改宿主 resolver。kol 原生 Git HTTP/1.1 ls-remote 当前 main c8e 成功；5机 DNS 成功、原生 Git 40秒超时，保留失败，不称公网完整 clone 可用。两机负向规则重验通过后方可接工作负载。

候选固定命令只接受同仓 codex PR、精确 main base/head、确定性 run ID。kol Git fetch 与 rootless BuildKit 构建、Docker save；5机只做 rootless load、固定可信 Compose、原 pytest7 和非模型 Playwright2。真实模型业务测试仍保留未覆盖：长期模型密钥不能进入 PR API。复用 n8n 编排和 SSH/SFTP 传输，不添加轮询器、任务状态数据库或 CI 平台。构建日志与测试结果受限保留，不自动公开任意 HTML/trace。

命令账户与 SFTP 账户分开：[OpenSSH 服务端](https://man.openbsd.org/sshd_config) ForceCommand / ChrootDirectory / internal-sftp，root 控制 authorized_keys，禁 forward/PTY，按可信 n8n 实际出口限制来源。只有专用 SFTP inbox/outbox 可传输；私钥仅可信 n8n，PR build/run 无 socket/SSH/凭据挂载。候选安装器先校验 sshd 配置再 reload，父代理审查前不运行。

现阶段边界：共享内核并非 VM；4GiB user slice/容器内存与进程已验证，尚未配置磁盘硬配额；新可信测试镜像尚未构建，rootless Chromium sandbox 与资源峰值待真实测试，不以禁 sandbox/加 SYS_ADMIN 解围。外部 fork 拒绝。默认 inactive 的候选不等于持续 CI 已运行。
