"""Real transport/scope probes; tools/list only, never tools/call or model invocation."""
import datetime, hashlib, json, pathlib, ssl, subprocess, time, urllib.request, urllib.error
ROOT=pathlib.Path('/opt/onticards-maintenance/propr/review-service')
base=['docker','exec','-i','onticards-preview-ci','/usr/bin/ssh','-F','/opt/onticards-preview-ci/ssh/review_config']
checks=[]
def attempt(name,args,body='',deadline=30):
    p=subprocess.run(base+args,input=body,capture_output=True,text=True,timeout=deadline)
    return p
for name,body in [('invalid_fields','{}'),('oversize','x'*4097),('shell_as_json','$(touch /tmp/onticards-forbidden)')]:
    p=attempt(name,['-T','automatic-review','id; touch /tmp/onticards-forbidden'],body)
    passed=p.returncode==0 and json.loads(p.stdout).get('state')=='invalid_request'
    checks.append({'name':name,'passed':passed});assert passed,name
p=attempt('wrong_host',['-o','HostKeyAlias=invalid-review-host','-T','automatic-review','id'])
checks.append({'name':'wrong_host_pin','passed':p.returncode==255});assert checks[-1]['passed']
p=attempt('remote_forward',['-o','ClearAllForwardings=no','-o','ExitOnForwardFailure=yes','-N','-R','127.0.0.1:19991:127.0.0.1:18122','automatic-review'])
checks.append({'name':'remote_forward_rejected','passed':p.returncode==255 and 'forwarding failed' in p.stderr});assert checks[-1]['passed']
p=attempt('pty',['-tt','automatic-review','id'],'{}')
checks.append({'name':'pty_rejected','passed':'PTY allocation request failed' in p.stderr});assert checks[-1]['passed']
start=time.monotonic()
child=subprocess.Popen(base+['-T','automatic-review','id'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
child.stdin.write('{');child.stdin.flush()
child.wait(timeout=12);child.stdin.close()
out=child.stdout.read();elapsed=time.monotonic()-start
checks.append({'name':'no_eof_bounded','passed':json.loads(out).get('state')=='invalid_request' and elapsed<10,'elapsed_seconds':round(elapsed,3)})
assert checks[-1]['passed']

tls=ssl.create_default_context(cafile='/srv/apps/voicebox/certs/voicebox-ca.crt')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=tls))
for name,url,expected in [('http_mcp_closed','http://10.66.66.5:18123/api/mcp',404),('http_mcp_subpath_closed','http://10.66.66.5:18123/api/mcp/x',404),('https_mcp_unauthenticated','https://127.0.0.1:18135/api/mcp',401),('existing_ui','http://10.66.66.5:18123/',200)]:
    try:
        with opener.open(url,timeout=15) as r:status=r.status
    except urllib.error.HTTPError as e:status=e.code
    checks.append({'name':name,'status':status,'passed':status==expected});assert checks[-1]['passed'],name

p={'repository':'stepll2026/OntiCards','pr':26,'head':'3105b7b61469c6b2945357f2eefa8fcb2e3aaee5','base':'c8e3dfee68d398a37842fc332f73af40a56f02a7','mode':'dry_run'}
p['idempotency_key']='review-'+hashlib.sha256(json.dumps([p['repository'],p['pr'],p['head'],p['base']],separators=(',',':')).encode()).hexdigest()
actual=attempt('native_dry_run',['-T','automatic-review','arbitrary original command ignored'],json.dumps(p),245)
result=json.loads(actual.stdout)
checks.append({'name':'native_mcp_read_only_entry','passed':result.get('state')=='native_review_entry_verified_no_dispatch' and result.get('grant_revocation')=='revoked_verified' and result.get('model_started') is False})
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'passed':all(x['passed'] for x in checks),'native_receipt':result,'tools_call_count':0,'model_calls':0,'github_writes':0,'review_enabled':False}
(ROOT/'state/service-probe.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
assert record['passed']
