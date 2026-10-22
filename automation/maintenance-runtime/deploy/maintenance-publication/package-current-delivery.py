"""Combine reviewed manifests with zipfile/Gitleaks; never run shipped code.

Scope and reuse rationale: research/final-delivery-reuse.md. This is a one-off
OntiCards evidence envelope, reusing the existing PR26/PR33 public artifacts.
"""
import argparse,datetime,hashlib,html,json,os,re,shutil,subprocess,tempfile,zipfile
from pathlib import Path
from review_secret_findings import classify_findings
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
target=args.output.resolve();assert target.is_relative_to(root.resolve()) and not target.exists()
stage=json.loads((root/'evidence/maintenance-final-staging.json').read_text(encoding='utf-8'))
publication=json.loads((root/'evidence/maintenance-update-publication-api.json').read_text(encoding='utf-8'))
assert stage['passed'] and publication['passed'] and publication['main_unchanged_observed']
assert publication['short_lived_token_revoked'] and not publication['force_push']
head=publication['head_sha'];assert re.fullmatch('[0-9a-f]{40}',head)
runtime='automation/maintenance-runtime/'
files={}
def add(source,destination,expected=None,purpose='reviewed source and evidence'):
    source=Path(source);assert source.is_file() and not source.is_symlink()
    assert source.resolve().is_relative_to(root.resolve())
    assert not Path(destination).is_absolute() and '..' not in Path(destination).parts
    raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    assert expected is None or sha==expected,'Source changed: '+str(source)
    assert destination not in files,'Duplicate destination: '+destination
    files[destination]={'source':str(source),'path':destination,'sha256':sha,'bytes':len(raw),'purpose':purpose}
for entry in stage['files']:
    source=Path(stage['stage'])/entry['path']
    add(source,entry['path'],entry['sha256'])
    # The downloadable source must be exactly the published commit, not a newer
    # working copy that happens to share the same filename.
    blob=subprocess.check_output(['git','-C',str(root/'repo'),'show',head+':'+entry['path']])
    assert hashlib.sha256(blob).hexdigest()==entry['sha256'],'Published Git object differs'
ci=json.loads((root/'evidence/preview-ci-public-artifact-allowlist.json').read_text(encoding='utf-8'))
for entry in ci['files']:
    destination=runtime+entry['path']
    if destination not in files:add(root/entry['path'],destination,entry['sha256'],'Previously reviewed PR26 public artifact')
pr33=json.loads((root/'evidence/pr33-static-publication.json').read_text(encoding='utf-8'))
for entry in pr33['files']:
    add(root/'deploy/soffice-concurrency/publish-allowlist'/entry['path'],runtime+'evidence/pr33-public/'+entry['path'],entry['sha256'],'Previously published PR33 artifact')
for relative in ['evidence/maintenance-update-publication-api.json','evidence/maintenance-final-staging.json',
                 'evidence/mcp-review-activation.json',
                 'evidence/pr26-rootless-evidence-portal.png','evidence/pr33-evidence-portal.png',
                 'evidence/pr33-final-native-ui.png']:
    add(root/relative,runtime+relative,purpose='Publication receipt or visually reviewed actual UI capture')
patterns=[rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'github_pat_[A-Za-z0-9_]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'\bsk-[A-Za-z0-9]{20,}',rb'propr_mcp_[A-Za-z0-9_-]{20,}',rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}']
for entry in files.values():
    raw=Path(entry['source']).read_bytes()
    assert not any(re.search(pattern,raw) for pattern in patterns),'Secret-shaped value: '+entry['path']
target.mkdir()
for entry in files.values():
    output=target/entry['path'];output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(entry['source'],output)
at=datetime.datetime.now(datetime.timezone.utc)
manifest={'generated_at':at.isoformat(),'expires_at':(at+datetime.timedelta(days=30)).isoformat(),
 'repository':'stepll2026/OntiCards','configuration_pr':30,'configuration_head':head,
 'main':publication['main_after'],'merge_performed':False,'build_host':'kol-stage2','test_host':'10.66.66.5',
 'scope':'Running test deployment; each requirement retains its current acceptance status in the audit.',
 'files':[{k:v for k,v in item.items() if k!='source'} for item in sorted(files.values(),key=lambda x:x['path'])],
 'generated_members':['DELIVERY-MANIFEST.json','index.html','SECRET-SCAN.json'],
 'archive_members':sorted(list(files)+['DELIVERY-MANIFEST.json','index.html','SECRET-SCAN.json']),
 'manifest_scope':'files hashes reviewed source/evidence; generated_members names envelope files; archive_members enumerates every member of the downloadable ZIP. SAFETY-CHECK.json and the ZIP itself belong only to the outer static publication.',
 'secrets_included':False,'raw_runtime_transcripts_included':False}
