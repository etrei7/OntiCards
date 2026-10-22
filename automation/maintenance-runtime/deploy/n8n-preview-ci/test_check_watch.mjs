import fs from 'node:fs';
import assert from 'node:assert/strict';
const workflow=JSON.parse(fs.readFileSync(new URL('./check-observe.workflow.json',import.meta.url)));
const run=(name,input,prior={})=>new Function('$input','$',workflow.nodes.find(n=>n.name===name).parameters.jsCode)(
  {first:()=>({json:input}),all:()=>[{json:input}]},name=>({first:()=>({json:prior[name]})}))[0].json;
const identity={mode:'watch',pr:33,head:'f'.repeat(40),base:'c'.repeat(40),check_id:'119950685976',check_name:'OntiCards LibreOffice concurrency evidence',external_id:'pr33-fdd3-final-concurrency'};
const valid=run('Validate Check identity',identity);
let tested=0;
for(const variant of [{mode:'run-tests'},{check_id:'1;id'},{head:'../main'},{pr:0}]){
 assert.throws(()=>run('Validate Check identity',{...identity,...variant}));tested++;
}
const exact={id:Number(identity.check_id),head_sha:identity.head,name:identity.check_name,external_id:identity.external_id,app:{id:5422414},status:'completed',conclusion:'success'};
const proof={...valid,revision:{current:true,observed_head:identity.head,observed_base:identity.base}};
let verdict=run('Determine Check action',{statusCode:200,body:exact},{'Preserve revision proof':proof});
assert.equal(verdict.needs_update,false);assert.equal(verdict.state,'watching');tested++;
for(const revision of [{current:false,observed_head:'e'.repeat(40),observed_base:identity.base},{current:false,observed_head:identity.head,observed_base:'d'.repeat(40)},{current:false,reason:'revision_unavailable'}]){
 verdict=run('Determine Check action',{statusCode:200,body:exact},{'Preserve revision proof':{...proof,revision}});
 assert.equal(verdict.needs_update,true);tested++;
}
for(const change of [{app:{id:1}},{id:99},{head_sha:'a'.repeat(40)},{name:'unrelated'},{external_id:'unrelated'}]){
 verdict=run('Determine Check action',{statusCode:200,body:{...exact,...change}},{'Preserve revision proof':{...proof,revision:{current:false}}});
 assert.equal(verdict.bound,false);assert.equal(verdict.needs_update,false);tested++;
}
const stale=run('Determine Check action',{statusCode:200,body:exact},{'Preserve revision proof':{...proof,revision:{current:false}}});
let result=run('Verify invalidation readback',{statusCode:200,body:exact},{'Determine Check action':stale});
assert.equal(result.state,'watching');assert.equal(result.update_result,'update_outcome_unknown');tested++;
result=run('Verify invalidation readback',{statusCode:200,body:{...exact,conclusion:'action_required'}},{'Determine Check action':stale});
assert.equal(result.state,'invalidated');tested++;
const recovered=run('Determine Check action',{statusCode:200,body:{...exact,conclusion:'action_required'}},{'Preserve revision proof':proof});
assert.equal(recovered.needs_update,false);assert.equal(recovered.state,'invalidated');tested++;
result=run('Return public Check registration',{statusCode:503},{'Preserve public Check result':stale});
assert.equal(result.state,'unverified');assert.equal(JSON.parse(result.detail).token_revoked,false);tested++;
assert(!JSON.stringify(workflow).includes('createModelLease'));assert(!workflow.nodes.some(n=>n.type.endsWith('executeCommand')));tested++;
// Native ExecuteWorkflow may attach metadata not accepted as top-level Code output.
const watch=JSON.parse(fs.readFileSync(new URL('./check-watch.workflow.json',import.meta.url),'utf8'));
const dirty=[{json:{registration_key:'fixture',state:'watching'},pairedItem:{item:0},metadata:{subExecution:{id:'synthetic'}}}];
for(const [w,n] of [[workflow,'Preserve public Check result'],[watch,'Keep verified watch outcomes']]){
 const code=w.nodes.find(x=>x.name===n).parameters.jsCode;
 const output=new Function('$input',code)({all:()=>dirty});
 assert.equal(output.length,1);assert.deepEqual(Object.keys(output[0]),['json']);assert.deepEqual(output[0].json,dirty[0].json);tested++;
}
console.log(JSON.stringify({passed:tested,failed:0,source:'actual native workflow Code nodes',github_requests:0,model_requests:0,synthetic:true}));
