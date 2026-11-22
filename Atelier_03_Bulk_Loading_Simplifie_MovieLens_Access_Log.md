# Atelier 03 — Bulk Loading simple avec MovieLens et access_log

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — atelier 03 |
| Durée indicative | 1 h 30 à 2 h |
| Prérequis | Elasticsearch de l’atelier 01 ; notions de mapping de l’atelier 02 ; Python 3 |
| Méthode | Python prépare le NDJSON ; curl envoie le fichier à l’API _bulk |
| Exercice guidé | Films MovieLens |
| Défi corrigé | Logs Apache access_log |

## 1. Objectif et simplification

Nous reprenons les deux étapes de préparation et de chargement du TP MovieLens :

```text
Fichier source → Python → NDJSON → curl /_bulk → Elasticsearch → vérification
```

Pas de bibliothèque Python Elasticsearch, pas de virtualenv nécessaire pour ces scripts, pas d’import parallèle ni de benchmark dans ce premier atelier Bulk. Python standard suffit à préparer les fichiers ; la communication avec Elasticsearch reste visible dans curl.

À la fin, vous saurez :

- produire une paire action/document par enregistrement ;
- conserver les types numériques et les tableaux ;
- définir le mapping avant le chargement ;
- envoyer un fichier avec --data-binary ;
- vérifier chaque résultat Bulk ;
- comprendre ce qui se passe lors d’un rejeu ;
- appliquer la même méthode à un fichier de logs.

Les index dédiés sont atelier03-movies et atelier03-access. Ils ne modifient ni movies du TP MovieLens ni les index de l’atelier 01.

## 2. Connexion : même choix que dans les ateliers 01 et 02

### Sans sécurité — utiliser les commandes telles quelles

```bash
export ES_URL='http://localhost:9200'
curl "$ES_URL/_cluster/health?pretty"
```

C’est la présentation utilisée dans tout le support.

### Avec sécurité — ajouter les options à chaque curl Elasticsearch

Si vous avez choisi la variante sécurisée dans l’atelier 01 :

```bash
export ES_URL='https://localhost:9200'
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD
printf '\n'
export ELASTIC_PASSWORD
```

Ajouter immédiatement après chaque curl adressé à Elasticsearch :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Exemple :

```bash
curl --fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  "$ES_URL/_cluster/health?pretty"
```

L’orthographe correcte est --fail-with-body, avec deux tirets. Cette option détecte les erreurs HTTP tout en gardant la réponse visible ; elle ne remplace pas la vérification des items Bulk.

Le JSON ne change pas. ES_URL doit être en HTTPS si le serveur est sécurisé. Ne pas utiliser -k pour masquer une erreur de certificat et ne pas ajouter ces options aux commandes Python, wget ou cat.

Les scripts Python ci-dessous ne se connectent pas au cluster : ils n’ont donc aucun mot de passe à recevoir.

## 3. Préparer le dossier de travail

```bash
mkdir -p ~/formation-observabilite/atelier03
cd ~/formation-observabilite/atelier03
python3 --version
```

Copier les scripts et mappings fournis dans ce dossier, ou les créer avec les blocs du support. Les résultats de préparation sont enregistrés dans le répertoire courant ; conserver des dossiers distincts pour des essais que vous voulez comparer.

Les mappings complets sont fournis : aucun fichier de l’ancien atelier Catalogue n’est requis.

---

# A — Comprendre le format Bulk

## A1 — Une action, puis un document

```ndjson
{"index":{"_id":"1"}}
{"movie_id":1,"title":"Toy Story","year":1995,"genres":["Adventure","Animation"],"source":"movielens-latest-small"}
{"index":{"_id":"2"}}
{"movie_id":2,"title":"Jumanji","year":1995,"genres":["Adventure","Children","Fantasy"],"source":"movielens-latest-small"}
```

| Ligne | Contenu |
|---|---|
| 1 | Action index et identifiant du premier film |
| 2 | Document du premier film |
| 3 | Action index et identifiant du deuxième film |
| 4 | Document du deuxième film |

