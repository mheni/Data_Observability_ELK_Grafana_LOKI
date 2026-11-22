# Atelier 07 — Interroger les données : bool, filtres, tris, agrégations et pagination profonde

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Programme | Data Observability — jour 3, atelier 7 sur 13 |
| Durée indicative | 2 heures ; export Python en prolongement si nécessaire |
| Environnement | Elasticsearch 9.x sur Ubuntu ; HTTP simple ou variante HTTPS de l’atelier 01 |
| Prérequis | Mapping, Bulk, recherche plein texte et contrôles des ateliers précédents |
| Corpus | Événements synthétiques d’exécution de pipelines de données |
| Livrables | Requêtes JSON, agrégations, pages PIT et export NDJSON |

## 1. Introduction et objectifs

Cet atelier passe de la recherche documentaire à une investigation d’observabilité : retrouver les erreurs d’une exécution, comparer les pipelines, compter les incidents et parcourir les résultats sans doublons.

Il complète l’atelier 05 : le scoring et les analyseurs ne sont pas repris en détail. Le catalogue de films `atelier05-movies` peut être conservé comme ressource ; un jeu d’événements dédié rend ici les calculs, tris et contrôles reproductibles.

### Objectifs pédagogiques

- Combiner recherche textuelle et contraintes dans `bool`.
- Distinguer `must`, `filter`, `should` et `must_not`.
- Filtrer par valeur, plage temporelle et durée.
- Trier sur des champs adaptés et limiter les champs retournés.
- Lire `hits.total`, les documents et les agrégations sans les confondre.
- Utiliser `terms`, `date_histogram`, `avg`, `max`, `percentiles` et `cardinality`.
- Choisir entre pagination simple et PIT + `search_after`.
- Recopier le tableau `sort` complet, y compris le départage technique PIT.
- Fermer les PIT et produire un export cohérent contrôlé.
- Expliquer la différence entre vue PIT, curseur search_after et contrôle OCC.
- Comprendre expiration, coût en ressources et limites d’une reprise après erreur.

## 2. Préparer la connexion et le dossier

### Objectif

Utiliser le même choix de connexion que dans les ateliers précédents.

### Mode simple — requêtes à utiliser telles quelles

```bash
mkdir -p ~/formation-observabilite/atelier07
cd ~/formation-observabilite/atelier07
export ES_URL='http://localhost:9200'
curl "$ES_URL/_cluster/health?pretty"
```

### Variante sécurisée de l’atelier 01

```bash
export ES_URL='https://localhost:9200'
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD
printf '\n'
export ELASTIC_PASSWORD
```

Ajouter immédiatement après chaque curl Elasticsearch :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Exemple :

```bash
curl --fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  "$ES_URL/_cluster/health?pretty"
```

L’option correcte a deux tirets. Ne pas employer -k pour masquer une erreur TLS. Le JSON ne change pas et les scripts Python ne reçoivent pas les options curl : l’exporteur fourni adapte lui-même son accès à ES_URL.

### Résultat attendu et dépannage

Le cluster répond. Distinguer les erreurs réseau/TLS/401/403 d’une recherche qui ne trouve aucun résultat. Conserver les mots de passe hors des fichiers de requêtes et captures.

## 3. Définir le corpus d’investigation

### Continuité avec MovieLens et les access logs

Le corpus représente des journaux applicatifs synthétiques des traitements déjà rencontrés :

- pipeline movies : import du catalogue de films ;
- pipeline ratings : transformation de notes ;
- pipeline access_logs : export de journaux d’accès.

Ces douze événements ne sont pas des lignes extraites de votre access_log ni des résultats d’import réellement mesurés. Ils permettent de vérifier les agrégations avec un corpus court et identique pour tous. Les champs pipeline_id et run_id enrichissent les logs avec leur contexte, comme la dénormalisation étudiée à l’atelier 06.

Les champs service, environment, level, status et les IDs sont des keyword pour les filtres, tris et regroupements ; message est text pour la recherche de mots. duration_ms et records_processed sont numériques, @timestamp est une date.



Nous utilisons douze événements du 3 novembre 2026, entre 08:00 et 08:11 UTC. Les horodatages sont fixes pour que tous les stagiaires disposent des mêmes résultats.

### Objectif

Créer des champs textuels pour les messages et des champs exacts pour les filtres, tris et agrégations.

### Mapping

```bash
cat > events-mapping.json <<'JSON'
{
  "settings":{"number_of_shards":1,"number_of_replicas":0},
  "mappings":{
    "dynamic":"strict",
    "properties":{
      "event_id":{"type":"keyword"},
      "@timestamp":{"type":"date"},
      "service":{"type":"keyword"},
      "environment":{"type":"keyword"},
      "pipeline_id":{"type":"keyword"},
      "run_id":{"type":"keyword"},
      "level":{"type":"keyword"},
      "status":{"type":"keyword"},
      "message":{"type":"text"},
      "duration_ms":{"type":"integer"},
      "records_processed":{"type":"integer"},
      "error_code":{"type":"keyword"}
    }
  }
}
JSON

curl -X PUT "$ES_URL/atelier07-events?pretty" \
  -H 'Content-Type: application/json' --data-binary @events-mapping.json
```

