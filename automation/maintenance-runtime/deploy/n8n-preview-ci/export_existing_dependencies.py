#!/usr/bin/env python3
"""Save existing tested amd64 dependency images, never build on the test host."""
import json
import subprocess
from pathlib import Path
import hashlib
from controller import image_identity

root=Path('/opt/onticards-preview-setup')
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()=='993dd953d413fa7d88b56ebfd19dfc35d40361cd9a370d639279cdbc858856d2'
locked={}
for key,tag,expected in [('db','postgres:15-alpine','sha256:3d0f7584ed7d04e27fa050d6683a74746608faf21f202be78460d679cc56461f'),
                         ('nginx','nginx:1.27-alpine','sha256:91fc9c3924b93f76adc9cd36a0bb93e53885ff8e97df10233caa45bb432789a5')]:
    info=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]
    assert info['Id']==expected and info['Architecture']=='amd64'
    locked[key]={'tag':tag,'identity':image_identity(info)}
archive=root/'preview-amd64-dependencies.tar'
subprocess.run(['docker','image','save','--output',str(archive)]+[v['tag'] for v in locked.values()],check=True,timeout=180)
archive.chmod(0o600)
with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
record={'source':'Existing test-host postgres15/nginx1.27 amd64 images; no build or tag mutation','images':locked,'archive_sha256':digest}
(root/'preview-amd64-dependencies.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'saved_bytes':archive.stat().st_size,'archive_sha256':digest,'builds':0,'root_services_changed':False}))
