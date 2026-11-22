# Atelier 02 — Concevoir un mapping Elasticsearch : types, multi-fields et analyseurs personnalisés

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 1, atelier 2 sur 13 |
| Durée indicative | 1 h 30 à 2 h |
| Environnement de référence | Elasticsearch 9.x installé nativement sur Ubuntu au cours de l’atelier 01 |
| Prérequis | Atelier 01 validé ; API Elasticsearch HTTP locale accessible. HTTPS et identifiants uniquement si la variante sécurisée a été choisie. |
| Modalité | Commandes curl guidées, vérifications, erreurs contrôlées et défi corrigé |
| Cas métier | Catalogue de produits et de services d’une plateforme data |
| Livrable | Mapping explicite, analyseur personnalisé, requêtes de validation |

## 1. Introduction

Le mapping décrit comment Elasticsearch doit interpréter et indexer les champs des documents. Une même chaîne peut être du texte à rechercher par mots, un identifiant à comparer exactement, une date ou une adresse IP. Le choix ne dépend pas seulement de l’apparence de la valeur : il dépend surtout des usages attendus.

Cet atelier part d’un petit catalogue technique pour relier chaque besoin à un type : recherche de mots dans un nom, filtrage par catégorie, tri par prix, suivi de date et agrégation. Un analyseur personnalisé permet ensuite de retrouver un terme indépendamment de sa casse et de certains accents.

L’import massif est réservé à l’atelier 03. Ici, quelques documents suffisent pour comprendre et vérifier le modèle.

### Objectifs pédagogiques

À la fin de l’atelier, le participant sait :

- distinguer document JSON, index, mapping et paramètres d’index ;
- choisir `text`, `keyword`, `integer`, `float`, `boolean` et `date` ;
- définir un mapping explicite avant l’indexation ;
- utiliser un multi-field pour rechercher, trier et agréger une même valeur ;
- expliquer tokenizer, token filter et normalizer ;
- créer un analyseur personnalisé et observer ses tokens avec `_analyze` ;
- détecter un champ inconnu ou une valeur de type incorrect ;
- ajouter un champ sans supposer qu’on peut changer librement les types existants.

## 2. Avant de commencer : choisir le même mode que dans l’atelier 01

Cet atelier ne réinstalle pas Elasticsearch et ne change pas sa configuration de sécurité. Utiliser le mode réellement choisi dans l’atelier 01.

Toutes les commandes sont exécutées dans le terminal de la VM Ubuntu. Le corps JSON des requêtes est identique dans les deux modes.

### Cas A — Vous avez suivi le parcours simple, sans sécurité

Définir l’URL une fois dans le terminal :

```bash
export ES_URL='http://localhost:9200'
```

Utiliser ensuite toutes les requêtes de l’atelier telles qu’elles sont écrites, sans ajouter de certificat ni d’identifiants :

```bash
curl "$ES_URL/?pretty"
```

C’est le mode utilisé pour présenter les commandes dans la suite du support.

### Cas B — Vous avez choisi la variante sécurisée dans l’atelier 01

Définir l’URL HTTPS et les variables de connexion :

```bash
export ES_URL='https://localhost:9200'
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD
printf '\n'
export ELASTIC_PASSWORD

test -r "$ES_CA" && echo 'Certificat CA accessible'
```

Le certificat doit être celui déjà préparé dans l’atelier 01. Ne pas recréer une CA ni copier des clés privées. Si vous avez choisi un autre emplacement, adapter ES_CA.

Pour chaque requête curl adressée à Elasticsearch dans cet atelier, ajouter immédiatement après `curl` :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Attention : l’option correcte est `--fail-with-body`, avec deux tirets au début, et non `-fail-with-body`.

Exemple de test sécurisé :

```bash
curl --fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  "$ES_URL/?pretty"
```

### Exemple concret : adapter une requête du TP

Requête présentée dans le support, à exécuter telle quelle en mode simple :

```bash
curl -X POST "$ES_URL/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"analyzer":"standard","text":"Écran de contrôle"}'
```

La même requête si vous avez choisi la sécurité :

