# Atelier 13 — Grafana : construire un dashboard Data Observability et investiguer un incident

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — atelier 13, fil rouge de clôture |
| Durée indicative | 3 h à 3 h 30 ; extension Elasticsearch 30 à 45 min |
| Méthode | Même progression qu’à l’atelier 08 : explorer → visualiser → assembler → filtrer → investiguer → vérifier |
| Plateforme | Ubuntu natif, Grafana, Loki et Alloy existants |
| Sources conservées | access_log, movies.csv et instrumentation JSON de l’atelier 11 |
| Livrable principal | Dashboard Grafana interactif avec KPI, chronologie, barres, histogrammes, heatmaps, table et logs |
| Fil rouge | Anomalie MovieLens et erreurs HTTP simulées, puis reprise |

## 1. Introduction : transposer la méthode de l’atelier 08 à Grafana

Nous ne commençons pas par importer un dashboard sans le comprendre. Nous vérifions les données, écrivons les requêtes dans Explore, puis créons les panneaux un par un.

```text
Contrôler les sources et le temps
→ explorer les lignes dans Grafana Explore
→ valider les agrégations par l’API
→ créer KPI, chronologie et comparaisons
→ construire histogrammes et heatmaps
→ ajouter tables, logs et variables
→ investiguer normal / incident / recovery
→ corréler avec Elasticsearch si l’extension est activée
→ définir une alerte et livrer les objets
```

### Objectifs pédagogiques

- Séparer datasource, requête, transformation, visualisation et dashboard.
- Mettre en relation volume, fraîcheur, distribution, qualité et complétude.
- Construire de vrais histogrammes et heatmaps à partir d’observations individuelles.
- Distinguer données sources, sondes, instrumentation et compteurs déclarés.
- Préserver un dénominateur correct quand les variables changent.
- Passer d’un indicateur agrégé aux événements d’un batch.
- Contrôler une valeur avec l’API, pas seulement l’œil.
- Définir un indicateur et une règle d’alerte sans prétendre avoir un SLO de production.

Les scripts et exports fournis servent de corrigé et de solution de secours. La construction manuelle reste le cœur pédagogique.

## 2. Ce que signifie « Data Observability complète » dans ce laboratoire

| Dimension | Signal construit | Limite à expliquer |
|---|---|---|
| Volume | Lignes observées, attendues et validées | Une ligne de catalogue n’est pas un import réussi |
| Complétude | Validées/attendues ; manquantes avant lecture | Le contrat attendu est déclaré, pas deviné par Loki |
| Qualité | Rejet pour titre absent ou ID dupliqué | Exemple de règles, pas validation universelle du catalogue |
| Fraîcheur | Date source, retard à l’observation, heartbeat | Les dates métier sont simulées ; l’année du film n’est pas un timestamp d’ingestion |
| Distribution | Histogramme/heatmap des tailles HTTP et du retard | Les sondes sont contrôlées, pas des requêtes réelles d’utilisateurs |
| Traçabilité | run_id, batch_id, event_id, référence et empreinte source | Ce n’est pas une plateforme de lineage ou de tracing distribuée complète |
| Santé du transport | Vérification des lignes et IDs arrivés dans Loki | Nécessite des contrôles séparés pour chaque chemin de collecte |

L’objectif est un parcours complet de diagnostic sur le périmètre du TP. Il ne remplace pas l’instrumentation réelle du SI, ses contrats, inventaires, règles métier, sauvegardes et politiques de sécurité.

Aucune latence HTTP n’est inventée : le fichier access_log d’origine n’en contient pas. Le temps du générateur par batch est une autre mesure, nommée comme telle.

## 3. Architecture et continuité des ateliers 09 à 12

```text
Références des deux fichiers A09, lues sans remplacement
       │
       ├─► sondes Apache ajoutées à access_log ─► Alloy A09 ─┐
       ├─► sondes CSV ajoutées à movies.csv ────► Alloy A09 ─┤
       └─► événements de simulation JSON ──────► Alloy A11 ─┤
                                                          ▼
                                                        Loki
                                                          ▲
                                                          │ LogQL
                                                Grafana Explore / Dashboard

Copie locale des mêmes événements JSON ──► Elasticsearch (extension)
                                             ▲
                                             │ autre datasource Grafana
```

Le générateur écrit l’instrumentation dans /var/log/formation-alloy11/events.jsonl, déjà suivi par Alloy. Aucun nouveau port, writer ou parser d’ingestion n’est requis. Le fichier logfmt A11 reste conservé mais n’est pas alimenté en double par ce scénario.

### Séparer trois représentations

- Les deux archives/références déjà présentes : conservées.
- Les lignes brutes de sonde : ajoutées pour tester les deux collectes A09.
- Les événements structurés : décrivent les décisions de la simulation et son contrat.

On n’additionne pas une ligne brute et sa trace JSON comme deux lignes métier distinctes. Les KPI principaux utilisent uniquement les événements JSON de type record.

## 4. Scénario normal → incident → recovery

Chaque phase traite cinq références access et cinq références MovieLens attendues.

### Normal

