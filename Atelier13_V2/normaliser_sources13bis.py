import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Vues JSON/logfmt des deux fichiers de A09, sans les modifier')
p.add_argument('--access',required=True)
p.add_argument('--movies',required=True)
p.add_argument('--output-dir',default='corpus13bis')
p.add_argument('--with-controls',action='store_true')
a=p.parse_args()
base=Path(a.output_dir)
if base.exists():
    p.error('Dossier de sortie deja present : choisir un nouveau nom')
access_path=Path(a.access)
movies_path=Path(a.movies)
if not access_path.is_file() or not movies_path.is_file():
    p.error('Source absente')
os.umask(0o077)
base.mkdir(parents=True)
start_ns=time.time_ns()-5_000_000_000
normalization_id=datetime.now(timezone.utc).strftime('N13B-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
counts={'access':0,'movies':0,'controls':0,'access_parse_failures':0}
pattern=re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] "(?P<request>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<size>\d+|-)')

def emit(source_dataset,source_line,fields,raw_line=None):
    event={'normalization_id':normalization_id,
           'record_id':f'{normalization_id}-{source_dataset}-{source_line}',
           'source_dataset':source_dataset,'source_line':source_line,
           'metadata':{'origin':'atelier13bis_normalisation','version':1},**fields}
    if raw_line is not None:
        event['raw_line']=raw_line
    json_out.write(json.dumps(event,ensure_ascii=False)+'\n')
    pairs=[]
    for key,value in event.items():
        if isinstance(value,(list,dict)) or value is None:
            continue
        if isinstance(value,bool):
            encoded='true' if value else 'false'
        elif isinstance(value,(int,float)):
            encoded=str(value)
        else:
            encoded=json.dumps(str(value),ensure_ascii=False)
        pairs.append(key+'='+encoded)
    logfmt_out.write(' '.join(pairs)+'\n')

with (base/'events.jsonl').open('x',encoding='utf-8') as json_out, \
     (base/'events.logfmt').open('x',encoding='utf-8') as logfmt_out:
    with access_path.open(encoding='utf-8') as src:
        for number,line in enumerate(src,1):
            raw=line.rstrip('\r\n')
            if not raw.strip():
                continue
            match=pattern.match(raw)
            fields={'service':'web-formation','parse_ok':bool(match)}
            if match:
                fields.update(client_ip=match['ip'],apache_time=match['apache_time'],
                              request_line=match['request'],status=int(match['status']))
                if match['size']!='-':
                    fields['bytes']=int(match['size'])
                request=match['request'].split(' ',2)
                if len(request)==3 and request[2].startswith('HTTP/'):
                    fields.update(method=request[0],path=request[1],protocol=request[2])
            else:
                fields['parse_reason']='Debut Apache non reconnu'
                counts['access_parse_failures']+=1
            emit('access',number,fields,raw)
            counts['access']+=1
    with movies_path.open(encoding='utf-8-sig',newline='') as src:
        reader=csv.DictReader(src)
        if reader.fieldnames!=['movieId','title','genres']:
            raise ValueError('Entete movies.csv inattendu')
        for number,row in enumerate(reader,1):
            if None in row or any(row.get(k) is None for k in reader.fieldnames):
                raise ValueError('CSV incomplet ou colonnes en trop')
            title=row['title']
            genres=[] if row['genres']=='(no genres listed)' else row['genres'].split('|')
            fields={'service':'movielens-import','parse_ok':True,
                    'movie_id':int(row['movieId']),'title':title,
                    'genres':genres,'genres_text':row['genres']}
            year=re.fullmatch(r'.* \((\d{4})\)',title)
            if year:
                fields['year']=int(year[1])
            emit('movies',number,fields)
            counts['movies']+=1
    if a.with_controls:
        controls=[
            {'test_case':'C_VALID','level':'WARN','duration_ms':1800,'elapsed':'1.8s','payload':'2MB','message':'Synthetic duration control'},
            {'test_case':'C_BAD','level':'ERROR','duration_ms':'unknown','elapsed':'unknown','payload':'unknown','message':'Synthetic invalid numeric value'},
            {'test_case':'C_MISSING','level':'INFO','message':'INFO mentions ERROR only as text'},
            {'test_case':'C_NEGATIVE','level':'ERROR','duration_ms':-5,'elapsed':'-5ms','payload':'1KB','message':'Synthetic negative duration'}
        ]
        for number,fields in enumerate(controls,1):
            emit('controls',number,{'service':'synthetic-controls','synthetic':True,**fields})
            counts['controls']+=1
report={'normalization_id':normalization_id,'start_ns':str(start_ns),**counts,
        'per_format':counts['access']+counts['movies']+counts['controls'],
        'expected_total_both_formats':2*(counts['access']+counts['movies']+counts['controls']),
        'sources_unchanged':True,'state':'Preparation only; no Loki delivery confirmed'}
(base/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
