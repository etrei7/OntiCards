"""Use the existing config event channel; do not restart or launch model work."""
import datetime,json,subprocess
from pathlib import Path
root=Path('/opt/onticards-maintenance/propr')
event={'type':'config_update','subtype':'agents_update','timestamp':int(datetime.datetime.now().timestamp()*1000)}
subscribers=int(subprocess.check_output(['docker','exec','onticards-propr-redis-1','redis-cli','-p','18124','PUBLISH','system:config:events',json.dumps(event)],text=True))
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_event':event,'subscribers':subscribers,'model_calls':0,'passed':subscribers>=2}
(root/'evidence/daily-alias-registry-refresh.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));assert record['passed']
