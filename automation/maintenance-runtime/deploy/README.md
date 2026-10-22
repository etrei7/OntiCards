# OntiCards 测试部署与交付入口

本交付以10.66.66.5测试运行实例为准，镜像构建仅在kol-stage2。复用ProPR/OpenCode、n8n、GitHub App/Checks、systemd、现有Docker/Compose及pytest/Playwright；新增适配对应矩阵中的具体缺口，未重写业务架构。

- [完整交付门户与下载包](http://10.66.66.5:18123/onticards-reports/acceptance/maintenance-20261023/)
- [维护系统](http://10.66.66.5:18123/)与[事实日报](http://10.66.66.5:18123/onticards-reports/)
- [PR26精确版本真实业务验收](http://10.66.66.5:18123/onticards-reports/acceptance/pr26-rootless-3105/)
- [PR33原生自动修复及并发PDF验收](http://10.66.66.5:18123/onticards-reports/acceptance/pr33-fdd3/)
- [当前部署/恢复说明](propr/DEPLOY-CURRENT.md)、[运行说明](propr/RUNBOOK.md)、[固定版本manifest](propr/manifest.json)
- [逐功能复用矩阵](../research/reuse-matrix.md)、[AC01–14验收审计](../research/acceptance-gap-audit.md)、[验证报告](testing-report.md)
- [普通咨询运行规则](n8n/RUNBOOK-current.md)、[持续CI与隔离](n8n-preview-ci/README.md)、[知识版本更新](propr/KNOWLEDGE-CURRENT.md)

PR26、PR30、PR33均交维护者审查和最终合并。本交付不把已有产品静态检查失败、未经过的30天运行或被拒绝的模型答案写成已通过。原始失败保留，版本变化后旧Check需要重新验证。早期18110/旧policy与冻结快照只作为历史证据，不是当前部署命令。

当前ProPR policy13已经在测试机三个核心服务运行，构建/编译及964项回归在kol完成，运行环境密钥未改变。自动CI已经通过自然轮询准入；当前模型CI账户15445单位低于下一次所需45000，未重置或继续付费验收。自动语义评审的源快照是已验证干跑，最终PR发布后的启用/基线状态请查看完整交付门户中单列的运行回执。
