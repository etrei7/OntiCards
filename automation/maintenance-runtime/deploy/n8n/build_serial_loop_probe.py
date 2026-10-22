"""Exercise the exact native loop and aggregation with synthetic two-thread input."""
import copy,json,uuid
from pathlib import Path
root=Path(__file__).parent
w=json.loads((root/'persistent-readonly-serial.workflow.json').read_text(encoding='utf-8'))
names=['Begin fixed repository poll','List all Issue and PR records','List all discussion comments','List all inline comments','List all PR heads','Read persisted thread snapshots','Validate lists and project thread targets','All list pages complete','Split thread targets','Loop one repository thread','Timeline needs fresh read','Reuse unchanged timeline snapshot','Prepare one timeline GET','Read complete thread timeline','Capture timeline with source thread','Only PR needs separate reviews','Reuse complete issue discussion pages','Prepare one review GET','Read reviews or issue discussion','Capture review with source thread','Validate all pages and prepare public records']
names+=['Issue metadata missing from full list','Prepare missing Issue metadata GET','Read missing Issue metadata','Bind fresh complementary Issue metadata','Reuse listed Issue or PR metadata','Select verified current thread','Current thread metadata complete','Preserve incomplete complementary thread']
w['id']='onticardsSerialLoopProbeV1';w['name']='OntiCards native two-thread serial loop fixture';w['nodes']=[n for n in w['nodes']if n['name']in names];w['active']=False
w['connections']={a:{'main':[[e for e in branch if e['node']in names]for branch in c['main']]}for a,c in w['connections'].items()if a in names}
def add(name,kind,p,version=1):
 w['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[len(w['nodes'])*190,0],'parameters':p})
def link(a,b,index=0):
 branches=w['connections'].setdefault(a,{'main':[]})['main']
 while len(branches)<=index:branches.append([])
 branches[index]=[{'node':b,'type':'main','index':0}]
add('Native serial loop fixture','webhook',{'httpMethod':'POST','path':'onticards-serial-loop-probe-v1','responseMode':'responseNode','options':{}},2.1)
w['nodes'][-1]['webhookId']='onticards-serial-loop-probe-v1'
issues=[{'id':n,'number':n,'title':'synthetic loop fixture','body':'synthetic','state':'open','created_at':'2026-10-22T12:30:00Z','updated_at':'2026-10-22T12:30:00Z','labels':[],'user':{'login':'synthetic-user','type':'User'}}for n in [90001,90002]]
issues[1]['pull_request']={'url':'https://api.github.com/repos/stepll2026/OntiCards/pulls/90002'}
closed={**issues[0],'id':90003,'number':90003,'state':'closed'}
comment={'id':50003,'body':'explicit synthetic missing-thread human input','created_at':'2026-10-22T12:30:00Z','updated_at':'2026-10-22T12:30:00Z','issue_url':'https://api.github.com/repos/stepll2026/OntiCards/issues/90003','user':{'login':'synthetic-user','type':'User'}}
for n in w['nodes']:
 n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+n['name']))
 if n['name']in names[1:5]:
  body=issues if n['name']==names[1]else([issues[1]]if n['name']==names[4]else[])
  n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':json.dumps({'complete':True,'pages':[{'statusCode':200,'body':body,'headers':{}}]}),'options':{}};n['retryOnFail']=False
  if n['name']==names[1]:n['parameters']['jsonOutput']='={{ {complete:true,pages:[{statusCode:200,headers:{},body:$("Native serial loop fixture").first().json.body.case==="empty_issues"?[]:'+json.dumps(body)+'}]} }}'
  if n['name']==names[2]:n['parameters']['jsonOutput']='={{ {complete:true,pages:[{statusCode:200,headers:{},body:$("Native serial loop fixture").first().json.body.case.startsWith("missing_")?'+json.dumps([comment])+':[]}]} }}'
 if n['name']=='Read persisted thread snapshots':n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':'{}','options':{}}
 if n['name']in ['Read complete thread timeline','Read reviews or issue discussion']:n['parameters']['workflowId']['value']='onticardsBoundedGetProbeChildV1'
 if n['name']=='Prepare one timeline GET':n['parameters']['jsonOutput']='={{ {url:"http://127.0.0.1:18127/webhook/onticards-get-fixture-v1?mode=valid&key=loop-"+$execution.id+"-timeline-"+$json.number,deadline:Date.now()+30000,token:""} }}'
 if n['name']=='Prepare one review GET':n['parameters']['jsonOutput']='={{ {url:"http://127.0.0.1:18127/webhook/onticards-get-fixture-v1?mode=valid&key=loop-"+$execution.id+"-review-"+$json.thread.number,deadline:Date.now()+30000,token:""} }}'
 if n['name']=='Prepare missing Issue metadata GET':n['parameters']['jsonOutput']='={{ {fixture:true} }}'
 if n['name']=='Read missing Issue metadata':n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':'={{ {statusCode:$("Native serial loop fixture").first().json.body.case==="missing_failed"?503:200,body:'+json.dumps(closed)+'} }}','options':{}};n['retryOnFail']=False
