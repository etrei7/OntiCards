"""Reuse native n8n JWT/HTTP subworkflow for each fresh, bounded PR revision check."""
import json, uuid
from pathlib import Path

root=Path(__file__).parent
nodes=[]; connections={}
def node(name,kind,parameters,version=1,**extra):
    nodes.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'onticards-preview-revision/'+name)),
      'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,
      'position':[len(nodes)*220,0],'parameters':parameters,**extra})
def link(a,b,index=0):
    branches=connections.setdefault(a,{'main':[]})['main']
    while len(branches)<=index:branches.append([])
    branches[index]=[{'node':b,'type':'main','index':0}]
def code(name,js):node(name,'code',{'jsCode':js},2)
def http(name,method,url,app=False,body=None):
    auth='={{ "Bearer "+$("Sign preview App JWT").first().json.token }}' if app else '={{ "Bearer "+$("Mint preview read token").first().json.body?.token }}'
    p={'method':method,'url':url,'sendHeaders':True,'headerParameters':{'parameters':[
      {'name':'Authorization','value':auth},{'name':'Accept','value':'application/vnd.github+json'},
      {'name':'X-GitHub-Api-Version','value':'2026-03-10'},{'name':'Cache-Control','value':'no-cache'}]},
      'options':{'timeout':20000,'proxy':'http://127.0.0.1:17891',
      'response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}}
    if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=json.dumps(body))
    node(name,'httpRequest',p,4.4,onError='continueRegularOutput',retryOnFail=method=='GET',maxTries=2,waitBetweenTries=500)
node('Native fixed revision request','executeWorkflowTrigger',{'inputSource':'passthrough'},1.1)
code('Validate fixed revision input',"""const p=$input.first().json;
if(!Number.isSafeInteger(p.pr)||p.pr<1||p.pr>9999999||!/^[a-f0-9]{40}$/.test(p.head??'')||!/^[a-f0-9]{40}$/.test(p.base??''))throw new Error('Invalid fixed revision');
return [{json:{pr:p.pr,head:p.head,base:p.base}}];""")
node('Sign preview App JWT','jwt',{'operation':'sign','useJson':True,
  'claimsJson':'={{ JSON.stringify({iat:Math.floor(Date.now()/1000)-60,exp:Math.floor(Date.now()/1000)+540,iss:"5422414"}) }}',
  'headerClaims':'{}','options':{'algorithm':'RS256'}},1,
  credentials={'jwtAuth':{'id':'onticardsPreviewAppJwt','name':'OntiCards preview revision App'}})
http('Mint preview read token','POST','https://api.github.com/app/installations/174029282/access_tokens',True,
     {'repositories':['OntiCards'],'permissions':{'pull_requests':'read','metadata':'read'}})
http('Verify preview token scope','GET','https://api.github.com/installation/repositories?per_page=100')
node('Exact preview read scope','if',{'conditions':{'options':{'typeValidation':'strict'},'conditions':[{
 'id':'scope','leftValue':'={{ (()=>{const m=$("Mint preview read token").first().json,p=m.body?.permissions||{},r=$json;return m.statusCode===201&&typeof m.body?.token==="string"&&Object.keys(p).length===2&&p.pull_requests==="read"&&p.metadata==="read"&&r.statusCode===200&&r.body?.total_count===1&&r.body.repositories?.[0]?.full_name==="stepll2026/OntiCards";})() }}',
 'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
http('Read exact current PR','GET','=https://api.github.com/repos/stepll2026/OntiCards/pulls/{{ $("Validate fixed revision input").first().json.pr }}')
code('Public revision verdict',"""const p=$('Validate fixed revision input').first().json,res=$input.first().json,r=res.body;
const current=res.statusCode===200&&r?.state==='open'&&r.head?.repo?.full_name==='stepll2026/OntiCards'&&r.base?.repo?.full_name==='stepll2026/OntiCards'&&r.head?.ref?.startsWith('codex/')&&r.base.ref==='main'&&r.head.sha===p.head&&r.base.sha===p.base;
return [{json:{...p,current,http_status:res.statusCode??null,observed_head:r?.head?.sha??null,observed_base:r?.base?.sha??null,reason:current?'exact_current_revision':'stale_or_remote_unverifiable',checked_at:new Date().toISOString()}}];""")
code('Scope rejected',"""return [{json:{...$('Validate fixed revision input').first().json,current:false,reason:'installation_scope_unverified',checked_at:new Date().toISOString()}}];""")
code('Preserve public revision',"return $input.all();")
http('Revoke preview read token','DELETE','https://api.github.com/installation/token')
code('Return public revision',"""const p=$('Preserve public revision').first().json,m=$('Mint preview read token').first().json,revoked=$input.first().json.statusCode===204;
return [{json:{...p,current:p.current&&revoked,token_issued:m.statusCode===201,token_revoked:revoked,permissions:{pull_requests:'read',metadata:'read'},credentials_in_output:false}}];""")
chain=['Native fixed revision request','Validate fixed revision input','Sign preview App JWT','Mint preview read token','Verify preview token scope','Exact preview read scope','Read exact current PR','Public revision verdict','Preserve public revision','Revoke preview read token','Return public revision']
for a,b in zip(chain,chain[1:]):link(a,b)
link('Exact preview read scope','Scope rejected',1);link('Scope rejected','Preserve public revision')
w={'id':'onticardsPreviewRevisionV1','name':'OntiCards exact PR revision - native App read only','active':False,'nodes':nodes,'connections':connections,
   'settings':{'executionOrder':'v1','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':180},'pinData':{}}
(root/'revision-guard.workflow.json').write_text(json.dumps(w,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'nodes':len(nodes),'permissions':['pull_requests:read','metadata:read'],'execution_bodies_saved':False}))
