"""After final PR30 publication: native baseline, then arm only future versions.
Requires an explicitly validated policy13 image. No replay, model call or GitHub POST.
Uses existing n8n workflow APIs/DataTable and the fixed host policy configuration.
"""
import argparse,datetime,http.cookiejar,json,pathlib,re,sqlite3,subprocess,time,urllib.request,uuid
from read_review_baseline import read_baseline
ROOT=pathlib.Path('/opt/onticards-maintenance/preview-ci')
SERVICE=pathlib.Path('/opt/onticards-maintenance/propr/review-service')
# policy13: 964/964 + full compilation on kol-stage2, immutable registry readback.
APPROVED_IMAGE_DIGESTS={'sha256:3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879'}
parser=argparse.ArgumentParser();parser.add_argument('--config-head',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
snapshot=read_baseline(args.config_head)
if not args.apply:
    print(json.dumps({'mode':'prepare_only','snapshot':snapshot,'model_calls':0,'enabled':False},indent=2));raise SystemExit(0)
containers=[]
for role in ['api','worker','daemon']:
    value=json.loads(subprocess.check_output(['docker','inspect','onticards-propr-'+role,'--format','{{json .}}'],text=True))
    image=value['Config']['Image']
    assert image.split('@')[-1] in APPROVED_IMAGE_DIGESTS and value['State']['Status']=='running', 'Native review guards not approved in all running services; keep disabled'
    containers.append({'role':role,'image':image,'image_id':value['Image'],'state':value['State']['Status']})
assert len({c['image'] for c in containers})==1
policy=json.loads((SERVICE/'policy.json').read_text());assert policy['enabled'] is False
db=sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True)
assert db.execute("select count(*) from execution_entity where deletedAt is null and status in ('new','running','waiting') and workflowId in ('onticardsReviewAdmissionV1','onticardsPreviewIntakeV1')").fetchone()[0]==0, 'Wait for current native batch to finish'
db.close()
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None,method=None):
 req=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 with opener.open(req,timeout=30) as response:
  d=json.loads(response.read());return d.get('data',d)
