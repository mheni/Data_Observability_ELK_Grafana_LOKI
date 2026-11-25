import argparse
import json
import math
import re
from pathlib import Path
p=argparse.ArgumentParser(description='Personnaliser les deux supports et requetes pour le corpus access complet, sans scenario')
p.add_argument('--manifest',default='preparation13bis.json')
p.add_argument('--reference',default='reference-normalisation13bis.json')
p.add_argument('--output-dir',default='supports13bis-corpus-complet')
a=p.parse_args()
m=json.loads(Path(a.manifest).read_text());r=json.loads(Path(a.reference).read_text());nid=m['normalization_id']
if r['normalization_id']!=nid:p.error('Identifiants differents entre manifeste et reference')
if not re.fullmatch(r'[A-Za-z0-9_.:-]+',nid):p.error('Identifiant non conforme pour les exemples de ce TP')
if int(m['access'])<10000:p.error('Le manifeste ne contient pas le corpus complet attendu : verifier la preparation avant de poursuivre')
seconds=math.ceil((int(r['to_ns'])-int(r['from_ns']))/1e9)
if seconds<=0:p.error('Periode invalide')
base=Path(a.output_dir)
if base.exists():p.error('Dossier existant : choisir un nouveau --output-dir')
base.mkdir(parents=True)
here=Path(__file__).resolve().parent
ctx='\n\n> Lot reel : '+nid+' ; access selon manifeste : '+str(m['access'])+' ; periode de collecte '+r['from_utc']+' a '+r['to_utc']+' ; duree '+str(seconds)+'s.\n\n'
for name in ['ATELIER_13BIS_MODELE.md','GUIDE_60_REQUETES_EXPLORE_MODELE.md']:
    text=(here/name).read_text(encoding='utf-8').replace('__NID__',nid).replace('__DUREE__',str(seconds)+'s')
    first,sep,rest=text.partition('\n')
    (base/name.replace('_MODELE','_PERSONNALISE')).write_text(first+ctx+rest,encoding='utf-8')
items=json.loads((here/'requetes_explore_corpus13bis.json').read_text())
qdir=base/'requetes-explore';qdir.mkdir()
for item in items:
    expr=item['query'].replace('__NID__',nid).replace('$__range',str(seconds)+'s')
    (qdir/(item['id']+'.logql')).write_text(expr+'\n',encoding='utf-8')
qdir=base/'requetes-api';qdir.mkdir()
for key,expr in json.loads((here/'requetes_dashboard_corpus13bis.json').read_text()).items():
    (qdir/(key+'.logql')).write_text(expr.replace('${nid}',nid).replace('$__range',str(seconds)+'s')+'\n',encoding='utf-8')
(base/'CONTEXTE.json').write_text(json.dumps({'normalization_id':nid,'expected_access':m['access'],'from_utc':r['from_utc'],'to_utc':r['to_utc'],'to_ns':r['to_ns'],'range_seconds':seconds},indent=2)+'\n')
print(json.dumps({'output_dir':str(base),'explore_queries':len(items),'expected_access':m['access']},indent=2))
