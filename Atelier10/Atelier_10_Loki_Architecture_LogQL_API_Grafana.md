# Atelier 10 — Comprendre Loki et écrire des requêtes LogQL avec ou sans Grafana

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 4, atelier 10 |
| Durée indicative | 2 h à 2 h 30 avec architecture et API |
| Infrastructure | VM Ubuntu de l’atelier 01, sans Docker |
| Prérequis | Atelier 09 actualisé : collecte Alloy de access_log et movies.csv |
| Sources suivies | /var/log/formation-alloy09/access_log et movies.csv |
| Outils | Grafana Explore, curl, Python standard ; LogCLI en complément |
| Livrables | Schéma des composants, bibliothèque LogQL et recherches API/Grafana comparées |

## 1. Introduction : la continuité avec l’atelier 09

L’atelier 09 a configuré Alloy pour lire deux fichiers et les transmettre à Loki. Cet atelier répond à trois questions :

1. Où est Loki, et où sont stockées les données ?
2. Que font ses composants, notamment distributor et ingester ?
3. Comment rechercher les mêmes lignes dans Grafana et directement par l’API ?

```text
Atelier 09 : produire/lire → traiter → transmettre
Atelier 10 : localiser le stockage → comprendre la lecture → rechercher et vérifier
```

Les objectifs LogQL du support initial sont conservés : sélecteurs exacts/regex, filtres de lignes, distinction labels/contenu, AND/OR, casse, recherche d’identifiants et validation des résultats.

Nous ne réutilisons pas les anciens douze logs JSON ni leurs comptes fixes. Le présent atelier garde access_log et movies.csv, avec les labels effectivement définis dans la nouvelle configuration Alloy.

Les parsers structurés seront approfondis à l’atelier 11 et les requêtes métriques à l’atelier 12. Les exercices principaux d’ici portent sur la recherche de lignes.

## 2. Objectifs pédagogiques

À la fin, le participant doit savoir :

- localiser processus, configuration, port HTTP et stockage Loki sur la VM ;
- distinguer Alloy, Loki et Grafana ;
- expliquer les chemins d’écriture et de lecture ;
- décrire distributor, ingester, querier, query frontend, index gateway, compactor et ruler sans les confondre ;
- distinguer composants logiques et services système déployés ;
- envoyer une recherche LogQL via query_range sans interface Grafana ;
- écrire le même LogQL dans Explore et comparer période, limites et résultats ;
- construire des filtres exacts, négatifs et regex sans transformer chaque identifiant en label ;
- relier une anomalie de collecte à son maillon probable, sans réinstaller toute la plateforme.

# A — Où est Loki et quel est son rôle ?

## 3. Loki n’est ni Alloy ni une page dans Grafana

| Élément | Où le trouve-t-on dans le lab ? | Responsabilité |
|---|---|---|
| Fichiers source | /var/log/formation-alloy09/ | Lignes produites ou copiées pour la formation |
| Alloy | Service alloy ; /etc/alloy/config.alloy | Lire les fichiers et pousser les entrées |
| Loki | Service loki-formation, processus Loki sur la VM | Recevoir, conserver et interroger les logs |
| Grafana | Service grafana-server, port 3000 | Interface de recherche et visualisation |
| Navigateur | Poste participant, souvent via SSH | Afficher Grafana ; il n’héberge pas Loki |

Les fichiers ne sont pas « dans Grafana ». Grafana enregistre sa configuration et ses objets, et interroge Loki pour afficher les logs. Si Grafana est indisponible mais Loki fonctionne, l’API Loki peut encore répondre aux recherches.

Alloy conserve son état de lecture et ses éventuels mécanismes de mise en tampon ; ce n’est pas pour autant le stockage historique principal des logs.

## 4. Localiser Loki sur la VM du parcours

### Commandes de diagnostic, sans modifier les services

```bash
sudo systemctl status loki-formation --no-pager
sudo systemctl show loki-formation -p MainPID -p ExecStart -p FragmentPath
sudo systemctl cat loki-formation
command -v loki
sudo ss -ltnp | grep ':3100'
curl -fsS http://127.0.0.1:3100/ready
curl -fsS http://127.0.0.1:3100/loki/api/v1/status/buildinfo | python3 -m json.tool
```

### Repères de l’atelier 01

```text
Unité dédiée : /etc/systemd/system/loki-formation.service
Configuration : /etc/loki-formation/loki.yml
Racine de stockage du lab : /var/lib/loki-formation
API HTTP : http://127.0.0.1:3100
```

Le chemin exact du binaire est celui d’ExecStart, pas nécessairement un emplacement à deviner. Si le formateur a préparé une autre unité, vérifier et adapter ces repères.

Pour examiner le profil local :

```bash
sudo ls -ld /var/lib/loki-formation
sudo less /etc/loki-formation/loki.yml
sudo journalctl -u loki-formation -n 100 --no-pager
```

Dans la configuration de référence : stockage filesystem, index TSDB, schéma v13, réplication 1 et ring local inmemory. Les sous-répertoires effectifs dépendent de cette configuration et de la version ; inspecter, ne pas les déplacer ou les effacer pour un test de requête.

### Point de contrôle

