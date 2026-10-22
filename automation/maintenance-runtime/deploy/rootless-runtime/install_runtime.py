#!/usr/bin/env python3
"""Install only OntiCards' isolated native rootless runtime, never a PR workload."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import time

USER = 'onticards-preview'
ROOT = Path('/opt/onticards-preview-setup')
EVIDENCE = ROOT / 'evidence'


def run(args, *, check=True, env=None):
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} exited {result.returncode}: {result.stderr[-1200:]}')
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert os.geteuid() == 0
ROOT.mkdir(mode=0o700, exist_ok=True)
EVIDENCE.mkdir(mode=0o700, exist_ok=True)
marker = ROOT / 'account.json'
before = {
    'recorded_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'root_docker_pid': run(['systemctl', 'show', 'docker', '-p', 'MainPID', '--value']).stdout.strip(),
    'apparmor_profile_sha256': digest('/etc/apparmor.d/rootlesskit'),
    'sysctls': run(['sysctl', 'kernel.apparmor_restrict_unprivileged_userns', 'kernel.unprivileged_userns_clone']).stdout.strip(),
    'uidmap': run(['dpkg-query', '-W', 'uidmap', 'libsubid4']).stdout.strip(),
}
(EVIDENCE / 'runtime-before.json').write_text(json.dumps(before, indent=2) + '\n')
try:
    account = pwd.getpwnam(USER)
    if not marker.exists() or json.loads(marker.read_text())['uid'] != account.pw_uid:
        raise RuntimeError('Existing account is not owned by this task; no mutation allowed')
except KeyError:
    run(['useradd', '--create-home', '--user-group', '--shell', '/bin/bash', '--comment', 'OntiCards isolated preview runtime', USER])
    account = pwd.getpwnam(USER)
    marker.write_text(json.dumps({'user': USER, 'uid': account.pw_uid, 'gid': account.pw_gid, 'home': account.pw_dir}, indent=2) + '\n')
    marker.chmod(0o600)
uid = account.pw_uid
assert uid >= 1000
assert run(['id', '-Gn', USER]).stdout.split() == [USER], 'Unexpected supplementary group'
Path(account.pw_dir).chmod(0o700)
assert run(['passwd', '-S', USER]).stdout.split()[1] == 'L', 'Account password must remain locked'


def mapping(path):
    entries = [line.split(':') for line in Path(path).read_text().splitlines() if line]
    ours = [(int(start), int(count)) for name, start, count in entries if name == USER]
    assert len(ours) == 1 and ours[0][1] >= 65536, 'Native subordinate mapping missing'
    start, count = ours[0]
    assert all(name == USER or start + count <= int(other) or int(other) + int(size) <= start for name, other, size in entries), 'Subordinate mapping overlaps another account'
    return start, count


subuid_start, subuid_count = mapping('/etc/subuid')
mapping('/etc/subgid')
subuid_range = f'{subuid_start}-{subuid_start + subuid_count - 1}'
guard = ROOT / 'network-guard.sh'
ipv4 = ['0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8', '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '198.18.0.0/15', '224.0.0.0/4', '240.0.0.0/4', '101.47.177.55/32']
lines = ['#!/bin/sh', 'set -eu', 'chain=ONTICARDS_PREVIEW',
         'ensure() { tool=$1; shift; "$tool" -w -C "$@" 2>/dev/null || "$tool" -w -A "$@"; }',
         'for tool in iptables ip6tables; do "$tool" -w -S "$chain" >/dev/null 2>&1 || "$tool" -w -N "$chain"; done',
         'ensure iptables "$chain" -m addrtype --dst-type LOCAL -j REJECT']
lines.extend(f'ensure iptables "$chain" -d {network} -j REJECT' for network in ipv4)
lines.extend(['ensure iptables "$chain" -j RETURN', 'ensure ip6tables "$chain" -j REJECT'])
for tool in ['iptables', 'ip6tables']:
    for owner in [str(uid), subuid_range]:
        lines.append(f'{tool} -w -C OUTPUT -m owner --uid-owner {owner} -j "$chain" 2>/dev/null || {tool} -w -I OUTPUT 1 -m owner --uid-owner {owner} -j "$chain"')
guard.write_text('\n'.join(lines) + '\n')
guard.chmod(0o700)
unit = Path('/etc/systemd/system/onticards-preview-network.service')
unit.write_text(f'[Unit]\nDescription=OntiCards preview UID-only network restrictions\nBefore=user@{uid}.service\n\n[Service]\nType=oneshot\nExecStart={guard}\nRemainAfterExit=yes\n\n[Install]\nWantedBy=multi-user.target\n')
dropin = Path(f'/etc/systemd/system/user@{uid}.service.d')
dropin.mkdir(exist_ok=True)
(dropin / '10-onticards-preview-network.conf').write_text('[Unit]\nRequires=onticards-preview-network.service\nAfter=onticards-preview-network.service\n')
slice_dir = Path(f'/etc/systemd/system/user-{uid}.slice.d')
slice_dir.mkdir(exist_ok=True)
(slice_dir / '50-onticards-preview-limits.conf').write_text('[Slice]\nMemoryMax=4G\nCPUQuota=200%\nTasksMax=4096\n')
run(['systemctl', 'daemon-reload'])
run(['systemctl', 'enable', '--now', 'onticards-preview-network.service'])
run(['loginctl', 'enable-linger', USER])
run(['systemctl', 'start', f'user@{uid}.service'])
user_command = ['runuser', '-u', USER, '--', 'env', f'XDG_RUNTIME_DIR=/run/user/{uid}', f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
install = run(user_command + ['dockerd-rootless-setuptool.sh', 'install', '--force'], check=False)
(EVIDENCE / 'rootless-install.log').write_text(install.stdout + install.stderr)
if install.returncode:
    raise RuntimeError(f'Native rootless install failed ({install.returncode}); no AppArmor/sysctl relaxation performed')
info_result = run(user_command + ['docker', '--context', 'rootless', 'info', '--format', '{{json .}}'])
info = json.loads(info_result.stdout)
assert 'name=rootless' in info['SecurityOptions'], 'Runtime is not rootless'
assert info['CgroupDriver'] == 'systemd' and info['CgroupVersion'] == '2', 'Required native resource controls absent'
after = {
    **before, 'completed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'uid': uid, 'gid': account.pw_gid, 'home': account.pw_dir,
    'subuid': [subuid_start, subuid_count], 'socket': f'/run/user/{uid}/docker.sock',
    'root_docker_pid_after': run(['systemctl', 'show', 'docker', '-p', 'MainPID', '--value']).stdout.strip(),
    'apparmor_profile_unchanged': digest('/etc/apparmor.d/rootlesskit') == before['apparmor_profile_sha256'],
    'sysctls_unchanged': run(['sysctl', 'kernel.apparmor_restrict_unprivileged_userns', 'kernel.unprivileged_userns_clone']).stdout.strip() == before['sysctls'],
    'rootless': {key: info.get(key) for key in ['ServerVersion', 'SecurityOptions', 'CgroupDriver', 'CgroupVersion', 'DockerRootDir', 'Driver', 'Containers', 'Images']},
    'user_service': run(user_command + ['systemctl', '--user', 'is-active', 'docker']).stdout.strip(),
    'network_guard': run(['systemctl', 'is-active', 'onticards-preview-network.service']).stdout.strip(),
    'groups': run(['id', '-Gn', USER]).stdout.split(), 'ssh_authorized_keys_created': False,
    'pr_builds': 0, 'pr_deployments': 0, 'network_negative_probes': 'pending',
}
assert after['root_docker_pid_after'] == before['root_docker_pid']
assert after['apparmor_profile_unchanged'] and after['sysctls_unchanged']
(EVIDENCE / 'runtime-installed.json').write_text(json.dumps(after, indent=2) + '\n')
print(json.dumps(after, indent=2))
