"""No-model acceptance checks for date boundaries, invalid inputs and initial config."""
import ast
import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile

root=Path(__file__).resolve().parents[2]
deploy=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'repo/automation'))
from onticards.report import window
spec=importlib.util.spec_from_file_location('daily_input_contract',deploy/'daily_input_contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
checks=[]
def record(name,condition,**details):
    checks.append({'name':name,'passed':bool(condition),**details})
cases=[
 ('2026-10-22T01:05:00Z','2026-10-21'),
 ('2026-11-01T01:05:00Z','2026-10-31'),
 ('2027-01-01T01:05:00Z','2026-12-31'),
 ('2024-03-01T01:05:00Z','2024-02-29'),
 ('2026-03-01T01:05:00Z','2026-02-28'),
 ('2026-10-21T15:59:59Z','2026-10-20'),
 ('2026-10-21T16:00:00Z','2026-10-21'),
 ('2026-10-22T01:04:59Z','2026-10-21'),
 ('2026-10-22T01:05:01Z','2026-10-21'),
]
for timestamp,expected in cases:
    day,start,end,_=contract.expected_window(timestamp)
    collector_start,collector_end=window(day)
    record('calendar '+timestamp,day==expected and start==collector_start and end==collector_end,
           target_day=day,window_start=start.isoformat(),window_end=end.isoformat())
for bad in ('not-an-ISO-timestamp','2026-10-22T09:05:00'):
    try: contract.expected_window(bad);passed=False
    except ValueError: passed=True
    record('reject invalid/naive time '+bad,passed)

temporary_parent=(root/'evidence/daily-input-tests').resolve()
assert temporary_parent.is_relative_to(root.resolve())
temporary_parent.mkdir(exist_ok=True)
timestamp='2026-11-01T01:05:00Z'
day,start,end,trigger=contract.expected_window(timestamp)
base={'repository':'stepll2026/OntiCards','day':day,'run_id':'synthetic-validation-run',
      'window_start':start.isoformat(),'window_end':end.isoformat(),
      'generated_at':(trigger-timedelta(minutes=1)).isoformat(),
      'expires_at':(trigger+timedelta(days=30)).isoformat(),'status':'complete',
      'counts':{},'snapshots':{},
      'facts':{'errors':[],'head_sha':'synthetic-sha','pull_requests':[],
               'repository':{},'current_open':[],'commits':[],'ai_comments':[],'ci_runs':[]}}
with tempfile.TemporaryDirectory(prefix='case-',dir=temporary_parent) as folder:
    p=Path(folder).resolve();assert p.is_relative_to(temporary_parent)
    def put(data,md=None):
        (p/(day+'.json')).write_text(json.dumps(data),encoding='utf-8')
        (p/(day+'.md')).write_text(md if md is not None else day+' '+data['run_id']+' '+data['generated_at'],encoding='utf-8')
    record('missing target waits',contract.selected_input(timestamp,p)['status']=='WAITING_FOR_FACTS')
    (p/'2026-10-30.json').write_text(json.dumps(base),encoding='utf-8')
    (p/'2026-10-30.md').write_text('synthetic old report',encoding='utf-8')
    record('older available file is not a fallback',contract.selected_input(timestamp,p)['status']=='WAITING_FOR_FACTS')
    put(base);actual=contract.selected_input(timestamp,p)
    record('selected complete pair accepted',actual['status']=='READY' and actual['target_day']==day)
    rich={**base,'facts':{**base['facts'],'current_open':[
        {'number':1,'is_pr':False,'title':'Existing question','html_url':'https://github.com/stepll2026/OntiCards/issues/1'},
        {'number':2,'is_pr':True,'title':'A PR','html_url':'https://github.com/stepll2026/OntiCards/pull/2'}]}}
    put(rich,md=day+' '+base['run_id']+' '+base['generated_at']+'\n'+'synthetic long comments '*10000)
    selected=contract.selected_input(timestamp,p)
    record('explicit open Issue facts survive long Markdown',selected['open_issues']==[rich['facts']['current_open'][0]])
    record('tool output excludes duplicated long Markdown',len(json.dumps(selected))<10000 and 'markdown' not in selected)
    for field,value in [('day','2026-10-30'),('repository','someone/else'),('window_end',start.isoformat()),
      ('status','partial'),('generated_at',(trigger+timedelta(minutes=1)).isoformat()),
      ('generated_at',(start-timedelta(minutes=1)).isoformat()),('expires_at',trigger.isoformat())]:
        changed={**base,field:value};put(changed)
        record('reject invalid '+field+' '+str(value),contract.selected_input(timestamp,p)['status']=='INPUT_INVALID')
    changed={**base,'facts':{**base['facts'],'errors':['synthetic API failure']}};put(changed)
    record('API errors rejected',contract.selected_input(timestamp,p)['status']=='INPUT_INVALID')
    put(base,md=day+' another-run '+base['generated_at'])
    record('mismatched JSON/MD runs rejected',contract.selected_input(timestamp,p)['status']=='INPUT_INVALID')
    put(base);(p/(day+'.json')).write_text('{broken',encoding='utf-8')
    record('malformed JSON rejected',contract.selected_input(timestamp,p)['status']=='INPUT_INVALID')

tree=ast.parse((deploy/'init_runtime.py').read_text(encoding='utf-8'))
assignments={n.targets[0].id:n.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
model_id=ast.literal_eval(assignments['model_id'])
config=eval(compile(ast.Expression(assignments['config']),'<config-literal>','eval'),{'model_id':model_id,'model':{'LLM_BASE_URL':'https://example.invalid/v1'}})
provider=config['provider']['bailian']
record('initial native model/timeout/thinking options',model_id=='qwen3.8-max-0902' and provider['options']['timeout']==300000 and provider['models'][model_id]['options']['enable_thinking'] is False and config['agent']['build']['steps']==24)
production_prompt=(deploy/'daily-production-prompt.txt').read_text(encoding='utf-8')
record('production prompt has no frozen acceptance date/run',all(x not in production_prompt for x in ['2026-10-21','8cd49268','673621a8']))
result={'kind':'no-model input-contract validation','model_calls':0,'github_calls':0,'checks':checks,'passed':all(x['passed'] for x in checks),
        'limits':'Tests execute deterministic input selection, not LLM compliance with the production prompt or a native scheduled run.'}
(root/'evidence/daily-input-contract-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[x for x in checks if not x['passed']]}))
raise SystemExit(0 if result['passed'] else 1)
