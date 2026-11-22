# Atelier 08 — Data Observability avec Kibana : dashboard complet des access logs

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 3, atelier 08 |
| Durée | 3 h à 3 h 30 ; GeoIP réel en prolongement si nécessaire |
| Environnement | Kibana et Elasticsearch 9.x de l’atelier 01 |
| Prérequis | access_log indexé dans atelier03-access ; mapping et Bulk de l’atelier 03 |
| Corpus principal | Vrais événements du fichier access_log fourni, ou sa copie actualisée |
| Index dashboard | atelier08-access, projection dédiée et non destructive |
| Outils | Discover, Data Views, Lens, Dashboards, Controls, Maps, Console |
| Livrables | Dashboard complet, investigation sauvegardée, contrôle des indicateurs et carte documentée |

## 1. Objectif de formation : observer, diagnostiquer, vérifier

Le but n’est pas d’aligner des graphiques décoratifs. Le participant doit repérer une anomalie, formuler une hypothèse, retrouver les requêtes concernées et expliquer les limites de ses indicateurs.

```text
Logs déjà indexés → contrôles qualité → enrichissement explicable
→ Discover → histogramme / table / heatmap → dashboard interactif
→ carte → scénario d’investigation → validation Elasticsearch
```

### Objectifs pédagogiques

- Distinguer santé du service web, qualité de sa télémétrie et qualité métier des données.
- Définir précisément un compteur et le dénominateur d’un taux.
- Vérifier dates, types, champs manquants et unité d’observation.
- Construire métriques, histogrammes, barres, tables et heatmap.
- Ajouter une table documentaire Discover pour revenir aux preuves.
- Créer une carte à partir d’un geo_point, via GeoIP ou un corpus de coordonnées explicitement simulées.
- Expliquer filtres globaux, locaux, période et interactions.
- Livrer un dashboard lisible et réouvrable, avec limites et contrôles chiffrés.

L’installation de Kibana n’est pas répétée. Les menus varient selon version et droits ; utiliser la recherche de navigation. Les manipulations décrites sont en mode Data View/KQL, pas ES|QL pour ce premier dashboard.

## 2. Ce que les access logs permettent réellement de mesurer

| Question d’observabilité | Signal disponible | Limite |
|---|---|---|
| Le trafic augmente-t-il ou disparaît-il ? | Nombre de requêtes dans le temps | Zéro log peut signifier absence de trafic ou panne de collecte |
| Le service répond-il en erreur ? | Statuts 4xx, 5xx et leur part | Un 404 n’a pas la même signification qu’un 503 |
| Quels chemins sont concernés ? | url_path, méthode, statut | Un chemin seul ne prouve pas la cause racine |
| Les événements sont-ils récents ? | Dernier @timestamp, comparaison à ingested_at | Une archive rejouée paraît volontairement ancienne |
| Les champs sont-ils exploitables ? | Part sans méthode, statut, taille, coordonnées | Certains champs manquants sont légitimes |
| D’où viennent les requêtes localisées ? | GeoIP ou coordonnées déclarées | Une IP n’identifie pas une personne ni sa position exacte |
| Quelle est la latence HTTP ? | Non disponible dans le format utilisé | Ne pas confondre taille en octets et durée |

Une ligne d’access log représente une requête journalisée, pas une personne, une session ou une exécution de pipeline. Unique count de client_ip donne une estimation d’IP distinctes, pas un nombre exact de visiteurs.

Les erreurs HTTP ne prouvent pas une anomalie de qualité des fichiers MovieLens. Ce dashboard observe le service et sa télémétrie ; la fraîcheur, le volume, le schéma, la distribution et la complétude sont des dimensions à discuter, pas des diagnostics automatiques.

## 3. Connexion et organisation des commandes

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

## 6. Mesurer la période et établir les références chiffrées

### Objectif

Adapter le dashboard aux vraies dates et comparer ses mesures à Elasticsearch.

```bash
curl -X POST "$ES_URL/atelier08-access/_search" \
  -H 'Content-Type: application/json' --data-binary @access-bornes-query.json \
  -o access-bornes.json

curl -X POST "$ES_URL/atelier08-access/_search" \
  -H 'Content-Type: application/json' --data-binary @access-validation-query.json \
  -o access-validation.json
```