Il n’y a pas de tableau JSON global ni de virgule entre les lignes. Chaque ligne est un objet JSON complet et le fichier se termine par un saut de ligne.

L’index sera donné dans l’URL /atelier03-movies/_bulk, pas dans les actions. Cela permet de réutiliser le fichier dans une destination explicitement choisie.

## A2 — Pourquoi index et un identifiant stable ?

index crée un document ou remplace le document du même ID. Rejouer le même corpus dans le même index n’ajoute donc pas de nouveaux documents pour ces identifiants.

create refuserait un ID déjà présent. Sans ID explicite, un rejeu pourrait créer de nouveaux documents.

Dans cet atelier, nous utilisons uniquement index. Les actions update et delete ne sont pas nécessaires à la première prise en main ; delete n’aurait d’ailleurs pas de ligne source.

---

# B — Exercice guidé : charger les films MovieLens

## B1 — Préparer movies.csv

Si le jeu du TP MovieLens est déjà présent, le réutiliser en copiant seulement son CSV :

```bash
cp "$HOME/tp-movielens/ml-latest-small/movies.csv" ./movies.csv
```

Sinon, télécharger le jeu officiel dans le dossier de travail :

```bash
wget -O ml-latest-small.zip https://files.grouplens.org/datasets/movielens/ml-latest-small.zip
unzip -n ml-latest-small.zip
cp ml-latest-small/movies.csv ./movies.csv
```

Lire le README et les conditions d’utilisation du jeu avant réutilisation ou redistribution.

```bash
head -n 5 movies.csv
```

Le CSV commence par :

```csv
movieId,title,genres
1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy
```

Un titre peut contenir des virgules ou des guillemets : le parseur csv est nécessaire. Un simple split(',') ne convient pas.

## B2 — Créer le mapping avant l’import

Créer movies-mapping.json :

```bash
cat > movies-mapping.json <<'JSON'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "movie_id": {
        "type": "integer"
      },
      "title": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "year": {
        "type": "integer"
      },
      "genres": {
        "type": "keyword"
      },
      "source": {
        "type": "keyword"
      }
    }
  }
}
JSON
```

Puis :

```bash
curl -X PUT "$ES_URL/atelier03-movies?pretty" \
  -H 'Content-Type: application/json' \
  --data-binary @movies-mapping.json
```

### Explication

| Élément | Rôle |
|---|---|
| settings | Paramètres de l’index : un shard, zéro réplique pour le lab |
| dynamic strict | Refuse les champs non déclarés |
| movie_id | Identifiant métier numérique provenant de movieId |
| title text | Recherche de mots dans le titre |
| title.keyword | Représentation exacte pour tri et agrégation |
| year integer | Comparaisons et agrégations numériques |
| genres keyword | Filtre exact sur chacun des éléments du tableau |
| source keyword | Traçabilité du corpus |

Les sous-champs comme title.keyword sont alimentés automatiquement ; on ne les écrit pas dans les documents.

```bash
curl "$ES_URL/atelier03-movies/_mapping?pretty"
```

Si l’index existe déjà, examiner son mapping et son contenu ; ne pas le supprimer automatiquement.

## B3 — Préparer movies.ndjson avec Python

Créer movies_vers_ndjson.py, ou utiliser le fichier joint :

```python
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
```

Exécuter :

```bash
python3 movies_vers_ndjson.py movies.csv movies.ndjson
head -n 4 movies.ndjson
wc -l movies.ndjson
cat movies-preparation.json
```

### Lecture du code

| Partie | Explication |
|---|---|
| csv.DictReader | Lit chaque ligne avec les noms de colonnes |
| utf-8-sig | Accepte aussi un éventuel marqueur BOM en début de CSV |
| year_pattern | Extrait l’année seulement si le titre finit par une année entre parenthèses |
| int(movieId) | Convertit l’identifiant en entier et le normalise pour _id |
| genres.split('|') | Transforme les genres en tableau |
| (no genres listed) | Devient un tableau vide, pas un vrai genre |
| json.dumps | Échappe correctement guillemets et caractères spéciaux |
| ensure_ascii False | Garde un fichier UTF-8 lisible |
| deux write | Écrit l’action puis le document, chacun suivi d’un saut de ligne |
| seen | Refuse les doublons d’identifiants MovieLens |

