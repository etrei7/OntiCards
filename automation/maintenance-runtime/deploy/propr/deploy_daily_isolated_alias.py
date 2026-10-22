"""Reuse ProPR's native alias/config selection and systemd readonly facts mount."""
import datetime,hashlib,json,os,shutil,subprocess
from pathlib import Path
root=Path('/opt/onticards-maintenance/propr')
target=root/'opencode/daily'
assert not target.exists(), 'Inspect an existing deployment rather than overwrite it'
target.mkdir(mode=0o700);os.chown(target,1000,1000)
config=json.loads((root/'opencode/opencode.json').read_text())
config['instructions']=[]
(target/'opencode.json').write_text(json.dumps(config,indent=2)+'\n')
for name in ['api-key','daily_input_contract.py']:
 shutil.copy2(root/'opencode'/name,target/name)
for p in target.iterdir():
 p.chmod(0o444 if p.name=='daily_input_contract.py' else 0o600);os.chown(p,1000,1000)
facts=target/'report-inputs';facts.mkdir(mode=0o755)
source=Path('/var/lib/onticards-report/reports')
unit=subprocess.check_output(['systemd-escape','--path','--suffix=mount',str(facts)],text=True).strip()
Path('/etc/systemd/system',unit).write_text(f'''[Unit]
Description=OntiCards readonly facts for native daily-only OpenCode alias
Before=docker.service
[Mount]
What={source}
Where={facts}
Type=none
Options=bind,ro
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
subprocess.run(['systemctl','enable','--now',unit],check=True,capture_output=True)
mount=json.loads(subprocess.check_output(['findmnt','--json','--target',str(facts)],text=True))['filesystems'][0]
assert 'ro' in mount['options'].split(',')
image='registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-agent:onticards-42931b1@sha256:79a910377ec4c63a0309070d3b5b5c891ddd77d6c97df4fa97f9eae95cc4e1e0'
base=['docker','run','--rm','--network','none','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--pids-limit','128','-e','OPENCODE_DISABLE_MODELS_FETCH=1','-v',str(target)+':/home/node/.config/opencode','-w','/tmp','--entrypoint','sh',image,'-c']
probe=subprocess.run(base+['opencode debug config'],text=True,capture_output=True,timeout=60)
assert probe.returncode==0,'Native config probe failed; stdout remains private in process memory'
resolved=json.loads(probe.stdout)
assert not resolved.get('instructions'), 'Global instruction contamination persists'
assert not (target/'AGENTS.md').exists() and not (target/'instructions').exists()
readprobe=subprocess.run(base+['python3 -I /home/node/.config/opencode/daily_input_contract.py 2026-10-22T17:29:00Z'],text=True,capture_output=True,timeout=30)
assert readprobe.returncode==0 and json.loads(readprobe.stdout)['status']=='READY'
subprocess.run(['docker','cp',str(root/'configure_daily_isolated_alias.mjs'),'onticards-propr-api:/usr/src/app/configure_daily_isolated_alias.mjs'],check=True,capture_output=True)
applied=subprocess.run(['docker','exec','-w','/usr/src/app','onticards-propr-api','node','--use-env-proxy','configure_daily_isolated_alias.mjs'],text=True,capture_output=True)
assert applied.returncode==0,'Inspect private native configuration; do not rerun blindly'
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_configuration':json.loads((root/'data/daily-isolated-alias.json').read_text()),'instructions':resolved.get('instructions',[]),'model':resolved.get('model'),'provider_names':list(resolved.get('provider',{})),'readonly_facts':True,'native_helper_ready':True,'new_model_calls':0,'helper_sha256':hashlib.sha256((target/'daily_input_contract.py').read_bytes()).hexdigest(),'unit':unit,'passed':True}
(root/'evidence/daily-isolated-alias.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
