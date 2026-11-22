import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Verifier le lot A13 dans Loki et figer le dashboard')
p.add_argument('--manifest',default='preparation13.json')
p.add_argument('--output',default='reference13.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=60)
a=p.parse_args()
if Path(a.output).exists():p.error('Reference deja presente')
if not 1<=a.timeout<=180:p.error('Timeout hors limites')
m=json.loads(Path(a.manifest).read_text(encoding='utf-8'));deadline=time.monotonic()+a.timeout
while True:
    end=time.time_ns()
    params=urllib.parse.urlencode({'query':'{job=~"atelier09|atelier11"} |= '+json.dumps(m['run_id']),
                                  'start':str(int(m['start_ns'])-5_000_000_000),'end':str(end),'limit':'2000','direction':'forward'})
    with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query_range?'+params,timeout=30) as response:r=json.load(response)
    if r.get('status')!='success' or r.get('data',{}).get('resultType')!='streams':raise SystemExit('Reponse Loki inattendue')
    counts=Counter();events=[];timestamps=[]
    for stream in r['data']['result']:
        labels=stream['stream']
        for value in stream.get('values',[]):
            timestamps.append(int(value[0]));line=value[1]
            if labels.get('job')=='atelier09' and labels.get('dataset') in ['access','movies']:counts[labels['dataset']]+=1
            elif labels.get('job')=='atelier11' and labels.get('format')=='json':counts['json']+=1;events.append(json.loads(line))
            else:raise SystemExit('Flux inattendu pour le run')
    expected=m['expected_stream_counts']
    if any(counts[k]>expected[k] for k in counts):raise SystemExit('Surplus ou doublons : '+str(counts))
    if all(counts[k]==v for k,v in expected.items()):
        ids=[e['event_id'] for e in events]
        if len(set(ids))!=len(ids) or set(ids)!=set(m['expected_event_ids']):raise SystemExit('IDs absents ou dupliques')
        if dict(Counter(e['a13_kind'] for e in events))!=m['expected_json_kinds']:raise SystemExit('Kinds incoherents')
        for batch in m['batches']:
            records=[e for e in events if e.get('batch_id')==batch['batch_id'] and e['a13_kind']=='record']
            if len(records)!=batch['attempted'] or sum(e['accepted'] for e in records)!=batch['accepted_count']:
                raise SystemExit('Contenu du batch incoherent')
        t=time.time_ns()
        def iso(ns):return datetime.fromtimestamp(ns/1_000_000_000,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        from_ns=min(int(m['start_ns'])-5_000_000_000,min(timestamps)-1_000_000_000)
        result={'run_id':m['run_id'],'from_ns':str(from_ns),'to_ns':str(t),
                'from_utc':iso(from_ns),'to_utc':iso(t),'observed':dict(counts),
                'verified_json_event_ids':True,'verified_batches':True}
        Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));break
    if time.monotonic()>=deadline:raise SystemExit('Collecte incomplete : '+str(counts))
    time.sleep(2)
