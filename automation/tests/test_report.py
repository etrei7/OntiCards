from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest

from onticards.report import counts, changes, database, safe, save_report, start_run, window, within, repair_report_files


def test_window_is_previous_shanghai_day_not_nine_to_nine():
    start, end = window("2026-10-21")
    assert start.isoformat() == "2026-10-20T16:00:00+00:00"
    assert end.isoformat() == "2026-10-21T16:00:00+00:00"
    assert within(start, start, end)
    assert not within(end, start, end)


def facts():
    return {"errors": [], "changed": [], "events": [], "pull_requests": [],
            "repository": {"stars": 479, "forks": 8}, "head_sha": "abc",
            "current_open": [], "ai_comments": [], "commits": [], "ci_runs": []}


def test_initial_or_nine_am_snapshots_cannot_imply_zero_net_change(tmp_path):
    db = database(tmp_path / "state.db")
    start, end = window("2026-10-21")
    db.execute("INSERT INTO snapshots VALUES(?,?,?,?)", ("stepll2026/OntiCards", (start + timedelta(hours=9)).isoformat(), 478, 8))
    db.execute("INSERT INTO snapshots VALUES(?,?,?,?)", ("stepll2026/OntiCards", (end + timedelta(hours=9)).isoformat(), 479, 8))
    assert changes(db, start, end)["stars_net"] is None


def test_boundary_snapshots_preserve_actual_time_and_negative_change(tmp_path):
    db = database(tmp_path / "state.db")
    start, end = window("2026-10-21")
    for t, s in ((start + timedelta(seconds=21), 479), (end + timedelta(seconds=43), 477)):
        db.execute("INSERT INTO snapshots VALUES(?,?,?,?)", ("stepll2026/OntiCards", t.isoformat(), s, 8))
    result = changes(db, start, end)
    assert result["stars_net"] == -2
    assert result["start_snapshot"][0].endswith("16:00:21+00:00")


def test_pr_and_issue_are_separate_and_multiple_close_events_count():
    start, end = window("2026-10-21")
    f = facts()
    f["changed"] = [{"is_pr": x, "created_at": start.isoformat()} for x in [True, False]]
    f["events"] = [{"is_pr": False, "number": 1, "created_at": start.isoformat(), "event": x}
                   for x in ["closed", "reopened", "closed"]]
    result = counts(f, start, end)
    assert result["issues"] == {"new": 1, "closed_events": 2, "reopened_events": 1}
    assert result["prs"]["new"] == 1


def test_merge_does_not_hide_earlier_unmerged_close():
    start, end = window("2026-10-21")
    f = facts()
    merged_at = (start + timedelta(hours=1)).isoformat()
    f["pull_requests"] = [{"number": 1, "merged_at": merged_at}]
    f["events"] = [{"is_pr": True, "number": 1, "event": "closed", "created_at": t}
                   for t in (start.isoformat(), (start + timedelta(hours=1, seconds=1)).isoformat())]
    result = counts(f, start, end)["prs"]
    assert result["merged"] == 1
    assert result["closed_unmerged_events"] == 1


def test_failed_collection_is_unknown_not_zero():
    f = facts()
    f["changed"] = f["events"] = None
    start, end = window("2026-10-21")
    assert counts(f, start, end)["issues"]["new"] is None
    assert counts(f, start, end)["prs"]["merged"] is None
    errors = []
    def fail():
        raise RuntimeError("secret must not enter report")
    assert safe(errors, "api", fail) is None
    assert "secret" not in str(errors)


def test_retry_and_restart_replace_same_logical_report(tmp_path):
    db = database(tmp_path / "state.db")
    save_report(db, tmp_path / "reports", "2026-10-21", facts(), "attempt1")
    db.close()
    db = database(tmp_path / "state.db")
    updated = facts()
    updated["repository"]["stars"] = 480
    save_report(db, tmp_path / "reports", "2026-10-21", updated, "attempt2")
    assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 1
    assert db.execute("SELECT run_id FROM reports").fetchone()[0] == "attempt2"
    assert len(list((tmp_path / "reports").glob("*.md"))) == 1
    assert "480" in (tmp_path / "reports/2026-10-21.md").read_text(encoding="utf-8")


