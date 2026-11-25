import argparse
import json
import os
import shlex
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser(description='Verifier la livraison JSON et logfmt du lot de normalisation A13bis')
p.add_argument('--manifest',default='preparation13bis.json')
p.add_argument('--corpus',default='corpus13bis')
p.add_argument('--output',default='reference-normalisation13bis.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=60)
a=p.parse_args()
if Path(a.output).exists():p.error('Reference deja presente : ne pas ecraser sans controle')
if not 1<=a.timeout<=180:p.error('Timeout hors limites')
m=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
expected=[json.loads(x)['record_id'] for x in Path(a.corpus,'events.jsonl').read_text(encoding='utf-8').splitlines()]
if len(expected)!=m['per_format'] or len(set(expected))!=len(expected):p.error('Corpus local incoherent')
start=int(m['start_ns'])-5_000_000_000
deadline=time.monotonic()+a.timeout
while True:
    end=time.time_ns()
    query='{job="atelier13bis",format=~"json|logfmt"} |= '+json.dumps(m['normalization_id'])
    params=urllib.parse.urlencode({'query':query,'start':str(start),'end':str(end),'limit':'2000','direction':'forward'})
    with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query_range?'+params,timeout=30) as f:r=json.load(f)
    if r.get('status')!='success' or r.get('data',{}).get('resultType')!='streams':raise SystemExit('Reponse Loki inattendue')
    ids={'json':[],'logfmt':[]}
    for stream in r['data']['result']:
        fmt=stream['stream'].get('format')
        if fmt not in ids:raise SystemExit('Format inattendu')
        for _,line in stream.get('values',[]):
            if fmt=='json':record=json.loads(line)['record_id']
            else:record=dict(x.split('=',1) for x in shlex.split(line) if '=' in x)['record_id']
            ids[fmt].append(record)
    for fmt,values in ids.items():
        if len(values)>len(expected) or len(set(values))!=len(values):raise SystemExit('Doublons/surplus dans '+fmt)
    if all(set(values)==set(expected) for values in ids.values()):
        iso=lambda ns:datetime.fromtimestamp(ns/1e9,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        result={'normalization_id':m['normalization_id'],'from_ns':str(start),'to_ns':str(end),
                'from_utc':iso(start),'to_utc':iso(end),'json':len(ids['json']),'logfmt':len(ids['logfmt']),
                'ids_checked_per_format':True}
        Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2));break
    if time.monotonic()>=deadline:raise SystemExit('Collecte incomplete : '+str({k:len(v) for k,v in ids.items()}))
    time.sleep(2)