Un film sans année identifiable reste importable : le champ year est absent. Aucune année arbitraire n’est inventée.

Pour l’édition MovieLens décrite dans le TP fourni : 9 742 documents donnent 19 484 lignes NDJSON. La référence de contrôle est le nombre effectivement lu dans votre CSV, enregistré sous documents dans movies-preparation.json.

Le script lit le CSV progressivement, mais garde l’ensemble des IDs pour détecter les doublons. C’est adapté à ce petit corpus.

Les fichiers de sortie et de rapport sont remplacés à chaque exécution. En cas d’erreur Python, ne pas envoyer un fichier NDJSON partiellement écrit : corriger la source puis relancer la préparation jusqu’à une fin sans erreur.

## B4 — Charger le fichier avec _bulk

```bash
curl -X POST "$ES_URL/atelier03-movies/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @movies.ndjson \
  -o movies-bulk-response.json
```

### Comprendre la commande

| Partie | Explication |
|---|---|
| -X POST | Envoie les opérations à l’API Bulk |
| atelier03-movies/_bulk | Fixe l’index destination |
| application/x-ndjson | Indique le format des données envoyées |
| --data-binary @movies.ndjson | Transmet le fichier sans perdre les sauts de ligne |
| -o | Enregistre la réponse, pas les données d’entrée |
| refresh=wait_for | Attend la visibilité dans les recherches pour simplifier le contrôle |

Ce fichier MovieLens est un petit chargement pédagogique. Pour un volume important, découper en lots bornés plutôt qu’envoyer un fichier arbitrairement gros. Le paramètre refresh est ici un choix de test, pas une recommandation d’attente à chaque lot de production.

Si curl échoue ou si la réponse n’est pas du JSON Bulk, diagnostiquer l’accès au serveur avant de poursuivre.

## B5 — Vérifier chaque résultat Bulk

Créer verifier_bulk.py, réutilisable pour les deux exercices :

```python
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Verifier chaque resultat de la reponse Bulk')
p.add_argument('response')
p.add_argument('--preparation', required=True)
a = p.parse_args()
response = json.loads(Path(a.response).read_text(encoding='utf-8'))
expected = json.loads(Path(a.preparation).read_text(encoding='utf-8'))['documents']
if not isinstance(response.get('items'), list) or not isinstance(response.get('errors'), bool):
    raise SystemExit('Reponse non Bulk ou incomplete : ' + json.dumps(response, ensure_ascii=False)[:1500])
success = 0
errors = []
for item in response['items']:
    operation, detail = next(iter(item.items()))
    if 200 <= detail.get('status', 0) < 300 and not detail.get('error'):
        success += 1
    else:
        errors.append({'operation':operation, **detail})
report = {'expected':expected,'returned_items':len(response['items']),
          'success':success,'failed':len(errors),'errors_flag':response['errors']}
Path('bulk-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
Path('bulk-rejets.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
for item in errors[:3]:
    print(json.dumps(item, ensure_ascii=False, indent=2))
if errors or response['errors'] or len(response['items']) != expected:
    raise SystemExit(1)
```

Exécuter :

```bash
python3 verifier_bulk.py movies-bulk-response.json \
  --preparation movies-preparation.json
```

### Résultat attendu

- expected et returned_items sont égaux au nombre de films préparés ;
- success est égal à ce même nombre ;
- failed vaut zéro ;
- errors_flag vaut false.

Le programme refuse une réponse non Bulk, contrôle tous les statuts et enregistre bulk-verification.json ainsi que bulk-rejets.json. Il retourne un code non nul si des opérations échouent ou si le nombre d’items est incorrect.

Un HTTP 200 global ne garantit pas le succès de chaque item. Même avec --fail-with-body en mode sécurisé, ce contrôle reste indispensable.

Ces deux fichiers de vérification sont remplacés à chaque utilisation ; copier ceux de MovieLens avant le défi si vous souhaitez les conserver.

