import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Apache access_log vers NDJSON Bulk')
p.add_argument('source', nargs='?', default='access_log')
p.add_argument('destination', nargs='?', default='access.ndjson')
p.add_argument('--limit', type=int, default=1000)
a = p.parse_args()
if a.limit < 1:
    p.error('--limit doit etre positif')
paths = [Path(a.source), Path(a.destination), Path('access-rejets.ndjson'), Path('access-preparation.json')]
if len({x.resolve() for x in paths}) != len(paths):
    p.error('Les fichiers source, destination et rapports doivent etre distincts')
pattern = re.compile(
    r'^(?P<client_ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] '
    r'"(?P<request_line>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'"(?P<referrer>(?:\\.|[^"\\])*)" "(?P<user_agent>(?:\\.|[^"\\])*)"\s*$'
)
months = {name:i for i, name in enumerate(
    ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'), 1)}

def parse_apache_date(value):
    day, month, rest = value.split('/', 2)
    numeric = f'{day}/{months[month]:02d}/{rest}'
    return datetime.strptime(numeric, '%d/%m/%Y:%H:%M:%S %z').astimezone(timezone.utc).isoformat().replace('+00:00','Z')

fingerprint = hashlib.sha256()
with open(a.source, 'rb') as f:
    for chunk in iter(lambda: f.read(1024*1024), b''):
        fingerprint.update(chunk)
source_hash = fingerprint.hexdigest()
read = accepted = rejected = 0
with open(a.source, encoding='utf-8', errors='strict') as src, \
     open(a.destination, 'w', encoding='utf-8') as dst, \
     open('access-rejets.ndjson', 'w', encoding='utf-8') as rejects:
    for line_number, line in enumerate(src, 1):
        if line_number > a.limit:
            break
        read += 1
        message = line.rstrip('\r\n')
        try:
            match = pattern.fullmatch(message)
            if not match:
                raise ValueError('Format Apache Combined non reconnu')
            values = match.groupdict()
            event_id = f'{source_hash}-{line_number}'
            doc = {
                '@timestamp':parse_apache_date(values['apache_time']),
                'event_id':event_id,'source_file_sha256':source_hash,
                'line_number':line_number,'client_ip':values['client_ip'],
                'request_line':values['request_line'],'status':int(values['status']),
                'referrer':values['referrer'],'user_agent':values['user_agent'],
                'message':message,'service':'web-formation'
            }
            if values['bytes'] != '-':
                doc['bytes'] = int(values['bytes'])
            request = values['request_line'].split(' ', 2)
            if len(request) == 3 and request[2].startswith('HTTP/'):
                doc.update(method=request[0], path=request[1], protocol=request[2])
        except (ValueError, KeyError) as exc:
            rejected += 1
            rejects.write(json.dumps({'line':line_number,'message':message,'error':str(exc)}, ensure_ascii=False) + '\n')
            continue
        dst.write(json.dumps({'index':{'_id':event_id}}) + '\n')
        dst.write(json.dumps(doc, ensure_ascii=False) + '\n')
        accepted += 1
report = {'lines_read':read,'documents':accepted,'rejected':rejected,
          'ndjson_lines':2*accepted,'source_file_sha256':source_hash}
Path('access-preparation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
