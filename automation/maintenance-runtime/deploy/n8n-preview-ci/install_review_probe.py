"""Import native review child and run one authenticated, fixed read-only transport probe.
Does not attach it to recurring intake or enable actual review.
"""
import datetime,http.cookiejar,json,pathlib,subprocess,time,urllib.request,urllib.error,uuid
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
child=json.loads((ROOT/'bundle/review-admission.workflow.json').read_text())
assert child['active'] is False
assert "const trusted_mode='dry_run'" in next(n for n in child['nodes'] if n['name']=='Validate fixed review candidate')['parameters']['jsCode']
ID='onticardsReviewReadOnlyProbeV1'
def n(name,kind,parameters,version=1,**extras):return {'id':str(uuid.uuid5(uuid.NAMESPACE_URL,ID+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[0,0],'parameters':parameters,**extras}
fixture={'id':ID,'name':'OntiCards fixed native MCP read only probe','active':False,'nodes':[
 n('Authenticated probe','webhook',{'httpMethod':'POST','path':'onticards-review-readonly-probe-v1','authentication':'headerAuth','responseMode':'lastNode','options':{}},2.1,credentials={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}},webhookId='onticards-review-readonly-probe-v1'),
 n('Fixed historical identity only','code',{'jsCode':"return [{json:{pr:26,head:'3105b7b61469c6b2945357f2eefa8fcb2e3aaee5',base:'c8e3dfee68d398a37842fc332f73af40a56f02a7',observed_at:new Date().toISOString()}}];"},2),
 n('Existing native review child','executeWorkflow',{'workflowId':{'__rl':True,'value':child['id'],'mode':'id'},'mode':'each','options':{'waitForSubWorkflow':True}},1.3)],
 'connections':{'Authenticated probe':{'main':[[{'node':'Fixed historical identity only','type':'main','index':0}]]},'Fixed historical identity only':{'main':[[{'node':'Existing native review child','type':'main','index':0}]]}},
 'settings':{'executionOrder':'v1','executionTimeout':300,'saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False},'pinData':{}}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
 with opener.open(req,timeout=30) as response:
  value=json.loads(response.read());return value.get('data',value)
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
temporary=ROOT/'state/review-probe-import.json';temporary.write_text(json.dumps([child,fixture]));temporary.chmod(0o644)
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError('Native import failed; raw output withheld')
try:
 run(['docker','cp',str(temporary),'onticards-preview-ci:/tmp/review-probe-import.json'])
 run(['docker','exec','onticards-preview-ci','n8n','import:workflow','--input=/tmp/review-probe-import.json'])
finally:
 run(['docker','exec','-u','root','onticards-preview-ci','rm','-f','/tmp/review-probe-import.json']);temporary.unlink(missing_ok=True)
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_schedule_triggers':0,'automatic_review_enabled':False,'models':0,'github_writes':0,'workflows':[]}
for w in [child,fixture]:
 current=api('workflows/'+w['id']);active=api('workflows/'+w['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 assert active['active'] is True
 record['workflows'].append({'id':w['id'],'version':active.get('activeVersionId'),'nodes':len(w['nodes'])})
time.sleep(2)
try:
 header=json.loads((ROOT/'secrets/trigger.json').read_text())
 request=urllib.request.Request('http://127.0.0.1:18132/webhook/onticards-review-readonly-probe-v1',data=b'{}',headers={header['name']:header['value'],'Content-Type':'application/json'},method='POST')
 with opener.open(request,timeout=300) as response:result=json.loads(response.read())
 if isinstance(result,list):result=result[0]
 record['result']=result
 detail=json.loads(result['detail'])
 record['passed']=result['state']=='native_review_entry_verified_no_dispatch' and detail['grant_revocation']=='revoked_verified' and detail['model_started'] is False
finally:
 api('workflows/'+ID+'/deactivate',{})
 record['probe_deactivated']=True
 (ROOT/'state/review-native-n8n-probe.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
assert record.get('passed') is True