## B6 — Compter et rechercher

```bash
curl "$ES_URL/atelier03-movies/_count?pretty"
curl "$ES_URL/atelier03-movies/_doc/109487?pretty"

curl -X POST "$ES_URL/atelier03-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"size":10,"query":{"match":{"title":"star wars"}}}'
```

Le document 109487 correspond normalement à Interstellar dans le jeu fourni ; le vérifier dans le CSV en cas de doute.

Une requête match à plusieurs mots utilise ici son comportement OR par défaut : elle peut retrouver un titre contenant star ou wars. Pour exiger les deux termes analysés :

```bash
curl -X POST "$ES_URL/atelier03-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"title":{"query":"star wars","operator":"and"}}}}'
```

Pour science-fiction après 2010 :

```bash
curl -X POST "$ES_URL/atelier03-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "sort":[{"year":"desc"}],
    "query":{"bool":{"filter":[
      {"term":{"genres":"Sci-Fi"}},
      {"range":{"year":{"gt":2010}}}
    ]}}
  }'
```

### Contrôle de rejeu

Réexécuter B4 puis B5. Sur un index dédié contenant uniquement ces films, le nombre de documents doit rester égal au nombre de movieId uniques. Les opérations peuvent être des remplacements ; le nombre d’opérations réussies n’est pas un nombre de nouvelles créations.

---

# C — Défi : Bulk Loading du fichier access_log

## Énoncé

Utiliser le fichier access_log de l’atelier 01, de préférence sa copie actualisée. Ne pas modifier le fichier que Logstash et Alloy suivent déjà dans /var/log/formation.

Vous devez :

1. Créer un index atelier03-access avec un mapping explicite.
2. Lire 1 000 lignes d’access_log avec Python.
3. Préparer un NDJSON contenant une action index et un document par ligne acceptée.
4. Extraire date, IP, requête HTTP, statut, taille, référent et agent utilisateur.
5. Convertir le statut et la taille en nombres ; ne pas transformer une taille inconnue '-' en faux zéro.
6. Normaliser la date Apache en UTC pour @timestamp.
7. Conserver la ligne d’origine dans message.
8. Enregistrer les rejets avec leur numéro de ligne et leur cause.
9. Charger avec curl et _bulk.
10. Vérifier les items, les volumes et un rejeu sans nouveaux IDs pour le même fichier.

Ne pas consulter le corrigé immédiatement.

### Champs visés

| Champ | Type / rôle |
|---|---|
| @timestamp | Date d’événement UTC |
| client_ip | keyword, choix pédagogique conservant la valeur textuelle |
| request_line | Requête brute, même si elle est atypique |
| method / path / protocol | Parties extraites seulement si la ligne de requête est reconnue |
| status | integer |
| bytes | long, absent si taille inconnue |
| referrer / user_agent | Contexte HTTP |
| message | Ligne originale |
| event_id | ID déterministe |
| source_file_sha256 / line_number | Traçabilité de la ligne dans cette version du fichier |
| service | web-formation |

---

# D — Corrigé du défi access_log

## D1 — Préparer une copie source

Copier dans le dossier courant le corpus de travail fourni ou actualisé, par exemple :

```bash
cp "$HOME/tp01/access_log_actualise" ./access_log
head -n 2 access_log
```

Adapter le chemin si vous utilisez access_log_formation ou le fichier original. Le script n’altère pas cette source.

Contrairement à Loki, cet exercice Bulk Elasticsearch ne nécessite pas de rendre les dates récentes pour accepter des documents historiques dans cet index ordinaire. Il conserve la date de la ligne. Dans Kibana, si le fichier date de 2017, choisir sa période absolue ou ne pas appliquer de filtre temporel.

Si vous souhaitez des événements récents, utiliser le script d’actualisation de l’atelier 01 avant la préparation Bulk. Réhorodater produit une nouvelle version du corpus et donc de nouveaux identifiants dans la stratégie choisie ci-dessous.

## D2 — Créer le mapping

Créer access-mapping.json :

