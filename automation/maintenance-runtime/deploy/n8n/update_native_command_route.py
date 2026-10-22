"""Patch only the existing ordinary-routing Set node; preserve live switches and budgets."""
import copy,datetime,hashlib,http.cookiejar,json,pathlib,sqlite3,urllib.request
root=pathlib.Path('/opt/onticards-maintenance/n8n');id='onticardsPersistentDraftsV1'
proof=json.loads((root/'evidence/native-slash-routing-probe.json').read_text())
assert proof['passed']and len(proof['assertions'])==9 and all(proof['assertions'].values())
candidate=json.loads((root/'persistent-drafts.workflow.json').read_text());name='Project deterministic routing observations'
node=next(n for n in candidate['nodes']if n['name']==name)
assert 'native_slash_command_context_only'in node['parameters']['jsonOutput']
c=sqlite3.connect('file:'+str(root/'persistent/state/database.sqlite')+'?mode=ro',uri=True)
assert c.execute("select count(*)from execution_entity where deletedAt is null and status in ('new','running','waiting')and workflowId=?",(id,)).fetchone()[0]==0,'Actual draft execution active; no patch';c.close()
o=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None,method=None):
 q=urllib.request.Request('http://127.0.0.1:18128/rest/'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with o.open(q,timeout=30)as r:d=json.loads(r.read());return d.get('data',d)
owner=json.loads((root/'persistent/secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
old=api('workflows/'+id);assert old['active']is True and len(old['nodes'])==45
configuration=json.loads(next(n for n in old['nodes']if n['name']=='Trusted routing configuration')['parameters']['jsonOutput'])
assert configuration['manual_handoff_threads']==[29,31]and configuration['max_model_calls_per_thread']==6 and configuration['max_app_comments_per_thread']==3
oldnode=next(n for n in old['nodes']if n['name']==name)
assert 'native_slash_command_context_only'not in oldnode['parameters']['jsonOutput'],'Already updated; no repeated mutation'
nodes=copy.deepcopy(old['nodes'])
for n in nodes:
 if n['name']==name:n['parameters']=node['parameters']
assert sum(a!=b for a,b in zip(old['nodes'],nodes))==1
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup=root/'persistent/state'/('native-command-before-'+stamp+'.json');backup.write_text(json.dumps(old));backup.chmod(0o600)
api('workflows/'+id+'/deactivate',{});current=api('workflows/'+id)
api('workflows/'+id,{'name':old['name'],'nodes':nodes,'connections':old['connections'],'settings':old['settings'],'versionId':current['versionId']},'PATCH')
current=api('workflows/'+id);assert current['nodes']==nodes and current['connections']==old['connections']
api('workflows/'+id+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
actual=api('workflows/'+id);assert actual['active']is True and actual['activeVersionId']==current['versionId']
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workflow_id':id,'version':current['versionId'],'active':True,'changed_nodes':[name],'connections_unchanged':True,'live_configuration_unchanged':True,'manual_handoff_threads':configuration['manual_handoff_threads'],'model_limit':6,'reply_limit':3,'old_expression_sha256':hashlib.sha256(oldnode['parameters']['jsonOutput'].encode()).hexdigest(),'new_expression_sha256':hashlib.sha256(node['parameters']['jsonOutput'].encode()).hexdigest(),'native_fixture_passed':9,'model_calls_triggered_by_update':0,'public_posts':0,'data_table_mutations_by_update':0}
(root/'evidence/native-slash-routing-deployment.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
