// Execute the actual native Set expressions with frozen public tree/file inputs.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const base=import.meta.dirname;
const current=JSON.parse(fs.readFileSync(path.join(base,'repository-context.workflow.json'),'utf8'));
const previous=JSON.parse(fs.readFileSync(path.resolve(base,'../../evidence/n8n/source-runtime-before-loop-fix.workflow.json'),'utf8'));
const core=['README.md','docker-compose.yaml','OntiCards_Api/app.py','OntiCards_Api/requirements.txt','OntiCards_Api/Dockerfile','OntiCards_Web/package.json'];
const targets=['OntiCards_Api/ext_migrate.py','OntiCards_Api/models/__init__.py','OntiCards_Api/migrations/deploy_check.py'];
const pdf='OntiCards_Api/libreoffice_exporter.py';
const make=paths=>paths.map(p=>({path:p,type:'blob',size:6000,sha:'a'.repeat(40)}));
function expression(w,name,data,lookup){
 const code=w.nodes.find(n=>n.name===name).parameters.jsonOutput.slice(3,-2);
 return vm.runInNewContext('('+code+')',{$json:data,$:name=>({first:()=>({json:lookup[name]})})});
}
function select(w,topic,paths){return expression(w,'Select existing bounded source paths',{statusCode:200,body:{truncated:false,sha:'b'.repeat(40),tree:make(paths)}},{'Fixed repository source request':{topic,ref:'main'},'Resolve actual source commit':{body:{sha:'c'.repeat(40)}}});}
function context(w,selected){return expression(w,'Verified source context',{}, {'Select existing bounded source paths':selected,'Require all blob hashes':{files:selected.paths.map(f=>({...f,content:'x'.repeat(6000)}))},'Fixed repository source request':{ref:'main'}});}
const topic=targets.join(' '),paths=[...core,...targets,'OntiCards_Api/cards.py',pdf];
const red=context(previous,select(previous,topic,paths));
const selected=select(current,topic,paths),green=context(current,selected);
const assertions={
 old_real_expression_omits_explicit_targets:targets.some(p=>!red.files.some(f=>f.path===p)),
 explicit_targets_precede_optional_core:targets.every((p,i)=>selected.paths[i].path===p),
 requested_excerpts_present:green.complete&&targets.every(p=>green.files.some(f=>f.path===p)),
 optional_core_truncation_allowed:green.complete&&green.files.length<selected.paths.length,
 brand_does_not_select_cards:!select(current,'OntiCards deployment',paths).paths.some(f=>f.path.endsWith('cards.py')),
 pdf_topic_is_first:select(current,'PDF export',paths).paths[0].path===pdf,
 selected_file_and_excerpt_caps:selected.paths.length<=12&&green.files.reduce((s,f)=>s+f.excerpt.length,0)<=24000,
 unsupported_explicit_target_rejected:select(current,'OntiCards_Api/entrypoint.sh',[...paths,'OntiCards_Api/entrypoint.sh']).complete===false,
};
const many=Array.from({length:13},(_,i)=>'OntiCards_Api/requested_'+i+'.py');
const overflow=select(current,many.join(' '),[...core,...many]);
assertions.explicit_file_limit_rejected=overflow.complete===false&&overflow.diagnostics[0].omitted_explicit_paths.length===1;
const five=many.slice(0,5),limited=context(current,select(current,five.join(' '),[...core,...five]));
assertions.explicit_excerpt_limit_rejected=limited.complete===false&&limited.omitted_required_paths.length===1;
const emptySelection=select(current,targets[1],paths);emptySelection.paths.find(f=>f.path===targets[1]).size=0;
const emptyContext=expression(current,'Verified source context',{}, {'Select existing bounded source paths':emptySelection,'Require all blob hashes':{files:emptySelection.paths.map(f=>({...f,content:f.size===0?'':'x'.repeat(6000)}))},'Fixed repository source request':{ref:'main'}});
assertions.verified_empty_file_remains_present=emptyContext.complete&&emptyContext.files.some(f=>f.path===targets[1]&&f.size===0&&f.empty===true&&f.excerpt==='');
const pdfSelected=select(current,'PDF export',paths);const pdfExcerpt=expression(current,'Verified source context',{}, {'Select existing bounded source paths':pdfSelected,'Require all blob hashes':{files:pdfSelected.paths.map(f=>({...f,content:f.path===pdf?Array(200).fill('# header').join('\n')+'\n    def _export_pdf(self):\n        pass':'x'.repeat(6000)}))},'Fixed repository source request':{ref:'main'}});
assertions.existing_pdf_method_excerpt_starts_at_actual_definition=pdfExcerpt.complete&&pdfExcerpt.files[0].line_start===201&&pdfExcerpt.files[0].excerpt.includes('def _export_pdf');
const helperContent=Array(100).fill('# header').join('\n')+'\n    def _build_and_convert_html(self):\n'+Array(80).fill('# conversion').join('\n')+'\n    def _export_pdf(self):\n        return self._build_and_convert_html()';
const helperContext=expression(current,'Verified source context',{}, {'Select existing bounded source paths':pdfSelected,'Require all blob hashes':{files:pdfSelected.paths.map(f=>({...f,content:f.path===pdf?helperContent:'x'.repeat(6000)}))},'Fixed repository source request':{ref:'main'}});
assertions.pdf_helper_and_entry_in_same_bounded_excerpt=helperContext.files[0].line_start===101&&helperContext.files[0].excerpt.includes('def _build_and_convert_html')&&helperContext.files[0].excerpt.includes('def _export_pdf');
for(const [name,result]of Object.entries(assertions))assert.equal(result,true,name);
const record={at:new Date().toISOString(),kind:'actual native Set expressions with frozen inputs',assertions,passed:true,checks:Object.keys(assertions).length,model_requests:0,github_requests:0,limitations:'This checks selection/projection, not live GitHub transport; independent native three-ref validation is separate.'};
fs.writeFileSync(path.resolve(base,'../../evidence/n8n/source-relevance-expression-probe.json'),JSON.stringify(record,null,2));
console.log(JSON.stringify(record));