(target/'DELIVERY-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
links=[('完整交付包（源码、配置、事实日报和测试证据）','OntiCards-test-delivery-20261023.zip'),
 ('逐功能复用矩阵',runtime+'research/reuse-matrix.md'),('AC01–14完整验收与缺口',runtime+'research/acceptance-gap-audit.md'),
 ('真实验证报告',runtime+'deploy/testing-report.md'),('部署与恢复说明',runtime+'deploy/propr/DEPLOY-CURRENT.md'),
 ('10月22日事实日报',runtime+'evidence/daily-2026-10-22/2026-10-22.md'),
 ('AI日报原文（质量未通过）',runtime+'evidence/daily-2026-10-22/native-attempt3/native-report.md'),
 ('日报显式复核修正版（独立10/10）',runtime+'evidence/daily-2026-10-22/reviewed/2026-10-22-reviewed.md'),
 ('PR26真实业务：API7/7、浏览器3/3、9张截图',runtime+'evidence/rootless-runtime/pr26-rootless-3105-public/index.html'),
 ('PR33自动修复：9回归、10竞态、2真实并发PDF',runtime+'evidence/pr33-public/index.html'),
 ('发布后的自动评审启用回执（基线与真实状态）',runtime+'evidence/mcp-review-activation.json'),
 ('逐文件SHA256与保留时间','DELIVERY-MANIFEST.json')]
body='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OntiCards 测试运行交付</title><style>body{max-width:1000px;margin:40px auto;padding:0 22px;font:17px/1.7 system-ui;color:#172336}a{color:#1559b8}code{overflow-wrap:anywhere}li{margin:.5em 0}.note{padding:18px;background:#fff3d7;border-left:4px solid #bd8200}img{max-width:100%;border:1px solid #d4dbe6}</style><h1>OntiCards 测试运行交付</h1><p>实例：<a href="http://10.66.66.5:18123/">维护系统</a>。镜像在 kol-stage2 构建，在 10.66.66.5 的隔离环境测试。复用 ProPR、n8n、GitHub、systemd、Docker Compose 和原生测试框架。</p><p>配置交付：<a href="https://github.com/stepll2026/OntiCards/pull/30">Draft PR30</a>；修复：<a href="https://github.com/stepll2026/OntiCards/pull/26">PR26</a>、<a href="https://github.com/stepll2026/OntiCards/pull/33">PR33</a>。最终合并由维护者操作。</p>'''
body+='<p>配置提交：<code>'+head+'</code>。快照：'+html.escape(at.isoformat())+'</p>'
body+='''<div class="note">按每项证据交付，不能视为全部验收通过：最新普通对话因错误SHA被拦截并转人工；原生AI日报质量失败，另附明确标注的复核修正版；下一次完整模型CI所需45000配额高于当前15445余额，需维护者分配预算。完整语义索引、未来自然定时和30天持续运行未宣称通过。其他未覆盖目标见验收审计。</div><ul>'''
body+=''.join('<li><a href="'+html.escape(url,quote=True)+'">'+html.escape(title)+'</a></li>' for title,url in links)
body+='</ul><h2>本次真实业务测试门户截图</h2><img alt="PR26 rootless真实验收门户截图" src="'+runtime+'evidence/pr26-rootless-evidence-portal.png"><p>测试结果、原始失败和已复核文件均绑定具体版本；截图用于呈现，机器断言见报告。</p></html>'
(target/'index.html').write_text(body,encoding='utf-8')
environment=os.environ.copy()
for key in ['GITLEAKS_CONFIG','GITLEAKS_CONFIG_TOML']:environment.pop(key,None)
with tempfile.TemporaryDirectory(prefix='onticards-delivery-scan-') as temporary:
    report=Path(temporary)/'report.json'
    result=subprocess.run([str(root/'tools/gitleaks-8.30.1/gitleaks.exe'),'dir',str(target),'--redact=100','--no-banner','--no-color','--ignore-gitleaks-allow','--gitleaks-ignore-path',temporary,'--timeout','60','--report-format','json','--report-path',str(report)],cwd=temporary,env=environment,capture_output=True,text=True,timeout=90)
    findings=json.loads(report.read_text(encoding='utf-8')) if report.exists() else None
    scan=classify_findings(findings,result.returncode,target)
    assert scan['passed'],'Public artifact has unreviewed secret findings'
scan.update(source_files_match_published_head=True,approved_binary_artifacts_match_prior_publication=True)
(target/'SECRET-SCAN.json').write_text(json.dumps(scan,indent=2)+'\n',encoding='utf-8')
# The downloadable archive contains all reviewed source/evidence, not itself.
download=target/'OntiCards-test-delivery-20261023.zip'
with zipfile.ZipFile(download,'w',zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(target.rglob('*')):
        if source.is_file() and source!=download:archive.write(source,source.relative_to(target).as_posix())
with zipfile.ZipFile(download) as archive:
    assert sorted(archive.namelist())==manifest['archive_members']
    assert archive.testzip() is None
    for entry in manifest['files']:
        assert hashlib.sha256(archive.read(entry['path'])).hexdigest()==entry['sha256']
safety={'secret_pattern_matches':0,'pdf_text_scanned':True,'pdf_scan_basis':'Exact immutable binaries already scanned in PR26/PR33 public publication receipts',
 'gitleaks':scan,'files':[{'path':f.relative_to(target).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(target.rglob('*')) if f.is_file()]}
(target/'SAFETY-CHECK.json').write_text(json.dumps(safety,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
public_zip=target.with_suffix('.zip')
with zipfile.ZipFile(public_zip,'w',zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(target.rglob('*')):
        if source.is_file():archive.write(source,source.relative_to(target).as_posix())
receipt={'directory':str(target),'public_zip':str(public_zip),'public_zip_sha256':hashlib.sha256(public_zip.read_bytes()).hexdigest(),
 'public_files':len(safety['files'])+1,'download_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'configuration_head':head,'scan':scan,'inner_archive_members_verified':True}
(root/'evidence/maintenance-final-package.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
