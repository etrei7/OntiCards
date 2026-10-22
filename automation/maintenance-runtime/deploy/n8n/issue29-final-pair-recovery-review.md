# Issue29 同一真人事件最后一组模型调用：待批准方案

此文件是可审阅恢复候选，尚未导入、触发或消耗预算。批准标识建议 `onticards-root-review-issue29-final-pair-20261023-v1`，只有root明确批准后才写入原生配置。

## 固定对象与已保留失败

- 仓库：stepll2026/OntiCards，Issue29，真人comment6346376385。
- 原事件键：d68c876a55aab27af14128dea27bfb65d683bc59d8a0311a690b2d0dfe4887f0。
- 原source_hash：2405a60afc18032437e094d6cd9ce06480b6823bd9a93d1a5b299863b0959c58。
- 原draft998与review1022及全部原文不修改。review为needs_human_review；本轮19195+19318tokens，0POST。
- 当前线程model_calls=4、reply_count=2，pending_event=原事件键，pending_state=model_request_started。Issue31仍显式人工封存且budget3，不纳入此恢复。

## 复用方式

复用已存在的原生手工恢复模式：Webhook、DataTable Get/Insert/Upsert、Set条件、Crypto source hash、实际source子流程与既有单次HTTP模型节点。建立一个固定29/固定comment的inactive恢复配置，无Schedule、不自行发帖、不改变常驻普通事件接入或水位；不启动第二套Agent。原Issue31手工入口保持inactive不改。

为保留历史且让已有审核/发布节点处理一次新尝试，新的工作行键使用 `SHA256(original_event_key + "|manual-recovery|" + approval_id)`。这是同一GitHub comment的明确恢复尝试键，不写入intake事件表，也不伪装成新的人类事件；source_snapshot中保留原comment id/body及recovery.original_event_key/approval_id/operator/reason。原draft/review行保留不动，新attempt row只存在于原生draft/review账本。

## 必须全满足的执行门禁

1. 配置默认manual_enabled=false；批准后仅一次Webhook可消耗该固定恢复键。现有attempt表中同恢复意图已存在即拒绝；即使发生超时也不能自动再次调用。
2. 原draft必须仍awaiting_semantic_review且source_hash完全匹配；原review必须仍needs_human_review、reserved_model_ordinal=4。原publisher无该事件POST/unknown/成功回执；新恢复键也无draft/review/publication/attempt。
3. conversation必须仍model_calls=4、reply_count=2、pending指向原事件；新鲜完整intake仍记录本App恰好2条评论，真人ID/全文/updated_at和线程title/body/state/labels/discussion/inline/reviews均与本次失败所绑定输入一致；AI标签存在则拒绝。
4. 原生source子流程重新读取实际main，要求complete+token_revoked，commit/tree仍与原失败c8e相同。使用当前修好的相关源码片段；若main或人类材料变化则只给差异并停止，不调用模型。
5. 在任何模型之前，原生attempt表先Insert意图，记录原draft/review全文、原源hash、审批人与原因、新源hash及最大预算6。然后conversation预算4→5、pending改为恢复尝试键，reply保持2；执行一遍现有draft HTTP（retry=false），保存真实响应与安全usage，不自动重试。
6. 若draft失败/unknown，保持已消耗5次及原意图，转人工并封存本恢复。若结构通过，既有常驻独立semantic流程在下一正常周期为新恢复键预留5→6并只调用一次审核。原review行因旧键保留，不能被覆盖或删除。
7. 独立审核通过才由现有publisher处理新恢复键：新鲜head/source/真人内容、所有App评论计数、AI路由及sticky unknown门禁仍适用。第三条回复单POST后GET确认，reply2→3；原真人ID写answered_human_ids。重复运行仅对账，第四条回复拒绝。
8. 任一步失败均不自动再恢复；总预算绝不超过6、总App回复绝不超过3。完成后停用专用恢复入口，持久意图保留。

## 激活前验证

先用同一固定guard的无模型原生fixture验证：正常意图只一次、重复/错误comment/预算非4/已有unknownPOST/AI标签/人类输入改变/source变更/过期水位全部0调用；模拟成功路径4→5→6与reply2→3，并证明原draft/review行逐字保留。只有root核对具体guard及fixture后才触发真实恢复。SHA错误及metadata quote门禁已经独立部署，历史本轮仍拒绝。


## 已批准执行后的终态（2026-10-23 02:00:51）

审批 onticards-root-review-issue29-final-pair-20261023-v1 仅执行一次。原生guard16/16与独立PDF源码7/7先通过，执行1220消耗第5次预算，真实18444 tokens。模型仍转录了错误完整SHA，精确门禁拒绝needs_structure_review；未调用第6次审核、未发布。原998/1022行逐字保留；恢复意图保留。专用入口已inactive/manualfalse，普通管道manual_handoff_threads=[29,31]。该方案现在是封存历史，不能再按上文激活或重复触发。最终事实见issue29-final-recovery-result.json与issue29-final-recovery-sealed.json。
