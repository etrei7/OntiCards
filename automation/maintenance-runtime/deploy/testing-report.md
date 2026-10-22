# OntiCards 真实验证报告

核对日期2026-10-23。各结果分别绑定代码与执行环境；不同版本、历史失败和配置测试不合并计算“整仓通过率”。测试构建仅在kol-stage2，业务运行仅在独立10.66.66.5环境，未操作生产库。

|范围|真实结果|版本/证据|
|---|---|---|
|维护底座适配|policy13：原679+20真实Redis/SQLite审查授权+265相关review/handoff/cancel/MCP=964通过，0失败/跳过，编译通过；API/worker/daemon已实际升级|evidence/propr-policy13-validation.json、propr-policy13-deployment.json、policy13-independent-review.json；精确镜像digest3bef8bde…|
|确定性事实采集|Linux37/37，0跳过；Windows36/1skip单列|最新collector安全列快照、完整分页、Checks分离与原子文件输出|
|日报日期/事实契约|28个输入校验通过；既有7个原生cron/Task检查|未把未来09:05自然运行当成已执行|
|知识增量|真实8abe→c8e→main，69/69；PDF相关源码另7/7|精确Git对象、22实际片段、29原生缓存行；0模型/0仓库写|
|PR33并发PDF修复|pytest9/9、竞态10/10、真实并发PDF2/2|head fdd3f291e8d4a51c31610f13d87670ab3288a6e9/base c8e3dfee68d398a37842fc332f73af40a56f02a7|
|PR26 rootless真实业务|API7/7、Playwright3/3、0跳过、9张原生PNG|head3105b7b61469c6b2945357f2eefa8fcb2e3aaee5/base c8e；Check119988255661|
|版本失效|真实synthetic过期base Check从neutral→action_required；PR33自然5分钟复查仍current|真实PR/main未改；原生n8n/DataTable/Checks|
|普通咨询|初答与续答、持久预算/去重/unknown发布拒绝均留证；最新一次18444 tokens仍有错误SHA，被拒绝且0POST，总5调用/2回复，29与31封存人工|见n8n RUNBOOK与最终回执，不用离线fixture替代自动发布|
|自动CI准入|真实自然批次1receiver/6PR，已消费不重投，PR30/33预算不足；52表达式+20原生fixture；0新增CI/SSH/模型|evidence/rootless-runtime/batch-budget-natural-poll.json；旧HTTP429 unknown保留并追加独立余额核对|
|自动语义审查接线|自然六PR只读MCP验证，TLS/SSH12项；13 envelope+6 wrapper+16真SQLite；baseline12项|evidence/mcp-review-*.json；dry_run/policy=false，0模型，不表示有效审查通过|
|停止与Git边界|pending Task Stop25/25；本地continuation49+干净合并后的语义失败负例1=50/50；Git准备取消另有真实子进程证据|evidence/ac11-prequeue-stop-native.json、propr-conflict-fork-semantic-validation.json、native-git-preparation-validation.json；不是语义冲突自动解决、真实外部fork写入或host reboot|

PR26 r4使用明确合成的三行订单：实际模型提取schema、生成/编辑数据卡、问数total_amount=250、单表三列基础空值检测，以及XLSX/DOCX/Markdown/PDF四种导出均真实完成。API/PR容器不含长期模型/GitHub/SSH/registry秘密，无宿主root Docker socket。临时模型token撤销，独立project容器/卷读取为0。报告范围不含规则库/关系盘点、任意业务全覆盖、lint/tsc基线清零或全部迁移。

模型验收历史：两个认证401均在provider前；r2被网关限流阻断、r3原生额度预扣不足而浏览器2/3，原断言与失败记录保留。r4为第三次实际provider业务验收，用40406原生配额单位，token撤销后余4594；账户总配额从未重置、余15445。原生配额不是美元，USD未知。

10/22事实日报run5da38704完整，当前6Issue/6PR、13原生任务、真实Checks与日界快照已纳入。第三次原生AI日报仍因空Checks语义及历史知识污染未通过独立质量审查，不能把Task completed称业务通过。显式复核修正版只修4处措辞并删1条不属于该事实窗的历史待办，独立10/10；原文与用量保留。未来日报已用原生独立alias隔离全局知识，无模型配置检查通过，尚未宣称该alias模型实跑质量。

已有产品问题与边界：前端lint/tsc基线失败；迁移检查5通过1跳过（缺three_way_check.py）；SQL R18三次候选被拒、未修复；完整语义索引60文件/0目录为partial并已停，policy11恢复旧job未增加模型调用。真实外部fork写入和复杂语义冲突不因Git/SQLite fixture通过而宣称E2E完成。30天TTL和清理配置/行为已验，尚未经过30个自然日。

所有修复以草稿PR交付。PR33成功Check仅覆盖其并发修复，PR26成功Check仅覆盖上述rootless业务范围；head/base变化会使现有证据失效。完整未覆盖项及最小后续条件以[验收审计](../research/acceptance-gap-audit.md)为准。

policy13只读评审在原生PR lease内绕过旧handoff/publication恢复，不改变已授权的内部Ultrafix循环。无AI编码标签的显式评审要求配置的精确作者白名单、真实评论及原生权限/命令校验；冒用bot、正文编辑、错命令ID等负例已验。发布findings前重新查询实际head/base，失配时保留模型usage/raw/session并将Task记FAILED；GitHub查询与POST不是原子锁，不能承诺零竞态。

源码封存时自动评审仍为dry_run、宿主policy=false。最终配置PR发布后才对当时全部开放PR建立历史基线并启用后续新版本，实际启用或失败以完整交付包的 `evidence/mcp-review-activation.json` 为准；该运行回执不会回写到同一源码commit。六PR干跑和964项无模型回归均不能替代新一次有效模型评审结果。
