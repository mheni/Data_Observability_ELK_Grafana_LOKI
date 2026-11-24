# Atelier 08 — Construire son premier dashboard Kibana, puis créer des alertes

Version cible : Kibana et Elasticsearch 9.5.7 — parcours débutant, puis approfondissement.

## 1. Fiche pédagogique et organisation

| Élément | Contenu |
|---|---|
| Public | Participants débutants dans Kibana |
| Socle guidé | 4 h à 5 h, avec pauses et vérifications |
| Alertes | 1 h à 1 h 30 supplémentaire |
| Approfondissements | 1 h à 2 h selon les options |
| Source | `atelier03-access`, import des access logs de l’atelier 3 |
| Destination principale | `atelier08-access` |
| Livrables | Dashboard enregistré, investigation Discover, règle testée, bilan de validation |
| Outils | Console, Discover, Data Views, Lens, Dashboards, Rules, Maps |

Ce support remplace le précédent atelier 08. Il conserve le corpus access logs et détaille les manipulations de l’interface. Il ne nécessite pas de réaliser la partie MovieLens de l’atelier 3. [file:37][file:38]

### Conventions de lecture

- `Cliquer` : clic gauche sur un bouton ou un menu.
- `Saisir` : remplacer le contenu d’un champ par le texte indiqué.
- `Glisser-déposer` : maintenir le clic sur un champ de la liste de gauche, déplacer le champ vers la zone indiquée, puis relâcher.
- `Console` : ouvrir Dev Tools → Console. Ne pas coller les commandes `curl` dans Console.
- `Terminal` : shell Linux de la VM, pas la barre de recherche de Kibana.
- Les libellés anglais sont conservés pour faciliter leur identification. La traduction peut varier.
- La navigation dépend de la solution sélectionnée et des droits. Pour trouver une application, utiliser la recherche globale en haut de Kibana : saisir `Discover`, `Dashboards`, `Data Views`, `Rules` ou `Dev Tools`, puis cliquer le résultat de navigation.

### Note de compatibilité

La cible demandée est 9.5.7. Les procédures s’appuient sur la documentation officielle actuelle et les fichiers du parcours ; elles n’ont pas été exécutées sur votre instance. Les variantes de libellés utiles sont indiquées, sans prétendre que chaque bouton occupe une position identique dans tous les déploiements. Ne pas confondre le mode Lens « Point-and-click » avec le mode « Query ». Le socle utilise Point-and-click et KQL. [web:74]

### Consigne formateur avant la séance

1. Vérifier les droits de création des Data Views, dashboards et visualisations.
2. Vérifier que `atelier03-access` est rempli et que `status` est numérique.
3. Réserver un Space de formation et un nom de règle par binôme.
4. Tester séparément les prérequis d’alerting : ne pas découvrir à cette étape que la sécurité ou la clé de chiffrement manque.
5. Prévoir une session distincte pour les extensions si le groupe découvre totalement Kibana.
6. Ne jamais supprimer automatiquement un index existant pour faire réussir un exercice.

## 2. Comprendre le résultat et les langages

Une ligne du log représente une requête journalisée, pas un utilisateur. Le dashboard montre des volumes, statuts et tailles ; le corpus ne contient pas de durée de réponse permettant de calculer une latence HTTP. [file:38]

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
| Barre Discover en mode Data View | KQL | `status >= 500 and status < 600` |
| Dimension Lens, onglet Formula | Formule Lens | `count(kql='status >= 500 and status < 600')` |
| Console | API Elasticsearch + JSON | `GET atelier08-access/_count` |
| Discover, mode ES|QL | ES|QL | `FROM atelier08-access | STATS n = COUNT(*)` |

La requête `status >= 500 and status < 600` est valide en KQL. Zéro résultat ne prouve pas une erreur de syntaxe : il peut simplement n’exister aucun 5xx dans l’échantillon ou dans la période sélectionnée. Le diagnostic de la section 6 doit être réalisé avant de changer les formules. [web:52]

## 3. Préparer les données : connexion, contrôles et projection

### Objectif

Réutiliser l’installation de l’atelier 01. Aucun cluster ni collecteur supplémentaire n’est nécessaire.

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

Dans Kibana → Dev Tools → Console, saisir méthode, chemin et JSON, pas une commande curl. Console utilise la connexion configurée de Kibana à Elasticsearch.

### Commandes curl depuis la VM

```bash
mkdir -p ~/formation-observabilite/atelier08
cd ~/formation-observabilite/atelier08
export ES_URL='http://localhost:9200'
```

Si la variante sécurisée est active : utiliser ES_URL en HTTPS, ES_CA et ELASTIC_PASSWORD comme précédemment, puis ajouter après chaque curl Elasticsearch :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Ne pas ajouter ces options dans Console ni dans les scripts Python. Ne pas utiliser -k.

## 4. Contrôler le corpus existant avant de créer un dashboard

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

## 5. Créer une projection dédiée au dashboard

### Objectif

Préserver atelier03-access et ajouter des champs explicables pour les regroupements et la qualité.

Les fichiers JSON complets sont joints à l’atelier. Dans le dossier contenant ces fichiers :

```bash
curl -X PUT "$ES_URL/atelier08-access" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json

curl -X PUT "$ES_URL/_ingest/pipeline/atelier08-access-base" \
  -H 'Content-Type: application/json' --data-binary @access-base-pipeline.json
```

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
| ingested_at | Heure d’ingestion de cette projection pédagogique |
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

### Réindexer sans modifier la source