```bash
curl --fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  -X POST "$ES_URL/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"analyzer":"standard","text":"Écran de contrôle"}'
```

Le JSON, l’endpoint, la méthode et les autres options ne changent pas. ES_URL doit bien être en HTTPS dans ce deuxième cas.

### À quoi servent ces éléments ?

| Élément | Explication |
|---|---|
| ES_URL | Adresse de l’API, en HTTP ou HTTPS selon le serveur |
| --cacert | Indique le certificat public de l’autorité de confiance pour vérifier le serveur HTTPS |
| -u | Envoie l’identifiant et le mot de passe au serveur |
| --fail-with-body | Rend une erreur HTTP détectable par le code de sortie tout en gardant la réponse visible ; ce n’est pas une option de sécurité |
| -H Content-Type | Indique que le corps de la requête est du JSON |
| -d ou --data-binary | Transmet le corps de la requête ; --data-binary @fichier lit un fichier |
| ?pretty | Rend la réponse JSON plus lisible |

Ne pas utiliser `-k` pour masquer un problème de certificat. Les variables sont à redéfinir si vous ouvrez un nouveau terminal ; ne pas enregistrer le mot de passe dans le support ou dans Git.

Le compte elastic est réservé ici à l’administration du laboratoire. Les applications réelles doivent utiliser une identité limitée.

### Point de contrôle

La requête de test retourne le nom du cluster et sa version. Si vous recevez une erreur 401, vérifier les identifiants ; si HTTP est refusé, vérifier que le serveur n’attend pas HTTPS.

Les commandes locales comme mkdir, cat et python3 ne reçoivent pas les options de connexion Elasticsearch. Dans Kibana Console, ne pas ajouter d’options curl : la connexion est gérée par Kibana.

---

## 3. Comprendre les types avant de créer l’index

### Les quatre notions à distinguer

| Notion | Rôle dans le TP | Exemple |
|---|---|---|
| Document | Un objet JSON représentant un élément du catalogue | Le produit P001 |
| Index | Regroupe les documents et leur organisation de recherche | atelier02-catalogue |
| Mapping | Déclare les champs et la manière de les indexer | stock est un integer |
| Settings | Définit notamment l’analyse et les shards de l’index | Analyseur catalogue_text |

Le mapping ne contient pas les produits : il décrit leur structure. Les documents seront envoyés seulement après la création de l’index.



### Objectif

Associer chaque champ métier à une utilisation.

| Champ | Exemple | Type retenu | Pourquoi ? |
|---|---|---|---|
| `product_id` | `P001` | `keyword` | Identifiant exact, pas une valeur à additionner |
| `name` | `Écran de contrôle` | `text` | Recherche de mots |
| `name.raw` | même nom | `keyword` | Valeur exacte et tri non analysé |
| `name.sort` | même nom normalisé | `keyword` avec normalizer | Tri et regroupement sans casse et avec repli ASCII |
| `description` | phrase descriptive | `text` | Recherche de contenu |
| `category` | `Matériel` | `keyword` normalisé | Filtre exact de catégorie |
| `price` | `249.9` | `float` | Démonstration numérique ; pas un modèle comptable |
| `stock` | `12` | `integer` | Quantité entière |
| `active` | `true` | `boolean` | État binaire |
| `created_at` | `2026-11-03T08:00:00Z` | `date` | Filtre et tri temporels |
| `tags` | `["Cloud", "Data"]` | `keyword` normalisé | Catégories multiples |

### Explication

- `text` est analysé pour rechercher des termes.
- `keyword` conserve une valeur unique par élément, adaptée au filtrage, tri et agrégations. Un normalizer peut la normaliser sans la découper en plusieurs tokens.
- Un tableau de chaînes utilise le même mapping qu’une chaîne ; il n’existe pas ici de type `array` à déclarer.
- Les multi-fields permettent d’indexer une seule valeur source de plusieurs façons.
- Pour de vrais montants financiers, choisir une représentation adaptée, par exemple un entier en centimes ou un `scaled_float` correctement conçu ; le `float` de ce lab sert uniquement à l’apprentissage.

### Point de contrôle