```bash
cat > access-mapping.json <<'JSON'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "event_id": {
        "type": "keyword"
      },
      "source_file_sha256": {
        "type": "keyword"
      },
      "line_number": {
        "type": "integer"
      },
      "client_ip": {
        "type": "keyword"
      },
      "request_line": {
        "type": "text"
      },
      "method": {
        "type": "keyword"
      },
      "path": {
        "type": "keyword"
      },
      "protocol": {
        "type": "keyword"
      },
      "status": {
        "type": "integer"
      },
      "bytes": {
        "type": "long"
      },
      "referrer": {
        "type": "keyword",
        "ignore_above": 2048
      },
      "user_agent": {
        "type": "text"
      },
      "message": {
        "type": "text"
      },
      "service": {
        "type": "keyword"
      }
    }
  }
}
JSON

curl -X PUT "$ES_URL/atelier03-access?pretty" \
  -H 'Content-Type: application/json' \
  --data-binary @access-mapping.json
```

Pourquoi ces types ? Les statuts et tailles doivent pouvoir être comparés numériquement ; @timestamp doit être triable dans le temps ; method et path servent aux filtres exacts ; message permet la recherche plein texte. L’IP est volontairement un keyword pour ce premier import, sans ajouter une validation réseau au parseur.

## D3 — Préparer le NDJSON avec Python

Créer access_vers_ndjson.py :

```python
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Apache access_log vers NDJSON Bulk')
p.add_argument('source', nargs='?', default='access_log')
p.add_argument('destination', nargs='?', default='access.ndjson')
p.add_argument('--limit', type=int, default=1000)
a = p.parse_args()
if a.limit < 1:
    p.error('--limit doit etre positif')
paths = [Path(a.source), Path(a.destination), Path('access-rejets.ndjson'), Path('access-preparation.json')]
if len({x.resolve() for x in paths}) != len(paths):
    p.error('Les fichiers source, destination et rapports doivent etre distincts')
pattern = re.compile(
    r'^(?P<client_ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] '
    r'"(?P<request_line>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'"(?P<referrer>(?:\\.|[^"\\])*)" "(?P<user_agent>(?:\\.|[^"\\])*)"\s*$'
)
months = {name:i for i, name in enumerate(
    ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'), 1)}

def parse_apache_date(value):
    day, month, rest = value.split('/', 2)
    numeric = f'{day}/{months[month]:02d}/{rest}'
    return datetime.strptime(numeric, '%d/%m/%Y:%H:%M:%S %z').astimezone(timezone.utc).isoformat().replace('+00:00','Z')

fingerprint = hashlib.sha256()
with open(a.source, 'rb') as f:
    for chunk in iter(lambda: f.read(1024*1024), b''):
        fingerprint.update(chunk)
source_hash = fingerprint.hexdigest()
read = accepted = rejected = 0
with open(a.source, encoding='utf-8', errors='strict') as src, \
     open(a.destination, 'w', encoding='utf-8') as dst, \
     open('access-rejets.ndjson', 'w', encoding='utf-8') as rejects:
    for line_number, line in enumerate(src, 1):
        if line_number > a.limit:
            break
        read += 1
        message = line.rstrip('\r\n')
        try:
            match = pattern.fullmatch(message)
            if not match:
                raise ValueError('Format Apache Combined non reconnu')
            values = match.groupdict()
            event_id = f'{source_hash}-{line_number}'
            doc = {
                '@timestamp':parse_apache_date(values['apache_time']),
                'event_id':event_id,'source_file_sha256':source_hash,
                'line_number':line_number,'client_ip':values['client_ip'],
                'request_line':values['request_line'],'status':int(values['status']),
                'referrer':values['referrer'],'user_agent':values['user_agent'],
                'message':message,'service':'web-formation'
            }
            if values['bytes'] != '-':
                doc['bytes'] = int(values['bytes'])
            request = values['request_line'].split(' ', 2)
            if len(request) == 3 and request[2].startswith('HTTP/'):
                doc.update(method=request[0], path=request[1], protocol=request[2])
        except (ValueError, KeyError) as exc:
            rejected += 1
            rejects.write(json.dumps({'line':line_number,'message':message,'error':str(exc)}, ensure_ascii=False) + '\n')
            continue
        dst.write(json.dumps({'index':{'_id':event_id}}) + '\n')
        dst.write(json.dumps(doc, ensure_ascii=False) + '\n')
        accepted += 1
report = {'lines_read':read,'documents':accepted,'rejected':rejected,
          'ndjson_lines':2*accepted,'source_file_sha256':source_hash}
Path('access-preparation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
```

