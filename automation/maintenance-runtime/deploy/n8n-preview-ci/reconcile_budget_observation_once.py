"""One approved native DataTable reconciliation; no CI, lease, quota or model execution."""
import copy, datetime, hashlib, http.cookiejar, json, pathlib, sqlite3, time, urllib.request, uuid

ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
ID='onticardsBudgetNativeProbeV1'
APPROVAL='onticards-root-review-pr30-pr33-budget-observation-20261023-v1'
old_evidence=json.loads((ROOT/'state/intake-dispatch-native-observation.json').read_text())
expected=[r for r in old_evidence['receipts'] if r['pr'] in (30,33)]
assert len(expected)==2 and all(r['state']=='budget_unverifiable' for r in expected)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None,method=None):
 request=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(request,timeout=60) as response:
  d=json.loads(response.read());return d.get('data',d)
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
old=api('workflows/'+ID);assert old['active'] is False
assert len(old['nodes'])==2 and old['nodes'][1]['parameters']['command']=='node /opt/onticards-preview-ci/bundle/budget_status.mjs'
backup=ROOT/'state/budget-native-probe.before-reconcile.json';backup.write_text(json.dumps(old));backup.chmod(0o600)
nodes=[copy.deepcopy(old['nodes'][0])];connections={}
def node(name,kind,parameters,version=2,**extra):
 nodes.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,APPROVAL+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'position':[len(nodes)*220,0],'parameters':parameters,**extra})
table={'__rl':True,'value':'onticards_ci_receipts_v1','mode':'name'}
node('Read actual existing receipts','dataTable',{'resource':'row','operation':'get','dataTableId':table,'returnAll':True},1.1)
guard='''const expected=EXPECTED;const rows=$('Read actual existing receipts').all().map(x=>x.json);const before=[];const instant=v=>Date.parse(v.includes('T')?v:v.replace(' ','T')+'Z');
for(const e of expected){const matches=rows.filter(r=>r.receipt_key===e.receipt_key);if(matches.length!==1)throw new Error('Exact prior receipt missing/duplicate');const r=matches[0];
if(r.pr!==e.pr||r.head!==e.head||r.base!==e.base||r.state!==e.state||r.detail!==e.detail||instant(r.updatedAt)!==instant(e.updatedAt))throw new Error('Prior receipt changed; review required');before.push(r);}
return [{json:{before}}];'''.replace('EXPECTED',json.dumps(expected))
node('Require exact two unchanged prior failures','code',{'jsCode':guard},executeOnce=True)
nodes.append(copy.deepcopy(old['nodes'][1]));nodes[-1]['position']=[len(nodes)*220,0]
prepare='''const p=$('Require exact two unchanged prior failures').first().json;let budget;try{budget=JSON.parse($input.first().json.stdout);}catch{throw new Error('No verified native observation');}
if(budget.state!=='budget_exhausted'||budget.required_quota!==45000||budget.remaining_quota!==15445||budget.token_creation_calls!==0||budget.provider_calls!==0||budget.account_quota_reset!==false||Date.now()-Date.parse(budget.checked_at)>60000||Date.parse(budget.checked_at)>Date.now()+5000)throw new Error('Approved observation condition changed');
return p.before.map(r=>{const detail=JSON.parse(r.detail);return {json:{receipt_key:r.receipt_key,pr:r.pr,head:r.head,base:r.base,state:'budget_exhausted',detail:JSON.stringify({...detail,original_receipt:{state:r.state,detail:r.detail,createdAt:r.createdAt,updatedAt:r.updatedAt},budget_reconciliation:{approval_id:'APPROVAL',actor:'AI maintenance operation under root task authorization; not a human UI click',at:new Date().toISOString(),observation:budget,ci_dispatch:false,model_calls:0,token_mint_calls:0,automatic_retry:false}})}}});'''.replace('APPROVAL',APPROVAL)
node('Append observation without overwriting original failure','code',{'jsCode':prepare},executeOnce=True)
node('Update only matching original admission rows','dataTable',{'resource':'row','operation':'update','dataTableId':table,'matchType':'allConditions','filters':{'conditions':[{'keyName':'receipt_key','condition':'eq','keyValue':'={{ $json.receipt_key }}'},{'keyName':'state','condition':'eq','keyValue':'budget_unverifiable'}]},'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
node('Return bounded verified reconciliation','code',{'jsCode':"const rows=$('Update only matching original admission rows').all().map(x=>x.json);if(rows.length!==2||!rows.every(r=>[30,33].includes(r.pr)&&r.state==='budget_exhausted'))throw new Error('Two exact native updates not confirmed');return [{json:{passed:true,before:$('Require exact two unchanged prior failures').first().json.before,after:rows,ci_dispatch:0,model_calls:0,token_mint_calls:0,quota_reset:false}}];"},executeOnce=True)
for a,b in zip(nodes,nodes[1:]):connections[a['name']]={'main':[[{'node':b['name'],'type':'main','index':0}]]}
settings=old['settings']|{'executionTimeout':90,'saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False}
record={'approval_id':APPROVAL,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_nodes':len(nodes),'original_receipt_source':'intake-dispatch-native-observation.json','original_receipt_sha256':hashlib.sha256((ROOT/'state/intake-dispatch-native-observation.json').read_bytes()).hexdigest()}
(ROOT/'state/budget-reconcile-reviewed.workflow.json').write_text(json.dumps({'id':ID,'active':False,'nodes':nodes,'connections':connections,'settings':settings},indent=2))
try:
 current=api('workflows/'+ID,{'name':old['name'],'nodes':nodes,'connections':connections,'settings':settings,'versionId':old['versionId']},'PATCH')
 current=api('workflows/'+ID);assert current['nodes']==nodes and current['connections']==connections
 active=api('workflows/'+ID+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']});assert active['active'] is True
 record['published_version']=current['versionId']
 for attempt in range(10):
  with sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True) as connection:
   hooks=connection.execute('select webhookPath,method from webhook_entity where workflowId=?',(ID,)).fetchall()
  if hooks:break
  time.sleep(0.5)
 record['registered_webhooks']=hooks
 assert hooks==[('onticards-budget-native-probe-v1','POST')], 'Native webhook registration not ready; no POST'
 credential=json.loads((ROOT/'secrets/trigger.json').read_text())
 request=urllib.request.Request('http://127.0.0.1:18132/webhook/onticards-budget-native-probe-v1',data=b'{}',headers={'Content-Type':'application/json',credential['name']:credential['value']})
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=90) as response:record['result']=json.loads(response.read())
 credential.clear()
 assert record['result']['passed'] is True
finally:
 current=api('workflows/'+ID)
 if current['active']:api('workflows/'+ID+'/deactivate',{})
 current=api('workflows/'+ID)
 api('workflows/'+ID,{'name':old['name'],'nodes':old['nodes'],'connections':old['connections'],'settings':old['settings'],'versionId':current['versionId']},'PATCH')
 restored=api('workflows/'+ID)
 record['original_read_only_probe_restored_inactive']=restored['active'] is False and restored['nodes']==old['nodes'] and restored['connections']==old['connections']
 record['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (ROOT/'state/budget-native-reconciliation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':record.get('result',{}).get('passed',False),'restored_inactive':record['original_read_only_probe_restored_inactive'],'ci_dispatch':0,'model_calls':0,'token_mint_calls':0}))
