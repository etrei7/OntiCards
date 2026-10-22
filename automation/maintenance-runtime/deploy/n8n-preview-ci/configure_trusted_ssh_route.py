#!/usr/bin/env python3
"""One dedicated CI UID and one destination/port native route, no tunnel."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import time

assert os.getuid()==0
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()=='993dd953d413fa7d88b56ebfd19dfc35d40361cd9a370d639279cdbc858856d2'
root=Path('/opt/onticards-maintenance/preview-ci').resolve()
assert str(root)=='/opt/onticards-maintenance/preview-ci' and root.is_dir()
def run(args):return subprocess.check_output(args,text=True)
before=run(['ip','-j','rule']);rules=json.loads(before)
assert not any(x['priority']==8997 for x in rules)
for value in [1003,'onticards-ci-trusted']:
    try:
        pwd.getpwuid(value) if isinstance(value,int) else pwd.getpwnam(value)
        raise RuntimeError('Dedicated CI UID/name already exists; review first')
    except KeyError:pass
route=run(['ip','route','show','table','main'])
assert 'default via ' in route
backup=Path('/opt/onticards-preview-setup/backups')/('ci-ssh-route-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()))
backup.mkdir(mode=0o700)
(backup/'ip-rule.json').write_text(before);(backup/'ip-rule.json').chmod(0o600)
(backup/'main-route.txt').write_text(route);(backup/'main-route.txt').chmod(0o600)
subprocess.run(['useradd','--uid','1003','--user-group','--no-create-home','--home-dir','/nonexistent',
                '--shell','/usr/sbin/nologin','--comment','OntiCards trusted CI only','onticards-ci-trusted'],check=True)
assert run(['id','-Gn','onticards-ci-trusted']).split()==['onticards-ci-trusted']
assert run(['passwd','-S','onticards-ci-trusted']).split()[1]=='L'
for name in ['database','secrets','state']:
    directory=root/name
    assert directory.resolve().is_relative_to(root) and not directory.is_symlink()
    os.chown(directory,1003,1003)
    for item in directory.rglob('*'):
        assert not item.is_symlink() and item.resolve().is_relative_to(directory)
        os.chown(item,1003,1003)
assert (root/'secrets/newapi-account.json').stat().st_mode & 0o777==0o600
script=Path('/opt/onticards-preview-setup/trusted-ssh-route.sh')
script.write_text('''#!/bin/sh
set -eu
ip rule show | grep -F '8997:' | grep -F 'to 101.47.177.55' | grep -F 'uidrange 1003-1003' | grep -F 'ipproto tcp dport 22' | grep -F 'lookup main' >/dev/null || ip rule add priority 8997 uidrange 1003-1003 to 101.47.177.55/32 ipproto tcp dport 22 lookup main
''');script.chmod(0o700)
unit=Path('/etc/systemd/system/onticards-preview-ssh-route.service')
unit.write_text('[Unit]\nDescription=OntiCards trusted CI UID exact SSH route\nAfter=network-pre.target\nBefore=docker.service\n\n[Service]\nType=oneshot\nExecStart='+str(script)+'\nRemainAfterExit=yes\n\n[Install]\nWantedBy=multi-user.target\n')
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','onticards-preview-ssh-route.service'],check=True)
after=json.loads(run(['ip','-j','rule']))
assert [x for x in after if x['priority']!=8997]==rules
selected=run(['ip','route','get','101.47.177.55','uid','1003','ipproto','tcp','dport','22'])
assert 'Mihomo' not in selected and '198.18.' not in selected
record={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'uid':1003,'user':'onticards-ci-trusted',
        'only_rule':next(x for x in after if x['priority']==8997),'other_rules_unchanged':True,
        'selected_route':selected.strip(),'backup':str(backup),'secrets_mode':'0600','secrets_owner':'1003:1003',
        'new_tunnel':False,'shared_uid1000_and_rootless1001_unchanged':True,
        'rollback':'systemctl disable --now onticards-preview-ssh-route; ip rule del priority 8997 uidrange 1003-1003 to 101.47.177.55/32 ipproto tcp dport 22 lookup main'}
Path('/opt/onticards-preview-setup/evidence/trusted-ssh-route.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
