#!/bin/sh
set -eu
base=/opt/onticards-maintenance
config_dir="$base/reporting-deploy"
if ! getent passwd onticards-report >/dev/null; then
  useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin onticards-report
fi
# Grant only this dedicated group traversal of the previously private parent.
chgrp onticards-report "$base"
chmod 0710 "$base"
install -d -o root -g onticards-report -m 0750 "$base/reporting"
tar -xzf "$base/reporting-source.tar.gz" -C "$base/reporting" --no-same-owner
chown -R root:onticards-report "$base/reporting"
find "$base/reporting" -type d -exec chmod 0750 {} +
find "$base/reporting" -type f -exec chmod 0640 {} +
python3 -m venv "$base/reporting/.venv"
env HTTP_PROXY=http://127.0.0.1:17891 HTTPS_PROXY=http://127.0.0.1:17891 \
  NO_PROXY=localhost,127.0.0.1,::1 \
  "$base/reporting/.venv/bin/python" -m pip install --disable-pip-version-check \
  -r "$base/reporting/requirements.txt"
chgrp -R onticards-report "$base/reporting"
chmod -R g+rX "$base/reporting"
install -o root -g root -m 0644 "$config_dir/onticards-collector@.service" /etc/systemd/system/onticards-collector@.service
install -o root -g root -m 0644 "$config_dir/onticards-report.timer" /etc/systemd/system/onticards-report.timer
install -o root -g root -m 0644 "$config_dir/onticards-snapshot.timer" /etc/systemd/system/onticards-snapshot.timer
install -o root -g root -m 0644 "$config_dir/onticards-report.tmpfiles.conf" /etc/tmpfiles.d/onticards-report.conf
if [ ! -f "$base/reporting.env" ]; then
  install -o root -g root -m 0600 "$config_dir/reporting.env.example" "$base/reporting.env"
fi
systemd-tmpfiles --create /etc/tmpfiles.d/onticards-report.conf
systemd-analyze verify /etc/systemd/system/onticards-collector@.service /etc/systemd/system/onticards-report.timer /etc/systemd/system/onticards-snapshot.timer
systemctl daemon-reload
"$base/reporting/.venv/bin/python" -m pip freeze
printf 'Installed; timers are enabled only after acceptance checks.\n'
