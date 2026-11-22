# Atelier 04 — Concurrence : contrôle optimiste Elasticsearch et verrouillage pessimiste

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 2, atelier 04 |
| Durée indicative | 1 h 30 à 2 h |
| Environnement | Elasticsearch 9.x local, Ubuntu, curl et Python 3 standard |
| Prérequis | Atelier 01 fonctionnel, mapping et documents JSON des ateliers 02/03 |
| Cas métier | Fiche de film MovieLens, places disponibles et compteur de vues |
| Index dédié | atelier04-movies |
| Livrable | Requêtes, réponse 409, relecture/recalcul et explication des métadonnées |

## 1. Objectifs et scénario

Deux utilisateurs consultent la même fiche de film. L’un réserve trois places et l’autre deux. Que se passe-t-il s’ils calculent chacun une nouvelle disponibilité à partir de la même ancienne valeur ?

```text
Places initiales : 20
A lit 20 ; prépare 20 - 3 = 17
B lit 20 ; prépare 20 - 2 = 18
A écrit 17
B écrit 18, sans vérifier si le document a changé
Résultat : 18 ; l’effet de la réservation A a été perdu
Résultat attendu pour les deux réservations : 15
```

Vous allez :

- comprendre la concurrence et la perte de mise à jour ;
- comparer pessimisme et optimisme selon la diapositive du cours ;
- distinguer _id, movie_id, _version, _seq_no et _primary_term ;
- obtenir volontairement un HTTP 409 ;
- résoudre le conflit par relecture et recalcul ;
- utiliser un script et expliquer exactement retry_on_conflict=3 ;
- distinguer nouvelle tentative de conflit et rejeu après incident réseau.

Les places sont une extension pédagogique de la fiche de film, pas un champ du corpus MovieLens original. Nous ne modifions ni movies ni atelier03-movies. Le TP est autonome : aucun nouvel import MovieLens n’est nécessaire.

> Cet exercice montre une mise à jour sur un document. Il ne constitue pas une application complète de billetterie ni une transaction avec paiement et réservation multi-films.

## 2. Connexion : même convention que dans les ateliers précédents

### Mode simple de l’atelier 01

```bash
export ES_URL='http://localhost:9200'
curl "$ES_URL/_cluster/health?pretty"
```

Utiliser toutes les commandes telles qu’elles sont présentées.

### Si vous avez choisi la variante sécurisée

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

L’option correcte est --fail-with-body avec deux tirets. Elle signale les erreurs HTTP par un code de sortie non nul tout en conservant leur réponse ; elle n’est pas une protection de concurrence.

Ne pas utiliser -k. Ne pas enregistrer les secrets dans le support ou les captures. Ne pas ajouter les options curl aux commandes Python ou SQL.

Les erreurs 409 seront volontaires : avec --fail-with-body, curl retourne normalement 22. Ne pas utiliser un script qui s’arrête à la première erreur attendue sans la traiter.

```bash
mkdir -p ~/formation-observabilite/atelier04
cd ~/formation-observabilite/atelier04
```

---

# A — Comprendre les deux stratégies de concurrence

## A1 — Que signifie « concurrence » ?

Plusieurs clients peuvent intervenir sur la même donnée pendant des périodes qui se recouvrent. Ils n’ont pas besoin d’envoyer leur écriture à la même microseconde pour créer un problème.

Le risque existe entre la lecture et l’écriture : une autre application peut avoir modifié le document pendant que le premier client calcule sa réponse ou que l’utilisateur remplit un formulaire.

Exemples : deux réservations sur le même film, deux administrateurs éditant le titre, plusieurs visiteurs incrémentant les vues.

### Trois opérations à distinguer

1. Lire une valeur courante.
2. Décider d’une modification métier.
3. Écrire le résultat.

Si ces opérations sont séparées, « ma dernière lecture » n’est pas forcément « l’état actuel au moment de mon écriture ».

## A2 — Comparaison avec la diapositive du cours

