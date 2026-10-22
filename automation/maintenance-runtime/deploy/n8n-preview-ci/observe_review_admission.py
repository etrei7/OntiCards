"""Read safe native receipt metadata, never execution payloads or credentials."""
import datetime,json,pathlib,re,sqlite3
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
db=sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
identities=db.execute('select id from data_table where name=?',('onticards_pr_reviews_v1',)).fetchall()
assert len(identities)==1 and re.fullmatch('[A-Za-z0-9_]+',identities[0]['id'])
tables=['data_table_user_'+identities[0]['id']]
assert {'review_key','pr','head','base','state','detail'}.issubset({r[1] for r in db.execute('pragma table_info("'+tables[0]+'")')})
rows=[]
allowed={'state','repository','pr','head','base','idempotency_key','mode','automatic_retry','model_started','checked_at','grant_scopes','grant_repository_count','fresh_revision','tls_verified','review_tool_visible','merge_tool_visible','grant_revocation','reason_code','observed_at','credential_cleanup_required','native_state','native_lifecycle','operation_id','native_payload_match','comment_id','comment_url','resolved_head'}
for row in db.execute('select review_key,pr,head,base,state,detail from "'+tables[0]+'" order by id'):
    value=dict(row);detail=json.loads(value.pop('detail'));value['detail']={k:v for k,v in detail.items() if k in allowed};rows.append(value)
workflows=[]
for wid in ['onticardsReviewAdmissionV1','onticardsPreviewIntakeV1']:
    row=db.execute('select id,active,activeVersionId,nodes from workflow_entity where id=?',(wid,)).fetchone()
    nodes=json.loads(row['nodes']);workflows.append({'id':wid,'active':bool(row['active']),'version':row['activeVersionId'],'nodes':len(nodes)})
executions=[dict(x) for x in db.execute("select id,workflowId,startedAt,deletedAt from execution_entity where workflowId in ('onticardsReviewAdmissionV1','onticardsPreviewIntakeV1') order by cast(id as integer) desc limit 16")]
db.close()
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workflows':workflows,'rows':rows,'latest_execution_metadata':executions,
        'dry_run_count':len([x for x in rows if x['review_key'].startswith('probe:')]),'real_admission_count':len([x for x in rows if not x['review_key'].startswith('probe:')]),'model_calls_from_dry_run':0}
out=ROOT/'state/review-natural-intake.json';out.write_text(json.dumps(record,indent=2));print(json.dumps(record))
