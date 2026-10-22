// Frozen response replay; never invokes a model or writes a publication.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const base=import.meta.dirname,evidence=path.resolve(base,'../../evidence/n8n');
const w=JSON.parse(fs.readFileSync(path.join(base,'persistent-drafts.workflow.json'),'utf8'));
const expression=w.nodes.find(n=>n.name==='Validate structure and require semantic review').parameters.jsonOutput.slice(3,-2);
const source=JSON.parse(fs.readFileSync(path.join(evidence,'issue29-final-source-snapshot.json'),'utf8'));
const original=JSON.parse(fs.readFileSync(path.join(evidence,'issue29-final-draft-response.json'),'utf8'));
const actual=source.repository_context.commit_sha,wrong='c8e3dfee68d598a37842fc332f73af40a56f02a7';
function run(d,s=source){return vm.runInNewContext('('+expression+')',{$json:{choices:[{message:{content:JSON.stringify(d)}}],usage:{}},$now:{toISO:()=>new Date().toISOString()},$:()=>({first:()=>({json:{event_key:'frozen-only',source_snapshot:JSON.stringify(s)}})})});}
const red=run(original),repairedFixture={...original,summary:original.summary.replaceAll(wrong,actual)};
const metadataOnly={...repairedFixture,summary:'The supplied immutable source is referenced using [baseline_pdf_path].'};
const rendered=run(metadataOnly),poisoned=structuredClone(source);
poisoned.repository_context.files[0].excerpt+=' '+wrong;
poisoned.trusted_facts.repo_README_md.excerpt+=' '+wrong;
const historical={...metadataOnly,summary:'Historical source '+source.trusted_facts.historical_runtime.source_sha+' [historical_exporter_identity].'};
const assertions={
 actual_original_sha_typo_rejected:red.status==='needs_structure_review'&&JSON.parse(red.quality_errors).includes('untrusted commit or blob SHA in model text'),
 corrected_frozen_sha_only_structure_passes:run(repairedFixture).status==='awaiting_semantic_review',
 exact_commit_and_url_rendered_by_set:rendered.reply_zh.includes('['+actual+'](https://github.com/stepll2026/OntiCards/tree/'+actual+')'),
 untrusted_source_excerpt_cannot_whitelist_sha:run(original,poisoned).status==='needs_structure_review',
 verified_historical_metadata_allowed:run(historical).status==='awaiting_semantic_review',
 case_insensitive_known_sha_allowed:run({...metadataOnly,summary:actual.toUpperCase()}).status==='awaiting_semantic_review',
};
for(const[name,value]of Object.entries(assertions))assert.equal(value,true,name);
const record={at:new Date().toISOString(),kind:'actual draft native Set expression frozen response replay',assertions,passed:true,checks:Object.keys(assertions).length,model_calls:0,github_posts:0,original_record_changed:false,limitations:'Corrected text is a synthetic fixture only, not a new model response or publishable approval. Semantic review and exact quote checks remain required.'};
fs.writeFileSync(path.join(evidence,'source-identity-expression-probe.json'),JSON.stringify(record,null,2));console.log(JSON.stringify(record));
