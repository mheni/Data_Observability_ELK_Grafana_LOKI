import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Figer une periode commune pour API et Grafana')
p.add_argument('--scenario',default='scenario10.json')
p.add_argument('--output',default='fenetre10.json')
a=p.parse_args()
source=json.loads(Path(a.scenario).read_text(encoding='utf-8'))
start=int(source['start_ns'])
end=time.time_ns()
if start >= end:
    p.error('Debut incoherent avec l horloge actuelle')
def rfc3339(ns):
    seconds,nanos=divmod(ns,1_000_000_000)
    return datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z'
result={'marker':source['marker'],'start_ns':str(start),'end_ns':str(end),
        'from_utc':rfc3339(start),'to_utc':rfc3339(end)}
Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
