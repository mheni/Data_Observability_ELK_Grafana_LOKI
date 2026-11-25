import argparse
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='A13bis : controle agrege de livraison, sans telecharger les logs et sans limite de 2000 lignes')
p.add_argument('--manifest',default='preparation13bis.json')
p.add_argument('--corpus',default='corpus13bis',help='Chemin conserve pour compatibilite ; le manifeste local y est verifie si present')
p.add_argument('--source',default='sources13bis/access_log',help='Source locale pour detecter un manifeste obsolete')
p.add_argument('--output',default='reference-normalisation13bis.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=180)
p.add_argument('--start-utc',help='Debut UTC ISO facultatif si la fenetre automatique est trop ancienne')
a=p.parse_args()
if Path(a.output).exists():p.error('Sortie deja presente : choisir un autre --output, ne pas ecraser une reference')
if not 1<=a.timeout<=600:p.error('Timeout entre 1 et 600 secondes')
m=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
nid=m['normalization_id']
expected=int(m['per_format']);expected_access=int(m['access'])
if expected<1 or expected_access<1:p.error('Manifeste sans corpus access')
source_path=Path(a.source)
if source_path.exists():
    with source_path.open(encoding='utf-8') as f:source_count=sum(1 for line in f if line.strip())
    if source_count!=expected_access:p.error('Source et normalisation differentes : source='+str(source_count)+' ; manifeste access='+str(expected_access)+'. Arreter et corriger la preparation, sans ecraser les fichiers suivis.')
local=Path(a.corpus,'manifest.json')
if local.exists():
    lm=json.loads(local.read_text(encoding='utf-8'))
    if lm.get('normalization_id')!=nid or int(lm['per_format'])!=expected:p.error('Le manifeste ne correspond pas au dossier corpus')
start=int(m['start_ns'])-5_000_000_000
if a.start_utc:
    dt=datetime.fromisoformat(a.start_utc.replace('Z','+00:00'))
    if dt.tzinfo is None:p.error('--start-utc doit inclure un fuseau')
    start=int(dt.timestamp()*1e9)
if start>=time.time_ns():p.error('Debut futur')

def query(fmt,access,seconds):
    expr='{job="atelier13bis",format='+json.dumps(fmt)+'} |= '+json.dumps(nid)
    parser='json' if fmt=='json' else 'logfmt'
    expr+='\n| '+parser+' n_id="normalization_id", src="source_dataset"\n| __error__=""\n| n_id='+json.dumps(nid)
    if access:expr+='\n| src="access"'
    return 'sum(count_over_time('+expr+' ['+str(seconds)+'s]))'

def evaluate(expr,end):
    params=urllib.parse.urlencode({'query':expr,'time':str(end),'timeout':'60s'})
    with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query?'+params,timeout=70) as f:r=json.load(f)
    if r.get('status')!='success' or r.get('data',{}).get('resultType')!='vector':
        raise RuntimeError('Reponse Loki non vectorielle : '+str(r)[:500])
    values=r['data']['result']
    if not values:return 0
    if len(values)!=1:raise RuntimeError('Agregation attendue : une seule serie')
    number=float(values[0]['value'][1])
    if not math.isfinite(number) or number<0 or number!=int(number):raise RuntimeError('Compte invalide')
    return int(number)

deadline=time.monotonic()+a.timeout
while True:
    end=time.time_ns();seconds=math.ceil((end-start)/1e9)
    values={}
    for fmt in ['json','logfmt']:
        values[fmt]=evaluate(query(fmt,False,seconds),end)
        values[fmt+'_access']=evaluate(query(fmt,True,seconds),end)
    targets={'json':expected,'logfmt':expected,'json_access':expected_access,'logfmt_access':expected_access}
    if any(values[k]>v for k,v in targets.items()):raise SystemExit('Surplus : verifier relectures, bornes et doublons. '+str(values))
    if values==targets:
        iso=lambda ns:datetime.fromtimestamp(ns/1e9,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        result={'normalization_id':nid,'from_ns':str(start),'to_ns':str(end),'from_utc':iso(start),'to_utc':iso(end),
                'observed':values,'expected':targets,'validation_kind':'aggregate_counts_only',
                'ids_checked_in_loki':False,'note':'Egalite de volumes, pas preuve evenement par evenement ; une perte et un doublon peuvent se compenser.'}
        Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2));break
    print('Comptes en attente : '+str(values),flush=True)
    if time.monotonic()>=deadline:raise SystemExit('Volumes incomplets : '+str(values))
    time.sleep(3)
