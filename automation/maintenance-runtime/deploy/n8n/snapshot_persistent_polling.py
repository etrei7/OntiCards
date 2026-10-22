"""Read-only public ledger/status evidence, excluding credentials and execution payloads."""
import hashlib,json,sqlite3,subprocess
from datetime import datetime,timezone
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');db=root/'persistent/state/database.sqlite'
conn=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
tables=[r[0] for r in conn.execute("select name from sqlite_master where type='table'")]
record={'captured_at':datetime.now(timezone.utc).isoformat(),'state_directory':str(db.parent),'model_calls_by_snapshot_reader':0,'repository_writes_by_snapshot_reader':0,'tables':{}}
for table in tables:
 if table.startswith('data_table_user_'):
  rows=[dict(row) for row in conn.execute('select * from "'+table+'"')]
  record['tables'][table]={'count':len(rows),'rows':rows}
record['workflows']=[dict(row) for row in conn.execute('select id,name,active from workflow_entity')]
record['reserved_model_calls_by_thread']=[{k:r[k]for k in ['thread_key','model_calls','pending_event','pending_state']}for t in record['tables'].values()for r in t['rows']if 'model_calls'in r and'thread_key'in r]
record['executions']=[dict(row) for row in conn.execute('select id,status,startedAt,stoppedAt,deletedAt from execution_entity order by id desc limit 20')]
record['execution_saved_nodes']=[]
for row in conn.execute('select executionId,data from execution_data'):
 data=json.loads(row['data']);result=data[int(data[0]['resultData'])]
 record['execution_saved_nodes'].append({'id':row['executionId'],'nodes':list(data[int(result['runData'])])})
conn.close()
inspect=json.loads(subprocess.check_output(['docker','inspect','onticards-maintenance-triage'],text=True))[0]
record['runtime']={'running':inspect['State']['Running'],'image':inspect['Image'],'restart':inspect['HostConfig']['RestartPolicy']['Name'],'network':inspect['HostConfig']['NetworkMode'],'privileged':inspect['HostConfig']['Privileged'],'cap_drop':inspect['HostConfig']['CapDrop'],'configuration':[v for v in inspect['Config']['Env'] if v.split('=',1)[0] in ['N8N_PORT','N8N_LISTEN_ADDRESS','N8N_CONCURRENCY_PRODUCTION_LIMIT','EXECUTIONS_DATA_SAVE_ON_SUCCESS','EXECUTIONS_DATA_SAVE_ON_ERROR']]}
stamp=datetime.now(timezone.utc).strftime('%H%M%S')
path=root/'evidence'/('persistent-polling-status-'+stamp+'.json');path.write_text(json.dumps(record,ensure_ascii=False,indent=2))
(root/'evidence/persistent-polling-status-latest.json').write_text(path.read_text())
print(json.dumps({'file':str(path),'running':record['runtime']['running'],'tables':{t:v['count'] for t,v in record['tables'].items()},'watermarks':[r for t in record['tables'].values() for r in t['rows'] if 'watermark' in r],'polls':[r for t in record['tables'].values() for r in t['rows'] if 'finished_at' in r],'executions':record['executions']},ensure_ascii=False))