Le participant indique : le PID, le fichier de config, le port, le compte de service et le chemin persistant. ready confirme un état de préparation, pas la présence des six sondes de cet atelier.

## 5. Comprendre le mode monolithique de notre laboratoire

Loki possède une architecture modulaire. Plusieurs fonctions peuvent être exécutées dans un seul processus, ou réparties dans plusieurs processus/services sur une plateforme plus importante.

| Mode | Principe | Dans ce TP |
|---|---|---|
| Monolithique / single binary | Fonctions regroupées dans un même processus, cible all par défaut | Oui, selon l’unité de référence de l’atelier 01 |
| Regroupé read/write/backend | Fonctions réunies par groupes de déploiement | Présentation conceptuelle seulement |
| Distribué / microservices | Composants déployés séparément selon les besoins | Pas de déploiement supplémentaire |

Le fait d’expliquer distributor et ingester ne signifie pas qu’il faut lancer deux nouvelles unités systemd. Ne pas chercher obligatoirement un service nommé distributor.service sur cette VM.

Les composants optionnels et leurs détails d’exécution dépendent du mode, de la configuration et de la version. Le schéma suivant explique les responsabilités ; il n’annonce pas tous les composants comme services autonomes actifs dans le lab.

## 6. Chemin d’écriture : de la ligne à son stockage

```text
access_log / movies.csv
        │ lecture des fichiers et positions
        ▼
Alloy : source → process → write
        │ POST /loki/api/v1/push
        ▼
Loki : distributor → ingester(s) → chunks + index / stockage configuré
```

### Distributor : recevoir, vérifier et orienter

- Reçoit les requêtes push des collecteurs/clients.
- Participe aux validations et limites de l’ingestion.
- Détermine les ingesters destinataires à partir du flux et du ring.
- Transmet les entrées selon la réplication configurée.

Il ne lit pas directement movies.csv sur disque, ne remplace pas Alloy et n’est pas le stockage historique. Le mot distributor désigne un rôle de distribution, pas une base de données.

### Ingester : accumuler et persister les données de flux

- Reçoit les entrées qui lui sont affectées.
- Les organise dans des chunks, blocs de lignes compressées par flux.
- Gère les données récentes encore disponibles en mémoire et leur persistance vers le backend configuré.
- Peut répondre aux recherches concernant les données récentes.

Les mécanismes de journalisation/WAL dépendent de la configuration retenue. Ne pas promettre qu’une simple présence en mémoire protège contre toutes les pertes.

### Réplication et ring

Le ring décrit notamment quels ingesters participent et comment les flux leur sont affectés. Ce n’est pas le répertoire contenant les fichiers de logs. En distribué, la réplication peut protéger contre certaines indisponibilités ; la réplication 1 du lab n’est pas une architecture hautement disponible.

Un rejet peut provenir des règles et limites de l’ensemble du chemin d’ingestion : lire la réponse et les journaux plutôt qu’attribuer toute erreur au distributor par principe.

## 7. Streams, labels, chunks et index

### Une entrée Loki

```text
Timestamp Loki + ensemble de labels + texte de la ligne
```

Une même combinaison de labels définit un stream. Les entrées sont compressées dans des chunks. L’index principal permet de retrouver les flux et blocs pertinents selon labels et temps ; ce n’est pas un index plein texte de tous les mots comme dans l’usage Elasticsearch étudié précédemment.

### Exemple du parcours

```text
job=atelier09, dataset=access, service=web-formation, status_class=5xx, ...
```

Le code Apache complet reste dans la ligne. movieId n’est pas une clé d’upsert Loki et une IP ne devient pas un label simplement parce qu’elle apparaît dans le texte.

Cette organisation explique l’ordre de travail : limiter la période, sélectionner les bons labels, puis examiner le contenu des chunks retenus avec les filtres nécessaires.

## 8. Chemin de lecture : qui exécute LogQL ?

```text
Grafana Explore ─┐
curl / Python ──┼─► API de lecture Loki → querier(s) → données récentes + stockage
LogCLI ─────────┘            ▲                              │
                            └──────── réponse ─────────────┘
```

Sur une plateforme distribuée, un frontend, un scheduler et des caches peuvent intervenir. Sur la VM, les fonctions peuvent être regroupées dans le processus Loki.

### Tableau des composants de lecture et de fond

| Composant | Rôle | À ne pas confondre avec |
|---|---|---|
| Querier | Exécuter LogQL, sélectionner/lire les données nécessaires, produire les résultats | Grafana, qui présente la requête et la réponse |
| Query frontend | Entrée optionnelle d’optimisation de lecture : découpage, ordonnancement/caches selon configuration | Une interface graphique |
| Query scheduler | Files et répartition du travail entre composants de requête, si utilisé | Le planificateur cron d’Ubuntu |
| Index gateway | Servir des informations de l’index et aider les accès correspondants dans les déploiements adaptés | Un proxy HTTP public de sécurité |
| Compactor | Compacter les index ; appliquer la rétention lorsque celle-ci est configurée | Une sauvegarde automatique ou une rétention toujours active |
| Ruler | Évaluer des règles d’enregistrement/alerte à partir de LogQL si configuré | Toute l’interface Grafana Alerting |
| Stockage | Conserver chunks et index selon le backend | Grafana ou le fichier de positions Alloy |

