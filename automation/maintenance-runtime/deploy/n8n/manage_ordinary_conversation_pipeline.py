"""Native owner API installation/activation for the reviewed ordinary pipeline.

Uses existing owner and encrypted n8n credentials. No credential creation, SQL
writes, webhook execution, direct model requests or GitHub API requests.
"""
import argparse,hashlib,http.cookiejar,json,sqlite3,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n')
arg=argparse.ArgumentParser();arg.add_argument('--enable',action='store_true');args=arg.parse_args()
spec=[('persistent-publication.workflow.json','Trusted publication policy'),('persistent-semantic-review.workflow.json','Trusted semantic policy'),('persistent-drafts.workflow.json','Trusted routing configuration')]
stamp=datetime.now(timezone.utc);record={'started_at':stamp.isoformat(),'enabled':args.enable,'actions':[],'models_directly_invoked':0,'github_requests':0}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,body=None,method=None):
 req=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 try:
  with opener.open(req,timeout=30)as r:
   data=json.loads(r.read());return data.get('data',data)
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise RuntimeError('Native management API HTTP '+str(e.code))from None
owner=json.loads((root/'persistent/secrets/owner.json').read_text());request('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
sealed_workflow=request('workflows/onticardsIssue31ManualResumeV1')
assert sealed_workflow and not sealed_workflow['active'],'Issue31 manual workflow must remain inactive'
sealed_cfg=json.loads(next(n for n in sealed_workflow['nodes']if n['name']=='Trusted routing configuration')['parameters']['jsonOutput'])
assert sealed_cfg.get('manual_enabled')is False,'Issue31 manual model switch must remain false'
record['issue31_manual_workflow_inactive']=True
workflows=[]
for filename,policy in spec:
 w=json.loads((root/filename).read_text());n=next(n for n in w['nodes']if n['name']==policy);cfg=json.loads(n['parameters']['jsonOutput'])
 assert cfg['repository']=='stepll2026/OntiCards'
 if policy=='Trusted routing configuration':
  assert cfg['max_model_calls_per_thread']==6 and cfg['max_app_comments_per_thread']==3 and 31 in cfg['manual_handoff_threads']
  assert not cfg['model_enabled']and not cfg['scope_all_ordinary_events']
  cfg.update(model_enabled=args.enable,scope_all_ordinary_events=args.enable,admission_after=stamp.isoformat(),allowed_model_threads=[],allowed_model_event_keys=[])
 elif policy=='Trusted semantic policy':
  assert cfg['max_model_calls_per_thread']==6 and 31 in cfg['manual_handoff_threads'] and not cfg['review_enabled']
  cfg['review_enabled']=args.enable
 else:
  assert cfg['approval']is None and not cfg['publication_enabled']and not cfg['automatic_enabled']
  cfg.update(publication_enabled=args.enable,automatic_enabled=args.enable)
 n['parameters']['jsonOutput']=json.dumps(cfg,ensure_ascii=False)
 workflows.append((filename,w,cfg))
ids=[w['id']for _,w,_ in workflows]
conn=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
running=[dict(r)for r in conn.execute("select id,workflowId,status from execution_entity where deletedAt is null and status in ('new','running','waiting')")if r['workflowId']in ids]
assert not running,'Target workflow has unfinished native execution'
# Preserve sealed history; this command must not reset or amend it.
sealed=[]
for row in conn.execute("select name from sqlite_master where type='table'and name like 'data_table_user_%'"):
 cols={r[1]for r in conn.execute('pragma table_info("'+row['name']+'")')}
 if {'thread_key','model_calls','pending_state'}.issubset(cols):
  sealed.extend(dict(r)for r in conn.execute('select thread_key,model_calls,pending_event,pending_state from "'+row['name']+'" where thread_key=?',('stepll2026/OntiCards#31',)))
conn.close();assert len(sealed)==1 and sealed[0]['model_calls']==3,'Issue31 budget sealing not verified';record['issue31_sealed_before']=sealed
backup=root/'evidence'/('ordinary-pipeline-backup-'+stamp.strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(mode=0o700)
for filename,w,cfg in workflows:
 previous=request('workflows/'+w['id'])
 if previous:
  (backup/(w['id']+'.json')).write_text(json.dumps(previous,ensure_ascii=False,indent=2))
  if previous.get('active'):request('workflows/'+w['id']+'/deactivate',{});previous=request('workflows/'+w['id'])
 payload={k:w[k]for k in ['name','nodes','connections','settings']}
 payload['name']=payload['name'].replace(' - disabled','')+(' - active ordinary scope'if args.enable else' - staged disabled')
 if previous:
  payload.update(versionId=previous['versionId'],expectedChecksum=previous['checksum']);updated=request('workflows/'+w['id'],payload,'PATCH')
 else:
  payload.update(id=w['id'],tags=[]);updated=request('workflows',payload,'POST')
 assert updated['id']==w['id']and not updated['active']
 if args.enable:updated=request('workflows/'+w['id']+'/activate',{'versionId':updated['versionId'],'expectedChecksum':updated['checksum']})
 actual=request('workflows/'+w['id']);assert actual['active']is args.enable
 actual_cfg=json.loads(next(n for n in actual['nodes']if n['name']in [policy for _,policy in spec])['parameters']['jsonOutput']);assert actual_cfg==cfg
 record['actions'].append({'id':w['id'],'active':actual['active'],'nodes':len(actual['nodes']),'version_id':actual['versionId'],'checksum':actual['checksum'],'source_sha256':hashlib.sha256((root/filename).read_bytes()).hexdigest(),'policy':{k:v for k,v in cfg.items()if k not in ['seed','facts_pdf']}})
record['completed_at']=datetime.now(timezone.utc).isoformat();out=root/'evidence'/('ordinary-pipeline-'+('enabled'if args.enable else'staged')+'.json');out.write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps(record,ensure_ascii=False))