```bash
curl -X POST "$ES_URL/_reindex?refresh=true" \
  -H 'Content-Type: application/json' --data-binary @access-reindex.json \
  -o access-reindex-response.json
python3 -m json.tool access-reindex-response.json
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

Objectif : connaître les données avant de créer des graphiques. Cette étape se fait dans Console et ne dépend pas du filtre temporel de Discover.

### 6.1 Ouvrir et utiliser Console

1. Dans la recherche globale Kibana, saisir `Dev Tools`.
2. Ouvrir Dev Tools, puis l’onglet Console.
3. Coller la requête suivante dans la zone de gauche.
4. Cliquer dans la requête.
5. Cliquer sur le triangle d’exécution associé à cette requête.
6. Lire la réponse dans la zone de droite.

```http
GET atelier08-access/_count
```

Si `count` vaut zéro, revenir aux étapes de réindexation. Si l’index est introuvable, revenir à sa création. Ne pas créer une Data View pour masquer ce prérequis manquant.

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
- Résultat supérieur à zéro, mais Discover vide : vérifier Data View, période, langage et filtres.
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

Une formule `count(...)` ne se colle pas dans la barre KQL : elle se saisit dans l’éditeur Formula d’une dimension Lens. [web:52][web:74]

## 7. Créer la Data View et afficher les bonnes dates

### 7.1 Créer la Data View

1. Utiliser la recherche globale et ouvrir Data Views.
2. Cliquer Create data view.
3. Dans Name, saisir `[A08] Access logs`.
4. Dans Index pattern, saisir exactement `atelier08-access`.
5. Ne pas saisir `atelier08-access*` : les extensions utilisent d’autres index qu’il ne faut pas additionner au corpus réel.
6. Dans Timestamp field, sélectionner `@timestamp`.
7. Cliquer Save data view to Kibana, ou le bouton de sauvegarde proposé.

Si une Data View équivalente existe, l’ouvrir et vérifier son motif plutôt que créer un doublon. [file:38]

### 7.2 Ouvrir Discover et régler la période absolue

1. Ouvrir Discover par la recherche globale.
2. Si nécessaire, choisir l’exploration par Data View, pas ES|QL.
3. En haut à gauche, ouvrir le sélecteur de Data View.
4. Sélectionner `[A08] Access logs`.
5. Vider la barre KQL.
6. Supprimer les pastilles de filtres avec leur croix ; vérifier aussi les filtres épinglés.
7. En haut à droite, cliquer le sélecteur de temps, souvent affiché « Last 15 minutes ».
8. Ouvrir la saisie de la date de début et choisir Absolute.
9. Saisir une date légèrement antérieure à la date minimale notée en section 6.
10. Ouvrir la date de fin, choisir Absolute, puis saisir une date légèrement postérieure à la date maximale.
11. Cliquer Update ou Apply.
12. Vérifier que le nombre de documents devient supérieur à zéro.

Les bornes Elasticsearch sont en UTC lorsqu’elles se terminent par `Z`. Le sélecteur peut afficher le fuseau du navigateur : convertir les dates ou utiliser une période plus large. Ne pas modifier le fuseau global d’un Space partagé sans accord.

Résultat attendu : les documents du corpus deviennent visibles. « Last 15 minutes » ne retrouve pas une archive historique. [file:38]

## 8. Explorer les documents pas à pas

### 8.1 Ajouter les colonnes

1. Dans la liste de champs à gauche, rechercher `event_id`.
2. Survoler le champ et cliquer l’icône d’ajout en colonne ; son infobulle indique l’action d’ajout.
3. Effacer la recherche de champs.
4. Répéter pour `client_ip`, `method`, `url_path`, `status`, `bytes` et `message`.
5. Garder également `@timestamp`.
6. Déplacer les en-têtes de colonnes par glisser-déposer pour obtenir : date, IP, méthode, chemin, statut, octets, message.
7. Cliquer l’en-tête `@timestamp` pour changer l’ordre de tri.
8. Cliquer la flèche d’ouverture au début d’une ligne.
9. Dans le détail du document, comparer `path` et `url_path` : les paramètres éventuels ont été retirés dans `url_path`.

### 8.2 Tester les recherches une par une

Dans la barre KQL, saisir une expression, puis cliquer Search/Update ou appuyer sur Entrée. Remplacer l’expression avant le test suivant.

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

Contrôle : zéro 5xx dans Console doit donner zéro 5xx dans Discover sur la totalité de la période, pas une erreur à « corriger » en inventant des logs.

## 9. Enregistrer une table d’investigation Discover

1. Garder les colonnes de la section 8.
2. Saisir `status >= 400 and status < 600` dans la barre KQL.
3. Exécuter la recherche.
4. Cliquer Save.
5. Nommer la session `[A08] Détail des erreurs HTTP`.
6. Si l’option de conservation du temps est proposée, ne pas figer une autre période que celle voulue pour le dashboard.
7. Confirmer la sauvegarde.
8. Revenir ensuite à une barre KQL vide avant de créer les autres panneaux.

Cette table garde une requête locale d’erreurs ; elle ne doit pas imposer le filtre d’erreur aux KPI de trafic total. [file:38]

## 10. Créer le dashboard et apprendre à ouvrir Lens

### 10.1 Dashboard vide

1. Ouvrir Dashboards.
2. Cliquer Create dashboard.
3. Vérifier la période absolue couvrant le corpus.
4. Vider la barre KQL et retirer les filtres temporaires.
5. Cliquer Save.
6. Saisir `[A08] Diagnostic Access logs`.
7. Activer la conservation de la période si l’option est proposée, puis enregistrer.
8. Cliquer Edit pour poursuivre les ajouts.

### 10.2 Procédure commune : ouvrir Lens

Cette procédure sera utilisée à chaque création de panneau :

1. Depuis le dashboard en mode Edit, cliquer Add, puis New visualization, ou directement Create visualization si ce bouton est proposé.
2. Choisir Lens si un choix d’éditeur apparaît.
3. Choisir le mode Point-and-click, pas Query.
4. Dans le sélecteur de Data View de Lens, choisir `[A08] Access logs`.
5. Repérer les trois zones : champs à gauche ; aperçu au centre ; dimensions de la couche à droite.
6. Au-dessus de l’aperçu, ouvrir le sélecteur de type de graphique. Choisir le type indiqué dans chaque exercice.

Si vous voyez un éditeur de requête ES|QL à la place des dimensions, revenir au mode Point-and-click. Lens permet de glisser les champs dans le panneau des dimensions ; un clic sur une zone « Drop a field or click to add » permet aussi de choisir une fonction. [web:74]

### 10.3 Procédure commune : terminer un panneau

1. Cliquer Save and return après configuration du graphique.
2. Si une boîte de titre apparaît, saisir le titre demandé.
3. Si aucun titre n’est demandé, de retour sur le dashboard ouvrir le menu `…` du panneau, puis Edit panel settings ou l’action de modification du titre proposée.
4. Saisir le titre et confirmer.
5. Cliquer Save sur le dashboard.

Sauvegarder le panneau et sauvegarder le dashboard sont deux gestes à vérifier. Si vous partez de Visualize Library, Lens peut proposer Save puis le choix du dashboard à la place de Save and return. [web:74]

## 11. Construire les KPI : manipulations détaillées

Objectif : obtenir cinq tuiles lisibles et vérifier leurs chiffres. Aucun filtre 4xx ou 5xx ne doit être placé dans la barre globale du dashboard pendant cette construction.

### 11.1 KPI « Requêtes journalisées »

1. Ouvrir Lens avec la procédure 10.2.
2. Ouvrir le sélecteur de graphique et choisir Metric.
3. Dans le panneau de droite, cliquer la zone Primary metric, « Drop a field or click to add » ou la métrique déjà présente.
4. Dans l’éditeur de dimension, sélectionner Quick function si nécessaire.
5. Choisir Count of records. Il n’y a pas de champ à sélectionner pour compter les documents.
6. Dans le libellé de la dimension, saisir `Requêtes`.
7. Dans Appearance → Value format, choisir Number si nécessaire, avec zéro décimale.
8. Fermer l’éditeur de dimension avec Close ou la croix du volet.
9. Vérifier le nombre au centre : il doit égaler N si toute la période est incluse et aucun document n’est sans date.
10. Terminer avec la procédure 10.3 ; titre `[A08] Requêtes journalisées`.

Si le champ Count of records était déjà prérempli, le conserver : ne pas ajouter une deuxième métrique.

### 11.2 KPI « Réponses 4xx » avec Formula

1. Depuis le dashboard, créer une nouvelle visualisation Lens.
2. Choisir Metric et `[A08] Access logs`.
3. Cliquer la dimension Primary metric à droite.
4. Choisir l’onglet Formula, pas la barre KQL située en haut de l’écran.
5. Effacer la formule proposée et saisir exactement :

```text
count(kql='status >= 400 and status < 500')
```

6. Attendre la validation de la formule. En cas d’erreur rouge, vérifier les parenthèses et les apostrophes simples droites `'`, pas les apostrophes typographiques.
7. Dans le libellé, saisir `Réponses 4xx`.
8. Choisir Number, zéro décimale.
9. Fermer l’éditeur de dimension.
10. Vérifier que le chiffre vaut C, puis enregistrer `[A08] Réponses 4xx`.

