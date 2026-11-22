# Atelier 05 — Recherche plein texte sur les films : scoring, BM25, boosting, highlighting et fuzziness

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 2, atelier 05 |
| Durée indicative | 2 h à 2 h 30 avec la lecture guidée des scores |
| Environnement | Elasticsearch 9.x local, Ubuntu, curl et Python 3 standard |
| Prérequis | Atelier 01 fonctionnel ; mappings et Bulk des ateliers 02 et 03 |
| Corpus | Huit fiches de films avec textes pédagogiques |
| Index dédié | atelier05-movies |
| Livrable | Requêtes expliquées et grille de pertinence avant/après |

## 1. Objectifs pédagogiques

Les objectifs de l’atelier initial sont conservés :

- distinguer recherche lexicale et compréhension sémantique ;
- observer les tokens de l’analyseur ;
- comparer match, AND, minimum_should_match et match_phrase ;
- rechercher dans plusieurs champs avec multi_match ;
- favoriser un champ ou une expression avec un boost ;
- afficher des extraits avec highlight ;
- tolérer certaines fautes avec fuzziness ;
- combiner score textuel et filtres structurés ;
- évaluer les résultats sur des questions métier.

Cette version développe aussi :

- TF et IDF, les idées de base du scoring lexical ;
- TF-IDF et ses différentes variantes ;
- BM25, sa saturation de fréquence et sa normalisation de longueur ;
- la lecture d’une explication de score avec _explain ;
- les limites des boosts et des comparaisons de scores.

La recherche vectorielle reste réservée à l’atelier 14. Ici nous cherchons des termes indexés, pas une proximité sémantique produite par un modèle d’embedding.

## 2. Connexion : même convention que dans les ateliers précédents

### Mode simple, sans sécurité

```bash
export ES_URL='http://localhost:9200'
curl "$ES_URL/_cluster/health?pretty"
```

Exécuter les requêtes de l’atelier telles qu’elles sont présentées.

### Mode sécurisé choisi dans l’atelier 01

```bash
export ES_URL='https://localhost:9200'
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD
printf '\n'
export ELASTIC_PASSWORD
```

Ajouter après chaque curl Elasticsearch :

```bash
--fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD"
```

Exemple :

```bash
curl --fail-with-body --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  "$ES_URL/_cluster/health?pretty"
```

Deux tirets sont nécessaires dans --fail-with-body. Cette option de détection des erreurs HTTP n’est pas une option de pertinence. Ne pas utiliser -k pour masquer une erreur de certificat.

Le JSON reste identique. Les commandes locales Python/cat ne reçoivent pas ces options, et Kibana Console gère sa propre connexion.

```bash
mkdir -p ~/formation-observabilite/atelier05
cd ~/formation-observabilite/atelier05
```

---

# A — Corpus et analyse : comprendre ce qui est réellement recherché

## A1 — Pourquoi un petit catalogue de films ?

Le corpus MovieLens des ateliers précédents fournit des titres et des genres, mais pas les résumés et descriptions nécessaires à tous les exercices multi-champs. Cet atelier crée donc huit fiches enrichies séparées.

Les résumés, descriptions, identifiants 9000501 à 9000508 et plusieurs titres sont synthétiques. Certaines fiches reprennent des noms de films connus pour faciliter la lecture ; ce ne sont pas des métadonnées MovieLens importées ni des synopsis officiels.

Nous ne modifions ni movies, ni atelier03-movies, ni atelier04-movies.

| ID | Titre | Particularité de recherche |
|---|---|---|
| M001 | Interstellar | voyage spatial dans le résumé |
| M002 | Voyage spatial | expression dans le titre |
| M003 | Voyage dans le temps | voyage sans spatial |
| M004 | Star Wars | voyage spatial dans la description |
| M005 | Gravity | espace, mais pas le terme voyage |
| M006 | La planète bleue | voyage dans un contexte documentaire |
| M007 | Voyage spatial — brouillon | correspondance forte mais fiche non publiée |
| M008 | Archive du cinéma | voyage dans le résumé, spatial dans la description |

Cette construction rend les différences de sélection observables sans dépendre d’un rang numérique mémorisé.

## A2 — Définir le mapping

Créer le fichier joint movies-search-mapping.json, ou copier :

