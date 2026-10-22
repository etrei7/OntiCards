# 专用原生 Rootless Docker 运行时

此目录提供两机原生执行环境配置；后续受限SSH、n8n固定CI、真实PR26构建/测试已接通，见 `../n8n-preview-ci/README.md`。研究与版本来源见 `research/n8n-rootless-preview-reuse.md`。原root Docker继续运行。

已有安装：Ubuntu uidmap/libsubid4 `1:4.13+dfsg1-4ubuntu3.2`；专用用户`onticards-preview` UID1001，子UID/GID165536:65536；user systemd daemon/linger，独立socket `/run/user/1001/docker.sock`，独立data root。账号无附加组、无密码登录；后续只允许固定来源及ForceCommand的专用公钥，不能交互登录。

受信配置脚本 `install_runtime.py`：使用系统已有 Docker installer，不造daemon；创建本用户systemd slice/drop-in与原生iptables owner链。仅该UID和子UID限制，原规则不删除/改写，IPv6对本身份全部拒绝。4GiB/CPU200%/4096 tasks为用户总上限；具体容器还需单独配置更低限制。

`probe_runtime.py`：传入本机已有 `busybox:latest`（kol）或 `redis:7-alpine`（5机），仅save/load再运行无业务探针。真实内核cgroup/CapEff、身份/权限、网络拒绝与正向TCP分别记录，不读秘密内容。源镜像tag只用于找到已缓存镜像，证据记录实际ID/层，禁止将浮动tag用于正式PR产物身份。

远端配置和备份记录位于root独占 `/opt/onticards-preview-setup/`。观察命令需以授权管理员执行：

```sh
runuser -u onticards-preview -- env XDG_RUNTIME_DIR=/run/user/1001 systemctl --user status docker
runuser -u onticards-preview -- env XDG_RUNTIME_DIR=/run/user/1001 docker --context rootless info
systemctl status onticards-preview-network.service
iptables -S ONTICARDS_PREVIEW
ip6tables -S ONTICARDS_PREVIEW
```

停止仅本运行时：先确认本用户无活动构建/容器，再`runuser ... systemctl --user stop docker`；不停止宿主docker，不删除其他工作目录。网络过滤应保留至该UID全部进程结束。若回滚配置，先停本user daemon、disable linger，并仅移除带本UID/子UID的两条OUTPUT跳转和`ONTICARDS_PREVIEW`独立链、对应systemd专属unit/drop-in；不要flush OUTPUT或全量restore旧网络规则。用户/数据保留供审计，删除须另行确认范围。

后续网络边界：kol专用namespace原生public DNS；5机rootless拒绝公网/私网/metadata，仅API可到10.66.66.5:18134的精确模型路径。registry由可信独立UID按digest拉取后只读交rootless；CI可信UID仅指定kol TCP22复用main路由，不改全局Mihomo。实际PR26非模型API7/PW2通过；完整模型与Check最新结论见CI README。本配置未实测整机重启后的执行链。