### 11.3 KPI « Réponses 5xx »

1. Créer un nouveau panneau Lens → Metric.
2. Ouvrir Primary metric → Formula.
3. Saisir :

```text
count(kql='status >= 500 and status < 600')
```

4. Saisir le libellé `Réponses 5xx`.
5. Choisir Number, zéro décimale.
6. Fermer le volet et comparer à S.
7. Enregistrer `[A08] Réponses 5xx`.

Résultat attendu si S = 0 : la tuile affiche zéro. Une formule correcte peut produire zéro. Si la tuile indique « No data », vérifier d’abord que le KPI Requêtes affiche des documents dans le même contexte.

### 11.4 Variante sans formule pour comprendre le filtre

À réaliser uniquement si les participants ont besoin de distinguer filtre et formule :

1. Dans un nouveau Metric, choisir Count of records.
2. Ouvrir Add advanced options → Filter by si disponible.
3. Saisir `status >= 500 and status < 600` dans ce filtre de métrique.
4. Ne pas saisir `count(...)` ici.
5. Comparer la valeur à la tuile de la section 11.3.
6. Annuler ce panneau de test pour ne pas garder un doublon.

Les formules Lens peuvent filtrer leurs agrégations avec `kql='...'`. Les fonctions de filtrage de dimension et la barre globale n’ont pas la même portée. [web:74]

### 11.5 KPI « Octets connus »

1. Créer un panneau Lens → Metric.
2. Dans la liste de gauche, rechercher `bytes`.
3. Glisser `bytes` vers Primary metric à droite.
4. Cliquer la dimension créée : Lens a pu proposer Average ou une autre opération.
5. Choisir explicitement Sum dans Quick function.
6. Vérifier que Field vaut `bytes`.
7. Dans Appearance → Value format, choisir Bytes.
8. Saisir le libellé `Octets connus`.
9. Fermer, puis enregistrer `[A08] Octets de réponse connus`.

Contrôle : la valeur formatée doit correspondre à B, avec une conversion d’unité d’affichage. Les documents sans `bytes` ne deviennent pas des réponses de taille zéro.

### 11.6 KPI « IP distinctes estimées »

1. Créer un panneau Lens → Metric.
2. Rechercher `client_ip` dans la liste de gauche.
3. Glisser ce champ sur Primary metric.
4. Ouvrir la dimension et choisir Unique count.
5. Vérifier Field = `client_ip`.
6. Saisir le libellé `IP distinctes estimées` et Number, zéro décimale.
7. Fermer et enregistrer `[A08] IP distinctes estimées`.

Ne pas nommer cette tuile « Visiteurs » : une IP n’est pas une personne, et la cardinalité est une estimation. [file:38]

### 11.7 Organiser la première ligne

1. Sur le dashboard, rester en mode Edit.
2. Déplacer chaque panneau par son en-tête vers la ligne supérieure.
3. Redimensionner avec la poignée du coin inférieur du panneau.
4. Prévoir une largeur suffisante pour lire le titre et la valeur.
5. Cliquer Save.

Point de contrôle formateur : chaque participant explique la différence entre nombre de documents, somme d’octets et nombre d’IP distinctes.

## 12. Construire et vérifier les taux

### 12.1 Part 5xx parmi les statuts valides

1. Créer un nouveau panneau Lens → Metric.
2. Cliquer Primary metric → Formula.
3. Saisir cette formule complète :

```text
count(kql='status >= 500 and status < 600') / count(kql='status >= 100 and status < 600')
```

4. Saisir le libellé `Part 5xx — statuts valides`.
5. Dans Appearance → Value format, choisir Percent.
6. Régler les décimales à 2 si ce réglage est proposé.
7. Ne pas multiplier la formule par 100 : le format Percent réalise l’affichage en pourcentage.
8. Fermer le volet.
9. Comparer la valeur affichée à `100 × S / V`, si V est supérieur à zéro.
10. Enregistrer `[A08] Part 5xx — statuts valides`.

Exemple de calcul explicatif seulement : 2 réponses 5xx sur 100 statuts valides donnent une valeur de formule 0,02, affichée 2 %. Ce n’est pas un chiffre imposé au corpus. Les ratios et le format Percent sont documentés dans Lens. [web:74]

### 12.2 Part des erreurs HTTP 4xx + 5xx

1. Créer un autre Metric.
2. Ouvrir Primary metric → Formula.
3. Saisir :

```text
count(kql='status >= 400 and status < 600') / count(kql='status >= 100 and status < 600')
```