```bash
cat > movies-search-mapping.json <<'JSON'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "movies_text": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding"
          ]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "movie_id": {
        "type": "integer"
      },
      "title": {
        "type": "text",
        "analyzer": "movies_text",
        "fields": {
          "raw": {
            "type": "keyword"
          }
        }
      },
      "summary": {
        "type": "text",
        "analyzer": "movies_text"
      },
      "description": {
        "type": "text",
        "analyzer": "movies_text"
      },
      "year": {
        "type": "integer"
      },
      "genres": {
        "type": "keyword"
      },
      "published": {
        "type": "boolean"
      },
      "source": {
        "type": "keyword"
      }
    }
  }
}
JSON

curl -X PUT "$ES_URL/atelier05-movies?pretty" \
  -H 'Content-Type: application/json' \
  --data-binary @movies-search-mapping.json
```

### Lecture du mapping

| Élément | Utilité |
|---|---|
| settings.analysis | Définit les traitements avant de les appliquer aux champs |
| standard tokenizer | Découpe le texte en termes |
| lowercase | Normalise les majuscules |
| asciifolding | Replie certains caractères accentués vers leur forme ASCII |
| title / summary / description | Trois champs textuels avec le même analyseur |
| title.raw | Égalité exacte sur le titre complet |
| genres keyword | Filtre exact sur un élément de genre |
| published boolean | Filtre fonctionnel de publication |
| dynamic strict | Refuse les nouveaux noms de champs non prévus |
| un shard, zéro réplique | Choix du laboratoire mono-nœud |

BM25 est utilisé par défaut : il n’est pas nécessaire d’ajouter une similarity personnalisée pour faire les exercices.

Si l’index existe, vérifier le mapping ; ne pas supprimer les données automatiquement. Pour modifier l’analyse d’indexation, prévoir un nouvel index et une réindexation.

## A3 — Charger les huit fiches

```bash
cat > movies-search.ndjson <<'NDJSON'
{"index": {"_id": "M001"}}
{"movie_id": 9000501, "title": "Interstellar", "summary": "Un voyage spatial pour sauver l’humanité.", "description": "Un équipage explore l’espace et affronte la gravité. Le temps transforme la mission en défi.", "year": 2014, "genres": ["Sci-Fi", "Drama"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M002"}}
{"movie_id": 9000502, "title": "Voyage spatial", "summary": "Une mission scientifique à destination d’une planète inconnue.", "description": "Un voyage spatial conduit un équipage vers une nouvelle planète. La mission associe exploration et découverte.", "year": 2026, "genres": ["Sci-Fi", "Adventure"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M003"}}
{"movie_id": 9000503, "title": "Voyage dans le temps", "summary": "Un voyage temporel change le destin d’une famille.", "description": "Une expérience permet de revenir dans le passé. Chaque décision transforme le futur.", "year": 2026, "genres": ["Sci-Fi", "Drama"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M004"}}
{"movie_id": 9000504, "title": "Star Wars", "summary": "Une guerre dans l’espace oppose plusieurs mondes.", "description": "Un voyage spatial conduit les héros vers une planète menacée. La mission devient une aventure.", "year": 1977, "genres": ["Sci-Fi", "Adventure"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M005"}}
{"movie_id": 9000505, "title": "Gravity", "summary": "Survivre dans l’espace après un accident.", "description": "Deux astronautes cherchent à rejoindre une station. Le danger et la survie rythment leur mission.", "year": 2013, "genres": ["Sci-Fi", "Drama"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M006"}}
{"movie_id": 9000506, "title": "La planète bleue", "summary": "Un voyage au fond des océans.", "description": "Un documentaire consacré à la biodiversité marine et à la protection de la planète.", "year": 2026, "genres": ["Documentary"], "published": true, "source": "atelier05-synthetique"}
{"index": {"_id": "M007"}}
{"movie_id": 9000507, "title": "Voyage spatial — brouillon", "summary": "Un voyage spatial en préparation.", "description": "Cette fiche de voyage spatial est un brouillon non validé du catalogue.", "year": 2026, "genres": ["Sci-Fi"], "published": false, "source": "atelier05-synthetique"}
{"index": {"_id": "M008"}}
{"movie_id": 9000508, "title": "Archive du cinéma", "summary": "Les grands récits de voyage.", "description": "Le programme spatial au cinéma et son histoire constituent le thème de cette archive.", "year": 2026, "genres": ["Documentary"], "published": true, "source": "atelier05-synthetique"}
NDJSON

curl -X POST "$ES_URL/atelier05-movies/_bulk?refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @movies-search.ndjson -o movies-bulk-response.json
```

