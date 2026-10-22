"""Run inside only the preview API container; create synthetic SQLite source."""
from pathlib import Path
import sqlite3
import json
import os

target = Path(os.environ.get('ONTICARDS_FIXTURE_PATH','/tmp/onticards-maintenance-fixture.sqlite'))
db = sqlite3.connect(target)
db.execute('CREATE TABLE IF NOT EXISTS maintenance_orders (order_id INTEGER PRIMARY KEY, region TEXT NOT NULL, amount NUMERIC NOT NULL)')
db.executemany('INSERT OR IGNORE INTO maintenance_orders(order_id, region, amount) VALUES (?, ?, ?)', [(1, 'North', 120), (2, 'South', 80), (3, 'North', 50)])
db.commit()
assert db.execute('SELECT COUNT(*), SUM(amount) FROM maintenance_orders').fetchone() == (3, 250)
print(json.dumps({'path': str(target), 'table': 'maintenance_orders', 'rows': 3, 'sum_amount': 250, 'synthetic': True}))
