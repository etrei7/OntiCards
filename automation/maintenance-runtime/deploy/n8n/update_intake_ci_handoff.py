"""Checksum update of the existing CI child only; preserve mode and parent."""
import argparse,hashlib,http.cookiejar,json,sqlite3,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');wid='onticardsIntakeCiHandoffV1'
parser=argparse.ArgumentParser();parser.add_argument('--dispatch',action='store_true');args=parser.parse_args()
if args.dispatch:
 proof=json.loads((root/'evidence/intake-lifecycle-ci-native-probe.json').read_text())
 assert proof.get('passed')is True and proof.get('native_published_version',{}).get('definition_exact')is True
 assert proof['assertions']['ci_multiple_rows_project_and_post_exactly_once']and proof['assertions']['ci_over_twenty_rejected_without_truncation']
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(q,timeout=30)as r:return json.loads(r.read())['data']
owner=json.loads((root/'persistent/secrets/owner.json').read_text());req('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
old=req('workflows/'+wid);record={'started_at':datetime.now(timezone.utc).isoformat(),'workflow':wid,'before_execute_once':{n['name']:n.get('executeOnce',False)for n in old['nodes']},'models':0,'github_writes':0,'manual_poll_triggers':0}
req('workflows/'+wid+'/deactivate',{})
for _ in range(30):
 db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True);count=db.execute("select count(*)from execution_entity where workflowId=?and deletedAt is null and status in ('running','new','waiting')",(wid,)).fetchone()[0];db.close()
 if count==0:break
 time.sleep(2)
else:raise RuntimeError('Existing CI child still executing; no replacement applied')
w=json.loads((root/'intake-ci-handoff.workflow.json').read_text());cfg=next(n for n in old['nodes']if n['name']=='Trusted CI handoff configuration')['parameters']
policy=json.loads(cfg['jsonOutput'])
if args.dispatch:assert policy['mode']=='dry_run';policy['mode']='dispatch';cfg['jsonOutput']=json.dumps(policy)
next(n for n in w['nodes']if n['name']=='Trusted CI handoff configuration')['parameters']=cfg
current=req('workflows/'+wid);payload={k:w[k]for k in ['name','nodes','connections','settings']};payload.update(versionId=current['versionId'],expectedChecksum=current['checksum']);updated=req('workflows/'+wid,payload,'PATCH');req('workflows/'+wid+'/activate',{'versionId':updated['versionId'],'expectedChecksum':updated['checksum']});actual=req('workflows/'+wid);assert actual['nodes']==w['nodes']
record.update(completed_at=datetime.now(timezone.utc).isoformat(),active=actual['active'],version_id=actual['versionId'],trusted_mode=policy['mode'],source_sha256=hashlib.sha256((root/'intake-ci-handoff.workflow.json').read_bytes()).hexdigest(),after_execute_once={n['name']:n.get('executeOnce',False)for n in actual['nodes']})
(root/'evidence'/('intake-ci-dispatch-enabled.json'if args.dispatch else'intake-ci-fanout-fix-deployment.json')).write_text(json.dumps(record,indent=2));print(json.dumps(record))
