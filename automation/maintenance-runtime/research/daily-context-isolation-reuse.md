# 日报全局上下文污染：复用配置隔离

2026-10-23，第三次真实日报仍把通用编码知识中的SQL R18写进只允许当前事实的日报，独立质量复核拒绝；同时把已获取的空Checks列表写为未知。原文和用量保留，不做第四次同日验收调用。

先核查ProPR固定上游的Agent registry、Agent definition.agentAlias及OpenCode configPath：同一原生registry支持多个配置，每个definition可选择alias，不需要新增Agent循环或更换框架。OpenCode[配置规则](https://opencode.ai/docs/config/)说明全局配置与instructions会进入上下文，[规则说明](https://opencode.ai/docs/rules/)确认全局AGENTS适用于每个session。因此本次采用已有原生配置隔离：新增日报专用alias，仍用同一OpenCode1.18.31镜像、同一供应商及模型，独立最小config目录，instructions为空，不复制全局知识或历史会话；沿用现成systemd只读事实bind和同一个输入helper。编码alias保持原配置。

验证为无模型的真实Agent镜像读取合成/真实事实及`opencode debug config`解析，只导出provider名称、instructions和只读挂载元数据，不打印key。原生definition只更新agentAlias，Schedule、模型、权限均保持。此验证证明配置不再加载通用知识，不证明未来模型语义百分之百正确。空Checks语义错误的原始结果保留，交付提供明确标注的复核修正版；正式定时输出仍需按A—F和来源质量检查。

新增内容仅部署配置、原生store调用及无模型验证脚本；不增加调度、采集或模型循环。重跑初始化不能覆盖现有agents列表。失败出口是保留原始报告与质量记录、停止同日验收尝试并交维护者，不通过删历史或伪造native completed质量来变绿。