La recherche peut combiner des données récentes des ingesters et des données du stockage. Ne pas supposer que les logs doivent attendre une écriture définitive dans un fichier de chunks avant de pouvoir apparaître en recherche.

### Ce qui n’est pas configuré automatiquement

Le fait que Loki soit installé ne crée pas vos règles d’alerte, seuils métier, rétention souhaitée, sauvegardes ni droits d’accès. Ces choix doivent être conçus explicitement.

# B — Préparer un test directement relié à l’atelier 09

## 9. Conserver la collecte existante

### Vérifications

```bash
sudo systemctl status alloy loki-formation grafana-server --no-pager
sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
sudo -u alloy alloy validate /etc/alloy/config.alloy
```

Le dernier test est pertinent si le service utilise ce fichier. Aucun changement Alloy n’est nécessaire pour les exercices.

### Labels attendus de la configuration actualisée

| Label | access | movies |
|---|---|---|
| job | atelier09 | atelier09 |
| dataset | access | movies |
| service | web-formation | movielens-import |
| format | apache_combined | csv |
| environment | formation | formation |
| time_basis | collection dans le parcours de base | collection |
| status_class | 1xx à 5xx si reconnue | absent |

filename peut être ajouté par la source. Vérifier les vrais labels dans une réponse avant de construire un sélecteur exigeant un champ inexistant.

Nous gardons job=atelier09 car il décrit la chaîne de collecte configurée. Le numéro de l’exercice ne modifie pas automatiquement ce label.

## 10. Générer six sondes dans les mêmes deux fichiers

### Objectif

Disposer de résultats contrôlés tout en conservant les vraies lignes déjà collectées.

```bash
mkdir -p ~/formation-observabilite/atelier10
cd ~/formation-observabilite/atelier10
sudo python3 generer_scenario10.py --report scenario10.json
```

Le script joint ajoute quatre lignes Apache et deux lignes CSV ; il ne remplace aucun fichier suivi et ne touche pas au stockage Alloy/Loki. Il refuse un rapport existant : pour rejouer volontairement, choisir un autre --report.

### Lignes du lot

| Corpus | Statut / contenu | Nombre |
|---|---|---:|
| access | 200, completed | 1 |
| access | 404, missing resource | 1 |
| access | 503, timeout upstream | 1 |
| access | 200, recovered after timeout | 1 |
| movies | Catalogue avec virgule et guillemets dans le titre | 1 |
| movies | Voyage sans erreur | 1 |

Les six lignes contiennent le même marker unique A10-.... Ce marqueur reste dans le contenu ; on ne crée pas un nouveau label par exécution de TP.

Le rapport prouve que le script a écrit, pas que Loki a tout reçu. Attendre quelques secondes et vérifier les marqueurs.

## 11. Fixer une fenêtre commune aux recherches

### Pourquoi ne pas comparer deux Last 15 minutes à des moments différents ?

Les fenêtres glissent. Pour comparer strictement une réponse API à Explore, figer la même période après l’arrivée des sondes :

```bash
python3 figer_fenetre10.py --scenario scenario10.json --output fenetre10.json
```

Le fichier fournit start_ns, end_ns, from_utc et to_utc. Il peut être régénéré si l’on constate que les sondes n’étaient pas encore collectées à la borne de fin ; noter alors la nouvelle période utilisée.

Le script de scénario conserve une petite marge avant l’écriture. La borne de fin doit inclure la collecte, qui peut être postérieure à l’écriture du fichier.

### Explication temporelle

Dans le parcours principal A09, le timestamp Loki est celui de collecte. La date Apache originale reste dans le texte des archives. Les sondes sont actuelles. Si vous avez activé la variante stage.timestamp à l’atelier 09, noter cette différence et vérifier le label/périmètre de recherche.

Une date de sortie de film n’est toujours pas le timestamp de collecte de la ligne CSV.

# C — Écrire des requêtes sans Grafana

## 12. API Loki : les endpoints à connaître

```bash
export LOKI_URL='http://127.0.0.1:3100'
```

| Endpoint | Méthode | Usage |
|---|---|---|
| /ready | GET | État de préparation |
| /loki/api/v1/status/buildinfo | GET | Informations de version |
| /loki/api/v1/labels | GET | Noms de labels sur le périmètre demandé |
| /loki/api/v1/label/dataset/values | GET | Valeurs d’un label connu |
| /loki/api/v1/series | GET | Combinaisons de labels correspondant aux sélecteurs |
| /loki/api/v1/query_range | GET | Recherche sur un intervalle, utilisée ici pour les lignes |
| /loki/api/v1/query | GET | Évaluation instantanée, surtout utile aux requêtes métriques |
| /loki/api/v1/push | POST | Ingestion, pas recherche |

On écrit du LogQL, pas du SQL ni une requête Elasticsearch DSL. Pour les recherches de lignes de cet atelier, utiliser query_range.

### Réseau et authentification

Ces commandes s’exécutent sur la VM où Loki écoute en local. Depuis le poste participant, 127.0.0.1 pointe vers le poste : ouvrir si nécessaire un tunnel dédié autorisé :

```bash
ssh -N -L 13100:127.0.0.1:3100 utilisateur@IP_PUBLIQUE_VM
```

