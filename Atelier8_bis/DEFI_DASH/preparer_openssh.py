import argparse
import collections
import hashlib
import ipaddress
import json
import re
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Loghub OpenSSH vers Bulk NDJSON, sans connexion reseau')
p.add_argument('source')
p.add_argument('--outdir', default='preparation')
p.add_argument('--year', type=int, required=True, help='Annee conventionnelle explicite, non deduite du log')
p.add_argument('--utc-offset', default='+0000')
p.add_argument('--geo-cache', help='Cache GeoIP reel exporte par le formateur, jamais des villes inventees')
a = p.parse_args()
if not re.fullmatch(r'[+-]\d{4}', a.utc_offset):
    p.error('Offset attendu : +0000, +0100, etc.')
base = Path(a.outdir)
base.mkdir(parents=True, exist_ok=True)
src = Path(a.source).resolve()
if src.parent == base.resolve():
    p.error('Placer la source hors du dossier de sortie')
sha = hashlib.sha256(src.read_bytes()).hexdigest()
cache = None
if a.geo_cache:
    cache = json.loads(Path(a.geo_cache).read_text(encoding='utf-8'))
    if cache.get('origin') != 'elasticsearch_geoip_export' or not cache.get('exported_at') or not cache.get('entries'):
        p.error('Cache GeoIP reel et date requis ; voir exporter_cache_geo.py')
months = {m:i for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(),1)}
head = re.compile(r'^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<program>[^\s\[:]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<body>.*)$')
auth = re.compile(r'^(?P<result>Failed|Accepted) (?P<method>password|publickey|none) for (?P<invalid>invalid user )?(?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+)\b')
invalid = re.compile(r'^Invalid user (?P<user>\S+) from (?P<ip>\S+)')
policy = f'assumed_year={a.year};assumed_offset={a.utc_offset};no_year_in_source'

def ip_value(token):
    for candidate in (token, token.strip('[];,').rstrip(':')):
        try:
            return ipaddress.ip_address(candidate)
        except ValueError:
            pass
    return None

def classify(body):
    d = {'event_type':'other', 'auth_record':False, 'auth_outcome':'not_applicable'}
    match = auth.match(body)
    if body.startswith('message repeated '):
        d['event_type'] = 'message_repeat'
        n = re.match(r'message repeated (\d+) times:', body)
        if n:
            d['repeat_count'] = int(n[1])
    elif match:
        d.update(event_type='auth_failure' if match['result']=='Failed' else 'auth_success',
                 auth_record=True, auth_outcome='failure' if match['result']=='Failed' else 'success',
                 auth_method=match['method'], user_name=match['user'],
                 invalid_user=bool(match['invalid']), source_port=int(match['port']))
    elif invalid.match(body):
        d['event_type'] = 'invalid_user'
        d['user_name'] = invalid.match(body)['user']
        d['invalid_user'] = True
    elif 'authentication failure' in body:
        d['event_type'] = 'pam_failure'
    elif 'disconnect' in body.lower() or body.startswith('Connection closed'):
        d['event_type'] = 'disconnect'
    elif body.startswith('reverse mapping checking'):
        d['event_type'] = 'reverse_dns_warning'
    elif body.startswith('Did not receive identification'):
        d['event_type'] = 'no_identification'
    candidates = []
    if match:
        candidates.append(match['ip'])
    if invalid.match(body):
        candidates.append(invalid.match(body)['ip'])
    candidates += re.findall(r'\b(?:from|by)\s+(\S+)', body)
    candidates += re.findall(r'\brhost=([^\s;]+)', body)
    if body.startswith('reverse mapping checking'):
        candidates += re.findall(r'\[([^\]]+)\]', body)
    for token in candidates:
        addr = ip_value(token)
        if addr:
            d.update(source_ip=str(addr),source_ip_public=addr.is_global)
            break
    return d

counts = collections.Counter()
ips = set()
first = last = None
read = accepted = rejected = 0
simdocs = []
sim_ips = set()
cachehash = hashlib.sha256(Path(a.geo_cache).read_bytes()).hexdigest() if cache else None
with src.open(encoding='utf-8', errors='strict') as f, \
     (base/'openssh.ndjson').open('w',encoding='utf-8') as dst, \
     (base/'rejets.ndjson').open('w',encoding='utf-8') as rej:
    for number,line in enumerate(f,1):
        read += 1
        raw = line.rstrip('\r\n')
        try:
            m = head.fullmatch(raw)
            if not m:
                raise ValueError('Entete syslog non reconnue')
            dt = datetime.strptime(f'{a.year}-{months[m["month"]]:02d}-{int(m["day"]):02d} {m["time"]} {a.utc_offset}', '%Y-%m-%d %H:%M:%S %z').astimezone(timezone.utc)
            stamp = dt.isoformat().replace('+00:00','Z')
            key = hashlib.sha256(f'v1|{sha}|{policy}|{number}'.encode()).hexdigest()
            d = {'@timestamp':stamp,'timestamp_policy':policy,'event_id':key,
                 'source_file_sha256':sha,'line_number':number,'host_name':m['host'],
                 'program':m['program'],'message':raw,'content':m['body'],
                 'dataset':'loghub_openssh_2k', 'geo_source':'none', 'geo_status':'no_ip'}
            if m['pid']:
                d['process_pid'] = int(m['pid'])
            d.update(classify(m['body']))
            if 'source_ip' in d:
                d['geo_status'] = 'not_located'
            if cache and d.get('source_ip') in cache['entries']:
                geo = cache['entries'][d['source_ip']]
                loc = geo.get('location', {})
                lat,lon = float(loc['lat']),float(loc['lon'])
                if not (-90<=lat<=90 and -180<=lon<=180):
                    raise ValueError('Coordonnees hors limites dans le cache')
                d['source_geo'] = {k:geo[k] for k in ('continent_name','country_iso_code','country_name','region_name','city_name') if k in geo}
                d['source_geo']['location'] = {'lat':lat,'lon':lon}
                d.update(geo_source='geoip_cache',geo_status='located',geo_reference_at=cache['exported_at'])
            dst.write(json.dumps({'index':{'_id':key}})+'\n')
            dst.write(json.dumps(d,ensure_ascii=False)+'\n')
            accepted += 1
            counts[d['event_type']] += 1
            if 'source_ip' in d:
                counts['with_ip'] += 1
                ips.add(d['source_ip'])
                if d['source_ip_public']:
                    counts['public_ip_records'] += 1
            if d['geo_status']=='located':
                counts['located_from_cache'] += 1
            first = stamp if first is None else min(first,stamp)
            last = stamp if last is None else max(last,stamp)
            if len(simdocs)<50 and d.get('source_ip_public') and d['source_ip'] not in sim_ips:
                simdocs.append({'_source':d})
                sim_ips.add(d['source_ip'])
        except (ValueError,KeyError) as exc:
            rejected += 1
            rej.write(json.dumps({'line':number,'error':str(exc),'message':raw},ensure_ascii=False)+'\n')
report = {'source':str(src),'source_file_sha256':sha,'timestamp_policy':policy,
          'lines_read':read,'documents':accepted,'rejected':rejected,
          'ndjson_lines':2*accepted,'event_types_and_quality':dict(counts),
          'distinct_ips_exact_local':len(ips),'first_event':first,'last_event':last,
          'geo_cache_sha256':cachehash,'parser_schema':'v1'}
(base/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'geo-simulate.json').write_text(json.dumps({'docs':simdocs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not accepted:
    raise SystemExit('Aucun document prepare : ne pas envoyer le Bulk')
