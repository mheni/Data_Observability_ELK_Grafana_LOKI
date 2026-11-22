import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Lot A12 dans les quatre fichiers deja suivis en A09/A11')
p.add_argument('--raw-dir',default='/var/log/formation-alloy09')
p.add_argument('--structured-dir',default='/var/log/formation-alloy11')
p.add_argument('--report',default='scenario12.json')
a=p.parse_args()
report=Path(a.report)
if report.exists():
    p.error('Rapport existant : choisir un nouveau --report')
raw,structured=Path(a.raw_dir),Path(a.structured_dir)
paths=[raw/'access_log',raw/'movies.csv',structured/'events.jsonl',structured/'events.logfmt']
for path in paths:
    if not path.is_file():
        p.error('Source A09/A11 absente : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        if f.tell():
            f.seek(-1,2)
            if f.read(1)!=b'\n':
                p.error('Saut de ligne final absent : '+str(path))
start_ns=time.time_ns()-5_000_000_000
now=datetime.now(timezone.utc)
marker=now.strftime('A12-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
with paths[0].open('a',encoding='utf-8') as f:
    for i,(status,size,msg) in enumerate([(200,100,'completed'),(404,200,'missing'),(503,300,'timeout'),(200,400,'recovered')],1):
        f.write(f'127.0.0.1 - - [{stamp}] "GET /atelier12/{marker}/probe-{i} HTTP/1.1" {status} {size} "-" "A12 {msg}"\n')
with paths[1].open('a',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n')
    writer.writerow([9001201,f'Film {marker}, edition "test" (2026)','Documentary'])
    writer.writerow([9001202,f'Voyage {marker} (2026)','Adventure'])
controls=[]
for group,values in [('access-demo',[100,200,300,1200,5000]),('movies-demo',[400,500,600,800])]:
    for i,value in enumerate(values,1):
        controls.append({'control_group':group,'test_case':f'{group}-{i}',
                         'control_kind':'valid','duration_ms':value})
controls.extend([
    {'control_group':'access-demo','test_case':'D_BAD','control_kind':'invalid','duration_ms':'unknown'},
    {'control_group':'access-demo','test_case':'D_MISSING','control_kind':'invalid'},
    {'control_group':'movies-demo','test_case':'D_NEGATIVE','control_kind':'invalid','duration_ms':-5}
])
with paths[2].open('a',encoding='utf-8') as jf,paths[3].open('a',encoding='utf-8') as lf:
    for number,fields in enumerate(controls,1):
        event={'normalization_id':marker,'record_id':f'{marker}-D{number:03d}',
               'source_dataset':'controls_metrics','synthetic':True,**fields}
        jf.write(json.dumps(event,ensure_ascii=False)+'\n')
        lf.write(' '.join(k+'='+json.dumps(v,ensure_ascii=False) for k,v in event.items())+'\n')
result={'marker':marker,'start_ns':str(start_ns),'written_at_utc':now.isoformat(),
        'expected':{'access':4,'movies':2,'json':12,'logfmt':12},
        'valid_duration_samples':9,'invalid_duration_controls':3,
        'response_bytes':{'sum':1000,'mean':250,'max':400},
        'note':'30 entrees synthetiques ecrites ; collecte a verifier ; aucune latence HTTP reelle'}
with report.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