- Cinq sondes HTTP 200.
- Cinq films valides.
- Retard source simulé de deux secondes.

### Incident

- Cinq sondes HTTP : 200, 200, 503, 503, 404.
- Les cinq observations HTTP restent valides en tant que logs, même si leur statut décrit une erreur.
- Pour movies : quatre lignes sont tentées sur cinq attendues.
- Deux films sont validés, un est rejeté pour titre métier vide, un pour ID dupliqué dans le batch.
- Une référence attendue n’est pas traitée : elle est manquante avant lecture.
- Les quatre événements movies portent une date source décalée de dix minutes.

### Recovery

- Cinq sondes HTTP 200 et cinq films valides.
- Retard source simulé de deux secondes.

### Point essentiel

Une reprise saine ne rattrape pas automatiquement la ligne manquante et les deux rejets de la phase précédente. Sur recovery seul, la complétude est 100 %. Sur tout le scénario, elle reste 90 % tant qu’aucun backfill n’est réellement réalisé.

Un 503 HTTP n’est pas un rejet de parsing ou de qualité du catalogue. Les dimensions « statut HTTP » et « enregistrement validé » restent distinctes.

## 5. Vérifier les prérequis et l’accès

### Commandes sur la VM

```bash
sudo systemctl status alloy loki-formation grafana-server --no-pager
curl -fsS http://127.0.0.1:3100/ready
curl -fsS http://127.0.0.1:3000/api/health | python3 -m json.tool
sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
sudo -u alloy test -r /var/log/formation-alloy11/events.jsonl
```

### Depuis le poste participant

```bash
ssh -N -L 3000:127.0.0.1:3000 utilisateur@IP_PUBLIQUE_VM
```

Ouvrir http://localhost:3000 avec une identité autorisée. Vérifier la datasource Loki-Formation, URL locale de Loki. Ne pas confondre cette URL racine avec /loki/api/v1/push.

Les fichiers A09 doivent contenir au moins cinq références ; les cinq premiers movieId doivent être distincts. Le script refuse de produire un scénario à partir d’entrées insuffisantes.

## 6. Préparer le corpus et vérifier son arrivée

Placer les scripts et requetes-templates-atelier13.json ensemble dans le dossier de travail :

```bash
mkdir -p ~/formation-observabilite/atelier13
cd ~/formation-observabilite/atelier13
set -o pipefail

sudo python3 generer_scenario13.py --output-dir scenario13 \
  --phase-wait 15 --pace 0.05 | tee preparation13.json

export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_scenario13.py --manifest preparation13.json --output reference13.json
```

Le scénario prend une trentaine de secondes pour rendre les phases visibles dans le temps. Ne pas relancer le générateur parce qu’un graphique n’est pas encore apparu : attendre le contrôle d’arrivée.

### Résultats attendus

| Représentation | Quantité |
|---|---:|
| Sondes access brutes | 15 |
| Sondes CSV brutes | 14 |
| Événements JSON record | 29 |
| Événements JSON batch | 6 |
| Heartbeats JSON | 3 |
| Total d’entrées Loki liées au run | 67 |

Le vérificateur contrôle les IDs JSON uniques, les comptes et la cohérence des records de chaque batch. Une ligne manquante dans le contrat métier n’est pas confondue avec un événement de simulation perdu pendant le transport.

### Fichiers produits

- preparation13.json : manifeste affiché, lisible par le participant.
- scenario13/produced_events.jsonl : copie exacte des 38 événements structurés, protégée car produite avec sudo.
- scenario13/manifest13.json : manifeste local protégé.
- reference13.json : période vérifiée et run_id à utiliser.

Ne pas continuer en cas d’erreur : un dossier de sortie partiel sans manifeste final n’est pas un scénario réussi. Les sources suivies ne sont jamais remplacées ; de nouvelles sondes y sont ajoutées.

## 7. Régler le temps et distinguer les horloges

### Procédure

Dans Grafana, choisir UTC et une période absolue correspondant à from_utc / to_utc de reference13.json. Elle inclut l’émission et la collecte.

| Horloge | Signification |
|---|---|
| Time de la ligne Loki | Collecte par la source Alloy, selon le parcours A09/A11 de base |
| @timestamp / producer_epoch du JSON | Émission de l’événement de simulation |
| event_time / source_event_epoch | Date métier simulée du jeu traité |
| source_delay_seconds | Retard source au moment de l’observation |

Le retard source max de 600 secondes reste 600 dans une période historique, même une heure plus tard. Ce n’est pas un calcul de l’âge actuel.

Une date affichée en From now vieillit avec l’heure du navigateur. Ce comportement est normal, mais diffère d’un retard mesuré à l’observation.

Ne pas utiliser la date de sortie du film comme date de collecte. Pour comparer Elasticsearch et Loki, la projection ES utilisera @timestamp, pas event_time décalé volontairement de dix minutes.

## 8. Explorer les données avant de visualiser

### Dans Explore, mode Code

Remplacer RUN_REEL par la valeur run_id de preparation13.json :

```logql
{job="atelier11",format="json"} |= "RUN_REEL"
```

Puis :