Puis utiliser http://127.0.0.1:13100 côté poste, sans ouvrir le port 3100 sur Internet.

Le profil local de l’atelier 01 est sans couche d’authentification Loki externe. Un déploiement protégé peut exiger authentification, CA et en-tête de tenant. X-Scope-OrgID identifie un tenant quand la multi-tenance l’exige ; ce n’est pas un mot de passe et il ne faut pas l’ajouter arbitrairement au lab. Les identifiants de connexion Grafana ne s’utilisent pas automatiquement comme identifiants HTTP Loki.

## 13. Découvrir les labels par curl

```bash
START=$(python3 -c 'import json; print(json.load(open("fenetre10.json"))["start_ns"])')
END=$(python3 -c 'import json; print(json.load(open("fenetre10.json"))["end_ns"])')

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/labels" \
  --data-urlencode "start=$START" --data-urlencode "end=$END"

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/label/dataset/values" \
  --data-urlencode "start=$START" --data-urlencode "end=$END"

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/series" \
  --data-urlencode 'match[]={job="atelier09"}' \
  --data-urlencode "start=$START" --data-urlencode "end=$END"
```

### Explication

Les valeurs de labels et les séries ne sont pas des lignes de logs. Elles peuvent refléter d’autres lignes de la même fenêtre ; le marqueur est dans le contenu, donc ne sert pas de matcher de série indexé.

Si aucun label attendu ne revient, vérifier période, URL et collecte avant d’écrire une regex plus compliquée.

## 14. Première recherche de lignes par curl

### Préparer un fichier LogQL avec le vrai marqueur

```bash
python3 - <<'PY'
import json
from pathlib import Path
marker=json.loads(Path('scenario10.json').read_text())['marker']
Path('recherche-ensemble.logql').write_text(
    '{job="atelier09"} |= "'+marker+'"\n',encoding='utf-8')
Path('recherche-timeout.logql').write_text(
    '{job="atelier09",dataset="access"} |= "'+marker+'" |= "timeout" != "recovered"\n',
    encoding='utf-8')
PY
```

### Exécuter la requête complète

```bash
curl --fail-with-body -G "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode "query=$(cat recherche-ensemble.logql)" \
  --data-urlencode "start=$START" --data-urlencode "end=$END" \
  --data-urlencode 'direction=forward' --data-urlencode 'limit=100' \
  -o reponse-ensemble.json

python3 -m json.tool reponse-ensemble.json
```

### Comprendre chaque paramètre

| Paramètre | Rôle |
|---|---|
| -G | Construire une requête GET avec des paramètres |
| query | Expression LogQL |
| --data-urlencode | Encoder accolades, guillemets, espaces, pipes et caractères spéciaux |
| start / end | Fenêtre d’interrogation ; ici chaînes en nanosecondes Unix |
| direction forward | Demander les lignes dans le sens chronologique |
| limit 100 | Plafond du nombre de lignes retournées |
| -o | Conserver le JSON pour contrôle |

Résultat attendu : six lignes du lot si toutes sont collectées dans la fenêtre, sans doublon et sous les limites. Le total de l’ancien access_log ne change pas ce résultat car le marker isole les sondes.

Si moins de six lignes apparaissent, vérifier la collecte avant de modifier le fichier source. Si la collecte est plus tardive, étendre la fenêtre et relancer. Si plus de six apparaissent, examiner relecture et doublons ; ne pas effacer l’état pour obtenir le nombre voulu.

## 15. Lire le JSON de réponse et ne pas confondre flux et lignes

Une réponse de recherche de logs possède notamment :

```json
{
  "status":"success",
  "data":{
    "resultType":"streams",
    "result":[{
      "stream":{"job":"atelier09","dataset":"access","status_class":"5xx"},
      "values":[["1790000000000000000","ligne Apache illustrative"]]
    }]
  }
}
```

Ce fragment illustre la structure, pas une réponse du lot généré.

- stream contient les labels de ce flux.
- values contient ses paires timestamp/texte.
- Les timestamps de cet exemple sont des chaînes en nanosecondes, pas des millisecondes.
- Un flux peut contenir plusieurs lignes ; le nombre de blocs result n’est pas le nombre de logs.
- Les flux sont regroupés dans le JSON ; leur ordre de présentation n’est pas forcément une table globale aplatie triée.

### Contrôle simple

```bash
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('reponse-ensemble.json').read_text())
if r.get('status')!='success' or r.get('data',{}).get('resultType')!='streams':
    raise SystemExit('Reponse Loki inattendue : '+str(r))
streams=r['data']['result']
print('Flux recus :',len(streams))
print('Lignes recues :',sum(len(x.get('values',[])) for x in streams))
for stream in streams:
    print(stream['stream'])
PY
```

Le compte est celui des lignes reçues, pas une volumétrie exhaustive garantie : la limite de requête et les limites serveur s’appliquent. Il n’existe pas de hits.total de type Elasticsearch à supposer dans cette structure.

## 16. Rechercher avec Python standard

### Objectif

Automatiser la même API sans bibliothèque Loki et afficher les timestamps lisiblement.

Le script interroger_loki.py joint effectue GET query_range, encode les paramètres et sauvegarde la réponse brute.

