# Atelier 06 — Modéliser les données : dénormalisation, nested et parent-child

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Programme | Data Observability — jour 2, atelier 6 sur 13 |
| Durée indicative | 2 heures ; comparaison automatisée en bonus si nécessaire |
| Référence | Elasticsearch 9.x sur Ubuntu, sans Docker |
| Prérequis | Mapping, Bulk API et API locale de l’atelier 01 ; HTTPS seulement si la variante sécurisée a été choisie |
| Cas métier commun | Films et offres de diffusion sur des plateformes |
| Livrables | Trois modèles, requêtes équivalentes et note de choix d’architecture |

## 1. Introduction et objectifs

Une même réalité métier peut être représentée de plusieurs façons dans Elasticsearch. Le choix influence les recherches, les mises à jour, le volume dupliqué, le routage et le coût d’exploitation.

Nous allons représenter le même catalogue avec :

1. Un document par offre, contenant une copie des informations du film : dénormalisation.
2. Un document film contenant un tableau d’offres de type `nested`.
3. Des documents film et offre séparés, liés par un champ `join` : parent-child.

Une quatrième représentation, un tableau d’objets ordinaires, servira uniquement à montrer le risque de perte de corrélation.

### Objectifs pédagogiques

- Partir des questions métier avant de choisir un mapping.
- Distinguer `object`, `nested`, dénormalisation et `join`.
- Reproduire un faux positif avec un tableau d’objets ordinaires.
- Conserver les associations plateforme/prix avec une requête `nested`.
- Créer une relation parent-child et appliquer le routage.
- Utiliser `parent_id`, `has_parent`, `has_child` et `inner_hits`.
- Comprendre la différence entre documents retournés et objets métier comptés.
- Comparer recherches et mises à jour sans généraliser un microbenchmark.
- Justifier un choix de modèle pour un cas d’observabilité.


### Progression pédagogique

```text
Besoin métier → object (contre-exemple) → dénormalisation
→ nested → parent-child → mises à jour → comparaison → défi
```

Nous gardons la même réalité métier et la même condition de recherche : seule la représentation change. Une solution qui renvoie plus vite un mauvais film n’est pas meilleure.

Les fiches films sont autonomes : aucun nouveau téléchargement MovieLens n’est nécessaire. Les IDs 109487 et 104841 rappellent les ateliers précédents ; ils ne créent aucune relation automatique entre leurs index et ceux de cet atelier.

## 2. Cas métier et question commune

Deux films possèdent des offres de diffusion sur plusieurs plateformes fictives :

| Film | Nom | Catégorie | Plateforme | Prix en centimes | Disponible |
|---|---|---|---|---:|---|
| 109487 | Interstellar | science-fiction | A | 1500 | oui |
| 109487 | Interstellar | science-fiction | B | 800 | oui |
| 104841 | Gravity | science-fiction | A | 700 | oui |
| 104841 | Gravity | science-fiction | C | 1200 | oui |

Question à résoudre dans les trois modèles :

> Quels films de catégorie science-fiction possèdent une offre disponible de la plateforme A à moins de 1000 centimes ?

Résultat métier attendu : uniquement 104841, via l’offre A à 700. 109487 ne convient pas : son offre à bas prix appartient à B, pas à A.

Les prix sont stockés en centimes entiers afin d’éviter un débat sur les arrondis monétaires. Les plateformes, prix et disponibilités sont fictifs : ce n’est pas un catalogue commercial réel ni un modèle complet de droits de diffusion.

### Lire la condition sans ambiguïté

Les quatre critères doivent être vrais ensemble : catégorie science-fiction, plateforme A, disponibilité true et prix strictement inférieur à 1000 centimes, soit 10 euros.

La plateforme, le prix et la disponibilité doivent concerner la même offre. Ce n’est pas « le film a une offre A et une autre offre à bas prix ».

Dans les nouveaux mappings, movie_id est volontairement un keyword : nous l’utilisons comme identifiant exact, sans calcul arithmétique. Cela ne modifie pas les movie_id entiers des autres index ; un choix de mapping est local à l’index. Les chaînes d’ID et les noms d’offres sont synthétiques pour la démonstration.

category représente ici une catégorie principale unique. Il ne faut pas confondre ce champ simplifié avec le tableau genres de MovieLens.

## 3. Préparer le dossier et choisir le mode de connexion

### Objectif

Conserver le même choix HTTP ou HTTPS que dans les ateliers 01 à 05, sans modifier leurs index.

### Mode simple — commandes à utiliser telles quelles

```bash
mkdir -p ~/formation-observabilite/atelier06
cd ~/formation-observabilite/atelier06
export ES_URL='http://localhost:9200'
curl "$ES_URL/_cluster/health?pretty"
```

