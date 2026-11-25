#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo 'Executer avec sudo bash.' >&2; exit 1; fi
if [[ $# -ne 2 ]]; then echo 'Usage: sudo bash installer_collecte13bis.sh sources13bis corpus13bis' >&2; exit 1; fi
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SOURCES=$(realpath "$1"); CORPUS=$(realpath "$2")
ALLOY=$(command -v alloy)
[[ "$ALLOY" != *' '* ]] || { echo 'Chemin du binaire avec espaces non pris en charge'; exit 1; }
id alloy >/dev/null
getent group alloy >/dev/null
for p in "$SOURCES/access_log" "$SOURCES/movies.csv" "$CORPUS/events.jsonl" "$CORPUS/events.logfmt" "$CORPUS/manifest.json"; do
  test -s "$p" || { echo "Fichier absent/vide : $p" >&2; exit 1; }
done
curl --fail-with-body -fsS http://127.0.0.1:3100/ready >/dev/null
if ss -ltnH 'sport = :12346' | grep -q .; then echo 'Port 12346 deja occupe. Arreter et adapter avant installation.' >&2; exit 1; fi
for p in /var/log/formation13bis /var/lib/alloy-atelier13bis /etc/alloy-atelier13bis /etc/systemd/system/alloy-atelier13bis.service; do
  if [[ -e "$p" ]]; then echo "Ressource deja presente : $p ; ne pas ecraser. Consulter le support." >&2; exit 1; fi
done
install -d -m 2750 -o root -g alloy /var/log/formation13bis
for d in raw json logfmt; do install -d -m 2750 -o root -g alloy "/var/log/formation13bis/$d"; done
install -m 640 -o root -g alloy "$SOURCES/access_log" /var/log/formation13bis/raw/access_log
install -m 640 -o root -g alloy "$SOURCES/movies.csv" /var/log/formation13bis/raw/movies.csv
install -m 640 -o root -g alloy "$CORPUS/events.jsonl" /var/log/formation13bis/json/events.jsonl
install -m 640 -o root -g alloy "$CORPUS/events.logfmt" /var/log/formation13bis/logfmt/events.logfmt
install -d -m 750 -o alloy -g alloy /var/lib/alloy-atelier13bis
install -d -m 750 -o root -g alloy /etc/alloy-atelier13bis
install -m 640 -o root -g alloy "$HERE/config-atelier13bis.alloy" /etc/alloy-atelier13bis/config.alloy
runuser -u alloy -- "$ALLOY" validate /etc/alloy-atelier13bis/config.alloy
sed "s|@ALLOY@|$ALLOY|g" "$HERE/alloy-atelier13bis.service.in" > /etc/systemd/system/alloy-atelier13bis.service
chmod 644 /etc/systemd/system/alloy-atelier13bis.service
systemctl daemon-reload
systemctl enable --now alloy-atelier13bis
systemctl --no-pager --full status alloy-atelier13bis
