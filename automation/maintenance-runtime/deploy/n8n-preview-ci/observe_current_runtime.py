"""Read only the named maintenance services, timers and native workflow metadata.
Never reads credentials, environment values, raw execution payloads or task bodies.
"""
import datetime,json,pathlib,sqlite3,subprocess,urllib.request,urllib.error
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
def run(argv):return subprocess.check_output(argv,text=True,timeout=30)
containers=[]
for role in ['api','worker','daemon','web']:
 value=json.loads(run(['docker','inspect','onticards-propr-'+role,'--format','{{json .}}']))
 containers.append({'role':role,'configured_image':value['Config']['Image'],'image_id':value['Image'],
                    'state':value['State']['Status'],'started_at':value['State']['StartedAt']})
timers=[]
for unit in ['onticards-snapshot.timer','onticards-report.timer']:
 fields={}
 for line in run(['systemctl','show',unit,'--property=Id,ActiveState,SubState,NextElapseUSecRealtime,LastTriggerUSec']).splitlines():
  key,_,value=line.partition('=');fields[key]=value
 timers.append(fields)
workflows=[]
for label,database,wids in [
 ('intake','/opt/onticards-maintenance/n8n/persistent/state/database.sqlite',['onticardsPersistentReadOnlyV1','onticardsIntakeCiHandoffV1']),
 ('ci',str(ROOT/'database/database.sqlite'),['onticardsPreviewIntakeV1','onticardsPreviewAdmissionV1','onticardsReviewAdmissionV1','onticardsReviewReadOnlyProbeV1','onticardsCheckWatchV1'])]:
 db=sqlite3.connect('file:'+database+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  for wid in wids:
   row=db.execute('select id,active,activeVersionId,nodes from workflow_entity where id=?',(wid,)).fetchone()
   if row is None:workflows.append({'instance':label,'id':wid,'found':False});continue
   nodes=json.loads(row['nodes']);entry={'instance':label,'id':wid,'found':True,'active':bool(row['active']),'active_version':row['activeVersionId'],'node_count':len(nodes)}
   if wid=='onticardsReviewAdmissionV1':
    code=next(n for n in nodes if n['name']=='Validate fixed review candidate')['parameters']['jsCode']
    entry['trusted_mode']=next((x for x in ['dry_run','baseline','review'] if "const trusted_mode='"+x+"'" in code),'unknown')
   workflows.append(entry)
 finally:db.close()
policy=json.loads(pathlib.Path('/opt/onticards-maintenance/propr/review-service/policy.json').read_text())
policy_safe={k:policy[k] for k in ['enabled','repository','activated_at','config_head','baseline_watermark'] if k in policy};policy_safe['baseline_version_count']=len(policy.get('baseline_versions',[]))
listeners=run(['ss','-H','-ltn','sport = :18135']).splitlines()
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));http={}
for path in ['/health','/api/mcp','/api/mcp/child']:
 url='http://127.0.0.1:18122/health' if path=='/health' else 'http://10.66.66.5:18123'+path
 try:
  with opener.open(url,timeout=10) as response:http[path]=response.status
 except urllib.error.HTTPError as e:http[path]=e.code
record={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containers':containers,'timers':timers,'workflows':workflows,'review_host_policy':policy_safe,'mcp_listener_lines':listeners,'http_status':http,'models':0,'mutations':0}
output=ROOT/'state/current-runtime.json';output.write_text(json.dumps(record,indent=2));print(json.dumps(record))
