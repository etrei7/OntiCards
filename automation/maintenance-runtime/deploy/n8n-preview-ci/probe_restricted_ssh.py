#!/usr/bin/env python3
"""Native OpenSSH/SFTP negative probes from the exact trusted CI image/UID."""
import json
from pathlib import Path
import subprocess
import time

root=Path('/opt/onticards-maintenance/preview-ci')
image='registry-intl.cn-hongkong.aliyuncs.com/shallopcr/n8n@sha256:b5b32a81eba912458faf4638b54641d249c959567519a2030a803711d7639663'
docker=['docker','run','--rm','--network','host','--user','1003:1003','--read-only','--tmpfs','/tmp:rw,mode=1777',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '-v',str(root/'secrets')+':/opt/onticards-preview-ci/secrets:ro',
        '-v',str(root/'ssh')+':/opt/onticards-preview-ci/ssh:ro',
        '-v',str(root/'ssh/passwd')+':/etc/passwd:ro','-v',str(root/'ssh/group')+':/etc/group:ro','--entrypoint','sh',image,'-c']
config='/opt/onticards-preview-ci/ssh/config'
def run(command):return subprocess.run(docker+[command],capture_output=True,text=True,timeout=45)
record={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'trusted_image':image,'uid':1003,'probes':[],'pr_workloads':0}
for role in ['build','test']:
    value=run(f'ssh -F {config} -T preview-{role} id')
    passed=value.returncode!=0 and 'rejected_command' in value.stderr
    record['probes'].append({'host_role':role,'arbitrary_command':'rejected','pass':passed})
    if not passed:raise RuntimeError('Fixed command verification failed: '+value.stderr[-1200:])
    value=run(f"printf 'pwd\nls /\n' | sftp -F {config} -b - preview-{role}-transfer")
    passed=value.returncode==0 and 'Remote working directory: /' in value.stdout
    record['probes'].append({'host_role':role,'pinned_sftp':'connected_to_chroot','pass':passed})
    if not passed:raise RuntimeError('SFTP positive control failed: '+value.stderr[-1200:])
    for name,batch in [('outside_chroot','get /../../etc/passwd /tmp/forbidden'),
                       ('write_outbox','put /tmp/synthetic /outbox/forbidden'),
                       ('symlink','symlink /etc/passwd /inbox/forbidden-link')]:
        value=run(f"printf synthetic > /tmp/synthetic; printf '{batch}\n' | sftp -F {config} -b - preview-{role}-transfer")
        passed=value.returncode!=0
        record['probes'].append({'host_role':role,'request':name,'expected':'denied','pass':passed})
        assert passed,'Restricted SFTP operation unexpectedly passed'
value=run(f'ssh -F {config} -o HostKeyAlias=101.47.177.55 -T preview-test id')
passed=value.returncode==255 and ('HOST IDENTIFICATION HAS CHANGED' in value.stderr or 'Host key verification failed' in value.stderr)
record['probes'].append({'request':'wrong_pinned_host_identity','expected':'denied_before_command','pass':passed})
assert passed,'Wrong host identity was not rejected'
out=Path('/opt/onticards-preview-setup/evidence/restricted-ssh-probe.json')
out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
