import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Recherche de lignes LogQL via API Loki query_range')
g=p.add_mutually_exclusive_group(required=True)
g.add_argument('--query')
g.add_argument('--query-file')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--window',help='Fichier fenetre10.json ; sinon les 15 dernieres minutes')
p.add_argument('--limit',type=int,default=100)
p.add_argument('--direction',choices=['forward','backward'],default='forward')
p.add_argument('--output',default='reponse-loki.json')
a=p.parse_args()
if a.limit < 1:
    p.error('--limit doit etre positif et rester compatible avec les limites serveur')
url=a.url.rstrip('/')
if urllib.parse.urlsplit(url).scheme not in ['http','https']:
    p.error('--url doit etre une URL HTTP ou HTTPS')
query=Path(a.query_file).read_text(encoding='utf-8').strip() if a.query_file else a.query
if not query.strip():
    p.error('Requete vide')
if Path(a.output).exists():
    p.error('Sortie deja presente : choisir un nouveau --output')
if a.window:
    window=json.loads(Path(a.window).read_text(encoding='utf-8'))
    start,end=int(window['start_ns']),int(window['end_ns'])
else:
    end=time.time_ns()
    start=end-15*60*1_000_000_000
if start>=end:
    p.error('Periode invalide')
params={'query':query,'start':str(start),'end':str(end),'limit':str(a.limit),'direction':a.direction}
request=urllib.request.Request(url+'/loki/api/v1/query_range?'+urllib.parse.urlencode(params))
try:
    with urllib.request.urlopen(request,timeout=30) as response:
        result=json.load(response)
except urllib.error.HTTPError as exc:
    raise SystemExit(f'HTTP {exc.code} : '+exc.read().decode('utf-8',errors='replace')[:3000])
except urllib.error.URLError as exc:
    raise SystemExit('Connexion Loki impossible : '+str(exc.reason))
if result.get('status')!='success' or result.get('data',{}).get('resultType')!='streams':
    raise SystemExit('Reponse de recherche de lignes inattendue : '+str(result)[:3000])
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=[]
for stream in result['data']['result']:
    for value in stream.get('values',[]):
        ns,text=value[0],value[1]
        seconds,nanos=divmod(int(ns),1_000_000_000)
        stamp=datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z'
        lines.append((int(ns),stamp,stream['stream'],text))
for _,stamp,labels,text in sorted(lines,key=lambda item:item[0],reverse=a.direction=='backward'):
    print(stamp,json.dumps(labels,ensure_ascii=False),text)
print(json.dumps({'streams_received':len(result['data']['result']),
                  'lines_received':len(lines),'request_limit':a.limit,
                  'complete_count_guaranteed':False,'raw_response':a.output},indent=2))