4. Choisir Percent, deux décimales.
5. Libellé `Part 4xx + 5xx — statuts valides`.
6. Vérifier `100 × (C + S) / V` si V > 0.
7. Enregistrer `[A08] Part des erreurs HTTP`.

### 12.3 Complétude du champ méthode

1. Créer un Metric → Primary metric → Formula.
2. Saisir :

```text
count(kql='method: *') / count()
```

3. Choisir Percent, deux décimales.
4. Saisir le libellé `Méthode présente`.
5. Enregistrer `[A08] Complétude méthode`.

Une méthode absente peut correspondre à une requête atypique conservée par le parseur, pas forcément à une perte de collecte. [file:37]

### 12.4 Expérience guidée : pourquoi un taux devient 100 %

1. Noter la valeur du taux global 4xx + 5xx.
2. Dans la barre KQL globale du dashboard, saisir `status >= 400 and status < 600`.
3. Appliquer la recherche.
4. Si des erreurs existent, observer le taux 4xx + 5xx : il devient 100 %, car son dénominateur est maintenant limité aux documents filtrés.
5. Observer aussi la baisse de la tuile Requêtes.
6. Effacer la barre globale et appliquer à nouveau.
7. Vérifier le retour aux valeurs de référence.
8. Ne pas sauvegarder le dashboard avec le filtre de test actif.

Si V = 0, ne pas transformer l’absence de dénominateur en « service sans erreur ». Afficher une absence de valeur et diagnostiquer les données. [file:38]

## 13. Construire l’histogramme temporel par classe HTTP

### 13.1 Définir explicitement les axes

1. Depuis le dashboard en mode Edit, créer une visualisation Lens.
2. Sélectionner `[A08] Access logs`.
3. Dans le sélecteur de graphique, choisir Bar, orientation verticale.
4. Repérer Horizontal axis, Vertical axis et Breakdown dans le panneau des dimensions à droite.
5. À gauche, rechercher `@timestamp`.
6. Glisser `@timestamp` vers Horizontal axis, pas vers le centre de l’aperçu.
7. Cliquer la dimension `@timestamp` créée.
8. Vérifier l’opération Date histogram.
9. Activer Customize time interval si vous voulez un intervalle explicite.
10. Choisir un minimum adapté : 1 minute pour quelques minutes de données, 5 minutes pour quelques heures, 1 heure pour plusieurs jours.
11. Fermer le volet de dimension.

Le minimum demandé peut être ajusté par Kibana pour limiter le nombre de barres. Ne pas demander des milliers d’intervalles sur une archive couvrant des années. [web:74]

### 13.2 Ajouter le comptage

1. À droite, cliquer la zone vide Vertical axis.
2. Choisir Count of records.
3. Saisir le libellé `Requêtes par intervalle`.
4. Fermer le volet.
5. Vérifier qu’une série de barres apparaît au centre.

Si toutes les requêtes tiennent dans une seule barre, vérifier l’étendue réelle des dates et réduire l’intervalle sans descendre sous une granularité utile.

### 13.3 Ajouter les classes et l’empilement

1. Dans la recherche de champs à gauche, saisir `status_class`.
2. Glisser `status_class` vers Breakdown.
3. Cliquer cette dimension.
4. Choisir Top values.
5. Régler Number of values à 6 ou davantage.
6. Si toutes les classes sont affichées et que la catégorie Other est inutile, ouvrir Advanced et désactiver Group other values as Other.
7. Fermer le volet.
8. Ouvrir les paramètres Style / options du graphique à barres.
9. Choisir Stacked pour l’empilement.
10. Ne pas choisir Percentage stacked : ici l’axe vertical doit représenter un nombre de requêtes, pas une part relative.
11. Garder la légende visible pour identifier les classes.
12. Enregistrer `[A08] Requêtes dans le temps par classe HTTP`.

Top values affiche les classes réellement présentes. L’absence de série 5xx si S = 0 est normale. Les opérations Date histogram et Top values sont configurables dans les dimensions Lens. [web:74]

### 13.4 Tester l’interaction temporelle

1. Sur le dashboard, noter la période affichée en haut à droite.
2. Dans le graphique, cliquer-glisser horizontalement sur une courte fenêtre de temps.
3. Valider le changement de période s’il est demandé.
4. Observer le changement des KPI.
5. Revenir à la période absolue du corpus avec le sélecteur de temps.
6. Cliquer Save uniquement lorsque le contexte initial est restauré.

Note formateur : demander « le nombre de requêtes a baissé, est-ce une perte de données ? ». Réponse attendue : non, nous avons restreint la période.

## 14. Visualiser la distribution des tailles

Objectif : distinguer une distribution de valeurs d’une évolution dans le temps.

1. Créer Lens → Bar verticale.
2. Glisser `bytes` dans Horizontal axis.
3. Ouvrir cette dimension et choisir Intervals / Histogram si proposé.
4. Régler une largeur d’intervalle, par exemple 10 000 octets, puis l’adapter aux valeurs du corpus.
5. Fermer la dimension.
6. Dans Vertical axis, choisir Count of records.
7. Dans la barre KQL locale de Lens, saisir `bytes: *`.
8. Vérifier que cette barre appartient à l’éditeur du panneau, pas au dashboard global.
9. Enregistrer `[A08] Distribution des tailles connues`.

Si l’opération Intervals n’est pas disponible, utiliser cette alternative guidée dans la même dimension horizontale :

1. Choisir Filters à la place du champ d’axe.
2. Cliquer Add a filter pour chaque tranche.
3. Ajouter les filtres et leurs libellés :

| Filtre KQL | Libellé |
|---|---|
| `bytes >= 0 and bytes < 1000` | `< 1 000 octets` |
| `bytes >= 1000 and bytes < 10000` | `1 000 à 9 999` |
| `bytes >= 10000 and bytes < 100000` | `10 000 à 99 999` |
| `bytes >= 100000` | `100 000 et plus` |

4. Garder Count of records en axe vertical.
5. Nommer cette variante `[A08] Tailles connues par tranches` : les classes n’ont pas toutes la même largeur, ce n’est pas un histogramme à classes égales.

## 15. Identifier les chemins et méthodes contributeurs

### 15.1 Top 10 des chemins en erreur

