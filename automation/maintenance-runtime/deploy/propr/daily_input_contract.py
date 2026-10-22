"""Read-only date/window validation for native ProPR reports; no I/O except the selected facts.

Reuses Python date/zoneinfo; ProPR owns scheduling and OpenCode owns tool execution.
Only the native Task timestamp selects the day. Missing data never falls back to latest.
"""
import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

REPORTS = Path('/home/node/.config/opencode/report-inputs')
TZ = ZoneInfo('Asia/Shanghai')

def expected_window(triggered_at):
    trigger = datetime.fromisoformat(triggered_at.replace('Z', '+00:00'))
    if trigger.tzinfo is None:
        raise ValueError('Native Task timestamp must include its UTC offset')
    target_day = trigger.astimezone(TZ).date() - timedelta(days=1)
    start = datetime.combine(target_day, time(), TZ)
    return target_day.isoformat(), start, start + timedelta(days=1), trigger

def selected_input(triggered_at, directory=REPORTS):
    day, start, end, trigger = expected_window(triggered_at)
    paths = [directory/(day+suffix) for suffix in ('.json', '.md')]
    identity = {'target_day': day, 'window_start': start.isoformat(), 'window_end': end.isoformat(),
                'triggered_at': trigger.astimezone(timezone.utc).isoformat()}
    if not all(p.is_file() for p in paths):
        return {**identity, 'status': 'WAITING_FOR_FACTS', 'reason': 'The selected date JSON/Markdown pair is missing'}
    try:
        data = json.loads(paths[0].read_text(encoding='utf-8'))
        markdown = paths[1].read_text(encoding='utf-8')
        checks = [data.get('repository') == 'stepll2026/OntiCards', data.get('day') == day,
            datetime.fromisoformat(data['window_start']) == start,
            datetime.fromisoformat(data['window_end']) == end,
            data.get('status') == 'complete', data['facts'].get('errors') == [],
            isinstance(data['facts']['head_sha'], str), isinstance(data['facts']['pull_requests'], list),
            isinstance(data['facts']['current_open'], list), isinstance(data['counts'], dict),
            bool(data.get('run_id')), data['run_id'] in markdown,
            data['generated_at'] in markdown, day in markdown,
            end <= datetime.fromisoformat(data['generated_at']) <= trigger,
            datetime.fromisoformat(data['expires_at']) > trigger]
        if not all(checks):
            raise ValueError('Repository/date/window/status/errors/run pair/availability time failed validation')
    except (KeyError, TypeError, ValueError, OSError) as error:
        return {**identity, 'status': 'INPUT_INVALID', 'reason': str(error)}
    return {**identity, 'status': 'READY',
        'metadata': {key: data[key] for key in ('repository','day','run_id','window_start','window_end','generated_at','status')},
        'errors': data['facts']['errors'], 'head_sha': data['facts']['head_sha'],
        'repository': data['facts']['repository'], 'counts': data['counts'], 'snapshots': data['snapshots'],
        'open_issues': [item for item in data['facts']['current_open'] if not item['is_pr']],
        'pull_requests': data['facts']['pull_requests'], 'commits': data['facts']['commits'],
        'ai_comment_count': len(data['facts']['ai_comments']),
        'ai_comment_threads': sorted({item['issue_number'] for item in data['facts']['ai_comments']}),
        'ci_runs': data['facts']['ci_runs'],
        'native_activity': data['facts'].get('native_activity'),
        'facts_report_url': 'http://10.66.66.5:18123/onticards-reports/'+day+'.md',
        'quality_notes': ['API requests succeeded but are not a transaction snapshot',
            'Current open items describe collection time, not day-end historical state',
            'Bot comment count is not proof of successful repairs; refer to native task evidence',
            'Commit status is separate from Checks and local business verification',
            'commit_status_count counts legacy commit statuses, never GitHub Checks; use check_runs for Checks',
            'Native task status is recorded system state, not proof of semantic or business acceptance',
            'Unknown daily snapshot differences are not zero'],
        'source_paths': [str(p) for p in paths]}

if __name__ == '__main__':
    try:
        result = selected_input(sys.argv[1])
    except (IndexError, ValueError) as error:
        result = {'status': 'INPUT_INVALID', 'reason': str(error)}
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['status'] == 'READY' else 2)
