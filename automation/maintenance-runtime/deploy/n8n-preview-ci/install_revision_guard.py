"""Native n8n credential/subworkflow import, fixed dedicated instance only; no trigger."""
import json, os, pathlib, sqlite3, subprocess

root=pathlib.Path('/opt/onticards-maintenance/preview-ci'); name='onticards-preview-ci'
def run(args,timeout=90):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError('Native credential/workflow operation failed; output withheld')
    return p.stdout
c=sqlite3.connect('file:'+str(root/'database/database.sqlite')+'?mode=ro',uri=True)
assert c.execute("select count(*) from execution_entity where status in ('running','new','waiting')").fetchone()[0]==0
c.close()
temporary=root/'secrets/preview-jwt-import.temporary.json'
key=pathlib.Path('/opt/onticards-maintenance/propr/secrets/github-app.pem').read_text()
payload=[{'id':'onticardsPreviewAppJwt','name':'OntiCards preview revision App','type':'jwtAuth',
          'data':{'keyType':'pemKey','privateKey':key,'publicKey':'','algorithm':'RS256'}}]
fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump(payload,f)
os.chown(temporary,1003,1003)
try:
    run(['docker','cp','-a',str(temporary),name+':/tmp/preview-jwt-import.json'])
    run(['docker','exec',name,'n8n','import:credentials','--input=/tmp/preview-jwt-import.json'])
finally:
    run(['docker','exec','-u','root',name,'rm','-f','/tmp/preview-jwt-import.json'])
    temporary.unlink(missing_ok=True)
    key='';payload=[]
for file in ['revision-guard.workflow.json','preview.workflow.json']:
    source=root/'bundle'/file
    w=json.loads(source.read_text());assert w['active'] is False
    run(['docker','cp',str(source),name+':/tmp/'+file])
    try:run(['docker','exec',name,'n8n','import:workflow','--input=/tmp/'+file])
    finally:run(['docker','exec','-u','root',name,'rm','-f','/tmp/'+file])
for workflow_id in ['onticardsPreviewRevisionV1','onticardsFixedPreviewV1']:
    run(['docker','exec',name,'n8n','publish:workflow','--id='+workflow_id])
record={'native_jwt_credential_imported':True,'private_key_temporary_removed':not temporary.exists(),
        'read_permissions':['pull_requests','metadata'],'no_token_to_pr_runtime':True,
        'source_pattern':'existing install_persistent_polling.py/build_repository_context.py',
        'workflow_restart_required':True,'triggered':False}
(root/'state/native-revision-guard-install.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
