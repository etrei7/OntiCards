# AC11：入队前取消复用核实

2026-10-23：先核对现有源码与上游，再验证，不新增取消系统。

来源：ProPR 0.9.0，上游固定 commit `42931b1502eb03ac299f14e306811736fab51eb4`；实际验证镜像为已部署 policy12，digest `sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa`。

- [上游 taskCancellation.ts](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/packages/core/src/services/taskCancellation.ts) 已有 `stopTaskExecution`。本地对应 `research/propr-src/packages/core/src/services/taskCancellation.ts`：`ensureCancelled` 允许 pending，写 abort 信号并持久取消，不要求先有队列 Job 或容器。原生 WorkerStateManager 写 Redis 状态与 SQLite Task/history，并拒绝 cancelled → processing 的晚到更新。
- `packages/api/routes/dockerRoutes.ts` 原生 Stop handler 传 `ensureCancelled: true`、`cancelled_by_user`；UI `propr-ui/src/components/TaskDetails/ActionBar.tsx` 和 `MetadataBar.tsx` 的活跃状态包含 PENDING/QUEUED，`proprApi.ts` 请求原生 `/api/task/:taskId/stop`。因此此前“prequeue Stop 未实现”的宽泛说法不成立，应区分已有实现与尚未做真实点击验收。
- 复用上游 `packages/api/test/stopTaskRoutes.test.ts` 的 Express 临时 HTTP/Auth 测试壳，但不替换 Stop executor、StateManager、Redis、数据库或 BullMQ；隔离夹具直接导入生产镜像编译模块。真实 OAuth 仍保持原配置，夹具身份中间件不等于完整 OAuth 回环验收。
- [Redis TTL 官方文档](https://redis.io/docs/latest/commands/ttl/) 用于核实实际 abort 信号仍有不超过 3600 秒的过期时间。复用现有固定 Redis 镜像 `redis:7-alpine@sha256:e7723ff73d963f5cc6d9c4643ea3d989527a402a319239054e9472a7fb9219a2`。

新增代码仅 `deploy/probe-prequeue-stop.py` 验证夹具，对应“该边界没有真实 Redis/SQLite/HTTP 联合证据”的缺口，不修改业务或取消实现。两条合成 Task 均从原生 createTaskStateIfAbsent 创建，尚未入队；验证 Stop/cancel alias、持久终态、abort TTL、重复请求和晚到 worker 状态更新。不会读取现有任务、生产 Redis 或生产数据库；不触发模型、GitHub、Worker、Agent。

首次尝试创建内部 Docker 网络因服务器预定义地址池耗尽失败，保留 `evidence/ac11-prequeue-stop-network-red.json`。改复用 Docker 原生 `--network none` 的 Redis 容器命名空间，应用夹具以 `--network container:<isolated-redis>` 仅访问同命名空间 loopback，无宿主端口、凭据或生产卷、外网路由；两个临时容器在 finally 中移除。此调整不改测试目标，也不调整现有 Docker 网络。

实际 02:49:11–02:49:24（北京时间，精确结束时间以 JSON 为准）最终 `evidence/ac11-prequeue-stop-native.json` 为 25/25，通过真实 Redis 7.4.10、SQLite 迁移后的原生 Task/history 与生产编译 HTTP handler。两任务均 job_id=null，Stop/cancel 返回200，Redis/SQLite终态 cancelled；abort 带操作者与3600秒内 TTL，重复请求400、未知任务404、晚到 processing 更新仍 cancelled。临时容器已移除，0 Worker、0模型、0 GitHub请求、无宿主端口/生产卷。

夹具首次使用了错误的历史表列名 `id`，在原生取消成功后读证据失败；依照现有 migration 改为 `history_id`，保留 `evidence/ac11-prequeue-stop-fixture-schema-red.json`。这是夹具缺陷，不能表述为业务取消失败或业务修复。最终25项独立重跑使用全新合成任务。

尚不将该夹具等同于浏览器真实点击 Stop、OAuth 身份授权全集、已运行 Agent 中断或跨实例并发取消验收。
