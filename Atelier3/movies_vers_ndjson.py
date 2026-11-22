import argparse
import csv
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description='CSV MovieLens vers NDJSON Bulk')
p.add_argument('source', nargs='?', default='movies.csv')
p.add_argument('destination', nargs='?', default='movies.ndjson')
a = p.parse_args()
if Path(a.source).resolve() == Path(a.destination).resolve():
    p.error('La destination ne doit pas ecraser la source')
year_pattern = re.compile(r'^(?P<title>.*) \((?P<year>\d{4})\)$')
seen = set()
count = without_year = 0

with open(a.source, encoding='utf-8-sig', newline='') as src, \
     open(a.destination, 'w', encoding='utf-8') as dst:
    reader = csv.DictReader(src)
    if not {'movieId', 'title', 'genres'} <= set(reader.fieldnames or []):
        raise SystemExit('Colonnes attendues : movieId,title,genres')
    for row in reader:
        movie_id = str(int(row['movieId']))
        if movie_id in seen:
            raise SystemExit('movieId duplique : ' + movie_id)
        seen.add(movie_id)
        raw_title = row['title'].strip()
        match = year_pattern.fullmatch(raw_title)
        doc = {
            'movie_id':int(movie_id),
            'title':match['title'] if match else raw_title,
            'genres':[] if row['genres'] == '(no genres listed)' else row['genres'].split('|'),
            'source':'movielens-latest-small'
        }
        if match:
            doc['year'] = int(match['year'])
        else:
            without_year += 1
        dst.write(json.dumps({'index':{'_id':movie_id}}) + '\n')
        dst.write(json.dumps(doc, ensure_ascii=False) + '\n')
        count += 1
report = {'documents':count,'ndjson_lines':2*count,'without_year':without_year,
          'source':a.source,'destination':a.destination}
Path('movies-preparation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
