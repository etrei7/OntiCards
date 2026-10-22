"""Native-node replay of bounded triage policy; no model or GitHub write nodes."""
import copy
import hashlib
import json
from pathlib import Path
import uuid

root=Path(__file__).parent
raw=json.loads((root.parents[1]/'evidence/n8n/issue25-native-quality-probe.json').read_text(encoding='utf-8'))
draft=raw['requests'][0]['result']['draft']
source=next(json.loads(row['source_snapshot']) for rows in raw['stored_rows'].values() for row in rows if row.get('event_key')=='issue25-one-model-v1')
approved_hash=hashlib.sha256(draft.encode()).hexdigest()
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':60}
bot='onticards-maintainer-stepll2026[bot]'
cases={}
def case(name,thread,event,**extra):
    cases[name]=dict(repository='stepll2026/OntiCards',thread_key=thread,event_key=thread+':'+event,number=90000,
        actor='synthetic-human',event_type='issue_comment',revision=event,fixture=True,fetch_complete=True,
        window_end='2026-10-22T11:00:00Z',base_comments=[],known_fields={},required_fields=[],
        classification='咨询',reply='【AI辅助｜合成回放】依据固定版本事实核实此咨询；本场景不写GitHub。',
        transport='created',**extra)

case('actual_issue25','actual:25','snapshot',number_override=25)
cases['actual_issue25'].update(number=25,fixture=False,base_comments=source['comments'],classification='缺信息',reply=draft)
case('consult','fixture:consult','human-1')
case('consult_bot','fixture:consult','bot-2');cases['consult_bot']['actor']=bot
case('consult_human','fixture:consult','human-3');cases['consult_human']['window_end']='2026-10-22T11:01:00Z'
case('missing','fixture:missing','human-1');cases['missing'].update(classification='缺信息',known_fields={'version':'3105'},required_fields=['version','deployment','reproduction'])
case('missing_followup','fixture:missing','human-2');cases['missing_followup'].update(classification='缺信息',known_fields={'deployment':'synthetic-compose','reproduction':'synthetic steps'},required_fields=['version','deployment','reproduction'],window_end='2026-10-22T11:02:00Z')
case('large_change','fixture:large','human-1');cases['large_change'].update(classification='大改需人工')
case('cap_human','fixture:cap','human-1');cases['cap_human']['base_comments']=[{'id':i,'author':bot,'body':'prior native component reply'} for i in range(3)]
case('cap_more_info','fixture:cap','human-2');cases['cap_more_info'].update(base_comments=cases['cap_human']['base_comments'],known_fields={'reproduction':'new human detail'},window_end='2026-10-22T11:03:00Z')
case('page_incomplete','fixture:pages','human-1');cases['page_incomplete']['fetch_complete']=False
case('page_recovered','fixture:pages','human-1')
case('unknown_found','fixture:unknown-found','human-1');cases['unknown_found']['transport']='created_but_504'
case('unknown_absent','fixture:unknown-absent','human-1');cases['unknown_absent']['transport']='absent_504'
case('unknown_new_info','fixture:unknown-absent','human-2');cases['unknown_new_info']['known_fields']={'reproduction':'new detail must not bypass pending POST'}
case('older_window','fixture:consult','human-4');cases['older_window']['window_end']='2026-10-22T10:59:00Z'

