"""Prepare existing ProPR/OpenCode configuration; never prints private values."""
import json
import os
from pathlib import Path
import secrets
import shlex
from urllib.parse import urlparse

root = Path('/opt/onticards-maintenance/propr')
root.mkdir(parents=True, exist_ok=True)
root.chmod(0o700)
for name in ('data', 'logs', 'secrets', 'git', 'egress', 'opencode', 'evidence'):
    (root / name).mkdir(exist_ok=True)
    (root / name).chmod(0o700)
model = {}
for line in Path('/opt/onticards-maintenance/secrets/model.env').read_text().splitlines():
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        name, value = line.split('=', 1)
        model[name] = shlex.split(value)[0] if value.strip() else ''
# This maintenance deployment uses the snapshot verified with native tool calls.
# The shared model.env may still name an older product model; it supplies credentials/base URL only.
model_id = 'qwen3.8-max-0902'
config = {
    'instructions': ['/home/node/.config/opencode/instructions/*.md'],
    '$schema': 'https://opencode.ai/config.json',
    'autoupdate': False, 'share': 'disabled',
    'enabled_providers': ['bailian'],
    'model': 'bailian/' + model_id,
    'small_model': 'bailian/' + model_id,
    'agent': {'build': {'steps': 24}, 'plan': {'steps': 12}},
    'provider': {'bailian': {
        'npm': '@ai-sdk/openai-compatible', 'name': 'Bailian (existing account)',
        'options': {'baseURL': model['LLM_BASE_URL'],
                    'apiKey': '{file:/home/node/.config/opencode/api-key}', 'timeout': 300000},
        'models': {model_id: {'name': 'OntiCards maintenance model', 'limit': {'context': 128000, 'output': 8192},
                              'options': {'enable_thinking': False}}},
    }},
}
for path, content in [(root/'opencode'/'opencode.json', json.dumps(config, indent=2)),
                      (root/'opencode'/'api-key', model['DASHSCOPE_API_KEY'])]:
    path.write_text(content)
    path.chmod(0o600)
    os.chown(path, 1000, 1000)
os.chown(root/'opencode', 1000, 1000)
runtime = root / 'runtime.env'
settings = {
    'NODE_ENV': 'production', 'LOG_LEVEL': 'info',
    'ONTICARDS_MAINTENANCE_MODE': '1', 'GH_AUTH_MODE': 'app',
    # Native PR worker falls back to this when CONFIG_REPO is unset.
    'PRIMARY_PROCESSING_LABELS': 'AI',
    'GITHUB_EVENT_INTAKE_MODE': 'polling', 'POLLING_INTERVAL_MS': '300000',
    'PROPR_CONTAINERIZED': '1', 'PROPR_UI_TUNNEL_ENABLED': 'false',
    'DB_FILENAME': '/usr/src/app/data/propr.sqlite', 'DATA_DIR': '/usr/src/app/data',
    'REDIS_HOST': '127.0.0.1', 'REDIS_PORT': '18124', 'WORKER_CONCURRENCY': '1',
    'GITHUB_USER_WHITELIST': 'stepll2026', 'PROPR_ADMIN_USERS': 'stepll2026',
    'GH_PRIVATE_KEY_PATH': '/run/propr-secrets/github-app.pem',
    'DASHBOARD_API_HOST': '127.0.0.1', 'DASHBOARD_API_PORT': '18122',
    'API_PUBLIC_URL': 'http://10.66.66.5:18123', 'FRONTEND_URL': 'http://10.66.66.5:18123',
    'GH_OAUTH_CALLBACK_URL': 'http://10.66.66.5:18123/api/auth/github/callback',
    'AUTH_ALLOW_HTTP_REDIRECT': 'true',
    'AUTH_INSECURE_SESSION_ORIGIN': 'http://10.66.66.5:18123',
    'PROPR_TRUSTED_PROXY_PEERS': '127.0.0.1,::1',
    'PROPR_LIVE_OUTPUT_TTL_SECONDS': '2592000',
    'OPENCODE_CONFIG_PATH': str(root/'opencode'),
    # Native analyze snapshots must be visible to the host Docker daemon at the same path.
    # This is inside the existing git bind, outside the source opencode config tree.
    'OPENCODE_ANALYSIS_ROOT': str(root/'git'/'opencode-analysis'),
    'GIT_CLONES_BASE_PATH': str(root/'git'/'clones'),
    'GIT_WORKTREES_BASE_PATH': str(root/'git'/'worktrees'),
    'GIT_SHALLOW_CLONE_DEPTH': '1',
    'WORKTREE_RETENTION_STRATEGY': 'always_keep', 'WORKTREE_RETENTION_HOURS': '720',
    'OPENCODE_TIMEOUT_MS': '600000', 'MAX_PROVIDER_REPLACEMENTS': '0',
    'INFRA_LOST_REPLACEMENT': 'false',
    'AGENT_CONTAINER_MEMORY_LIMIT': '4g', 'AGENT_CONTAINER_CPU_LIMIT': '2',
    'AGENT_CONTAINER_PIDS_LIMIT': '512', 'AGENT_NETWORK_MODE': 'restricted',
    'AGENT_NETWORK_MODE_ENFORCED': 'true', 'AGENT_NETWORK_IGNORE_REPOSITORY_ALLOW': 'true',
    'AGENT_NETWORK_ALLOW': urlparse(model['LLM_BASE_URL']).hostname,
    'PROPR_EGRESS_SOCKET_DIR': str(root/'egress'), 'HOST_PROPR_EGRESS_SOCKET_DIR': str(root/'egress'),
    'HTTP_PROXY': 'http://127.0.0.1:17891', 'HTTPS_PROXY': 'http://127.0.0.1:17891',
    'NO_PROXY': '127.0.0.1,localhost,10.66.66.5',
}
if runtime.exists():
    old = dict(line.split('=', 1) for line in runtime.read_text().splitlines() if '=' in line)
else:
    old = {}
for name in ('SESSION_SECRET', 'SYSTEM_TASK_SECRET', 'PROPR_CREDENTIAL_ENCRYPTION_KEY'):
    settings[name] = old.get(name) or secrets.token_hex(32)
runtime.write_text(''.join(f'{name}={value}\n' for name, value in settings.items()))
runtime.chmod(0o600)
print(json.dumps({'configuration_prepared': True, 'model': 'bailian/' + model_id,
                  'github_credentials_present': (root/'secrets'/'github-app.pem').exists(),
                  'scope': 'stepll2026/OntiCards', 'secret_values_printed': False}))
