"""Exercise the actual publication graph against localhost native transport only."""
import copy,hashlib,json,uuid
from pathlib import Path
root=Path(__file__).parent
raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':90}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
def expr(s):
 if s.startswith('={{'):
  q=s[3:-2]
  while '}}'in q:q=q.replace('}}','} }')
  return '={{'+q+'}}'
 return s
Builder.set=lambda self,name,s,**kw:self.node(name,'set',{'mode':'raw','jsonOutput':expr(s),'options':{}},3.4,**kw)
# This fixture has no real authorization credentials and cannot address GitHub.
t=Builder('onticardsPublicationTransportProbeV1')
comments='onticards_pub_probe_comments_v2';counter='onticards_pub_probe_posts_v2'
for method in ['GET','POST']:
 t.node(method+' fixture','webhook',{'httpMethod':method,'path':'onticards-pub-transport-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-pub-transport-v1-'+method)
 t.table('Ensure comments '+method,comments,[('case_key','string'),('body','string')]);t.link(method+' fixture','Ensure comments '+method)
t.row('Read fixture comments',comments,'get','case_key','={{ $("GET fixture").first().json.query.key }}',alwaysOutputData=True)
t.respond('Return comments or controlled failure',expr('={{ $("GET fixture").first().json.query.mode==="read_failure"?{fixture_error:true}:$input.all().map(i=>i.json).filter(r=>r.body).map(r=>({id:r.id,body:r.body,html_url:"https://github.com/stepll2026/OntiCards/issues/90001#issuecomment-"+r.id,user:{id:346235449,login:"onticards-maintainer-stepll2026[bot]",type:"Bot"}})) }}'),'={{ $("GET fixture").first().json.query.mode==="read_failure"?503:200 }}')
t.chain(['Ensure comments GET','Read fixture comments','Return comments or controlled failure'])
t.table('Ensure POST counters',counter,[('case_key','string'),('post_count','number')]);t.row('Read POST counter',counter,'get','case_key','={{ $("POST fixture").first().json.query.key }}',alwaysOutputData=True)
t.set('Increment actual fixture POST count','={{ {case_key:$("POST fixture").first().json.query.key,post_count:Number($json.post_count||0)+1} }}')
t.row('Persist actual POST count',counter,'upsert','case_key','={{ $json.case_key }}')
t.iff('Fixture remote stores comment','={{ $("POST fixture").first().json.query.mode!=="absent_504" }}')
t.set('Fixture remote comment','={{ {case_key:$("POST fixture").first().json.query.key,body:$("POST fixture").first().json.body.body} }}')
t.row('Insert fixture remote comment',comments,'insert',None,None)
t.respond('Return stored response','={{ {fixture:true,stored:true} }}','={{ $("POST fixture").first().json.query.mode==="created_504"?504:201 }}')
t.respond('Return unknown absent','={{ {fixture:true,unknown:true} }}',504)
t.chain(['Ensure comments POST','Ensure POST counters','Read POST counter','Increment actual fixture POST count','Persist actual POST count','Fixture remote stores comment','Fixture remote comment','Insert fixture remote comment','Return stored response']);t.link('Fixture remote stores comment','Return unknown absent',1)

w=json.loads((root/'persistent-publication.workflow.json').read_text(encoding='utf-8'));w['id']='onticardsPublicationNativeProbeV1';w['name']='OntiCards full publication graph localhost fixture';w['settings']=settings
w['nodes']=[n for n in w['nodes']if not n['type'].endswith('scheduleTrigger')];w['connections'].pop('Every five minutes approved publication',None)
for n in w['nodes']:
 n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+n['name']))
 if n['type'].endswith('dataTable'):
  p=n['parameters']
  if 'tableName'in p:p['tableName']='fixture_pub_v2_'+p['tableName']
  if 'dataTableId'in p:p['dataTableId']['value']='fixture_pub_v2_'+p['dataTableId']['value']
 n.pop('credentials',None)
