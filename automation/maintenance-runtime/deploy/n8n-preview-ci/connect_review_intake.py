"""Append one native dry-run Execute Workflow branch to the current CI receiver.
Preserve all existing nodes and connections, including batch-budget fixes.
"""
import datetime,http.cookiejar,json,pathlib,sqlite3,urllib.request,uuid
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None,method=None):
 r=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(r,timeout=30) as response:
  d=json.loads(response.read());return d.get('data',d)
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
ids=['onticardsReviewAdmissionV1','onticardsPreviewIntakeV1']
db=sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True)
assert db.execute("select count(*) from execution_entity where deletedAt is null and status in ('new','running','waiting') and workflowId in (?,?)",ids).fetchone()[0]==0
db.close()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup=ROOT/'state'/('review-connection-before-'+stamp);backup.mkdir(mode=0o700)
def update(old,w):
 (backup/(w['id']+'.json')).write_text(json.dumps(old));(backup/(w['id']+'.json')).chmod(0o600)
 if old['active']:api('workflows/'+w['id']+'/deactivate',{})
 cur=api('workflows/'+w['id'])
 api('workflows/'+w['id'],{'name':w['name'],'nodes':w['nodes'],'connections':w['connections'],'settings':w['settings'],'versionId':cur['versionId']},'PATCH')
 cur=api('workflows/'+w['id']);assert cur['nodes']==w['nodes'] and cur['connections']==w['connections']
 api('workflows/'+w['id']+'/activate',{'versionId':cur['versionId'],'expectedChecksum':cur['checksum']})
 return {'id':w['id'],'version':cur['versionId'],'nodes':len(w['nodes'])}
child=json.loads((ROOT/'bundle/review-admission.workflow.json').read_text())
assert child['active'] is False and "const trusted_mode='dry_run'" in next(n for n in child['nodes'] if n['name']=='Validate fixed review candidate')['parameters']['jsCode']
record={'at':stamp,'mode':'dry_run','model_calls':0,'new_schedules':0,'workflows':[]}
record['workflows'].append(update(api('workflows/'+child['id']),child))
old=api('workflows/onticardsPreviewIntakeV1');receiver=json.loads(json.dumps(old))
name='Native semantic review admission'
assert not any(n['name']==name for n in receiver['nodes']), 'Already connected; do not overwrite'
assert any(n['name']=='Read one native balance per complete batch' for n in receiver['nodes'])
receiver['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,receiver['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.executeWorkflow','typeVersion':1.3,'position':[800,600],'parameters':{'workflowId':{'__rl':True,'value':child['id'],'mode':'id'},'mode':'each','options':{'waitForSubWorkflow':True}},'onError':'continueRegularOutput','retryOnFail':False})
branch=receiver['connections']['Validate complete existing snapshot']['main'][0]
branch.append({'node':name,'type':'main','index':0})
assert receiver['nodes'][:-1]==old['nodes']
record['workflows'].append(update(old,receiver))
record['complete']=True
(ROOT/'state/review-intake-connection.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
