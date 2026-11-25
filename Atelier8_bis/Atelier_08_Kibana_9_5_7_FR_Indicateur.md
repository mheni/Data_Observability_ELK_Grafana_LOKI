# Atelier 08 — Construire son premier tableau de bord Kibana, puis créer des alertes

Version cible : Kibana et Elasticsearch 9.5.7 — parcours débutant, puis approfondissement.


## 0. Lecture obligatoire — faisabilité vérifiée sur les fichiers fournis

Cette révision conserve les clics détaillés du support 9.5.7 mais corrige les dépendances aux données. Les tests locaux ont exécuté le convertisseur fourni sur `access_log_actualise.txt`, puis vérifié la cohérence des champs avec le mapping destination. Aucun pipeline Painless ni écran Kibana n’a été exécuté sur un cluster pendant cet audit.

### 0.1 Résultats mesurés, pas des hypothèses

| Indicateur | Les 1 000 premières lignes, import par défaut de l’atelier 3 |
|---|---:|
| Documents préparés | 1 000 |
| Rejets de préparation | 0 |
| Statuts 200 / 301 / 304 | 881 / 71 / 18 |
| Statuts 403 / 404 | 2 / 28 |
| Statuts 5xx | 0 |
| Méthode absente | 0 |
| Taille absente | 341 |
| Somme des octets connus | 9 614 598 |
| IP distinctes, calcul exact local | 154 |
| Première date UTC | 2026-11-22 18:51:30 |
| Dernière date UTC | 2026-11-22 18:51:35 |

Les résultats concernent le fichier joint, avec le script joint et `--limit 1000`. Un autre import, un fichier modifié ou un index déjà rempli peut produire d’autres chiffres. La cardinalité Lens est une estimation, contrairement au comptage exact local ci-dessus.

Le fichier complet contient 102 972 lignes reconnues par la regex, couvre seulement dix minutes (18:51:30 à 19:01:30 UTC) et contient 248 statuts 500. Il ne contient pas plusieurs heures ou plusieurs jours d’historique. Charger tout le fichier ne résout donc pas l’exercice de comparaison H-1. Le test complet a vérifié les correspondances de format et les dates ; il n’a pas indexé les documents.

### 0.2 Choix pédagogiques :

- Socle : conserver les 1 000 documents de l’atelier 3, les statuts 5xx à zéro et les dates originales.
- Histogrammes et carte thermique : minimum de 1 seconde pour cet échantillon, pas cinq minutes ou une heure.
- Comparaison temporelle : décalage de 3 secondes sur deux fenêtres couvertes par le corpus, pas H-1.
- Erreurs : les 30 réponses 4xx permettent réellement l’investigation ; ne pas exiger un 5xx dans les vrais logs importés.
- Alertes : événements récents synthétiques dans `atelier08-alert-demo`, jamais dans les KPI réels.
- Cartographie : utiliser les six points produits par le script fourni ; aucun besoin de GeoIP pour le parcours principal.
- GeoIP réel, notifications externes et interface d’alerting : modules conditionnels à vérifier avant la séance.

### 0.3 Fichiers, résultats générés et services

| Élément | Disponible ? | Action |
|---|---|---|
| Scripts d’import et mapping de l’atelier 3 | Inclus dans le pack corrigé | Réutiliser pour créer la source si nécessaire |
| Fichier de logs `access_log_actualise.txt` | Déjà fourni séparément | Copier dans le dossier de travail ; non dupliqué dans le pack |
| `atelier03-access` | Non vérifiable hors cluster | Exécuter `_count` ; importer si absent |
| `atelier08-access` | Non vérifiable hors cluster | Créer avec le mapping puis réindexer |
| `access-bornes.json` | Résultat à générer | Ne pas le confondre avec `access-bornes-query.json` |
| `geo-demo.ndjson` | Résultat à générer | Exécuter `preparer_geo_demo.py` après les bornes |
| `status_class`, `url_path` | Produits par le pipeline de l’atelier 8 | Ne pas chercher ces champs dans l’index source |
| Coordonnées des vrais logs | Absentes avant enrichissement | Carte de simulation dans une autre vue de données |
| Base GeoIP / SMTP / connecteur externe | Non fournis et non garantis | Ne pas rendre le socle dépendant de ces services |
| `validation_atelier08.json` d’origine | Bilan statique, pas preuve cluster | Le bilan corrigé s’appelle `validation_locale.json` |

Les documents `access-base-pipeline.json`, `access-reindex.json`, `access-tableau de bord-mapping.json` sont cohérents : tous les champs projetés et ajoutés sont déclarés. Le filtre `_source` de la réindexation est indispensable car le mapping destination est strict. Ne pas le retirer : `referrer`, `protocol`, `source_file_sha256` et `line_number` ne sont pas prévus dans la destination. [file:75][file:83][file:84][file:85]

### 0.4 Préparer le dossier sans fichier manquant

1. Extraire le pack corrigé dans un dossier de travail de la VM.
2. Copier le fichier de logs joint dans ce même dossier sous son nom `access_log_actualise.txt`.
3. Ouvrir un terminal dans ce dossier. Toutes les commandes qui lisent `@fichier.json` se lancent depuis ce dossier.
4. Définir `ES_URL` comme dans l’atelier 1. Ne pas écraser une URL HTTPS par HTTP si votre cluster est sécurisé.
5. Vérifier les fichiers :

```bash
pwd
ls access_log_actualise.txt access-mapping.json access_vers_ndjson.py verifier_bulk.py
ls access-dashboard-mapping.json access-base-pipeline.json access-reindex.json
ls access-bornes-query.json access-validation-query.json preparer_geo_demo.py
```

Si vous changez ensuite de répertoire, les fichiers n’y apparaissent pas automatiquement : copier les fichiers ou revenir dans ce dossier.

### 0.5 Si l’import de l’atelier 3 n’a pas été fait

Vérifier d’abord dans Console :

```http
GET atelier03-access/_count
```

- Index déjà rempli : conserver son contenu et poursuivre avec les contrôles de section 4.
- Index absent : appliquer le mapping avec la première commande ci-dessous.
- Index existant mais vide : inspecter `_mapping` ; si compatible, sauter la commande de création et importer.
- Mapping incompatible ou données d’une autre session : arrêter et convenir d’un index distinct  ; ne pas supprimer automatiquement.

Terminal, cas d’un index absent, avec les options de sécurité de l’atelier 1 si nécessaires :

```bash
curl --fail-with-body -sS -X PUT "$ES_URL/atelier03-access" \
  -H 'Content-Type: application/json' --data-binary @access-mapping.json

python3 access_vers_ndjson.py access_log_actualise.txt access.ndjson --limit 1000
cat access-preparation.json
```

Vérifier `documents: 1000`, `rejected: 0` pour le fichier joint. Si le bilan diffère, lire les rejets ; ne pas poursuivre avec zéro document.

```bash
curl --fail-with-body -sS -X POST "$ES_URL/atelier03-access/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @access.ndjson \
  -o access-bulk-response.json

python3 verifier_bulk.py access-bulk-response.json --preparation access-preparation.json
curl --fail-with-body -sS "$ES_URL/atelier03-access/_count?pretty"
```

Les mêmes identifiants sont stables pour un fichier inchangé. Une autre version du fichier change les identifiants : ne pas mélanger les sessions si vous souhaitez retrouver les références exactes de cet audit. [file:79]

## 1. Fiche pédagogique et organisation

| Élément | Contenu |
|---|---|
| Public | Participants débutants dans Kibana |
| Socle guidé | 4 h à 5 h, avec pauses et vérifications |
| Alertes | 1 h à 1 h 30 supplémentaire |
| Approfondissements | 1 h à 2 h selon les options |
| Source | `atelier03-access`, import des access logs de l’atelier 3 |
| Destination principale | `atelier08-access` |
| Livrables | Tableau de bord enregistré, investigation Découvrir, règle testée, bilan de validation |
| Outils | Console, Découvrir, Vues de données, Lens, Tableaux de bord, Règles, Cartes |

Ce support remplace le précédent atelier 08. Il conserve le corpus access logs et détaille les manipulations de l’interface. Il ne nécessite pas de réaliser la partie MovieLens de l’atelier 3. 

### Conventions de lecture

- `Cliquer` : clic gauche sur un bouton ou un menu.
- `Saisir` : remplacer le contenu d’un champ par le texte indiqué.
- `Glisser-déposer` : maintenir le clic sur un champ de la liste de gauche, déplacer le champ vers la zone indiquée, puis relâcher.
- `Console` : ouvrir Outils de développement → Console. Ne pas coller les commandes `curl` dans Console.
- `Terminal` : shell Linux de la VM, pas la barre de recherche de Kibana.
- Les consignes d’interface sont en français. Le type de graphique de valeur unique est nommé « Indicateur » dans votre interface. Les noms techniques et les expressions à copier restent inchangés.
- La navigation dépend de la solution sélectionnée et des droits. Pour trouver une application, utiliser la recherche globale en haut de Kibana : saisir `Découvrir`, `Tableaux de bord`, `Vues de données`, `Règles` ou `Outils de développement`, puis cliquer le résultat de navigation.

### Note de compatibilité

La cible demandée est 9.5.7. Les procédures s’appuient sur la documentation officielle actuelle et les fichiers du parcours ; elles n’ont pas été exécutées sur votre instance. Les variantes de libellés utiles sont indiquées, sans prétendre que chaque bouton occupe une position identique dans tous les déploiements. Ne pas confondre le mode Lens « Pointer-cliquer » avec le mode « Requête ». Le socle utilise Pointer-cliquer et KQL.

### Consigne avant la séance

1. Vérifier les droits de création des Vues de données, tableaux de bord et visualisations.
2. Vérifier que `atelier03-access` est rempli et que `status` est numérique.
3. Réserver un Space de formation et un nom de règle par binôme.
4. Tester séparément les prérequis d’alerting : ne pas découvrir à cette étape que la sécurité ou la clé de chiffrement manque.
5. Prévoir une session distincte pour les extensions si le groupe découvre totalement Kibana.
6. Ne jamais supprimer automatiquement un index existant pour faire réussir un exercice.

## 2. Comprendre le résultat et les langages

Une ligne du log représente une requête journalisée, pas un utilisateur. Le tableau de bord montre des volumes, statuts et tailles ; le corpus ne contient pas de durée de réponse permettant de calculer une latence HTTP. [file:38]

```text
access_log → atelier 3 : Python + Bulk → atelier03-access
                                           │
                                 copie + pipeline
                                           ▼
                                    atelier08-access
                                           │
                            Data View → Discover → Lens
                                           ▼
                                   Dashboard Kibana
```

