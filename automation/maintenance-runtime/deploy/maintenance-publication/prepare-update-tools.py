"""Reuse the reviewed Git-object exporter/publisher for a single PR30 fast-forward.

No network or GitHub write occurs here. The allowlist and exact object digest are
frozen after the final staging review. Main is never a mutation target.
"""
import argparse
import json
from pathlib import Path

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--allowlist', type=Path, required=True)
parser.add_argument('--export-validation', type=Path)
args = parser.parse_args()
paths = json.loads(args.allowlist.read_text(encoding='utf-8'))['paths']
assert paths and len(set(paths)) == len(paths)
assert all(not p.startswith('/') and '..' not in Path(p).parts for p in paths)
base = '10c6862d4c7325c85618f86455aacf9d10c088b5'
original_base = 'c8e3dfee68d398a37842fc332f73af40a56f02a7'
allowed = 'ALLOWED_FILES = ' + repr(set(sorted(paths))) + '\n'

def replace_allowlist(source):
    start = source.index('ALLOWED_FILES = {')
    end = source.index('\n}', start) + 2
    return source[:start] + allowed.rstrip() + source[end:]

source = (here/'export-git-data.py').read_text(encoding='utf-8')
source = replace_allowlist(source).replace("BASE = '"+original_base+"'", "BASE = '"+base+"'")
source = source.replace('Export the approved linear maintenance range', 'Export the reviewed PR30 update range')
(here/'export-update-git-data.py').write_text(source, encoding='utf-8')
if not args.export_validation:
    print(json.dumps({'prepared': 'exporter', 'base': base, 'allowed_files': len(paths)}))
    raise SystemExit(0)

audit = json.loads(args.export_validation.read_text(encoding='utf-8'))
assert audit['passed'] and audit['base'] == base and audit['commit_count'] == 1
assert sorted(audit['allowed_paths']) == sorted(paths)
head, digest = audit['head'], audit['data_sha256']
source = (here/'publish-exact-branch.py').read_text(encoding='utf-8')
source = replace_allowlist(source)
source = source.replace("BASE = '"+original_base+"'", "BASE = '"+base+"'")
source = source.replace("HEAD = '"+base+"'", "HEAD = '"+head+"'")
source = source.replace('62c518812804fcd48fb2ca3e0e79ac5498bfcc92738ff622ccf69a347b6c8e4a', digest)
source = source.replace('maintenance-branch-publication-api.json', 'maintenance-update-publication-api.json')
source = source.replace('maintenance-branch-readonly.json', 'maintenance-update-readonly.json')
source = source.replace('incoming/maintenance-git-data.json', 'incoming/maintenance-update-git-data.json')
source = source.replace("len(data['commits']) != 4 or len(data['blobs']) != 30", f"len(data['commits']) != 1 or len(data['blobs']) != {audit['unique_blob_count']}")
source = source.replace("if method not in ('GET', 'POST'):", "if method not in ('GET', 'POST', 'PATCH'):")
source = source.replace("raise SafeFailure('ref_updates_and_deletions_forbidden')", "raise SafeFailure('unsupported_method')\n            if method == 'PATCH' and (suffix != 'refs/heads/' + BRANCH or payload != {'sha': HEAD, 'force': False}):\n                raise SafeFailure('only_exact_nonforce_pr30_update_allowed')")
source = source.replace("if result['main_before'] is None:", "if result['main_before'] != '"+original_base+"':")
source = source.replace("not in (None, HEAD)", "not in (BASE, HEAD)")
source = source.replace("if immediately_before is None:", "if immediately_before == BASE:")
source = source.replace("created_ref = api('POST', 'refs', {'ref': 'refs/heads/' + BRANCH, 'sha': HEAD})", "created_ref = api('PATCH', 'refs/heads/' + BRANCH, {'sha': HEAD, 'force': False})\n                result['ref_updates'] += 1")
source = source.replace('created_exact_branch_git_data_api', 'fast_forwarded_exact_pr30_branch_git_data_api')
source = source.replace('# POST create only: a race cannot overwrite an existing branch.', '# Non-force update: a divergent concurrent commit causes GitHub to reject the update.')
source = source.replace('This one-shot adapter creates only the approved branch after exact SHA matching.', 'This one-shot adapter fast-forwards only the existing PR30 branch after exact SHA matching.')
source = source.replace('It cannot update a ref, create a\nPR, merge, or execute repository code.', 'It cannot force-push, create a PR, merge, or execute repository code.')
(here/'publish-update-branch.py').write_text(source, encoding='utf-8')
print(json.dumps({'prepared': 'pinned publisher', 'base': base, 'head': head, 'data_sha256': digest, 'allowed_files': len(paths)}))
