import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const w=JSON.parse(fs.readFileSync(new URL('./review-admission.workflow.json',import.meta.url)));
const run=(name,input,prior={},all=null)=>new Function('$input','$',w.nodes.find(x=>x.name===name).parameters.jsCode)(
 {first:()=>({json:input}),all:()=>all??[{json:input}]},name=>({first:()=>({json:prior[name]}),all:()=>[prior[name]].flat().map(json=>({json}))}));
let checks=0;
const p={pr:26,head:'a'.repeat(40),base:'b'.repeat(40),mode:'review'};
const validated=run('Validate fixed review candidate',p)[0].json;assert.equal(validated.mode,'dry_run');checks++;
for(const bad of [{pr:0},{pr:true},{pr:'26'},{head:'x;id'},{base:'HEAD'}]){assert.throws(()=>run('Validate fixed review candidate',{...p,...bad}));checks++;}
const hash=p=>createHash('sha256').update(JSON.stringify(['stepll2026/OntiCards',p.pr,p.head,p.base])).digest('hex');
const identity=run('Set fixed native key',{...validated,version_hash:hash(p)})[0].json;
for(const state of ['admitted','baseline','native_posted','native_failed','submission_outcome_unknown','credential_cleanup_unknown']) {
 const got=run('Preserve every consumed outcome',{}, {'Set fixed native key':identity},[{json:{review_key:identity.review_key,state}}])[0].json;
 assert.equal(got.consumed,true);assert.deepEqual(got.prior_states,[state]);checks++;
 const prior=run('Return permanent prior outcome',got)[0].json;
 assert.equal(prior.model_started,state==='baseline'?false:null);assert.equal(prior.new_submission,false);
}
for(const change of [{head:'c'.repeat(40)},{base:'c'.repeat(40)}]){assert.notEqual(hash({...p,...change}),hash(p));checks++;}
const baseline=run('Prepare permanent admission before SSH',{...identity,mode:'baseline'})[0].json;
assert.equal(baseline.state,'baseline');assert.equal(JSON.parse(baseline.detail).model_started,false);checks++;
const admission=run('Prepare permanent admission before SSH',{...identity,mode:'review'})[0].json;
assert.equal(admission.state,'admitted');assert.equal(JSON.parse(admission.detail).automatic_retry,false);checks++;
for(const stdout of ['',JSON.stringify({state:'native_posted',pr:99})]){
 const r=run('Project actual fixed capability receipt',{stdout},{'Set fixed native key':{...identity,mode:'review'}})[0].json;
 assert.equal(r.state,'submission_outcome_unknown');assert.equal(JSON.parse(r.detail).model_started,null);checks++;
}
assert.equal(w.connections['Baseline never invokes SSH'].main[1][0].node,'Safe review receipt');checks++;
assert.equal(w.connections['Persist admitted before any mutation'].main[0][0].node,'Baseline never invokes SSH');checks++;
assert.equal(w.nodes.filter(n=>n.type.endsWith('scheduleTrigger')).length,0);assert.equal(w.active,false);checks++;
assert.equal(w.nodes.filter(n=>n.type.endsWith('executeCommand')).length,1);assert(w.nodes.find(n=>n.type.endsWith('executeCommand')).parameters.command.includes('dispatch_review.mjs'));checks++;
console.log(JSON.stringify({passed:checks,total:checks,model_calls:0,native_expressions:true}));
