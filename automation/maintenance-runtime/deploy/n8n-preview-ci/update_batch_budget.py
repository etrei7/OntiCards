"""Update only existing CI receiver/admission with reviewed native batch observation."""
import datetime,hashlib,http.cookiejar,json,pathlib,sqlite3,urllib.request
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
proof=json.loads(pathlib.Path('/opt/onticards-maintenance/n8n/evidence/intake-lifecycle-ci-native-probe.json').read_text())
required=['six_pr_items_read_balance_once_and_bind_all','consumed_batch_performs_no_balance_login','dry_run_batch_performs_no_balance_login','stale_batch_observation_rejected','cross_batch_observation_rejected']
assert proof['passed'] and all(proof['assertions'].get(x)is True for x in required)
files=['intake-admission.workflow.json','intake-receiver.workflow.json']
candidate=[json.loads((ROOT/'bundle'/x).read_text())for x in files]
assert [x['id']for x in candidate]==['onticardsPreviewAdmissionV1','onticardsPreviewIntakeV1']
assert not any(n['type'].endswith('executeCommand')for n in candidate[0]['nodes'])
assert len([n for n in candidate[1]['nodes']if n['type'].endswith('executeCommand')])==1
assert all(x['active']is False for x in candidate)
connection=sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True)
assert connection.execute("select count(*)from execution_entity where deletedAt is null and status in ('new','running','waiting') and workflowId in (?,?)",tuple(x['id']for x in candidate)).fetchone()[0]==0,'Existing target execution active; no update'
connection.close()
o=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with o.open(q,timeout=30)as r:d=json.loads(r.read());return d.get('data',d)
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup=ROOT/'state'/('batch-budget-before-'+stamp);backup.mkdir(mode=0o700)
record={'started_at':stamp,'model_calls':0,'github_posts':0,'quota_reset':False,'credential_changes':False,'workflows':[],'native_fixture_assertions':{x:proof['assertions'][x]for x in required}}
for w,file in zip(candidate,files):
 old=api('workflows/'+w['id']);assert old['active'] is True
 assert len(old['nodes'])==({'onticardsPreviewAdmissionV1':27,'onticardsPreviewIntakeV1':4}[w['id']]),'Unexpected existing definition; review before applying'
 (backup/(w['id']+'.json')).write_text(json.dumps(old));(backup/(w['id']+'.json')).chmod(0o600)
 api('workflows/'+w['id']+'/deactivate',{})
 current=api('workflows/'+w['id'])
 api('workflows/'+w['id'],{'name':w['name'],'nodes':w['nodes'],'connections':w['connections'],'settings':w['settings'],'versionId':current['versionId']},'PATCH')
 current=api('workflows/'+w['id']);assert current['nodes']==w['nodes']and current['connections']==w['connections']
 api('workflows/'+w['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 actual=api('workflows/'+w['id']);assert actual['active']is True and actual['activeVersionId']==current['versionId']
 record['workflows'].append({'id':w['id'],'version':current['versionId'],'nodes':len(w['nodes']),'template_sha256':hashlib.sha256((ROOT/'bundle'/file).read_bytes()).hexdigest(),'active':True})
record['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(ROOT/'state/batch-budget-deployment.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
