"""Compose native n8n nodes for persistent read-only single-repository intake."""
import json,uuid
from pathlib import Path
root=Path(__file__).parent
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':240}
prior=(root/'build_event_replay.py').read_text(encoding='utf-8')
exec(prior[prior.index('class Builder:'):prior.index('# Native test transport only.')])
def expression_spacing(expr):
 if expr.startswith('={{'):
  inner=expr[3:-2]
  while '}}' in inner:inner=inner.replace('}}','} }')
  return '={{'+inner+'}}'
 return expr
Builder.set=lambda self,name,expr,**extra:self.node(name,'set',{'mode':'raw','jsonOutput':expression_spacing(expr),'options':{}},3.4,**extra)
b=Builder('onticardsPersistentReadOnlyV1')
api='https://api.github.com/repos/stepll2026/OntiCards'
tables={'events':'onticards_intake_events_v1','threads':'onticards_intake_threads_v1','watermark':'onticards_intake_watermark_v1','polls':'onticards_intake_polls_v1'}
b.node('Every five minutes','scheduleTrigger',{'rule':{'interval':[{'field':'minutes','minutesInterval':5}]}},1.2)
b.node('Local read-only poll','webhook',{'httpMethod':'POST','path':'onticards-intake-readonly-v1','responseMode':'onReceived','options':{}},2.1,webhookId='onticards-intake-readonly-v1')
b.set('Begin fixed repository poll','={{ {repository:"stepll2026/OntiCards",poll_id:$execution.id,started_at:$now.toISO(),mode:"persistent_read_only_dry_run",model_calls:0,repository_writes:0} }}')
schemas={
 'events':[('event_key','string'),('thread_key','string'),('event_id','string'),('kind','string'),('actor','string'),('actor_type','string'),('status','string'),('payload','string')],
 'threads':[('thread_key','string'),('number','number'),('kind','string'),('snapshot','string'),('app_reply_count','number'),('observed_at','string')],
 'watermark':[('repository','string'),('watermark','string'),('poll_id','string'),('event_count','number'),('thread_count','number')],
 'polls':[('poll_id','string'),('started_at','string'),('finished_at','string'),('status','string'),('details','string')]}