La première requête retourne les dates minimale/maximale d’événement et d’ingestion. La seconde calcule volume, classes de statut, erreurs, somme des octets connus, champs manquants et couverture géographique.

Dans Console, on peut envoyer directement le contenu JSON des fichiers après POST atelier08-access/_search.

### Tableau de référence à compléter

| Mesure | Source de contrôle |
|---|---|
| Requêtes | hits.total.value avec relation eq |
| Statuts valides | statuts_valides.doc_count, plage 100 à 599 |
| 4xx + 5xx | erreurs_http.doc_count |
| 5xx | erreurs_serveur.doc_count |
| Octets connus | octets_connus.value |
| Sans date / méthode / statut / taille | buckets sans_* |
| Géolocalisés | geolocalises.doc_count |

Il n’y a pas de total imposé : version du fichier, taille de l’échantillon et rejets de préparation peuvent différer. Les références de l’ancien corpus atelier07-events ne s’appliquent plus.

Une ligne sans date n’apparaîtra pas normalement dans une recherche filtrée sur @timestamp. Si sans_date est non nul, investiguer avant de comparer le total brut aux panneaux temporels.

## 7. Créer la Data View et fixer la période

### Procédure

1. Ouvrir Data Views via la navigation.
2. Create data view.
3. Name : [A08] Access logs.
4. Index pattern exact : atelier08-access.
5. Timestamp field : @timestamp.
6. Enregistrer dans le Space du lab.
7. Dans Discover, choisir une période absolue couvrant premier_evenement à dernier_evenement, avec une petite marge aux bornes.

### Explication

La Data View ne copie pas les documents ; elle décrit leur accès dans Kibana. Ne pas utiliser atelier08-access* : cela mélangerait plus tard les copies GeoIP et la démonstration et doublerait artificiellement les volumes.

Utiliser UTC si le formateur l’a prévu, sinon noter le fuseau navigateur et convertir correctement. Ne pas modifier les réglages de tout un Space partagé sans accord.

Last 15 minutes ne retrouve pas une archive ancienne. L’auto-refresh ne rajeunit pas les événements. Choisir la période à partir des données, pas en réimportant jusqu’à voir des points.

## 8. Explorer les requêtes dans Discover

### Objectif

Comprendre les documents avant leurs agrégations.

Ajouter les colonnes :

```text
@timestamp
event_id
client_ip
method
url_path
status
bytes
message
```

Trier par @timestamp. Développer une requête pour comparer path et url_path. Les octets absents ne doivent pas avoir été inventés à zéro.

### KQL d’investigation

```kql
status >= 500 and status < 600
```

```kql
status >= 400 and status < 500
```

```kql
method : "GET" and status : 404
```

```kql
not method : *
```

```kql
url_path : "/robots.txt"
```

Le nom et l’existence de /robots.txt dépendent du corpus ; zéro résultat est acceptable. Un champ method absent peut correspondre à une requête atypique conservée par le parseur, pas nécessairement à une perte de ligne.

## 9. Sauvegarder l’investigation documentaire

### Procédure

- Garder les colonnes utiles.
- Définir la requête locale : status >= 400 and status < 600.
- Retirer les filtres temporaires sur IP et chemin.
- Sauvegarder : [A08] Requêtes HTTP en erreur — détail.

Cette session Discover sera une table de vrais documents dans le dashboard. Une table Lens agrégée a une autre finalité ; ne pas agréger message pour afficher chaque log.

## 10. Créer le dashboard et son contrat de lecture

### Procédure

1. Dashboards → Create dashboard.
2. Période absolue du corpus, barre KQL vide et aucun filtre temporaire hérité.
3. Nom : [A08] Data Observability — Access logs.
4. Sauvegarder la période si proposé.
5. Ajouter un panneau texte avec : source, taille de l’échantillon, fuseau, bornes, sens des taux et absence de mesure de latence.

### Règle commune

