"""One-time operator baseline from the existing committed n8n intake, read-only.
No GitHub client, scheduler, event store, credential read or source-body output.
"""
import datetime,hashlib,json,re,sqlite3
from pathlib import Path
DB=Path('/opt/onticards-maintenance/n8n/persistent/state/database.sqlite')
def read_baseline(expected_config_head):
    assert re.fullmatch('[a-f0-9]{40}',expected_config_head)
    db=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        db.execute('BEGIN')
        tables={}
        for row in db.execute("select name from sqlite_master where type='table' and name like 'data_table_user_%'"):
            name=row['name'];assert re.fullmatch('[a-zA-Z0-9_]+',name)
            columns={c[1] for c in db.execute('pragma table_info("'+name+'")')}
            for role,required in [('watermark',{'repository','watermark','poll_id','thread_count'}),('threads',{'thread_key','snapshot','observed_at','kind','number'}),('runs',{'poll_id','status','started_at','finished_at','details'})]:
                if required.issubset(columns):
                    assert role not in tables, 'Ambiguous native intake table schema'
                    tables[role]=name
        assert set(tables)=={'watermark','threads','runs'}, 'Existing native intake tables unavailable'
        mark=db.execute('select * from "'+tables['watermark']+'" where repository=?',('stepll2026/OntiCards',)).fetchone()
        assert mark is not None
        run=db.execute('select * from "'+tables['runs']+'" where poll_id=? order by id desc limit 1',(mark['poll_id'],)).fetchone()
        assert run and run['status']=='complete_readonly_dry_run'
        details=json.loads(run['details'])
        assert details.get('token_revoked') is True and details.get('watermark')==mark['watermark']
        observed=datetime.datetime.fromisoformat(mark['watermark'].replace('Z','+00:00'))
        assert 0 <= (datetime.datetime.now(datetime.timezone.utc)-observed).total_seconds() <= 600, 'No fresh complete snapshot; wait for existing native poll'
        rows=db.execute('select thread_key,number,kind,snapshot from "'+tables['threads']+'" where observed_at=?',(run['started_at'],)).fetchall()
        assert len(rows)==mark['thread_count']
        versions=[]
        for row in rows:
            if row['kind']!='pull_request':continue
            value=json.loads(row['snapshot'])
            if value['state']!='open':continue
            number=int(row['number']);assert number==row['number'] and 1<=number<=9999999
            assert value['number']==number and value['kind']=='pull_request'
            assert row['thread_key']=='stepll2026/OntiCards#'+str(number)
            assert all(re.fullmatch('[a-f0-9]{40}',value[k]) for k in ['head','base'])
            versions.append({'pr':number,'head':value['head'],'base':value['base'],'observed_at':run['finished_at']})
        assert len(versions)<=20 and len({v['pr'] for v in versions})==len(versions)
        assert next(v for v in versions if v['pr']==30)['head']==expected_config_head, 'Final configuration PR head not yet in complete intake'
        for v in versions:v['review_key']='review-'+hashlib.sha256(json.dumps(['stepll2026/OntiCards',v['pr'],v['head'],v['base']],separators=(',',':')).encode()).hexdigest()
        return {'source':'onticards_intake_threads_v1','poll_id':mark['poll_id'],'watermark':mark['watermark'],'thread_count':mark['thread_count'],'token_revoked':True,'versions':versions,'config_head':expected_config_head}
    finally:db.close()
if __name__=='__main__':
    import sys
    assert len(sys.argv)==2
    print(json.dumps(read_baseline(sys.argv[1]),indent=2))