Pourquoi `P001` est-il un `keyword` alors que `stock` est un `integer` ?

Réponse : un identifiant sert à identifier exactement ; le stock sert aux comparaisons et opérations numériques.

## 4. Observer un analyseur intégré

### Objectif

Comprendre le résultat de l’analyse standard avant de créer une variante.

### Commande

```bash
curl -X POST "$ES_URL/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"analyzer":"standard","text":"Écran de contrôle CLOUD"}'
```

### Résultat attendu

Les valeurs `token` sont :

```text
écran
de
contrôle
cloud
```

### Explication

Un analyseur est une chaîne de traitement. Ici le texte est découpé en mots, puis normalisé notamment en minuscules. Les accents ne sont pas automatiquement supprimés par le seul analyseur `standard`.

Nous allons ajouter `asciifolding` pour obtenir `ecran` et `controle`.

### Point de contrôle

Dans la réponse, distinguer `token`, `position`, `start_offset` et `end_offset`.

### Dépannage

L’API `_analyze` analyse le texte fourni dans la requête ; elle ne lit pas automatiquement un document déjà stocké.

## 5. Préparer l’analyseur et le normalizer

### Comprendre les étapes de traitement

| Élément | Fonction | Exemple |
|---|---|---|
| Tokenizer standard | Découpe le texte en unités de recherche | Écran de contrôle devient plusieurs mots |
| Filtre lowercase | Met les tokens en minuscules | CLOUD devient cloud |
| Filtre asciifolding | Replie certains caractères vers leur forme ASCII | écran devient ecran |
| Analyzer | Assemble un tokenizer et des filtres pour un champ text | name produit plusieurs tokens |
| Normalizer | Normalise un keyword en une seule valeur | Matériel devient materiel |

L’ordre des filtres est défini dans le tableau filter. Ici, nous cherchons simplement à neutraliser casse et certains accents, sans supprimer les mots de liaison ni ajouter de synonymes.


### Objectif

Comprendre les deux traitements retenus.

```text
Analyseur catalogue_text :
texte → tokenizer standard → lowercase → asciifolding → plusieurs tokens

Normalizer catalogue_keyword :
valeur keyword → lowercase → asciifolding → une seule valeur normalisée
```

### Explication

L’analyseur traite les champs `text`. Le normalizer traite les champs `keyword` et garantit une seule valeur tokenisée. Dans cet atelier, aucune suppression de mots vides, aucun stemming et aucun dictionnaire de synonymes ne sont ajoutés : l’effet observé reste simple et explicite.

`asciifolding` aide à rapprocher certaines lettres accentuées de leur forme ASCII. Ce n’est pas une compréhension sémantique et cela ne garantit pas une translittération universelle de toutes les langues.

### Point de contrôle

Le participant sait expliquer pourquoi `category = "Matériel"` devient une valeur `materiel`, tandis que `name = "Écran de contrôle"` produit plusieurs mots.

## 6. Créer le mapping avant l’indexation

### Objectif

Créer un index dédié, strict et réutilisable pour l’atelier Bulk suivant.

### Commandes

```bash
mkdir -p ~/formation-observabilite/atelier02
cd ~/formation-observabilite/atelier02

cat > catalogue-mapping.json <<'JSON'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "catalogue_text": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      },
      "normalizer": {
        "catalogue_keyword": {
          "type": "custom",
          "char_filter": [],
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "product_id": {"type": "keyword"},
      "name": {
        "type": "text",
        "analyzer": "catalogue_text",
        "fields": {
          "raw": {"type": "keyword", "ignore_above": 256},
          "sort": {
            "type": "keyword",
            "normalizer": "catalogue_keyword",
            "ignore_above": 256
          }
        }
      },
      "description": {"type": "text", "analyzer": "catalogue_text"},
      "category": {"type": "keyword", "normalizer": "catalogue_keyword"},
      "price": {"type": "float"},
      "stock": {"type": "integer"},
      "active": {"type": "boolean"},
      "created_at": {"type": "date"},
      "tags": {"type": "keyword", "normalizer": "catalogue_keyword"}
    }
  }
}
JSON

python3 -m json.tool catalogue-mapping.json > /dev/null

curl -X PUT "$ES_URL/atelier02-catalogue?pretty" \
  -H 'Content-Type: application/json' \
  --data-binary @catalogue-mapping.json
```