| Zone de saisie | Langage | Exemple |
|---|---|---|
| Barre Découvrir en mode vue de données | KQL | `status >= 500 and status < 600` |
| Dimension Lens, onglet Formule | Formule Lens | `count(kql='status >= 500 and status < 600')` |
| Console | API Elasticsearch + JSON | `GET atelier08-access/_count` |
| Découvrir, mode ES|QL | ES|QL | `FROM atelier08-access | STATS n = COUNT(*)` |

La requête `status >= 500 and status < 600` est valide en KQL. Zéro résultat ne prouve pas une erreur de syntaxe : il peut simplement n’exister aucun 5xx dans l’échantillon ou dans la période sélectionnée. Le diagnostic de la section 6 doit être réalisé avant de changer les formules. 

## 3. Préparer les données : connexion, contrôles et projection

### Objectif

Réutiliser l’installation de l’atelier 01. Aucun cluster ni collecteur supplémentaire n’est nécessaire pour le tableau de bord. Le module alertes exige une configuration Kibana compatible, à vérifier avant la séance.

### Accès Kibana

Si un tunnel SSH est nécessaire :

```bash
ssh -N -L 5601:127.0.0.1:5601 utilisateur@IP_PUBLIQUE_VM
```

Garder le tunnel ouvert et utiliser l’adresse Kibana définie à l’atelier 01, généralement :

```text
http://localhost:5601
```

Ne pas exposer Kibana publiquement pour contourner un problème d’accès. La session et les droits dépendent du mode sécurisé ou non retenu dans le lab.

### Commandes Console

Dans Kibana → Outils de développement → Console, saisir méthode, chemin et JSON, pas une commande curl. Console utilise la connexion configurée de Kibana à Elasticsearch.

### Commandes curl depuis la VM

```bash
# Se placer dans le dossier extrait contenant les fichiers JSON et Python.
# Variante sans sécurité uniquement :
export ES_URL='http://localhost:9200'
```

Si la variante sécurisée est active : utiliser ES_URL en HTTPS, ES_CA et ELASTIC_PASSWORD comme précédemment, puis ajouter après chaque curl Elasticsearch :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Ne pas ajouter ces options dans Console ni dans les scripts Python. Ne pas utiliser -k.

## 4. Contrôler le corpus existant avant de créer un tableau de bord

### Objectif

Ne pas construire des indicateurs sur un index vide, un texte brut non parsé ou des types incompatibles.

### Console

```http
GET atelier03-access/_count
GET atelier03-access/_mapping
POST atelier03-access/_search
{
  "size": 3,
  "sort": [{"@timestamp":"asc"}],
  "_source":["@timestamp","client_ip","method","path","status","bytes","message"]
}
```

### Résultat attendu et explication

Des documents avec @timestamp date, status numérique, bytes numérique lorsqu’il est connu, méthode et chemin lorsque la requête a été reconnue.

Le support suppose les champs de l’atelier 03 simplifié. Si vous utilisez l’index Logstash de l’atelier 01 avec un autre schéma, inspecter ses champs et adapter explicitement la projection ci-dessous. Ne pas remplacer aveuglément status par un champ ECS sans vérifier son mapping.

Si seuls message et @timestamp existent, reprendre le parsing avant les visualisations structurées. Ne pas créer un index vide du bon nom pour masquer l’absence de données.

### Point de contrôle

Le participant identifie la période réelle, le nombre de documents et les champs numériques. Le jeu peut être limité aux 1 000 lignes de l’atelier 03 : ne pas présenter ce sous-ensemble comme tout le trafic du serveur.

## 5. Créer une projection dédiée au tableau de bord

### Objectif

Préserver atelier03-access et ajouter des champs explicables pour les regroupements et la qualité.

Les fichiers JSON complets sont joints à l’atelier. Dans le dossier contenant ces fichiers :

```bash
curl --fail-with-body -sS -X PUT "$ES_URL/atelier08-access" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json

curl --fail-with-body -sS -X PUT "$ES_URL/_ingest/pipeline/atelier08-access-base" \
  -H 'Content-Type: application/json' --data-binary @access-base-pipeline.json
```
Cette requête crée ou remplace un pipeline d’ingestion nommé atelier08-access-base dans Elasticsearch.

Elle enregistre les traitements décrits dans le fichier access-base-pipeline.json. Elle n’insère aucun log, ne lance pas la réindexation et ne modifie pas les documents déjà présents. Dans votre atelier, ce pipeline sera utilisé ensuite par la requête de réindexation.


### Mapping de référence

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "event_id": {
        "type": "keyword"
      },
      "@timestamp": {
        "type": "date"
      },
      "ingested_at": {
        "type": "date"
      },
      "ingest_delay_ms": {
        "type": "long"
      },
      "client_ip": {
        "type": "keyword"
      },
      "method": {
        "type": "keyword"
      },
      "path": {
        "type": "keyword",
        "ignore_above": 4096
      },
      "url_path": {
        "type": "keyword",
        "ignore_above": 4096
      },
      "status": {
        "type": "integer"
      },
      "status_class": {
        "type": "keyword"
      },
      "is_http_error": {
        "type": "boolean"
      },
      "bytes": {
        "type": "long"
      },
      "message": {
        "type": "text"
      },
      "request_line": {
        "type": "text"
      },
      "user_agent": {
        "type": "text"
      },
      "service": {
        "type": "keyword"
      },
      "environment": {
        "type": "keyword"
      },
      "dataset": {
        "type": "keyword"
      },
      "geo_source": {
        "type": "keyword"
      },
      "client_geo": {
        "properties": {
          "country_iso_code": {
            "type": "keyword"
          },
          "country_name": {
            "type": "keyword"
          },
          "city_name": {
            "type": "keyword"
          },
          "location": {
            "type": "geo_point"
          }
        }
      },
      "tags": {
        "type": "keyword"
      }
    }
  }
}
```

### Comprendre les nouveaux champs

| Champ | Explication |
|---|---|
| event_id | Copie de l’ID du document source pour l’investigation |
| status_class | 2xx, 3xx, 4xx, 5xx… pour les regroupements |
| is_http_error | Vrai pour les statuts 400 à 599 |
| url_path | Chemin sans query string, pour limiter la cardinalité et l’exposition de paramètres |
| ingested_at | Heure d’ingestion de cette projection |
| ingest_delay_ms | Écart entre événement et ingestion de la projection |
| dataset | Identifie le corpus réel, séparément des démonstrations |
| client_geo.location | geo_point réservé à l’enrichissement/carte |

Le mapping est explicite : un objet contenant deux nombres ne devient pas automatiquement un geo_point. Les champs keyword servent aux agrégations ; message reste text pour la recherche et le détail documentaire.

### Pipeline de préparation

```json
{
  "description": "Classification et trace ingestion du corpus access_log atelier08",
  "processors": [
    {
      "set": {
        "field": "ingested_at",
        "value": "{{{_ingest.timestamp}}}"
      }
    },
    {
      "set": {
        "field": "service",
        "value": "web-formation"
      }
    },
    {
      "set": {
        "field": "environment",
        "value": "formation"
      }
    },
    {
      "set": {
        "field": "dataset",
        "value": "access_log_reel"
      }
    },
    {
      "script": {
        "lang": "painless",
        "source": "if (ctx.status != null) { int s = Integer.parseInt(ctx.status.toString()); ctx.status = s; ctx.status_class = s >= 100 && s < 600 ? Integer.toString((int)(s / 100)) + 'xx' : 'autre'; ctx.is_http_error = s >= 400 && s < 600; } if (ctx.path != null) { String p = ctx.path.toString(); int q = p.indexOf('?'); ctx.url_path = q >= 0 ? p.substring(0, q) : p; } if (ctx['@timestamp'] != null) { ctx.ingest_delay_ms = java.time.Duration.between(java.time.ZonedDateTime.parse(ctx['@timestamp']), java.time.ZonedDateTime.parse(ctx.ingested_at)).toMillis(); }"
      }
    }
  ]
}
```

Le pipeline classe les statuts et retire la query string de path sans analyser toute la sémantique d’une URL. Il conserve message, donc les données sensibles du log peuvent toujours s’y trouver : ne pas diffuser les résultats sans examen.

ingested_at mesure l’arrivée dans cette projection, pas nécessairement la première ingestion réelle du serveur. Sur une archive de 2017 rejouée aujourd’hui, ingest_delay_ms sera très élevé par construction. Ne pas en faire un SLI de retard de collecte en production.

### Contrôle bloquant avant la réindexation : tester le pipeline sur Elasticsearch

Le pack contient `access-simulate.json`, construit à partir de trois vraies lignes du fichier joint. La commande suivante teste le pipeline enregistré sans indexer ces documents :

```bash
curl --fail-with-body -sS -X POST "$ES_URL/_ingest/pipeline/atelier08-access-base/_simulate" \
  -H 'Content-Type: application/json' --data-binary @access-simulate.json \
  -o access-simulate-response.json
python3 verifier_resultat_atelier08.py simulate access-simulate-response.json
```

Attendu : chaque résultat contient un document transformé, un `status_class`, un `url_path` et un `ingested_at`. Si un élément contient `error`, arrêter et corriger avant `_reindex` même si HTTP vaut 200. Ce contrôle est nécessaire car un test Python ne compile pas Painless et ne prouve pas le fonctionnement du pipeline sur votre version.

### Réindexer sans modifier la source

```bash
curl --fail-with-body -sS -X POST "$ES_URL/_reindex?refresh=true" \
  -H 'Content-Type: application/json' --data-binary @access-reindex.json \
  -o access-reindex-response.json
