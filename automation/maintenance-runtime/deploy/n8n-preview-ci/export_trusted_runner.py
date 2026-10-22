#!/usr/bin/env python3
"""Native save+gzip of the already built trusted browser tester, no PR code."""
import hashlib
import json
from pathlib import Path
import subprocess

root=Path('/opt/onticards-preview-setup')
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()=='67b5d2d3c1ded3fd584d2923367d4fe323d24054ff8ac28267123e5b8c8c28b4'
target=root/'trusted-tests-v1.tar.gz'
with target.open('wb') as output:
    docker=subprocess.Popen(['runuser','-u','onticards-preview','--','env','XDG_RUNTIME_DIR=/run/user/1001',
        'docker','--context','rootless','image','save','onticards-ci-trusted-tests:pw1.64.1-api7-browser2-v1'],stdout=subprocess.PIPE)
    zipped=subprocess.run(['gzip','-1'],stdin=docker.stdout,stdout=output,timeout=600)
    docker.stdout.close();assert docker.wait(timeout=15)==0 and zipped.returncode==0
target.chmod(0o600)
with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
record={'archive_sha256':digest,'bytes':target.stat().st_size,'kind':'trusted-test-runner-only','pr_images':False}
(root/'evidence/trusted-tests-transfer.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
