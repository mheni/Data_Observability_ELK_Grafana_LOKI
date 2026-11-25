# Atelier 13 bis — De fichiers autonomes à un tableau de bord Grafana complet avec Loki

Fusion pédagogique des ateliers 11 et 13 : préparer → collecter → explorer avec LogQL → vérifier → créer chaque panneau → investiguer.

## 1. Fiche pédagogique et contrat de l’atelier

| Élément | Choix |
|---|---|
| Public | Participants débutants dans Grafana et LogQL, accompagnés sur Linux |
| Infrastructure déjà installée | Ubuntu, Loki local, Grafana, binaire Alloy et compte système `alloy` |
| Anciens TP requis pour les données | Aucun : ni atelier 9, ni 10, ni 11, ni 13 |
| Sources par défaut | Cinq lignes Apache et cinq films de démonstration créés par le pack |
| Formats | Brut Apache, CSV, copies JSON et logfmt |
| Collecte dédiée | Service `alloy-atelier13bis`, sans remplacer le service Alloy précédent |
| Dashboard | 24 panneaux, dont contexte et limites, plus un tableau de bord de détail |
| Exploration | 60 requêtes avec consignes de saisie, exécution et lecture |
| Durée complète réaliste | Environ 1,5 à 2 jours avec exercices et explications ; le formateur peut répartir les panneaux |
| Extension | Projection des mêmes événements dans Elasticsearch et règle Grafana-managed |

Ce pack intègre les objectifs de l’atelier 11 — parsers, alias, CSV, conversions et erreurs — et le fil rouge normal/incident/recovery de l’atelier 13. Il remplace leurs dépendances aux sources A09/A11 par des sources et une collecte dédiées. [file:178][file:164]

### 1.1 Ce qui est autonome et ce qui ne l’est pas

L’atelier fournit données de référence, normaliseur, configuration Alloy, installation du service de TP, générateur du scénario, contrôles Loki, requêtes et exports de secours. Il ne réinstalle pas le serveur Loki ni Grafana. Il ne nécessite pas Elasticsearch pour le parcours principal.

La configuration fournie vise un Loki mono-tenant local accessible sur `http://127.0.0.1:3100`, dans le laboratoire non exposé publiquement. Un déploiement distant, authentifié ou multi-tenant exige de préparer URL, CA, authentification et en-tête de tenant de manière cohérente avant la séance. Ne pas désactiver TLS pour contourner un problème.

### 1.2 Interface Grafana : ne pas recopier les menus de Kibana

Le texte est en français. Les boutons Grafana sont indiqués sous leur nom anglais avec leur fonction française : **Explore / Explorer**, **Add visualization / Ajouter une visualisation**, **Run queries / Exécuter**, **Apply / Appliquer**, **Save dashboard / Enregistrer le tableau de bord**.

Le type de tuile est **Stat** dans Grafana : il ne faut pas chercher le menu « Indicateur » de Kibana. La version et la langue exactes de Grafana n’ont pas été communiquées ; la position et certaines traductions restent à confirmer sur le laboratoire. Si l’éditeur n’a pas de bouton Apply, utiliser l’action de retour au dashboard qui conserve le panneau, puis enregistrer le dashboard.

### 1.3 Lire une consigne de manipulation

- Cliquer : clic gauche.
- Glisser : maintenir le clic sur la poignée ou l’en-tête indiqué, déplacer puis relâcher.
- Dans Grafana, on ne glisse pas les champs dans les axes comme dans Lens : on saisit LogQL, puis on configure la visualisation et les transformations.
- Une requête de lignes renvoie des événements ; une requête métrique renvoie des nombres. Le choix Instant/Range doit être explicite.
- Un panneau et le dashboard doivent être conservés : revenir au dashboard ne dispense pas de l’enregistrer.

## 2. Architecture et jeux de données

```text
Pack autonome
  ├─ sources13bis/access_log  : cinq références Apache
  ├─ sources13bis/movies.csv  : cinq films de démonstration
  └─ normalisation → JSON + logfmt, plus quatre contrôles
          │ installation dans des copies de travail dédiées
          ▼
/var/log/formation13bis/
  ├─ raw/access_log
  ├─ raw/movies.csv
  ├─ json/events.jsonl
  └─ logfmt/events.logfmt
          │ service alloy-atelier13bis, stockage de positions dédié
          ▼
Loki → Grafana Explore → LogQL → panneaux → dashboard
          ▲
          │ le scénario ajoute 15 sondes Apache, 14 sondes CSV,
          │ et 38 événements JSON ; il ne remplace pas les références
```

### 2.1 Provenance : ne pas maquiller les exemples

Par défaut, les cinq films portent des titres fictifs « Film de démonstration ... ». Le second contient une virgule et des guillemets pour tester le CSV, un autre n’a pas d’année. Ce n’est pas un extrait authentique de MovieLens. Les cinq lignes Apache sont aussi des références synthétiques, signalées par `A13B_SEED` et une IP de boucle locale.

Le nom fonctionnel `movies` est conservé pour le schéma et le scénario. Si l’on souhaite de vraies références, le script accepte `--access` et `--movies` vers deux fichiers existants, sans exiger un atelier précédent. Il n’en prélève que cinq références et ne revendique pas de provenance publique à leur place. Les résultats exacts de l’exploration des références changent alors ; les comptes du scénario restent définis par son contrat.

Aucune latence HTTP ni position géographique réelle n’est ajoutée. Le temps de génération des batches est une mesure de simulation nommée comme telle.

### 2.2 Labels de stockage et champs extraits

| Flux | Labels stables |
|---|---|
| Apache brut | `job="atelier13bis_raw", dataset="access"` |
| CSV brut | `job="atelier13bis_raw", dataset="movies"` |
| JSON | `job="atelier13bis", format="json"` |
| logfmt | `job="atelier13bis", format="logfmt"` |

`source_dataset`, `phase`, `accepted`, `status`, `title`, `run_id` et `event_id` restent dans les lignes : on les extrait à la requête. On ne crée pas un label de stockage par film, IP ou événement. Un parser LogQL ne réécrit pas rétroactivement l’index. [web:188]

## 3. Vérifier l’infrastructure avant de créer des données

1. Ouvrir un terminal sur la VM.
2. Vérifier les composants installés :

```bash
command -v alloy
alloy --version
id alloy
getent group alloy
sudo systemctl status loki-formation grafana-server --no-pager
curl --fail-with-body -fsS http://127.0.0.1:3100/ready
curl --fail-with-body -fsS http://127.0.0.1:3000/api/health | python3 -m json.tool
sudo ss -ltnp | grep -E ':(3000|3100|12346)\b'
```

Adapter le nom du service Loki si votre installation utilise un autre nom. Le port 12346 doit être libre : il sera l’interface locale du collecteur dédié. Les ports 3000 et 3100 sont ceux déjà utilisés par Grafana/Loki.

3. Ne pas poursuivre si `/ready` échoue ou si le compte Alloy n’existe pas. L’atelier ne résout pas une installation serveur absente par un changement de requête.
4. Depuis le poste participant, ouvrir Grafana. Si nécessaire, garder ce tunnel SSH ouvert :

```bash
ssh -N -L 3000:127.0.0.1:3000 utilisateur@IP_PUBLIQUE_VM
```

Ouvrir `http://localhost:3000`, se connecter avec un compte autorisé. Ne pas exposer les services au public ni activer l’accès anonyme pour contourner les droits.

## 4. Préparer directement les références et copies structurées

### 4.1 Utiliser un dossier de travail contenant le pack

1. Extraire tout le ZIP dans un dossier de travail.
2. Ouvrir un terminal dans le dossier qui contient les scripts.
3. Vérifier :

```bash
pwd
ls preparer_sources13bis.py normaliser_sources13bis.py config-atelier13bis.alloy
python3 --version
```

Ne pas créer ensuite un nouveau dossier vide et y lancer les commandes sans copier les fichiers.

### 4.2 Générer les références autonomes

```bash
python3 preparer_sources13bis.py --output-dir sources13bis
cat sources13bis/sources-manifest.json
head -n 5 sources13bis/access_log
cat sources13bis/movies.csv
```

Attendu : cinq lignes Apache et cinq enregistrements de films, plus l’en-tête CSV. Le dossier déjà présent est refusé pour ne pas remplacer une source suivie.

Variante facultative, à choisir à la place de la génération synthétique :

```bash
python3 preparer_sources13bis.py --output-dir sources13bis \
  --access /chemin/vers/access_log --movies /chemin/vers/movies.csv
```

Les deux fichiers doivent être fournis ensemble. Ne pas utiliser cette variante après la génération dans le même dossier ; décider avant le démarrage du TP.

### 4.3 Produire JSON et logfmt avec les contrôles

