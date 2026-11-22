import argparse
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Ajoute des sondes synthetiques aux deux fichiers de lab')
p.add_argument('--directory', default='/var/log/formation-alloy09')
p.add_argument('--kind', choices=['access','movies','both'], default='both')
a = p.parse_args()
base = Path(a.directory)
paths = [base/'access_log'] if a.kind == 'access' else [base/'movies.csv'] if a.kind == 'movies' else [base/'access_log',base/'movies.csv']
for path in paths:
    if not path.is_file():
        p.error('Fichier de lab absent : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        size=f.tell()
        if size:
            f.seek(-1,2)
            if f.read(1)!=b'\n':
                p.error('Fichier sans saut de ligne final : '+str(path))
now=datetime.now(timezone.utc)
marker=now.strftime('A09-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
if a.kind in ['access','both']:
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
    line=f'127.0.0.1 - - [{stamp}] "GET /atelier09/probe/{marker} HTTP/1.1" 503 128 "-" "Alloy-formation-probe"'
    with (base/'access_log').open('a',encoding='utf-8') as f:
        f.write(line+'\n')
if a.kind in ['movies','both']:
    title=f'Alloy probe {marker}, edition "test" (2026)'
    with (base/'movies.csv').open('a',encoding='utf-8',newline='') as f:
        csv.writer(f,lineterminator='\n').writerow([9000901,title,'Documentary|Sci-Fi'])
print(json.dumps({'marker':marker,'kind':a.kind,'synthetic':True,
                  'movie_id_note':'ID de test repete volontairement ; Loki conserve les lignes, sans upsert'},ensure_ascii=False,indent=2))
