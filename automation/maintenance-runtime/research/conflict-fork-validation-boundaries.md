# 确定冲突、语义冲突与 fork 继续的实测边界

2026-10-23，固定 policy12 tree `b3dd9a914e431b15b41febbf97211d736e6428fd`。只复用原生 Git merge/rollback、ProPR continuation 与已有人工作业边界，不向外部仓库写入，不调用模型。

`packages/core/test/conflictResolution.test.ts` 随 policy12 原467回归实际运行：真实本地 Git 文本/二进制冲突进入 unresolved，模型与标题生成回调均为0、回滚且不推送；确定的独立文件整合仅向 PR 分支形成双父 merge，main 不变；头已变更、已包含 base 的路径不重复执行。

另外在同一已编译镜像、`--network none` 执行原生 `test/prContinuation.test.ts` 49项及一个真实语义负例，共50/50无跳过。fork测试使用真实本地 bare upstream/fork、实际提交/父子关系/作者信息，但 GitHub 权限响应和 PR API 是 fixture，并非真实外部 fork E2E。已有分支无权发布时原生 continuation 保留源 SHA、作者与 base；维护模式只用 codex/ 自有目标，原 contributor 分支保持不变。没有新建线上 PR。

语义负例的两个分支各自执行通过：PR 将函数 run 改名 execute 并改已有调用者；main 新增使用 run 的另一调用者。Git 无文本冲突地整合，真实 Node 执行合并后新增调用者却因缺失导出失败。**这不是“语义冲突已自动解决”的通过证据**；它证实 clean merge 只能代表 Git 文本整合成功，必须继续现有精确 head/base 测试与人工审查，最终不得由机器人合并 main。

证据 `evidence/propr-conflict-fork-semantic-validation.json` 包含真实结果、界限、源码tree及日志hash；负例源码 `deploy/propr/fixtures/maintenanceSemanticConflictFixture.test.ts` 是独立验收fixture，不改变生产 patch。policy12 的679项构建回归与这50项补充验收分别统计，避免把边界负例的测试通过解释成业务语义通过。