### Résultat attendu

La réponse contient `acknowledged: true` et `index: atelier02-catalogue`.

### Explication

- Les settings portent les shards et l’analyse.
- Les mappings portent les champs et leurs types.
- `dynamic: strict` refuse les champs non déclarés ; cela aide à détecter une faute de nom.
- Un seul shard et zéro réplique sont choisis pour ce lab mono-nœud, pas pour illustrer la résilience de production.

### Point de contrôle

```bash
curl "$ES_URL/atelier02-catalogue/_mapping?pretty"

curl "$ES_URL/atelier02-catalogue/_settings?pretty"
```

### Dépannage

- `resource_already_exists_exception` : l’index existe. Inspecter son mapping ; ne pas le supprimer automatiquement.
- JSON invalide : vérifier le fichier avec `python3 -m json.tool`.
- Ne pas placer `analysis` dans `mappings` : il appartient aux `settings`.

### Lecture guidée du fichier catalogue-mapping.json

```text
settings
├── number_of_shards / number_of_replicas : organisation du lab mono-nœud
└── analysis
    ├── analyzer / catalogue_text : traitement des champs text
    └── normalizer / catalogue_keyword : traitement des champs keyword

mappings
├── dynamic : comportement face aux nouveaux champs
└── properties : liste des champs et de leurs types
    └── name / fields : plusieurs indexations de la même valeur source
```

| Partie | Pourquoi elle est présente |
|---|---|
| settings.analysis | Définit les traitements nommés avant de les référencer dans les champs |
| mappings.properties | Déclare la structure des documents |
| dynamic strict | Refuse un champ dont le nom n’est pas déclaré |
| name.analyzer | Applique catalogue_text à la recherche plein texte |
| name.fields.raw | Ajoute une représentation exacte sans normalisation |
| name.fields.sort | Ajoute une représentation normalisée, utilisable pour un tri simple |
| ignore_above 256 | N’indexe pas les valeurs trop longues de ces sous-champs keyword ; ne tronque pas _source |
| number_of_replicas 0 | Évite de demander une copie sur un autre nœud absent du lab |

La commande cat crée un fichier local. python3 -m json.tool vérifie sa syntaxe JSON. curl -X PUT crée ensuite l’index avec son contenu. Une validation JSON réussie ne garantit pas que tous les paramètres Elasticsearch sont corrects : lire aussi la réponse du serveur.

Les sous-champs name.raw et name.sort ne sont pas des champs supplémentaires à écrire dans les documents. Elasticsearch les alimente à partir de name.

## 7. Observer les tokens de chaque champ

### Lire la réponse de _analyze

- token : terme produit et utilisé pour la recherche.
- position : position logique du terme dans le texte analysé.
- start_offset / end_offset : emplacement du terme dans le texte d’origine.

La requête avec field utilise le traitement réellement associé à ce champ dans cet index. Elle vérifie donc le mapping, et pas seulement le nom d’un analyseur saisi séparément.


### Objectif

Comparer l’analyse plein texte, le keyword exact et le keyword normalisé.

### Commandes

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"field":"name","text":"Écran de contrôle CLOUD"}'
```

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"field":"name.raw","text":"Écran de contrôle CLOUD"}'
```

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"field":"name.sort","text":"Écran de contrôle CLOUD"}'
```

### Résultat attendu

| Champ | Tokens attendus |
|---|---|
| `name` | `ecran`, `de`, `controle`, `cloud` |
| `name.raw` | `Écran de contrôle CLOUD` — un seul token |
| `name.sort` | `ecran de controle cloud` — un seul token |

### Explication

Le sous-champ `.sort` ne réalise pas un tri linguistique français complet. Il offre un tri sur une valeur normalisée. Un tri tenant compte des règles linguistiques peut nécessiter une autre conception.

### Point de contrôle

Comprendre que `ignore_above: 256` limite l’indexation des valeurs trop longues de ces sous-champs keyword ; ce n’est pas une instruction de troncature du titre dans `_source`.

### Dépannage

Si `_analyze` ne produit pas ces résultats, vérifier le mapping du bon index, puis les paramètres `analyzer` et `normalizer` réellement appliqués.

## 8. Indexer trois documents de validation

### Comprendre une commande d’indexation

```text
PUT /atelier02-catalogue/_doc/P001?refresh=wait_for
     └ index             └ ID       └ visibilité attendue dans les recherches