### Données

```bash
cat > events.ndjson <<'EOF'
{"index":{"_id":"E001"}}
{"event_id":"E001","@timestamp":"2026-11-03T08:00:00Z","service":"movies-api","environment":"formation","pipeline_id":"movies","run_id":"R001","level":"INFO","status":"success","message":"Import movies completed","duration_ms":100,"records_processed":1000}
{"index":{"_id":"E002"}}
{"event_id":"E002","@timestamp":"2026-11-03T08:01:00Z","service":"movies-api","environment":"formation","pipeline_id":"movies","run_id":"R002","level":"WARN","status":"slow","message":"Slow response from source database","duration_ms":1200,"records_processed":800}
{"index":{"_id":"E003"}}
{"event_id":"E003","@timestamp":"2026-11-03T08:02:00Z","service":"movies-api","environment":"formation","pipeline_id":"movies","run_id":"R003","level":"ERROR","status":"failed","message":"Connection timeout to source database","duration_ms":5000,"records_processed":0,"error_code":"TIMEOUT"}
{"index":{"_id":"E004"}}
{"event_id":"E004","@timestamp":"2026-11-03T08:03:00Z","service":"ratings-worker","environment":"formation","pipeline_id":"ratings","run_id":"R004","level":"INFO","status":"success","message":"Ratings transformation completed","duration_ms":200,"records_processed":400}
{"index":{"_id":"E005"}}
{"event_id":"E005","@timestamp":"2026-11-03T08:04:00Z","service":"ratings-worker","environment":"formation","pipeline_id":"ratings","run_id":"R005","level":"ERROR","status":"failed","message":"Invalid schema in ratings input","duration_ms":300,"records_processed":0,"error_code":"SCHEMA"}
{"index":{"_id":"E006"}}
{"event_id":"E006","@timestamp":"2026-11-03T08:05:00Z","service":"ratings-worker","environment":"formation","pipeline_id":"ratings","run_id":"R006","level":"WARN","status":"slow","message":"Transformation duration above threshold","duration_ms":2200,"records_processed":300}
{"index":{"_id":"E007"}}
{"event_id":"E007","@timestamp":"2026-11-03T08:06:00Z","service":"access-exporter","environment":"formation","pipeline_id":"access_logs","run_id":"R007","level":"INFO","status":"success","message":"Access log export completed","duration_ms":400,"records_processed":200}
{"index":{"_id":"E008"}}
{"event_id":"E008","@timestamp":"2026-11-03T08:07:00Z","service":"access-exporter","environment":"formation","pipeline_id":"access_logs","run_id":"R008","level":"ERROR","status":"failed","message":"Connection timeout to log storage provider","duration_ms":5000,"records_processed":0,"error_code":"TIMEOUT"}
{"index":{"_id":"E009"}}
{"event_id":"E009","@timestamp":"2026-11-03T08:08:00Z","service":"access-exporter","environment":"formation","pipeline_id":"access_logs","run_id":"R009","level":"INFO","status":"success","message":"Access log export recovery completed","duration_ms":600,"records_processed":250}
{"index":{"_id":"E010"}}
{"event_id":"E010","@timestamp":"2026-11-03T08:09:00Z","service":"movies-api","environment":"formation","pipeline_id":"movies","run_id":"R010","level":"INFO","status":"success","message":"Import recovered after connection timeout","duration_ms":150,"records_processed":1100}
{"index":{"_id":"E011"}}
{"event_id":"E011","@timestamp":"2026-11-03T08:10:00Z","service":"ratings-worker","environment":"test","pipeline_id":"ratings","run_id":"R011","level":"ERROR","status":"failed","message":"Test connection timeout intentionally generated","duration_ms":5000,"records_processed":0,"error_code":"TIMEOUT"}
{"index":{"_id":"E012"}}
{"event_id":"E012","@timestamp":"2026-11-03T08:11:00Z","service":"access-exporter","environment":"formation","pipeline_id":"access_logs","run_id":"R012","level":"INFO","status":"success","message":"Final access_logs export completed","duration_ms":700,"records_processed":300}
EOF

curl -X POST "$ES_URL/atelier07-events/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @events.ndjson \
  -o bulk-response.json

python3 - <<'PY'
import json
r = json.load(open('bulk-response.json'))
if 'items' not in r:
    raise SystemExit(f'Reponse non Bulk : {r}')
print('Operations :', len(r['items']), 'errors :', r['errors'])
for item in r['items']:
    d = next(iter(item.values()))
    if d.get('error'):
        print(d)
PY
```

### Résultat attendu

Douze documents et aucun rejet. Un rejeu remplace les mêmes identifiants.

### Point de contrôle

```bash
curl "$ES_URL/atelier07-events/_count?pretty"
```

### Dépannage

Si l’index existe déjà, inspecter son mapping et son contenu avant de poursuivre. Les résultats chiffrés suivants supposent exactement ce corpus, sans documents supplémentaires.

## 4. Construire une requête booléenne d’investigation

### Objectif