1. Créer Lens → Bar, orientation horizontale.
2. Glisser `url_path` dans l’axe des catégories, généralement Vertical axis pour des barres horizontales.
3. Ouvrir la dimension → Top values → Number of values = 10.
4. Choisir un classement par Count of records décroissant.
5. Dans l’axe numérique, généralement Horizontal axis, choisir Count of records.
6. Dans la barre KQL locale Lens, saisir `status >= 400 and status < 600`.
7. Fermer les dimensions et vérifier les libellés des chemins.
8. Enregistrer `[A08] Top 10 chemins en erreur HTTP`.

Si aucune erreur n’existe, conserver le constat. Pour apprendre l’interface avec des données visibles, créer séparément un panneau « Top 10 chemins — tous statuts » sans le filtre, sans le présenter comme des erreurs.

### 15.2 Trafic par méthode

1. Créer un nouveau Lens → Bar horizontale.
2. Glisser `method` dans l’axe des catégories → Top values → 10 valeurs.
3. Dans l’axe numérique, choisir Count of records.
4. Ne pas appliquer de filtre local d’erreur.
5. Enregistrer `[A08] Requêtes par méthode`.

## 16. Construire une table agrégée

1. Créer Lens et sélectionner le type Table.
2. Glisser `url_path` dans Rows.
3. Ouvrir la dimension → Top values → 10 valeurs.
4. Cliquer la zone Metrics → Count of records ; libellé `Requêtes`.
5. Cliquer Add metric ou la zone vide suivante dans Metrics.
6. Choisir Formula et saisir `count(kql='status >= 400 and status < 500')` ; libellé `4xx`.
7. Ajouter une métrique Formula `count(kql='status >= 500 and status < 600')` ; libellé `5xx`.
8. Ajouter une métrique Formula avec le ratio de la section 12.1 ; libellé `Part 5xx`, format Percent.
9. Ajouter une métrique Sum sur `bytes`, format Bytes ; libellé `Octets connus`.
10. Cliquer la colonne Requêtes pour trier décroissant si le tri interactif est disponible ; sinon utiliser les paramètres de classement de Rows.
11. Enregistrer `[A08] Routes — volume et erreurs`.

Le ratio est calculé pour chaque chemin. Une route avec une requête et un échec peut afficher 100 % ; lire le volume avec le taux. Un top 10 n’est pas le total du corpus. [file:38]

## 17. Créer une heatmap temps × classe HTTP

1. Créer Lens → Heat map.
2. Glisser `@timestamp` sur Horizontal axis → Date histogram.
3. Choisir un intervalle adapté à la période comme en section 13.
4. Glisser `status_class` sur Vertical axis → Top values → 6 valeurs.
5. Dans Cell value, choisir Count of records.
6. Ouvrir les réglages de palette et choisir un dégradé séquentiel lisible.
7. Garder la légende visible.
8. Enregistrer `[A08] Intensité du trafic — temps et classe`.
9. Survoler une cellule et lire la classe, l’intervalle et le nombre de requêtes.

Il s’agit d’une matrice de comptages, pas d’une carte géographique. Si les 2xx dominent, créer une variante locale filtrée sur les erreurs et adapter son titre. Ne pas modifier silencieusement le filtre global. [file:38]

## 18. Ajouter les contrôles et assembler le dashboard

### 18.1 Liste déroulante « Méthode »

1. Ouvrir le dashboard → Edit.
2. Cliquer Add → Controls → Control, ou Controls → Add control.
3. Choisir Select a field si le choix de source est proposé.
4. Data view : `[A08] Access logs`.
5. Field : `method`.
6. Control type : Options list.
7. Label : `Méthode`.
8. Autoriser plusieurs sélections pour cet exercice.
9. Cliquer Save ou Save and close.
10. Sélectionner GET dans le nouveau contrôle.
11. Vérifier que Requêtes diminue ou reste égal au total.
12. Effacer la sélection pour revenir à tous les documents.

### 18.2 Ajouter classe HTTP et chemin

Recommencer les étapes précédentes avec :

| Champ | Type | Libellé |
|---|---|---|
| `status_class` | Options list | `Classe HTTP` |
| `url_path` | Options list | `Chemin` |
| `bytes` | Range slider | `Taille connue` |

Pour le Range slider, déplacer une borne puis observer le filtrage. Retirer ensuite la sélection : ce contrôle peut exclure les documents sans taille. Les contrôles filtrent les panneaux pertinents selon leurs champs et sources. [web:59][web:60]

### 18.3 Ajouter la table Discover

1. Dashboard en mode Edit → Add → From library / Add from library.
2. Rechercher `[A08] Détail des erreurs HTTP`.
3. Choisir la session Discover enregistrée.
4. Fermer le volet d’ajout.
5. Agrandir le panneau pour lire plusieurs lignes.
6. Vérifier que la table reste dédiée aux erreurs tandis que le KPI Requêtes compte tout le corpus.

### 18.4 Ajouter un panneau texte

1. Cliquer Add → Text, ou le panneau texte/Markdown proposé.
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
5. Placer heatmap et top chemins côte à côte, puis la table des routes et la table Discover en bas.
6. Sauvegarder le dashboard.

## 19. Vérifier un panneau avec Inspect

1. Retirer les filtres de test et restaurer la période complète.
2. Sur la tuile Requêtes, ouvrir le menu `…`.
3. Choisir Inspect si proposé ; sinon ouvrir la visualisation, puis More → Inspect.
4. Dans View, choisir Data pour voir la valeur renvoyée.
5. Choisir Requests pour examiner la requête Elasticsearch.
6. Repérer le filtre de date et vérifier qu’il couvre le corpus.
7. Utiliser Open in Console si proposé pour examiner la requête sans la modifier.
8. Fermer Inspect et comparer le résultat aux références de la section 6.

Ne pas comparer un comptage Elasticsearch sans filtre à un panneau limité à une méthode ou à une période différente. L’inspecteur permet de consulter les données, requêtes et, selon le panneau, d’exporter le tableau en CSV. [web:74]

## 20. Alertes : comprendre règle, alerte et action

| Terme | Sens dans l’exercice |
|---|---|
| Rule / règle | Vérification planifiée : compter les 5xx récents toutes les minutes |
| Condition | Nombre de 5xx strictement supérieur à zéro |
| Alert / alerte | Instance active lorsque la condition est vraie |
| Recovery | La condition redevient fausse lors d’une exécution ultérieure |
| Connector | Configuration de connexion à un service de notification |
| Action | Notification ou autre opération exécutée selon la configuration |

