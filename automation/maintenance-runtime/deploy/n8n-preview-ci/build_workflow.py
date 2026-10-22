"""Generate an inactive native n8n subworkflow; caller remains the existing PR intake."""
import json
from pathlib import Path
import uuid

root=Path(__file__).resolve().parent
nodes=[];connections={}
def node(name,kind,parameters,version=1,**extra):
    nodes.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'onticards-preview-v1/'+name)),'name':name,
                  'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[len(nodes)*220,0],'parameters':parameters,**extra})
def link(a,b):connections[a]={'main':[[{'node':b,'type':'main','index':0}]]}
node('Existing trusted PR intake','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
node('Validate fixed input','code',{'jsCode':'''const input=$input.first().json,p=input.body??input;
if(!Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??''))throw new Error('Invalid fixed PR identity');
return [{json:{pr:p.pr,head:p.head,base:p.base,...(p.validation_only===true?{validation_only:true}:{}),receipt_key:`stepll2026/OntiCards#${p.pr}:${p.head}:${p.base}`}}];'''},2)
node('Read current PR','executeWorkflow',{'workflowId':{'__rl':True,'value':'onticardsPreviewRevisionV1','mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}},1.3,onError='continueRegularOutput')
node('Reject forks or stale revision','code',{'jsCode':'''const r=$input.first().json,p=$('Validate fixed input').first().json;
if(r.current!==true||r.token_revoked!==true||r.head!==p.head||r.base!==p.base)throw new Error('PR scope/revision rejected');
return [{json:p}];'''},2)
node('Ensure native receipt table','dataTable',{'resource':'table','operation':'create','tableName':'onticards_ci_receipts_v1',
    'columns':{'column':[{'name':name,'type':kind} for name,kind in [('receipt_key','string'),('head','string'),('base','string'),('state','string'),('detail','string'),('pr','number')]]},
    'options':{'createIfNotExists':True}},1.1)
table={'__rl':True,'value':'onticards_ci_receipts_v1','mode':'name'}
node('Read native receipt','dataTable',{'resource':'row','operation':'get','dataTableId':table,'matchType':'allConditions',
    'filters':{'conditions':[{'keyName':'receipt_key','condition':'eq','keyValue':"={{ $('Reject forks or stale revision').first().json.receipt_key }}"}]},'returnAll':True},1.1,alwaysOutputData=True)
node('Stop previously consumed revision','code',{'jsCode':'''const rows=$input.all().map(i=>i.json);if(rows.some(r=>r.receipt_key))return [];
const p=$('Reject forks or stale revision').first().json;return [{json:{...p,state:'running',detail:'native fixed preview; same head/base consumed before side effects'}}];'''},2)
def upsert(name):
    node(name,'dataTable',{'resource':'row','operation':'upsert','dataTableId':table,'matchType':'allConditions',
        'filters':{'conditions':[{'keyName':'receipt_key','condition':'eq','keyValue':"={{ $json.receipt_key }}"}]},
        'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
upsert('Persist before native execution')
node('Fixed OpenSSH build transfer test','executeCommand',{'executeOnce':True,'command':"=node /opt/onticards-preview-ci/bundle/dispatch.mjs {{ $('Reject forks or stale revision').first().json.pr }} {{ $('Reject forks or stale revision').first().json.head }} {{ $('Reject forks or stale revision').first().json.base }}"},1,onError='continueRegularOutput')
node('Capture bounded result','code',{'jsCode':'''const p=$('Reject forks or stale revision').first().json,r=$input.first().json;let result;
try{result=JSON.parse(r.stdout??'');}catch{result={state:'transport_or_execution_failed'};}
return [{json:{...p,state:result.state??'failed',detail:JSON.stringify(result)}}];'''},2)
node('Read PR after tests','executeWorkflow',{'workflowId':{'__rl':True,'value':'onticardsPreviewRevisionV1','mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}},1.3,onError='continueRegularOutput')
node('Mark stale or unavailable result','code',{'jsCode':'''const p=$('Final native outcome').first().json,r=$input.first().json;
if(r.current!==true||r.token_revoked!==true||r.head!==p.head||r.base!==p.base)p.state='stale_or_remote_unverifiable';return [{json:p}];'''},2)
upsert('Persist native outcome')
for left,right in zip(nodes,nodes[1:]):link(left['name'],right['name'])
node('Model after non-model success','if',{'conditions':{'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict'},
    'conditions':[{'id':'model-gate','leftValue':'={{ $json.state }}','rightValue':'tests_passed_partial_model_unverified','operator':{'type':'string','operation':'equals'}}],'combinator':'and'},'options':{}},2.2)
node('Read PR before model','executeWorkflow',{'workflowId':{'__rl':True,'value':'onticardsPreviewRevisionV1','mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}},1.3,onError='continueRegularOutput')
node('Require current model revision','code',{'jsCode':"const r=$input.first().json,p=$('Capture bounded result').first().json;if(r.current!==true||r.token_revoked!==true||r.head!==p.head||r.base!==p.base)throw new Error('Model not started: revision unverified');return [{json:p}];"},2)
node('Explicit bounded model phase','executeCommand',{'executeOnce':True,'command':"=node /opt/onticards-preview-ci/bundle/dispatch_model.mjs {{ $('Reject forks or stale revision').first().json.pr }} {{ $('Reject forks or stale revision').first().json.head }} {{ $('Reject forks or stale revision').first().json.base }}"},1,onError='continueRegularOutput')
node('Capture model outcome','code',{'jsCode':'''const p=$('Capture bounded result').first().json,r=$input.first().json;let result;
try{result=JSON.parse(r.stdout??'');}catch{result={state:'model_phase_transport_or_execution_failed'};}
return [{json:{...p,state:result.state??'failed',detail:JSON.stringify({non_model:JSON.parse(p.detail),model:result})}}];'''},2)
node('Final native outcome','code',{'jsCode':'return $input.all();'},2)
link('Capture bounded result','Model after non-model success')
connections['Model after non-model success']={'main':[[{'node':'Read PR before model','type':'main','index':0}],[{'node':'Final native outcome','type':'main','index':0}]]}
link('Read PR before model','Require current model revision');link('Require current model revision','Explicit bounded model phase');link('Explicit bounded model phase','Capture model outcome');link('Capture model outcome','Final native outcome');link('Final native outcome','Read PR after tests')
node('Trusted intake webhook','webhook',{'httpMethod':'POST','path':'onticards-fixed-preview-v1','authentication':'headerAuth','responseMode':'onReceived','options':{}},2.1,
     credentials={'httpHeaderAuth':{'name':'onticards-preview-trigger'}},webhookId='onticards-fixed-preview-v1')
link('Trusted intake webhook','Validate fixed input')
node('Validation only entry','if',{'conditions':{'options':{'typeValidation':'strict'},'conditions':[{'id':'validation-only','leftValue':'={{ $json.validation_only === true }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
node('Return validation only proof','code',{'jsCode':"const p=$input.first().json;return [{json:{pr:p.pr,head:p.head,base:p.base,state:'dry_run_ci_entry_verified',validation_only:true,ssh_commands:0,model_calls:0,receipt_consumed:false}}];"},2)
link('Reject forks or stale revision','Validation only entry')
connections['Validation only entry']={'main':[[{'node':'Return validation only proof','type':'main','index':0}],[{'node':'Ensure native receipt table','type':'main','index':0}]]}
workflow={'id':'onticardsFixedPreviewV1','name':'OntiCards fixed rootless preview v1','active':False,'nodes':nodes,'connections':connections,
          'settings':{'executionOrder':'v1','executionTimeout':7200,'saveExecutionProgress':True},'pinData':{},
          'meta':{'templateCredsSetupCompleted':False,'readiness':'fixed SSH/rootless/trusted test image verified; native PR acceptance and intake wiring pending'}}
(root/'preview.workflow.json').write_text(json.dumps(workflow,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nodes':len(nodes),'active':False,'github_mutations':0,'new_scheduler':False}))
