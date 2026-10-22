"""Native localhost-only transport fixture; zero production credentials/model/GitHub."""
import copy,json,uuid
from pathlib import Path
root=Path(__file__).parent
raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':45}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
child=json.loads((root/'bounded-get.workflow.json').read_text(encoding='utf-8'));child['id']='onticardsBoundedGetProbeChildV1';child['name']='OntiCards bounded GET localhost fixture child'
for n in child['nodes']:
 n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,child['id']+'/'+n['name']))
 if n['name']=='Validate bounded fixed repository GET':n['parameters']['jsonOutput']=n['parameters']['jsonOutput'].replace('https://api.github.com/repos/stepll2026/OntiCards/','http://127.0.0.1:18127/webhook/onticards-get-fixture-v1?')
 if n['type'].endswith('httpRequest'):
  n['parameters']['options'].pop('proxy',None);n['parameters']['options'].pop('pagination',None);n['parameters']['headerParameters']['parameters']=[{'name':'Accept','value':'application/json'}]
f=Builder('onticardsBoundedGetTransportV1')
f.node('Fixture GET','webhook',{'httpMethod':'GET','path':'onticards-get-fixture-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-get-fixture-v1')
f.table('Ensure fixture counters','onticards_get_fixture_v1',[('case_key','string'),('case_mode','string'),('request_count','number')])
f.row('Read fixture counter','onticards_get_fixture_v1','get','case_key','={{ $("Fixture GET").first().json.query.key }}',alwaysOutputData=True)
f.set('Increment fixture counter','={{ {case_key:$("Fixture GET").first().json.query.key,case_mode:$("Fixture GET").first().json.query.mode,request_count:Number($json.request_count||0)+1} }}')
f.row('Persist fixture counter','onticards_get_fixture_v1','upsert','case_key','={{ $json.case_key }}')
f.respond('Return controlled response','={{ $json.case_mode==="empty200"&&$json.request_count===1?{}:[{fixture:true,request_count:$json.request_count}] }}','={{ $json.case_mode==="always503"||($json.case_mode==="recover503"&&$json.request_count===1)?503:200 }}')
f.chain(['Fixture GET','Ensure fixture counters','Read fixture counter','Increment fixture counter','Persist fixture counter','Return controlled response'])
p=Builder('onticardsBoundedGetProbeV1')
p.node('Local retry probe','webhook',{'httpMethod':'POST','path':'onticards-get-probe-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-get-probe-v1')
p.set('Select fixed fixture','={{ (()=>{const q=$json.body;if(!["recover503","empty200","always503","valid"].includes(q.mode)||!/^[a-z0-9-]+$/.test(q.key))throw new Error("Unknown fixture");return {url:"http://127.0.0.1:18127/webhook/onticards-get-fixture-v1?mode="+q.mode+"&key="+q.key,deadline:Date.now()+30000,token:""};})() }}')
p.node('Retry bounded native child twice','executeWorkflow',{'workflowId':{'__rl':True,'value':child['id'],'mode':'id'},'mode':'once','options':{'waitForSubWorkflow':True}},1.3,executeOnce=True,retryOnFail=True,maxTries=2,waitBetweenTries=100,onError='continueRegularOutput')
p.respond('Return safe native retry result','={{ {fixture:true,complete:$json.complete===true,final_request_count:$json.pages?.[0]?.body?.[0]?.request_count||null,error_present:!!$json.error,github_requests:0,model_requests:0} }}')
p.chain(['Local retry probe','Select fixed fixture','Retry bounded native child twice','Return safe native retry result'])
(root/'bounded-get-probe.workflow.json').write_text(json.dumps([child,f.workflow('OntiCards native GET transport fixture'),p.workflow('OntiCards native bounded GET retry probe')],ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'workflows':3,'fixture_cases':4,'production_credentials':0,'github_requests':0,'model_requests':0}))
