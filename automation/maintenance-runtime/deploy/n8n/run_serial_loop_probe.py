"""Run exact loop/aggregation graph on the existing native localhost fixture."""
import hashlib,json,sqlite3,subprocess,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native fixture command failed; raw output excluded')
 return p.stdout
record={'started_at':datetime.now(timezone.utc).isoformat(),'github_requests':0,'model_requests':0,'cases':{}}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def native_ready():
 started=json.loads(run(['docker','inspect',name]))[0]['State']['StartedAt']
 for _ in range(120):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as response:
    logs=run(['docker','logs','--since',started,name])
    if response.status==200 and 'Editor is now accessible'in logs and 'Finished building workflow dependency index'in logs:return
  except OSError:pass
  time.sleep(1)
 raise RuntimeError('Native fixture has not finished startup; no import/request attempted')
try:
 run(['docker','start',name]);native_ready()
 if '--existing-published' not in sys.argv:
  run(['docker','cp',str(root/'serial-loop-probe.workflow.json'),name+':/tmp/serial-loop-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/serial-loop-probe.json'])
 db=sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True);version=db.execute('select versionId from workflow_entity where id=?',('onticardsSerialLoopProbeV1',)).fetchone()[0];db.close()
 if '--existing-published' not in sys.argv:
  run(['docker','exec',name,'n8n','publish:workflow','--id=onticardsSerialLoopProbeV1','--versionId='+version]);run(['docker','restart',name]);native_ready()
 for _ in range(20):
  db=sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True);row=db.execute('select publishedVersionId from workflow_published_version where workflowId=?',('onticardsSerialLoopProbeV1',)).fetchone()
  if row and row[0]==version:
   published=row[0];actual=db.execute('select nodes,connections from workflow_history where versionId=?',(published,)).fetchone();db.close();break
  db.close();time.sleep(0.5)
 else:raise RuntimeError('Exact native publication not ready; no fixture requests sent')
 expected=json.loads((root/'serial-loop-probe.workflow.json').read_text());assert published==version and json.loads(actual[0])==expected['nodes']and json.loads(actual[1])==expected['connections'],'Native published version differs from exact fixture; no requests sent'
 record['native_published_version']={'version_id':published,'nodes':len(expected['nodes']),'file_sha256':hashlib.sha256((root/'serial-loop-probe.workflow.json').read_bytes()).hexdigest(),'definition_exact':True}
 for case in ['normal','empty_issues','missing_closed','missing_failed','count_mismatch','lifecycle']:
  for _ in range(25):
   try:
    q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-serial-loop-probe-v1',data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(q,timeout=60)as r:record['cases'][case]=json.loads(r.read())
    break
   except urllib.error.HTTPError as error:
    if error.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Native fixture route was not registered at its expected path')
 c=record['cases'];result=c['normal']
 record['assertions']={
  'native_two_thread_loop_complete':result.get('complete')is True and result.get('thread_count')==2 and result.get('timeline_pages')==2 and result.get('review_pages')==2,
  'native_per_thread_projection_retained':result.get('event_count')==5 and result.get('event_thread_keys',[]).count('stepll2026/OntiCards#90001')==2 and result.get('event_thread_keys',[]).count('stepll2026/OntiCards#90002')==3,
  'empty_issue_list_with_nonzero_metadata_rejected':c['empty_issues'].get('complete')is False and c['empty_issues'].get('event_count')==0,
  'comment_referenced_missing_closed_issue_fetched':c['missing_closed'].get('complete')is True and c['missing_closed'].get('thread_count')==3 and 'discussion_comment:50003'in c['missing_closed'].get('event_ids',[]),
  'complement_get_failure_blocks_complete':c['missing_failed'].get('complete')is False and c['missing_failed'].get('event_count')==0,
  'independent_open_count_mismatch_rejected':c['count_mismatch'].get('complete')is False,
  'close_and_reopen_each_thread_preserved':sum(e['kind']=='timeline_closed'for e in c['lifecycle']['events'])==2 and sum(e['kind']=='timeline_reopened'for e in c['lifecycle']['events'])==2,
  'all_pr_review_surfaces_preserved':all(any(e['id']==i and e['thread_key']=='stepll2026/OntiCards#90002'for e in c['lifecycle']['events'])for i in ['review:70001','inline_comment:80001','discussion_comment:60002']),
  'app_comment_excluded_from_human_events':next(e for e in c['lifecycle']['events']if e['id']=='discussion_comment:60002')['status']=='ignored_machine_event',
  'human_comment_stays_on_same_issue':next(e for e in c['lifecycle']['events']if e['id']=='discussion_comment:60001')['thread_key']=='stepll2026/OntiCards#90001',
 }
 record['ci_cases']={}
 for case in ['normal','incomplete','unrevoked','wrong_poll','count_mismatch','bad_sha','closed','issue','multiple','oversize']:
  q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-ci-projection-probe-v1',data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
  with opener.open(q,timeout=30)as response:record['ci_cases'][case]=json.loads(response.read())
 ci=record['ci_cases']
 record['assertions'].update({
  'ci_exact_public_fields_only':ci['normal'].get('eligible')is True and ci['normal']['payload']['threads']==[{'pr':90002,'head':'a'*40,'base':'b'*40,'state':'open'}]and'MUST_NOT_LEAVE_INTAKE'not in json.dumps(ci['normal']),
  'ci_rejects_incomplete_unrevoked_wrong_poll_count_and_sha':all(ci[k].get('eligible')is False for k in ['incomplete','unrevoked','wrong_poll','count_mismatch','bad_sha']),
  'ci_skips_closed_pr_and_issue':all(ci[k].get('eligible')is True and ci[k]['payload']['threads']==[]for k in ['closed','issue']),
  'ci_multiple_rows_project_and_post_exactly_once':ci['multiple'].get('eligible')is True and len(ci['multiple']['payload']['threads'])==2 and ci['multiple']['project_items']==1 and ci['multiple']['transport_items']==1 and ci['multiple']['post_count']==1,
  'ci_over_twenty_rejected_without_truncation':ci['oversize'].get('eligible')is False and ci['oversize'].get('reason')=='open_pr_bound_or_duplicate',
 })
 record['batch_budget_cases']={}
 for case in ['six_unseen','consumed','dry_run','stale','cross_batch']:
  q=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-batch-budget-probe-v1',data=json.dumps({'case':case}).encode(),headers={'Content-Type':'application/json'})
  with opener.open(q,timeout=30)as response:record['batch_budget_cases'][case]=json.loads(response.read())
 b=record['batch_budget_cases']
 record['assertions'].update({
  'six_pr_items_read_balance_once_and_bind_all':b['six_unseen']['candidate_items']==6 and b['six_unseen']['bound_items']==6 and b['six_unseen']['transport_count']==1 and b['six_unseen']['post_count']==1 and b['six_unseen']['state']=='budget_exhausted',
  'consumed_batch_performs_no_balance_login':b['consumed']['needed']is False and b['consumed']['transport_count']==0 and b['consumed']['post_count']==0,
  'dry_run_batch_performs_no_balance_login':b['dry_run']['needed']is False and b['dry_run']['transport_count']==0 and b['dry_run']['post_count']==0,
  'stale_batch_observation_rejected':b['stale']['allowed']is False and b['stale']['state']=='budget_unverifiable',
  'cross_batch_observation_rejected':b['cross_batch']['allowed']is False and b['cross_batch']['state']=='budget_unverifiable',
 })
 record['passed']=all(record['assertions'].values())
finally:
 run(['docker','stop',name]);record['probe_stopped']=True;record['completed_at']=datetime.now(timezone.utc).isoformat();(root/'evidence/intake-lifecycle-ci-native-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:v for k,v in record.items()if k not in ['cases','ci_cases','batch_budget_cases']}))
