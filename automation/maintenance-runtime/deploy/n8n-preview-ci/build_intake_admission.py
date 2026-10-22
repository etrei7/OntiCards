"""Connect the existing complete intake to native CI. No new trigger schedule or GitHub listing."""
import json, uuid
from pathlib import Path
ROOT=Path(__file__).parent
class Workflow:
 def __init__(self,id,name):self.id=id;self.name=name;self.nodes=[];self.connections={}
 def node(self,name,kind,p,version=1,**extra):
  self.nodes.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,self.id+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[len(self.nodes)*220,0],'parameters':p,**extra})
 def code(self,name,source):self.node(name,'code',{'jsCode':source},2)
 def link(self,a,b,index=0):
  branches=self.connections.setdefault(a,{'main':[]})['main']
  while len(branches)<=index:branches.append([])
  branches[index]=[{'node':b,'type':'main','index':0}]
 def chain(self,*names):
  for a,b in zip(names,names[1:]):self.link(a,b)
 def iff(self,name,expr):self.node(name,'if',{'conditions':{'options':{'typeValidation':'strict'},'conditions':[{'id':name,'leftValue':expr,'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
 def sub(self,name,id):self.node(name,'executeWorkflow',{'workflowId':{'__rl':True,'value':id,'mode':'id'},'mode':'each','options':{'waitForSubWorkflow':True}},1.3,onError='continueRegularOutput')
 def save(self,file,timeout):
  data={'id':self.id,'name':self.name,'active':False,'nodes':self.nodes,'connections':self.connections,'settings':{'executionOrder':'v1','executionTimeout':timeout,'saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False},'pinData':{}}
  (ROOT/file).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

a=Workflow('onticardsPreviewAdmissionV1','OntiCards current PR native CI admission')
a.node('Existing intake version candidate','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
a.code('Fixed version admission identity',"""const p=$input.first().json;
if(!Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??'')||!['dispatch','dry_run'].includes(p.mode))throw new Error('Invalid fixed admission identity');
const key=`stepll2026/OntiCards#${p.pr}:${p.head}:${p.base}`;
return [{json:{pr:p.pr,head:p.head,base:p.base,mode:p.mode,watermark:p.watermark,observed_at:p.observed_at,batch_budget:p.batch_budget??null,receipt_key:key,admission_key:'admission:'+key,policy:'preview-v1'}}];""")
a.node('Ensure existing native CI receipts','dataTable',{'resource':'table','operation':'create','tableName':'onticards_ci_receipts_v1','columns':{'column':[{'name':n,'type':t} for n,t in [('receipt_key','string'),('head','string'),('base','string'),('state','string'),('detail','string'),('pr','number')]]},'options':{'createIfNotExists':True}},1.1)
table={'__rl':True,'value':'onticards_ci_receipts_v1','mode':'name'}
def get(name,key):
 a.node(name,'dataTable',{'resource':'row','operation':'get','dataTableId':table,'matchType':'allConditions','filters':{'conditions':[{'keyName':'receipt_key','condition':'eq','keyValue':"={{ $('Fixed version admission identity').first().json."+key+" }}"}]},'returnAll':True},1.1,alwaysOutputData=True)
def upsert(name):
 a.node(name,'dataTable',{'resource':'row','operation':'upsert','dataTableId':table,'matchType':'allConditions','filters':{'conditions':[{'keyName':'receipt_key','condition':'eq','keyValue':'={{ $json.receipt_key }}'}]},'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
get('Read existing CI receipt','receipt_key');get('Read existing admission receipt','admission_key')
a.code('Select unseen version',"""const p=$('Fixed version admission identity').first().json;
const main=$('Read existing CI receipt').all().map(x=>x.json).filter(x=>x.receipt_key===p.receipt_key);
const admission=$input.all().map(x=>x.json).filter(x=>x.receipt_key===p.admission_key);
return [{json:{...p,consumed:main.length>0||admission.length>0,prior_states:[...main,...admission].map(x=>x.state),validation_only:p.mode==='dry_run'}}];""")
a.iff('Unseen or validation only','= {{ $json.validation_only === true || $json.consumed === false }}'.replace('= {{','={{'))
a.code('Return prior receipt proof',"const p=$input.first().json;return [{json:{pr:p.pr,head:p.head,base:p.base,state:'already_consumed',prior_states:p.prior_states,model_calls:0,dispatched:false}}];")
a.sub('Fresh existing PR revision guard','onticardsPreviewRevisionV1')
a.code('Preserve fresh scope verdict',"""const p=$('Select unseen version').first().json,r=$input.first().json;
return [{json:{...p,current:r.current===true&&r.token_revoked===true&&r.head===p.head&&r.base===p.base,revision_reason:r.reason??'revision_unavailable',revision_token_revoked:r.token_revoked===true}}];""")
a.iff('Current approved repository scope','={{ $json.current === true }}')
a.code('Scope requires human review',"const p=$input.first().json;return [{json:{...p,state:'manual_review_required',reason:'Same-repository codex/main exact revision not verified; fork or stale/unavailable scope is never dispatched'}}];")
a.code('Determine native admission',"""const p=$('Preserve fresh scope verdict').first().json;const b=p.batch_budget,age=Date.now()-Date.parse(b?.checked_at);
const valid=b&&b.watermark===p.watermark&&b.observed_at===p.observed_at&&Number.isFinite(age)&&age>=-5000&&age<=300000&&b.required_quota===45000&&b.provider_calls===0&&b.token_creation_calls===0&&b.account_quota_reset===false&&Number.isSafeInteger(b.remaining_quota)&&b.remaining_quota>=0;
const budget=valid?b:{state:'budget_unverifiable',reason_code:'batch_observation_stale_missing_or_mismatched',provider_calls:0,token_creation_calls:0};
const allowed=valid&&budget.state==='budget_available'&&budget.remaining_quota>=budget.required_quota;
return [{json:{...p,budget,allowed,state:allowed?'dispatching':budget.state==='budget_exhausted'?'budget_exhausted':'budget_unverifiable'}}];""")
a.iff('Validation transport only','={{ $json.validation_only === true }}')
a.code('Prepare existing CI dry run',"const p=$input.first().json;return [{json:{pr:p.pr,head:p.head,base:p.base,validation_only:true}}];")
a.sub('Validate same native CI entry','onticardsFixedPreviewV1')
a.code('Return dry run admission proof',"""const p=$('Determine native admission').first().json,r=$input.first().json;
return [{json:{pr:p.pr,head:p.head,base:p.base,state:r.state==='dry_run_ci_entry_verified'?'dry_run_verified':'dry_run_entry_unverified',budget:p.budget,prior_receipt_consumed:p.consumed,model_calls:0,token_creation_calls:0,ssh_commands:r.ssh_commands??null,admission_written:false,ci_entry_state:r.state??null}}];""")
a.code('Prepare persisted admission',"""const p=$input.first().json;
if(p.validation_only===true)return [{json:{...p,state:'dry_run_scope_rejected',dispatched:false}}];
return [{json:{receipt_key:p.admission_key,pr:p.pr,head:p.head,base:p.base,state:p.state,detail:JSON.stringify({policy:p.policy,source:'onticards_intake_threads_v1',watermark:p.watermark,observed_at:p.observed_at,admitted_at:new Date().toISOString(),budget:p.budget??null,revision_token_revoked:p.revision_token_revoked,reason:p.reason??null,automatic_retry:false,model_calls:0})}}];""")
a.iff('Write only real admission','={{ !$json.validation_only }}')
upsert('Persist before any CI dispatch')
a.iff('Native budget permits execution',"={{ $json.state === 'dispatching' }}")
a.code('Prepare exact existing CI request',"const p=$input.first().json;return [{json:{pr:p.pr,head:p.head,base:p.base}}];")
a.sub('Dispatch existing fixed native CI','onticardsFixedPreviewV1')
a.code('Record bounded native dispatch outcome',"""const p=$('Persist before any CI dispatch').first().json,r=$input.first().json;let detail;
try{detail=JSON.parse(p.detail);}catch{detail={};}
const matching=r.pr===p.pr&&r.head===p.head&&r.base===p.base;
return [{json:{receipt_key:p.receipt_key,pr:p.pr,head:p.head,base:p.base,state:matching&&typeof r.state==='string'?'dispatched_'+r.state:'dispatch_outcome_unknown',detail:JSON.stringify({...detail,completed_at:new Date().toISOString(),ci_state:matching?r.state:null,ci_receipt_key:matching?r.receipt_key:null,automatic_retry:false})}}];""")
upsert('Persist exact native dispatch outcome')
a.code('Return public admission outcome',"return $input.all().map(x=>({json:{pr:x.json.pr,head:x.json.head,base:x.json.base,state:x.json.state,receipt_key:x.json.receipt_key??null,detail:x.json.detail??null}}));")
a.chain('Existing intake version candidate','Fixed version admission identity','Ensure existing native CI receipts','Read existing CI receipt','Read existing admission receipt','Select unseen version','Unseen or validation only','Fresh existing PR revision guard','Preserve fresh scope verdict','Current approved repository scope','Determine native admission','Validation transport only','Prepare existing CI dry run','Validate same native CI entry','Return dry run admission proof')
a.link('Unseen or validation only','Return prior receipt proof',1)
a.link('Current approved repository scope','Scope requires human review',1);a.link('Scope requires human review','Prepare persisted admission')
a.link('Validation transport only','Prepare persisted admission',1)
a.chain('Prepare persisted admission','Write only real admission','Persist before any CI dispatch','Native budget permits execution','Prepare exact existing CI request','Dispatch existing fixed native CI','Record bounded native dispatch outcome','Persist exact native dispatch outcome','Return public admission outcome')
a.link('Write only real admission','Return public admission outcome',1);a.link('Native budget permits execution','Return public admission outcome',1)
a.save('intake-admission.workflow.json',7500)

r=Workflow('onticardsPreviewIntakeV1','OntiCards complete existing intake to fixed CI')
r.node('Trusted complete intake','webhook',{'httpMethod':'POST','path':'onticards-preview-intake-v1','authentication':'headerAuth','responseMode':'onReceived','options':{}},2.1,credentials={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}},webhookId='onticards-preview-intake-v1')
r.code('Validate complete existing snapshot',"""const p=$input.first().json.body??{},mode=p.mode??'dispatch';
const observed=Date.parse(p.observed_at),watermark=Date.parse(p.watermark);
if(p.source!=='onticards_intake_threads_v1'||p.complete!==true||p.token_revoked!==true||!['dispatch','dry_run'].includes(mode)||!Number.isFinite(observed)||!Number.isFinite(watermark)||observed>Date.now()+300000||Date.now()-observed>900000||watermark>observed+300000||!Array.isArray(p.threads)||p.threads.length>20)throw new Error('Incomplete, stale, oversized or unauthorized intake snapshot');
const seen=new Set();return p.threads.map(t=>{
if(!Number.isSafeInteger(t.pr)||t.pr<1||t.pr>9999999||t.state!=='open'||!/^[a-f0-9]{40}$/.test(t.head??'')||!/^[a-f0-9]{40}$/.test(t.base??'')||seen.has(t.pr))throw new Error('Invalid or duplicate fixed PR candidate');seen.add(t.pr);
return {json:{pr:t.pr,head:t.head,base:t.base,mode,watermark:p.watermark,observed_at:p.observed_at}};});""")
r.node('Read existing batch CI receipts','dataTable',{'resource':'row','operation':'get','dataTableId':table,'returnAll':True},1.1,executeOnce=True,alwaysOutputData=True)
r.code('Select bounded unseen batch budget need',"""const candidates=$('Validate complete existing snapshot').all().map(x=>x.json),rows=$('Read existing batch CI receipts').all().map(x=>x.json);
const consumed=new Set(rows.map(x=>x.receipt_key).filter(x=>typeof x==='string'));
const needed=candidates.some(p=>p.mode==='dispatch'&&!consumed.has(`stepll2026/OntiCards#${p.pr}:${p.head}:${p.base}`)&&!consumed.has(`admission:stepll2026/OntiCards#${p.pr}:${p.head}:${p.base}`));
return [{json:{needed,candidates}}];""")
r.iff('Only unseen real batch needs balance','={{ $json.needed === true }}')
r.node('Read one native balance per complete batch','executeCommand',{'executeOnce':True,'command':'node /opt/onticards-preview-ci/bundle/budget_status.mjs'},1,onError='continueRegularOutput')
r.code('Skip balance for dry run or consumed batch',"return [{json:{stdout:JSON.stringify({state:'not_required',checked_at:new Date().toISOString(),token_creation_calls:0,provider_calls:0})}}];")
r.code('Bind native observation to exact batch',"""const p=$('Select bounded unseen batch budget need').first().json;let raw;try{raw=JSON.parse($input.first().json.stdout??'');}catch{raw={state:'budget_unverifiable'};}
const budget={state:raw.state,required_quota:raw.required_quota,remaining_quota:raw.remaining_quota,checked_at:raw.checked_at,provider_calls:raw.provider_calls,token_creation_calls:raw.token_creation_calls,account_quota_reset:raw.account_quota_reset,reason_code:raw.reason_code??null};
return p.candidates.map(c=>({json:{...c,batch_budget:{...budget,watermark:c.watermark,observed_at:c.observed_at}}}));""")
r.sub('Native exact version admission','onticardsPreviewAdmissionV1')
r.code('Safe dispatch receipt projection',"return $input.all().map(x=>({json:x.json}));")
r.chain('Trusted complete intake','Validate complete existing snapshot','Read existing batch CI receipts','Select bounded unseen batch budget need','Only unseen real batch needs balance','Read one native balance per complete batch','Bind native observation to exact batch','Native exact version admission','Safe dispatch receipt projection')
r.link('Only unseen real batch needs balance','Skip balance for dry run or consumed batch',1);r.link('Skip balance for dry run or consumed batch','Bind native observation to exact batch')
r.save('intake-receiver.workflow.json',7600)
print(json.dumps({'admission_nodes':len(a.nodes),'receiver_nodes':len(r.nodes),'new_schedule_triggers':0,'new_github_list_clients':0,'model_calls_in_generation':0}))