python3 -m json.tool access-reindex-response.json
python3 verifier_resultat_atelier08.py reindex access-reindex-response.json
```

Corps envoyé :

```json
{
  "source": {
    "index": "atelier03-access",
    "_source": [
      "@timestamp",
      "client_ip",
      "method",
      "path",
      "status",
      "bytes",
      "message",
      "request_line",
      "user_agent"
    ]
  },
  "dest": {
    "index": "atelier08-access",
    "pipeline": "atelier08-access-base",
    "op_type": "create"
  },
  "script": {
    "lang": "painless",
    "source": "ctx._source.event_id = ctx._id;"
  }
}
```

La sélection _source évite de recopier des champs non prévus par le mapping strict. L’ID est conservé et event_id l’expose dans les colonnes. op_type:create détecte les collisions ; cette commande n’est pas à rejouer aveuglément dans une destination déjà remplie.

Contrôler timed_out=false, failures vide, aucun conflit et created égal au volume source attendu. _reindex n’est pas une transaction globale : un échec peut laisser une destination partiellement alimentée. Diagnostiquer avant toute relance ou suppression.

### Point de contrôle

```http
GET atelier08-access/_count
POST atelier08-access/_search
{
  "size":3,
  "_source":["event_id","@timestamp","status","status_class","path","url_path","ingested_at","ingest_delay_ms"]
}
```

Si la destination existe avec un ancien schéma, inspecter avant de poursuivre. Ne pas supprimer les index source ni les index système Kibana.


## 6. Établir une référence fiable et diagnostiquer « aucun résultat »

Objectif : connaître les données avant de créer des graphiques. Cette étape se fait dans Console et ne dépend pas du filtre temporel de Découvrir.

### 6.1 Ouvrir et utiliser Console

1. Dans la recherche globale Kibana, saisir `Outils de développement`.
2. Ouvrir Outils de développement, puis l’onglet Console.
3. Coller la requête suivante dans la zone de gauche.
4. Cliquer dans la requête.
5. Cliquer sur le triangle d’exécution associé à cette requête.
6. Lire la réponse dans la zone de droite.

```http
GET atelier08-access/_count
```

Si `count` vaut zéro, revenir aux étapes de réindexation. Si l’index est introuvable, revenir à sa création. Ne pas créer une vue de données pour masquer ce prérequis manquant.

### 6.2 Vérifier types, dates et distribution

Exécuter successivement :

```http
GET atelier08-access/_field_caps?fields=status,bytes,@timestamp,status_class
```

Attendu : `status` entier, `bytes` long, `@timestamp` date, `status_class` keyword.

```http
POST atelier08-access/_search
{
  "size": 0,
  "track_total_hits": true,
  "aggs": {
    "premier_evenement": {"min": {"field": "@timestamp"}},
    "dernier_evenement": {"max": {"field": "@timestamp"}},
    "statuts": {"terms": {"field": "status", "size": 100}},
    "classes": {"terms": {"field": "status_class", "size": 10}},
    "statuts_valides": {"filter": {"range": {"status": {"gte": 100, "lt": 600}}}},
    "erreurs_4xx": {"filter": {"range": {"status": {"gte": 400, "lt": 500}}}},
    "erreurs_5xx": {"filter": {"range": {"status": {"gte": 500, "lt": 600}}}},
    "octets_connus": {"sum": {"field": "bytes"}},
    "sans_date": {"missing": {"field": "@timestamp"}},
    "sans_methode": {"missing": {"field": "method"}},
    "sans_taille": {"missing": {"field": "bytes"}}
  }
}
```

Recopier les résultats dans ce tableau :

| Référence | Valeur de votre réponse |
|---|---|
| N = `hits.total.value` | |
| V = `statuts_valides.doc_count` | |
| C = `erreurs_4xx.doc_count` | |
| S = `erreurs_5xx.doc_count` | |
| B = `octets_connus.value` | |
| Date minimale, `value_as_string` | |
| Date maximale, `value_as_string` | |
| Nombre sans date / méthode / taille | |

Ne pas imposer « 1 000 documents » si la préparation de l’atelier 3 a produit des rejets ou si votre corpus diffère. [file:37]

### 6.3 Vérifier directement les 5xx

```http
POST atelier08-access/_count
{
  "query": {
    "range": {"status": {"gte": 500, "lt": 600}}
  }
}
```

- Résultat `0` : l’absence de 5xx est réelle dans cet index à cet instant. Une tuile à zéro est correcte.
- Résultat supérieur à zéro, mais Découvrir vide : vérifier vue de données, période, langage et filtres.
- Champ `status` absent : inspecter un document et revenir au bon index ; ne pas remplacer automatiquement ce champ par un nom ECS.
- Champ mal typé : corriger la préparation et le mapping dans un nouvel index approprié ; une formule Lens ne répare pas le type Elasticsearch.

### 6.4 Distinguer KQL et Lucene

Pour tout le socle, utiliser KQL. Si le sélecteur de langage de la barre affiche Lucene, ouvrir ce sélecteur et choisir KQL. Ne pas passer en mode ES|QL.

Équivalents, uniquement pour comprendre :

```text
KQL     : status >= 500 and status < 600
Lucene  : status:[500 TO 599]
ES|QL   : FROM atelier08-access | WHERE status >= 500 AND status < 600
```

Une formule `count(...)` ne se colle pas dans la barre KQL : elle se saisit dans l’éditeur Formule d’une dimension Lens. 

### 6.5 Générer les fichiers de résultat attendus par les scripts

Les commandes Console précédentes ne créent pas de fichier sur la VM. Pour le générateur géographique, exécuter dans le dossier contenant les fichiers du pack :

```bash
curl --fail-with-body -sS -X POST "$ES_URL/atelier08-access/_search" \
  -H 'Content-Type: application/json' --data-binary @access-bornes-query.json \
  -o access-bornes.json
python3 verifier_resultat_atelier08.py bornes access-bornes.json

curl --fail-with-body -sS -X POST "$ES_URL/atelier08-access/_search" \
  -H 'Content-Type: application/json' --data-binary @access-validation-query.json \
  -o access-validation.json
python3 -m json.tool access-validation.json
```

Le fichier de requête existe avant l’appel ; le fichier de réponse est créé par `-o`. Une réponse d’erreur HTTP ou des bornes sans date ne doivent jamais être utilisées pour générer la carte.

## 7. Créer la vue de données et afficher les bonnes dates

### 7.1 Créer la vue de données

1. Utiliser la recherche globale et ouvrir Vues de données.
2. Cliquer Créer une vue de données.
3. Dans Nom, saisir `[A08] Access logs`.
4. Dans Modèle d’index, saisir exactement `atelier08-access`.
5. Ne pas saisir `atelier08-access*` : les extensions utilisent d’autres index qu’il ne faut pas additionner au corpus réel.
6. Dans Champ d’horodatage, sélectionner `@timestamp`.
7. Cliquer Enregistrer la vue de données dans Kibana, ou le bouton de sauvegarde proposé.

Si une vue de données équivalente existe, l’ouvrir et vérifier son motif plutôt que créer un doublon. [file:38]

### 7.2 Ouvrir Découvrir et régler la période absolue

1. Ouvrir Découvrir par la recherche globale.
2. Si nécessaire, choisir l’exploration par vue de données, pas ES|QL.
3. En haut à gauche, ouvrir le sélecteur de vue de données.
4. Sélectionner `[A08] Access logs`.
5. Vider la barre KQL.
6. Supprimer les pastilles de filtres avec leur croix ; vérifier aussi les filtres épinglés.
7. En haut à droite, cliquer le sélecteur de temps, souvent affiché « 15 dernières minutes ».
8. Ouvrir la saisie de la date de début et choisir Absolu.
9. Saisir une date légèrement antérieure à la date minimale notée en section 6.
10. Ouvrir la date de fin, choisir Absolu, puis saisir une date légèrement postérieure à la date maximale.
11. Cliquer Actualiser ou Appliquer.
12. Vérifier que le nombre de documents devient supérieur à zéro.

Les bornes Elasticsearch sont en UTC lorsqu’elles se terminent par `Z`. Le sélecteur peut afficher le fuseau du navigateur : convertir les dates ou utiliser une période plus large. Ne pas modifier le fuseau global d’un Space partagé sans accord.

Résultat attendu : les documents du corpus deviennent visibles. « 15 dernières minutes » ne retrouve pas une archive historique. [file:38]

## 8. Explorer les documents pas à pas

### 8.1 Ajouter les colonnes

1. Dans la liste de champs à gauche, rechercher `event_id`.
  <img width="218" height="221" alt="image" src="https://github.com/user-attachments/assets/953a52ad-0fc8-432e-a659-e7dd93f4dd3e" />

3. Survoler le champ et cliquer l’icône d’ajout en colonne ; son infobulle indique l’action d’ajout.
4. Effacer la recherche de champs.
5. Répéter pour `client_ip`, `method`, `url_path`, `status`, `bytes` et `message`.
6. Garder également `@timestamp`.
7. Déplacer les en-têtes de colonnes par glisser-déposer pour obtenir : date, IP, méthode, chemin, statut, octets, message.
8. Cliquer l’en-tête `@timestamp` pour changer l’ordre de tri.
9. Cliquer la flèche d’ouverture au début d’une ligne.
10. Dans le détail du document, comparer `path` et `url_path` : les paramètres éventuels ont été retirés dans `url_path`.

### 8.2 Tester les recherches une par une

Dans la barre KQL, saisir une expression, puis cliquer Rechercher / Actualiser ou appuyer sur Entrée. Remplacer l’expression avant le test suivant.

```kql
status: *
```

```kql
status >= 400 and status < 500
```

```kql
status >= 500 and status < 600
```

```kql
method: "GET" and status: 404
```

```kql
not bytes: *
```

Pour une valeur garantie présente, reprendre un code dans l’agrégation `statuts` de la section 6 et rechercher `status: CODE` en remplaçant CODE par ce nombre.

Contrôle : zéro 5xx dans Console doit donner zéro 5xx dans Découvrir sur la totalité de la période, pas une erreur à « corriger » en inventant des logs.

## 9. Enregistrer une table d’investigation Découvrir

1. Garder les colonnes de la section 8.
2. Saisir `status >= 400 and status < 600` dans la barre KQL.
3. Exécuter la recherche.
4. Cliquer Enregistrer.
5. Nommer la session `[A08] Détail des erreurs HTTP`.
6. Si l’option de conservation du temps est proposée, ne pas figer une autre période que celle voulue pour le tableau de bord.
7. Confirmer la sauvegarde.
8. Revenir ensuite à une barre KQL vide avant de créer les autres panneaux.

Cette table garde une requête locale d’erreurs ; elle ne doit pas imposer le filtre d’erreur aux KPI de trafic total. 

## 10. Créer le tableau de bord et construire ses cinq indicateurs

Chaque manipulation ci-dessous décrit le parcours complet : ouvrir le tableau de bord, ajouter une visualisation Lens, sélectionner le type « Indicateur », configurer la valeur, vérifier puis enregistrer. Ajoutez une nouvelle tuile à chaque manipulation ; ne remplacez pas les précédentes.

Les libellés d’interface sont rédigés en français ; certains peuvent varier selon l’écran. Le type de graphique « Indicateur » correspond au libellé confirmé sur votre interface. Les noms des champs, des index et les formules ne sont pas traduits.

### 10.1 Créer la première tuile : requêtes journalisées

#### A. Ouvrir le tableau de bord et Lens

1. Ouvrez « Tableaux de bord » dans Kibana.
2. Ouvrez `[A08] Diagnostic Access logs`, puis cliquez sur « Modifier ». S’il n’existe pas, cliquez sur « Créer un tableau de bord », puis enregistrez-le sous ce nom avant de poursuivre sa modification.
3. Réglez la période pour couvrir le corpus. Pour les 1 000 premières lignes du fichier fourni : incluez le 22 novembre 2026 de 18:51:30 à 18:51:35 UTC, avec une marge avant et après ; convertissez si votre navigateur affiche un autre fuseau.
4. Videz la barre KQL et retirez les filtres temporaires.
5. Cliquez sur « Créer une visualisation », ou sur « Ajouter » puis « Nouvelle visualisation » selon l’écran.
6. Choisissez Lens si un choix d’éditeur apparaît.
7. Sélectionnez la vue de données `[A08] Access logs`.
8. Si un éditeur ES|QL apparaît, revenez au mode de configuration par champs et dimensions, plutôt qu’au mode de requête.
9. Ouvrez le menu du type de graphique et choisissez « Indicateur ».

Vous êtes maintenant dans l’éditeur d’une tuile affichant une valeur unique. Les champs sont à gauche, l’aperçu au centre et la configuration à droite.

#### B. Configurer le comptage

1. À droite, cliquez sur la zone de la valeur principale : soit la dimension déjà présente, soit l’invitation à déposer un champ ou à cliquer pour en ajouter un.
2. Dans le volet ouvert, choisissez la fonction rapide de comptage des documents, « Nombre d’enregistrements ». Si elle est déjà sélectionnée, conservez-la.
3. Ne choisissez pas de champ : nous comptons les documents. N’ajoutez pas une deuxième valeur.
4. Dans le libellé, saisissez `Requêtes`.
5. Si le format est proposé, choisissez « Nombre » et zéro décimale.
6. Fermez uniquement le volet de configuration de la dimension, sans quitter Lens.
7. Comparez le nombre dans l’aperçu à N, le total attendu relevé lors des contrôles. Pour l’import neuf des 1 000 premières lignes du fichier fourni, le résultat attendu est 1 000.

Si la valeur diffère, vérifiez la vue de données, la période et les filtres avant d’enregistrer.

#### C. Ajouter la tuile et enregistrer

1. Cliquez sur « Enregistrer et revenir ».
2. Si le titre est demandé, saisissez `[A08] Requêtes journalisées` et confirmez.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrez le menu `…` de la nouvelle tuile, puis l’action de modification des paramètres du panneau. Saisissez ce titre et confirmez.
4. Cliquez sur « Enregistrer » en haut du tableau de bord.

Résultat attendu : la tuile `[A08] Requêtes journalisées` est visible et enregistrée. Conservez-la ; la manipulation suivante ajoute une deuxième tuile.

### 10.2 Ajouter une tuile : réponses 4xx

#### A. Ajouter une nouvelle visualisation

1. Ouvrez `[A08] Diagnostic Access logs` puis cliquez sur « Modifier » si nécessaire.
2. Vérifiez la période complète du corpus et l’absence de filtre global temporaire sur les erreurs.
3. Cliquez sur « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation ». N’ouvrez pas la modification d’une tuile précédente.
4. Choisissez Lens si nécessaire et la vue de données `[A08] Access logs`.
5. Dans le menu des graphiques, choisissez « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquez sur la dimension de la valeur principale, vide ou préremplie.
2. Dans le volet qui s’ouvre, choisissez l’onglet « Formule ».
3. Effacez le contenu proposé et saisissez exactement :

```text
count(kql='status >= 400 and status < 500')
```

4. Attendez la validation. En cas d’erreur, vérifiez les parenthèses et les apostrophes droites `'`.
5. Ne collez pas cette formule dans la barre de recherche KQL du tableau de bord.
6. Saisissez `Réponses 4xx` comme libellé, puis choisissez « Nombre » avec zéro décimale si ce réglage est proposé.
7. Fermez uniquement le volet de configuration pour regarder l’aperçu.