Une règle n’utilise pas automatiquement la période absolue du dashboard. Elle évalue sa propre fenêtre glissante, par exemple les cinq dernières minutes. Une archive de 2017 ne peut donc pas déclencher une règle basée sur les cinq dernières minutes de `@timestamp`. [web:44][web:51]

### 20.1 Vérification formateur obligatoire

Avant de faire réaliser les manipulations aux débutants :

1. Ouvrir Rules via la recherche globale.
2. Vérifier la présence du type Index threshold.
3. Vérifier les droits de création de règles et la lecture de l’index de démonstration.
4. Faire configurer par l’administrateur une clé persistante `xpack.encryptedSavedObjects.encryptionKey` d’au moins 32 caractères.
5. Vérifier la configuration de sécurité/API keys et les exigences TLS du déploiement.
6. Vérifier la disponibilité et les conditions de licence du connecteur envisagé.
7. Si le lab initial sans sécurité ne permet pas l’alerting, préparer une variante sécurisée avant la séance. Ne pas demander aux stagiaires d’activer la sécurité au milieu de l’exercice.

Les fonctions d’alerte peuvent être bloquées par l’absence de clé de chiffrement ou de configuration requise. Ne pas contourner les droits ni désactiver TLS pour « débloquer » l’atelier. [web:66][web:67]

## 21. Préparer un corpus récent séparé pour tester les règles

Objectif : provoquer une alerte sans polluer les vrais access logs.

### 21.1 Créer l’index de simulation

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

### 21.2 Créer un pipeline d’horodatage de test

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

## 22. Créer une règle 5xx et observer son cycle de vie

### 22.1 Créer la règle avant d’injecter les documents

1. Ouvrir Rules par la recherche globale ; dans une navigation classique, Stack Management → Rules.
2. Cliquer Create rule.
3. Choisir Index threshold.
4. Name : `[A08-DEMO] Au moins un 5xx récent — binomeXX` ; remplacer XX par votre identifiant.
5. Indices : `atelier08-alert-demo`.
6. Time field : `@timestamp`.
7. Dans WHEN, choisir count.
8. Dans OVER, choisir all documents ; ne pas activer de regroupement pour ce premier test.
9. Comparaison : is above.
10. Seuil : `0`.
11. Dans FOR THE LAST, saisir `5`, unité minutes.
12. Dans le filtre KQL optionnel, saisir `status >= 500 and status < 600`.
13. Check interval : `1 minute`, ou le minimum autorisé par l’environnement si supérieur.
14. Si un nombre d’exécutions consécutives est proposé, conserver `1` pour ce test.
15. Ne pas ajouter d’action externe à ce stade. Si un avertissement indique qu’aucune notification ne sera envoyée, le distinguer d’une impossibilité de créer la règle.
16. Cliquer Save / Create rule.

La règle Index threshold propose les clauses WHEN, OVER/GROUPED OVER, la comparaison, la fenêtre et le filtre KQL. [web:44]

### 22.2 Injecter un événement de test récent

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

### 22.3 Voir l’alerte

1. Revenir à Rules.
2. Ouvrir la règle créée.
3. Attendre l’exécution planifiée, puis rafraîchir la page ; le scheduler peut ajouter un délai.
4. Ouvrir l’onglet Alerts ou la liste d’alertes associées à la règle.
5. Vérifier qu’une instance active apparaît.
6. Ouvrir Execution history / l’historique d’exécution pour distinguer une règle exécutée sans correspondance d’une règle en erreur.
7. Noter l’heure du document, l’heure de vérification et le résultat.

### 22.4 Observer la récupération

1. Ne plus injecter de 5xx.
2. Attendre que le dernier 5xx sorte de la fenêtre de cinq minutes, puis une nouvelle exécution de la règle.
3. Rafraîchir les détails.
4. Vérifier que l’alerte devient récupérée/inactive selon le libellé de l’écran ; l’historique conserve sa trace.
5. Comprendre qu’injecter un 200 ne neutralise pas un 503 encore dans la fenêtre.
6. Désactiver la règle en fin de séance pour éviter de laisser tourner les tests.

Une alerte active puis récupérée valide le cycle ; cliquer seulement sur un bouton de test ne prouve pas que l’exécution planifiée fonctionne. [web:44]

## 23. Ajouter une notification, uniquement si le connecteur est autorisé

Parcours optionnel, préparé avec le formateur. Une règle peut être étudiée sans envoyer de message externe.

1. Ouvrir la règle → Edit.
2. Aller dans Actions → Add action.
3. Sélectionner un connecteur déjà configuré pour le lab, par exemple un connecteur de journalisation serveur s’il est proposé et autorisé.
4. Ne pas saisir d’adresse personnelle ni de secret dans un support partagé.
5. Choisir une fréquence « lors du changement d’état » / « On status changes » si elle est disponible, plutôt qu’à chaque minute pendant toute la durée d’alerte.
6. Dans le message, saisir `Atelier 08 — simulation : seuil 5xx depasse.`
7. Pour ajouter le nom de règle ou les valeurs, utiliser le sélecteur de variables du formulaire. Ne pas recopier au hasard une variable d’un autre type de règle.
8. Sauvegarder.
9. Réinjecter un 503 avec la commande de la section 22.2.
10. Observer le nouvel état et faire vérifier la notification par le formateur.
11. Si l’alerte existe mais pas le message, contrôler séparément l’action, le connecteur, la fréquence et les erreurs d’exécution.

La disponibilité des actions dépend de la configuration, des droits et de la licence. Ne pas présenter l’envoi d’e-mails comme acquis sans serveur SMTP et connecteur opérationnels. [web:44][web:66]

## 24. Approfondissement guidé : comparer deux périodes

Prérequis : le corpus contient suffisamment d’événements dans deux fenêtres comparables. Sinon, constater l’absence de données ; ne pas fabriquer une tendance.

1. Ouvrir le dashboard et choisir une période contenant plusieurs heures de données.
2. Créer Lens → Line.
3. Glisser `@timestamp` sur Horizontal axis → Date histogram.
4. Dans Vertical axis, choisir Count of records ; libellé `Période courante`.
5. Ajouter une seconde métrique sur le même axe → Formula.
6. Saisir `count(shift='1h')`.
7. Libellé `Décalage 1 heure`.
8. Ne pas ajouter Top values pour ce premier exercice.
9. Enregistrer `[A08] Trafic — comparaison à H-1`.
10. Survoler un point et expliquer que les deux courbes comparent des fenêtres décalées, pas deux serveurs.

