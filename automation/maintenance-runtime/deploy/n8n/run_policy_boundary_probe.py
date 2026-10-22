"""Native safe diagnostics and automatic approval selection; no model/GitHub calls."""
import json,subprocess,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native boundary fixture management failed; raw output excluded')
record={'started_at':datetime.now(timezone.utc).isoformat(),'github_requests':0,'model_requests':0,'results':{}}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'policy-boundary-probe.workflow.json'),name+':/tmp/policy-boundary-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/policy-boundary-probe.json'])
 for wid in ['onticardsSafeResponseProbeV1','onticardsAutomaticSelectionProbeV1']:run(['docker','exec',name,'n8n','publish:workflow','--id='+wid])
 run(['docker','restart',name])
 for _ in range(120):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 for path,cases in [('safe-response',['normal','redaction','http_error','timeout','bounded']),('automatic-selection',['published_issue29','one_pending','unknown_and_new','untrusted_policy'])]:
  for case in cases:
   for _ in range(25):
    try:
     q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-'+path+'-probe-v1',data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
     with opener.open(q,timeout=45)as r:response=json.loads(r.read())
     break
    except urllib.error.HTTPError as e:
     if e.code!=404:raise
     time.sleep(1)
   else:raise RuntimeError('Native fixture route unavailable')
   record['results'][case]=response
 x=record['results'];raw=json.dumps({k:x[k]for k in ['normal','redaction','http_error','timeout','bounded']})
 record['assertions']={
  'normal_assistant_body_retained':x['normal']['body_excerpt']=='synthetic safe content',
  'known_token_shapes_redacted':'FIXTURE_SECRET'not in raw and 'FIXTURESECRET'not in raw,
  'request_headers_never_retained':all('headers'not in r and'error'not in r for k,r in x.items()),
  'http_status_and_category_retained':x['http_error']['http_status']==401 and x['http_error']['category']=='http_error'and not x['http_error']['body_excerpt'],
  'timeout_category_retained':x['timeout']['category']=='timeout',
  'assistant_body_bounded':len(x['bounded']['body_excerpt'])==16384 and x['bounded']['body_truncated']is True,
  'both_published_issue29_replies_not_selected':x['published_issue29']['event_key']is None,
  'one_pending_approval_selected':x['one_pending']['event_key']=='pending',
  'unknown_reconciliation_does_not_starve_older_pending':x['unknown_and_new']['event_key']=='new',
  'untrusted_approval_origin_not_selected':x['untrusted_policy']['event_key']is None}
 record['passed']=all(record['assertions'].values())
finally:
 run(['docker','stop',name]);record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence/policy-boundary-native-probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in record.items()if k!='results'},ensure_ascii=False))