Contrôler les huit items, comme dans l’atelier 03 :

```bash
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('movies-bulk-response.json').read_text())
if not isinstance(r.get('items'), list):
    raise SystemExit('Reponse non Bulk : ' + str(r))
errors = []
for item in r['items']:
    operation, detail = next(iter(item.items()))
    if not 200 <= detail.get('status', 0) < 300 or detail.get('error'):
        errors.append((operation, detail))
print('Items :', len(r['items']), '; rejets :', len(errors))
for error in errors:
    print(error)
if errors or r.get('errors') or len(r['items']) != 8:
    raise SystemExit(1)
PY

curl "$ES_URL/atelier05-movies/_count?pretty"
```

Huit documents sont attendus sur un index neuf. Ne pas comparer la pertinence tant qu’un import est incomplet.

## A4 — Observer les tokens avant le score

```bash
curl -X POST "$ES_URL/atelier05-movies/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"field":"title","text":"VOYAGE SPATIAL et planète"}'
```

Tokens attendus : voyage, spatial, et, planete.

Ce qui n’est pas fait : suppression des mots de liaison, stemming, synonymes ou compréhension sémantique. espace n’est pas automatiquement le même terme que spatial ; voyages n’est pas systématiquement réduit à voyage.

Dans la réponse, token contient le terme, position sa position logique et les offsets son emplacement dans le texte d’origine.

---

# B — Comprendre TF-IDF, BM25 et _score

## B1 — Sélection et classement ne sont pas la même chose

```text
Analyse du texte → identification des documents correspondants → score → classement
```

Une requête peut modifier les candidats retenus, leur classement, ou les deux.

- AND ou un filtre de genre peuvent exclure des documents.
- Un boost positif modifie principalement la contribution au score d’une correspondance.
- Un tri explicite par année peut remplacer le classement par pertinence.

Le _score est une valeur relative à la requête, aux champs, au corpus et à la construction de la requête. Ce n’est ni un pourcentage de vérité ni une note universelle du film.

## B2 — TF : fréquence du terme

TF signifie Term Frequency. L’idée : un terme présent dans un champ est un signal de correspondance ; plusieurs occurrences peuvent renforcer ce signal.

```text
Document A : voyage spatial
Document B : voyage voyage voyage spatial
```

B contient davantage d’occurrences de voyage, mais il est aussi plus long. On ne peut pas attribuer tout écart de score uniquement à TF sans tenir compte des autres facteurs.

Selon le modèle, TF peut être un compte brut, une transformation logarithmique, une racine ou une fonction saturante. Il n’existe pas une formule TF unique pour tous les moteurs.

## B3 — IDF : rareté dans le corpus

IDF signifie Inverse Document Frequency. Un terme présent dans peu de documents est généralement plus discriminant qu’un terme présent partout.

Ne pas confondre :

- fréquence du terme dans un document : nombre de ses occurrences ;
- fréquence documentaire : nombre de documents contenant ce terme au moins une fois.

Exemple conceptuel : si tous les résumés contiennent film, ce terme discrimine peu. Si un seul contient gravité, gravité peut apporter un signal de rareté plus élevé.

La rareté n’est pas la pertinence métier à elle seule : un mot très rare peut être hors sujet. Les statistiques concernent les termes des champs recherchés, pas un dictionnaire universel de la langue.

## B4 — TF-IDF : une famille de pondérations

Une formulation pédagogique simple est :

\[
 w(t,d)=\operatorname{TF}(t,d)\times \operatorname{IDF}(t)
\]

Par exemple, on peut définir une IDF simplifiée :

\[
 \operatorname{IDF}(t)=\ln\left(\frac{N}{df(t)}\right)
\]

où N est le nombre de documents considérés et df(t) le nombre qui contiennent le terme. Ce n’est qu’une variante illustrative : lissage, normalisation et agrégation changent selon les modèles.

Le message à retenir est « présence/fréquence locale × pouvoir discriminant global ». Ce n’est pas une formule à coller dans un script Elasticsearch pour reproduire automatiquement son score actuel.

Les anciennes versions et anciens supports peuvent parler de TF-IDF classique. Elasticsearch 9.x utilise BM25 par défaut pour les champs textuels ; il ne faut donc pas présenter le produit brut TF × IDF comme son calcul exact.

