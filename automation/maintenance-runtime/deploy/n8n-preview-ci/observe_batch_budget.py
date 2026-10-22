"""Read existing natural poll receipts/log status, without dispatch or credential access."""
import datetime,json,pathlib,re,sqlite3,subprocess,hashlib
root=pathlib.Path('/opt/onticards-maintenance/preview-ci')
deployment=json.loads((root/'state/batch-budget-deployment.json').read_text())
reconciled=json.loads((root/'state/budget-native-reconciliation.json').read_text())['result']
original=json.loads((root/'state/intake-dispatch-native-observation.json').read_text())['receipts']
after=deployment['completed_at'];cutoff=after[:19].replace('T',' ')
with sqlite3.connect('file:'+str(root/'database/database.sqlite')+'?mode=ro',uri=True)as c:
 c.row_factory=sqlite3.Row
 executions=[dict(r)for r in c.execute('select id,workflowId,status,startedAt,stoppedAt,deletedAt from execution_entity where startedAt>? and workflowId in (?,?,?) order by id',(cutoff,'onticardsPreviewIntakeV1','onticardsPreviewAdmissionV1','onticardsFixedPreviewV1'))]
 table=c.execute('select id from data_table where name=?',('onticards_ci_receipts_v1',)).fetchone()[0]
 assert re.fullmatch('[A-Za-z0-9_-]+',table)
 rows=[dict(r)for r in c.execute('select receipt_key,pr,head,base,state,detail,createdAt,updatedAt from "data_table_user_'+table+'"')]
def same(a,b):return all(a[k]==b[k]for k in ['receipt_key','pr','head','base','state','detail'])
expected={r['receipt_key']:r for r in original};expected.update({r['receipt_key']:r for r in reconciled['after']})
unchanged=len(rows)==len(expected)and all(r['receipt_key']in expected and same(r,expected[r['receipt_key']])for r in rows)
logs=subprocess.run(['docker','logs','--timestamps','--since',after,'new-api'],capture_output=True,text=True,timeout=30)
auth=[]
for line in (logs.stdout+'\n'+logs.stderr).splitlines():
 path=next((p for p in ['/api/user/login','/api/user/self']if p in line),None)
 if path:
  status=re.search(r'\|\s*(\d{3})\s*\|',line);timestamp=re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z',line)
  auth.append({'path':path,'status':int(status.group(1))if status else None,'timestamp':timestamp.group(0)if timestamp else None})
record={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deployment':deployment,'source':'read-only native SQLite execution/receipt tables plus existing container log status projection','executions':executions,'receipts':[{'pr':r['pr'],'state':r['state'],'receipt_key':r['receipt_key'],'detail_sha256':hashlib.sha256(r['detail'].encode()).hexdigest()}for r in rows],'new_api_auth_requests_after_deployment':auth,'reconciliation_originals_preserved':all(json.loads(r['detail'])['original_receipt']['detail']==next(o for o in original if o['receipt_key']==r['receipt_key'])['detail']for r in rows if r['pr']in (30,33)),'all_receipts_unchanged_since_reconciliation':unchanged,'note':'n8n saveData=none leaves soft-deleted execution shells status=running; deletedAt is a deletion marker, not a real completion timestamp. No manual trigger was sent.'}
record['assertions']={'natural_receiver_observed':any(r['workflowId']=='onticardsPreviewIntakeV1'for r in executions),'six_native_child_admissions_observed':sum(r['workflowId']=='onticardsPreviewAdmissionV1'for r in executions)>=6,'no_ci_main_execution':not any(r['workflowId']=='onticardsFixedPreviewV1'for r in executions),'no_unfinished_target_execution':all(r['deletedAt']or r['status']not in ['running','new','waiting']for r in executions),'all_sticky_receipts_unchanged':unchanged,'no_new_native_login_for_consumed_batch':logs.returncode==0 and not auth,'both_prior_unknown_details_preserved':record['reconciliation_originals_preserved']}
record['passed']=all(record['assertions'].values())
(root/'state/batch-budget-natural-poll.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'passed':record['passed'],'assertions':record['assertions'],'receiver_ids':[r['id']for r in executions if r['workflowId']=='onticardsPreviewIntakeV1']}))
