"""Import only the existing CI validation extension and native intake admission; no PR execution."""
import datetime, http.cookiejar, json, pathlib, subprocess, urllib.request
root=pathlib.Path('/opt/onticards-maintenance/preview-ci');name='onticards-preview-ci'
files=['preview.workflow.json','intake-admission.workflow.json','intake-receiver.workflow.json']
workflows=[json.loads((root/'bundle'/p).read_text()) for p in files]
assert all(w['active'] is False for w in workflows)
assert all(not any(n['type'].endswith('scheduleTrigger') for n in w['nodes']) for w in workflows)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
 with opener.open(req,timeout=30) as response:
  value=json.loads(response.read());return value.get('data',value)
owner=json.loads((root/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
execution=api('executions?limit=1')
assert execution.get('concurrentExecutionsCount')==0, 'Actual native execution active; do not replace running workflow'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=root/'state'/('intake-before-'+stamp);backup.mkdir(mode=0o700)
for w in workflows:
 try:old=api('workflows/'+w['id'])
 except urllib.error.HTTPError as error:
  if error.code==404:continue
  raise
 (backup/(w['id']+'.json')).write_text(json.dumps(old));(backup/(w['id']+'.json')).chmod(0o600)
temporary=root/'state/intake-workflows-import.json';temporary.write_text(json.dumps(workflows));temporary.chmod(0o644)
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError('Native workflow operation failed; output withheld')
run(['docker','cp',str(temporary),name+':/tmp/intake-workflows-import.json'])
try:run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/intake-workflows-import.json'])
finally:
 run(['docker','exec','-u','root',name,'rm','-f','/tmp/intake-workflows-import.json']);temporary.unlink(missing_ok=True)
record={'started_at':stamp,'new_schedules':0,'models_or_tests_started':False,'backup':str(backup),'workflows':[]}
for w in workflows:
 current=api('workflows/'+w['id'])
 active=api('workflows/'+w['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 assert active['active'] is True
 record['workflows'].append({'id':w['id'],'nodes':len(w['nodes']),'active':True})
record['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(root/'state/intake-admission-install.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