## B5 — BM25 : mêmes intuitions, traitement plus maîtrisé

BM25 combine notamment :

1. la rareté des termes, via une IDF ;
2. leur fréquence dans le champ, avec saturation ;
3. la longueur du champ relativement à sa longueur moyenne.

### Saturation

Passer d’une à deux occurrences peut ajouter un signal significatif. Passer de cent à cent une occurrences ne devrait pas apporter le même gain. Répéter artificiellement un mot n’augmente donc pas indéfiniment sa contribution de façon linéaire.

### Longueur

Une occurrence dans un champ de dix termes n’a pas le même contexte qu’une occurrence dans un champ de mille termes. La comparaison de longueur se fait au niveau du champ et de sa longueur moyenne.

Un titre n’est pas automatiquement favorisé par rapport à une description uniquement parce qu’il est plus court : les statistiques des champs sont distinctes. Pour exprimer l’importance métier du titre, utiliser une pondération explicite et la tester.

### Formule de référence pédagogique

Une forme classique de BM25 est :

\[
 \operatorname{score}(d,q)=\sum_{t\in q}
 \operatorname{IDF}(t)\,
 \frac{f(t,d)(k_1+1)}{f(t,d)+k_1\left(1-b+b\frac{|d|}{\operatorname{avgdl}}\right)}
\]

| Symbole | Signification |
|---|---|
| f(t,d) | Fréquence du terme dans le champ du document |
| \|d\| | Longueur du champ en termes, pas en caractères |
| avgdl | Longueur moyenne de ce champ |
| k1 | Contrôle la saturation de fréquence |
| b | Contrôle la normalisation par la longueur |

L’IDF BM25 utilisée dans les explications Lucene/Elastic s’appuie notamment sur une forme lissée :

\[
 \ln\left(1+\frac{N-df(t)+0.5}{df(t)+0.5}\right)
\]

Ces équations expliquent les facteurs, pas une promesse de reproduction bit à bit du _score. Le facteur multiplicatif k1+1 peut être traité différemment selon la similarity/implémentation Lucene utilisée ; les normes stockées et la composition de la requête interviennent aussi. Pour votre installation, lire _explain plutôt qu’imposer un calcul manuel unique.

### Paramètres par défaut

| Paramètre | Valeur par défaut | Interprétation |
|---|---:|---|
| k1 | 1,2 | Saturation non linéaire de fréquence |
| b | 0,75 | Poids de la normalisation par longueur |

b=0 désactive l’effet de longueur ; cela ne désactive pas les autres composantes du score. Nous conservons les valeurs par défaut : modifier k1/b n’est pas le premier remède à une requête mal conçue.

## B6 — TF-IDF et BM25 : synthèse

| Aspect | TF-IDF au sens général | BM25 |
|---|---|---|
| Idée commune | Fréquence locale et rareté documentaire | Fréquence locale et rareté documentaire |
| Répétition | Dépend de la variante de TF | Saturation explicite |
| Longueur | Normalisation variable selon le modèle | Rapport à la longueur moyenne du champ |
| Paramètres ici | Pas de formule universelle | k1 et b notamment |
| Place dans le TP | Comprendre les fondements | Similarity utilisée par défaut |

## B7 — Lire un score réel avec _explain

Pour isoler le premier raisonnement, chercher un seul terme dans un seul champ :

```bash
curl -X POST "$ES_URL/atelier05-movies/_explain/M002?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"description":"voyage"}}}'
```

Repérer matched, explanation.value et l’arbre explanation.details. Selon la version et les détails renvoyés, chercher le champ, la fréquence, l’IDF, les longueurs et les paramètres de similarité.

Comparer avec M004 sur exactement la même requête :

```bash
curl -X POST "$ES_URL/atelier05-movies/_explain/M004?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"description":"voyage"}}}'
```

Questions : le terme est-il présent ? Combien de fois ? Les descriptions ont-elles la même longueur ? La pondération de requête est-elle la même ?

Ne pas attendre un score fixé dans le support. Modifier ou ajouter un document peut modifier les statistiques ; un filtre publié n’oblige pas Elasticsearch à recalculer l’IDF uniquement sur les fiches publiées. Les statistiques peuvent aussi dépendre des shards ; le lab utilise un shard pour simplifier l’observation.

