"""Publish exact reviewed Git objects via native Git Data API, trusted host only.

This one-shot adapter creates only the approved branch after exact SHA matching.
Default mode performs read-only checks with a contents-read token. --apply is
reserved for separately approved publication. It cannot update a ref, create a
PR, merge, or execute repository code.
"""
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from github import Auth, Github, GithubIntegration
from github.GithubException import UnknownObjectException

REPOSITORY = 'stepll2026/OntiCards'
BRANCH = 'codex/ai-maintenance-20261022'
BASE = 'c8e3dfee68d398a37842fc332f73af40a56f02a7'
HEAD = '10c6862d4c7325c85618f86455aacf9d10c088b5'
DATA_SHA256 = '62c518812804fcd48fb2ca3e0e79ac5498bfcc92738ff622ccf69a347b6c8e4a'
APPLY = sys.argv[1:] == ['--apply']
if sys.argv[1:] not in ([], ['--apply']):
    raise SystemExit('Use no arguments for read-only checks, or --apply for the separately approved publication')
ROOT = Path('/opt/onticards-maintenance/propr')
OUTPUT = ROOT / ('evidence/maintenance-branch-publication-api.json' if APPLY else 'evidence/maintenance-branch-readonly.json')
KEY = ROOT / 'secrets/github-app.pem'
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


class SafeFailure(Exception):
    pass