Toutes les commandes suivantes sont présentées sans certificat ni authentification.

### Si vous avez choisi la variante sécurisée dans l’atelier 01

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

L’option correcte est --fail-with-body avec deux tirets. Elle signale les erreurs HTTP mais ne remplace pas la lecture des réponses Bulk. Le JSON ne change pas ; ES_URL doit être en HTTPS dans ce cas. Ne pas utiliser -k.

Les scripts locaux et commandes Python n’acceptent pas ces options curl. Le script de mesure facultatif plus loin adapte lui-même sa connexion à ES_URL.

### Résultat attendu et précaution

Le cluster répond. Les index portent le préfixe atelier06- et sont indépendants des catalogues films des ateliers précédents. Si un de ces index existe déjà avec l’ancien schéma produits, ne pas mélanger les structures : utiliser une nouvelle VM/snapshot de lab ou faire choisir de nouveaux noms cohérents par le formateur.

Ne pas supprimer automatiquement un ancien index. Ne pas publier les secrets dans les livrables.

## 4. Démonstration : le piège des tableaux object

### Notion : structure du JSON et structure de recherche

Un tableau dans _source peut garder son apparence d’origine alors que ses valeurs sont indexées dans des champs multivalués indépendants. Une bonne présentation du JSON n’est donc pas une garantie de corrélation à la recherche.

Représentation simplifiée du contre-exemple :

```text
offers.platform    = [A, B]
offers.price_cents = [1500, 800]
```

Les deux conditions A et prix < 1000 trouvent chacune une valeur, mais pas dans la même offre. object reste tout à fait adapté à un objet simple ou à des tableaux sans besoin de corrélation ; nested n’est pas nécessaire pour chaque tableau.


### Objectif

Observer une correspondance qui mélange deux offres distinctes.

### Créer et alimenter l’index témoin

```bash
curl -X PUT "$ES_URL/atelier06-object" -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"dynamic":"strict","properties":{
      "movie_id":{"type":"keyword"},
      "offers":{"properties":{
        "platform":{"type":"keyword"},
        "price_cents":{"type":"integer"},
        "available":{"type":"boolean"}
      }}
    }}
  }'

curl -X PUT "$ES_URL/atelier06-object/_doc/109487?refresh=wait_for" \
  -H 'Content-Type: application/json' \
  -d '{"movie_id":"109487","offers":[
    {"platform":"A","price_cents":1500,"available":true},
    {"platform":"B","price_cents":800,"available":true}
  ]}'
```

### Requête

```bash
curl -X POST "$ES_URL/atelier06-object/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"filter":[
    {"term":{"offers.platform":"A"}},
    {"range":{"offers.price_cents":{"lt":1000}}}
  ]}}}'
```

### Résultat attendu

109487 est retourné, bien que la plateforme A ne propose pas l’offre à moins de 1000.

### Explication

Les valeurs d’un tableau `object` sont aplaties lors de l’indexation. Les critères peuvent correspondre à des objets différents : A est présent dans une offre, 800 dans une autre.

Cela ne modifie pas l’apparence du tableau dans `_source`, mais change la façon dont la requête retrouve les valeurs. `nested` sert à préserver cette corrélation dans les recherches.

### Point de contrôle

Le participant doit pouvoir expliquer le faux positif sans dire que les données sources sont corrompues : la représentation de recherche ne conserve pas l’association de chaque offre dans ce modèle object.

## 5. Modèle A — Dénormaliser, un document par offre

### Lecture du modèle

```text
Document 109487-A = film Interstellar + catégorie + offre A
Document 109487-B = film Interstellar + catégorie + offre B
```

Dénormaliser signifie copier le contexte utile dans l’unité recherchée, pas dupliquer aveuglément toutes les données. Ici, la plateforme et le prix appartiennent au même document autonome : aucun parcours relationnel n’est requis pour filtrer l’offre.

Le résultat technique est une offre. Le résultat métier demandé est un film : utiliser movie_id pour interpréter les hits. Dans un catalogue plus large, plusieurs offres peuvent pointer vers le même film.


### Objectif

Stocker dans chaque offre les champs film nécessaires aux recherches.

### Mapping

```bash
curl -X PUT "$ES_URL/atelier06-denorm" -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"dynamic":"strict","properties":{
      "offer_id":{"type":"keyword"},
      "movie_id":{"type":"keyword"},
      "title":{"type":"text"},
      "category":{"type":"keyword"},
      "platform":{"type":"keyword"},
      "price_cents":{"type":"integer"},
      "available":{"type":"boolean"}
    }}
  }'
```

### Données