_explain est un outil de diagnostic d’une requête sur un document, pas une option à activer sans réflexion pour tous les résultats en production.

---

# C — Contrôler la sélection des films

## C1 — match et la logique OR par défaut

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":10,"_source":["title","published"],
    "query":{"match":{"title":"voyage spatial"}}
  }'
```

Un titre contenant voyage ou spatial peut correspondre. M003 peut donc être sélectionné, même sans spatial. Relever les IDs et leurs scores, sans supposer un ordre fixe entre ex æquo.

## C2 — operator and : exiger tous les termes

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"title":{"query":"voyage spatial","operator":"and"}}}}'
```

Dans ce corpus, M002 et M007 contiennent les deux termes dans le titre. Le filtre de publication n’a pas encore été appliqué.

## C3 — minimum_should_match : un compromis

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"title":{"query":"voyage spatial temps","minimum_should_match":2}}}}'
```

Au moins deux termes analysés sont requis. M003 peut correspondre avec voyage et temps ; M002 avec voyage et spatial. Ce réglage change les candidats, pas seulement leur poids.

Tester 1, 2 et 3, puis noter les identifiants retournés. Un entier est volontairement utilisé pour éviter les arrondis des pourcentages dans cette première démonstration.

## C4 — match_phrase : positions et ordre

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match_phrase":{"title":"voyage spatial"}}}'
```

M002 et M007 contiennent cette suite analysée. match_phrase n’est pas une égalité sur tout le titre ; un suffixe brouillon n’empêche pas la correspondance.

Pour le titre complet exact :

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"title.raw":"Voyage spatial"}}}'
```

Cette égalité retrouve M002 et pas le titre plus long de M007. title.raw n’est pas normalisé : casse et texte exact comptent.

---

# D — Rechercher dans plusieurs champs et utiliser le boosting

## D1 — multi_match sans boost

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":10,"_source":["title","summary","description"],
    "query":{"multi_match":{
      "query":"voyage spatial","type":"best_fields",
      "fields":["title","summary","description"],"operator":"and"
    }}
  }'
```

M001 peut correspondre grâce au résumé ; M004 grâce à la description ; M002 grâce au titre notamment. M007 correspond aussi, avant filtrage.

### Attention à best_fields

L’opérateur AND s’applique à chaque champ considéré, pas à une fusion automatique de tous les mots des différents champs. M008 a voyage dans summary et spatial dans description, mais aucun de ces champs ne contient les deux termes : cette requête ne suffit pas à le sélectionner.

best_fields conserve par défaut le meilleur score de champ. Ce n’est pas automatiquement la somme des scores title + summary + description. Avec un tie_breaker, une partie des autres scores de champs peut être ajoutée ; nous n’en avons pas besoin ici.

Pour un besoin véritablement centré termes à travers les champs, étudier combined_fields ou une stratégie adaptée ; ne pas essayer de corriger une absence de correspondance en augmentant seulement un boost.

## D2 — Qu’est-ce qu’un boost ?

Un boost est une pondération de requête. Il exprime une préférence métier, par exemple : « si les mots recherchés sont dans le titre, cette correspondance compte davantage que s’ils sont seulement dans la description ».

```text
BM25 : mesure lexicale selon les termes et les statistiques.
Boost : poids donné à une contribution dans la requête.
Composition : combine les clauses selon multi_match, bool, etc.
```

| Exemple | Intention |
|---|---|
| title^4 | Pondérer le champ titre par 4 dans cette recherche multi-champs |
| summary^2 | Donner au résumé un poids intermédiaire |
| description | Poids implicite 1 |
| boost:3 sur match_phrase | Renforcer une clause d’expression |
| boost positif inférieur à 1 | Atténuer une contribution, sans exclure les documents |

Un boost n’est pas une probabilité et ne crée pas une correspondance absente. title^4 ne veut pas dire « ce film est quatre fois plus pertinent pour un humain ».

## D3 — Favoriser le titre, puis le résumé

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":10,"_source":["title","summary"],
    "query":{"multi_match":{
      "query":"voyage spatial","type":"best_fields",
      "fields":["title^4","summary^2","description"],"operator":"and"
    }}
  }'
