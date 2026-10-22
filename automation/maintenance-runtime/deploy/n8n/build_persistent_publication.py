"""Native approval-bound publication; reuses tested sticky reconciliation and App JWT."""
import json,uuid
from pathlib import Path
root=Path(__file__).parent
prior=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':240}
exec(prior[prior.index('class Builder:'):prior.index('# Native test transport only.')])
def spacing(s):
 if s.startswith('={{'):
  inner=s[3:-2]
  while '}}'in inner:inner=inner.replace('}}','} }')
  return '={{'+inner+'}}'
 return s
Builder.set=lambda self,name,expr,**extra:self.node(name,'set',{'mode':'raw','jsonOutput':spacing(expr),'options':{}},3.4,**extra)
b=Builder('onticardsPersistentPublicationV1');api='https://api.github.com/repos/stepll2026/OntiCards'
approval_path=root/'persistent-publication-approval.json'
approval=json.loads(approval_path.read_text(encoding='utf-8'))if approval_path.exists()else None
table='onticards_publication_v1'
cols=[('event_key','string'),('thread_key','string'),('status','string'),('source_hash','string'),('body_hash','string'),('body','string'),('comment_id','string'),('comment_url','string'),('reply_count','number'),('should_post','boolean'),('reason','string'),('token_revoked','boolean')]
b.node('Every five minutes approved publication','scheduleTrigger',{'rule':{'interval':[{'field':'minutes','minutesInterval':5}]}},1.2)
b.node('Local approved publication reconciliation','webhook',{'httpMethod':'POST','path':'onticards-persistent-publication-v1','responseMode':'onReceived','options':{}},2.1,webhookId='onticards-persistent-publication-v1')
b.set('Trusted reviewed approval','={{ $json }}')
b.iff('Explicit reviewed approval exists','={{ $json.publication_enabled===true && !!$json.approval && /^[0-9a-f]{64}$/.test($json.approval.event_key||"") }}')
b.set('No approved publication','={{ {status:"publication_disabled_or_no_approval",model_calls:0,github_posts:0} }}')
b.table('Ensure native publication ledger',table,cols)
b.table('Ensure publication run receipts','onticards_publication_runs_v1',[('run_id','string'),('finished_at','string'),('token_revoked','boolean'),('details','string')])
b.row('Read approved original draft','onticards_draft_events_v1','get','event_key','={{ $("Trusted reviewed approval").first().json.approval.event_key }}',alwaysOutputData=True)
b.row('Read original conversation','onticards_conversation_v1','get','thread_key','={{ $("Read approved original draft").first().json.thread_key }}',alwaysOutputData=True)
b.row('Read sticky publication state',table,'get','event_key','={{ $("Trusted reviewed approval").first().json.approval.event_key }}',alwaysOutputData=True)
b.set('Bind approval and immutable draft','={{ (()=>{const a=$("Trusted reviewed approval").first().json.approval,d=$("Read approved original draft").first().json;let s={};try{s=JSON.parse(d.source_snapshot||"{}")}catch(error){};return {approval:a,draft:d,source:s,body:a.body||"",source_snapshot:d.source_snapshot||""};})() }}')
b.node('Hash reviewed body','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.body }}','dataPropertyName':'calculated_body_hash','encoding':'hex'},2)
b.node('Hash original bound source','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.source_snapshot }}','dataPropertyName':'calculated_source_hash','encoding':'hex'},2)
b.iff('Approval hashes and exact event match','={{ (()=>{const a=$json.approval,d=$json.draft,s=$json.source,fields=["deployment_method","api_image_identity","source_version","reproduction","expected_behavior","actual_behavior","sanitized_error"];return $json.calculated_body_hash===a.body_hash && $json.calculated_source_hash===a.source_hash && d.source_hash===a.source_hash && d.event_key===a.event_key && d.status==="awaiting_semantic_review" && s.repository==="stepll2026/OntiCards" && s.thread_key===d.thread_key && Number.isInteger(s.number) && s.number>0 && a.body.includes("<!-- onticards-triage:"+a.event_key+" -->") && a.reviewed===true && a.asked_fields_reviewed===true && Array.isArray(a.observed_fields) && a.observed_fields.every(f=>fields.includes(f.field)&&typeof f.value==="string"&&f.value.trim()&&s.event.body.includes(f.value)&&f.source_event_id===String(s.event.id)) && Array.isArray(a.asked_fields) && new Set(a.asked_fields).size===a.asked_fields.length && a.asked_fields.every(f=>fields.includes(f)&&!Object.hasOwn(s.known_fields,f)&&!a.observed_fields.some(o=>o.field===f));})() }}')
b.set('Approval rejected no network','={{ {status:"approval_rejected",model_calls:0,github_posts:0} }}')
b.node('Sign publication App JWT','jwt',{'operation':'sign','useJson':True,'claimsJson':'={{ JSON.stringify({iat:Math.floor(Date.now()/1000)-60,exp:Math.floor(Date.now()/1000)+540,iss:"5422414"}) }}','headerClaims':'{}','options':{'algorithm':'RS256'}},1,credentials={'jwtAuth':{'id':'onticardsIntakeAppJwt','name':'OntiCards single-repository intake App'}})
def http(name,method,url,app=False,body=None,pages=False):
 auth='={{ "Bearer "+$("Sign publication App JWT").first().json.token }}'if app else'={{ "Bearer "+$("Mint bounded publication token").first().json.body?.token }}'
 p={'method':method,'url':url,'sendHeaders':True,'headerParameters':{'parameters':[{'name':'Authorization','value':auth},{'name':'Accept','value':'application/vnd.github+json'},{'name':'X-GitHub-Api-Version','value':'2026-03-10'},{'name':'Cache-Control','value':'no-cache'}]},'options':{'timeout':20000,'proxy':'http://127.0.0.1:17891','response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}}
 if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=body)
 if pages:p['options']['pagination']={'pagination':{'paginationMode':'responseContainsNextURL','nextURL':r'''={{ (()=>{const u=($response.headers.link||'').match(/<([^>]+)>;\s*rel="next"/)?.[1]||'';if(u&&!u.startsWith('https://api.github.com/repos/stepll2026/OntiCards/'))throw new Error('Pagination left fixed repository');return u;})() }}''','paginationCompleteWhen':'other','completeExpression':'={{ !($response.headers.link||"").includes(\'rel="next"\') }}','limitPagesFetched':True,'maxRequests':50,'requestInterval':100}}
 b.node(name,'httpRequest',p,4.4,retryOnFail=False,onError='continueRegularOutput',executeOnce=True)
http('Mint bounded publication token','POST','https://api.github.com/app/installations/174029282/access_tokens',True,json.dumps({'repositories':['OntiCards'],'permissions':{'issues':'write','pull_requests':'read','contents':'read','metadata':'read'}}))
http('Verify publication repository scope','GET','https://api.github.com/installation/repositories?per_page=100')
b.iff('Only expected repository and permissions','={{ (()=>{const p=$("Mint bounded publication token").first().json.body?.permissions||{};return $("Mint bounded publication token").first().json.statusCode===201 && Object.keys(p).length===4 && p.issues==="write"&&p.pull_requests==="read"&&p.contents==="read"&&p.metadata==="read"&&$json.statusCode===200&&$json.body?.total_count===1&&$json.body.repositories[0]?.full_name==="stepll2026/OntiCards";})() }}')
number='$("Bind approval and immutable draft").first().json.source.number'
kind='$("Bind approval and immutable draft").first().json.source.kind'
http('Read fresh issue source','GET','={{ "'+api+'/issues/"+'+number+' }}')
http('Read complete fresh discussion','GET','={{ "'+api+'/issues/"+'+number+'+"/comments?per_page=100" }}',pages=True)
http('Read fresh PR or issue details','GET','={{ "'+api+'"+('+kind+'==="pull_request"?"/pulls/":"/issues/")+'+number+' }}')
http('Read complete inline or issue discussion','GET','={{ "'+api+'"+('+kind+'==="pull_request"?"/pulls/":"/issues/")+'+number+'+"/comments?per_page=100" }}',pages=True)
http('Read complete reviews or issue discussion','GET','={{ "'+api+'"+('+kind+'==="pull_request"?"/pulls/":"/issues/")+'+number+'+('+kind+'==="pull_request"?"/reviews?per_page=100":"/comments?per_page=100") }}',pages=True)
http('Verify current source commit','GET','={{ "'+api+'/commits/"+('+kind+'==="pull_request"?$("Read fresh PR or issue details").first().json.body?.head?.sha:"main") }}')
b.set('Evaluate sticky state and fresh source',r'''={{ (()=>{
 const bound=$('Hash original bound source').first().json,a=bound.approval,s=bound.source,prev=$('Read sticky publication state').first().json,conv=$('Read original conversation').first().json;
 const pages=name=>$(name).all().map(i=>i.json),good=xs=>xs.length>0&&xs.every(x=>x.statusCode===200&&Array.isArray(x.body))&&!String(xs.at(-1).headers?.link||'').includes('rel="next"');
 const cp=pages('Read complete fresh discussion'),ip=pages('Read complete inline or issue discussion'),rp=pages('Read complete reviews or issue discussion');
 const complete=good(cp)&&good(ip)&&good(rp),comments=complete?cp.flatMap(x=>x.body):[];
 const app=comments.filter(c=>c.user?.id===346235449||c.user?.login==='onticards-maintainer-stepll2026[bot]');
 const sticky=prev.status==='posting_unknown'||prev.status?.startsWith('published'),intent=sticky?prev:{body:a.body,body_hash:a.body_hash,source_hash:a.source_hash};
 const marker='<!-- onticards-triage:'+a.event_key+' -->',marked=comments.filter(c=>c.body?.includes(marker));
 const confirmed=marked.length===1&&marked[0].body===intent.body&&marked[0].user?.id===346235449&&marked[0].user?.login==='onticards-maintainer-stepll2026[bot]'&&marked[0].user?.type==='Bot'?marked[0]:null;
 const ir=$('Read fresh issue source').first().json,issue=ir.body,pr=$('Read fresh PR or issue details').first().json,commit=$('Verify current source commit').first().json;
 const same=(live,old)=>Array.isArray(old)&&live.length===old.length&&new Set(live.map(c=>c.id)).size===live.length&&live.every(c=>old.some(o=>o.id===c.id&&o.body===(c.body||'')&&o.updated_at===(c.updated_at||c.submitted_at||c.created_at)));
 let status=prev.status==='posting_unknown'||prev.status?.startsWith('published')?prev.status:'needs_human_review',reason='',should_post=false;
 if(!complete||ir.statusCode!==200||pr.statusCode!==200||commit.statusCode!==200)reason='fresh source read incomplete';
 else if(confirmed){status='published_reconciled';reason='GET verified exact approved App comment';}
 else if(marked.length)reason='marker collision';
 else if(prev.status==='posting_unknown')reason='previous POST uncertain; GET only';
 else if(prev.status?.startsWith('published'))reason='published comment absent; no automatic replacement';
 else if(prev.status==='native_repair_route'){status='native_repair_route';reason='prior native repair handoff; no automatic post';}
 else if((issue.labels||[]).some(l=>(typeof l==='string'?l:l.name)==='AI')){status='native_repair_route';reason='AI label now routes this thread to native repair; no consultation post';}
 else if(app.length>=3||Number(conv.reply_count||0)>=3){status='reply_cap_reached';reason='all previous App replies count';}
 else if(conv.pending_event!==a.event_key||conv.pending_state!=='model_request_started')reason='conversation reservation mismatch';
 else if((s.kind==='pull_request'?pr.body.id:issue.id)!==s.thread.id||issue.number!==s.number||issue.html_url!=='https://github.com/stepll2026/OntiCards/'+(s.kind==='pull_request'?'pull':'issues')+'/'+s.number)reason='thread scope mismatch';
 else if(issue.body!==s.thread.body||issue.title!==s.thread.title||issue.state!==s.thread.state||!same(comments,s.thread.discussion))reason='issue or discussion changed after draft';
 else if(s.kind==='pull_request'&&(pr.body.head?.sha!==s.thread.head||pr.body.base?.sha!==s.thread.base||!same(ip.flatMap(x=>x.body),s.thread.inline)||!same(rp.flatMap(x=>x.body),s.thread.reviews)))reason='PR version or review changed after draft';
 else if(commit.body?.sha!==s.repository_context?.commit_sha)reason='current source commit moved';
 else {status='approved_ready';reason='exact reviewed body and fresh bound source';should_post=true;}
 return {event_key:a.event_key,thread_key:s.thread_key,status,source_hash:intent.source_hash,body_hash:intent.body_hash,body:intent.body,comment_id:confirmed?String(confirmed.id):prev.comment_id||'',comment_url:confirmed?.html_url||prev.comment_url||'',reply_count:complete?app.length:prev.reply_count||0,should_post,reason,token_revoked:false};
})() }}''',executeOnce=True)
b.iff('One approved POST permitted','={{ $json.should_post===true }}')
b.set('Durable uncertain POST intent','={{ {...$json,status:"posting_unknown",should_post:false,reason:"POST intent persisted before network request"} }}')
b.row('Persist uncertain intent',table,'upsert','event_key','={{ $json.event_key }}')
http('Publish reviewed body once','POST','={{ "'+api+'/issues/"+'+number+'+"/comments" }}',body='={{ JSON.stringify({body:$("Persist uncertain intent").first().json.body}) }}')
http('GET reconcile actual published comments','GET','={{ "'+api+'/issues/"+'+number+'+"/comments?per_page=100" }}',pages=True)
b.set('Confirm exact App body after POST',r'''={{ (()=>{const r=$('Persist uncertain intent').first().json,pages=$input.all().map(i=>i.json),complete=pages.length>0&&pages.every(p=>p.statusCode===200&&Array.isArray(p.body))&&!String(pages.at(-1).headers?.link||'').includes('rel="next"'),comments=complete?pages.flatMap(p=>p.body):[],app=comments.filter(c=>c.user?.id===346235449||c.user?.login==='onticards-maintainer-stepll2026[bot]'),matches=app.filter(c=>c.body===r.body&&c.user?.id===346235449&&c.user?.login==='onticards-maintainer-stepll2026[bot]'&&c.user?.type==='Bot');return {...r,status:matches.length===1?'published_confirmed':'posting_unknown',comment_id:matches.length===1?String(matches[0].id):r.comment_id,comment_url:matches.length===1?matches[0].html_url:r.comment_url,reply_count:complete?app.length:r.reply_count,reason:matches.length===1?'GET confirmed exact App body':'POST uncertain; later runs GET only'};})() }}''',executeOnce=True)
b.row('Persist publication observation',table,'upsert','event_key','={{ $json.event_key }}')
b.iff('Remote publication confirmed','={{ $json.status.startsWith("published") && !!$json.comment_id && $json.body_hash===$("Trusted reviewed approval").first().json.approval.body_hash && $json.source_hash===$("Trusted reviewed approval").first().json.approval.source_hash && !JSON.parse($("Read original conversation").first().json.publication_ids||"[]").includes($json.comment_id) }}')
b.set('Apply reviewed conversation increment',r'''={{ (()=>{const r=$json,b=$('Bind approval and immutable draft').first().json,a=b.approval,s=b.source,c=$('Read original conversation').first().json,known=JSON.parse(c.known_fields||'{}');for(const f of a.observed_fields||[])if(f.source_event_id===String(s.event.id)&&s.event.body.includes(f.value))known[f.field]=f.value;const unique=xs=>[...new Set(xs)];return {thread_key:r.thread_key,model_calls:c.model_calls,reply_count:Math.max(Number(c.reply_count||0),r.reply_count),pending_event:c.pending_event===r.event_key?'':c.pending_event,pending_state:c.pending_event===r.event_key?'published_verified':c.pending_state,known_fields:JSON.stringify(known),asked_fields:JSON.stringify(unique([...JSON.parse(c.asked_fields||'[]'),...a.asked_fields])),answered_human_ids:JSON.stringify(unique([...JSON.parse(c.answered_human_ids||'[]'),String(s.event.id)])),publication_ids:JSON.stringify(unique([...JSON.parse(c.publication_ids||'[]'),r.comment_id]))};})() }}''')
b.row('Persist reviewed conversation', 'onticards_conversation_v1','upsert','thread_key','={{ $json.thread_key }}')
http('Revoke bounded publication token','DELETE','https://api.github.com/installation/token')
b.set('Safe publication run receipt','={{ (()=>{let state={status:"scope_rejected"};try{state=$("Persist publication observation").first().json}catch(error){};return {run_id:$execution.id,finished_at:$now.toISO(),token_revoked:$json.statusCode===204,details:JSON.stringify({event_key:$("Trusted reviewed approval").first().json.approval.event_key,status:state.status,comment_id:state.comment_id||"",comment_url:state.comment_url||"",reply_count:state.reply_count||0,reason:state.reason||"scope rejected",model_calls:0})};})() }}')
b.row('Persist safe publication run receipt','onticards_publication_runs_v1','upsert','run_id','={{ $json.run_id }}')
b.set('Trusted publication policy',json.dumps({'repository':'stepll2026/OntiCards','approval':approval,'publication_enabled':False,'automatic_enabled':False,'semantic_policy_version':'normal-consultation-source-review-v1'},ensure_ascii=False))
b.iff('Automatic ordinary publication enabled','={{ $json.publication_enabled===true && $json.automatic_enabled===true }}')
b.table('Ensure automatic approval ledger','onticards_reviewed_approvals_v1',[('event_key','string'),('thread_key','string'),('status','string'),('approval','string'),('observed_at','string')])
b.table('Ensure publication ledger for selection',table,cols)
def allrows(name,table_name):b.node(name,'dataTable',{'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':table_name,'mode':'name'},'returnAll':True},1.1,alwaysOutputData=True,executeOnce=True)
allrows('Read native approved ordinary replies','onticards_reviewed_approvals_v1')
allrows('Read all sticky publication receipts',table)
allrows('Read publication conversation states','onticards_conversation_v1')
b.set('Select at most one native approved reply',r'''={{ (()=>{const cfg=$('Trusted publication policy').first().json,states=$('Read all sticky publication receipts').all().map(x=>x.json),conversations=$('Read publication conversation states').all().map(x=>x.json),eligible=[];for(const row of $('Read native approved ordinary replies').all().map(x=>x.json)){if(row.status!=='approved'||!row.approval)continue;let a;try{a=JSON.parse(row.approval)}catch(error){continue;}if(a.approval_origin!=='independent_semantic_review'||a.policy_version!==cfg.semantic_policy_version||a.event_key!==row.event_key)continue;const state=states.find(s=>s.event_key===row.event_key),c=conversations.find(s=>s.thread_key===row.thread_key);if(state?.status?.startsWith('published')&&state.comment_id&&c&&JSON.parse(c.publication_ids||'[]').includes(state.comment_id))continue;eligible.push({approval:a,at:state?.updatedAt||row.createdAt||row.observed_at});}eligible.sort((a,b)=>Date.parse(a.at)-Date.parse(b.at));return {repository:cfg.repository,publication_enabled:cfg.publication_enabled,approval:eligible[0]?.approval||null};})() }}''',executeOnce=True)
b.set('Use explicit reviewed publication policy','={{ $("Trusted publication policy").first().json }}')
b.link('Every five minutes approved publication','Trusted publication policy');b.link('Local approved publication reconciliation','Trusted publication policy')
b.chain(['Trusted publication policy','Automatic ordinary publication enabled','Ensure automatic approval ledger','Ensure publication ledger for selection','Read native approved ordinary replies','Read all sticky publication receipts','Read publication conversation states','Select at most one native approved reply','Trusted reviewed approval'])
b.link('Automatic ordinary publication enabled','Use explicit reviewed publication policy',1);b.link('Use explicit reviewed publication policy','Trusted reviewed approval')
b.chain(['Trusted reviewed approval','Explicit reviewed approval exists','Ensure native publication ledger','Ensure publication run receipts','Read approved original draft','Read original conversation','Read sticky publication state','Bind approval and immutable draft','Hash reviewed body','Hash original bound source','Approval hashes and exact event match','Sign publication App JWT','Mint bounded publication token','Verify publication repository scope','Only expected repository and permissions','Read fresh issue source','Read complete fresh discussion','Read fresh PR or issue details','Read complete inline or issue discussion','Read complete reviews or issue discussion','Verify current source commit','Evaluate sticky state and fresh source','One approved POST permitted','Durable uncertain POST intent','Persist uncertain intent','Publish reviewed body once','GET reconcile actual published comments','Confirm exact App body after POST','Persist publication observation','Remote publication confirmed','Apply reviewed conversation increment','Persist reviewed conversation','Revoke bounded publication token','Safe publication run receipt','Persist safe publication run receipt'])
b.link('Explicit reviewed approval exists','No approved publication',1);b.link('Approval hashes and exact event match','Approval rejected no network',1);b.link('Only expected repository and permissions','Revoke bounded publication token',1)
b.link('One approved POST permitted','Persist publication observation',1);b.link('Remote publication confirmed','Revoke bounded publication token',1)
w=b.workflow('OntiCards native reviewed publication - disabled')
(root/'persistent-publication.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'enabled':False,'github_comment_post_nodes':1,'model_nodes':0,'approval_present':bool(approval)}))
