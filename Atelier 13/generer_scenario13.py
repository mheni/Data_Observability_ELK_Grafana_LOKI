import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime,timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Incident data A13 : references A09, instrumentation A11')
p.add_argument('--raw-dir',default='/var/log/formation-alloy09')
p.add_argument('--events',default='/var/log/formation-alloy11/events.jsonl')
p.add_argument('--output-dir',default='scenario13')
p.add_argument('--phase-wait',type=float,default=15)
p.add_argument('--pace',type=float,default=0.05)
a=p.parse_args()
if a.phase_wait<0 or a.pace<0:p.error('Delais negatifs interdits')
base=Path(a.output_dir);raw=Path(a.raw_dir);events_path=Path(a.events)
if base.exists():p.error('Dossier de sortie existant')
for path in [raw/'access_log',raw/'movies.csv',events_path]:
    if not path.is_file():p.error('Source A09/A11 absente : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        if f.tell():
            f.seek(-1,2)
            if f.read(1)!=b'\n':p.error('Saut de ligne final absent : '+str(path))
with (raw/'access_log').open(encoding='utf-8') as f:
    access=[]
    for line in f:
        if line.strip():access.append(line.rstrip('\r\n'))
        if len(access)==5:break
with (raw/'movies.csv').open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    if reader.fieldnames!=['movieId','title','genres']:p.error('Entete CSV inattendu')
    movies=[]
    for row in reader:
        if None in row or any(row.get(k) is None for k in reader.fieldnames):p.error('CSV incomplet')
        if any('\n' in v or '\r' in v for v in row.values()):p.error('CSV multiligne incompatible avec le suivi brut A09')
        movies.append(row)
        if len(movies)==5:break
if len(access)!=5 or len(movies)!=5:p.error('Au moins cinq references de chaque source sont requises')
if len({r['movieId'] for r in movies})!=5:p.error('Les cinq references MovieLens doivent avoir des IDs distincts')
os.umask(0o077);base.mkdir(parents=True)
run=datetime.now(timezone.utc).strftime('A13-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
start_ns=time.time_ns();batches=[];all_events=[]
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
def iso(epoch):return datetime.fromtimestamp(epoch,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def emit(event):
    line=json.dumps(event,ensure_ascii=False)+'\n'
    with events_path.open('a',encoding='utf-8') as f:f.write(line)
    with (base/'produced_events.jsonl').open('a',encoding='utf-8') as f:f.write(line)
    all_events.append(event)
for phase_index,phase in enumerate(['normal','incident','recovery']):
    for dataset in ['access','movies']:
        tick=time.perf_counter();batch_id=f'{run}-{phase}-{dataset}'
        attempted=4 if dataset=='movies' and phase=='incident' else 5
        accepted_count=0;max_delay=0;source_times=[]
        for i in range(attempted):
            now=time.time();delay=600 if dataset=='movies' and phase=='incident' else 2
            event_id=f'{batch_id}-R{i+1:03d}'
            event={'@timestamp':iso(now),'producer_epoch':now,'event_time':iso(now-delay),
                   'source_event_epoch':now-delay,'source_delay_seconds':delay,
                   'run_id':run,'event_id':event_id,'batch_id':batch_id,'phase':phase,
                   'source_dataset':dataset,'a13_kind':'record','synthetic':True}
            if dataset=='access':
                status=[200,200,503,503,404][i] if phase=='incident' else 200
                size=[128,512,1500,4096,8192][i]
                reference=access[i]
                event.update(accepted=True,quality_reason='ok',http_status=status,response_bytes=size,
                             source_reference=f'access_log:reference:{i+1}',source_sha256=hashlib.sha256(reference.encode()).hexdigest())
                n=datetime.now(timezone.utc)
                stamp=f'{n.day:02d}/{months[n.month-1]}/{n.year:04d}:'+n.strftime('%H:%M:%S')+' +0000'
                line=f'127.0.0.1 - - [{stamp}] "GET /atelier13/{event_id} HTTP/1.1" {status} {size} "-" "A13-synthetic-probe"\n'
                with (raw/'access_log').open('a',encoding='utf-8') as f:f.write(line)
            else:
                original=movies[i];movie_id=original['movieId'];title=original['title'];reason='ok'
                if phase=='incident' and i==2:title='';reason='title_missing'
                if phase=='incident' and i==3:movie_id=movies[0]['movieId'];reason='duplicate_movie_id'
                event.update(accepted=reason=='ok',quality_reason=reason,movie_id=movie_id,title=title,
                             genres_text=original['genres'],source_reference=f'movies.csv:reference:{i+1}',
                             source_sha256=hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest())
                with (raw/'movies.csv').open('a',encoding='utf-8',newline='') as f:
                    csv.writer(f,lineterminator='\n').writerow([movie_id,title+f' [probe:{event_id}]',original['genres']])
            emit(event);accepted_count+=int(event['accepted']);max_delay=max(max_delay,delay);source_times.append(now-delay)
            time.sleep(a.pace * (4 if dataset=='movies' and phase=='incident' else 1))
        now=time.time()
        summary={'@timestamp':iso(now),'producer_epoch':now,'event_time':iso(max(source_times)),
                 'source_event_epoch':max(source_times),'source_delay_seconds':max_delay,
                 'event_id':batch_id+'-summary','batch_id':batch_id,'run_id':run,'phase':phase,
                 'source_dataset':dataset,'a13_kind':'batch','synthetic':True,'expected':5,
                 'attempted':attempted,'accepted_count':accepted_count,'rejected_count':attempted-accepted_count,
                 'missing_count':5-attempted,'processing_duration_ms':round((time.perf_counter()-tick)*1000,3)}
        emit(summary);batches.append(summary)
    now=time.time()
    emit({'@timestamp':iso(now),'producer_epoch':now,'event_time':iso(now),
          'event_id':f'{run}-{phase}-heartbeat','run_id':run,'phase':phase,
          'source_dataset':'control','a13_kind':'heartbeat','synthetic':True})
    if phase_index<2:time.sleep(a.phase_wait)
end_ns=time.time_ns()
manifest={'run_id':run,'start_ns':str(start_ns),'end_ns':str(end_ns),
          'expected_stream_counts':{'access':15,'movies':14,'json':38},
          'expected_json_kinds':{'record':29,'batch':6,'heartbeat':3},
          'expected_event_ids':[e['event_id'] for e in all_events],
          'totals':{'expected':30,'attempted':29,'accepted':27,'rejected':2,'missing':1,
                    'http_requests':15,'http_5xx':2,'http_4xx':1,'max_source_delay_seconds':600},
          'batches':batches,'note':'Simulation instrumentee ; references initiales non remplacees ; sondes ajoutees'}
(base/'manifest13.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
