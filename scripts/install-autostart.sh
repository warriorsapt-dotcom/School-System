#!/usr/bin/env bash
# Install the boot service for the school's Ubuntu/Tailscale test VM.
set -euo pipefail

fail() { echo "$*" >&2; exit 1; }
[[ $(uname -s) == Linux && -d /run/systemd/system ]] || fail "Run this on the Ubuntu VM with systemd."
(( EUID != 0 )) || fail "Run as the school account. The installer calls sudo where needed."

project=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
account=$(id -un)
python="$project/.venv312/bin/python"
unit=school-system.service
[[ $project =~ ^/[a-zA-Z0-9_./-]+$ && $account =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ ]] || fail "Unsupported account name or project path."
[[ -x $python && -f $project/manage.py ]] || fail "Expected manage.py and .venv312/bin/python in $project."
cd "$project"
"$python" manage.py check
address=$(tailscale ip -4) || fail "Connect the VM to Tailscale, then run the installer again."
[[ $address =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "Expected one Tailscale IPv4 address."
if ! systemctl is-active --quiet "$unit" && [[ -n $(ss -H -ltn 'sport = :8000') ]]; then
    fail "Port 8000 is in use. Stop the manually started server with Ctrl+C, then rerun this script."
fi

unit_file=$(mktemp)
trap 'rm -f -- "$unit_file"' EXIT
cat >"$unit_file" <<EOF
[Unit]
Description=School System on Tailscale
Wants=network-online.target postgresql.service tailscaled.service
After=network-online.target postgresql.service tailscaled.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=$account
WorkingDirectory=$project
Environment=PYTHONUNBUFFERED=1
ExecStart=$python $project/manage.py runserver $address:8000 --noreload
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF
sudo install -m 0644 "$unit_file" "/etc/systemd/system/$unit"
sudo systemctl daemon-reload
sudo systemctl enable "$unit"
sudo systemctl restart "$unit"

# Type=simple can be active before Django is actually listening.
if "$python" - "$address" <<'PY'
import http.client
import sys
import time

for _ in range(20):
    conn = http.client.HTTPConnection(sys.argv[1], 8000, timeout=1)
    try:
        conn.request("GET", "/")
        if conn.getresponse().status == 200:
            sys.exit(0)
    except OSError:
        pass
    finally:
        conn.close()
    time.sleep(1)
sys.exit(1)
PY
then
    echo "Ready at http://$address:8000/ and enabled at boot."
else
    fail "Service installed, but the login page did not respond successfully. Check: sudo journalctl -u $unit -n 50 --no-pager"
fi
