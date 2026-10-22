"""Stage exact reviewed text allowlists for PR30 and scan before any GitHub write."""
import argparse,ast,datetime,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from review_secret_findings import classify_findings

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--stage',type=Path,required=True)
args=parser.parse_args();stage=args.stage.resolve()
assert stage.is_relative_to(root.resolve()) and stage!=root.resolve() and not stage.exists()
lists=['evidence/propr-knowledge-collector-allowlist.json','evidence/preview-ci-source-allowlist.json','deploy/n8n/PR30_ALLOWLIST.json']
entries={};contents={}
def add(relative,expected=None,target=None,purpose='current reviewed delivery'):
 source=(root/relative).resolve()
 assert source.is_relative_to(root.resolve()) and source.is_file() and not (root/relative).is_symlink(), relative
 raw=source.read_bytes();raw.decode('utf-8')
 source_digest=hashlib.sha256(raw).hexdigest()
 assert expected is None or source_digest==expected, 'Refresh changed allowlist: '+relative
 # Existing repository files use Git's LF text representation. Preserve the
 # reviewed deployed-template bytes elsewhere, without changing user Git config.
 staged=raw.replace(b'\r\n',b'\n') if relative.startswith('repo/') else raw
 digest=hashlib.sha256(staged).hexdigest()
 assert source.suffix.lower() not in ['.pem','.key','.sqlite','.db','.tar','.gz','.zip','.log','.pyc','.jsonl','.har']
 assert not source.name.endswith('.env') and source.name not in ['opencode.json','owner.json','storageState.json']
 destination=target or (relative[5:] if relative.startswith('repo/') else 'automation/maintenance-runtime/'+relative)
 assert '..' not in Path(destination).parts and not Path(destination).is_absolute()
 if destination in entries:
  assert entries[destination]['sha256']==digest, 'Destination collision: '+destination
 entries[destination]={'source':relative,'source_sha256':source_digest,'path':destination,'sha256':digest,'bytes':len(staged),'purpose':purpose}
 contents[destination]=staged
for filename in lists:
 data=json.loads((root/filename).read_text(encoding='utf-8'))
 for entry in data['files']:
  relative=entry.get('path') or entry['source_relative'].removeprefix('outputs/onticards/')
  add(relative,entry['sha256'],purpose=entry.get('purpose',entry.get('reason','reviewed component')))
 for source,destination in data.get('repository_documents_ready',{}).items():add(source,target=destination)
original=ast.parse((root/'deploy/maintenance-publication/export-git-data.py').read_text(encoding='utf-8'))
for node in original.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED_FILES' for t in node.targets):
  for path in ast.literal_eval(node.value):add('repo/'+path)
for path in '''
deploy/README.md
deploy/testing-report.md
research/reuse-matrix.md
research/acceptance-gap-audit.md
research/component-versions.json
research/final-delivery-reuse.md
research/propr-patch-map.md
research/propr-patch-map.json
evidence/propr-knowledge-collector-allowlist.json
evidence/preview-ci-source-allowlist.json
deploy/n8n/PR30_ALLOWLIST.json
evidence/maintenance-update-generator-independent-review.json
evidence/maintenance-delivery-independent-review.json
deploy/maintenance-publication/stage-current-delivery.py
deploy/maintenance-publication/package-current-delivery.py
deploy/maintenance-publication/prepare-update-tools.py
deploy/maintenance-publication/prepare-static-delivery.py
deploy/maintenance-publication/export-git-data.py
deploy/maintenance-publication/publish-exact-branch.py
deploy/maintenance-publication/review_secret_findings.py
deploy/maintenance-publication/test_review_secret_findings.py
deploy/maintenance-publication/reviewed-nonsecret-findings.json
evidence/maintenance-final-scan-redacted-findings.json
evidence/maintenance-secret-scan-review.json
repo/docs/maintenance/acceptance-gap-audit.md
'''.split():add(path)
patterns=[rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'github_pat_[A-Za-z0-9_]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'\bsk-[A-Za-z0-9]{20,}',rb'propr_mcp_[A-Za-z0-9_-]{20,}',rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}']
for entry in entries.values():
 assert not any(re.search(pattern,(root/entry['source']).read_bytes()) for pattern in patterns), 'Secret-shaped value: '+entry['path']
stage.mkdir()
for entry in entries.values():
 destination=stage/entry['path'];destination.parent.mkdir(parents=True,exist_ok=True)
 destination.write_bytes(contents[entry['path']])
environment=os.environ.copy()
for key in ['GITLEAKS_CONFIG','GITLEAKS_CONFIG_TOML']:environment.pop(key,None)
scanner=root/'tools/gitleaks-8.30.1/gitleaks.exe'
with tempfile.TemporaryDirectory(prefix='onticards-final-scan-') as directory:
 result_path=Path(directory)/'report.json'
 run=subprocess.run([str(scanner),'dir',str(stage),'--redact=100','--no-banner','--no-color','--ignore-gitleaks-allow','--gitleaks-ignore-path',directory,'--timeout','60','--report-format','json','--report-path',str(result_path)],cwd=directory,env=environment,capture_output=True,text=True,timeout=90)
 findings=json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else None
 scan=classify_findings(findings,run.returncode,stage)
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':str(stage),'file_count':len(entries),'total_bytes':sum(x['bytes'] for x in entries.values()),'source_allowlists':lists,'files':sorted(entries.values(),key=lambda e:e['path']),
 'secret_scan':scan,'passed':scan['passed'],'github_writes':0,'native_model_calls':0}
(root/'evidence/maintenance-final-staging.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:receipt[k] for k in ['stage','file_count','total_bytes','secret_scan','passed']}))
raise SystemExit(0 if receipt['passed'] else 2)
