"""Trusted host installation of one fixed SSH capability and loopback MCP TLS.
Source files must be staged in /opt/onticards-maintenance/propr/review-stage.
Does not arm review, publish comments, start model jobs or modify shared 443.
"""
import datetime, hashlib, json, os, pathlib, shutil, subprocess

ROOT=pathlib.Path('/opt/onticards-maintenance/propr')
STAGE=ROOT/'review-stage'
SERVICE=ROOT/'review-service'
CI=pathlib.Path('/opt/onticards-maintenance/preview-ci')
def run(argv, **kwargs):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=120,**kwargs)
    if p.returncode: raise RuntimeError('Fixed install command failed: '+pathlib.Path(argv[0]).name)
    return p.stdout
def put(path, text, mode=0o600):
    path.write_text(text,encoding='utf-8');path.chmod(mode)
def copy(source, destination, mode=0o600):
    assert source.is_file() and not source.is_symlink()
    shutil.copyfile(source,destination);destination.chmod(mode)

assert os.getuid()==0
assert not SERVICE.is_symlink() and not CI.is_symlink()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=ROOT/'recovery'/('mcp-service-'+stamp);backup.mkdir(parents=True,mode=0o700)
for name in ['compose.yaml','nginx.conf','mcp.env','mcp-tls.conf']:
    if (ROOT/name).exists():copy(ROOT/name,backup/name)
SERVICE.mkdir(mode=0o700,exist_ok=True);(SERVICE/'state').mkdir(mode=0o700,exist_ok=True)
for name in ['ssh_gate.py','mcp_review.mjs','receipt.mjs','configure_native.mjs']:
    copy(STAGE/name,SERVICE/name)
if not (SERVICE/'policy.json').exists():
    put(SERVICE/'policy.json',json.dumps({'enabled':False,'repository':'stepll2026/OntiCards','baseline_versions':[],'activation':'operator baseline after final configuration PR commit'}))
assert json.loads((SERVICE/'policy.json').read_text())['enabled'] is False
copy(STAGE/'mcp-tls.conf',ROOT/'mcp-tls.conf',0o644)
copy(STAGE/'mcp.env.template',ROOT/'mcp.env')

# Patch the current deployed configuration in place; never replace other portals.
nginx=(ROOT/'nginx.conf').read_text()
if 'location = /api/mcp { return 404; }' not in nginx:
    anchor='    location /api/ {'
    assert nginx.count(anchor)==1
    nginx=nginx.replace(anchor,'    location = /api/mcp { return 404; }\n    location ^~ /api/mcp/ { return 404; }\n'+anchor)
put(ROOT/'nginx.conf',nginx,0o644)
compose=(ROOT/'compose.yaml').read_text()
assert any(image in compose for image in [
    'onticards-42931b1-policy12@sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa',
    'onticards-42931b1-policy13@sha256:3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879',
]), 'Install only against the specifically verified policy12 or policy13 image; activation separately requires policy13'
if 'path: mcp.env' not in compose:
    anchor='      - path: oauth.env\n        required: false'
    assert compose.count(anchor)==1
    compose=compose.replace(anchor,anchor+'\n      - path: mcp.env\n        required: false')
if './review-service:/run/propr-review:ro' not in compose:
    anchor='      - ./secrets:/run/propr-secrets:ro'
    api_start=compose.index('\n  api:');api_end=compose.index('\n  daemon:',api_start)
    api=compose[api_start:api_end];assert api.count(anchor)==1
    api=api.replace(anchor,anchor+'\n      - ./review-service:/run/propr-review:ro\n      - /srv/apps/voicebox/certs/voicebox-ca.crt:/run/propr-tls/ca.crt:ro')
    compose=compose[:api_start]+api+compose[api_end:]
if './mcp-tls.conf:' not in compose:
    anchor='      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro';assert compose.count(anchor)==1
    compose=compose.replace(anchor,anchor+'\n      - ./mcp-tls.conf:/etc/nginx/conf.d/onticards-mcp.conf:ro\n      - /srv/apps/voicebox/certs/voicebox-server.crt:/run/propr-tls/server.crt:ro\n      - /srv/apps/voicebox/certs/voicebox-server.key:/run/propr-tls/server.key:ro')