owner=json.loads((ROOT/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup=ROOT/'state'/('review-activation-before-'+stamp);backup.mkdir(mode=0o700)
child=json.loads((ROOT/'bundle/review-admission.workflow.json').read_text());assert child['active'] is False and child['id']=='onticardsReviewAdmissionV1' and len(child['nodes'])==19
receiver=api('workflows/onticardsPreviewIntakeV1')
assert len([n for n in receiver['nodes'] if n['name']=='Native semantic review admission'])==1
assert len([n for n in receiver['nodes'] if n['name']=='Read one native balance per complete batch'])==1
for w in [api('workflows/'+child['id']),receiver]:
 f=backup/(w['id']+'.json');f.write_text(json.dumps(w));f.chmod(0o600)
(backup/'policy.json').write_text(json.dumps(policy));(backup/'policy.json').chmod(0o600)
def update_child(mode):
 current=api('workflows/'+child['id'])
 if current['active']:api('workflows/'+child['id']+'/deactivate',{})
 w=json.loads(json.dumps(child));node=next(n for n in w['nodes'] if n['name']=='Validate fixed review candidate')
 assert "const trusted_mode='dry_run'" in node['parameters']['jsCode']
 node['parameters']['jsCode']=node['parameters']['jsCode'].replace("const trusted_mode='dry_run'","const trusted_mode='"+mode+"'")
 current=api('workflows/'+child['id'])
 api('workflows/'+child['id'],{'name':w['name'],'nodes':w['nodes'],'connections':w['connections'],'settings':w['settings'],'versionId':current['versionId']},'PATCH')
 current=api('workflows/'+child['id']);assert current['nodes']==w['nodes']
 api('workflows/'+child['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 return current['versionId']
record={'at':stamp,'snapshot':snapshot,'containers':containers,'models_called_by_installer':0,'github_writes':0,'old_versions_replayed':False,'enabled':False}
child_touched=False
try:
    api('workflows/'+receiver['id']+'/deactivate',{})
    db=sqlite3.connect('file:'+str(ROOT/'database/database.sqlite')+'?mode=ro',uri=True)
    try:active=db.execute("select count(*) from execution_entity where deletedAt is null and status in ('new','running','waiting') and workflowId in ('onticardsReviewAdmissionV1','onticardsPreviewIntakeV1')").fetchone()[0]
    finally:db.close()
    assert active==0, 'Existing native batch active after receiver deactivation; keep dry run'
    child_touched=True
    update_child('baseline')
    fixture=api('workflows/onticardsReviewReadOnlyProbeV1')
    assert fixture['active'] is False
    f=backup/(fixture['id']+'.json');f.write_text(json.dumps(fixture));f.chmod(0o600)
    fixed=next(n for n in fixture['nodes'] if n['name']=='Fixed historical identity only')
    fixed['parameters']['jsCode']='return '+json.dumps([{'json':v} for v in snapshot['versions']])+';'
    # The native webhook returns one item by default. Aggregate all child results
    # explicitly so six baseline rows cannot be mistaken for one successful row.
    aggregate_name='Collect all baseline receipts'
    fixture['nodes']=[n for n in fixture['nodes'] if n['name']!=aggregate_name]
    fixture['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,fixture['id']+'/'+aggregate_name)),
        'name':aggregate_name,'type':'n8n-nodes-base.code','typeVersion':2,'position':[600,0],
        'parameters':{'jsCode':'return [{json:{versions:$input.all().map(x=>x.json)}}];'}})
    fixture['connections']['Existing native review child']={'main':[[{'node':aggregate_name,'type':'main','index':0}]]}
    api('workflows/'+fixture['id'],{'name':fixture['name'],'nodes':fixture['nodes'],'connections':fixture['connections'],'settings':fixture['settings'],'versionId':fixture['versionId']},'PATCH')
    fixture=api('workflows/'+fixture['id'])
    api('workflows/'+fixture['id']+'/activate',{'versionId':fixture['versionId'],'expectedChecksum':fixture['checksum']});time.sleep(2)
    header=json.loads((ROOT/'secrets/trigger.json').read_text())
    request=urllib.request.Request('http://127.0.0.1:18132/webhook/onticards-review-readonly-probe-v1',data=b'{}',headers={header['name']:header['value'],'Content-Type':'application/json'},method='POST')
    with opener.open(request,timeout=300) as response:envelope=json.loads(response.read())
    if isinstance(envelope,list):assert len(envelope)==1;envelope=envelope[0]
    assert isinstance(envelope,dict) and set(envelope)=={'versions'}
    results=envelope['versions'];assert isinstance(results,list)
    assert len(results)==len(snapshot['versions'])
    for expected in snapshot['versions']:
        value=next(r for r in results if r['pr']==expected['pr'])
        assert value['head']==expected['head'] and value['base']==expected['base']
        assert value['state']=='baseline' or value['state']=='already_consumed' and value['prior_states']==['baseline']
    record['baseline_rows_verified']=len(results)
    api('workflows/'+fixture['id']+'/deactivate',{})
    record['review_workflow_version']=update_child('review')
    policy={'enabled':True,'repository':'stepll2026/OntiCards','baseline_versions':[v['review_key'] for v in snapshot['versions']],
            'baseline_watermark':snapshot['watermark'],'activated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config_head':args.config_head}
    tmp=SERVICE/'policy.new.json';tmp.write_text(json.dumps(policy,indent=2));tmp.chmod(0o600);tmp.replace(SERVICE/'policy.json')
    current=api('workflows/'+receiver['id'])
    api('workflows/'+receiver['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
    actual=api('workflows/'+child['id']);receiver_actual=api('workflows/'+receiver['id'])
    actual_mode=next(n for n in actual['nodes'] if n['name']=='Validate fixed review candidate')['parameters']['jsCode']
    assert actual['active'] is True and actual['activeVersionId']==record['review_workflow_version'] and "const trusted_mode='review'" in actual_mode
    assert receiver_actual['active'] is True and json.loads((SERVICE/'policy.json').read_text())==policy
    record.update(enabled=True,activated_at=policy['activated_at'],trigger='existing complete intake only; new repo/PR/head/base tuples',receipt_policy='all outcomes permanent; no cross-poll retries')
except Exception as error:
    record['failure']='BASELINE_OR_ACTIVATION_CHECK_FAILED'
finally:
    try:
        try:api('workflows/onticardsReviewReadOnlyProbeV1/deactivate',{})
        except Exception:record['temporary_probe_deactivation_unknown']=True
        if not record['enabled']:
            try:
                policy['enabled']=False;(SERVICE/'policy.json').write_text(json.dumps(policy));(SERVICE/'policy.json').chmod(0o600)
            except Exception:record['host_policy_restore']='unknown'
            # Restore normal CI intake without erasing baseline or retry budgets.
            try:
                if child_touched:update_child('dry_run')
                current=api('workflows/'+receiver['id']);api('workflows/'+receiver['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
            except Exception:record['workflow_restore']='unknown'
    finally:
        output=ROOT/'state/mcp-review-activation.json';output.write_text(json.dumps(record,indent=2));output.chmod(0o600)
print(json.dumps(record))
raise SystemExit(0 if record['enabled'] and not any(record.get(k) for k in ['host_policy_restore','workflow_restore','temporary_probe_deactivation_unknown']) else 2)
