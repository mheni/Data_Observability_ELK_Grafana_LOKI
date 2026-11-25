#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Executer avec sudo bash.' >&2; exit 1; }
[[ $# -eq 1 ]] || { echo 'Usage : sudo bash installer_collecte13bis.sh preparation13bis' >&2; exit 1; }
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PREP=$(realpath "$1")
ALLOY=$(command -v alloy)
[[ "$ALLOY" != *' '* ]] || { echo 'Chemin du binaire Alloy non pris en charge'; exit 1; }
id alloy >/dev/null
getent group alloy >/dev/null
command -v ss >/dev/null
curl --fail-with-body -sS http://127.0.0.1:3100/ready >/dev/null
if ss -ltnH 'sport = :12347' | grep -q .; then echo 'Port 12347 occupe ; ne pas continuer.' >&2; exit 1; fi
for p in /var/log/atelier13bis-access /var/lib/alloy-atelier13bis-access /etc/alloy-atelier13bis-access /etc/systemd/system/alloy-atelier13bis-access.service; do
  [[ ! -e "$p" ]] || { echo "Ressource deja presente : $p. Ne pas ecraser les donnees/positions." >&2; exit 1; }
done
python3 - "$PREP" <<'PY'
import json,re,sys
from pathlib import Path
base=Path(sys.argv[1]);m=json.loads((base/'manifest.json').read_text())
if not re.fullmatch(r'[A-Za-z0-9_.:-]+',m['lot']):raise SystemExit('Lot invalide')
for name in ['access_log','events.jsonl','events.logfmt']:
    with (base/name).open(encoding='utf-8') as f:n=sum(1 for line in f if line.strip())
    if n!=m['expected_per_format']:raise SystemExit('Compte local incoherent pour '+name)
PY
install -d -m 2750 -o root -g alloy /var/log/atelier13bis-access
for name in access_log events.jsonl events.logfmt; do
  install -m 640 -o root -g alloy "$PREP/$name" "/var/log/atelier13bis-access/$name"
done
install -d -m 750 -o root -g alloy /etc/alloy-atelier13bis-access
install -d -m 750 -o alloy -g alloy /var/lib/alloy-atelier13bis-access
python3 - "$PREP/manifest.json" "$HERE" "$ALLOY" <<'PY'
import json,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text());base=Path(sys.argv[2]);binary=sys.argv[3]
Path('/etc/alloy-atelier13bis-access/config.alloy').write_text((base/'config13bis.alloy.in').read_text().replace('__LOT__',m['lot']))
Path('/etc/systemd/system/alloy-atelier13bis-access.service').write_text((base/'alloy-atelier13bis-access.service.in').read_text().replace('__BINARY__',binary))
PY
chown root:alloy /etc/alloy-atelier13bis-access/config.alloy
chmod 640 /etc/alloy-atelier13bis-access/config.alloy
chmod 644 /etc/systemd/system/alloy-atelier13bis-access.service
runuser -u alloy -- "$ALLOY" validate /etc/alloy-atelier13bis-access/config.alloy
systemctl daemon-reload
systemctl enable --now alloy-atelier13bis-access
systemctl --no-pager --full status alloy-atelier13bis-access