```

Comparer à D1. Les correspondances du titre sont favorisées, mais l’ordre précis dépend des scores de chaque champ et de la composition de requête. Ne pas promettre un rang fixe.

Avec best_fields, le boost peut même changer quel champ fournit le meilleur score pour un document. Ce n’est donc pas « multiplier systématiquement tout le score final par 4 ».

### Utilité et limites

- Utile si le titre représente mieux le sujet principal.
- Utile pour favoriser une expression exacte ou un signal métier justifié.
- Inutile pour réparer un mauvais analyseur, un champ non interrogé ou un AND trop restrictif.
- Risqué si un poids énorme masque le reste de la pertinence.

Multiplier uniformément tous les scores d’une même requête par une même constante positive ne change pas, en soi, leur ordre. Pour modifier le classement, il faut généralement pondérer différemment certaines contributions ou ajouter un signal discriminant.

## D4 — Ajouter une préférence de phrase et des filtres

```bash
cat > recherche-boost-movies.json <<'JSON'
{
  "size":10,
  "_source":["title","summary","genres","published"],
  "query":{"bool":{
    "must":[{"multi_match":{
      "query":"voyage spatial","type":"best_fields",
      "fields":["title^4","summary^2","description"],"operator":"and"
    }}],
    "should":[{"match_phrase":{"title":{"query":"voyage spatial","boost":3}}}],
    "minimum_should_match":0,
    "filter":[{"term":{"published":true}},{"term":{"genres":"Sci-Fi"}}]
  }}
}
JSON

curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @recherche-boost-movies.json
```

### Lecture de la requête

| Bloc | Sélection | Effet direct sur le score |
|---|---|---|
| must | Recherche textuelle obligatoire | Oui |
| should + minimum_should_match 0 | Bonus facultatif si la phrase correspond | Oui pour la clause correspondante |
| filter published | Exclut le brouillon | Pas de contribution directe |
| filter genres | Exige Sci-Fi | Pas de contribution directe |

M007 est exclu même s’il aurait un bon score textuel. Un filtre obligatoire est préférable à un simple petit boost quand la règle métier exige une exclusion.

published est ici une règle fonctionnelle, pas une autorisation de sécurité : quelqu’un ayant un accès direct à l’index pourrait formuler une autre requête.

## D5 — Comprendre le bonus de phrase

Le score de la clause de phrase, pondéré par 3, contribue lorsqu’elle correspond. Ce n’est pas nécessairement un ajout constant de trois points.

Dans un bool avec des clauses scorantes, ces contributions sont combinées selon la requête. Ne pas comparer directement un score de cette requête enrichie au score d’une requête simple comme s’ils étaient sur une échelle universelle.

Pour diagnostiquer une fiche particulière, envoyer le même bloc query à l’API _explain, par exemple pour M002. Un endpoint _explain attend query, pas le corps complet contenant size et highlight.

---

# E — Highlighting et tolérance aux fautes

## E1 — Afficher les extraits correspondants

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size":5,"_source":["title","summary"],
    "query":{"bool":{
      "must":[{"multi_match":{
        "query":"voyage spatial","fields":["title^4","summary^2","description"],
        "operator":"and"
      }}],
      "filter":[{"term":{"published":true}}]
    }},
    "highlight":{
      "pre_tags":["<mark>"],"post_tags":["</mark>"],
      "fields":{
        "title":{"number_of_fragments":0},
        "summary":{"fragment_size":150,"number_of_fragments":1},
        "description":{"fragment_size":150,"number_of_fragments":1}
      }
    }
  }'
```

Les fragments sont dans highlight, séparément de _source. number_of_fragments:0 demande le champ titre complet. La segmentation précise peut varier.

Le highlight n’augmente pas le score et ne modifie pas les documents. Un terme surligné ne prouve pas à lui seul toute la logique booléenne de sélection.

Les balises mark sont des données de restitution, pas des titres HTML du support. Une interface doit échapper les contenus et contrôler les balises autorisées avant tout rendu HTML.

## E2 — Recherche stricte d’une faute

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"title":"interstelar"}}}'
```

Le terme mal orthographié n’est pas normalement indexé comme tel dans le corpus.

## E3 — Ajouter fuzziness

```bash
curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "query":{"bool":{
      "must":[{"match":{"title":{
        "query":"interstelar","fuzziness":"AUTO",
        "prefix_length":2,"max_expansions":50
      }}}],
      "filter":[{"term":{"published":true}}]
    }}
  }'