```bash
set -o pipefail
python3 normaliser_sources13bis.py \
  --access sources13bis/access_log --movies sources13bis/movies.csv \
  --output-dir corpus13bis --with-controls | tee preparation13bis.json

test -s corpus13bis/manifest.json
cat preparation13bis.json
wc -l corpus13bis/events.jsonl corpus13bis/events.logfmt
```

Avec les références autonomes : 5 access + 5 movies + 4 contrôles = 14 événements dans chaque format, donc 28 représentations. Ce n’est pas 28 requêtes ou 28 films distincts.

Le script lit les originaux sans les modifier. Il conserve les lignes Apache dans `raw_line`, traite le CSV avec le module Python `csv`, crée `normalization_id` et `record_id`, et encode correctement les guillemets. Les objets et tableaux JSON ne deviennent pas implicitement des tableaux logfmt.

### 4.4 Comprendre les quatre contrôles

| Cas | Niveau | Nombre `duration_ms` | Durée `elapsed` | Taille `payload` | Sens |
|---|---|---|---|---|---|
| C_VALID | WARN | 1800 | 1.8s | 2MB | Valeurs convertibles |
| C_BAD | ERROR | unknown | unknown | unknown | Conversion impossible |
| C_MISSING | INFO | absent | absent | absent | Champ manquant, message mentionnant ERROR |
| C_NEGATIVE | ERROR | -5 | -5ms | 1KB | Convertible mais incohérent pour une durée positive |

Les contrôles sont étiquetés `synthetic=true`. Une recherche textuelle d’ERROR et une égalité sur le champ `level` ne répondront pas à la même question. Le JSON valide n’assure ni champ complet, ni valeur convertible, ni sens métier correct. [file:178]

## 5. Charger les fichiers dans Loki avec une collecte dédiée

### 5.1 Pourquoi un service distinct ?

Le TP n’écrase pas `/etc/alloy/config.alloy`, ne concatène pas aveuglément des blocs et ne redémarre pas l’ancien service Alloy. Le nouveau service utilise son propre chemin de configuration, son propre état de lecture et son interface locale sur 12346.

Les fichiers de positions d’Alloy permettent de reprendre la lecture. Le réglage `tail_from_end=false` lit le contenu existant si aucune position n’est enregistrée ; il ne force pas la relecture complète à chaque redémarrage. Ne pas supprimer cet état pour corriger artificiellement un compte. [web:185]

### 5.2 Lire la configuration avant de l’appliquer

Ouvrir `config-atelier13bis.alloy`. Repérer :

1. Les deux cibles brutes et les labels `dataset`.
2. Les deux cibles JSON/logfmt et le label `format`.
3. `tail_from_end=false`.
4. `forward_to=[loki.write.a13bis.receiver]`.
5. L’unique composant `loki.write "a13bis"` avec l’URL `/loki/api/v1/push`.

Aucun parser d’ingestion et aucun `stage.timestamp` n’est utilisé : le but est de parser dans LogQL. Les dates Apache de référence restent du texte ; le timestamp Loki est l’heure de collecte. Cela évite aussi de soumettre involontairement un vieux timestamp source aux limites de Loki. `loki.source.file` lit les lignes et les transmet au writer configuré. [web:190]

### 5.3 Installer la collecte

Depuis le dossier du pack, exécuter une seule fois :

```bash
sudo bash installer_collecte13bis.sh sources13bis corpus13bis
```

Le script vérifie le compte et le port, refuse d’écraser des ressources déjà présentes, copie les quatre fichiers, fixe les droits, valide la configuration Alloy et crée le service. Il ne vide aucun ancien stockage.

Lire ensuite :

```bash
sudo systemctl status alloy-atelier13bis --no-pager
sudo journalctl -u alloy-atelier13bis -n 80 --no-pager
sudo -u alloy test -r /var/log/formation13bis/raw/access_log
sudo -u alloy test -r /var/log/formation13bis/raw/movies.csv
sudo -u alloy test -r /var/log/formation13bis/json/events.jsonl
sudo -u alloy test -r /var/log/formation13bis/logfmt/events.logfmt
```

Si une installation partielle est arrêtée par `alloy validate`, inspecter les ressources créées et corriger la configuration avec le formateur. Ne pas supprimer automatiquement le dossier de logs ou l’état de positions. Après correction, valider explicitement et reprendre la création/démarrage du service si elle n’a pas encore eu lieu.

### 5.4 Contrôler la livraison des deux formats

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_normalisation13bis.py \
  --manifest preparation13bis.json --corpus corpus13bis \
  --output reference-normalisation13bis.json
```

Attendu : 14 JSON, 14 logfmt, mêmes IDs vérifiés séparément par format. Le rapport fige une période réelle de collecte. Il distingue la préparation locale de la livraison ; la simple présence du fichier ne prouve pas son arrivée dans Loki.

Ne pas remplacer le lot par une nouvelle normalisation parce que la collecte prend quelques secondes. En cas de résultat incomplet, lire les logs Alloy et vérifier les droits/labels.

## 6. Ajouter le scénario normal → incident → recovery

### 6.1 Déroulement du scénario

| Phase | Access | Catalogue movies | Retard source simulé |
|---|---|---|---|
| normal | 5 sondes HTTP 200 | 5 attendues, 5 tentées et validées | 2 s |
| incident | 200, 200, 503, 503, 404 | 5 attendues, 4 tentées, 2 validées, 2 rejetées, 1 manquante avant lecture | 600 s sur les 4 records movies |
| recovery | 5 sondes HTTP 200 | 5 attendues, 5 tentées et validées | 2 s |

Les rejets sont `title_missing` et `duplicate_movie_id`. La phase recovery ne rattrape pas les anomalies précédentes. Les 503 access ne sont pas automatiquement la cause des rejets de catalogue : le scénario les place dans une même phase pour apprendre à distinguer les signaux. [file:165]

### 6.2 Exécuter un seul nouveau run

```bash
set -o pipefail
sudo python3 generer_scenario13bis.py \
  --raw-dir /var/log/formation13bis/raw \
  --events /var/log/formation13bis/json/events.jsonl \
  --output-dir scenario13bis --phase-wait 15 --pace 0.05 \
  | tee manifest-scenario13bis.json

test -s manifest-scenario13bis.json
sudo test -s scenario13bis/manifest13.json
```

Le générateur ajoute des sondes aux copies de travail. Il écrit uniquement les événements instrumentés du scénario dans le flux JSON ; le logfmt reste la copie normalisée initiale. Ce choix évite de doubler les KPI du scénario dans deux formats.

Le dossier de sortie déjà présent est refusé. Ne pas rejouer le générateur pour masquer un graphique vide : un nouveau run est un nouvel essai, pas un upsert du précédent.

### 6.3 Vérifier les trois chemins de collecte

```bash
python3 verifier_scenario13bis.py \
  --manifest manifest-scenario13bis.json --output reference13bis.json
```

Attendu pour ce run :

| Chemin | Quantité |
|---|---:|
| Sondes Apache brutes | 15 |
| Sondes CSV brutes | 14 |
| JSON record | 29 |
| JSON batch | 6 |
| JSON heartbeat | 3 |
| Total JSON | 38 |
| Total des représentations du run dans Loki | 67 |

Le vérificateur contrôle les IDs JSON uniques et les contenus par batch. Les 67 lignes de transport ne sont pas 67 lignes métier ; les KPI de records utilisent les 29 JSON de type record.

### 6.4 Générer les requêtes prêtes à copier et le support personnalisé

```bash
python3 construire_requetes_base13bis.py \
  --manifest preparation13bis.json --output-dir requetes13bis-base

python3 construire_exploration13bis.py \
  --normalisation preparation13bis.json --scenario manifest-scenario13bis.json \
  --reference reference13bis.json --output-dir exploration13bis

python3 personnaliser_support13bis.py \
  --normalisation preparation13bis.json --scenario manifest-scenario13bis.json \
  --reference reference13bis.json --output-dir supports13bis
```

Les 60 expressions d’Explore sont écrites avec les vrais identifiants : aucun ancien manifeste A10/A11 n’est nécessaire. Ouvrir ensuite le guide personnalisé dans `supports13bis`, pas son modèle avec marqueurs.

Les requêtes des panneaux utilisent les variables de dashboard `${run}`, `${dataset:regex}` et `${phase:regex}` ; ces variables seront créées explicitement avant la première visualisation.

## 7. Configurer Loki dans Grafana et exécuter les premières recherches

### 7.1 Créer ou vérifier la source de données

1. Ouvrir Grafana dans le navigateur et se connecter.
2. Dans la navigation, ouvrir **Connections / Connexions**, puis **Data sources / Sources de données**. Sur une navigation plus ancienne, passer par le menu de configuration des sources.
3. Si `Loki-Formation` existe, l’ouvrir et vérifier son type Loki et son URL ; ne pas créer un doublon sans raison.
4. Sinon, cliquer **Add new data source**, chercher Loki et sélectionner ce type.
5. Nommer la source `Loki-Formation`.
6. Dans l’URL serveur, saisir `http://127.0.0.1:3100` si Grafana et Loki sont sur la même VM native. Ce n’est pas l’URL `/push`.
7. Conserver l’authentification conforme au laboratoire ; ne pas inventer d’identifiants.
8. Cliquer **Save & test / Enregistrer et tester** et lire le résultat.

