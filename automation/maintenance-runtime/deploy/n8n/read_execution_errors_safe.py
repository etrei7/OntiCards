"""Read only error node names and known error families, never payloads/headers."""
import json,sqlite3
from pathlib import Path
root=Path('/opt/onticards-maintenance/n8n');db=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
records=[]
for row in db.execute('select e.id,e.status,e.workflowId,e.startedAt,e.stoppedAt,d.data from execution_entity e left join execution_data d on e.id=d.executionId order by e.id desc limit 15'):
 rec={k:row[k]for k in ['id','status','workflowId','startedAt','stoppedAt']}
 if row['data']:
  data=json.loads(row['data'])
  def value(x):return data[int(x)]if isinstance(x,str)and x.isdigit()else x
  result=value(data[0].get('resultData',{}));error=value(result.get('error',{}))if isinstance(result,dict)else{}
  if isinstance(error,dict):
   rec['error_keys']=list(error)
   if 'name'in error:rec['error_type']=value(error['name'])
   if 'node'in error:
    node=value(error['node']);rec['error_node']=value(node.get('name'))if isinstance(node,dict)else None
   message=str(value(error.get('message','')))
   rec['error_families']=[s for s in ['JSON','Referenced node','not executed','Paired item','paired item','match','Workflow','timeout','deadline','array','undefined','Cannot','Invalid','scope','credentials','Data table']if s.lower()in message.lower()]
  if isinstance(result,dict)and'lastNodeExecuted'in result:rec['last_node']=value(result['lastNodeExecuted'])
 records.append(rec)
db.close();(root/'evidence/native-execution-error-tags.json').write_text(json.dumps(records,indent=2));print(json.dumps(records))
