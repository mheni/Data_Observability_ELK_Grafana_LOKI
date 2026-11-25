import argparse
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Verifier le lot access dans Loki par des agregations, sans telecharger toutes les lignes')
p.add_argument('--manifest',default='preparation13bis/manifest.json')
p.add_argument('--output',default='reference13bis.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=600)
a=p.parse_args()
if Path(a.output).exists():p.error('Sortie deja presente ; choisir un autre nom')
if not 1<=a.timeout<=1800:p.error('Timeout entre 1 et 1800 secondes')
mp=Path(a.manifest);m=json.loads(mp.read_text());ref=json.loads((mp.parent/m['reference_file']).read_text());lot=m['lot'];n=m['expected_per_format']
if n!=ref['nonempty_lines'] or n<1:p.error('Manifest et reference incoherents')
start=int(m['prepared_start_ns'])-5_000_000_000
selectors={
    'raw':'{job="atelier13bis_raw",dataset="access",format="raw",lot='+json.dumps(lot)+'}',
    'json':'{job="atelier13bis",format="json",lot='+json.dumps(lot)+'}',
    'logfmt':'{job="atelier13bis",format="logfmt",lot='+json.dumps(lot)+'}'}

def call(query,end):
    params=urllib.parse.urlencode({'query':query,'time':str(end),'timeout':'60s'})
    try:
        with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query?'+params,timeout=70) as f:r=json.load(f)
    except Exception as ex:raise SystemExit('Erreur API Loki : '+str(ex))
    if r.get('status')!='success' or r.get('data',{}).get('resultType')!='vector':raise SystemExit('Reponse Loki inattendue : '+str(r)[:300])
    return r['data']['result']
def count(selector,seconds,end):
    result=call('sum(count_over_time('+selector+' ['+str(seconds)+'s]))',end)
    if not result:return 0
    if len(result)!=1:raise SystemExit('Compte agrege non scalaire')
    value=float(result[0]['value'][1])
    if not math.isfinite(value) or value<0 or value!=int(value):raise SystemExit('Compte invalide')
    return int(value)

deadline=time.monotonic()+a.timeout
while True:
    end=time.time_ns();seconds=math.ceil((end-start)/1e9)
    if seconds<1:raise SystemExit('Horloge invalide')
    observed={fmt:count(sel,seconds,end) for fmt,sel in selectors.items()}
    if any(v>n for v in observed.values()):raise SystemExit('Surplus de lignes : '+str(observed))
    if all(v==n for v in observed.values()):
        status_expr='sum by (v_status)(count_over_time('+selectors['json']+' | json v_status="status" | __error__="" | v_status!="" ['+str(seconds)+'s]))'
        codes={entry['metric']['v_status']:int(float(entry['value'][1])) for entry in call(status_expr,end)}
        if codes!={str(k):v for k,v in ref['status_counts'].items()}:raise SystemExit('Volumes arrives mais repartition HTTP differente de la source : '+str(codes))
        iso=lambda ns:datetime.fromtimestamp(ns/1e9,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        # The display period may extend to the current instant; the source lot remains fixed.
        r={'lot':lot,'source_sha256':m['source_sha256'],'expected_per_format':n,'observed':observed,'http_status_counts':codes,
           'from_ns':str(start),'to_ns':str(end),'from_utc':iso(start),'to_utc':iso(end),
           'validation':'aggregate_counts_and_status_distribution','all_event_ids_checked':False,
           'note':'Egalite de volumes et distribution HTTP ; pas preuve d identite de chaque evenement en ligne.'}
        Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2));break
    print('Collecte en cours : '+str(observed)+' ; attendu '+str(n)+' par format',flush=True)
    if time.monotonic()>=deadline:raise SystemExit('Collecte incomplete : consulter journalctl -u alloy-atelier13bis-access ; '+str(observed))
    time.sleep(5)
