# OntiCards 仓库事实与基线（2026-10-22）

本记录来自本地实际源码、只读基线和已核实官方文档。以下初始盘点保留为8abe历史，不代表当前main；当前结论以下方更新为准。状态只覆盖实测范围，不代表全系统已通过。

## 2026-10-22 18:00 当前事实更新

当前核验 main 为 `c8e3dfee68d398a37842fc332f73af40a56f02a7`。8abe→c8e的7个变更路径涉及元数据作用域、入口、迁移扩展、Alembic0001_baseline、自检、SOP及models导入；PDF组合完整保留这7个blob。原来“未发现版本迁移文件”及环境文件物化描述仅适用于8abe，不能套用到当前入口。

[草稿PR #26](https://github.com/stepll2026/OntiCards/pull/26) 的 `3105b7b61469c6b2945357f2eefa8fcb2e3aaee5` 基于c8e，cherry-pick既有f076/f553保作者，仅3文件，最终blob与已验证修复一致。打包机原Dockerfile镜像digest `sha256:793385f53e61fc8b753d1c41055ed5d96894f76f0dffc3d8509c9faa952e7996` 已在独立 `http://10.66.66.5:18111` 运行。真实soffice3/3、API7/7、Playwright3/3及9截图；API1页、多规则3页、失败样本/关系2页PDF完成文字与视觉验证。迁移运行到0001_baseline/28表，自检5通过1跳过（缺three_way_check.py）；并发导出与全方言未验。完整证据：`deploy/evidence-pdf-current-main/manifest.json`。此为独立复用验证，不是Issue25后台成功；后者尚在基础设施失败阶段。

SQL三轮模型候选已被独立审查否决，R18未修复，原扫描器未改。全局方括号/双引号mask会遗漏PostgreSQL数组、下标及dollar字符串场景中的真实表；两个调用方白名单受影响，真实PG15.18探针已证实。sqlparse0.6.0默认lexer也不足以直接替代安全边界。禁止沿用下列历史“局部屏蔽”建议；后续先明确dialect设计，保留真实表不漏报。详见 `research/sql-candidate-review.md`。

## 身份与版本

- repository: `stepll2026/OntiCards`
- remote: `https://github.com/stepll2026/OntiCards.git`
- 审计起点 branch: `main`
- commit: `8abe9e20d58df2605b8a66c3a4296d3dcfe325a2`
- 许可：根目录 `LICENSE` / README 标识 AGPL-3.0。
- 源码目录：`outputs/onticards/repo`。读盘时 git status 为空。
- 未发现 AGENTS.md、工作流目录 `.github/workflows`、pytest 配置或 Playwright 配置。`.github` 有 Bug/功能/部署/安全 Issue 表单，可直接复用，不能据此推断服务器或 GitHub 平台没有另配自动化。

## 已有结构与可复用能力

| 范围 | 事实文件、职责与依赖 | 接入方向 |
|---|---|---|
| 前端 | `OntiCards_Web/package.json`，Next.js 14.1.3、React ^18、Ant Design；`app/[lng]` 包含登录、工作空间、定向/全域盘点、问数、治理、审计、监控、用户与设置；`yarn.lock` 已存在 | 沿用 Yarn 冻结锁文件、`yarn build`/`yarn lint`，不更换前端技术栈 |
| 后端 | `OntiCards_Api/app.py` 创建 Flask 应用；`controllers/__init__.py` 注册蓝图；Flask 2.3.3、SQLAlchemy 2.0.36、gunicorn 21.2.0 | 沿用现有 API 与进程入口 |
| 身份 | `controllers/user/userManagement.py` 暴露 `/console/api/login`、`/user` 等；`core/passport.py`、`extensions/ext_login.py` 处理身份；独立 `/sso` 蓝图 | 测试合成账号的登录成功/失败及未授权 API；不另造认证 |
| 数据源/元数据 | `controllers/datasource`、`models/datasource_infos.py`、`models/user_datasource_schema.py`；已有多方言适配 | 只在独立合成数据源验证连接、元数据读取 |
| 数据卡片 | `controllers/datacard/data_card_tool.py`，`/console/api/datacard_tool`，关联 Weaviate | 保留生成/更新与检索既有实现 |
| 问数 | `controllers/query/query_by_datacards_agg.py` 及 plugin 入口，共用 `sql_from_guard.py`、`sql_join_utils.py`、`sql_prompt_loader.py` | 测试复用真实入口；修复尽量落在共享模块 |
| 治理/导出 | `controllers/governance/governance_api.py` 已有规则、执行、报告生成/状态、下载；`models/governance_*` | 对合成规则运行/导出添加业务断言，不重写报告功能 |
| 数据与初始化 | PostgreSQL；`app.py` 调用 `ensure_database_initialized`，空库执行 `init.sql`；`migrations` 有 Alembic 框架但未发现版本迁移文件 | 测试使用独立空库，禁止连接已有生产业务库；记录真实初始化结果 |
| 容器 | 根 `docker-compose.yaml` 含 Postgres 15-alpine、Weaviate 1.36.0、API、Web、Nginx；API/Web Dockerfile、多阶段构建、healthcheck、restart 已有 | 复用 Compose 和 Dockerfile；在打包机构建，10.66.66.5 仅接收镜像并测试 |
| 环境 | 根 `.env.prod` 以及可选 `.env`；API entrypoint 已把容器环境写入权限0600的内部 `.env`；DB/Weaviate Docker DNS由Compose覆盖 | 新增测试环境配置，仅使用合成账号/密钥；不得提交真实 `.env` |
| 业务定时 | `run_scheduler.py`、APScheduler 3.10.4 为业务数据清理；此脚本并非仓库运营调度器，Compose 未显式启动它 | 保留现有业务定时，不把它改写为另一套仓库通用调度 |
| 文档/知识 | README 三语、CONTRIBUTING、SECURITY、前端docs与模型提示词已存在 | 知识初始化以这些事实为基础追加版本化运行说明，不另建向量知识平台 |

## 隔离部署需要的配置缺口

1. 根 Compose 显式 `networks.onticards.name: onticards`，会绕过 project name 的网络前缀。仅 `docker compose -p task-id` 不足以隔离。必须用测试 override 给网络唯一名称，验证 `docker compose ... config` 最终结果。[Docker 网络name语义](https://docs.docker.com/reference/compose-file/networks/)
2. 绑定卷 `./volumes/postgresql/data`、`./volumes/weaviate/data`、`./volumes/governance/reports` 必须位于独立任务目录或改为独立命名卷。不能引用既有服务数据目录。
3. API/Web `pull_policy: build` 会触发构建，测试机应使用覆盖配置和已在打包机生成的唯一镜像标签/digest，并显式 `--no-build`。这属于现有配置调整。
4. Nginx 默认主机端口9107，可用 `NGINX_HOST_PORT` 配置；已有端口占用由环境盘点核实。
5. `next.config.js` 已设置 `eslint.ignoreDuringBuilds: true` 和 `typescript.ignoreBuildErrors: true`。因此 build 成功不代表 lint/typecheck 通过，必须分别记录。保持原状不代表认可为新检查的替代。

## 只读基线结果

实际命令：`python outputs/onticards/research/baseline_probe.py`，退出码1。

- Python 3.10.8 对148个Python源文件执行 `ast.parse`，语法失败0。
- 普通显式JOIN扫描、字符串中的假FROM各1项通过。
- 双引号表名/列别名包含FROM的2项回归探针失败。
- 真实内存SQLite建表和查询成功返回 `[[7]]`；失败来自现有扫描器返回额外不存在表名，不是捏造SQL预期。
- 原始机器可读结果：`baseline-results.json`；可重复脚本：`baseline_probe.py`。
- 此脚本只导入不依赖应用的扫描模块，不导入 Flask 应用，不读取凭据、不访问网络/生产数据。
- 前端构建、lint、类型检查、容器、API、浏览器、模型均尚未由本子任务执行，不能记为通过。
- 现有 `controllers/governance/test_report_libreoffice.py` 是独立手工导出脚本，会在源码目录生成报告，不能当成现成完整pytest套件。`test/` 主要是模型连接手工脚本、NL2SQL用例文档和SQL数据。

## 历史 SQL 候选调查（已否决，不是实施建议）

需求：扫描 SQL 的 FROM/JOIN 表引用时，忽略引用标识符内部的关键字。

重现：在 SQLite :memory: 创建 `"sales FROM archive"` 并写入7；`SELECT amount FROM "sales FROM archive"` 实际返回7。现有扫描器却返回 `['"sales FROM archive"', 'archive']`。`SELECT 1 AS "FROM phantom" FROM orders` 同样产生虚假 `phantom`。

位置：`OntiCards_Api/controllers/query/sql_from_guard.py:182`。Step1只标记单引号字符串，Step2正则扫描全部FROM/JOIN，未排除双引号/反引号/方括号标识符内部。两个问数入口都调用此共享模块。该记录只确认扫描结果错误；完整问数API的具体错误响应仍待集成测试，不能写成已验证。

历史初选曾提出保留扫描器并扩展引号屏蔽；该结论已被后续跨方言真实探针推翻，不得实施。已检索 [SQLGlot](https://github.com/tobymao/sqlglot) 和 [sqlparse](https://github.com/andialbrecht/sqlparse)；当前不是缺一个解析框架，而是已有共享实现的局部缺陷。更换解析器会扩大两条查询路径的方言和白名单行为变更，不符合本次最小修复范围；不能把该理由写成这些库不支持。SQLite官方明确定义双引号标识符，并支持方括号/反引号兼容形式：[引用规则](https://www.sqlite.org/lang_keywords.html)。

当前决定：本轮停止SQL候选修改，保留失败证据；未采用任何候选生产代码。未来工作不得减少现有白名单安全断言。

### 候选版本和修复语法边界补核

- SQLGlot：PyPI 30.24.0（2026-10-20发布），MIT；tag `v30.24.0` 对应 `5d588c0f32d17a08191898638f67ff27bb0a13ff`。文档表明可按方言解析AST并找表；若未来替换应先覆盖项目现有各数据库方言再迁移。本次尚未安装/运行，不能写成已实测不适配。
- sqlparse：PyPI 0.6.0（2026-08-13发布），BSD-3-Clause，已读取tag对应LICENSE；tag `0.6.0` 对应 `5172fd0b3c5fec4a4587c2c14a29c53225c9915d`。它是非验证型token树解析器，需要项目自己的表引用遍历/白名单适配，不能直接代替所有安全校验。本次尚未安装/运行。
- 来源：[SQLGlot PyPI](https://pypi.org/project/sqlglot/30.24.0/)、[sqlparse PyPI](https://pypi.org/project/sqlparse/0.6.0/)、[sqlparse LICENSE](https://github.com/andialbrecht/sqlparse/blob/0.6.0/LICENSE)。具体metadata保存在 `sql-parser-candidates.json`；GitHub `/releases/latest` 不可用后使用PyPI和 `git ls-remote --tags --refs` 核实，不把接口失败记成工具缺能力。
- 首个整体验证更适合用普通物理表配带关键字的列别名：`SELECT amount AS "FROM phantom" FROM orders`。带空格物理表名还会触发调用方 `raw_tbl.split()[-1]` 的另一项规范化限制；不能只修扫描器就承诺所有复杂表名均已端到端支持。
- 原初选仅列引用标识符、转义及JOIN/子查询覆盖，遗漏了 PostgreSQL 数组/dollar字符串等方言冲突，不能再作为可实施的修复边界。
- sqlparse后续已进行14个独立lexer探针；其默认规则同样存在跨方言漏真实表。当前未引入依赖，未继续修改；任何后续方案需明确dialect接口后重新核实。
