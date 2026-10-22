"""Run native budget transitions, preserving existing fixture state across restart."""
import json,subprocess,time,urllib.request,urllib.error,sys,concurrent.futures,threading,sqlite3,hashlib
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');name='onticards-n8n-server-probe'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError('Native budget fixture management failed; raw output excluded')
 return p.stdout
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def ready():
 for _ in range(90):
  try:
   with opener.open('http://127.0.0.1:18127/healthz/readiness',timeout=2)as r:
    if r.status==200:return
  except OSError:pass
  time.sleep(1)
 raise RuntimeError('Native fixture not ready')
record={'started_at':datetime.now(timezone.utc).isoformat(),'model_requests':0,'github_posts':0,'requests':[]}
concurrency_only='--concurrency-only'in sys.argv
routing_only='--routing-only'in sys.argv
original_name=name+'-before-concurrency';renamed=False
if concurrency_only:
 # Reuse the stopped isolated fixture DB/image; match the live production limit.
 # Keep the old container intact for restoration, and never touch the live server.
 info=json.loads(run(['docker','inspect',name]))[0]
 assert not info['State']['Running'],'Existing isolated fixture is busy'
 assert not subprocess.run(['docker','inspect',original_name],capture_output=True).returncode==0,'Backup fixture name already exists'
 mount=next(m for m in info['Mounts']if m['Destination']=='/home/node/.n8n')
 assert mount['Source']==str(root/'server-probe-v2')
 run(['docker','rename',name,original_name]);renamed=True
 command=['docker','run','-d','--name',name,'--network','host','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','2g','--cpus','1','-v',mount['Source']+':/home/node/.n8n']
 for value in info['Config']['Env']:
  if value.startswith(('N8N_','EXECUTIONS_'))and not value.startswith('N8N_CONCURRENCY_PRODUCTION_LIMIT='):command+=['-e',value]
 command+=['-e','N8N_CONCURRENCY_PRODUCTION_LIMIT=1',info['Image'],'start'];run(command)
