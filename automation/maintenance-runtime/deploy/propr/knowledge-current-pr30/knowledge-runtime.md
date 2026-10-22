# OntiCards 当前知识来源与更新方式

核对日期：2026-10-23（Asia/Shanghai）。此文件是新增的运行事实补充；原有历史文档与已部署的冻结知识包保持原样。

当前 main 在真实读取时为 `c8e3dfee68d398a37842fc332f73af40a56f02a7`，tree `99f6c09c69ae8553c62fe223d3eaf6ed650e1955`。实际任务必须继续读取本次 checkout；此处 SHA 是观察记录，不是永久最新值。

| 来源 | 固定版本及作用 | 更新入口与边界 |
|---|---|---|
| 项目事实档案与处理规则 | PR30 commit `10c6862d4c7325c85618f86455aacf9d10c088b5` 的 AGENTS、repository-context、response-policy；三文件现场 SHA256 与 manifest 一致 | OpenCode 原生 instructions 读取版本目录。作为补充知识，不能覆盖实际 checkout；PR30 人工合并后应改用原生项目相对路径，避免长期并载历史副本。 |
| 本次修复代码 | ProPR 原生 fetch/checkout/worktree，任务/PR记录实际 head/base | 每次任务读取同版本源码；失败准备受 policy12 中既有 Git 期限与取消机制保护。外部输入不能改变受信权限/分支/合并边界。 |
| 普通 Issue/PR 的源码上下文 | n8n 2.42.7 原生 GitHub HTTP、Crypto SHA1、DataTable、Loop；`onticardsRepositoryContextV1` | 每个符合条件事件先解析 main 或 PR head，再按同 commit/tree/blob 读取；最多 12 文件、24000 字符、单文件 180 行/6000 字符。显式必需文件缺失则 incomplete；空源文件有 empty 标记。未覆盖路径和部署实况不得推断。 |
| 源版本档案 | 原生源文件 DataTable 的 commit:path/blob/content hash 与 tree 表 | 缓存不可变版本内容，fresh commit 解析充当当前指针；没有额外“最新知识”数据库。source_snapshot 和原生 SHA256 将输入绑定到事件。 |
| 主分支与运行事实 | 每日日报 collector、原生任务记录、独立构建/验收报告 | 日报同时标统计窗口与采集时间；测试报告绑定 head/base，变更后旧通过失效。Git 版本不证明部署版本。 |

真实跨版本验证已完成：8abe → c8e → main，两个修改文件及两个新增迁移文件、22 段实际上下文、29 条缓存均与精确 Git 对象一致，69/69 检查通过。8abe 空 `models/__init__.py` 与 c8e 非空版本被正确区分；必需非空源被预算截断仍拒绝。首次两个失败保留，不以最后结果改写历史。详见 独立交付包中的 `evidence/knowledge-main-refresh-independent.json` 与 `research/knowledge-native-refresh.md`。

PDF 专题另有一次定位不足的失败记录：仅从 `_export_pdf` 入口读取会漏掉前面的转换及失败逻辑。沿用同一 180 行/6000 字符窗口定位到 `_build_and_convert_html` 后，真实 c8e 的 871–1012 行同时包含 HTML/soffice 转换、PDF 无降级的异常与入口调用；7 项独立 Git/摘录检查通过。该内容仅说明当前源码，不能推断运行环境或证明模型回答正确。

现成普通事件流程 `onticardsPersistentDraftsV1` 已 active、5 分钟调度，源码读取与 complete/撤销令牌门禁均已配置；不会为知识另建定时器。既有 Issue29 自然事件确实绑定了 c8e 源版本，但回答审查失败并拒绝发布。该记录只证明来源绑定，不能算咨询验收通过。无新事件时 source reader 不自行做全仓轮询；任务开始与现有日报仍获取各自需要的实际版本。

冻结 PR30 档案中的早期状态应这样理解：

- “尚未验证并发 LibreOffice”是其写入时状态。之后 PR33 head `fdd3f291e8d4a51c31610f13d87670ab3288a6e9` 完成 9 个回归、10 次竞态探针及真实两路 PDF 复验；证据只覆盖并发范围，未合并时不能当作 main 已修复。公开证据：[PR33 固定版本验收](http://10.66.66.5:18123/onticards-reports/acceptance/pr33-fdd3/)。
- 日报采集已改用 systemd LoadCredential 与 PyGithub AppInstallationAuth 的只读权限；早期匿名配额路径不再代表当前配置。私钥不进入模型或公开产物。
- policy12 于 `2026-10-22T18:31:20Z` 部署，镜像 digest `sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa`；独立构建回归 679/679。该测试数只描述底座适配，不是 OntiCards 全产品验收。
- SQL R18 历史失败仍在独立事实档案，不应自动注入每日活动摘要。第三次 10/22 日报因这类全局历史污染及空 Checks 语义错误仍未通过质量审查；原文保留，不再第四次验收重跑。
- 日报随后复用独立原生 alias `onticards-daily-qwen`，`instructions=[]`、同源只读 facts，definition revision13 保留原调度。真实镜像配置解析与 helper READY 已无模型验证；不得据此宣称新 alias 已通过模型质量验收。显式修正版日报独立通过，原生失败原文仍保留。

全仓语义摘要是可选加速层，目前 `summarization.enabled=false`，main/HEAD 原生索引状态均 failed、last_indexed_hash=null。历史 60 条文件摘要、零目录摘要是部分产物，不能称全仓阅读完成。旧预算失败任务在 policy11 下无模型收尾、队列为空；恢复必须由原生显式新任务进行且保持 6 次分析/600 秒共享预算，不自动重开旧预算。本交付不再调用付费索引。

当前说明与证据的来源清单见同目录 `knowledge-source-manifest.json`。模型、凭据、日志原文不属于该清单。