Si Grafana tourne dans un conteneur ou sur une autre machine, localhost ne désigne pas la VM Loki. Faire adapter l’adresse côté serveur avant la séance ; le parcours principal vise l’installation Ubuntu native.

### 7.2 Explorer le premier flux brut

1. Ouvrir **Explore / Explorer** depuis la navigation.
2. Dans le sélecteur de source en haut de l’espace de requête, choisir `Loki-Formation`.
3. Sélectionner **Code** plutôt que **Builder**.
4. Cliquer dans la requête A et saisir :

```logql
{job="atelier13bis_raw",dataset="access"}
```

5. Régler une période absolue couvrant la collecte depuis `reference-normalisation13bis.json` jusqu’à la fin de `reference13bis.json` si vous voulez voir références et sondes.
6. Cliquer **Run query / Exécuter**.
7. Développer une ligne. Repérer `job`, `dataset`, `filename` éventuel et le texte Apache.
8. Retirer toute déduplication d’affichage pour les contrôles. Une limite de lignes n’est pas un compteur exhaustif.

### 7.3 Explorer le lot JSON du scénario

Remplacer le texte de la requête A par le bloc suivant, dans le guide personnalisé où `__RUN__` est résolu :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
```

1. Régler la période sur les bornes de `reference13bis.json`.
2. Cliquer Exécuter.
3. Lire 38 événements de ce run si la limite est suffisante, pas seulement les 29 records.
4. Ajouter le parser puis les filtres :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", ds="source_dataset", ph="phase"
| __error__=""
| kind="record"
| ds="movies"
| ph="incident"
```

5. Exécuter de nouveau ; attendre quatre records.
6. Développer chacun pour lire `accepted`, `quality_reason`, `batch_id`, `event_id`, `event_time` et `source_delay_seconds`.

Loki renvoie les lignes et les champs extraits ; Grafana Explore permet de raffiner une requête avant de l’utiliser dans un panneau. [web:191]

## 8. Parcours Explore complet : apprendre avant de dessiner

Ouvrir le guide personnalisé `GUIDE_60_REQUETES_EXPLORE.md`. Chaque fiche précise la période, le type de requête, le code exact, le résultat attendu et les gestes de lecture. Exécuter les requêtes une à une en remplaçant A, pas en empilant 60 requêtes simultanées.

| Groupe | Manipulations | Compréhension à faire verbaliser |
|---|---|---|
| Flux et filtres textuels | E01–E07 | La sous-chaîne ERROR n’est pas le champ level=ERROR |
| Apache et CSV | E08–E13 | pattern/regexp ciblé, limites d’un découpage CSV naïf |
| JSON et qualité | E14–E22 | Alias, objets, présence, conversion et sens métier |
| logfmt et présentation | E23–E28 | Durées/tailles explicites, mauvais parser, line_format et label_format |
| Scénario | E29–E36 | Records, batches, rejets, 5xx, retard, heartbeat et recovery |
| Métriques et panneaux | E37–E60 | count, rate, unwrap, agrégations, ratios et limites de lignes |

### 8.1 Les différences de qualité à observer, pas seulement à réciter

1. Exécuter E05 et noter les trois contrôles qui contiennent ERROR dans le texte.
2. Exécuter E17 et lire seulement les deux contrôles dont le niveau vaut ERROR.
3. Exécuter E19 : la durée de C_VALID est comparable à 1000.
4. Exécuter E20 : C_BAD est JSON valide mais sa valeur unknown ne se convertit pas.
5. Exécuter E21 : C_MISSING ne contient pas le champ ; ce n’est pas le nombre zéro.
6. Exécuter E22 : C_NEGATIVE est convertible mais incohérent pour le besoin de durée positive.
7. Exécuter E26 : mauvais parser sur un autre format, donc erreur de structure.

Les erreurs ne sont pas toujours supprimées par Loki. Elles sont transmises dans `__error__`, et le filtre doit être placé après l’étape qui les crée, notamment après `unwrap`. [web:187][web:188]

### 8.2 Avant les requêtes métriques

- `count_over_time` compte les lignes dans une fenêtre.
- `rate` exprime un nombre de lignes par seconde sur une fenêtre, pas une latence.
- `unwrap` extrait une valeur numérique par observation pour une agrégation de valeurs.
- `sum_over_time` sur `accepted_count` additionne les compteurs des résumés, pas les occurrences d’un mot.
- Une fenêtre de 10 s évaluée tous les 10 s reste une construction de fenêtres ; ne pas sommer ses points pour reconstituer un total sans étudier les bornes et recouvrements.

Les métriques sur lignes et les métriques sur valeurs dépliées par unwrap ne sont pas interchangeables. [web:186]

## 9. Créer le tableau de bord et ses variables, clic par clic

### 9.1 Créer un dashboard vide

1. Dans la navigation Grafana, ouvrir **Dashboards**.
2. Cliquer **New / Nouveau**, puis **New dashboard / Nouveau tableau de bord**.
3. Choisir la création d’un tableau de bord vide, pas l’import du JSON de secours.
4. Cliquer **Save dashboard / Enregistrer**.
5. Titre : `[A13bis] Data Observability — Access et catalogue`.
6. Choisir le dossier du laboratoire autorisé et confirmer.
7. Ouvrir les paramètres du dashboard, souvent via la roue dentée ou **Settings / Paramètres**.
8. Dans les options temporelles, choisir UTC pour rendre les relevés comparables ; enregistrer les paramètres.
9. Régler la période absolue sur `from_utc` et `to_utc` de `reference13bis.json`. C’est le scénario, pas le lot de normalisation, qui alimente les panneaux principaux.

### 9.2 Variable de source Loki

1. Ouvrir Settings → Variables.
2. Cliquer **Add variable / Ajouter une variable**.
3. Name : `loki_ds`. Label affiché : `Source Loki`.
4. Type : **Data source**.
5. Type de source recherché : Loki.
6. Dans l’aperçu/sélection, choisir `Loki-Formation` ; conserver le choix comme valeur courante.
7. Confirmer la variable, revenir au dashboard et enregistrer.

### 9.3 Variable du run

1. Retourner dans Settings → Variables → Ajouter une variable.
2. Name : `run`. Label : `Run du scénario`.
3. Type : **Text box / Zone de texte**.
4. Valeur : `__RUN__` dans le support personnalisé, sans guillemets supplémentaires ni espaces.
5. Confirmer puis revenir au tableau de bord et enregistrer.

### 9.4 Variable de corpus

1. Settings → Variables → Ajouter.
2. Name : `dataset`. Label : `Corpus`.
3. Type : **Custom / Personnalisée**.
4. Values : `access,movies`.
5. Activer les sélections multiples.
6. Activer **Include All / Inclure Tout**.
7. Dans la valeur personnalisée de All, saisir `.*`.
8. Confirmer, revenir au tableau de bord, choisir All/Tout et enregistrer.

### 9.5 Variable de phase

1. Ajouter une autre variable de type Custom.
2. Name : `phase`. Label : `Phase`.
3. Values : `normal,incident,recovery`.
4. Activer le multi-choix et All ; valeur personnalisée All : `.*`.
5. Confirmer puis sélectionner All/Tout sur le tableau de bord.
6. Enregistrer.

Une variable n’applique pas un filtre magique. Chaque requête ci-dessous référence ses variables. Les deux côtés d’un ratio reçoivent les mêmes sélections ; le heartbeat ignore volontairement dataset car il concerne le contrôle global.

## 10. Construire les six KPI initiaux, chacun jusqu’à l’enregistrement

Ne pas lancer les panneaux sans avoir créé les quatre variables. Les blocs ci-dessous sont destinés aux panneaux Grafana ; leurs variables `$...` sont normales. Ne pas les envoyer telles quelles avec curl : les fichiers d’API résolus sont générés séparément.

### 10.1 P01 — Lignes métier observées

Objectif : Le comptage porte sur les records JSON, pas sur toutes les représentations brutes et structurées.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir None / Sans unité, ou un format numérique simple.
6. Régler les décimales à 0.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **29**. 

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P01 — Lignes métier observées`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 10.2 P02 — Attendues — contrat

Objectif : Le contrat déclare cinq références par corpus et par phase. Il ne s’agit pas d’un décompte de lignes déjà arrivées.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir None / Sans unité, ou un format numérique simple.
6. Régler les décimales à 0.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **30**. 

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P02 — Attendues — contrat`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 10.3 P03 — Validées — simulation