```bash
python3 interroger_loki.py --query-file recherche-ensemble.logql \
  --window fenetre10.json --output reponse-python-ensemble.json

python3 interroger_loki.py --query-file recherche-timeout.logql \
  --window fenetre10.json --output reponse-python-timeout.json
```

Attendus sur le lot isolé : six lignes, puis une ligne 503 contenant timeout upstream.

### Explication

- --query accepte une expression directe ; --query-file lit un fichier.
- --window reprend exactement les bornes figées ; sinon le défaut est les quinze dernières minutes.
- --limit et --direction contrôlent le résultat, pas la conservation des données.
- Le script trie localement les lignes retournées pour les présenter ; il ne récupère pas magiquement les lignes au-delà du plafond API.
- Un fichier de sortie existant est refusé pour préserver les preuves ; choisir un nouveau nom pour un nouveau test.
- Aucun secret Grafana n’est nécessaire sur le profil Loki local de ce TP.

Ce client vise le lab local. Un environnement protégé demande une adaptation explicite de son authentification et du tenant ; ne pas coder les secrets dans le fichier pour contourner cela.

## 17. LogCLI : troisième manière d’interroger sans Grafana

### Objectif

Identifier le client officiel de ligne de commande, sans ajouter une installation obligatoire au TP.

Si le formateur a préparé LogCLI depuis une source officielle :

```bash
command -v logcli
logcli --version
logcli help query

FROM=$(python3 -c 'import json; print(json.load(open("fenetre10.json"))["from_utc"])')
TO=$(python3 -c 'import json; print(json.load(open("fenetre10.json"))["to_utc"])')
QUERY=$(cat recherche-timeout.logql)

logcli --addr="$LOKI_URL" query --from="$FROM" --to="$TO" \
  --forward --limit=100 "$QUERY"
```

Vérifier l’aide de la version installée pour les options disponibles. LogCLI n’est pas automatiquement présent parce que Grafana est installé. Si absent, curl et Python suffisent à tous les exercices obligatoires.

LogCLI traduit la demande en appels à Loki ; ce n’est pas un stockage supplémentaire. Il ne faut pas confondre une requête distante avec un filtrage local d’un fichier sur stdin.

# D — Écrire les mêmes requêtes dans Grafana

## 18. Grafana Explore n’utilise pas un autre langage

### Procédure

1. Ouvrir Grafana via le tunnel habituel vers le port 3000.
2. Ouvrir Explore et la datasource Loki-Formation.
3. Passer en mode Code.
4. Copier le texte de recherche-ensemble.logql.
5. Définir une période absolue correspondant à from_utc/to_utc de fenetre10.json ; vérifier le fuseau affiché.
6. Exécuter une recherche Range, pas Live tail pour ce test comparatif.
7. Reprendre recherche-timeout.logql.

### Résultats attendus

Même ensemble de six lignes, puis même 503 que dans l’API, à bornes et limites compatibles. Si l’interface arrondit les bornes de temps, les placer avec une marge qui conserve exactement le lot identifié par son marqueur.

Les barres de volume et l’affichage Explore sont une présentation ; ils n’ajoutent pas de nouvelles lignes au fichier et ne déclenchent pas Alloy.

### Comparer correctement

Même datasource/destination Loki, même expression, même période, même tenant si applicable, limites et direction compatibles. Vérifier les filtres ajoutés par l’interface et les options de déduplication/affichage avant de conclure que l’API et Grafana sont incohérents.

# E — Sélecteurs et filtres de lignes sur les deux corpus

## 19. Distinguer labels et contenu

```logql
{job="atelier09", dataset="access", status_class="5xx"}
```

Ceci sélectionne des flux par leurs labels. status_class existe parce que la configuration Alloy de l’atelier 09 l’a extrait et promu, pas parce que Loki reconnaît automatiquement Apache.

```logql
{job="atelier09", dataset="movies"} |= "Voyage"
```

Ceci sélectionne les flux movies puis filtre leur contenu CSV. Les colonnes movieId/title/genres ne sont pas automatiquement des labels.

```logql
{job="atelier09", movieId="9001001"}
```

N’est pas une recherche valide de colonne pour notre modèle : ce label n’a pas été créé. La requête peut être syntaxiquement acceptée mais ne retrouver aucune ligne.

Pour les exercices suivants, ajouter |= "MARQUEUR_REEL" à chaque requête quand un résultat chiffré doit se limiter au lot des six sondes.

## 20. Sélecteurs exacts et négatifs

Tous les logs collectés par la chaîne du TP :

```logql
{job="atelier09"}
```

Access uniquement :

```logql
{job="atelier09",dataset="access",environment="formation"}
```

Sans movies :

```logql
{job="atelier09",dataset!="movies"}
```

### Explication

Les virgules sont un AND. Les labels sont sensibles à la casse. Un matcher négatif peut aussi inclure des flux dépourvus de ce label selon sa correspondance avec la valeur vide ; pour cibler exactement access, préférer dataset="access".

Un sélecteur doit garder au moins un matcher qui ne correspond pas à la chaîne vide, comme job="atelier09". Une sélection négative seule et trop large n’est pas une bonne base d’investigation.

## 21. Regex de labels : ancrage complet

Deux corpus connus :

