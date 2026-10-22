# 内网 HTTP 原生 New Task UUID 兼容缺口

记录时间：2026-10-22。此项先确认现有实现与现成依赖，再修改 UI；不更改服务端任务、幂等、调度或 Agent 流程。

## 已证实缺口及范围

10.66.66.5 内网 HTTP 的原生 New Task 页面点击一次后停在 Submitting。父流程在浏览器实际取得 13:10:57Z 的 `TypeError: crypto.randomUUID is not a function`。`NewTaskPage.tsx` 设置 submitting/busy 后，在 try/finally 之外生成 key，因此既未生成 submission ID，也未调用 IndexedDB/POST，异常也未恢复表单。服务端当次 task_submissions 与队列均空，不能当成未知 GitHub 创建后自动重发。

这属于 AC08/AC11 内网管理入口的实际兼容缺口。现有 IndexedDB 存储、同 ID 重试、未知 POST 查询、服务端持久幂等机制继续复用，不另建提交服务。

## 复用选择（实施前）

| 需求 | 已有能力与精确来源 | 接入方式 | 已验证与限制 |
| --- | --- | --- | --- |
| HTTP 下强随机 UUID v4 | 仓库 root 已依赖 uuid；lock 精确 14.0.1，MIT。[v4 源码](https://raw.githubusercontent.com/uuidjs/uuid/v14.0.1/src/v4.ts)、[rng 源码](https://raw.githubusercontent.com/uuidjs/uuid/v14.0.1/src/rng.ts) | UI 显式声明同一已有依赖，调用 v4；库优先原生 randomUUID，缺失时采用 crypto.getRandomValues | 已查源码，无 Math.random 降级、无自行实现 UUID。实际浏览器和回归测试待执行。 |
| 提交前异常恢复 | 原生 NewTask run 的 try/catch/finally | 将 ID 构造纳入同一异常边界；不存在 current 时不查询不存在的 submission | 保留输入及文件，错误可见；继续使用原 finally 恢复按钮。 |
| 同一请求安全重试 | 原生 TaskSnapshot、taskSnapshotStorage、submitTask/retryTaskSubmission/getTaskSubmission | 不改 key 生命周期；持久快照始终先于网络写 | 既有测试加回归确认，不生成第二套 receipt。 |

[Web Crypto 规范](https://w3c.github.io/webcrypto/#Crypto-method-randomUUID) 对 randomUUID 指定 SecureContext；远程私网 HTTP 不属于可信 loopback。[getRandomValues 文档](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues) 明确支持非安全上下文且使用密码学随机源。仓库另有 Date/Math.random 的界面临时 ID 降级，不适用于跨重试提交幂等键，故不复用它们。

## 验证计划与交付边界

先在原实现执行新增回归取得失败，再修改并跑既有 NewTask 测试。另用无真实凭据的浏览器 HTTP 非 loopback origin 验证 `isSecureContext=false`、原生 randomUUID 缺失、getRandomValues 可用、实际表单仅发一次带合法 UUID 的 stub POST；错误注入只作用测试随机源，不接触服务端或模型。镜像仅在 kol-stage2 构建，目标 `propr-ui:policy6-http-ui`；构建完成后记录 digest，父流程审阅后负责部署。

## 实际验证与镜像（未部署）

- 原实现：新增两项失败，旧 20 项通过；两项出现未捕获 randomUUID 异常。修复后 NewTask 22/22 通过。
- 实际隔离 Edge、Playwright 1.64.1、HTTP `onticards-http.test:18417`：明确断言 `isSecureContext=false`、`randomUUID=undefined`、`getRandomValues=function`；2/2 通过。使用同一构建镜像提取的静态 UI、原生真实 IndexedDB/同 key retry，服务端全部为已有 upstream fixture。未使用真实凭据或创建 Issue。
- 第一次浏览器执行发现 upstream fixture 对原生 retry POST 的空正文不兼容；仅为测试增加精确 retry 路由。另修正测试文件 CommonJS 的路径计算。最终测试与生产镜像相同，两个测试问题不作为产品失败或额外模型重跑。
- `tsc --noEmit` 的整个 UI 检查未通过：上游 UI Docker builder 未拷贝完整 desktop 源码及 electron 类型，产生 78 行诊断。原实现与修复实现诊断逐字节一致，修改文件无新诊断；不能声称全仓类型检查通过。
- 原生 UI Dockerfile 未改变，kol 构建成功。镜像 `registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-ui:policy6-http-ui`，registry digest `sha256:758a1db30bcaafd4901b0ea8f68f4705001e85628f1fd840b2432b8f2356eb72`，kol image ID `sha256:a4441bd11b4a4bd383857e77c76b65598f4a5bf2384feb825d7dfc998779855a`。
- 独立 agent 审阅未见新增阻断：已有 snapshot 优先、生成失败仍经过 finally、未知 POST 继续查同 key。

完整安全记录：`evidence/new-task-http-validation.json`；22 项红/绿日志、浏览器 JSON 与两张截图。补丁：`deploy/propr-ui-http-compat.patch`。生产改动仅 NewTaskPage 和 UI/package-lock 的既有依赖声明，未修改 frozen app 源码、身份验证或服务端状态。此子任务尚未部署；部署后的实际 New Task 验收由父流程执行。