Contrôle : le résultat attendu est 30 réponses pour les 1 000 premières lignes fournies. Ces valeurs ne s’appliquent qu’au corpus de référence dans un index neuf et à sa période complète.

#### C. Ajouter la tuile et enregistrer

1. Cliquez sur « Enregistrer et revenir ».
2. Si un titre est demandé, saisissez `[A08] Réponses 4xx` puis confirmez.
3. Si le titre n’a pas été demandé, de retour sur le tableau de bord, ouvrez le menu `…` de la nouvelle tuile, choisissez l’action de modification des paramètres du panneau et renseignez ce titre.
4. Vérifiez que les tuiles précédentes sont toujours présentes.
5. Cliquez sur « Enregistrer » en haut du tableau de bord.

### 10.3 Ajouter une tuile : réponses 5xx

#### A. Ajouter une nouvelle visualisation

1. Ouvrez `[A08] Diagnostic Access logs` puis cliquez sur « Modifier » si nécessaire.
2. Vérifiez la période complète du corpus et l’absence de filtre global temporaire sur les erreurs.
3. Cliquez sur « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation ». N’ouvrez pas la modification d’une tuile précédente.
4. Choisissez Lens si nécessaire et la vue de données `[A08] Access logs`.
5. Dans le menu des graphiques, choisissez « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquez sur la dimension de la valeur principale, vide ou préremplie.
2. Dans le volet qui s’ouvre, choisissez l’onglet « Formule ».
3. Effacez le contenu proposé et saisissez exactement :

```text
count(kql='status >= 500 and status < 600')
```

4. Attendez la validation. En cas d’erreur, vérifiez les parenthèses et les apostrophes droites `'`.
5. Ne collez pas cette formule dans la barre de recherche KQL du tableau de bord.
6. Saisissez `Réponses 5xx` comme libellé, puis choisissez « Nombre » avec zéro décimale si ce réglage est proposé.
7. Fermez uniquement le volet de configuration pour regarder l’aperçu.

Contrôle : le résultat attendu est zéro pour les 1 000 premières lignes fournies : elles ne contiennent aucun 5xx. Ces valeurs ne s’appliquent qu’au corpus de référence dans un index neuf et à sa période complète.

Zéro n’est pas une erreur de formule. Ne créez pas de faux 5xx dans l’index réel pour remplir la tuile. Si l’écran indique « Aucune donnée », vérifiez aussi la période et la vue de données.

#### C. Ajouter la tuile et enregistrer

1. Cliquez sur « Enregistrer et revenir ».
2. Si un titre est demandé, saisissez `[A08] Réponses 5xx` puis confirmez.
3. Si le titre n’a pas été demandé, de retour sur le tableau de bord, ouvrez le menu `…` de la nouvelle tuile, choisissez l’action de modification des paramètres du panneau et renseignez ce titre.
4. Vérifiez que les tuiles précédentes sont toujours présentes.
5. Cliquez sur « Enregistrer » en haut du tableau de bord.

### 10.4 Ajouter une tuile : octets connus

#### A. Ajouter une nouvelle visualisation

1. Ouvrez `[A08] Diagnostic Access logs` puis cliquez sur « Modifier » si nécessaire.
2. Vérifiez la période complète du corpus et l’absence de filtre global temporaire sur les erreurs.
3. Cliquez sur « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation ». N’ouvrez pas la modification d’une tuile précédente.
4. Choisissez Lens si nécessaire et la vue de données `[A08] Access logs`.
5. Dans le menu des graphiques, choisissez « Indicateur ».

#### B. Configurer la valeur

1. Dans la liste des champs à gauche, recherchez `bytes`.
2. Maintenez le clic sur ce champ et glissez-le sur la zone de la valeur principale à droite. Si une valeur est déjà préremplie, remplacez-la au lieu d’en ajouter une deuxième.
3. Cliquez sur la dimension créée pour ouvrir sa configuration.
4. Choisissez explicitement « Somme », et non une moyenne.
5. Vérifiez que le champ sélectionné est `bytes`.
6. Saisissez `Octets connus` comme libellé.
7. Choisissez le format « Octets » si proposé.
8. Fermez uniquement le volet de configuration pour regarder l’aperçu.

Contrôle : le résultat attendu est 9 614 598 octets connus pour les 1 000 premières lignes fournies. Ces valeurs ne s’appliquent qu’au corpus de référence dans un index neuf et à sa période complète.

Le format peut afficher une unité abrégée. Les documents sans taille ne représentent pas des réponses de taille zéro.

#### C. Ajouter la tuile et enregistrer

1. Cliquez sur « Enregistrer et revenir ».
2. Si un titre est demandé, saisissez `[A08] Octets de réponse connus` puis confirmez.
3. Si le titre n’a pas été demandé, de retour sur le tableau de bord, ouvrez le menu `…` de la nouvelle tuile, choisissez l’action de modification des paramètres du panneau et renseignez ce titre.
4. Vérifiez que les tuiles précédentes sont toujours présentes.
5. Cliquez sur « Enregistrer » en haut du tableau de bord.

### 10.5 Ajouter une tuile : ip distinctes estimées

#### A. Ajouter une nouvelle visualisation

1. Ouvrez `[A08] Diagnostic Access logs` puis cliquez sur « Modifier » si nécessaire.
2. Vérifiez la période complète du corpus et l’absence de filtre global temporaire sur les erreurs.
3. Cliquez sur « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation ». N’ouvrez pas la modification d’une tuile précédente.
4. Choisissez Lens si nécessaire et la vue de données `[A08] Access logs`.
5. Dans le menu des graphiques, choisissez « Indicateur ».

#### B. Configurer la valeur

1. Dans la liste des champs à gauche, recherchez `client_ip`.
2. Maintenez le clic sur ce champ et glissez-le sur la zone de la valeur principale à droite. Si une valeur est déjà préremplie, remplacez-la au lieu d’en ajouter une deuxième.
3. Cliquez sur la dimension créée pour ouvrir sa configuration.
4. Choisissez explicitement la fonction de dénombrement unique, qui compte les valeurs distinctes, et non les documents.
5. Vérifiez que le champ sélectionné est `client_ip`.
6. Saisissez `IP distinctes estimées` comme libellé.
7. Choisissez le format « Nombre » avec zéro décimale si proposé.
8. Fermez uniquement le volet de configuration pour regarder l’aperçu.

Contrôle : le résultat attendu est une estimation du nombre d’IP distinctes ; le comptage exact local de l’échantillon est 154. Ces valeurs ne s’appliquent qu’au corpus de référence dans un index neuf et à sa période complète.

Ne nommez pas cette tuile « Visiteurs » : une IP ne représente pas nécessairement une personne.

#### C. Ajouter la tuile et enregistrer

