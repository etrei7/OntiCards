"""Exercise the real entry's session lifecycle against the app's invalidation contract."""
import io, json, os, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch

class EntrySessionTests(unittest.TestCase):
 def execute(self,stale=False):
  with tempfile.TemporaryDirectory() as d:
   results=Path(d)/'results';results.mkdir()
   if stale:(results/'old-checks.json').write_text('{}')
   calls=[];state={'rotated':False,'cross_second':False}
   class Response:
    def __init__(self,data,ok=True):self.data=data;self.ok=ok
    def raise_for_status(self):
     if not self.ok:raise RuntimeError('401: revoked synthetic session')
    def json(self):return self.data
   def request(url,json=None,headers=None,**kwargs):
    path=url.split('/console/api')[-1];token=(headers or {}).get('Authorization');calls.append((path,token))
    if path=='/login':return Response({'code':200,'data':{'token':'fresh-session' if state['rotated'] and state['cross_second'] else 'same-second-session' if state['rotated'] else 'old-session'}})
    if path=='/user':return Response({'data':{'id':1}})
    if path=='/change_password':state['rotated']=True;return Response({'code':200})
    if path=='/model_config':
     if token!='fresh-session':return Response({},False)
     return Response({'code':200,'data':[]})
    raise AssertionError('Unexpected API call')
   def sleep(seconds):
    self.assertGreaterEqual(seconds,1.0);self.assertLessEqual(seconds,1.1)
    self.assertTrue(state['rotated']);state['cross_second']=True
   source=Path(__file__).with_name('test_entry.py').read_text().split("api = subprocess.run",1)[0]
   source=source.replace("Path('/results')",repr(str(results))).replace("RESULTS = "+repr(str(results)),"RESULTS = Path("+repr(str(results))+")")
   source=source.replace("Path('/tmp/synthetic-admin.json')","Path("+repr(str(Path(d)/'credentials.json'))+")")
   env={'ONTICARDS_PREVIEW_URL':'http://fixture','ONTICARDS_MODEL_TEST':'1'}
   fake=types.SimpleNamespace(post=request,get=request)
   lease={'model':'fixture-chat','embedding_model':'fixture-embedding','base_url':'http://fixture/v1','api_key':'synthetic'}
   with patch.dict(os.environ,env),patch.dict('sys.modules',{'requests':fake}),patch('sys.stdin',io.StringIO(json.dumps(lease))),patch('time.sleep',side_effect=sleep),patch('subprocess.run',return_value=types.SimpleNamespace(returncode=0)):
    exec(compile(source,'actual_test_entry.py','exec'),{})
   return calls
 def test_password_rotation_requires_new_session_before_model_configuration(self):
  calls=self.execute();model=[token for path,token in calls if path=='/model_config']
  self.assertEqual(model,['fresh-session']*3)
  self.assertEqual(sum(path=='/login' for path,_ in calls),2)
 def test_old_results_are_rejected_before_api_or_model_work(self):
  with self.assertRaisesRegex(AssertionError,'empty'):self.execute(stale=True)

if __name__=='__main__':unittest.main(verbosity=2)
