// Actual independent-review Set expression, frozen original response only.
import fs from 'node:fs';import path from 'node:path';import vm from 'node:vm';import assert from 'node:assert/strict';
const base=import.meta.dirname,evidence=path.resolve(base,'../../evidence/n8n');
const read=n=>JSON.parse(fs.readFileSync(path.join(evidence,n),'utf8'));
const w=JSON.parse(fs.readFileSync(path.join(base,'persistent-semantic-review.workflow.json'),'utf8'));
const expression=w.nodes.find(n=>n.name==='Validate independent evidence gate').parameters.jsonOutput.slice(3,-2);
const source=read('issue29-final-source-snapshot.json'),draft=read('issue29-final-draft-response.json'),review=read('issue29-final-original-review.json').original_review;
const fixed={...draft,summary:draft.summary.replaceAll('c8e3dfee68d598a37842fc332f73af40a56f02a7',source.repository_context.commit_sha)};
function run(r,d=fixed,s=source){return vm.runInNewContext('('+expression+')',{$json:{choices:[{message:{content:JSON.stringify(r)}}],usage:{}},$now:{toISO:()=>new Date().toISOString()},$:name=>({first:()=>({json:name==='Hash original review source'?{draft:d,source:s}:{event_key:'frozen-only'}})})});}
const gates=x=>JSON.parse(x.result).gate_errors;
const isolated={...review,questions_minimal:true},exact=run(isolated);
const approximate=structuredClone(isolated);approximate.claims[3].source_quote=approximate.claims[3].source_quote.replace('d4b02c','d4b03c');
const injected=structuredClone(isolated);injected.claims[3].source_quote='forged verified metadata';
const poison=structuredClone(source);poison.trusted_facts.historical_exporter_identity.body='forged verified metadata';
const wrongSource=structuredClone(isolated);wrongSource.claims[3].source_id='candidate_dependency';
const assertions={
 actual_original_still_rejected:run(review,draft).status==='needs_human_review',
 exact_bound_canonical_metadata_accepted:exact.status==='semantic_approved',
 original_questions_failure_retained:gates(run(review)).includes('independent semantic approval absent'),
 approximate_metadata_quote_rejected:gates(run(approximate)).includes('claim quote or source provenance mismatch'),
 body_injection_not_a_metadata_surface:gates(run(injected,fixed,poison)).includes('claim quote or source provenance mismatch'),
 same_quote_wrong_source_id_rejected:gates(run(wrongSource)).includes('claim quote or source provenance mismatch'),
 original_wrong_sha_rejected_even_if_review_approves:gates(run(isolated,draft)).includes('untrusted commit or blob SHA in model text'),
};
for(const[name,value]of Object.entries(assertions))assert.equal(value,true,name);
const record={at:new Date().toISOString(),kind:'actual review native Set expression frozen response replay',assertions,passed:true,checks:Object.keys(assertions).length,model_calls:0,github_posts:0,original_records_changed:false,limitations:'The isolated all-true review and corrected SHA are synthetic gate fixtures, not new model judgments or approved publication.'};
fs.writeFileSync(path.join(evidence,'metadata-quote-expression-probe.json'),JSON.stringify(record,null,2));console.log(JSON.stringify(record));