```bash
cat > denorm.ndjson <<'EOF'
{"index":{"_id":"109487-A"}}
{"offer_id":"109487-A","movie_id":"109487","title":"Interstellar","category":"science-fiction","platform":"A","price_cents":1500,"available":true}
{"index":{"_id":"109487-B"}}
{"offer_id":"109487-B","movie_id":"109487","title":"Interstellar","category":"science-fiction","platform":"B","price_cents":800,"available":true}
{"index":{"_id":"104841-A"}}
{"offer_id":"104841-A","movie_id":"104841","title":"Gravity","category":"science-fiction","platform":"A","price_cents":700,"available":true}
{"index":{"_id":"104841-C"}}
{"offer_id":"104841-C","movie_id":"104841","title":"Gravity","category":"science-fiction","platform":"C","price_cents":1200,"available":true}
EOF

curl -X POST "$ES_URL/atelier06-denorm/_bulk?refresh=wait_for&pretty" \
  -H 'Content-Type: application/x-ndjson' --data-binary @denorm.ndjson
```

Vérifier `errors: false` et quatre items réussis.

### Requête métier

```bash
cat > query-denorm.json <<'JSON'
{
  "size":10,
  "query":{"bool":{"filter":[
    {"term":{"category":"science-fiction"}},
    {"term":{"platform":"A"}},
    {"term":{"available":true}},
    {"range":{"price_cents":{"lt":1000}}}
  ]}}
}
JSON

curl -X POST "$ES_URL/atelier06-denorm/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @query-denorm.json
```

### Résultat attendu

L’offre 104841-A est retournée. Son champ `movie_id` donne le film 104841.

### Explication

La recherche est directe, sans jointure. En contrepartie, `title` et `category` sont dupliqués. Une modification du film doit être propagée à toutes ses offres si l’application exige une copie à jour.

Plusieurs offres pourraient correspondre au même film : nombre de hits et nombre de films ne sont pas forcément égaux. Une interface film devra dédupliquer, agréger ou utiliser une stratégie adaptée.

### Dépannage

Ne pas comparer directement les nombres de hits des trois modèles sans vérifier si les résultats sont des offres ou des films.

## 6. Modèle B — Intégrer les offres avec nested

### Lecture du modèle

```text
Document racine 109487 : Interstellar
  ├── offre A : 1500 centimes
  └── offre B : 800 centimes
```

Nested conserve une portée de recherche propre à chaque objet. L’application écrit un seul document racine avec un tableau ; Elasticsearch gère les documents internes nécessaires.

Le path identifie le tableau. La requête interne s’applique à une offre à la fois. score_mode none convient ici à une recherche de conditions exactes : nous ne classons pas les films selon la pertinence textuelle de leurs offres.


### Objectif

Conserver plusieurs offres dans un document film tout en respectant les associations plateforme/prix.

### Mapping

```bash
curl -X PUT "$ES_URL/atelier06-nested" -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"dynamic":"strict","properties":{
      "movie_id":{"type":"keyword"},
      "title":{"type":"text"},
      "category":{"type":"keyword"},
      "offers":{"type":"nested","properties":{
        "offer_id":{"type":"keyword"},
        "platform":{"type":"keyword"},
        "price_cents":{"type":"integer"},
        "available":{"type":"boolean"}
      }}
    }}
  }'
```

### Données

```bash
cat > nested.ndjson <<'EOF'
{"index":{"_id":"109487"}}
{"movie_id":"109487","title":"Interstellar","category":"science-fiction","offers":[{"offer_id":"109487-A","platform":"A","price_cents":1500,"available":true},{"offer_id":"109487-B","platform":"B","price_cents":800,"available":true}]}
{"index":{"_id":"104841"}}
{"movie_id":"104841","title":"Gravity","category":"science-fiction","offers":[{"offer_id":"104841-A","platform":"A","price_cents":700,"available":true},{"offer_id":"104841-C","platform":"C","price_cents":1200,"available":true}]}
EOF

curl -X POST "$ES_URL/atelier06-nested/_bulk?refresh=wait_for&pretty" \
  -H 'Content-Type: application/x-ndjson' --data-binary @nested.ndjson
```

### Requête métier

```bash
cat > query-nested.json <<'JSON'
{
  "size":10,
  "query":{"bool":{"filter":[
    {"term":{"category":"science-fiction"}},
    {"nested":{
      "path":"offers",
      "score_mode":"none",
      "query":{"bool":{"filter":[
        {"term":{"offers.platform":"A"}},
        {"term":{"offers.available":true}},
        {"range":{"offers.price_cents":{"lt":1000}}}
      ]}},
      "inner_hits":{"name":"offres_correspondantes","size":5}
    }}
  ]}}
}
JSON

curl -X POST "$ES_URL/atelier06-nested/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @query-nested.json
```

### Résultat attendu

