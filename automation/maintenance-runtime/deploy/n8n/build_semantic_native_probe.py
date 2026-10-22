"""Full native review/ledger graph, with source/model transport replaced by fixtures."""
import copy,hashlib,json,uuid
from pathlib import Path
root=Path(__file__).parent
w=json.loads((root/'persistent-semantic-review.workflow.json').read_text(encoding='utf-8'))
w['id']='onticardsSemanticNativeProbeV1';w['name']='OntiCards full native semantic review fixture';w['settings']['executionTimeout']=60
w['nodes']=[n for n in w['nodes']if not n['type'].endswith('scheduleTrigger')];w['connections'].pop('Every five minutes semantic review',None)
for n in w['nodes']:
 n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+n['name']));n.pop('credentials',None)
 if n['type'].endswith('dataTable'):
  p=n['parameters']
  if 'tableName'in p:p['tableName']='fixture_semantic_v3_'+p['tableName']
  if 'dataTableId'in p:p['dataTableId']['value']='fixture_semantic_v3_'+p['dataTableId']['value']
def node(name):return next(n for n in w['nodes']if n['name']==name)
def aset(name,expr):
 n=node(name);n['type']='n8n-nodes-base.set';n['typeVersion']=3.4;n['parameters']={'mode':'raw','jsonOutput':expr,'options':{}}
def append(name,kind,p,version=1,**extra):
 w['nodes'].append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,w['id']+'/'+name)),'name':name,'type':'n8n-nodes-base.'+kind,'typeVersion':version,'parameters':p,'position':[len(w['nodes'])*180,0],**extra})
def link(a,b,index=0):
 c=w['connections'].setdefault(a,{'main':[]})['main']
 while len(c)<=index:c.append([])
 c[index]=[{'node':b,'type':'main','index':0}]
catalog={};flags=['direct_answer','facts_supported','runtime_distinguished','questions_minimal','in_scope','observed_fields_verified','asked_fields_verified']
for case in ['approve','bad_quote','runtime_confusion','known_field_conflict','invalid_json','budget_six','manual31','changed_source','issue29_initial','issue29_followup']:
 eventkey=hashlib.sha256(('semantic-native-v3:'+case).encode()).hexdigest();thread='fixture:semantic-v3:'+case
 body='synthetic consultation: API request failed; no runtime details supplied'
 source={'repository':'stepll2026/OntiCards','thread_key':thread,'kind':'issue','number':90050,'event':{'id':case,'author_type':'User','body':body},'thread':{'title':'synthetic semantic gate fixture'},'known_fields':{},'previously_asked_fields':[],'repository_context':{'complete':True,'token_revoked':True,'commit_sha':'f'*40,'tree_sha':'a'*40},'source_watermark':'REPLACE_NATIVE_NOW','trusted_facts':{'fixture_source':{'excerpt':'service: api\nimage: example:reference','url':'https://example.invalid/source'}}}
 draft={'classification':'缺信息','summary':'参考配置的镜像为 example:reference；尚未核实运行环境。','next_step':'请提供部署方式。','source_ids':['fixture_source'],'missing_evidence':['deployment_method'],'observed_fields':[]}
 review={'decision':'approve',**{f:True for f in flags},'claims':[{'quote':'参考配置的镜像为 example:reference','source_id':'fixture_source','source_quote':'image: example:reference'}],'issues':[]}
 compatibility=None
 if case.startswith('issue29_'):
  phase=case.removeprefix('issue29_');old=json.loads((root.parents[1]/('evidence/n8n/issue29-'+phase+'-source-snapshot.json')).read_text(encoding='utf-8'))
  filename='issue29-initial-draft.md'if phase=='initial'else'issue29-followup-reviewed.md';published=(root/filename).read_text(encoding='utf-8').strip()
  source['event']=old.get('human_event',{'id':old['id'],'author_type':old['author_type'],'body':old['body']});source['known_fields']=old.get('known_fields',{});source['trusted_facts']=old['trusted_facts'];source['previously_asked_fields']=old.get('previously_asked_fields',[])
  # Keep the previously approved published text byte-for-byte in the compatibility view.
  draft.update(summary=published,next_step='历史批准正文的结构兼容回放；不再次发布。',source_ids=['candidate_pdf_path'],missing_evidence=[])
  quote='python-docx'if phase=='initial'else'候选3105'
  review['claims']=[{'quote':quote,'source_id':'candidate_pdf_path','source_quote':'_build_docx_with_python(report, results, source_path)'}]
  compatibility={'historical_published_body_sha256':hashlib.sha256(published.encode()).hexdigest(),'mode':'frozen prior human approval compatibility; not a new model semantic decision','comment_id':'6339994362'if phase=='initial'else'6340579230'}
 if case=='manual31':source['number']=31
 if case=='bad_quote':review['claims'][0]['source_quote']='not in actual source'
 if case=='runtime_confusion':review.update(decision='human',runtime_distinguished=False,issues=['source defaults are not runtime observations'])
 if case=='known_field_conflict':source['known_fields']={'deployment_method':'already supplied'}
 response={'choices':[{'message':{'content':'NOT_JSON'if case=='invalid_json'else json.dumps(review,ensure_ascii=False)}}],'usage':{'fixture':True}}
 row={'event_key':eventkey,'thread_key':thread,'status':'awaiting_semantic_review','classification':draft['classification'],'source_snapshot':'NATIVE_BIND','source_hash':'NATIVE_HASH','draft':json.dumps(draft,ensure_ascii=False),'reply_zh':draft['summary']+'\n\n'+draft['next_step'],'usage':'{}','quality_errors':'[]','observed_at':'NATIVE_NOW'}
 conversation={'thread_key':thread,'model_calls':6 if case=='budget_six'else 3 if case=='manual31'else 1,'reply_count':0,'pending_event':eventkey,'pending_state':'model_request_started','known_fields':json.dumps(source['known_fields']),'asked_fields':'[]','answered_human_ids':'[]','publication_ids':'[]'}
 catalog[case]={'source':source,'draft_row':row,'conversation':conversation,'response':response,'compatibility':compatibility}