```logql
{job="atelier11",format="json"} |= "RUN_REEL"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value="movies"
| phase_value="incident"
```

### Résultat attendu

Quatre records, dont deux accepted=false. Développer une ligne et relever event_id, batch_id, quality_reason, event_time et source_delay_seconds.

### Vérifier la différence labels/champs

job et format sont des labels d’ingestion. phase, accepted, source_dataset et event_id viennent du JSON. Ils sont parsés à la requête ; ils ne se placent pas dans le sélecteur initial comme s’ils avaient été indexés par Alloy.

Les requêtes conservent la ligne JSON originale pour les transformations d’affichage. Ne pas insérer line_format avant l’extraction de champs du panneau histogramme.

## 9. Créer le dashboard vide et ses variables

### Procédure

1. Dashboards → New dashboard.
2. Nommer [A13] Data Observability — Access et MovieLens.
3. Régler la période absolue vérifiée et UTC.
4. Enregistrer.
5. Ouvrir les paramètres du dashboard → Variables.

### Variables à créer dans cet ordre

| Nom | Type | Réglages |
|---|---|---|
| loki_ds | Data source | Type Loki ; sélectionner Loki-Formation |
| run | Text box | Coller le run_id exact, sans guillemets |
| dataset | Custom | access,movies ; multi-value ; Include All ; Custom all value = .* |
| phase | Custom | normal,incident,recovery ; multi-value ; Include All ; Custom all value = .* |

Les panneaux utilisent la datasource ${loki_ds}. Les requêtes de la bibliothèque utilisent les autres variables : ${run}, ${dataset:regex}, ${phase:regex}.

Une variable ne filtre pas magiquement tous les panneaux. Chaque requête compatible doit la référencer, y compris les deux côtés des ratios. Les variables de ce TP ont des valeurs contrôlées ; ne pas les traiter comme des paramètres arbitraires non validés d’une API publique.

Le heartbeat est global aux deux datasets ; sa requête ignore volontairement dataset et cela doit être indiqué si l’on en ajoute un panneau.

## 10. Méthode commune pour chaque panneau

Pour chaque visualisation :

1. Dashboard en édition → Add visualization.
2. Choisir ${loki_ds} / Loki-Formation.
3. Mode Code, coller la requête indiquée dans requetes-logql-atelier13.md.
4. Choisir Instant ou Range comme précisé.
5. Sélectionner la visualisation.
6. Régler unité, légende et titre.
7. Inspecter les données avant de masquer des champs.
8. Appliquer, enregistrer et vérifier le résultat dans son contexte de variables.

Les libellés de menus varient selon la version. Les transformations n’altèrent pas Loki ; elles agissent sur les données déjà reçues par le panneau. Leur ordre est important.

Les numéros de requêtes ci-dessous correspondent à la bibliothèque fournie, pas à des endpoints d’API.

## 11. Première ligne : six KPI contrôlables

### Configuration

Tous ces panneaux sont des Stat en Instant à la fin de la période du dashboard, All pour dataset et phase.

| Panneau | Requête | Unité | Attendu |
|---|---|---|---:|
| P01 — Lignes métier observées | 01_observed_records | Nombre | 29 |
| P02 — Attendues, contrat | 02_expected | Nombre | 30 |
| P03 — Validées, simulation | 03_accepted | Nombre | 27 |
| P04 — Rejetées | 04_rejected | Nombre | 2 |
| P05 — Manquantes avant lecture | 05_missing | Nombre | 1 |
| P06 — Validées / attendues | 06_completeness | Percent 0–1 | 90 % |

La fenêtre [$__range] représente la durée sélectionnée, avec une seule évaluation à sa fin pour ces KPI. Ne pas utiliser Last d’une courbe de fenêtres chevauchantes pour reconstituer un total de période.

### Lire le contrat

```text
Attendues = tentées + manquantes = 29 + 1 = 30
Tentées = validées + rejetées = 27 + 2 = 29
```

Les compteurs de batch proviennent de la simulation. Ils ne sont pas un accusé de réception d’une base cible. La projection ES et le contrôle des IDs sont des vérifications supplémentaires distinctes.

### Mise en forme

Nombre de décimales 0 pour les comptes, 1 ou 2 pour le pourcentage. Garder No data visible ; ne pas transformer toutes les absences en zéro vert. Les seuils de couleur sont des conventions pédagogiques, pas un SLO déjà approuvé.

## 12. Chronologie et barres de répartition

### P07 — Lignes observées par corpus dans le temps

- Requête 07_timeline, Range.
- Time series ; légende {{dataset_value}}.
- Fenêtre de comptage 10 s et espacement d’évaluation cohérent, minimum 10 s pour cet exercice.
- Titre précisant « fenêtre 10 s ».

Une fenêtre glissante n’est pas un histogramme calendaire sans recouvrement. Ne pas sommer les points pour retrouver les 29 lignes.

### P08 — Réponses HTTP par code

- Requête 08_http_codes, Instant.
- Bar gauge horizontal ou barres selon le format de retour de votre version.
- Légende {{status_value}} ; unité nombre.
- Attendus : 200=12, 503=2, 404=1.