for key in tables:b.table('Ensure '+key,tables[key],schemas[key])
b.row('Read successful watermark',tables['watermark'],'get','repository','stepll2026/OntiCards',alwaysOutputData=True)
b.node('Sign read-only App request','jwt',{'operation':'sign','useJson':True,'claimsJson':'={{ JSON.stringify({iat:Math.floor(Date.now()/1000)-60,exp:Math.floor(Date.now()/1000)+540,iss:"5422414"}) }}','headerClaims':'{}','options':{'algorithm':'RS256'}},1,credentials={'jwtAuth':{'id':'onticardsIntakeAppJwt','name':'OntiCards single-repository intake App'}})
def http(name,method,url,auth='installation',body=None,pages=False,once=True):
 authvalue='={{ "Bearer " + $("Sign read-only App request").first().json.token }}' if auth=='app' else '={{ "Bearer " + $("Mint read-only token").first().json.body.token }}'
 p={'method':method,'url':url,'sendHeaders':True,'headerParameters':{'parameters':[{'name':'Authorization','value':authvalue},{'name':'Accept','value':'application/vnd.github+json'},{'name':'X-GitHub-Api-Version','value':'2026-03-10'},{'name':'Cache-Control','value':'no-cache'}]},'options':{'timeout':20000,'proxy':'http://127.0.0.1:17891','response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}}
 if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=body)
 if pages:
  p['options']['pagination']={'pagination':{'paginationMode':'responseContainsNextURL','nextURL':r'''={{ (()=>{const u=($response.headers.link||'').match(/<([^>]+)>;\s*rel="next"/)?.[1]||'';if(u&&!u.startsWith('https://api.github.com/repos/stepll2026/OntiCards/'))throw new Error('Pagination left fixed repository');return u;})() }}''','paginationCompleteWhen':'other','completeExpression':'={{ !($response.headers.link||"").includes(\'rel="next"\') }}','limitPagesFetched':True,'maxRequests':50,'requestInterval':100}}
 p['options']['batching']={'batch':{'batchSize':1,'batchInterval':1000}}
 # Only idempotent GET transport failures may retry; mint/revoke never retry.
 b.node(name,'httpRequest',p,4.4,retryOnFail=method=='GET',maxTries=2,waitBetweenTries=1000,onError='continueRegularOutput',executeOnce=once)
http('Mint read-only token','POST','https://api.github.com/app/installations/174029282/access_tokens','app',json.dumps({'repositories':['OntiCards'],'permissions':{'issues':'read','pull_requests':'read','metadata':'read'}}))
http('Verify installation repository','GET','https://api.github.com/installation/repositories?per_page=100')
b.iff('Exact read-only scope','={{ (()=>{const p=$("Mint read-only token").first().json.body?.permissions||{};return $("Mint read-only token").first().json.statusCode===201 && Object.keys(p).length===3 && p.issues==="read" && p.pull_requests==="read" && p.metadata==="read" && $json.statusCode===200 && $json.body.total_count===1 && $json.body.repositories[0]?.full_name==="stepll2026/OntiCards";})() }}')
for name,endpoint in [('List all Issue and PR records','/issues?state=all&sort=updated&direction=desc&per_page=100'),('List all discussion comments','/issues/comments?sort=updated&direction=desc&per_page=100'),('List all inline comments','/pulls/comments?sort=updated&direction=desc&per_page=100'),('List all PR heads','/pulls?state=all&sort=updated&direction=desc&per_page=100')]:http(name,'GET',api+endpoint,pages=True)
b.set('Validate lists and project thread targets',r'''={{ (()=>{
 const names=['List all Issue and PR records','List all discussion comments','List all inline comments','List all PR heads'];
 const groups=names.map(name=>$(name).all().map(x=>x.json));
 const complete=groups.every(rows=>rows.length>0&&rows.every(r=>r.statusCode===200&&Array.isArray(r.body))&&!String(rows.at(-1).headers?.link||'').includes('rel="next"'));
 const records=complete?groups[0].flatMap(r=>r.body):[],prs=complete?groups[3].flatMap(r=>r.body):[];
 const diagnostics=names.map(name=>({stage:name,pages:$(name).all().map(x=>({status:x.json.statusCode||null,body_array:Array.isArray(x.json.body),has_next:String(x.json.headers?.link||'').includes('rel="next"')}))}));
 return {complete,diagnostics,targets:records.map(i=>({number:i.number,kind:i.pull_request?'pull_request':'issue',issue:i,pr:prs.find(p=>p.number===i.number)||null})),counts:groups.map(rows=>rows.reduce((n,r)=>n+(Array.isArray(r.body)?r.body.length:0),0))};
})() }}''',executeOnce=True)
b.iff('All list pages complete','={{ $json.complete && $json.targets.length>0 }}')
b.node('Split thread targets','splitOut',{'fieldToSplitOut':'targets','options':{}},1)
http('Read complete thread timeline','GET','={{ "'+api+'/issues/"+$json.number+"/timeline?per_page=100" }}',pages=True,once=False)
b.set('Capture timeline with source thread','={{ {thread:$("Split thread targets").item.json,page:{statusCode:$json.statusCode,body:$json.body,headers:$json.headers},capture:{body_array:Array.isArray($json.body),body_type:typeof $json.body,response_keys:Object.keys($json),content_type:$json.headers?.["content-type"]||null,content_length:$json.headers?.["content-length"]||null,request_id:$json.headers?.["x-github-request-id"]||null}} }}')
http('Read reviews or issue discussion','GET','={{ "'+api+'"+($json.thread.kind==="pull_request"?"/pulls/":"/issues/")+$json.thread.number+($json.thread.kind==="pull_request"?"/reviews?per_page=100":"/comments?per_page=100") }}',pages=True,once=False)
b.set('Capture review with source thread','={{ {thread:$("Capture timeline with source thread").item.json.thread,page:{statusCode:$json.statusCode,body:$json.body,headers:$json.headers},capture:{body_array:Array.isArray($json.body),body_type:typeof $json.body,response_keys:Object.keys($json),content_type:$json.headers?.["content-type"]||null,content_length:$json.headers?.["content-length"]||null,request_id:$json.headers?.["x-github-request-id"]||null}} }}')
b.set('Validate all pages and prepare public records',r'''={{ (()=>{
 const targets=$('Validate lists and project thread targets').first().json.targets;
 const timelines=$('Capture timeline with source thread').all().map(x=>x.json),reviews=$input.all().map(x=>x.json);
 const completeFor=(rows,n)=>{const pages=rows.filter(r=>r.thread.number===n).map(r=>r.page);return pages.length>0&&pages.every(p=>p.statusCode===200&&Array.isArray(p.body))&&!String(pages.at(-1).headers?.link||'').includes('rel="next"');};
 const complete=targets.every(t=>completeFor(timelines,t.number)&&completeFor(reviews,t.number));
 const discussions=$('List all discussion comments').all().flatMap(x=>x.json.body),inline=$('List all inline comments').all().flatMap(x=>x.json.body);
 const events=[],threads=[],seen=new Set();
 const bot=u=>u?.type==='Bot'||u?.id===346235449||String(u?.login||'').endsWith('[bot]');
 const add=(t,kind,id,payload,user)=>{const key=t.number+':'+kind+':'+String(id)+':'+JSON.stringify(payload);if(seen.has(key))return;seen.add(key);events.push({thread_key:'stepll2026/OntiCards#'+t.number,event_id:kind+':'+String(id),kind,actor:user?.login||'',actor_type:user?.type||'unknown',status:bot(user)?'ignored_machine_event':'pending_readonly_dry_run',payload:JSON.stringify(payload)});};
 if(complete)for(const t of targets){
 const discussion=discussions.filter(c=>c.issue_url==='https://api.github.com/repos/stepll2026/OntiCards/issues/'+t.number);
 const lines=inline.filter(c=>c.pull_request_url==='https://api.github.com/repos/stepll2026/OntiCards/pulls/'+t.number);
 const timeline=timelines.filter(r=>r.thread.number===t.number).flatMap(r=>r.page.body);
 const review=t.kind==='pull_request'?reviews.filter(r=>r.thread.number===t.number).flatMap(r=>r.page.body):[];
 const slim=c=>({id:c.id,author:c.user?.login,type:c.user?.type,body:c.body||'',updated_at:c.updated_at||c.submitted_at||c.created_at,state:c.state||null,url:c.html_url||null});
 const snapshot={id:t.issue.id,number:t.number,kind:t.kind,title:t.issue.title,body:t.issue.body||'',state:t.issue.state,created_at:t.issue.created_at,updated_at:t.issue.updated_at,labels:t.issue.labels.map(l=>l.name),head:t.pr?.head?.sha||null,base:t.pr?.base?.sha||null};
 add(t,t.kind+'_snapshot',t.issue.id,snapshot,t.issue.user);
 for(const c of discussion)add(t,'discussion_comment',c.id,slim(c),c.user);
 for(const c of lines)add(t,'inline_comment',c.id,{...slim(c),path:c.path,line:c.line,commit_id:c.commit_id},c.user);
 for(const c of review)add(t,'review',c.id,{...slim(c),commit_id:c.commit_id},c.user);
 for(const e of timeline)add(t,'timeline_'+e.event,e.id||e.sha||e.commit_id||JSON.stringify(e),{id:e.id||null,event:e.event,created_at:e.created_at||e.submitted_at||null,actor:e.actor?.login||e.user?.login||null,body:e.body||'',state:e.state||null,commit_id:e.commit_id||e.sha||null,label:e.label?.name||null},e.actor||e.user);
 threads.push({thread_key:'stepll2026/OntiCards#'+t.number,number:t.number,kind:t.kind,snapshot:JSON.stringify({...snapshot,discussion:discussion.map(slim),inline:lines.map(slim),reviews:review.map(slim),timeline}),app_reply_count:discussion.filter(c=>c.user?.id===346235449||c.user?.login==='onticards-maintainer-stepll2026[bot]').length,observed_at:$('Begin fixed repository poll').first().json.started_at});
 }
 const pageDiagnostic=(r,stage)=>({stage,number:r.thread.number,status:r.page.statusCode||null,body_array:Array.isArray(r.page.body),has_next:String(r.page.headers?.link||'').includes('rel="next"'),...(!Array.isArray(r.page.body)?{capture:r.capture,body_type:typeof r.page.body,body_keys:r.page.body&&typeof r.page.body==='object'?Object.keys(r.page.body).slice(0,8):[],body_preview:r.page.statusCode===200?String(JSON.stringify(r.page.body)).slice(0,100):null}:{})});
 const diagnostics=[...timelines.map(r=>pageDiagnostic(r,'timeline')),...reviews.map(r=>pageDiagnostic(r,'review_or_discussion'))];
 return {complete,diagnostics,events,threads,source_counts:$('Validate lists and project thread targets').first().json.counts,timeline_pages:timelines.length,review_pages:reviews.length};
})() }}''',executeOnce=True)
b.iff('All thread pages complete','={{ $json.complete && $json.events.length>0 }}')
b.node('Split thread snapshots','splitOut',{'fieldToSplitOut':'threads','options':{}},1)
b.row('Persist current thread context',tables['threads'],'upsert','thread_key','={{ $json.thread_key }}')
b.set('Select stable event records','={{ {events:$("Validate all pages and prepare public records").first().json.events} }}',executeOnce=True)
b.node('Split stable event records','splitOut',{'fieldToSplitOut':'events','options':{}},1)
b.node('Hash stable event revision','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.thread_key+"|"+$json.event_id+"|"+$json.payload }}','dataPropertyName':'event_key','encoding':'hex'},2)
b.row('Persist event revisions',tables['events'],'upsert','event_key','={{ $json.event_key }}')
b.set('Prepare successful watermark','={{ {repository:"stepll2026/OntiCards",watermark:[$("Read successful watermark").first().json.watermark||"",$("Begin fixed repository poll").first().json.started_at].sort().at(-1),poll_id:$("Begin fixed repository poll").first().json.poll_id,event_count:$("Validate all pages and prepare public records").first().json.events.length,thread_count:$("Validate all pages and prepare public records").first().json.threads.length} }}',executeOnce=True)
b.row('Commit complete watermark',tables['watermark'],'upsert','repository','stepll2026/OntiCards')
b.set('Successful poll receipt','={{ {poll_id:$("Begin fixed repository poll").first().json.poll_id,started_at:$("Begin fixed repository poll").first().json.started_at,finished_at:$now.toISO(),status:"complete_readonly_dry_run",details:JSON.stringify({watermark:$json.watermark,event_count:$json.event_count,thread_count:$json.thread_count,source_counts:$("Validate all pages and prepare public records").first().json.source_counts,timeline_pages:$("Validate all pages and prepare public records").first().json.timeline_pages,review_pages:$("Validate all pages and prepare public records").first().json.review_pages,model_calls:0,repository_writes:0})} }}')
b.set('Failed poll preserves watermark','={{ {poll_id:$("Begin fixed repository poll").first().json.poll_id,started_at:$("Begin fixed repository poll").first().json.started_at,finished_at:$now.toISO(),status:"incomplete_no_watermark_advance",details:JSON.stringify({previous_watermark:$("Read successful watermark").first().json.watermark||null,diagnostics:$json.diagnostics||[{stage:"installation_scope",status:$json.statusCode||null}],model_calls:0,repository_writes:0})} }}')
b.row('Persist poll receipt',tables['polls'],'upsert','poll_id','={{ $json.poll_id }}')
http('Revoke read-only token','DELETE','https://api.github.com/installation/token')
b.set('Safe execution result','={{ (()=>{const r=$("Persist poll receipt").first().json;return {poll_id:r.poll_id,started_at:r.started_at,finished_at:$now.toISO(),status:r.status,details:JSON.stringify({...JSON.parse(r.details),token_revoked:$json.statusCode===204,token_permissions:$("Mint read-only token").first().json.body?.permissions||null})};})() }}')
b.row('Persist authentication completion',tables['polls'],'upsert','poll_id','={{ $json.poll_id }}')
b.link('Every five minutes','Begin fixed repository poll');b.link('Local read-only poll','Begin fixed repository poll')
b.chain(['Begin fixed repository poll','Ensure events','Ensure threads','Ensure watermark','Ensure polls','Read successful watermark','Sign read-only App request','Mint read-only token','Verify installation repository','Exact read-only scope','List all Issue and PR records','List all discussion comments','List all inline comments','List all PR heads','Validate lists and project thread targets','All list pages complete','Split thread targets','Read complete thread timeline','Capture timeline with source thread','Read reviews or issue discussion','Capture review with source thread','Validate all pages and prepare public records','All thread pages complete','Split thread snapshots','Persist current thread context','Select stable event records','Split stable event records','Hash stable event revision','Persist event revisions','Prepare successful watermark','Commit complete watermark','Successful poll receipt','Persist poll receipt','Revoke read-only token','Safe execution result','Persist authentication completion'])
for name in ['Exact read-only scope','All list pages complete','All thread pages complete']:b.link(name,'Failed poll preserves watermark',1)
b.link('Failed poll preserves watermark','Persist poll receipt')
w=b.workflow('OntiCards 单仓5分钟只读采集 — 常驻DRY RUN')
for node in w['nodes']:
 def check(v):
  if isinstance(v,dict):
   for x in v.values():check(x)
  elif isinstance(v,list):
   for x in v:check(x)
  elif isinstance(v,str) and v.startswith('={{'):assert '}}' not in v[3:-2],node['name']
 check(node['parameters'])
(root/'persistent-readonly.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'model_nodes':0,'repository_write_nodes':0,'schedule_minutes':5,'active_in_export':False}))