def test_exclusive_restart_recovers_interrupted_attempt_without_losing_report(tmp_path):
    db = database(tmp_path / "state.db")
    old = start_run(db, "report")
    save_report(db, tmp_path / "reports", "2026-10-21", facts(), old)
    db.close()  # Simulates termination after saving but before run completion.
    db = database(tmp_path / "state.db")
    new = start_run(db, "catch-up", recover_interrupted=True)
    assert db.execute("SELECT status FROM runs WHERE run_id=?", (old,)).fetchone()[0] == "interrupted"
    assert db.execute("SELECT status FROM runs WHERE run_id=?", (new,)).fetchone()[0] == "running"
    assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 1


def test_standalone_invocation_does_not_relabel_another_live_process(tmp_path):
    db = database(tmp_path / "state.db")
    old = start_run(db, "report")
    start_run(db, "snapshot")
    assert db.execute("SELECT status FROM runs WHERE run_id=?", (old,)).fetchone()[0] == "running"


def test_kill_between_json_and_markdown_is_repaired_from_sqlite_without_recapture(tmp_path, monkeypatch):
    db = database(tmp_path / "state.db")
    directory = tmp_path / 'reports'
    save_report(db, directory, '2026-10-21', facts(), 'old')
    replacement = Path.replace
    def fail_markdown(path, target):
        if str(target).endswith('.md'):
            raise OSError('simulated interrupted file publication')
        return replacement(path, target)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'replace', fail_markdown)
        with pytest.raises(OSError):
            save_report(db, directory, '2026-10-21', facts(), 'new')
    assert json.loads((directory / '2026-10-21.json').read_text(encoding='utf-8'))['run_id'] == 'new'
    assert '运行：old' in (directory / '2026-10-21.md').read_text(encoding='utf-8')
    db.close()
    db = database(tmp_path / 'state.db')
    repair_report_files(db, directory)
    assert '运行：new' in (directory / '2026-10-21.md').read_text(encoding='utf-8')
    assert db.execute('SELECT run_id FROM reports').fetchone()[0] == 'new'
    saved = json.loads(db.execute('SELECT payload FROM reports').fetchone()[0])
    generated = datetime.fromisoformat(saved['generated_at']).timestamp()
    assert abs((directory / '2026-10-21.md').stat().st_mtime - generated) < 0.001


