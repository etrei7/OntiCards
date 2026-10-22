"""Import/activate only the three native Check workflows in the dedicated CI instance."""
import datetime,http.cookiejar,json,pathlib,subprocess,urllib.request
root=pathlib.Path('/opt/onticards-maintenance/preview-ci');name='onticards-preview-ci'
files=['check-observe.workflow.json','check-register.workflow.json','check-watch.workflow.json']
workflows=[json.loads((root/'bundle'/p).read_text()) for p in files]
assert all(w['active'] is False for w in workflows)
temp=root/'state/check-workflows-import.json';temp.write_text(json.dumps(workflows));temp.chmod(0o644)
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError('Native workflow import failed; output withheld')
run(['docker','cp',str(temp),name+':/tmp/check-workflows-import.json'])
try:run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/check-workflows-import.json'])
finally:
 run(['docker','exec','-u','root',name,'rm','-f','/tmp/check-workflows-import.json']);temp.unlink(missing_ok=True)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:18132/rest/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
 with opener.open(req,timeout=30) as response:
  value=json.loads(response.read());return value.get('data',value)
owner=json.loads((root/'secrets/owner.json').read_text());api('login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']});owner.clear()
record={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actions':[],'shared_instances_changed':False,'tests_or_model_started':False}
for w in workflows:
 current=api('workflows/'+w['id'])
 active=api('workflows/'+w['id']+'/activate',{'versionId':current['versionId'],'expectedChecksum':current['checksum']})
 assert active['active'] is True
 record['actions'].append({'id':w['id'],'active':True,'nodes':len(w['nodes'])})
record['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(root/'state/check-watch-install.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