```logql
{job="atelier09",dataset=~"access|movies"}
```

Classes d’erreur :

```logql
{job="atelier09",dataset="access",status_class=~"4xx|5xx"}
```

Ne pas écrire deux égalités dataset="access",dataset="movies" pour exprimer un OR : elles seraient contradictoires sur un même flux.

Les regex de labels sont entièrement ancrées. service=~"formation" ne veut pas dire « contient formation » ; service=~".*formation.*" exprimerait ce besoin.

RE2 n’offre pas toutes les fonctionnalités PCRE : éviter notamment lookarounds et backreferences non pris en charge.

## 22. Inclusion littérale avec |=

```logql
{job="atelier09",dataset="access"} |= "timeout"
```

Avec le marqueur du lot : deux lignes, une 503 et une 200 de rétablissement.

|= cherche une sous-chaîne sensible à la casse. La présence de timeout n’est pas une preuve d’échec. De même, un titre CSV contenant le mot erreur ne constitue pas un incident du pipeline d’import.

Pour un exemple sur movies :

```logql
{job="atelier09",dataset="movies"} |= "Catalogue"
```

Avec le marqueur du lot : une ligne, malgré sa virgule et ses guillemets CSV. Le filtre cherche du texte ; il ne découpe pas correctement toutes les colonnes.

## 23. Exclusion de ligne avec !=

```logql
{job="atelier09",dataset="access"} |= "timeout" != "recovered"
```

Avec le marqueur : une ligne, le 503 du lot.

Ce != porte sur le texte, contrairement à dataset!="movies" dans les accolades. Les filtres successifs se combinent par AND et s’appliquent à la ligne sélectionnée.

Exclure recovered est pertinent pour le texte contrôlé du TP, pas une règle universelle de reconnaissance d’incident. Un message réel peut mentionner le rétablissement d’un autre composant tout en décrivant un échec.

## 24. Regex de ligne et alternative OR

```logql
{job="atelier09",dataset="access"} |~ "timeout|missing"
```

Avec le marqueur : trois lignes, deux contenant timeout et une contenant missing.

```logql
{job="atelier09",dataset="access"} |= "timeout" |= "missing"
```

Avec le marqueur : zéro, car le lot ne contient pas les deux mots dans une même ligne.

Pour ignorer la casse :

```logql
{job="atelier09",dataset="access"} |~ "(?i)TIMEOUT"
```

Pour exclure un motif :

```logql
{job="atelier09",dataset="access"} |= "timeout" !~ "(?i)recovered|recovery"
```

Contrairement aux matchers de labels, les regex de ligne ne sont pas entièrement ancrées ; timeout peut correspondre à une partie de la ligne. Utiliser |= pour une simple chaîne et réserver la regex aux besoins qui la justifient.

## 25. Rechercher un code HTTP dans le texte : limites

```logql
{job="atelier09",dataset="access"} |= "503"
```

Peut retrouver le code, mais aussi une IP, un identifiant ou une URL contenant ces chiffres. Pour la famille 5xx, utiliser le label existant status_class="5xx".

Une regex illustrant la place du statut après la requête entre guillemets peut être :