add('Verify installation repository','set',{'mode':'raw','jsonOutput':'={{ {body:{repositories:[{open_issues_count:$("Native serial loop fixture").first().json.body.case==="count_mismatch"?3:2}]}} }}','options':{}},3.4)
add('Return actual loop result','respondToWebhook',{'respondWith':'json','responseBody':'={{ {fixture:true,complete:$json.complete,thread_count:$json.threads?.length||0,event_count:$json.events?.length||0,event_thread_keys:($json.events||[]).map(e=>e.thread_key),event_ids:($json.events||[]).map(e=>e.event_id),diagnostics:$json.diagnostics||[],timeline_pages:$json.timeline_pages||0,review_pages:$json.review_pages||0,github_requests:0,model_requests:0} }}','options':{}},1.4)
chain=['Native serial loop fixture','Verify installation repository']+names[:5]+['Read persisted thread snapshots','Validate lists and project thread targets']
for a,b in zip(chain,chain[1:]):link(a,b)
link('All list pages complete','Return actual loop result',1);link('Validate all pages and prepare public records','Return actual loop result')

# Lifecycle/review events reuse the production aggregation. Only transport replies
# are frozen; no remote service, credentials, model, or public writes are present.
for n in w['nodes']:
 if n['name']=='Return actual loop result':
  n['parameters']['responseBody']=n['parameters']['responseBody'].replace('event_ids:','events:($json.events||[]).map(e=>({id:e.event_id,kind:e.kind,status:e.status,thread_key:e.thread_key})),threads:($json.threads||[]).map(t=>JSON.parse(t.snapshot)),event_ids:')
 if n['name']=='Read complete thread timeline':
  n['type']='n8n-nodes-base.set';n['typeVersion']=3.4
  n['parameters']={'mode':'raw','jsonOutput':'''={{ (()=>{const q=$('Native serial loop fixture').first().json.body,n=$('Loop one repository thread').item.json.number;return {complete:true,pages:[{statusCode:200,headers:{},body:q.case==='lifecycle'?[{id:n*10+1,event:'closed',created_at:'2026-10-22T12:31:00Z',actor:{login:'fixture-human',type:'User'}},{id:n*10+2,event:'reopened',created_at:'2026-10-22T12:32:00Z',actor:{login:'fixture-human',type:'User'}}]:[{fixture:true}]}]};})() }}''','options':{}}
 if n['name']=='Read reviews or issue discussion':
  n['type']='n8n-nodes-base.set';n['typeVersion']=3.4
  n['parameters']={'mode':'raw','jsonOutput':'''={{ {complete:true,pages:[{statusCode:200,headers:{},body:$('Native serial loop fixture').first().json.body.case==='lifecycle'?[{id:70001,body:'synthetic review text',state:'CHANGES_REQUESTED',submitted_at:'2026-10-22T12:33:00Z',commit_id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',user:{login:'fixture-reviewer',type:'User'}}]:[{fixture:true}]}]} }}''','options':{}}
 if n['name']=='List all discussion comments':
  old=n['parameters']['jsonOutput'][3:-2]
  n['parameters']['jsonOutput']='={{ $("Native serial loop fixture").first().json.body.case==="lifecycle"?{complete:true,pages:[{statusCode:200,headers:{},body:[{id:60001,body:"synthetic human followup",updated_at:"2026-10-22T12:34:00Z",issue_url:"https://api.github.com/repos/stepll2026/OntiCards/issues/90001",user:{login:"fixture-human",type:"User"}},{id:60002,body:"synthetic app response",updated_at:"2026-10-22T12:35:00Z",issue_url:"https://api.github.com/repos/stepll2026/OntiCards/issues/90002",user:{id:346235449,login:"onticards-maintainer-stepll2026[bot]",type:"Bot"}}]}]}:('+old+') }}'
 if n['name']=='List all inline comments':
  n['parameters']['jsonOutput']='={{ {complete:true,pages:[{statusCode:200,headers:{},body:$("Native serial loop fixture").first().json.body.case==="lifecycle"?[{id:80001,body:"synthetic inline comment",updated_at:"2026-10-22T12:34:00Z",pull_request_url:"https://api.github.com/repos/stepll2026/OntiCards/pulls/90002",path:"app.py",line:8,commit_id:"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",user:{login:"fixture-reviewer",type:"User"}}]:[]}]} }}'

