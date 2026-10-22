"""Build host: reconstruct exact policy13 from fixed upstream and the public full patch."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess

root = Path('/opt/onticards-build')
repo = root / 'propr-src'
target = root / 'propr-policy13-src'
patch = root / 'propr-policy13.patch'
validation = json.loads((root/'propr-policy13-patch-validation.json').read_text())
assert not target.exists(), 'Refuse to overwrite an existing policy13 source'
assert hashlib.sha256(patch.read_bytes()).hexdigest() == validation['patch_sha256']
assert validation['upstream_commit'] == '42931b1502eb03ac299f14e306811736fab51eb4'
index = root / 'policy13-source.index'
assert not index.exists(), 'Refuse to reuse an unrelated staging index'
env = {**os.environ, 'GIT_INDEX_FILE': str(index)}
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),*args], env=env)
try:
    git('read-tree', validation['upstream_commit'])
    git('apply','--cached','--check',str(patch)); git('apply','--cached',str(patch))
    assert git('write-tree').decode().strip() == validation['applied_tree']
    target.mkdir()
    git('checkout-index','--all','--prefix',str(target)+'/')
finally:
    index.unlink(missing_ok=True)
for item in validation['delta_files']:
    assert hashlib.sha256((target/item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
marker = {'verified_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'upstream': validation['upstream_commit'], 'tree': validation['applied_tree'],
          'patch_sha256': validation['patch_sha256'], 'delta_sha256': validation['delta_sha256'],
          'exact_delta_files': len(validation['delta_files']), 'status':'verified',
          'worktree_wide_copy':False, 'private_archive_required':False}
(target/'.onticards-source-verified.json').write_text(json.dumps(marker,indent=2)+'\n')
print(json.dumps(marker))