try:
 run(['docker','start',name]);ready()
 started=json.loads(run(['docker','inspect',name]))[0]['State']['StartedAt']
 for _ in range(90):
  if 'Finished building workflow dependency index'in run(['docker','logs','--since',started,name]):break
  time.sleep(1)
 else:raise RuntimeError('Native startup index not finished; no import')
 run(['docker','cp',str(root/'conversation-budget-probe.workflow.json'),name+':/tmp/conversation-budget-probe.json']);run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/conversation-budget-probe.json'])
 with sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True)as c:version=c.execute('select versionId from workflow_entity where id=?',('onticardsConversationBudgetProbeV1',)).fetchone()[0]
 run(['docker','exec',name,'n8n','publish:workflow','--id=onticardsConversationBudgetProbeV1','--versionId='+version]);run(['docker','restart',name]);ready()
 expected=json.loads((root/'conversation-budget-probe.workflow.json').read_text())
 for _ in range(90):
  with sqlite3.connect('file:'+str(root/'server-probe-v2/database.sqlite')+'?mode=ro',uri=True)as c:
   row=c.execute('select publishedVersionId from workflow_published_version where workflowId=?',('onticardsConversationBudgetProbeV1',)).fetchone()
   actual=c.execute('select nodes,connections from workflow_history where versionId=?',(row[0],)).fetchone()if row else None
  if row and row[0]==version and json.loads(actual[0])==expected['nodes']and json.loads(actual[1])==expected['connections']:break
  time.sleep(1)
 else:raise RuntimeError('Exact native fixture publication not ready; no requests sent')
 record['native_published_version']={'version_id':version,'nodes':len(expected['nodes']),'file_sha256':hashlib.sha256((root/'conversation-budget-probe.workflow.json').read_bytes()).hexdigest(),'definition_exact':True}
 cases=[(name,2)for name in ['native_mcp','native_fix','native_ultrafix','near_command','marker_only','leading_blank','normal_followup','native_pending','manual29','manual31']]if routing_only else [('closed',2),('reopened',2),('prreview',2),('prinline',2),('machine',2)]if concurrency_only else [('ordinary',1),('ordinary',2),('ordinary',3),('ordinary',4),('ordinary',2),('manual31',1),('manual31',2),('failed',2),('odd_budget',2)]
 for case,round in cases:
  if case=='ordinary'and round==3:run(['docker','restart',name]);ready();record['restart_before_third_reply']=True
  for _ in range(25):
   try:
    req=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-budget6-probe-v1',data=json.dumps({'case':case,'round':round}).encode(),headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=65)as r:response=json.loads(r.read())
    break
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    time.sleep(1)
  else:raise RuntimeError('Fixture registration unavailable')
  record['requests'].append({'case':case,'round':round,'response':response})
 results=[r['response']for r in record['requests']]
 if routing_only:
  r={x['case']:x['response']for x in record['requests']}
  record['assertions']={
   'native_mcp_formatter_body_context_only':r['native_mcp']['route']=='native_slash_command_context_only'and r['native_mcp']['conversation']['model_calls']==0,
   'fix_ultrafix_native_commands_context_only':all(r[x]['route']=='native_slash_command_context_only'and r[x]['conversation']['model_calls']==0 for x in ['native_fix','native_ultrafix']),
   'near_command_not_overfiltered':r['near_command']['route']=='eligible_draft_disabled'and r['near_command']['conversation']['model_calls']==2,
   'marker_alone_never_native_authorization':r['marker_only']['route']=='eligible_draft_disabled'and r['marker_only']['conversation']['model_calls']==2,
   'leading_blank_matches_native_noncommand':r['leading_blank']['route']=='eligible_draft_disabled'and r['leading_blank']['conversation']['model_calls']==2,
   'normal_human_followup_remains_eligible':r['normal_followup']['route']=='eligible_draft_disabled'and r['normal_followup']['conversation']['model_calls']==2,
   'pending_reservation_preserved':r['native_pending']['route']=='model_request_started'and r['native_pending']['conversation']['model_calls']==2 and r['native_pending']['conversation']['pending_state']=='model_request_started',
   'issue29_sealed_unchanged':r['manual29']['route']=='explicit_manual_handoff'and r['manual29']['conversation']['model_calls']==5 and r['manual29']['conversation']['reply_count']==2,
   'issue31_sealed_unchanged':r['manual31']['route']=='explicit_manual_handoff'and r['manual31']['conversation']['model_calls']==3,
  }
 elif concurrency_only:
  barrier=threading.Barrier(2);nonce=int(time.time())%100000000
  def concurrent_request(_):
   barrier.wait();request=urllib.request.Request('http://127.0.0.1:18127/webhook/onticards-budget6-probe-v1',data=json.dumps({'case':'concurrent','round':2,'nonce':nonce}).encode(),headers={'Content-Type':'application/json'})
   with opener.open(request,timeout=65)as response:return json.loads(response.read())
  with concurrent.futures.ThreadPoolExecutor(max_workers=2)as executor:record['concurrent_results']=list(executor.map(concurrent_request,range(2)))
  pair=sorted(record['concurrent_results'],key=lambda r:r['entered_at'])
  record['assertions']={
   'closed_event_context_only_zero_budget':results[0]['route']=='context_only_unattributed_or_timeline'and results[0]['conversation']['model_calls']==0,
   'reopened_event_context_only_zero_budget':results[1]['route']=='context_only_unattributed_or_timeline'and results[1]['conversation']['model_calls']==0,
   'human_pr_review_routes_to_same_bounded_conversation':results[2]['conversation']['model_calls']==2 and results[2]['conversation']['reply_count']==1,
   'human_pr_inline_routes_to_same_bounded_conversation':results[3]['conversation']['model_calls']==2 and results[3]['conversation']['reply_count']==1,
   'machine_comment_context_only_zero_budget':results[4]['route']=='ignored_machine_event'and results[4]['conversation']['model_calls']==0,
   'two_simultaneous_webhooks_enter_serially':pair[1]['entered_at']>=pair[0]['completed_at'],
   'same_human_event_only_one_reservation_pair':all(r['conversation']['model_calls']==2 and r['conversation']['reply_count']==1 for r in pair)and sorted(r['route']for r in pair)==['already_answered_verified','eligible_draft_disabled'],
   'native_limit_matches_live_production': 'N8N_CONCURRENCY_PRODUCTION_LIMIT=1'in json.loads(run(['docker','inspect',name]))[0]['Config']['Env'],
  }
 else:record['assertions']={
  'first_reply_reserves_draft_and_review':results[0]['conversation']['model_calls']==2 and results[0]['conversation']['reply_count']==1,
  'human_followup_preserves_budget_to_four':results[1]['conversation']['model_calls']==4 and results[1]['conversation']['reply_count']==2,
  'third_reply_after_restart_reaches_six':results[2]['conversation']['model_calls']==6 and results[2]['conversation']['reply_count']==3,
  'fourth_reply_rejected_unchanged':results[3]['route']=='thread_reply_cap_human_required'and results[3]['conversation']['model_calls']==6,
  'duplicate_human_event_rejected_unchanged':results[4]['route']=='already_answered_verified'and results[4]['conversation']['model_calls']==6,
  'issue31_first_event_sealed_at_three':results[5]['route']=='explicit_manual_handoff'and results[5]['conversation']['model_calls']==3,
  'issue31_new_human_event_still_sealed':results[6]['route']=='explicit_manual_handoff'and results[6]['conversation']['model_calls']==3,
  'other_failed_thread_remains_manual':results[7]['route']=='waiting_existing_thread_review'and results[7]['conversation']['model_calls']==2,
  'one_remaining_slot_not_enough_for_pair':results[8]['route']=='insufficient_budget_for_draft_and_independent_review'and results[8]['conversation']['model_calls']==5,
 }
 record['passed']=all(record['assertions'].values())
finally:
 run(['docker','stop',name])
 if renamed:
  run(['docker','rm',name]);run(['docker','rename',original_name,name]);record['original_stopped_fixture_restored']=True
 record.update(probe_stopped=True,completed_at=datetime.now(timezone.utc).isoformat());(root/'evidence'/('native-slash-routing-probe.json'if routing_only else'ordinary-concurrency-native-probe.json'if concurrency_only else'conversation-budget-native-probe.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in record.items()if k!='requests'}))