Retrouver les erreurs contenant timeout, dans l’environnement de formation et sur la période connue.

### Commande

```bash
cat > query-investigation.json <<'JSON'
{
  "size":10,
  "track_total_hits":true,
  "_source":["event_id","@timestamp","service","run_id","message","duration_ms"],
  "query":{"bool":{
    "must":[{"match":{"message":"timeout"}}],
    "filter":[
      {"term":{"environment":"formation"}},
      {"term":{"level":"ERROR"}},
      {"range":{"@timestamp":{"gte":"2026-11-03T08:00:00Z","lt":"2026-11-03T09:00:00Z"}}}
    ],
    "must_not":[{"term":{"status":"success"}}]
  }}
}
JSON

curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @query-investigation.json
```

### Résultat attendu

E003 et E008. E011 est exclu par l’environnement et E010 par le niveau et le statut.

### Explication

- `must` contribue au score et impose une correspondance.
- `filter` impose une condition sans contribuer directement au score.
- `must_not` exclut ; il est ici volontairement redondant avec `level: ERROR` pour montrer sa syntaxe.
- Le champ `message` est textuel, alors que `environment` et `level` sont des valeurs exactes.

### Point de contrôle

Expliquer pourquoi un `match` sur timeout seul aurait aussi retrouvé E010 et E011.

## 5. Ne pas confondre should facultatif et OR obligatoire

### Objectif

Sélectionner les événements WARN ou ERROR sans accepter tous les INFO de formation.

### Commande

```bash
curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":20,
    "query":{"bool":{
      "filter":[{"term":{"environment":"formation"}}],
      "should":[
        {"term":{"level":"WARN"}},
        {"term":{"level":"ERROR"}}
      ],
      "minimum_should_match":1
    }}
  }'
```

### Résultat attendu

E002, E003, E005, E006 et E008 : cinq événements.

### Explication

Avec un `filter` ou un `must` présent, les clauses should sont facultatives par défaut. Pour les utiliser comme un OR obligatoire, demander explicitement `minimum_should_match: 1`.

Pour sélectionner plusieurs valeurs d’un même champ, une alternative plus simple est un filtre `terms` :

```json
{"terms":{"level":["WARN","ERROR"]}}
```

### Point de contrôle

Retirer temporairement `minimum_should_match`, constater l’élargissement, puis le rétablir.

## 6. Trier et réduire la réponse

### Objectif

Classer les événements par durée tout en gardant un ordre déterministe.

### Commande

```bash
curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":5,
    "track_total_hits":true,
    "_source":["event_id","service","level","duration_ms"],
    "sort":[{"duration_ms":"desc"},{"event_id":"asc"}],
    "query":{"term":{"environment":"formation"}}
  }'
```

### Résultat attendu

Les deux durées 5000 sont départagées par `event_id`. L’ordre commence par E003, E008, E006, E002, E012.

### Explication

Le tri explicite sur la durée remplace le classement par pertinence par défaut. Un `_score` nul dans une recherche triée par champs n’est pas nécessairement une erreur.

`_source` limite les champs visibles dans la réponse ; ce n’est ni une restriction d’accès ni une modification des données stockées.

### Point de contrôle

`hits.total.value` indique onze événements de formation, même si seulement cinq sont présents dans `hits.hits`.

### Dépannage

Ne pas trier directement sur `message`, champ `text`. Utiliser un champ keyword dédié lorsque l’on doit trier une valeur textuelle exacte.

## 7. Agréger les événements par service

### Objectif

Produire une synthèse sans renvoyer les documents individuels.

### Commande

```bash
cat > query-aggs.json <<'JSON'
{
  "size":0,
  "track_total_hits":true,
  "query":{"term":{"environment":"formation"}},
  "aggs":{
    "par_service":{
      "terms":{"field":"service","size":10,"order":{"_key":"asc"}},
      "aggs":{
        "duree_moyenne":{"avg":{"field":"duration_ms"}},
        "duree_max":{"max":{"field":"duration_ms"}},
        "erreurs":{
          "filter":{"term":{"level":"ERROR"}}
        },
        "enregistrements":{"sum":{"field":"records_processed"}}
      }
    }
  }
}
JSON

curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @query-aggs.json
```

### Résultat attendu

| Service | Événements | Moyenne ms | Max ms | Erreurs | Enregistrements |
|---|---:|---:|---:|---:|---:|
| access-exporter | 4 | 1675 | 5000 | 1 | 750 |
| movies-api | 4 | 1612,5 | 5000 | 1 | 2900 |
| ratings-worker | 3 | 900 | 2200 | 1 | 700 |

### Explication

Le filtre de la requête s’applique aux documents et aux agrégations. `size: 0` supprime les hits de la réponse, mais laisse calculer les agrégations.

Une sous-agrégation `filter` possède son propre `doc_count`, ici le nombre d’erreurs du service.

### Point de contrôle

Les nombres d’événements par service totalisent onze et les erreurs trois.

### Dépannage

