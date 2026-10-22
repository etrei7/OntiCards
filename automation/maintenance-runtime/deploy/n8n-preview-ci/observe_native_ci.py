"""Read only sanitized evidence from the dedicated native n8n instance."""
import datetime, json, pathlib, sqlite3
root=pathlib.Path('/opt/onticards-maintenance/preview-ci')
db=sqlite3.connect('file:'+str(root/'database/database.sqlite')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
def decode(text):
    a=json.loads(text);seen={}
    def d(v):
        if isinstance(v,str) and v.isdigit() and int(v)<len(a):
            n=int(v)
            if n in seen:return seen[n]
            x=a[n]
            if isinstance(x,dict):
                z={};seen[n]=z;z.update({k:d(t) for k,t in x.items()});return z
            if isinstance(x,list):
                z=[];seen[n]=z;z.extend(d(t) for t in x);return z
            return x
        return v
    return d('0')
record={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executions':[]}
for row in db.execute("select id,workflowId,status,startedAt,stoppedAt from execution_entity where workflowId=? order by id desc limit 8", ("onticardsFixedPreviewV1",)):
    item=dict(row)
    # Only the public main workflow; never expose credential-bearing subworkflow node outputs.
    if row['workflowId']=='onticardsFixedPreviewV1':
        data=db.execute('select data from execution_data where executionId=?',(row['id'],)).fetchone()
        if data:
            result=decode(data[0]).get('resultData',{});item['last_node']=result.get('lastNodeExecuted')
            item['nodes']=[{'name':name,'status':r.get('executionStatus'),'duration_ms':r.get('executionTime'),
                           'error_type':r.get('error',{}).get('name')} for name,rs in result.get('runData',{}).items() for r in rs]
            for name in ['Read current PR','Read PR before model','Read PR after tests','Persist native outcome','Return validation only proof']:
                rs=result.get('runData',{}).get(name,[])
                if rs:
                    values=rs[-1].get('data',{}).get('main',[[]])[0]
                    if values:
                        value=values[0].get('json',{})
                        item.setdefault('public_results',{})[name]={k:value[k] for k in
                          ['current','head','base','pr','reason','checked_at','token_issued','token_revoked','state','receipt_key','validation_only','ssh_commands','model_calls','receipt_consumed'] if k in value}
    record['executions'].append(item)
model=root/'state/19aa3bbf395b323dc3869bd6/model-lease.json'
if model.exists():
    value=json.loads(model.read_text());record['model_lease']={k:value.get(k) for k in ['state','token_id','expires_at','revoked_at']}
for filename in ['model-phase-status.json','model-test-receipt.json']:
    path=root/'state/19aa3bbf395b323dc3869bd6'/filename
    if path.exists():
        value=json.loads(path.read_text());record[filename]={k:value.get(k) for k in ['state','model_state','lease','evidence_status','tests_started','test_exit','failed_stage','failure_kind','cleanup']}
record['check_watch']={'rows':[], 'schedule_executions':[]}
for table, in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user%'"):
    # Table names come only from sqlite_master; restrict them before native SQL identifiers.
    if not table.replace('_','').isalnum(): continue
    columns=[row[1] for row in db.execute('pragma table_info("'+table+'")')]
    if 'registration_key' not in columns: continue
    for row in db.execute('select * from "'+table+'"'):
        item=dict(row)
        record['check_watch']['rows'].append({k:item.get(k) for k in
          ['registration_key','pr','head','base','check_id','check_name','external_id','state','detail','createdAt','updatedAt']})
for row in db.execute("select id,workflowId,status,mode,startedAt,stoppedAt from execution_entity where workflowId='onticardsCheckWatchV1' order by id desc limit 5"):
    record['check_watch']['schedule_executions'].append(dict(row))
(root/'state/native-ci-observation.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
