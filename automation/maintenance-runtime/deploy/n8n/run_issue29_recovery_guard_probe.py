"""Native guard fixtures only, separate 18127 instance; never starts recovery."""
import json,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe';opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native guard fixture management failed; output excluded')
record={'started_at':datetime.now(timezone.utc).isoformat(),'model_calls':0,'github_posts':0,'ledger_writes':0,'cases':{}}
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'issue29-recovery-guard-probe.workflow.json'),name+':/tmp/issue29-recovery-guard-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/issue29-recovery-guard-probe.json']);run(['docker','exec',name,'n8n','publish:workflow','--id=onticardsIssue29RecoveryGuardProbe']);run(['docker','restart',name])
 for _ in range(60):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 cases=['valid','duplicate_intent','budget5','reply3','app3','ai_label','changed_human','changed_original_hash','review_not_failed','stale','wrong_human_id','posting_unknown','unknown_response_consumed','changed_commit','incomplete_source','revoke_unknown']
 for c in cases:
  for _ in range(25):
   try:
    q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-issue29-recovery-guard-probe',data=json.dumps({'case':c}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(q,timeout=50)as r:record['cases'][c]=json.loads(r.read())
    break
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Native guard route unavailable')
  r=record['cases'][c];expected=c=='valid';r['passed']=(r['eligible']and r['source_complete'])==expected and r['projected_budget']==5 and r['model_calls']==0
 record['passed']=all(x['passed']for x in record['cases'].values());record['checks']=len(cases)
 record['limitations']='Actual native Set guards and projected budget only; state persistence/concurrency covered by prior native DataTable budget fixtures and independent recovery graph review, not claimed here.'
finally:
 run(['docker','stop',name]);record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence/issue29-recovery-guard-native-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
