import argparse
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Verifier dans Loki le lot OpenSSH par agregations, sans telecharger les lignes')
p.add_argument('--manifest', default='preparation_defi13/manifest.json')
p.add_argument('--output', default='reference_loki_defi13.json')
p.add_argument('--url', default=os.environ.get('LOKI_URL', 'http://127.0.0.1:3100'))
p.add_argument('--timeout', type=int, default=300)
a = p.parse_args()
if Path(a.output).exists():
    p.error('Sortie deja presente : choisir un autre nom')
if not 1 <= a.timeout <= 1800:
    p.error('Timeout entre 1 et 1800 secondes')
mp = Path(a.manifest)
m = json.loads(mp.read_text(encoding='utf-8'))
ref = json.loads((mp.parent / m['reference_file']).read_text(encoding='utf-8'))
lot = m['lot']
n = int(m['expected_per_stream'])
start = int(m['prepared_start_ns']) - 5_000_000_000
raw_sel = '{job="defi13_openssh_raw",format="raw",lot=' + json.dumps(lot) + '}'
json_sel = '{job="defi13_openssh",format="json",lot=' + json.dumps(lot) + '}'

def call(query, end):
    params = urllib.parse.urlencode({'query': query, 'time': str(end), 'timeout': '60s'})
    try:
        with urllib.request.urlopen(a.url.rstrip('/') + '/loki/api/v1/query?' + params, timeout=70) as response:
            r = json.load(response)
    except Exception as exc:
        raise SystemExit('Erreur API Loki : ' + str(exc))
    if r.get('status') != 'success' or r.get('data', {}).get('resultType') != 'vector':
        raise SystemExit('Reponse Loki inattendue : ' + str(r)[:300])
    return r['data']['result']

def scalar(selector, seconds, end, extra=''):
    result = call('sum(count_over_time(' + selector + extra + ' [' + str(seconds) + 's]))', end)
    if not result:
        return 0
    if len(result) != 1:
        raise SystemExit('Agregation non scalaire')
    value = float(result[0]['value'][1])
    if not math.isfinite(value) or value < 0 or value != int(value):
        raise SystemExit('Compte invalide')
    return int(value)

deadline = time.monotonic() + a.timeout
while True:
    end = time.time_ns()
    seconds = math.ceil((end - start) / 1e9)
    observed = {'raw': scalar(raw_sel, seconds, end), 'json': scalar(json_sel, seconds, end)}
    if any(v > n for v in observed.values()):
        raise SystemExit('Surplus de lignes : ' + str(observed) + ' ; attendu ' + str(n) + ' par flux. Verifier une double collecte.')
    if all(v == n for v in observed.values()):
        types_query = 'sum by (v_type) (count_over_time(' + json_sel + ' | json v_type="event_type" | __error__="" | v_type!="" [' + str(seconds) + 's]))'
        loki_types = {item['metric'].get('v_type', ''): int(float(item['value'][1])) for item in call(types_query, end)}
        if loki_types != ref['event_type_counts']:
            raise SystemExit('Volumes identiques mais repartition des types differente : ' + str(loki_types))
        canonical = scalar(json_sel, seconds, end, ' | json v_auth="is_auth_record" | __error__="" | v_auth="1"')
        failures = scalar(json_sel, seconds, end, ' | json v_fail="is_failure" | __error__="" | v_fail="1"')
        successes = scalar(json_sel, seconds, end, ' | json v_ok="is_success" | __error__="" | v_ok="1"')
        if (canonical, failures, successes) != (ref['A_canonical_records'], ref['F_failures'], ref['S_successes']):
            raise SystemExit('Comptes canoniques differents : ' + str((canonical, failures, successes)))
        iso = lambda ns: datetime.fromtimestamp(ns / 1e9, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        result = {'lot': lot, 'source_sha256': m['source_sha256'], 'expected_per_stream': n, 'observed': observed,
                  'A_canonical_records': canonical, 'F_failures': failures, 'S_successes': successes,
                  'event_type_counts': loki_types, 'from_ns': str(start), 'to_ns': str(end), 'from_utc': iso(start), 'to_utc': iso(end),
                  'validation': 'aggregate_counts_event_types_and_auth_flags', 'all_record_ids_checked': False,
                  'note': 'Egalite de volumes et de repartitions ; pas une preuve identifiant par identifiant.'}
        Path(a.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        break
    print('Collecte en cours : ' + str(observed) + ' ; attendu ' + str(n), flush=True)
    if time.monotonic() >= deadline:
        raise SystemExit('Collecte incomplete : lire journalctl -u alloy-defi13 ; ' + str(observed))
    time.sleep(5)