hook=node('Local semantic review acceptance');hook['parameters'].update(path='onticards-semantic-native-probe-v1',responseMode='responseNode');hook['webhookId']='onticards-semantic-native-probe-v1'
append('Frozen semantic fixture catalog','set',{'mode':'raw','jsonOutput':json.dumps(catalog,ensure_ascii=False),'options':{}},3.4)
append('Select bounded semantic fixture','set',{'mode':'raw','jsonOutput':'={{ (()=>{const key=$("Local semantic review acceptance").first().json.body.case,c=$json[key];if(!c)throw new Error("Unknown fixture");return {...c,case:key,source:{...c.source,source_watermark:$now.toISO()} };})() }}','options':{}},3.4)
append('Bind fixture source snapshot','set',{'mode':'raw','jsonOutput':'={{ {...$json,source_snapshot:JSON.stringify($json.source)} }}','options':{}},3.4)
append('Hash fixture source snapshot','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.source_snapshot }}','dataPropertyName':'source_hash','encoding':'hex'},2)
link('Local semantic review acceptance','Frozen semantic fixture catalog');link('Frozen semantic fixture catalog','Select bounded semantic fixture');link('Select bounded semantic fixture','Bind fixture source snapshot');link('Bind fixture source snapshot','Hash fixture source snapshot');link('Hash fixture source snapshot','Trusted semantic policy')
cfg=json.loads(node('Trusted semantic policy')['parameters']['jsonOutput']);cfg['review_enabled']=True;node('Trusted semantic policy')['parameters']['jsonOutput']=json.dumps(cfg)
aset('Read original structured drafts','={{ (()=>{const c=$("Hash fixture source snapshot").first().json;return {...c.draft_row,source_snapshot:c.source_snapshot,source_hash:c.source_hash,observed_at:$now.toISO()};})() }}')
# Native conversation is inserted only on the first run; repeat never resets consumed review budget.
append('Ensure fixture native conversations','dataTable',{'resource':'table','operation':'create','tableName':'fixture_semantic_v3_onticards_conversation_v1','columns':{'column':[{'name':k,'type':'number'if k in ['model_calls','reply_count']else'string'}for k in catalog['approve']['conversation']]},'options':{'createIfNotExists':True}},1.1)
append('Read fixture conversation seed','dataTable',{'resource':'row','operation':'get','dataTableId':{'__rl':True,'value':'fixture_semantic_v3_onticards_conversation_v1','mode':'name'},'returnAll':True,'filters':{'conditions':[{'keyName':'thread_key','keyValue':'={{ $("Hash fixture source snapshot").first().json.conversation.thread_key }}'}]}},1.1,alwaysOutputData=True)
append('Fixture conversation absent','if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':'seed','leftValue':'={{ !$json.thread_key }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
append('Project fixture conversation seed','set',{'mode':'raw','jsonOutput':'={{ $("Hash fixture source snapshot").first().json.conversation }}','options':{}},3.4)
append('Insert fixture native conversation','dataTable',{'resource':'row','operation':'insert','dataTableId':{'__rl':True,'value':'fixture_semantic_v3_onticards_conversation_v1','mode':'name'},'columns':{'mappingMode':'autoMapInputData','value':{},'schema':[]},'options':{}},1.1)
link('Read original structured drafts','Ensure fixture native conversations');link('Ensure fixture native conversations','Read fixture conversation seed');link('Read fixture conversation seed','Fixture conversation absent');link('Fixture conversation absent','Project fixture conversation seed');link('Project fixture conversation seed','Insert fixture native conversation');link('Insert fixture native conversation','Read review conversation budgets');link('Fixture conversation absent','Read review conversation budgets',1)
aset('Read fresh immutable review source','={{ {complete:true,token_revoked:true,commit_sha:$("Hash fixture source snapshot").first().json.case==="changed_source"?"b".repeat(40):"f".repeat(40),tree_sha:"a".repeat(40)} }}')
aset('One independent review no retry','={{ $("Hash fixture source snapshot").first().json.response }}')
append('Return semantic fixture evidence','respondToWebhook',{'respondWith':'json','responseBody':'={{ {result:$json,case:$("Hash fixture source snapshot").first().json.case,compatibility:$("Hash fixture source snapshot").first().json.compatibility,model_calls:0,github_posts:0} }}','options':{}},1.4)
for name in ['Review complete without GitHub write','Review disabled or no candidate','Persist premodel source rejection']:link(name,'Return semantic fixture evidence')
assert not any(n['type'].endswith(('httpRequest','executeWorkflow'))for n in w['nodes'])
(root/'semantic-native-probe.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'semantic-native-probe-cases.json').write_text(json.dumps({k:{'event_key':v['draft_row']['event_key'],'thread_key':v['draft_row']['thread_key']}for k,v in catalog.items()},indent=2))
print(json.dumps({'nodes':len(w['nodes']),'cases':len(catalog),'http_nodes':0,'model_calls':0}))
