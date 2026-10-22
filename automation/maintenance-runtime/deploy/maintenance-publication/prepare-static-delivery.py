"""Freeze the already-validated Nginx static publisher to the reviewed delivery ZIP."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
receipt=json.loads((root/'evidence/maintenance-final-package.json').read_text(encoding='utf-8'))
source=(root/'deploy/n8n-preview-ci/publish_static_pr26_evidence.py').read_text(encoding='utf-8')
slug='maintenance-20261023'
changes={
 'PR26 rootless r4 allowlist':'OntiCards final delivery allowlist',
 'pr26-rootless-3105-public-evidence.zip':'maintenance-20261023-public.zip',
 '1d3f5a35ba1a3ddf6dfaaf01db559fd514257cb67cea5f11e10085c73d94842c':receipt['public_zip_sha256'],
 'pr26-rootless-3105':slug,
 "len(expected) == 36":f"len(expected) == {receipt['public_files']-1}",
 "len(archive.namelist()) == 37":f"len(archive.namelist()) == {receipt['public_files']}",
 "'file_count':37":f"'file_count':{receipt['public_files']}",
 'nginx.before-pr26-rootless-':'nginx.before-maintenance-delivery-',
 'pr26-rootless-static-publication.json':'maintenance-final-static-publication.json',
}
for old,new in changes.items():
 assert old in source,old
 source=source.replace(old,new)
path=root/'deploy/maintenance-publication/publish-static-delivery.py'
path.write_text(source,encoding='utf-8')
print(json.dumps({'script':str(path),'files':receipt['public_files'],'zip_sha256':receipt['public_zip_sha256']}))