Sur de gros index multi-shards, `terms` fournit un top de buckets, pas toujours un inventaire exhaustif avec des comptes exacts. Examiner les champs d’erreur et `sum_other_doc_count`. Pour parcourir toutes les clés, étudier une agrégation composite plutôt qu’augmenter sans limite `size`.

## 8. Créer une chronologie avec date_histogram

### Objectif

Compter les événements par fenêtres de cinq minutes en UTC.

### Commande

```bash
curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":0,
    "query":{"bool":{"filter":[
      {"term":{"environment":"formation"}},
      {"range":{"@timestamp":{"gte":"2026-11-03T08:00:00Z","lt":"2026-11-03T08:15:00Z"}}}
    ]}},
    "aggs":{"chronologie":{
      "date_histogram":{
        "field":"@timestamp",
        "fixed_interval":"5m",
        "time_zone":"UTC",
        "min_doc_count":0
      }
    }}
  }'
```

### Résultat attendu

08:00 → 5 événements ; 08:05 → 5 ; 08:10 → 1.

### Explication

Une fenêtre fixe de cinq minutes n’est pas la même chose qu’un intervalle calendaire. Les limites temporelles explicites évitent la dépendance à l’heure réelle de la formation.

`min_doc_count: 0` autorise des buckets vides entre les limites effectivement couvertes. Pour imposer une plage au-delà des données, considérer `extended_bounds`, tout en gardant le filtre de temps : les bounds ne remplacent pas le filtrage des documents.

## 9. Mesurer une latence et compter les exécutions

### Objectif

Comprendre les limites des percentiles et des comptages distincts.

### Commande

```bash
curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":0,
    "query":{"term":{"environment":"formation"}},
    "aggs":{
      "latences":{"percentiles":{"field":"duration_ms","percents":[50,95,99]}},
      "executions_distinctes":{"cardinality":{"field":"run_id","precision_threshold":100}}
    }
  }'
```

### Résultat attendu

Les percentiles sont retournés et le comptage distinct est attendu proche de onze sur ce petit corpus. Ne pas présenter ce paramètre comme une garantie générale d’exactitude.

### Explication

`cardinality` est un comptage approximatif. `precision_threshold` ajuste le compromis précision/mémoire, sans transformer l’algorithme en comptage exact garanti.

Les percentiles ne sont pas des moyennes et leur calcul peut aussi être approximatif. Sur onze observations, leur interprétation statistique est très limitée.

Ici, une ligne correspond volontairement à une exécution. Dans des logs réels, une exécution produit souvent plusieurs lignes : compter les événements n’est pas compter les exécutions ni mesurer directement un taux de réussite métier.

## 10. Pagination simple : from et size

### Objectif

Afficher deux pages de trois événements avec un tri stable.

### Première page

```bash
curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "from":0,"size":3,
    "_source":["event_id","@timestamp","service"],
    "sort":[{"@timestamp":"asc"},{"event_id":"asc"}],
    "query":{"term":{"environment":"formation"}}
  }'
```

### Deuxième page

Reprendre la même requête avec `from: 3`.

### Résultat attendu

Page 1 : E001, E002, E003. Page 2 : E004, E005, E006.

### Explication

`from` est un décalage, pas un numéro de page. `from + size` est limité par `index.max_result_window`, généralement 10000 par défaut. Une pagination profonde augmente le travail de collecte et de tri ; ne pas augmenter cette limite par réflexe.

Ce petit exemple montre la mécanique. Le prochain permet une navigation cohérente lorsque l’index évolue.


### Choisir une méthode de pagination

| Méthode | Usage | Limite principale |
|---|---|---|
| from + size | Quelques pages, interface simple | Coût des grands décalages et fenêtre de résultats |
| search_after sans PIT | Parcours si une vue changeante est acceptable | Les refresh peuvent changer les résultats entre appels |
| PIT + search_after | Parcours profond ou export cohérent | Gestion du curseur, durée de vie et fermeture |
| Scroll | Usages historiques ou spécialisés | Pas le premier choix recommandé ici pour une nouvelle pagination profonde |

PIT + search_after n’enlève pas toutes les limites de taille ou de ressources. Le parcours se fait toujours par lots raisonnables. Les trois événements par page du TP servent à voir la mécanique, pas à fixer une taille de production.

## 11. Ouvrir un PIT

### PIT signifie Point In Time

Un PIT conserve une vue de l’état de recherche visible au moment de son ouverture. Les pages suivantes interrogent cette même vue, même si l’index continue à recevoir des écritures.

Pensez à un catalogue consulté à une date de référence : le catalogue vivant évolue, mais votre parcours reste basé sur l’état retenu. C’est une analogie de lecture, pas une copie physique indépendante de toutes les données.

### Pourquoi un tri stable ne suffit pas toujours

Sans PIT, chaque page peut voir un état de recherche différent après un refresh. Un nouveau document, une suppression ou une modification de champ trié peut déplacer les résultats entre deux appels. Un identifiant de départage rend l’ordre déterministe pour un état donné ; il ne fige pas cet état.

```text
Sans PIT : page 1 sur l’état A → écritures + refresh → page 2 sur l’état B
Avec PIT : page 1 sur la vue A → écritures + refresh → page 2 toujours sur la vue A
```