Pour toutes les visualisations suivantes : créer depuis le dashboard en édition, sélectionner [A08] Access logs, configurer, titrer avec unité, puis Save and return. Revenir au contexte global pour valider les valeurs.

Un bouton absent peut indiquer un privilège manquant ; ne pas ouvrir l’accès anonyme pour contourner le problème.

## 11. KPI : volume, erreurs et trafic transféré

### Objectif

Obtenir une première lecture en quelques secondes.

| Panneau Lens Metric | Configuration |
|---|---|
| [A08] Requêtes journalisées | Count of records |
| [A08] Réponses 4xx | count(kql='status >= 400 and status < 500') |
| [A08] Réponses 5xx | count(kql='status >= 500 and status < 600') |
| [A08] Octets de réponse connus | Sum bytes, format Bytes |
| [A08] IP distinctes estimées | Unique count client_ip |

Count of records n’est pas un débit par seconde. Sum bytes n’est ni la taille totale du pipeline ni une durée. Unique count est approximatif et affecté par NAT, proxys et robots.

L’absence de 5xx dans l’échantillon est un résultat valide : ne pas ajouter de fausses erreurs aux vraies requêtes pour rendre le graphique intéressant.

## 12. Formules : nommer le numérateur et le dénominateur

### Taux 5xx parmi les requêtes à statut valide

```text
count(kql='status >= 500 and status < 600') / count(kql='status >= 100 and status < 600')
```

Format Percent, deux décimales, sans multiplier par 100. Titre : [A08] Part 5xx — statuts valides.

### Taux d’erreurs HTTP 4xx + 5xx

```text
count(kql='status >= 400 and status < 600') / count(kql='status >= 100 and status < 600')
```

### Complétude des méthodes

```text
count(kql='method: *') / count()
```

### Couverture géographique — zéro est acceptable avant enrichissement

```text
count(kql='client_geo.location: *') / count()
```

Les formules sont évaluées dans le contexte du panneau. Si l’on filtre globalement sur status:503, le taux 5xx du sous-ensemble devient 100 %. Cela ne prouve pas une panne générale.

Si le dénominateur est nul, afficher une absence de valeur plutôt que prétendre « aucune erreur ». Les codes 4xx et 5xx ne doivent pas être assimilés automatiquement à un SLO universel de disponibilité : définir les routes, exclusions et requêtes éligibles.

## 13. Histogramme temporel du trafic par classe HTTP

### Procédure Lens

1. Type : barres verticales empilées.
2. Axe horizontal : @timestamp, Date histogram.
3. Axe vertical : Count of records.
4. Répartition : Top values status_class, taille 6 ou plus.
5. Intervalle : adapté à la période, par exemple 5 minutes pour une fenêtre courte, une heure pour plusieurs jours.
6. Titre : [A08] Requêtes dans le temps par classe HTTP.

### Explication

Lire d’abord le volume puis la part visuelle d’erreurs. Une hausse des erreurs absolues avec trafic multiplié par dix n’a pas le même sens qu’une hausse du ratio à trafic stable.

L’intervalle Auto varie avec la période et la taille du panneau. Documenter l’intervalle utilisé pour comparer deux captures. Un bucket vide n’est pas une preuve suffisante de panne de collecte.

## 14. Histogramme numérique de taille de réponse

### Procédure

1. Lens, barres verticales.
2. Axe horizontal : bytes avec Intervals / Histogram, par exemple tranches de 10 000 octets selon la distribution observée.
3. Axe vertical : Count of records.
4. Filtre local : bytes:*.
5. Titre : [A08] Distribution des tailles de réponse connues.

Si la version ne propose pas ce type de bucket dans Lens, utiliser l’éditeur d’agrégations Histogram ou des filtres par tranches dans une visualisation en barres. Ne pas utiliser une agrégation Top values sur chaque valeur d’octets pour simuler un histogramme.

### Explication

Histogramme numérique = répartition par intervalles de valeurs ; histogramme temporel = comptage par fenêtres de temps. Les réponses sans bytes sont exclues et doivent être suivies séparément. Une taille nulle peut être réelle ; elle ne signifie pas forcément un champ manquant.

