# Atelier 12 — LogQL métrique : volumes, débits, ratios, unwrap et quantiles

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 4, atelier 12 |
| Durée indicative | 2 h à 2 h 30 |
| Infrastructure | Ubuntu natif, Alloy, Loki et Grafana déjà installés |
| Prérequis | Sources A09 et copies JSON/logfmt A11 conservées ; API et parsers A10/A11 compris |
| Corpus principal | access_log et movies.csv ; sondes ajoutées aux mêmes fichiers |
| Corpus de durée | Contrôles explicitement synthétiques dans les copies structurées A11 |
| Livrables | Requêtes métriques, référence temporelle, réponses API et dashboard expliqué |

## 1. Introduction : des lignes aux indicateurs

Les ateliers 09 à 11 ont appris à collecter, retrouver et parser les lignes. Nous allons transformer des sélections validées en séries numériques.

```text
Lignes sélectionnées → count_over_time / rate → volume et débit
Champs extraits → unwrap → somme, moyenne, maximum et quantile
Indicateurs compatibles → ratio → interprétation métier
```

### Objectifs conservés et adaptés

- Compter les lignes et calculer un débit par seconde.
- Comprendre [5m], l’instant d’évaluation et le step.
- Agréger par dataset/service, puis par groupe de contrôle extrait.
- Calculer une part de réponses 5xx avec un dénominateur explicite.
- Distinguer absence de série, zéro observé et absence de télémétrie.
- Utiliser unwrap et filtrer les erreurs à la bonne étape.
- Comparer somme, moyenne, maximum et p95.
- Vérifier les résultats avec l’API Instant avant le dashboard.
- Nommer les unités et éviter les conclusions métier non justifiées.

Aucun nouveau Loki ni nouveau writer Alloy n’est requis. L’ancien générateur JSON des trois services ne fait plus partie des prérequis.

## 2. Les données : réelles, sondes et contrôles synthétiques

| Source | Que mesure-t-on ? | Ce que l’on ne prétend pas mesurer |
|---|---|---|
| Archive access_log | Requêtes journalisées et octets de réponse connus | Disponibilité actuelle du serveur |
| movies.csv collecté | Lignes de données lues par le collecteur | Exécutions d’import réussies |
| Sondes Apache/CSV A12 | Chaîne de collecte et résultats contrôlés | Trafic utilisateur réel |
| Durées de contrôle A12 | Syntaxe unwrap/quantiles et qualité numérique | Latence HTTP réelle |

L’access log utilisé ne possède pas de durée de requête. Les octets et le retard de collecte ne sont pas des substituts de latence. Les durées ci-dessous sont des données d’exercice dont la provenance reste visible.

Les deux représentations JSON et logfmt A11 décrivent les mêmes contrôles. Choisir un seul format pour les métriques de durée, ici JSON ; ne pas additionner les deux copies.

## 3. Reprendre exactement les sources existantes

### Vérifications

```bash
sudo systemctl status alloy loki-formation grafana-server --no-pager
curl -fsS http://127.0.0.1:3100/ready
sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
sudo -u alloy test -r /var/log/formation-alloy11/events.jsonl
sudo -u alloy test -r /var/log/formation-alloy11/events.logfmt
```

### Labels déjà configurés

- job=atelier09 et dataset=access/movies pour les deux sources brutes.
- job=atelier11 et format=json/logfmt pour les copies normalisées.
- service=normalisation-lab est un label de la chaîne A11, pas le nom des groupes de durée.

Nous ne créons pas un label job=atelier12 pour cet exercice : le numéro de l’atelier ne modifie pas automatiquement l’ingestion. Le marqueur A12 dans le contenu isole le lot.

Si les fichiers A11 manquent, reprendre cette étape avant le TP. Ne pas créer des fichiers vides et annoncer que les durées devraient déjà être disponibles.

## 4. Préparer un lot contrôlé sans remplacer de fichiers

### Commandes

```bash
mkdir -p ~/formation-observabilite/atelier12
cd ~/formation-observabilite/atelier12
sudo python3 generer_scenario12.py --report scenario12.json
```

Le script joint vérifie les quatre fichiers, puis ajoute les lignes. Il refuse un rapport existant ; pour rejouer volontairement, choisir un autre --report. Ne pas effacer les positions Alloy.

### Sondes sur les deux sources A09

| Corpus | Statuts / contenu | Quantité |
|---|---|---:|
| access | 200, 404, 503, 200 ; tailles 100, 200, 300, 400 octets | 4 |
| movies | Deux films de test, dont un titre cité avec virgule | 2 |

Les six lignes contiennent le même marker. Les sondes sont explicitement synthétiques ; elles ne réécrivent pas l’archive.