| Point du cours | Contrôle optimiste, utilisé dans ce TP Elasticsearch | Verrouillage pessimiste, exemple de SGBDR |
|---|---|---|
| Principe | Autoriser les lectures ; vérifier l’état attendu à l’écriture | Acquérir un verrou avant la modification et le conserver pendant la transaction |
| Lecture | Pas de verrou applicatif conservé entre le GET du client et son écriture | SELECT FOR UPDATE peut verrouiller les lignes sélectionnées |
| Conflit | Modification refusée si l’état attendu n’est plus courant | Une opération incompatible attend généralement le verrou, ou échoue selon les options et délais |
| Écritures | Contrôlées à l’écriture, sans transaction cliente qui verrouille pendant sa réflexion | Écritures incompatibles sur les mêmes lignes sérialisées par les verrous |
| Coût principal | Conflits, relectures et recalculs | Attentes, contention et risque d’interblocage |
| Réaction du client | Interpréter 409, relire et réévaluer | Gérer attente, timeout ou transaction annulée |
| Cas fréquent | Beaucoup de lectures, conflits assez rares | Sections transactionnelles courtes nécessitant de réserver une ressource |

### Nuances à retenir

- « Aucun verrou posé » signifie ici : pas de verrou applicatif de longue durée entre lecture et écriture. Elasticsearch conserve des mécanismes internes de coordination ; ce n’est pas une absence absolue de synchronisation.
- Les SGBDR ne fonctionnent pas tous uniquement en pessimiste. Ils peuvent utiliser MVCC, des versions et du contrôle optimiste.
- Un SELECT ordinaire ne pose pas systématiquement un verrou bloquant les mises à jour. L’exemple pessimiste emploie explicitement SELECT FOR UPDATE.
- Les verrous ne sérialisent pas nécessairement toutes les écritures de la base : cela dépend de leur portée et de leur compatibilité.
- Un verrouillage distribué est possible, mais maintenir de longs verrous augmente les difficultés de coordination et de disponibilité. « Peu adapté » n’est pas « impossible ».

## A3 — Illustration SQL : verrouillage pessimiste

Exemple pédagogique de syntaxe PostgreSQL, à lire seulement. Aucun SGBDR supplémentaire n’est requis pour ce TP.

Supposer une table movies avec movie_id et available_seats, contenant 20 places pour le film 109487.

### Transaction A

```sql
BEGIN;
SELECT available_seats
FROM movies
WHERE movie_id = 109487
FOR UPDATE;
-- A voit 20 et conserve le verrou sur la ligne.
```

### Transaction B, pendant que A n’a pas terminé

```sql
BEGIN;
SELECT available_seats
FROM movies
WHERE movie_id = 109487
FOR UPDATE;
-- Cette requête attend le verrou de A.
```

A termine, après contrôle de la disponibilité :

```sql
UPDATE movies
SET available_seats = available_seats - 3
WHERE movie_id = 109487 AND available_seats >= 3;
COMMIT;
```

B peut ensuite obtenir la ligne actualisée dans le cas courant READ COMMITTED de PostgreSQL, voir 17, contrôler sa disponibilité, puis :

```sql
UPDATE movies
SET available_seats = available_seats - 2
WHERE movie_id = 109487 AND available_seats >= 2;
COMMIT;
```

Contrôler le nombre de lignes modifiées avant d’annoncer une réservation. Le comportement précis dépend du SGBDR et du niveau d’isolation ; d’autres niveaux peuvent signaler une erreur de sérialisation.

### Qu’est-ce qu’un interblocage ?

```text
Transaction A verrouille le film 1 puis attend le film 2.
Transaction B verrouille le film 2 puis attend le film 1.
A attend B ; B attend A : cycle d’attente, appelé deadlock.
```

Le SGBDR peut détecter ce cycle et annuler une transaction. Garder les transactions courtes et verrouiller les ressources dans un ordre cohérent aide à limiter ce risque.

## A4 — Équivalent conceptuel optimiste

```text
A : GET du film, mémorise les jetons de modification.
B : GET du même état, mémorise les mêmes jetons.
A : écrit avec ses conditions → accepté.
B : écrit avec les anciennes conditions → HTTP 409.
B : relit, recalcule ou demande une confirmation utilisateur.
```

La lecture ne réserve pas le document. La protection n’est effective que si le client soumet les conditions d’écriture adaptées.

---

# B — Préparer une fiche de film de démonstration

## B1 — Créer un index isolé

