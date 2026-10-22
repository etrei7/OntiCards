# 固定版本 Check 与失效处理复用

GitHub Check Run 绑定 commit，base 更新不会自动让已有 success 失效。现有 n8n 原生 Schedule Trigger、DataTable、JWT、HTTP Request 已实际使用；复用这些节点定期比较登记的 PR/head/base 和 GitHub 当前值，再用 Checks API PATCH 将旧 Check 标成 `action_required`。不新建调度器，不重新执行测试，也不改变任何分支/合并。

来源：[GitHub Checks REST](https://docs.github.com/en/rest/checks/runs?apiVersion=2026-03-10)，2026-03-10 API；n8n 2.42.7 已锁镜像。App 已批准 Checks write，无新增权限。只为此子工作流签发 OntiCards 单仓 `checks:write/metadata:read`（版本读取另用原生子工作流独立`pull_requests:read/metadata:read`） 短 token，核 scope，执行后撤销；不传给 PR 容器。读取或撤销未知不能生成新的 success。

注册入口必须是已有受信 Header Auth Webhook，登记 Check ID/head/base/name/external_id，并真实 GET 验证 App ID5422414、head/name/external_id完全一致；不可仅信任调用方字段。原始证据继续保留，失效后提示当前版本需要重新验证。PR33 登记仅用于版本失效，不调用 PR26 的独立测试控制器。实际18+8+8原生节点、20 Code断言通过；PR26 Check119988255661/PR33 Check119950685976已登记。5min自然trigger17:45:36复查PR33 current、token撤销；neutral synthetic-base119966580036真实PATCH200/GET200并独立读回action_required，0模型/test/ref写。首次PATCH表达式及Code passthrough格式失败保留，修复复用原Code节点投影与HTTP JSON参数。原始证据保留；网络失败不保证即时失效，5min观察窗口如实说明。