# Exact CI projection expression with frozen native DataTable-shaped inputs.
ci=json.loads((root/'intake-ci-handoff.workflow.json').read_text(encoding='utf-8'))
add('CI projection fixture input','webhook',{'httpMethod':'POST','path':'onticards-ci-projection-probe-v1','responseMode':'responseNode','options':{}},2.1)
w['nodes'][-1]['webhookId']='onticards-ci-projection-probe-v1'
add('Native complete intake handoff','set',{'mode':'raw','jsonOutput':'={{ {poll_id:"fixture-poll",status:$("CI projection fixture input").first().json.body.case==="incomplete"?"incomplete_no_watermark_advance":"complete_readonly_dry_run",started_at:$now.toISO(),finished_at:$now.toISO(),details:JSON.stringify({watermark:$now.toISO(),token_revoked:$("CI projection fixture input").first().json.body.case!=="unrevoked"})} }}','options':{}},3.4)
add('Trusted CI handoff configuration','set',{'mode':'raw','jsonOutput':'{"mode":"dry_run","max_open_prs":20,"freshness_seconds":600}','options':{}},3.4)
add('Read committed intake watermark','set',{'mode':'raw','jsonOutput':'={{ {repository:"stepll2026/OntiCards",poll_id:$("CI projection fixture input").first().json.body.case==="wrong_poll"?"other":"fixture-poll",watermark:JSON.parse($("Native complete intake handoff").first().json.details).watermark,thread_count:$("CI projection fixture input").first().json.body.case==="count_mismatch"?2:1} }}','options':{}},3.4)
add('Read current intake threads for CI','set',{'mode':'raw','jsonOutput':'={{ (()=>{const c=$("CI projection fixture input").first().json.body.case;return {thread_key:"stepll2026/OntiCards#90002",number:90002,kind:c==="issue"?"issue":"pull_request",observed_at:$("Native complete intake handoff").first().json.started_at,snapshot:JSON.stringify({number:90002,kind:"pull_request",state:c==="closed"?"closed":"open",head:c==="bad_sha"?"bad":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",base:"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",body:"MUST_NOT_LEAVE_INTAKE",discussion:[{body:"MUST_NOT_LEAVE_INTAKE"}]})};})() }}','options':{}},3.4)
actual=copy.deepcopy(next(n for n in ci['nodes']if n['name']=='Project complete public PR revisions'));actual['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+actual['name']));w['nodes'].append(actual)
add('Return actual CI projection','respondToWebhook',{'respondWith':'json','responseBody':'={{ $json }}','options':{}},1.4)
c=['CI projection fixture input','Native complete intake handoff','Trusted CI handoff configuration','Read committed intake watermark','Read current intake threads for CI','Project complete public PR revisions','Return actual CI projection']
for a,b in zip(c,c[1:]):link(a,b)

# Multi-row input reproduces the observed Set fanout boundary. Use the exact
# production executeOnce flags and HTTP node, changing only localhost transport.
for n in w['nodes']:
 if n['name']=='Read committed intake watermark':
  n['parameters']['jsonOutput']=n['parameters']['jsonOutput'].replace('case==="count_mismatch"?2:1','case==="oversize"?21:["count_mismatch","multiple"].includes($("CI projection fixture input").first().json.body.case)?2:1')
 if n['name']=='Read current intake threads for CI':
  n['name']='Prepare frozen CI rows';n['parameters']['jsonOutput']='={{ (()=>{const c=$("CI projection fixture input").first().json.body.case,count=c==="oversize"?21:c==="multiple"?2:1;return {rows:Array.from({length:count},(_,i)=>({thread_key:"stepll2026/OntiCards#"+(90002+i),number:90002+i,kind:c==="issue"?"issue":"pull_request",observed_at:$("Native complete intake handoff").first().json.started_at,snapshot:JSON.stringify({number:90002+i,kind:"pull_request",state:c==="closed"?"closed":"open",head:c==="bad_sha"?"bad":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",base:"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",body:"MUST_NOT_LEAVE_INTAKE",discussion:[{body:"MUST_NOT_LEAVE_INTAKE"}]})}))};})() }}'
add('Read current intake threads for CI','splitOut',{'fieldToSplitOut':'rows','options':{}},1)
link('Read committed intake watermark','Prepare frozen CI rows');link('Prepare frozen CI rows','Read current intake threads for CI');link('Read current intake threads for CI','Project complete public PR revisions')
gate=copy.deepcopy(next(n for n in ci['nodes']if n['name']=='Complete revoked bounded snapshot only'));w['nodes'].append(gate)
http=copy.deepcopy(next(n for n in ci['nodes']if n['name']=='Send snapshot to existing trusted CI'));http['parameters']['url']='http://127.0.0.1:18127/webhook/onticards-ci-count-fixture-v1';http['parameters'].pop('authentication',None);http['parameters'].pop('genericAuthType',None);http.pop('credentials',None);w['nodes'].append(http)
add('Return actual single POST result','respondToWebhook',{'respondWith':'json','responseBody':'={{ {eligible:true,payload:$("Project complete public PR revisions").first().json.payload,project_items:$("Project complete public PR revisions").all().length,transport_items:$input.all().length,post_count:Math.max(...$input.all().map(x=>x.json.body?.post_count||0)),github_requests:0,model_requests:0} }}','options':{}},1.4)
link('Project complete public PR revisions','Complete revoked bounded snapshot only');link('Complete revoked bounded snapshot only','Send snapshot to existing trusted CI');link('Complete revoked bounded snapshot only','Return actual CI projection',1);link('Send snapshot to existing trusted CI','Return actual single POST result')
add('Local CI count transport','webhook',{'httpMethod':'POST','path':'onticards-ci-count-fixture-v1','responseMode':'responseNode','options':{}},2.1)
w['nodes'][-1]['webhookId']='onticards-ci-count-fixture-v1'
add('Ensure CI POST counters','dataTable',{'resource':'table','operation':'create','tableName':'fixture_intake_ci_posts_v1','columns':{'column':[{'name':'watermark','type':'string'},{'name':'post_count','type':'number'}]},'options':{'createIfNotExists':True}},1.1)
counter={'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':'fixture_intake_ci_posts_v1','mode':'name'},'matchType':'allConditions','filters':{'conditions':[{'keyName':'watermark','condition':'eq','keyValue':'={{ $("Local CI count transport").first().json.body.watermark }}'}]},'returnAll':True}
add('Read CI POST count','dataTable',counter,1.1);w['nodes'][-1]['alwaysOutputData']=True
add('Increment actual native CI POST count','set',{'mode':'raw','jsonOutput':'={{ {watermark:$("Local CI count transport").first().json.body.watermark,post_count:Number($json.post_count||0)+1} }}','options':{}},3.4)
counter=copy.deepcopy(counter);counter['operation']='upsert';counter.pop('returnAll');counter['columns']={'mappingMode':'autoMapInputData','value':{},'schema':[]};counter['options']={}
add('Persist actual native CI POST count','dataTable',counter,1.1)
add('Return local CI transport count','respondToWebhook',{'respondWith':'json','responseBody':'={{ {post_count:$json.post_count} }}','options':{}},1.4)
for a,b in zip(['Local CI count transport','Ensure CI POST counters','Read CI POST count','Increment actual native CI POST count','Persist actual native CI POST count'],['Ensure CI POST counters','Read CI POST count','Increment actual native CI POST count','Persist actual native CI POST count','Return local CI transport count']):link(a,b)
# Reuse this existing localhost native counter to verify one bounded balance read
# for six PR items. Actual receiver/admission Code and If nodes are copied exactly;
# only NewAPI transport/account data is replaced by the existing native HTTP fixture.
batch=json.loads((root.parent/'n8n-preview-ci/intake-receiver.workflow.json').read_text())
admission=json.loads((root.parent/'n8n-preview-ci/intake-admission.workflow.json').read_text())
add('Batch balance fixture','webhook',{'httpMethod':'POST','path':'onticards-batch-budget-probe-v1','responseMode':'responseNode','options':{}},2.1)
w['nodes'][-1]['webhookId']='onticards-batch-budget-probe-v1'
add('Prepare six actual input items','set',{'mode':'raw','jsonOutput':'={{ {rows:Array.from({length:6},(_,i)=>({pr:90001+i,head:"a".repeat(40),base:"b".repeat(40),mode:$("Batch balance fixture").first().json.body.case==="dry_run"?"dry_run":"dispatch",watermark:$now.toISO(),observed_at:$now.toISO()}))} }}','options':{}},3.4)
add('Validate complete existing snapshot','splitOut',{'fieldToSplitOut':'rows','options':{}},1)
add('Prepare prior batch receipts','set',{'mode':'raw','jsonOutput':'={{ {rows:$("Batch balance fixture").first().json.body.case==="consumed"?$("Validate complete existing snapshot").all().map(x=>({receipt_key:`admission:stepll2026/OntiCards#${x.json.pr}:${x.json.head}:${x.json.base}`,state:"budget_exhausted"})):[{}]} }}','options':{}},3.4);w['nodes'][-1]['executeOnce']=True
add('Read existing batch CI receipts','splitOut',{'fieldToSplitOut':'rows','options':{}},1)
for name in ['Select bounded unseen batch budget need','Only unseen real batch needs balance','Skip balance for dry run or consumed batch','Bind native observation to exact batch']:
 w['nodes'].append(copy.deepcopy(next(n for n in batch['nodes']if n['name']==name)))
