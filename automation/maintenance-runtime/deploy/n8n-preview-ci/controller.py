#!/usr/bin/env python3
"""Fixed SSH adapter to native Git, rootless Docker/Compose and existing tests.

Installed root-owned; never loaded from the PR. No scheduler or GitHub credential.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import signal
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time

TRUST = Path('/opt/onticards-preview-controller')
STATE = Path('/home/onticards-preview/runs')
TRANSFER = Path('/opt/onticards-preview-transfer-root')
REPO = 'https://github.com/stepll2026/OntiCards.git'
SHA = r'[0-9a-f]{40}'
DIGEST = r'[0-9a-f]{64}'
MAX_ARCHIVE = 12 * 1024 ** 3

def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())

class OperationFailed(RuntimeError):
    pass

class OperationTimeout(OperationFailed):
    pass

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',',':')).encode()

def request_from_command(command, role):
    if role not in {'build','test'}:
        raise ValueError('invalid_host_role')
    match = re.fullmatch(r'onticards-preview-v1 (build|test|test-model) ([1-9][0-9]{0,6}) ('+SHA+r') ('+SHA+r')(?: ('+DIGEST+r'))?',command)
    if not match:
        raise ValueError('rejected_command')
    action, pr, head, base, manifest = match.groups()
    if (action == 'build') != (role == 'build') or action.startswith('test') != bool(manifest):
        raise ValueError('rejected_role_or_manifest')
    identity = {'repository':'stepll2026/OntiCards','pr':int(pr),'head':head,'base':base,'contract':'preview-v1'}
    identity['run_id'] = hashlib.sha256(canonical(identity)).hexdigest()[:24]
    return action, identity, manifest

def validate_model_lease(lease,identity,timestamp=None):
    timestamp=time.time() if timestamp is None else timestamp
    expected=set(identity)|{'token_id','expires_at','base_url','model','embedding_model','api_key'}
    if set(lease)!=expected or any(lease.get(k)!=v for k,v in identity.items()):raise ValueError('lease_identity_rejected')
    if (type(lease['expires_at'])!=int or not timestamp+120<lease['expires_at']<=timestamp+901
        or type(lease['token_id'])!=int or lease['token_id']<=0
        or lease['base_url']!='http://10.66.66.5:18134/v1'
        or lease['model']!='onticards-preview-qwen3.8-max-0902'
        or lease['embedding_model']!='onticards-preview-qwen3.7-text-embedding-flash'
        or not re.fullmatch(r'sk-[A-Za-z0-9_-]{16,128}',lease['api_key'])):raise ValueError('lease_scope_or_expiry_rejected')

def read_model_lease(identity):
    data=b'';deadline=time.monotonic()+8
    while True:
        left=deadline-time.monotonic()
        if left<=0 or not select.select([sys.stdin.buffer],[],[],left)[0]:raise ValueError('lease_input_timeout')
        part=os.read(sys.stdin.fileno(),min(1024,4097-len(data)))
        if not part:break
        data+=part
        if len(data)>4096:raise ValueError('lease_input_too_large')
    lease=json.loads(data);validate_model_lease(lease,identity);return lease

def image_identity(info):
    # Docker 28 config ID and Docker 29 OCI image ID differ after save/load.
    # Their inspect responses also omit/present empty optional Config fields.
    config=dict(info['Config'])
    for key,default in {'Labels':{},'OnBuild':[],'User':'','Env':[],'Entrypoint':[],'Cmd':[],
                         'ExposedPorts':{},'Volumes':{},'WorkingDir':'','StopSignal':'','ArgsEscaped':False}.items():
        if config.get(key) is None:config[key]=default
    return {'config_sha256':hashlib.sha256(canonical(config)).hexdigest(),
            'layers':info['RootFS']['Layers'],'os':info['Os'],'architecture':info['Architecture']}

def validate_remote_pr(data, identity):
    if (data.get('state')!='open' or data.get('head',{}).get('repo',{}).get('full_name')!='stepll2026/OntiCards'
        or data.get('base',{}).get('repo',{}).get('full_name')!='stepll2026/OntiCards'
        or data.get('base',{}).get('ref')!='main' or not data.get('head',{}).get('ref','').startswith('codex/')
        or data.get('head',{}).get('sha')!=identity['head'] or data.get('base',{}).get('sha')!=identity['base']):
        raise ValueError('remote_pr_scope_or_revision_rejected')

def assert_manifest(data, identity, trusted_images):
    if data.get('identity') != identity or data.get('state') != 'built':
        raise ValueError('manifest_identity_mismatch')
    if set(data.get('images',{})) != {'api','web','db','weaviate','nginx','tests'}:
        raise ValueError('manifest_image_scope_mismatch')
    if not re.fullmatch(DIGEST,data.get('archive_sha256','')) or not 0 < data.get('archive_bytes',0) <= MAX_ARCHIVE:
        raise ValueError('manifest_archive_invalid')
    if data.get('archive_kind') not in {None,'registry-pair'}:
        raise ValueError('manifest_archive_kind_rejected')
    if data.get('archive_kind')=='registry-pair':
        if set(data.get('archives',{}))!={'api','web'} or set(data.get('registry',{}))!={'api','web'}:
            raise ValueError('manifest_registry_scope_rejected')
        for key,archive in data['archives'].items():
            if (archive.get('name')!=f'images-{key}.tar' or not re.fullmatch(DIGEST,archive.get('sha256',''))
                or not 0<archive.get('bytes',0)<=MAX_ARCHIVE
                or not re.fullmatch(re.escape('registry-intl.cn-hongkong.aliyuncs.com/shallopcr/onticards-ci-'+key)+r'@sha256:'+DIGEST,data['registry'][key])):
                raise ValueError('manifest_registry_archive_rejected')
    for key in ['db','weaviate','nginx','tests']:
        if data['images'][key] != trusted_images[key]:
            raise ValueError('trusted_image_mismatch')
    for key in ['api','web']:
        if data['images'][key]['tag'] != f'onticards-ci-{key}:{identity["run_id"]}':
            raise ValueError('candidate_image_tag_mismatch')

def compose_spec(identity, images, environment, fixture):
    common = {'pull_policy':'never','restart':'no','security_opt':['no-new-privileges:true'],
              'cap_drop':['ALL'],'pids_limit':256,'cpus':1,'networks':['preview']}
    def service(name, **values):
        return {**common,'image':images[name],**values}
    health = lambda cmd: {'test':cmd,'interval':'5s','timeout':'4s','retries':36,'start_period':'20s'}
    services = {
        'onticards-db':service('db',mem_limit='256m',cap_add=['CHOWN','DAC_OVERRIDE','FOWNER','SETUID','SETGID'],
            environment={'POSTGRES_USER':'postgres','POSTGRES_PASSWORD':environment['DB_PASSWORD'],'POSTGRES_DB':'onticards_preview'},
            volumes=['db:/var/lib/postgresql/data'],healthcheck=health(['CMD','pg_isready','-U','postgres','-d','onticards_preview'])),
        'onticards-weaviate':service('weaviate',mem_limit='512m',
            command=['--host','0.0.0.0','--port','8080','--scheme','http'],
            environment={'AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED':'true','PERSISTENCE_DATA_PATH':'/var/lib/weaviate','ENABLE_API_BASED_MODULES':'false','CLUSTER_HOSTNAME':'node1','GRPC_PORT':'50051'},
            volumes=['weaviate:/var/lib/weaviate'],healthcheck=health(['CMD-SHELL','wget -qO- http://127.0.0.1:8080/v1/.well-known/ready >/dev/null'])),
        'onticards_api':service('api',mem_limit='1024m',environment=environment,networks=['preview','model-egress'],
            volumes=['reports:/data/governance/reports',f'{fixture}:/tmp/onticards-maintenance-fixture.sqlite:ro'],
            depends_on={x:{'condition':'service_healthy'} for x in ['onticards-db','onticards-weaviate']},
            healthcheck=health(['CMD','curl','--fail','--silent','http://127.0.0.1:9103/healthz'])),
        'onticards_web':service('web',mem_limit='512m',read_only=True,tmpfs=['/tmp'],
            environment={'PORT':'3000','HOSTNAME':'0.0.0.0','DEPLOY_ENV':'TEST'},
            healthcheck=health(['CMD','node','-e',"fetch('http://127.0.0.1:3000/login').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"])),
        'onticards_nginx':service('nginx',mem_limit='64m',cap_add=['CHOWN','DAC_OVERRIDE','SETUID','SETGID'],
            environment={'NGINX_SERVER_NAME':'_','NGINX_ENVSUBST_FILTER':'^NGINX_SERVER_NAME$'},
            volumes=[f'{TRUST}/nginx.conf:/etc/nginx/templates/default.conf.template:ro'],
            depends_on={x:{'condition':'service_healthy'} for x in ['onticards_api','onticards_web']}),
        'tests':service('tests',mem_limit='1024m',init=True,user='1001:1001',read_only=True,
            cap_add=['SYS_CHROOT'],
            tmpfs=['/tmp:rw,mode=1777'],shm_size='256m',volumes=['test-results:/results'],
            security_opt=['no-new-privileges:true',f'seccomp={TRUST}/playwright-seccomp.json'],
            environment={'ONTICARDS_PREVIEW_URL':'http://onticards_nginx:9107','ONTICARDS_RUN_ID':identity['run_id'],
                'ONTICARDS_TASK_ID':f'PR-{identity["pr"]}','ONTICARDS_TESTED_HEAD_SHA':identity['head'],
                'ONTICARDS_TESTED_BASE_SHA':identity['base'],'ONTICARDS_WEB_HEAD_SHA':identity['head']},profiles=['tests']),
    }
    return {'name':'oci-'+identity['run_id'],'services':services,
            'networks':{'preview':{'internal':True},'model-egress':{'internal':False}},
            'volumes':{name:{} for name in ['db','weaviate','reports','test-results']}}

class Execution:
    def __init__(self, identity,model=False):
        self.identity=identity
        self.model=model
        self.output_id=identity['run_id']+('-model' if model else '')
        self.root=STATE/self.output_id
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/home/onticards-preview','XDG_RUNTIME_DIR':'/run/user/1001',
                  'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1001/bus',
                  'DOCKER_HOST':'unix:///run/user/1001/docker.sock','DOCKER_BUILDKIT':'1',
                  'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0','LC_ALL':'C.UTF-8'}
        self.docker=['docker','--host','unix:///run/user/1001/docker.sock']
        self.commands=[]
        self.stage='preflight'
        self.tests_started=False
        self.cleanup={}
        self.started_at=now()

    def run(self,args,*,timeout=120,check=True,capture=True,file_limit=64*1024**2,input=None):
        import resource
        record={'stage':self.stage,'program':Path(args[0]).name,'timeout_seconds':timeout,'started_at':now()}
        self.commands.append(record)
        def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(file_limit,file_limit))
        log=None if capture else (self.root/'execution.log').open('a')
        try:
            process=subprocess.Popen(args,env=self.env,stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,stdout=subprocess.PIPE if capture else log,
                stderr=subprocess.PIPE if capture else subprocess.STDOUT,text=True,start_new_session=True,preexec_fn=limits)
            try:
                stdout,stderr=process.communicate(input=input,timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.communicate(timeout=5)
                # Child clients/SSH helpers share this session. Do not leave descendants.
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                record.update({'ended_at':now(),'exit_code':process.returncode,'timed_out':True,'process_group_signalled':['SIGTERM','SIGKILL']})
                raise OperationTimeout('bounded_operation_timeout')
            result=subprocess.CompletedProcess(args,process.returncode,stdout,stderr)
            record.update({'ended_at':now(),'exit_code':result.returncode,'timed_out':False})
        finally:
            if log:log.close()
        if check and result.returncode:
            raise OperationFailed('fixed_command_failed; see restricted execution.log')
        return result

    def stop_build(self):
        # Docker BuildKit cancellation after client loss is not assumed. Restart only
        # the new dedicated user daemon, under its exclusive execution lock.
        self.stage='cancel_dedicated_builder'
        restarted=self.run(['systemctl','--user','restart','docker'],timeout=45,check=False,capture=False)
        probe=self.run(self.docker+['ps','-aq'],timeout=20,check=False)
        self.cleanup={'dedicated_daemon_restart_exit':restarted.returncode,'container_probe_exit':probe.returncode,
                      'remaining_containers':probe.stdout.split() if probe.returncode==0 else None,
                      'shared_root_docker_touched':False}

    def cleanup_compose(self,command,test_name):
        self.stage='compose_cleanup'
        attempts=[]
        for attempt in range(2):
            try:
                self.run(self.docker+['rm','-f',test_name],timeout=30,check=False)
            except OperationFailed:pass
            try:
                # Compose excludes profile-only resources unless that profile is enabled.
                down=self.run(command+['--profile','tests','down','--volumes','--remove-orphans','--timeout','15'],timeout=90,check=False,capture=False)
                label='label=com.docker.compose.project=oci-'+self.output_id
                remaining=self.run(self.docker+['ps','-aq','--filter',label],timeout=20,check=False)
                volumes=self.run(self.docker+['volume','ls','-q','--filter',label],timeout=20,check=False)
                record={'compose_down_exit':down.returncode,'container_probe_exit':remaining.returncode,'volume_probe_exit':volumes.returncode,
                    'remaining_project_containers':remaining.stdout.split() if remaining.returncode==0 else None,
                    'remaining_project_volumes':volumes.stdout.split() if volumes.returncode==0 else None}
                attempts.append(record)
                self.cleanup={'attempts':attempts,'shared_root_docker_touched':False}
                if down.returncode==remaining.returncode==volumes.returncode==0 and not remaining.stdout.strip() and not volumes.stdout.strip():return
            except OperationFailed:
                attempts.append({'cleanup_operation_failed_or_timed_out':True})
            if attempt==0:
                try:self.run(['systemctl','--user','restart','docker'],timeout=45,check=False,capture=False)
                except OperationFailed:pass
        self.cleanup={'attempts':attempts,'shared_root_docker_touched':False}
        raise OperationFailed('preview_cleanup_incomplete')

    def package_results(self,result,result_dir):
        self.stage='package_results'
        result={**result,'cleanup':self.cleanup,'started_at':self.started_at,'ended_at':now()}
        out=TRANSFER/'outbox'/self.output_id;out.mkdir(mode=0o750)
        selected=[]
        for file in result_dir.rglob('*'):
            relative=file.relative_to(result_dir).as_posix()
            if file.is_symlink():raise ValueError('result_symlink_rejected')
            if file.is_file() and (relative in {'checks.json','api.xml','boundary.json','browser/results.xml','browser/results.json'} or (relative.startswith('browser/test-results/') and file.suffix=='.png')
                or (relative.startswith('browser/html/data/') and file.suffix=='.png')
                or (self.model and relative.startswith('product/') and file.suffix in {'.json','.pdf','.docx','.xlsx','.md'})):
                selected.append(file)
        if sum(x.stat().st_size for x in selected)>100*1024**2:raise ValueError('result_size_limit')
        result_path=out/'result.json';result_path.write_text(json.dumps(result,indent=2)+'\n');result_path.chmod(0o640)
        archive=out/'evidence.tar'
        with tarfile.open(archive,'w') as bundle:
            bundle.add(result_path,arcname='result.json',recursive=False)
            for file in sorted(selected):bundle.add(file,arcname=file.relative_to(result_dir).as_posix(),recursive=False)
        archive.chmod(0o640)
        return {**result,'result_sha256':sha(result_path),'evidence_sha256':sha(archive),'evidence_files':len(selected)+1}

    def inspect(self,tag):
        return json.loads(self.run(self.docker+['image','inspect',tag]).stdout)[0]

    def namespace(self):
        pid=int(Path('/run/user/1001/dockerd-rootless/child_pid').read_text())
        assert Path(f'/proc/{pid}').stat().st_uid==1001
        return ['nsenter','-U','-m','-n','-t',str(pid)]

    def git(self,args,timeout=900):
        return self.run(self.namespace()+['git','-c','http.version=HTTP/1.1','-c','core.hooksPath=/dev/null',
                         '-c','core.fsmonitor=false','-c','credential.helper=','-c','protocol.file.allow=never']+args,timeout=timeout)

    def build(self,locked):
        self.stage='source_scope_verification'
        if shutil.disk_usage(self.root).free < 20*1024**3:
            raise RuntimeError('insufficient_free_disk')
        pid=int(Path('/run/user/1001/dockerd-rootless/child_pid').read_text())
        probe='import urllib.request,json; print(urllib.request.urlopen(urllib.request.Request('+repr('https://api.github.com/repos/stepll2026/OntiCards/pulls/'+str(self.identity['pr']))+',headers={"User-Agent":"onticards-fixed-preview-v1"}),timeout=30).read().decode())'
        remote=self.run(['nsenter','-U','-m','-n','-t',str(pid),'python3','-I','-c',probe],timeout=45)
        validate_remote_pr(json.loads(remote.stdout),self.identity)
        self.stage='git_fetch'
        source=self.root/'source'
        self.git(['init','--',str(source)])
        self.git(['-C',str(source),'fetch','--no-tags','--depth=1',REPO,
            f'+refs/pull/{self.identity["pr"]}/head:refs/heads/candidate','+refs/heads/main:refs/heads/base'])
        for ref,expected in [('candidate',self.identity['head']),('base',self.identity['base'])]:
            if self.git(['-C',str(source),'rev-parse',ref]).stdout.strip()!=expected:
                raise ValueError('remote_head_or_base_changed')
        self.git(['-C',str(source),'checkout','--detach',self.identity['head']])
        self.git(['-C',str(source),'fsck','--no-reflogs'])
        tree=self.git(['-C',str(source),'rev-parse','HEAD^{tree}']).stdout.strip()
        images=dict(locked)
        for key,directory in [('api','OntiCards_Api'),('web','OntiCards_Web')]:
            self.stage='build_'+key
            tag=f'onticards-ci-{key}:{self.identity["run_id"]}'
            context=source/directory
            if context.is_symlink() or not context.is_dir() or (context/'Dockerfile').is_symlink():
                raise ValueError('invalid_build_context')
            # BuildKit's registry auth provider runs in the native CLI, so it too
            # needs the existing isolated public resolver; never allow host DNS.
            self.run(self.namespace()+self.docker+['build','--pull=false','--network=default','--build-arg',f'COMMIT_SHA={self.identity["head"]}',
                '--label',f'org.opencontainers.image.revision={self.identity["head"]}',
                '--label',f'org.onticards.preview.base={self.identity["base"]}','--tag',tag,str(context)],timeout=2400,capture=False)
            images[key]={'tag':tag,'identity':image_identity(self.inspect(tag))}
        for key in ['db','weaviate','nginx','tests']:
            if image_identity(self.inspect(images[key]['tag']))!=images[key]['identity']:
                raise ValueError('trusted_image_changed')
        out=TRANSFER/'outbox'/self.identity['run_id'];out.mkdir(mode=0o750)
        archive=out/'images.tar'
        self.stage='save_images'
        self.run(self.docker+['image','save','--output',str(archive)]+[images[k]['tag'] for k in sorted(images)],timeout=600,capture=False,file_limit=MAX_ARCHIVE)
        if not 0 < archive.stat().st_size <= MAX_ARCHIVE:
            raise ValueError('archive_size_limit')
        manifest={'identity':self.identity,'state':'built','source_tree':tree,'images':images,'archive_sha256':sha(archive),
                  'archive_bytes':archive.stat().st_size,'created_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        path=out/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
        for file in [archive,path]:file.chmod(0o640)
        return {'state':'built','identity':self.identity,'manifest_sha256':sha(path),'archive_sha256':manifest['archive_sha256']}

    def test(self,locked,expected_manifest,lease=None):
        self.stage='verify_transfer'
        inbox=TRANSFER/'inbox'/self.identity['run_id']
        # Copy through descriptors with O_NOFOLLOW; never extract a caller-provided source archive.
        def transfer_file(name,limit):
            parent=os.open(inbox,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
            finally:os.close(parent)
            with os.fdopen(fd,'rb') as src, (self.root/name).open('xb') as dest:
                import stat
                if not stat.S_ISREG(os.fstat(src.fileno()).st_mode) or not 0 < os.fstat(src.fileno()).st_size <= limit:
                    raise ValueError('invalid_transfer_file')
                shutil.copyfileobj(src,dest)
        transfer_file('manifest.json',128*1024)
        if sha(self.root/'manifest.json')!=expected_manifest:
            raise ValueError('manifest_digest_mismatch')
        data=json.loads((self.root/'manifest.json').read_text());assert_manifest(data,self.identity,locked)
        archives=list(data['archives'].values()) if data.get('archive_kind')=='registry-pair' else [
            {'name':'images.tar','sha256':data['archive_sha256'],'bytes':data['archive_bytes']}]
        for archive in archives:
            transfer_file(archive['name'],MAX_ARCHIVE)
            file=self.root/archive['name']
            if sha(file)!=archive['sha256'] or file.stat().st_size!=archive['bytes']:
                raise ValueError('archive_digest_mismatch')
        self.stage='load_images'
        for archive in archives:
            self.run(self.docker+['load','--input',str(self.root/archive['name'])],timeout=600,capture=False)
        self.stage='verify_loaded_images'
        images={}
        for key,image in data['images'].items():
            info=self.inspect(image['tag'])
            if image_identity(info)!=image['identity']:
                raise ValueError('loaded_image_identity_mismatch')
            images[key]=info['Id']
        environment={'TZ':'Asia/Shanghai','DEPLOY_ENV':'TEST','DB_USERNAME':'postgres','DB_PASSWORD':secrets.token_urlsafe(32),
            'DB_DATABASE':'onticards_preview','DB_HOST':'onticards-db','DB_PORT':'5432',
            'SECRET_KEY':secrets.token_hex(32),'SSO_SECRET_KEY':secrets.token_hex(32),'CONNECT_INFO_MASTER_KEY':secrets.token_hex(32),
            'PUBLIC_BASE_URL':'http://onticards_nginx:9107','ALLOWED_ORIGINS':'http://onticards_nginx:9107',
            'COMPOSE_MANAGED_ENV':'1','DIFY_PORT':'9103','PORT':'9103','RUN_DB_MIGRATION':'true',
            'WEAVIATE_URL':'http://onticards-weaviate:8080','GRPC_PORT':'50051','GOVERNANCE_EXPORT_PATH':'/data/governance/reports',
            'GUNICORN_WORKERS':'1','GUNICORN_THREADS':'4','LOG_LEVEL':'WARNING','GUNICORN_LOG_LEVEL':'warning',
            # Reuse the existing .env.prod/gunicorn.py settings: core.env.get
            # currently raises for a missing key before applying its default.
            'GUNICORN_WORKER_CLASS':'gthread','GUNICORN_WORKER_CONNECTIONS':'200','GUNICORN_TIMEOUT':'28800',
            'GUNICORN_GRACEFUL_TIMEOUT':'30','GUNICORN_MAX_REQUESTS':'1000','GUNICORN_MAX_REQUESTS_JITTER':'100',
            'WORKER_MEMORY_LIMIT_MB':'800','GUNICORN_WORKER_MEMORY_LIMIT_AUTO':'0','CONTAINER_MEMORY_MB':'1024',
            'LOG_ROTATE_BYTES':'10485760','LOG_ROTATE_BACKUPS':'2'}
        fixture=self.root/'fixture.sqlite'
        with sqlite3.connect(fixture) as db:
            db.execute('CREATE TABLE maintenance_orders (order_id INTEGER PRIMARY KEY, region TEXT NOT NULL, amount NUMERIC NOT NULL)')
            db.executemany('INSERT INTO maintenance_orders VALUES(?,?,?)',[(1,'North',120),(2,'South',80),(3,'North',50)])
        fixture.chmod(0o444)
        spec=compose_spec(self.identity,images,environment,fixture)
        spec['name']='oci-'+self.output_id
        scripts=['test_entry.py']
        if self.model:
            validate_model_lease(lease,self.identity)
            scripts.append('exercise-product-flow.py')
            spec['services']['tests']['environment']['ONTICARDS_MODEL_TEST']='1'
        spec['services']['tests']['volumes'] += [f'{TRUST}/{name}:/trusted-bundle/{name}:ro' for name in scripts]
        spec['services']['tests']['entrypoint']=['python','/trusted-bundle/test_entry.py']
        self.trusted_script_hashes={name:sha(TRUST/name) for name in scripts}
        compose=self.root/'compose.json';compose.write_text(json.dumps(spec));compose.chmod(0o600)
        command=self.docker+['compose','--file',str(compose),'--project-name','oci-'+self.output_id]
        test_name='oci-'+self.output_id+'-tests'
        result_dir=self.root/'test-results';result_dir.mkdir()
        failure_stage=None
        try:
            self.stage='compose_startup'
            self.run(command+['up','--detach','--no-build','--pull','never','--wait','--wait-timeout','240'],timeout=300,capture=False)
            boundary=[]
            def capture_boundary(container):
                info=json.loads(self.run(self.docker+['inspect',container]).stdout)[0]
                env_names={x.split('=',1)[0] for x in info['Config'].get('Env',[])}
                boundary.append({'service':info['Config'].get('Labels',{}).get('com.docker.compose.service'),'image_id':info['Image'],
                    'user':info['Config'].get('User'),'network_mode':info['HostConfig']['NetworkMode'],
                    'privileged':info['HostConfig']['Privileged'],'cap_add':info['HostConfig'].get('CapAdd'),
                    'cap_drop':info['HostConfig'].get('CapDrop'),'security_opt':info['HostConfig'].get('SecurityOpt'),
                    'readonly_rootfs':info['HostConfig']['ReadonlyRootfs'],
                    'mounts':[{'destination':x['Destination'],'rw':x['RW'],'type':x['Type']} for x in info['Mounts']],
                    'long_lived_key_or_ssh_env_present':bool(env_names&{'DASHSCOPE_API_KEY','GITHUB_TOKEN','GH_TOKEN','SSH_AUTH_SOCK'}),
                    'docker_socket_mounted':any('docker.sock' in x['Destination'] for x in info['Mounts'])})
            for container in self.run(command+['ps','-q']).stdout.split():capture_boundary(container)
            self.stage='existing_api7_model_flow_and_browser3' if self.model else 'existing_api7_and_non_model_browser2'
            self.tests_started=True
            if self.model:validate_model_lease(lease,self.identity)
            tested=self.run(command+['run','--no-deps','-T','--interactive','--name',test_name,'tests'],timeout=600,check=False,capture=False,
                input=json.dumps(lease) if self.model else None)
            self.stage='collect_results'
            capture_boundary(test_name)
            (result_dir/'boundary.json').write_text(json.dumps({'time':now(),'identity':self.identity,'containers':boundary},indent=2)+'\n')
            self.run(self.docker+['cp',test_name+':/results/.',str(result_dir)],check=False)
            if tested.returncode==0:
                verify_test_results(result_dir,self.model)
            else:
                self.run(command+['logs','--no-color','--tail','120'],timeout=30,check=False,capture=False)
            state=('tests_passed_model_business' if self.model else 'tests_passed_partial_model_unverified') if tested.returncode==0 else 'tests_failed'
            result={'identity':self.identity,'state':state,'test_exit':tested.returncode,'source_tree':data['source_tree'],
                'build_manifest_sha256':expected_manifest,'images':data['images'],'model_business_test':'real_chat_embedding_flow' if self.model else 'not_run_in_non_model_phase',
                'trusted_script_hashes':getattr(self,'trusted_script_hashes',{}),
                'results_directory':str(result_dir),'commands':self.commands}
        except Exception:
            failure_stage=self.stage
            self.stage='collect_failure_logs'
            try:self.run(command+['logs','--no-color','--tail','120'],timeout=30,check=False,capture=False)
            except OperationFailed:pass
            raise
        finally:
            self.cleanup_compose(command,test_name)
            if failure_stage:self.stage=failure_stage
        return self.package_results(result,result_dir)

def verify_test_results(directory,model=False):
    import xml.etree.ElementTree as ET
    checks=json.loads((directory/'checks.json').read_text())
    expected={'api_exit':0,'api_tests':7,'browser_exit':0,'browser_expected':3 if model else 2,'browser_unexpected':0,'browser_skipped':0}
    if any(checks.get(k)!=v for k,v in expected.items()):
        raise ValueError('test_checks_incomplete_or_failed')
    suite=ET.parse(directory/'api.xml').getroot().find('testsuite')
    if suite is None or any(int(suite.attrib.get(k,-1))!=v for k,v in {'tests':7,'errors':0,'failures':0,'skipped':0}.items()):
        raise ValueError('api_machine_report_incomplete_or_failed')
    stats=json.loads((directory/'browser/results.json').read_text())['stats']
    if any(stats.get(k)!=v for k,v in {'expected':3 if model else 2,'unexpected':0,'skipped':0}.items()):
        raise ValueError('browser_machine_report_incomplete_or_failed')
    # Playwright's successful body attachments are materialized by its native
    # HTML reporter in html/data; screenshot-on-failure uses test-results.
    screenshots=list((directory/'browser/test-results').rglob('*.png'))+list((directory/'browser/html/data').glob('*.png'))
    if not (directory/'browser/results.xml').is_file() or not screenshots:
        raise ValueError('browser_artifacts_missing')
    for file in screenshots:
        if file.is_symlink() or not 8<file.stat().st_size<=10*1024**2:
            raise ValueError('browser_screenshot_invalid')
        with file.open('rb') as png:
            if png.read(8)!=b'\x89PNG\r\n\x1a\n':raise ValueError('browser_screenshot_invalid')
    if model:
        flow=json.loads((directory/'product/flow-summary.json').read_text())
        required={'extract-schema','query-total','governance-execute','export-xlsx','export-docx','export-md','export-pdf'}
        if not required.issubset({x['step'] for x in flow['steps'] if x['status']==x['code']==200}):raise ValueError('model_product_evidence_incomplete')
        for suffix in ['xlsx','docx','md','pdf']:
            if (directory/('product/quality-report.'+suffix)).stat().st_size<=100:raise ValueError('model_export_missing')

def main():
    import fcntl
    if os.getuid()!=1001:
        raise RuntimeError('dedicated_nonroot_account_required')
    role=(TRUST/'role').read_text().strip()
    host_identities=json.loads((TRUST/'host-identities.json').read_text())
    if sha('/etc/machine-id')!=host_identities.get(role):
        raise RuntimeError('host_role_mismatch')
    action,identity,manifest=request_from_command(os.environ.get('SSH_ORIGINAL_COMMAND',''),role)
    locked=json.loads((TRUST/'trusted-images.json').read_text())
    if set(locked)!={'db','weaviate','nginx','tests'} or not all(v.get('identity') for v in locked.values()):
        raise RuntimeError('trusted_image_lock_incomplete')
    STATE.mkdir(mode=0o700,exist_ok=True)
    with (STATE/'.execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        execution=Execution(identity,model=action=='test-model');receipt=execution.root/'receipt.json'
        if receipt.exists():
            # Same head/base never silently gets a fresh attempt after failure or crash.
            print(receipt.read_text());return
        started_at=now()
        result={'identity':identity,'state':'running','action':action,'started_at':started_at}
        receipt.write_text(json.dumps(result));receipt.chmod(0o600)
        try:
            info=json.loads(execution.run(execution.docker+['info','--format','{{json .}}']).stdout)
            if 'name=rootless' not in info['SecurityOptions'] or info['CgroupDriver']!='systemd':
                raise RuntimeError('rootless_boundary_not_active')
            if execution.run(execution.docker+['ps','-aq']).stdout.strip():
                raise RuntimeError('dedicated_runtime_has_existing_containers')
            lease=read_model_lease(identity) if action=='test-model' else None
            result=execution.build(locked) if action=='build' else execution.test(locked,manifest,lease)
        except Exception as error:
            failed_stage=execution.stage
            if action=='build' and failed_stage.startswith('build_'):
                try:execution.stop_build()
                except Exception:execution.cleanup={'dedicated_builder_cancellation':'failed; trusted operator required'}
            result={'identity':identity,'state':'test_execution_failed' if execution.tests_started else 'infrastructure_failed',
                'failed_stage':failed_stage,'error_type':type(error).__name__,
                'reason':'fixed_operation_failed; trusted operator must inspect restricted log; no automatic retry'}
        result.update({'started_at':started_at,'ended_at':now(),'tests_started':execution.tests_started,
                       'model_business_test':result.get('model_business_test','not_completed' if action=='test-model' else 'not_run_in_non_model_phase'),
                       'commands':execution.commands,'cleanup':execution.cleanup})
        receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    main()
