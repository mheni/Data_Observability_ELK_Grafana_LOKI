import base64
import json
import os
import ssl
import statistics
import time
import urllib.request
from pathlib import Path

url = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
headers = {'Content-Type':'application/json'}
context = None
if url.startswith('https://'):
    context = ssl.create_default_context(cafile=os.environ['ES_CA'])
    auth = base64.b64encode(('elastic:' + os.environ['ELASTIC_PASSWORD']).encode()).decode()
    headers['Authorization'] = 'Basic ' + auth
elif not url.startswith('http://'):
    raise SystemExit('ES_URL doit commencer par http:// ou https://')
models = [
    ('atelier06-denorm','query-denorm.json'),
    ('atelier06-nested','query-nested.json'),
    ('atelier06-join','query-join.json'),
]

def search(index, filename):
    request = urllib.request.Request(
        url + '/' + index + '/_search', data=Path(filename).read_bytes(),
        headers=headers, method='POST')
    start = time.perf_counter()
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        result = json.load(response)
    return (time.perf_counter()-start)*1000, result['took']

reports = []
for index, filename in models:
    for _ in range(3):
        search(index, filename)
    values = [search(index, filename) for _ in range(10)]
    reports.append({
        'index':index,
        'client_median_ms':round(statistics.median(x[0] for x in values),3),
        'es_took_median_ms':statistics.median(x[1] for x in values)
    })
Path('mesures-locales.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
print(json.dumps(reports, indent=2))
