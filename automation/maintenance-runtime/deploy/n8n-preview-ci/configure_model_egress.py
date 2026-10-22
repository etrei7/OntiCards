#!/usr/bin/env python3
"""Narrow only the existing test UID chain; no shared Docker/network mutations."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path('/opt/onticards-preview-setup')
GUARD=ROOT/'network-guard.sh'
CHAIN='ONTICARDS_PREVIEW'
HOST='993dd953d413fa7d88b56ebfd19dfc35d40361cd9a370d639279cdbc858856d2'
ALLOW=['-d','10.66.66.5/32','-p','tcp','--dport','18134','-j','ACCEPT']

def run(args,check=True):
    return subprocess.run(args,capture_output=True,text=True,check=check)

def snapshot():
    return run(['iptables-save']).stdout

def unrelated(value):
    return '\n'.join(re.sub(r'\[\d+:\d+\]','[counters]',x) for x in value.splitlines()
                     if 'ONTICARDS_PREVIEW' not in x and not x.startswith('#'))

assert os.getuid()==0
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()==HOST
verify_only=sys.argv[1:]==['--verify-applied']
assert verify_only or not sys.argv[1:]
before=snapshot();original=GUARD.read_text()
if verify_only:
    backup=sorted((ROOT/'backups').glob('model-egress-*'))[-1]
    before=(backup/'iptables-save.txt').read_text()
    original=(backup/'network-guard.sh').read_text()
assert 'ensure iptables "$chain" -m addrtype --dst-type LOCAL -j REJECT' in original
assert 'ensure iptables "$chain" -j RETURN' in original, 'Already changed or unexpected source; operator review required'
recorded=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
allow_line='iptables -w -C "$chain" -d 10.66.66.5/32 -p tcp --dport 18134 -j ACCEPT 2>/dev/null || iptables -w -I "$chain" 1 -d 10.66.66.5/32 -p tcp --dport 18134 -j ACCEPT'
updated=original.replace('ensure iptables "$chain" -m addrtype --dst-type LOCAL -j REJECT',
                        allow_line+'\nensure iptables "$chain" -m addrtype --dst-type LOCAL -j REJECT')
updated=updated.replace('ensure iptables "$chain" -j RETURN','ensure iptables "$chain" -j REJECT')
if not verify_only:
    assert run(['iptables','-C',CHAIN,'-j','RETURN'],check=False).returncode==0
    assert run(['iptables','-C',CHAIN,*ALLOW],check=False).returncode!=0
    backup=ROOT/'backups'/('model-egress-'+recorded);backup.mkdir(parents=True,mode=0o700)
    (backup/'network-guard.sh').write_text(original);(backup/'network-guard.sh').chmod(0o600)
    (backup/'iptables-save.txt').write_text(before);(backup/'iptables-save.txt').chmod(0o600)
    temp=GUARD.with_suffix('.candidate');temp.write_text(updated);temp.chmod(0o700)
    run(['/bin/sh','-n',str(temp)])
    # Remove permissive tail first: a process interruption fails closed.
    run(['iptables','-w','-D',CHAIN,'-j','RETURN'])
    run(['iptables','-w','-A',CHAIN,'-j','REJECT'])
    run(['iptables','-w','-I',CHAIN,'1',*ALLOW])
    temp.replace(GUARD)
    run([str(GUARD)])
assert GUARD.read_text()==updated
after=snapshot()
assert unrelated(before)==unrelated(after), 'Unexpected other-chain mutation'
rules=run(['iptables','-S',CHAIN]).stdout.splitlines()
assert '10.66.66.5/32' in rules[1] and '--dport 18134' in rules[1]
assert rules[-1].startswith('-A '+CHAIN+' -j REJECT')
assert not any('-j RETURN' in x for x in rules)
result={'at':recorded,'backup_directory':str(backup),'host':'10.66.66.5','uid':1001,'subuid':'165536-231071',
        'exact_allow':'tcp 10.66.66.5:18134','public_egress':'denied','other_rules_unchanged':True,
        'rules':rules,'guard_sha256':hashlib.sha256(GUARD.read_bytes()).hexdigest(),
        'rollback':'Restore only the reviewed task guard and task chain from restricted backup; never apply whole-host iptables-save blindly.',
        'runtime_probe':'pending','supplier_calls':0}
out=ROOT/'evidence/model-egress-configuration.json';out.write_text(json.dumps(result,indent=2)+'\n');out.chmod(0o600)
print(json.dumps(result))

