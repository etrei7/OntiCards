"""Native checksum update of intake only; preserve ledgers and scheduled entry."""
import hashlib,http.cookiejar,json,sqlite3,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n');wid='onticardsPersistentReadOnlyV1'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(q,timeout=30)as r:return json.loads(r.read())['data']
owner=json.loads((root/'persistent/secrets/owner.json').read_text());req('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
record={'started_at':datetime.now(timezone.utc).isoformat(),'manual_poll_triggers':0,'model_requests':0,'github_requests':0,'ledger_writes':0}
previous=req('workflows/'+wid);backup=root/'evidence'/('intake-before-completeness-'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json');backup.write_text(json.dumps(previous,ensure_ascii=False,indent=2));backup.chmod(0o600)
req('workflows/'+wid+'/deactivate',{})
for _ in range(120):
 db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True)
 count=db.execute("select count(*) from execution_entity where workflowId=?and deletedAt is null and status in ('new','running','waiting')",(wid,)).fetchone()[0];db.close()
 if count==0:break
 time.sleep(3)
else:raise RuntimeError('Intake paused but prior execution still active; no replacement applied')
w=json.loads((root/'persistent-readonly-serial.workflow.json').read_text());assert w['id']==wid and len(w['nodes'])==59
assert 'since='not in next(n for n in w['nodes']if n['name']=='Prepare List all Issue and PR records')['parameters']['jsonOutput']
current=req('workflows/'+wid);payload={k:w[k]for k in ['name','nodes','connections','settings']};payload.update(versionId=current['versionId'],expectedChecksum=current['checksum'])
updated=req('workflows/'+wid,payload,'PATCH');req('workflows/'+wid+'/activate',{'versionId':updated['versionId'],'expectedChecksum':updated['checksum']});actual=req('workflows/'+wid)
assert actual['active']and len(actual['nodes'])==59
record.update(completed_at=datetime.now(timezone.utc).isoformat(),active=actual['active'],nodes=len(actual['nodes']),version_id=actual['versionId'],checksum=actual['checksum'],source_sha256=hashlib.sha256((root/'persistent-readonly-serial.workflow.json').read_bytes()).hexdigest(),prior_backup=str(backup))
(root/'evidence/intake-completeness-deployment.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
