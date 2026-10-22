# Issue32 原生任务 Git 准备实测

2026-10-22，只读诊断，无新模型、重试或终止动作。

原生 queue job ID：`issue-stepll2026-onticards-32-onticards-qwen-opencode-bailian/qwen3.8-max-0902-main`；实际数据库 task ID：`stepll2026-onticards-32-onticards-qwen-opencode-bailian-qwen3.8-max-0902-60bf7d5c-4ea9-405b-a083-52c27d7b0dd4`，二者不可混用。统计通过 job_id 找到真实 task_id/correlation_id 后查询：processing，0 llm_executions、0 llm_logs。

## 已确认

- 13:50:00Z worker 的 git clone 已运行391秒；宿主 Git/worker UID0。这不是 Agent 沙箱 UID，也不代表模型已启动。
- clone 使用 `--depth=1`、干净 HTTPS origin，认证通过原生 process-local extraheader；未读取或输出 token。全局实际 `http.version=HTTP/1.1`。网络使用已有代理配置，此安全报告仅记录已启用，不包含代理路径/凭据。
- index-pack 正在接收数据，临时 pack 从13:50:49的2,473,983字节增至13:51:33的2,711,551字节；13:54:04为3,571,711字节。是慢传输，不能写成“完全无连接”。
- 大小写缓存分叉：旧 `clones/stepll2026/OntiCards` inode3964181，HEAD `c8e3dfee68d398a37842fc332f73af40a56f02a7`、shallow、3个worktree注册；新 `clones/stepll2026/onticards` inode3974383，HEAD未解析、0个worktree。不能移动/覆盖旧缓存。
- `taskSubmissionRoutes.ts:372` 对 New Task repository 做 toLowerCase；`git/repositoryPaths.ts:107–110` 保留传入大小写形成文件路径。既有bootstrap固定 `OntiCards`，本次 New Task 实际要求 `onticards`。Linux上两个缓存不同。

## 600 秒和 Stop 的边界

13:54:06左右实际 clone 已638秒，13:55:01为693秒，仍在运行。`processGitHubIssueJob.ts:310` 直接 await ensureRepoCloned；`hooklessGit.ts:24–39` 未设置 simple-git timeout/AbortSignal，repoManager clone 路径也没有任务600秒的封顶。因此不能称本阶段已有600秒自动终止；Agent分析/执行层的600秒不是整个任务预算。

主流程尝试UI Stop确认时浏览器控制超时。13:55:24读取精确 taskId 与 jobId 的 `worker:abort` 均不存在（TTL -2），数据库仍processing，API从13:53:30起没有该任务的 stop-execution事件。没有证据说明这次停止请求到达API，不能归因为“已收到Stop但Git忽略”这一单一事件。

源码独立显示准备期停止缺口：原生UI `dockerRoutes.ts:104` 使用 ensureCancelled=true，收到请求应即使无容器也持久cancelled+abort；`taskCancellation.ts:384–413`设置标记，`422–430`只查claude_execution中已记录容器。Git准备阶段无此容器，也未接入该abort检查。现成 Agent admission/abort helper存在，可供后续最小扩展审查，但本次没有实现。

## 最小复用方向（尚未执行）

1. 先由主流程确认原生停止/终态以及旧Git进程退出；不能在活跃clone目录上修复或重跑。
2. 复用已经验证的 `bootstrap_native_git.py/.mjs` 运输受信浅Git对象，再调用现成 ensureRepoCloned/createWorktreeForIssue；目标必须是这次实际的lowercase仓库路径，对应URL校验也须匹配大小写。
3. 不改变旧uppercase目录及其3个worktree。不得通过共享同一.git的临时符号链接掩盖原生storage registry身份。
4. 准备阶段的硬时限和Stop需另列真实缺口，优先复用simple-git原生abort/timeout与既有任务abort helper，不写新Agent/调度循环；未验证前不宣称已修。

证据：`evidence/issue32-git-preparation.json`（无模型env、秘密、原始进程参数或raw logs）。当前为观察时快照，最终任务结局须以主流程后续证据为准。

## 取消后恢复和原生能力验证