### P09 — Part de 5xx

- Requête 09_http_5xx_ratio, Instant.
- Stat, Percent 0–1.
- Attendu : 2/15, environ 13,33 % sur tout le run.

Le numérateur est complété à zéro seulement si un dénominateur HTTP reconnu existe. Avec dataset=movies, No data est normal pour ce panneau HTTP ; zéro aurait un autre sens.

Ne pas ajouter un filtre global « 5xx seulement » sans l’appliquer de manière pensée au dénominateur. La requête isole le numérateur, pas toute la population du ratio.

## 13. Histogramme P10 : distribution des tailles HTTP individuelles

### Objectif

Afficher une distribution de quinze tailles, pas une distribution de moyennes calculées par fenêtre.

### Requête et type

- Requête 10_access_observations.
- Mode Range, résultat de lignes ; limite au moins 100 pour le lot, 2000 dans l’export fourni.
- Visualisation Histogram.

### Transformations dans cet ordre

1. Extract fields : choisir le champ contenant la ligne JSON, généralement Line ; format JSON.
2. Remplacer les champs par les extractions ; conserver Time le temps de vérifier.
3. Convert field type : response_bytes → Numeric.
4. Filter fields by name / Organize fields : conserver uniquement response_bytes.
5. Vérifier dans l’aperçu qu’il y a quinze valeurs et aucun champ epoch, statut ou durée ajouté à l’histogramme.

### Réglages

- Bucket size : 1000 octets.
- Bucket offset : 0.
- Unité de valeur : bytes ; fréquence : nombre d’observations.
- Ne pas combiner des colonnes numériques sans rapport.

### Attendu sur All / All

Les tailles 128, 512, 1500, 4096 et 8192 se répètent trois fois. Les classes non vides sont :

| Intervalle de taille | Observations |
|---|---:|
| [0,1000) | 6 |
| [1000,2000) | 3 |
| [4000,5000) | 3 |
| [8000,9000) | 3 |

La somme des fréquences vaut 15. Si l’histogramme compte aussi des timestamps, revenir au filtrage des champs, pas au générateur.

### Pourquoi ne pas utiliser avg_over_time ?

Un histogramme de moyennes glissantes représente la distribution de ces moyennes, pas celle des réponses HTTP individuelles. Les deux peuvent être utiles, mais ils ne répondent pas à la même question.

## 14. Heatmap P11 : tailles HTTP dans le temps

### Objectif

Voir comment la distribution précédente se répartit selon le temps de collecte.

### Procédure

1. Dupliquer P10 et renommer P11 — Tailles HTTP / temps de collecte.
2. Conserver la même requête de lignes, pas une moyenne métrique.
3. Modifier les transformations pour conserver Time ET response_bytes uniquement.
4. Time doit être un champ temporel, response_bytes un champ numérique.
5. Choisir Heatmap.
6. Calculate from data = Yes : les valeurs ne sont pas déjà des buckets.
7. X Bucket : Size 5s.
8. Y Bucket : Linear, Size 1000.
9. Palette séquentielle, légende/tooltip montrant la fréquence.
10. Vérifier le sens des axes : X temps, Y taille ; couleur nombre d’observations.

### Résultat attendu

Plusieurs tranches temporelles correspondant aux trois phases, avec cinq observations HTTP par phase. Le nombre exact de cellules dépend de l’alignement des bornes de 5 s et du délai réel de collecte.

Changer le filtre phase conserve la même population que P10. Ce sont les mêmes quinze observations, réparties différemment ; ce n’est pas une série de p95.

### Distinction essentielle

Cette heatmap n’est ni une carte géographique ni une matrice de catégories arbitraires. Pour comparer access/movies par phase, une table colorée ou des barres sont souvent plus adaptées. Les IP locales de sonde ne doivent jamais être géolocalisées artificiellement.

## 15. Heatmap P12 : retard source simulé dans le temps

### Procédure

1. Dupliquer la heatmap des tailles.
2. Requête 19_delay_observations : les records des deux datasets.
3. Extraire le JSON ; convertir source_delay_seconds en Numeric.
4. Garder seulement Time et source_delay_seconds.
5. Calculate from data = Yes.
6. X Bucket 5s, Y Bucket Size 60 s, échelle linéaire.
7. Unité seconds ; titre contenant « retard source simulé à l’observation ».

### Attendu

25 observations portent un retard de 2 s et 4 observations movies/incident un retard de 600 s. La heatmap montre le groupe retardé en hauteur pendant la phase incident.

Ce retard a été calculé par le producteur de simulation entre date source et observation. Il n’est pas l’âge actuel du dernier événement ni la durée d’une requête HTTP.

### Contrôle d’échantillonnage

L’aperçu doit contenir 29 lignes sur All/All. Les limites de réponse de logs s’appliquent à ces panneaux : un gros corpus demanderait une stratégie d’agrégation/bucketing adaptée côté source, pas une limite arbitraire masquée.

## 16. Fraîcheur : deux panneaux qui ne disent pas la même chose

### P13 — Retard source maximal observé