```

Le corps -d contient le produit. Un PUT avec le même ID remplace le document correspondant ; il ne réalise pas une simple mise à jour partielle. Ici les trois commandes sont volontairement envoyées une par une, car le Bulk sera étudié à l’atelier 03.

refresh=wait_for attend un rafraîchissement rendant l’écriture visible par les recherches ; ce n’est pas une commande de sauvegarde.


### Objectif

Vérifier le mapping avec un petit ensemble contrôlé.

### Commandes

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_doc/P001?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "product_id":"P001",
    "name":"Écran de contrôle",
    "description":"Affichage des indicateurs de la plateforme data.",
    "category":"Matériel",
    "price":249.9,
    "stock":12,
    "active":true,
    "created_at":"2026-11-03T08:00:00Z",
    "tags":["Data","Observabilité"]
  }'
```

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_doc/P002?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "product_id":"P002",
    "name":"Clavier technique",
    "description":"Clavier pour administrer une infrastructure cloud.",
    "category":"MATÉRIEL",
    "price":79.9,
    "stock":30,
    "active":true,
    "created_at":"2026-11-03T08:05:00Z",
    "tags":["Cloud","Administration"]
  }'
```

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_doc/P003?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "product_id":"P003",
    "name":"Formation Elasticsearch",
    "description":"Formation à la recherche et à l’observabilité des données.",
    "category":"Service",
    "price":900,
    "stock":8,
    "active":false,
    "created_at":"2026-11-03T08:10:00Z",
    "tags":["Formation","Data"]
  }'
```

### Résultat attendu

Trois documents sont présents. Un premier envoi retourne `created` ; un rejeu avec les mêmes identifiants peut retourner `updated` sans augmenter le nombre de documents.

### Point de contrôle

```bash
curl "$ES_URL/atelier02-catalogue/_count?pretty"

curl "$ES_URL/atelier02-catalogue/_doc/P001?pretty"
```

### Explication

`_id` est l’identifiant technique du document. `product_id` est un champ métier stocké dans `_source` ; nous avons volontairement choisi la même valeur pour simplifier le lab, mais Elasticsearch ne les synchronise pas automatiquement.

### Dépannage

Ne pas ajouter `name.raw` ou `name.sort` dans les documents JSON. Ce sont des multi-fields alimentés automatiquement à partir de `name`.

## 9. Vérifier la recherche plein texte

### Pourquoi match ici ?

La valeur utilisateur ECRAN est analysée selon le champ name. Le texte du document et la question peuvent alors partager le token ecran. Sur name.raw, nous testerons au contraire une valeur exacte complète.

Un match ne signifie pas une égalité du texte original. Les options de pertinence avancées seront étudiées dans le TP consacré au Full Text Search.


### Objectif

Retrouver le document avec un mot sans accent.

### Commande

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"name":"ECRAN"}}}'
```

### Résultat attendu

P001 est retourné, même si `_source.name` contient `Écran`.

### Explication

La recherche `match` analyse la requête selon l’analyseur du champ, sauf configuration différente. La normalisation rapproche `ECRAN` et `Écran` de `ecran`.

### Point de contrôle

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"name.raw":"Écran de contrôle"}}}'
```

La valeur exacte trouve P001. `ecran de controle` sur `name.raw` ne doit pas le retrouver, car ce sous-champ n’a pas de normalizer.

### Dépannage

`term` sur un champ `text` ne réalise pas la même analyse qu’une requête `match`. Pour un mot recherché par l’utilisateur, commencer par `match` sur le champ textuel ; pour une catégorie, utiliser `term` sur un keyword.