def node(name):return next(n for n in w['nodes']if n['name']==name)
def as_set(name,s):
 n=node(name);n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':expr(s),'options':{}};n['retryOnFail']=False
def link(a,b,index=0):
 c=w['connections'].setdefault(a,{'main':[]})['main']
 while len(c)<=index:c.append([])
 c[index]=[{'node':b,'type':'main','index':0}]
def append(name,kind,p,version=1,**kw):
 n={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'parameters':p,'position':[len(w['nodes'])*190,0],**kw};w['nodes'].append(n);return n
cases={}
for idx,key in enumerate(['success','unknown_absent','unknown_found','changed_source','cap','bad_asked','ai_takeover','unknown_ai']):
 ek=hashlib.sha256(('fixture-pub-v2:'+key).encode()).hexdigest();num=90201+idx
 source={'repository':'stepll2026/OntiCards','thread_key':'stepll2026/OntiCards#'+str(num),'number':num,'kind':'issue','event':{'id':1234,'body':'synthetic deployment material'},'known_fields':{},'thread':{'id':num,'number':num,'title':'synthetic fixture','body':'synthetic source','state':'open','discussion':[],'inline':[],'reviews':[]},'repository_context':{'commit_sha':'f'*40}}
 ss=json.dumps(source,ensure_ascii=False,separators=(',',':'));sh=hashlib.sha256(ss.encode()).hexdigest();body='【AI辅助｜合成测试】请补充部署方式。\n<!-- onticards-triage:'+ek+' -->'
 approval={'event_key':ek,'source_hash':sh,'body_hash':hashlib.sha256(body.encode()).hexdigest(),'body':body,'reviewed':True,'asked_fields_reviewed':True,'asked_fields':['deployment_method']if key!='bad_asked'else['not_a_field'],'observed_fields':[]}
 draft={'event_key':ek,'thread_key':source['thread_key'],'source_hash':sh,'source_snapshot':ss,'status':'awaiting_semantic_review','draft':json.dumps({'missing_evidence':['deployment_method','api_image_identity']})}
 conversation={'thread_key':source['thread_key'],'model_calls':1,'reply_count':3 if key=='cap' else 0,'pending_event':ek,'pending_state':'model_request_started','known_fields':'{}','asked_fields':'[]','answered_human_ids':'[]','publication_ids':'[]'}
 cases[key]={'approval':approval,'draft':draft,'conversation':conversation,'source':source}