result = {
    'started_at': datetime.now(timezone.utc).isoformat(), 'passed': False, 'mode': 'apply' if APPLY else 'read-only',
    'repository': REPOSITORY, 'branch': BRANCH, 'source_base': BASE, 'head_sha': HEAD,
    'source_base_meaning': 'Exact frozen maintenance source base; product and deployment validation recorded separately',
    'current_main_combination_verified': False,
    'data_sha256': DATA_SHA256, 'method': 'PyGithub 2.10.0 native Git Data REST API',
    'force_push': False, 'ref_updates': 0, 'pull_request_created': False,
    'private_key_host': '10.66.66.5', 'token_persisted': False, 'secrets_printed': False,
    'verified_objects': [],
}
client = None
try:
    if os.geteuid() != 0:
        raise SafeFailure('trusted_host_identity_required')
    raw = (ROOT / 'incoming/maintenance-git-data.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise SafeFailure('data_checksum_mismatch')
    data = json.loads(raw)
    if (data['repository'], data['branch'], data['source_base'], data['head']) != (REPOSITORY, BRANCH, BASE, HEAD):
        raise SafeFailure('data_scope_mismatch')
    if len(data['commits']) != 4 or len(data['blobs']) != 30:
        raise SafeFailure('data_object_count_mismatch')
    if {entry['path'] for commit in data['commits'] for entry in commit['entries']} != ALLOWED_FILES:
        raise SafeFailure('file_scope_mismatch')
    expected_parent = BASE
    for commit in data['commits']:
        if commit['parent'] != expected_parent:
            raise SafeFailure('parent_chain_mismatch')
        expected_parent = commit['expected_sha']
        if any(entry['type'] != 'blob' or entry['mode'] != '100644' or entry['sha'] not in data['blobs'] for entry in commit['entries']):
            raise SafeFailure('tree_entry_scope_mismatch')
    if expected_parent != HEAD:
        raise SafeFailure('head_scope_mismatch')
    for expected_sha, encoded in data['blobs'].items():
        content = base64.b64decode(encoded, validate=True)
        if hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest() != expected_sha:
            raise SafeFailure('local_blob_hash_mismatch')
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
        os.environ[name] = 'http://127.0.0.1:17891'
    for name in ('ALL_PROXY', 'all_proxy'):
        os.environ.pop(name, None)
    os.environ['NO_PROXY'] = os.environ['no_proxy'] = '127.0.0.1,localhost'
    with GithubIntegration(auth=Auth.AppAuth(5422414, KEY.read_text()), timeout=30, retry=2) as app:
        identity = app.get_app()
        installation = app.get_app_installation(174029282)
        if identity.id != 5422414 or identity.slug != 'onticards-maintainer-stepll2026':
            raise SafeFailure('app_identity_mismatch')
        if installation.account.login != 'stepll2026' or installation.repository_selection != 'selected':
            raise SafeFailure('installation_scope_mismatch')
        requested_permissions = {'contents': 'write' if APPLY else 'read', 'metadata': 'read'}
        authorization = app.get_access_token(174029282, permissions=requested_permissions)
        client = Github(auth=Auth.Token(authorization.token), timeout=30, retry=2)
        if authorization.permissions != requested_permissions:
            raise SafeFailure('short_lived_token_permission_mismatch')
        _, repositories = client.requester.requestJsonAndCheck('GET', '/installation/repositories', parameters={'per_page': 100})
        if repositories['total_count'] != 1 or [item['full_name'] for item in repositories['repositories']] != [REPOSITORY]:
            raise SafeFailure('short_lived_token_repository_scope_mismatch')
        result['token_permissions'] = authorization.permissions
        result['token_expires_at'] = authorization.expires_at.isoformat()
        prefix = '/repos/' + REPOSITORY + '/git/'

        def api(method, suffix, payload=None):
            if method != 'GET' and not APPLY:
                raise SafeFailure('readonly_mode_refuses_write')
            if method not in ('GET', 'POST'):
                raise SafeFailure('ref_updates_and_deletions_forbidden')
            return client.requester.requestJsonAndCheck(method, prefix + suffix, input=payload)[1]

        def ref(branch):
            try:
                found = api('GET', 'ref/heads/' + branch)
            except UnknownObjectException:
                return None
            if found['ref'] != 'refs/heads/' + branch:
                raise SafeFailure('exact_reference_mismatch')
            return found['object']['sha']

        result['main_before'] = ref('main')
        result['remote_branch_before'] = ref(BRANCH)
        if result['main_before'] is None:
            raise SafeFailure('main_tip_unavailable')
        if result['remote_branch_before'] not in (None, HEAD):
            raise SafeFailure('remote_branch_contains_other_work')
        if not APPLY:
            result['publication_action'] = 'checked_only_no_write'
        elif result['remote_branch_before'] == HEAD:
            result['publication_action'] = 'already_present_no_write'
        else:
            # Objects remain unreferenced until every original SHA has matched.
            for expected_sha, encoded in data['blobs'].items():
                created = api('POST', 'blobs', {'content': encoded, 'encoding': 'base64'})
                result['verified_objects'].append({'type': 'blob', 'expected': expected_sha, 'actual': created['sha']})
                if created['sha'] != expected_sha:
                    raise SafeFailure('remote_blob_hash_mismatch')
            for commit in data['commits']:
                tree = api('POST', 'trees', {'base_tree': commit['base_tree'], 'tree': commit['entries']})
                result['verified_objects'].append({'type': 'tree', 'expected': commit['expected_tree'], 'actual': tree['sha']})
                if tree['sha'] != commit['expected_tree']:
                    raise SafeFailure('remote_tree_hash_mismatch')
                payload = {name: commit[name] for name in ('message', 'author', 'committer')}
                payload.update(tree=tree['sha'], parents=[commit['parent']])
                created = api('POST', 'commits', payload)
                result['verified_objects'].append({'type': 'commit', 'expected': commit['expected_sha'], 'actual': created['sha']})
                if created['sha'] != commit['expected_sha']:
                    raise SafeFailure('remote_commit_hash_mismatch')
            immediately_before = ref(BRANCH)
            if immediately_before not in (None, HEAD):
                raise SafeFailure('remote_branch_appeared_with_other_work')
            if immediately_before is None:
                # POST create only: a race cannot overwrite an existing branch.
                created_ref = api('POST', 'refs', {'ref': 'refs/heads/' + BRANCH, 'sha': HEAD})
                if created_ref['ref'] != 'refs/heads/' + BRANCH or created_ref['object']['sha'] != HEAD:
                    raise SafeFailure('created_reference_mismatch')
                result['publication_action'] = 'created_exact_branch_git_data_api'
            else:
                result['publication_action'] = 'same_branch_appeared_no_reference_write'
        result['remote_branch_after'] = ref(BRANCH)
        result['main_after'] = ref('main')
        result['main_unchanged_observed'] = result['main_before'] == result['main_after']
        if APPLY:
            result['api_branch_readback'] = client.get_repo(REPOSITORY).get_branch(BRANCH).commit.sha
            if result['remote_branch_after'] != HEAD or result['api_branch_readback'] != HEAD:
                raise SafeFailure('branch_readback_mismatch')
        elif result['remote_branch_before'] != result['remote_branch_after']:
            raise SafeFailure('reference_changed_during_readonly_check')
        result['changed_files'] = sorted(ALLOWED_FILES)
        result['passed'] = True
except SafeFailure as error:
    result['error_code'] = str(error)
except Exception as error:
    result['error_code'] = 'publication_failed'
    result['error_type'] = type(error).__name__
    result['http_status'] = getattr(error, 'status', None)
finally:
    if client is not None:
        try:
            client.requester.requestJsonAndCheck('DELETE', '/installation/token')
            result['short_lived_token_revoked'] = True
        except Exception:
            result['short_lived_token_revoked'] = False
        client.close()
    result['completed_at'] = datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['passed'] else 2)
