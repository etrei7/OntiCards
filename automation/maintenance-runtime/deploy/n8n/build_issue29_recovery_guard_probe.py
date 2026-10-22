"""Actual recovery precondition/source/budget expressions in native Set nodes; no network/model."""
import copy,json,uuid
from pathlib import Path
root=Path(__file__).parent;evidence=root.parents[1]/'evidence/n8n'
data=json.loads((evidence/'issue29-recovery-fixture-input.json').read_text(encoding='utf-8'))
draft=data['original_event'];review=data['original_review'];conversation=data['original_conversation'];source=json.loads(draft['source_snapshot'])
w=json.loads((root/'issue29-final-recovery.workflow.json').read_text(encoding='utf-8'));original={n['name']:n for n in w['nodes']};w.update(id='onticardsIssue29RecoveryGuardProbe',name='OntiCards actual final recovery native guards fixture',active=False);w['nodes']=[];w['connections']={}
def node(name,kind,p,v=3.4):w['nodes'].append({'name':name,'id':str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name)),'type':'n8n-nodes-base.'+kind,'typeVersion':v,'parameters':p,'position':[0,0]})
def setting(name,expression):node(name,'set',{'mode':'raw','jsonOutput':expression,'options':{}})
def copy_node(name):
 n=copy.deepcopy(original[name]);n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name));n.pop('credentials',None);w['nodes'].append(n)
def link(a,b):w['connections'][a]={'main':[[{'node':b,'type':'main','index':0}]]}
node('Fixture request','webhook',{'httpMethod':'POST','path':'onticards-issue29-recovery-guard-probe','responseMode':'responseNode','options':{}},2.1);w['nodes'][-1]['webhookId']='onticards-issue29-recovery-guard-probe'
copy_node('Trusted recovery configuration');cfg=json.loads(w['nodes'][-1]['parameters']['jsonOutput']);cfg['manual_enabled']=True;w['nodes'][-1]['parameters']['jsonOutput']=json.dumps(cfg)
values={'Read original event':draft,'Read original review':review,'Read original conversation':conversation,'Read current thread':{'number':29,'app_reply_count':2,'snapshot':json.dumps(source['thread'])},'Read complete watermark':{},'Read prior recovery attempts':{},'Read recovery event':{},'Read original publication':{},'Read recovery publication':{},'Read recovery review':{}}
for name,value in values.items():
 change=''
 if name=='Read original event':change="if(c==='changed_original_hash')v.source_hash='0'.repeat(64);if(c==='wrong_human_id'){const s=JSON.parse(v.source_snapshot);s.event.id=1;v.source_snapshot=JSON.stringify(s);}"
 if name=='Read original review':change="if(c==='review_not_failed')v.status='semantic_approved';"
 if name=='Read original conversation':change="if(c==='budget5'||c==='unknown_response_consumed')v.model_calls=5;if(c==='reply3')v.reply_count=3;"
 if name=='Read current thread':change="if(c==='app3')v.app_reply_count=3;if(c==='ai_label'||c==='changed_human'){const s=JSON.parse(v.snapshot);if(c==='ai_label')s.labels.push('AI');else s.discussion.find(x=>String(x.id)==='6346376385').body+=' changed';v.snapshot=JSON.stringify(s);}"
 if name=='Read complete watermark':change="v.watermark=new Date(Date.now()-(c==='stale'?3600000:0)).toISOString();"
 if name=='Read prior recovery attempts':change="if(c==='duplicate_intent'||c==='unknown_response_consumed')v.approval_id=$('Trusted recovery configuration').first().json.approval_id;"
 if name=='Read original publication':change="if(c==='posting_unknown')Object.assign(v,{event_key:$('Trusted recovery configuration').first().json.original_event_key,status:'posting_unknown'});"
 setting(name,'={{ (()=>{const v='+json.dumps(value,ensure_ascii=False)+',c=$("Fixture request").first().json.body.case;'+change+'return v;})() }}')
copy_node('Verify final recovery preconditions')
setting('Frozen unchanged source','={{ (()=>{const v='+json.dumps(source['repository_context'],ensure_ascii=False)+',c=$("Fixture request").first().json.body.case;if(c==="changed_commit")v.commit_sha="0".repeat(40);if(c==="incomplete_source")v.complete=false;if(c==="revoke_unknown")v.token_revoked=false;return v;})() }}')
copy_node('Bind actual source to final recovery');copy_node('Reserve final draft model budget')
node('Return actual recovery guards','respondToWebhook',{'respondWith':'json','responseBody':'={{ {eligible:$("Verify final recovery preconditions").first().json.eligible,errors:$("Verify final recovery preconditions").first().json.errors,source_complete:$("Bind actual source to final recovery").first().json.source_complete,projected_budget:$json.model_calls,projected_pending:$json.pending_event,model_calls:0,github_posts:0,ledger_writes:0} }}','options':{}},1.4)
names=[n['name']for n in w['nodes']]
for a,b in zip(names,names[1:]):link(a,b)
def spacing(v):
 if isinstance(v,dict):return {k:spacing(x)for k,x in v.items()}
 if isinstance(v,list):return [spacing(x)for x in v]
 if isinstance(v,str)and v.startswith('={{'):
  s=v[3:-2]
  while '}}'in s:s=s.replace('}}','} }')
  return '={{'+s+'}}'
 return v
for n in w['nodes']:n['parameters']=spacing(n['parameters'])
w['settings']['executionTimeout']=45
(root/'issue29-recovery-guard-probe.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'model_nodes':0,'external_http':0,'ledger_writes':0}))
