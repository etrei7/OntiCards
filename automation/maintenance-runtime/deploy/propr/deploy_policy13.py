"""Reuse Compose for a drained, reversible update; builds occur only on kol."""
import datetime,hashlib,json,os,sqlite3,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path('/opt/onticards-maintenance/propr')
OLD='registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy12@sha256:ccb66ea8a0e6af41d277627d8ca04c445bcb28fe3efd2917ff02de7cf4566faa'
NEW='registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy13@sha256:3bef8bdeac0024fd513a85e1951329d8c955c3f9ef292908ed6d409cc84ef879'
EVIDENCE=ROOT/'evidence/policy13-deployment'
def run(args):return subprocess.run(args,cwd=ROOT,check=True,text=True,capture_output=True)
def counts():
    return {state:int(run(['docker','exec','onticards-propr-redis-1','redis-cli','-p','18124','LLEN' if state in ('wait','active','paused') else 'ZCARD','bull:github-issue-processor:'+state]).stdout) for state in ('wait','active','paused','delayed','prioritized','waiting-children')}
def services():
    result=[]
    for name in ('api','worker','daemon'):
        value=json.loads(run(['docker','inspect','onticards-propr-'+name]).stdout)[0]
        result.append({'name':name,'image':value['Config']['Image'],'image_id':value['Image'],'state':value['State']['Status'],'started_at':value['State']['StartedAt']})
    return result
def main():
    assert NEW.startswith('registry-intl.cn-hongkong.aliyuncs.com/shallopcr/propr-app:onticards-42931b1-policy13@sha256:') and len(NEW.rsplit(':',1)[1])==64, 'Candidate digest is not finalized'
    before=(ROOT/'compose.yaml').read_text()
    assert before.count(OLD)==1 and NEW not in before
    initial=services();assert all(item['image']==OLD and item['state']=='running' for item in initial)
    runtime=ROOT/'runtime.env'
    runtime_hash=hashlib.sha256(runtime.read_bytes()).hexdigest()
    EVIDENCE.mkdir(exist_ok=False)
    record={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'old_image':OLD,'new_image':NEW,'before':initial,'build_on_test_host':False}
    (EVIDENCE/'deployment.json').write_text(json.dumps(record,indent=2)+'\n')
    pull=run(['docker','pull',NEW]);(EVIDENCE/'pull.log').write_text(pull.stdout+pull.stderr)
    run(['docker','compose','stop','daemon'])
    try:
        record['queue_before']=counts();assert not any(record['queue_before'].values())
        with sqlite3.connect('file:'+str(ROOT/'data/propr.sqlite')+'?mode=ro',uri=True) as db:
            assert db.execute("SELECT COUNT(*) FROM agent_runs WHERE state NOT IN ('completed','failed','cancelled','skipped')").fetchone()[0]==0
            backup_fd=os.open(str(EVIDENCE/'before.sqlite'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(backup_fd)
            with sqlite3.connect(EVIDENCE/'before.sqlite') as destination:db.backup(destination)
        (EVIDENCE/'before.sqlite').chmod(0o600)
    except Exception:
        run(['docker','start','onticards-propr-daemon'])
        raise
    run(['docker','compose','stop','worker','api'])
    (EVIDENCE/'compose-before.yaml').write_text(before)
    record['runtime_change']={'modified':False,'sha256':runtime_hash}
    (ROOT/'compose.yaml').write_text(before.replace(OLD,NEW))
    up=run(['docker','compose','up','-d','--no-deps','api','worker','daemon'])
    (EVIDENCE/'compose-up.log').write_text(up.stdout+up.stderr)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for attempt in range(30):
        try:
            with opener.open('http://127.0.0.1:18122/health',timeout=2) as response:
                if response.status==200:break
        except Exception:pass
        time.sleep(1)
    else:raise RuntimeError('API health not ready')
    assert hashlib.sha256(runtime.read_bytes()).hexdigest()==runtime_hash, 'Runtime changed during update'
    after=services();assert all(item['image']==NEW and item['state']=='running' for item in after)
    record.update(after=after,queue_after=counts(),source_tree='0af2178f1461819a893d6705a0e23dcad6330595',compose_sha256=hashlib.sha256((ROOT/'compose.yaml').read_bytes()).hexdigest(),completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),success=True)
    (EVIDENCE/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()

