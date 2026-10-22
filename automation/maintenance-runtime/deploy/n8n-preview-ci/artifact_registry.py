#!/usr/bin/env python3
"""Fixed native skopeo transport. Credentials never enter the PR runtime UID."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import time
sys.path.insert(0,'/opt/onticards-preview-controller')
import controller as c

TRUST=Path('/opt/onticards-preview-artifacts')
HOME=Path('/home/onticards-artifact')
REGISTRY='registry-intl.cn-hongkong.aliyuncs.com'
PREFIX=REGISTRY+'/shallopcr/onticards-ci-'

def read_input(limit=128*1024):
    data=b'';deadline=time.monotonic()+8
    while True:
        left=deadline-time.monotonic()
        if left<=0 or not select.select([sys.stdin.buffer],[],[],left)[0]:raise ValueError('bounded_input_timeout')
        part=os.read(sys.stdin.fileno(),min(4096,limit+1-len(data)))
        if not part:break
        data+=part
        if len(data)>limit:raise ValueError('input_size_rejected')
    return data

def copy_snapshot(source,dest,limit):
    # The source's final components are opened without symlink traversal. The
    # private destination is exclusive and inaccessible to source UID 1001.
    parent=os.open(source.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:fd=os.open(source.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
    finally:os.close(parent)
    with os.fdopen(fd,'rb') as src, dest.open('xb') as out:
        metadata=os.fstat(src.fileno())
        if not stat.S_ISREG(metadata.st_mode) or not 0<metadata.st_size<=limit:raise ValueError('source_file_rejected')
        dest.chmod(0o600)
        copied=0
        while True:
            block=src.read(min(1024*1024,limit+1-copied))
            if not block:break
            copied+=len(block)
            if copied>limit:raise ValueError('source_grew_beyond_limit')
            out.write(block)
    if dest.stat().st_size!=metadata.st_size:raise ValueError('source_changed_during_copy')

def main():
    os.umask(0o077)
    config=json.loads((TRUST/'role.json').read_text());role=config['role']
    assert os.getuid()==config['uid'] and os.getuid()!=1001
    hosts=json.loads((c.TRUST/'host-identities.json').read_text())
    assert c.sha('/etc/machine-id')==hosts['build' if role=='publish' else 'test']
    match=re.fullmatch(r'onticards-artifact-v1 (publish|fetch) ([1-9][0-9]{0,6}) ('+c.SHA+r') ('+c.SHA+r') ('+c.DIGEST+r')',os.environ.get('SSH_ORIGINAL_COMMAND',''))
    if not match or match[1]!=role:raise ValueError('fixed_artifact_command_rejected')
    _,identity,_=c.request_from_command(f'onticards-preview-v1 build {match[2]} {match[3]} {match[4]}','build')
    expected=match[5];runs=HOME/'runs';runs.mkdir(mode=0o700,exist_ok=True)
    with (runs/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        root=runs/identity['run_id'];root.mkdir(mode=0o700,exist_ok=True)
        receipt=root/'receipt.json'
        if receipt.exists():print(receipt.read_text());return
        record={'identity':identity,'state':'running','role':role,'started_at':c.now(),'commands':[]}
        receipt.write_text(json.dumps(record));receipt.chmod(0o600)
        auth=HOME/'.config/containers/auth.json'
        assert auth.stat().st_uid==os.getuid() and auth.stat().st_mode & 0o777==0o600
        env={'PATH':'/usr/bin:/bin','HOME':str(HOME),'LC_ALL':'C.UTF-8'}
        # Existing registry direct route was measured independently (0.84 s vs
        # 12.84 s proxy manifest). No global routing/proxy configuration changes.
        def run(args,timeout=1800,capture=False):
            row={'operation':args[1],'started_at':c.now(),'timeout_seconds':timeout};record['commands'].append(row)
            with (root/'skopeo.log').open('a') as output:
                process=subprocess.Popen(args,env=env,stdout=subprocess.PIPE if capture else output,
                                         stderr=output,text=True,start_new_session=True)
                try:stdout,_=process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.communicate()
                    row.update(ended_at=c.now(),timed_out=True,exit_code=process.returncode)
                    raise RuntimeError('bounded_registry_transport_timeout')
                row.update(ended_at=c.now(),timed_out=False,exit_code=process.returncode)
                if process.returncode:raise RuntimeError('native_registry_operation_failed')
                return stdout
        locked=json.loads((c.TRUST/'trusted-images.json').read_text())
        try:
            if role=='publish':
                source=c.TRANSFER/'outbox'/identity['run_id']
                copy_snapshot(source/'manifest.json',root/'manifest.json',128*1024)
                if c.sha(root/'manifest.json')!=expected:raise ValueError('source_manifest_hash_rejected')
                manifest=json.loads((root/'manifest.json').read_text());c.assert_manifest(manifest,identity,locked)
                copy_snapshot(source/'images.tar',root/'images.tar',c.MAX_ARCHIVE)
                if c.sha(root/'images.tar')!=manifest['archive_sha256']:raise ValueError('source_archive_hash_rejected')
                published={}
                for name in ['api','web']:
                    tag=PREFIX+name+':'+identity['run_id'];digestfile=root/(name+'.digest')
                    run(['skopeo','copy','--retry-times','0','--dest-authfile',str(auth),'--digestfile',str(digestfile),
                         'docker-archive:'+str(root/'images.tar')+':'+manifest['images'][name]['tag'],'docker://'+tag])
                    digest=digestfile.read_text().strip()
                    if not re.fullmatch('sha256:'+c.DIGEST,digest):raise ValueError('registry_digest_invalid')
                    raw=run(['skopeo','inspect','--authfile',str(auth),'--raw','docker://'+PREFIX+name+'@'+digest],timeout=60,capture=True)
                    if hashlib.sha256(raw.encode()).hexdigest()!=digest.removeprefix('sha256:'):raise ValueError('registry_digest_readback_mismatch')
                    published[name]=PREFIX+name+'@'+digest
                record.update(state='published',build_manifest=manifest,source_manifest_sha256=expected,registry=published,
                              auth_boundary='single registry entry in private trusted publisher home; not repository-minimal credential')
            else:
                raw=read_input()
                if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('publication_input_hash_rejected')
                publication=json.loads(raw)
                if publication.get('identity')!=identity or publication.get('state')!='published':raise ValueError('publication_identity_rejected')
                manifest=publication['build_manifest'];c.assert_manifest(manifest,identity,locked)
                if set(publication['registry'])!={'api','web'}:raise ValueError('registry_image_scope_rejected')
                destination=c.TRANSFER/'inbox'/identity['run_id'];destination.mkdir(mode=0o750);destination.chmod(0o750)
                archives={}
                for name in ['api','web']:
                    ref=publication['registry'][name]
                    if not re.fullmatch(re.escape(PREFIX+name)+r'@sha256:'+c.DIGEST,ref):raise ValueError('registry_reference_rejected')
                    path=destination/('images-'+name+'.tar')
                    run(['skopeo','copy','--retry-times','0','--src-authfile',str(auth),'docker://'+ref,
                         'docker-archive:'+str(path)+':'+manifest['images'][name]['tag']])
                    if not 0<path.stat().st_size<=c.MAX_ARCHIVE:raise ValueError('download_archive_size_rejected')
                    path.chmod(0o640);archives[name]={'name':path.name,'sha256':c.sha(path),'bytes':path.stat().st_size}
                manifest={**manifest,'archive_kind':'registry-pair','archives':archives,'registry':publication['registry']}
                file=destination/'manifest.json';file.write_text(json.dumps(manifest,indent=2)+'\n');file.chmod(0o640)
                record.update(state='downloaded',manifest_sha256=c.sha(file),registry=publication['registry'],
                              archive_bytes=sum(x['bytes'] for x in archives.values()))
        except Exception as error:
            record.update(state='registry_transport_failed',error_type=type(error).__name__,
                          reason='Trusted operator must inspect private skopeo log; no automatic retry')
        record['ended_at']=c.now();receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

if __name__=='__main__':main()
