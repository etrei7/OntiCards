"""Native DataTable replay of actual routing/reservation/publication increments.

No model/HTTP nodes. Frozen approval and comment confirmation replace external
transports; the routing and three state-transition expressions are unmodified.
"""
import copy,json,uuid,hashlib
from pathlib import Path
root=Path(__file__).parent
raw=(root/'build_event_replay.py').read_text(encoding='utf-8')
settings={'executionOrder':'v1','timezone':'Asia/Shanghai','saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False,'executionTimeout':60}
exec(raw[raw.index('class Builder:'):raw.index('# Native test transport only.')])
def spaced(expr):
 if not expr.startswith('={{'):return expr
 inner=expr[3:-2]
 while '}}'in inner:inner=inner.replace('}}','} }')
 return '={{'+inner+'}}'
Builder.set=lambda self,name,expr:self.node(name,'set',{'mode':'raw','jsonOutput':spaced(expr),'options':{}},3.4)
draft=json.loads((root/'persistent-drafts.workflow.json').read_text(encoding='utf-8'))
review=json.loads((root/'persistent-semantic-review.workflow.json').read_text(encoding='utf-8'))
publication=json.loads((root/'persistent-publication.workflow.json').read_text(encoding='utf-8'))
b=Builder('onticardsConversationBudgetProbeV1');table='fixture_conversation_budget6_v1'
def cloned(w,name):
 n=copy.deepcopy(next(n for n in w['nodes']if n['name']==name));n['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,b.wid+'/'+name));n['position']=[len(b.nodes)*190,0];b.nodes.append(n)
cols=[('thread_key','string'),('model_calls','number'),('reply_count','number'),('pending_event','string'),('pending_state','string'),('known_fields','string'),('asked_fields','string'),('answered_human_ids','string'),('publication_ids','string')]
b.node('Budget fixture request','webhook',{'httpMethod':'POST','path':'onticards-budget6-probe-v1','responseMode':'responseNode','options':{}},2.1,webhookId='onticards-budget6-probe-v1')
b.set('Bound fixture input','={{ (()=>{const q=$json.body;if(!["ordinary","manual31","failed","odd_budget","concurrent","closed","reopened","prreview","prinline","machine"].includes(q.case)||![1,2,3,4].includes(q.round))throw new Error("Unknown fixture");if(q.case==="concurrent"&&(!Number.isSafeInteger(q.nonce)||q.nonce<1||q.nonce>100000000))throw new Error("Invalid concurrency nonce");const n=q.case==="concurrent"?100000+q.nonce:["closed","reopened","prreview","prinline","machine"].includes(q.case)?90200+["closed","reopened","prreview","prinline","machine"].indexOf(q.case):q.case==="manual31"?31:q.case==="ordinary"?90100:q.case==="failed"?90101:90102;return {entered_at:$now.toISO(),case:q.case,round:q.round,number:n,thread_key:"fixture-budget6:"+n,event_key:"fixture-budget6:"+n+":"+q.round,event_id:"human-"+q.round,seed:{thread_key:"fixture-budget6:"+n,model_calls:q.case==="manual31"?3:q.case==="odd_budget"?5:q.case==="failed"?2:0,reply_count:q.case==="odd_budget"?2:0,pending_event:q.case==="manual31"||q.case==="failed"?"existing-failed-event":"",pending_state:q.case==="manual31"||q.case==="failed"?"model_request_started":"",known_fields:"{}",asked_fields:"[]",answered_human_ids:"[]",publication_ids:"[]"}};})() }}')
b.table('Ensure native budget fixture table',table,cols)
b.row('Read native fixture seed',table,'get','thread_key','={{ $("Bound fixture input").first().json.thread_key }}',alwaysOutputData=True)
b.iff('Seed only missing fixture','={{ !$json.thread_key }}')
b.set('Initial fixture conversation','={{ $("Bound fixture input").first().json.seed }}')
b.row('Insert missing fixture conversation',table,'insert',None,None)
cloned(draft,'Trusted routing configuration')
b.set('Read complete watermark','={{ {repository:"stepll2026/OntiCards",watermark:$now.toISO()} }}')
b.set('Read collected events','={{ (()=>{const q=$("Bound fixture input").first().json,p={id:q.event_id,body:"Synthetic human material "+q.round,created_at:$now.toISO(),updated_at:$now.toISO(),title:"Explicit native budget fixture"};return {event_key:q.event_key,thread_key:q.thread_key,event_id:q.event_id,kind:q.case==="closed"?"timeline_closed":q.case==="reopened"?"timeline_reopened":q.case==="prreview"?"review":q.case==="prinline"?"inline_comment":q.round===1?"issue_snapshot":"discussion_comment",actor:q.case==="machine"?"fixture[bot]":"fixture-human",actor_type:q.case==="machine"?"Bot":"User",payload:JSON.stringify(p)};})() }}')
b.set('Read current thread contexts','={{ (()=>{const q=$("Bound fixture input").first().json,p=JSON.parse($("Read collected events").first().json.payload);return {thread_key:q.thread_key,number:q.number,kind:["prreview","prinline"].includes(q.case)?"pull_request":"issue",app_reply_count:0,snapshot:JSON.stringify({...p,labels:[],discussion:[p],inline:[p],reviews:[p]})};})() }}')
b.set('Read prior draft events','{}')
b.row('Read conversations',table,'get','thread_key','={{ $("Bound fixture input").first().json.thread_key }}',alwaysOutputData=True)
cloned(draft,'Project deterministic routing observations')
b.iff('Actual route eligible','={{ !!$json.candidate }}')
b.iff('Concurrent fixture deliberate overlap','={{ $("Bound fixture input").first().json.case === "concurrent" }}')
b.node('Native short wait only in concurrency fixture','wait',{'amount':2,'unit':'seconds'},1.1)
cloned(draft,'Reserve thread model budget')
b.row('Persist actual draft reservation',table,'upsert','thread_key','={{ $json.thread_key }}')
b.set('Hash original review source','={{ {conversation:$("Persist actual draft reservation").first().json} }}')
cloned(review,'Reserve review in original thread budget')
b.row('Persist actual review reservation',table,'upsert','thread_key','={{ $json.thread_key }}')
b.row('Read original conversation',table,'get','thread_key','={{ $("Bound fixture input").first().json.thread_key }}',alwaysOutputData=True)
b.set('Bind approval and immutable draft','={{ (()=>{const q=$("Bound fixture input").first().json;return {approval:{asked_fields:[],observed_fields:[]},source:{event:{id:q.event_id,body:"Synthetic human material "+q.round}}};})() }}')
b.set('Frozen remote publication confirmation','={{ (()=>{const q=$("Bound fixture input").first().json,c=$("Read original conversation").first().json;return {thread_key:q.thread_key,event_key:q.event_key,comment_id:"fixture-published-"+q.round,reply_count:Number(c.reply_count)+1};})() }}')
cloned(publication,'Apply reviewed conversation increment')
b.row('Persist actual confirmed conversation',table,'upsert','thread_key','={{ $json.thread_key }}')
b.respond('Return actual transitioned state','={{ {route:$("Project deterministic routing observations").first().json.observations[0].status,conversation:$json,execution_id:$execution.id,entered_at:$("Bound fixture input").first().json.entered_at,completed_at:$now.toISO(),external_model_calls:0,github_posts:0} }}')
b.respond('Return blocked unchanged state','={{ {route:$("Project deterministic routing observations").first().json.observations[0].status,conversation:$("Read conversations").first().json,execution_id:$execution.id,entered_at:$("Bound fixture input").first().json.entered_at,completed_at:$now.toISO(),external_model_calls:0,github_posts:0} }}')
b.chain(['Budget fixture request','Bound fixture input','Ensure native budget fixture table','Read native fixture seed','Seed only missing fixture','Initial fixture conversation','Insert missing fixture conversation','Trusted routing configuration','Read complete watermark','Read collected events','Read current thread contexts','Read prior draft events','Read conversations','Project deterministic routing observations','Actual route eligible','Concurrent fixture deliberate overlap','Native short wait only in concurrency fixture','Reserve thread model budget','Persist actual draft reservation','Hash original review source','Reserve review in original thread budget','Persist actual review reservation','Read original conversation','Bind approval and immutable draft','Frozen remote publication confirmation','Apply reviewed conversation increment','Persist actual confirmed conversation','Return actual transitioned state'])
b.link('Seed only missing fixture','Trusted routing configuration',1);b.link('Actual route eligible','Return blocked unchanged state',1)
b.link('Concurrent fixture deliberate overlap','Reserve thread model budget',1)
# New native-command cases reuse this real DataTable fixture without touching
# any earlier fixture records or historical production budget.
native_fixture=json.loads((root.parents[1]/'evidence/n8n/native-mcp-slash-body-fixture.json').read_text(encoding='utf-8'))
route_cases=['native_mcp','native_fix','native_ultrafix','near_command','marker_only','leading_blank','normal_followup','native_pending','manual29']
for n in b.nodes:
 if n['name']=='Bound fixture input':
  expr=n['parameters']['jsonOutput'];expr=expr.replace('"machine"].includes(q.case)', '"machine",'+','.join(json.dumps(x)for x in route_cases)+'].includes(q.case)')
  expr=expr.replace('const n=q.case===', 'const n=q.case==="manual29"?29:'+json.dumps(route_cases[:-1])+'.includes(q.case)?90300+'+json.dumps(route_cases[:-1])+'.indexOf(q.case):q.case===',1)
  expr=expr.replace('model_calls:q.case===', 'model_calls:q.case==="manual29"?5:q.case==="native_pending"?2:q.case===',1).replace('reply_count:q.case===','reply_count:q.case==="manual29"?2:q.case===',1)
  expr=expr.replace('q.case==="manual31"||q.case==="failed"','["manual31","failed","manual29","native_pending"].includes(q.case)')
  n['parameters']['jsonOutput']=spaced(expr)
 if n['name']=='Read collected events':
  expr=n['parameters']['jsonOutput'];bodies={'native_mcp':native_fixture['body'],'native_fix':'/fix all\nExplicit synthetic fixture only','native_ultrafix':'/ultrafix goal=8 max=3\nExplicit synthetic fixture only','near_command':'/reviewer is an ordinary documentation example','marker_only':'已补充运行环境：Linux。<!-- propr-mcp:fixture-only; head:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -->','leading_blank':'\n/review is prose after a blank line','normal_followup':'补充验收材料：仅测试环境，单表，Linux，仍未提供失败PDF。','native_pending':native_fixture['body'],'manual29':native_fixture['body']}
  expr=expr.replace('body:"Synthetic human material "+q.round','body:('+json.dumps(bodies,ensure_ascii=False)+')[q.case]||"Synthetic human material "+q.round')
  n['parameters']['jsonOutput']=spaced(expr)
 if n['name']=='Read current thread contexts':
  n['parameters']['jsonOutput']=n['parameters']['jsonOutput'].replace('["prreview","prinline"].includes(q.case)','["prreview","prinline",'+','.join(json.dumps(x)for x in route_cases)+'].includes(q.case)')
 if n['name']=='Read prior draft events':
  n['parameters']['jsonOutput']='={{ $("Bound fixture input").first().json.case==="native_pending"?{event_key:$("Bound fixture input").first().json.event_key,status:"model_request_started",source_snapshot:"frozen existing source",draft:"frozen existing draft",usage:"{}"}:{} }}'
w=b.workflow('OntiCards three ordinary replies six model reservations native fixture')
assert not any(n['type'].endswith(('httpRequest','executeCommand'))for n in w['nodes'])
(root/'conversation-budget-probe.workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
proof={n['name']:hashlib.sha256(n['parameters']['jsonOutput'].encode()).hexdigest()for n in w['nodes']if n['name']in ['Project deterministic routing observations','Reserve thread model budget','Reserve review in original thread budget','Apply reviewed conversation increment']}
(root/'conversation-budget-probe-provenance.json').write_text(json.dumps({'exact_production_expression_sha256':proof,'transports':'frozen approvals and confirmations; zero model or GitHub calls','state':'native DataTable seeded only if absent'},indent=2))
print(json.dumps({'nodes':len(w['nodes']),'model_requests':0,'github_requests':0}))
