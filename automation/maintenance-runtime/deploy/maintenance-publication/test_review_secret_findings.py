"""No-network boundary tests for immutable Gitleaks finding classification."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


class ExactFindingReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='onticards-scan-review-test-')
        self.directory = Path(self.temp.name)
        self.root = self.directory / 'scan'
        self.root.mkdir()
        shutil.copyfile(HERE / 'review_secret_findings.py', self.directory / 'review_secret_findings.py')
        self.policy = json.loads((HERE / 'reviewed-nonsecret-findings.json').read_text(encoding='utf-8'))
        self.rule = copy.deepcopy(self.policy['findings'][0])
        source = HERE.parents[1] / self.rule['path'].removeprefix('automation/maintenance-runtime/')
        self.file = self.root / self.rule['path']
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(source.read_bytes())
        self.original = self.file.read_bytes()
        self.write_policy()
        spec = importlib.util.spec_from_file_location('isolated_review', self.directory / 'review_secret_findings.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.finding = {k: self.rule[k] for k in ('RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn')}
        self.finding['File'] = str(self.file)

    def tearDown(self):
        self.temp.cleanup()

    def write_policy(self):
        (self.directory / 'reviewed-nonsecret-findings.json').write_text(json.dumps(self.policy), encoding='utf-8')

    def classify(self, findings, code=1, **options):
        return self.module.classify_findings(findings, code, self.root, **options)

    def test_exact_approved_finding(self):
        result = self.classify([self.finding])
        self.assertTrue(result['passed'])
        self.assertEqual(result['raw_exit_code'], 1)
        self.assertEqual(result['reviewed_nonsecret_count'], 1)
        self.assertFalse(result['scanner_configured_exclusions'])

    def test_changed_bytes_same_location(self):
        self.file.write_bytes(self.original + b'\nchanged')
        self.assertFalse(self.classify([self.finding])['passed'])

    def test_changed_path_same_bytes(self):
        other = self.root / 'renamed.json'
        other.write_bytes(self.original)
        self.assertFalse(self.classify([{**self.finding, 'File': str(other)}])['passed'])

    def test_rule_and_each_span_coordinate(self):
        for key in ('RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn'):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.finding)
                changed[key] = 'unreviewed-rule' if key == 'RuleID' else changed[key] + 1
                self.assertFalse(self.classify([changed])['passed'])

    def test_additional_finding(self):
        changed = {**self.finding, 'StartColumn': self.finding['StartColumn'] + 1}
        self.assertFalse(self.classify([self.finding, changed])['passed'])

    def test_exit_codes_and_missing_report(self):
        for findings, code in ((None, 0), (None, 1), ([], 1), ([self.finding], 0), ([self.finding], 2), ([], 2)):
            with self.subTest(code=code, count=None if findings is None else len(findings)):
                self.assertFalse(self.classify(findings, code)['passed'])
        self.assertTrue(self.classify([], 0)['passed'])

    def test_duplicate_review_records_rejected(self):
        self.policy['findings'].append(copy.deepcopy(self.rule))
        self.write_policy()
        with self.assertRaises(AssertionError):
            self.classify([self.finding])

    def test_unreviewed_policy_rejected(self):
        self.policy['independently_reviewed'] = False
        self.write_policy()
        with self.assertRaises(AssertionError):
            self.classify([self.finding])

    def test_outside_root_rejected(self):
        outside = self.directory / 'outside.json'
        outside.write_bytes(self.original)
        with self.assertRaises(AssertionError):
            self.classify([{**self.finding, 'File': str(outside)}])

    def test_git_blob_prefix_is_explicit_and_exact(self):
        blob = self.root / ('a' * 40) / self.rule['path']
        blob.parent.mkdir(parents=True)
        blob.write_bytes(self.original)
        finding = {**self.finding, 'File': str(blob)}
        self.assertTrue(self.classify([finding], git_objects=True)['passed'])
        self.assertFalse(self.classify([finding], git_objects=False)['passed'])
        bad = self.root / 'not-a-git-object' / self.rule['path']
        bad.parent.mkdir(parents=True)
        bad.write_bytes(self.original)
        self.assertFalse(self.classify([{**self.finding, 'File': str(bad)}], git_objects=True)['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