Si la période décalée ne contient pas d’événement, la comparaison n’est pas probante. Choisir `1d` n’a de sens que si le corpus couvre aussi la journée précédente. Les décalages temporels et leurs restrictions sont documentés dans Lens. [web:74]

## 25. Approfondissement guidé : référence et annotation

### 25.1 Ajouter une ligne de référence

1. Depuis le dashboard, ouvrir le panneau temporel → Edit visualization.
2. Cliquer Add layer → Reference lines.
3. Cliquer la valeur de l’axe vertical de cette couche.
4. Choisir Static.
5. Saisir une valeur pédagogique adaptée aux volumes, par exemple 20 requêtes par intervalle si le graphique utilise des volumes de cet ordre.
6. Libellé : `Repère pédagogique — pas un SLO`.
7. Régler une couleur contrastée.
8. Sauvegarder et revenir au dashboard.

Une ligne de référence visuelle ne crée aucune règle d’alerte. Son unité doit correspondre à la mesure : nombre par intervalle, et non requêtes par seconde si la métrique n’est pas normalisée. [web:74]

### 25.2 Ajouter une annotation statique

1. Réouvrir le même graphique dans Lens.
2. Cliquer Add layer → Annotations.
3. Choisir Static date.
4. Saisir une date à l’intérieur du corpus, relevée sur le graphique.
5. Nommer l’annotation `Point de discussion — aucune cause prouvée`.
6. Choisir une icône et une couleur lisibles.
7. Sauvegarder.

Ne pas étiqueter « déploiement » ou « panne » une date pour laquelle vous n’avez aucune preuve. L’annotation est ici un repère de lecture, pas une causalité établie. [web:74]

## 26. Approfondissement guidé : analyse ES|QL indépendante

Cette section change explicitement de langage. Ne pas coller cette requête dans la barre KQL du dashboard.

1. Ouvrir Discover dans un nouvel onglet pour garder le dashboard ouvert.
2. Sélectionner le mode ES|QL / Query.
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
9. Revenir au dashboard sans remplacer sa Data View par une requête.

Objectif pédagogique : KQL filtre des documents dans une Data View ; ES|QL permet d’écrire une chaîne de filtrage, agrégation et tri. Les visualisations en mode Query constituent un parcours distinct dans Lens. [web:74]

## 27. Carte guidée reproductible, séparée du corpus réel

Objectif : apprendre Maps même sans base GeoIP disponible. Les trois coordonnées suivantes sont des repères de villes et ne localisent aucune IP de votre corpus.

### 27.1 Préparer trois documents synthétiques

Dans Console :

```http
PUT atelier08-map-demo
{
  "settings": {"number_of_shards": 1, "number_of_replicas": 0},
  "mappings": {
    "properties": {
      "city": {"type": "keyword"},
      "geo_source": {"type": "keyword"},
      "location": {"type": "geo_point"}
    }
  }
}
```

Puis exécuter les trois requêtes suivantes séparément :

```http
PUT atelier08-map-demo/_doc/paris?refresh=wait_for
{"city":"Paris","geo_source":"simulation","location":{"lat":48.8566,"lon":2.3522}}
```

```http
PUT atelier08-map-demo/_doc/tunis?refresh=wait_for
{"city":"Tunis","geo_source":"simulation","location":{"lat":36.8065,"lon":10.1815}}
```

```http
PUT atelier08-map-demo/_doc/montreal?refresh=wait_for
{"city":"Montréal","geo_source":"simulation","location":{"lat":45.5017,"lon":-73.5673}}
```

Créer une Data View `[A08] Carte SIMULATION` sur le motif exact `atelier08-map-demo`, en choisissant l’option sans filtre temporel : ces documents ne contiennent volontairement pas de date. Ils ne doivent pas entrer dans les métriques de trafic.

### 27.2 Créer la carte

1. Ouvrir Maps par la recherche globale.
2. Cliquer Create map.
3. Cliquer Add layer.
4. Choisir Documents.
5. Data view : `[A08] Carte SIMULATION`.
6. Champ géographique : `location`.
7. Dans les propriétés de couche, ajouter `city` et `geo_source` aux Tooltip fields.
8. Donner à la couche le nom `Repères de villes — SIMULATION`.
9. Cliquer Add layer / Save & close selon le volet.
10. Utiliser l’action Fit to data / ajuster aux données, ou dézoomer jusqu’à voir les trois villes.
11. Survoler les points et vérifier leurs infobulles.
12. Sauvegarder `[A08] Carte — SIMULATION sans IP réelle`.
13. Dans le dashboard en mode Edit, choisir Add from library et ajouter cette carte.
14. Ajouter un texte visible : `Carte pédagogique indépendante : aucune provenance réelle des requêtes n’est représentée.`

Si le fond ne charge pas, distinguer les points du service de fond cartographique : faire vérifier les accès réseau et la configuration par le formateur. Ne pas contourner TLS. Si un filtre global du dashboard vide une couche indépendante, retirer ce filtre et tester Maps seul. [file:38]

### 27.3 Extension GeoIP réelle, si la base est disponible

Le parcours reproductible ci-dessus ne remplace pas un enrichissement réel. Pour ce dernier :

1. Dans Console, exécuter `GET _ingest/geoip/stats`.
2. Faire préparer par le formateur le pipeline GeoIP de l’annexe.
3. Ouvrir un document source et copier une IP publique réellement présente.
4. Dans la requête `_simulate` de l’annexe, remplacer l’IP de boucle locale par cette IP.
5. Exécuter et vérifier `client_geo.location` ou les tags de diagnostic.
6. Réindexer seulement après un test concluant, dans un index séparé.
7. Créer une Data View exacte sur cet index enrichi.
8. Dans Maps, reprendre les clics de la section 27.2 avec `client_geo.location` comme champ géographique.
9. Mesurer la couverture avant d’interpréter la carte. Une IP privée ou une base indisponible peut ne produire aucun point.

Ne jamais attribuer arbitrairement Paris à une IP réelle pour faire apparaître un point. [file:38]

## 28. Scénario final guidé et corrigé attendu

### Travail participant

1. Ouvrir le dashboard enregistré.
2. Effacer les filtres temporaires et restaurer la période absolue du corpus.
3. Noter Requêtes, 4xx, 5xx et part d’erreurs.
4. Dans le contrôle Classe HTTP, sélectionner une classe d’erreur réellement présente.
5. Dans le Top 10, relever le chemin le plus fréquent.
6. Sélectionner ce chemin dans le contrôle Chemin.
7. Lire au moins trois documents de la table Discover, s’ils existent.
8. Ouvrir un document dans Discover pour examiner `message`.
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
- Le dashboard d’archive et la règle sur cinq minutes n’observent pas la même fenêtre.
- Une alerte et une notification ne sont pas la même chose.
- La carte de simulation n’apporte aucune preuve sur la provenance des vraies requêtes.

