import argparse
import json
import math
from pathlib import Path
p=argparse.ArgumentParser(description='Produire les supports A13bis avec vrais marqueurs et vraie periode')
p.add_argument('--normalisation',default='preparation13bis.json')
p.add_argument('--scenario',default='manifest-scenario13bis.json')
p.add_argument('--reference',default='reference13bis.json')
p.add_argument('--output-dir',default='supports13bis')
a=p.parse_args()
n=json.loads(Path(a.normalisation).read_text());m=json.loads(Path(a.scenario).read_text());r=json.loads(Path(a.reference).read_text())
if m['run_id']!=r['run_id']:p.error('Run different entre manifeste et reference')
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie existant : conserver les anciennes versions')
base.mkdir(parents=True)
seconds=math.ceil((int(r['to_ns'])-int(r['from_ns']))/1e9)
context='\n\n> Support personnalise : normalisation '+n['normalization_id']+' ; run '+m['run_id']+' ; periode scenario '+r['from_utc']+' a '+r['to_utc']+' UTC.\n\n'
for source,dest in [('ATELIER_13BIS_MODELE.md','ATELIER_13BIS_PERSONNALISE.md'),('GUIDE_60_REQUETES_EXPLORE_MODELE.md','GUIDE_60_REQUETES_EXPLORE.md')]:
    text=Path(__file__).with_name(source).read_text(encoding='utf-8')
    text=text.replace('Ce support se personnalise avec `personnaliser_support13bis.py`. Ne pas exécuter les marqueurs `__NID__`, `__RUN__` ou `__RANGE_SECONDS__` littéralement. La version personnalisée contient les vrais identifiants et la durée correspondant aux références.', 'Ce support est personnalisé avec les identifiants et la durée de la séance. Les blocs LogQL peuvent être copiés dans Explore avec les périodes indiquées.')
    text=text.replace('__NID__',n['normalization_id']).replace('__RUN__',m['run_id']).replace('__RANGE_SECONDS__',str(seconds))
    first,sep,rest=text.partition('\n')
    (base/dest).write_text(first+context+rest,encoding='utf-8')
(base/'CONTEXTE.json').write_text(json.dumps({'normalisation':n['normalization_id'],'run':m['run_id'],'scenario_from':r['from_utc'],'scenario_to':r['to_utc'],'range_seconds':seconds},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output_dir':str(base),'supports':2,'range_seconds':seconds},indent=2))