```bash
curl -X PUT "$ES_URL/atelier04-movies?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"dynamic":"strict","properties":{
      "movie_id":{"type":"integer"},
      "title":{"type":"text","fields":{"keyword":{"type":"keyword"}}},
      "year":{"type":"integer"},
      "genres":{"type":"keyword"},
      "available_seats":{"type":"integer"},
      "view_count":{"type":"integer"},
      "last_editor":{"type":"keyword"}
    }}
  }'
```

Un shard et zéro réplique simplifient ce lab mono-nœud ; ce n’est pas une illustration de haute disponibilité. Si l’index existe déjà, vérifier son mapping plutôt que le supprimer.

## B2 — Initialiser le film

```bash
curl -X PUT "$ES_URL/atelier04-movies/_doc/109487?refresh=wait_for&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "movie_id":109487,
    "title":"Interstellar",
    "year":2014,
    "genres":["Adventure","Drama","Sci-Fi"],
    "available_seats":20,
    "view_count":10,
    "last_editor":"initialisation"
  }'
```

PUT crée ou remplace l’intégralité de ce document de lab. Ne pas l’utiliser pour réinitialiser une réservation réelle. refresh=wait_for rend l’écriture visible aux recherches ; il ne crée pas de verrou.

```bash
curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

---

# C — _id, _version, _seq_no et _primary_term

## C1 — Lire la réponse, pas seulement _source

Exemple de structure ; les chiffres sont illustratifs :

```json
{
  "_index":"atelier04-movies",
  "_id":"109487",
  "_version":1,
  "_seq_no":0,
  "_primary_term":1,
  "found":true,
  "_source":{
    "movie_id":109487,
    "title":"Interstellar",
    "available_seats":20
  }
}
```

Ne pas copier les nombres de cet exemple dans vos conditions : récupérer ceux de votre cluster.

## C2 — À quoi servent les identifiants et les numéros ?

| Élément | Répond à quelle question ? | Rôle |
|---|---|---|
| _id | Quel document viser dans cet index ? | Identité technique dans l’URL ; reste la même lors d’une modification |
| movie_id | Quel film représente le document ? | Champ métier de votre JSON |
| _version | À quelle version interne du document suis-je ? | Métadonnée de version qui augmente lors des modifications effectives ; pas un historique consultable des anciennes sources |
| _seq_no | Quelle opération a modifié ce document en dernier ? | Séquence attribuée par son shard primaire, pas compteur propre au film |
| _primary_term | Sous quel terme de primaire cette modification a-t-elle été faite ? | Distingue les générations de primaire dans la coordination distribuée |
| _seq_no + _primary_term | Est-ce toujours l’état sur lequel je me suis basé ? | Paire employée par l’OCC moderne |

### Différences importantes

- _id n’est pas une version : le film reste 109487 même après dix modifications.
- movie_id et _id sont volontairement identiques ici, mais Elasticsearch ne les synchronise pas automatiquement.
- _version n’est pas le nombre de vues ni une valeur métier. Un update sans changement peut être un noop et ne pas l’incrémenter.
- _seq_no peut faire des sauts entre deux modifications du même film : d’autres documents du même shard partagent l’espace des numéros d’opérations.
- _primary_term ne change pas à chaque écriture. Le terme porté par une ancienne modification n’est pas à interpréter comme une horloge applicative.
- Le numéro de séquence seul ne remplace pas la paire OCC.
- _version ne permet pas de demander automatiquement « restitue-moi le document tel qu’il était à la version 2 ».

Dans ce TP 9.x, nous ne reprenons pas l’ancien exemple ?version=... pour protéger _update. Nous utilisons if_seq_no et if_primary_term.

## C3 — Retenir la règle

```text
_id : identité du document à modifier.
_version : version interne observée.
_seq_no + _primary_term : état attendu pour autoriser l’écriture conditionnelle.
```

Même titre dans deux documents différents : pas forcément le même _id. Même _version dans deux films : pas une version globale du catalogue. Même _seq_no sur deux shards différents : pas un identifiant global de document.

---

# D — Montrer la perte de mise à jour sans OCC

## D1 — Réinitialiser uniquement les valeurs utiles

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":20,"last_editor":"reset-sans-occ"}}'
```

Les deux clients sont supposés lire 20 avant les deux écritures. A prépare 17 et B prépare 18.

## D2 — A écrit sa valeur, puis B sa valeur devenue ancienne

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":17,"last_editor":"client-a"}}'

