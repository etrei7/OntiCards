"""Real synthetic product flow; evidence omits credentials and auth headers."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import requests

ROOT=Path(__file__).parent
OUT=Path(os.environ['ONTICARDS_PRODUCT_EVIDENCE_DIR'])
OUT.mkdir(exist_ok=True)
session=requests.Session()
session.trust_env=False
BASE=os.environ['ONTICARDS_PREVIEW_URL'].rstrip('/')+'/console/api'
credentials=json.loads(Path(os.environ['ONTICARDS_PREVIEW_CREDENTIALS']).read_text())
login=session.post(BASE+'/login',json=credentials,timeout=30).json()
assert login['code']==200,'Synthetic login failed'
session.headers['Authorization']=login['data']['token']
records=json.loads(OUT.joinpath('flow-summary.json').read_text()).get('steps',[]) if OUT.joinpath('flow-summary.json').exists() else []

def redact(value):
    if isinstance(value,dict):
        return {k:('[omitted]' if any(s in k.lower() for s in ['password','token','api_key','connect_info']) else redact(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    return value

def call(name,path,payload=None,method=None):
    started=time.monotonic()
    response=session.request(method or ('POST' if payload is not None else 'GET'),BASE+path,json=payload,timeout=300)
    try: body=response.json()
    except ValueError: body={'non_json':True,'bytes':len(response.content)}
    safe=redact(body)
    OUT.joinpath(name+'.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    record={'step':name,'status':response.status_code,'duration_seconds':round(time.monotonic()-started,3),'code':body.get('code'),'evidence':name+'.json'}
    records.append(record)
    OUT.joinpath('flow-summary.json').write_text(json.dumps({'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha':os.environ['ONTICARDS_TESTED_HEAD_SHA'],'synthetic_data_only':True,'steps':records},indent=2)+'\n')
    print(json.dumps(record),flush=True)
    assert response.status_code==200 and body.get('code')==200,f'{name} failed; see sanitized evidence'
    return body

if __name__=='__main__':
    if not OUT.joinpath('extract-schema.json').exists():
        call('extract-schema','/extract_schema',{'db_type':'sqlite','sqlite_path':'/tmp/onticards-maintenance-fixture.sqlite','connect_name':'maintenance-synthetic-baseline','request_id':os.environ['ONTICARDS_RUN_ID']})
    extracted=json.loads(OUT.joinpath('extract-schema.json').read_text(encoding='utf-8'))
    assert len(extracted['data']['generated_cards'])==1,'Expected one real generated card'
    datasource=extracted['data']['datasource_info']['id']
    sources=call('datasources','/datasource_tool')
    assert any(x['id']==datasource and x['table_num']==1 for x in sources['data']['items'])
    cards=call('cards','/datacard_tool?group_by=flat&parse_json=true')
    assert cards['data']['total_cards']==1
    card=cards['data']['items'][0]
    card_data=card['card_data']
    if isinstance(card_data,str): card_data=json.loads(card_data)
    marker=' [Synthetic preview: reviewed for maintenance smoke test.]'
    if marker not in card_data['Abstract']:
        card_data['Abstract']+=marker
        call('edit-card','/datacard_tool',{'doc_id':card['doc_id'],'w_uuid':card['w_uuid'],'card_data':card_data},method='PUT')
    reloaded=call('cards-after-edit','/datacard_tool?group_by=flat&parse_json=true')
    assert marker in reloaded['data']['items'][0]['card_data']['Abstract']
    query=call('query-total','/query_by_datacards_agg',{'query':'查询 maintenance_orders 表的所有订单 amount 总和，以 total_amount 为列名。','datasource_id':datasource})
    assert query['data']['final_rows']==[{'total_amount':250}]
    if OUT.joinpath('governance-execute.json').exists():
        governance=json.loads(OUT.joinpath('governance-execute.json').read_text(encoding='utf-8'))
    else: governance=call('governance-execute','/governance/execute',{'datasource_id':datasource,'include_basic_audit':True,'include_relation_discovery':False})
    assert governance['data']['basic_audit_detail']['rules_count']==3
    assert all(row['total_count']==3 and row['passed_count']==3 for row in governance['data']['basic_audit_detail']['results'])
    report_id=governance['data']['report_id']
    for format in ['xlsx','docx','md','pdf']:
        call('export-'+format,'/governance/report',{'report_id':report_id,'format':format,'file_name':'maintenance-synthetic-quality'})
        downloaded=session.get(BASE+'/governance/reports/'+report_id+'/download',timeout=300)
        assert downloaded.status_code==200
        assert len(downloaded.content)>100
        OUT.joinpath('quality-report.'+format).write_bytes(downloaded.content)
        print(json.dumps({'download':format,'bytes':len(downloaded.content),'sha256':hashlib.sha256(downloaded.content).hexdigest()}),flush=True)