- Requête 12_max_observed_delay, Instant.
- Stat, seconds.
- All phases : 600 s ; recovery seule : 2 s.

Le maximum historique reste élevé après la reprise, tant que l’incident est dans la période. Il ne doit pas être présenté comme « retard actuel du pipeline ».

### P14 — Dernière date source observée

- Requête 13_last_source_timestamp, Instant.
- Stat par dataset ; l’expression convertit l’epoch en millisecondes.
- Unité From now ou date/heure, légende {{dataset_value}}.

Sur movies/incident, la date source est environ dix minutes antérieure à l’émission. Sur toutes les phases, la dernière date vient normalement de recovery.

From now utilise l’heure d’affichage et vieillit même dans un dashboard historique. Pour un compte rendu figé, préférer une date UTC explicite et conserver la période.

### Contrôles complémentaires

Le heartbeat prouve une émission/collecte sur le chemin JSON, pas à lui seul la santé des deux fichiers bruts. Le vérificateur contrôle séparément les sondes A09.

Sans trafic attendu ou heartbeat continu, une absence d’événement n’est pas un diagnostic complet de panne. Le générateur s’arrête volontairement après recovery.

## 17. Complétude et qualité : passer du ratio à la cause

### P15 — Validées/attendues par dataset

- Requête 14_completeness_by_dataset, Instant.
- Bar gauge ou table, Percent 0–1.
- All phases : access=100 %, movies=80 %.
- movies/incident : 2/5=40 %.

Le dénominateur provient des batches attendus de la simulation. Un batch entièrement non émis ne serait pas retrouvé par cette seule somme ; le manifeste/inventaire externe et le contrôle de livraison sont nécessaires pour détecter ce cas.

### P17 — Rejets par règle

- Requête 16_rejected_by_reason, Instant.
- Barres horizontales ; légende {{reason}}.
- title_missing=1 et duplicate_movie_id=1.

Le taux de rejet parmi les tentatives vaut 2/29, environ 6,90 %. Ce n’est pas le même indicateur que 1 - complétude : ce dernier inclut aussi la ligne manquante avant lecture.

Les règles sont exécutées avant l’ajout du suffixe technique [probe:event_id] au titre de sonde CSV. Le titre métier vide reste vide dans l’instrumentation JSON ; le marqueur technique ne le rend pas valide.

## 18. Table P16 : la synthèse par batch

### Objectif

Séparer les lignes agrégées de batch de la liste des records détaillés.

### Procédure

1. Requête 15_batch_table, Range de lignes.
2. Visualisation Table.
3. Extract fields depuis Line, JSON ; conserver Time.
4. Conserver : Time, phase, source_dataset, batch_id, expected, attempted, accepted_count, rejected_count, missing_count, source_delay_seconds.
5. Convertir les compteurs en Numeric si nécessaire.
6. Trier par Time croissant.
7. Colorer les compteurs rejected_count et missing_count lorsqu’ils sont >0.

### Attendu

Six lignes de synthèse ; la ligne movies/incident indique 5 attendues, 4 tentées, 2 validées, 2 rejetées, 1 manquante et 600 s de retard.

Ne pas sommer des compteurs de batch après les avoir joints à chaque record : un join un-à-plusieurs pourrait répéter le même total cinq fois.

## 19. Histogramme P18 : temps du générateur par batch

### Procédure

- Requête 15_batch_table, Range de lignes.
- Extract fields JSON.
- Convert processing_duration_ms en Numeric.
- Garder cette seule colonne.
- Histogram, taille de classe 100 ms, unité milliseconds.

La mesure correspond au temps de boucle du générateur, comprenant ses écritures et temporisations de simulation. Pour movies/incident, la pause par ligne est volontairement augmentée. Ce n’est ni une latence réseau ni un temps serveur HTTP.

Il n’y a que six valeurs : cela suffit pour comprendre la visualisation, pas pour conclure sur un percentile de production. Les valeurs exactes dépendent de l’exécution et ne sont pas imposées comme constantes.

## 20. Ajouter les logs et le parcours de détail

### P19 — Événements d’investigation

- Requête 17_investigation_logs, Range.
- Visualisation Logs, heure visible, détails activés, pas de déduplication pour la validation.
- Choisir movies puis incident ; examiner les deux rejets et le résumé.

Le filtre dataset ne montre pas le heartbeat control ; la requête dédiée 20_heartbeat permet de l’examiner séparément.

### Lien depuis un batch

Dans la table P16, ajouter un Data link au champ batch_id :

```text
/d/a13-investigation/detail?var-run=${run}&var-event_id=${__data.fields.batch_id}&from=${__from}&to=${__to}
```

Le dashboard de détail fourni utilise event_id comme texte ou préfixe de batch :

```logql
{job=~"atelier09|atelier11"} |= "${run}" |= "${event_id}"
```

Un batch_id est un préfixe des event_id de ses records ; le lien retrouve les observations structurées et leurs sondes brutes. Les IDs générés utilisent des caractères simples compatibles avec cet exemple de lien.

La période est transmise. Partager le lien ne confère aucun droit supplémentaire et ne contourne pas la connexion Grafana.