## 29. Sauvegarder, exporter et transmettre

### 29.1 Vérifier la réouverture

1. Cliquer Save sur le dashboard.
2. Revenir à la liste Dashboards.
3. Réouvrir `[A08] Diagnostic Access logs`.
4. Vérifier titres, contrôles, table Discover et période.
5. Vérifier qu’aucun filtre de test n’est resté actif.
6. Tester la lecture avec un compte autorisé si le formateur en fournit un.

### 29.2 Exporter les objets Kibana

1. Ouvrir Saved Objects par la recherche globale.
2. Rechercher le dashboard par son nom.
3. Cocher le dashboard voulu.
4. Cliquer Export.
5. Inclure les objets liés si l’option est proposée.
6. Conserver l’export NDJSON avec le compte rendu.

L’export des objets Kibana ne sauvegarde pas les documents Elasticsearch. Ne pas supposer qu’il constitue une sauvegarde portable des règles, des secrets ou des connecteurs ; prévoir leur gestion séparément selon les possibilités du déploiement. [file:38][web:71]

## 30. Dépannage rapide et critères de réussite

| Symptôme | Vérification guidée |
|---|---|
| Aucun document dans Discover | Console `_count`, puis Data View exacte, période absolue, filtres |
| KQL 5xx renvoie zéro | Exécuter le `_count` range de la section 6.3 |
| Erreur de syntaxe dans une formule | Onglet Formula ; apostrophes droites ; parenthèses ; pas dans la barre KQL |
| `status` absent | Ouvrir un document et vérifier le schéma source ; ne pas renommer au hasard |
| Champ numérique non agrégeable | `_field_caps`, mapping et source correcte |
| Taux affiché 200 % au lieu de 2 % | Retirer le `* 100` si format Percent |
| Taux à 100 % partout | Retirer le filtre global d’erreurs et vérifier le dénominateur |
| Courbe avec une seule barre | Dates réellement présentes et intervalle de l’histogramme |
| Aucun 5xx dans la légende | Vérifier S ; une classe absente n’a pas de série |
| Règle impossible à créer | Droits, sécurité, clé chiffrante persistante, configuration et licence |
| Règle saine mais aucune alerte | Index exact, propre fenêtre de cinq minutes, date récente, seuil |
| Alerte sans notification | Action/connector, fréquence, droits, historique d’exécution |
| Un 200 n’efface pas l’alerte | Le 503 reste dans la fenêtre jusqu’à expiration |
| Carte sans points | Data View exacte, geo_point, filtres et données de la couche |
| Totaux doublés | Motif trop large incluant index réel et copies |

### Grille d’évaluation

| Critère | Preuve attendue |
|---|---|
| Prérequis | Index source rempli, projection validée, pas de suppression de source |
| Recherche | Participant distingue KQL, Formula et Console |
| KPI | N, C, S et B cohérents avec la référence |
| Taux | Dénominateur nommé et format Percent correct |
| Temps | Période absolue documentée et histogramme lisible |
| Interaction | Deux contrôles testés, filtres remis à zéro |
| Investigation | Table documentaire et hypothèse sans cause inventée |
| Alerte | Règle exécutée, événement de simulation, état actif puis récupéré |
| Avancé | Inspect et au moins un exercice comparaison / annotation / ES|QL |
| Carte | Simulation explicitement identifiée ou couverture GeoIP documentée |
| Conservation | Dashboard sauvegardé ; règle de test désactivée |

### Note formateur à faire reformuler

« Je sais quelle donnée je compte, sur quelle période et avec quels filtres. Je vérifie les résultats Elasticsearch avant de conclure qu’une formule est fausse. Je distingue un graphique historique d’une règle planifiée et une simulation d’un événement réel. »

## 31. Sources et limites de validation

- Les fichiers de départ définissent le schéma, le corpus et la séparation entre projection réelle et démonstrations. [file:37][file:38]
- La syntaxe des plages KQL est documentée par Elastic. [web:52]
- Lens documente les dimensions, formules, pourcentages, décalages, annotations et Inspect. [web:74]
- Les procédures de création de dashboard et de contrôles suivent les fonctions documentées. [web:59][web:62]
- Les règles Index threshold et leurs prérequis sont documentés séparément du dashboard. [web:44][web:66][web:67]

Ce document est un guide préparé pour 9.5.7, pas un procès-verbal de test de votre instance. Le formateur doit confirmer les libellés, droits et connecteurs sur le Space de formation avant diffusion. Les chiffres dépendent du corpus importé ; aucun succès de réindexation, affichage ou déclenchement réel n’est présumé.

## Annexe A — Définition du pipeline GeoIP réel (formateur)

### Préconditions et limites

- Base GeoIP disponible et à jour sur les nœuds d’ingestion.
- Accès réseau et politique du lab compatibles avec son téléchargement, ou base gérée par le formateur.
- IP publiques résolubles ; IP privées, réservées, proxys ou données anciennes peuvent ne pas produire de coordonnées.
- Une localisation IP est approximative et peut représenter un fournisseur ou un point de sortie, pas l’utilisateur.

### Vérifier l’état et créer le pipeline

```http
GET _ingest/geoip/stats
```

```bash
curl -X PUT "$ES_URL/_ingest/pipeline/atelier08-geoip" \
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
curl -X PUT "$ES_URL/atelier08-access-geoip" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json

curl -X POST "$ES_URL/_reindex?refresh=true" \
  -H 'Content-Type: application/json' --data-binary @geoip-reindex.json \
  -o geoip-reindex-response.json
python3 -m json.tool geoip-reindex-response.json
```

Ce second pipeline ne réécrit pas ingested_at. Les IDs sont conservés dans une copie enrichie ; ne pas inclure source et copie dans la même Data View de volume.

Créer [A08] Access GeoIP sur atelier08-access-geoip avec @timestamp. Mesurer les documents ayant client_geo.location et le total. Si aucune coordonnée n’est produite, conserver le constat et utiliser le parcours B. Chercher les tags _geoip_failed, _geoip_expired_database ou de base indisponible, et consulter les statistiques/logs selon le cas.


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
