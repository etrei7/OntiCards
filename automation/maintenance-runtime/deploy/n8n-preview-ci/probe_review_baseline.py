"""Actual native n8n baseline/deduplication fixture; isolated table, no SSH/model.
Run on the trusted test host. Uses existing owner/header credentials in memory.
"""
import copy,datetime,hashlib,http.cookiejar,json,pathlib,subprocess,time,urllib.request,uuid
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
CHILD='onticardsReviewBaselineFixtureV1';PARENT='onticardsReviewBaselineProbeV1';TABLE='onticards_review_baseline_fixture_v1'
source=json.loads((ROOT/'bundle/review-admission.workflow.json').read_text())
child=copy.deepcopy(source);child.update(id=CHILD,name='OntiCards isolated native review baseline fixture',active=False)
for n in child['nodes']:
 n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,CHILD+'/'+n['name']))
 if n['name']=='Validate fixed review candidate':n['parameters']['jsCode']=n['parameters']['jsCode'].replace("const trusted_mode='dry_run'","const trusted_mode='baseline'")
 if n['type']=='n8n-nodes-base.dataTable':
  if 'tableName' in n['parameters']:n['parameters']['tableName']=TABLE
  if 'dataTableId' in n['parameters']:n['parameters']['dataTableId']['value']=TABLE
 if n['name']=='Native fixed SSH review capability':
  n.update(type='n8n-nodes-base.code',typeVersion=2,parameters={'jsCode':"throw new Error('Baseline must never invoke SSH');"})
versions=[{'pr':900001+i,'head':format(i+1,'040x'),'base':'b'*40,'observed_at':'2026-10-22T00:00:00Z'} for i in range(6)]
def node(name,kind,p,version=1,**extras):return {'id':str(uuid.uuid5(uuid.NAMESPACE_URL,PARENT+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[0,0],'parameters':p,**extras}
parent={'id':PARENT,'name':'OntiCards isolated six-item baseline probe','active':False,'nodes':[
 node('Authenticated probe','webhook',{'httpMethod':'POST','path':'onticards-review-baseline-probe-v1','authentication':'headerAuth','responseMode':'lastNode','options':{}},2.1,credentials={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}},webhookId='onticards-review-baseline-probe-v1'),
 node('Six synthetic versions','code',{'jsCode':'return '+json.dumps([{'json':v} for v in versions])+';'},2),
 node('Native baseline child','executeWorkflow',{'workflowId':{'__rl':True,'value':CHILD,'mode':'id'},'mode':'each','options':{'waitForSubWorkflow':True}},1.3),
 node('Collect all baseline receipts','code',{'jsCode':'return [{json:{versions:$input.all().map(x=>x.json)}}];'},2)],'connections':{},'settings':source['settings'],'pinData':{}}
for a,b in zip(parent['nodes'],parent['nodes'][1:]):parent['connections'][a['name']]={'main':[[{'node':b['name'],'type':'main','index':0}]]}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
 with opener.open(req,timeout=30) as response:
  d=json.loads(response.read());return d.get('data',d)
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError('Native fixture import failed; raw output withheld')
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
temp=ROOT/'state/review-baseline-import.json';temp.write_text(json.dumps([child,parent]));temp.chmod(0o644)
try:
 run(['docker','cp',str(temp),'onticards-preview-ci:/tmp/review-baseline-import.json'])
 run(['docker','exec','onticards-preview-ci','n8n','import:workflow','--input=/tmp/review-baseline-import.json'])
finally:
 run(['docker','exec','-u','root','onticards-preview-ci','rm','-f','/tmp/review-baseline-import.json']);temp.unlink(missing_ok=True)
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hashlib.sha256((ROOT/'bundle/review-admission.workflow.json').read_bytes()).hexdigest(),'fixture_table':TABLE,'synthetic':True,'ssh_calls':0,'models':0,'github_writes':0,'assertions':[]}
try:
 for w in [child,parent]:
  current=api('workflows/'+w['id']);assert current['nodes']==w['nodes'] and current['connections']==w['connections']
  api('workflows/'+w['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 time.sleep(2)
 header=json.loads((ROOT/'secrets/trigger.json').read_text())
 for iteration in range(2):
  req=urllib.request.Request('http://127.0.0.1:18132/webhook/onticards-review-baseline-probe-v1',data=b'{}',headers={header['name']:header['value'],'Content-Type':'application/json'},method='POST')
  with opener.open(req,timeout=120) as response:value=json.loads(response.read())
  if isinstance(value,list):assert len(value)==1;value=value[0]
  assert set(value)=={'versions'} and len(value['versions'])==6
  for expected,result in zip(versions,value['versions']):
   assert all(result[k]==expected[k] for k in ['pr','head','base'])
   assert result['state']==('baseline' if iteration==0 else 'already_consumed')
   if iteration==1:assert result['prior_states']==['baseline'] and result['automatic_retry'] is False
   record['assertions'].append({'iteration':iteration+1,'pr':expected['pr'],'state':result['state'],'passed':True})
 record['passed']=True
finally:
 for wid in [PARENT,CHILD]:
  try:api('workflows/'+wid+'/deactivate',{})
  except Exception:record['deactivation_unknown']=True
 (ROOT/'state/review-baseline-native-probe.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record));assert record.get('passed') and not record.get('deactivation_unknown')
