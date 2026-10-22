import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import path from 'node:path';
const base=import.meta.dirname;
const files=['persistent-readonly.workflow.json','persistent-drafts.workflow.json','repository-context.workflow.json','persistent-publication.workflow.json','persistent-semantic-review.workflow.json','bounded-get.workflow.json','persistent-readonly-serial.workflow.json','issue31-manual-resume.workflow.json'];
let count=0;
for(const file of files){
 const w=JSON.parse(fs.readFileSync(path.join(base,file),'utf8'));
 function walk(x){if(typeof x==='string'&&x.startsWith('={{')){assert(!x.slice(3,-2).includes('}}'),file+': nested n8n delimiter');new vm.Script('('+x.slice(3,-2)+')');count++;}else if(Array.isArray(x))x.forEach(walk);else if(x&&typeof x==='object')Object.values(x).forEach(walk);}
 for(const n of w.nodes)walk(n.parameters);
}
const intake=JSON.parse(fs.readFileSync(path.join(base,files[0]),'utf8'));
const next=intake.nodes.find(n=>n.name==='List all Issue and PR records').parameters.options.pagination.pagination.nextURL.slice(3,-2);
assert.equal(vm.runInNewContext(next,{$response:{headers:{link:'<https://api.github.com/repos/stepll2026/OntiCards/issues?page=2>; rel="next"'}}}),'https://api.github.com/repos/stepll2026/OntiCards/issues?page=2');
assert.throws(()=>vm.runInNewContext(next,{$response:{headers:{link:'<https://example.invalid/steal>; rel="next"'}}}));
const output={syntax_expressions:count,next_page_whitespace:true,foreign_next_url_rejected:true,github_requests:0,model_requests:0};
fs.writeFileSync(path.resolve(base,'../../evidence/n8n/persistent-expression-validation.json'),JSON.stringify(output,null,2));
console.log(JSON.stringify(output));
