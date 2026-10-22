"""Read-only runtime evidence without credentials, source bodies or request data."""
import json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n');db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
ids=['onticardsPersistentDraftsV1','onticardsPersistentSemanticReviewV1','onticardsPersistentPublicationV1','onticardsIssue31ManualResumeV1']
record={'captured_at':datetime.now(timezone.utc).isoformat(),'workflows':[],'watermarks':[],'conversation_budgets':[],'latest_draft_runs':[],'review_statuses':[],'publication_statuses':[],'direct_model_calls':0,'github_requests':0}
for wid in ids:
 row=db.execute('select id,name,active,nodes from workflow_entity where id=?',(wid,)).fetchone()
 if not row:continue
 nodes=json.loads(row['nodes']);item={k:row[k]for k in ['id','name','active']};item['nodes']=len(nodes)
 for node in nodes:
  if node['name']in ['Trusted routing configuration','Trusted semantic policy','Trusted publication policy']:
   cfg=json.loads(node['parameters']['jsonOutput']);item['policy']={k:v for k,v in cfg.items()if k not in ['seed','facts_pdf','manual_recovery','approval']}
 item['executions']=[dict(r)for r in db.execute('select id,status,startedAt,stoppedAt,deletedAt from execution_entity where workflowId=? order by id desc limit 3',(wid,))]
 record['workflows'].append(item)
for row in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user_%'"):
 cols={r[1]for r in db.execute('pragma table_info("'+row['name']+'")')};table='"'+row['name']+'"'
 if {'repository','watermark'}.issubset(cols):record['watermarks'].extend(dict(r)for r in db.execute('select repository,watermark,poll_id,event_count,thread_count from '+table))
 if {'thread_key','model_calls','reply_count'}.issubset(cols):record['conversation_budgets'].extend(dict(r)for r in db.execute('select thread_key,model_calls,reply_count,pending_event,pending_state from '+table))
 if {'run_id','status','finished_at','details'}.issubset(cols):
  for r in db.execute('select run_id,status,finished_at,details from '+table+' order by id desc limit 4'):
   data=dict(r);details=json.loads(data.pop('details'))
   if 'model_calls_attempted'in details:record['latest_draft_runs'].append({**data,**details})
 if {'event_key','reserved_model_ordinal','policy_version'}.issubset(cols):record['review_statuses'].extend(dict(r)for r in db.execute('select event_key,thread_key,status,reserved_model_ordinal from '+table))
 if {'event_key','comment_id','should_post'}.issubset(cols):record['publication_statuses'].extend(dict(r)for r in db.execute('select event_key,thread_key,status,comment_id,comment_url,should_post from '+table))
db.close();out=root/'evidence/ordinary-pipeline-runtime.json';out.write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps(record,ensure_ascii=False))