### Garanties et limites

| PIT fait | PIT ne fait pas |
|---|---|
| Maintenir une vue de recherche pour les appels successifs | Bloquer les écritures |
| Préserver le jeu parcouru malgré les refresh ultérieurs | Créer une sauvegarde restaurable |
| Fournir un contexte pour search_after | Stocker votre position de page à votre place |
| Conserver les versions nécessaires à cette vue | Réserver les documents pour une modification métier |

Une mise à jour ou suppression devenue visible après l’ouverture n’est pas appliquée rétroactivement à la vue du PIT. Les nouvelles données attendent une nouvelle recherche hors PIT ou un nouveau PIT.

Le PIT ne transforme pas Elasticsearch en transaction multi-documents avec une horloge transactionnelle globale entre tous les shards. Il s’agit de contextes de lecture sur l’état de recherche visible. Une écriture non encore visible à l’ouverture n’est pas garantie d’y figurer.

### Ne pas confondre avec l’atelier 04

- OCC : autoriser une écriture seulement si le document n’a pas changé depuis sa lecture.
- PIT : garder une vue stable pour un parcours de lecture.
- Un document vu dans un PIT peut déjà avoir changé dans l’index vivant ; le PIT n’autorise pas à écraser son état courant sans contrôle.

### PIT, curseur et page

```text
pit.id       = dans quelle vue lire ?
sort         = dans quel ordre parcourir ?
search_after = après quel dernier document reprendre ?
size         = combien de documents demander à cet appel ?
```

Le PIT seul n’est pas le curseur. Une application conserve le dernier tableau sort et le PIT ID le plus récent pour demander la suite. search_after est un parcours séquentiel, pas un accès direct gratuit à la page 500 sans curseur précédent. Une interface « précédent » doit conserver les curseurs utiles ou adopter une stratégie dédiée.

### Ressources et durée de vie

keep_alive=5m signifie : conserver suffisamment longtemps le contexte jusqu’au prochain appel. Cela ne signifie ni attendre cinq minutes ni arrêter l’export après exactement cinq minutes. Chaque recherche peut prolonger sa durée ; la valeur doit couvrir le délai de traitement et d’attente avant l’appel suivant.

Le PIT retient des segments et des ressources de lecture ; des mises à jour/suppressions peuvent augmenter le suivi des versions nécessaires. Beaucoup de PIT longs peuvent peser sur les fichiers ouverts, le disque et la mémoire. Fermer dès la fin et choisir une durée raisonnable.

Si le PIT expire ou devient inutilisable après une panne de shard, ne pas ouvrir silencieusement un nouveau PIT au milieu d’un export annoncé cohérent. Recommencer proprement avec un nouveau contexte et un nouveau fichier.



### Objectif

Conserver une vue cohérente pour plusieurs recherches successives.

### Commandes

```bash
curl -X POST "$ES_URL/atelier07-events/_pit?keep_alive=5m&allow_partial_search_results=false" -o pit-open.json

export PIT_ID=$(python3 -c 'import json; print(json.load(open("pit-open.json"))["id"])')
test -n "$PIT_ID" && echo 'PIT ouvert'
```

### Résultat attendu

Un identifiant PIT est disponible.

### Explication

Le PIT est une vue légère de l’état de recherche, pas une sauvegarde et pas un verrou empêchant les écritures. Les documents nouvellement rendus visibles après son ouverture ne viennent pas modifier le jeu parcouru par ce PIT.

`keep_alive` doit couvrir le délai avant la prochaine requête ; chaque recherche peut prolonger la durée. Les PIT retiennent des ressources et doivent être fermés dès la fin du traitement.

### Dépannage

Un PIT expiré ne se réutilise pas. Pour un export cohérent, recommencer depuis un nouveau PIT et une nouvelle sortie plutôt que reprendre aveuglément un ancien curseur.

## 12. Lire la première page PIT

### Objectif

Construire une requête valide sans difficulté de guillemets shell.

### Commandes

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path
query = {
    'size': 3,
    'track_total_hits': True,
    '_source': ['event_id', '@timestamp', 'service', 'run_id'],
    'pit': {'id': os.environ['PIT_ID'], 'keep_alive': '5m'},
    'sort': [{'@timestamp': 'asc'}, {'event_id': 'asc'}, {'_shard_doc': 'asc'}],
    'query': {'term': {'environment': 'formation'}}
}
Path('page1-request.json').write_text(json.dumps(query), encoding='utf-8')
PY

curl -X POST "$ES_URL/_search?allow_partial_search_results=false" -H 'Content-Type: application/json' \
  --data-binary @page1-request.json -o page1-response.json