## 15. Barres et répartition : localiser les contributeurs

Créer deux panneaux :

| Panneau | Dimension | Mesure / filtre |
|---|---|---|
| [A08] Chemins générant des 4xx/5xx | Top values url_path, taille 10 | Count ; filtre local status >= 400 and status < 600 |
| [A08] Trafic par méthode HTTP | Top values method | Count |

Une troisième variante en anneau sur status_class est facultative. Si les compteurs sont très déséquilibrés, préférer les barres pour comparer les petites catégories.

Top 10 n’est pas une liste exhaustive. Un même chemin avec de nombreuses query strings peut générer une forte cardinalité dans path ; url_path les regroupe volontairement. Cette simplification peut aussi fusionner des usages métier différents : discuter le besoin.

## 16. Construire une table agrégée exploitable

### Table Lens

| Colonne | Configuration |
|---|---|
| Chemin | Top values url_path, taille 10 |
| Requêtes | Count of records |
| 4xx | count(kql='status >= 400 and status < 500') |
| 5xx | count(kql='status >= 500 and status < 600') |
| Part 5xx | formule de la section 12, Percent |
| Octets connus | Sum bytes |

Titre : [A08] Routes — volume et erreurs. Trier par volume ou nombre de 5xx, en indiquant le choix.

### Explication

La formule est calculée par ligne dans le contexte du chemin. Une route avec une requête et une erreur peut avoir 100 %, sans être la plus importante en nombre d’échecs. Afficher le volume avec le taux.

Les sommes d’un top de routes peuvent être inférieures au total global. Ne pas conclure immédiatement à un défaut d’ingestion.

## 17. Heatmap : repérer les plages et catégories anormales

### Objectif

Croiser deux dimensions, avec une valeur exprimée par la couleur.

### Procédure Lens

1. Type : Heat map.
2. Axe horizontal : @timestamp, Date histogram.
3. Axe vertical : Top values status_class.
4. Cell value : Count of records.
5. Choisir une palette séquentielle ; renseigner une légende.
6. Titre : [A08] Intensité du trafic — temps × classe HTTP.

### Lecture

Une cellule représente un nombre de requêtes pour une classe et un intervalle. La couleur n’est pas une localisation géographique.

Un fort trafic 2xx peut masquer des petites cellules 5xx dans une échelle commune. Créer une variante locale status >= 400 and status < 600, ou une heatmap temps × url_path des erreurs, sans changer le sens du titre.

Une case sans observation n’est pas automatiquement un taux de zéro. Ne pas confondre cette matrice avec une couche Heat map dans Maps, qui montre une densité spatiale.

## 18. Qualité et fraîcheur de la télémétrie

### Panneaux qualité

- Complétude méthode : formule de la section 12.
- Requêtes sans taille : count(kql='not bytes: *').
- Statuts manquants : count(kql='not status: *').
- Dernier événement observé : Max @timestamp, format date si disponible, ou table/Discover trié décroissant avec une ligne.
- Dernière ingestion de projection : Max ingested_at, même précaution de restitution.

Si Lens de votre version ne permet pas un Max date dans Metric, utiliser une table ou une session Discover triée ; ne pas convertir une date en durée juste pour obtenir une tuile.

### Interprétation Data Observability

Un champ absent peut être un signal de parsing, un changement de format, ou une valeur inconnue légitime. Dans le format Apache, bytes='-' n’est pas un faux zéro.

Les lignes rejetées avant indexation ne sont pas visibles dans cet index : leur taux doit être calculé avec le rapport de préparation/rejets de l’atelier 03 ou des métriques du collecteur. Un dashboard basé uniquement sur les documents réussis ne prouve pas la complétude de toute la collecte.

Sur une archive rejouée, un grand écart ingested_at - @timestamp est attendu. Sur un vrai flux avec horloges synchronisées, suivre cet écart peut aider à détecter du retard, mais il faut conserver la vraie date d’ingestion dès l’entrée du pipeline.

## 19. Géographie : choisir un parcours sans bloquer la formation

### Deux parcours

