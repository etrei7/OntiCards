"""Trusted existing API and browser tests; no PR test scripts or model secret."""
import json
import os
from pathlib import Path
import secrets
import sys
import subprocess
import time
import xml.etree.ElementTree as ET
import requests

BASE = os.environ['ONTICARDS_PREVIEW_URL']
RESULTS = Path('/results')
credentials = Path('/tmp/synthetic-admin.json')
assert RESULTS.is_dir() and not any(RESULTS.iterdir()), 'Expected empty isolated test results directory'
def request(path, body=None, token=None):
    headers = {'Authorization': token} if token else {}
    response = requests.post(BASE+path,json=body,headers=headers,timeout=30) if body is not None else requests.get(BASE+path,headers=headers,timeout=30)
    response.raise_for_status()
    return response.json()

login = request('/console/api/login', {'username':'admin','password':'admin123'})
assert login.get('code') == 200, 'Synthetic initial login rejected'
token = login['data']['token']
profile = request('/console/api/user',token=token)
password = secrets.token_urlsafe(32)
change = request('/console/api/change_password', {'id':profile['data']['id'],'old_password':'admin123','new_password':password},token)
assert change.get('code') == 200, 'Synthetic password rotation rejected'
# Existing product JWT iat is integer seconds while password_reset_at has microseconds.
# A real no-model probe proves same-second re-login is rejected; cross that boundary.
time.sleep(1.05)
# The existing application revokes sessions on password rotation.
login = request('/console/api/login', {'username':'admin','password':password})
assert login.get('code') == 200, 'Synthetic renewed login rejected'
token = login['data']['token']
credentials.write_text(json.dumps({'username':'admin','password':password}))
credentials.chmod(0o600)
os.environ['ONTICARDS_PREVIEW_CREDENTIALS'] = str(credentials)
os.environ['ONTICARDS_EVIDENCE_DIR'] = '/results/browser'
model_enabled=os.environ.get('ONTICARDS_MODEL_TEST')=='1'
if model_enabled:
    # Only a bound short-lived native New API token enters this trusted process.
    # It is configured through the application's existing admin model API.
    lease=json.loads(sys.stdin.read(4097));assert len(json.dumps(lease))<=4096
    existing=request('/console/api/model_config',token=token)['data']
    for model_class,name,path in [('base',lease['model'],'/chat/completions'),('embedding',lease['embedding_model'],'/embeddings')]:
        assert not any(x['model_class']==model_class for x in existing),'Expected fresh isolated model configuration'
        result=request('/console/api/model_config',{'model_name':name,'model_type':'qwen','model_class':model_class,
            'url':lease['base_url']+path,'model_api_key':lease['api_key']},token)
        assert result.get('code')==200,'Short-lived model configuration failed'
    del lease
    os.environ['ONTICARDS_PRODUCT_EVIDENCE_DIR']='/results/product'
    product=subprocess.run(['python','/trusted-bundle/exercise-product-flow.py'],cwd='/trusted-tests').returncode
    assert product==0,'Real model product flow failed; no model retry'
api = subprocess.run(['python','-m','pytest','-q','test_preview_api.py','--junitxml=/results/api.xml'],cwd='/trusted-tests').returncode
browser_args=['node','node_modules/@playwright/test/cli.js','test']
if not model_enabled:browser_args+=['--grep-invert','真实数据卡片、问数总额250与治理报告详情']
browser = subprocess.run(browser_args,cwd='/trusted-tests').returncode
suite = ET.parse(RESULTS/'api.xml').getroot().find('testsuite')
api_count = int(suite.attrib['tests']) if suite is not None else 0
pw = json.loads((RESULTS/'browser/results.json').read_text())
stats = pw['stats']
record = {'api_exit':api,'api_tests':api_count,'browser_exit':browser,'browser_expected':stats['expected'],'browser_unexpected':stats['unexpected'],'browser_skipped':stats['skipped'],
          'model_business_test':'real_chat_embedding_flow' if model_enabled else 'not_run_in_non_model_phase; target retained',
          'long_lived_model_or_github_or_ssh_secret_supplied':False}
(RESULTS/'checks.json').write_text(json.dumps(record,indent=2)+'\n')
credentials.unlink()
assert api == browser == 0 and api_count == 7 and stats['expected'] == (3 if model_enabled else 2) and stats['unexpected'] == stats['skipped'] == 0, 'Trusted test assertions failed'