python3 -m json.tool page1-response.json
```

### Résultat attendu

E001, E002, E003. Chaque hit contient un tableau `sort` à trois valeurs : timestamp de tri, `event_id`, départage technique `_shard_doc`.

### Explication

- Avec PIT, l’URL de recherche est `/_search`, sans nom d’index.
- `_shard_doc` est ajouté implicitement aux recherches triées avec PIT ; il est écrit explicitement ici pour rendre les trois valeurs visibles dans le support.
- Cette valeur technique est stable pour le document dans le PIT, mais ce n’est ni son `_id` ni un champ métier.
- Le format de tri du timestamp peut être numérique : ne pas le convertir manuellement.

### Point de contrôle

Lire exactement `hits.hits[-1].sort`. Ne pas inventer un curseur à partir de `_source`.

## 13. Lire la page suivante avec le curseur complet

### Comprendre le départage _shard_doc

Plusieurs événements peuvent avoir le même timestamp. event_id fournit un départage métier explicite et _shard_doc un départage technique unique et stable dans le PIT.

Ce dernier combine une référence de shard dans le PIT et un ID Lucene interne. Ce n’est ni _id, ni _seq_no, ni le numéro de page, et il n’est pas réutilisable comme identifiant métier hors de ce contexte.

Copier les valeurs de hits.hits[-1].sort exactement, avec leur type JSON et dans leur ordre. Ne pas convertir le timestamp en chaîne, ne pas retirer la dernière valeur et ne pas reconstruire le curseur depuis _source.



### Objectif

Réutiliser tous les critères de tri et l’identifiant PIT le plus récent.

### Commandes

```bash
python3 - <<'PY'
import json
from pathlib import Path
request = json.loads(Path('page1-request.json').read_text())
response = json.loads(Path('page1-response.json').read_text())
if response.get('timed_out') or response.get('_shards', {}).get('failed', 0):
    raise SystemExit('Reponse partielle : ne pas avancer la pagination')
hits = response['hits']['hits']
if not hits:
    raise SystemExit('Aucune page suivante')
request['pit']['id'] = response.get('pit_id', request['pit']['id'])
request['search_after'] = hits[-1]['sort']
Path('page2-request.json').write_text(json.dumps(request), encoding='utf-8')
print('search_after =', request['search_after'])
PY

curl -X POST "$ES_URL/_search?allow_partial_search_results=false" -H 'Content-Type: application/json' \
  --data-binary @page2-request.json -o page2-response.json

python3 -m json.tool page2-response.json
```

### Résultat attendu

E004, E005, E006.

### Explication

`search_after` reprend après le dernier document de la page précédente. Garder la même requête et le même tri. Si Elasticsearch renvoie un nouveau `pit_id`, l’utiliser pour l’appel suivant.

Ne pas ajouter `from: 3` : ce n’est pas une combinaison avec le décalage de pagination classique. Pour continuer, reprendre le même principe à partir de la dernière réponse et du dernier curseur.

### Dépannage

- Nombre incorrect de valeurs de tri : copier le tableau entier, y compris `_shard_doc`.
- Duplication : vérifier que le dernier hit de la bonne page est utilisé et que le tri n’a pas changé.
- PIT expiré : recommencer la séquence ; ne pas masquer l’erreur par un nouvel ID au milieu d’un export dont on exige la cohérence.

## 14. Fermer le PIT

### Objectif

Libérer le contexte de recherche dès la fin de l’exercice.

### Commandes

```bash
python3 - <<'PY'
import json
from pathlib import Path
request = json.loads(Path('page2-request.json').read_text())
response = json.loads(Path('page2-response.json').read_text())
pit_id = response.get('pit_id', request['pit']['id'])
Path('pit-close.json').write_text(json.dumps({'id': pit_id}), encoding='utf-8')
PY

curl -X DELETE "$ES_URL/_pit?pretty" -H 'Content-Type: application/json' \
  --data-binary @pit-close.json
```

### Résultat attendu

Une réponse indiquant le succès de la fermeture. Le nombre de contextes libérés dépend du PIT et du cluster.

### Dépannage

Si une étape précédente a échoué, utiliser le dernier ID connu valide. Ne pas laisser des PIT ouverts en répétant l’exercice sans nettoyage.

## 15. Exporter toutes les pages avec Python standard — prolongement

### Objectif

Automatiser PIT + search_after sans client supplémentaire et produire une preuve d’export complet.

### Commande

```bash
cat > export_pit.py <<'PY'
import argparse
import base64
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

p = argparse.ArgumentParser(description='Export du laboratoire avec PIT et search_after')
p.add_argument('--scenario', help='JSON de recherche ; seuls query, sort et _source sont repris')
p.add_argument('--page-size', type=int, default=3)
p.add_argument('--output', default='export-events.ndjson')
a = p.parse_args()
if a.page_size < 1:
    p.error('--page-size doit etre positif')
output = Path(a.output)
partial = output.with_name(output.name + '.partial')
report_path = output.with_name(output.name + '.rapport.json')
if any(path.exists() for path in (output, partial, report_path)):
    p.error('Une sortie existe deja : choisir un nouveau --output')
scenario = json.loads(Path(a.scenario).read_text(encoding='utf-8')) if a.scenario else {}
query = scenario.get('query', {'term':{'environment':'formation'}})
sort = list(scenario.get('sort', [{'@timestamp':'asc'},{'event_id':'asc'}]))
if not any(x == '_shard_doc' or isinstance(x, dict) and '_shard_doc' in x for x in sort):
    sort.append({'_shard_doc':'asc'})
url = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
headers = {'Content-Type':'application/json'}
context = None
if url.startswith('https://'):
    context = ssl.create_default_context(cafile=os.environ['ES_CA'])
    auth = base64.b64encode(('elastic:' + os.environ['ELASTIC_PASSWORD']).encode()).decode()
    headers['Authorization'] = 'Basic ' + auth
elif not url.startswith('http://'):
    p.error('ES_URL doit commencer par http:// ou https://')

def call(method, path, body=None):
    request = urllib.request.Request(
        url+path, data=None if body is None else json.dumps(body).encode(),
        method=method, headers=headers)
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        return json.load(response)

pit_id = None
seen = set()
count = pages = 0
expected = None
pit_closed = False
try:
    opened = call('POST','/atelier07-events/_pit?keep_alive=5m&allow_partial_search_results=false')
    pit_id = opened['id']
    if opened.get('_shards',{}).get('failed',0):
        raise RuntimeError('Ouverture PIT incomplete')
    cursor = None
    with partial.open('x',encoding='utf-8') as f:
        while True:
            body = {
                'size':a.page_size,'track_total_hits':True,
                'pit':{'id':pit_id,'keep_alive':'5m'},
                'sort':sort,'query':query
            }
            if '_source' in scenario:
                body['_source'] = scenario['_source']
            if cursor is not None:
                body['search_after'] = cursor
            response = call('POST','/_search?allow_partial_search_results=false',body)
            pit_id = response.get('pit_id',pit_id)
            if response.get('timed_out') or response.get('_shards',{}).get('failed',0):
                raise RuntimeError('Recherche partielle : ne pas avancer le curseur')
            total = response['hits']['total']
            if total['relation'] != 'eq':
                raise RuntimeError('Le total doit etre exact pour ce controle')
            if expected is None:
                expected = total['value']
            elif total['value'] != expected:
                raise RuntimeError('Total changeant dans le meme PIT')
            hits = response['hits']['hits']
            if not hits:
                break
            pages += 1
            for hit in hits:
                key = (hit['_index'],hit['_id'])
                if key in seen:
                    raise RuntimeError('Doublon : '+str(key))
                seen.add(key)
                f.write(json.dumps({'_id':hit['_id'],'_source':hit['_source']},ensure_ascii=False)+'\n')
                count += 1
            new_cursor = hits[-1]['sort']
            if new_cursor == cursor:
                raise RuntimeError('Le curseur n avance plus')
            cursor = new_cursor
    if count != expected:
        raise RuntimeError(f'Export incomplet : {count} / {expected}')
    partial.replace(output)
finally:
    if pit_id is not None:
        try:
            closed = call('DELETE','/_pit',{'id':pit_id})
            pit_closed = bool(closed.get('succeeded'))
            if not pit_closed:
                print('Attention : fermeture PIT non confirmee',file=sys.stderr)
        except Exception as exc:
            print('Attention : fermeture PIT non confirmee : '+type(exc).__name__,file=sys.stderr)
report = {'export':str(output),'documents':count,'expected':expected,
          'non_empty_pages':pages,'pit_closed':pit_closed}
report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
PY

python3 -m py_compile export_pit.py
python3 export_pit.py
wc -l export-events.ndjson
```

### Résultat attendu

Onze documents, sans E011, pas de doublon et PIT fermé. Le fichier final n’est créé qu’après le contrôle de complétude ; la sortie intermédiaire porte le suffixe .partial. Un rapport indique aussi si la fermeture PIT est confirmée.

### Explication

Le programme refuse de remplacer un fichier de sortie, un fichier .partial ou un rapport déjà présent : choisir un nouveau nom pour rejouer un export.

Le programme est dimensionné pour ce laboratoire : le set de contrôle des identifiants conserve toutes les clés en mémoire et `track_total_hits: true` est redemandé à chaque page. Pour un export massif, optimiser ces points et concevoir la reprise sur erreur.

Ne pas modifier silencieusement le PIT en cas d’expiration : un nouveau PIT représente un autre état. Si l’on redémarre, produire un nouvel export et contrôler sa cohérence.

Le fichier exporté contient `_id` et `_source`, mais pas les lignes d’action Bulk : il n’est donc pas directement un fichier de réimport `_bulk`.

## 16. Défi final

### Énoncé

Produire un dossier d’investigation qui :

1. sélectionne l’environnement `formation` et la fenêtre 08:00–08:15 UTC du corpus ;
2. conserve les niveaux WARN ou ERROR ;
3. trie par durée décroissante puis identifiant ;
4. affiche uniquement les champs nécessaires au diagnostic ;
5. calcule le nombre d’événements, la durée moyenne et le maximum par pipeline ;
6. exporte ces cinq événements avec PIT + search_after, deux par page ;
7. confirme absence de doublons et fermeture du PIT.

## 17. Corrigé du défi

### Requête

```bash
cat > defi-query.json <<'JSON'
{
  "size":10,
  "track_total_hits":true,
  "_source":["event_id","@timestamp","pipeline_id","run_id","level","message","duration_ms"],
  "sort":[{"duration_ms":"desc"},{"event_id":"asc"}],
  "query":{"bool":{"filter":[
    {"term":{"environment":"formation"}},
    {"terms":{"level":["WARN","ERROR"]}},
    {"range":{"@timestamp":{"gte":"2026-11-03T08:00:00Z","lt":"2026-11-03T08:15:00Z"}}}
  ]}},
  "aggs":{"par_pipeline":{
    "terms":{"field":"pipeline_id","size":10,"order":{"_key":"asc"}},
    "aggs":{
      "moyenne_ms":{"avg":{"field":"duration_ms"}},
      "maximum_ms":{"max":{"field":"duration_ms"}}
    }
  }}
}
JSON