## 21. Organiser le dashboard avant d’enregistrer

Disposition proposée :

```text
Périmètre, sources et variables

Observées | Attendues | Validées | Rejetées | Manquantes | Complétude

Chronologie par corpus | Codes HTTP | Part 5xx

Histogramme tailles | Heatmap tailles / temps

Heatmap retard source | Retard max | Dernière date source

Complétude par dataset | Table des batches

Rejets par règle | Histogramme temps du générateur

Logs détaillés + liens d’investigation

Limites, couverture et définition des indicateurs
```

Ajouter dans un panneau Text les définitions du contrat, de la complétude et des horloges. Garder les tableaux assez larges pour lire les IDs et raisons. Un chiffre exact dans un panneau illisible n’est pas un résultat satisfaisant.

## 22. Tester les contrôles comme à l’atelier 08

| Sélection | Attendues | Observées/tentées | Validées | Rejetées | Manquantes | Complétude |
|---|---:|---:|---:|---:|---:|---:|
| All / All | 30 | 29 | 27 | 2 | 1 | 90 % |
| movies / All | 15 | 14 | 12 | 2 | 1 | 80 % |
| movies / incident | 5 | 4 | 2 | 2 | 1 | 40 % |
| movies / recovery | 5 | 5 | 5 | 0 | 0 | 100 % |
| access / incident | 5 | 5 | 5 | 0 | 0 | 100 % |

Sur access/incident, la part 5xx vaut 2/5=40 % alors que la complétude des logs reste 100 %. Cette différence illustre le rôle de chaque indicateur.

Sur movies/recovery, 100 % ne signifie pas que les anomalies précédentes ont été réparées. Revenir à All phases pour lire le bilan global.

Les histogrammes/heatmaps doivent suivre les filtres de leurs requêtes, sans recevoir un filtre HTTP appliqué par erreur aux batches movies. Garder les mêmes variables au numérateur et au dénominateur.

## 23. Investigation guidée : du signal à la preuve

### Mission

Un utilisateur signale une baisse de complétude MovieLens. Votre dashboard doit permettre de répondre sans inventer de cause racine.

### Étapes

1. All phases : observer 80 % de complétude movies et deux règles de rejet.
2. Isoler incident : 40 %, une référence manquante et retard de 600 s.
3. Ouvrir la table de batch puis le lien de détail.
4. Identifier title_missing et duplicate_movie_id.
5. Examiner source_reference et source_sha256 pour retrouver les références utilisées.
6. Comparer le nombre de records observés au compteur attempted du résumé.
7. Passer à recovery : flux sain, mais pas de preuve de backfill.
8. Vérifier séparément les 503 access ; ne pas affirmer qu’ils causent les rejets MovieLens uniquement parce qu’ils ont été générés pendant la même phase.

### Conclusion attendue

La simulation montre une combinaison de complétude, qualité et retard. Elle ne prouve pas une dépendance technique entre le serveur web et l’import MovieLens. Un incident réel demanderait des éléments de causalité supplémentaires.

## 24. Vérifier un indicateur avec l’API Loki

Le constructeur fourni génère des requêtes sans variables Grafana dans livrables13/requetes-api.

```bash
python3 construire_dashboard13.py --manifest preparation13.json \
  --reference reference13.json --output-dir livrables13

END_REF=$(python3 -c 'import json; print(json.load(open("reference13.json"))["to_ns"])')

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode "query=$(cat livrables13/requetes-api/06_completeness.logql)" \
  --data-urlencode "time=$END_REF" \
  -o controle13-completude.json
```

Attendu : un résultat vectoriel de valeur 0.9 si toutes les phases et les deux datasets sont inclus.

Les requêtes générées remplacent $__range par une durée entière arrondie vers le haut qui couvre la période vérifiée. Le marker unique évite de ramener d’autres lots sur cette marge.

Pour une requête de lignes, utiliser query_range avec from_ns/to_ns et une limite appropriée ; ne pas compter les séries d’un vector comme des records.

Si le dashboard et l’API divergent, comparer : datasource, variables, bornes, Instant/Range, limite de lignes et transformations. Un Histogram qui manque des valeurs peut être correct sur les seules lignes reçues mais incomplet sur la population.

## 25. Export/import : corrigé proposé, pas preuve de fonctionnement

Le constructeur crée :

- dashboard13-grafana.json : 21 panneaux incluant contexte et explications.
- dashboard13-investigation.json : détail par événement ou batch.
- les requêtes API personnalisées.

### Importer si nécessaire

1. Dashboards → New/Import.
2. Charger le JSON de détail puis le principal.
3. Sélectionner la datasource Loki correcte dans la variable loki_ds.
4. Vérifier la période absolue et les variables.
5. Ouvrir P10/P11 et vérifier le champ source Line dans Extract fields.
6. Ajuster si votre version nomme le champ différemment.
7. Vérifier les types Time/numeric et Calculate from data des heatmaps.
8. Refaire les contrôles de la section 22.

Deux modèles JSON statiques sont également joints : ils ont un run à remplacer et une période relative par défaut. Pour obtenir les exports personnalisés avec votre période vérifiée, privilégier le constructeur.

