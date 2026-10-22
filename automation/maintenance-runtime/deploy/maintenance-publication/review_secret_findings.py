"""Classify native Gitleaks findings against reviewed immutable non-secret bytes.

The scanner still reads every byte with no configured exclusions. Its raw exit
code/count are retained. Only exact file digest, path, rule and span may match an
independently reviewed non-secret record; new or changed findings fail closed.
"""
import hashlib
import json
from pathlib import Path
import re


def classify_findings(findings, exit_code, scan_root, *, git_objects=False):
    rules_path = Path(__file__).with_name('reviewed-nonsecret-findings.json')
    rules = json.loads(rules_path.read_text(encoding='utf-8'))
    assert rules['independently_reviewed'] is True
    assert rules['scope'] == 'exact immutable non-secret findings only'
    fields = ('RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn')
    approved = rules['findings']
    assert approved and all(r['reason'] and re.fullmatch('[0-9a-f]{64}', r['sha256']) for r in approved)
    root = Path(scan_root).resolve()
    observed = []
    reviewed = 0
    for item in findings or []:
        original_path = Path(item['File'])
        assert not original_path.is_symlink()
        path = original_path.resolve()
        assert path.is_relative_to(root) and path.is_file()
        relative = path.relative_to(root).as_posix()
        if git_objects:
            parts = relative.split('/', 1)
            if len(parts) == 2 and re.fullmatch('[0-9a-f]{40}', parts[0]):
                relative = parts[1]
        safe = {key: item.get(key) for key in fields}
        safe.update(path=relative, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        matches = [rule for rule in approved if all(rule.get(k) == v for k, v in safe.items())]
        assert len(matches) <= 1, 'Ambiguous non-secret review record'
        if matches:
            reviewed += 1
            safe['reviewed_nonsecret_reason'] = matches[0]['reason']
        observed.append(safe)
    unreviewed = len(observed) - reviewed
    return {'tool': 'Gitleaks8.30.1', 'raw_exit_code': exit_code,
            'raw_findings_count': len(observed) if findings is not None else None,
            'reviewed_nonsecret_count': reviewed, 'unreviewed_findings_count': unreviewed,
            'scanner_configured_exclusions': False, 'exact_nonsecret_reviews_applied': reviewed > 0,
            'review_policy_sha256': hashlib.sha256(rules_path.read_bytes()).hexdigest(),
            'redact': 100, 'findings': observed,
            'passed': isinstance(findings, list) and exit_code in (0, 1)
                      and (exit_code == 0) == (len(observed) == 0) and unreviewed == 0}
