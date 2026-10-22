"""Native systemd read-only bind mount; reuses OpenCode's existing config mount."""
import json
from pathlib import Path
import subprocess

source = Path('/var/lib/onticards-report/reports')
target = Path('/opt/onticards-maintenance/propr/opencode/report-inputs')
target.mkdir(parents=True, exist_ok=True)
subprocess.run(['setfacl', '-R', '-m', 'u:1000:rX', str(source)], check=True)
subprocess.run(['setfacl', '-d', '-m', 'u:1000:rX', str(source)], check=True)
unit = subprocess.check_output(['systemd-escape', '--path', '--suffix=mount', str(target)], text=True).strip()
Path('/etc/systemd/system', unit).write_text(f'''[Unit]
Description=OntiCards read-only facts for the existing OpenCode runtime
Before=docker.service

[Mount]
What={source}
Where={target}
Type=none
Options=bind,ro

[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl', 'daemon-reload'], check=True)
subprocess.run(['systemctl', 'enable', '--now', unit], check=True)
print(json.dumps({'unit': unit, 'source': str(source), 'destination': str(target), 'read_only': True}))
