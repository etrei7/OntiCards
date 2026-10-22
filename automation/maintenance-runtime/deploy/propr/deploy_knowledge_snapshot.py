"""Install the reviewed versioned document bundle through native OpenCode instructions."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import tarfile

ROOT = Path('/opt/onticards-maintenance/propr')
REVISION = '10c6862d4c7325c85618f86455aacf9d10c088b5'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

def main():
    for state in ['wait', 'active', 'paused', 'delayed', 'prioritized', 'waiting-children']:
        result = subprocess.check_output(['docker','exec','onticards-propr-redis-1','redis-cli','-p','18124',
            'LLEN' if state in ['wait','active','paused'] else 'ZCARD','bull:github-issue-processor:'+state], text=True)
        assert int(result)==0, 'Native task queue must be idle'
    config_path=ROOT/'opencode/opencode.json'
    original=config_path.read_bytes()
    config=json.loads(original)
    assert config.get('instructions')==['/home/node/.config/opencode/instructions/*.md']
    other_before=digest(canonical({k:v for k,v in config.items() if k!='instructions'}))
    receipt=ROOT/'evidence/versioned-knowledge-deployment.json'
    assert not receipt.exists()
    target=ROOT/'opencode/knowledge'/REVISION
    assert not target.exists()
    allowed={'AGENTS.md','response-policy.md','repository-context.md','00-snapshot-source.md','manifest.json','opencode-instructions.fragment.json'}
    with tarfile.open(ROOT/'data/knowledge-snapshot.tar') as archive:
        members=archive.getmembers()
        assert {m.name for m in members}==allowed and all(m.isfile() for m in members)
        contents={m.name:archive.extractfile(m).read() for m in members}
    manifest=json.loads(contents['manifest.json'])
    assert manifest['sourceCommit']==REVISION and manifest['repository']=='stepll2026/OntiCards'
    for item in manifest['files']:
        assert item['file'] in allowed and digest(contents[item['file']])==item['sha256']
    target.mkdir(parents=True,mode=0o755)
    for name,content in contents.items():
        path=target/name;path.write_bytes(content);path.chmod(0o444);os.chown(path,0,0)
    backup=ROOT/'data/opencode-before-versioned-knowledge.json'
    with backup.open('xb') as stream:stream.write(original)
    backup.chmod(0o600)
    fragment=json.loads(contents['opencode-instructions.fragment.json'])
    expected=[f'/home/node/.config/opencode/knowledge/{REVISION}/*.md']
    assert fragment['instructions']==expected
    config['instructions']=expected
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    config_path.chmod(0o600);os.chown(config_path,1000,1000)
    after=json.loads(config_path.read_text())
    assert digest(canonical({k:v for k,v in after.items() if k!='instructions'}))==other_before
    record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':manifest,
        'state':'configured_verified','before_instructions':['/home/node/.config/opencode/instructions/*.md'],
        'after_instructions':after['instructions'],'other_configuration_sha256':other_before,
        'before_config_sha256':digest(original),'after_config_sha256':digest(config_path.read_bytes()),
        'old_files_preserved':True,'model_calls':0,'github_writes':0,'native_indexing_enabled':False,
        'note':'Versioned supplemental documents only; actual task checkout remains authoritative. Parent OpenCode config is agent-writable, so this is not a host security boundary.'}
    receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__':main()
