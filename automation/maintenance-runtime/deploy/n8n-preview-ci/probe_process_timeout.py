#!/usr/bin/env python3
"""Harmless real child-process timeout probe, no Docker/build/model/PR."""
import json
import os
from pathlib import Path
import tempfile
import time
import controller as c

assert os.geteuid()==1001
with tempfile.TemporaryDirectory(prefix='onticards-timeout-',dir='/home/onticards-preview') as temp:
    c.STATE=Path(temp)
    _,identity,_=c.request_from_command('onticards-preview-v1 build 26 '+('a'*40)+' '+('b'*40),'build')
    execution=c.Execution(identity);execution.stage='harmless_timeout_probe'
    pidfile=execution.root/'child.pid'
    code='import subprocess,time,pathlib; p=subprocess.Popen(["sleep","60"]); pathlib.Path('+repr(str(pidfile))+').write_text(str(p.pid)); time.sleep(60)'
    try:
        execution.run(['python3','-I','-c',code],timeout=1)
        raise AssertionError('Expected bounded timeout')
    except c.OperationTimeout:pass
    pid=int(pidfile.read_text());time.sleep(.2)
    status=Path(f'/proc/{pid}/status')
    state=next((line.split()[1] for line in status.read_text().splitlines() if line.startswith('State:')),None) if status.exists() else None
    assert state in [None,'Z'], 'Timed-out child is still executing'
    print(json.dumps({'probe':'real_process_group_timeout','pass':True,'descendant_alive_executing':False,
                      'remaining_state':state,'commands':execution.commands,'docker_builds':0,'model_calls':0},indent=2))
