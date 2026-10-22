import fs from 'node:fs';
import assert from 'node:assert/strict';
const load=name=>JSON.parse(fs.readFileSync(new URL(name,import.meta.url)));
const receiver=load('./intake-receiver.workflow.json'),admission=load('./intake-admission.workflow.json'),ci=load('./preview.workflow.json');
const run=(workflow,name,input,prior={},all=null)=>new Function('$input','$',workflow.nodes.find(x=>x.name===name).parameters.jsCode)(
 {first:()=>({json:input}),all:()=>all??[{json:input}]},name=>({first:()=>({json:prior[name]?.[0]??prior[name]}),all:()=>{const p=prior[name];return (Array.isArray(p)?p:[p]).map(json=>({json}));}}));
const p={pr:26,head:'a'.repeat(40),base:'b'.repeat(40),state:'open'};
const snapshot={source:'onticards_intake_threads_v1',watermark:new Date().toISOString(),observed_at:new Date().toISOString(),complete:true,token_revoked:true,threads:[p]};
let count=0;
const candidate=run(receiver,'Validate complete existing snapshot',{body:snapshot})[0].json;assert.equal(candidate.mode,'dispatch');count++;
for(const change of [{complete:false},{token_revoked:false},{source:'other'},{threads:Array(21).fill(p)},{threads:[p,p]},{mode:'paid_retry'},{observed_at:'invalid'},{observed_at:'2000-01-01T00:00:00Z'},{watermark:'invalid'}]){
 assert.throws(()=>run(receiver,'Validate complete existing snapshot',{body:{...snapshot,...change}}));count++;
}
for(const change of [{head:'../main'},{base:'c8e'},{pr:0},{state:'closed'}]){assert.throws(()=>run(receiver,'Validate complete existing snapshot',{body:{...snapshot,threads:[{...p,...change}]}}));count++;}
const identity=run(admission,'Fixed version admission identity',candidate)[0].json;
assert.equal(identity.admission_key,'admission:'+identity.receipt_key);count++;
for(const change of [{head:'c'.repeat(40)},{base:'c'.repeat(40)}]){const n=run(admission,'Fixed version admission identity',{...candidate,...change})[0].json;assert.notEqual(n.admission_key,identity.admission_key);count++;}
const select=(main=[],extra=[])=>run(admission,'Select unseen version',{}, {'Fixed version admission identity':identity,'Read existing CI receipt':main},extra.map(json=>({json})))[0].json;
assert.equal(select().consumed,false);count++;
for(const state of ['running','tests_failed','tests_passed_model_business','dispatch_outcome_unknown']){
 assert.equal(select([{receipt_key:identity.receipt_key,state}]).consumed,true);count++;
}
for(const state of ['budget_exhausted','dispatching','dispatch_outcome_unknown','manual_review_required']){
 assert.equal(select([],[{receipt_key:identity.admission_key,state}]).consumed,true);count++;
}
const selected=select();
for(const rev of [{current:false,reason:'fork_or_stale'},{current:true,token_revoked:false,head:p.head,base:p.base},{current:true,token_revoked:true,head:'d'.repeat(40),base:p.base}]){
 assert.equal(run(admission,'Preserve fresh scope verdict',rev,{'Select unseen version':selected})[0].json.current,false);count++;
}
const proof={...selected,current:true,revision_token_revoked:true};
const budget=quota=>({state:quota>=45000?'budget_available':'budget_exhausted',required_quota:45000,remaining_quota:quota,token_creation_calls:0,provider_calls:0,account_quota_reset:false,checked_at:new Date().toISOString(),watermark:proof.watermark,observed_at:proof.observed_at});
const admissionFor=value=>run(admission,'Determine native admission',{}, {'Preserve fresh scope verdict':{...proof,batch_budget:value}})[0].json;
for(const value of [budget(15445),budget(44999),{...budget(45000),provider_calls:1},{...budget(45000),required_quota:1}]){
 const r=admissionFor(value);assert.equal(r.allowed,false);assert.notEqual(r.state,'dispatching');count++;
}
const blocked=admissionFor(budget(15445));
const row=run(admission,'Prepare persisted admission',blocked)[0].json;assert.equal(row.state,'budget_exhausted');assert.equal(row.receipt_key,identity.admission_key);assert.equal(JSON.parse(row.detail).automatic_retry,false);count++;
const admitted=admissionFor(budget(45000));assert.equal(admitted.state,'dispatching');count++;
for(const change of [{watermark:'other'},{observed_at:'other'},{checked_at:new Date(Date.now()-300001).toISOString()},{checked_at:new Date(Date.now()+6000).toISOString()},{account_quota_reset:true},{remaining_quota:null}]){
 const result=admissionFor({...budget(45000),...change});assert.equal(result.allowed,false);assert.equal(result.state,'budget_unverifiable');count++;
}
assert.equal(admissionFor(null).state,'budget_unverifiable');count++;
const batchCandidates=[26,30,33,40,41,42].map(pr=>({...candidate,pr}));
const need=(candidates,rows)=>run(receiver,'Select bounded unseen batch budget need',{}, {'Validate complete existing snapshot':candidates,'Read existing batch CI receipts':rows})[0].json;
assert.equal(need(batchCandidates,[]).needed,true);count++;
const prior=batchCandidates.map(c=>({receipt_key:`admission:stepll2026/OntiCards#${c.pr}:${c.head}:${c.base}`,state:'budget_exhausted'}));
assert.equal(need(batchCandidates,prior).needed,false);assert.equal(need(batchCandidates.map(c=>({...c,mode:'dry_run'})),[]).needed,false);count++;
const bound=run(receiver,'Bind native observation to exact batch',{stdout:JSON.stringify(budget(15445))},{'Select bounded unseen batch budget need':{candidates:batchCandidates}});
assert.equal(bound.length,6);assert(bound.every(x=>x.json.batch_budget.watermark===candidate.watermark&&x.json.batch_budget.observed_at===candidate.observed_at));count++;
assert.equal(admission.nodes.filter(n=>n.type.endsWith('executeCommand')).length,0);assert.equal(receiver.nodes.filter(n=>n.type.endsWith('executeCommand')).length,1);assert.equal(receiver.nodes.find(n=>n.type.endsWith('executeCommand')).parameters.executeOnce,true);count++;
const uncertain=run(admission,'Record bounded native dispatch outcome',{error:'outcome unavailable'},{'Persist before any CI dispatch':row})[0].json;assert.equal(uncertain.state,'dispatch_outcome_unknown');count++;
const normal=run(ci,'Validate fixed input',{...p})[0].json;assert(!('validation_only'in normal));count++;
const dry=run(ci,'Validate fixed input',{...p,validation_only:true})[0].json;assert.equal(dry.validation_only,true);
const dryProof=run(ci,'Return validation only proof',dry)[0].json;assert.equal(dryProof.state,'dry_run_ci_entry_verified');assert.equal(dryProof.ssh_commands,0);assert.equal(dryProof.model_calls,0);count++;
assert.equal(ci.connections['Validation only entry'].main[0][0].node,'Return validation only proof');
assert.equal(ci.connections['Validation only entry'].main[1][0].node,'Ensure native receipt table');count++;
for(const w of [receiver,admission]){
 assert(!w.nodes.some(n=>n.type.endsWith('scheduleTrigger')));assert(!w.nodes.some(n=>n.type.endsWith('httpRequest')));assert.equal(w.active,false);count++;
}
console.log(JSON.stringify({passed:count,failed:0,source:'actual generated native Code/connection graphs',network_calls:0,provider_calls:0,synthetic:true}));
