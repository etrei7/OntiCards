"""Full native graph fixture; actual HTTP POSTs address localhost transport only."""
import json,sqlite3,subprocess,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native publication fixture management failed; raw output excluded')
record={'started_at':datetime.now(timezone.utc).isoformat(),'github_requests':0,'model_requests':0,'requests':[]}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'publication-native-probe.workflow.json'),name+':/tmp/publication-native-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/publication-native-probe.json'])
 for wid in ['onticardsPublicationTransportProbeV1','onticardsPublicationNativeProbeV1']:run(['docker','exec',name,'n8n','publish:workflow','--id='+wid])
 run(['docker','restart',name])
 for _ in range(120):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 cases=[('success','normal'),('success','recover'),('unknown_absent','normal'),('unknown_absent','read_failure'),('unknown_absent','recover'),('unknown_found','normal'),('unknown_found','read_failure'),('unknown_found','recover'),('changed_source','normal'),('cap','normal'),('bad_asked','normal'),('ai_takeover','normal'),('ai_takeover','recover'),('unknown_ai','normal'),('unknown_ai','ai_added')]
 for case,stage in cases:
  for attempt in range(25):
   try:
    q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-pub-native-probe-v1',data=json.dumps({'case':case,'stage':stage}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(q,timeout=75)as r:response=json.loads(r.read())
    break
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Fixture webhook registration unavailable')
  record['requests'].append({'case':case,'stage':stage,'response':response})
 expected=json.loads((root/'publication-native-probe-cases.json').read_text())
 db=sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 rows=[]
 for t in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user_%'"):rows.extend(dict(r)for r in db.execute('select * from "'+t[0]+'"'))
 db.close()
 posts={r['case_key'].removeprefix('v2:'):r['post_count']for r in rows if'case_key'in r and'post_count'in r and r['case_key'].startswith('v2:')};record['localhost_posts']=posts
 ledger={case:next((r for r in rows if r.get('event_key')==v['event_key']and'comment_id'in r),{})for case,v in expected.items()}
 record['ledger']={k:{p:r.get(p)for p in ['status','comment_id','should_post','reason']}for k,r in ledger.items()}
 conversation=next((r for r in rows if r.get('thread_key')==expected['success']['thread_key']and'model_calls'in r),{})
 record['assertions']={'success_one_post':posts.get('success')==1,'unknown_absent_one_post':posts.get('unknown_absent')==1,'unknown_absent_sticky':ledger['unknown_absent'].get('status')=='posting_unknown','unknown_found_one_post':posts.get('unknown_found')==1,'unknown_found_reconciled':ledger['unknown_found'].get('status')=='published_reconciled','changed_source_zero_posts':posts.get('changed_source',0)==0,'cap_zero_posts':posts.get('cap',0)==0,'invalid_asked_fields_zero_posts':posts.get('bad_asked',0)==0,'reviewed_asked_fields_only':json.loads(conversation.get('asked_fields','[]'))==['deployment_method'],'ai_takeover_zero_posts':posts.get('ai_takeover',0)==0 and ledger['ai_takeover'].get('status')=='native_repair_route','unknown_then_ai_preserves_sticky':posts.get('unknown_ai')==1 and ledger['unknown_ai'].get('status')=='posting_unknown','model_budget_preserved':conversation.get('model_calls')==1,'conversation_increment_once':len(json.loads(conversation.get('publication_ids','[]')))==1}
 record['passed']=all(record['assertions'].values())
finally:
 run(['docker','stop',name]);record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence/publication-native-ai-gate-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