```logql
{job="atelier09",dataset="access"} |~ `" (4|5)[0-9]{2} `
```

Ce motif est plus contextuel qu’un chiffre isolé, mais ne remplace pas un parseur Apache complet. L’atelier 11 permettra de comparer un champ extrait plutôt que de multiplier les suppositions textuelles.

Les backticks définissent une chaîne brute LogQL : les guillemets peuvent y être écrits directement. Ne pas ajouter arbitrairement les échappements d’une chaîne JSON si l’éditeur attend du LogQL brut.

## 26. Retrouver un identifiant sans en faire un label

Le marker du scénario se trouve dans le chemin Apache et dans les titres CSV :

```logql
{job="atelier09"} |= "MARQUEUR_REEL"
```

Six lignes sont attendues sur le lot, deux formats réunis. Il s’agit d’une corrélation pédagogique explicite entre sondes, pas de la preuve qu’un vrai utilisateur HTTP a déclenché l’import de ces films.

Un identifiant partiel peut correspondre à plusieurs valeurs. Choisir un marqueur complet, un intervalle et des labels cohérents. Dans un système réel, plusieurs lignes peuvent partager un run_id ou request_id ; cet identifiant n’a pas besoin de devenir un label de flux pour être recherché.

## 27. Construire une investigation progressive

### Scénario

Une sonde montre un timeout. Trouver l’échec, le distinguer du rétablissement et conserver les preuves avec et sans Grafana.

```text
1. Période de collecte et marqueur du lot
2. job atelier09
3. dataset access
4. lignes contenant timeout
5. distinguer 503 et 200 de rétablissement
6. conserver le texte, les labels, le timestamp Loki et la date Apache
7. vérifier avec curl / Python puis Explore
```

Une bonne investigation examine les résultats intermédiaires. Un filtre prématuré trop restrictif peut masquer la ligne de rétablissement qui explique la chronologie.

Le 503 de nos sondes est synthétique. Un vrai 503 ne prouve pas seul la cause racine : il faudrait examiner le service amont, l’état du pipeline et d’autres signaux de contexte.

# F — Synthèse, défi et diagnostic

## 28. Matrice des opérateurs

| Position | Opérateur | Sens |
|---|---|---|
| Dans {...} | = | Égalité exacte d’un label |
| Dans {...} | != | Exclusion d’une valeur de label |
| Dans {...} | =~ | Regex sur toute la valeur du label |
| Dans {...} | !~ | Exclusion par regex de label |
| Après {...} | \|= | Sous-chaîne présente dans la ligne |
| Après {...} | != | Sous-chaîne absente de la ligne |
| Après {...} | \|~ | Regex présente dans la ligne |
| Après {...} | !~ | Regex absente de la ligne |

Virgules de labels = AND ; filtres successifs = AND ; alternative regex a|b = OR entre motifs. Les requêtes ne créent pas automatiquement de nouveaux labels d’ingestion.

## 29. Défi final

Sur le lot des six sondes :

1. Localiser Loki : processus, config, stockage et port.
2. Expliquer le rôle de distributor et ingester dans l’écriture, puis querier dans la lecture.
3. Retrouver les six lignes avec leur marker.
4. Séparer quatre access et deux movies.
5. Retrouver deux lignes timeout, puis une seule hors recovered.
6. Retrouver les trois lignes timeout OU missing.
7. Retrouver les deux lignes 4xx/5xx par regex sur status_class.
8. Exécuter la même recherche finale en curl et dans Explore sur la même fenêtre.
9. Expliquer pourquoi le nombre de flux n’est pas six et pourquoi Grafana n’est pas le stockage.

Pour chaque recherche : période, LogQL exact, limite et nombre de lignes reçues/affichées. Aucun effacement de fichiers ou d’état n’est requis.

## 30. Corrigé et références attendues

La bibliothèque requetes-logql-atelier10.md jointe contient les requêtes complètes avec le filtre de marqueur. Valeurs attendues :

| Besoin | Lignes |
|---|---:|
| Lot entier | 6 |
| Access | 4 |
| Movies | 2 |
| Timeout | 2 |
| Timeout hors rétablissement | 1 |
| Timeout ou missing | 3 |
| Classes 4xx ou 5xx | 2 |

Exemple complet du dernier cas :

```logql
{job="atelier09",dataset="access",status_class=~"4xx|5xx"} |= "MARQUEUR_REEL"
```

Les comptes supposent un lot unique, correctement collecté, sans doublons, couvert par la période et sous les limites. Moins ou plus de lignes demande une investigation, pas une réinitialisation destructrice.

### Réponse d’architecture attendue

Alloy lit ; le distributor reçoit et oriente ; l’ingester gère les chunks et données récentes puis leur stockage ; le querier exécute la recherche ; Grafana l’envoie et présente la réponse. Sur notre VM, ces rôles Loki ne sont pas nécessairement des processus séparés.

## 31. Diagnostiquer le bon maillon

| Symptôme | Vérification |
|---|---|
| Pas de processus/écoute Loki | systemd, ExecStart, configuration et journaux |
| ready mais pas de sondes | Fichier écrit, Alloy, droits, destinations et limites d’ingestion |
| Lignes visibles par API, pas Grafana | Datasource, période, droits, filtres et limite d’affichage |
| Grafana inaccessible | Tunnel, service Grafana ; tester Loki séparément |
| Requête API 400 | LogQL, encodage, bornes et limites serveur |
| Requête très large | Période et labels avant regex de contenu |
| status_class absent | Configuration/stage.template A09, motif non reconnu ; inspecter la ligne |
| Résultats incomplets | Période trop courte, collecte tardive, limite ou erreurs |
| Colonne CSV introuvable en label | CSV brut non converti en labels/champs persistants |
| Même ID de film plusieurs fois | Entrées de log, pas upserts Elasticsearch |

Ne pas confondre une politique multi-tenant et une authentification. Ne pas modifier la rétention ni désactiver les limites de dates pour résoudre une mauvaise période de recherche.

## 32. Bonnes pratiques et évaluation

- Commencer par une période précise et des labels utiles.
- Préférer les filtres littéraux quand ils suffisent.
- Ne pas ajouter IP, titre ou identifiant unique comme label pour une recherche ponctuelle.
- Comparer les mêmes fenêtres et destinations dans les différents clients.
- Conserver le JSON brut comme preuve, sans l’annoncer exhaustif au-delà de la limite.
- Ne pas tirer de benchmark d’un lot de six lignes.
- Distinguer trace d’événement, signal de service et preuve de cause racine.

### Livrables

Schéma de la VM et des chemins, bibliothèque de requêtes expliquée, scenario10.json, fenetre10.json, réponses API et capture Explore. Aucun mot de passe, token, requête sensible ou IP réelle à diffuser sans contrôle.

## 33. Conservation et suite

Conserver les deux fichiers, les services et l’état de lecture. Les exercices suivants réutiliseront access et movies ; les anciens exemples JSON/logfmt doivent être adaptés ou introduits explicitement, pas supposés présents.

L’atelier 11 approfondira le parsing des lignes à la requête, avec attention au CSV et à ses virgules. L’atelier 12 construira des métriques et taux à partir de sélections validées.

## Annexes — Scripts complets

### generer_scenario10.py

```python
import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Six sondes dans les deux fichiers conserves depuis A09')
p.add_argument('--directory', default='/var/log/formation-alloy09')
p.add_argument('--report', default='scenario10.json')
a = p.parse_args()
base = Path(a.directory)
report_path = Path(a.report)
if report_path.exists():
    p.error('Rapport deja present : choisir un nouveau --report')
