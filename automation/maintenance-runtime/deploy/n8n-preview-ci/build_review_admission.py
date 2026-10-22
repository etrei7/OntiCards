"""Native n8n per-version review admission; no schedule, model, parser or publisher."""
import json,uuid
from pathlib import Path
ROOT=Path(__file__).parent
ID='onticardsReviewAdmissionV1'
nodes=[];connections={}
def node(name,kind,p,version=1,**extras):
 nodes.append(dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,ID+'/'+name)),name=name,type='n8n-nodes-base.'+kind,typeVersion=version,position=[len(nodes)*220,0],parameters=p,**extras))
def code(name,source):node(name,'code',{'jsCode':source},2)
def link(a,b,i=0):
 branches=connections.setdefault(a,{'main':[]})['main']
 while len(branches)<=i:branches.append([])
 branches[i]=[{'node':b,'type':'main','index':0}]
def chain(*items):
 for a,b in zip(items,items[1:]):link(a,b)
def iff(name,expression):node(name,'if',{'conditions':{'options':{'typeValidation':'strict'},'conditions':[{'id':name,'leftValue':expression,'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
table={'__rl':True,'value':'onticards_pr_reviews_v1','mode':'name'}
def persist(name):node(name,'dataTable',{'resource':'row','operation':'upsert','dataTableId':table,'matchType':'allConditions','filters':{'conditions':[{'keyName':'review_key','condition':'eq','keyValue':'={{ $json.review_key }}'}]},'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
node('Existing complete intake candidate','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
code('Validate fixed review candidate',"""const p=$input.first().json;
if(!Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??''))throw new Error('Invalid review version');
// This literal is operator configuration; webhook/PR input cannot choose it.
const trusted_mode='dry_run';
return [{json:{repository:'stepll2026/OntiCards',pr:p.pr,head:p.head,base:p.base,mode:trusted_mode,observed_at:p.observed_at??null}}];""")
node('Native exact review identity hash','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':"={{ JSON.stringify([$json.repository,$json.pr,$json.head,$json.base]) }}",'dataPropertyName':'version_hash','encoding':'hex'},2)
code('Set fixed native key',"const p=$input.first().json;if(!/^[a-f0-9]{64}$/.test(p.version_hash??''))throw new Error('Invalid version hash');return [{json:{...p,review_key:'review-'+p.version_hash}}];")
node('Ensure native permanent review receipts','dataTable',{'resource':'table','operation':'create','tableName':'onticards_pr_reviews_v1','columns':{'column':[{'name':n,'type':t} for n,t in [('review_key','string'),('pr','number'),('head','string'),('base','string'),('state','string'),('detail','string')]]},'options':{'createIfNotExists':True}},1.1)
node('Read native version admission','dataTable',{'resource':'row','operation':'get','dataTableId':table,'matchType':'allConditions','filters':{'conditions':[{'keyName':'review_key','condition':'eq','keyValue':"={{ $('Set fixed native key').first().json.review_key }}"}]},'returnAll':True},1.1,alwaysOutputData=True)
code('Preserve every consumed outcome',"const p=$('Set fixed native key').first().json;const rows=$input.all().map(x=>x.json).filter(x=>x.review_key===p.review_key);return [{json:{...p,consumed:rows.length>0,prior_states:rows.map(r=>r.state)}}];")
iff('Unseen or dry verification',"={{ $json.mode === 'dry_run' || $json.consumed === false }}")
code('Return permanent prior outcome',"const p=$input.first().json;return [{json:{pr:p.pr,head:p.head,base:p.base,state:'already_consumed',prior_states:p.prior_states,automatic_retry:false,model_started:p.prior_states.every(s=>s==='baseline')?false:null,new_submission:false}}];")
iff('Persist only real admission',"={{ $json.mode !== 'dry_run' }}")
code('Prepare permanent admission before SSH',"const p=$input.first().json;return [{json:{review_key:p.review_key,pr:p.pr,head:p.head,base:p.base,state:p.mode==='baseline'?'baseline':'admitted',detail:JSON.stringify({at:new Date().toISOString(),source:'onticards_intake_threads_v1',observed_at:p.observed_at,automatic_retry:false,model_started:p.mode==='baseline'?false:null})}}];")
persist('Persist admitted before any mutation')
iff('Baseline never invokes SSH',"={{ $('Set fixed native key').first().json.mode === 'review' }}")
node('Native fixed SSH review capability','executeCommand',{'executeOnce':True,'command':"=node /opt/onticards-preview-ci/bundle/dispatch_review.mjs {{ $('Set fixed native key').first().json.pr }} {{ $('Set fixed native key').first().json.head }} {{ $('Set fixed native key').first().json.base }} {{ $('Set fixed native key').first().json.mode }}"},1,onError='continueRegularOutput')
code('Project actual fixed capability receipt',"""const p=$('Set fixed native key').first().json;let r;
try{r=JSON.parse($input.first().json.stdout??'');}catch{r=null;}
const match=r&&r.repository===p.repository&&r.pr===p.pr&&r.head===p.head&&r.base===p.base&&r.idempotency_key===p.review_key&&r.mode===p.mode;
const result=match?r:{state:'submission_outcome_unknown',model_started:p.mode==='review'?null:false,automatic_retry:false};
return [{json:{review_key:p.review_key,pr:p.pr,head:p.head,base:p.base,state:typeof result.state==='string'?result.state:'submission_outcome_unknown',detail:JSON.stringify({...result,observed_at:new Date().toISOString(),automatic_retry:false})}}];""")
iff('Store only real terminal observation',"={{ $('Set fixed native key').first().json.mode === 'review' }}")
code('Dry probe cannot consume real admission',"const p=$input.first().json;return [{json:{...p,review_key:'probe:'+p.review_key}}];")
persist('Persist actual outcome without retries')
code('Safe review receipt',"return $input.all().map(x=>({json:x.json}));")
chain('Existing complete intake candidate','Validate fixed review candidate','Native exact review identity hash','Set fixed native key','Ensure native permanent review receipts','Read native version admission','Preserve every consumed outcome','Unseen or dry verification','Persist only real admission','Prepare permanent admission before SSH','Persist admitted before any mutation','Baseline never invokes SSH','Native fixed SSH review capability','Project actual fixed capability receipt','Store only real terminal observation','Persist actual outcome without retries','Safe review receipt')
link('Baseline never invokes SSH','Safe review receipt',1)
link('Unseen or dry verification','Return permanent prior outcome',1)
link('Persist only real admission','Native fixed SSH review capability',1)
link('Store only real terminal observation','Dry probe cannot consume real admission',1)
link('Dry probe cannot consume real admission','Persist actual outcome without retries')
workflow={'id':ID,'name':'OntiCards native automatic semantic review admission','active':False,'nodes':nodes,'connections':connections,'settings':{'executionOrder':'v1','executionTimeout':300,'saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False},'pinData':{}}
(ROOT/'review-admission.workflow.json').write_text(json.dumps(workflow,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nodes':len(nodes),'schedule_triggers':0,'mode':'dry_run','active':False}))
