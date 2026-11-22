import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Six sondes dans les deux fichiers conserves depuis A09')
p.add_argument('--directory', default='/var/log/formation-alloy09')
p.add_argument('--report', default='scenario10.json')
a = p.parse_args()
base = Path(a.directory)
report_path = Path(a.report)
if report_path.exists():
    p.error('Rapport deja present : choisir un nouveau --report')
paths = [base/'access_log',base/'movies.csv']
for path in paths:
    if not path.is_file():
        p.error('Fichier A09 absent : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        if f.tell():
            f.seek(-1,2)
            if f.read(1) != b'\n':
                p.error('Saut de ligne final absent : '+str(path))
start_ns=time.time_ns()-5_000_000_000
now=datetime.now(timezone.utc)
marker=now.strftime('A10-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
rows=[(200,'completed'),(404,'missing resource'),(503,'timeout upstream'),(200,'recovered after timeout')]
with paths[0].open('a',encoding='utf-8') as f:
    for number,(status,message) in enumerate(rows,1):
        f.write(f'127.0.0.1 - - [{stamp}] "GET /atelier10/{marker}/probe-{number} HTTP/1.1" {status} 128 "-" "A10 {message}"\n')
with paths[1].open('a',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n')
    writer.writerow([9001001,f'Catalogue {marker}, edition "test" (2026)','Documentary'])
    writer.writerow([9001002,f'Voyage {marker} sans erreur (2026)','Adventure|Sci-Fi'])
report={'marker':marker,'start_ns':str(start_ns),'written_at_utc':now.isoformat(),
        'access_entries':4,'movies_entries':2,'expected_loki_entries':6,
        'note':'Sondes synthetiques A10 ; meme collecte A09 ; ne prouve pas une livraison Loki'}
with report_path.open('x',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