| Parcours | Source des coordonnées | Usage |
|---|---|---|
| A — GeoIP réel, optionnel | Enrichissement de client_ip par une base GeoIP | Carte des événements réellement enrichis |
| B — Démonstration reproductible | Coordonnées explicites dans six documents synthétiques séparés | Apprentissage Maps, même sans base GeoIP |

Ne pas attribuer les coordonnées d’une ville aux vraies IP simplement parce que GeoIP ne répond pas. Les index et titres doivent rendre la différence visible.

Le parcours B est recommandé pour garantir l’exercice de carte ; le A montre la chaîne d’enrichissement réelle lorsque l’environnement le permet.

## 20. Parcours A — GeoIP réel, si disponible

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

## 21. Parcours B — Coordonnées explicites dans un corpus de démonstration

### Objectif

Garantir une carte reproductible sans inventer la provenance des requêtes réelles.

Les coordonnées sont des repères de villes, pas des positions personnelles. Le jeu contient six événements synthétiques, deux à Paris, deux à Tunis et deux à Montréal. Il n’y a aucune client_ip attribuée à ces villes.

### Préparer et charger

Le script lit access-bornes.json et utilise la date du premier événement réel uniquement pour placer les points de démonstration dans la même période de dashboard. Les événements restent synthétiques et séparés.

```bash
python3 preparer_geo_demo.py --bornes access-bornes.json

curl -X PUT "$ES_URL/atelier08-access-geo-demo" \
  -H 'Content-Type: application/json' --data-binary @access-dashboard-mapping.json

curl -X POST "$ES_URL/atelier08-access-geo-demo/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @geo-demo.ndjson \
  -o geo-demo-bulk-response.json
```

Contrôler les six items Bulk, pas seulement HTTP 200. Le script remplace son fichier local geo-demo.ndjson ; les IDs stables empêchent les doublons lors d’un rejeu des mêmes six événements.

Créer [A08] Géographie — SIMULATION sur le motif exact atelier08-access-geo-demo, champ temps @timestamp.

### Latitude et longitude : éviter l’inversion

Nous utilisons l’objet explicite :

```json
{"client_geo":{"location":{"lat":36.8065,"lon":10.1815}}}
```

- Latitude lat : entre -90 et 90.
- Longitude lon : entre -180 et 180.
- Le format tableau, si utilisé, est [longitude, latitude], pas l’inverse.
- Les coordonnées de ce lab sont exprimées en degrés sur le repère géographique WGS84.

Garder lat/lon nommés réduit les erreurs. Deux champs numériques séparés sans mapping geo_point ne suffisent pas à créer la couche géographique décrite ici.

## 22. Construire la carte dans Maps

### Procédure commune

1. Ouvrir Maps → Create map.
2. Add layer → Documents, ou Clusters selon la version.
3. Choisir la Data View GeoIP ou la Data View SIMULATION, jamais le motif large contenant les deux copies.
4. Choisir client_geo.location.
5. Ajouter les infobulles : client_geo.city_name, country_name, status, geo_source, event_id.
6. Colorer par status_class si disponible, ou utiliser un style simple avec légende.
7. Pour les agrégats, taille du symbole = Count ; préférer les clusters pour de nombreux documents ou des points superposés.
8. Ajuster la carte aux données.
9. Sauvegarder : [A08] Géographie des requêtes enrichies, ou [A08] Carte — SIMULATION DE COORDONNÉES.
10. Ajouter le panneau Maps au dashboard depuis la bibliothèque.

### Résultats attendus pour la simulation

Six documents mais trois positions distinctes. Sur une couche Documents, deux points à la même coordonnée peuvent se superposer ; sur une couche de clusters, le nombre affiché dépend aussi du zoom. L’absence de six symboles distincts ne prouve pas une perte de données.

Le taux d’erreurs du jeu synthétique est 3/6 = 50 %, dont deux 5xx, mais ces chiffres ne doivent jamais être fusionnés avec ceux des access logs réels.

### Carte réelle et couverture

Une carte GeoIP n’affiche que les documents géolocalisés. Afficher sa couverture dans son titre/description ou un panneau dédié sur la même Data View. Sans cette information, une zone vide pourrait être prise à tort pour une zone sans trafic.