```

M001 doit pouvoir être retrouvé dans ce corpus.

| Paramètre | Rôle |
|---|---|
| fuzziness AUTO | Tolérance limitée dépendant de la longueur du terme |
| prefix_length 2 | Les deux premiers caractères doivent rester corrects |
| max_expansions 50 | Borne le nombre d’expansions |

Une faute dans le préfixe protégé peut empêcher la correspondance. Fuzziness traite des différences de caractères, pas des synonymes ou une reformulation comme « film sur la gravité » pour retrouver automatiquement Interstellar.

Tester fuzziness:0, 1 et AUTO. Plus de tolérance peut augmenter le coût et les faux positifs. Ne pas appliquer une recherche floue aux IDs, dates ou codes HTTP qui doivent être exacts.

---

# F — Grille d’évaluation de pertinence

## F1 — Comparer des requêtes, pas seulement des nombres

| Besoin utilisateur | Fiches à examiner | Point à vérifier |
|---|---|---|
| voyage spatial | M001, M002, M004 | Champ de correspondance et poids du titre |
| voyage dans le temps | M003 | Importance de la phrase et des mots |
| voyage documentaire | M006, éventuellement M008 | Filtre de genre et choix OR/AND |
| interstelar | M001 | Faute corrigée sans élargissement excessif |
| voyage spatial publié | M001, M002, M004 | M007 exclu |

Les attentes sont des jugements pédagogiques proposés, pas une vérité universelle.

Pour chaque test, noter :

| Requête | Variante | Rang 1 / 2 / 3 | Résultat absent | Utile / partiel / non utile | Explication |
|---|---|---|---|---|---|
| voyage spatial | Sans boost | à relever | à relever | à relever | champ, tokens, contraintes |
| voyage spatial | title^4, summary^2 | à relever | à relever | à relever | préférence métier |
| voyage spatial | Avec bonus de phrase et filtres | à relever | à relever | à relever | sélection et classement |

Les boosts se choisissent sur un ensemble de besoins. Tester une seule requête jusqu’à obtenir le résultat souhaité peut dégrader les autres.

## F2 — Questions sur les scores

1. Un mot rare est-il forcément pertinent ? Non, il faut qu’il corresponde au besoin.
2. Plus d’occurrences veut-il toujours dire premier résultat ? Non, longueur et autres facteurs interviennent.
3. Un titre est-il toujours avant une description ? Non, le poids métier se conçoit et se teste.
4. Un score de 8 signifie-t-il 80 % ? Non.
5. Une requête filter seule calcule-t-elle la même pertinence qu’un match ? Non.
6. Le highlighting améliore-t-il BM25 ? Non, il aide à lire les correspondances.
7. Un boost peut-il faire entrer un document qui ne satisfait pas un filtre ? Non.
8. Des scores de requêtes différentes sont-ils directement comparables ? Pas comme une mesure universelle de qualité.

---

# G — Défi final et corrigé

## G1 — Énoncé

Construire une recherche pour voyage spatial qui :

1. interroge title, summary et description ;
2. donne plus d’importance au titre, puis au résumé ;
3. exige les deux termes dans un même champ avec best_fields ;
4. conserve les fiches publiées du genre Sci-Fi ;
5. ajoute un bonus à la phrase voyage spatial dans le titre ;
6. affiche des extraits surlignés ;
7. explique pourquoi M007 et M008 ne sont pas retenus ;
8. propose séparément une recherche tolérante pour interstelar ;
9. justifie la différence entre sélection et classement en citant BM25 et les boosts.

## G2 — Corrigé principal

Créer recherche-finale-movies.json ou utiliser le fichier joint :

```bash
cat > recherche-finale-movies.json <<'JSON'
{
  "size": 5,
  "_source": [
    "movie_id",
    "title",
    "summary",
    "genres",
    "published"
  ],
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "voyage spatial",
            "type": "best_fields",
            "fields": [
              "title^4",
              "summary^2",
              "description"
            ],
            "operator": "and"
          }
        }
      ],
      "filter": [
        {
          "term": {
            "published": true
          }
        },
        {
          "term": {
            "genres": "Sci-Fi"
          }
        }
      ],
      "should": [
        {
          "match_phrase": {
            "title": {
              "query": "voyage spatial",
              "boost": 3
            }
          }
        }
      ],
      "minimum_should_match": 0
    }
  },
  "highlight": {
    "pre_tags": [
      "<mark>"
    ],
    "post_tags": [
      "</mark>"
    ],
    "fields": {
      "title": {
        "number_of_fragments": 0
      },
      "summary": {
        "fragment_size": 150,
        "number_of_fragments": 1
      },
      "description": {
        "fragment_size": 150,
        "number_of_fragments": 1
      }
    }
  }
}
JSON

