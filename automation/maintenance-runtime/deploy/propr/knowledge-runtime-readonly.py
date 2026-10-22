"""Safe, read-only snapshot. No credentials or prompt bodies are emitted."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

root = Path('/opt/onticards-maintenance/propr')
db = sqlite3.connect(f'file:{root}/data/propr.sqlite?mode=ro', uri=True)
def config(key, default):
    row = db.execute('SELECT value FROM system_configs WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else default
summary = config('summarization', {'enabled': False, 'agent_alias': ''})
repos = config('repos_to_monitor', [])
instructions = json.loads((root/'opencode/opencode.json').read_text()).get('instructions', [])
source_commit = '10c6862d4c7325c85618f86455aacf9d10c088b5'
files = []
for filename in ('AGENTS.md', 'repository-context.md', 'response-policy.md'):
    p = root/'opencode/knowledge'/source_commit/filename
    files.append({'name': filename, 'exists': p.is_file(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None})
print(json.dumps({'observed_at': datetime.now(timezone.utc).isoformat(),
    'summarization': {k: summary.get(k) for k in ('enabled', 'agent_alias', 'fallback_agent_alias')},
    'repositories': [{k: r.get(k) for k in ('name', 'enabled', 'baseBranch', 'contextRepositories', 'autoResolveMergeConflicts')} for r in repos],
    'instructions': instructions, 'instruction_source_commit': source_commit, 'instruction_files': files,
    'indexed_repositories': [dict(zip(('full_name', 'branch', 'indexing_status', 'last_indexed_hash'), row)) for row in db.execute('SELECT full_name, branch, indexing_status, last_indexed_hash FROM repositories WHERE lower(full_name)=?', ('stepll2026/onticards',))],
    'read_only': True, 'models_invoked': 0}, ensure_ascii=False, indent=2))
db.close()