1. Cliquez sur « Enregistrer et revenir ».
2. Si un titre est demandé, saisissez `[A08] IP distinctes estimées` puis confirmez.
3. Si le titre n’a pas été demandé, de retour sur le tableau de bord, ouvrez le menu `…` de la nouvelle tuile, choisissez l’action de modification des paramètres du panneau et renseignez ce titre.
4. Vérifiez que les tuiles précédentes sont toujours présentes.
5. Cliquez sur « Enregistrer » en haut du tableau de bord.

### 10.6 Disposer les cinq tuiles

1. Sur le tableau de bord, cliquez sur « Modifier » si nécessaire.
2. Repérez les cinq tuiles : requêtes, réponses 4xx, réponses 5xx, octets connus et IP distinctes.
3. Déplacez chaque tuile en la faisant glisser par son en-tête.
4. Redimensionnez-la avec la poignée située dans le coin inférieur.
5. Organisez une ou deux lignes lisibles, sans tronquer les titres.
6. Retirez les filtres de test et cliquez sur « Enregistrer ».

### 10.7 Option : comparer filtre de dimension et formule

1. Depuis le tableau de bord en modification, ajoutez une nouvelle visualisation Lens.
2. Sélectionnez `[A08] Access logs` puis le type « Indicateur ».
3. Ouvrez la dimension principale et choisissez le comptage des documents.
4. Dans les options avancées de cette dimension, ouvrez le réglage de filtrage s’il est proposé.
5. Saisissez `status >= 500 and status < 600` dans ce filtre, sans `count(...)` autour.
6. Comparez l’aperçu à la tuile 5xx : les deux doivent afficher zéro pour cet échantillon.
7. Annulez cette visualisation de test pour ne pas ajouter un doublon.

La section suivante ajoute les taux dans de nouvelles visualisations ; conservez les cinq tuiles existantes.

## 11. Construire et vérifier les taux

### 11.1 Part 5xx parmi les statuts valides

1. Créer un nouveau panneau Lens → Indicateur.
2. Cliquer dimension principale → Formule.
3. Saisir cette formule complète :

```text
count(kql='status >= 500 and status < 600') / count(kql='status >= 100 and status < 600')
```

4. Saisir le libellé `Part 5xx — statuts valides`.
5. Dans Apparence → Format de valeur, choisir Pourcentage.
6. Régler les décimales à 2 si ce réglage est proposé.
7. Ne pas multiplier la formule par 100 : le format Pourcentage réalise l’affichage en pourcentage.
8. Fermer le volet.
9. Comparer la valeur affichée à `100 × S / V`, si V est supérieur à zéro.
10. Enregistrer `[A08] Part 5xx — statuts valides`.

Exemple de calcul explicatif seulement : 2 réponses 5xx sur 100 statuts valides donnent une valeur de formule 0,02, affichée 2 %. Ce n’est pas un chiffre imposé au corpus. Les ratios et le format Pourcentage sont documentés dans Lens.

### 11.2 Part des erreurs HTTP 4xx + 5xx

1. Créer un autre indicateur.
2. Ouvrir dimension principale → Formule.
3. Saisir :

```text
count(kql='status >= 400 and status < 600') / count(kql='status >= 100 and status < 600')
```

4. Choisir Pourcentage, deux décimales.
5. Libellé `Part 4xx + 5xx — statuts valides`.
6. Vérifier `100 × (C + S) / V` si V > 0.
7. Enregistrer `[A08] Part des erreurs HTTP`.

### 11.3 Complétude du champ méthode

1. Créer un Indicateur → dimension principale → Formule.
2. Saisir :

```text
count(kql='method: *') / count()
```

3. Choisir Pourcentage, deux décimales.
4. Saisir le libellé `Méthode présente`.
5. Enregistrer `[A08] Complétude méthode`.

Une méthode absente peut correspondre à une requête atypique conservée par le parseur, pas forcément à une perte de collecte. [file:37]

### 11.4 Expérience guidée : pourquoi un taux devient 100 %

1. Noter la valeur du taux global 4xx + 5xx.
2. Dans la barre KQL globale du tableau de bord, saisir `status >= 400 and status < 600`.
3. Appliquer la recherche.
4. Si des erreurs existent, observer le taux 4xx + 5xx : il devient 100 %, car son dénominateur est maintenant limité aux documents filtrés.
5. Observer aussi la baisse de la tuile Requêtes.
6. Effacer la barre globale et appliquer à nouveau.
7. Vérifier le retour aux valeurs de référence.
8. Ne pas sauvegarder le tableau de bord avec le filtre de test actif.

Si V = 0, ne pas transformer l’absence de dénominateur en « service sans erreur ». Afficher une absence de valeur et diagnostiquer les données. [file:38]

## 12. Construire l’histogramme temporel par classe HTTP

### 12.1 Définir explicitement les axes

1. Depuis le tableau de bord en mode Modifier, créer une visualisation Lens.
2. Sélectionner `[A08] Access logs`.
3. Dans le sélecteur de graphique, choisir Barres, orientation verticale.
4. Repérer Axe horizontal, Axe vertical et Ventilation dans le panneau des dimensions à droite.
5. À gauche, rechercher `@timestamp`.
6. Glisser `@timestamp` vers Axe horizontal, pas vers le centre de l’aperçu.
7. Cliquer la dimension `@timestamp` créée.
8. Vérifier l’opération Histogramme de dates.
9. Activer Personnaliser l’intervalle de temps si vous voulez un intervalle explicite.
10. Pour les 1 000 documents fournis, choisir un minimum de `1 seconde` (`1s`) : ils ne couvrent que cinq secondes. Un intervalle d’une minute regrouperait ici tout l’échantillon dans une seule barre. Pour un autre corpus, choisir le minimum à partir des bornes mesurées.
11. Fermer le volet de dimension.

Le minimum demandé peut être ajusté par Kibana pour limiter le nombre de barres. Ne pas demander des milliers d’intervalles sur une archive couvrant des années.

### 12.2 Ajouter le comptage

1. À droite, cliquer la zone vide Axe vertical.
2. Choisir Nombre d’enregistrements.
3. Saisir le libellé `Requêtes par intervalle`.
4. Fermer le volet.
5. Vérifier qu’une série de barres apparaît au centre.

Si toutes les requêtes tiennent dans une seule barre, vérifier l’étendue réelle des dates et réduire l’intervalle sans descendre sous une granularité utile.

### 12.3 Ajouter les classes et l’empilement

1. Dans la recherche de champs à gauche, saisir `status_class`.
2. Glisser `status_class` vers Ventilation.
3. Cliquer cette dimension.
4. Choisir Valeurs les plus fréquentes.
5. Régler Nombre de valeurs à 6 ou davantage.
6. Si toutes les classes sont affichées et que la catégorie Other est inutile, ouvrir Options avancées et désactiver Regrouper les autres valeurs dans Autre.
7. Fermer le volet.
8. Ouvrir les paramètres Style / options du graphique à barres.
9. Choisir Empilé pour l’empilement.
10. Ne pas choisir Empilé en pourcentage : ici l’axe vertical doit représenter un nombre de requêtes, pas une part relative.
11. Garder la légende visible pour identifier les classes.
12. Enregistrer `[A08] Requêtes dans le temps par classe HTTP`.

Valeurs les plus fréquentes affiche les classes réellement présentes. L’absence de série 5xx si S = 0 est normale. Les opérations Histogramme de dates et Valeurs les plus fréquentes sont configurables dans les dimensions Lens. 

### 12.4 Tester l’interaction temporelle

1. Sur le tableau de bord, noter la période affichée en haut à droite.
2. Dans le graphique, cliquer-glisser horizontalement sur une courte fenêtre de temps.
3. Valider le changement de période s’il est demandé.
4. Observer le changement des KPI.
5. Revenir à la période absolue du corpus avec le sélecteur de temps.
6. Cliquer Enregistrer uniquement lorsque le contexte initial est restauré.


## 13. Visualiser la distribution des tailles

Objectif : distinguer une distribution de valeurs d’une évolution dans le temps.

1. Créer Lens → Barres verticale.
2. Glisser `bytes` dans Axe horizontal.
3. Ouvrir cette dimension et choisir Intervalles / Histogramme si proposé.
4. Ajuster la granularité Intervalles pour distinguer plusieurs classes. Selon l’éditeur, Kibana propose une granularité automatique plutôt qu’une largeur exacte ; ne pas chercher obligatoirement une case « 10 000 ». Pour des bornes déterministes, utiliser la variante Filtres ci-dessous.
5. Fermer la dimension.
6. Dans Axe vertical, choisir Nombre d’enregistrements.
7. Dans la barre KQL locale de Lens, saisir `bytes: *`.
8. Vérifier que cette barre appartient à l’éditeur du panneau, pas au tableau de bord global.
9. Enregistrer `[A08] Distribution des tailles connues`.

Si l’opération Intervalles n’est pas disponible, utiliser cette alternative guidée dans la même dimension horizontale :

1. Choisir Filtres à la place du champ d’axe.
2. Cliquer Ajouter un filtre pour chaque tranche.
3. Ajouter les filtres et leurs libellés :

| Filtre KQL | Libellé |
|---|---|
| `bytes >= 0 and bytes < 1000` | `< 1 000 octets` |
| `bytes >= 1000 and bytes < 10000` | `1 000 à 9 999` |
| `bytes >= 10000 and bytes < 100000` | `10 000 à 99 999` |
| `bytes >= 100000` | `100 000 et plus` |

4. Garder Nombre d’enregistrements en axe vertical.
5. Nommer cette variante `[A08] Tailles connues par tranches` : les classes n’ont pas toutes la même largeur, ce n’est pas un histogramme à classes égales.

## 14. Identifier les chemins et méthodes contributeurs

### 14.1 Top 10 des chemins en erreur

1. Créer Lens → Barres, orientation horizontale.
2. Glisser `url_path` dans l’axe des catégories, généralement Axe vertical pour des barres horizontales.
3. Ouvrir la dimension → Valeurs les plus fréquentes → Nombre de valeurs = 10.
4. Choisir un classement par Nombre d’enregistrements décroissant.
5. Dans l’axe numérique, généralement Axe horizontal, choisir Nombre d’enregistrements.
6. Dans la barre KQL locale Lens, saisir `status >= 400 and status < 600`.
7. Fermer les dimensions et vérifier les libellés des chemins.
8. Enregistrer `[A08] Top 10 chemins en erreur HTTP`.

Si aucune erreur n’existe, conserver le constat. Pour apprendre l’interface avec des données visibles, créer séparément un panneau « Top 10 chemins — tous statuts » sans le filtre, sans le présenter comme des erreurs.

### 14.2 Trafic par méthode

