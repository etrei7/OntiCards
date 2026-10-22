#!/usr/bin/env python3
"""Use an already cached image for native isolation probes; no PR or build."""
import json
import os
from pathlib import Path
import pwd
import socket
import subprocess
import sys
import time

root = Path('/opt/onticards-preview-setup')
account = pwd.getpwnam('onticards-preview')
user = ['runuser', '-u', account.pw_name, '--', 'env', f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}']
docker = user + ['docker', '--context', 'rootless']
image = sys.argv[1]
assert image in ['busybox:latest', 'redis:7-alpine']


def run(command, *, timeout=60):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


info = json.loads(run(['docker', 'image', 'inspect', image]).stdout)[0]
source = subprocess.Popen(['docker', 'image', 'save', image], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
loaded = subprocess.run(docker + ['image', 'load'], stdin=source.stdout, capture_output=True, text=True, timeout=120)
source.stdout.close()
assert source.wait(timeout=20) == 0 and loaded.returncode == 0
loaded_info = json.loads(run(docker + ['image', 'inspect', image]).stdout)[0]
assert loaded_info['RootFS']['Layers'] == info['RootFS']['Layers']

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(('127.0.0.1', 0))
listener.listen(8)
port = listener.getsockname()[1]
with socket.create_connection(('127.0.0.1', port), timeout=2):
    pass
negative_code = '''import socket,json,os
targets=json.loads(__import__('sys').argv[1]); results=[]
for name,host,port in targets:
 try:
  s=socket.create_connection((host,port),timeout=2); s.close(); results.append({'name':name,'blocked':False})
 except OSError as e: results.append({'name':name,'blocked':True,'errno':e.errno})
try:
 s=socket.socket(socket.AF_UNIX); s.connect('/var/run/docker.sock'); s.close(); denied=False
except OSError: denied=True
print(json.dumps({'connections':results,'root_docker_socket_denied':denied,'app_private_key_readable':os.access('/opt/onticards-maintenance/propr/secrets/github-app.pem',os.R_OK),'root_ssh_directory_readable':os.access('/root/.ssh',os.R_OK)}))
'''
targets = [('host-loopback', '127.0.0.1', port), ('rfc1918-10', '10.66.66.5', 9922), ('docker-bridge', '172.17.0.1', 80), ('rfc1918-192', '192.168.1.1', 80), ('link-local-metadata', '169.254.169.254', 80), ('cgnat-metadata', '100.100.100.200', 80), ('build-host-public', '101.47.177.55', 22), ('ipv6-loopback', '::1', port)]
host_probe = run(user + ['python3', '-c', negative_code, json.dumps(targets)])
assert host_probe.returncode == 0, host_probe.stderr
host_results = json.loads(host_probe.stdout)
assert all(x['blocked'] for x in host_results['connections'])
assert host_results['root_docker_socket_denied'] and not host_results['app_private_key_readable'] and not host_results['root_ssh_directory_readable']

restrictions = ['run', '--rm', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=64m', '--cpus=0.5', '--entrypoint=/bin/sh']
limits = run(docker + restrictions + ['--network=none', image, '-c', 'printf "memory="; cat /sys/fs/cgroup/memory.max; printf "pids="; cat /sys/fs/cgroup/pids.max; printf "cpu="; cat /sys/fs/cgroup/cpu.max; grep -E "^(CapEff|NoNewPrivs):" /proc/self/status; test ! -S /var/run/docker.sock; test ! -e /opt/onticards-maintenance/propr/secrets/github-app.pem'])
assert limits.returncode == 0, limits.stderr
assert 'memory=67108864' in limits.stdout and 'pids=64' in limits.stdout and 'cpu=50000 100000' in limits.stdout
assert 'CapEff:\t0000000000000000' in limits.stdout and 'NoNewPrivs:\t1' in limits.stdout
container_targets = targets[:-1] + [('rootless-host-gateway', '10.0.2.2', port)]
commands = ['command -v nc >/dev/null || exit 90', 'command -v timeout >/dev/null || exit 91']
for name, address, target_port in container_targets:
    commands.append(f'if timeout 3 nc -w 2 {address} {target_port} </dev/null >/dev/null 2>&1; then echo "{name}=UNEXPECTED_ACCESS"; else echo "{name}=blocked"; fi')
container = run(docker + restrictions + [image, '-c', '; '.join(commands)], timeout=50)
assert container.returncode == 0, container.stderr
assert 'UNEXPECTED_ACCESS' not in container.stdout
assert container.stdout.count('=blocked') == len(container_targets)
listener.close()
public = run(user + ['python3', '-c', 'import socket; s=socket.create_connection(("1.1.1.1",443),timeout=5); s.close(); print("tcp_connected")'], timeout=10)
record = {
    'captured_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'user': account.pw_name, 'uid': account.pw_uid,
    'source_image': image, 'source_image_id': info['Id'], 'rootless_image_id': loaded_info['Id'],
    'image_layers_match': True, 'image_source': 'Existing local root Docker image save/load; no build or registry credential',
    'loopback_control_root_connection_passed': True, 'host_user_probes': host_results,
    'container_limits': limits.stdout.strip(), 'container_network_probes': container.stdout.splitlines(),
    'public_ipv4_tcp_probe': 'connected' if public.returncode == 0 else 'not_connected',
    'ipv4_guard_counters': run(['iptables', '-w', '-L', 'ONTICARDS_PREVIEW', '-n', '-v', '-x']).stdout,
    'ipv6_guard_counters': run(['ip6tables', '-w', '-L', 'ONTICARDS_PREVIEW', '-n', '-v', '-x']).stdout,
    'rootlesskit': run(['pgrep', '-a', '-u', str(account.pw_uid), 'rootlesskit']).stdout.strip(),
    'root_docker_active': run(['systemctl', 'is-active', 'docker']).stdout.strip(),
    'remaining_containers': run(docker + ['ps', '-aq']).stdout.split(),
    'ssh_authorized_keys_created': False, 'pr_builds': 0, 'pr_deployments': 0,
    'limitations': ['No SSH node wiring or forced-command credential authorized yet', 'No PR image/build/test execution', 'IPv6 egress rejected for this UID and subUID range', 'Public proxy DNS and package/registry access are not yet validated', 'Not a VM/hypervisor security boundary'],
}
assert not record['remaining_containers']
(root / 'evidence/runtime-probe.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