### Contrôles de durée dans les deux fichiers A11

Neuf valeurs valides, chacune représentée en JSON et logfmt :

```text
access-demo : 100, 200, 300, 1200, 5000 ms
movies-demo : 400, 500, 600, 800 ms
```

Trois contrôles supplémentaires : unknown, champ absent et -5 ms. Au total : 12 lignes JSON et 12 lignes logfmt. source_dataset=controls_metrics et synthetic=true distinguent ces contrôles des autres données normalisées.

30 lignes sont donc écrites au total, mais cela ne représente ni 30 requêtes HTTP ni 30 durées valides.

## 5. Confirmer la collecte et figer l’instant T

### Objectif

Vérifier les nombres à un instant reproductible plutôt que courir après Last 5 minutes pendant tout le TP.

À exécuter juste après le générateur :

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 figer_reference12.py --scenario scenario12.json --output reference12.json
python3 construire_requetes12.py --scenario scenario12.json --output-dir requetes12
```

### Ce qui est contrôlé

Le premier script interroge les lignes portant le marker, attend de voir 4 access, 2 movies, 12 JSON et 12 logfmt, puis enregistre T en nanosecondes et UTC. Il refuse un surplus ou une collecte incomplète au-delà du délai.

La fenêtre de validation est fixée à cinq minutes et le lot doit encore y tenir. Le script refuse un lot trop ancien : générer volontairement un nouveau lot, ou préparer avec le formateur une autre fenêtre et recalculer tous les débits ; ne pas modifier seulement une requête isolée.

reference12.json peut être réutilisé plus tard : une requête à T reste une interrogation historique à T, même si le TP prend du temps. Ne pas remplacer T par l’heure courante si l’on veut conserver les chiffres de référence.

Ce T n’est pas un PIT Elasticsearch : il fixe le temps d’évaluation, pas un verrou ni une vue de stockage figée contre toute arrivée tardive. Le marker unique et le contrôle préalable bornent notre scénario.

Les fichiers LogQL générés contiennent le marker réel. Les blocs ci-dessous utilisent __MARKER__ comme notation pédagogique, à remplacer si vous les saisissez directement.

## 6. Comprendre Instant, Range, fenêtre et step

| Élément | Rôle |
|---|---|
| Instant à T | Une évaluation à cet instant |
| [5m] | Données recherchées dans les cinq minutes précédant chaque évaluation |
| Range | Évaluations répétées entre un début et une fin |
| step=30s | Espacement entre deux évaluations, pas largeur de la fenêtre |
| Période Grafana | Intervalle affiché, distinct de [5m] |

```text
À T       : calcul sur les 5 minutes précédentes
À T+30 s  : calcul sur les 5 minutes précédant T+30 s
À T+60 s  : nouvelle fenêtre, encore largement recouvrante
```

Une ligne peut donc contribuer à plusieurs points. Additionner tous les points d’une courbe de comptages glissants ne donne pas le nombre de lignes uniques de la période.

Avec un step plus grand que la fenêtre, une activité courte peut se situer entre deux évaluations. À l’inverse, un step minuscule multiplie les évaluations sans créer de nouvelles observations.

## 7. Compter avec count_over_time

### Requête

```logql
sum by (dataset) (
  count_over_time(
    {job="atelier09",dataset=~"access|movies"} |= "__MARKER__"
    [5m]
  )
)
```

### Résultat attendu à T

access=4 et movies=2. Pour regrouper par producteur logique, remplacer dataset par service dans sum by : web-formation=4 et movielens-import=2.

### Explication

count_over_time compte les entrées par série sur une fenêtre. sum by(dataset) fusionne les séries du même corpus en supprimant les dimensions inutiles comme filename ou status_class pour ce total.

Ne pas utiliser une agrégation count(...) externe pour compter les lignes : elle compte des éléments/séries du vecteur, pas leur volume. Pour additionner les comptes de lignes, employer sum.

Le nom du panneau doit dire « lignes collectées sur 5 min », pas « imports réussis » ni « visiteurs ».

## 8. Calculer un débit avec rate

```logql
sum by (dataset) (
  rate(
    {job="atelier09",dataset=~"access|movies"} |= "__MARKER__"
    [5m]
  )
)
```

### Valeurs à T

| Corpus | Nombre | Débit moyen sur 300 secondes |
|---|---:|---:|
| access | 4 | 4/300, environ 0,01333 ligne/s |
| movies | 2 | 2/300, environ 0,00667 ligne/s |

### Explication

rate sur un log-range mesure des entrées par seconde. Ce n’est pas une durée et ce n’est pas la vitesse d’exécution CPU de Python. Pour exprimer la cadence moyenne en lignes/minute, multiplier par 60 et changer l’unité affichée.

Passer de [5m] à [1m] change la fenêtre et potentiellement le nombre de lignes retenues. Si tout le lot est inclus, le dénominateur temporel change aussi ; ne pas interpréter cette hausse mécanique comme une hausse réelle de trafic.

## 9. Compter les classes HTTP et les 5xx

### Distribution des réponses

```logql
sum by (status_class) (
  count_over_time(
    {job="atelier09",dataset="access"} |= "__MARKER__"
    [5m]
  )
)
```

Attendu : 2xx=2, 4xx=1, 5xx=1. La source A09 a créé status_class : Loki ne reconnaît pas le format Apache automatiquement.

### Débit de 5xx

```logql
sum by (service) (
  rate(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
```

Attendu : web-formation=1/300, soit environ 0,00333 réponse 5xx/s.

Une requête textuelle |= "503" pourrait aussi correspondre à une URL ou un identifiant. Pour les familles HTTP, utiliser le label validé à l’ingestion ou parser le statut comme à l’atelier 11.

## 10. Construire un ratio avec des vecteurs compatibles

### Définition choisie

Part des réponses 5xx parmi les lignes access dont la classe de statut valide a été reconnue, dans la même fenêtre et le même périmètre.

```logql
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
/
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
)
```

### Résultat attendu

1/4=0,25, soit 25 %. Dans Grafana : Percent (0.0–1.0), sans multiplication supplémentaire par 100.

### Explication

Les deux côtés sont agrégés par service. Ils produisent les mêmes dimensions de regroupement pour être mis en correspondance. Garder status_class d’un seul côté pourrait empêcher le matching souhaité.

Le dénominateur exclut les lignes sans classe reconnue, comme le choix « statuts valides » du dashboard Kibana. Cela ne prouve pas que les lignes non classées n’existent pas : leur couverture doit être suivie séparément.

Ne pas inclure movies dans le dénominateur HTTP. Un ratio 5xx sur toutes les lignes de tous les formats n’aurait pas le même sens.

La part 4xx+5xx du lot vaut 2/4=50 %, mais un 404 n’est pas automatiquement un échec de disponibilité au même titre qu’un 503. Un vrai SLI exige routes éligibles, exclusions et définition métier.

## 11. Absence de série, zéro et absence de données

Un service avec des requêtes mais aucune erreur peut n’avoir aucune série au numérateur. Une division simple peut alors ne rien afficher pour lui plutôt que 0 %.

### Compléter seulement les services présents au dénominateur

```logql
(
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
  or on (service)
  (0 * sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
))
)
/
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
)
```

### Explication

0 * total fournit un zéro portant les labels des services réellement présents avec un statut reconnu. or on(service) ne remplace pas un numérateur existant ; il ajoute le zéro si cette série d’erreurs est absente.

Si le service n’a plus aucune donnée éligible, il reste absent du dénominateur. On n’invente pas « 0 % d’erreurs donc tout va bien ».

Un or vector(0) global ne reconstruit pas automatiquement les séries manquantes de chaque service. La gestion des absences doit être adaptée aux labels et à l’inventaire attendu.

## 12. Bytes des logs Loki ou bytes des réponses HTTP ?

```logql
sum(bytes_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  [5m]
))
```

bytes_over_time mesure le volume de texte des entrées de logs, pas la valeur du champ bytes d’Apache. De même, bytes_rate exprime le débit du contenu des logs, pas le débit réseau des réponses HTTP.

Pour additionner les tailles de réponses, il faut extraire ce champ et agréger ses valeurs avec unwrap. Le mot bytes dans le nom de la fonction ne sélectionne pas une colonne par son nom.

## 13. Unwrap sur les tailles réelles du format Apache

### Objectif

Passer d’un comptage de lignes à une somme de valeurs.

```logql
sum(
  sum_over_time(
    {job="atelier09",dataset="access"} |= "__MARKER__"
    | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
    | response_size!=""
    | response_size!="-"
    | unwrap response_size
    | __error__=""
    [5m]
  )
)
```

Attendu sur les quatre sondes : 100+200+300+400=1000 octets.

### Moyenne et maximum

```logql
avg_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
  | response_size!=""
  | response_size!="-"
  | unwrap response_size
  | __error__=""
  [5m]
) by (service)
```

```logql
max_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
  | response_size!=""
  | response_size!="-"
  | unwrap response_size
  | __error__=""
  [5m]
) by (service)
```

Attendus : moyenne 250 octets et maximum 400 octets.

### Lecture du pipeline

1. Le pattern extrait response_size.
2. Les champs vides et le tiret « taille inconnue » sont exclus.
3. unwrap convertit la valeur extraite en échantillon numérique.
4. Le filtre __error__ situé après unwrap écarte les conversions impossibles.
5. La fonction agrège les échantillons dans [5m].

La somme utilise une agrégation externe : sum_over_time sur valeurs extraites ne prend pas ici le même regroupement direct que avg_over_time. Ne pas recopier by(service) après n’importe quelle fonction sans vérifier son support.

Sur l’archive, une taille inconnue exclue n’est pas un faux zéro ; publier la couverture des tailles si l’indicateur est utilisé en analyse réelle.

## 14. Contrôles de durée : préparer une population exploitable

Les copies A11 contiennent 12 contrôles A12 par format, dont 9 durées valides. On choisit exclusivement format=json et source_dataset=controls_metrics.

### Politique de qualité

- Champ manquant : exclu de la population de durée.
- unknown : non convertible, exclu mais investigable.
- -5 : convertible mais rejeté par la règle métier durée >=0.
- Autres valeurs : neuf échantillons exploitables, en millisecondes.

Les filtres sont donnés dans les requêtes générées. Ils ne doivent pas être retirés simplement pour éviter No data.

### Contrôler le volume avant de calculer un quantile

```logql
sum(count_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  [5m]
))
```

Attendu : 12.

```logql
sum(count_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  [5m]
))
```

Attendu : 9. Trois contrôles sont exclus, soit une couverture exploitable de 75 %. Ce ratio décrit les contrôles du TP, pas la qualité de tout le trafic.

## 15. Moyenne des durées et regroupement sur un champ extrait

```logql
avg_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

