"""Native response-redaction and automatic-publication selection fixtures."""
import copy,json,uuid
from pathlib import Path
from native_response_audit import add_response_audit
root=Path(__file__).parent;raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':30}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
Builder.set=lambda self,name,expr,**extra:self.node(name,'set',{'mode':'raw','jsonOutput':expr,'options':{}},3.4,**extra)
a=Builder('onticardsSafeResponseProbeV1')
a.node('Native safe response probe','webhook',{'httpMethod':'POST','path':'onticards-safe-response-probe-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-safe-response-probe-v1')
catalog={'normal':{'choices':[{'message':{'content':'synthetic safe content'}}],'usage':{'total_tokens':1}},'redaction':{'choices':[{'message':{'content':'Bearer FIXTURE_SECRET_123 token="FIXTURE_SECRET_456" api_key=FIXTURE_SECRET_789 sk-FIXTURE_SECRET_LONG ghp_FIXTURESECRET123456'}}]},'http_error':{'statusCode':401,'body':{'error':{'message':'Authorization: Bearer FIXTURE_SECRET_ERROR'}},'headers':{'authorization':'FIXTURE_SECRET_HEADER'}},'timeout':{'error':{'message':'ETIMEDOUT timeout containing FIXTURE_SECRET_ERROR','request':{'headers':{'Authorization':'FIXTURE_SECRET_HEADER'}}}},'bounded':{'choices':[{'message':{'content':'X'*17000}}]}}
a.set('Frozen response diagnostic catalog',json.dumps(catalog))
a.set('Fixture model response','={{ $("Frozen response diagnostic catalog").first().json[$("Native safe response probe").first().json.body.case] }}')
audit=add_response_audit(a,'safe-fixture','Fixture model response','"fixture:response"')
a.respond('Return only safe audit','={{ $json }}')
a.chain(['Native safe response probe','Frozen response diagnostic catalog','Fixture model response',audit['ensure'],audit['sanitize'],audit['persist'],'Return only safe audit'])
p=Builder('onticardsAutomaticSelectionProbeV1')
p.node('Native automatic selection probe','webhook',{'httpMethod':'POST','path':'onticards-automatic-selection-probe-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-automatic-selection-probe-v1')
def approval(key):return {'event_key':key,'thread_key':'fixture:'+key,'status':'approved','createdAt':'2026-10-22T00:00:00Z','approval':json.dumps({'event_key':key,'approval_origin':'independent_semantic_review','policy_version':'normal-consultation-source-review-v1'})}
selection={
 'published_issue29':{'approvals':[approval('initial29'),approval('followup29')],'states':[{'event_key':'initial29','status':'published_confirmed','comment_id':'6339994362'},{'event_key':'followup29','status':'published_reconciled','comment_id':'6340579230'}],'conversations':[{'thread_key':'fixture:initial29','publication_ids':'["6339994362","6340579230"]'},{'thread_key':'fixture:followup29','publication_ids':'["6339994362","6340579230"]'}]},
 'one_pending':{'approvals':[approval('pending')],'states':[{}],'conversations':[{}]},
 'unknown_and_new':{'approvals':[approval('unknown'),approval('new')],'states':[{'event_key':'unknown','status':'posting_unknown','updatedAt':'2026-10-22T12:00:00Z'}],'conversations':[{}]},
 'untrusted_policy':{'approvals':[{**approval('wrong'),'approval':json.dumps({'event_key':'wrong','approval_origin':'issue_body','policy_version':'normal-consultation-source-review-v1'})}],'states':[{}],'conversations':[{}]}}
p.set('Frozen native selection catalog',json.dumps(selection))
p.set('Select native selection fixture','={{ $("Frozen native selection catalog").first().json[$("Native automatic selection probe").first().json.body.case] }}')
p.set('Trusted publication policy',json.dumps({'repository':'stepll2026/OntiCards','publication_enabled':True,'automatic_enabled':True,'semantic_policy_version':'normal-consultation-source-review-v1'}))
previous='Trusted publication policy'
for name,key in [('Read native approved ordinary replies','approvals'),('Read all sticky publication receipts','states'),('Read publication conversation states','conversations')]:
 p.set('Prepare '+key,'={{ {rows:$("Select native selection fixture").first().json.'+key+'} }}')
 p.node(name,'splitOut',{'fieldToSplitOut':'rows','options':{}},1)
 p.chain([previous,'Prepare '+key,name]);previous=name
original=json.loads((root/'persistent-publication.workflow.json').read_text(encoding='utf-8'))
node=copy.deepcopy(next(n for n in original['nodes']if n['name']=='Select at most one native approved reply'));node['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,p.wid+'/select'));p.nodes.append(node)
p.respond('Return selected approval only','={{ {event_key:$json.approval?.event_key||null,model_calls:0,github_posts:0} }}')
p.chain(['Native automatic selection probe','Frozen native selection catalog','Select native selection fixture','Trusted publication policy']);p.chain([previous,'Select at most one native approved reply','Return selected approval only'])
workflows=[a.workflow('OntiCards safe diagnostic native fixture'),p.workflow('OntiCards automatic selection native fixture')]
for w in workflows:
 assert not any(n['type'].endswith(('httpRequest','executeWorkflow','scheduleTrigger'))for n in w['nodes'])
 for n in w['nodes']:
  for value in n['parameters'].values():
   if isinstance(value,str)and value.startswith('={{'):assert '}}'not in value[3:-2],n['name']
(root/'policy-boundary-probe.workflow.json').write_text(json.dumps(workflows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'workflows':2,'http_nodes':0,'model_calls':0,'cases':9}))
