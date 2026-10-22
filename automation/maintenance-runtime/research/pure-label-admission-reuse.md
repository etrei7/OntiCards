# 普通标签初次分发的持久边界（冻结 policy12）

2026-10-23，先登记缺口，再修改。基线 ProPR 0.9.0 / Apache-2.0，上游 `42931b1502eb03ac299f14e306811736fab51eb4`，已部署 policy11 tree `c5ace8247411ee8c33802a62169fd02e54d0378b`。

## 已有实现与真实缺口

`issueDetection.ts` 普通 parent 固定 job ID、attempts=3、removeOnComplete/removeOnFail=true；`issueJobDispatcher.ts` 在 GitHub 认证、读取 Issue、选择模型与入队前不创建 Task。纯标签没有 `task_submissions` 记录。因此父任务失败后，下一 poll 能重新开始。

policy5 的 `findFailedLabelTask` 只看 SQLite 最新 failed 历史。原生 `WorkerStateManager.persistTaskStateCreation` 和 `publishTaskStateTransition` 会记录但吞掉持久化错误；`prepareIssueJob` 也允许创建状态失败后继续。因此有工作已执行而 SQLite 无 failed 终态的实际代码路径。这是预算边界缺口，不是模型质量问题。

BullMQ 5.81.3 的 [auto-removal](https://docs.bullmq.io/guide/queues/auto-removal-of-jobs) 明确移除后同 ID 不再去重。只保留 job 仍受共享集合 age/count 清理、模型/base 变更影响。现有原生 issue retry request + accepted tombstone 已解决**有认证请求**的去重；不得伪造 requester/comment/submission 来套用。

## 采用的现成能力和最小衔接

复用原生 `WorkerStateManager.createTaskStateIfAbsent`、Redis [SET NX](https://redis.io/docs/latest/commands/set/)、已有 `tasks` 唯一 task_id 和 task_history、状态发布、原生 orphan/terminal reconciliation、已认证 Task Follow Up。没有新表、计数器、调度器或通用 receipt 服务。

维护模式下，纯标签首次分发先检查同 repo/issue 的原生 issue Task（不仅 failed；pending/unknown 不能自动恢复预算），再用固定规范化 Issue 身份创建**真实分发 Task**，与随机 correlation 共同确认 NX 的赢家。必须读回自己已提交的 SQLite task + pending history，才能调用 GitHub/选择目标/加入 child。失败保持原生 failed/unknown；成功仅记录“分发完成”，不冒称修复成功。当前父分发错误使用 BullMQ 原生 [UnrecoverableError](https://docs.bullmq.io/patterns/stop-retrying-jobs) 终止这个未获人工续办的首投递，既有 child 限次保持原样。

该记录在任务执行前存在，因此子任务最终 failed 写入丢失也不会授权下一 poll 新预算。原生认证 retry request 仍先解析，沿既有原子入队/永久 accepted tombstone 一次续办；不删除或复位首记录。已完成分发记录是防重复依据，不应被普通存储整理清除；显式整库重置/管理员删除状态属于外部破坏此持久性假设，必须先停止 intake，不视为自动恢复。

实施前候选只在隔离 overlay 修改。随后主流程审阅2个生产文件并授权 kol 构建。最终 delta 为生产 `issueJobDispatcher.ts` +42/−2、`taskHistoryControl.ts` +3/−0；新测试174行，既有聚焦测试注入2行。没有修改上游通用状态管理器，也没有将 best-effort 状态写入改成新的全局机制。

## 已完成的无模型红绿与构建

原 policy11 的父分发失败红例 0/1：两个不同 poll 重复认证并再次失败，仍没有 Task。candidate 9/9：真实 SQLite trigger 分别拒绝 Task 插入、pending history、失败终态；任一前置未持久化时没有认证/child 入队。模拟 child 已接受但回复丢失且 failed history 写失败，移除 Redis/队列、重开 SQLite pool后多 poll、大小写/model/base 变化仍不能新增预算。两个并发投递仅原生 NX 一位赢家。真实 reserve/begin/record/select/enqueue/consume 的已认证 retry 在初次失败后只入队一次，删除 child 后 accepted tombstone 仍阻止重入。

固定 tree `b3dd9a914e431b15b41febbf97211d736e6428fd` 从上游完整补丁重构通过；完整补丁 SHA256 `6faa1328f318ceff10c018271222a5f3a7828c022f30417167246b9f111ca2a7`。kol 编译、原467项、索引11项、新9项及相关192项共 **679/679，0 skip**，0模型、0外部仓库写入。`evidence/propr-policy12-admission-validation.json` 保存各组与红例的实际退出结果、日志hash、source tree与镜像digest。早期存储组因未设 REDIS_PORT 的6项 skip仅作历史，最终已启用该原生fixture并全部通过。

主流程已于 `2026-10-22T18:31:20Z` 部署 policy12：API/worker/daemon 均固定 digest `sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa`，队列切换前后为0；见 `evidence/propr-policy12-deployment.json`。完整补丁89文件的逐组原因见 `research/propr-patch-map.md`，不是89项新功能；本次只有2个生产扩展点。未知任务需等原生终态重放/orphan reconciliation或人工核查后明确恢复，不把未知自动改 failed 来获得续办。该边界不承诺管理员整库删除/显式删除Task后的持久性，也不会回填从未记录过的历史付费运行。
