"""Update existing native Set/prompt gates, preserving runtime configuration and ledgers."""
import hashlib,http.cookiejar,json,sqlite3,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n')
targets=[('onticardsPersistentDraftsV1','persistent-drafts.workflow.json','Trusted routing configuration'),('onticardsPersistentSemanticReviewV1','persistent-semantic-review.workflow.json','Trusted semantic policy')]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(q,timeout=30)as r:return json.loads(r.read())['data']
owner=json.loads((root/'persistent/secrets/owner.json').read_text());req('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
record={'started_at':datetime.now(timezone.utc).isoformat(),'manual_triggers':0,'model_requests':0,'github_requests':0,'ledger_writes':0,'actions':[]}
for wid,filename,configuration in targets:
 for _ in range(100):
  db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True)
  count=db.execute("select count(*) from execution_entity where workflowId=? and deletedAt is null and status in ('new','running','waiting')",(wid,)).fetchone()[0];db.close()
  if count==0:break
  time.sleep(3)
 else:raise RuntimeError('Existing execution remains active; target not updated')
 previous=req('workflows/'+wid);assert previous['active']
 backup=root/'evidence'/('identity-before-'+wid+'-'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json');backup.write_text(json.dumps(previous,ensure_ascii=False,indent=2));backup.chmod(0o600)
 w=json.loads((root/filename).read_text());assert w['id']==wid
 old=next(n for n in previous['nodes']if n['name']==configuration)
 next(n for n in w['nodes']if n['name']==configuration)['parameters']=old['parameters']
 cfg=json.loads(old['parameters']['jsonOutput']);assert cfg['max_model_calls_per_thread']==6 and 31 in cfg['manual_handoff_threads']
 payload={k:w[k]for k in ['name','nodes','connections','settings']};payload.update(versionId=previous['versionId'],expectedChecksum=previous['checksum'])
 updated=req('workflows/'+wid,payload,'PATCH');req('workflows/'+wid+'/activate',{'versionId':updated['versionId'],'expectedChecksum':updated['checksum']});actual=req('workflows/'+wid)
 assert actual['active']and next(n for n in actual['nodes']if n['name']==configuration)['parameters']==old['parameters']
 record['actions'].append({'id':wid,'nodes':len(w['nodes']),'active':True,'configuration_preserved':True,'version_id':actual['versionId'],'checksum':actual['checksum'],'template_sha256':hashlib.sha256((root/filename).read_bytes()).hexdigest(),'prior_backup':str(backup)})
record['completed_at']=datetime.now(timezone.utc).isoformat();(root/'evidence/identity-gates-deployment.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