Objectif : Ces décisions sont celles de la simulation, pas des accusés de réception d’une base métier.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir None / Sans unité, ou un format numérique simple.
6. Régler les décimales à 0.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **27**. 

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P03 — Validées — simulation`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 10.4 P04 — Rejetées — règles métier

Objectif : Un titre vide et un identifiant dupliqué sont rejetés. Un HTTP 503 n’est pas un rejet de catalogue.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="rejected_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir None / Sans unité, ou un format numérique simple.
6. Régler les décimales à 0.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **2**. 

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P04 — Rejetées — règles métier`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 10.5 P05 — Manquantes avant lecture

Objectif : Une référence attendue du batch movies/incident n’est pas traitée. Elle ne produit pas un record à rechercher.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="missing_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir None / Sans unité, ou un format numérique simple.
6. Régler les décimales à 0.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **1**. 

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P05 — Manquantes avant lecture`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 10.6 P06 — Validées sur attendues

Objectif : Définition : validées / attendues, pas validées / records observés.

#### A. Ajouter une nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Dans la zone de code A, sélectionner le contenu existant et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
/
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Choisir une seule évaluation et afficher la valeur

1. Dans les options de la requête A, choisir **Type = Instant**. Ne pas laisser Both ou Range pour ce total de période.
2. Cliquer **Run queries / Exécuter les requêtes**.
3. Ouvrir le sélecteur de visualisation à droite et choisir **Stat**.
4. Dans les options de valeur, choisir le calcul **Last not null / Dernière non nulle**. La requête Instant renvoie déjà le résultat final ; ce calcul ne doit pas sommer une courbe.
5. Dans **Standard options → Unit / Unité**, choisir Percent (0.0–1.0), correspondant au code percentunit.
6. Régler les décimales à 1 ou 2.
7. Ne pas transformer automatiquement No data / Aucune donnée en zéro vert.
8. Garder le mode graphique de tendance désactivé pour cette tuile de total ; ne pas laisser une courbe suggérer une série que la requête Instant ne fournit pas.

#### C. Vérifier avant d’enregistrer

Attendu avec les deux corpus et les trois phases : **0,9, affiché 90 %**. Ne pas ajouter *100 à la formule si l’unité est Percent (0.0–1.0).

Si la valeur ne correspond pas, vérifier le run, les deux variables de filtre, la période et le type Instant avant de relancer des données. La somme des points d’une requête Range n’est pas la procédure de récupération d’un total.

#### D. Placer et enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P06 — Validées sur attendues`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 11. Chronologie, codes HTTP et ratio d’erreurs

### 11.1 P07 — Lignes par corpus dans une fenêtre de 10 secondes

#### A. Ouvrir un nouveau panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller dans A :

```logql
sum by (dataset_value) (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[10s]
))
```

#### B. Configurer la série temporelle

1. Choisir le type de requête **Range**, pas Instant.
2. Dans les options de requête/intervalle minimum, demander un pas minimum de `10s` pour le TP. Lire le pas réellement exécuté dans l’inspecteur si l’affichage diverge.
3. Cliquer Exécuter.
4. Dans le sélecteur de visualisation, choisir **Time series / Série temporelle**.
5. Dans le champ Legend / Légende de la requête, saisir `{{dataset_value}}`.
6. Choisir une unité numérique simple et zéro décimale pour les comptes.
7. Conserver la légende et les infobulles visibles.
8. Survoler un point : il représente un nombre de records dans les 10 s précédentes, pas un total absolu du run.
9. Ne pas sommer ces points pour retrouver les 29 records ; changer le pas peut changer la population des fenêtres lues.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P07 — Lignes par corpus — fenêtre glissante 10 s`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 11.2 P08 — Répartition des réponses HTTP par code

#### A. Créer le panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum by (status_value) (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
))
```

#### B. Configurer les barres de valeurs

1. Type de requête : **Instant**.
2. Cliquer Exécuter et observer les séries par `status_value`.
3. Choisir **Bar gauge / Jauge à barres** ; ne pas sélectionner Bar chart si la version attend un tableau catégoriel non préparé.
4. Orientation : horizontale.
5. Légende de la requête : `{{status_value}}`.
6. Calcul d’affichage : Last not null ; unité None, zéro décimale.
7. Vérifier les valeurs 200=12, 503=2 et 404=1 sur All/All.
8. Avec `dataset=movies`, absence de données HTTP attendue ; ne pas ajouter des HTTP fictifs au catalogue. Revenir à All après le test.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P08 — Réponses HTTP par code — sondes de simulation`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 11.3 P09 — Part de HTTP 5xx

#### A. Ajouter le panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller la formule complète, avec son traitement du zéro au numérateur :

```logql
(
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
| status_value >= 500
| __error__=""
[$__range]
))
 or
 (0 * sum (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
)))
) /
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
))
```

#### B. Configurer Stat et son unité

1. Type : **Instant**, puis Exécuter.
2. Visualisation : Stat.
3. Calcul de valeur : Last not null.
4. Unit : **Percent (0.0–1.0)**, deux décimales.
5. Ne pas multiplier la requête par 100.
6. Vérifier 2/15, environ 13,33 % sur All/All.
7. Tester access/incident : 2/5, soit 40 %. La complétude des logs access reste pourtant 100 %.
8. Tester movies : No data est correct, car le dénominateur HTTP n’existe pas. Ne pas convertir cette absence en « zéro erreur HTTP ».
9. Revenir à All/All avant la sauvegarde de référence.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P09 — Part de 5xx — HTTP reconnus`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 12. Construire les distributions sur les observations individuelles

Les trois panneaux de cette section manipulent des lignes, pas des moyennes calculées par fenêtre. Le résultat brut doit être inspecté avant de choisir l’histogramme ou la heatmap. L’option Heatmap « Calculate from data » détermine si le panneau doit calculer les classes à partir d’observations ou reçoit déjà des classes. [web:184]

### 12.1 P10 — Histogramme des quinze tailles HTTP

#### A. Ajouter une nouvelle visualisation et les lignes

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
```

9. Type : **Range**. Régler la limite de logs à 2000 pour ce petit scénario, puis Exécuter.
10. Basculer temporairement l’aperçu en Table view / Vue tabulaire. Repérer le champ contenant le texte JSON, souvent nommé `Line`. Le noter ; ne pas choisir un champ de labels à sa place.

#### B. Extraire un seul champ numérique utile

1. Ouvrir l’onglet **Transformations** sous la requête.
2. Cliquer **Add transformation / Ajouter une transformation**.
3. Rechercher **Extract fields / Extraire des champs** et cliquer ce choix.
4. Dans Source, sélectionner le champ de texte JSON repéré, généralement `Line`.
5. Format : JSON. Activer le remplacement des champs par les champs extraits ; conserver Time à cette étape pour vérifier l’origine.
6. Ajouter la transformation **Convert field type / Convertir le type de champ**.
7. Choisir `response_bytes` et le type **Numeric / Number**.
8. Ajouter **Filter fields by name / Filtrer les champs par nom**.
9. Dans la sélection des champs à conserver, décocher tous les champs, puis cocher uniquement `response_bytes`.
10. Dans l’aperçu tabulaire, vérifier qu’il reste une colonne numérique utile et quinze observations sur All/All. Ne pas laisser `producer_epoch`, `http_status`, un identifiant ou une durée dans la population de l’histogramme.
11. Si plusieurs data frames apparaissent, appliquer les transformations à toutes les trames pertinentes ; ne pas utiliser Organize fields seul s’il refuse plusieurs trames. Le filtre de champs est le choix principal ici.

#### C. Régler l’histogramme

1. Revenir au sélecteur de visualisation et choisir **Histogram / Histogramme**.
2. Dans les options d’histogramme, régler **Bucket size / Taille de classe = 1000**.
3. Offset / Décalage = 0.
4. Si un réglage combine plusieurs séries, l’utiliser uniquement après avoir confirmé que toutes contiennent le même champ `response_bytes`, pas d’autres nombres.
5. Étiqueter l’axe des valeurs comme une taille en octets et la fréquence comme un nombre d’observations. Si un réglage d’unité est appliqué au champ `response_bytes`, choisir bytes ; ne pas laisser une unité d’octets sur la fréquence par inadvertance.
6. Survoler les classes : [0,1000)=6, [1000,2000)=3, [4000,5000)=3, [8000,9000)=3.
7. Vérifier que la somme des fréquences vaut 15. Les valeurs 128, 512, 1500, 4096, 8192 sont chacune présentes dans les trois phases.

Un histogramme de `avg_over_time(response_bytes)` montrerait des moyennes glissantes, pas la distribution des quinze réponses. Ce n’est pas le calcul demandé.

#### D. Enregistrer et placer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P10 — Histogramme des tailles HTTP individuelles`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 12.2 P11 — Heatmap des tailles HTTP dans le temps