1. Créer un nouveau Lens → Barres horizontale.
2. Glisser `method` dans l’axe des catégories → Valeurs les plus fréquentes → 10 valeurs.
3. Dans l’axe numérique, choisir Nombre d’enregistrements.
4. Ne pas appliquer de filtre local d’erreur.
5. Enregistrer `[A08] Requêtes par méthode`.

## 15. Construire une table agrégée

1. Créer Lens et sélectionner le type Tableau.
2. Glisser `url_path` dans Lignes.
3. Ouvrir la dimension → Valeurs les plus fréquentes → 10 valeurs.
4. Cliquer la zone calculs → Nombre d’enregistrements ; libellé `Requêtes`.
5. Cliquer Ajouter un calcul ou la zone vide suivante dans calculs.
6. Choisir Formule et saisir `count(kql='status >= 400 and status < 500')` ; libellé `4xx`.
7. Ajouter une métrique Formule `count(kql='status >= 500 and status < 600')` ; libellé `5xx`.
8. Ajouter une métrique Formule avec le ratio de la section 11.1 ; libellé `Part 5xx`, format Pourcentage.
9. Ajouter une métrique Somme sur `bytes`, format Octets ; libellé `Octets connus`.
10. Cliquer la colonne Requêtes pour trier décroissant si le tri interactif est disponible ; sinon utiliser les paramètres de classement de Lignes.
11. Enregistrer `[A08] Routes — volume et erreurs`.

Le ratio est calculé pour chaque chemin. Une route avec une requête et un échec peut afficher 100 % ; lire le volume avec le taux. Un top 10 n’est pas le total du corpus. [file:38]

## 16. Créer une carte thermique temps × classe HTTP

1. Créer Lens → Carte thermique.
2. Glisser `@timestamp` sur Axe horizontal → Histogramme de dates.
3. Choisir un minimum de 1 seconde pour les 1 000 lignes du fichier joint ; utiliser les bornes de section 6 pour un autre import.
4. Glisser `status_class` sur Axe vertical → Valeurs les plus fréquentes → 6 valeurs.
5. Dans Valeur de cellule, choisir Nombre d’enregistrements.
6. Ouvrir les réglages de palette et choisir un dégradé séquentiel lisible.
7. Garder la légende visible.
8. Enregistrer `[A08] Intensité du trafic — temps et classe`.
9. Survoler une cellule et lire la classe, l’intervalle et le nombre de requêtes.

Il s’agit d’une matrice de comptages, pas d’une carte géographique. Si les 2xx dominent, créer une variante locale filtrée sur les erreurs et adapter son titre. Ne pas modifier silencieusement le filtre global. [file:38]

## 17. Ajouter les contrôles et assembler le tableau de bord

### 17.1 Liste déroulante « Méthode »

1. Ouvrir le tableau de bord → Modifier.
2. Cliquer Ajouter → Contrôles → Contrôle, ou Contrôles → Ajouter control.
3. Choisir Sélectionner un champ si le choix de source est proposé.
4. Vue de données : `[A08] Access logs`.
5. Champ : `method`.
6. Type de contrôle : Liste d’options.
7. Libellé : `Méthode`.
8. Autoriser plusieurs sélections pour cet exercice.
9. Cliquer Enregistrer ou Enregistrer et fermer.
10. Sélectionner GET dans le nouveau contrôle.
11. Vérifier que Requêtes diminue ou reste égal au total.
12. Effacer la sélection pour revenir à tous les documents.

### 17.2 Ajouter classe HTTP et chemin

Recommencer les étapes précédentes avec :

| Champ | Type | Libellé |
|---|---|---|
| `status_class` | Liste d’options | `Classe HTTP` |
| `url_path` | Liste d’options | `Chemin` |
| `bytes` | Curseur de plage | `Taille connue` |

Pour le Curseur de plage, déplacer une borne puis observer le filtrage. Retirer ensuite la sélection : ce contrôle peut exclure les documents sans taille. Les contrôles filtrent les panneaux pertinents selon leurs champs et sources.

### 17.3 Ajouter la table Découvrir

1. Tableau de bord en mode Modifier → Ajouter → Depuis la bibliothèque / Ajouter depuis la bibliothèque.
2. Rechercher `[A08] Détail des erreurs HTTP`.
3. Choisir la session Découvrir enregistrée.
4. Fermer le volet d’ajout.
5. Agrandir le panneau pour lire plusieurs lignes.
6. Vérifier que la table reste dédiée aux erreurs tandis que le KPI Requêtes compte tout le corpus.

### 17.4 Ajouter un panneau texte

1. Cliquer Ajouter → Texte, ou le panneau texte/Markdown proposé.
2. Saisir :

```markdown
### Contrat de lecture
- Source : atelier08-access, copie des access logs de l’atelier 3.
- Une ligne représente une requête journalisée, pas un visiteur.
- Période et fuseau : à compléter avec les bornes réelles.
- Les taux sont calculés parmi les statuts HTTP valides et dépendent des filtres.
- La taille en octets ne mesure pas la latence.
- Une archive historique ne décrit pas la disponibilité actuelle du serveur.
```

3. Enregistrer le panneau.
4. Placer le texte sous les contrôles, les KPI sur la première ligne, puis le graphique temporel sur une large ligne.
5. Placer carte thermique et top chemins côte à côte, puis la table des routes et la table Découvrir en bas.
6. Sauvegarder le tableau de bord.

## 18. Vérifier un panneau avec Inspecter

1. Retirer les filtres de test et restaurer la période complète.
2. Sur la tuile Requêtes, ouvrir le menu `…`.
3. Choisir Inspecter si proposé ; sinon ouvrir la visualisation, puis Plus → Inspecter.
4. Dans Vue, choisir Données pour voir la valeur renvoyée.
5. Choisir Requêtes pour examiner la requête Elasticsearch.
6. Repérer le filtre de date et vérifier qu’il couvre le corpus.
7. Utiliser Ouvrir dans la console si proposé pour examiner la requête sans la modifier.
8. Fermer Inspecter et comparer le résultat aux références de la section 6.

Ne pas comparer un comptage Elasticsearch sans filtre à un panneau limité à une méthode ou à une période différente. L’inspecteur permet de consulter les données, requêtes et, selon le panneau, d’exporter le tableau en CSV.

## 19. Alertes : comprendre règle, alerte et action

| Terme | Sens dans l’exercice |
|---|---|
| Rule / règle | Vérification planifiée : compter les 5xx récents toutes les minutes |
| Condition | Nombre de 5xx strictement supérieur à zéro |
| Alert / alerte | Instance active lorsque la condition est vraie |
| Recovery | La condition redevient fausse lors d’une exécution ultérieure |
| Connector | Configuration de connexion à un service de notification |
| Action | Notification ou autre opération exécutée selon la configuration |

Une règle n’utilise pas automatiquement la période absolue du tableau de bord. Elle évalue sa propre fenêtre glissante, par exemple les cinq dernières minutes. Une archive de 2017 ne peut donc pas déclencher une règle basée sur les cinq dernières minutes de `@timestamp`.

### 19.1 Vérification obligatoire

Avant de faire réaliser les manipulations aux débutants :

1. Ouvrir Règles via la recherche globale.
2. Vérifier la présence du type Seuil d’index.
3. Vérifier les droits de création de règles et la lecture de l’index de démonstration.
4. Faire configurer par l’administrateur une clé persistante `xpack.encryptedSavedObjects.encryptionKey` d’au moins 32 caractères.
5. Vérifier la configuration de sécurité/API keys et les exigences TLS du déploiement.
6. Vérifier la disponibilité et les conditions de licence du connecteur envisagé.
7. Si le lab initial sans sécurité ne permet pas l’alerting, préparer une variante sécurisée avant la séance. Ne pas demander aux stagiaires d’activer la sécurité au milieu de l’exercice.

Les fonctions d’alerte peuvent être bloquées par l’absence de clé de chiffrement ou de configuration requise. Ne pas contourner les droits ni désactiver TLS pour « débloquer » l’atelier. 


## 20. Préparer un corpus récent séparé pour tester les règles

Objectif : provoquer une alerte sans polluer les vrais access logs.

### 20.1 Créer l’index de simulation

Dans Console, exécuter une fois :

```http
PUT atelier08-alert-demo
{
  "settings": {"number_of_shards": 1, "number_of_replicas": 0},
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "@timestamp": {"type": "date"},
      "status": {"type": "integer"},
      "url_path": {"type": "keyword"},
      "service": {"type": "keyword"},
      "dataset": {"type": "keyword"},
      "message": {"type": "text"}
    }
  }
}
```

Si l’index existe, inspecter son mapping ; ne pas le supprimer.

### 20.2 Créer un pipeline d’horodatage de test

```http
PUT _ingest/pipeline/atelier08-alert-demo-now
{
  "description": "SIMULATION uniquement : date courante pour tester une regle",
  "processors": [
    {"set": {"field": "@timestamp", "value": "{{{_ingest.timestamp}}}"}},
    {"set": {"field": "dataset", "value": "simulation_alerting"}}
  ]
}
```

Ne pas appliquer ce pipeline au corpus réel : il remplace volontairement la date d’événement. Garder le nom exact `atelier08-access` dans les KPI évite de compter cette simulation. [file:38]

## 21. Créer une règle 5xx et observer son cycle de vie

### 21.1 Créer la règle avant d’injecter les documents

1. Ouvrir Règles par la recherche globale ; dans une navigation classique, Gestion de la pile → Règles.
2. Cliquer Créer une règle.
3. Choisir Seuil d’index.
4. Nom : `[A08-DEMO] Au moins un 5xx récent — binomeXX` ; remplacer XX par votre identifiant.
5. Indices : `atelier08-alert-demo`.
6. Champ temporel : `@timestamp`.
7. Dans QUAND, choisir count.
8. Dans SUR, choisir tous les documents ; ne pas activer de regroupement pour ce premier test.
9. Comparaison : est supérieur à.
10. Seuil : `0`.
11. Dans AU COURS DES DERNIÈRES, saisir `5`, unité minutes.
12. Dans le filtre KQL optionnel, saisir `status >= 500 and status < 600`.
13. Intervalle de vérification : `1 minute`, ou le minimum autorisé par l’environnement si supérieur.
14. Si un nombre d’exécutions consécutives est proposé, conserver `1` pour ce test.
15. Ne pas ajouter d’action externe à ce stade. Si un avertissement indique qu’aucune notification ne sera envoyée, le distinguer d’une impossibilité de créer la règle.
16. Cliquer Enregistrer / Créer une règle.

La règle Seuil d’index propose les clauses QUAND, SUR/REGROUPÉ PAR, la comparaison, la fenêtre et le filtre KQL. 

### 21.2 Injecter un événement de test récent

Dans Console :