curl -X POST "$ES_URL/atelier04-movies/_update/109487?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":18,"last_editor":"client-b"}}'

curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

### Résultat attendu

Les deux appels aboutissent ; available_seats vaut 18. L’effet métier de A a disparu dans ce champ.

L’exécution séquentielle de ces commandes reproduit un entrelacement possible de clients concurrents. La cause est le calcul de B sur une ancienne lecture, pas la vitesse de frappe des commandes.

Une mise à jour partielle _update ne garantit pas que votre valeur numérique a été calculée à partir du dernier état.

---

# E — Protéger l’écriture et comprendre HTTP 409

## E1 — Préparer une lecture commune pour A et B

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":20,"last_editor":"reset-occ"}}'

curl "$ES_URL/atelier04-movies/_doc/109487" -o lecture-initiale.json

SEQ_INITIAL=$(python3 -c 'import json; print(json.load(open("lecture-initiale.json"))["_seq_no"])')
TERM_INITIAL=$(python3 -c 'import json; print(json.load(open("lecture-initiale.json"))["_primary_term"])')
printf 'seq_no=%s ; primary_term=%s\n' "$SEQ_INITIAL" "$TERM_INITIAL"
```

Les deux clients se basent sur ce même état. Un seul terminal suffit pour rendre le conflit reproductible. Le GET direct d’un document est temps réel par défaut : pas besoin d’un refresh de recherche pour cette lecture.

## E2 — Client A : écriture conditionnelle

```bash
curl -i -X POST "$ES_URL/atelier04-movies/_update/109487?if_seq_no=$SEQ_INITIAL&if_primary_term=$TERM_INITIAL&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":17,"last_editor":"client-a"}}'
```

### Explication

- Le chemin vise toujours le même _id, 109487.
- if_seq_no attend le numéro d’opération observé.
- if_primary_term attend le terme associé.
- Le serveur applique la modification seulement si les deux correspondent encore à la dernière modification du document.

Résultat attendu : HTTP 200 et result updated.

## E3 — Client B : réutiliser volontairement l’ancienne paire

Ne pas actualiser les variables entre A et B :

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?if_seq_no=$SEQ_INITIAL&if_primary_term=$TERM_INITIAL&pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":18,"last_editor":"client-b"}}' \
  -o conflit-409.json -w '\nHTTP %{http_code}\n'

python3 -m json.tool conflit-409.json
```

### Résultat attendu

```text
HTTP 409
version_conflict_engine_exception
```

La formulation précise de la raison dépend de la version ; elle indique notamment les conditions attendues et l’état trouvé.

## E4 — Que signifie HTTP 409 ?

409 Conflict signifie ici : votre écriture conditionnelle n’est plus compatible avec l’état actuel du document. A a modifié le film depuis la lecture commune ; l’écriture de B est refusée et n’a pas remplacé les 17 places.

Ce n’est ni une panne d’Elasticsearch, ni un mauvais mot de passe, ni un verrou pessimiste en attente. Le conflit signale que la protection a fonctionné.

Un 409 peut aussi avoir d’autres causes, par exemple create sur un ID déjà existant. Toujours lire le corps d’erreur, pas seulement le numéro.

| Code | Exemple de sens dans le TP |
|---|---|
| 200 | Opération technique réussie ; lire aussi result |
| 400 | Requête ou données invalides |
| 401 | Authentification incorrecte |
| 403 | Droits insuffisants |
| 404 | Document absent |
| 409 | Conflit d’état/version dans l’écriture de ce scénario |

Avec curl seul, une réponse HTTP 409 peut laisser un code de sortie shell égal à zéro : le transfert HTTP a fonctionné. Avec --fail-with-body, le code de sortie est normalement 22. HTTP 409 et code shell 22 ne sont pas le même numéro.

## E5 — Vérifier que B n’a rien écrasé