#### A. Créer le panneau indépendant

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller la requête de lignes, pas une moyenne métrique :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
```

9. Type Range, limite 2000, puis Exécuter et ouvrir la vue tabulaire.

#### B. Garder une date et une valeur numérique

1. Ouvrir Transformations → Ajouter → Extract fields.
2. Source : le champ de ligne JSON, généralement `Line` ; format JSON.
3. Remplacer les champs mais **conserver Time**.
4. Ajouter Convert field type : `response_bytes` vers Numeric.
5. Ajouter Filter fields by name : ne garder que `Time` et `response_bytes`.
6. Vérifier dans l’aperçu que Time est un champ de temps, pas une chaîne créée depuis `event_time` ; `response_bytes` doit être numérique.
7. Vérifier quinze observations avant d’interpréter les cellules. Si les colonnes ne sont pas correctes, corriger les transformations plutôt que changer les données.

#### C. Configurer la heatmap

1. Choisir **Heatmap / Carte thermique** dans les visualisations.
2. Régler **Calculate from data = Yes / Oui** : les valeurs ne sont pas déjà des classes.
3. X Bucket : mode Size, valeur `5s`.
4. Y Bucket : échelle Linear, mode Size, valeur `1000`.
5. Utiliser une palette séquentielle et garder l’infobulle ainsi que la légende visibles.
6. Vérifier : X = temps de collecte, Y = taille HTTP en octets, couleur = nombre d’observations dans la cellule.
7. Survoler les cellules des trois phases. Cinq observations HTTP existent par phase ; le nombre exact de cellules dépend de l’alignement des 5 s et de la collecte réelle.
8. Ne pas nommer cette visualisation « carte géographique » et ne pas attribuer une latitude à l’IP de boucle locale des sondes.

#### D. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P11 — Heatmap tailles HTTP — temps de collecte`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 12.3 P12 — Heatmap du retard source simulé

#### A. Ajouter la visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

9. Type Range, limite 2000, puis Exécuter.

#### B. Préparer les deux colonnes

1. Ouvrir Transformations → Ajouter → Extract fields.
2. Sélectionner le champ contenant le JSON, format JSON, remplacer les champs et garder Time.
3. Ajouter Convert field type : `source_delay_seconds` vers Numeric.
4. Ajouter Filter fields by name et garder uniquement `Time` et `source_delay_seconds`.
5. Examiner la table avant le graphique : 29 observations sur All/All, dont 25 à 2 s et 4 à 600 s.
6. Ne pas garder `producer_epoch` ou `source_event_epoch` comme valeurs de retard ; ils sont des dates exprimées en epoch.

#### C. Choisir et régler la heatmap

1. Sélectionner Heatmap.
2. Calculate from data = Yes.
3. X Bucket : Size `5s`.
4. Y Bucket : Linear, Size `60` ; l’unité de la valeur est la seconde.
5. Garder légende et infobulle.
6. Lire le groupe de quatre observations retardées pendant movies/incident.
7. Sélectionner phase=recovery pour vérifier les seules observations à 2 s, puis revenir à All avant le contrôle global.

Ce retard est calculé au moment de l’observation, pas recalculé en fonction de l’heure du navigateur. Le maximum historique reste 600 s si l’incident est toujours dans la période.

#### D. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P12 — Heatmap du retard source simulé à l’observation`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 13. Fraîcheur, comparaison par corpus et synthèse par batch

### 13.1 P13 — Retard maximal observé

