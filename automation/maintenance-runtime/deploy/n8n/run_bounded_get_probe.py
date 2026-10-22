"""Run native n8n retry fixture in the existing separate server probe, then stop it."""
import json,sqlite3,subprocess,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe';dbpath=root/'server-probe-v2/database.sqlite'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native probe command failed; raw output excluded')
 return p.stdout
db=sqlite3.connect('file:'+str(dbpath)+'?mode=ro',uri=True)
assert not any(any(n['type'].endswith('scheduleTrigger')for n in json.loads(row[0]))for row in db.execute('select nodes from workflow_entity where active=1')),'Existing fixture has scheduled actions'
db.close()
record={'started_at':datetime.now(timezone.utc).isoformat(),'github_requests':0,'model_requests':0,'new_credentials':0,'cases':[]}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'bounded-get-probe.workflow.json'),name+':/tmp/bounded-get-probe.json'])
 run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/bounded-get-probe.json'])
 for wid in ['onticardsBoundedGetProbeChildV1','onticardsBoundedGetTransportV1','onticardsBoundedGetProbeV1']:run(['docker','exec',name,'n8n','publish:workflow','--id='+wid])
 run(['docker','restart',name])
 for _ in range(120):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 else:raise RuntimeError('Native probe readiness failed')
 stamp=datetime.now(timezone.utc).strftime('%H%M%S')
 for mode in ['recover503','empty200','always503','valid']:
  key='get-'+stamp+'-'+mode.lower();req=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-get-probe-v1',data=json.dumps({'mode':mode,'key':key}).encode(),headers={'Content-Type':'application/json'})
  for registration_wait in range(25):
   try:
    with opener.open(req,timeout=50)as r:result=json.loads(r.read())
    break
   except urllib.error.HTTPError as error:
    if error.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Native fixture webhook did not register')
  record['cases'].append({'key':key,'mode':mode,'result':result})
 db=sqlite3.connect('file:'+str(dbpath)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 for row in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user_%'"):
  table=row[0];cols=[r[1]for r in db.execute('pragma table_info("'+table+'")')]
  if 'case_mode'in cols and'request_count'in cols:
   counters=[dict(r)for r in db.execute('select * from "'+table+'"')]
   for case in record['cases']:case['native_request_count']=next(r['request_count']for r in counters if r['case_key']==case['key'])
 db.close()
 expected={'recover503':(True,2),'empty200':(True,2),'always503':(False,2),'valid':(True,1)}
 for case in record['cases']:
  complete,count=expected[case['mode']];assert case['result']['complete'] is complete and case['native_request_count']==count,case['mode']
 record['assertions_passed']=4
finally:
 run(['docker','stop',name]);record['probe_stopped']=True;record['completed_at']=datetime.now(timezone.utc).isoformat()
 (root/'evidence/bounded-get-native-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