Exécuter :

```bash
python3 access_vers_ndjson.py access_log access.ndjson --limit 1000
head -n 4 access.ndjson
cat access-preparation.json
wc -l access-rejets.ndjson
```

### Comprendre le code

| Partie | Explication |
|---|---|
| pattern | Reconnaît la structure Apache Combined en tolérant les caractères échappés dans les champs entre guillemets |
| request_line | Conserve la requête même si ce n’est pas une requête HTTP classique |
| parse_apache_date | Convertit le mois anglais et l’offset de la date en UTC, sans dépendre de la langue du système |
| int(status) | Produit un entier JSON, pas une chaîne numérique |
| bytes différent de '-' | N’indexe une taille que si elle est connue |
| split de request_line | Extrait method, path et protocol lorsque la structure est reconnue |
| rejects | Conserve les lignes non reconnues ou les dates invalides |
| SHA-256 + numéro de ligne | Distingue les occurrences identiques et stabilise les IDs pour le même fichier inchangé |

Le hash est calculé sur la totalité du fichier d’entrée, même avec --limit 1000. Un simple renommage du fichier ne change pas les IDs ; une modification de son contenu les change tous. Cette stratégie convient au rejeu d’un corpus figé, pas au suivi incrémental d’un fichier qui grandit.

Une requête brute atypique peut rester importable sans method/path/protocol : ces champs ne sont pas obligatoires. Un rejet Python n’est pas envoyé à Elasticsearch et ne se retrouve donc pas dans les rejets Bulk.

Les fichiers de préparation et de rejets sont remplacés à chaque exécution. En cas d’erreur Python, notamment d’encodage, ne pas charger une sortie partielle.

### Résultats à contrôler

```text
lines_read = documents + rejected
ndjson_lines = 2 × documents
```

Le test effectué pendant la préparation du support sur les 1 000 premières lignes du fichier original fourni a produit 1 000 documents et zéro rejet de préparation. Vérifier votre propre bilan si votre fichier est différent.

Ne pas charger si documents vaut zéro. Pour la première validation, conserver la limite 1 000 ; l’import de tout le corpus et son découpage en lots constituent une extension.

## D4 — Charger avec _bulk

```bash
curl -X POST "$ES_URL/atelier03-access/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @access.ndjson \
  -o access-bulk-response.json

python3 verifier_bulk.py access-bulk-response.json \
  --preparation access-preparation.json
```

Résultat attendu : tous les documents préparés ont un item réussi. Le fichier access-rejets.ndjson concerne la préparation ; bulk-rejets.json concerne les opérations serveur. Vérifier les deux.

Bulk n’est pas une transaction globale : certaines opérations peuvent réussir malgré le rejet d’autres opérations. Ne pas supposer qu’un échec annule tout le fichier.

## D5 — Vérifier les documents et les champs

```bash
curl "$ES_URL/atelier03-access/_count?pretty"

curl -X POST "$ES_URL/atelier03-access/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"size":3,"sort":[{"@timestamp":"desc"}],"query":{"match_all":{}}}'
```

Sur un index neuf, le compteur attendu est documents du rapport de préparation, à condition que tous les items aient réussi.

Rechercher un statut :

```bash
curl -X POST "$ES_URL/atelier03-access/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"status":200}}}'
```

Compter les statuts :

```bash
curl -X POST "$ES_URL/atelier03-access/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"size":0,"aggs":{"statuts":{"terms":{"field":"status","size":20}}}}'
```

Ici chaque document a un statut unique : si tous les statuts présents sont retournés par l’agrégation, la somme des doc_count des buckets correspond au total de documents.