## 10. Filtrer, trier et agréger avec les bons champs

### Lire les quatre opérations

| Élément de requête | Question traitée |
|---|---|
| term sur category | Quels documents appartiennent à cette catégorie exacte normalisée ? |
| range sur price | Quels produits satisfont une borne numérique ? |
| sort sur name.sort | Dans quel ordre retourner les résultats ? |
| aggs / terms | Combien de documents possède chaque catégorie ? |

Dans l’agrégation, size:0 au niveau principal masque les hits, pas les compteurs des buckets. Le size du bloc terms limite, lui, le nombre de catégories renvoyées.


### Objectif

Relier les types aux opérations disponibles.

### Filtre exact normalisé

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"category":"materiel"}}}'
```

### Résultat attendu

P001 et P002 : `Matériel` et `MATÉRIEL` sont indexés comme `materiel` dans ce champ.

### Filtre numérique

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"sort":[{"price":"asc"}],"query":{"range":{"price":{"lt":300}}}}'
```

P002, puis P001 sont retournés.

### Tri par nom normalisé

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"sort":[{"name.sort":"asc"}],"query":{"match_all":{}}}'
```

### Agrégation par catégorie

```bash
curl -X POST "$ES_URL/atelier02-catalogue/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"size":0,"aggs":{"categories":{"terms":{"field":"category","size":10}}}}'
```

### Résultat attendu

Deux catégories : `materiel` avec deux documents et `service` avec un document.

### Explication

Le normalizer s’applique à l’indexation et aux recherches sur le keyword, notamment les requêtes `term`. Il ne modifie pas le texte original conservé dans `_source`.

### Point de contrôle

Expliquer pourquoi `_source.category` affiche encore `MATÉRIEL` dans P002 alors que l’agrégation affiche `materiel`.

### Dépannage

Ne pas activer `fielddata` sur `name` pour réparer un tri. Utiliser le sous-champ keyword approprié. Les agrégations et requêtes avancées seront approfondies dans les ateliers suivants.

## 11. Provoquer et comprendre deux erreurs de mapping

### Objectif

Distinguer contrôle de structure et contrôle de type.

Ces commandes doivent échouer au niveau HTTP : c’est volontaire.

- En mode simple avec curl seul, le JSON d’erreur est affiché mais le code de sortie shell peut rester zéro si le transfert a réussi.
- En mode sécurisé, avec --fail-with-body ajouté selon la section 2, le JSON reste visible et curl retourne normalement le code de sortie 22 pour cette erreur HTTP.

Dans les deux cas, lire la réponse Elasticsearch et vérifier que le document a bien été refusé. Ne pas copier ces tests d’erreur dans un script qui s’arrête au premier échec sans les traiter explicitement.

### A. Champ inconnu avec mapping strict

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_doc/ERREUR1?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"product_id":"ERREUR1","name":"Produit test","unexpected_field":"non prévu"}'
```

### Résultat attendu

HTTP 400 avec `strict_dynamic_mapping_exception`, directement ou dans la cause de l’erreur.

