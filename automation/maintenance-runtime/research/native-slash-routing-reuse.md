# R03/R07：普通咨询与原生命令分流

2026-10-23。root发现具体重复消费缺口：既有n8n只过滤Bot和AI标签，ProPR MCP使用已授权账号发表的 `/review` 评论是User身份、PR未必有AI标签，可能再次触发普通咨询模型。

先核现有实现与上游 [slashCommandParser.ts@42931b1](https://github.com/integry/propr/blob/42931b1502eb03ac299f14e306811736fab51eb4/packages/core/src/webhook/slashCommandParser.ts)：原生命令为review/fix/merge/switch/use/ultrafix，区分大小写，仅原始首行trim后识别，不能跳过前置空行；参数中内嵌CR/U+2028/U+2029拒绝。`commentEventHandler.processCommentEvent`用于PR discussion/inline comment；`packages/api/mcp/reviewModels.ts::postModelReviews`原生formatter将 `/review <model>`放首行，随后instructions和propr-mcp marker。原生角色/仓库授权仍由ProPR处理，marker本身不授予权限。

最小适配只在现有 `Project deterministic routing observations` 的Set表达式中加入原生parser的布尔投影，并将这些PR comment标为 `native_slash_command_context_only`。独立n8n镜像没有ProPR模块挂载，因此不调用另一个服务解析，不引入新的命令解释器或执行入口。匹配只跳过普通咨询模型，不接受任何comment为执行授权；常规人类材料仍按原门禁，已有pending/原稿/29与31封存及预算保持。

新增无模型验证沿用现有conversation budget native fixture，使用原生formatter离线捕获的MCP正文、普通补充、近似命令、marker-only、pending及29/31边界。离线formatter transport为明确内存stub，绝无GitHub评论或模型；未将fixture正文声称为已经公开发表的MCP评论。


03:16实际原生fixture 9/9通过：formatter `/review`、`/fix`、`/ultrafix`仅context；近似命令、单独marker、开头空行、正常人类材料保持原行为；pending reservation与29/31封存原值不变。03:19:34只更新常驻45节点draft的既有routing Set，active版本 `2b95ea32-3719-4cb5-8b5b-ca5ae7a6cf1f`，其余连线、开关和DataTable未改，0模型/公开发帖。证据 `evidence/n8n/native-mcp-slash-body-fixture.json`、`native-slash-routing-probe.json`、`native-slash-routing-deployment.json`。这不替代真实普通咨询语义闭环，也不宣称已有实际MCP评论。
