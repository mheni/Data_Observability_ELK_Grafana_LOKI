import argparse
import base64
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

p = argparse.ArgumentParser(description='Export du laboratoire avec PIT et search_after')
p.add_argument('--scenario', help='JSON de recherche ; seuls query, sort et _source sont repris')
p.add_argument('--page-size', type=int, default=3)
p.add_argument('--output', default='export-events.ndjson')
a = p.parse_args()
if a.page_size < 1:
    p.error('--page-size doit etre positif')
output = Path(a.output)
partial = output.with_name(output.name + '.partial')
report_path = output.with_name(output.name + '.rapport.json')
if any(path.exists() for path in (output, partial, report_path)):
    p.error('Une sortie existe deja : choisir un nouveau --output')
scenario = json.loads(Path(a.scenario).read_text(encoding='utf-8')) if a.scenario else {}
query = scenario.get('query', {'term':{'environment':'formation'}})
sort = list(scenario.get('sort', [{'@timestamp':'asc'},{'event_id':'asc'}]))
if not any(x == '_shard_doc' or isinstance(x, dict) and '_shard_doc' in x for x in sort):
    sort.append({'_shard_doc':'asc'})
url = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
headers = {'Content-Type':'application/json'}
context = None
if url.startswith('https://'):
    context = ssl.create_default_context(cafile=os.environ['ES_CA'])
    auth = base64.b64encode(('elastic:' + os.environ['ELASTIC_PASSWORD']).encode()).decode()
    headers['Authorization'] = 'Basic ' + auth
elif not url.startswith('http://'):
    p.error('ES_URL doit commencer par http:// ou https://')

def call(method, path, body=None):
    request = urllib.request.Request(
        url+path, data=None if body is None else json.dumps(body).encode(),
        method=method, headers=headers)
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        return json.load(response)

pit_id = None
seen = set()
count = pages = 0
expected = None
pit_closed = False
try:
    opened = call('POST','/atelier07-events/_pit?keep_alive=5m&allow_partial_search_results=false')
    pit_id = opened['id']
    if opened.get('_shards',{}).get('failed',0):
        raise RuntimeError('Ouverture PIT incomplete')
    cursor = None
    with partial.open('x',encoding='utf-8') as f:
        while True:
            body = {
                'size':a.page_size,'track_total_hits':True,
                'pit':{'id':pit_id,'keep_alive':'5m'},
                'sort':sort,'query':query
            }
            if '_source' in scenario:
                body['_source'] = scenario['_source']
            if cursor is not None:
                body['search_after'] = cursor
            response = call('POST','/_search?allow_partial_search_results=false',body)
            pit_id = response.get('pit_id',pit_id)
            if response.get('timed_out') or response.get('_shards',{}).get('failed',0):
                raise RuntimeError('Recherche partielle : ne pas avancer le curseur')
            total = response['hits']['total']
            if total['relation'] != 'eq':
                raise RuntimeError('Le total doit etre exact pour ce controle')
            if expected is None:
                expected = total['value']
            elif total['value'] != expected:
                raise RuntimeError('Total changeant dans le meme PIT')
            hits = response['hits']['hits']
            if not hits:
                break
            pages += 1
            for hit in hits:
                key = (hit['_index'],hit['_id'])
                if key in seen:
                    raise RuntimeError('Doublon : '+str(key))
                seen.add(key)
                f.write(json.dumps({'_id':hit['_id'],'_source':hit['_source']},ensure_ascii=False)+'\n')
                count += 1
            new_cursor = hits[-1]['sort']
            if new_cursor == cursor:
                raise RuntimeError('Le curseur n avance plus')
            cursor = new_cursor
    if count != expected:
        raise RuntimeError(f'Export incomplet : {count} / {expected}')
    partial.replace(output)
finally:
    if pit_id is not None:
        try:
            closed = call('DELETE','/_pit',{'id':pit_id})
            pit_closed = bool(closed.get('succeeded'))
            if not pit_closed:
                print('Attention : fermeture PIT non confirmee',file=sys.stderr)
        except Exception as exc:
            print('Attention : fermeture PIT non confirmee : '+type(exc).__name__,file=sys.stderr)
report = {'export':str(output),'documents':count,'expected':expected,
          'non_empty_pages':pages,'pit_closed':pit_closed}
report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