curl -X POST "$ES_URL/atelier05-movies/_search?pretty" \
  -H 'Content-Type: application/json' --data-binary @recherche-finale-movies.json
```

### Résultats pédagogiques attendus

- M001 : correspondance des deux termes dans le résumé.
- M002 : correspondance dans le titre, avec préférence de champ et bonus de phrase.
- M004 : correspondance dans la description.
- M007 : refusé par published:false, quel que soit son score potentiel.
- M008 : ne remplit pas le AND par champ de best_fields et n’a pas le genre requis.

Ne pas fixer les scores ni imposer tout l’ordre des trois résultats. Vérifier le classement réellement obtenu puis interpréter les contributions avec _explain si nécessaire.

### Explication attendue

BM25 pondère les correspondances lexicales selon fréquence, rareté et longueur du champ. Les boosts expriment l’importance métier des champs et d’une expression. Les filtres imposent les conditions obligatoires sans ajouter directement de pertinence. Le highlight rend les correspondances lisibles sans modifier le classement.

Pour interstelar, reprendre E3, sans appliquer de recherche floue à movie_id ou au genre exact.

---

# H — Bilan, dépannage et livrables

## H1 — Erreurs fréquentes

| Situation | Diagnostic / correction |
|---|---|
| Aucun résultat avec AND | Vérifier tokens et champs ; best_fields n’assemble pas librement les mots entre champs |
| Trop de résultats | OR trop large ; ajouter contraintes ou seuil justifiés |
| Brouillon présent | Appliquer le filtre, pas seulement un petit poids négatif |
| Boost peu visible | Observer les clauses et champs qui scorent ; tester plusieurs requêtes |
| Score différent d’une capture | Corpus, requête, normes, versions, shards ou écritures différents |
| Champs filtrés qui « devraient augmenter le score » | filter ne contribue pas directement au score |
| Highlight absent | Vérifier correspondance et champ interrogé |
| Faute non corrigée | Distance, préfixe protégé et expansions |
| Erreur Bulk | Corriger les items avant d’évaluer la pertinence |

## H2 — Checklist pédagogique

- Analyseur et tokens compris.
- OR, AND et minimum_should_match comparés.
- Phrase distinguée de l’égalité exacte.
- TF distinguée de df et IDF.
- BM25 expliqué sans le confondre avec TF-IDF brut.
- k1 et b identifiés, sans tuning arbitraire.
- _explain utilisé pour un document et une requête.
- Pondérations title^4 et summary^2 justifiées.
- Filtre obligatoire distingué de préférence facultative.
- Highlight et fuzziness testés avec leurs limites.
- Grille de pertinence complétée et défi corrigé.

## H3 — Livrables et conservation

Conserver le mapping, le corpus, la requête finale, deux réponses _explain et la grille avant/après. Aucun secret dans les livrables.

L’index peut être conservé pour les recherches avancées de l’atelier 07 ; il remplace le rôle pédagogique de l’ancien atelier05-knowledge. Adapter les futurs exemples à ces champs films si nécessaire.

Nettoyage facultatif et destructif, après accord seulement :

```bash
curl -X DELETE "$ES_URL/atelier05-movies?pretty"
```

## Références et validation formateur

Objectifs conservés à partir de l’atelier 05 fourni. Corpus remplacé pour harmonisation avec les ateliers MovieLens et enrichi de textes synthétiques pour les exercices multi-champs.

Références techniques : Elastic, Similarity settings et BM25 ; Practical BM25 ; Multi-match query ; Highlighting ; Match query et fuzziness ; API Explain. Les anciennes documentations TF-IDF peuvent expliquer les fondements mais ne doivent pas remplacer la documentation de scoring de la version utilisée.

Les JSON intégrés et les exemples Python ont été vérifiés syntaxiquement. Le corpus joint contient huit documents et seize lignes NDJSON avec saut de ligne final. Les requêtes, scripts de diagnostic et scores n’ont pas été exécutés contre un cluster Elasticsearch lors de la génération : valider le scénario avec les versions retenues avant formation.
