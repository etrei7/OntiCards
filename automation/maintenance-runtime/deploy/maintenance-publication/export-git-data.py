"""Export the approved linear maintenance range without executing its code.

Reuse native Git object reads and Gitleaks; retain every original commit identity.
The resulting data is not a publication: the separate pinned publisher creates
only the exact approved ref after GitHub reproduces all expected object hashes.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from review_secret_findings import classify_findings

REPOSITORY = 'stepll2026/OntiCards'
BRANCH = 'codex/ai-maintenance-20261022'
BASE = 'c8e3dfee68d398a37842fc332f73af40a56f02a7'
ALLOWED_FILES = {
    '.propr/pr-template.md', '.propr/workflow.yml', 'AGENTS.md',
    'automation/.gitignore', 'automation/README.md',
    'automation/deploy/install-reporting.sh', 'automation/deploy/onticards-collector@.service',
    'automation/deploy/onticards-report.timer', 'automation/deploy/onticards-report.tmpfiles.conf',
    'automation/deploy/onticards-snapshot.timer', 'automation/deploy/reporting.env.example',
    'automation/deploy/requirements.lock.txt', 'automation/onticards/__init__.py',
    'automation/onticards/report.py', 'automation/requirements.txt', 'automation/tests/test_report.py',
    'docs/maintenance/github-app.md', 'docs/maintenance/repository-context.md',
    'docs/maintenance/repository.md', 'docs/maintenance/response-policy.md', 'docs/maintenance/reuse-matrix.md',
}
# Reuse the delivery package's existing explicit secret-shaped-value checks in
# addition to the upstream scanner. Never include a match's text in evidence.
SECRET_PATTERNS = [
    rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
    rb'gh[pousr]_[A-Za-z0-9]{20,}', rb'github_pat_[A-Za-z0-9_]{20,}',
    rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}',
    rb'sk-[A-Za-z0-9]{20,}',
    rb'propr_mcp_[A-Za-z0-9_-]{20,}',
    rb'(?i)(?:authorization|proxy-authorization)["\x27]?\s*[:=]\s*["\x27]?\s*(?:bearer|basic)\s+[A-Za-z0-9+/_.=-]{12,}',
]


def git_hash(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def identity(raw):
    match = re.fullmatch(r'(.*) <([^<>]+)> (-?\d+) ([+-]\d{4})', raw)
    if not match:
        raise ValueError('unsupported_commit_identity')
    name, email, epoch, offset = match.groups()
    minutes = (int(offset[1:3]) * 60 + int(offset[3:])) * (-1 if offset[0] == '-' else 1)
    value = datetime.fromtimestamp(int(epoch), timezone(timedelta(minutes=minutes)))
    return {'name': name, 'email': email, 'date': value.isoformat()}


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--gitleaks', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}', args.head), 'full_head_required'
    environment = os.environ.copy()
    environment['GIT_NO_REPLACE_OBJECTS'] = '1'
    for key in ['GITLEAKS_CONFIG', 'GITLEAKS_CONFIG_TOML']:
        environment.pop(key, None)
    def git(*arguments):
        return subprocess.check_output(['git', '--no-replace-objects', '-C', str(args.repo), *arguments], env=environment)
    assert git('branch', '--show-current').decode().strip() == BRANCH, 'branch_mismatch'
    assert git('rev-parse', 'HEAD').decode().strip() == args.head, 'working_head_mismatch'
    assert not git('status', '--porcelain', '--untracked-files=all'), 'working_tree_not_clean'
    commits = git('rev-list', '--reverse', '--topo-order', BASE + '..' + args.head).decode().splitlines()
    assert commits, 'empty_range'
    version = subprocess.check_output([str(args.gitleaks), 'version'], env=environment, text=True).strip()
    assert version == '8.30.1', 'scanner_version_mismatch'
    data = {'repository': REPOSITORY, 'branch': BRANCH, 'source_base': BASE, 'head': args.head, 'commits': [], 'blobs': {}}
    audit = {'captured_at': datetime.now(timezone.utc).isoformat(), 'repository': REPOSITORY, 'branch': BRANCH,
             'base': BASE, 'head': args.head, 'commits': [], 'blob_versions': [], 'secret_scan': {},
             'source_code_executed': False, 'github_write_performed': False}
    expected_parent, all_paths = BASE, set()
    with tempfile.TemporaryDirectory(prefix='onticards-git-export-') as directory:
        temporary = Path(directory)
        raw_dir = temporary / 'original-git-objects'
        raw_dir.mkdir()
        for sha in commits:
            raw = git('cat-file', 'commit', sha)
            assert git_hash('commit', raw) == sha, 'commit_object_hash_mismatch'
            headers, message = raw.decode('utf-8').split('\n\n', 1)
            parts = [line.split(' ', 1) for line in headers.splitlines()]
            assert [x[0] for x in parts] == ['tree', 'parent', 'author', 'committer'], 'unsupported_commit_headers_or_merge'
            values = dict(parts)
            assert values['parent'] == expected_parent, 'nonlinear_parent_chain'
            tree_raw = git('cat-file', 'tree', values['tree'])
            assert git_hash('tree', tree_raw) == values['tree'], 'tree_object_hash_mismatch'
            entry = {'expected_sha': sha, 'expected_tree': values['tree'],
                     'base_tree': git('rev-parse', expected_parent + '^{tree}').decode().strip(),
                     'parent': expected_parent, 'message': message,
                     'author': identity(values['author']), 'committer': identity(values['committer']), 'entries': []}
            # Reconstruct the commit GitHub will create, including original timezone.
            def original_identity(person):
                instant = datetime.fromisoformat(person['date'])
                return f"{person['name']} <{person['email']}> {int(instant.timestamp())} {instant.strftime('%z')}"
            reconstructed = (f"tree {entry['expected_tree']}\nparent {entry['parent']}\nauthor {original_identity(entry['author'])}\ncommitter {original_identity(entry['committer'])}\n\n" + message).encode()
            assert reconstructed == raw, 'api_identity_cannot_reproduce_original_commit'
            (raw_dir / (sha + '.commit.txt')).write_bytes(raw)
            changes = git('diff-tree', '--no-commit-id', '--raw', '--no-abbrev', '--no-renames', '-z', '-r', expected_parent, sha).split(b'\0')
            assert changes[-1] == b'' and (len(changes) - 1) % 2 == 0, 'invalid_diff_records'
            for i in range(0, len(changes) - 1, 2):
                old_mode, mode, old_sha, blob_sha, status = changes[i].decode().split()
                path = changes[i + 1].decode('utf-8')
                assert path in ALLOWED_FILES and status in ('A', 'M'), 'file_or_change_outside_allowlist'
                assert mode == '100644' and old_mode in (':000000', ':100644'), 'nonregular_or_executable_file'
                assert git('cat-file', '-t', blob_sha).strip() == b'blob', 'not_a_blob'
                content = git('cat-file', 'blob', blob_sha)
                content.decode('utf-8')  # This approved package contains only text.
                assert len(content) < 2_000_000 and git_hash('blob', content) == blob_sha, 'blob_size_or_hash_mismatch'
                for pattern_index, pattern in enumerate(SECRET_PATTERNS):
                    for match in re.finditer(pattern, content):
                        # The reviewed redaction fixture deliberately contains a
                        # synthetic Authorization header. Bind the exception to
                        # every byte and this exact match; all other shapes fail.
                        assert (pattern_index == 6
                                and path == 'automation/maintenance-runtime/deploy/n8n/build_policy_boundary_probe.py'
                                and hashlib.sha256(content).hexdigest() == '609797a8fc290d30b6f9f67d0943ac43b4661fce045778f2322764b3d376a74e'
                                and hashlib.sha256(match.group()).hexdigest() == '18b16b04c0297625fe6283cfadedb6c878366f1495a974b23c57aeaeceab0454'), 'secret_shaped_blob_value'
                        audit.setdefault('reviewed_synthetic_header_matches', []).append(
                            {'path': path, 'pattern_index': pattern_index, 'line': content[:match.start()].count(b'\n') + 1,
                             'reason': 'Frozen synthetic redaction fixture independently reviewed in maintenance-secret-scan-review.json'})
                data['blobs'][blob_sha] = base64.b64encode(content).decode()
                entry['entries'].append({'path': path, 'mode': mode, 'type': 'blob', 'sha': blob_sha})
                all_paths.add(path)
                artifact = raw_dir / blob_sha / path
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_bytes(content)
                audit['blob_versions'].append({'commit': sha, 'path': path, 'mode': mode, 'blob': blob_sha,
                                               'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
            data['commits'].append(entry)
            audit['commits'].append({k: entry[k] for k in ['expected_sha', 'parent', 'expected_tree', 'base_tree', 'author', 'committer', 'message']})
            expected_parent = sha
        assert expected_parent == args.head and all_paths == ALLOWED_FILES, 'final_scope_mismatch'
        final_paths = set(git('diff', '--name-only', '-z', BASE, args.head).decode().strip('\0').split('\0'))
        assert final_paths == ALLOWED_FILES, 'final_diff_scope_mismatch'
        scan_report = temporary / 'scan.json'
        scanner = subprocess.run([str(args.gitleaks.resolve()), 'dir', str(raw_dir), '--redact=100', '--no-banner', '--no-color',
                                  '--ignore-gitleaks-allow', '--gitleaks-ignore-path', str(temporary), '--timeout', '60',
                                  '--report-format', 'json', '--report-path', str(scan_report)],
                                 cwd=temporary, env=environment, text=True, capture_output=True, timeout=90)
        findings = json.loads(scan_report.read_text(encoding='utf-8')) if scan_report.exists() else None
        audit['secret_scan'] = {'tool': 'Gitleaks', 'version': version, 'scope': 'Every changed full blob version and raw commit in the approved range',
                                'exit_code': scanner.returncode, 'findings_count': len(findings) if findings is not None else None,
                                'findings': [{k: item.get(k) for k in ['RuleID', 'File', 'StartLine']} for item in findings or []],
                                'redact': 100, 'ignore_allow_comments': True, 'configured_exclusions': False,
                                'additional_existing_secret_patterns_passed': True}
        audit['secret_scan'].update(classify_findings(findings, scanner.returncode, raw_dir, git_objects=True))
        args.output.mkdir(parents=True, exist_ok=True)
        audit['passed'] = audit['secret_scan']['passed']
        if not audit['passed']:
            (args.output / 'export-validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            raise ValueError('secret_scan_failed_no_publication_data_written')
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    audit.update({'data_sha256': hashlib.sha256(encoded).hexdigest(), 'commit_count': len(commits),
                  'unique_blob_count': len(data['blobs']), 'allowed_paths': sorted(ALLOWED_FILES), 'file_count': len(ALLOWED_FILES)})
    (args.output / 'maintenance-git-data.json').write_bytes(encoded)
    (args.output / 'export-validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ['passed', 'head', 'commit_count', 'unique_blob_count', 'file_count', 'data_sha256', 'secret_scan']}))


if __name__ == '__main__':
    run()