104841 est retourné comme document racine, avec l’offre A à 700 dans `inner_hits.offres_correspondantes`. 109487 est exclu.

### Explication

Les objets nested sont indexés comme documents Lucene distincts associés au document racine. Ils ne deviennent pas pour autant des documents autonomes que l’on met à jour par un simple `_doc/{offer_id}`.

Pour imposer « même offre », tous les critères plateforme/prix/disponibilité doivent être dans la même requête `nested`. Deux clauses `nested` distinctes peuvent chacune correspondre à une offre différente.

### Point de contrôle

Comparer la requête avec celle du modèle `object`. Expliquer pourquoi `_source` contient toutes les offres alors que `inner_hits` isole les correspondances.

### Dépannage

Une requête `term` directement sur `offers.platform` au niveau racine n’est pas l’équivalent d’une requête `nested`. Respecter le `path`.

## 7. Modèle C — Parent-child avec un champ join

### Lecture du modèle

```text
Document parent 109487 : Interstellar
  ├── document enfant 109487-A
  └── document enfant 109487-B
```

Le parent et l’enfant sont deux documents Elasticsearch autonomes du même index. Le champ relation décrit leur rôle ; il ne réintroduit pas les anciens mapping types _type supprimés des API modernes.

Ne pas confondre trois identifiants :

| Élément | Exemple | Utilité |
|---|---|---|
| _id du parent | 109487 | Identité du document film |
| relation.parent dans l’enfant | 109487 | Lien logique vers ce parent |
| routing de l’opération | 109487 | Sélection du shard où chercher/écrire la famille |

Le routage est stable et doit accompagner les accès directs aux enfants. Le fait d’avoir un seul nœud ne signifie pas un seul shard.


### Objectif

Faire évoluer les films et offres comme documents distincts.

### Mapping

```bash
curl -X PUT "$ES_URL/atelier06-join" -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":2,"number_of_replicas":0},
    "mappings":{"dynamic":"strict","properties":{
      "relation":{"type":"join","relations":{"movie":"offer"}},
      "movie_id":{"type":"keyword"},
      "title":{"type":"text"},
      "category":{"type":"keyword"},
      "offer_id":{"type":"keyword"},
      "platform":{"type":"keyword"},
      "price_cents":{"type":"integer"},
      "available":{"type":"boolean"}
    }}
  }'
```

### Explication

Deux shards primaires sont choisis ici pour montrer le rôle du routage, même sur un seul nœud. Ce choix ne constitue pas une recommandation de dimensionnement. Pour une comparaison de performances contrôlée, utiliser le même nombre de shards dans tous les modèles.

### Données — parents avant enfants

```bash
cat > join.ndjson <<'EOF'
{"index":{"_id":"109487","routing":"109487"}}
{"relation":"movie","movie_id":"109487","title":"Interstellar","category":"science-fiction"}
{"index":{"_id":"104841","routing":"104841"}}
{"relation":"movie","movie_id":"104841","title":"Gravity","category":"science-fiction"}
{"index":{"_id":"109487-A","routing":"109487"}}
{"relation":{"name":"offer","parent":"109487"},"offer_id":"109487-A","platform":"A","price_cents":1500,"available":true}
{"index":{"_id":"109487-B","routing":"109487"}}
{"relation":{"name":"offer","parent":"109487"},"offer_id":"109487-B","platform":"B","price_cents":800,"available":true}
{"index":{"_id":"104841-A","routing":"104841"}}
{"relation":{"name":"offer","parent":"104841"},"offer_id":"104841-A","platform":"A","price_cents":700,"available":true}
{"index":{"_id":"104841-C","routing":"104841"}}
{"relation":{"name":"offer","parent":"104841"},"offer_id":"104841-C","platform":"C","price_cents":1200,"available":true}
EOF

curl -X POST "$ES_URL/atelier06-join/_bulk?refresh=wait_for&pretty" \
  -H 'Content-Type: application/x-ndjson' --data-binary @join.ndjson
```

### Résultat attendu

Six documents : deux films parents et quatre offres enfants. Vérifier `errors: false`.

### Explication : pourquoi le routage ?

Le parent et tous ses enfants doivent appartenir au même shard logique. Fournir la même valeur de routage le garantit, dans ce modèle non partitionné. `parent` définit la relation logique ; `routing` choisit l’emplacement. L’un ne remplace pas l’autre.

```text
109487 et 109487-A / 109487-B → même valeur routing = 109487 → même shard
104841 et 104841-A / 104841-C → même valeur routing = 104841 → même shard
```

109487 et 104841 peuvent eux-mêmes tomber sur le même shard par le calcul de routage ; aucun numéro n’est garanti. « Une famille sur un même shard » ne signifie pas « une famille par shard ».

