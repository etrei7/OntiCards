#!/usr/bin/env python3
"""Credential-free probe of the native rootless network; never calls a supplier."""
import json
import os
from pathlib import Path
import subprocess
import time

assert os.getuid()==0
root=Path('/opt/onticards-preview-setup')
user=['runuser','-u','onticards-preview','--']
docker=user+['docker','--host','unix:///run/user/1001/docker.sock']
image='redis:7-alpine'
names=['onticards-preview-probe-internal','onticards-preview-probe-egress']
def run(args,timeout=20):return subprocess.run(args,capture_output=True,text=True,timeout=timeout)
assert not run(docker+['ps','-aq']).stdout.strip()
before=run(['systemctl','show','docker','-p','MainPID','--value']).stdout.strip()
result={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'suppliers_called':0,'credentials_used':False,
        'representative_container':'existing trusted redis alpine, cap_drop ALL, no_new_privileges, read_only',
        'probes':[]}
try:
    for name in names:
        args=['network','create']+(['--internal'] if name.endswith('internal') else [])+[name]
        assert run(docker+args).returncode==0
    def probe(network,command):
        return run(docker+['run','--rm','--network',network,'--user','1000:1000','--read-only','--cap-drop','ALL',
                           '--security-opt','no-new-privileges:true','--pids-limit','32','--memory','64m',
                           '--entrypoint','sh',image,'-c',command])
    response=probe(names[1],"wget -S -O /dev/null -T 5 --user-agent=onticards-rootless-model-route-probe --post-data='{}' http://10.66.66.5:18134/v1/chat/completions")
    output=response.stdout+response.stderr
    assert '401 Unauthorized' in output, 'Expected credential-free 401 route response'
    result['probes'].append({'network':'model-egress','destination':'10.66.66.5:18134','expected':401,'actual':401,'pass':True})
    positive=probe(names[1],'nc -z -w 2 10.66.66.5 18134')
    assert positive.returncode==0, 'TCP probe command must pass the allowed positive control'
    for host,port in [('10.66.66.5',3000),('10.66.66.5',9922),('127.0.0.1',18134),('169.254.169.254',80),
                      ('100.100.100.200',80),('10.66.66.1',80),('1.1.1.1',443),('101.47.177.55',22)]:
        value=probe(names[1],f'nc -z -w 2 {host} {port}')
        passed=value.returncode!=0
        result['probes'].append({'network':'model-egress','destination':f'{host}:{port}','expected':'blocked','pass':passed})
        assert passed, 'Unexpected egress allowed'
    value=probe(names[0],'nc -z -w 2 10.66.66.5 18134')
    result['probes'].append({'network':'internal-only','destination':'10.66.66.5:18134','expected':'blocked','pass':value.returncode!=0})
    assert value.returncode!=0, 'Internal-only container obtained egress'
finally:
    cleanup=[run(docker+['network','rm',name]).returncode for name in names]
    result['cleanup']={'network_remove_exit':cleanup,'remaining_containers':run(docker+['ps','-aq']).stdout.split()}
    result['root_docker_pid_unchanged']=run(['systemctl','show','docker','-p','MainPID','--value']).stdout.strip()==before
    (root/'evidence/model-egress-probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
