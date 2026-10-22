# Issue29 最后一次普通回复的实际验收边界

2026-10-23。人类候选正文为 `issue29-persistent-final-followup.md`；仅交给根流程，由已授权人类账号 Edge 提交。子代理不调用 App 发布输入，不新建 Issue，不修改 Issue31，也不伪装新人类事件。

真实首周期证据 `evidence/n8n/ordinary-pipeline-runtime.json`：draft执行788于00:52:07完成，在00:50:05新鲜水位上无eligible新事件，model_calls_attempted=0；新review/pub表为空。当前Issue29会话model_calls=2、reply_count=2；Issue31仍3/0并显式人工封存。此验收可适用Issue29最后一条回复，正常结果为draft预留到3、独立review预留到4、GET确认App第三条回复到reply_count3；任一阶段失败则保留已消耗预算与人工状态，不自动模型重试、不补发未知POST。

该问题只核对当前main的PDF备用路径与统一错误的证据边界，接续同Issue原有历史材料。没有重新打开Issue31的架构咨询，也不制造真实运行故障。期望来源是本轮实际GitHub SHA/tree/blob读取，不能硬编码c8e为当前main；候选3105/PR26及其他候选不是已合并当前实现的证明。

验收判定：从真实人类评论ID/原文入站，5分钟原生Schedule接纳一次；已知部署方式/历史镜像沿原会话保留；问题缺失项只能是区别失败环节所需最少脱敏观测。草稿结构通过后还需一次独立模型审核，逐句出处与人类材料来源校验；只有自动语义门禁通过并fresh source/评论/App计数一致，才由已绑定App节点发布一次，GET确证并更新会话。第三回复后同线程任何第四回复都拒绝，marker不能重置次数。

不能预先承诺模型质量通过。若正文无依据、误将源码当当前运行事实、重复索取已知材料、来源变化、AI接管、未知POST或不足预算，均应保留明确拒绝证据。本文件不作为模型输入，不向模型提供固定预期答案。
