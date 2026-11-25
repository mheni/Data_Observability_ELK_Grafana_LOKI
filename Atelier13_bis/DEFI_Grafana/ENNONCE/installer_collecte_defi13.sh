#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Executer avec : sudo bash installer_collecte_defi13.sh preparation_defi13' >&2; exit 1; }
[[ $# -eq 1 ]] || { echo 'Usage : sudo bash installer_collecte_defi13.sh preparation_defi13' >&2; exit 1; }
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PREP=$(realpath "$1")
ALLOY=$(command -v alloy || true)
[[ -n "$ALLOY" ]] || { echo 'Binaire alloy introuvable.' >&2; exit 1; }
[[ "$ALLOY" != *' '* ]] || { echo 'Chemin du binaire Alloy non pris en charge.' >&2; exit 1; }
id alloy >/dev/null 2>&1 || { echo 'Compte systeme alloy absent.' >&2; exit 1; }
getent group alloy >/dev/null || { echo 'Groupe alloy absent.' >&2; exit 1; }
command -v ss >/dev/null || { echo 'Commande ss absente.' >&2; exit 1; }
curl --fail-with-body -sS http://127.0.0.1:3100/ready >/dev/null || { echo 'Loki ne repond pas sur 127.0.0.1:3100.' >&2; exit 1; }
if ss -ltnH 'sport = :12348' | grep -q .; then echo 'Port 12348 occupe : ne pas continuer.' >&2; exit 1; fi
for path in /var/log/defi13-openssh /var/lib/alloy-defi13 /etc/alloy-defi13 /etc/systemd/system/alloy-defi13.service; do
  [[ ! -e "$path" ]] || { echo "Ressource deja presente : $path. Ne pas ecraser les donnees ni les positions de lecture." >&2; exit 1; }
done
python3 - "$PREP" <<'PY'
import json, re, sys
from pathlib import Path
base = Path(sys.argv[1])
m = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
if not re.fullmatch(r'[A-Za-z0-9_.:-]+', m['lot']):
    raise SystemExit('Lot invalide')
for key, name in m['files'].items():
    with (base / name).open(encoding='utf-8') as f:
        count = sum(1 for line in f if line.strip())
    if count != m['expected_per_stream']:
        raise SystemExit('Compte local incoherent pour ' + name + ' : ' + str(count))
print('Controle local OK : ' + str(m['expected_per_stream']) + ' lignes par flux')
PY
install -d -m 2750 -o root -g alloy /var/log/defi13-openssh
install -m 640 -o root -g alloy "$PREP/openssh.log" /var/log/defi13-openssh/openssh.log
install -m 640 -o root -g alloy "$PREP/events.jsonl" /var/log/defi13-openssh/events.jsonl
install -d -m 750 -o root -g alloy /etc/alloy-defi13
install -d -m 750 -o alloy -g alloy /var/lib/alloy-defi13
python3 - "$PREP/manifest.json" "$HERE" "$ALLOY" <<'PY'
import json, sys
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
base = Path(sys.argv[2]); binary = sys.argv[3]
Path('/etc/alloy-defi13/config.alloy').write_text((base / 'config_defi13.alloy.in').read_text(encoding='utf-8').replace('__LOT__', manifest['lot']), encoding='utf-8')
Path('/etc/systemd/system/alloy-defi13.service').write_text((base / 'alloy-defi13.service.in').read_text(encoding='utf-8').replace('__BINARY__', binary), encoding='utf-8')
PY
chown root:alloy /etc/alloy-defi13/config.alloy
chmod 640 /etc/alloy-defi13/config.alloy
chmod 644 /etc/systemd/system/alloy-defi13.service
if runuser -u alloy -- "$ALLOY" validate --help >/dev/null 2>&1; then
  runuser -u alloy -- "$ALLOY" validate /etc/alloy-defi13/config.alloy
else
  echo 'Sous-commande validate absente dans cette version d Alloy : controle de configuration saute ; lire journalctl apres demarrage.'
fi
systemctl daemon-reload
systemctl enable --now alloy-defi13
systemctl --no-pager --full status alloy-defi13
