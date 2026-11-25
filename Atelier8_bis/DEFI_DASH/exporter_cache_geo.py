import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser(description='Exporter un cache de coordonnees GeoIP reelles deja calculees')
p.add_argument('response')
p.add_argument('destination')
a=p.parse_args()
r=json.loads(Path(a.response).read_text(encoding='utf-8'))
if 'error' in r or r.get('timed_out') or r.get('_shards',{}).get('failed',0):
    raise SystemExit('Reponse Elasticsearch en erreur')
hits=r['hits']['hits']
if r['hits']['total']['relation']!='eq' or len(hits)!=r['hits']['total']['value']:
    raise SystemExit('Export incomplet : augmenter la taille autorisee ou paginer')
entries={}
for hit in hits:
    s=hit['_source']
    if s.get('geo_source')!='elasticsearch_geoip':
        raise SystemExit('Origine GeoIP Elasticsearch non attestee dans un document')
    loc=s.get('source_geo',{}).get('location')
    if s.get('source_ip') and loc:
        entries[s['source_ip']]=s['source_geo']
if not entries:
    raise SystemExit('Aucune coordonnee reelle a exporter')
obj={'origin':'elasticsearch_geoip_export','exported_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
     'database_version':'non exposee par cet export ; conserver separement la reference de base du serveur',
     'interpretation':'estimation GeoIP a la date de reference, pas localisation historique prouvee',
     'entries':entries}
Path(a.destination).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ips':len(entries),'destination':a.destination},ensure_ascii=False))
