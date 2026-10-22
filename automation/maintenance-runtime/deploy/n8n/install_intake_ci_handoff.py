"""Native credential/workflow import; no manual intake/model/build invocation."""
import hashlib,http.cookiejar,json,os,sqlite3,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n');name='onticards-maintenance-triage'
record={'started_at':datetime.now(timezone.utc).isoformat(),'manual_poll_triggers':0,'models':0,'github_writes':0,'mode':'dry_run'}
def command(args):
 p=subprocess.run(args,capture_output=True,timeout=90)
 if p.returncode:raise RuntimeError('Native credential import failed; raw output excluded')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 try:
  with opener.open(q,timeout=30)as r:return json.loads(r.read())['data']
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise RuntimeError('Native management HTTP '+str(e.code))from None
owner=json.loads((root/'persistent/secrets/owner.json').read_text());req('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
wid='onticardsPersistentReadOnlyV1';old=req('workflows/'+wid)
assert old and old['active'] and len(old['nodes'])==59,'Require unmodified current 59-node intake before first handoff installation'
expected=json.loads((root/'persistent-readonly-serial.workflow.json').read_text())
assert old['nodes']==expected['nodes']and old['connections']==expected['connections'],'Intake changed since reviewed candidate'
backup=root/'evidence'/('intake-before-ci-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json');backup.write_text(json.dumps(old));backup.chmod(0o600)
req('workflows/'+wid+'/deactivate',{})
for _ in range(120):
 db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True)
 running=db.execute("select count(*)from execution_entity where workflowId=?and deletedAt is null and status in ('new','running','waiting')",(wid,)).fetchone()[0];db.close()
 if not running:break
 time.sleep(3)
else:raise RuntimeError('Prior intake still running; inactive workflow preserved for inspection')
credential=json.loads(Path('/opt/onticards-maintenance/preview-ci/secrets/trigger.json').read_text());assert set(credential)=={'name','value'}
tmp=root/'persistent/secrets/ci-header-import.temporary.json'
fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w')as f:json.dump([{'id':'onticardsPreviewIntakeHeader','name':'OntiCards existing trusted CI intake only','type':'httpHeaderAuth','data':credential}],f)
credential.clear();os.chown(tmp,1000,1000)
try:
 command(['docker','cp','-a',str(tmp),name+':/tmp/onticards-ci-header-import.json']);command(['docker','exec',name,'n8n','import:credentials','--input=/tmp/onticards-ci-header-import.json'])
finally:
 command(['docker','exec','-u','root',name,'rm','-f','/tmp/onticards-ci-header-import.json']);tmp.unlink(missing_ok=True)
record['workflows']=[]
for filename in ['intake-ci-handoff.workflow.json','persistent-readonly-ci.workflow.json']:
 w=json.loads((root/filename).read_text());previous=req('workflows/'+w['id']);payload={k:w[k]for k in ['name','nodes','connections','settings']}
 if previous:
  assert not previous['active'];payload.update(versionId=previous['versionId'],expectedChecksum=previous['checksum']);updated=req('workflows/'+w['id'],payload,'PATCH')
 else:payload.update(id=w['id'],tags=[]);updated=req('workflows',payload,'POST')
 req('workflows/'+w['id']+'/activate',{'versionId':updated['versionId'],'expectedChecksum':updated['checksum']});actual=req('workflows/'+w['id']);assert actual['active']and actual['nodes']==w['nodes']and actual['connections']==w['connections']
 record['workflows'].append({'id':w['id'],'nodes':len(w['nodes']),'active':True,'version_id':actual['versionId'],'source_sha256':hashlib.sha256((root/filename).read_bytes()).hexdigest()})
record.update(completed_at=datetime.now(timezone.utc).isoformat(),backup=str(backup),credential_values_exported=False)
(root/'evidence/intake-ci-handoff-deployment.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
