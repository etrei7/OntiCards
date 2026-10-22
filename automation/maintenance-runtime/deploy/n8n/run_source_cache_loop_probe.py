"""Run native cache mixed-branch red/green without a model or external GET."""
import json,subprocess,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native cache fixture management failed; raw output excluded')
record={'started_at':datetime.now(timezone.utc).isoformat(),'model_requests':0,'github_requests':0,'cases':{}}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'source-cache-loop-probe.workflow.json'),name+':/tmp/source-cache-loop-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/source-cache-loop-probe.json'])
 for wid in ['onticardsSourceCacheRedProbe','onticardsSourceCacheGreenProbe']:run(['docker','exec',name,'n8n','publish:workflow','--id='+wid])
 run(['docker','restart',name])
 for _ in range(90):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 for mode,case in [('red','mixed'),('green','cached'),('green','fresh'),('green','mixed'),('green','bad_hash')]:
  for _ in range(25):
   try:
    q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-source-cache-'+mode,data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(q,timeout=55)as r:record['cases'][mode+'_'+case]=json.loads(r.read())
    break
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Cache fixture route unavailable')
 c=record['cases'];record['assertions']={'original_mixed_branch_reproduces_incomplete':c['red_mixed']['complete']is False and c['red_mixed']['count']<c['red_mixed']['expected'],'all_cache_verified':c['green_cached']['complete']is True,'all_fresh_verified':c['green_fresh']['complete']is True,'mixed_cache_collected_once':c['green_mixed']['complete']is True and c['green_mixed']['count']==2,'bad_hash_still_rejected':c['green_bad_hash']['complete']is False}
 record['passed']=all(record['assertions'].values())
finally:
 run(['docker','stop',name]);record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence/source-cache-loop-native-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
