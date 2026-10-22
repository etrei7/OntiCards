"""Export only existing ProPR task metadata; no new task state or scheduler."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import quote

REPOSITORY = 'stepll2026/OntiCards'


def snapshot(database, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=35)
    result = {'repository': REPOSITORY, 'captured_at': now.isoformat(),
              'coverage_start': since.isoformat(), 'status': 'complete', 'tasks': []}
    with sqlite3.connect('file:' + str(Path(database).resolve()) + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('''SELECT t.task_id,t.issue_number,t.task_type,t.model_name,t.created_at,
            h.state,h.timestamp FROM tasks t JOIN task_history h ON h.task_id=t.task_id
            WHERE lower(t.repository)=? AND julianday(h.timestamp)>=julianday(?)
            ORDER BY h.history_id''', (REPOSITORY.lower(), since.isoformat()))
        grouped = {}
        for row in rows:
            value = dict(row)
            task_id = value['task_id']
            if not re.fullmatch(r'[A-Za-z0-9_.:\-]{1,255}', task_id):
                raise ValueError('Unexpected native task identifier')
            if task_id not in grouped:
                grouped[task_id] = {key:value[key] for key in ('task_id','issue_number','task_type','model_name','created_at')}
                grouped[task_id].update(url='http://10.66.66.5:18123/tasks/'+quote(task_id,safe=''),history=[])
            grouped[task_id]['history'].append({'state':value['state'],'timestamp':value['timestamp']})
        result['tasks'] = list(grouped.values())
    return result


def select_window(data, start, end, now=None):
    now = now or datetime.now(timezone.utc)
    captured = datetime.fromisoformat(data['captured_at'])
    if data['repository'] != REPOSITORY or data['status'] != 'complete':
        raise ValueError('Native activity source unavailable')
    if not timedelta(0) <= now-captured <= timedelta(minutes=20):
        raise ValueError('Native activity snapshot is stale')
    if datetime.fromisoformat(data['coverage_start']) > start:
        raise ValueError('Native activity snapshot does not cover requested window')
    def parsed(value):
        value=datetime.fromisoformat(value.replace('Z','+00:00'))
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    selected=[]
    for task in data['tasks']:
        history=[event for event in task['history'] if parsed(event['timestamp'])<end]
        if any(start<=parsed(event['timestamp'])<end for event in history):
            selected.append({key:value for key,value in task.items() if key!='history'} |
                {'native_state_at_window_end':history[-1]['state'],'last_event_at':history[-1]['timestamp']})
    return {'source':'ProPR native tasks/task_history, selected metadata only',
            'captured_at':data['captured_at'],'tasks':selected,
            'meaning':'Native state is not independent semantic review or business-test acceptance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=snapshot(args.database)
    except Exception as error:
        result={'repository':REPOSITORY,'captured_at':datetime.now(timezone.utc).isoformat(),
                'status':'unavailable','error_type':type(error).__name__}
    # A failed read replaces stale success; the collector records partial data.
    publish_snapshot(args.output,result)
    print(json.dumps({'status':result['status'],'task_count':len(result.get('tasks',[]))}))


def publish_snapshot(output,result):
    # The directory belongs to the collector. Never open/chmod a predictable path as root.
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',prefix='.native-activity-',
                                     dir=output.parent,delete=False) as file:
        temporary=Path(file.name)
        json.dump(result,file,ensure_ascii=False)
        file.flush()
        os.fchmod(file.fileno(),0o644)
    try:
        os.replace(temporary,output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__=='__main__':
    main()
