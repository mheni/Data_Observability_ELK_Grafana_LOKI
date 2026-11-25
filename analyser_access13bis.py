import argparse
import collections
import datetime
import hashlib
import json
import math
import re
from pathlib import Path
p=argparse.ArgumentParser(description='Reference locale du fichier access complet ; aucune publication dans Loki')
p.add_argument('--source',default='sources13bis/access_log')
p.add_argument('--output',default='reference_access_locale.json')
a=p.parse_args()
path=Path(a.source)
if Path(a.output).exists():p.error('Sortie existante : choisir un nouveau nom')
rx=re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<date>[^\]]+)\] "(?P<request>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<size>\d+|-)')
codes=collections.Counter();methods=collections.Counter();ips=collections.Counter();paths=collections.Counter();sizes=[];dates=[];n=bad=0
with path.open(encoding='utf-8') as f:
    for line in f:
        if not line.strip():continue
        n+=1;m=rx.match(line)
        if not m:bad+=1;continue
        codes[int(m['status'])]+=1;ips[m['ip']]+=1
        r=m['request'].split(' ',2)
        if len(r)==3 and r[2].startswith('HTTP/'):
            methods[r[0]]+=1;paths[r[1]]+=1
        else:methods['(absente)']+=1
        if m['size']!='-':sizes.append(int(m['size']))
        dates.append(datetime.datetime.strptime(m['date'],'%d/%b/%Y:%H:%M:%S %z'))
sizes.sort()
def quant(q):
    if not sizes:return None
    z=(len(sizes)-1)*q;lo=math.floor(z);hi=math.ceil(z)
    return sizes[lo]+(sizes[hi]-sizes[lo])*(z-lo)
result={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'nonempty_lines':n,'apache_prefix_ok':n-bad,'apache_prefix_failures':bad,
        'status_counts':dict(sorted(codes.items())),'class_counts':dict(collections.Counter({str(k)+'xx':sum(v for code,v in codes.items() if k*100<=code<(k+1)*100) for k in range(1,6)})),
        'method_counts':dict(methods),'unique_ips':len(ips),'unique_paths_with_query_string':len(paths),
        'known_bytes':len(sizes),'missing_bytes':n-bad-len(sizes),'bytes_sum':sum(sizes),'bytes_mean':sum(sizes)/len(sizes) if sizes else None,
        'bytes_min':min(sizes) if sizes else None,'bytes_max':max(sizes) if sizes else None,'bytes_p95_linear':quant(.95),
        'top_ips':ips.most_common(10),'top_paths':paths.most_common(10),
        'source_date_min':min(dates).isoformat() if dates else None,'source_date_max':max(dates).isoformat() if dates else None}
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
