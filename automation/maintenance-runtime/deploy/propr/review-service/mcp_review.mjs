// Trusted host adapter only. Reuses ProPR's native grants, policy, MCP and receipts.
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {projectReceipt,projectFailure,requireRevocation,findPriorOperation} from './receipt.mjs';
const require=createRequire('/usr/src/app/package.json');
const {db}=await import(require.resolve('@propr/core'));
const native='/usr/src/app/dist/packages/api/';
const {githubUserGrantService}=await import(native+'githubUserGrantService.js');
const {resolveDurableInstanceAuthorization}=await import(native+'authorization.js');
const {resolveMcpConfig,getMcpScopeCeilingSync}=await import(native+'mcp/configResolver.js');
const {McpOAuthProvider}=await import(native+'mcp/oauth.js');
const {McpStore,digest}=await import(native+'mcp/store.js');
const {McpPolicy}=await import(native+'mcp/policy.js');
const {canonical}=await import(native+'mcp/operations.js');
const {resolveReviewModels}=await import(native+'mcp/reviewModels.js');
const owner='318866723',repository='stepll2026/OntiCards',clientId='onticards-version-review';
const expectedResource='https://127.0.0.1:18135/api/mcp';
let provider,grant,result={state:'service_unavailable',automatic_retry:false},bearer,mutationAttempted=false;
function fail(code){const error=new Error(code);error.safeCode=code;throw error;}
function identity(p){
  if(!p||Object.keys(p).sort().join(',')!=='base,head,idempotency_key,mode,pr,repository'||p.repository!==repository||
     !Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!['dry_run','review','status'].includes(p.mode)||
     !/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??''))fail('INVALID_IDENTITY');
  if(p.idempotency_key!=='review-'+createHash('sha256').update(JSON.stringify([repository,p.pr,p.head,p.base])).digest('hex'))fail('INVALID_IDEMPOTENCY_KEY');
  return p;
}
async function rpc(method,params,id){
  const response=await fetch(expectedResource,{method:'POST',headers:{Authorization:'Bearer '+bearer,
    Accept:'application/json, text/event-stream','Content-Type':'application/json','MCP-Protocol-Version':'2025-11-25'},
    body:JSON.stringify({jsonrpc:'2.0',id,method,params}),signal:AbortSignal.timeout(60000)});
  if(!response.ok)fail('NATIVE_MCP_HTTP_'+response.status);
  const text=await response.text();
  const packet=response.headers.get('content-type')?.includes('text/event-stream')
    ? text.split('\n').filter(line=>line.startsWith('data: ')).map(line=>JSON.parse(line.slice(6))).find(x=>x.id===id)
    : JSON.parse(text);
  if(!packet||packet.error)fail('NATIVE_MCP_REJECTED');
  return packet.result;
}
try{
  const chunks=[];let length=0;
  for await(const chunk of process.stdin){length+=chunk.length;if(length>4096)fail('INPUT_TOO_LARGE');chunks.push(chunk);}
  const p=identity(JSON.parse(Buffer.concat(chunks).toString()));
  result={...p,automatic_retry:false,model_started:false,checked_at:new Date().toISOString()};
  const config=await resolveMcpConfig(db);
  if(!config||config.resource!==expectedResource)fail('MCP_CONFIGURATION_UNAVAILABLE');
  if(JSON.stringify([...(getMcpScopeCeilingSync()??config.scopeCeiling??[])].sort())!==JSON.stringify(['read','review']))fail('MCP_SCOPE_CEILING_MISMATCH');
  const shared=await githubUserGrantService.resolve(owner);
  if(shared.status!=='active')fail('NATIVE_USER_GRANT_UNAVAILABLE');
  const row=await db('github_user_grants').where({github_user_id:owner}).first('github_username');
  if(row?.github_username!=='stepll2026')fail('NATIVE_OWNER_MISMATCH');
  const user={id:owner,login:row.github_username,username:row.github_username,displayName:row.github_username,email:null,avatarUrl:null,
    accessToken:shared.accessToken,refreshToken:shared.refreshToken,tokenExpiresAt:shared.tokenExpiresAt,refreshTokenExpiresAt:shared.refreshTokenExpiresAt};
  const authorization=await resolveDurableInstanceAuthorization(owner,db);
  if(!['local','managed','connect'].includes(authorization.source))fail('NATIVE_MEMBERSHIP_UNAVAILABLE');
  provider=new McpOAuthProvider(new McpStore(db,config.encryptionKey),config,()=>getMcpScopeCeilingSync()??config.scopeCeiling);
  await provider.store.put('client',clientId,{client_id:clientId,client_name:'OntiCards automatic version review',redirect_uris:[],grant_types:[],response_types:[],token_endpoint_auth_method:'none'});
  const issued=await provider.issueDelegatedGrant({credential:user,clientId,clientName:'OntiCards automatic version review',
    scopes:['read','review'],repositories:[repository],membershipSource:authorization.source,ttlMs:300000});
  grant=issued.grant;bearer=issued.accessToken;
  const policy=new McpPolicy(provider,config),principal=await policy.authenticate(bearer);
  policy.requireScope(principal,'review');await policy.repository(principal,repository,true);
  if(grant.repositories.length!==1||JSON.stringify([...principal.scopes].sort())!==JSON.stringify(['read','review']))fail('NATIVE_GRANT_SCOPE_MISMATCH');
  result.grant_scopes=['read','review'];result.grant_repository_count=1;
  const pr=(await principal.github.request('GET /repos/{owner}/{repo}/pulls/{pull_number}',{owner:'stepll2026',repo:'OntiCards',pull_number:p.pr})).data;
  if(pr.state!=='open'||pr.head.sha!==p.head||pr.base.sha!==p.base||pr.base.ref!=='main'||pr.base.repo?.full_name!==repository)fail('FRESH_REVISION_OR_SCOPE_REJECTED');
  result.fresh_revision=true;
  const instructions=`由 OntiCards AI 维护流程自动触发。仅审查 ${repository} PR #${p.pr}，head ${p.head}，base ${p.base}。这是一项自动审查请求，不代表新的人工修复或合并授权。保持原生严格审查格式；版本变化时停止，不修改代码、不自动修复、不合并。`;
  const model='onticards-qwen:opencode-bailian/qwen3.8-max-0902';
  const choices=await resolveReviewModels([model]); // Existing enabled-model validation; never substitutes a model.
  if(choices.length!==1||choices[0].agentAlias!=='onticards-qwen'||choices[0].model!=='opencode-bailian/qwen3.8-max-0902')fail('NATIVE_REVIEW_MODEL_MISMATCH');
  const args={repository,pullRequest:p.pr,idempotencyKey:p.idempotency_key,expectedHead:p.head,instructions,model};
  const hash=digest(canonical({tool:'review_pull_request',args}));
  // Native idempotency includes grant_id. Preserve semantics across new short grants.
  const previous=await findPriorOperation(db,{owner,repository,key:p.idempotency_key,hash});
  if(previous){
    Object.assign(result,{state:'already_recorded',operation_id:previous.id,native_state:previous.state,native_lifecycle:previous.lifecycle,native_payload_match:true,model_started:null});
  }else if(p.mode==='status'){
    result.state='no_native_operation';
  }else{
    await rpc('initialize',{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:clientId,version:'1'}},1);
    const list=await rpc('tools/list',{},2);const names=new Set(list.tools?.map(t=>t.name));
    result.tls_verified=true;result.review_tool_visible=names.has('review_pull_request');result.merge_tool_visible=names.has('merge_pull_request');
    if(!result.review_tool_visible||result.merge_tool_visible)fail('NATIVE_VISIBLE_SCOPE_MISMATCH');
    if(p.mode==='dry_run')result.state='native_review_entry_verified_no_dispatch';
    else{
      // The host policy is configuration, never supplied by a PR or the SSH caller.
      const policy=JSON.parse(await fs.readFile('/run/propr-review/policy.json','utf8'));
      if(policy.enabled!==true||policy.repository!==repository||!Array.isArray(policy.baseline_versions)||policy.baseline_versions.includes(p.idempotency_key))fail('AUTOMATIC_REVIEW_NOT_ARMED_FOR_VERSION');
      mutationAttempted=true;result.model_started=null;
      const response=await rpc('tools/call',{name:'review_pull_request',arguments:args},3);
      Object.assign(result,projectReceipt(response,p));
    }
  }
}catch(error){Object.assign(result,projectFailure(error,mutationAttempted));}
finally{
  if(grant&&provider){try{await provider.revokeGrant(grant.id);const row=await provider.store.get('grant',grant.id);result.grant_revocation=row?.revoked===true?'revoked_verified':'unknown';}catch{result.grant_revocation='unknown';}}
  else result.grant_revocation='not_issued';
  result=requireRevocation(result);
  bearer=undefined;
  process.stdout.write('ONTICARDS_REVIEW_RESULT:'+JSON.stringify(result)+'\n');
  await db.destroy();
  process.exit(0);
}
