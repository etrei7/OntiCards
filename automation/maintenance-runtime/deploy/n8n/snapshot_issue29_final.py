"""Read-only evidence for the maintainer's real final Issue29 event."""
import hashlib,json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
root=Path('/opt/onticards-maintenance/n8n');db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
target='6346376385';record={'captured_at':datetime.now(timezone.utc).isoformat(),'human_comment_id':target,'human_comment_url':'https://github.com/stepll2026/OntiCards/issues/29#issuecomment-'+target,'intake':[],'drafts':[],'reviews':[],'publications':[],'safe_model_responses':[],'conversation':[],'model_calls_by_reader':0,'github_requests_by_reader':0};rows=[]
for t in db.execute("select name from sqlite_master where type='table'and name like 'data_table_user_%'"):rows.extend(dict(r)for r in db.execute('select * from "'+t['name']+'"'))
db.close();keys=set()
for r in rows:
 if r.get('thread_key')=='stepll2026/OntiCards#29'and'model_calls'in r:record['conversation'].append(r)
 if 'payload'in r:
  try:p=json.loads(r['payload'])
  except (ValueError,TypeError):continue
  if str(p.get('id'))==target:record['intake'].append(r);keys.add(r.get('event_key'))
 if 'source_snapshot'in r:
  try:s=json.loads(r['source_snapshot'])
  except (ValueError,TypeError):continue
  if str(s.get('event',{}).get('id'))==target:record['drafts'].append(r);keys.add(r.get('event_key'))
for r in rows:
 if r.get('event_key')not in keys:continue
 if 'reserved_model_ordinal'in r:record['reviews'].append(r)
 if 'comment_id'in r:record['publications'].append(r)
 if 'response_key'in r:record['safe_model_responses'].append(r)
summary={'captured_at':record['captured_at'],'human_comment_id':target,'intake_count':len(record['intake']),'event_keys':sorted(keys),'draft_statuses':[{k:r.get(k)for k in ['event_key','status','classification','source_hash','usage','quality_errors']}for r in record['drafts']],'review_statuses':[{k:r.get(k)for k in ['event_key','status','reserved_model_ordinal','usage','result']}for r in record['reviews']],'publication_statuses':[{k:r.get(k)for k in ['event_key','status','comment_id','comment_url','reason']}for r in record['publications']],'conversation':[{k:r.get(k)for k in ['thread_key','model_calls','reply_count','pending_event','pending_state']}for r in record['conversation']]}
out=root/'evidence/issue29-final-native-latest.json';text=json.dumps(record,ensure_ascii=False,indent=2);out.write_text(text)
stable={k:v for k,v in record.items()if k!='captured_at'};signature=hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest();immutable=root/'evidence'/('issue29-final-native-'+signature[:12]+'.json')
if not immutable.exists():immutable.write_text(text)
(root/'evidence/issue29-final-native-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