Les exports emploient des UID de laboratoire fixes. S’ils existent déjà, ne pas écraser un objet utilisé sans accord ; dupliquer ou adapter l’UID. Le JSON est généré et contrôlé structurellement, pas testé dans votre version Grafana. La procédure manuelle reste la référence pour adapter options et transformations.

## 26. Extension du fil rouge : corréler réellement Loki et Elasticsearch

### Objectif

Projeter exactement les mêmes event_id dans Elasticsearch, sans prétendre que l’ancien index atelier08-access contient déjà ces événements.

L’index atelier13-events est une projection d’observabilité. Il conserve records, décisions de rejet, résumés et heartbeats ; ce n’est pas une table métier dédupliquée sur movieId.

### Publier la copie structurée

Le mapping et le script sont fournis. Exemple avec les chemins de certificat préparés à l’atelier 01 :

```bash
sudo python3 publier_elasticsearch13.py \
  --events scenario13/produced_events.jsonl \
  --mapping mapping-atelier13-events.json \
  --url https://localhost:9200 \
  --ca "$HOME/.config/elastic-lab/http_ca.crt" \
  --index atelier13-events --username elastic
```

Le mot de passe est saisi au prompt, pas dans la commande. Le compte administrateur est réservé à cette initialisation sur VM pédagogique. La variante --auth api-key demande une clé encodée au prompt. Ne jamais désactiver la vérification TLS pour passer une erreur de certificat.

Le script crée l’index s’il est absent et vérifie les types de champs principaux s’il existe ; il ne le supprime pas. Les droits create_index/write nécessaires à l’initialisation sont différents des droits de lecture de Grafana.

### Contrôle Elasticsearch

Dans Dev Tools, sur le run réel :

```http
GET atelier13-events/_count
{
  "query":{"bool":{"filter":[
    {"term":{"run_id":"RUN_REEL"}},
    {"term":{"a13_kind":"record"}},
    {"term":{"accepted":true}}
  ]}}
}
```

Attendu : 27 documents de record validés. La projection complète possède 38 événements pour ce run, pas 27 ; il faut reproduire le même filtre avant de comparer.

### Ajouter une datasource Elasticsearch dans Grafana

- URL HTTPS locale compatible avec le certificat.
- Index atelier13-events, champ de temps @timestamp.
- Authentification de lecture dédiée et CA approuvée.
- Ne pas laisser le compte elastic comme identité permanente de la datasource.

Ajouter en bonus une table ou un compteur avec requête Lucene :

```text
run_id:"${run}" AND a13_kind:"record" AND accepted:true AND source_dataset:/${dataset:regex}/ AND phase:/${phase:regex}/
```

Les champs sont des keywords pour ces filtres. Tester la syntaxe et les valeurs All dans la version du plugin installée. Le panneau ES doit utiliser la même période et les mêmes filtres métier que le panneau Loki comparable.

### Corrélation

Copier un event_id de la projection ES et le rechercher dans Loki. Le même ID apparaît dans l’instrumentation et la sonde brute correspondante. Le lien peut être configuré vers le dashboard de détail avec cet event_id et la période.

Ce n’est pas un join serveur entre Loki et Elasticsearch. Si l’on utilise une transformation de jointure dans Grafana, vérifier l’unicité et la cardinalité des clés pour éviter une multiplication des lignes.

La projection ES emploie event_id comme _id : republier les mêmes événements met à jour les mêmes documents. Une réémission dans un fichier Loki n’est pas un upsert et peut produire des doublons. Ne pas comparer les deux systèmes sans comprendre cette différence.

## 27. Indicateur, objectif et alerte : exercice contrôlé

### Définition

Indicateur de simulation : somme des validées movies / somme des attendues movies sur les batches émis dans les cinq dernières minutes.

Objectif d’exercice : au moins 95 %. Ce seuil n’est pas un SLO de production validé.

### Construire une règle Grafana-managed

1. Alerting → Alert rules → New rule.
2. Datasource Loki-Formation et expression de regle-alert-atelier13.logql.
3. La requête est autonome : pas de variable de dashboard ni de run spécifique.
4. Réduire à la dernière valeur si nécessaire ; condition <0.95.
5. Pour un test de laboratoire : évaluation environ 30 s et pending None/0 s ; ne pas extrapoler ces réglages en production.
6. Étiqueter formation=true ; laisser les notifications externes désactivées tant que leur destination n’a pas été validée.
7. Définir explicitement le comportement No data et Error.

La règle utilise les batches présents dans sa fenêtre. Sans inventaire attendu/heartbeat, elle ne détecte pas un batch totalement absent ni une panne générale par un ratio vide.

L’incident reste dans une fenêtre de cinq minutes même après recovery ; l’alerte peut donc persister jusqu’à sa sortie. Ce n’est pas une incohérence avec un panneau filtré sur recovery uniquement.

Une règle active évalue l’heure courante. Elle ne rejoue pas automatiquement le T historique du dashboard. Si le scénario est ancien, produire un nouveau run volontairement ; ne pas attendre une alerte sur des événements sortis de la fenêtre.