paths = [base/'access_log',base/'movies.csv']
for path in paths:
    if not path.is_file():
        p.error('Fichier A09 absent : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        if f.tell():
            f.seek(-1,2)
            if f.read(1) != b'\n':
                p.error('Saut de ligne final absent : '+str(path))
start_ns=time.time_ns()-5_000_000_000
now=datetime.now(timezone.utc)
marker=now.strftime('A10-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
rows=[(200,'completed'),(404,'missing resource'),(503,'timeout upstream'),(200,'recovered after timeout')]
with paths[0].open('a',encoding='utf-8') as f:
    for number,(status,message) in enumerate(rows,1):
        f.write(f'127.0.0.1 - - [{stamp}] "GET /atelier10/{marker}/probe-{number} HTTP/1.1" {status} 128 "-" "A10 {message}"\n')
with paths[1].open('a',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n')
    writer.writerow([9001001,f'Catalogue {marker}, edition "test" (2026)','Documentary'])
    writer.writerow([9001002,f'Voyage {marker} sans erreur (2026)','Adventure|Sci-Fi'])
report={'marker':marker,'start_ns':str(start_ns),'written_at_utc':now.isoformat(),
        'access_entries':4,'movies_entries':2,'expected_loki_entries':6,
        'note':'Sondes synthetiques A10 ; meme collecte A09 ; ne prouve pas une livraison Loki'}
with report_path.open('x',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
```

### figer_fenetre10.py

```python
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Figer une periode commune pour API et Grafana')
p.add_argument('--scenario',default='scenario10.json')
p.add_argument('--output',default='fenetre10.json')
a=p.parse_args()
source=json.loads(Path(a.scenario).read_text(encoding='utf-8'))
start=int(source['start_ns'])
end=time.time_ns()
if start >= end:
    p.error('Debut incoherent avec l horloge actuelle')
def rfc3339(ns):
    seconds,nanos=divmod(ns,1_000_000_000)
    return datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z'
result={'marker':source['marker'],'start_ns':str(start),'end_ns':str(end),
        'from_utc':rfc3339(start),'to_utc':rfc3339(end)}
Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
```

### interroger_loki.py

```python
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Recherche de lignes LogQL via API Loki query_range')
g=p.add_mutually_exclusive_group(required=True)
g.add_argument('--query')
g.add_argument('--query-file')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--window',help='Fichier fenetre10.json ; sinon les 15 dernieres minutes')
p.add_argument('--limit',type=int,default=100)
p.add_argument('--direction',choices=['forward','backward'],default='forward')
p.add_argument('--output',default='reponse-loki.json')
a=p.parse_args()
if a.limit < 1:
    p.error('--limit doit etre positif et rester compatible avec les limites serveur')
url=a.url.rstrip('/')
if urllib.parse.urlsplit(url).scheme not in ['http','https']:
    p.error('--url doit etre une URL HTTP ou HTTPS')
query=Path(a.query_file).read_text(encoding='utf-8').strip() if a.query_file else a.query
if not query.strip():
    p.error('Requete vide')
if Path(a.output).exists():
    p.error('Sortie deja presente : choisir un nouveau --output')
if a.window:
    window=json.loads(Path(a.window).read_text(encoding='utf-8'))
    start,end=int(window['start_ns']),int(window['end_ns'])
else:
    end=time.time_ns()
    start=end-15*60*1_000_000_000
if start>=end:
    p.error('Periode invalide')
params={'query':query,'start':str(start),'end':str(end),'limit':str(a.limit),'direction':a.direction}
request=urllib.request.Request(url+'/loki/api/v1/query_range?'+urllib.parse.urlencode(params))
try:
    with urllib.request.urlopen(request,timeout=30) as response:
        result=json.load(response)
except urllib.error.HTTPError as exc:
    raise SystemExit(f'HTTP {exc.code} : '+exc.read().decode('utf-8',errors='replace')[:3000])
except urllib.error.URLError as exc:
    raise SystemExit('Connexion Loki impossible : '+str(exc.reason))
if result.get('status')!='success' or result.get('data',{}).get('resultType')!='streams':
    raise SystemExit('Reponse de recherche de lignes inattendue : '+str(result)[:3000])
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=[]
for stream in result['data']['result']:
    for value in stream.get('values',[]):
        ns,text=value[0],value[1]
        seconds,nanos=divmod(int(ns),1_000_000_000)
        stamp=datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z'
        lines.append((int(ns),stamp,stream['stream'],text))
for _,stamp,labels,text in sorted(lines,key=lambda item:item[0],reverse=a.direction=='backward'):
    print(stamp,json.dumps(labels,ensure_ascii=False),text)
print(json.dumps({'streams_received':len(result['data']['result']),
                  'lines_received':len(lines),'request_limit':a.limit,
                  'complete_count_guaranteed':False,'raw_response':a.output},indent=2))
```

## Références Grafana
 Loki components, Loki architecture, Query Loki, Log queries, HTTP API et LogCLI. 

