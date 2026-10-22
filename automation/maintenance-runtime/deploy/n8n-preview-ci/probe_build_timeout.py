#!/usr/bin/env python3
"""A trusted sleep-only BuildKit probe, only on kol; no PR build."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,'/opt/onticards-preview-controller')
import controller as c

assert os.getuid()==1001
assert (c.TRUST/'role').read_text().strip()=='build'
_,identity,_=c.request_from_command('onticards-preview-v1 build 9999998 '+('f'*40)+' '+('e'*40),'build')
with tempfile.TemporaryDirectory(prefix='trusted-build-timeout-',dir='/home/onticards-preview') as temp:
    c.STATE=Path(temp);execution=c.Execution(identity)
    assert not execution.run(execution.docker+['ps','-aq']).stdout.strip()
    context=execution.root/'context';context.mkdir()
    (context/'Dockerfile').write_text('FROM onticards-ci-trusted-tests:pw1.64.1-api7-browser2-v1\nRUN sleep 173\n')
    execution.stage='build_timeout_probe'
    try:
        execution.run(execution.docker+['build','--pull=false','--network=none',str(context)],timeout=5,capture=False)
        raise AssertionError('Expected real BuildKit timeout')
    except c.OperationTimeout:
        execution.stop_build()
    assert execution.cleanup['dedicated_daemon_restart_exit']==0
    assert execution.cleanup['container_probe_exit']==0 and not execution.cleanup['remaining_containers']
    # Native /proc proof for the unique, trusted sleep instruction.
    alive=[]
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                argv=(entry/'cmdline').read_bytes().split(b'\0')
                if argv[:2]==[b'sleep',b'173']:alive.append(int(entry.name))
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
    assert not alive,'Trusted build sleep survived bounded cleanup'
    print(json.dumps({'at':c.now(),'trusted_build_timeout':True,'pr_builds':0,'sleep_processes_remaining':alive,
                      'commands':execution.commands,'cleanup':execution.cleanup},indent=2))
