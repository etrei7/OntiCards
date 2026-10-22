#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import time

assert os.geteuid() == 0
root = Path('/opt/onticards-preview-setup')
account = pwd.getpwnam('onticards-preview')
assert account.pw_uid == 1001
user = ['runuser', '-u', account.pw_name, '--', 'env', 'XDG_RUNTIME_DIR=/run/user/1001', 'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus']
def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, '', 'bounded_probe_timeout')
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
before = {'host_resolver_sha256': sha('/etc/resolv.conf'), 'root_docker_pid':run(['systemctl','show','docker','-p','MainPID','--value']).stdout.strip(), 'rules':run(['iptables','-S','ONTICARDS_PREVIEW']).stdout}
target = Path('/usr/local/lib/onticards-preview-runtime')
target.mkdir(mode=0o755, exist_ok=True)
shutil.copyfile(root/'configure_namespace_dns.py',target/'configure_namespace_dns.py')
(target/'configure_namespace_dns.py').chmod(0o755)
home = Path(account.pw_dir)
config = home/'.config/docker/daemon.json'
config.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
assert not config.exists(), 'Do not overwrite an existing daemon configuration'
config.write_text(json.dumps({'dns':['1.1.1.1','8.8.8.8']})+'\n')
os.chown(config.parent,account.pw_uid,account.pw_gid); os.chown(config,account.pw_uid,account.pw_gid)
dropin = home/'.config/systemd/user/docker.service.d'
dropin.mkdir(mode=0o755,exist_ok=True)
(dropin/'70-onticards-namespace-dns.conf').write_text('[Service]\nExecStartPost=/usr/bin/python3 /usr/local/lib/onticards-preview-runtime/configure_namespace_dns.py\n')
assert not run(user+['docker','--context','rootless','ps','-q']).stdout.strip(), 'Do not interrupt running containers'
assert run(user+['systemctl','--user','daemon-reload']).returncode==0
restart = run(user+['systemctl','--user','restart','docker'])
assert restart.returncode==0, restart.stderr
pid=int(Path('/run/user/1001/dockerd-rootless/child_pid').read_text())
namespace=user+['nsenter','-U','-m','-n','-t',str(pid)]
resolver=run(namespace+['cat','/etc/resolv.conf']).stdout
dns=run(namespace+['getent','ahostsv4','github.com'])
git=run(namespace+['git','-c','http.version=HTTP/1.1','ls-remote','https://github.com/stepll2026/OntiCards.git','refs/heads/main'])
after={'captured_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':'only onticards-preview RootlessKit mount/network namespace and daemon container DNS','resolver':resolver,'host_resolver_unchanged':sha('/etc/resolv.conf')==before['host_resolver_sha256'],'host_resolver_sha256':before['host_resolver_sha256'],'root_docker_pid_unchanged':run(['systemctl','show','docker','-p','MainPID','--value']).stdout.strip()==before['root_docker_pid'],'network_rules_unchanged':run(['iptables','-S','ONTICARDS_PREVIEW']).stdout==before['rules'],'namespace_dns_passed':dns.returncode==0,'native_public_git_exit':git.returncode,'native_public_main_sha':git.stdout.split()[0] if git.returncode==0 and git.stdout else None,'private_network_allowance_added':False,'namespace_helper_sha256':sha(target/'configure_namespace_dns.py')}
assert after['host_resolver_unchanged'] and after['root_docker_pid_unchanged'] and after['network_rules_unchanged']
(root/'evidence/namespace-dns.json').write_text(json.dumps(after,indent=2)+'\n')
print(json.dumps(after,indent=2))
