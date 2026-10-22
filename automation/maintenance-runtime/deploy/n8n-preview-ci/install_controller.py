#!/usr/bin/env python3
"""Reviewable one-time native SSH wiring; does not generate keys/build/run PRs."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--role',choices=['build','test'],required=True)
parser.add_argument('--source-ip',required=True,help='Verified trusted n8n SSH egress IP; exact /32 or /128 only')
parser.add_argument('--command-public-key',type=Path,required=True)
parser.add_argument('--transfer-public-key',type=Path,required=True)
parser.add_argument('--trusted-images',type=Path,required=True)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
assert os.geteuid()==0
source=str(ipaddress.ip_address(args.source_ip))
bundle=Path(__file__).resolve().parent
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()==json.loads((bundle/'host-identities.json').read_text())[args.role], 'Host role mismatch'
keys=[]
for path in [args.command_public_key,args.transfer_public_key]:
    parts=path.read_text().split()
    assert len(parts)>=2 and parts[0]=='ssh-ed25519' and re.fullmatch(r'[A-Za-z0-9+/]+={0,2}',parts[1])
    keys.append(' '.join(parts[:2]))
lock=json.loads(args.trusted_images.read_text())
assert set(lock)=={'db','weaviate','nginx','tests'} and all(v.get('identity') for v in lock.values())
preview=pwd.getpwnam('onticards-preview');assert preview.pw_uid==1001
assert subprocess.check_output(['id','-Gn',preview.pw_name],text=True).split()==[preview.pw_name]
root=Path('/opt/onticards-preview-controller');chroot=Path('/opt/onticards-preview-transfer-root')
config=Path('/etc/ssh/sshd_config.d/61-onticards-preview.conf')
assert not config.exists(), 'Existing SSH policy must be reviewed, not silently overwritten'
try:
    pwd.getpwnam('onticards-preview-transfer')
    raise RuntimeError('Unexpected existing transfer identity')
except KeyError:
    pass
policy='''# Dedicated OntiCards rootless CI identities only. No shared SSH policy changes.
Match User onticards-preview
    AuthorizedKeysFile /etc/ssh/onticards-preview-keys/%u
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    DisableForwarding yes
    PermitTTY no
    X11Forwarding no
    ForceCommand /usr/bin/python3 -I /opt/onticards-preview-controller/controller.py
Match User onticards-preview-transfer
    AuthorizedKeysFile /etc/ssh/onticards-preview-keys/%u
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    DisableForwarding yes
    PermitTTY no
    X11Forwarding no
    ChrootDirectory /opt/onticards-preview-transfer-root
    ForceCommand internal-sftp -d / -u 0027 -P symlink,hardlink,rename,posix-rename,setstat,fsetstat
Match all
'''
if not args.apply:
    print(json.dumps({'review_only':True,'role':args.role,'source_ip':source,'fixed_command':str(root/'controller.py'),
                      'transfer_chroot':str(chroot),'keys_in_output':False,'builds':0,'pr_deployments':0}))
    raise SystemExit(0)
assert 'permituserenvironment no' in subprocess.check_output(['/usr/sbin/sshd','-T'],text=True)
subprocess.run(['useradd','--no-create-home','--user-group','--home-dir','/','--shell','/usr/sbin/nologin',
                '--comment','OntiCards fixed SFTP transfer only','onticards-preview-transfer'],check=True)
transfer=pwd.getpwnam('onticards-preview-transfer')
assert subprocess.check_output(['id','-Gn',transfer.pw_name],text=True).split()==[transfer.pw_name]
root.mkdir(mode=0o755)
for name in ['controller.py','nginx.conf','playwright-seccomp.json','host-identities.json','test_entry.py','exercise-product-flow.py']:
    shutil.copyfile(bundle/name,root/name);(root/name).chmod(0o644)
(root/'role').write_text(args.role+'\n');(root/'role').chmod(0o644)
(root/'trusted-images.json').write_text(json.dumps(lock,indent=2)+'\n');(root/'trusted-images.json').chmod(0o644)
chroot.mkdir(mode=0o755)
for name,owner,group in [('outbox',preview.pw_uid,transfer.pw_gid),('inbox',transfer.pw_uid,preview.pw_gid)]:
    directory=chroot/name;directory.mkdir();os.chown(directory,owner,group);directory.chmod(0o2750)
keydir=Path('/etc/ssh/onticards-preview-keys');keydir.mkdir(mode=0o755,exist_ok=True)
for name,key in zip(['onticards-preview','onticards-preview-transfer'],keys):
    path=keydir/name
    assert not path.exists()
    path.write_text(f'from="{source}",restrict {key}\n');path.chmod(0o644)
config.write_text(policy);config.chmod(0o644)
validated=subprocess.run(['/usr/sbin/sshd','-t'],capture_output=True)
if validated.returncode:
    config.unlink()
    raise RuntimeError('sshd configuration rejected; active daemon not reloaded; review partial new-user setup')
subprocess.run(['systemctl','reload','ssh'],check=True)
for name in ['onticards-preview','onticards-preview-transfer']:
    effective=subprocess.check_output(['/usr/sbin/sshd','-T','-C',f'user={name},addr={source},host=preview-ci'],text=True)
    assert 'disableforwarding yes' in effective and 'permittty no' in effective and 'passwordauthentication no' in effective and 'permituserenvironment no' in effective
print(json.dumps({'installed':True,'role':args.role,'source_restricted':True,'host_policy':'ForceCommand + pinned OpenSSH client',
                  'root_or_docker_group_granted':False,'ssh_private_keys_read':False,'builds':0,'pr_deployments':0}))
