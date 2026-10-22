import copy
import unittest
import json
import tempfile
from types import SimpleNamespace
from pathlib import Path
import controller as c

HEAD='a'*40;BASE='b'*40
class FixedBoundaryTests(unittest.TestCase):
    def setUp(self):
        _,self.identity,_=c.request_from_command(f'onticards-preview-v1 build 26 {HEAD} {BASE}','build')
        self.image={'config_sha256':'c'*64,'layers':['sha256:'+'d'*64],'os':'linux','architecture':'amd64'}
        self.lock={k:{'tag':k+':fixed','identity':copy.deepcopy(self.image)} for k in ['db','weaviate','nginx','tests']}
        self.manifest={'identity':self.identity,'state':'built','archive_sha256':'e'*64,'archive_bytes':100,'images':copy.deepcopy(self.lock)}
        self.manifest['images'].update({k:{'tag':f'onticards-ci-{k}:{self.identity["run_id"]}','identity':copy.deepcopy(self.image)} for k in ['api','web']})
        self.pr={'state':'open','head':{'repo':{'full_name':'stepll2026/OntiCards'},'ref':'codex/fix','sha':HEAD},'base':{'repo':{'full_name':'stepll2026/OntiCards'},'ref':'main','sha':BASE}}
    def test_same_identity_reuses_deterministic_run(self):
        action,i,d=c.request_from_command(f'onticards-preview-v1 test 26 {HEAD} {BASE} '+('c'*64),'test')
        self.assertEqual(i,self.identity);self.assertEqual(action,'test')
    def test_shell_metacharacters_rejected(self):
        for tail in ['; id','\nrm -rf /',' $(id)',' `id`',' /tmp/source']:
            with self.subTest(tail=tail),self.assertRaises(ValueError):c.request_from_command(f'onticards-preview-v1 build 26 {HEAD} {BASE}'+tail,'build')
    def test_ref_names_paths_and_short_sha_rejected(self):
        for value in ['main','refs/heads/main','../etc/passwd','a'*39,'A'*40]:
            with self.subTest(value=value),self.assertRaises(ValueError):c.request_from_command(f'onticards-preview-v1 build 26 {value} {BASE}','build')
    def test_no_build_on_test_host(self):
        with self.assertRaises(ValueError):c.request_from_command(f'onticards-preview-v1 build 26 {HEAD} {BASE}','test')
    def test_test_requires_bound_manifest(self):
        with self.assertRaises(ValueError):c.request_from_command(f'onticards-preview-v1 test 26 {HEAD} {BASE}','test')
    def lease(self):
        return {**self.identity,'token_id':8,'expires_at':1800,'base_url':'http://10.66.66.5:18134/v1',
            'model':'onticards-preview-qwen3.8-max-0902','embedding_model':'onticards-preview-qwen3.7-text-embedding-flash','api_key':'sk-'+'x'*24}
    def test_explicit_model_phase_keeps_identity_and_requires_manifest(self):
        action,identity,_=c.request_from_command(f'onticards-preview-v1 test-model 26 {HEAD} {BASE} '+('c'*64),'test')
        self.assertEqual(action,'test-model');self.assertEqual(identity,self.identity)
        with self.assertRaises(ValueError):c.request_from_command(f'onticards-preview-v1 test-model 26 {HEAD} {BASE}','test')
    def test_bound_native_lease_both_aliases_and_expiry(self):
        lease=self.lease();c.validate_model_lease(lease,self.identity,1000)
        for key,value in [('base_url','http://10.66.66.5:3000/v1'),('embedding_model','other'),('head','f'*40),('expires_at',1001),('expires_at',3000)]:
            changed={**lease,key:value}
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):c.validate_model_lease(changed,self.identity,1000)
    def test_long_credential_or_unapproved_fields_rejected(self):
        lease=self.lease();lease['DASHSCOPE_API_KEY']='never accepted'
        with self.assertRaises(ValueError):c.validate_model_lease(lease,self.identity,1000)
    def test_valid_manifest_accepted(self):c.assert_manifest(self.manifest,self.identity,self.lock)
    def registry_pair(self):
        self.manifest.update(archive_kind='registry-pair',archives={k:{'name':'images-'+k+'.tar','sha256':'f'*64,'bytes':100} for k in ['api','web']},registry={k:'registry-intl.cn-hongkong.aliyuncs.com/shallopcr/onticards-ci-'+k+'@sha256:'+'f'*64 for k in ['api','web']})
    def test_registry_pair_requires_exact_archive_names(self):
        self.registry_pair();c.assert_manifest(self.manifest,self.identity,self.lock)
        self.manifest['archives']['api']['name']='../../secrets/auth.json'
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_registry_pair_requires_fixed_repo_and_digest(self):
        self.registry_pair();self.manifest['registry']['api']='attacker.example/api@sha256:'+'f'*64
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_registry_pair_does_not_replace_trusted_images(self):
        self.registry_pair();self.manifest['archives']['tests']={'name':'images-tests.tar','sha256':'f'*64,'bytes':100}
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_docker28_29_empty_fields_normalize_but_command_change_does_not(self):
        info={'Config':{'Cmd':['postgres']},'RootFS':{'Layers':['sha256:x']},'Os':'linux','Architecture':'amd64'}
        other=copy.deepcopy(info);other['Config'].update({'Labels':None,'OnBuild':None,'User':''})
        self.assertEqual(c.image_identity(info),c.image_identity(other))
        other['Config']['Cmd']=['malicious']
        self.assertNotEqual(c.image_identity(info),c.image_identity(other))
    def test_cross_run_artifact_rejected(self):
        self.manifest['identity']={**self.identity,'head':'f'*40}
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_replaced_trusted_runner_rejected(self):
        self.manifest['images']['tests']['identity']['config_sha256']='f'*64
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_extra_or_global_image_tag_rejected(self):
        self.manifest['images']['api']['tag']='postgres:15-alpine'
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_oversized_archive_rejected(self):
        self.manifest['archive_bytes']=c.MAX_ARCHIVE+1
        with self.assertRaises(ValueError):c.assert_manifest(self.manifest,self.identity,self.lock)
    def test_fork_rejected_even_with_matching_sha(self):
        self.pr['head']['repo']['full_name']='attacker/OntiCards'
        with self.assertRaises(ValueError):c.validate_remote_pr(self.pr,self.identity)
    def test_changed_base_and_closed_pr_rejected(self):
        self.pr['base']['sha']='f'*40
        with self.assertRaises(ValueError):c.validate_remote_pr(self.pr,self.identity)
        self.pr['base']['sha']=BASE;self.pr['state']='closed'
        with self.assertRaises(ValueError):c.validate_remote_pr(self.pr,self.identity)
    def test_no_external_network_ports_socket_or_model_credentials(self):
        spec=c.compose_spec(self.identity,{k:'sha256:'+'a'*64 for k in self.manifest['images']},{'DB_PASSWORD':'synthetic'},Path('/home/onticards-preview/runs/x/fixture.sqlite'))
        self.assertTrue(spec['networks']['preview']['internal'])
        self.assertFalse(spec['networks']['model-egress']['internal'])
        for name,service in spec['services'].items():
            self.assertNotIn('ports',service);self.assertNotIn('build',service);self.assertNotIn('privileged',service);self.assertNotIn('network_mode',service)
            self.assertIn('no-new-privileges:true',service['security_opt'])
            self.assertFalse(any('docker.sock' in v or '/secrets' in v or '/.ssh' in v for v in service.get('volumes',[])))
            self.assertFalse(any(k in service.get('environment',{}) for k in ['DASHSCOPE_API_KEY','GITHUB_TOKEN','SSH_AUTH_SOCK']))
            self.assertEqual(service['networks'],['preview','model-egress'] if name=='onticards_api' else ['preview'])
        self.assertEqual(spec['services']['tests']['user'],'1001:1001')
        self.assertEqual(spec['services']['onticards_api']['cap_drop'],['ALL'])
        self.assertNotIn('cap_add',spec['services']['onticards_api'])
        self.assertEqual(spec['services']['tests']['cap_add'],['SYS_CHROOT'])

    def test_missing_machine_reports_never_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(FileNotFoundError):c.verify_test_results(root)
            (root/'checks.json').write_text(json.dumps({'api_exit':0,'api_tests':7,'browser_exit':0,'browser_expected':2,'browser_unexpected':0,'browser_skipped':0}))
            with self.assertRaises(FileNotFoundError):c.verify_test_results(root)

    def test_cleanup_includes_profile_only_volume_and_probes_zero(self):
        execution=object.__new__(c.Execution);execution.identity=self.identity;execution.output_id=self.identity['run_id']+'-model';execution.docker=['docker'];calls=[]
        def run(args,**kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0,stdout='')
        execution.run=run
        execution.cleanup_compose(['docker','compose'],'test-container')
        self.assertTrue(any('--profile' in a and 'tests' in a and 'down' in a for a in calls))
        self.assertTrue(any('volume' in a and 'ls' in a and 'label=com.docker.compose.project=oci-'+execution.output_id in a for a in calls))
        self.assertEqual(execution.cleanup['attempts'][-1]['remaining_project_volumes'],[])

    def test_leftover_profile_volume_prevents_cleanup_success(self):
        execution=object.__new__(c.Execution);execution.identity=self.identity;execution.output_id=self.identity['run_id']+'-model';execution.docker=['docker']
        def run(args,**kwargs):
            return SimpleNamespace(returncode=0,stdout='old-results\n' if 'volume' in args else '')
        execution.run=run
        with self.assertRaises(c.OperationFailed):execution.cleanup_compose(['docker','compose'],'test-container')

    def test_missing_screenshots_never_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'browser/test-results').mkdir(parents=True)
            (root/'checks.json').write_text(json.dumps({'api_exit':0,'api_tests':7,'browser_exit':0,'browser_expected':2,'browser_unexpected':0,'browser_skipped':0}))
            (root/'api.xml').write_text('<testsuites><testsuite tests="7" errors="0" failures="0" skipped="0"/></testsuites>')
            (root/'browser/results.json').write_text(json.dumps({'stats':{'expected':2,'unexpected':0,'skipped':0}}))
            (root/'browser/results.xml').write_text('<testsuites/>')
            with self.assertRaises(ValueError):c.verify_test_results(root)
            (root/'browser/test-results/one.png').write_bytes(b'\x89PNG\r\n\x1a\nfixture')
            c.verify_test_results(root)
            (root/'browser/html/data').mkdir(parents=True)
            (root/'browser/test-results/one.png').rename(root/'browser/html/data/native-success-attachment.png')
            c.verify_test_results(root)
            (root/'browser/html/data/native-success-attachment.png').write_bytes(b'invalid-png')
            with self.assertRaises(ValueError):c.verify_test_results(root)

    def test_failed_api_machine_report_never_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'checks.json').write_text(json.dumps({'api_exit':0,'api_tests':7,'browser_exit':0,'browser_expected':2,'browser_unexpected':0,'browser_skipped':0}))
            (root/'api.xml').write_text('<testsuites><testsuite tests="7" errors="0" failures="1" skipped="0"/></testsuites>')
            with self.assertRaises(ValueError):c.verify_test_results(root)

if __name__=='__main__':unittest.main(verbosity=2)
