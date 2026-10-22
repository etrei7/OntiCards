"""One approved same-comment recovery; reuse native audit/source/draft nodes."""
import copy,hashlib,json,uuid
from pathlib import Path
from native_response_audit import add_response_audit
root=Path(__file__).parent;raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':300}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
base=json.loads((root/'persistent-drafts.workflow.json').read_text(encoding='utf-8'))
def spacing(s):
 if s.startswith('={{'):
  q=s[3:-2]
  while '}}'in q:q=q.replace('}}','} }')
  return '={{'+q+'}}'
 return s
Builder.set=lambda self,name,expr,**extra:self.node(name,'set',{'mode':'raw','jsonOutput':spacing(expr),'options':{}},3.4,**extra)
b=Builder('onticardsIssue29FinalRecoveryV1')
def add(name):
 n=copy.deepcopy(next(n for n in base['nodes']if n['name']==name));n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,b.wid+'/'+name));b.nodes.append(n)
event='d68c876a55aab27af14128dea27bfb65d683bc59d8a0311a690b2d0dfe4887f0'
approval='onticards-root-review-issue29-final-pair-20261023-v1'
newkey=hashlib.sha256((event+'|manual-recovery|'+approval).encode()).hexdigest()
cfg={'repository':'stepll2026/OntiCards','thread_key':'stepll2026/OntiCards#29','comment_id':'6346376385','original_event_key':event,'recovery_key':newkey,'original_source_hash':'2405a60afc18032437e094d6cd9ce06480b6823bd9a93d1a5b299863b0959c58','approval_id':approval,'operator':'Codex parent /root under maintainer authorization','reason':'One approved final pair after source coverage and exact metadata gates were corrected; preserve draft998/review1022; no automatic retry.','manual_enabled':False,'max_model_calls_per_thread':6,'freshness_seconds':600}
attempts='onticards_model_attempts_v1'
cols=[('attempt_key','string'),('event_key','string'),('ordinal','number'),('origin','string'),('status','string'),('operator','string'),('reason','string'),('approval_id','string'),('approved_at','string'),('reserved_at','string'),('execution_id','string'),('prior_execution_id','string'),('source_hash','string'),('payload','string')]
b.node('Local explicit final recovery','webhook',{'httpMethod':'POST','path':'onticards-issue29-final-recovery-v1','responseMode':'onReceived','options':{}},2.1,webhookId='onticards-issue29-final-recovery-v1')
b.set('Trusted recovery configuration',json.dumps(cfg,ensure_ascii=False));b.table('Ensure immutable recovery audit',attempts,cols)
reads=[('Read original event','onticards_draft_events_v1','event_key',event),('Read original review','onticards_semantic_reviews_v1','event_key',event),('Read original conversation','onticards_conversation_v1','thread_key',cfg['thread_key']),('Read current thread','onticards_intake_threads_v1','thread_key',cfg['thread_key']),('Read complete watermark','onticards_intake_watermark_v1','repository',cfg['repository']),('Read prior recovery attempts',attempts,'event_key',event),('Read recovery event','onticards_draft_events_v1','event_key',newkey),('Read original publication','onticards_publication_v1','event_key',event),('Read recovery publication','onticards_publication_v1','event_key',newkey),('Read recovery review','onticards_semantic_reviews_v1','event_key',newkey)]
for name,table,key,value in reads:b.row(name,table,'get',key,value,alwaysOutputData=True,executeOnce=True)
b.set('Verify final recovery preconditions',r'''={{ (()=>{
 const cfg=$('Trusted recovery configuration').first().json,d=$('Read original event').first().json,r=$('Read original review').first().json,c=$('Read original conversation').first().json,t=$('Read current thread').first().json,m=$('Read complete watermark').first().json,old=JSON.parse(d.source_snapshot||'{}'),live=JSON.parse(t.snapshot||'{}'),errors=[];
 if(d.event_key!==cfg.original_event_key||d.status!=='awaiting_semantic_review'||d.source_hash!==cfg.original_source_hash)errors.push('original draft changed');
 if(r.event_key!==cfg.original_event_key||r.status!=='needs_human_review'||r.reserved_model_ordinal!==4||r.source_hash!==cfg.original_source_hash)errors.push('original review changed');
 if(c.thread_key!==cfg.thread_key||c.model_calls!==4||c.reply_count!==2||c.pending_event!==cfg.original_event_key||c.pending_state!=='model_request_started')errors.push('original budget or pending state changed');
 if(t.number!==29||t.app_reply_count!==2)errors.push('thread or actual App count changed');
 if(!m.watermark||!Number.isFinite(Date.parse(m.watermark))||Date.now()-Date.parse(m.watermark)>cfg.freshness_seconds*1000)errors.push('complete intake stale');
 if(String(old.event?.id)!==cfg.comment_id||old.event?.author_type!=='User'||old.repository!==cfg.repository)errors.push('original human event mismatch');
 if((live.labels||[]).includes('AI'))errors.push('native AI route');
 if(JSON.stringify(live.id)!==JSON.stringify(old.thread?.id))errors.push('source changed: id');
 if(JSON.stringify(live.number)!==JSON.stringify(old.thread?.number))errors.push('source changed: number');
 if(JSON.stringify(live.title)!==JSON.stringify(old.thread?.title))errors.push('source changed: title');
 if(JSON.stringify(live.body)!==JSON.stringify(old.thread?.body))errors.push('source changed: body');
 if(JSON.stringify(live.state)!==JSON.stringify(old.thread?.state))errors.push('source changed: state');
 if(JSON.stringify(live.labels)!==JSON.stringify(old.thread?.labels))errors.push('source changed: labels');
 if(JSON.stringify(live.discussion)!==JSON.stringify(old.thread?.discussion))errors.push('source changed: discussion');
 if(JSON.stringify(live.inline)!==JSON.stringify(old.thread?.inline))errors.push('source changed: inline');
 if(JSON.stringify(live.reviews)!==JSON.stringify(old.thread?.reviews))errors.push('source changed: reviews');
 if(!(live.discussion||[]).some(x=>String(x.id)===cfg.comment_id&&x.body===old.event.body&&x.updated_at===old.event.updated_at))errors.push('human comment changed');
 if($('Read prior recovery attempts').all().some(x=>x.json.approval_id===cfg.approval_id))errors.push('recovery intent consumed');
 for(const name of ['Read recovery event','Read original publication','Read recovery publication','Read recovery review'])if($(name).all().some(x=>x.json.event_key))errors.push('existing recovery or publication record: '+name);
 return {eligible:errors.length===0,errors,original:d,original_review:r,conversation:c,context:{...old,thread:live,source_watermark:m.watermark},manual_enabled:cfg.manual_enabled};
})() }}''')
b.iff('Final exact recovery eligible','={{ $json.eligible }}');b.set('Recovery rejected no mutation','={{ {status:"manual_final_recovery_rejected",errors:$json.errors||[],model_calls:0,github_posts:0} }}')
b.set('Prepare immutable source lookup','={{ {ref:"main",topic:$("Verify final recovery preconditions").first().json.context.thread.title+" "+$("Verify final recovery preconditions").first().json.context.event.body} }}');add('Read actual repository source context')
b.set('Bind actual source to final recovery',r'''={{ (()=>{const p=$('Verify final recovery preconditions').first().json,cfg=$('Trusted recovery configuration').first().json,r=$json,old=p.context.repository_context,ok=r.complete===true&&r.token_revoked===true&&r.commit_sha===old.commit_sha&&r.tree_sha===old.tree_sha;
 const facts=Object.fromEntries(Object.entries(p.context.trusted_facts).filter(([k])=>!k.startsWith('repo_')));if(ok)for(const f of r.files)facts['repo_'+f.path.replace(/[^a-zA-Z0-9]/g,'_')]={...f,fact:'已按不可变commit与Git blob校验的源码片段；不代表实际部署。'};
 const snapshot={...p.context,trusted_facts:facts,repository_context:r,recovery:{original_event_key:cfg.original_event_key,approval_id:cfg.approval_id,operator:cfg.operator,reason:cfg.reason}};
 return {...p,source_complete:ok,source_difference:{old_commit:old.commit_sha,new_commit:r.commit_sha||null,complete:r.complete===true,token_revoked:r.token_revoked===true},candidate:{row:{...p.original,event_key:cfg.recovery_key,status:'model_request_started',source_snapshot:JSON.stringify(snapshot),source_hash:'',draft:'',reply_zh:'',usage:'{}',quality_errors:'[]'},conversation:p.conversation,app_reply_count:2}};
})() }}''')
b.iff('Approved switch and unchanged actual source','={{ $json.source_complete && $json.manual_enabled===true }}');b.set('Final source probe no mutation','={{ {status:$json.source_complete?"manual_disabled_source_ready":"source_incomplete_or_changed",source_difference:$json.source_difference,model_calls:0,github_posts:0} }}')
b.set('Prepare final bound source','={{ $("Bind actual source to final recovery").first().json.candidate.row }}');add('Hash bound source snapshot')
b.set('Immutable final recovery intent',r'''={{ (()=>{const cfg=$('Trusted recovery configuration').first().json,p=$('Verify final recovery preconditions').first().json;return {attempt_key:cfg.recovery_key+':5',event_key:cfg.original_event_key,ordinal:5,origin:'explicit_same_human_event_final_recovery',status:'reserved_no_retry',operator:cfg.operator,reason:cfg.reason,approval_id:cfg.approval_id,approved_at:'2026-10-23 parent explicit approval',reserved_at:$now.toISO(),execution_id:String($execution.id),prior_execution_id:'998,1022',source_hash:$json.source_hash,payload:JSON.stringify({original_event:p.original,original_review:p.original_review,original_conversation:p.conversation,recovery_event_key:cfg.recovery_key,new_source_snapshot:$json.source_snapshot,max_thread_budget:6,max_app_replies:3})};})() }}''');b.row('Insert final recovery intent once',attempts,'insert',None,None)
b.set('Reserve final draft model budget','={{ (()=>{const c=$("Read original conversation").first().json,k=$("Trusted recovery configuration").first().json.recovery_key;return {thread_key:c.thread_key,model_calls:5,reply_count:c.reply_count,pending_event:k,pending_state:"model_request_started",known_fields:c.known_fields,asked_fields:c.asked_fields,answered_human_ids:c.answered_human_ids,publication_ids:c.publication_ids};})() }}');add('Persist consumed model budget')
b.set('Persist nonretryable model reservation','={{ $("Hash bound source snapshot").first().json }}')
for name in ['Strict bounded draft request','One draft model request no retry','Validate structure and require semantic review']:add(name)
audit=add_response_audit(b,'draft','One draft model request no retry','$("Persist nonretryable model reservation").first().json.event_key')
b.set('Restore strict final draft request','={{ $("Strict bounded draft request").first().json }}')
b.set('Preserve final response with immutable prior audit','={{ (()=>{const a=$("Insert final recovery intent once").first().json,{id,createdAt,updatedAt,...record}=a;return {...record,status:$json.status,payload:JSON.stringify({...JSON.parse(a.payload),original_final_model_event:$json})};})() }}');b.row('Persist final response audit',attempts,'upsert','attempt_key','={{ $json.attempt_key }}')
b.set('Restore final draft candidate','={{ $("Validate structure and require semantic review").first().json }}');add('Persist original model draft')
b.set('Final pair recovery completed','={{ {status:"final_draft_recorded_wait_native_review",recovery_event_key:$("Trusted recovery configuration").first().json.recovery_key,model_calls_reserved:5,github_posts:0} }}')
chain=['Local explicit final recovery','Trusted recovery configuration','Ensure immutable recovery audit',*[x[0]for x in reads],'Verify final recovery preconditions','Final exact recovery eligible','Prepare immutable source lookup','Read actual repository source context','Bind actual source to final recovery','Approved switch and unchanged actual source','Prepare final bound source','Hash bound source snapshot','Immutable final recovery intent','Insert final recovery intent once','Reserve final draft model budget','Persist consumed model budget','Persist nonretryable model reservation','Strict bounded draft request',audit['ensure'],'Restore strict final draft request','One draft model request no retry',audit['sanitize'],audit['persist'],audit['restore'],'Validate structure and require semantic review','Preserve final response with immutable prior audit','Persist final response audit','Restore final draft candidate','Persist original model draft','Final pair recovery completed']
b.chain(chain);b.link('Final exact recovery eligible','Recovery rejected no mutation',1);b.link('Approved switch and unchanged actual source','Final source probe no mutation',1)
w=b.workflow('OntiCards Issue29 final same-comment recovery - disabled')
(root/'issue29-final-recovery.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'manual_enabled':False,'schedule_nodes':0,'recovery_key':newkey,'approval_id':approval}))
