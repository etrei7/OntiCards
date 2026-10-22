from datetime import datetime, timedelta, timezone
import json
import sqlite3
from types import SimpleNamespace as NS

import pytest

from onticards.native_activity import snapshot, select_window, publish_snapshot
from onticards.report import collect, window
from test_report import comment_repository


def pr_repository(checks):
    repo=comment_repository([])
    start,_=window('2026-10-22')
    pr=NS(raw_data={'number':33,'title':'fixture','state':'open'},head=NS(sha='a'*40,repo=None),base=NS(sha='b'*40))
    issue=NS(number=33,raw_data={'number':33,'pull_request':{},'created_at':start.isoformat(),'state':'open'},get_events=lambda:[],as_pull_request=lambda:pr)
    repo.get_issues=lambda **kwargs:[issue]
    repo.open_issues_count=1
    observed=[]
    def commit(sha):
        observed.append(sha)
        return NS(get_combined_status=lambda:NS(state='pending',total_count=0),get_check_runs=lambda:checks())
    repo.get_commit=commit
    return repo,observed


def test_checks_are_independent_of_zero_commit_statuses():
    runs=[NS(raw_data={'id':119950685976,'name':'concurrency','head_sha':'a'*40,'status':'completed','conclusion':'success','html_url':'https://github.com/stepll2026/OntiCards/runs/119950685976','details_url':'http://10.66.66.5:18123/onticards-reports/acceptance/pr33-fdd3/'})]
    repo,observed=pr_repository(lambda:iter(runs))
    facts=collect(repo,*window('2026-10-22'),set())
    pr=facts['pull_requests'][0]
    assert observed==['a'*40]
    assert pr['commit_status_count']==0 and len(pr['check_runs'])==1
    assert pr['check_runs'][0]['conclusion']=='success'
    assert '未执行本系统测试' not in pr['verification']


def test_check_pagination_failure_preserves_pr_and_marks_unknown():
    def failed_page():
        yield NS(raw_data={'id':1})
        raise RuntimeError('private response must not be serialized')
    repo,_=pr_repository(failed_page)
    facts=collect(repo,*window('2026-10-22'),set())
    assert facts['pull_requests'][0]['check_runs'] is None
    assert facts['errors']==[{'section':'checks:33','error_type':'RuntimeError','http_status':None}]
    assert 'private response' not in json.dumps(facts)


def test_failed_native_snapshot_is_not_zero_activity(monkeypatch,tmp_path):
    path=tmp_path/'native.json';path.write_text(json.dumps({'status':'unavailable'}))
    monkeypatch.setenv('REPORT_NATIVE_ACTIVITY_PATH',str(path))
    facts=collect(comment_repository([]),*window('2026-10-22'),set())
    assert facts['native_activity'] is None
    assert facts['errors'][-1]['section']=='native_activity'


def native_db(path):
    db=sqlite3.connect(path)
    db.executescript('CREATE TABLE tasks(task_id,repository,issue_number,task_type,model_name,created_at,initial_job_data);CREATE TABLE task_history(history_id INTEGER PRIMARY KEY,task_id,state,timestamp,reason,metadata);')
    for task,repo in [('ours','stepll2026/onticards'),('other','another/repository')]:
        db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?)',(task,repo,33,'fix','configured-model','2026-10-22 14:00:00','SECRET INITIAL DATA'))
        for state,at in [('started','2026-10-22 14:00:00'),('completed','2026-10-22 15:00:00'),('later','2026-10-22 17:00:00')]:
            db.execute('INSERT INTO task_history(task_id,state,timestamp,reason,metadata) VALUES(?,?,?,?,?)',(task,state,at,'SECRET REASON','SECRET METADATA'))
    db.commit();db.close()


def test_native_export_scope_window_and_secret_columns(tmp_path):
    path=tmp_path/'native.sqlite';native_db(path)
    now=datetime(2026,10,22,18,tzinfo=timezone.utc)
    data=snapshot(path,now)
    assert [task['task_id'] for task in data['tasks']]==['ours']
    assert 'SECRET' not in json.dumps(data)
    selected=select_window(data,*window('2026-10-22'),now)
    assert selected['tasks'][0]['native_state_at_window_end']=='completed'
    assert 'later' not in json.dumps(selected)


@pytest.mark.parametrize('kind',['stale','future','coverage','failed','repository'])
def test_native_snapshot_rejects_invalid_source(tmp_path,kind):
    path=tmp_path/'native.sqlite';native_db(path)
    now=datetime(2026,10,22,18,tzinfo=timezone.utc)
    data=snapshot(path,now)
    if kind=='stale':data['captured_at']=(now-timedelta(hours=1)).isoformat()
    if kind=='future':data['captured_at']=(now+timedelta(minutes=1)).isoformat()
    if kind=='coverage':data['coverage_start']=now.isoformat()
    if kind=='failed':data['status']='unavailable'
    if kind=='repository':data['repository']='another/repository'
    with pytest.raises(ValueError):select_window(data,*window('2026-10-22'),now)


def test_root_snapshot_does_not_follow_preexisting_temporary_symlink(tmp_path):
    import os
    if os.name=='nt':pytest.skip('Linux production symlink boundary')
    target=tmp_path/'unrelated';target.write_text('retain this')
    output=tmp_path/'native-activity.json'
    output.with_suffix('.tmp').symlink_to(target)
    output.symlink_to(target)
    publish_snapshot(output,{'status':'complete','tasks':[]})
    assert target.read_text()=='retain this'
    assert not output.is_symlink()
    assert json.loads(output.read_text())['status']=='complete'
