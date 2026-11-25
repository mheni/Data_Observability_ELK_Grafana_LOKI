import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description='Preparer TOUT le fichier Apache ; aucun echantillonnage et aucune modification du fichier fourni')
p.add_argument('--access',required=True)
p.add_argument('--output-dir',default='sources13bis')
a=p.parse_args();src=Path(a.access);base=Path(a.output_dir)
if not src.is_file():p.error('Fichier access absent')
if base.exists():p.error('Dossier de sortie existant : ne pas ecraser ; utiliser le parcours de reprise du support')
with src.open(encoding='utf-8') as f:n=sum(1 for line in f if line.strip())
if not n:p.error('Fichier sans ligne non vide')
base.mkdir(parents=True)
shutil.copyfile(src,base/'access_log')
movies=[['1001','Film de demonstration A (2001)','Adventure|Comedy'],['1002','Film B, le "retour" (2002)','Drama'],['1003','Film de demonstration C (2003)','Sci-Fi|Adventure'],['1004','Film de demonstration D','(no genres listed)'],['1005','Film de demonstration E (2005)','Comedy']]
with (base/'movies.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['movieId','title','genres']);w.writerows(movies)
m={'source_dir':str(base),'access':n,'access_source':src.name,'access_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'movies':5,'raw_marker':'',
   'provenance':'Access : fichier complet fourni, copie sans alteration. Movies : cinq exemples synthetiques, hors dashboard principal.'}
(base/'sources-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(m,ensure_ascii=False,indent=2))