Les filtres d’un panneau Maps et du dashboard dépendent de leurs sources et champs compatibles. Sur la simulation, un filtre de chemin réel peut vider la carte : c’est normal. Ne pas enregistrer une sélection spatiale ou un filtre de pays qui élimine silencieusement les documents réels sans coordonnées.

### Si le fond de carte ne se charge pas

Distinguer absence de points et absence de fond. Vérifier réseau navigateur/Kibana, configuration du service de fond cartographique et droits Maps. En environnement isolé, le formateur peut prévoir un fond autorisé/local ; l’apprentissage du champ geo_point ne dépend pas du succès d’un téléchargement GeoIP.

Ne pas contourner les politiques réseau ou les contrôles TLS pour afficher un fond de carte.

## 23. Assembler un dashboard complet et lisible

### Disposition proposée

```text
Contrôles : méthode / classe HTTP / code / chemin / taille
Panneau texte : source, période, échantillon et limites

Requêtes | 4xx | 5xx | Part 5xx | Octets connus | IP estimées

Histogramme temporel par classe HTTP

Heatmap temps × classe HTTP | Top chemins en erreur

Histogramme des tailles | Table routes, volume et erreurs

Qualité : méthode / statut / taille / dernier événement

Carte GeoIP ou carte SIMULATION clairement étiquetée

Table Discover : événements HTTP en erreur
```

### Contrat de lecture de la carte

Si la carte utilise les données simulées, ajouter un texte visible : « Carte pédagogique indépendante. Les points et compteurs cartographiques ne décrivent pas la géographie des access logs réels. » Les KPI restent basés exclusivement sur atelier08-access.

### Contrôles interactifs

| Contrôle | Type | Champ principal |
|---|---|---|
| Méthode | Options list | method |
| Classe HTTP | Options list | status_class |
| Statut | Options list | status |
| Chemin | Options list | url_path |
| Taille connue | Range slider si disponible | bytes |

Les listes peuvent être contraintes par période, filtres et chaînage. Un filtre bytes sélectionne les valeurs connues et peut exclure les événements sans taille. L’absence d’une valeur dans une liste n’est pas une preuve d’absence dans tout l’index.

Tous les panneaux principaux utilisent la même Data View. Les panneaux cartographiques sur une autre source doivent être identifiés et testés séparément.

## 24. Scénario d’investigation guidée

### Question

« Une hausse d’erreurs apparaît. Est-ce un incident serveur, une mauvaise route cliente, un effet de volume ou un problème de collecte ? »

### Étapes

1. Noter le volume et les taux avant tout filtre.
2. Repérer une fenêtre dans l’histogramme ou la heatmap.
3. Filtrer cette fenêtre et examiner 4xx et 5xx séparément.
4. Identifier les chemins et méthodes contributeurs.
5. Lire les messages de la table Discover pour plusieurs événements.
6. Vérifier la complétude des champs et la période de collecte.
7. Utiliser la carte réelle seulement si la couverture est connue ; ne pas inférer une attaque ou une cause à partir d’un pays.
8. Écrire une hypothèse et le contrôle complémentaire nécessaire.

### Explication attendue

Un 404 peut provenir d’un robot ou d’une ressource manquante ; un 5xx est un signal serveur mais pas une cause racine. Une chute de logs peut correspondre à moins de requêtes ou à une perte de collecte. Une archive ne prouve pas la disponibilité actuelle du service.

Le dashboard oriente l’enquête. Les ateliers Loki/Grafana permettront de compléter la lecture par les logs et des identifiants de corrélation ; une juxtaposition de graphiques n’est pas une corrélation automatique.

## 25. Vérifier les indicateurs et leurs filtres

### Procédure

1. Réinitialiser les filtres temporaires et la période personnalisée des panneaux.
2. Comparer les KPI à access-validation.json.
3. Pour un sous-ensemble, reproduire sa période et ses filtres dans la query du fichier de validation.
4. Utiliser Inspect sur un panneau si disponible pour examiner requêtes et données.
5. Documenter la source de la carte et son nombre de documents enrichis.

