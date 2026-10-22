#!/usr/bin/env python3
"""One-time fixed native Skopeo publisher/fetcher installation, never executes images."""
import argparse, hashlib, ipaddress, json, os, pathlib, pwd, re, shutil, subprocess, time
p=argparse.ArgumentParser();p.add_argument('--role',choices=['publish','fetch'],required=True)
p.add_argument('--source-ip',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
assert os.getuid()==0
bundle=pathlib.Path(__file__).resolve().parent
role='build' if a.role=='publish' else 'test';uid=1003 if a.role=='publish' else 1004
assert hashlib.sha256(pathlib.Path('/etc/machine-id').read_bytes()).hexdigest()==json.loads((bundle/'host-identities.json').read_text())[role]
source=str(ipaddress.ip_address(a.source_ip));name='onticards-artifact'
for lookup,arg in [(pwd.getpwnam,name),(pwd.getpwuid,uid)]:
    try:lookup(arg)
    except KeyError:pass
    else:raise RuntimeError('dedicated_identity_already_exists_review_required')
target='registry-intl.cn-hongkong.aliyuncs.com'
old=json.loads(pathlib.Path('/root/.docker/config.json').read_text())
entry=old.get('auths',{}).get(target)
assert entry and entry.get('auth')
key=(bundle/'preview-command.pub').read_text().split()
assert key[0]=='ssh-ed25519' and re.fullmatch(r'[A-Za-z0-9+/]+={0,2}',key[1])
config=pathlib.Path('/etc/ssh/sshd_config.d/62-onticards-artifact.conf');assert not config.exists()
assert 'permituserenvironment no' in subprocess.check_output(['/usr/sbin/sshd','-T'],text=True)
version=subprocess.check_output(['skopeo','--version'],text=True).strip()
if not a.apply:
    print(json.dumps({'review_only':True,'role':a.role,'uid':uid,'registry_entries_copied':1,'version':version}));raise SystemExit()
os.umask(0o077)
subprocess.run(['useradd','--uid',str(uid),'--create-home','--user-group','--home-dir','/home/'+name,'--shell','/bin/bash',name],check=True)
if a.role=='publish':subprocess.run(['usermod','--append','--groups','onticards-preview-transfer',name],check=True)
home=pathlib.Path('/home/'+name);home.chmod(0o700)
authdir=home/'.config/containers';authdir.mkdir(parents=True,mode=0o700)
auth=authdir/'auth.json';auth.write_text(json.dumps({'auths':{target:entry}}));auth.chmod(0o600)
for path in [home,home/'.config',authdir,auth]:os.chown(path,uid,uid)
root=pathlib.Path('/opt/onticards-preview-artifacts');root.mkdir(mode=0o755);root.chmod(0o755)
shutil.copyfile(bundle/'artifact_registry.py',root/'artifact_registry.py');(root/'artifact_registry.py').chmod(0o644)
(root/'role.json').write_text(json.dumps({'role':a.role,'uid':uid}));(root/'role.json').chmod(0o644)
keyfile=pathlib.Path('/etc/ssh/onticards-preview-keys')/name;assert not keyfile.exists()
keyfile.write_text(f'from="{source}",restrict '+ ' '.join(key[:2])+'\n');keyfile.chmod(0o644)
if a.role=='fetch':
    inbox=pathlib.Path('/opt/onticards-preview-transfer-root/inbox')
    assert not list(inbox.iterdir()),'existing inbox requires operator review'
    os.chown(inbox,uid,1001);inbox.chmod(0o2750)
config.write_text('''# Only the dedicated trusted artifact identity.
Match User onticards-artifact
    AuthorizedKeysFile /etc/ssh/onticards-preview-keys/%u
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    DisableForwarding yes
    PermitTTY no
    X11Forwarding no
    ForceCommand /usr/bin/python3 -I /opt/onticards-preview-artifacts/artifact_registry.py
Match all
''');config.chmod(0o644)
validated=subprocess.run(['/usr/sbin/sshd','-t'],capture_output=True)
if validated.returncode:config.unlink();raise RuntimeError('new_ssh_config_rejected_no_reload')
subprocess.run(['systemctl','reload','ssh'],check=True)
effective=subprocess.check_output(['/usr/sbin/sshd','-T','-C',f'user={name},addr={source},host=preview-ci'],text=True)
assert all(v in effective for v in ['disableforwarding yes','permittty no','passwordauthentication no','permituserenvironment no'])
denied=subprocess.run(['runuser','-u','onticards-preview','--','test','-r',str(auth)]).returncode!=0
assert denied
print(json.dumps({'installed':True,'role':a.role,'uid':uid,'version':version,'auth_entries':1,
 'uid1001_auth_read_denied':denied,'auth_mode':oct(auth.stat().st_mode&0o777),'source_restricted':True,
 'root_or_docker_group_granted':False,'socket_access':False,'built_or_executed_images':0,
 'credential_scope':'existing registry credential, not repository-minimal','time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}))