### Attendus

| Groupe synthétique | Échantillons | Moyenne ms |
|---|---:|---:|
| access-demo | 5 | 1360 |
| movies-demo | 4 | 575 |

metric_group est un alias extrait de control_group. Ce regroupement de résultats ne crée pas de nouveaux labels d’ingestion.

Le label service=normalisation-lab décrit la chaîne de collecte ; il ne suffit pas à séparer ces deux groupes. Nous regroupons volontairement sur le champ pertinent plutôt que prétendre disposer des trois anciens services applicatifs.

### Unités

unwrap sans conversion explicite tente une valeur numérique. L’unité reste la milliseconde par définition de la source synthétique. Choisir milliseconds dans Grafana ; ne pas diviser par 1000 puis conserver l’unité ms.

## 16. Maximum et p95 : ce qu’ils disent, ce qu’ils ne disent pas

### Maximum

```logql
max_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

Attendu : access-demo=5000 ms, movies-demo=800 ms.

### Quantile 0,95

```logql
quantile_over_time(
  0.95,
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

Le p95 n’est pas la moyenne ni systématiquement le maximum. Il dépend des échantillons retenus et de la convention de calcul/interpolation. Avec seulement cinq et quatre valeurs, c’est un exercice de syntaxe et de lecture, pas une preuve statistique d’un engagement de performance.

Ne pas imposer un score entier d’une capture : vérifier d’abord l’instant T, les neuf valeurs, le filtre de qualité et le regroupement.

### Quantile global

La requête 13_controles_durees_p95_global.logql regroupe les neuf valeurs sur le job unique retenu, en retirant la séparation metric_group. Ce n’est pas la moyenne des deux p95.

Même pour la moyenne, une moyenne simple de 1360 et 575 ne donne pas la moyenne globale : les groupes ont des tailles différentes. La moyenne globale pondérée des neuf valeurs vaut 9100/9, environ 1011,11 ms.

Ne pas calculer le p95 de toute une période en moyennant les p95 de plusieurs fenêtres glissantes. Recalculer sur la population et la période voulues.

## 17. Compter les valeurs lentes sans utiliser unwrap inutilement

```logql
sum by (metric_group) (
  count_over_time(
    {job="atelier11",format="json"} |= "__MARKER__"
    | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
    | __error__=""
    | kind="controls_metrics"
    | duration_value!=""
    | duration_value >= 0
    | __error__=""
    | duration_value >= 1000
    | __error__=""
    [5m]
  )
)
```

Deux échantillons access-demo sont >=1000 ms : 1200 et 5000. Aucun échantillon movies-demo ne satisfait le seuil ; sa série de sélection peut être absente plutôt que 0.

Une comparaison numérique suffit pour compter des lignes satisfaisant une condition. unwrap sert quand l’on agrège les valeurs elles-mêmes.

Le seuil de 1000 ms est un choix pédagogique sur des contrôles synthétiques. Un seuil réel doit être défini selon le service et le besoin métier, pas copié de cet atelier.

## 18. Montrer une erreur d’unwrap sans la confondre avec No data

### Requête volontairement sans filtre final

```logql
avg_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | unwrap duration_value
  [5m]
) by (metric_group)
```

Si D_BAD est dans la fenêtre, unknown produit une erreur de conversion pouvant faire échouer la requête métrique. Le champ absent et la valeur négative sont des problèmes différents.

### Diagnostic dans une requête de lignes

Le fichier 18_diagnostic_unwrap_logs.logql extrait et teste la valeur pour retrouver le contrôle non convertible. Utiliser une recherche de lignes pour voir l’erreur et son contexte ; ne pas supprimer toutes les traces du problème pour obtenir un graphique.

### Correction raisonnée

La requête de moyenne validée vérifie présence et règle >=0, contrôle les erreurs de comparaison, puis effectue unwrap et contrôle à nouveau __error__ après cette conversion.

Filtrer seulement avant unwrap n’élimine pas une erreur créée par unwrap. Mais filtrer les erreurs de conversion ne rejette pas automatiquement une valeur métier négative ; il faut aussi la règle explicite.

Un filtre de qualité change la population calculée. Toujours conserver le compte des valeurs retenues et une vue des rejets.

## 19. API Loki : une métrique ne renvoie plus des lignes de logs

### Une évaluation Instant à T

```bash
export END_REF=$(python3 -c 'import json; print(json.load(open("reference12.json"))["time_ns"])')

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode "query=$(cat requetes12/01_count_par_dataset.logql)" \
  --data-urlencode "time=$END_REF" \
  -o count12-response.json
```

### Réponse attendue : vector

```json
{
  "status":"success",
  "data":{
    "resultType":"vector",
    "result":[{"metric":{"dataset":"access"},"value":[1790000000,"4"]}]
  }
}
```

Ce fragment est illustratif ; le résultat complet contient aussi movies=2.

- metric porte les labels de la série de résultat.
- value contient timestamp d’évaluation et valeur numérique, généralement encodée comme chaîne.
- Le timestamp des valeurs métriques est exprimé en secondes Unix, pas dans les chaînes nanosecondes des lignes de logs.
- Le nombre d’éléments result est un nombre de séries, pas de logs.

### Client Python fourni

```bash
python3 interroger_metriques12.py \
  --query-file requetes12/01_count_par_dataset.logql \
  --reference reference12.json --mode instant --output count12-python.json
```

Le client de lignes A10 attend streams ; celui-ci attend vector ou matrix selon le mode. Ne pas utiliser le parseur de réponse des logs comme s’il s’agissait de la même structure.

## 20. API Range et courbes Grafana

```bash
python3 interroger_metriques12.py \
  --query-file requetes12/02_rate_par_dataset.logql \
  --reference reference12.json --mode range --step 30s \
  --history-minutes 10 --output rate12-range.json
```

query_range produit ici une matrix : chaque série possède values, liste de couples temps/valeur.

step règle les instants d’évaluation des métriques. Ce n’est pas interval, utilisé pour espacer les entrées de recherches de logs. Ne pas ajouter limit en croyant fixer le nombre de points d’une matrice comme le nombre de lignes d’un résultat streams.

### Dans Grafana Explore

- Datasource Loki-Formation, mode Code.
- Reprendre les fichiers de requêtes.
- Pour le contrôle à T, fixer la fin de période à time_utc de reference12.json et utiliser Instant.
- Pour une courbe, utiliser Range, période absolue autour de T, et un step cohérent.

Si l’interface arrondit une borne, vérifier que la fenêtre continue à couvrir tout le lot. L’API à time_ns constitue la référence exacte.

Une Stat utilisant Last d’une courbe peut montrer No data une fois le lot sorti de la fenêtre. Revenir à T pour le contrôle plutôt que modifier le calcul afin de retrouver un chiffre.

## 21. Dashboard Grafana orienté Data Observability

### Objectif

Présenter ce qui est observé, avec unité, fenêtre et provenance visibles.

Créer [A12] Métriques des logs — Access et MovieLens, puis ajouter :

| Panneau | Source / requête | Visualisation / unité |
|---|---|---|
| Lignes collectées par corpus — 5 min | 01 | Stat ou table, nombre |
| Débit par corpus — fenêtre 5 min | 02 | Time series, lignes/s |
| Réponses par classe HTTP | 03 | Barres ou table, nombre |
| Part 5xx — statuts reconnus | 06 | Stat, Percent 0–1 |
| Octets HTTP connus — 5 min | 07 | Stat, bytes |
| Contrôles de durée — moyenne | 10 | Table ou Time series, ms |
| Contrôles de durée — p95 | 12 | Time series, ms |
| Valeurs exploitables / total | 16 et 15 | Deux Stats ou table, 9 / 12 |

### Procédure commune

1. Ajouter une visualisation, datasource Loki-Formation.
2. Mode Code, copier le fichier LogQL généré.
3. Choisir Instant pour un contrôle à T, Range pour une courbe.
4. Nommer fenêtre et unité ; légende {{dataset}}, {{service}} ou {{metric_group}} selon la requête.
5. Séparer visuellement les panneaux HTTP/CSV des durées synthétiques.
6. Ajouter un texte : « Les durées sont des contrôles, pas une mesure de latence du serveur. »
7. Sauvegarder et rouvrir le dashboard.

Un dashboard figé autour de T n’est pas une supervision vivante. Pour de vraies séries continues, un producteur et une instrumentation continue sont nécessaires ; l’auto-refresh seul n’ajoute aucune observation.

## 22. Observer l’absence sans la transformer en état sain

Le fichier 19_absence_sonde.logql utilise absent_over_time sur une fenêtre d’une minute pour la sonde access sélectionnée.

- Si des lignes correspondantes existent dans la fenêtre, la fonction ne renvoie pas cette alerte d’absence.
- Si la sélection est absente, elle peut produire un indicateur d’absence valant 1.

Après arrêt du générateur ponctuel et sortie du lot de la fenêtre, c’est normal pour le TP. Ce n’est pas la preuve d’une panne du serveur web.

Un vrai contrôle distingue trafic attendu, santé de la source, état d’Alloy, refus d’ingestion et disponibilité de Loki. Il nécessite des attentes explicites, pas seulement une requête d’erreurs vide.

La politique d’alerte et le comportement No data doivent être décidés séparément ; une série sans erreurs n’est pas la même chose qu’aucune télémétrie.

## 23. Défi final

### Énoncé

Avec le même lot et le même T :

1. Retrouver les comptes access=4 et movies=2.
2. Calculer les débits par seconde et expliquer le diviseur temporel.
3. Mesurer 25 % de 5xx sur les quatre statuts reconnus.
4. Vérifier somme/moyenne/max des tailles HTTP.
5. Prouver que neuf des douze contrôles de durée sont exploitables.
6. Présenter moyenne, maximum et p95 par groupe, sans moyenner les quantiles.
7. Retrouver D_BAD dans une requête de lignes.
8. Comparer Instant API et panneau Grafana à la même référence.
9. Expliquer un cas d’absence de série et une limite métier de chaque indicateur.

## 24. Corrigé et contrôles attendus

| Indicateur à T | Résultat |
|---|---|
| Lignes access / movies | 4 / 2 |
| Débits access / movies | 4/300 et 2/300 ligne/s |
| Réponses 2xx / 4xx / 5xx | 2 / 1 / 1 |
| Part 5xx parmi statuts reconnus | 25 % |
| Somme / moyenne / maximum bytes HTTP | 1000 / 250 / 400 octets |
| Contrôles totaux / exploitables | 12 / 9 |
| Moyenne access-demo / movies-demo | 1360 / 575 ms |
| Maximum access-demo / movies-demo | 5000 / 800 ms |
| Durées >=1000 ms | 2 dans access-demo ; aucune dans movies-demo |

Le p95 est évalué à partir des valeurs et du regroupement réellement retenus. Il n’est pas présenté comme une preuve de SLO sur quatre ou cinq observations.

### Réponse conceptuelle attendue

Count et rate agrègent des entrées de logs ; unwrap transforme une valeur extraite en échantillon. Un ratio exige population, fenêtre et labels compatibles. Les filtres qualité influencent la population. Un débit d’entrées CSV n’est pas un taux de réussite métier et une durée synthétique n’est pas une mesure HTTP observée.

## 25. Dépannage

| Symptôme | Vérification |
|---|---|
| Valeurs changent à chaque refresh | Heure de fin mobile et fenêtres glissantes ; revenir à T |
| Count trop élevé | Marker absent, source JSON/logfmt doublée, sondes répétées ou relectures |
| Taux très petit | rate est en lignes/seconde et la fenêtre vaut 300 s |
| Ratio vide | Numérateur absent ou labels incompatibles |
| Metric query contains errors | Étape de parser/conversion/unwrap ; filtrer après l’étape responsable et diagnostiquer les lignes |
| Moyenne trop basse | Valeur négative conservée ou population incorrecte |
| Bytes Loki différents de 1000 | bytes_over_time mesure le contenu des logs, pas la colonne Apache |
| Trop de séries | Extraction trop large, IDs conservés ou regroupement absent |
| No data après quelques minutes | Lot ponctuel sorti de la fenêtre, pas nécessairement perte de stockage |
| Interroger un log avec /query échoue | Utiliser query_range pour une recherche de lignes |

## 26. Checklist et livrables

- Sources A09/A11 conservées, aucune nouvelle configuration de collecte nécessaire.
- Marker et reference12.json documentés.
- Count et rate compris, avec unités.
- Ratio et cas de zéro présent/absence expliqués.
- Octets des logs distingués des octets HTTP.
- Unwrap et contrôle post-conversion compris.
- Trois contrôles invalides exclus explicitement, pas cachés.
- Maximum et p95 distingués ; pas de moyenne de quantiles.
- Réponse vector/matrix distinguée de streams.
- Dashboard enregistré avec provenance visible.

Livrer les requêtes, les JSON de contrôle, le dashboard et une note sur les limites. Ne pas publier de secrets ou de données personnelles issues des vrais logs.

## 27. Conservation et passage au fil rouge

Conserver services, fichiers et positions Alloy. Un nouveau lot s’ajoute ; il ne remplace pas les anciennes entrées. Le projet final pourra réunir Elasticsearch et Loki avec des identifiants communs et des définitions d’indicateurs explicites.

Les sondes de ce TP sont corrélées par un marqueur pédagogique ; elles ne constituent pas un tracing distribué ni une preuve qu’une vraie requête a déclenché un import MovieLens.

## Annexes — Scripts fournis

### generer_scenario12.py

```python
import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Lot A12 dans les quatre fichiers deja suivis en A09/A11')
p.add_argument('--raw-dir',default='/var/log/formation-alloy09')
p.add_argument('--structured-dir',default='/var/log/formation-alloy11')
p.add_argument('--report',default='scenario12.json')
a=p.parse_args()
report=Path(a.report)
if report.exists():
    p.error('Rapport existant : choisir un nouveau --report')
raw,structured=Path(a.raw_dir),Path(a.structured_dir)
paths=[raw/'access_log',raw/'movies.csv',structured/'events.jsonl',structured/'events.logfmt']
for path in paths:
    if not path.is_file():
        p.error('Source A09/A11 absente : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        if f.tell():
            f.seek(-1,2)
            if f.read(1)!=b'\n':
                p.error('Saut de ligne final absent : '+str(path))
start_ns=time.time_ns()-5_000_000_000
now=datetime.now(timezone.utc)
marker=now.strftime('A12-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
with paths[0].open('a',encoding='utf-8') as f:
    for i,(status,size,msg) in enumerate([(200,100,'completed'),(404,200,'missing'),(503,300,'timeout'),(200,400,'recovered')],1):
        f.write(f'127.0.0.1 - - [{stamp}] "GET /atelier12/{marker}/probe-{i} HTTP/1.1" {status} {size} "-" "A12 {msg}"\n')
with paths[1].open('a',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n')
    writer.writerow([9001201,f'Film {marker}, edition "test" (2026)','Documentary'])
    writer.writerow([9001202,f'Voyage {marker} (2026)','Adventure'])
controls=[]
for group,values in [('access-demo',[100,200,300,1200,5000]),('movies-demo',[400,500,600,800])]:
    for i,value in enumerate(values,1):
        controls.append({'control_group':group,'test_case':f'{group}-{i}',
                         'control_kind':'valid','duration_ms':value})
controls.extend([
    {'control_group':'access-demo','test_case':'D_BAD','control_kind':'invalid','duration_ms':'unknown'},
    {'control_group':'access-demo','test_case':'D_MISSING','control_kind':'invalid'},
    {'control_group':'movies-demo','test_case':'D_NEGATIVE','control_kind':'invalid','duration_ms':-5}
])
with paths[2].open('a',encoding='utf-8') as jf,paths[3].open('a',encoding='utf-8') as lf:
    for number,fields in enumerate(controls,1):
        event={'normalization_id':marker,'record_id':f'{marker}-D{number:03d}',
               'source_dataset':'controls_metrics','synthetic':True,**fields}
        jf.write(json.dumps(event,ensure_ascii=False)+'\n')
        lf.write(' '.join(k+'='+json.dumps(v,ensure_ascii=False) for k,v in event.items())+'\n')
result={'marker':marker,'start_ns':str(start_ns),'written_at_utc':now.isoformat(),
        'expected':{'access':4,'movies':2,'json':12,'logfmt':12},
        'valid_duration_samples':9,'invalid_duration_controls':3,
        'response_bytes':{'sum':1000,'mean':250,'max':400},
        'note':'30 entrees synthetiques ecrites ; collecte a verifier ; aucune latence HTTP reelle'}
with report.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
```

### figer_reference12.py

```python
import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Confirmer les 30 sondes et figer T pour les metriques A12')
p.add_argument('--scenario',default='scenario12.json')
p.add_argument('--output',default='reference12.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
p.add_argument('--timeout',type=int,default=60)
a=p.parse_args()
if a.timeout<1 or a.timeout>180:p.error('--timeout entre 1 et 180 secondes')
if Path(a.output).exists():p.error('Reference deja presente : choisir un nouveau --output')
scenario=json.loads(Path(a.scenario).read_text(encoding='utf-8'))
start=int(scenario['start_ns']);marker=scenario['marker'];deadline=time.monotonic()+a.timeout
expected=scenario['expected']
while True:
    now=time.time_ns()
    if now-start>240*1_000_000_000:
        raise SystemExit('Lot deja trop ancien pour ce controle 5m : produire volontairement un nouveau lot')
    query='{job=~"atelier09|atelier11"} |= '+json.dumps(marker)
    params=urllib.parse.urlencode({'query':query,'start':str(start),'end':str(now),'limit':'200','direction':'forward'})
    with urllib.request.urlopen(a.url.rstrip('/')+'/loki/api/v1/query_range?'+params,timeout=20) as response:
        result=json.load(response)
    if result.get('status')!='success' or result.get('data',{}).get('resultType')!='streams':
        raise SystemExit('Reponse Loki inattendue : '+str(result)[:2000])
    counts={'access':0,'movies':0,'json':0,'logfmt':0}
    other=0;timestamps=[]
    for stream in result['data']['result']:
        labels=stream['stream'];values=stream.get('values',[])
        if labels.get('job')=='atelier09' and labels.get('dataset') in ['access','movies']:
            key=labels['dataset']
        elif labels.get('job')=='atelier11' and labels.get('format') in ['json','logfmt']:
            key=labels['format']
        else:
            other+=len(values);continue
        counts[key]+=len(values)
        timestamps.extend(int(value[0]) for value in values)
    if other or any(counts[key]>expected[key] for key in counts):
        raise SystemExit('Doublons ou perimetre inattendu : '+str(counts))
    if counts==expected:
        t=time.time_ns()
        seconds,nanos=divmod(t,1_000_000_000)
        result={'marker':marker,'time_ns':str(t),
                'time_utc':datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}Z',
                'window':'5m','window_seconds':300,'observed':counts,
                'first_loki_timestamp_ns':str(min(timestamps)),
                'last_loki_timestamp_ns':str(max(timestamps))}
        if min(timestamps)<=t-300*1_000_000_000:
            raise SystemExit('Le lot ne tient plus dans la fenetre 5m')
        Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2));break
    if time.monotonic()>=deadline:
        raise SystemExit('Collecte incomplete : '+str(counts))
    time.sleep(2)
```

### interroger_metriques12.py

```python
import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

p=argparse.ArgumentParser(description='Interroger une metrique Loki en Instant ou Range')
p.add_argument('--query-file',required=True)
p.add_argument('--reference',default='reference12.json')
p.add_argument('--mode',choices=['instant','range'],default='instant')
p.add_argument('--step',default='30s')
p.add_argument('--history-minutes',type=int,default=10)
p.add_argument('--output',default='metric-response.json')
p.add_argument('--url',default=os.environ.get('LOKI_URL','http://127.0.0.1:3100'))
a=p.parse_args()
if a.history_minutes<1:p.error('--history-minutes doit etre positif')
if Path(a.output).exists():p.error('Fichier de sortie deja present')
reference=json.loads(Path(a.reference).read_text(encoding='utf-8'))
t=int(reference['time_ns'])
query=Path(a.query_file).read_text(encoding='utf-8').strip()
params={'query':query}
if a.mode=='instant':
    endpoint='/loki/api/v1/query';params['time']=str(t);expected='vector'
else:
    endpoint='/loki/api/v1/query_range'
    params.update(start=str(t-a.history_minutes*60*1_000_000_000),end=str(t),step=a.step)
    expected='matrix'
with urllib.request.urlopen(a.url.rstrip('/')+endpoint+'?'+urllib.parse.urlencode(params),timeout=30) as response:
    result=json.load(response)
if result.get('status')!='success' or result.get('data',{}).get('resultType')!=expected:
    raise SystemExit('Reponse metrique inattendue : '+str(result)[:3000])
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for item in result['data']['result']:
    print(item['metric'],item.get('value',item.get('values')))
print(json.dumps({'mode':a.mode,'resultType':expected,'series_received':len(result['data']['result'])},indent=2))
```

Le script construire_requetes12.py et la bibliothèque complète de vingt requêtes sont joints ; les exemples __MARKER__ y sont personnalisés depuis scenario12.json.


## Références Grafana : 
Metric queries, LogQL reference, pipeline errors et Loki HTTP API. Les regroupements autorisés dépendent de la fonction ; la somme sur unwrap emploie ici une agrégation externe.