def test_catch_up_recovers_known_partial_older_than_lookback_without_unknown_history(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import sys
    import onticards.report as module

    db = database(tmp_path / 'repository.sqlite3')
    incomplete = facts()
    incomplete['errors'] = [{'section': 'issues', 'error_type': 'TimeoutError', 'http_status': None}]
    save_report(db, tmp_path / 'reports', '2026-10-10', incomplete, 'old-failure')
    save_report(db, tmp_path / 'reports', '2026-10-22', incomplete, 'future-failure')
    for day in range(15, 22):
        save_report(db, tmp_path / 'reports', f'2026-10-{day}', facts(), 'already-complete')
    db.close()
    collected = []
    def collect(repo, start, end, excluded):
        collected.append(start.astimezone(module.TZ).date().isoformat())
        return facts()
    class Client:
        def __init__(self, **kwargs): pass
        def get_repo(self, name):
            assert name == module.REPOSITORY
            return SimpleNamespace(stargazers_count=479, forks_count=8)
        def close(self): pass
    monkeypatch.setattr(module, 'Github', Client)
    monkeypatch.setattr(module, 'collect', collect)
    monkeypatch.setattr(sys, 'argv', ['report', 'catch-up', '--state', str(tmp_path), '--day', '2026-10-21'])
    assert module.main() == 0
    assert collected == ['2026-10-10']
    db = database(tmp_path / 'repository.sqlite3')
    assert db.execute("SELECT status FROM reports WHERE day='2026-10-10'").fetchone()[0] == 'complete'
    assert db.execute("SELECT run_id,status FROM reports WHERE day='2026-10-22'").fetchone() == ('future-failure', 'partial')
    assert db.execute("SELECT COUNT(*) FROM reports WHERE run_id='already-complete'").fetchone()[0] == 7
    assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 9
    db.close()


def test_entry_failure_records_window_and_preserves_completed_history(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import sys
    import onticards.report as module

    class Client:
        failing = True
        def __init__(self, **kwargs): pass
        def get_repo(self, name):
            if self.failing:
                raise TimeoutError('sensitive infrastructure detail')
            return SimpleNamespace(stargazers_count=1, forks_count=1)
        def close(self): pass
    monkeypatch.setattr(module, 'Github', Client)
    db = database(tmp_path / 'repository.sqlite3')
    saved = save_report(db, tmp_path / 'reports', '2026-10-09', facts(), 'prior-complete')
    original_file = (tmp_path / 'reports/2026-10-09.json').read_bytes()
    for day in range(15, 22):
        save_report(db, tmp_path / 'reports', f'2026-10-{day}', facts(), 'recent-complete')
    db.close()
    for day in ('2026-10-10', '2026-10-09', '2026-10-22', '2026-10-10'):
        monkeypatch.setattr(sys, 'argv', ['report', 'report', '--state', str(tmp_path), '--day', day])
        assert module.main() == 2
    db = database(tmp_path / 'repository.sqlite3')
    assert db.execute("SELECT status,payload FROM reports WHERE day='2026-10-10'").fetchone() == ('pending', None)
    assert json.loads(db.execute("SELECT payload FROM reports WHERE day='2026-10-09'").fetchone()[0]) == saved
    db.close()
    Client.failing = False
    collected = []
    def collect(repo, start, end, excluded):
        collected.append(start.astimezone(module.TZ).date().isoformat())
        return facts()
    monkeypatch.setattr(module, 'collect', collect)
    monkeypatch.setattr(sys, 'argv', ['report', 'catch-up', '--recover-interrupted', '--state', str(tmp_path), '--day', '2026-10-21'])
    assert module.main() == 0
    assert collected == ['2026-10-10']
    assert (tmp_path / 'reports/2026-10-09.json').read_bytes() == original_file
    db = database(tmp_path / 'repository.sqlite3')
    assert db.execute("SELECT status,payload FROM reports WHERE day='2026-10-22'").fetchone() == ('pending', None)
    assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 10
    assert db.execute("SELECT COUNT(*) FROM reports WHERE run_id='recent-complete'").fetchone()[0] == 7
    db.close()


def test_terminated_process_window_survives_beyond_lookback(tmp_path, monkeypatch):
    import os
    import subprocess
    import sys
    import time
    from types import SimpleNamespace
    import onticards.report as module

    ready = tmp_path / 'network-entry-ready'
    child = '''
import pathlib, sys, time
sys.path.insert(0, sys.argv[1])
import onticards.report as m
state, ready = sys.argv[2:4]
class Client:
    def __init__(self, **kwargs): pass
    def get_repo(self, name):
        pathlib.Path(ready).write_text('ready')
        time.sleep(300)
    def close(self): pass
m.Github = Client
sys.argv = ['report', 'report', '--state', state, '--day', '2026-10-10']
m.main()
'''
    environment = os.environ.copy()
    environment.pop('GITHUB_TOKEN', None)
    process = subprocess.Popen([sys.executable, '-c', child, str(Path(module.__file__).parents[1]), str(tmp_path), str(ready)], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 15
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert ready.exists(), 'child did not reach the simulated network boundary'
    finally:
        process.kill()
        process.communicate(timeout=10)
    assert process.returncode != 0
    db = database(tmp_path / 'repository.sqlite3')
    assert db.execute("SELECT status,payload FROM reports WHERE day='2026-10-10'").fetchone() == ('pending', None)
    assert db.execute("SELECT status FROM runs").fetchone()[0] == 'running'
    save_report(db, tmp_path / 'reports', '2026-10-21', facts(), 'recent-complete')
    db.close()
    class Client:
        def __init__(self, **kwargs): pass
        def get_repo(self, name): return SimpleNamespace(stargazers_count=1, forks_count=1)
        def close(self): pass
    collected = []
    def collect(repo, start, end, excluded):
        collected.append(start.astimezone(module.TZ).date().isoformat())
        return facts()
    monkeypatch.setattr(module, 'Github', Client)
    monkeypatch.setattr(module, 'collect', collect)
    monkeypatch.setattr(sys, 'argv', ['report', 'catch-up', '--lookback-days', '1', '--recover-interrupted', '--state', str(tmp_path), '--day', '2026-10-21'])
    assert module.main() == 0
    assert collected == ['2026-10-10']
    db = database(tmp_path / 'repository.sqlite3')
    assert db.execute("SELECT COUNT(*) FROM runs WHERE status='interrupted'").fetchone()[0] == 1
    assert db.execute("SELECT status FROM reports WHERE day='2026-10-10'").fetchone()[0] == 'complete'
    assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 2
    db.close()


@pytest.mark.parametrize('head_status_unavailable', [False, True])
def test_status_uses_exact_pr_head_beyond_capped_commit_list(head_status_unavailable):
    from types import SimpleNamespace as NS
    from github import GithubException
    from onticards.report import collect

    start, end = window('2026-10-21')
    head = 'f' * 40
    old = NS(get_combined_status=lambda: NS(state='success', total_count=1))
    pr = NS(commits=251, head=NS(sha=head, repo=None), base=NS(sha='b' * 40),
            get_commits=lambda: [old] * 250,
            raw_data={'number': 777, 'title': 'API boundary fixture', 'state': 'open', 'merged_at': None})
    issue = NS(number=777, raw_data={'number': 777, 'pull_request': {}, 'created_at': start.isoformat()},
               get_events=lambda: [], as_pull_request=lambda: pr)
    looked_up = []
    def get_commit(sha):
        looked_up.append(sha)
        if head_status_unavailable:
            raise GithubException(403, {'message': 'sensitive API body'})
        return NS(get_combined_status=lambda: NS(state='failure', total_count=2), get_check_runs=lambda: [])
    repo = NS(full_name='stepll2026/OntiCards', stargazers_count=1, forks_count=1, default_branch='main',
              html_url='https://github.com/stepll2026/OntiCards', get_branch=lambda _: NS(commit=NS(sha='b' * 40)),
              get_issues=lambda **_: [issue], get_issues_comments=lambda **_: [], get_commits=lambda **_: [],
              get_workflow_runs=lambda **_: [], get_commit=get_commit)
    result = collect(repo, start, end, set())
    assert looked_up == [head]
    if head_status_unavailable:
        assert result['pull_requests'] == []
        assert result['errors'] == [{'section': 'pr:777', 'error_type': 'GithubException', 'http_status': 403}]
        assert 'sensitive API body' not in json.dumps(result)
    else:
        assert result['pull_requests'][0]['head_sha'] == head
        assert result['pull_requests'][0]['commit_status'] == 'failure'
        assert result['pull_requests'][0]['commit_status_count'] == 2
        assert result['errors'] == []


def comment_repository(comments):
    from types import SimpleNamespace as NS
    return NS(full_name='stepll2026/OntiCards', stargazers_count=1, forks_count=1, default_branch='main',
              html_url='https://github.com/stepll2026/OntiCards', get_branch=lambda _: NS(commit=NS(sha='b' * 40)),
              get_issues=lambda **_: [], get_issues_comments=lambda **_: comments,
              get_commits=lambda **_: [], get_workflow_runs=lambda **_: [])


def comment(number, created_at, user_id=346235449, user_type='Bot', issue=25, body='Native task failed; see execution log.'):
    from types import SimpleNamespace as NS
    return NS(id=number, created_at=created_at, body=body,
              html_url=f'https://github.com/stepll2026/OntiCards/issues/{issue}#issuecomment-{number}',
              issue_url=f'https://api.github.com/repos/stepll2026/OntiCards/issues/{issue}',
              user=NS(id=user_id, type=user_type, login='onticards-maintainer-stepll2026[bot]'))


def test_ai_comments_use_verified_bot_id_and_type_not_body_or_login(tmp_path):
    from onticards.report import collect, markdown
    start, end = window('2026-10-21')
    items = [comment(1, start), comment(2, start, body='<!-- onticards-ai:review -->'),
             comment(3, start, user_id=123, user_type='User', body='<!-- onticards-ai:success -->'),
             comment(4, start, user_id=999, body='<!-- onticards-ai:success -->'),
             comment(5, start, user_type='User', body='<!-- onticards-ai:success -->')]
    items.append(comment(6, start))
    items[-1].user = None  # Deleted/missing account cannot identify this App.
    result = collect(comment_repository(items), start, end, set())
    assert [x['id'] for x in result['ai_comments']] == [1, 2]
    assert result['ai_comments'][0] == {
        'id': 1, 'html_url': items[0].html_url, 'created_at': start.isoformat(), 'issue_number': 25,
        'author': {'id': 346235449, 'type': 'Bot', 'login': 'onticards-maintainer-stepll2026[bot]'},
        'marker_present': False}
    assert result['ai_comment_identity'] == {'user_id': 346235449, 'type': 'Bot', 'source': 'GitHub comment.user'}
    report = save_report(database(tmp_path / 'state.db'), tmp_path / 'reports', '2026-10-21', result, 'identity-test')
    rendered = markdown(report)
    assert f']({items[0].html_url})' in rendered
    assert 'Issue/PR #25' in rendered and '346235449' in rendered
    assert '评论数量不代表执行成功' in rendered
    assert '本系统标记的AI评论' not in rendered


def test_ai_comment_window_and_report_issue_exclusion():
    from onticards.report import collect
    start, end = window('2026-10-21')
    items = [comment(1, start - timedelta(microseconds=1)), comment(2, start),
             comment(3, end - timedelta(microseconds=1)), comment(4, end),
             comment(5, start, issue=30), comment(6, start, body=None)]
    result = collect(comment_repository(items), start, end, {30})
    assert [x['id'] for x in result['ai_comments']] == [2, 3, 6]
    assert result['ai_comments'][-1]['marker_present'] is False
    assert result['errors'] == []


@pytest.mark.parametrize('failure_at', ['pagination', 'author'])
def test_ai_comment_api_failures_remain_unknown_and_redacted(failure_at):
    from github import GithubException
    from onticards.report import collect
    start, end = window('2026-10-21')
    def fail():
        raise GithubException(403, {'message': 'sensitive comment API body'})
    def comments():
        yield comment(1, start)
        if failure_at == 'pagination':
            fail()
        class LazyComment:
            id = 2
            created_at = start
            issue_url = 'https://api.github.com/repos/stepll2026/OntiCards/issues/25'
            body = ''
            @property
            def user(self): return fail()
        yield LazyComment()
    result = collect(comment_repository(comments()), start, end, set())
    assert result['ai_comments'] is None
    assert result['errors'] == [{'section': 'comments', 'error_type': 'GithubException', 'http_status': 403}]
    assert 'sensitive comment API body' not in json.dumps(result)


def legacy_report():
    start, end = window('2026-10-21')
    f = facts()
    f['ai_comments'] = [{'id': 1, 'html_url': 'https://github.com/stepll2026/OntiCards/issues/1#issuecomment-1',
                         'created_at': start.isoformat()}]
    return {'repository': 'stepll2026/OntiCards', 'day': '2026-10-21', 'run_id': 'legacy-marker',
            'window_start': '2026-10-21T00:00:00+08:00', 'window_end': '2026-10-22T00:00:00+08:00',
            'generated_at': '2026-10-22T01:00:00+00:00', 'expires_at': '2099-01-01T00:00:00+00:00',
            'status': 'complete', 'facts': f, 'counts': counts(f, start, end),
            'snapshots': {'status': '基线建立中', 'start_snapshot': None, 'end_snapshot': None,
                          'tolerance_seconds': 120, 'stars_net': None, 'forks_net': None}}


def test_legacy_marker_payload_keeps_frozen_markdown_and_repair_does_not_rewrite(tmp_path, monkeypatch):
    import hashlib
    from onticards.report import markdown, write_report_files
    report = legacy_report()
    # Frozen from the deployed pre-identity renderer, before changing production code.
    assert hashlib.sha256(markdown(report).encode()).hexdigest() == 'b38f451d97ddaeb0a97741a02e53bce8baa6c50a8437e07c32e8e56382de53d2'
    db = database(tmp_path / 'state.db')
    body = json.dumps(report, ensure_ascii=False, indent=2)
    db.execute('INSERT INTO reports VALUES(?,?,?,?,?,?)',
               (report['repository'], report['day'], report['run_id'], report['status'], report['generated_at'], body))
    db.commit()
    directory = tmp_path / 'reports'
    write_report_files(directory, report)
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()}
    def no_rewrite(*args): raise AssertionError('legacy report file was rewritten')
    monkeypatch.setattr(Path, 'replace', no_rewrite)
    repair_report_files(db, directory)
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()}
    assert db.execute('SELECT payload FROM reports').fetchone()[0] == body
    db.close()