put(ROOT/'compose.yaml',compose,0o644)
run(['docker','compose','--project-directory',str(ROOT),'config','--quiet'])
# Existing production image validates the new config before replacing web.
run(['docker','run','--rm','--network','host','-v',str(ROOT/'nginx.conf')+':/etc/nginx/conf.d/default.conf:ro',
     '-v',str(ROOT/'mcp-tls.conf')+':/etc/nginx/conf.d/onticards-mcp.conf:ro',
     '-v','/srv/apps/voicebox/certs/voicebox-server.crt:/run/propr-tls/server.crt:ro',
     '-v','/srv/apps/voicebox/certs/voicebox-server.key:/run/propr-tls/server.key:ro',
     'nginx:1.27-alpine@sha256:91fc9c3924b93f76adc9cd36a0bb93e53885ff8e97df10233caa45bb432789a5','nginx','-t'])

sshdir=pathlib.Path('/root/.ssh');sshdir.mkdir(mode=0o700,exist_ok=True)
authorized=sshdir/'authorized_keys';before=authorized.read_text() if authorized.exists() else ''
put(backup/'authorized_keys',before)
key=CI/'secrets/automatic-review'
if not key.exists():run(['/usr/bin/ssh-keygen','-t','ed25519','-N','','-C','onticards-fixed-review-v1','-f',str(key)])
key.chmod(0o600);os.chown(key,1003,1003)
pub=(key.with_suffix('.pub')).read_text().strip()
command='/usr/bin/env -i PATH=/usr/bin:/bin HOME=/root /usr/bin/python3 -I '+str(SERVICE/'ssh_gate.py')
entry='from="127.0.0.1",restrict,no-user-rc,no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty,command="'+command+'" '+pub
if pub not in before:put(authorized,before.rstrip()+'\n'+entry+'\n')
else:assert entry in before
effective=run(['/usr/sbin/sshd','-T','-C','user=root,addr=127.0.0.1,host=localhost,laddr=127.0.0.1,lport=9922'])
accept=[x.split(maxsplit=1)[1] for x in effective.splitlines() if x.startswith('acceptenv ')]
assert all(x in ['LANG','LC_*'] for x in accept), 'Unexpected accepted environment; do not weaken sshd'
assert 'port 9922\n' in effective
hostpub=pathlib.Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
put(CI/'ssh/review_known_hosts','[127.0.0.1]:9922 '+hostpub[0]+' '+hostpub[1]+'\n',0o644)
config='''Host automatic-review
  HostName 127.0.0.1
  Port 9922
  User root
  IdentityFile /opt/onticards-preview-ci/secrets/automatic-review
  IdentitiesOnly yes
  StrictHostKeyChecking yes
  UserKnownHostsFile /opt/onticards-preview-ci/ssh/review_known_hosts
  BatchMode yes
  RequestTTY no
  ClearAllForwardings yes
  ConnectTimeout 10
  ServerAliveInterval 15
  ServerAliveCountMax 2
'''
put(CI/'ssh/review_config',config,0o644)
run(['docker','compose','--project-directory',str(ROOT),'up','-d','--no-deps','api','web'])
settings=run(['docker','exec','onticards-propr-api','node','/run/propr-review/configure_native.mjs'])
safe=[x.split('ONTICARDS_MCP_SETTINGS:',1)[1] for x in settings.splitlines() if x.startswith('ONTICARDS_MCP_SETTINGS:')]
assert len(safe)==1
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backup':str(backup),'mcp_settings':json.loads(safe[0]),
        'review_enabled':False,'models_started':False,'shared_443_changed':False,'ssh_source':'127.0.0.1',
        'key_options':['restrict','no-user-rc','no-port-forwarding','no-agent-forwarding','no-X11-forwarding','no-pty','fixed command'],
        'compose_sha256':hashlib.sha256(compose.encode()).hexdigest(),'nginx_sha256':hashlib.sha256(nginx.encode()).hexdigest()}
put(SERVICE/'state/service-install.json',json.dumps(record,indent=2))
print(json.dumps(record))
