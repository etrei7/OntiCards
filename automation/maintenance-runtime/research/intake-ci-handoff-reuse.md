# 完整采集向既有 CI 的最小接入（2026-10-23）

实施前检查：18128 已有每五分钟完整单仓采集、原生 Data Table 当前线程及水位、短期 App 读令牌撤销；18132 已有独立可信 CI Webhook / Header Auth / 逐 PR fresh revision guard。缺口仅为两者之间尚无触发连线。没有另加 GitHub 列表采集、Scheduler、客户端、构建器或凭据服务。

复用 n8n 2.42.7 的 [Execute Sub-workflow](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow/)（等待完成）、Execute Workflow Trigger、Data Table、Set、If、HTTP Request 与 Header Auth。上游官方文档于本轮再次核实；实际 node 版本沿用现有实例的 1.3/1.1/3.4/2.2/4.4。新增配置只完成有界字段投影、完整水位/撤销/新鲜度门禁及现有子流程调用。

上游真实 `kind` 为 `pull_request`，不是 `pr`；snapshot 只有 head/base SHA，没有 head_repository/head_ref/base_ref。仅向 CI 投递 `{pr,head,base,state}`，这些元信息必须由 18132 既有 fresh revision guard 再核实，不以缺失字段默认为同仓。正文、讨论、认证头、App token 均不传给 CI。最多 20 个 open PR，超过则拒绝整批，不截断。

配置默认 `dry_run`；原采集末尾仅在完整水位成功落盘且令牌已撤销时调用。内部 POST 不重试，CI 原有版本 admission/receipt 负责去重和未知请求处理。采集成功不等于 CI 构建成功，两个结果分别记录。

并发边界：生产实例配置 `N8N_CONCURRENCY_PRODUCTION_LIMIT=1`，Data Table Get→Upsert 不是跨实例 CAS。既有顺序回放不能冒称并发实测。关闭/重开 timeline 为上下文事件，不作为真人新问题自动消费；真实普通会话语义成功仍以单独实测结论为准。


## 实际多行 fanout 缺陷与修正

02:21 首个常驻dry_run实际把29个线程item各投一次同批snapshot。既有Set节点默认逐item；新增投影已调用`.all()`聚合却漏了`executeOnce=true`，后接HTTP因此29份重复。原13项fixture只有单row，不能检验此问题。已有n8n原生executeOnce即满足需求；02:23:53只调整child的Project/HTTP/安全结果节点配置，不改scheduler/客户端，不清CI状态。原失败在rootless-runtime/intake-first-native-dry-run.json，27个尚未运行的重复receiver经原生停止；首批PR30/26/33验证分别到既有validation_only出口，0SSH、0模型、未消耗CI回执。

回归沿用既有build/run_serial_loop_probe，输入2个真实原生SplitOut item，克隆当前Project和HTTP节点，目的地只替换为隔离loopback的DataTable计数Webhook；必须投射1item/HTTP1item/remote计数1。另21个open PR必须整批拒绝而非截断。此项通过前不把配置升级等同真实修复，不切正常dispatch。隔离fixture首次import失败也保留；静态检查发现并修正了重复节点ID。随后确认CLI import的当前版本不等于原生published版本，因此测试必须等启动/依赖索引完成，显式publish --versionId，并比较实际published节点与connections；不能把旧定义的响应算作新代码验收。


02:34:40最终原生fixture15/15通过，publishedVersion=6efd99f5-719a-4737-9b28-cc73348bdb8d，实际49节点/连接与文件SHA a29732dda5cb5762f4ec68d5bce8211b9bf9013d79fb47be22ab802e7f558070一致。2行投影、HTTP和计数各1；21行整批拒绝。修后自然25分仅receiver241，3个既有CI validation_only成功，无模型/SSH。02:35:24切受控consumer trusted_mode=dispatch；是否启动/跳过/预算拒绝以18132原生admission回执为准，不因配置已启用而声称构建通过。
