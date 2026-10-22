from types import SimpleNamespace as NS

import pytest

from onticards.report import collect, collector_auth, counts, window
from test_report import comment_repository


def issue(number, start):
    return NS(number=number, raw_data={'number':number,'created_at':start.isoformat(),
        'updated_at':start.isoformat(),'state':'open'}, get_events=lambda: [])


def test_empty_since_response_does_not_hide_current_day_issue():
    start,end=window('2026-10-22')
    repo=comment_repository([])
    obj=issue(31,start)
    calls=[]
    def get_issues(**parameters):
        calls.append(parameters)
        return [] if 'since' in parameters else [obj]
    repo.get_issues=get_issues
    facts=collect(repo,start,end,set())
    assert counts(facts,start,end)['issues']['new']==1
    assert not facts['errors']
    assert any(call['state']=='all' and 'since' not in call for call in calls)


def test_inconsistent_full_listing_is_unknown_not_zero():
    start,end=window('2026-10-22')
    repo=comment_repository([])
    repo.open_issues_count=1
    repo.get_issues=lambda **kw: [issue(31,start)] if kw['state']=='open' else []
    facts=collect(repo,start,end,set())
    assert facts['changed'] is None
    assert counts(facts,start,end)['issues']['new'] is None
    assert facts['errors']==[{'section':'changed','error_type':'InconsistentIssueListing','http_status':None}]


def test_full_list_supplies_open_items_even_when_separate_open_endpoint_is_empty():
    start,end=window('2026-10-22')
    repo=comment_repository([])
    obj=issue(31,start)
    repo.open_issues_count=1
    repo.get_issues=lambda **kw: [obj] if kw['state']=='all' else []
    facts=collect(repo,start,end,set())
    assert [item['number'] for item in facts['current_open']]==[31]
    assert facts['errors']==[]


def test_open_metadata_mismatch_cannot_be_reported_as_complete():
    start,end=window('2026-10-22')
    repo=comment_repository([])
    repo.open_issues_count=0
    repo.get_issues=lambda **kw:[issue(31,start)]
    facts=collect(repo,start,end,set())
    assert facts['current_open'] is None and facts['changed'] is None
    assert counts(facts,start,end)['issues']['new'] is None
    assert facts['errors'][0]['error_type']=='InconsistentIssueListing'


def test_app_auth_uses_runtime_credential_and_read_permissions(monkeypatch,tmp_path):
    import onticards.report as module
    monkeypatch.setenv('REPORT_GITHUB_APP_ID','5422414')
    monkeypatch.setenv('REPORT_GITHUB_INSTALLATION_ID','174029282')
    monkeypatch.setenv('CREDENTIALS_DIRECTORY',str(tmp_path))
    (tmp_path/'github-app.pem').write_text('synthetic-private-key')
    observed={}
    def factory(app_id,key):
        observed.update(app_id=app_id,key=key)
        def install(installation,permissions):
            observed.update(installation=installation,permissions=permissions)
            return 'native-auth'
        return NS(get_installation_auth=install)
    monkeypatch.setattr(module.Auth,'AppAuth',factory)
    assert collector_auth()=='native-auth'
    assert observed['app_id']==5422414 and observed['installation']==174029282
    assert observed['key']=='synthetic-private-key'
    assert set(observed['permissions'].values())=={'read'}
    assert set(observed['permissions'])=={'contents','issues','pull_requests','actions','checks','metadata'}


def test_incomplete_app_configuration_never_falls_back_anonymous(monkeypatch):
    monkeypatch.setenv('REPORT_GITHUB_APP_ID','5422414')
    monkeypatch.delenv('REPORT_GITHUB_INSTALLATION_ID',raising=False)
    monkeypatch.delenv('CREDENTIALS_DIRECTORY',raising=False)
    with pytest.raises(ValueError,match='Incomplete'):
        collector_auth()


def test_auth_failure_reserves_window_and_recovers_beyond_lookback(monkeypatch,tmp_path):
    import sys
    import onticards.report as module
    from test_report import facts
    def broken_auth():
        raise ValueError('synthetic configuration failure')
    monkeypatch.setattr(module,'collector_auth',broken_auth)
    monkeypatch.setattr(sys,'argv',['report','report','--state',str(tmp_path),'--day','2026-10-10'])
    assert module.main()==2
    db=module.database(tmp_path/'repository.sqlite3')
    assert db.execute("SELECT status FROM reports WHERE day='2026-10-10'").fetchone()==('pending',)
    module.save_report(db,tmp_path/'reports','2026-10-21',facts(),'already-complete')
    db.close()
    class Client:
        def __init__(self,**kwargs):pass
        def get_repo(self,name):return NS(stargazers_count=1,forks_count=1)
        def close(self):pass
    dates=[]
    def collect(repo,start,end,excluded):
        dates.append(start.astimezone(module.TZ).date().isoformat())
        return facts()
    monkeypatch.setattr(module,'collector_auth',lambda:None)
    monkeypatch.setattr(module,'Github',Client)
    monkeypatch.setattr(module,'collect',collect)
    monkeypatch.setattr(sys,'argv',['report','catch-up','--state',str(tmp_path),'--day','2026-10-21','--lookback-days','1','--recover-interrupted'])
    assert module.main()==0
    assert dates==['2026-10-10']