Dans Kibana, utiliser une Data View sur atelier03-access. Sans filtre temporel pour une première vérification, ou avec @timestamp et une période qui inclut les dates réelles du corpus.

## D6 — Rejouer le même fichier

Réexécuter D4 puis le compteur D5. Le nombre de documents ne doit pas augmenter pour les mêmes actions et IDs.

Le document est remplacé par index ; ce n’est pas une absence d’écriture. Un corpus modifié ou réhorodaté change son hash et ne représente plus le même jeu d’identifiants. Utiliser alors un nouvel index de session si vous souhaitez comparer des comptes propres.

---

# E — Dépannage, bilan et livrables

## E1 — Erreurs courantes

| Symptôme | Vérification |
|---|---|
| Erreur de parsing Bulk | Une action puis un document, chaque objet sur une ligne, saut de ligne final |
| HTTP 200 mais documents manquants | Exécuter verifier_bulk.py et lire chaque rejet |
| Réponse avec error mais sans items | Erreur globale, pas une réponse Bulk à valider comme un succès |
| Fichier source introuvable | Répertoire courant et chemins des CSV/logs |
| Trop peu de documents | Préparation, rejets, IDs dupliqués, index non vide ou import incomplet |
| _count différent immédiatement | Attendre visibilité ; les commandes du support utilisent refresh=wait_for |
| Discover vide | Index/Data View et période, notamment pour access_log historique |
| HTTP 401/403 | Identité ou droits du mode sécurisé |
| Problème de certificat | URL HTTPS, bon CA, pas de contournement -k |
| HTTP 413 | Fichier trop gros : réduire le volume et préparer des lots |
| HTTP 429 | Réduire la pression ; ne pas réessayer en boucle sans diagnostic |

Un compteur correct ne prouve pas que tous les champs sont bons : lire quelques documents et vérifier les types, dates et valeurs.

## E2 — Checklist

- Mapping créé avant l’import.
- Conversion MovieLens réussie avec nombre de films connu.
- Une paire action/document par enregistrement préparé.
- Réponse Bulk contrôlée item par item.
- Recherche et compteur MovieLens cohérents.
- access_log transformé sans modification de la source.
- Dates converties, tailles inconnues distinguées de zéro.
- Rejets de préparation séparés des rejets serveur.
- Rejeu sans nouveaux documents pour un corpus inchangé.
- Aucun secret dans les scripts et livrables.

## E3 — Livrables

- Deux mappings JSON.
- movies_vers_ndjson.py et access_vers_ndjson.py.
- verifier_bulk.py.
- Fichiers de préparation, réponses Bulk et bilans.
- Trois requêtes de contrôle et leur interprétation.

Les rejets et messages peuvent contenir des IP, URL ou autres données sensibles : relire avant diffusion.

## E4 — Nettoyage optionnel

Conserver les index pour les TP suivants si le formateur le demande. Sinon, après autorisation, supprimer seulement les deux index de cet atelier :

```bash
curl -X DELETE "$ES_URL/atelier03-movies,atelier03-access?pretty"
```

Ne pas exécuter par défaut. Ne pas utiliser un wildcard global ni supprimer les index des ateliers 01 et 02.

## Sources et validation du support

Le scénario MovieLens reprend les étapes « préparer le fichier NDJSON » et « charger les films avec l’API Bulk » du TP 02 MovieLens fourni. Le défi réutilise access_log de l’atelier 01. Les anciens exemples _type/doc_type ne sont pas repris : ils ne correspondent pas à l’API du laboratoire 9.x.

Les scripts ont été vérifiés syntaxiquement ; la conversion MovieLens a été exécutée sur un petit CSV de test contenant notamment des virgules, des guillemets et un titre sans année. La conversion access_log a été exécutée sur 1 000 lignes du fichier original fourni. La vérification Bulk a été testée sur des réponses synthétiques de succès, d’échec et de nombre d’items incorrect.

Aucun chargement n’a été effectué sur votre cluster pendant la génération. Valider les requêtes et mappings sur votre environnement avant formation.