### B. Valeur numérique invalide

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_doc/ERREUR2?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"product_id":"ERREUR2","name":"Produit test","stock":"beaucoup"}'
```

### Résultat attendu

HTTP 400 avec une erreur de parsing du champ `stock`. Le nom exact de l’exception peut varier selon la version.

### Explication

`dynamic: strict` refuse les champs non prévus. Cela ne rend pas tous les champs obligatoires et ne désactive pas toutes les conversions automatiques. Par exemple, certaines chaînes numériques peuvent être converties si la coercition est autorisée.

### Point de contrôle

Le compteur doit rester à trois documents après ces deux erreurs.

### Dépannage

Conserver les messages d’erreur pour le compte rendu, mais pas les secrets présents dans les commandes. Lire la cause et le nom du champ avant de modifier le mapping.

## 12. Faire évoluer le mapping

### Ce que fait PUT _mapping

La commande ci-dessous ajoute une propriété autorisée. Elle n’ajoute aucune valeur dans les documents déjà présents et ne change pas leur contenu _source. Avec dynamic strict, un nouveau nom doit être déclaré avant de pouvoir être envoyé.


### Objectif

Ajouter un champ sans recréer l’index.

### Commande

```bash
curl -X PUT "$ES_URL/atelier02-catalogue/_mapping?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"properties":{"supplier":{"type":"keyword"}}}'
```

### Résultat attendu

`acknowledged: true`. Les documents existants ne reçoivent pas automatiquement une valeur `supplier`.

### Explication

Ajouter un champ est différent de modifier le type d’un champ existant. Pour changer un type ou l’analyse d’un champ existant à l’indexation, prévoir généralement un nouvel index, son mapping, une réindexation et éventuellement un basculement d’alias.

Ajouter un nouveau multi-field à un champ existant ne remplit pas rétroactivement ses valeurs pour les documents déjà présents : il faut les retraiter/réindexer pour qu’ils bénéficient du nouveau sous-champ.

### Point de contrôle

```bash
curl "$ES_URL/atelier02-catalogue/_mapping/field/supplier?pretty"
```

### Dépannage

Ne pas supprimer l’index par réflexe si une modification de mapping échoue. Identifier d’abord s’il s’agit d’un ajout compatible ou d’une migration de modèle.

## 13. Observation dans Kibana — option courte

Contrairement à access_log dans l’atelier 01, created_at est ici une date métier fixe de catalogue. Il n’est pas nécessaire de la remettre à aujourd’hui : la Data View proposée n’utilise pas de filtre temporel.


### Objectif

Relier les manipulations REST à l’interface.

### Procédure

1. Ouvrir Kibana via le tunnel de l’atelier 01.
2. Créer une Data View `Atelier 02 — Catalogue` sur `atelier02-catalogue`.
3. Choisir de ne pas utiliser de filtre temporel pour ce catalogue.
4. Dans Discover, afficher `product_id`, `name`, `category`, `price`, `stock`, `active`.
5. Observer les valeurs originales dans un document développé.

### Résultat attendu

Les trois produits apparaissent sans dépendre d’une plage temporelle relative.

### Explication

`created_at` est une date de création métier, pas nécessairement le temps utile pour limiter une vue catalogue. Le choisir comme champ temporel pourrait masquer des produits anciens dans « Last 15 minutes ».

### Dépannage

Discover vide alors que `_count` vaut trois : vérifier Data View, filtre temporel éventuel et filtres KQL.

## 14. Défi final

### Énoncé

Créer `atelier02-services` pour un catalogue de prestations techniques avec :

- `service_id` : identifiant exact ;
- `title` : texte normalisé en minuscules et sans certains accents ;
- `title.raw` : valeur exacte pour tri/agrégation ;
- `domain` : catégorie normalisée ;
- `duration_hours` : entier ;
- `available` : booléen.

Contraintes :

1. Mapping explicite avec `dynamic: strict`.
2. Analyseur personnalisé avec tokenizer standard, lowercase et asciifolding.
3. Normalizer pour `domain`.
4. Deux documents de test.
5. Recherche de `securite` retrouvant `Sécurité Elasticsearch`.
6. Agrégation regroupant `CLOUD` et `Cloud` dans le même bucket.
7. Démonstration du refus d’un champ inconnu.

Ne pas consulter immédiatement le corrigé.

## 15. Corrigé du défi

### Création de l’index

```bash
curl -X PUT "$ES_URL/atelier02-services?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "settings":{
      "number_of_shards":1,"number_of_replicas":0,
      "analysis":{
        "analyzer":{
          "service_text":{"type":"custom","tokenizer":"standard","filter":["lowercase","asciifolding"]}
        },
        "normalizer":{
          "service_keyword":{"type":"custom","filter":["lowercase","asciifolding"]}
        }
      }
    },
    "mappings":{
      "dynamic":"strict",
      "properties":{
        "service_id":{"type":"keyword"},
        "title":{"type":"text","analyzer":"service_text","fields":{"raw":{"type":"keyword"}}},
        "domain":{"type":"keyword","normalizer":"service_keyword"},
        "duration_hours":{"type":"integer"},
        "available":{"type":"boolean"}
      }
    }
  }'
