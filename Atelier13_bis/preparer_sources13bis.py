import argparse
import csv
import json
from pathlib import Path
p=argparse.ArgumentParser(description='References autonomes de demonstration, sans telechargement ni anciens ateliers')
p.add_argument('--output-dir',default='sources13bis')
p.add_argument('--access',help='Fichier Apache facultatif : prendre cinq lignes non vides')
p.add_argument('--movies',help='CSV facultatif movieId,title,genres : prendre cinq enregistrements')
a=p.parse_args()
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie existant ; ne pas remplacer une source suivie')
if bool(a.access)!=bool(a.movies):p.error('Fournir --access ET --movies, ou aucun des deux')
if a.access:
    with Path(a.access).open(encoding='utf-8') as f:
        access=[]
        for line in f:
            if line.strip():access.append(line.rstrip('\r\n'))
            if len(access)==5:break
    with Path(a.movies).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['movieId','title','genres']:p.error('Entete CSV inattendu')
        movies=[]
        for row in reader:
            if None in row or any(v is None or '\n' in v or '\r' in v for v in row.values()):
                p.error('CSV incomplet ou multiligne incompatible avec le suivi brut')
            movies.append(row)
            if len(movies)==5:break
    marker=''
    provenance='Cinq references des fichiers fournis par le participant ; aucune revendication de provenance publique ajoutee'
else:
    sizes=[128,512,1500,4096,8192]
    statuses=[200,200,503,404,200]
    access=[f'127.0.0.1 - - [01/Jan/2000:00:00:{i:02d} +0000] "GET /A13B_SEED/ref{i+1} HTTP/1.1" {statuses[i]} {sizes[i]} "-" "A13B_SEED demo only"' for i in range(5)]
    movies=[{'movieId':str(1001+i),'title':title,'genres':genre} for i,(title,genre) in enumerate([
        ('Film de demonstration A (2001)','Adventure|Comedy'),
        ('Film B, le "retour" (2002)','Drama'),
        ('Film de demonstration C (2003)','Sci-Fi|Adventure'),
        ('Film de demonstration D','(no genres listed)'),
        ('Film de demonstration E (2005)','Comedy')])]
    marker='A13B_SEED'
    provenance='References entierement synthetiques generees pour le TP ; pas un extrait du vrai catalogue MovieLens ni du trafic reel'
if len(access)!=5 or len(movies)!=5:p.error('Au moins cinq references par source sont requises')
if len({m['movieId'] for m in movies})!=5:p.error('Cinq identifiants de film distincts sont requis')
for m in movies:int(m['movieId'])
base.mkdir(parents=True)
(base/'access_log').write_text('\n'.join(access)+'\n',encoding='utf-8')
with (base/'movies.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['movieId','title','genres'],lineterminator='\n')
    w.writeheader();w.writerows(movies)
report={'source_dir':str(base),'raw_marker':marker,'access':5,'movies':5,'provenance':provenance,'next_step':'normaliser_sources13bis.py'}
(base/'sources-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