Un enfant n’a qu’un parent dans le champ `join`. Il ne s’agit pas d’une relation many-to-many ni d’une jointure SQL générale entre index.

### Point de contrôle

```bash
curl "$ES_URL/atelier06-join/_doc/109487-A?routing=109487&pretty"

curl "$ES_URL/atelier06-join/_search_shards?routing=109487&pretty"
```

### Dépannage

Un essai sans routage peut sembler fonctionner sur un index à un shard ou par coïncidence de hash. Cela ne rend pas le routage facultatif : il faut le conserver pour l’indexation, lecture, modification et suppression des enfants.

## 8. Rechercher les parents avec has_child

### Lire le sens de la jointure

```text
Chercher les enfants répondant aux conditions → retourner leurs parents.
```

Le type offer est le nom de relation enfant déclaré dans le join. Les filtres platform/price/available sont dans une même requête enfant pour ne pas mélanger plusieurs enfants.

inner_hits montre les offres responsables de la correspondance. Ce n’est pas une suppression des autres offres du parent ni une modification de ses données.


### Objectif

Répondre à la question métier en sélectionnant des films dont une offre correspond.

### Commande

```bash
cat > query-join.json <<'JSON'
{
  "size":10,
  "query":{"bool":{"filter":[
    {"term":{"category":"science-fiction"}},
    {"has_child":{
      "type":"offer",
      "score_mode":"none",
      "query":{"bool":{"filter":[
        {"term":{"platform":"A"}},
        {"term":{"available":true}},
        {"range":{"price_cents":{"lt":1000}}}
      ]}},
      "inner_hits":{"name":"offres_correspondantes","size":5}
    }}
  ]}}
}
JSON

curl -X POST "$ES_URL/atelier06-join/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @query-join.json
```

### Résultat attendu

Parent 104841 avec l’enfant 104841-A dans `inner_hits`.

### Explication

La catégorie est vérifiée sur le parent ; plateforme, disponibilité et prix sont vérifiés sur un même enfant. Les requêtes `has_child` et `has_parent` coûtent davantage qu’une simple recherche sur un document autonome ; utiliser `join` lorsqu’une vraie justification métier le nécessite.

### Dépannage

Si les jointures sont refusées par la configuration `search.allow_expensive_queries`, consulter le formateur. Ne pas modifier une politique de cluster partagé sans accord.

## 9. Rechercher les enfants : parent_id et has_parent

### Choisir la requête selon ce que vous connaissez

| Requête | Point de départ | Retour |
|---|---|---|
| has_child | Conditions sur les offres | Films parents |
| parent_id | ID du film déjà connu | Offres enfants |
| has_parent | Conditions sur les attributs du film | Offres enfants |

parent_type et type sont ici des noms de relations du champ join, pas les anciens types d’indexation. Une recherche par parent_id n’est pas un GET direct d’enfant ; les règles de routage d’un accès direct restent à respecter.


### Objectif

Distinguer le cas d’un parent déjà connu d’une recherche sur ses attributs.

### Enfants d’un identifiant parent connu

```bash
curl -X POST "$ES_URL/atelier06-join/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"parent_id":{"type":"offer","id":"109487"}}}'
```

### Enfants dont le parent possède un nom recherché

```bash
curl -X POST "$ES_URL/atelier06-join/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"has_parent":{
    "parent_type":"movie",
    "query":{"match":{"title":"gravity"}},
    "score":false
  }}}'
```

### Résultat attendu

La première requête retrouve 109487-A et 109487-B ; la seconde 104841-A et 104841-C.

### Point de contrôle

Expliquer le sens de retour : `has_child` retourne les parents ; `has_parent` retourne les enfants.

## 10. Comparer les mises à jour d’offre

### Ce que l’on compare

Même changement métier : l’offre A d’Interstellar passe de 15 euros à 9 euros. La condition prix < 10 euros devient vraie pour ce film.

Le coût ne se limite pas au nombre de requêtes HTTP. Pour nested, une requête de mise à jour du parent peut entraîner le retraitement de son bloc d’objets internes. Pour join, l’enfant a sa propre écriture, mais les recherches et structures de jointure restent à maintenir.

Comme dans l’atelier 04, des clients concurrents peuvent exiger if_seq_no/if_primary_term ou une mise à jour scriptée adaptée. La modélisation ne supprime pas le besoin de gérer la concurrence.


### Objectif

Passer le prix de 109487-A de 1500 à 900 dans les trois modèles.

### Dénormalisé

```bash
curl -X POST "$ES_URL/atelier06-denorm/_update/109487-A?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"price_cents":900}}'
```

### Nested