La comparaison entre un total brut Elasticsearch sans période et un panneau Kibana temporel n’est valide que si toutes les dates sont présentes et incluses. La Data View, les filtres locaux, épinglés et globaux doivent être identiques.

### Point pédagogique sur le ratio

Filtrer globalement status >= 500 and status < 600 fait passer la part 5xx à 100 % s’il y a des résultats. Retirer ce filtre doit rétablir la référence globale. Le filtre local de la table d’erreurs peut rester actif sans modifier les autres panneaux.

## 26. Défi final : livrer une vue d’observabilité complète

### Énoncé

Livrer [A08] Diagnostic Access logs avec :

1. Data View et période documentées.
2. KPI de volume, 4xx, 5xx et part 5xx avec bon dénominateur.
3. Histogramme temporel, histogramme numérique et barres de contributeurs.
4. Table agrégée par chemin et table documentaire des erreurs.
5. Heatmap avec deux dimensions et unité explicite.
6. Carte GeoIP ou simulation séparée, avec origine et couverture des données.
7. Au moins deux contrôles testés.
8. Un indicateur de qualité et une limite sur la fraîcheur.
9. Une validation DSL et un compte rendu d’investigation, sans cause racine inventée.

## 27. Corrigé et critères de réussite

### Corpus principal

Les chiffres de référence sont ceux de votre access-validation.json, pas un total arbitraire. Vérifier N requêtes, V statuts valides, S réponses 5xx ; le ratio est S/V si V>0.

Les histogrammes/tableaux peuvent montrer des sous-ensembles : réponses sans taille, top 10, documents sans chemin. Expliquer ces exclusions avant de rechercher une erreur technique.

### Carte simulée

- Motif exact atelier08-access-geo-demo.
- Six documents, trois positions, geo_source=simulation.
- Deux documents par ville ; un compteur de cluster dépend du zoom.
- Aucun de ces six documents dans les KPI du corpus réel.

### Note d’interprétation attendue

« Le panneau mesure les requêtes journalisées dans la période, pas les utilisateurs. Le taux 5xx est conditionné par les filtres actifs. La carte ne couvre que les documents localisés, ou utilise un corpus de démonstration clairement séparé. La latence n’est pas disponible dans ce format de log. »

Si l’environnement ne permet pas GeoIP, la carte de coordonnées explicites satisfait l’objectif technique, mais ne doit pas être présentée comme une observation réelle des clients.

## 28. Sauvegarde, partage et livrables

### Procédure

- Sauvegarder dashboard, visualisations réutilisables, carte et session Discover.
- Tester la réouverture avec une session autorisée.
- Partager une URL uniquement aux personnes ayant les droits requis.
- Exporter les Saved Objects et dépendances si autorisé sur votre version.

Un export d’objets Kibana n’inclut pas les documents Elasticsearch. Un lien partagé ne crée pas de droits. Ne pas activer l’accès anonyme pour contourner une autorisation manquante.

### Livrables

- Capture du dashboard et contrat de lecture.
- Période, fuseau et taille de l’échantillon.
- Valeurs de validation avec contexte de filtre.
- Source géographique, couverture ou mention SIMULATION.
- Scénario d’investigation et limites.
- Mapping, pipelines et scripts utilisés.

Avant diffusion : relire IP, paramètres d’URL et messages. Une IP ou une requête peut exposer des données sensibles ; conserver uniquement les informations nécessaires et appliquer la politique de protection du lab.

### Checklist du dashboard complet

- Indicateurs HTTP avec dénominateur connu.
- Histogramme temporel et histogramme de taille distincts.
- Barres des routes contributrices.
- Table agrégée et table documentaire.
- Heatmap avec deux axes et une unité.
- Carte dont l’origine et la couverture sont explicites.
- Contrôles interactifs et période vérifiés.
- Panneau qualité et avertissement sur la fraîcheur d’archive.
- Vérification Elasticsearch dans le même contexte.

## 29. Dépannage

