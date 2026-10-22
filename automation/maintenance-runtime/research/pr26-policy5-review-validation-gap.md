# PR26 policy5 审查产物失败：真实证据与最小修复依据

2026-10-22；Task `pr-comments-batch-stepll2026-OntiCards-26-1792672304792-6340804900`。模型传输完成、API返回success、GitHub评论成功创建，不等于审查产物有效。本轮正式审查44.372秒，input28874/output1229；scout64.568秒，input18488/output1392/cacheRead39424。USD未知。原生后台误记 completed/reviewsPosted=1；不得作为AC审查通过。

真实App评论6340882455只发布 `Review output was invalid and could not be displayed safely.` 加元数据及 `/fix` 引导，没有合格审查结论。见 `../evidence/pr26-policy5-published-review.json`、`pr26-policy5-native-review.json`。原始助手输出有3004字符，SHA256 `2899d141d365de7983d73167928ba8a88617c449eb4998526de332b53dd633c9`，单独保存在 `pr26-policy5-invalid-review-response.json`，已检查不含模型key；没有导出原prompt、环境或运行日志。

## 现成能力与确切缺口

- `reviewOutputParser.ts::parsePublishableReview` 已实现严格校验，`reviewCommentFormatter.ts::effectiveReviewScore` 复用它并保留现有 legacy suggestion normalize。无需扩展schema或新建语义审核器。
- 原始输出使用 `### F1`、`### S1`，缺 `: title`；F字段为File/Problem/Evidence/Fix，缺原生必需 violatedRequirement、introducedByPR、requiredForMerge、minimumCorrection。原生 parser正确拒绝，不能自动猜补权限/合并条件。
- `buildReviewComment` 在校验失败时用普通成功review外壳包裹invalid占位和/fix引导。`buildReviewCommentWithReservedRecordRanges` 将该占位的0 findings当正常返回；`prReviewRunner.runSingleReview`仍保留Agent的success=true，POST后交给后续任务/metrics投影，所以policy5已有provider failure修复没有覆盖“provider成功、结构失败”。
- 必须在runner发布前复用同一有效性入口；无效时保留原response、tokenUsage、session、耗时，标本轮analysisResult失败，再走既有error-comment/FAILED任务路径。不得throw进会清零耗时并丢掉usage的通用catch，不能放宽parser、伪造missing fields或新增自动模型重试。

## 人工质量审阅

原文F1承认当前PDF路径不触发，且 `_FILTER_MAP` 是PR前已有代码；不能作为本PR引入且必需修复的blocker。S1声称patch.object目标改名会“静默失效”不成立，默认create=False会报AttributeError。行号也与固定文件位置不符。这些内容人审拒绝，不能仅自动修正标题/字段后发布。原生提示已要求严格字段和只报告本PR引入的必要修复；本轮不是“完全没有格式约束”。改善应使用已有 `settings.pr_review_prompt` 配置提供简短中文有效示例、明确证据范围与验证来源，保持上游末尾强制schema；不增加另一轮自动修复或伪造新模型成功。

## UI日志与token显示待核实

真实execution2有sessionId及28874/1229用量，但history_id=NULL，五条Task history均无sessionId，故taskHistoryRoutes按history/session关联不到这条execution。liveDetailsRoutes已有按task查session及completedExecutionDetails读取持久详情的fallback，应先验证此现成路径/刷新，而非直接重写UI。当前记录不能把UI的0当真实用量。

## policy6 局部修复与无模型验证（已完成，等待统一部署）

生产只改 `src/jobs/prReviewRunner.ts`：provider返回成功后复用现有 `effectiveReviewScore(response, { changedFilePaths })`；结构无效就保留原始response、session、usage和耗时，将本轮analysisResult标失败，再走原生错误评论/FAILED路径。没有放宽parser/schema，没有自动模型重试。未知账单仍未知。原始无效输出没有转换后发布。

真实fixture red 4项中2失败、exit1；修复后5测试文件合计31/31、0skip、exit0（7.523秒）。覆盖真实无效response、有效clean、缺字段/文件证据范围、provider failure及原预算/Follow Up/metrics/formatter回归。旧成功fixture仅改成合法四段原生格式。见 `../evidence/pr26-policy6-review-validation-tests.json`。这不等于下一次真实模型审查已经成功。

`../deploy/propr/configure_review_prompt.mjs`（默认只读、显式 `--apply`）与 `review-prompt-zh-supplement.txt` 使用原生 `settings.pr_review_prompt`，保留 `DEFAULT_REVIEW_GUIDANCE`，追加简短中文证据范围和虚构最小合法F/S例子。例子用原生parsePublishableReview静态验过1F/1S，不调用模型；尚未应用。上游强制schema仍由原生builder末尾追加。本轮真实prompt长81,262字符且已包含全部必需字段和标题格式，故修复没有将问题归因为“原本缺少格式要求”。

## UI原生回退读取实证（只读）

2026-10-22T12:57:48.898Z，在当前policy5 API容器中对同一任务直接调用现成getTaskHistory/getLiveDetails（SQLite query_only、只读Redis）。history返回200且5项，但0项execution关联、0项token；live-details返回200、1个thought，原文SHA与失败产物一致，用量input28874/output1229。见 `../evidence/pr26-policy5-ui-projection.json`。因此持久原文/用量仍可由现成fallback读回，下一步应先在原生UI刷新并重选最新Run3，不为此重写任务系统或篡改旧终态。

本探针没有执行浏览器刷新，也没有证明浏览器当前缓存已恢复。原生live-details把缺失cache字段归零，不能解释成供应商明确报告cache=0。第一版探针的Express响应替身缺type/send导致探针history500；补齐替身后200，这不是产品API故障。没有修改生产源码、任务、队列或Github数据。
