#!/usr/bin/env python3
"""Use util-linux nsenter to configure only this user's RootlessKit resolver."""
import json
import os
from pathlib import Path
import pwd
import subprocess

account = pwd.getpwnam('onticards-preview')
assert os.geteuid() == account.pw_uid == 1001
pid = int(Path(f'/run/user/{account.pw_uid}/dockerd-rootless/child_pid').read_text())
assert Path(f'/proc/{pid}').stat().st_uid == account.pw_uid
assert os.readlink(f'/proc/{pid}/ns/mnt') != os.readlink('/proc/self/ns/mnt')
assert os.readlink(f'/proc/{pid}/ns/user') != os.readlink('/proc/self/ns/user')
payload = 'from pathlib import Path; Path("/etc/resolv.conf").write_text("nameserver 1.1.1.1\\nnameserver 8.8.8.8\\noptions timeout:2 attempts:2\\n")'
subprocess.run(['nsenter', '-U', '-m', '-n', '-t', str(pid), '/usr/bin/python3', '-c', payload], check=True)
print(json.dumps({'rootless_namespace_resolver_configured': True, 'host_resolver_modified': False}))
