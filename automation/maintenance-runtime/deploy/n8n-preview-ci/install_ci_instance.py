#!/usr/bin/env python3
"""Native dedicated n8n instance and inactive workflow import; no PR trigger."""
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import time
import urllib.request

assert os.getuid()==0
root=Path('/opt/onticards-maintenance/preview-ci');name='onticards-preview-ci';uid=1003
assert root.resolve()==root
for port in [18132,18133]:
    with socket.socket() as probe:probe.bind(('127.0.0.1',port))
runtime=root/'secrets/runtime.env';assert not runtime.exists()
runtime.write_text('N8N_ENCRYPTION_KEY='+secrets.token_hex(32)+'\n');runtime.chmod(0o600);os.chown(runtime,uid,uid)
owner=root/'secrets/owner.json';assert not owner.exists()
owner.write_text(json.dumps({'email':'onticards-preview-admin@example.invalid','firstName':'OntiCards','lastName':'Preview',
                            'password':'A9!'+secrets.token_urlsafe(32)}));owner.chmod(0o600);os.chown(owner,uid,uid)
trigger=root/'secrets/trigger.json';assert not trigger.exists()
trigger.write_text(json.dumps({'name':'X-OntiCards-Preview-Trigger','value':secrets.token_urlsafe(48)}));trigger.chmod(0o600);os.chown(trigger,uid,uid)
def run(args):
    value=subprocess.run(args,capture_output=True,text=True,timeout=90)
    if value.returncode:raise RuntimeError('Native setup command failed; restricted output excluded')
    return value.stdout
record={'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'uid':uid,'instance':name,
        'existing_workflow_instances_modified':False,'pr_triggered':False,'workflow_published':False}
compose=['docker','compose','--project-directory',str(root),'-f',str(root/'compose.ci.yml')]
run(compose+['config','--quiet']);run(compose+['up','-d','--no-build','--pull','never'])
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None):
    req=urllib.request.Request('http://127.0.0.1:18132'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=20) as response:return json.load(response)
for attempt in range(120):
    try:request('/healthz/readiness');request('/rest/settings');break
    except Exception:time.sleep(1)
else:raise RuntimeError('Dedicated n8n startup failed; no PR started')
request('/rest/owner/setup',json.loads(owner.read_text()))
temporary=root/'secrets/trigger.temporary.json'
data=json.loads(trigger.read_text())
temporary.write_text(json.dumps([{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger','type':'httpHeaderAuth','data':data}]))
temporary.chmod(0o600);os.chown(temporary,uid,uid)
try:
    run(['docker','cp','-a',str(temporary),name+':/tmp/preview-trigger.json'])
    run(['docker','exec',name,'n8n','import:credentials','--input=/tmp/preview-trigger.json'])
finally:
    run(['docker','exec','-u','root',name,'rm','-f','/tmp/preview-trigger.json']);temporary.unlink(missing_ok=True)
workflow=json.loads((root/'bundle/preview.workflow.json').read_text())
assert workflow['id']=='onticardsFixedPreviewV1' and workflow['active'] is False
for node in workflow['nodes']:
    if node['type']=='n8n-nodes-base.webhook':node['credentials']={'httpHeaderAuth':{'id':'onticardsPreviewTrigger','name':'onticards-preview-trigger'}}
candidate=root/'workflow-import.json';candidate.write_text(json.dumps(workflow));candidate.chmod(0o644)
run(['docker','cp',str(candidate),name+':/tmp/preview-workflow.json'])
run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/preview-workflow.json'])
run(['docker','exec','-u','root',name,'rm','-f','/tmp/preview-workflow.json'])
db=sqlite3.connect('file:'+str(root/'database/database.sqlite')+'?mode=ro',uri=True)
row=db.execute('select id,active from workflow_entity where id=?',('onticardsFixedPreviewV1',)).fetchone();db.close()
assert row==('onticardsFixedPreviewV1',0)
info=json.loads(run(['docker','inspect',name]))[0]
record.update({'image_id':info['Image'],'user':info['Config']['User'],'restart':info['HostConfig']['RestartPolicy']['Name'],
               'listen':'127.0.0.1:18132','concurrency':1,'workflow_nodes':len(workflow['nodes']),'inactive_verified':True,
               'completed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
Path('/opt/onticards-preview-setup/evidence/ci-instance-install.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
