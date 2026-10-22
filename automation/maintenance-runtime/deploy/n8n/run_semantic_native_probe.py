"""Run the full native review graph with frozen source/model responses only."""
import json,sqlite3,subprocess,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native semantic fixture management failed; raw output excluded')
record={'started_at':datetime.now(timezone.utc).isoformat(),'github_requests':0,'model_requests':0,'requests':[]}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 run(['docker','start',name]);run(['docker','cp',str(root/'semantic-native-probe.workflow.json'),name+':/tmp/semantic-native-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/semantic-native-probe.json']);run(['docker','exec',name,'n8n','publish:workflow','--id=onticardsSemanticNativeProbeV1']);run(['docker','restart',name])
 for _ in range(120):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:break
  except OSError:pass
  time.sleep(1)
 for case in ['approve','approve','bad_quote','runtime_confusion','known_field_conflict','invalid_json','budget_six','manual31','changed_source','issue29_initial','issue29_initial','issue29_followup','issue29_followup']:
  for _ in range(25):
   try:
    q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-semantic-native-probe-v1',data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(q,timeout=75)as r:response=json.loads(r.read())
    break
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Fixture webhook registration unavailable')
  record['requests'].append({'case':case,'response':response})
 expected=json.loads((root/'semantic-native-probe-cases.json').read_text())
 db=sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;rows=[]
 for t in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user_%'"):rows.extend(dict(r)for r in db.execute('select * from "'+t[0]+'"'))
 db.close()
 reviews={case:next((r for r in rows if r.get('event_key')==v['event_key']and'reserved_model_ordinal'in r),None)for case,v in expected.items()}
 conversations={case:next((r for r in rows if r.get('thread_key')==v['thread_key']and'model_calls'in r),None)for case,v in expected.items()}
 approvals={case:[r for r in rows if r.get('event_key')==v['event_key']and'approval'in r]for case,v in expected.items()}
 record['review_statuses']={k:v['status']if v else None for k,v in reviews.items()};record['budgets']={k:v['model_calls']if v else None for k,v in conversations.items()}
 record['assertions']={
  'approved_once_with_one_review_budget':reviews['approve']['status']=='semantic_approved'and conversations['approve']['model_calls']==2 and len(approvals['approve'])==1,
  'duplicate_review_no_new_reservation':record['requests'][1]['response']['result']['status']=='semantic_review_disabled_or_no_eligible_candidate',
  'bad_source_quote_requires_human':reviews['bad_quote']['status']=='needs_human_review'and not approvals['bad_quote'],
  'runtime_confusion_requires_human':reviews['runtime_confusion']['status']=='needs_human_review'and not approvals['runtime_confusion'],
  'known_field_conflict_requires_human':reviews['known_field_conflict']['status']=='needs_human_review'and not approvals['known_field_conflict'],
  'invalid_json_consumes_once_no_approval':reviews['invalid_json']['status']=='needs_human_review'and conversations['invalid_json']['model_calls']==2 and not approvals['invalid_json'],
  'budget_six_never_reviewed':reviews['budget_six']is None and conversations['budget_six']['model_calls']==6,
  'sealed_issue31_never_reviewed':reviews['manual31']is None and conversations['manual31']['model_calls']==3,
  'source_change_blocks_before_budget':reviews['changed_source']['status']=='needs_human_review' and reviews['changed_source']['reserved_model_ordinal']==0 and conversations['changed_source']['model_calls']==1,
  'issue29_initial_prior_text_compatible':reviews['issue29_initial']['status']=='semantic_approved'and len(approvals['issue29_initial'])==1,
  'issue29_followup_prior_text_compatible':reviews['issue29_followup']['status']=='semantic_approved'and len(approvals['issue29_followup'])==1,
  'issue29_duplicates_no_new_budget':conversations['issue29_initial']['model_calls']==2 and conversations['issue29_followup']['model_calls']==2,
 }
 record['passed']=all(record['assertions'].values());record['semantic_quality_claim']='No new model call; frozen fixture reviewer decisions test gate/state compatibility, not general model accuracy.'
finally:
 run(['docker','stop',name]);record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence/semantic-native-budget6-probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in record.items()if k!='requests'},ensure_ascii=False))
