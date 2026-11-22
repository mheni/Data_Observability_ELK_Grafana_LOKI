import argparse
import csv
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Copies de travail access_log et MovieLens pour Alloy')
p.add_argument('--access', required=True)
p.add_argument('--movies', required=True)
p.add_argument('--output-dir', default='corpus09')
p.add_argument('--access-lines', type=int, default=200)
p.add_argument('--movies-rows', type=int, default=200)
a = p.parse_args()
if a.access_lines < 1 or a.movies_rows < 1:
    p.error('Les tailles doivent etre positives')
sources = [Path(a.access).resolve(),Path(a.movies).resolve()]
if not all(x.is_file() for x in sources):
    p.error('Un fichier source est absent')
target = Path(a.output_dir)
if target.exists():
    p.error('Le dossier de sortie existe deja : choisir un nouveau nom')
access = []
with sources[0].open(encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        access.append(line.rstrip('\r\n'))
        if len(access) == a.access_lines:
            break
movies = []
with sources[1].open(encoding='utf-8-sig',newline='') as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != ['movieId','title','genres']:
        p.error('Entete MovieLens attendu : movieId,title,genres')
    for row in reader:
        if None in row or any(row.get(key) is None for key in reader.fieldnames):
            p.error('Ligne CSV incomplete ou colonnes en trop')
        if any('\n' in value or '\r' in value for value in row.values()):
            p.error('Champ CSV multiligne : non adapte a une collecte Loki ligne par ligne')
        int(row['movieId'])
        movies.append(row)
        if len(movies) == a.movies_rows:
            break
if not access or not movies:
    p.error('Les deux sources doivent contenir des donnees')
target.mkdir(parents=True)
(target/'access_log').write_text('\n'.join(access)+'\n',encoding='utf-8')
with (target/'movies.csv').open('w',encoding='utf-8',newline='') as f:
    writer = csv.DictWriter(f,fieldnames=['movieId','title','genres'],lineterminator='\n')
    writer.writeheader()
    writer.writerows(movies)
report = {
    'access_source':str(sources[0]),'movies_source':str(sources[1]),
    'access_lines':len(access),'movies_records':len(movies),
    'movies_file_lines_including_header':len(movies)+1,
    'expected_loki_entries_before_probes':len(access)+len(movies),
    'note':'Copies echantillonnees, sources intactes ; horodatage Loki = collecte'
}
(target/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
