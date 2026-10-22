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