#### A. Ajouter la requête

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
max (max_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_delay_seconds"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Configurer l’affichage

1. Type Instant, puis Exécuter.
2. Visualisation Stat.
3. Calcul Last not null.
4. Unit : seconds / secondes, pas milliseconds.
5. Zéro décimale.
6. All/All : 600 s ; phase recovery : 2 s.
7. Revenir à All. Ne pas transformer le titre en « retard actuel », car il s’agit d’un maximum de période.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P13 — Retard source maximal observé — non actuel`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 13.2 P14 — Dernière date source observée par corpus

#### A. Ajouter le panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller la requête complète, qui multiplie l’epoch en secondes par 1000 :

```logql
1000 * max by (dataset_value) (max_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_event_epoch"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Régler les dates

1. Type Instant, puis Exécuter.
2. Visualisation Stat ; affichage de chaque série, calcul Last not null.
3. Légende de la requête : `{{dataset_value}}`.
4. Choisir une unité Date & time / Date et heure, de préférence un affichage ISO/UTC explicite.
5. Vérifier que la valeur affichée correspond à une date source, pas à un nombre de millisecondes pris pour une durée.
6. Tester movies/incident : la date source précède l’émission d’environ dix minutes.
7. Revenir à All/All : les dates les plus récentes viennent normalement de recovery.
8. Facultativement tester From now / Depuis maintenant, observer que cette présentation vieillit, puis revenir à une date explicite pour le compte rendu.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P14 — Dernière date source observée — UTC`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 13.3 P15 — Complétude comparée des deux corpus

#### A. Ouvrir la visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum by (dataset_value) (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
/
sum by (dataset_value) (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

#### B. Afficher les ratios séparés

1. Type Instant, puis Exécuter.
2. Visualisation Bar gauge.
3. Orientation horizontale ; calcul Last not null.
4. Légende `{{dataset_value}}`.
5. Unit Percent (0.0–1.0), une ou deux décimales.
6. Minimum 0, maximum 1 si des bornes sont demandées dans le format ratio.
7. Vérifier access=100 % et movies=80 % sur toutes les phases.
8. Sélectionner phase=incident : access=100 %, movies=40 % ; revenir ensuite à All.

Un batch totalement absent n’est pas inventé par Loki : le ratio seul, calculé sur les summaries présents, ne remplace pas le manifeste externe ni la vérification des IDs.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P15 — Validées sur attendues par corpus`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 13.4 P16 — Tableau des six batches

#### A. Ajouter la requête de lignes

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

9. Type Range et limite 2000, puis Exécuter.
10. Sélectionner **Table** et inspecter le champ de ligne JSON dans l’aperçu.

#### B. Construire un tableau lisible

1. Transformations → Add transformation → Extract fields.
2. Source : le champ JSON, généralement `Line`. Format JSON ; remplacer les champs tout en conservant Time.
3. Si les résultats sont répartis en plusieurs tables/trames, ajouter **Merge series/tables / Fusionner séries et tables** et vérifier qu’on obtient toujours six lignes, pas un produit cartésien.
4. Ajouter Convert field type et convertir vers Numeric : `expected`, `attempted`, `accepted_count`, `rejected_count`, `missing_count`, `source_delay_seconds`.
5. Ajouter Filter fields by name ; garder `Time`, `phase`, `source_dataset`, `batch_id`, `expected`, `attempted`, `accepted_count`, `rejected_count`, `missing_count`, `source_delay_seconds`.
6. Si la table est maintenant unique, ajouter Organize fields pour placer les colonnes dans cet ordre et masquer seulement les champs non voulus.
7. Cliquer l’en-tête Time pour trier de façon croissante.
8. Agrandir la colonne `batch_id` en tirant la séparation d’en-tête ; ne pas supprimer l’ID nécessaire à l’investigation.
9. Pour colorer les anomalies, ajouter un override / remplacement par nom de champ pour `rejected_count`, puis un seuil pédagogique >0 et un mode de cellule colorée si disponible ; recommencer pour `missing_count`. Ne pas appliquer une couleur rouge à tous les nombres sans distinction.
10. Lire la ligne movies/incident : expected=5, attempted=4, accepted=2, rejected=2, missing=1, delay=600.
11. Ne pas joindre ensuite ce résumé à chaque record pour sommer les compteurs : cela pourrait répéter les mêmes totaux plusieurs fois.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P16 — Contrat et résultats par batch`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 14. Causes de rejet, durée de simulation et lecture des événements

### 14.1 P17 — Rejets par règle de qualité

#### A. Ajouter la nouvelle visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum by (reason) (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", reason="quality_reason", accepted_value="accepted"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| accepted_value="false"
[$__range]
))
```

#### B. Configurer les barres

1. Type Instant, puis Exécuter.
2. Visualisation Bar gauge ; orientation horizontale.
3. Légende de requête : `{{reason}}`.
4. Calcul Last not null ; unité None, zéro décimale.
5. Vérifier deux motifs : `title_missing`=1 et `duplicate_movie_id`=1.
6. Sur une sélection sans rejet, la requête peut ne renvoyer aucune série ; ne pas remplacer indistinctement tout No data par zéro sans expliquer le périmètre.
7. Ne pas confondre les 2 rejets parmi 29 tentatives avec 1 moins la complétude : la ligne manquante avant lecture n’est pas un rejet.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P17 — Rejets par règle — simulation`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 14.2 P18 — Histogramme du temps de génération des six batches

#### A. Ajouter les summaries

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

9. Type Range, limite de lignes 2000, puis Exécuter.

#### B. Ne garder que les six mesures

1. Transformations → Ajouter → Extract fields depuis le champ de ligne JSON ; format JSON, remplacer les champs.
2. Ajouter Convert field type : `processing_duration_ms` → Numeric.
3. Ajouter Filter fields by name et garder uniquement `processing_duration_ms`.
4. Lire la vue tabulaire : six valeurs sur All/All. Ne pas transformer `source_delay_seconds` en cette mesure : ce sont deux concepts distincts.
5. Choisir la visualisation Histogram.
6. Bucket size = 100 ms, offset = 0, puis adapter à l’étendue constatée si le graphique devient illisible.
7. Étiqueter clairement la valeur en millisecondes du générateur et la fréquence en nombre de batches.
8. Ne pas imposer une valeur exacte : la durée comprend les écritures et pauses, et varie selon l’exécution.

Cette distribution de six observations enseigne un geste ; elle ne suffit pas à conclure sur un percentile de production. Elle ne mesure pas la latence HTTP ou celle de Loki.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P18 — Temps du générateur par batch — pas HTTP`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 14.3 P19 — Panneau des logs d’investigation

#### A. Ajouter la visualisation de logs

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

#### B. Garder la preuve originale

1. Type Range ; limite 2000, puis Exécuter.
2. Choisir la visualisation **Logs**.
3. Activer l’affichage de l’heure et les détails des logs.
4. Choisir l’ordre croissant si proposé pour lire le déroulement ; activer le retour à la ligne pour les longs JSON.
5. Désactiver la déduplication pendant la validation. Ne pas supprimer des événements de l’affichage parce qu’ils se ressemblent.
6. Ne pas ajouter `line_format` avant les transformations que vous souhaiteriez appliquer au JSON ; ici garder les lignes originales.
7. Sur All/All, les filtres regex `.*` incluent aussi les heartbeats de source_dataset=control ; la population peut donc contenir 38 JSON, pas seulement les records.
8. Sélectionner movies puis incident : lire quatre records et leur résumé, dont les deux décisions de rejet.
9. Développer les lignes pour retrouver `event_id` et `batch_id`, puis revenir à All/All.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P19 — Logs du run — records, batches et contrôle`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 15. Ajouter trois lectures complémentaires

### 15.1 P21 — Somme des octets des sondes HTTP

#### A. Créer le panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| json byte_value="response_bytes"
| byte_value!=""
| unwrap byte_value
| __error__=""
[$__range]
))
```

#### B. Afficher le total

1. Type Instant, puis Exécuter.
2. Choisir Stat ; calcul Last not null.
3. Unit : bytes / octets.
4. Vérifier le total 43 284 octets sur All/All, calculé comme 3 × (128+512+1500+4096+8192).
5. Chaque phase access porte 14 428 octets. Avec dataset=movies, l’absence de mesures HTTP est normale.
6. Ne pas ajouter ce total à un compteur de films : les unités n’ont aucun rapport.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P21 — Octets des sondes HTTP — total de période`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 15.2 P22 — Débit de lignes par corpus

#### A. Ouvrir la visualisation

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum by (dataset_value) (rate(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[10s]
))
```

#### B. Configurer les courbes et leur unité

1. Type Range, intervalle minimum 10 s pour ce TP, puis Exécuter.
2. Visualisation Time series.
3. Légende `{{dataset_value}}`.
4. Choisir une unité d’opérations/lignes par seconde, par exemple ops/s, et un titre qui précise le sens « lignes/s ».
5. Autoriser des décimales : 5 lignes sur 10 s donnent environ 0,5 ligne/s, pas cinq secondes de durée.
6. Survoler un point et comparer à P07 dans la même fenêtre. Le taux est normalisé par la durée de fenêtre.
7. Ne pas sommer les points de débit pour obtenir les 29 records.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P22 — Débit de records par corpus — lignes/s sur 10 s`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

### 15.3 P23 — Décisions accepted par record

#### A. Ajouter le panneau

1. Dans Grafana, ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer **Edit / Modifier** si le dashboard n’est pas en édition.
3. Vérifier le run courant, la période absolue du scénario, `dataset=All` et `phase=All` pour le premier contrôle.
4. Cliquer **Add / Ajouter** puis **Visualization / Visualisation**, ou directement **Add visualization** selon le menu. Ne pas modifier le panneau précédent.
5. Choisir `Loki-Formation` dans la liste des sources pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir la variable `${loki_ds}` si elle est proposée ; sinon garder Loki-Formation et noter ce choix fixe.
7. Dans la requête A, sélectionner le mode **Code**, pas Builder.

8. Coller :

```logql
sum by (accepted_value) (count_over_time(
{job="atelier13bis",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", accepted_value="accepted"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[$__range]
))
```

#### B. Comparer records et compteurs de batch

1. Type Instant, puis Exécuter.
2. Visualisation Bar gauge horizontale.
3. Légende : `accepted={{accepted_value}}`.
4. Calcul Last not null ; unité None, zéro décimale.
5. Sur All/All, vérifier true=27 et false=2.
6. Comparer ces valeurs, issues des records arrivés, aux compteurs de batch P03/P04. Leur cohérence est un contrôle supplémentaire, pas un accusé de réception d’une application externe.
7. Les batchs et heartbeats ne possèdent pas le même rôle accepted ; ils sont exclus par `kind="record"`.

#### C. Enregistrer

1. Dans les options de panneau à droite, ouvrir **Panel options / Options du panneau**.
2. Dans Title / Titre, saisir `P23 — Décisions de validation sur les records reçus`.
3. Cliquer **Apply / Appliquer** pour revenir au dashboard ; si cette version utilise une autre action de retour conservant les changements, l’utiliser.
4. Sur le dashboard, maintenir le clic sur l’en-tête du nouveau panneau et le placer dans une zone libre. Ne pas le superposer à un autre panneau.
5. Tirer sa poignée du coin inférieur pour obtenir une taille lisible.
6. Cliquer **Save dashboard / Enregistrer le dashboard**, puis confirmer la sauvegarde et sa description si demandée.
7. Vérifier que les panneaux précédents sont toujours présents.

## 16. Ajouter le contexte et les limites : P00 et P20

### 16.1 P00 — Périmètre et consignes de lecture

1. Ouvrir le dashboard `[A13bis] Data Observability — Access et catalogue`.
2. Cliquer Edit puis Add visualization.
3. Dans le choix de source, choisir **Grafana / Built-in** si une source est demandée ; un panneau de texte ne doit pas exécuter une requête Loki.
4. Dans les visualisations, sélectionner **Text / Texte**.
5. Choisir le mode Markdown dans les options.
6. Saisir :

```markdown
### Périmètre du laboratoire
Références et scénario synthétiques, clairement identifiés.
Run : ${run}. Corpus : ${dataset}. Phase : ${phase}.
Les KPI de période utilisent Instant et une fenêtre couvrant la sélection.
Une ligne brute et sa représentation JSON ne sont pas deux événements métier distincts.
Les erreurs HTTP, les rejets de catalogue et les pertes de transport sont des notions séparées.
Aucune latence HTTP ni géolocalisation réelle n’est fournie.
```

7. Titre du panneau : `P00 — Périmètre et méthode`.
8. Appliquer, placer tout en haut par glisser de son en-tête, lui donner une grande largeur, puis enregistrer le dashboard.

### 16.2 P20 — Limites et horloges

1. Depuis le même dashboard en édition, ajouter une nouvelle visualisation, sans modifier P00.
2. Choisir Text, mode Markdown, sans requête Loki.
3. Saisir :

```markdown
### Lire les indicateurs correctement
Complétude de simulation = validées / attendues du contrat.
Les compteurs de batch ne prouvent pas l’import dans une base métier.
Le retard source a été mesuré à l’observation ; son maximum historique n’est pas un retard actuel.
Time Loki = collecte ; @timestamp JSON = émission ; event_time = date métier simulée.
Recovery 100 % ne signifie pas que les rejets et la référence manquante ont été rattrapés.
Les histogrammes et heatmaps reposent sur les observations individuelles reçues, sous réserve de limite de lignes.
```

4. Titre : `P20 — Définitions, couverture et limites`.
5. Appliquer et placer sous les logs, puis enregistrer le dashboard.

Vous avez maintenant 24 panneaux P00 à P23, dont les deux textes. Le comptage des panneaux ne dispense pas de vérifier leurs données.

## 17. Organiser, placer et sauvegarder le dashboard complet

### 17.1 Disposition proposée

```text
Variables : source Loki | run | corpus | phase
P00 Périmètre

P01 Observées | P02 Attendues | P03 Validées | P04 Rejetées | P05 Manquantes | P06 Complétude
P07 Chronologie | P08 Codes HTTP | P09 Part 5xx
P10 Histogramme tailles | P11 Heatmap tailles
P12 Heatmap retard | P13 Retard maximal | P14 Dernière date source
P15 Complétude corpus | P16 Table des batches
P17 Motifs de rejet | P18 Temps du générateur
P21 Octets HTTP | P22 Débit | P23 Décisions accepted
P19 Logs détaillés
P20 Limites
```

### 17.2 Manipuler la grille

1. Ouvrir le dashboard et cliquer Edit.
2. Repérer un panneau par son numéro Pxx.
3. Maintenir le clic sur son en-tête ou sa poignée de déplacement, le glisser vers la ligne souhaitée et relâcher lorsqu’une zone de placement apparaît.
4. Utiliser la poignée du coin inférieur pour agrandir ou réduire le panneau.
5. Donner davantage de largeur aux histogrammes, aux heatmaps et à la table des batches.
6. Ne pas chercher à tenir les 24 panneaux sur un seul écran au détriment des textes et axes.
7. Vérifier Run, All/All et les bornes du scénario.
8. Cliquer Save dashboard, confirmer et revenir à la liste des dashboards.
9. Rouvrir votre dashboard et vérifier que panneaux, variables et période sont conservés.

## 18. Construire le dashboard de détail et le lien depuis un batch

### 18.1 Créer un dashboard d’investigation indépendant

1. Ouvrir Dashboards → New dashboard.
2. Enregistrer sous `[A13bis] Investigation — événement ou batch`.
3. Créer dans Settings → Variables une variable Data source `loki_ds` de type Loki, choisissant Loki-Formation.
4. Ajouter une variable Text box `run`, valeur du run réel `__RUN__`.
5. Ajouter une variable Text box `event_id`, valeur vide pour commencer.
6. Revenir au dashboard, régler la période absolue du scénario et enregistrer.
7. Cliquer Add visualization et choisir Loki-Formation / `${loki_ds}`.
8. Mode Code ; coller :

```logql
{job=~"atelier13bis_raw|atelier13bis"} |= "${run}" |= "${event_id}"
```

9. Type Range, limite 2000, puis Exécuter.
10. Visualisation Logs ; afficher l’heure, les détails et le retour à la ligne ; déduplication désactivée.
11. Titre `Détail corrélé — JSON et sondes brutes`.
12. Appliquer puis enregistrer le dashboard.
13. Copier son URL, notamment le segment `/d/UID/nom`. Pour une création manuelle, l’UID peut différer de l’export de secours ; utiliser l’UID réel, pas celui du modèle par habitude.

### 18.2 Relier la table P16 au détail

1. Revenir au dashboard principal, ouvrir le menu du panneau P16 puis Edit.
2. Dans les options de champs à droite, ajouter un **Override / Remplacement** sur le champ nommé `batch_id`.
3. Ajouter la propriété **Data links / Liens de données**.
4. Cliquer Add link ; titre `Investiguer ce batch`.
5. Utiliser l’URL de votre dashboard de détail et y ajouter les paramètres suivants :

```text
/d/UID_REEL/nom?var-run=${run}&var-event_id=${__data.fields.batch_id}&from=${__from}&to=${__to}
```

6. Remplacer seulement le chemin UID/nom par celui copié. Les variables `${...}` restent interprétées par Grafana.
7. Confirmer le lien, appliquer P16 et enregistrer le dashboard principal.
8. Cliquer le batch movies/incident dans la table pour ouvrir le lien ; selon la cellule, choisir le lien dans son menu.
9. Vérifier la période transmise et le texte de batch_id dans la variable `event_id` du détail.
10. Lire les quatre records, le summary et les sondes CSV correspondantes si elles sont collectées dans la période. Un `batch_id` est le préfixe des IDs de ses records.

Partager un lien ne confère pas de droits. Il s’agit d’une corrélation par identifiant dans les lignes, pas d’un join automatique entre bases.

## 19. Vérifier les chiffres, les filtres et les requêtes exécutées

### 19.1 Grille attendue

| Corpus / phase | Attendues | Records observés | Validées | Rejetées | Manquantes | Complétude |
|---|---:|---:|---:|---:|---:|---:|
| All / All | 30 | 29 | 27 | 2 | 1 | 90 % |
| movies / All | 15 | 14 | 12 | 2 | 1 | 80 % |
| movies / incident | 5 | 4 | 2 | 2 | 1 | 40 % |
| movies / recovery | 5 | 5 | 5 | 0 | 0 | 100 % |
| access / incident | 5 | 5 | 5 | 0 | 0 | 100 % |

1. Choisir chaque combinaison dans les variables en haut du dashboard.
2. Attendre l’actualisation ou cliquer Refresh.
3. Comparer P01 à P06 à la ligne attendue et noter le résultat.
4. Sur access/incident, comparer la complétude 100 % et la part 5xx 40 % ; elles ne mesurent pas la même chose.
5. Revenir à All/All après les vérifications.

### 19.2 Inspecter un panneau

1. Ouvrir le menu `…` d’un Stat, par exemple P06.
2. Choisir Inspect / Inspecter puis l’onglet Query / Requête.
3. Examiner l’expression réellement transmise : les variables ont-elles été remplacées comme prévu ?
4. Vérifier les bornes, la source et le type Instant.
5. Ouvrir l’onglet Data / Données pour lire la valeur numérique avant formatage.
6. Fermer l’inspecteur sans modifier les données du run.

### 19.3 Contrôler par l’API, sans les variables de Grafana

Générer les exports et requêtes résolues après vérification de la livraison :

```bash
python3 construire_dashboard13bis.py \
  --manifest manifest-scenario13bis.json --reference reference13bis.json \
  --output-dir livrables13bis

END_REF=$(python3 -c 'import json; print(json.load(open("reference13bis.json"))["to_ns"])')
curl --fail-with-body -sS -G "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode "query=$(cat livrables13bis/requetes-api/06_completeness.logql)" \
  --data-urlencode "time=$END_REF" -o controle-completude13bis.json
python3 -m json.tool controle-completude13bis.json
```

Attendu : résultat vectoriel de valeur 0.9. Les fichiers API remplacent les variables par le run et une durée arrondie couvrant la période vérifiée. Ne pas compter le nombre de séries comme un nombre d’événements.

Pour une expression de lignes, utiliser `/query_range` avec les bornes de référence et une limite adaptée. Les résultats d’API et ceux de Grafana ne sont comparables qu’avec même source, mêmes filtres et mêmes bornes.

## 20. Investigation guidée, du signal à la preuve

1. Partir de All/All et noter les compteurs globaux et 90 %.
2. Sélectionner movies : 80 %. Identifier un corpus, pas encore une cause.
3. Sélectionner incident : 40 %, deux rejets, une référence manquante et retard maximal 600 s.
4. Lire la ligne movies/incident de P16.
5. Suivre son lien vers le détail et ouvrir les deux records rejetés.
6. Relever `quality_reason`, `source_reference` et `source_sha256`.
7. Vérifier que quatre records existent pour cinq références attendues : la manquante n’a pas un record rejeté caché.
8. Passer à recovery et constater 100 % pour cette phase seulement.
9. Revenir à toutes les phases : le bilan reste 80 % pour movies, car aucun backfill n’a été exécuté.
10. Examiner séparément les 503 access ; leur coexistence temporelle avec les rejets n’est pas une preuve de causalité.
11. Écrire une conclusion : faits, périmètre, hypothèse et preuve manquante.

## 21. Alerte Grafana-managed : option guidée, sans notification externe automatique

### 21.1 Définition de l’exercice

Sur les summaries movies des cinq dernières minutes : validées / attendues. Objectif pédagogique 95 %, pas SLO de production. La requête fournie dans `regle-alert-atelier13bis.logql` ne contient aucune variable de dashboard ni run fixé.

Le générateur s’arrête : une règle basée sur le temps courant ne rejoue pas la période historique affichée. Si le run a plus de cinq minutes, ne pas attendre un déclenchement historique.

### 21.2 Créer et tester sans envoyer de message externe

1. Vérifier avec le formateur que Grafana Alerting est disponible et que le compte possède les droits.
2. Ouvrir Alerting → Alert rules → New alert rule.
3. Nom : `[A13bis] Complétude movies de démonstration`.
4. Source Loki-Formation ; coller l’expression du fichier `regle-alert-atelier13bis.logql` dans A.
5. Vérifier que la requête ne contient pas `${run}` ou `$__range` : une règle n’a pas les variables du dashboard.
6. Utiliser une évaluation Instant si le formulaire le propose, ou une requête et une réduction Last adaptées à cette version.
7. Ajouter la condition de seuil : ratio inférieur à 0.95.
8. Choisir le dossier et le groupe d’évaluation du laboratoire. Pour un test, environ 30 s et pending nul si autorisé ; ce ne sont pas des réglages de production.
9. Configurer explicitement les états No data et Error selon le besoin du TP. Ne pas transformer une panne de source en « tout va bien ».
10. Ne pas configurer de notification externe ni de destinataire sans validation du formateur.
11. Prévisualiser l’expression. Si le scénario n’est plus dans la fenêtre, noter No data comme résultat cohérent.
12. Pour un vrai cycle, créer volontairement un nouveau run dans un nouveau dossier, puis l’observer dans le temps courant. Ne pas écraser les manifestes du premier run.
13. Lire l’historique de la règle ; l’incident peut rester dans la fenêtre après recovery.
14. Désactiver la règle de laboratoire à la fin de la séance si elle n’a pas vocation à continuer.

Plusieurs runs dans cinq minutes peuvent contribuer au ratio de cette règle sans filtre de run. Ce périmètre est volontairement à discuter : pour isoler un environnement réel, il faut un label ou un inventaire adapté, pas copier un identifiant de test dans une règle permanente.

## 22. Extension facultative : les mêmes événements dans Elasticsearch

Le parcours Loki/Grafana ci-dessus est complet sans cette extension.

1. Sur une infrastructure ES préparée et sécurisée, publier la copie exacte produite par le scénario :

```bash
sudo python3 publier_elasticsearch13.py \
  --events scenario13bis/produced_events.jsonl --mapping mapping-atelier13-events.json \
  --url https://localhost:9200 --ca "$HOME/.config/elastic-lab/http_ca.crt" \
  --index atelier13bis-events --username elastic
```

2. Saisir le secret au prompt, ne pas l’inscrire dans le support ; utiliser un compte adapté au laboratoire.
3. Dans Console Elasticsearch, contrôler le run réel :

```http
GET atelier13bis-events/_count
{
  "query": {"bool": {"filter": [
    {"term": {"run_id": "__RUN__"}},
    {"term": {"a13_kind": "record"}},
    {"term": {"accepted": true}}
  ]}}
}
```

4. Attendu : 27 records validés ; la projection complète contient 38 événements, pas 27.
5. Ajouter éventuellement une source Elasticsearch de lecture dans Grafana avec CA et droits dédiés, sans garder elastic comme compte permanent.
6. Copier un `event_id` dans ES et le chercher dans le dashboard Loki de détail avec la même période.
7. Ne pas présenter cette corrélation comme un join serveur. Une réindexation ES sur le même `_id` remplace un document ; une réémission de ligne Loki n’est pas un upsert équivalent.

## 23. Exports de secours : après l’apprentissage, pas à la place des clics

Le constructeur génère deux JSON : `livrables13bis/dashboard13bis-grafana.json` et `livrables13bis/dashboard13bis-investigation.json`, plus 24 expressions d’API résolues.

1. Ouvrir Dashboards → New → Import si l’on utilise la correction de secours.
2. Importer le détail puis le principal.
3. Vérifier la source `${loki_ds}`, le run et la période de référence.
4. Les UID des exports sont fixes pour ce laboratoire : si un dashboard existe déjà avec cet UID, ne pas l’écraser sans accord. Importer une copie ou ajuster l’UID.
5. Ouvrir les histogrammes/heatmaps et vérifier les champs `Line`/`Time` et les transformations sur cette version de Grafana.
6. Refaire les valeurs de référence. Un JSON valide syntaxiquement n’est pas une preuve d’import fonctionnel.

Les modèles ne sont pas conçus pour imposer une langue d’interface. Les constructions manuelles précédentes restent la procédure principale.

## 24. Dépannage opérationnel

| Symptôme | Contrôle concret |
|---|---|
| Source A11 absente | Ne pas chercher A11 : utiliser les chemins dédiés `/var/log/formation13bis` créés ici |
| Port 12346 occupé | Ne pas stopper un autre service au hasard ; choisir un autre port avec le formateur et adapter l’unité |
| L’installateur refuse une ressource déjà présente | Inspecter l’installation existante/partielle, ne pas écraser fichiers et positions |
| Les fichiers existent mais Loki est vide | Droits du compte alloy, service dédié actif, destination et journal d’erreur |
| Normalisation 28 versus scénario 67 | Deux lots, deux unités de comptage ; isoler normalization_id ou run_id |
| Une seule copie normalisée arrive | Vérifier séparément les cibles JSON et logfmt et leur lecture |
| Explore vide avant parser | Période, source, labels et marqueur avant de changer le parser |
| Valeur extraite introuvable dans les accolades | Champ JSON de contenu, à parser après le sélecteur, pas label d’ingestion |
| Le titre avec virgule est tronqué | Éviter le découpage CSV naïf ; lire la vue structurée préparée par csv.DictReader |
| Erreur numérique | Champ présent, valeur convertible, puis `__error__` après conversion/unwrap |
| KPI faux malgré une belle couleur | Instant/Range, run, All/All, bornes, définition du dénominateur |
| Histogramme compte aussi des dates | Filter fields by name : une seule colonne numérique pertinente |
| Organize fields refuse le résultat | Plusieurs trames ; filtrer par nom pour toutes, fusion contrôlée pour la table si nécessaire |
| Heatmap vide | Time conservé et temporel, valeur numérique, calcul à partir des données, limite de lignes |
| Seules des moyennes sont visibles | Revenir aux observations individuelles si la question porte sur leur distribution |
| Recovery 100 % mais bilan mauvais | Aucun backfill ; lire toutes les phases |
| Retard max reste 600 s | Maximum historique, pas retard actuel |
| No data pour HTTP avec movies | Pas de dénominateur HTTP sur ce corpus, résultat normal |
| Alerte ancienne silencieuse | La règle évalue maintenant, pas la plage historique du dashboard |

## 25. Conservation, arrêt et livrables

### 25.1 Conserver sans polluer les anciens ateliers

1. Enregistrer et rouvrir les deux dashboards.
2. Exporter leur JSON depuis les fonctions de partage/export disponibles, avec les droits requis.
3. Conserver `preparation13bis.json`, `manifest-scenario13bis.json`, les deux références, les requêtes et les réponses de contrôle.
4. Les copies originales fournies sont dans `originaux/` pour comparaison ; ne pas les lancer à la place des scripts adaptés.
5. Les journaux de référence synthétiques restent identifiés comme tels. Les sondes ajoutées aux copies de travail ne deviennent pas des données originales d’un catalogue public.
6. Un export de dashboard ne contient ni les logs Loki, ni les documents Elasticsearch, ni les secrets de source.

Pour arrêter uniquement le collecteur de TP en fin de séance, si autorisé :

```bash
sudo systemctl stop alloy-atelier13bis
```

Cette action ne supprime pas les données Loki ni les positions. Pour reprendre, redémarrer ce service sans vider son état. Ne pas utiliser `rm -rf` pour retrouver artificiellement les compteurs d’un premier run.

### 25.2 Critères de réussite

- Préparation autonome et deux formats livrés : 14 + 14 événements normalisés vérifiés.
- Scénario : 67 représentations, dont 38 JSON et 29 records, IDs et batches vérifiés.
- Plusieurs requêtes Explore expliquées, incluant mauvais parser, conversion, champ manquant et négatif métier.
- Totaux 30/29/27/2/1 et ratio 90 % reproduits.
- Au moins un histogramme et une heatmap fondés sur les observations individuelles, pas des moyennes.
- Dashboard principal de 24 panneaux lisibles, détail ouvert par un batch et référence API contrôlée.
- Définitions correctes des horloges, filtres et limites ; aucune causalité inventée.

### 25.3 Validation du pack, pas certification du serveur

Les scripts adaptés sont testés localement sur les références autonomes : normalisation, échappement CSV/JSON/logfmt, scénario, IDs, distributions et exports. Les vérificateurs HTTP sont testés avec des réponses simulées. Le JSON et la syntaxe Bash/Python sont contrôlés.

Aucun Loki/Alloy/Grafana réel n’a été lancé ni interrogé pendant la fabrication du pack. Les 60 LogQL n’ont pas été compilés par un serveur réel. Le formateur doit répéter `alloy validate`, la collecte, le requêtage et les transformations sur ses versions avant la séance. Le rapport `validation_locale13bis.json` distingue ces limites des tests réellement exécutés.