curl -X POST "$ES_URL/atelier07-events/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @defi-query.json
```

### Résultats attendus

Ordre : E003, E008, E006, E002, E005.

| Pipeline | Événements | Moyenne ms | Maximum ms |
|---|---:|---:|---:|
| access_logs | 1 | 5000 | 5000 |
| ratings | 2 | 1250 | 2200 |
| movies | 2 | 3100 | 5000 |

### Export corrigé complet

Le même exporteur lit le bloc query et le tri du fichier du défi. Il ne reprend pas ses agrégations à chaque page et ajoute le départage _shard_doc si nécessaire :

```bash
python3 export_pit.py --scenario defi-query.json \
  --page-size 2 --output export-defi.ndjson
```

Cette commande fonctionne en HTTP simple ou avec les variables HTTPS de la section 2. Aucun package Python supplémentaire n’est requis.

### Résultat attendu

Cinq documents : E003, E008, E006, E002, E005 ; trois pages non vides (2 + 2 + 1), puis une réponse vide termine la boucle. Le rapport doit indiquer documents=5, expected=5, non_empty_pages=3 et pit_closed=true.

Le fichier exporté contient _id et _source, pas les lignes d’action Bulk de l’atelier 03. Il ne se réimporte donc pas directement avec _bulk.

### Explication du script

| Partie | Utilité |
|---|---|
| --scenario | Réutilise le besoin de recherche sans recopier le code de pagination |
| --page-size | Fixe la taille des lots, indépendamment du size du scénario |
| Contrôle d’existence des sorties | Évite de remplacer silencieusement un précédent export |
| Réponse partielle / total | Refuse d’annoncer un export complet en cas d’échec de recherche |
| set seen | Détecte les IDs répétés pendant ce petit lab |
| Dernier sort | Déplace le curseur après la page traitée |
| Nouveau pit_id | Poursuit dans le contexte fourni le plus récemment |
| finally | Tente la fermeture même si une étape échoue |
| Rapport | Distingue contenu exporté et fermeture confirmée |

Une erreur conserve éventuellement un fichier .partial, jamais à présenter comme complet. Choisir un nouveau --output pour recommencer ; ne pas réutiliser le curseur d’un PIT expiré.

## 18. Synthèse et pièges à éviter

| Piège | Bonne pratique |
|---|---|
| `should` supposé obligatoire | Définir explicitement le seuil selon le besoin |
| Agréger un champ text | Utiliser un champ keyword ou numérique approprié |
| Confondre `size` et total | Lire `hits.total`, puis la taille réelle de `hits.hits` |
| Confondre logs et exécutions | Définir l’unité métier de comptage |
| Attendre une cardinalité exacte garantie | Connaître son caractère approximatif |
| Augmenter le result window pour tout exporter | Employer PIT + search_after |
| Oublier la troisième valeur de sort | Copier l’intégralité du tableau retourné |
| Réutiliser un ancien PIT ID | Conserver le dernier ID renvoyé |
| Laisser les PIT ouverts | Fermer en fin de traitement et sur erreur |
| Export partiel annoncé complet | Vérifier timeouts, shards, total et doublons |

## 19. Livrables, conservation et suite

Conserver le mapping, le corpus, les requêtes JSON, les réponses utiles, l’export et une synthèse des résultats. Ne pas partager les secrets.

L’atelier 08 utilisera ces événements pour créer une Data View, explorer les champs et construire un dashboard Kibana. Conserver donc l’index `atelier07-events`.

Suppression facultative, uniquement après accord du formateur :

```bash
curl -X DELETE "$ES_URL/atelier07-events?pretty"
```

## 20. Références et validation formateur

Alignement : programme fourni, jour 3, atelier 7 — requêtes booléennes, agrégations et pagination profonde.

Documentation Elastic : Boolean query, Terms aggregation, Cardinality aggregation, Date histogram, Paginate search results, Open/Close point in time.

Les JSON et exemples Python ont été vérifiés syntaxiquement ; les chiffres ont été recalculés depuis le corpus. L’exporteur a été testé avec des réponses HTTP simulées pour le parcours complet, le défi et un échec partiel, notamment la rotation des IDs PIT et la fermeture du dernier contexte. Il n’a pas été exécuté contre Elasticsearch pendant la génération. Les chiffres attendus sont dérivés du corpus pédagogique présenté ; valider l’exécution complète sur les versions retenues avant la session.
