#!/usr/bin/env python3
"""Build only the trusted test runner on kol; reuse the existing dependency images."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import subprocess
import time
from controller import image_identity

root=Path(__file__).resolve().parent
assert os.geteuid()==0
assert hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()==json.loads((root/'host-identities.json').read_text())['build']
assert pwd.getpwnam('onticards-preview').pw_uid==1001
user=['runuser','-u','onticards-preview','--','env','XDG_RUNTIME_DIR=/run/user/1001','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus']
docker=user+['docker','--host','unix:///run/user/1001/docker.sock']
assert not subprocess.check_output(docker+['ps','-aq'],text=True).strip()
before=subprocess.check_output(['systemctl','show','docker','-p','MainPID','--value'],text=True).strip()
deps={'weaviate':('onticards-maintenance-weaviate:1.36.0-amd64','sha256:a6acdbf5c3b3e163476da5a1dce55f12ebd84f3a026b3b2bd5d77ba4442aacd5')}
existing=json.loads((root/'preview-amd64-dependencies.json').read_text())
archive=root/'preview-amd64-dependencies.tar'
with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==existing['archive_sha256']
with archive.open('rb') as stream:subprocess.run(docker+['load'],stdin=stream,stdout=subprocess.DEVNULL,check=True,timeout=240)
locked=existing['images']
for image in locked.values():
    actual=json.loads(subprocess.check_output(docker+['image','inspect',image['tag']]))[0]
    assert image_identity(actual)==image['identity'] and actual['Architecture']=='amd64'
for name,(tag,expected) in deps.items():
    info=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]
    assert info['Id']==expected and info['Architecture']=='amd64'
    source=subprocess.Popen(['docker','image','save',tag],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    loaded=subprocess.run(docker+['load'],stdin=source.stdout,stdout=subprocess.DEVNULL,timeout=240)
    source.stdout.close();assert source.wait(timeout=10)==0 and loaded.returncode==0
    actual=json.loads(subprocess.check_output(docker+['image','inspect',tag]))[0]
    assert image_identity(info)==image_identity(actual)
    locked[name]={'tag':tag,'identity':image_identity(info)}
test_tag='onticards-ci-trusted-tests:pw1.64.1-api7-browser2-v1'
context=Path('/opt/onticards-preview-tests-context')
context.mkdir(mode=0o755,exist_ok=True)
assert context.stat().st_uid==0 and not context.is_symlink()
for name in ['Dockerfile.tests','requirements.tests.txt','package.json','package-lock.json','test_preview_api.py','test_entry.py','playwright.config.ts','tests/preview.spec.ts']:
    target=context/name;target.parent.mkdir(mode=0o755,exist_ok=True)
    assert not target.is_symlink() and not (root/name).is_symlink()
    shutil.copyfile(root/name,target);target.chmod(0o644)
log=root/'trusted-tests-build.log'
with log.open('w') as output:
    process=subprocess.Popen(docker+['build','--pull=false','--tag',test_tag,'--file',str(context/'Dockerfile.tests'),str(context)],
                             stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    try:code=process.wait(timeout=2400)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
        subprocess.run(user+['systemctl','--user','restart','docker'],check=True,timeout=45)
        raise RuntimeError('Trusted runner build timed out; dedicated builder restarted')
log.chmod(0o600)
if code:
    subprocess.run(user+['systemctl','--user','restart','docker'],check=True,timeout=45)
    raise RuntimeError('Trusted runner build failed; restricted log retained')
info=json.loads(subprocess.check_output(docker+['image','inspect',test_tag]))[0]
assert info['Config']['User']=='pwuser'
locked['tests']={'tag':test_tag,'identity':image_identity(info)}
(root/'trusted-images.json').write_text(json.dumps(locked,indent=2)+'\n')
assert subprocess.check_output(['systemctl','show','docker','-p','MainPID','--value'],text=True).strip()==before
print(json.dumps({'trusted_runner_built_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'pr_builds':0,
                  'test_image_id':info['Id'],'lock_sha256':hashlib.sha256((root/'trusted-images.json').read_bytes()).hexdigest(),
                  'root_docker_unchanged':True,'image_user':info['Config']['User']}))
