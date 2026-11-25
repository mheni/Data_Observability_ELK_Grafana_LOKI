import argparse
import base64
import getpass
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

p=argparse.ArgumentParser(description='Projection optionnelle des memes evenements A13 vers Elasticsearch')
p.add_argument('--events',required=True)
p.add_argument('--mapping',required=True)
p.add_argument('--url',default='https://localhost:9200')
p.add_argument('--ca',required=True)
p.add_argument('--index',default='atelier13-events')
p.add_argument('--username',default='elastic')
p.add_argument('--auth',choices=['basic','api-key'],default='basic')
a=p.parse_args()
if not a.url.startswith('https://'):p.error('HTTPS requis pour cette projection')
if not a.index.startswith('atelier13-'):p.error('Index de formation atelier13-* requis')
ctx=ssl.create_default_context(cafile=a.ca)
if a.auth=='basic':
    password=getpass.getpass('Mot de passe Elasticsearch (non journalise) : ')
    authorization='Basic '+base64.b64encode((a.username+':'+password).encode()).decode()
else:
    authorization='ApiKey '+getpass.getpass('Cle API Elasticsearch encodee (non journalisee) : ')
base=a.url.rstrip('/');index=urllib.parse.quote(a.index,safe='')
def request(method,path,data=None,content_type='application/json'):
    req=urllib.request.Request(base+path,data=data,method=method,
                               headers={'Authorization':authorization,'Content-Type':content_type})
    try:
        with urllib.request.urlopen(req,context=ctx,timeout=30) as response:
            raw=response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code==404 and method=='HEAD':return None
        raise SystemExit(f'HTTP {exc.code} : '+exc.read().decode(errors='replace')[:3000])
if request('HEAD','/'+index) is None:
    request('PUT','/'+index,Path(a.mapping).read_bytes())
else:
    existing=request('GET','/'+index+'/_mapping')
    fields=existing[a.index]['mappings'].get('properties',{})
    expected=json.loads(Path(a.mapping).read_text())['mappings']['properties']
    mismatches=[key for key,value in expected.items() if fields.get(key,{}).get('type')!=value['type']]
    if mismatches:raise SystemExit('Mapping existant incompatible : '+str(mismatches))
events=[json.loads(line) for line in Path(a.events).read_text(encoding='utf-8').splitlines() if line.strip()]
ids=[event['event_id'] for event in events]
if len(set(ids))!=len(ids):raise SystemExit('IDs dupliques dans la projection source')
lines=[]
for event in events:
    lines.extend([json.dumps({'index':{'_index':a.index,'_id':event['event_id']}}),json.dumps(event,ensure_ascii=False)])
result=request('POST','/_bulk?refresh=wait_for',('\n'.join(lines)+'\n').encode(), 'application/x-ndjson')
if result.get('errors'):
    failed=[item for item in result.get('items',[]) if item['index'].get('error')]
    raise SystemExit('Erreurs bulk : '+json.dumps(failed,ensure_ascii=False)[:5000])
print(json.dumps({'index':a.index,'documents_acknowledged':len(result.get('items',[])),
                  'id_policy':'event_id ; reindexer ces memes IDs ne duplique pas les documents'},indent=2))