```http
POST atelier08-alert-demo/_doc?pipeline=atelier08-alert-demo-now&refresh=wait_for
{
  "status": 503,
  "url_path": "/demo-alert",
  "service": "web-formation-demo",
  "message": "SIMULATION : erreur volontaire pour tester la regle"
}
```

Puis vérifier exactement la même fenêtre :

```http
POST atelier08-alert-demo/_count
{
  "query": {
    "bool": {
      "filter": [
        {"range": {"@timestamp": {"gte": "now-5m", "lte": "now"}}},
        {"range": {"status": {"gte": 500, "lt": 600}}}
      ]
    }
  }
}
```

Attendu juste après l’injection : au moins un document.

### 21.3 Voir l’alerte

1. Revenir à Règles.
2. Ouvrir la règle créée.
3. Attendre l’exécution planifiée, puis rafraîchir la page ; le scheduler peut ajouter un délai.
4. Ouvrir l’onglet Alertes ou la liste d’alertes associées à la règle.
5. Vérifier qu’une instance active apparaît.
6. Ouvrir Historique d’exécution / l’historique d’exécution pour distinguer une règle exécutée sans correspondance d’une règle en erreur.
7. Noter l’heure du document, l’heure de vérification et le résultat.

### 21.4 Observer la récupération

1. Ne plus injecter de 5xx.
2. Attendre que le dernier 5xx sorte de la fenêtre de cinq minutes, puis une nouvelle exécution de la règle.
3. Rafraîchir les détails.
4. Vérifier que l’alerte devient récupérée/inactive selon le libellé de l’écran ; l’historique conserve sa trace.
5. Comprendre qu’injecter un 200 ne neutralise pas un 503 encore dans la fenêtre.
6. Désactiver la règle en fin de séance pour éviter de laisser tourner les tests.

Une alerte active puis récupérée valide le cycle ; cliquer seulement sur un bouton de test ne prouve pas que l’exécution planifiée fonctionne. 

## 22. Ajouter une notification, uniquement si le connecteur est autorisé

Parcours optionnel. Une règle peut être étudiée sans envoyer de message externe.

1. Ouvrir la règle → Modifier.
2. Aller dans Actions → Ajouter une action.
3. Sélectionner un connecteur déjà configuré pour le lab, par exemple un connecteur de journalisation serveur s’il est proposé et autorisé.
4. Ne pas saisir d’adresse personnelle ni de secret dans un support partagé.
5. Choisir une fréquence « lors du changement d’état » / « Lors des changements d’état » si elle est disponible, plutôt qu’à chaque minute pendant toute la durée d’alerte.
6. Dans le message, saisir `Atelier 08 — simulation : seuil 5xx depasse.`
7. Pour ajouter le nom de règle ou les valeurs, utiliser le sélecteur de variables du formulaire. Ne pas recopier au hasard une variable d’un autre type de règle.
8. Sauvegarder.
9. Réinjecter un 503 avec la commande de la section 21.2.
10. Observer le nouvel état et  vérifier la notification.
11. Si l’alerte existe mais pas le message, contrôler séparément l’action, le connecteur, la fréquence et les erreurs d’exécution.

La disponibilité des actions dépend de la configuration, des droits et de la licence. Ne pas présenter l’envoi d’e-mails comme acquis sans serveur SMTP et connecteur opérationnels. 

## 23. Approfondissement guidé : comparer deux fenêtres réellement disponibles

Le corpus par défaut couvre cinq secondes et le fichier complet dix minutes. Une comparaison H-1 ou J-1 n’est pas réalisable avec ces seules données. Nous utilisons un décalage de trois secondes uniquement pour apprendre la fonction, sans présenter ces quelques secondes comme une tendance métier. 

1. Ouvrir le tableau de bord et créer Lens → Courbe.
2. Choisir `[A08] Access logs`.
3. Régler la période absolue de l’éditeur sur le 22 novembre 2026 de 18:51:33 à 18:51:36 UTC. Convertir si le navigateur affiche un autre fuseau.
4. Glisser `@timestamp` sur Axe horizontal → Histogramme de dates.
5. Cocher Personnaliser l’intervalle de temps et choisir Intervalle minimal = `1s`.
6. Dans Axe vertical, choisir Nombre d’enregistrements ; libellé `Fenêtre courante`.
7. Ajouter une deuxième métrique sur le même axe → Formule.
8. Saisir `count(shift='3s')` et le libellé `Trois secondes auparavant`.
9. Ne pas ajouter Valeurs les plus fréquentes et ne pas mélanger un décalage de trois secondes avec un intervalle d’une minute.
10. Observer que les points courants de 18:51:33 à 18:51:35 se comparent aux points de 18:51:30 à 18:51:32.
11. Enregistrer `[A08] Comparaison — décalage 3 secondes`.
12. Si la version de l’éditeur refuse ce décalage court ou si le corpus diffère, utiliser le repli ci-dessous ; ne pas inventer des heures absentes.
13. Restaurer la période complète après l’exercice ou définir une période locale au panneau si l’option est disponible.

### Repli sans décalage Lens : comparer explicitement deux fenêtres

Dans Console :

```http
POST atelier08-access/_search
{
  "size": 0,
  "aggs": {
    "fenetres": {
      "filters": {
        "filters": {
          "premieres_trois_secondes": {"range": {"@timestamp": {"gte": "2026-11-22T18:51:30Z", "lt": "2026-11-22T18:51:33Z"}}},
          "trois_secondes_suivantes": {"range": {"@timestamp": {"gte": "2026-11-22T18:51:33Z", "lt": "2026-11-22T18:51:36Z"}}}
        }
      }
    }
  }
}
```

Lire les deux `doc_count`. Les bornes sont explicites et les fenêtres ne se chevauchent pas. Cette expérience illustre un périmètre de comparaison ; elle ne permet pas de conclure sur la santé durable du service.

## 24. Approfondissement guidé : référence et annotation

### 24.1 Ajouter une ligne de référence

1. Depuis le tableau de bord, ouvrir le panneau temporel → Modifier la visualisation.
2. Cliquer Ajouter une couche → Lignes de référence.
3. Cliquer la valeur de l’axe vertical de cette couche.
4. Choisir Statique.
5. Saisir une valeur pédagogique adaptée aux volumes, par exemple 20 requêtes par intervalle si le graphique utilise des volumes de cet ordre.
6. Libellé : `Repère pédagogique — pas un SLO`.
7. Régler une couleur contrastée.
8. Sauvegarder et revenir au tableau de bord.

Une ligne de référence visuelle ne crée aucune règle d’alerte. Son unité doit correspondre à la mesure : nombre par intervalle, et non requêtes par seconde si la métrique n’est pas normalisée. 

### 24.2 Ajouter une annotation statique

1. Réouvrir le même graphique dans Lens.
2. Cliquer Ajouter une couche → Annotations.
3. Choisir Date statique.
4. Saisir une date à l’intérieur du corpus, relevée sur le graphique.
5. Nommer l’annotation `Point de discussion — aucune cause prouvée`.
6. Choisir une icône et une couleur lisibles.
7. Sauvegarder.

Ne pas étiqueter « déploiement » ou « panne » une date pour laquelle vous n’avez aucune preuve. L’annotation est ici un repère de lecture, pas une causalité établie.

## 25. Approfondissement guidé : analyse ES|QL indépendante

Cette section change explicitement de langage. Ne pas coller cette requête dans la barre KQL du tableau de bord.

1. Ouvrir Découvrir dans un nouvel onglet pour garder le tableau de bord ouvert.
2. Sélectionner le mode ES|QL / Requête.
3. Coller :

```esql
FROM atelier08-access
| WHERE status >= 400 AND status < 600
| STATS erreurs = COUNT(*) BY url_path
| SORT erreurs DESC
| LIMIT 10
```

4. Exécuter la requête.
5. Si un filtre de temps est actif dans cette exploration, régler la période sur celle du corpus.
6. Comparer les chemins à la visualisation Top 10, en tenant compte des filtres et des ex æquo.
7. Modifier `LIMIT 10` en `LIMIT 5`, puis réexécuter.
8. Sauvegarder la session `[A08] ES|QL — chemins en erreur` si les droits le permettent.
9. Revenir au tableau de bord sans remplacer sa vue de données par une requête.

Objectif pédagogique : KQL filtre des documents dans une vue de données ; ES|QL permet d’écrire une chaîne de filtrage, agrégation et tri. Les visualisations en mode Requête constituent un parcours distinct dans Lens.
## 26. Carte guidée reproductible avec les fichiers réellement fournis

Le pack fournit déjà `preparer_geo_demo.py` : nous l’utilisons au lieu d’introduire une deuxième structure géographique. Il crée six documents, trois positions distinctes et aucune IP réelle. Il dépend de `access-bornes.json`, généré en section 6.5. [file:90]

### 26.1 Générer puis charger la simulation

Dans le terminal du dossier de travail :

```bash
python3 verifier_resultat_atelier08.py bornes access-bornes.json
python3 preparer_geo_demo.py --bornes access-bornes.json
wc -l geo-demo.ndjson
```

Attendu : six documents, douze lignes NDJSON. Ne pas lancer `preparer_geo_demo.py` avec le fichier de requête à la place du fichier de réponse.

Créer l’index uniquement s’il n’existe pas :

```bash
curl --fail-with-body -sS -X PUT "$ES_URL/atelier08-access-geo-demo" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json
```

S’il existe déjà, contrôler son mapping et son contenu ; ne pas supprimer l’index. Charger ensuite :

```bash
curl --fail-with-body -sS -X POST "$ES_URL/atelier08-access-geo-demo/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @geo-demo.ndjson \
  -o geo-demo-bulk-response.json
python3 verifier_resultat_atelier08.py bulk geo-demo-bulk-response.json --expected 6
```

Les identifiants stables du générateur évitent de multiplier ces mêmes six documents lors d’un rejeu. Les vérifier avec `_count` ; ne pas supposer qu’un HTTP 200 implique le succès des six opérations.

### 26.2 Créer la vue de données et la carte

