# OntiCards 仓库事实档案

核对日期：2026-10-22；repository：`stepll2026/OntiCards`；初始 main：`8abe9e20d58df2605b8a66c3a4296d3dcfe325a2`；2026-10-22 18:00 发布前后回读的 main：`c8e3dfee68d398a37842fc332f73af40a56f02a7`；已验证 PDF PR #26 head：`3105b7b61469c6b2945357f2eefa8fcb2e3aaee5`。本档案只描述已检查的结构；执行任务时必须读取实际checkout，不能把此处基线当作最新提交。

## 已有产品与模块

产品覆盖数据源连接、元数据盘点、数据卡片、自然语言问数、数据治理及报告导出。前端是Next.js14.1.3/React18/Ant Design；API是Flask2.3.3/SQLAlchemy2.0.36；已有PostgreSQL15和Weaviate1.36.0 Compose服务。

|路径|职责与接入点|
|---|---|
|`OntiCards_Api/app.py`、`controllers/__init__.py`|Flask创建、数据库初始化及蓝图注册|
|`controllers/user/userManagement.py`、`core/passport.py`|登录与用户权限；复用现有身份逻辑|
|`controllers/datasource`、`models/datasource_infos.py`|数据源及连接配置|
|`models/user_datasource_schema.py`|盘点元数据|
|`controllers/datacard/data_card_tool.py`|数据卡生成/更新与Weaviate关联|
|`controllers/query/query_by_datacards_agg.py`及plugin入口|两条问数路径，共用SQL扫描与校验模块|
|`controllers/query/sql_from_guard.py`|已有FROM/JOIN表引用扫描器；引号标识符关键字误识别已复现|
|`controllers/governance/governance_api.py`及报告导出模块|质检、报告生成、状态及下载|
|`OntiCards_Web/app/[lng]`|登录、工作空间、盘点、问数、治理、审计、监控和用户设置|
|`docker-compose.yaml`、API/Web Dockerfile|现有五服务部署；不另造产品运行平台|
|`init.sql`、`migrations`|8abe 是 Alembic 骨架；c8e 已增加 `0001_baseline`、部署自检和迁移 SOP，启动入口支持执行迁移|
|`run_scheduler.py`|产品自己的业务清理，不作为仓库运营调度器|

## 测试基线与可复用命令

前端沿用Yarn锁文件和`yarn build`/`yarn lint`；另外运行`yarn tsc --noEmit`。已有Next配置在build时跳过lint和类型错误，所以build成功不代表静态检查通过。初始独立lint因缺少TypeScript ESLint规则失败；类型检查有3处现有cloneElement/style TS2769错误，不能由本任务的其他测试成功掩盖。

后端148个Python文件通过语法解析。没有现成完整pytest或Playwright套件，因此只补OntiCards业务spec，测试运行器使用pytest9.1.1与Playwright1.64.1。实测合成SQLite数据源→元数据→真实模型数据卡→1024维向量→问数SQL返回250；卡片编辑、质检、XLSX/DOCX/MD导出通过。历史 PDF 先因缺 LibreOffice 返回500，补环境后出现5页破版。现已复用 `_build_docx_with_python` 与现有 soffice 转换，在 PR #26 修复版式及依赖；3105 在当前 main c8e 上完成3项真实转换回归、7项API、3项浏览器验证、9张关键截图。真实PDF单页、45规则三页和失败样本/关系两页均通过文字、边界和逐页渲染检查。完整证据位于部署交付包，不把截图替代API断言。

SQL扫描器最小复现：SQLite `orders(amount)` 中一条7，`SELECT amount AS "FROM phantom" FROM orders` 可执行，但现有扫描器额外返回`phantom`。本轮三次模型尝试后的生产候选已被独立审查否决，R18仍未修复；禁止继续采用全局方括号或双引号屏蔽建议。PostgreSQL数组/下标中的真实子查询、dollar字符串中的引号会使候选漏掉真实表，两条生产调用方的白名单均受影响。sqlparse0.6.0默认lexer也有跨方言遗漏，未接入。后续必须先明确dialect接口并保持真实表不漏报；不能用窄示例通过换安全退化。证据见交付包 `research/sql-candidate-review.md` 和真实 PostgreSQL15.18探针。

## 部署与凭据边界

镜像在`kol-stage2`打包，测试机`10.66.66.5`只加载或拉取已构建镜像。历史 f553/8abe 预览保留在 `http://10.66.66.5:18110`、`/opt/onticards-maintenance/preview`。当前 main + PDF 3105 独立预览在 `http://10.66.66.5:18111`、`/opt/onticards-maintenance/preview-current-main`，project 为 `onticards-maintenance-current-main`。基础Compose有显式网络名`onticards`与`pull_policy: build`，测试override必须覆盖网络/卷/端口以及构建策略，并用`--no-build`。镜像架构必须检查为linux/amd64；已有错误arm64镜像曾导致启动失败，已保留失败证据。

维护日报位于`/opt/onticards-maintenance/reporting`，状态由专用低权限用户保存到`/var/lib/onticards-report`；原生systemd在北京时间00:00采快照、09:00补报，flock排他、15分钟超时、30天文件保留。SQLite payload为日报事实源，中断后重建文件，已完成窗口不重复采集。App私钥不进入日报进程；若匿名额度不足，使用独立只读短期令牌。

自动修复主底座选ProPR锁定源码`42931b1502eb03ac299f14e306811736fab51eb4`，复用OpenCode和其原生队列、任务、Git工作区与发布流程。部署策略补丁仅补实例级禁止最终合并、受控分支、禁止Agent可写令牌及测试机禁止build。该策略从受信宿主环境读取，不接受Issue/PR文本覆盖。

## 当前 main 组合的实测边界

8abe→c8e 共7个变更路径：`core/metadata_scope.py`、`docker/entrypoint.sh`、`extensions/ext_migrate.py`、`migrations/deploy_check.py`、`migrations/versions/0001_baseline.py`、`migrations/上线迁移SOP.md`、`models/__init__.py`（均在 API 目录）。3105 保留这7个blob；仅复用原PDF修复的3文件。

API镜像 digest 为 `sha256:793385f53e61fc8b753d1c41055ed5d96894f76f0dffc3d8509c9faa952e7996`，在打包机构建、5机 `--no-build` 启动；Web复用8abe镜像，因完整Web tree与c8e/3105完全一致。新的启动入口使用容器环境并监听内部9103，运行迁移后数据库为 `0001_baseline`、28表。原生 `deploy_check.py` 5通过1跳过：缺少 `scripts/three_way_check.py`，不能称三线schema验证完成。未测试并发LibreOffice或全部数据库方言。

[草稿修复PR #26](https://github.com/stepll2026/OntiCards/pull/26) 是独立复用已有修复并验证的结果，不是 Issue #25 原生后台成功；后者在克隆基础设施阶段失败、未执行编码Agent。完整版本绑定证据在交付包 `deploy/evidence-pdf-current-main/manifest.json`、README及截图目录。最终合并由维护者操作。

## 更新方式

任务开始记录实际head/base/tree，读取本次涉及模块及其现有文档。主分支变化时更新受影响事实；在任务结果中列出文档版本和测试版本。运行报告、模型用量和测试证据必须绑定实际SHA；旧head的通过记录不能用于新head。
