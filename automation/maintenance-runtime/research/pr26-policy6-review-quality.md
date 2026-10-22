# PR26 policy6 真实审查：失败已正确投影，产物未通过

Task `pr-comments-batch-stepll2026-OntiCards-26-1792674184541-6341426679`；2026-10-22T13:03:15.502Z创建，13:05:37.608Z原生FAILED。review输入28876/output830，56.183秒；scout输入6194/output649/cacheRead4096，27.575秒。USD未知。队列reviewsPosted=0/reviewsFailed=1，所有活跃/等待状态为0。无后续模型重跑。

原生公开[失败评论6341479762](https://github.com/stepll2026/OntiCards/pull/26#issuecomment-6341479762)只说明structured contract失败、marker error=true，没有发布findings或/fix引导。原始助手输出已保存在 `../evidence/pr26-policy6-review-response.json`；任务与用量见 `pr26-policy6-native-review.json`；公开评论见 `pr26-policy6-published-review.json`。

## 配置确实进入本次模型输入

持久user prompt为93,531字符，SHA256 `fc10a86b674992eccb67aaf3a4d62fb21370e935b05be7982e3419e250adef64`。实际包含“中文审查补充约定”、虚构src/example.py示例，以及violatedRequirement/introducedByPR/requiredForMerge/minimumCorrection、### F1:/### S1:等全部必需字段。本次不是配置字段未使用或缓存仍旧提示。没有导出完整prompt/原日志/凭据。

## 结构和事实均不合格

模型仍使用英文段落F1./F2./S1.而不是原生### F/S标题，不提供必需字段。Score8/10同时把F描述为“defensive improvements rather than correctness blockers”，与原生F必须合并前必要修复的语义冲突。门禁正确拒绝，不应把这些文字强凑成schema后发布。

事实核验：F1称未显式声明lxml，固定head3105的 `OntiCards_Api/requirements.txt` 实际明确 `lxml==5.3.0`，因此该发现错误。F2猜测未来python-docx变更namespace解析，却没有当前PR触发故障证据，不能作blocker。S1一面承认现有120秒timeout，一面说可以无限挂起，没有提供绕过该timeout的真实路径。其余建议也不能弥补不合格格式和错误F。此次可验收的是“无效产物正确Failed、错误公开、usage/raw保留”，不是“代码审查功能产出有效结论”。

## 边界观察及限制

只读observer在13:05:11开始，捕获当时仍运行的review容器1个；scout此前已结束，未捕获其Docker inspect。数据在 `../evidence/pr26-policy6-review-boundary.json`。沿用受限网络/只读repository挂载，无Docker socket/App私钥挂载，token仅记录存在布尔。Config.User=0:0是容器启动用户，不能证明模型进程实际UID。父流程要求停止后observer收到精确SIGINT并退出（KeyboardInterrupt，exit1），没有停止任务或沙箱。因为旧observer未实现signal收尾，原JSON没有finishedAt；此处补充停止来源，原记录不改写。后续Issue observer将只读docker top/proc status捕获实际UID。

## 后续可复用配置（只研究，未应用、未调用模型）

`src/jobs/reviewRuntimeSettings.ts:15–36` 每次任务读取原生settings：pr_review_context_enabled=false关闭额外scout；pr_review_max_context_tokens设绝对上限（0为无上限），pr_review_context_budget_percent设模型安全容量比例。`reviewPromptBuilder.ts:249–264` 已有按序裁剪，先移除scout、评论历史、整文件副本，再裁diff，最后才裁目标/当前指令/override；有显式partial说明。可以先以8k–12k候选上限离线静态核对section tokens及完整3文件diff是否还在，再决定是否真实验收。尚未进行这次预算模拟，不能宣称质量已改善。

现有模型配置enable_thinking=false已通过native-request-shape.json的本地mock验证透传。百炼[官方Chat Completions参数](https://help.aliyun.com/en/model-studio/qwen-api-via-openai-chat-completions)列明qwen3.8-max-0902支持reasoning_effort或thinking_budget，两者不可同时设置；[深度思考说明](https://help.aliyun.com/zh/model-studio/deep-thinking)及[OpenCode模型选项](https://docs.opencode.ai/docs/models/)提供原生配置入口。若之后选择开启思考，应独立评估成本/600秒期限，不能把参数更大等同于修复幻觉。此版本OpenCode为1.18.31，继续使用其provider.models.<id>.options形式；不要照抄不同主版本的v2 providers/settings格式。未修改reasoning配置、未调用额外模型。
