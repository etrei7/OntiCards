"""Actual source hash/cache graph with frozen HTTP; preserves native red/green."""
import copy,hashlib,json,uuid
from pathlib import Path
root=Path(__file__).parent
files=[{'path':'OntiCards_Api/'+name+'.py','sha':hashlib.sha1(b'blob 3\0'+body.encode()).hexdigest(),'size':3,'commit_sha':'f'*40,'content':body}for name,body in [('a','abc'),('b','def')]]
names=['Select existing bounded source paths','Split verified source paths','Read existing immutable source files','Select matching cached source','Matching immutable content exists','Use cached source through existing hash verifier','Read file at immutable commit','Decode native source content','Verify native Git blob SHA','Require all blob hashes','Loop one immutable source file']
workflows=[]
for mode,path in [('red',root.parents[1]/'evidence/n8n/source-runtime-before-loop-fix.workflow.json'),('green',root/'repository-context.workflow.json')]:
 w=json.loads(path.read_text(encoding='utf-8'));w['id']='onticardsSourceCache'+mode.title()+'Probe';w['name']='OntiCards native source cache '+mode+' fixture';w['active']=False;w['nodes']=[n for n in w['nodes']if n['name']in names]
 w['settings'].update(executionTimeout=45,saveDataSuccessExecution='none',saveDataErrorExecution='none',saveManualExecutions=False)
 w['connections']={a:{'main':[[e for e in branch if e['node']in names]for branch in c['main']]}for a,c in w['connections'].items()if a in names}
 def link(a,b,index=0):
  branches=w['connections'].setdefault(a,{'main':[]})['main']
  while len(branches)<=index:branches.append([])
  branches[index]=[{'node':b,'type':'main','index':0}]
 def add(name,kind,p,version):w['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[0,0],'parameters':p})
 for n in w['nodes']:
  n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+n['name']));n.pop('credentials',None)
  if n['name']=='Select existing bounded source paths':n['parameters']['jsonOutput']='={{ {paths:$("Cache fixture request").first().json.body.case==="cached"?'+json.dumps(files[:1])+':$("Cache fixture request").first().json.body.case==="fresh"?'+json.dumps(files[1:])+':'+json.dumps(files)+'} }}'
  if n['name']=='Read existing immutable source files':n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':json.dumps({'commit_sha':'f'*40,'path':files[0]['path'],'blob_sha':files[0]['sha'],'content':'abc'}),'options':{}}
  if n['name']=='Read file at immutable commit':n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':'={{ (()=>{const e=$("Split verified source paths").item.json;return {statusCode:200,body:{type:"file",path:e.path,sha:e.sha,size:e.size,encoding:"base64",content:($("Cache fixture request").first().json.body.case==="bad_hash"?"xxx":e.content).base64Encode()}};})() }}','options':{}};n['retryOnFail']=False
 add('Cache fixture request','webhook',{'httpMethod':'POST','path':'onticards-source-cache-'+mode,'responseMode':'responseNode','options':{}},2.1);w['nodes'][-1]['webhookId']='onticards-source-cache-'+mode
 add('Return actual hash aggregation','respondToWebhook',{'respondWith':'json','responseBody':'={{ {complete:$json.complete,count:$json.files.length,expected:$("Select existing bounded source paths").first().json.paths.length,diagnostics:$json.diagnostics,model_requests:0,github_requests:0} }}','options':{}},1.4)
 link('Cache fixture request','Read existing immutable source files');link('Read existing immutable source files','Select existing bounded source paths');link('Select existing bounded source paths','Split verified source paths');link('Require all blob hashes','Return actual hash aggregation')
 def spacing(v):
  if isinstance(v,dict):return {k:spacing(x)for k,x in v.items()}
  if isinstance(v,list):return [spacing(x)for x in v]
  if isinstance(v,str)and v.startswith('={{'):
   inner=v[3:-2]
   while '}}'in inner:inner=inner.replace('}}','} }')
   return '={{'+inner+'}}'
  return v
 for n in w['nodes']:n['parameters']=spacing(n['parameters'])
 workflows.append(w)
(root/'source-cache-loop-probe.workflow.json').write_text(json.dumps(workflows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'workflows':len(workflows),'external_http_nodes':0,'models':0}))
