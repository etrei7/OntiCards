"""Reuse native subworkflow retries for one bounded idempotent GitHub GET."""
import copy,json,uuid
from pathlib import Path
root=Path(__file__).parent
raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':35}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
b=Builder('onticardsBoundedGetV1')
b.node('Native single GET input','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
b.set('Validate bounded fixed repository GET','={{ (()=>{const u=String($json.url),deadline=Number($json.deadline);if(!u.startsWith("https://api.github.com/repos/stepll2026/OntiCards/")||u.includes("#"))throw new Error("GET outside fixed repository");if(!Number.isFinite(deadline)||Date.now()>=deadline||deadline>Date.now()+240000)throw new Error("GET poll deadline expired");return {url:u,deadline,token:$json.token};})() }}')
p={'method':'GET','url':'={{ $json.url }}','sendHeaders':True,'headerParameters':{'parameters':[{'name':'Authorization','value':'={{ "Bearer "+$json.token }}'},{'name':'Accept','value':'application/vnd.github+json'},{'name':'X-GitHub-Api-Version','value':'2026-03-10'}]},'options':{'proxy':'http://127.0.0.1:17891','timeout':'={{ Math.max(1,Math.min(20000,$json.deadline-Date.now())) }}','response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}},'pagination':{'pagination':{'paginationMode':'responseContainsNextURL','nextURL':r'''={{ (()=>{const u=($response.headers.link||'').match(/<([^>]+)>;\s*rel="next"/)?.[1]||'';if(u&&!u.startsWith('https://api.github.com/repos/stepll2026/OntiCards/'))throw new Error('Pagination left fixed repository');return u;})() }}''','paginationCompleteWhen':'other','completeExpression':'={{ !($response.headers.link||"").includes(\'rel="next"\') }}','limitPagesFetched':True,'maxRequests':50,'requestInterval':100}}}}
b.node('One native GET attempt','httpRequest',p,4.4,retryOnFail=False,onError='stopWorkflow')
b.node('Require complete array pages','set',{'mode':'raw','jsonOutput':'={{ (()=>{const pages=$input.all().map(i=>i.json);if(!pages.length||pages.some(p=>p.statusCode!==200||!Array.isArray(p.body))||String(pages.at(-1).headers?.link||"").includes(\'rel="next"\'))throw new Error("GET response incomplete or non-array");return {pages,complete:true};})() }}','options':{}},3.4,executeOnce=True)
b.chain(['Native single GET input','Validate bounded fixed repository GET','One native GET attempt','Require complete array pages'])
w=b.workflow('OntiCards bounded single-repository GET')
(root/'bounded-get.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')

# Native loop serializes targets; native Execute Workflow retries this GET-only child twice.
parent=json.loads((root/'persistent-readonly.workflow.json').read_text(encoding='utf-8'))
def node(name):return next(n for n in parent['nodes']if n['name']==name)
def append(name,kind,parameters,version=1,**extra):
 entry={'id':str(__import__('uuid').uuid5(__import__('uuid').NAMESPACE_URL,parent['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'parameters':parameters,'position':[len(parent['nodes'])*190,0],**extra};parent['nodes'].append(entry);return entry
append('Loop one repository thread','splitInBatches',{'batchSize':1,'options':{}},3)
append('Read persisted thread snapshots','dataTable',{'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':'onticards_intake_threads_v1','mode':'name'},'returnAll':True},1.1,alwaysOutputData=True,executeOnce=True)
append('Timeline needs fresh read','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'timeline-needed','leftValue':'={{ $json.timeline_needed }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
append('Reuse unchanged timeline snapshot','set',{'mode':'raw','jsonOutput':'={{ {complete:true,pages:[{statusCode:200,headers:{},body:$json.cached.timeline}]} }}','options':{}},3.4)
append('Only PR needs separate reviews','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'is-pr','leftValue':'={{ $json.thread.kind === "pull_request" }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
append('Reuse complete issue discussion pages','set',{'mode':'raw','jsonOutput':'={{ {complete:true,pages:[{statusCode:200,headers:{},body:$("List all discussion comments").first().json.pages.flatMap(p=>p.body).filter(c=>c.issue_url==="https://api.github.com/repos/stepll2026/OntiCards/issues/"+$json.thread.number)}]} }}','options':{}},3.4)
def prepare(name,url):
 append(name,'set',{'mode':'raw','jsonOutput':'={{ {url:'+url+',deadline:Date.parse($("Begin fixed repository poll").first().json.started_at)+240000,token:$("Mint read-only token").first().json.body.token} }}','options':{}},3.4)
prepare('Prepare one timeline GET','"https://api.github.com/repos/stepll2026/OntiCards/issues/"+$json.number+"/timeline?per_page=100"')
prepare('Prepare one review GET','"https://api.github.com/repos/stepll2026/OntiCards"+($json.thread.kind==="pull_request"?"/pulls/":"/issues/")+$json.thread.number+($json.thread.kind==="pull_request"?"/reviews?per_page=100":"/comments?per_page=100")')
for name in ['Read complete thread timeline','Read reviews or issue discussion']:
 n=node(name);n['type']='n8n-nodes-base.executeWorkflow';n['typeVersion']=1.3;n['parameters']={'workflowId':{'__rl':True,'value':'onticardsBoundedGetV1','mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}};n.update(executeOnce=True,retryOnFail=True,maxTries=2,waitBetweenTries=500,onError='continueRegularOutput')
node('Capture timeline with source thread')['parameters']['jsonOutput']='={{ {thread:$("Loop one repository thread").item.json,pages:$json.complete?$json.pages:[{statusCode:null,body:null,headers:{},bounded_get_failed:true}]} }}'
node('Capture review with source thread')['parameters']['jsonOutput']='={{ {thread:$("Capture timeline with source thread").item.json.thread,timeline_pages:$("Capture timeline with source thread").item.json.pages,review_pages:$json.complete?$json.pages:[{statusCode:null,body:null,headers:{},bounded_get_failed:true}]} }}'
validate=node('Validate all pages and prepare public records')['parameters']['jsonOutput']
validate=validate.replace("const timelines=$('Capture timeline with source thread').all().map(x=>x.json),reviews=$input.all().map(x=>x.json);","const combined=$input.all().map(x=>x.json);const timelines=combined.flatMap(x=>x.timeline_pages.map(page=>({thread:x.thread,page}))),reviews=combined.flatMap(x=>x.review_pages.map(page=>({thread:x.thread,page}))); ")
node('Validate all pages and prepare public records')['parameters']['jsonOutput']=validate
def link(a,b,index=0):
 c=parent['connections'].setdefault(a,{'main':[]})['main']
 while len(c)<=index:c.append([])
 c[index]=[{'node':b,'type':'main','index':0}]
link('Read successful watermark','Read persisted thread snapshots');link('Read persisted thread snapshots','Sign read-only App request')
link('Split thread targets','Loop one repository thread');link('Loop one repository thread','Validate all pages and prepare public records');link('Loop one repository thread','Timeline needs fresh read',1)
link('Timeline needs fresh read','Prepare one timeline GET');link('Timeline needs fresh read','Reuse unchanged timeline snapshot',1);link('Reuse unchanged timeline snapshot','Capture timeline with source thread')
link('Prepare one timeline GET','Read complete thread timeline');link('Capture timeline with source thread','Only PR needs separate reviews');link('Only PR needs separate reviews','Prepare one review GET');link('Only PR needs separate reviews','Reuse complete issue discussion pages',1);link('Reuse complete issue discussion pages','Capture review with source thread');link('Prepare one review GET','Read reviews or issue discussion');link('Capture review with source thread','Loop one repository thread')
# The four top-level list GETs share the same deadline and retry/shape contract.
lists=['List all Issue and PR records','List all discussion comments','List all inline comments','List all PR heads']
previous='Exact read-only scope'
for name in lists:
 n=node(name);url=n['parameters']['url'];prep='Prepare '+name
 prepare(prep,json.dumps(url))
 n['type']='n8n-nodes-base.executeWorkflow';n['typeVersion']=1.3;n['parameters']={'workflowId':{'__rl':True,'value':'onticardsBoundedGetV1','mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}};n.update(executeOnce=True,retryOnFail=True,maxTries=2,waitBetweenTries=500,onError='continueRegularOutput')
 link(previous,prep);link(prep,name);previous=name
lists_validation=node('Validate lists and project thread targets')['parameters']['jsonOutput']
lists_validation=lists_validation.replace("const groups=names.map(name=>$(name).all().map(x=>x.json));","const pages=name=>$(name).all().flatMap(x=>x.json.complete?x.json.pages:[{statusCode:null,body:null,headers:{}}]);const groups=names.map(pages);")
lists_validation=lists_validation.replace("$(name).all().map(x=>({status:x.json.statusCode||null,body_array:Array.isArray(x.json.body),has_next:String(x.json.headers?.link||'').includes('rel=\"next\"')}))","pages(name).map(x=>({status:x.statusCode||null,body_array:Array.isArray(x.body),has_next:String(x.headers?.link||'').includes('rel=\"next\"')}))")
lists_validation=lists_validation.replace('body_array:Array.isArray(x.body),has_next:', 'body_array:Array.isArray(x.body),count:Array.isArray(x.body)?x.body.length:null,first_number:x.body?.[0]?.number||null,first_id:x.body?.[0]?.id||null,request_id:x.headers?.["x-github-request-id"]||null,has_next:')
lists_validation=lists_validation.replace('return {complete,diagnostics,targets:records.map(i=>({number:i.number,kind:i.pull_request?\'pull_request\':\'issue\',issue:i,pr:prs.find(p=>p.number===i.number)||null})),counts:',r'''const stored=$('Read persisted thread snapshots').all().map(x=>x.json);
 const targets=[...records.filter(i=>!i.pull_request).map(i=>({number:i.number,kind:'issue',issue:i,pr:null})),...prs.map(p=>({number:p.number,kind:'pull_request',issue:p,pr:p}))].map(t=>{
  const row=stored.find(r=>r.number===t.number),cached=row?JSON.parse(row.snapshot):null;
  const priorAt=cached?.timeline_checked_at;
  const changed=!cached||['title','body','state','updated_at'].some(k=>(t.issue[k]||'')!==(cached[k]||''))||JSON.stringify(t.issue.labels.map(l=>l.name))!==JSON.stringify(cached.labels)||((t.pr?.head?.sha||null)!==cached.head)||((t.pr?.base?.sha||null)!==cached.base);
  return {...t,cached,timeline_needed:changed||!Array.isArray(cached?.timeline)||!priorAt||Date.now()-Date.parse(priorAt)>=1800000};
 });
 return {complete,diagnostics,targets,counts:''')
node('Validate lists and project thread targets')['parameters']['jsonOutput']=lists_validation
combined=node('Validate all pages and prepare public records')['parameters']['jsonOutput']
for name in ['List all discussion comments','List all inline comments']:
 combined=combined.replace("$('"+name+"').all().flatMap(x=>x.json.body)","$('"+name+"').all().flatMap(x=>x.json.pages.flatMap(p=>p.body))")
node('Validate all pages and prepare public records')['parameters']['jsonOutput']=combined
node('Validate all pages and prepare public records')['parameters']['jsonOutput']=combined.replace('reviews:review.map(slim),timeline}', 'reviews:review.map(slim),timeline,timeline_checked_at:t.timeline_needed?$("Begin fixed repository poll").first().json.started_at:t.cached.timeline_checked_at}')
# Reuse the proven daily collector strategy: one complete state=all listing,
# no since filter, with an independent repository open-count consistency check.
# /installation/repositories already supplies the repository metadata.
target_expr=node('Validate lists and project thread targets')['parameters']['jsonOutput']
target_expr=target_expr.replace('const complete=groups.every', 'let complete=groups.every')
target_expr=target_expr.replace("const stored=$('Read persisted thread snapshots').all().map(x=>x.json);",r'''const stored=$('Read persisted thread snapshots').all().map(x=>x.json);
 const expectedOpen=$('Verify installation repository').first().json.body?.repositories?.[0]?.open_issues_count;
 const observedOpen=records.filter(i=>i.state==='open').length;
 if(!Number.isInteger(expectedOpen)||observedOpen!==expectedOpen)complete=false;
 diagnostics.push({stage:'independent_repository_open_count',expected:expectedOpen??null,observed:observedOpen,matched:complete});
 const known=new Set([...records,...prs].map(i=>i.number));
 const commentNumbers=[...new Set(groups[1].flatMap(p=>Array.isArray(p.body)?p.body:[]).map(c=>String(c.issue_url||'').match(/^https:\/\/api\.github\.com\/repos\/stepll2026\/OntiCards\/issues\/(\d+)$/)?.[1]).filter(Boolean).map(Number))];
 const missing=commentNumbers.filter(n=>!known.has(n)).map(number=>({number,kind:'issue',issue:{number},pr:null,metadata_needed:true}));
 diagnostics.push({stage:'comment_thread_complement',numbers:missing.map(t=>t.number)});''')
target_expr=target_expr.replace("pr:p}))].map(t=>{", "pr:p})),...missing].map(t=>{")
target_expr=target_expr.replace('t.issue.labels.map(l=>l.name)','(t.issue.labels||[]).map(l=>l.name)')
node('Validate lists and project thread targets')['parameters']['jsonOutput']=target_expr
append('Issue metadata missing from full list','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'missing','leftValue':'={{ $json.metadata_needed===true }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
prepare('Prepare missing Issue metadata GET','"https://api.github.com/repos/stepll2026/OntiCards/issues/"+$json.number')
metadata_http=copy.deepcopy(p);metadata_http['options'].pop('pagination',None)
append('Read missing Issue metadata','httpRequest',metadata_http,4.4,retryOnFail=True,maxTries=2,waitBetweenTries=500,onError='continueRegularOutput',executeOnce=True)
append('Bind fresh complementary Issue metadata','set',{'mode':'raw','jsonOutput':'={{ (()=>{const t=$("Loop one repository thread").item.json,i=$json.body,ok=$json.statusCode===200&&i?.number===t.number&&Number.isInteger(i.id)&&!i.pull_request&&Array.isArray(i.labels);return {...t,issue:ok?i:t.issue,metadata_complete:ok,timeline_needed:true};})() }}','options':{}},3.4)
append('Reuse listed Issue or PR metadata','set',{'mode':'raw','jsonOutput':'={{ {...$json,metadata_complete:true} }}','options':{}},3.4)
append('Select verified current thread','set',{'mode':'raw','jsonOutput':'={{ $json }}','options':{}},3.4)
append('Current thread metadata complete','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'complete','leftValue':'={{ $json.metadata_complete===true }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
append('Preserve incomplete complementary thread','set',{'mode':'raw','jsonOutput':'={{ {thread:$json,timeline_pages:[{statusCode:null,body:null,headers:{},metadata_failed:true}],review_pages:[{statusCode:null,body:null,headers:{},metadata_failed:true}]} }}','options':{}},3.4)
link('Loop one repository thread','Issue metadata missing from full list',1)
link('Issue metadata missing from full list','Prepare missing Issue metadata GET');link('Prepare missing Issue metadata GET','Read missing Issue metadata');link('Read missing Issue metadata','Bind fresh complementary Issue metadata');link('Bind fresh complementary Issue metadata','Select verified current thread')
link('Issue metadata missing from full list','Reuse listed Issue or PR metadata',1);link('Reuse listed Issue or PR metadata','Select verified current thread');link('Select verified current thread','Current thread metadata complete');link('Current thread metadata complete','Timeline needs fresh read');link('Current thread metadata complete','Preserve incomplete complementary thread',1);link('Preserve incomplete complementary thread','Loop one repository thread')
node('Capture timeline with source thread')['parameters']['jsonOutput']=node('Capture timeline with source thread')['parameters']['jsonOutput'].replace('$("Loop one repository thread").item.json','$("Select verified current thread").item.json')
aggregate=node('Validate all pages and prepare public records')['parameters']['jsonOutput']
aggregate=aggregate.replace("const targets=$('Validate lists and project thread targets').first().json.targets;",'')
aggregate=aggregate.replace('const combined=$input.all().map(x=>x.json);','const combined=$input.all().map(x=>x.json),targets=combined.map(x=>x.thread);')
node('Validate all pages and prepare public records')['parameters']['jsonOutput']=aggregate
parent['name']='OntiCards native serial bounded intake - read only'
parent['settings']['executionTimeout']=300
def native_spacing(value):
 if isinstance(value,dict):return {k:native_spacing(v)for k,v in value.items()}
 if isinstance(value,list):return [native_spacing(v)for v in value]
 if isinstance(value,str)and value.startswith('={{'):
  inner=value[3:-2]
  while '}}'in inner:inner=inner.replace('}}','} }')
  return '={{'+inner+'}}'
 return value
for n in parent['nodes']:n['parameters']=native_spacing(n['parameters'])
(root/'persistent-readonly-serial.workflow.json').write_text(json.dumps(parent,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'child_nodes':len(w['nodes']),'serial_parent_nodes':len(parent['nodes']),'per_get_max_attempts':2,'poll_get_deadline_seconds':240,'whole_execution_seconds':parent['settings']['executionTimeout'],'model_nodes':0,'repository_write_nodes':0,'deployed':False}))
