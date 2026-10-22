"""Actual product session precision probe. No model configuration or inference request."""
import base64,json,os,time
from pathlib import Path
import requests
base=os.environ['ONTICARDS_PREVIEW_URL'];s=requests.Session();s.trust_env=False
password='admin123'
def call(path,body=None,token=None):
 headers={'Authorization':token} if token else {}
 r=s.request('POST' if body is not None else 'GET',base+'/console/api'+path,json=body,headers=headers,timeout=20)
 try:j=r.json()
 except ValueError:j={}
 return r.status_code,j
def login():
 status,j=call('/login',{'username':'admin','password':password});assert status==j['code']==200
 return j['data']['token']
token=login();initial=call('/model_config',token=token)[0]
profile=call('/user',token=token)[1]['data']
while time.time()%1>0.15:time.sleep(0.01)
new='SyntheticAuthPrecision9!';status,j=call('/change_password',{'id':profile['id'],'old_password':password,'new_password':new},token);assert status==j['code']==200
password=new;immediate=login();parts=immediate.split('.');payload=json.loads(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1]))%4)))
same_status,same=call('/model_config',token=immediate)
while time.time()<payload['iat']+1.05:time.sleep(0.01)
renewed=login();later_status=call('/model_config',token=renewed)[0]
reason=json.dumps(same).lower()
record={'initial_model_config_status':initial,'immediate_renewed_status':same_status,'jwt_iat_is_integer':type(payload['iat']) is int,
 'immediate_denial_is_password_reset':('issued before password reset' in reason),'cross_second_renewed_status':later_status,
 'model_config_writes':0,'provider_requests':0,'credentials_in_output':False}
Path('/results/auth-session-probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
assert initial==later_status==200 and same_status==401 and record['immediate_denial_is_password_reset']