```bash
curl -X POST "$ES_URL/atelier06-nested/_update/109487?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"script":{
    "lang":"painless",
    "source":"for (def offer : ctx._source.offers) { if (offer.offer_id == params.id) { offer.price_cents = params.price; } }",
    "params":{"id":"109487-A","price":900}
  }}'
```

### Parent-child

```bash
curl -X POST "$ES_URL/atelier06-join/_update/109487-A?routing=109487&refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"price_cents":900}}'
```

### Résultat attendu

Rejouer les trois requêtes métier : 109487 et 104841 sont maintenant admissibles. Dans le modèle dénormalisé, les hits sont les offres A correspondantes.

### Explication

- Dénormalisé : l’offre seule est réindexée.
- Nested : modifier une offre implique la réindexation du bloc du document racine et de ses objets nested.
- Parent-child : l’enfant est mis à jour indépendamment du parent, mais les recherches de relation ont leur coût.

Il n’y a pas de transaction entre ces trois index : ils représentent ici trois implémentations indépendantes. Dans une application, appliquer les contrôles de concurrence de l’atelier 04 quand ils sont nécessaires.

### Dépannage

Si un appel retourne `noop`, la valeur est peut-être déjà 900. Le test doit être compris en fonction de l’état réel, pas seulement d’un résultat `updated` attendu.

## 11. Comparer un changement des informations film

### Pourquoi mettre à jour le titre ?

Un prix appartient à l’offre ; le titre appartient au film. Dans le modèle dénormalisé, le titre est recopié dans chaque offre : sa correction doit être propagée. Dans join, seul le parent contient le titre. Dans nested, il est dans la racine, mais l’écriture réindexe aussi son bloc interne.

Il faut donc observer séparément la fréquence de changement des offres et celle des données communes au film.


### Objectif

Observer le coût logique de propagation d’une donnée dupliquée.

Changer le nom de 109487 dans le modèle dénormalisé :

```bash
curl -X POST "$ES_URL/atelier06-denorm/_update_by_query?refresh=true&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "query":{"term":{"movie_id":"109487"}},
    "script":{"lang":"painless","source":"ctx._source.title = params.name;","params":{"name":"Interstellar — édition restaurée"}}
  }'
```

Changer le document racine nested :

```bash
curl -X POST "$ES_URL/atelier06-nested/_update/109487?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"title":"Interstellar — édition restaurée"}}'
```

Changer le parent join :

```bash
curl -X POST "$ES_URL/atelier06-join/_update/109487?routing=109487&refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"title":"Interstellar — édition restaurée"}}'
```

### Résultat attendu

Dans denorm, deux documents d’offre sont à mettre à jour. Dans nested et join, une requête cible un seul document racine ou parent, mais les coûts physiques ne sont pas identiques.

### Explication

`_update_by_query` n’est pas une transaction multi-document : contrôler `updated`, les conflits et les échecs. Son paramètre `refresh=true` n’est pas équivalent à `refresh=wait_for` de l’API Update ; cet exemple choisit un refresh final pour le petit lab.

### Point de contrôle

Combien de copies du nom faudrait-il modifier si le film possédait 50 000 offres dénormalisées ? Et quel serait le coût d’un document nested contenant autant d’offres ? Justifier sans supposer qu’une stratégie gagne dans tous les cas.

## 12. Observer volumes, documents et mesures de recherche

### Comparer la correction avant la vitesse

Vérifier d’abord les mêmes films admissibles et la même offre responsable. Comparer seulement le nombre de hits donnerait une fausse équivalence si un modèle retourne des offres et l’autre des films.

Le _count est une vue logique des documents recherchables ; docs.count de _cat/indices reflète des documents Lucene et peut inclure les objets nested internes. Une différence n’implique pas une duplication métier.


### Objectif

Comparer ce que chaque modèle stocke et mesure.

### Commandes

```bash
curl "$ES_URL/_cat/indices/atelier06-*?v&h=index,pri,rep,docs.count,store.size"

for idx in atelier06-denorm atelier06-nested atelier06-join; do
  curl "$ES_URL/$idx/_count?pretty"
done
```

### Résultats attendus

| Modèle | Documents applicatifs visibles via `_count` | Observation |
|---|---:|---|
| Dénormalisé | 4 | Une offre par document |
| Nested | 2 | Deux racines film ; les quatre objets nested ajoutent des documents Lucene internes |
| Parent-child | 6 | Deux parents et quatre enfants autonomes |

### Explication

`_cat/indices` peut compter les documents Lucene nested, contrairement au comptage des racines par `_count`. Ne pas en déduire une anomalie d’import.

Le stockage de quelques documents est dominé par les structures internes : ce corpus ne permet pas de conclure sur le ratio de stockage d’un système réel.

### Mesure facultative reproductible côté client