```bash
curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

available_seats doit rester 17 et last_editor client-a. Les métadonnées décrivent maintenant la modification acceptée de A.

Si A avait déjà reçu 409, une autre écriture a pu se produire après E1 : recommencer à partir d’un état connu. Ne pas enlever les conditions pour faire passer la requête.

---

# F — Résoudre le conflit par relecture et recalcul

## F1 — Relire l’état actuel

```bash
curl "$ES_URL/atelier04-movies/_doc/109487" -o lecture-courante.json
SEQ_COURANT=$(python3 -c 'import json; print(json.load(open("lecture-courante.json"))["_seq_no"])')
TERM_COURANT=$(python3 -c 'import json; print(json.load(open("lecture-courante.json"))["_primary_term"])')
```

## F2 — Recalculer la réservation de B, pas seulement changer les jetons

Supprimer un éventuel ancien fichier de corps local, pas les données serveur :

```bash
rm -f reservation-b.json
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('lecture-courante.json').read_text())
seats = r['_source']['available_seats']
quantity = 2
if seats < quantity:
    raise SystemExit('Places insuffisantes : ne pas envoyer la reservation')
body = {'doc':{'available_seats':seats-quantity,'last_editor':'client-b-recalcule'}}
Path('reservation-b.json').write_text(json.dumps(body), encoding='utf-8')
PY
```

Si le programme réussit et crée le fichier :

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?if_seq_no=$SEQ_COURANT&if_primary_term=$TERM_COURANT&pretty" \
  -H 'Content-Type: application/json' --data-binary @reservation-b.json

curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

### Résultat attendu

17 - 2 = 15 places. Les deux réservations sont prises en compte dans la simulation.

Si un autre client écrit entre F1 et F2, un nouveau conflit reste possible : limiter les tentatives et réévaluer à chaque fois. Remplacer les jetons tout en gardant la valeur obsolète 18 aurait supprimé l’utilité métier du recalcul.

Pour un changement de titre validé manuellement par un utilisateur, demander une confirmation peut être préférable à une fusion automatique.

---

# G — Mise à jour scriptée et retry_on_conflict=3

## G1 — Préparer un compteur de vues

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"view_count":10}}'
```

## G2 — Incrémenter sur l’état courant côté serveur

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?retry_on_conflict=3&pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "script":{
      "lang":"painless",
      "source":"ctx._source.view_count += params.increment;",
      "params":{"increment":1}
    }
  }'
```

### Lire le corps de la requête

| Élément | Rôle |
|---|---|
| script | Demande un calcul serveur au lieu d’une valeur absolue préparée par le client |
| lang painless | Langage de script fourni par Elasticsearch |
| ctx._source | Contenu courant du document dans le contexte de mise à jour |
| params.increment | Valeur variable, ici 1 |
| += | Ajoute à la valeur disponible au moment du traitement |

Le document et son champ doivent déjà exister dans ce test ; pas d’upsert implicite. Ne pas ajouter en parallèle un bloc doc en pensant qu’il sera fusionné avec le script.

Résultat attendu sans autre écriture : view_count vaut 11.

## G3 — Utilité exacte de retry_on_conflict=3

L’API Update réalise conceptuellement : lecture interne → application de la modification → tentative d’écriture. Une autre mise à jour peut intervenir pendant ce cycle.

```text
Tentative initiale
  ├── succès → fin
  └── conflit interne → relire l’état courant et réappliquer la mise à jour
        ├── retry 1
        ├── retry 2 si nécessaire
        └── retry 3 si nécessaire
```

retry_on_conflict=3 autorise au plus trois nouvelles tentatives après la tentative initiale, soit jusqu’à quatre tentatives de mise à jour pour cette requête. Le défaut est zéro retry.

Si une tentative réussit, les retries suivants ne sont pas exécutés. Un seul appel d’incrément réussi ne doit donc pas ajouter quatre vues sous prétexte que la limite est 3.

Si les conflits persistent après la limite, l’appel peut encore se terminer par HTTP 409. Le paramètre ne garantit pas le succès et ne crée pas de verrou.

## G4 — Pourquoi c’est adapté au compteur

Avec le script, Elasticsearch peut relire la nouvelle valeur et refaire +1. La logique dépend explicitement de l’état courant.

En revanche :

```json
{"doc":{"view_count":11}}
```

envoie toujours 11. Ajouter retry_on_conflict=3 à cette valeur absolue ne transforme pas magiquement un ancien calcul client en incrément correct.

### Ce que retry_on_conflict ne fait pas

- Il ne gère pas automatiquement les erreurs 401, 403, un JSON invalide ou toutes les pannes réseau.
- Il ne transforme pas l’opération en transaction multi-documents.
- Il ne remplace pas une décision utilisateur quand deux éditions sont incompatibles.
- Il ne fournit pas de déduplication métier après un timeout.
- Il ne doit pas être combiné dans ce TP avec une paire if_seq_no / if_primary_term figée : une condition sur un ancien état et un recalcul automatique sur un nouvel état sont deux intentions différentes.

## G5 — Retry interne et rejeu client : différence essentielle

Un retry interne relance le traitement d’une tentative en conflit. Une écriture réussie termine la requête.

Si le serveur applique +1 puis que sa réponse réseau se perd, le client peut ignorer le succès. Renvoyer toute la requête peut ajouter encore +1. Il faut alors une stratégie d’idempotence métier, pas seulement retry_on_conflict.

---

# H — Petite simulation concurrente de vues

## H1 — Réinitialiser le compteur

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487" \
  -H 'Content-Type: application/json' -d '{"doc":{"view_count":0}}'
mkdir -p vues
```

