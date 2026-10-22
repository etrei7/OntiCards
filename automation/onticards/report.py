"""Deterministic repository facts. PyGithub owns HTTP, pagination and retries.

G01/G02: natural-day accounting and durable window/snapshot semantics missing
from the upstream repo-status prompt. No agent, scheduler or GitHub write code.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from github import Auth, Github

UTC = timezone.utc
TZ = ZoneInfo("Asia/Shanghai")
REPOSITORY = "stepll2026/OntiCards"


def stamp():
    return datetime.now(UTC).isoformat()


def window(day):
    start = datetime.combine(date.fromisoformat(day), time(), TZ)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def within(value, start, end):
    if not value:
        return False
    value = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    return start <= value < end


def database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.executescript("""
      PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS snapshots(
        repository TEXT, sampled_at TEXT, stars INTEGER, forks INTEGER,
        PRIMARY KEY(repository, sampled_at));
      CREATE TABLE IF NOT EXISTS reports(
        repository TEXT, day TEXT, run_id TEXT, status TEXT, generated_at TEXT,
        payload TEXT, PRIMARY KEY(repository, day));
      CREATE TABLE IF NOT EXISTS runs(
        run_id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT,
        command TEXT, status TEXT, detail TEXT);
    """)
    return db


def start_run(db, command, recover_interrupted=False):
    """Called after the deployment wrapper acquires the repository's flock.

    Recovery is opt-in so a standalone invocation cannot relabel a live run.
    systemd's timeout/kill cannot execute Python's exception handler; the next
    exclusive invocation records these abandoned attempts before continuing.
    """
    run_id, now = str(uuid.uuid4()), stamp()
    with db:
        if recover_interrupted:
            db.execute("UPDATE runs SET finished_at=?,status='interrupted',detail=? WHERE status='running'",
                       (now, json.dumps({"reason": "previous_process_ended_without_completion",
                                         "detected_at": now})))
        db.execute("INSERT INTO runs VALUES(?,?,NULL,?,'running',NULL)",
                   (run_id, now, command))
    return run_id


def safe(errors, name, action):
    try:
        return action()
    except Exception as exc:
        # Do not serialize request headers, credentials, remote bodies or URLs.
        errors.append({"section": name, "error_type": type(exc).__name__,
                       "http_status": getattr(exc, "status", None)})
        return None


def item(issue):
    r = issue.raw_data
    return {k: r.get(k) for k in ("number", "title", "html_url", "state", "created_at", "updated_at", "closed_at")} | {
        "is_pr": "pull_request" in r,
        "labels": [x.get("name") for x in r.get("labels", [])],
        "comments_count": r.get("comments"),
    }


def collect(repo, start, end, excluded):
    errors = []
    facts = {"errors": errors}
    facts["repository"] = safe(errors, "repository", lambda: {
        "full_name": repo.full_name, "stars": repo.stargazers_count,
        "forks": repo.forks_count, "default_branch": repo.default_branch,
        "html_url": repo.html_url})
    facts["head_sha"] = safe(errors, "head", lambda: repo.get_branch(repo.default_branch).commit.sha)
    open_objects = safe(errors, "current_open", lambda: list(repo.get_issues(state="open")))
    facts["current_open"] = None if open_objects is None else [item(x) for x in open_objects if x.number not in excluded]
    changed = safe(errors, "changed", lambda: list(repo.get_issues(state="all", since=start, sort="updated", direction="asc")))
    facts["changed"] = None if changed is None else [item(x) for x in changed if x.number not in excluded]
    facts["events"] = [] if changed is not None else None
    facts["pull_requests"] = []
    seen = set()
    for issue in changed or []:
        if issue.number in excluded:
            continue
        events = safe(errors, f"events:{issue.number}", lambda: list(issue.get_events()))
        if events is None:
            facts["events"] = None
        elif facts["events"] is not None:
            for event in events:
                r = event.raw_data
                if r.get("id") not in seen and within(r.get("created_at"), start, end):
                    seen.add(r.get("id"))
                    facts["events"].append({"id": r.get("id"), "number": issue.number,
                        "event": r.get("event"), "created_at": r.get("created_at"),
                        "is_pr": "pull_request" in issue.raw_data})
    relevant_prs = {x.number: x for x in (changed or []) + (open_objects or []) if x.number not in excluded and "pull_request" in x.raw_data}
    for number, issue in relevant_prs.items():
        def pr_data():
            pr = issue.as_pull_request()
            r = pr.raw_data
            checks = list(pr.get_commits())[-1].get_combined_status() if pr.commits else None
            return {k: r.get(k) for k in ("number", "html_url", "title", "state", "draft", "merged_at", "mergeable", "mergeable_state")} | {
                "head_sha": pr.head.sha, "base_sha": pr.base.sha,
                "head_repository": pr.head.repo.full_name if pr.head.repo else None,
                "commit_status": checks.state if checks else None,
                "commit_status_count": checks.total_count if checks else None,
                "verification": "未执行本系统测试；GitHub状态不等于业务验证通过"}
        result = safe(errors, f"pr:{number}", pr_data)
        if result is not None:
            facts["pull_requests"].append(result)
    comments = safe(errors, "comments", lambda: list(repo.get_issues_comments(since=start)))
    facts["ai_comments"] = None if comments is None else [
        {"id": c.id, "html_url": c.html_url, "created_at": c.created_at.isoformat()}
        for c in comments if within(c.created_at, start, end)
        and int(c.issue_url.rsplit("/", 1)[-1]) not in excluded
        and "<!-- onticards-ai:" in c.body]
    facts["commits"] = safe(errors, "commits", lambda: [
        {"sha": c.sha, "html_url": c.html_url, "message": c.commit.message.splitlines()[0],
         "committed_at": c.commit.committer.date.isoformat()}
        for c in repo.get_commits(since=start, until=end)
        if within(c.commit.committer.date, start, end)])
    facts["ci_runs"] = safe(errors, "ci_runs", lambda: [
        {k: run.raw_data.get(k) for k in ("id", "html_url", "head_sha", "status", "conclusion", "created_at")}
        for run in repo.get_workflow_runs(created=f"{start.isoformat()}..{end.isoformat()}")
        if within(run.created_at, start, end)])
    return facts


def boundary_snapshot(db, boundary, tolerance=120):
    rows = db.execute("SELECT sampled_at,stars,forks FROM snapshots WHERE repository=?", (REPOSITORY,)).fetchall()
    eligible = [(abs((datetime.fromisoformat(row[0]) - boundary).total_seconds()), row) for row in rows]
    eligible = [x for x in eligible if x[0] <= tolerance]
    return min(eligible, key=lambda x: x[0])[1] if eligible else None


def changes(db, start, end):
    a, b = boundary_snapshot(db, start), boundary_snapshot(db, end)
    return {"status": "已取得日界附近快照" if a and b else "基线建立中",
            "start_snapshot": a, "end_snapshot": b, "tolerance_seconds": 120,
            "stars_net": b[1] - a[1] if a and b else None,
            "forks_net": b[2] - a[2] if a and b else None}


def counts(facts, start, end):
    result = {}
    for kind, pr in (("issues", False), ("prs", True)):
        changed, events = facts.get("changed"), facts.get("events")
        result[kind] = {
            "new": None if changed is None else sum(x["is_pr"] == pr and within(x["created_at"], start, end) for x in changed),
            "closed_events": None if events is None else sum(x["is_pr"] == pr and x["event"] == "closed" for x in events),
            "reopened_events": None if events is None else sum(x["is_pr"] == pr and x["event"] == "reopened" for x in events),
        }
    prs = facts.get("pull_requests", [])
    pr_failure = any(x["section"].startswith("pr:") for x in facts["errors"])
    merged = None if pr_failure or facts.get("changed") is None else sum(within(x.get("merged_at"), start, end) for x in prs)
    result["prs"]["merged"] = merged
    # GitHub can timestamp the merge and its close event a second apart.
    # Earlier closes still count as unmerged, including close/reopen/merge.
    merged_times = {x["number"]: datetime.fromisoformat(x["merged_at"].replace("Z", "+00:00"))
                    for x in prs if x.get("merged_at")}
    result["prs"]["closed_unmerged_events"] = None if pr_failure or facts.get("events") is None else sum(
        x["is_pr"] and x["event"] == "closed" and
        (x["number"] not in merged_times or datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) < merged_times[x["number"]])
        for x in facts["events"])
    return result


def show(value):
    return "未获取" if value is None else str(value)


def markdown(report):
    f, c, s = report["facts"], report["counts"], report["snapshots"]
    repo = f.get("repository") or {}
    lines = [f'# OntiCards 运营日报 {report["day"]}', '',
             f'统计窗口：{report["window_start"]} 至 {report["window_end"]}（左闭右开，北京时间自然日）。',
             f'报告生成：{report["generated_at"]}；实际采集：{f.get("captured_at") or report["generated_at"]}；运行：{report["run_id"]}；状态：{report["status"]}。',
             f'采集来源：{f.get("capture_source") or "服务器 PyGithub 实时只读采集"}。',
             f'本报告文件保留至：{report["expires_at"]}。', '',
             '## A 仓库概况', '',
             f'[stepll2026/OntiCards](https://github.com/{REPOSITORY})，当前主分支 `{f.get("head_sha") or "未获取"}`。',
             f'当前 Star：{show(repo.get("stars"))}；自然日净变化：{show(s["stars_net"])}（{s["status"]}）。',
             f'当前 Fork：{show(repo.get("forks"))}；自然日净变化：{show(s["forks_net"])}。',
             '净变化仅用两端日界±120秒内快照；实际快照时间见JSON。不推算新增/取消Star。', '',
             '## B Issue', '',
             f'新增 {show(c["issues"]["new"])}；关闭事件 {show(c["issues"]["closed_events"])}；重开事件 {show(c["issues"]["reopened_events"])}。',
             '', '## C PR', '',
             f'新增 {show(c["prs"]["new"])}；合并 {show(c["prs"]["merged"])}；未合并关闭事件 {show(c["prs"]["closed_unmerged_events"])}；重开事件 {show(c["prs"]["reopened_events"])}。', '']
    for p in f.get("pull_requests", []):
        lines.append(f'- [PR #{p["number"]} {p["title"]}]({p["html_url"]})：{p["state"]}；冲突状态 {p["mergeable_state"] or "未获取"}；commit status {p["commit_status"] or "未获取"}（{p["commit_status_count"]}项）；head `{p["head_sha"]}`；{p["verification"]}。')
    lines += ['', '## D AI工作与代码 CI', '',
              f'本系统标记的AI评论：{show(None if f["ai_comments"] is None else len(f["ai_comments"]))}；完整执行记录以对应底座run为准。',
              f'默认分支提交：{show(None if f["commits"] is None else len(f["commits"]))}；窗口内Actions运行：{show(None if f["ci_runs"] is None else len(f["ci_runs"]))}。']
    for commit in f.get("commits") or []:
        lines.append(f'- [{commit["sha"][:8]}]({commit["html_url"]}) {commit["message"]}')
    for run in f.get("ci_runs") or []:
        lines.append(f'- [CI {run["id"]}]({run["html_url"]})：{run["status"]}/{run["conclusion"]}，SHA `{run["head_sha"]}`')
    lines += ['', '## E 维护者待办', '', '当前开放项（采集时状态，非昨日末快照）：']
    if f.get("current_open") is None:
        lines.append('- 未获取当前待办。')
    else:
        for x in f["current_open"]:
            age = (datetime.fromisoformat(report["generated_at"]) - datetime.fromisoformat(x["created_at"].replace("Z", "+00:00"))).days
            flags = ["待审查" if x["is_pr"] else "待维护者回复" if x["comments_count"] == 0 else "需检查最新评论"]
            if age >= 7:
                flags.append(f"已开放{age}天")
            flags.extend(x["labels"] or ["优先级未标注"])
            lines.append(f'- [{"PR" if x["is_pr"] else "Issue"} #{x["number"]} {x["title"]}]({x["html_url"]})：{"；".join(flags)}。')
    lines += ['', '最终合并由维护者在GitHub操作。本报告不因缺少检查而将PR标为可合并。', '', '## F 数据质量', '']
    lines.extend(f'- {e["section"]}: {e["error_type"]}, HTTP {e["http_status"]}' for e in f["errors"])
    if not f["errors"]:
        lines.append('- 本次所请求API均成功完成分页；请求期间数据可能继续变化，非事务快照。')
    lines += [f'- Star/Fork：{s["status"]}；不存在的日界历史不会用当前值回填。',
              '- 当前待回复采用无评论/需核对评论口径，未将其冒称精确最后人类回复状态。',
              '- 重新打开和关闭按事件数统计，同一Issue可出现多次；事件按ID去重。',
              '- 统计排除配置的专用日报Issue；初始历史快照不足/后补报采集时间均保留。',
              '- 模型调用量与账单不由本确定性采集器推算。', '']
    return '\n'.join(lines)


def write_report_files(directory, report):
    directory.mkdir(parents=True, exist_ok=True)
    day, run_id = report['day'], report['run_id']
    body = json.dumps(report, ensure_ascii=False, indent=2)
    generated = datetime.fromisoformat(report['generated_at']).timestamp()
    for suffix, content in (("json", body), ("md", markdown(report))):
        target = directory / f'{day}.{suffix}'
        if not target.exists() or target.read_text(encoding='utf-8') != content:
            tmp = directory / f'.{day}.{run_id}.{suffix}.tmp'
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(target)
        # Repair must not extend the deployment's mtime-based 30-day retention.
        if abs(target.stat().st_mtime - generated) > 0.001:
            os.utime(target, (generated, generated))


def repair_report_files(db, directory):
    """Reconcile files with the committed SQLite payload under the external flock.

    A process can be killed between two file replacements. SQLite remains the
    authoritative generation; catch-up cannot skip a report with stale files.
    Expired reports are left to the deployment's retention policy.
    """
    now = datetime.now(UTC)
    for (payload,) in db.execute("SELECT payload FROM reports WHERE repository=?", (REPOSITORY,)):
        report = json.loads(payload)
        if datetime.fromisoformat(report['expires_at']) > now:
            write_report_files(directory, report)


def save_report(db, directory, day, facts, run_id):
    start, end = window(day)
    now = datetime.now(UTC)
    report = {"repository": REPOSITORY, "day": day, "run_id": run_id,
        "window_start": start.astimezone(TZ).isoformat(), "window_end": end.astimezone(TZ).isoformat(),
        "generated_at": now.isoformat(), "expires_at": (now + timedelta(days=30)).isoformat(),
        "status": "partial" if facts["errors"] else "complete",
        "facts": facts, "counts": counts(facts, start, end), "snapshots": changes(db, start, end)}
    body = json.dumps(report, ensure_ascii=False, indent=2)
    # Commit the authoritative payload first; restart repairs any interrupted
    # file publication from this transaction, without querying GitHub again.
    with db:
        db.execute("INSERT INTO reports VALUES(?,?,?,?,?,?) ON CONFLICT(repository,day) DO UPDATE SET run_id=excluded.run_id,status=excluded.status,generated_at=excluded.generated_at,payload=excluded.payload",
                   (REPOSITORY, day, run_id, report["status"], now.isoformat(), body))
    write_report_files(directory, report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["snapshot", "report", "catch-up"])
    parser.add_argument("--state", type=Path, default=Path("state"))
    parser.add_argument("--day", default=(datetime.now(TZ).date() - timedelta(days=1)).isoformat())
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--recover-interrupted", action="store_true",
                        help="Only use while holding the deployment's exclusive flock")
    args = parser.parse_args()
    db = database(args.state / "repository.sqlite3")
    if args.recover_interrupted:
        repair_report_files(db, args.state / "reports")
    run_id = start_run(db, args.command, args.recover_interrupted)
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    excluded = {int(x) for x in os.environ.get("REPORT_ISSUES", "").split(",") if x.strip()}
    client = Github(auth=Auth.Token(token) if token else None, per_page=100, timeout=30, retry=2)
    try:
        repo = client.get_repo(REPOSITORY)
        with db:
            db.execute("INSERT INTO snapshots VALUES(?,?,?,?)", (REPOSITORY, stamp(), repo.stargazers_count, repo.forks_count))
        status = "complete"
        if args.command != "snapshot":
            days = [args.day]
            if args.command == "catch-up":
                first = date.fromisoformat(args.day) - timedelta(days=args.lookback_days - 1)
                days = [(first + timedelta(days=i)).isoformat() for i in range(args.lookback_days)]
                days = [d for d in days if not db.execute("SELECT 1 FROM reports WHERE repository=? AND day=? AND status='complete'", (REPOSITORY, d)).fetchone()]
            for day in days:
                start, end = window(day)
                report = save_report(db, args.state / "reports", day, collect(repo, start, end, excluded), run_id)
                if report["status"] != "complete":
                    status = "partial"
        with db:
            db.execute("UPDATE runs SET finished_at=?,status=? WHERE run_id=?", (stamp(), status, run_id))
        print(json.dumps({"run_id": run_id, "status": status, "command": args.command}))
        return 0 if status == "complete" else 2
    except Exception as exc:
        detail = json.dumps({"error_type": type(exc).__name__, "http_status": getattr(exc, "status", None)})
        with db:
            db.execute("UPDATE runs SET finished_at=?,status='infrastructure_failure',detail=? WHERE run_id=?", (stamp(), detail, run_id))
        print(json.dumps({"run_id": run_id, "status": "infrastructure_failure", "detail": detail}))
        return 2
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