Créer un script utilisant uniquement Python standard :

```bash
cat > compare_queries.py <<'PY'
import base64
import json
import os
import ssl
import statistics
import time
import urllib.request
from pathlib import Path

url = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
headers = {'Content-Type':'application/json'}
context = None
if url.startswith('https://'):
    context = ssl.create_default_context(cafile=os.environ['ES_CA'])
    auth = base64.b64encode(('elastic:' + os.environ['ELASTIC_PASSWORD']).encode()).decode()
    headers['Authorization'] = 'Basic ' + auth
elif not url.startswith('http://'):
    raise SystemExit('ES_URL doit commencer par http:// ou https://')
models = [
    ('atelier06-denorm','query-denorm.json'),
    ('atelier06-nested','query-nested.json'),
    ('atelier06-join','query-join.json'),
]

def search(index, filename):
    request = urllib.request.Request(
        url + '/' + index + '/_search', data=Path(filename).read_bytes(),
        headers=headers, method='POST')
    start = time.perf_counter()
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        result = json.load(response)
    return (time.perf_counter()-start)*1000, result['took']

reports = []
for index, filename in models:
    for _ in range(3):
        search(index, filename)
    values = [search(index, filename) for _ in range(10)]
    reports.append({
        'index':index,
        'client_median_ms':round(statistics.median(x[0] for x in values),3),
        'es_took_median_ms':statistics.median(x[1] for x in values)
    })
Path('mesures-locales.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
print(json.dumps(reports, indent=2))
PY

python3 compare_queries.py
```

### Limites de la comparaison

Ce n’est pas un benchmark :

- le modèle join a deux shards contre un pour les autres ;
- le corpus est minuscule ;
- les requêtes ne retournent pas exactement la même structure ;
- `inner_hits` ajoute un coût ;
- le script inclut des coûts réseau/TLS côté client ;
- caches, rafraîchissements et activités de la VM influencent les temps.

Pour une étude contrôlée, préparer des index comparables, un corpus plus grand avec différentes cardinalités, une même projection métier, un ordre d’essais alterné et des répétitions sous charge. Ne pas choisir un modèle parce qu’un seul `took` vaut 0 ou 1 ms.

## 13. Contraintes à connaître

### Éviter une fausse promesse relationnelle

Le join relie des documents dans le même index ; il ne remplace pas les clés étrangères, les transactions multi-lignes ni les jointures SQL générales. La suppression d’un parent ne doit pas être supposée supprimer automatiquement tous ses enfants.

Les global ordinals sont des structures de correspondance utilisées notamment par les jointures ; leur construction/actualisation a un coût. « Enfants indépendants » ne veut donc pas dire « aucun coût collectif sur le shard ».


### Parent-child

- Un seul champ `join` par index.
- Un enfant a un seul parent.
- Parent et enfants sur le même shard, avec routage cohérent.
- Les jointures ajoutent un coût et utilisent notamment les global ordinals.
- Une famille très volumineuse peut créer un déséquilibre de shard.
- Ne pas supposer une contrainte de clé étrangère ou une suppression en cascade comparable à un SGBDR.
- Pour déplacer un enfant vers un autre parent/routage, prévoir suppression à l’ancien emplacement et réindexation au nouvel emplacement, avec contrôle des doublons et erreurs.

### Nested

- Les critères corrélés doivent partager la même portée nested.
- Les objets nested participent aux limites et au coût de l’index.
- Les mises à jour réindexent le bloc racine.
- Les tableaux sans borne de croissance demandent une réflexion architecturale.

### Dénormalisation

- Recherche directe et données prêtes à afficher.
- Duplication volontaire des attributs nécessaires.
- Propagation des changements à concevoir explicitement.
- Ne pas copier tout le parent sans analyser les besoins réels.

## 14. Grille de décision

| Besoin | Choix à considérer en premier |
|---|---|
| Recherches fréquentes sur des offres avec quelques attributs film stables | Dénormalisation |
| Petit tableau borné dont les associations doivent rester exactes | Nested |
| Très nombreuses offres évoluant indépendamment d’un parent | Parent-child à évaluer avec mesures |
| Tags ou catégories simples multiples | Tableau keyword, sans nested inutile |
| Relations many-to-many avec contraintes fortes et transactions | Modèle applicatif/source relationnelle puis projection de recherche |
| Données d’observabilité | Événement autonome enrichi avec le contexte utile, souvent dénormalisé |

### Application à l’observabilité

Un log enrichi avec `service`, `environment`, `pipeline_id` et `run_id` est généralement une projection dénormalisée. Il n’est pas nécessaire de créer un parent-child entre chaque service et chacun de ses logs pour les retrouver par service.