append('Frozen synthetic approval catalog','set',{'mode':'raw','jsonOutput':json.dumps(cases,ensure_ascii=False),'options':{}},3.4)
link('Local approved publication reconciliation','Frozen synthetic approval catalog');link('Frozen synthetic approval catalog','Trusted reviewed approval')
as_set('Trusted reviewed approval','={{ (()=>{const catalog=$("Frozen synthetic approval catalog").first().json;const input=$("Local approved publication reconciliation").first().json.body,c=catalog[input.case];if(!c||!["normal","read_failure","recover","changed_approval","ai_added"].includes(input.stage))throw new Error("Unknown fixture");return {repository:"stepll2026/OntiCards",publication_enabled:true,...c,case_key:input.case,stage:input.stage};})() }}')
hook=node('Local approved publication reconciliation');hook['parameters'].update(path='onticards-pub-native-probe-v1',responseMode='responseNode');hook['webhookId']='onticards-pub-native-probe-v1'
as_set('Read approved original draft','={{ $("Trusted reviewed approval").first().json.draft }}')
append('Ensure fixture conversations','dataTable',{'resource':'table','operation':'create','tableName':'fixture_pub_v2_onticards_conversation_v1','columns':{'column':[{'name':k,'type':'number'if k in ['model_calls','reply_count']else'string'}for k in cases['success']['conversation']]},'options':{'createIfNotExists':True}},1.1)
seedread=copy.deepcopy(node('Read original conversation'));seedread['name']='Read fixture seed';seedread['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/Read fixture seed'));w['nodes'].append(seedread)
append('Fixture seed required','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'seed','leftValue':'={{ !$json.thread_key }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
append('Project fixture seed','set',{'mode':'raw','jsonOutput':'={{ $("Trusted reviewed approval").first().json.conversation }}','options':{}},3.4)
append('Insert fixture conversation','dataTable',{'resource':'row','operation':'insert','dataTableId':{'__rl':True,'value':'fixture_pub_v2_onticards_conversation_v1','mode':'name'},'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
link('Read approved original draft','Ensure fixture conversations');link('Ensure fixture conversations','Read fixture seed');link('Read fixture seed','Fixture seed required');link('Fixture seed required','Project fixture seed');link('Project fixture seed','Insert fixture conversation');link('Insert fixture conversation','Read original conversation');link('Fixture seed required','Read original conversation',1)
as_set('Sign publication App JWT','{"fixture":true}')
as_set('Mint bounded publication token',json.dumps({'statusCode':201,'body':{'permissions':{'issues':'write','pull_requests':'read','contents':'read','metadata':'read'}}}))
as_set('Verify publication repository scope',json.dumps({'statusCode':200,'body':{'total_count':1,'repositories':[{'full_name':'stepll2026/OntiCards'}]}}))
as_set('Read fresh issue source','={{ (()=>{const c=$("Trusted reviewed approval").first().json,s=c.source;return {statusCode:200,body:{...s.thread,labels:c.case_key==="ai_takeover"||c.stage==="ai_added"?[{name:"AI"}]:[],body:c.case_key==="changed_source"?"modified":s.thread.body,html_url:"https://github.com/stepll2026/OntiCards/issues/"+s.number}};})() }}')
as_set('Read fresh PR or issue details','={{ $("Read fresh issue source").first().json }}')
for name in ['Read complete inline or issue discussion','Read complete reviews or issue discussion']:as_set(name,'{"statusCode":200,"body":[],"headers":{}}')
as_set('Verify current source commit','{"statusCode":200,"body":{"sha":"'+('f'*40)+'"}}')
as_set('Revoke bounded publication token','{"fixture":true,"statusCode":204}')
for name in ['Read complete fresh discussion','Publish reviewed body once','GET reconcile actual published comments']:
 n=node(name);p=n['parameters'];p.pop('sendHeaders',None);p.pop('headerParameters',None);p['options']={'timeout':10000,'response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}
 mode='c.stage==="read_failure"?"read_failure":"normal"'if name=='Read complete fresh discussion'else('["unknown_absent","unknown_ai"].includes(c.case_key)?"absent_504":c.case_key==="unknown_found"?"created_504":"normal"'if name=='Publish reviewed body once'else'c.case_key.startsWith("unknown_")&&c.stage==="normal"?"read_failure":"normal"')
 p['url']=expr('={{ (()=>{const c=$("Trusted reviewed approval").first().json;return "http://127.0.0.1:18127/webhook/onticards-pub-transport-v1?key=v2:"+c.case_key+"&mode="+('+mode+');})() }}')
append('Return fixture outcome','respondToWebhook',{'respondWith':'json','responseBody':'={{ {fixture:true,result:$json,github_requests:0,model_requests:0} }}','options':{}},1.4)
for name in ['Persist safe publication run receipt','No approved publication','Approval rejected no network']:link(name,'Return fixture outcome')
(root/'publication-native-probe.workflow.json').write_text(json.dumps([t.workflow('OntiCards native local publication transport'),w],ensure_ascii=False,indent=2),encoding='utf-8')
(root/'publication-native-probe-cases.json').write_text(json.dumps({k:{'event_key':v['approval']['event_key'],'thread_key':v['draft']['thread_key']}for k,v in cases.items()},indent=2))
print(json.dumps({'workflows':2,'publisher_nodes':len(w['nodes']),'transport_nodes':len(t.nodes),'github_requests':0,'model_nodes':0,'credentials':0}))
