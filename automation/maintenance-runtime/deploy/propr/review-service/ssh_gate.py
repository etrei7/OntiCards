"""Fixed local SSH capability. No shell, paths, credentials or model input from caller."""
import fcntl
import hashlib
import json
import os
import pathlib
import select
import subprocess
import sys
import time

ROOT = pathlib.Path('/opt/onticards-maintenance/propr/review-service')
FIELDS = {'repository', 'pr', 'head', 'base', 'idempotency_key', 'mode'}


def validate(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('invalid_fields')
    if value['repository'] != 'stepll2026/OntiCards' or type(value['pr']) is not int or not 1 <= value['pr'] <= 9999999:
        raise ValueError('invalid_repository_or_pr')
    if any(not isinstance(value[k], str) or len(value[k]) != 40 or any(c not in '0123456789abcdef' for c in value[k]) for k in ['head', 'base']):
        raise ValueError('invalid_revision')
    raw = json.dumps([value['repository'], value['pr'], value['head'], value['base']], separators=(',', ':')).encode()
    expected = 'review-' + hashlib.sha256(raw).hexdigest()
    if value['idempotency_key'] != expected or value['mode'] not in ['dry_run', 'review', 'status']:
        raise ValueError('invalid_operation_identity')
    return value


def bounded_input():
    result = bytearray()
    deadline = time.monotonic() + 5
    while True:
        left = deadline - time.monotonic()
        if left <= 0 or not select.select([sys.stdin.buffer], [], [], left)[0]:
            raise ValueError('input_timeout')
        part = os.read(sys.stdin.fileno(), 4097 - len(result))
        if not part:
            return validate(json.loads(result))
        result.extend(part)
        if len(result) > 4096:
            raise ValueError('input_too_large')


def invoke(request):
    # All errors after invoking the helper are uncertain, including malformed JSON.
    unknown = {'state': 'invocation_outcome_unknown', 'model_started': None,
               'grant_revocation': 'unknown', 'automatic_retry': False}
    try:
        command = ['/usr/bin/docker', 'exec', '-i',
                   '-e', 'NODE_EXTRA_CA_CERTS=/run/propr-tls/ca.crt',
                   'onticards-propr-api', '/usr/bin/timeout', '-s', 'TERM', '-k', '5', '210',
                   'node', '--use-env-proxy', '/run/propr-review/mcp_review.mjs']
        process = subprocess.run(command, input=json.dumps(request), capture_output=True, text=True,
                                 timeout=225, env={'PATH': '/usr/bin:/bin', 'HOME': '/root'})
        # Native library logs are never returned to the SSH client.
        lines = [line.removeprefix('ONTICARDS_REVIEW_RESULT:') for line in process.stdout.splitlines()
                 if line.startswith('ONTICARDS_REVIEW_RESULT:')]
        if len(lines) != 1:
            return unknown
        value = json.loads(lines[0])
        allowed = {'state', 'repository', 'pr', 'head', 'base', 'idempotency_key', 'mode',
                   'operation_id', 'comment_id', 'comment_url', 'native_state', 'native_lifecycle',
                   'resolved_head', 'grant_revocation', 'grant_scopes', 'grant_repository_count',
                   'native_payload_match', 'model_started', 'automatic_retry', 'reason_code',
                   'checked_at', 'tls_verified', 'fresh_revision', 'review_tool_visible', 'merge_tool_visible',
                   'credential_cleanup_required'}
        if not isinstance(value, dict) or set(value) - allowed:
            return unknown
        if process.returncode != 0 or not isinstance(value.get('state'), str):
            return unknown
        return value
    except Exception:
        return unknown


def main():
    # SSH_ORIGINAL_COMMAND and all incoming environment variables are ignored.
    try:
        request = bounded_input()
    except (ValueError, json.JSONDecodeError):
        return {'state': 'invalid_request', 'model_started': False}
    lock_path = ROOT / 'state/invocation.lock'
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'state': 'busy_no_dispatch', 'model_started': False}
        return invoke(request)


def safe_main():
    try:
        return main()
    except Exception:
        # Even lock cleanup can fail after invoke returned. A top-level failure
        # cannot prove that the native mutation was never attempted.
        return {'state': 'invocation_outcome_unknown', 'automatic_retry': False,
                'model_started': None, 'grant_revocation': 'unknown'}


if __name__ == '__main__':
    print(json.dumps(safe_main(), separators=(',', ':')))