1. Ouvrir Vues de données → Créer une vue de données.
2. Nom : `[A08] Géographie — SIMULATION`.
3. Modèle d’index exact : `atelier08-access-geo-demo`.
4. Champ d’horodatage : `@timestamp`.
5. Enregistrer.
6. Ouvrir Cartes par la recherche globale → Créer une carte.
7. Régler la période sur celle du corpus, car les six points sont datés au premier événement réel.
8. Cliquer Ajouter une couche → Documents.
9. Vue de données : `[A08] Géographie — SIMULATION`.
10. Champ géographique : `client_geo.location`.
11. Ajouter aux Champs d’infobulle : `client_geo.city_name`, `status`, `geo_source`, `event_id`.
12. Nommer la couche `Repères de villes — SIMULATION`.
13. Cliquer Ajouter une couche / Enregistrer et fermer selon le volet.
14. Utiliser Ajuster aux données ou dézoomer jusqu’à Paris, Tunis et Montréal.
15. Survoler les points. Six documents donnent trois positions superposées deux à deux : ce n’est pas une perte de données.
16. Sauvegarder `[A08] Carte — SIMULATION sans IP réelle`.
17. Dans le tableau de bord en mode Modifier, cliquer Ajouter depuis la bibliothèque et ajouter la carte.
18. Ajouter un panneau texte : `Carte pédagogique indépendante : aucune provenance réelle des requêtes n’est représentée.`
19. Ne pas mélanger cette vue de données avec les KPI `atelier08-access`.

Un filtre global sur un chemin réel peut vider cette carte indépendante, dont les chemins valent `/demo`. Effacer les filtres d’investigation pour tester la carte, ou l’ouvrir dans Cartes. Si les paramètres de panneau le permettent, ignorer les filtres globaux uniquement pour ce panneau de simulation et l’indiquer dans sa description. Une période excluant le premier événement peut aussi masquer tous les points.


### 26.3 GeoIP réel : option non bloquante

1. Dans Console, exécuter `GET _ingest/geoip/stats`.
2. Faire préparer le pipeline `geoip-pipeline.json`selon l’annexe A.
3. Copier une IP publique d’un document source dans la requête `_simulate` de l’annexe.
4. Vérifier si `client_geo.location` est réellement produit.
5. Seulement après ce test, réindexer dans `atelier08-access-geoip` et vérifier les erreurs de traitement.
6. Mesurer la part de documents qui possèdent `client_geo.location`.
7. Créer une vue de données exacte sur l’index enrichi, puis reprendre les clics Cartes avec ce champ.
8. Si la base ou les coordonnées ne sont pas disponibles, conserver la carte de simulation. Ne pas en faire un échec du socle tableau de bord.

Ne jamais attribuer une ville fictive à une IP réelle. La base GeoIP n’est pas incluse dans les fichiers fournis. 

## 27. Scénario final guidé et corrigé attendu

### Travail participant

1. Ouvrir le tableau de bord enregistré.
2. Effacer les filtres temporaires et restaurer la période absolue du corpus.
3. Noter Requêtes, 4xx, 5xx et part d’erreurs.
4. Dans le contrôle Classe HTTP, sélectionner une classe d’erreur réellement présente.
5. Dans le Top 10, relever le chemin le plus fréquent.
6. Sélectionner ce chemin dans le contrôle Chemin.
7. Lire au moins trois documents de la table Découvrir, s’ils existent.
8. Ouvrir un document dans Découvrir pour examiner `message`.
9. Écrire : constat, hypothèse, preuve disponible, preuve manquante.
10. Retirer tous les filtres et vérifier le retour aux valeurs initiales.
11. Montrer l’historique de la règle de simulation et son passage actif/récupéré.

Si aucun 4xx/5xx n’est présent, réaliser l’investigation sur une classe existante en la nommant correctement ; réserver les erreurs artificielles à `atelier08-alert-demo`.

### Corrigé de raisonnement

- Une valeur zéro peut être juste ; vérifier la distribution avant d’accuser la formule.
- Un 404 ne prouve pas une panne serveur.
- Un 503 ne révèle pas à lui seul la cause racine.
- Une baisse après filtre est une modification de périmètre, pas une perte d’indexation.
- Un taux est interprétable avec son dénominateur et son volume.
- Le tableau de bord d’archive et la règle sur cinq minutes n’observent pas la même fenêtre.
- Une alerte et une notification ne sont pas la même chose.
- La carte de simulation n’apporte aucune preuve sur la provenance des vraies requêtes.

## 28. Sauvegarder, exporter et transmettre

### 28.1 Vérifier la réouverture

1. Cliquer Enregistrer sur le tableau de bord.
2. Revenir à la liste Tableaux de bord.
3. Réouvrir `[A08] Diagnostic Access logs`.
4. Vérifier titres, contrôles, table Découvrir et période.
5. Vérifier qu’aucun filtre de test n’est resté actif.

### 28.2 Exporter les objets Kibana

1. Ouvrir Objets enregistrés par la recherche globale.
2. Rechercher le tableau de bord par son nom.
3. Cocher le tableau de bord voulu.
4. Cliquer Exporter.
5. Inclure les objets liés si l’option est proposée.
6. Conserver l’export NDJSON avec le compte rendu.

L’export des objets Kibana ne sauvegarde pas les documents Elasticsearch. Ne pas supposer qu’il constitue une sauvegarde portable des règles, des secrets ou des connecteurs ; prévoir leur gestion séparément selon les possibilités du déploiement. 

## 29. Dépannage rapide et critères de réussite

| Symptôme | Vérification guidée |
|---|---|
| Aucun document dans Découvrir | Console `_count`, puis vue de données exacte, période absolue, filtres |
| KQL 5xx renvoie zéro | Exécuter le `_count` range de la section 6.3 |
| Erreur de syntaxe dans une formule | Onglet Formule ; apostrophes droites ; parenthèses ; pas dans la barre KQL |
| `status` absent | Ouvrir un document et vérifier le schéma source ; ne pas renommer au hasard |
| Champ numérique non agrégeable | `_field_caps`, mapping et source correcte |
| Taux affiché 200 % au lieu de 2 % | Retirer le `* 100` si format Pourcentage |
| Taux à 100 % partout | Retirer le filtre global d’erreurs et vérifier le dénominateur |
| Courbe avec une seule barre | Dates réellement présentes et intervalle de l’histogramme |
| Aucun 5xx dans la légende | Vérifier S ; une classe absente n’a pas de série |
| Règle impossible à créer | Droits, sécurité, clé chiffrante persistante, configuration et licence |
| Règle saine mais aucune alerte | Index exact, propre fenêtre de cinq minutes, date récente, seuil |
| Alerte sans notification | Action/connector, fréquence, droits, historique d’exécution |
| Un 200 n’efface pas l’alerte | Le 503 reste dans la fenêtre jusqu’à expiration |
| Carte sans points | vue de données exacte, geo_point, filtres et données de la couche |
| Totaux doublés | Motif trop large incluant index réel et copies |

### Grille d’évaluation

| Critère | Preuve attendue |
|---|---|
| Prérequis | Index source rempli, projection validée, pas de suppression de source |
| Recherche | Participant distingue KQL, Formule et Console |
| KPI | N, C, S et B cohérents avec la référence |
| Taux | Dénominateur nommé et format Pourcentage correct |
| Temps | Période absolue documentée et histogramme lisible |
| Interaction | Deux contrôles testés, filtres remis à zéro |
| Investigation | Tableau documentaire et hypothèse sans cause inventée |
| Alerte | Règle exécutée, événement de simulation, état actif puis récupéré |
| Avancé | Inspecter et au moins un exercice comparaison / annotation / ES|QL |
| Carte | Simulation explicitement identifiée ou couverture GeoIP documentée |
| Conservation | Tableau de bord sauvegardé ; règle de test désactivée |


## Annexe A — Définition du pipeline GeoIP réel

### Préconditions et limites

- Base GeoIP disponible et à jour sur les nœuds d’ingestion.
- IP publiques résolubles ; IP privées, réservées, proxys ou données anciennes peuvent ne pas produire de coordonnées.
- Une localisation IP est approximative et peut représenter un fournisseur ou un point de sortie, pas l’utilisateur.

### Vérifier l’état et créer le pipeline

```http
GET _ingest/geoip/stats
```

```bash
curl --fail-with-body -sS -X PUT "$ES_URL/_ingest/pipeline/atelier08-geoip" \
  -H 'Content-Type: application/json' --data-binary @geoip-pipeline.json
```

```json
{
  "description": "GeoIP optionnel ; ne pas fabriquer des coordonnees pour les IP sans resultat",
  "processors": [
    {
      "geoip": {
        "field": "client_ip",
        "target_field": "client_geo",
        "properties": [
          "country_iso_code",
          "country_name",
          "city_name",
          "location"
        ],
        "ignore_missing": true,
        "on_failure": [
          {
            "append": {
              "field": "tags",
              "value": "_geoip_failed",
              "allow_duplicates": false
            }
          }
        ]
      }
    },
    {
      "set": {
        "if": "ctx.client_geo != null && ctx.client_geo.location != null",
        "field": "geo_source",
        "value": "geoip"
      }
    }
  ]
}
```

### Tester une vraie ligne avant l’ensemble

Dans Console, POST _ingest/pipeline/atelier08-geoip/_simulate avec un document contenant une client_ip de votre corpus. Inspecter la sortie : présence de client_geo.location ou tags signalant un problème. Un succès HTTP ne garantit pas une localisation.

```http
POST _ingest/pipeline/atelier08-geoip/_simulate
{
  "docs":[{"_source":{"client_ip":"127.0.0.1"}}]
}
```

Cet exemple de boucle locale ne doit pas produire une vraie position publique : le remplacer par une IP réelle du corpus pour tester l’enrichissement disponible. Ne pas promettre qu’une IP précise possède un enregistrement GeoIP.

### Enrichir dans un nouvel index, sans altérer le corpus principal

```bash
curl --fail-with-body -sS -X PUT "$ES_URL/atelier08-access-geoip" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json

curl --fail-with-body -sS -X POST "$ES_URL/_reindex?refresh=true" \
  -H 'Content-Type: application/json' --data-binary @geoip-reindex.json \
  -o geoip-reindex-response.json
python3 -m json.tool geoip-reindex-response.json
```

Ce second pipeline ne réécrit pas ingested_at. Les IDs sont conservés dans une copie enrichie ; ne pas inclure source et copie dans la même vue de données de volume.

Créer [A08] Access GeoIP sur atelier08-access-geoip avec @timestamp. Mesurer les documents ayant client_geo.location et le total. Si aucune coordonnée n’est produite, conserver le constat et utiliser la simulation guidée de section 26. Chercher les tags _geoip_failed, _geoip_expired_database ou de base indisponible, et consulter les statistiques/logs selon le cas.


### Corps complet pour geoip-reindex.json

```json
{
  "source": {"index": "atelier08-access"},
  "dest": {
    "index": "atelier08-access-geoip",
    "pipeline": "atelier08-geoip",
    "op_type": "create"
  }
}
```

Créer ce fichier dans le dossier de travail avant d’utiliser la commande correspondante. Contrôler `failures`, `version_conflicts`, `created` et le nombre de documents localisés. Ne pas relancer aveuglément sur une destination partiellement remplie.
