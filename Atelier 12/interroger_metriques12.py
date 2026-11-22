import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

p=argparse.ArgumentParser(description='Interroger une metrique Loki en Instant ou Range')
p.add_argument('--query-file',required=True)
p.add_argument('--reference',default='reference12.json')
p.add_argument('--mode',choices=['instant','range'],default='instant')
p.add_argument('--step',default='30s')
p.add_argument('--history-minutes',type=int,default=10)
p.add_argument('--output',default='metric-response.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
a=p.parse_args()
if a.history_minutes<1:p.error('--history-minutes doit etre positif')
if Path(a.output).exists():p.error('Fichier de sortie deja present')
reference=json.loads(Path(a.reference).read_text(encoding='utf-8'))
t=int(reference['time_ns'])
query=Path(a.query_file).read_text(encoding='utf-8').strip()
params={'query':query}
if a.mode=='instant':
    endpoint='/loki/api/v1/query';params['time']=str(t);expected='vector'
else:
    endpoint='/loki/api/v1/query_range'
    params.update(start=str(t-a.history_minutes*60*1_000_000_000),end=str(t),step=a.step)
    expected='matrix'
with urllib.request.urlopen(a.url.rstrip('/')+endpoint+'?'+urllib.parse.urlencode(params),timeout=30) as response:
    result=json.load(response)
if result.get('status')!='success' or result.get('data',{}).get('resultType')!=expected:
    raise SystemExit('Reponse metrique inattendue : '+str(result)[:3000])
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for item in result['data']['result']:
    print(item['metric'],item.get('value',item.get('values')))
print(json.dumps({'mode':a.mode,'resultType':expected,'series_received':len(result['data']['result'])},indent=2))
