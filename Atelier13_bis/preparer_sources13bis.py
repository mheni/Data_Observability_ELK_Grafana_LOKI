import argparse
import collections
import csv
import hashlib
import json
import math
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Preparer toutes les lignes access pour Loki, sans echantillonnage')
p.add_argument('--source',default='donnees/access_log_actualise')
p.add_argument('--output-dir',default='preparation13bis')
a=p.parse_args();src=Path(a.source);base=Path(a.output_dir)
if not src.is_file():p.error('Fichier source absent : '+str(src))
if base.exists():p.error('Dossier de sortie deja present : ne pas ecraser une preparation')
os.umask(0o077);base.mkdir(parents=True)
lot=datetime.now(timezone.utc).strftime('A13B-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
start=time.time_ns();sha=hashlib.sha256(src.read_bytes()).hexdigest()
rx=re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] "(?P<request>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<size>\d+|-)')
n=bad=0;codes=collections.Counter();methods=collections.Counter();ips=collections.Counter();paths=collections.Counter();protocols=collections.Counter();sizes=[];dates=[]
with src.open(encoding='utf-8') as inp, (base/'access_log').open('w',encoding='utf-8',newline='') as rawout, (base/'events.jsonl').open('w',encoding='utf-8') as jout, (base/'events.logfmt').open('w',encoding='utf-8') as lout:
    for physical,line in enumerate(inp,1):
        raw=line.rstrip('\r\n')
        if not raw.strip():continue
        n+=1;rawout.write(raw+'\n');m=rx.match(raw)
        e={'lot':lot,'record_id':lot+'-'+str(n),'source_dataset':'access','source_line':physical,
           'raw_line':raw,'parse_ok':bool(m),'service':'web-formation','metadata':{'origin':'atelier13bis_access','version':1}}
        if not m:bad+=1;e['parse_reason']='Debut Apache non reconnu'
        else:
            status=int(m['status']);codes[status]+=1;ips[m['ip']]+=1
            e.update(client_ip=m['ip'],apache_time=m['apache_time'],request_line=m['request'],status=status)
            try:dates.append(datetime.strptime(m['apache_time'],'%d/%b/%Y:%H:%M:%S %z'))
            except ValueError:pass
            if m['size']!='-':e['bytes']=int(m['size']);sizes.append(e['bytes'])
            req=m['request'].split(' ',2)
            if len(req)==3 and req[2].startswith('HTTP/'):
                e.update(method=req[0],path=req[1],protocol=req[2]);methods[req[0]]+=1;paths[req[1]]+=1;protocols[req[2]]+=1
            else:methods['(absente)']+=1;protocols['(absent)']+=1
        jout.write(json.dumps(e,ensure_ascii=False,separators=(',',':'))+'\n')
        pairs=[]
        for k,v in e.items():
            if isinstance(v,(dict,list)) or v is None:continue
            value=('true' if v else 'false') if isinstance(v,bool) else (str(v) if isinstance(v,(int,float)) else json.dumps(v,ensure_ascii=False))
            pairs.append(k+'='+value)
        lout.write(' '.join(pairs)+'\n')
if not n:raise SystemExit('Fichier sans ligne non vide : aucune preparation reussie')
sizes.sort()
def quant(q):
    if not sizes:return None
    z=(len(sizes)-1)*q;lo=math.floor(z);hi=math.ceil(z)
    return sizes[lo]+(sizes[hi]-sizes[lo])*(z-lo)
ranges=[('1-999',1,1000),('1000-9999',1000,10000),('10000-99999',10000,100000),('100000-999999',100000,1000000),('>=1000000',1000000,None)]
ref={'source_file':src.name,'source_sha256':sha,'nonempty_lines':n,'apache_prefix_ok':n-bad,'apache_prefix_failures':bad,
     'status_counts':dict(sorted(codes.items())),'class_counts':{str(k)+'xx':sum(v for code,v in codes.items() if k*100<=code<(k+1)*100) for k in range(1,6)},
     'method_counts':dict(methods),'protocol_counts':dict(protocols),'known_bytes':len(sizes),'missing_bytes':n-len(sizes),
     'bytes_sum':sum(sizes),'bytes_mean':sum(sizes)/len(sizes) if sizes else None,'bytes_max':max(sizes) if sizes else None,'bytes_p95_linear':quant(.95),
     'unique_ips':len(ips),'unique_paths':len(paths),'top_ips':ips.most_common(10),'top_paths':paths.most_common(10),
     'source_date_min':min(dates).isoformat() if dates else None,'source_date_max':max(dates).isoformat() if dates else None,
     'size_bins':[{'label':label,'from':lo,'to_exclusive':hi,'count':sum(v>=lo and (hi is None or v<hi) for v in sizes)} for label,lo,hi in ranges]}
manifest={'lot':lot,'prepared_start_ns':str(start),'prepared_end_ns':str(time.time_ns()),'source_sha256':sha,'expected_per_format':n,
          'formats':['raw','json','logfmt'],'files':{'raw':'access_log','json':'events.jsonl','logfmt':'events.logfmt'},
          'reference_file':'reference_source.json','time_basis':'collection','state':'prepared; delivery not yet checked'}
(base/'reference_source.json').write_text(json.dumps(ref,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output_dir':str(base),'lot':lot,'expected_per_format':n,'source_sha256':sha},ensure_ascii=False,indent=2))
