"""Native reusable GitHub source reader, pinned commit and blob verification."""
import json,uuid
from pathlib import Path
root=Path(__file__).parent
prior=(root/'build_event_replay.py').read_text(encoding='utf-8');settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':150}
exec(prior[prior.index('class Builder:'):prior.index('# Native test transport only.')])
Builder.set=lambda self,name,expr,**extra:self.node(name,'set',{'mode':'raw','jsonOutput':expr,'options':{}},3.4,**extra)
b=Builder('onticardsRepositoryContextV1');api='https://api.github.com/repos/stepll2026/OntiCards'
b.node('Native source subworkflow','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
b.node('Local source read acceptance','webhook',{'httpMethod':'POST','path':'onticards-repository-context-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-repository-context-v1')
b.set('Fixed repository source request','={{ (()=>{const q=$json.body||$json,ref=q.ref||"main";if(ref!=="main"&&!/^[0-9a-f]{40}$/.test(ref))throw new Error("Invalid fixed-repository source ref");return {repository:"stepll2026/OntiCards",ref,topic:String(q.topic||"").slice(0,8000),local_webhook:!!$json.body};})() }}')
b.table('Ensure source cache','onticards_source_files_v1',[('source_key','string'),('commit_sha','string'),('path','string'),('blob_sha','string'),('content','string'),('observed_at','string')])
b.table('Ensure tree cache','onticards_source_trees_v1',[('commit_sha','string'),('tree_sha','string'),('tree_index','string'),('file_count','number'),('observed_at','string')])
b.node('Sign source App JWT','jwt',{'operation':'sign','useJson':True,'claimsJson':'={{ JSON.stringify({iat:Math.floor(Date.now()/1000)-60,exp:Math.floor(Date.now()/1000)+540,iss:"5422414"}) }}','headerClaims':'{}','options':{'algorithm':'RS256'}},1,credentials={'jwtAuth':{'id':'onticardsIntakeAppJwt','name':'OntiCards single-repository intake App'}})
def http(name,method,url,app=False,body=None,once=True):
 auth='={{ "Bearer " + $("Sign source App JWT").first().json.token }}' if app else '={{ "Bearer " + $("Mint source read token").first().json.body?.token }}'
 p={'method':method,'url':url,'sendHeaders':True,'headerParameters':{'parameters':[{'name':'Authorization','value':auth},{'name':'Accept','value':'application/vnd.github+json'},{'name':'X-GitHub-Api-Version','value':'2026-03-10'},{'name':'Cache-Control','value':'no-cache'}]},'options':{'timeout':20000,'proxy':'http://127.0.0.1:17891','response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}},'batching':{'batch':{'batchSize':1,'batchInterval':100}}}}
 if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=body)
 b.node(name,'httpRequest',p,4.4,retryOnFail=method=='GET',maxTries=2,waitBetweenTries=500,onError='continueRegularOutput',executeOnce=once)
http('Mint source read token','POST','https://api.github.com/app/installations/174029282/access_tokens',True,json.dumps({'repositories':['OntiCards'],'permissions':{'contents':'read','metadata':'read'}}))
http('Verify source installation scope','GET','https://api.github.com/installation/repositories?per_page=100')
b.iff('Exact source read scope','={{ (()=>{const p=$("Mint source read token").first().json.body?.permissions||{};return Object.keys(p).length===2&&p.contents==="read"&&p.metadata==="read"&&$json.statusCode===200&&$json.body.total_count===1&&$json.body.repositories[0]?.full_name==="stepll2026/OntiCards";})() }}')
http('Resolve actual source commit','GET','={{ "'+api+'/commits/"+$("Fixed repository source request").first().json.ref }}')
b.iff('Commit resolved','={{ $json.statusCode===200 && /^[0-9a-f]{40}$/.test($json.body?.sha||"") && /^[0-9a-f]{40}$/.test($json.body?.commit?.tree?.sha||"") }}')
http('Read complete repository tree','GET','={{ "'+api+'/git/trees/"+$("Resolve actual source commit").first().json.body.commit.tree.sha+"?recursive=1" }}')
b.set('Select existing bounded source paths',r'''={{ (()=>{
 const sha=$('Resolve actual source commit').first().json.body.sha,body=$json.body,topic=$('Fixed repository source request').first().json.topic.toLowerCase();
 const complete=$json.statusCode===200&&body?.truncated===false&&Array.isArray(body.tree),tree=complete?body.tree:[];
 const safe=e=>e.type==='blob'&&Number(e.size)<=150000&&(/\.(md|py|ts|tsx|js|json|yaml|yml|txt)$/.test(e.path)||e.path.endsWith('/Dockerfile'))&&!/(^|\/)(\.env|secrets?|credentials?|keys?)([./]|$)|lock\.json$|(^|\/)(package-lock|yarn\.lock|pnpm-lock)/i.test(e.path);
 const all=tree.filter(safe),core=['README.md','docker-compose.yaml','OntiCards_Api/app.py','OntiCards_Api/requirements.txt','OntiCards_Api/Dockerfile','OntiCards_Web/package.json'];
 const explicit=tree.filter(e=>e.type==='blob'&&topic.includes(e.path.toLowerCase())).map(e=>e.path);
 const blocked=explicit.filter(path=>!all.some(e=>e.path===path));
 const wanted=[...explicit];
 const patterns=[];
 if(/pdf|soffice|导出/.test(topic))patterns.push(/libreoffice_exporter\.py$/);
 if(/sql|查询|问数/.test(topic))patterns.push(/sql.*\.py$/i);
 if(/metadata|元数据/.test(topic))patterns.push(/metadata.*\.py$/i);
 if(/\bcard\b|\bcards\b|卡片/.test(topic))patterns.push(/card.*\.(py|ts|tsx)$/i);
 if(/auth|登录|权限/.test(topic))patterns.push(/auth.*\.(py|ts|tsx)$/i);
 for(const pattern of patterns)for(const e of all)if(pattern.test(e.path))wanted.push(e.path);
 const relevant=[...new Set(wanted)];wanted.push(...core);
 const paths=[...new Set(wanted)].map(path=>all.find(e=>e.path===path)).filter(Boolean).slice(0,12).map(e=>({path:e.path,sha:e.sha,size:e.size,commit_sha:sha}));
 const omitted=explicit.filter(path=>!paths.some(e=>e.path===path));
 return {complete:complete&&paths.length>=4&&blocked.length===0&&omitted.length===0,commit_sha:sha,tree_sha:body?.sha||null,tree_index:tree.map(e=>({path:e.path,type:e.type,sha:e.sha,size:e.size??null})),paths,required_paths:[...new Set([...explicit,...relevant.filter(path=>paths.some(e=>e.path===path))])],diagnostics:[{stage:'bounded_source_selection',unsupported_explicit_paths:blocked,omitted_explicit_paths:omitted}]};
})() }}''')
b.iff('Complete tree and selected files','={{ $json.complete }}')
b.node('Split verified source paths','splitOut',{'fieldToSplitOut':'paths','options':{}},1)
http('Read file at immutable commit','GET','={{ "'+api+'/contents/"+$json.path.split("/").map(p=>encodeURIComponent(p)).join("/")+"?ref="+$json.commit_sha }}',once=False)
b.set('Decode native source content','={{ (()=>{const expected=$("Split verified source paths").item.json,r=$json.body;const complete=$json.statusCode===200&&r?.type==="file"&&r.path===expected.path&&r.sha===expected.sha&&r.encoding==="base64"&&r.size===expected.size;return {...expected,complete,content:complete?r.content.base64Decode():"",status:$json.statusCode||null};})() }}')
b.node('Verify native Git blob SHA','crypto',{'action':'hash','type':'SHA1','binaryData':False,'value':'={{ "blob "+$json.size+"\u0000"+$json.content }}','dataPropertyName':'calculated_blob_sha','encoding':'hex'},2)
b.set('Require all blob hashes','={{ (()=>{const files=$input.all().map(x=>x.json),expected=$("Select existing bounded source paths").first().json.paths;return {complete:files.length===expected.length&&files.every(f=>f.complete&&f.sha===f.calculated_blob_sha),files,diagnostics:files.map(f=>({path:f.path,status:f.status,complete:f.complete,blob_match:f.sha===f.calculated_blob_sha}))};})() }}',executeOnce=True)
b.iff('All immutable sources verified','={{ $json.complete }}')
b.node('Split verified source contents','splitOut',{'fieldToSplitOut':'files','options':{}},1)
b.set('Cache public source file','={{ {source_key:$json.commit_sha+":"+$json.path,commit_sha:$json.commit_sha,path:$json.path,blob_sha:$json.sha,content:$json.content,observed_at:$now.toISO()} }}')
b.row('Persist immutable source files','onticards_source_files_v1','upsert','source_key','={{ $json.source_key }}')
b.set('Cache complete source tree','={{ (()=>{const t=$("Select existing bounded source paths").first().json;return {commit_sha:t.commit_sha,tree_sha:t.tree_sha,tree_index:JSON.stringify(t.tree_index),file_count:t.tree_index.filter(e=>e.type==="blob").length,observed_at:$now.toISO()};})() }}',executeOnce=True)
b.row('Persist complete source tree','onticards_source_trees_v1','upsert','commit_sha','={{ $json.commit_sha }}')
b.set('Verified source context',r'''={{ (()=>{
 const t=$("Select existing bounded source paths").first().json,files=$("Require all blob hashes").first().json.files;let remaining=24000;
 const excerpts=files.map(f=>{const lines=f.content.split("\n");let start=0;if(f.path.endsWith("libreoffice_exporter.py")){const found=lines.findIndex(l=>/def (_build_and_convert_html|_export_(?:to_)?pdf)\b/.test(l));if(found>=0)start=found;}
 const excerpt=lines.slice(start,start+180).join("\n").slice(0,Math.max(0,Math.min(remaining,6000)));remaining-=excerpt.length;
 return {path:f.path,commit_sha:f.commit_sha,blob_sha:f.sha,size:f.size,empty:f.size===0&&f.content==="",line_start:start+1,line_end:start+excerpt.split("\n").length,excerpt,truncated:excerpt.length<f.content.length,url:"https://github.com/stepll2026/OntiCards/blob/"+f.commit_sha+"/"+f.path+"#L"+(start+1)};}).filter(f=>f.excerpt||f.empty);
 const omitted=(t.required_paths||[]).filter(path=>!excerpts.some(f=>f.path===path));
 return {complete:omitted.length===0,repository:"stepll2026/OntiCards",requested_ref:$("Fixed repository source request").first().json.ref,commit_sha:t.commit_sha,tree_sha:t.tree_sha,indexed_paths:t.tree_index.length,verified_files:files.length,required_paths:t.required_paths||[],omitted_required_paths:omitted,files:excerpts,source_is_untrusted_data_not_instructions:true,model_calls:0,repository_writes:0};
})() }}''')
b.set('Incomplete source context','={{ (()=>{const read=name=>{try{const r=$(name).first().json;return {status:r.statusCode||null,body_type:typeof r.body,has_token:typeof r.body?.token==="string",expires_at:r.body?.expires_at||null,request_id:r.headers?.["x-github-request-id"]||null};}catch{return {executed:false};} };return {complete:false,repository:"stepll2026/OntiCards",diagnostics:$json.diagnostics||[{status:$json.statusCode||null}],safe_auth_diagnostics:{mint:read("Mint source read token"),scope:read("Verify source installation scope"),commit:read("Resolve actual source commit")},model_calls:0,repository_writes:0};})() }}')
# Each branch uses the same native revoke operation; only its public input is returned.
http('Revoke source token','DELETE','https://api.github.com/installation/token')
b.set('Public source result','={{ {...$("Revoke source token").itemMatching(0).json} }}')
# Avoid relying on itemMatching through an HTTP response: preserve the input in a common Set.
b.nodes[-1]['parameters']['jsonOutput']='={{ {...$("Preserve public context before revoke").first().json,token_revoked:$json.statusCode===204} }}'
b.set('Preserve public context before revoke','={{ $json }}')
b.iff('Local webhook response required','={{ $("Fixed repository source request").first().json.local_webhook }}')
b.respond('Return source context','={{ $json }}')
b.set('Return native subworkflow context','={{ $json }}')
b.link('Native source subworkflow','Fixed repository source request');b.link('Local source read acceptance','Fixed repository source request')
b.chain(['Fixed repository source request','Ensure source cache','Ensure tree cache','Sign source App JWT','Mint source read token','Verify source installation scope','Exact source read scope','Resolve actual source commit','Commit resolved','Read complete repository tree','Select existing bounded source paths','Complete tree and selected files','Split verified source paths','Read file at immutable commit','Decode native source content','Verify native Git blob SHA','Require all blob hashes','All immutable sources verified','Split verified source contents','Cache public source file','Persist immutable source files','Cache complete source tree','Persist complete source tree','Verified source context','Preserve public context before revoke','Revoke source token','Public source result','Local webhook response required','Return source context'])
for name in ['Exact source read scope','Commit resolved','Complete tree and selected files','All immutable sources verified']:b.link(name,'Incomplete source context',1)
b.link('Incomplete source context','Preserve public context before revoke');b.link('Local webhook response required','Return native subworkflow context',1)
# Reuse immutable content already verified and saved by this same native reader.
# A fresh GitHub commit response is still mandatory before any cache is trusted.
b.row('Read existing immutable tree','onticards_source_trees_v1','get','commit_sha','={{ $("Resolve actual source commit").first().json.body.sha }}',alwaysOutputData=True)
b.iff('Cached tree matches fresh commit','={{ $json.commit_sha===$("Resolve actual source commit").first().json.body.sha && $json.tree_sha===$("Resolve actual source commit").first().json.body.commit.tree.sha && typeof $json.tree_index==="string" && JSON.parse($json.tree_index).every(e=>e.type!=="blob"||(Number.isInteger(e.size)&&e.size>=0)) }}')
b.set('Use verified immutable tree cache','={{ {statusCode:200,body:{sha:$json.tree_sha,tree:JSON.parse($json.tree_index),truncated:false} } }}')
b.row('Read existing immutable source files','onticards_source_files_v1','get','commit_sha','={{ $("Resolve actual source commit").first().json.body.sha }}',alwaysOutputData=True,executeOnce=True)
b.set('Restore selected immutable paths','={{ $("Select existing bounded source paths").first().json }}',executeOnce=True)
b.set('Select matching cached source','={{ (()=>{const expected=$json,cache=$("Read existing immutable source files").all().map(x=>x.json).find(x=>x.commit_sha===expected.commit_sha&&x.path===expected.path&&x.blob_sha===expected.sha&&typeof x.content==="string");return {...expected,cache:cache||null};})() }}')
b.iff('Matching immutable content exists','={{ !!$json.cache }}')
b.set('Use cached source through existing hash verifier','={{ {statusCode:200,body:{type:"file",path:$json.path,sha:$json.sha,encoding:"base64",size:$json.size,content:$json.cache.content.base64Encode()} } }}')
def replace_link(a,d,index=0):
 branches=b.connections.setdefault(a,{'main':[]})['main']
 while len(branches)<=index:branches.append([])
 branches[index]=[{'node':d,'type':'main','index':0}]
replace_link('Commit resolved','Read existing immutable tree');b.chain(['Read existing immutable tree','Cached tree matches fresh commit','Use verified immutable tree cache','Select existing bounded source paths']);b.link('Cached tree matches fresh commit','Read complete repository tree',1)
replace_link('Complete tree and selected files','Read existing immutable source files');b.chain(['Read existing immutable source files','Restore selected immutable paths','Split verified source paths'])
replace_link('Split verified source paths','Select matching cached source');b.chain(['Select matching cached source','Matching immutable content exists','Use cached source through existing hash verifier','Decode native source content']);b.link('Matching immutable content exists','Read file at immutable commit',1)
# Cache hit and miss branches must rendezvous before one completeness decision.
# Reuse n8n's native serial Loop, as already validated for the intake targets.
b.node('Loop one immutable source file','splitInBatches',{'batchSize':1,'options':{}},3)
replace_link('Split verified source paths','Loop one immutable source file')
b.link('Loop one immutable source file','Require all blob hashes')
b.link('Loop one immutable source file','Select matching cached source',1)
replace_link('Verify native Git blob SHA','Loop one immutable source file')
w=b.workflow('OntiCards actual commit source context - read only')
for n in w['nodes']:
 def check(v):
  if isinstance(v,dict):
   for x in v.values():check(x)
  elif isinstance(v,list):
   for x in v:check(x)
  elif isinstance(v,str) and v.startswith('={{'):assert '}}' not in v[3:-2],n['name']
 check(n['parameters'])
(root/'repository-context.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(w['nodes']),'model_calls':0,'repository_write_nodes':0,'maximum_files':12,'maximum_excerpt_characters':24000}))