class Builder:
    def __init__(self, wid):self.wid=wid;self.nodes=[];self.connections={}
    def node(self,name,kind,p,ver=1,**extra):
        self.nodes.append(dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,self.wid+'/'+name)),name=name,type='n8n-nodes-base.'+kind,typeVersion=ver,position=[len(self.nodes)*190,0],parameters=p,**extra))
    def set(self,name,expr):self.node(name,'set',{'mode':'raw','jsonOutput':expr,'options':{}},3.4)
    def iff(self,name,expr):self.node(name,'if',{'conditions':{'options':{'caseSensitive':True,'typeValidation':'strict','version':2},'conditions':[{'id':name,'leftValue':expr,'rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},2.2)
    def respond(self,name,expr,code=200):self.node(name,'respondToWebhook',{'respondWith':'json','responseBody':expr,'options':{'responseCode':code}},1.4)
    def link(self,a,b,index=0):
        x=self.connections.setdefault(a,{'main':[]})['main']
        while len(x)<=index:x.append([])
        x[index].append({'node':b,'type':'main','index':0})
    def chain(self,names):
        for a,b in zip(names,names[1:]):self.link(a,b)
    def table(self,name,table,cols):self.node(name,'dataTable',{'resource':'table','operation':'create','tableName':table,'columns':{'column':[{'name':k,'type':v} for k,v in cols]},'options':{'createIfNotExists':True}},1.1)
    def row(self,name,table,op,key,val,**extra):
        p={'resource':'row','operation':op,'dataTableId':{'__rl':True,'value':table,'mode':'name'}}
        if op!='insert':p.update(matchType='allConditions',filters={'conditions':[{'keyName':key,'condition':'eq','keyValue':val}]})
        if op=='get':p.update(returnAll=True)
        else:p.update(columns={'mappingMode':'autoMapInputData','value':{},'schema':[]},options={})
        self.node(name,'dataTable',p,1.1,**extra)
    def workflow(self,name):return {'id':self.wid,'name':name,'active':False,'nodes':self.nodes,'connections':self.connections,'settings':settings,'pinData':{},'tags':[]}

# Native test transport only. It holds synthetic comments, never contacts GitHub.
s=Builder('onticardsReplayTransportV3')
mocktable='onticards_replay_comments_v3'
mockcols=[('thread_key','string'),('marker','string'),('body','string'),('body_hash','string'),('author','string')]
for method in ['GET','POST']:
    s.node(method+' local comments','webhook',{'httpMethod':method,'path':'onticards-replay-comments-v3','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-replay-comments-v3-'+method)
    s.table('Ensure mock table '+method,mocktable,mockcols)
    s.link(method+' local comments','Ensure mock table '+method)
s.row('List synthetic comments',mocktable,'get','thread_key','={{ $("GET local comments").first().json.query.thread_key }}',alwaysOutputData=True)
s.respond('Return synthetic list','={{ {fixture:true,comments:$input.all().map(i=>i.json).filter(x=>x.marker)} }}')
s.chain(['Ensure mock table GET','List synthetic comments','Return synthetic list'])
s.iff('Simulate remote persistence','={{ $("POST local comments").first().json.body.behavior !== "absent_504" }}')
s.set('Project synthetic comment','={{ {thread_key:$("POST local comments").first().json.body.thread_key,marker:$("POST local comments").first().json.body.marker,body:$("POST local comments").first().json.body.body,body_hash:$("POST local comments").first().json.body.body_hash,author:"onticards-maintainer-stepll2026[bot]"} }}')
s.row('Insert synthetic remote comment',mocktable,'insert',None,None)
s.respond('Return created or uncertain','={{ {fixture:true,id:$json.id,marker:$json.marker} }}','= {{ 200 }}'.replace('= {{ 200 }}','={{ $("POST local comments").first().json.body.behavior === "created_but_504" ? 504 : 201 }}'))
s.respond('Return uncertain without comment','={{ {fixture:true,unknown:true} }}',504)
s.chain(['Ensure mock table POST','Simulate remote persistence','Project synthetic comment','Insert synthetic remote comment','Return created or uncertain'])
s.link('Simulate remote persistence','Return uncertain without comment',1)

b=Builder('onticardsEventPolicyReplayV3')
events='onticards_replay_events_v3';threads='onticards_replay_threads_v3';marks='onticards_replay_watermarks_v3'
eventcols=[('event_key','string'),('thread_key','string'),('status','string'),('marker','string'),('body_hash','string'),('body','string'),('comment_id','string'),('classification','string')]
threadcols=[('thread_key','string'),('reply_count','number'),('pending_event','string'),('known_fields','string'),('asked_fields','string'),('state','string')]
markcols=[('thread_key','string'),('watermark','string')]
b.node('Replay local event','webhook',{'httpMethod':'POST','path':'onticards-event-policy-replay-v3','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-event-policy-replay-v3')
b.set('Frozen catalog',json.dumps({'cases':cases,'frozen_draft':draft,'approved_sha256':approved_hash},ensure_ascii=False))
b.set('Select authorized case','={{ {source:$("Frozen catalog").first().json.cases[$("Replay local event").first().json.body.variant],draft:$("Frozen catalog").first().json.frozen_draft} }}')
b.iff('Known fixed case','={{ !!$json.source && $json.source.repository === "stepll2026/OntiCards" }}')
b.respond('Unknown case','={{ {status:"rejected",model_calls:0,github_writes:0} }}')
b.node('Hash frozen real response','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.draft }}','dataPropertyName':'frozen_sha256','encoding':'hex'},2)
b.set('Separate structure review and formatting',r'''={{ (()=>{
 const d=JSON.parse($json.draft),keys=['classification','summary','next_step','missing_evidence','source_ids'];
 const structural=keys.every(k=>k in d)&&Object.keys(d).every(k=>keys.includes(k))&&d.classification==='缺信息'
 &&typeof d.summary==='string'&&typeof d.next_step==='string'&&d.summary.length>0&&d.next_step.length>0
 &&Array.isArray(d.missing_evidence)&&d.missing_evidence.length===1&&d.missing_evidence[0]==='native_issue25_run'
 &&Array.isArray(d.source_ids)&&d.source_ids.every(k=>['code_docx_soffice','independent_pdf26','native_issue25_status'].includes(k));
 const reviewed=$json.frozen_sha256===$('Frozen catalog').first().json.approved_sha256;
 return {schema_pass:structural,semantic_review_bound_to_exact_response:reviewed,quality_pass:structural&&reviewed,
 original_native_gate_passed:false,format_notes:['Original 150-character limit was an author-imposed expectation, not user requirement.','Repeated inline references are readability notes; raw response preserved.'],
 semantic_note:'This frozen response only was independently reviewed; no automatic approval of new free text.',frozen_sha256:$json.frozen_sha256};
})() }}''')
b.table('Ensure events',events,eventcols);b.table('Ensure threads',threads,threadcols);b.table('Ensure watermarks',marks,markcols)
b.iff('Complete input pages','={{ $("Select authorized case").first().json.source.fetch_complete }}')
b.respond('Incomplete page no watermark','={{ {status:"pagination_incomplete",watermark_advanced:false,model_calls:0,github_writes:0,synthetic_posts:0} }}')
b.row('Read event ledger',events,'get','event_key','={{ $("Select authorized case").first().json.source.event_key }}',alwaysOutputData=True)
b.iff('Completed duplicate','={{ !!$json.id && $json.status !== "posting_unknown" }}')
b.respond('Return duplicate','={{ {status:"duplicate",stored_status:$json.status,comment_id:$json.comment_id,model_calls:0,github_writes:0,synthetic_posts:0} }}')
def http(name,method,url,body=None):
    p={'method':method,'url':url,'options':{'timeout':10000,'response':{'response':{'fullResponse':True,'responseFormat':'json','neverError':True}}}}
    if body is not None:p.update(sendBody=True,specifyBody='json',jsonBody=body)
    b.node(name,'httpRequest',p,4.4,retryOnFail=False,executeOnce=True)
http('Read current synthetic comments','GET','={{ "http://127.0.0.1:18127/webhook/onticards-replay-comments-v3?thread_key="+encodeURIComponent($("Select authorized case").first().json.source.thread_key) }}')
b.row('Read thread state',threads,'get','thread_key','={{ $("Select authorized case").first().json.source.thread_key }}',alwaysOutputData=True)
b.row('Read prior watermark',marks,'get','thread_key','={{ $("Select authorized case").first().json.source.thread_key }}',alwaysOutputData=True)
b.set('Decide bounded native action',r'''={{ (()=>{
 const x=$('Select authorized case').first().json.source,old=$('Read event ledger').first().json,t=$('Read thread state').first().json;
 const comments=$('Read current synthetic comments').first().json.body.comments,bot='onticards-maintainer-stepll2026[bot]';
 const count=Math.max((x.base_comments||[]).filter(c=>c.author===bot||c.user?.id===346235449).length+comments.filter(c=>c.author===bot).length,t.reply_count||0);
 const known={...JSON.parse(t.known_fields||'{}'),...x.known_fields},asked=JSON.parse(t.asked_fields||'[]');
 const missing=x.required_fields.filter(k=>!known[k]),marker='<!-- onticards-triage:'+x.event_key+' -->';
 const existing=comments.find(c=>c.marker===marker&&c.author===bot);
 let status='ready',should_post=false,pending=t.pending_event||'',body=x.reply,comment_id='';
 if(old.status==='posting_unknown') {status=existing&&existing.body_hash===old.body_hash?'published_reconciled':'posting_unknown';comment_id=existing?String(existing.id):'';pending=status==='posting_unknown'?x.event_key:'';body=old.body;}
 else if(x.actor===bot||/\[bot\]$/i.test(x.actor))status='ignored_bot';
 else if(pending)status='waiting_prior_post_reconciliation';
 else if(count>=3)status='cap_reached_needs_maintainer';
 else if(!x.fixture)status='needs_human_review';
 else {should_post=true;pending=x.event_key;
   if(x.classification==='缺信息'&&missing.length){status='waiting_information';const fresh=missing.filter(k=>!asked.includes(k));body='【AI辅助｜合成回放】请补充必要字段：'+fresh.join('、')+'。已提供材料不会重复索取。';}
   else if(x.classification==='缺信息'){status='information_received_needs_diagnosis';body='【AI辅助｜合成回放】已收到补充信息，保留原任务，等待受信诊断；没有启动新修复。';}
   else if(x.classification==='大改需人工'){status='needs_maintainer_decision';body='【AI辅助｜合成回放】需求涉及范围和影响，请维护者决定；不执行架构改动。';}
   else status='consultation_answered';}
 const watermark=[$json.watermark||'',x.window_end].sort().at(-1);
 return {event_key:x.event_key,thread_key:x.thread_key,status,desired_status:status,marker,body_hash:old.body_hash||'',body,comment_id,
 classification:x.classification,reply_count:count,pending_event:pending,known_fields:JSON.stringify(known),asked_fields:JSON.stringify([...new Set([...asked,...missing])]),
 watermark,should_post,fixture:x.fixture,transport:x.transport,synthetic_posts:0};
})() }}''')
b.node('Hash prepared body','crypto',{'action':'hash','type':'SHA256','binaryData':False,'value':'={{ $json.body }}','dataPropertyName':'body_hash','encoding':'hex'},2)
b.iff('Authorized synthetic POST only','={{ $json.should_post && $json.fixture }}')
eventproj="{event_key:$json.event_key,thread_key:$json.thread_key,status:$json.status,marker:$json.marker,body_hash:$json.body_hash,body:$json.body,comment_id:$json.comment_id,classification:$json.classification}"
threadproj="{thread_key:$json.thread_key,reply_count:$json.reply_count,pending_event:$json.pending_event,known_fields:$json.known_fields,asked_fields:$json.asked_fields,state:$json.status}"
b.set('Persist unknown before transport','={{ '+eventproj.replace('status:$json.status',"status:'posting_unknown'")+' }}')
b.row('Save pending event',events,'upsert','event_key','={{ $json.event_key }}')
b.set('Persist pending thread','={{ '+threadproj.replace('$json.', '$("Hash prepared body").first().json.')+' }}')
b.row('Save pending thread',threads,'upsert','thread_key','={{ $json.thread_key }}')
http('One synthetic POST no retry','POST','http://127.0.0.1:18127/webhook/onticards-replay-comments-v3','={{ {thread_key:$("Hash prepared body").first().json.thread_key,marker:$("Hash prepared body").first().json.marker,body:$("Hash prepared body").first().json.body,body_hash:$("Hash prepared body").first().json.body_hash,behavior:$("Hash prepared body").first().json.transport} }}')
http('Reconcile by native GET','GET','={{ "http://127.0.0.1:18127/webhook/onticards-replay-comments-v3?thread_key="+encodeURIComponent($("Hash prepared body").first().json.thread_key) }}')
b.set('Confirm exact remote marker and body',r'''={{ (()=>{
 const x=$('Hash prepared body').first().json,comments=$json.body.comments;
 const found=comments.find(c=>c.author==='onticards-maintainer-stepll2026[bot]'&&c.marker===x.marker&&c.body_hash===x.body_hash&&c.body===x.body);
 const count=$('Select authorized case').first().json.source.base_comments.filter(c=>c.author==='onticards-maintainer-stepll2026[bot]'||c.user?.id===346235449).length+comments.filter(c=>c.author==='onticards-maintainer-stepll2026[bot]').length;
 return {...x,status:found?x.desired_status:'posting_unknown',comment_id:found?String(found.id):'',reply_count:Math.max(count,x.reply_count),pending_event:found?'':x.event_key,synthetic_posts:1,
 post_status:$('One synthetic POST no retry').first().json.statusCode,reconciled:!!found};
})() }}''')
b.set('Final state','={{ $json }}')
b.set('Project final event','={{ '+eventproj+' }}');b.row('Save final event',events,'upsert','event_key','={{ $json.event_key }}')
b.set('Project final thread','={{ '+threadproj.replace('$json.','$("Final state").first().json.')+' }}');b.row('Save final thread',threads,'upsert','thread_key','={{ $json.thread_key }}')
b.set('Project committed watermark','={{ {thread_key:$("Final state").first().json.thread_key,watermark:$("Final state").first().json.watermark} }}');b.row('Commit persisted watermark',marks,'upsert','thread_key','={{ $json.thread_key }}')
b.respond('Return replay result','={{ {...$("Final state").first().json,quality:$("Separate structure review and formatting").first().json,model_calls:0,github_writes:0,transport:"native loopback synthetic Webhook, not GitHub"} }}')
b.chain(['Replay local event','Frozen catalog','Select authorized case','Known fixed case','Hash frozen real response','Separate structure review and formatting','Ensure events','Ensure threads','Ensure watermarks','Complete input pages','Read event ledger','Completed duplicate'])
b.link('Known fixed case','Unknown case',1);b.link('Complete input pages','Incomplete page no watermark',1)
b.link('Completed duplicate','Return duplicate');b.link('Completed duplicate','Read current synthetic comments',1)
b.chain(['Read current synthetic comments','Read thread state','Read prior watermark','Decide bounded native action','Hash prepared body','Authorized synthetic POST only','Persist unknown before transport','Save pending event','Persist pending thread','Save pending thread','One synthetic POST no retry','Reconcile by native GET','Confirm exact remote marker and body','Final state'])
b.link('Authorized synthetic POST only','Final state',1)
b.chain(['Final state','Project final event','Save final event','Project final thread','Save final thread','Project committed watermark','Commit persisted watermark','Return replay result'])
workflows=[s.workflow('OntiCards replay-only comment transport'),b.workflow('OntiCards native event policy replay — no model or GitHub writes')]
(root/'triage-event-policy-replay-v3.workflow.json').write_text(json.dumps(workflows,ensure_ascii=False,indent=2),encoding='utf-8')

runner=(root/'run_server_probe.py').read_text(encoding='utf-8')
runner=runner.replace("resume='--resume' in sys.argv","resume=True").replace("live_mode='--live-model' in sys.argv","live_mode=False")
runner=runner.replace("workflow_filename='triage-server-live-model.workflow.json' if live_mode else 'triage-server-probe.workflow.json'","workflow_filename='triage-event-policy-replay-v3.workflow.json'")
runner=runner.replace("workflow_id='onticardsServerLiveModelV2' if live_mode else 'onticardsServerProbeV2'","workflow_id='onticardsEventPolicyReplayV3'")
runner=runner.replace("webhook_path='/webhook/onticards-server-live-model-v2' if live_mode else '/webhook/onticards-server-probe-v2'","webhook_path='/webhook/onticards-event-policy-replay-v3'")
runner=runner.replace("evidence_name='native-server-live-model-probe' if live_mode else 'native-server-datatable-probe'","evidence_name='native-event-policy-replay-v3'")
runner=runner.replace("'native-server-datatable-probe-attempt-'","'native-event-policy-replay-v3-attempt-'")
runner=runner.replace("run(['docker','exec',name,'n8n','publish:workflow','--id='+workflow_id])","run(['docker','exec',name,'n8n','publish:workflow','--id=onticardsReplayTransportV3'])\n        run(['docker','exec',name,'n8n','publish:workflow','--id='+workflow_id])")
variants=['actual_issue25','actual_issue25','consult','consult','consult_bot','consult_human','missing','missing_followup','large_change','cap_human','cap_more_info','page_incomplete','page_recovered','unknown_found','unknown_found','unknown_absent','unknown_new_info','unknown_absent','older_window']
runner=runner.replace("(('live','live') if live_mode else ('actual','actual','valid_fixture','valid_fixture','invalid_fixture','bot_fixture'))",repr(tuple(variants)))
(root/'run_event_replay.py').write_text(runner,encoding='utf-8')
print(json.dumps({'workflows':len(workflows),'nodes':[len(w['nodes']) for w in workflows],'replay_events':len(variants),'new_model_calls':0,'github_writes':0,'approved_frozen_sha256':approved_hash}))