| Symptôme | Vérifications |
|---|---|
| Discover vide | Motif exact, dates réelles, fuseau, filtres épinglés |
| Tous les taux à 100 % | Statut déjà filtré globalement, mauvais dénominateur |
| Heatmap peu lisible | Période trop large, granularité et palette, dominance des 2xx |
| Pas de latence | Champ absent du log ; ne pas utiliser bytes ou ingest_delay_ms comme latence HTTP |
| Carte sans points | geo_point, données localisées, période et filtres |
| Carte sans fond | Connectivité/configuration cartographique distincte de GeoIP |
| Seulement trois positions pour six démos | Coordonnées partagées et superposition |
| Couverture GeoIP faible | IP privées/réservées, base, réseau, champs et tags |
| Réindexation partielle | failures, collisions et source ; pas de relance aveugle |
| Nombre doublé | Data View trop large incluant source et copie enrichie |
| Panneaux incohérents | Sources ou périodes locales différentes, carte simulée indépendante |
| Objet non sauvegardable | Droits Kibana/Space ; pas de contournement public |

## 30. Conservation et suite du parcours

Conserver atelier03-access et atelier08-access ainsi que les objets Kibana. Les index géographiques optionnels sont des ressources de lab distinctes, à supprimer seulement après accord et vérification des dépendances.

Ne pas supprimer les index système Kibana. Supprimer une Data View ne supprime pas ses documents, et supprimer un index peut laisser des panneaux sans source.

L’atelier 09 poursuit l’observabilité des logs dans Loki/Grafana ; conserver des identifiants, champs et conventions de temps cohérents pour les investigations ultérieures.

## Annexe — Script de génération de la carte de démonstration

Le fichier preparer_geo_demo.py joint contient le code suivant. Il ne se connecte à aucun service et n’attribue aucune ville aux IP réelles.

```python
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Petit corpus de points fictifs, independant des vraies IP')
p.add_argument('--bornes', default='access-bornes.json')
a = p.parse_args()
response = json.loads(Path(a.bornes).read_text(encoding='utf-8'))
start = response['aggregations']['premier_evenement'].get('value_as_string')
if not start:
    raise SystemExit('Pas de date de reference : verifier le corpus et la reponse de bornes')
cities = [
    ('Paris','France','FR',48.8566,2.3522),
    ('Tunis','Tunisie','TN',36.8065,10.1815),
    ('Montreal','Canada','CA',45.5017,-73.5673),
    ('Paris','France','FR',48.8566,2.3522),
    ('Tunis','Tunisie','TN',36.8065,10.1815),
    ('Montreal','Canada','CA',45.5017,-73.5673)
]
statuses = [200,200,404,503,200,500]
with Path('geo-demo.ndjson').open('w',encoding='utf-8') as f:
    for i, ((city,country,iso,lat,lon),status) in enumerate(zip(cities,statuses),1):
        key = f'GEO-DEMO-{i:03d}'
        doc = {
            'event_id':key,'@timestamp':start,'dataset':'demo_geographique',
            'environment':'formation','service':'web-formation','method':'GET',
            'path':'/demo','url_path':'/demo','status':status,
            'status_class':f'{status//100}xx','is_http_error':status>=400,
            'message':'Evenement entierement synthetique pour la carte',
            'geo_source':'simulation',
            'client_geo':{'city_name':city,'country_name':country,
                          'country_iso_code':iso,'location':{'lat':lat,'lon':lon}}
        }
        f.write(json.dumps({'index':{'_id':key}})+'\n')
        f.write(json.dumps(doc,ensure_ascii=False)+'\n')
print(json.dumps({'documents':6,'points_distincts':3,'timestamp_reference':start,
                  'source':'simulation ; aucune IP reelle localisee'},ensure_ascii=False,indent=2))
```

## Références et validation formateur

Cette version conserve l’exploration Discover, Lens, les formules, le dashboard interactif, les contrôles, le partage et la vérification du support d’origine. Le corpus est remplacé par les access logs du parcours ; heatmap, Maps, enrichissement géographique et contrôles de qualité sont développés.

Références : Elastic, Lens et heat map charts ; GeoIP processor ; geo_point ; Maps vector layers ; Data Views et dashboard controls.