## 28. Défi final

### Énoncé

Livrer un dashboard construit et expliqué qui permet de :

1. Retrouver les totaux 30 attendues, 29 observées, 27 validées, 2 rejetées et 1 manquante.
2. Isoler movies/incident avec 40 % de complétude.
3. Montrer histogramme et heatmap des quinze tailles HTTP sans calculer une distribution de moyennes.
4. Localiser les quatre événements retardés de dix minutes.
5. Distinguer erreurs HTTP, rejets métier et problème de transport.
6. Ouvrir les records depuis un batch.
7. Vérifier au moins un KPI par l’API.
8. Expliquer pourquoi recovery=100 % ne signifie pas bilan global réparé.
9. En extension, retrouver le même event_id dans Elasticsearch et Loki.
10. Documenter indicateur, objectif d’exercice et limites de l’alerte.

## 29. Corrigé et contrôles attendus

| Contrôle | Attendu |
|---|---|
| JSON / records / batches / heartbeats | 38 / 29 / 6 / 3 |
| Sondes access / movies | 15 / 14 |
| Total attendu / validé / rejeté / manquant | 30 / 27 / 2 / 1 |
| Complétude globale / movies globale | 90 % / 80 % |
| Complétude movies incident / recovery | 40 % / 100 % |
| HTTP 200 / 503 / 404 | 12 / 2 / 1 |
| Part HTTP 5xx globale / incident | 13,33 % environ / 40 % |
| Histogramme tailles | 15 observations, fréquences 6 / 3 / 3 / 3 dans les classes non vides |
| Heatmap retard | 25 valeurs à 2 s ; 4 à 600 s |
| Rejets par cause | 1 title_missing, 1 duplicate_movie_id |
| Projection ES complète / records validés | 38 / 27, si extension publiée sans erreurs |

Le nombre exact de cellules de heatmap et le temps mesuré du générateur dépendent du déroulement réel ; ils ne sont pas imposés comme des constantes.

## 30. Dépannage

| Problème | Vérification |
|---|---|
| Explore vide | Source, période, run_id et collecte avant le parser |
| KPI différents | Variables, phase/dataset, Instant, doublons ou filtre local |
| Histogramme de timestamps | Filtrer les champs ; ne garder que la valeur numérique voulue |
| Histogramme à 3 valeurs au lieu de 15 | Une agrégation a été faite avant le panneau |
| Heatmap vide | Time conservé, type numérique, champ Line et limite de lignes |
| Heatmap de moyennes | Revenir aux observations individuelles ou expliciter cette autre population |
| Complétude 100 % après reprise | Filtre recovery ; revenir à All pour le bilan |
| Retard max reste 600 s | Agrégation historique, pas retard actuel |
| Titre vide paraît rempli dans le CSV | Le suffixe de sonde est technique ; inspecter le titre métier JSON |
| ES 38 versus Loki 29 | Types d’événement différents : reproduire record et accepted |
| Alarme No data | Lot ponctuel sorti de la fenêtre ; attente et collecte continue à définir |

## 31. Sauvegarde, partage et conservation

Enregistrer le dashboard et celui d’investigation. Réouvrir les liens avec une session autorisée, vérifier les variables et exporter le JSON selon les permissions.

Un export de dashboard ne contient ni les logs Loki, ni les documents ES, ni les secrets de datasource à diffuser. Partager un lien ne crée pas les droits et ne doit pas conduire à activer l’accès anonyme pour contourner un problème.

Conserver scénario, rapports, requêtes et captures. Ne pas supprimer les stockages de lecture Alloy ou les données historiques pour remettre artificiellement les compteurs à zéro. Pour un nouvel essai, utiliser un nouveau run et le sélectionner explicitement.

Les sondes ont été ajoutées aux copies de travail A09 ; ne pas les présenter ultérieurement comme des lignes originales du jeu public. Les références initiales utilisées restent identifiables et non remplacées.

## 32. Livrables et validation formateur

Livrer :

- le dashboard et le détail, avec export JSON si autorisé ;
- preparation13.json et reference13.json ;
- les requêtes et une réponse API de contrôle ;
- une note sur définitions, couverture et limites ;
- en extension, preuve de corrélation ES/Loki et configuration d’alerte expurgée.

Les scripts, requêtes et exports sont joints. La génération a été testée localement sur échantillons ; les comptes, IDs et distributions ont été contrôlés. Les clients Loki/ES ont été testés avec des réponses simulées. Les JSON des dashboards ont été contrôlés structurellement.

Aucun import Grafana, exécution LogQL réelle, publication Elasticsearch réelle ni activation d’alerte n’a été effectué pendant la génération. Les transformations, options de heatmap et datasource doivent être répétées sur les versions du laboratoire. Le support ne présente pas un export généré comme un dashboard déjà validé en interface.

## Documentation Grafana :
Histogram, Heatmap, Introduction to histograms and heatmaps, transformations Extract fields/Convert field type, variables, data links et dashboards. Points structurants : distribution d’observations, heatmap temporelle, effet des agrégations préalables et portée explicite des variables.