## H2 — Lancer cinq appels en parallèle

En mode sécurisé, ajouter les options de la section 2 après curl dans la boucle, comme pour toutes les autres requêtes :

```bash
for i in $(seq 1 5); do
  curl --silent --show-error \
    -X POST "$ES_URL/atelier04-movies/_update/109487?retry_on_conflict=3" \
    -H 'Content-Type: application/json' \
    -d '{"script":{"lang":"painless","source":"ctx._source.view_count += params.increment;","params":{"increment":1}}}' \
    -o "vues/reponse-$i.json" -w '%{http_code}' \
    > "vues/http-$i.txt" 2> "vues/stderr-$i.txt" &
done
wait
```

& lance chaque appel en arrière-plan ; wait attend leur fin. Ce lancement augmente la possibilité de recouvrement, mais ne garantit pas qu’un conflit sera effectivement observé.

## H3 — Contrôler les réponses puis le compteur

```bash
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
counts = Counter()
for i in range(1, 6):
    code = Path(f'vues/http-{i}.txt').read_text().strip()
    try:
        response = json.loads(Path(f'vues/reponse-{i}.json').read_text())
    except (OSError, ValueError):
        counts['reponse_invalide'] += 1
        continue
    if code == '200' and response.get('result') == 'updated':
        counts['updated'] += 1
    else:
        counts['autre_reponse'] += 1
        print('A examiner :', i, code, response)
print(dict(counts))
PY
curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

Si les cinq appels sont confirmés updated et qu’aucun autre client n’a écrit, view_count vaut 5.

Avec un budget de trois retries, des conflits non résolus restent possibles ; ne pas présenter cinq succès comme garanti. En cas de réponse réseau absente, le résultat de l’appel peut être incertain : le nombre de succès confirmés n’est plus une preuve complète du nombre d’écritures réellement appliquées.

Ne pas relancer cette boucle en attendant encore 5 sans réinitialiser le compteur. Les fichiers de réponses sont remplacés lors d’une nouvelle exécution.

---

# I — Défi : éviter les places négatives

## I1 — Énoncé

1. Remettre available_seats à 3.
2. Écrire un script qui retire quantity uniquement si assez de places restent.
3. Utiliser retry_on_conflict=3.
4. Faire quatre demandes successives d’une place.
5. Vérifier trois updated, un noop et zéro place restante.
6. Expliquer pourquoi HTTP 200 ne veut pas forcément dire « réservation acceptée ».

Ce défi successif vérifie d’abord la logique métier. Le lancer ensuite en parallèle est un bonus : analyser alors aussi les conflits éventuellement non résolus.

## I2 — Corrigé

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487" \
  -H 'Content-Type: application/json' \
  -d '{"doc":{"available_seats":3}}'

cat > reservation-script.json <<'JSON'
{
  "script":{
    "lang":"painless",
    "source":"if (params.quantity <= 0) { throw new IllegalArgumentException('Quantite positive requise'); } if (ctx._source.available_seats >= params.quantity) { ctx._source.available_seats -= params.quantity; } else { ctx.op = 'noop'; }",
    "params":{"quantity":1}
  }
}
JSON
```

Exécuter quatre fois, successivement :