14:00 后已确认原生服务持久化 cancelled，但精确 Git 树仍活跃。只对该已取消任务的四个已核 PID 执行 operator cleanup，3秒后全退出；没有终止 worker。这不是原生 Stop 成功停止 Git 的证据。随后保留原小写 partial 到独立 recovery 目录，复用已有 bootstrap 脚本和已核浅仓库对象，再调用原生 ensureRepoCloned / createWorktreeForIssue。三个阶段成功，真实 origin fetch 27.932秒，临时 contents-read token 已撤销；旧大写 inode/HEAD/3 worktrees 不变。详见 `evidence/issue32-operator-git-cleanup.json`、`native-git-bootstrap-lowercase.json`。原生 cache ownership registry 尚未登记，禁止冒称自动清理已接管。

新增代码前复用判断：锁定依赖 simple-git 4.0.2 已有 [AbortSignal 插件](https://github.com/steveukx/git-js/blob/simple-git%404.0.2/simple-git/src/lib/plugins/abort-plugin.ts)、[timeout 插件](https://github.com/steveukx/git-js/blob/simple-git%404.0.2/simple-git/src/lib/plugins/timeout-plugin.ts) 与 [执行层](https://github.com/steveukx/git-js/blob/simple-git%404.0.2/simple-git/src/lib/runners/git-executor-chain.ts)。插件发 SIGINT 给 Git，不是另写 process runner；timeout 的 stdOut/stdErr=false 可防进度输出延长 wallclock。隔离无网容器内用真实 Git 对本机停滞 HTTP 端点克隆：abort 205ms，700ms timeout 854ms，clone / remote / remote-http 子进程均无存活。仅证明这类 Git 网络进程路径，不宣称能杀任意不可信脚本。

必要适配范围：复用既有 createExecutionDeadline、execution ownership context 和 Redis setupAbortChecker，向 hookless Git 注入原生 AbortSignal；将 Issue 的 clone/fetch 和 worktree 准备接入有界阶段。不会新增 Agent 循环、任务调度器、通用进程树系统，也不更改任务终态存储。准备阶段时限不等于整个包含模型/发布的任务总预算。候选通过真实子进程回归与既有取消测试后才可交主流程审批部署。

## 候选结果（未部署）

- `deploy/propr-native-git-preparation.patch` 是相对于已部署 policy6 源码的增量，10文件，其中6个生产文件和4个测试文件。生产改动只接现成 AbortSignal、deadline、task cancellation checker；现有 Docker checker 保持原清理流程，Git 目标不调用 Docker teardown、不消费共享 abort marker。
- clone/fetch、worktree 创建、HEAD 读取、首次 push 使用同一 monotonic 600秒准备预算。取消轮询默认2秒；Redis失联会停止准备且作为失败，不冒充用户取消。限时作用于这些 Git 阶段，不是整个任务/HTTP请求/文件系统操作的通用硬限时；现有 storage 等待和清理保留自己的有限超时。
- 两个真实 Git HTTP 子进程测试先 red（仍运行），修改后 green。最终 core + root TypeScript 编译通过；5个测试文件共51项通过、0失败、0跳过。新9项包含真实 clone/remote/remote-http 停止、Redis标记注入（隔离测试替身）、查询失败fail closed、期限、已取消拒绝启动、吞掉底层错误仍拒绝进入下一阶段、成功路径、过期共享预算拒绝启动。
- 没有使用生产模型、GitHub写凭据、生产Redis、Docker socket或外部网络。容器内的HTTP服务器只模拟停滞的 Git 传输；Git本身和其子进程是真实进程。测试与编译通过不等于部署后的真实任务验收已完成。
- 相对 policy6 测试镜像 `git apply --check` 通过。复验入口：`deploy/propr/run-native-git-preparation-tests.sh`；真实输出保存在 `evidence/native-git-preparation-tests.log`，其中仅无凭据测试夹具路径/错误。

缓存 registry 拒绝的原因已另用只读函数核实：`repositoryMetadataFingerprint` 返回 `unknown_git_state`。`storage/repositorySafety.ts:158–159` 的允许名单不包括 `.git/shallow`，因此保留原浅仓库的 bootstrap 按现有安全策略不可获得自动清理所有权。这不是需要强行修复的注册错误；保留，不手工伪造记录。
