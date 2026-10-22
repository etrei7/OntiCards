"""Connect complete existing intake to existing CI; no new schedule or GitHub reader."""
import copy,json,uuid
from pathlib import Path
root=Path(__file__).parent
raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':90}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
b=Builder('onticardsIntakeCiHandoffV1')
b.node('Native complete intake handoff','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
b.set('Trusted CI handoff configuration',json.dumps({'mode':'dry_run','max_open_prs':20,'freshness_seconds':600}))
b.node('Read committed intake watermark','dataTable',{'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':'onticards_intake_watermark_v1','mode':'name'},'returnAll':True},1.1,alwaysOutputData=True,executeOnce=True)
b.node('Read current intake threads for CI','dataTable',{'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':'onticards_intake_threads_v1','mode':'name'},'returnAll':True},1.1,alwaysOutputData=True,executeOnce=True)
b.set('Project complete public PR revisions',r'''={{ (()=>{
 const input=$('Native complete intake handoff').first().json,cfg=$('Trusted CI handoff configuration').first().json;
 let details;try{details=JSON.parse(input.details||'{}');}catch{return {eligible:false,reason:'invalid_poll_details'};}
 const mark=$('Read committed intake watermark').all().map(x=>x.json).find(x=>x.repository==='stepll2026/OntiCards');
 if(input.status!=='complete_readonly_dry_run'||details.token_revoked!==true||!mark||mark.poll_id!==input.poll_id||mark.watermark!==details.watermark)return {eligible:false,reason:'incomplete_or_unrevoked_poll'};
 const age=Date.now()-Date.parse(mark.watermark);if(!Number.isFinite(age)||age<0||age>cfg.freshness_seconds*1000)return {eligible:false,reason:'stale_watermark'};
 const current=$('Read current intake threads for CI').all().map(x=>x.json).filter(x=>x.observed_at===input.started_at);
 if(current.length!==mark.thread_count)return {eligible:false,reason:'thread_count_mismatch'};
 const threads=[];for(const row of current){if(row.kind!=='pull_request')continue;let s;try{s=JSON.parse(row.snapshot);}catch{return {eligible:false,reason:'invalid_thread_snapshot'};}
  if(s.state!=='open')continue;
  if(!Number.isSafeInteger(row.number)||row.number<1||row.thread_key!=='stepll2026/OntiCards#'+row.number||s.number!==row.number||s.kind!=='pull_request'||!(/^[a-f0-9]{40}$/).test(s.head||'')||!(/^[a-f0-9]{40}$/).test(s.base||''))return {eligible:false,reason:'invalid_pr_revision'};
  threads.push({pr:row.number,head:s.head,base:s.base,state:s.state});
 }
 if(threads.length>cfg.max_open_prs||new Set(threads.map(p=>p.pr)).size!==threads.length)return {eligible:false,reason:'open_pr_bound_or_duplicate'};
 if(!['dry_run','dispatch'].includes(cfg.mode))return {eligible:false,reason:'invalid_trusted_mode'};
 return {eligible:true,payload:{source:'onticards_intake_threads_v1',watermark:mark.watermark,observed_at:input.finished_at,complete:true,token_revoked:true,mode:cfg.mode,threads}};
})() }}''')
b.iff('Complete revoked bounded snapshot only','={{ $json.eligible === true }}')
b.node('Send snapshot to existing trusted CI','httpRequest',{'method':'POST','url':'http://127.0.0.1:18132/webhook/onticards-preview-intake-v1','authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth','sendBody':True,'specifyBody':'json','jsonBody':'={{ $json.payload }}','options':{'timeout':60000,'response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}},4.4,credentials={'httpHeaderAuth':{'id':'onticardsPreviewIntakeHeader','name':'OntiCards existing trusted CI intake only'}},retryOnFail=False,onError='continueRegularOutput')
b.set('Safe CI handoff observation','={{ {watermark:$("Project complete public PR revisions").first().json.payload.watermark,mode:$("Project complete public PR revisions").first().json.payload.mode,pr_count:$("Project complete public PR revisions").first().json.payload.threads.length,transport_status:$json.statusCode||null,acknowledged:Number($json.statusCode)>=200&&Number($json.statusCode)<300,unknown:!$json.statusCode,model_calls:0,github_writes:0} }}')
b.set('CI handoff refused','={{ {eligible:false,reason:$json.reason,model_calls:0,github_writes:0} }}')
b.chain(['Native complete intake handoff','Trusted CI handoff configuration','Read committed intake watermark','Read current intake threads for CI','Project complete public PR revisions','Complete revoked bounded snapshot only','Send snapshot to existing trusted CI','Safe CI handoff observation'])
b.link('Complete revoked bounded snapshot only','CI handoff refused',1)
child=b.workflow('OntiCards complete intake to existing trusted CI')
for node in child['nodes']:
 if node['name'] in ['Project complete public PR revisions','Send snapshot to existing trusted CI','Safe CI handoff observation','CI handoff refused']:
  node['executeOnce']=True
parent=json.loads((root/'persistent-readonly-serial.workflow.json').read_text(encoding='utf-8'))
parent['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,parent['id']+'/CI handoff after authentication completion')),'name':'CI handoff after authentication completion','type':'n8n-nodes-base.executeWorkflow','typeVersion':1.3,'position':[12000,0],'parameters':{'workflowId':{'__rl':True,'value':child['id'],'mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}},'executeOnce':True,'retryOnFail':False,'onError':'continueRegularOutput'})
parent['connections']['Persist authentication completion']={'main':[[{'node':'CI handoff after authentication completion','type':'main','index':0}]]}
def spacing(v):
 if isinstance(v,dict):return {k:spacing(x)for k,x in v.items()}
 if isinstance(v,list):return [spacing(x)for x in v]
 if isinstance(v,str)and v.startswith('={{'):
  inner=v[3:-2]
  while '}}'in inner:inner=inner.replace('}}','} }')
  return '={{'+inner+'}}'
 return v
child=spacing(child)
for name,w in [('intake-ci-handoff.workflow.json',child),('persistent-readonly-ci.workflow.json',parent)]:
 (root/name).write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'child_nodes':len(child['nodes']),'parent_nodes':len(parent['nodes']),'schedule_nodes_added':0,'mode':'dry_run'}))