```bash
curl -X POST "$ES_URL/atelier04-movies/_update/109487?retry_on_conflict=3&pretty" \
  -H 'Content-Type: application/json' --data-binary @reservation-script.json
```

Puis :

```bash
curl "$ES_URL/atelier04-movies/_doc/109487?pretty"
```

### Explication

Le test available_seats >= quantity et la décrémentation sont exécutés dans la même mise à jour de document. En cas de conflit interne, le script peut être réévalué sur l’état courant.

Dans ce script précis, noop signifie « pas assez de places, aucune mutation ». Il peut être retourné avec HTTP 200 : le traitement technique a réussi mais la réservation n’a pas été effectuée. Lire result, pas seulement le statut.

La signification de noop dépend du script ; ce n’est pas universellement une erreur de réservation. Cette opération reste limitée à un document et ne gère pas le paiement, l’audit métier, la réservation de plusieurs films ni les doublons après réponse perdue.

---

# J — Synthèse et validation

## J1 — Choisir la bonne stratégie

| Besoin | Approche |
|---|---|
| Formulaire basé sur une ancienne lecture | if_seq_no + if_primary_term et traitement du 409 |
| Incrément d’un compteur | Script serveur et retries bornés si recalcul acceptable |
| Places à vérifier et décrémenter sur un seul document | Script conditionnel ; interprétation explicite du résultat |
| Transaction relationnelle sur une ressource | Selon le SGBDR, verrouillage explicite et transaction courte |
| Opération sur plusieurs documents ou systèmes | Architecture transactionnelle/métier adaptée ; ne pas supposer une atomicité globale Elasticsearch |

## J2 — Questions de validation et réponses

1. L’ID change-t-il après modification du titre ? Non, le même document garde son _id.
2. Pourquoi _seq_no peut-il sauter ? Il appartient aux opérations du shard, pas au seul film.
3. Pourquoi garder _primary_term ? La paire identifie la modification attendue dans la coordination du primaire.
4. _version permet-il de lire une ancienne copie ? Non, pas un historique des sources.
5. Un 409 est-il forcément une panne ? Non, c’est ici le refus attendu d’une écriture obsolète.
6. retry_on_conflict=3 signifie-t-il trois écritures réussies ? Non, trois retries au maximum après la tentative initiale.
7. Corrige-t-il une valeur absolue calculée sur une vieille lecture ? Non.
8. Tout SELECT relationnel bloque-t-il les écritures ? Non ; distinguer lecture ordinaire, MVCC et lecture verrouillante.
9. Peut-on relancer aveuglément +=1 après un timeout ? Non, le premier appel peut avoir été appliqué.

## J3 — Dépannage

| Symptôme | Action |
|---|---|
| A reçoit déjà 409 | Relire ; vérifier une autre écriture après la capture |
| B réussit alors qu’un conflit était attendu | Vérifier qu’il utilise bien l’ancienne paire |
| 409 persistant | Relire/réévaluer ou examiner la contention ; ne pas retirer les conditions sans décision |
| Erreur 400 avec retry et conditions | Séparer les deux stratégies |
| Compteur inattendu | Vérifier réponses, relances, reset et autres clients |
| 404 sur _update | Document absent ; pas de création implicite dans ces exemples |
| Erreur de script | Types de _source, paramètres et guillemets JSON/Painless |
| HTTP 200 avec noop | Interpréter la logique du script |

## J4 — Livrables

- Lecture initiale et explication des métadonnées.
- Réponse 409 enregistrée et interprétée.
- Relecture/recalcul avec disponibilité finale de 15.
- Résultat de l’incrément et explication des trois retries.
- Réponses de la simulation concurrente.
- Défi avec zéro place restante et un noop.
- Comparaison optimiste/pessimiste en quelques phrases.

Ne pas enregistrer les mots de passe dans les livrables.

## J5 — Nettoyage optionnel

Après validation du formateur seulement :

```bash
curl -X DELETE "$ES_URL/atelier04-movies?pretty"
```

Cette suppression cible uniquement le nouvel index du TP. Les films des ateliers précédents restent conservés.

## Références et 

Documentation de référence : Elastic, Optimistic concurrency control et Update API ; PostgreSQL, Explicit locking, notamment SELECT FOR UPDATE et deadlocks. La comparaison SQL est illustrative et n’exige pas l’installation d’un SGBDR dans la VM.