balance=copy.deepcopy(http);balance['name']='Read one native balance per complete batch';balance['parameters']['jsonBody']='={{ {watermark:$("Select bounded unseen batch budget need").first().json.candidates[0].watermark} }}';w['nodes'].append(balance)
add('Frozen native balance observation','set',{'mode':'raw','jsonOutput':'={{ {stdout:JSON.stringify({state:"budget_exhausted",required_quota:45000,remaining_quota:15445,checked_at:$("Batch balance fixture").first().json.body.case==="stale"?new Date(Date.now()-300001).toISOString():new Date().toISOString(),token_creation_calls:0,provider_calls:0,account_quota_reset:false}),post_count:$json.body.post_count} }}','options':{}},3.4)
add('Preserve fresh scope verdict','code',{'jsCode':'''const p=$('Bind native observation to exact batch').first().json,c=$('Batch balance fixture').first().json.body.case;return [{json:{...p,current:true,revision_token_revoked:true,batch_budget:{...p.batch_budget,...(c==='cross_batch'?{watermark:'different'}:{})}}}];'''},2)
w['nodes'].append(copy.deepcopy(next(n for n in admission['nodes']if n['name']=='Determine native admission')))
add('Return batch native boundary proof','respondToWebhook',{'respondWith':'json','responseBody':'={{ {case:$("Batch balance fixture").first().json.body.case,candidate_items:$("Validate complete existing snapshot").all().length,bound_items:$("Bind native observation to exact batch").all().length,needed:$("Select bounded unseen batch budget need").first().json.needed,transport_count:$("Read one native balance per complete batch").isExecuted?$("Read one native balance per complete batch").all().length:0,post_count:$("Frozen native balance observation").isExecuted?$("Frozen native balance observation").first().json.post_count:0,state:$json.state,allowed:$json.allowed,budget:$json.budget,models:0,github_requests:0} }}','options':{}},1.4)
chain=['Batch balance fixture','Prepare six actual input items','Validate complete existing snapshot','Prepare prior batch receipts','Read existing batch CI receipts','Select bounded unseen batch budget need','Only unseen real batch needs balance','Read one native balance per complete batch','Frozen native balance observation','Bind native observation to exact batch','Preserve fresh scope verdict','Determine native admission','Return batch native boundary proof']
for a,b in zip(chain,chain[1:]):link(a,b)
link('Only unseen real batch needs balance','Skip balance for dry run or consumed batch',1);link('Skip balance for dry run or consumed batch','Bind native observation to exact batch')
def spacing(v):
 if isinstance(v,dict):return {k:spacing(x)for k,x in v.items()}
 if isinstance(v,list):return [spacing(x)for x in v]
 if isinstance(v,str)and v.startswith('={{'):
  inner=v[3:-2]
  while '}}'in inner:inner=inner.replace('}}','} }')
  return '={{'+inner+'}}'
 return v
for n in w['nodes']:n['parameters']=spacing(n['parameters']);n.pop('credentials',None)
for n in w['nodes']:n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+n['name']))
assert len({n['id']for n in w['nodes']})==len(w['nodes'])
(root/'serial-loop-probe.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'github_requests':0,'model_requests':0,'fixture_threads':2}))
