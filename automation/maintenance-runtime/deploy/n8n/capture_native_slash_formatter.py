"""Capture real shipped MCP formatter with in-memory GitHub transport, no network."""
import datetime,json,subprocess,pathlib,hashlib
image='registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy12@sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa'
source=r'''
import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {postModelReviews}from './dist/packages/api/mcp/reviewModels.js';
import {parseSlashCommand}from './packages/core/dist/webhook/slashCommandParser.js';
const head='a'.repeat(40),base='b'.repeat(40),pr=90001,model='onticards-qwen:opencode-bailian/qwen3.8-max-0902';
const instructions=`由 OntiCards AI 维护流程自动触发。仅审查 stepll2026/OntiCards PR #${pr}，head ${head}，base ${base}。这是一项自动审查请求，不代表新的人工修复或合并授权。保持原生严格审查格式；版本变化时停止，不修改代码、不自动修复、不合并。`;
const captured=[];const principal={github:{request:async(route,request)=>{assert.equal(route,'POST /repos/{owner}/{repo}/issues/{issue_number}/comments');captured.push(request.body);return {data:{id:900001,html_url:'https://example.invalid/native-formatter-fixture'}};}}};
await postModelReviews(principal,{pullRequest:pr,expectedHead:head,instructions},{owner:'stepll2026',repo:'OntiCards',resolvedHead:head,headSource:'fixture',operationId:'offline-fixture-only'},[{command:model,requested:model,agentAlias:'onticards-qwen',model:'opencode-bailian/qwen3.8-max-0902'}]);
assert.equal(captured.length,1);assert.equal(parseSlashCommand(captured[0]).command,'review');
const paths=['dist/packages/api/mcp/reviewModels.js','packages/core/dist/webhook/slashCommandParser.js'];
console.log('SAFE_FIXTURE='+JSON.stringify({body:captured[0],native_command:parseSlashCommand(captured[0]).command,formatter_transport:'in-memory stub only; not a GitHub post',compiled_files:Object.fromEntries(paths.map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]))}));process.exit(0);
'''
run=subprocess.run(['docker','run','--rm','--pull=never','--network','none','-e','PROPR_DEMO_MODE=true','-i',image,'node','--input-type=module'],input=source,text=True,capture_output=True,timeout=30)
assert run.returncode==0,'Isolated native formatter failed; no public action permitted'
record=next(json.loads(line.split('=',1)[1])for line in run.stdout.splitlines()if line.startswith('SAFE_FIXTURE='))
record.update(image=image,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),github_posts=0,model_calls=0,credentials_mounted=False,network='none',source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
p=pathlib.Path('/opt/onticards-maintenance/n8n/evidence/native-mcp-slash-body-fixture.json');p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'native_command':record['native_command'],'github_posts':0,'model_calls':0}))