Cette observation prépare le fil rouge Loki ↔ Elasticsearch : les identifiants communs facilitent la corrélation sans imposer une jointure parent-child.

## 15. Défi final

### Énoncé

Ajouter 9000603, « Voyage vers Mars », catégorie science-fiction :

- offre plateforme A, 2000 centimes, disponible ;
- offre plateforme B, 600 centimes, disponible.

1. Représenter 9000603 dans les trois modèles.
2. Rejouer la question métier : 9000603 ne doit pas être sélectionné.
3. Passer le prix de l’offre A à 900.
4. Rejouer : 9000603 doit maintenant être sélectionné.
5. Vérifier les offres responsables de la correspondance dans `inner_hits`.
6. Choisir un modèle pour un catalogue avec peu d’offres par film, puis pour un catalogue avec beaucoup d’offres très volatiles.

## 16. Corrigé du défi final

### Dénormalisé

```bash
cat > defi-denorm.ndjson <<'EOF'
{"index":{"_id":"9000603-A"}}
{"offer_id":"9000603-A","movie_id":"9000603","title":"Voyage vers Mars","category":"science-fiction","platform":"A","price_cents":2000,"available":true}
{"index":{"_id":"9000603-B"}}
{"offer_id":"9000603-B","movie_id":"9000603","title":"Voyage vers Mars","category":"science-fiction","platform":"B","price_cents":600,"available":true}
EOF

curl -X POST "$ES_URL/atelier06-denorm/_bulk?refresh=wait_for&pretty" \
  -H 'Content-Type: application/x-ndjson' --data-binary @defi-denorm.ndjson
```

### Nested

```bash
curl -X PUT "$ES_URL/atelier06-nested/_doc/9000603?refresh=wait_for" \
  -H 'Content-Type: application/json' \
  -d '{"movie_id":"9000603","title":"Voyage vers Mars","category":"science-fiction","offers":[
    {"offer_id":"9000603-A","platform":"A","price_cents":2000,"available":true},
    {"offer_id":"9000603-B","platform":"B","price_cents":600,"available":true}
  ]}'
```

### Parent-child

```bash
cat > defi-join.ndjson <<'EOF'
{"index":{"_id":"9000603","routing":"9000603"}}
{"relation":"movie","movie_id":"9000603","title":"Voyage vers Mars","category":"science-fiction"}
{"index":{"_id":"9000603-A","routing":"9000603"}}
{"relation":{"name":"offer","parent":"9000603"},"offer_id":"9000603-A","platform":"A","price_cents":2000,"available":true}
{"index":{"_id":"9000603-B","routing":"9000603"}}
{"relation":{"name":"offer","parent":"9000603"},"offer_id":"9000603-B","platform":"B","price_cents":600,"available":true}
EOF

curl -X POST "$ES_URL/atelier06-join/_bulk?refresh=wait_for&pretty" \
  -H 'Content-Type: application/x-ndjson' --data-binary @defi-join.ndjson
```

### Mise à jour

Reprendre les trois commandes de la section 10 : remplacer 109487 par 9000603, 109487-A par 9000603-A et conserver le nouveau prix 900.

### Vérification finale

Rejouer `query-denorm.json`, `query-nested.json` et `query-join.json`. 9000603 est absent avant la baisse du prix A, présent après. Comme 109487 a déjà été modifié à la section 10, les films finaux admissibles sont 109487, 104841 et 9000603 si toutes les étapes ont été exécutées dans l’ordre.

### Justification attendue

- Peu d’offres, tableaux bornés et besoin de corrélation : nested est un candidat naturel, à comparer à la dénormalisation.
- Beaucoup d’offres très volatiles : évaluer des documents d’offre dénormalisés ; envisager join si l’indépendance des parents et les recherches transversales le justifient.
- Le nombre d’offres seul ne suffit pas : fréquence de modification du parent, requêtes, volumes et exigences de cohérence comptent aussi.

## 17. Checklist et livrables

- Faux positif object refilm et expliqué.
- Trois mappings et jeux de données cohérents.
- Même résultat métier identifié dans les trois approches.
- Portée nested et routage join compris.
- Mise à jour d’offre et de film comparée.
- Différence entre documents racines et documents Lucene expliquée.
- Mesures accompagnées de leurs limites.
- Note d’architecture argumentée et défi validé.

## 18. Conservation et nettoyage

Conserver les fichiers et résultats pour le compte rendu. Suppression facultative et destructive des seuls index du lab :

```bash
curl -X DELETE "$ES_URL/atelier06-object,atelier06-denorm,atelier06-nested,atelier06-join?ignore_unavailable=true&pretty"
```

L’atelier 07 approfondira l’interrogation des données, les agrégations, les tris et la pagination profonde.

