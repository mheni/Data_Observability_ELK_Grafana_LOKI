import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Confirmer les 30 sondes et figer T pour les metriques A12')
p.add_argument('--scenario',default='scenario12.json')
p.add_argument('--output',default='reference12.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=60)
a=p.parse_args()
if a.timeout<1 or a.timeout>180:p.error('--timeout entre 1 et 180 secondes')
if Path(a.output).exists():p.error('Reference deja presente : choisir un nouveau --output')
scenario=json.loads(Path(a.scenario).read_text(encoding='utf-8'))
start=int(scenario['start_ns']);marker=scenario['marker'];deadline=time.monotonic()+a.timeout
expected=scenario['expected']
while True:
    now=time.time_ns()
    if now-start>240*1_000_000_000:
        raise SystemExit('Lot deja trop ancien pour ce controle 5m : produire volontairement un nouveau lot')
    query='{job=~"atelier09|atelier11"} |= '+json.dumps(marker)
    params=urllib.parse.urlencode({'query':query,'start':str(start),'end':str(now),'limit':'200','direction':'forward'})
    with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query_range?'+params,timeout=20) as response:
        result=json.load(response)
    if result.get('status')!='success' or result.get('data',{}).get('resultType')!='streams':
        raise SystemExit('Reponse Loki inattendue : '+str(result)[:2000])
    counts={'access':0,'movies':0,'json':0,'logfmt':0}
    other=0;timestamps=[]
    for stream in result['data']['result']:
        labels=stream['stream'];values=stream.get('values',[])
        if labels.get('job')=='atelier09' and labels.get('dataset') in ['access','movies']:
            key=labels['dataset']
        elif labels.get('job')=='atelier11' and labels.get('format') in ['json','logfmt']:
            key=labels['format']
        else:
            other+=len(values);continue
        counts[key]+=len(values)
        timestamps.extend(int(value[0]) for value in values)
    if other or any(counts[key]>expected[key] for key in counts):
        raise SystemExit('Doublons ou perimetre inattendu : '+str(counts))
    if counts==expected:
        t=time.time_ns()
        seconds,nanos=divmod(t,1_000_000_000)
        result={'marker':marker,'time_ns':str(t),
                'time_utc':datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z',
                'window':'5m','window_seconds':300,'observed':counts,
                'first_loki_timestamp_ns':str(min(timestamps)),
                'last_loki_timestamp_ns':str(max(timestamps))}
        if min(timestamps)<=t-300*1_000_000_000:
            raise SystemExit('Le lot ne tient plus dans la fenetre 5m')
        Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2));break
    if time.monotonic()>=deadline:
        raise SystemExit('Collecte incomplete : '+str(counts))
    time.sleep(2)
