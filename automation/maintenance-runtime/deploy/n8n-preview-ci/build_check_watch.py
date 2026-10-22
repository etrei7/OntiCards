"""Native n8n Check registration and bounded head/base invalidation; never run PR tests."""
import json, uuid
from pathlib import Path
root=Path(__file__).parent

class Workflow:
 def __init__(self,id,name):self.id=id;self.name=name;self.nodes=[];self.connections={}
 def node(self,name,kind,p,version=1,**extra):
  self.nodes.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,self.id+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[len(self.nodes)*220,0],'parameters':p,**extra})
 def code(self,name,js):self.node(name,'code',{'jsCode':js},2)
 def link(self,a,b,index=0):
  v=self.connections.setdefault(a,{'main':[]})['main']
  while len(v)<=index:v.append([])
  v[index]=[{'node':b,'type':'main','index':0}]
 def chain(self,*names):
  for a,b in zip(names,names[1:]):self.link(a,b)
 def iff(self,name,expr):self.node(name,'if',{'conditions':{'options':{'typeValidation':'strict'},'conditions':[{'id':name,'leftValue':expr,'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
 def sub(self,name,id):self.node(name,'executeWorkflow',{'workflowId':{'__rl':True,'value':id,'mode':'id'},'mode':'each','options':{'waitForSubWorkflow':True}},1.3,onError='continueRegularOutput')
 def table(self):self.node('Ensure native Check registrations','dataTable',{'resource':'table','operation':'create','tableName':'onticards_ci_checks_v1','columns':{'column':[{'name':n,'type':t} for n,t in [('registration_key','string'),('pr','number'),('head','string'),('base','string'),('check_id','string'),('check_name','string'),('external_id','string'),('state','string'),('detail','string')]]},'options':{'createIfNotExists':True}},1.1)
 def row(self,name,operation):
  p={'resource':'row','operation':operation,'dataTableId':{'__rl':True,'value':'onticards_ci_checks_v1','mode':'name'},'matchType':'allConditions','filters':{'conditions':[]}}
  if operation=='get':p.update(returnAll=True);p['filters']['conditions']=[{'keyName':'state','condition':'eq','keyValue':'watching'}]
  else:p.update(columns={'mappingMode':'autoMapInputData','value':{},'schema':[]},options={});p['filters']['conditions']=[{'keyName':'registration_key','condition':'eq','keyValue':'={{ $json.registration_key }}'}]
  self.node(name,'dataTable',p,1.1,alwaysOutputData=operation=='get')
 def save(self,file,timeout=180):
  w={'id':self.id,'name':self.name,'active':False,'nodes':self.nodes,'connections':self.connections,'settings':{'executionOrder':'v1','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':timeout},'pinData':{}}
  (root/file).write_text(json.dumps(w,indent=2)+'\n',encoding='utf-8')

b=Workflow('onticardsCheckObserveV1','OntiCards Check revision observation and invalidation')
b.node('Native Check request','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
b.code('Validate Check identity',"""const p=$input.first().json;
if(!['register','watch'].includes(p.mode)||!Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??'')||!/^[1-9][0-9]{0,17}$/.test(String(p.check_id??''))||typeof p.check_name!=='string'||p.check_name.length<1||p.check_name.length>128||typeof p.external_id!=='string'||p.external_id.length<1||p.external_id.length>256)throw new Error('Invalid Check registration');
return [{json:{mode:p.mode,pr:p.pr,head:p.head,base:p.base,check_id:String(p.check_id),check_name:p.check_name,external_id:p.external_id,registration_key:'pr'+p.pr+':check'+p.check_id}}];""")
b.sub('Fresh native read-only revision','onticardsPreviewRevisionV1')
b.code('Preserve revision proof',"""const r=$input.first().json,p=$('Validate Check identity').first().json;
return [{json:{...p,revision:{current:r.current===true&&r.token_revoked===true&&r.head===p.head&&r.base===p.base,observed_head:r.observed_head??null,observed_base:r.observed_base??null,reason:r.reason??'revision_unavailable',checked_at:r.checked_at??new Date().toISOString()}}}];""")
b.node('Sign Check action App JWT','jwt',{'operation':'sign','useJson':True,'claimsJson':'={{ JSON.stringify({iat:Math.floor(Date.now()/1000)-60,exp:Math.floor(Date.now()/1000)+540,iss:"5422414"}) }}','headerClaims':'{}','options':{'algorithm':'RS256'}},1,credentials={'jwtAuth':{'id':'onticardsPreviewAppJwt','name':'OntiCards preview revision App'}})
def http(name,method,url,app=False,body=None):
 auth='={{ "Bearer "+$("Sign Check action App JWT").first().json.token }}' if app else '={{ "Bearer "+$("Mint Check action token").first().json.body?.token }}'
 p={'method':method,'url':url,'sendHeaders':True,'headerParameters':{'parameters':[{'name':'Authorization','value':auth},{'name':'Accept','value':'application/vnd.github+json'},{'name':'X-GitHub-Api-Version','value':'2026-03-10'},{'name':'Cache-Control','value':'no-cache'}]},'options':{'timeout':20000,'proxy':'http://127.0.0.1:17891','response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}}
 if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=body)
 b.node(name,'httpRequest',p,4.4,onError='continueRegularOutput',retryOnFail=method=='GET',maxTries=2,waitBetweenTries=500)
http('Mint Check action token','POST','https://api.github.com/app/installations/174029282/access_tokens',True,json.dumps({'repositories':['OntiCards'],'permissions':{'checks':'write','metadata':'read'}}))
http('Verify Check action scope','GET','https://api.github.com/installation/repositories?per_page=100')
b.iff('Exact Check action scope','={{ (()=>{const m=$("Mint Check action token").first().json,p=m.body?.permissions||{},r=$json;return m.statusCode===201&&Object.keys(p).length===2&&p.checks==="write"&&p.metadata==="read"&&r.statusCode===200&&r.body?.total_count===1&&r.body.repositories?.[0]?.full_name==="stepll2026/OntiCards";})() }}')
check_url='=https://api.github.com/repos/stepll2026/OntiCards/check-runs/{{ $("Validate Check identity").first().json.check_id }}'
http('Read exact owned Check','GET',check_url)
b.code('Determine Check action',"""const p=$('Preserve revision proof').first().json,r=$input.first().json,c=r.body;
const bound=r.statusCode===200&&String(c?.id)===p.check_id&&c.head_sha===p.head&&c.name===p.check_name&&c.external_id===p.external_id&&c.app?.id===5422414;
const already=bound&&c.status==='completed'&&c.conclusion==='action_required';
const check_update={status:'completed',conclusion:'action_required',completed_at:new Date().toISOString(),output:{title:'Current PR revision requires verification',summary:'This Check binds head '+p.head+' against base '+p.base+'. Current head/base changed or could not be verified. Original evidence is retained. No automatic test rerun or merge was performed.'}};
return [{json:{...p,check_update,bound,needs_update:bound&&!p.revision.current&&!already,state:!bound?'unverified':already?'invalidated':'watching',observed_conclusion:bound?c.conclusion:null}}];""")
b.iff('Invalidate changed or unverifiable revision','={{ $json.needs_update===true }}')
http('Mark exact Check awaiting verification','PATCH',check_url,body='={{ JSON.stringify($json.check_update) }}')
http('Read back invalidated Check','GET',check_url)
b.code('Verify invalidation readback',"""const p=$('Determine Check action').first().json,r=$input.first().json,c=r.body,patch=$('Mark exact Check awaiting verification').first().json??{};
const confirmed=r.statusCode===200&&String(c?.id)===p.check_id&&c.head_sha===p.head&&c.name===p.check_name&&c.external_id===p.external_id&&c.app?.id===5422414&&c.status==='completed'&&c.conclusion==='action_required';
return [{json:{...p,state:confirmed?'invalidated':'watching',update_result:confirmed?'action_required_verified':'update_outcome_unknown',update_http_status:patch.statusCode??null,update_error_category:['JSON','syntax','Referenced node','item','timeout','timed out','certificate','URL','not executed','expression'].find(x=>String(patch.error?.message??patch.error??'').toLowerCase().includes(x.toLowerCase()))??(patch.error?'other_node_error':null),update_error_fields:Array.isArray(patch.body?.errors)?patch.body.errors.filter(x=>x&&typeof x==='object').map(x=>({resource:x.resource??null,field:x.field??null,code:x.code??null})):[],readback_http_status:r.statusCode??null}}];""")
b.code('Check scope unverified',"return [{json:{...$('Preserve revision proof').first().json,state:'unverified',bound:false,update_result:'scope_unverified'}}];")
b.code('Preserve public Check result',"return $input.all().map(x=>({json:x.json}));")
http('Revoke Check action token','DELETE','https://api.github.com/installation/token')
b.code('Return public Check registration',"""const p=$('Preserve public Check result').first().json,revoked=$input.first().json.statusCode===204;
return [{json:{registration_key:p.registration_key,pr:p.pr,head:p.head,base:p.base,check_id:p.check_id,check_name:p.check_name,external_id:p.external_id,state:p.bound&&revoked?p.state:'unverified',detail:JSON.stringify({checked_at:new Date().toISOString(),revision:p.revision,bound:p.bound===true,observed_conclusion:p.observed_conclusion??null,update_result:p.update_result??'not_required',update_http_status:p.update_http_status??null,update_error_category:p.update_error_category??null,update_error_fields:p.update_error_fields??[],readback_http_status:p.readback_http_status??null,token_revoked:revoked,checks_write_only_in_this_action:true,model_calls:0,test_runs:0})}}];""")
b.chain('Native Check request','Validate Check identity','Fresh native read-only revision','Preserve revision proof','Sign Check action App JWT','Mint Check action token','Verify Check action scope','Exact Check action scope','Read exact owned Check','Determine Check action','Invalidate changed or unverifiable revision','Mark exact Check awaiting verification','Read back invalidated Check','Verify invalidation readback','Preserve public Check result','Revoke Check action token','Return public Check registration')
b.link('Exact Check action scope','Check scope unverified',1);b.link('Check scope unverified','Preserve public Check result');b.link('Invalidate changed or unverifiable revision','Preserve public Check result',1)
b.save('check-observe.workflow.json',240)

r=Workflow('onticardsCheckRegisterV1','OntiCards register exact verified Check')
r.node('Trusted Check registration','webhook',{'httpMethod':'POST','path':'onticards-check-register-v1','authentication':'headerAuth','responseMode':'responseNode','options':{}},2.1,credentials={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}},webhookId='onticards-check-register-v1')
r.code('Fixed Check registration input',"return [{json:{...$input.first().json.body,mode:'register'}}];")
r.table();r.code('Restore Check registration input',"return $('Fixed Check registration input').all();")
r.sub('Verify exact owned Check','onticardsCheckObserveV1')
r.iff('Verified registration result','={{ ["watching","invalidated"].includes($json.state) && !!$json.registration_key }}')
r.row('Persist exact Check registration','upsert')
r.node('Return Check registration','respondToWebhook',{'respondWith':'json','responseBody':'={{ $json }}','options':{}},1.4)
r.chain('Trusted Check registration','Fixed Check registration input','Ensure native Check registrations','Restore Check registration input','Verify exact owned Check','Verified registration result','Persist exact Check registration','Return Check registration')
r.link('Verified registration result','Return Check registration',1)
r.save('check-register.workflow.json',300)

w=Workflow('onticardsCheckWatchV1','OntiCards native Check head and base invalidation every five minutes')
w.node('Native five minute schedule','scheduleTrigger',{'rule':{'interval':[{'field':'minutes','minutesInterval':5}]}},1.2)
w.node('Trusted Check observation acceptance','webhook',{'httpMethod':'POST','path':'onticards-check-watch-v1','authentication':'headerAuth','responseMode':'onReceived','options':{}},2.1,credentials={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}},webhookId='onticards-check-watch-v1')
w.table();w.row('Read registered watching Checks','get')
w.code('Bounded native registered Checks',"const rows=$input.all().map(x=>x.json).filter(x=>x.registration_key&&x.state==='watching');if(rows.length>20)throw new Error('Native Check watch bound exceeded; operator review required');return rows.map(x=>({json:{...x,mode:'watch'}}));")
w.sub('Observe registered exact Check','onticardsCheckObserveV1')
w.code('Keep verified watch outcomes',"return $input.all().filter(x=>['watching','invalidated'].includes(x.json.state)&&x.json.registration_key).map(x=>({json:x.json}));")
w.row('Persist observed Check state','upsert')
w.chain('Native five minute schedule','Ensure native Check registrations','Read registered watching Checks','Bounded native registered Checks','Observe registered exact Check','Keep verified watch outcomes','Persist observed Check state')
w.link('Trusted Check observation acceptance','Ensure native Check registrations')
w.save('check-watch.workflow.json',1200)
print(json.dumps({'observe_nodes':len(b.nodes),'register_nodes':len(r.nodes),'watch_nodes':len(w.nodes),'native_schedule_minutes':5,'model_or_test_runs':0,'registration_starts_tests':False}))
