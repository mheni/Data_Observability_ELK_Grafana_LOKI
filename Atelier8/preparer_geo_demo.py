import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Petit corpus de points fictifs, independant des vraies IP')
p.add_argument('--bornes', default='access-bornes.json')
a = p.parse_args()
response = json.loads(Path(a.bornes).read_text(encoding='utf-8'))
start = response['aggregations']['premier_evenement'].get('value_as_string')
if not start:
    raise SystemExit('Pas de date de reference : verifier le corpus et la reponse de bornes')
cities = [
    ('Paris','France','FR',48.8566,2.3522),
    ('Tunis','Tunisie','TN',36.8065,10.1815),
    ('Montreal','Canada','CA',45.5017,-73.5673),
    ('Paris','France','FR',48.8566,2.3522),
    ('Tunis','Tunisie','TN',36.8065,10.1815),
    ('Montreal','Canada','CA',45.5017,-73.5673)
]
statuses = [200,200,404,503,200,500]
with Path('geo-demo.ndjson').open('w',encoding='utf-8') as f:
    for i, ((city,country,iso,lat,lon),status) in enumerate(zip(cities,statuses),1):
        key = f'GEO-DEMO-{i:03d}'
        doc = {
            'event_id':key,'@timestamp':start,'dataset':'demo_geographique',
            'environment':'formation','service':'web-formation','method':'GET',
            'path':'/demo','url_path':'/demo','status':status,
            'status_class':f'{status//100}xx','is_http_error':status>=400,
            'message':'Evenement entierement synthetique pour la carte',
            'geo_source':'simulation',
            'client_geo':{'city_name':city,'country_name':country,
                          'country_iso_code':iso,'location':{'lat':lat,'lon':lon}}
        }
        f.write(json.dumps({'index':{'_id':key}})+'\n')
        f.write(json.dumps(doc,ensure_ascii=False)+'\n')
print(json.dumps({'documents':6,'points_distincts':3,'timestamp_reference':start,
                  'source':'simulation ; aucune IP reelle localisee'},ensure_ascii=False,indent=2))