```

### Documents

```bash
curl -X PUT "$ES_URL/atelier02-services/_doc/S001?refresh=wait_for" \
  -H 'Content-Type: application/json' \
  -d '{"service_id":"S001","title":"Sécurité Elasticsearch","domain":"CLOUD","duration_hours":7,"available":true}'

curl -X PUT "$ES_URL/atelier02-services/_doc/S002?refresh=wait_for" \
  -H 'Content-Type: application/json' \
  -d '{"service_id":"S002","title":"Supervision des systèmes","domain":"Cloud","duration_hours":14,"available":true}'
```

### Recherches de validation

```bash
curl -X POST "$ES_URL/atelier02-services/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"title":"securite"}}}'

curl -X POST "$ES_URL/atelier02-services/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"size":0,"aggs":{"domaines":{"terms":{"field":"domain"}}}}'
```

### Champ inconnu — erreur attendue

```bash
curl -X PUT "$ES_URL/atelier02-services/_doc/TEST?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"service_id":"TEST","champ_inconnu":"erreur volontaire"}'
```

### Résultat attendu

- S001 correspond à `securite`.
- Un bucket `cloud` contient deux documents.
- Le document TEST est refusé et le compteur reste deux.

### Explication

L’analyseur rend les mots comparables pour la recherche ; le normalizer rend comparables les catégories ; le mapping strict protège la structure des événements, sans remplacer une validation métier complète.

## 16. Checklist et livrables

| Compétence | Validation |
|---|---|
| Typage | Chaque champ est justifié par son usage |
| Mapping explicite | Création avant l’ingestion |
| Multi-fields | `name`, `name.raw`, `name.sort` distingués |
| Analyse | Tokens observés et expliqués |
| Normalisation | `Matériel` et `MATÉRIEL` regroupés |
| Source | Différence entre `_source` original et valeurs indexées comprise |
| Erreurs | Champ inconnu et entier invalide refusés |
| Évolution | Champ ajouté sans réinitialiser l’index |
| Défi | Index services créé, recherches et erreurs validées |

Livrables :

- `catalogue-mapping.json` ;
- mapping du défi ;
- réponses `_analyze` annotées ;
- exemples de recherches et agrégation ;
- justification des types en quelques lignes ;
- messages d’erreurs contrôlées.

Aucun mot de passe ni certificat privé ne doit être inclus dans les livrables.

## 17. Passage à l’atelier 03 et nettoyage optionnel

Le choix HTTP ou HTTPS reste celui de la section 2. Les options de sécurité se rajoutent aussi à une requête DELETE si vous utilisez la variante sécurisée ; elles ne changent pas son caractère destructif.


Conserver `atelier02-catalogue` et son fichier de mapping pour préparer le chargement massif. L’atelier 03 réutilisera ce modèle ou sa copie dans un index Bulk distinct pour éviter de mélanger les compteurs des deux exercices.

Si le formateur autorise le nettoyage, commandes destructives :

```bash
curl -X DELETE "$ES_URL/atelier02-catalogue,atelier02-services?ignore_unavailable=true&pretty"
```

Ne pas exécuter si les index sont encore nécessaires. Une suppression de Data View Kibana n’est pas une suppression des documents Elasticsearch, et inversement.

## 18. Références et validation formateur

Support aligné sur le programme fourni : jour 1, atelier 2 — types de champs, multi-fields et analyseurs personnalisés.

Références techniques Elastic :

- Field data types : distinction text/keyword et usages des multi-fields.
- Normalizer : garantie d’un seul token et application à l’indexation et à la recherche.
- Dynamic field mapping : contrôle du comportement dynamique.
- Multi-fields : ajout de sous-champs et retraitement des documents existants.

Cette révision conserve les exercices du support initial et les aligne sur le parcours HTTP local de l’atelier 01. Les balises HTML details/summary ne sont pas utilisées. Les fichiers JSON intégrés ont été vérifiés syntaxiquement lors de la génération ; les commandes Elasticsearch n’ont pas été exécutées contre votre cluster. Valider une exécution complète sur les versions retenues avant la session.
