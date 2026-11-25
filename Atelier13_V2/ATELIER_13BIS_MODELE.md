# Atelier 13 bis — Corpus access complet : Loki, Explore et dashboard Grafana guidé

Révision des deux supports fournis : le fichier `access_log_actualise` remplace les cinq références Apache comme source principale. Les requêtes, résultats attendus, variables et panneaux ont été réécrits ; il ne s’agit pas d’un simple remplacement de `A13B_SEED`. Les anciens documents limitaient la préparation à cinq références puis sélectionnaient le run synthétique dans les panneaux. [file:228][file:229]

## 0. Vous avez déjà commencé : reprendre sans réimporter

C’est le parcours recommandé pour votre séance en cours.

1. Conserver les fichiers, les données Loki et l’état de lecture Alloy. Ne pas relancer le générateur de scénario et ne pas supprimer les positions.
2. Sauvegarder vos deux anciens documents sous un autre nom, puis placer les fichiers de cette révision dans le dossier du pack. Le ZIP est une révision du pack précédent, pas une réinstallation de Grafana/Loki/Alloy. Les scripts de configuration et d’installation Alloy déjà fournis restent nécessaires pour une première installation.
3. Ouvrir un terminal dans `~/Atelier13_bis`, comme lors de votre vérification précédente. Tous les chemins relatifs suivants partent du dossier du pack.
4. Exécuter le contrôle local du fichier, sans toucher à la collecte :

```bash
python3 analyser_access13bis.py --source sources13bis/access_log \
  --output reference_access_locale.json
cat preparation13bis.json
```

Si la sortie existe déjà, choisir un autre nom ; ne pas l’écraser sans la lire.

5. Vérifier que `access` dans `preparation13bis.json` correspond bien au fichier complet. Pour le fichier joint analysé : 102 972. Si le manifeste indique encore 5, arrêter : le bon fichier a été copié trop tard ou une autre normalisation est sélectionnée. Ne pas remplacer en place un fichier déjà suivi par Alloy ; faire préparer une nouvelle source/version avec le formateur.
6. Remplacer l’ancien `verifier_normalisation13bis.py` par la version incluse dans cette révision, puis lancer :

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_normalisation13bis.py \
  --manifest preparation13bis.json --corpus corpus13bis \
  --source sources13bis/access_log \
  --output reference-normalisation13bis-corpus.json
```

Ce vérificateur utilise des agrégations côté Loki au lieu de télécharger 2000 lignes. Il contrôle les volumes total et access séparément dans JSON et logfmt. Il ne prétend plus vérifier chaque ID en ligne. Une perte et un doublon peuvent se compenser : égalité des comptes n’est pas preuve d’identité événement par événement. [web:186]

7. Après succès, générer les documents et expressions de la séance :

```bash
python3 personnaliser_support_corpus13bis.py \
  --manifest preparation13bis.json \
  --reference reference-normalisation13bis-corpus.json \
  --output-dir supports13bis-corpus-complet
```

8. Ouvrir `supports13bis-corpus-complet/ATELIER_13BIS_PERSONNALISE.md` et le guide personnalisé du même dossier. Les marqueurs `__NID__` et `__DUREE__` y sont remplacés.
9. Passer directement à la section 6 pour Explore, puis à la section 8 pour créer le nouveau dashboard. Les sections de préparation/installation suivantes servent aux nouvelles séances, pas à rejouer votre chargement actuel.

## 1. Périmètre, infrastructure et données réellement disponibles

| Élément | Révision corpus complet |
|---|---|
| Principal | Toutes les lignes du fichier access fourni |
| Source des panneaux | Copie JSON normalisée : `job="atelier13bis",format="json"`, normalization_id exact et source_dataset=access |
| Brut | `job="atelier13bis_raw",dataset="access"`, pour apprendre et inspecter |
| logfmt | Même lot de normalisation, pour comparer les formats ; jamais ajouté au compteur JSON |
| Hors dashboard principal | Films, quatre contrôles et scénario normal/incident/recovery |
| Grafana | 24 panneaux dont deux textes, guide de 60 requêtes, JSON de secours facultatif |
| Prérequis | Ubuntu natif, Loki/Grafana opérationnels, binaire Alloy et utilisateur/groupe alloy |
| Langue d’interface | Boutons anglais expliqués en français ; version Grafana non communiquée |

Le type de panneau d’une valeur unique est Stat dans Grafana. On ne cherche pas le menu « Indicateur » de Kibana. Dans Grafana on saisit LogQL puis configure le graphique ; le glisser-déposer sert surtout à la disposition du dashboard, pas à déposer des champs comme dans Lens.

### 1.1 Référence du fichier joint, calculée localement

| Mesure | Référence |
|---|---:|
| Lignes non vides et préfixes Apache reconnus | 102 972 |
| 2xx / 3xx / 4xx / 5xx | 91 145 / 8 909 / 2 670 / 248 |
| Tailles connues / absentes | 67 987 / 34 985 |
| Méthodes non extraites | 267 |
| Somme des tailles connues | 1 293 498 000 octets |
| Moyenne sur tailles connues | 19 025,66667 octets |
| P95 local par interpolation linéaire | 58 043 octets |
| Maximum connu | 2 017 208 octets |
| IP distinctes dans le fichier | 4 540 |
| Chemins distincts, paramètres inclus | 30 610 |

SHA-256 : `09693e55a8bcb1dedd3659c23833aa06a4ad2c8fb5f46b7fd2d9b93ee941c815`. Le rapport joint contient les détails. Les chiffres ne certifient pas une livraison sur votre serveur et ne doivent pas être appliqués à un fichier différent. [file:208]

### 1.2 Deux horloges à ne pas confondre

Le texte Apache du fichier s’étend du 22 novembre 2026 à 18:51:30 UTC au 22 novembre 2026 à 19:01:30 UTC. La configuration du TP n’applique pas de `stage.timestamp` : les données déjà chargées ont donc une date Loki de collecte.

La période du dashboard doit inclure la collecte sur votre VM, même si elle a eu lieu le 25 novembre. Les courbes temporelles de cette révision représentent le chargement/collecte, pas le trafic historique reconstruit du serveur. Un import rapide peut produire une seule pointe ou une seule colonne de heatmap. Ne pas inventer trois phases pour remplir les graphiques.

### 1.3 Limites sémantiques

- Le tiret source pour la taille signifie « taille non renseignée », pas zéro octet.
- Les 267 requêtes non séparées en méthode/chemin/protocole restent des documents access et conservent `request_line` et `raw_line`.
- Un 500 est une réponse HTTP, pas une décision de rejet de catalogue.
- Une IP n’est pas une personne ; `::1` ne doit pas être géolocalisée.
- Aucune durée HTTP n’est disponible. Ne pas appeler la taille, la date ou le débit « latence ».
- Le volume du fichier n’est pas une mesure de visiteurs ou sessions uniques.

## 2. Fichiers et scripts : ce qui change

| Élément | Action |
|---|---|
| Deux Markdown et LIRE_AVANT | Remplacés par les versions corpus complet |
| `verifier_normalisation13bis.py` | Remplacé : agrégations de volumes, sans plafond de logs de 2000 |
| `preparer_corpus_access13bis.py` | Nouveau : copie intégralement le fichier fourni, sans prélèvement de cinq lignes |
| `analyser_access13bis.py` | Nouveau : calcule la référence locale du fichier réellement utilisé |
| `personnaliser_support_corpus13bis.py` | Nouveau : n’utilise ni manifeste de scénario ni phase synthétique |
| `requetes_dashboard_corpus13bis.json` | Nouvelle bibliothèque des calculs des panneaux |
| `requetes_explore_corpus13bis.json` | Nouvelle bibliothèque des 60 recherches et références |
| `construire_dashboard_corpus13bis.py` | Nouveau constructeur de secours du dashboard complet |
| Anciens constructeurs/scénario | Conservés uniquement pour l’extension synthétique ; ne plus les lancer pour ce dashboard |
| Configuration/installation Alloy | Reprise du pack initial ; ne pas la réinstaller si le service est déjà actif |

## 3. Nouvelle séance seulement : préparer toutes les lignes

Ne pas refaire cette section si la section 0 confirme votre chargement existant.

### A. Vérifier le dossier et l’infrastructure

```bash
pwd
ls preparer_corpus_access13bis.py normaliser_sources13bis.py
command -v alloy
id alloy
curl --fail-with-body -fsS http://127.0.0.1:3100/ready
curl --fail-with-body -fsS http://127.0.0.1:3000/api/health
```

Le parcours vise Loki local mono-tenant sans authentification sur la boucle locale. Si vous utilisez TLS, un proxy ou un tenant, préparer configuration et clients avec les paramètres appropriés avant la séance ; ne pas désactiver la vérification TLS.

### B. Copier le corpus complet, sans modifier le script

Dans le terminal, depuis le dossier du pack :

```bash
python3 preparer_corpus_access13bis.py \
  --access access_log_actualise --output-dir sources13bis
cat sources13bis/sources-manifest.json
wc -l sources13bis/access_log
head -n 5 sources13bis/access_log
```

Ce nouveau script remplace la combinaison « créer cinq références puis écraser access_log puis corriger le manifeste ». Il écrit lui-même le bon compte et l’empreinte. Il refuse un dossier existant pour protéger la séance en cours. Les cinq films restent seulement pour les exercices complémentaires et la compatibilité de l’ancien installateur.

Ne pas mettre cette commande à l’intérieur d’un `.py`. Les blocs `bash` de ce support se copient dans le terminal ; les blocs LogQL dans Grafana.

### C. Normaliser et conserver le rapport

```bash
set -o pipefail
python3 normaliser_sources13bis.py \
  --access sources13bis/access_log --movies sources13bis/movies.csv \
  --output-dir corpus13bis --with-controls | tee preparation13bis.json
cat preparation13bis.json
```

Pour le fichier joint, 102972 + 5 + 4 = 102981 événements par format. Ces copies JSON et logfmt ne sont pas deux lots métier différents. Le snapshot de normalisation ne suit pas automatiquement les nouvelles lignes ajoutées au brut.

## 4. Première installation seulement : collecter sans modifier les anciens ateliers

1. Reprendre `config-atelier13bis.alloy`, `installer_collecte13bis.sh` et `alloy-atelier13bis.service.in` du pack initial, déjà détaillés dans la notice d’origine. Ils lisent les quatre fichiers dédiés et utilisent leur propre état de lecture. [file:230]
2. Lire la destination Loki et vérifier que le port local 12346 du service dédié est libre.
3. Si aucune installation 13 bis n’existe encore :

```bash
sudo bash installer_collecte13bis.sh sources13bis corpus13bis
sudo systemctl status alloy-atelier13bis --no-pager
sudo journalctl -u alloy-atelier13bis -n 80 --no-pager
```

4. Ne pas écraser les fichiers sous `/var/log/formation13bis` si le service les suit déjà. Ne pas supprimer `/var/lib/alloy-atelier13bis`.
5. Lancer le nouveau contrôle puis la personnalisation indiqués en section 0, étapes 6 et 7.

Une erreur 429, une entrée trop ancienne ou un refus de flux est à lire dans les logs du collecteur ; changer de requête ne répare pas le transport.

## 5. Comprendre le contrôle de livraison corrigé

Le vérificateur lit le manifeste de préparation, pas le manifeste des sources et pas celui du scénario. Il compare les volumes dans quatre périmètres : tout le lot JSON, access JSON, tout le lot logfmt, access logfmt.

| Contrôle pour ce fichier, avec cinq films et quatre contrôles | Attendu |
|---|---:|
| JSON total normalisé | 102 981 |
| JSON access | 102 972 |
| logfmt total normalisé | 102 981 |
| logfmt access | 102 972 |

Les événements ajoutés par le scénario ne possèdent pas le normalization_id de ce snapshot ; les filtres exacts de la révision les excluent. En revanche le brut peut contenir les sondes : il ne doit pas être comparé aveuglément au snapshot JSON.

La référence contient `validation_kind=aggregate_counts_only` et `ids_checked_in_loki=false`. C’est volontaire : ne pas conserver l’ancienne affirmation « tous les IDs en ligne vérifiés » alors que le contrôle a changé.

Si le début automatique dépasse les limites temporelles autorisées par Loki, fournir `--start-utc` avec une date UTC précédant la collecte, mais ne pas enlever une partie du chargement pour atteindre artificiellement le bon compte. La borne doit rester cohérente avec le lot.

## 6. Grafana Explore : voir les données avant de créer les panneaux

### A. Vérifier la source de données

1. Ouvrir Grafana et se connecter avec le compte du TP.
2. Dans Connections → Data sources, ouvrir Loki-Formation. Si elle n’existe pas, Add new data source → Loki, nom Loki-Formation.
3. URL : `http://127.0.0.1:3100` pour les services natifs sur la même VM ; pas `/push`.
4. Cliquer Save & test. Pour une installation conteneurisée, localhost doit être adapté par le formateur.

### B. Voir le brut

1. Ouvrir Explore / Explorer dans la navigation.
2. Choisir Loki-Formation dans le sélecteur de source.
3. Cliquer Code plutôt que Builder.
4. Dans la requête A, coller :

```logql
{job="atelier13bis_raw",dataset="access"}
```

5. Régler la période absolue couvrant la collecte sur votre VM.
6. Choisir Range ; limiter l’affichage à 500 ou 2000 pour examiner le texte sans essayer de télécharger tout le fichier.
7. Cliquer Run query. Développer une ligne et repérer ses labels et son texte Apache.
8. Retirer la déduplication d’affichage lors des contrôles.

### C. Voir la bonne population JSON

Dans le support personnalisé, le marqueur est déjà résolu. Remplacer la requête A par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status="500"
```

1. Conserver la période de référence et le mode Range.
2. Exécuter et ouvrir une ligne. Le fichier comporte 248 réponses 500 sur sa population complète.
3. Lire `raw_line`, `apache_time`, `request_line`, `bytes` éventuel et `client_ip`.
4. Retirer temporairement le filtre 500 pour retrouver le corpus ; ne pas remplacer n_id par un run synthétique.

## 7. Guide des 60 requêtes : nouvelle lecture

Ouvrir le guide personnalisé généré à côté de cet atelier. Les 60 manipulations ont été réécrites sur les labels/champs réellement disponibles. Les expressions statistiques sont évaluées côté Loki, indépendamment du plafond d’affichage des logs. [web:186]

Avant de dessiner, réaliser au minimum E09, E12, E19, E21, E37, E41, E42 et E45. Expliquer pourquoi 267 méthodes non extraites et 34985 tailles absentes ne sont pas des logs perdus.

Le préfiltre de ligne sur le NID accélère la sélection ; le filtre exact après parsing contrôle le lot. Les extractions ciblées évitent d’ajouter `record_id`, `raw_line` ou des milliers de chemins aux labels intermédiaires des calculs. [web:188]

## 8. Créer un nouveau dashboard et seulement les variables utiles

Ne pas modifier l’ancien dashboard synthétique en renommant quelques tuiles. Créer un nouvel objet pour éviter de mélanger anciens calculs et nouvelles valeurs.

### A. Créer et régler le dashboard

1. Dashboards → New → New dashboard.
2. Enregistrer sous `[A13bis] Access complet — diagnostic Loki`.
3. Ouvrir Settings / Paramètres, choisir UTC pour l’affichage des dates, puis enregistrer les paramètres.
4. Dans le sélecteur de temps en haut à droite, choisir la période absolue de la référence de normalisation, pas celle de `reference13bis.json` du scénario.
5. Appliquer la période et vérifier l’absence de filtre temporaire global.

### B. Variable de source

1. Settings → Variables → Add variable.
2. Name : `loki_ds`. Label : `Source Loki`. Type : Data source.
3. Type de source : Loki ; choisir Loki-Formation comme source courante.
4. Confirmer, revenir au dashboard et enregistrer.

### C. Variable de lot normalisé

1. Settings → Variables → Add variable.
2. Name : `nid`. Label : `Lot access normalisé`. Type : Text box.
3. Valeur : `__NID__` dans le support personnalisé, donc l’identifiant réel de `preparation13bis.json`.
4. Ne pas ajouter de guillemets ni d’espace à la valeur.
5. Confirmer, revenir au dashboard et enregistrer.

Les requêtes des panneaux utilisent `${nid}` ; Grafana le remplace à l’exécution. Il n’y a plus de variable run, phase ou dataset à créer pour ce dashboard. Les filtres métier supplémentaires se testeront dans Explore, sans changer le dénominateur des ratios globaux par accident.

## 9. Construire les 24 panneaux, chacun jusqu’à la sauvegarde

Les valeurs de référence ci-dessous supposent le fichier joint, le bon NID, aucune restriction supplémentaire et toute la période de collecte. Une fenêtre plus courte ne doit pas être comparée au total du fichier. Les chiffres calculés localement sont des références à contrôler, pas des résultats annoncés comme déjà mesurés sur votre Loki.

### 9.1 P01 — Access logs du lot — total

Objectif et limite : Tous les access logs normalisés, même si la méthode ou la taille est absente.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 102 972.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P01 — Access logs du lot — total`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.2 P02 — Réponses 2xx

Objectif et limite : Inclut 91 074 réponses 200 et 71 réponses 206.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 200
| v_status < 300
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 91 145.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P02 — Réponses 2xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.3 P03 — Réponses 4xx

Objectif et limite : Compter les codes 400 à 499, pas des rejets métier de catalogue.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 2 670.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P03 — Réponses 4xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.4 P04 — Réponses 5xx

Objectif et limite : Dans le fichier joint, les réponses de cette famille ont le code 500, pas 503.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 248.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P04 — Réponses 5xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.5 P05 — Part de réponses 4xx

Objectif et limite : Numérateur 2670 ; dénominateur 102972. Ne pas filtrer globalement le dashboard sur les erreurs.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
(
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[$__range]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
))))
) / (
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
))
)
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Décimales : 3. Ne pas multiplier la formule par 100 : le format pourcentage s’en charge.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 2,592937886 %.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P05 — Part de réponses 4xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.6 P06 — Part de réponses 5xx

Objectif et limite : Ce ratio porte sur toutes les lignes access du lot, pas seulement les tailles ou méthodes connues.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
(
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[$__range]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
))))
) / (
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
))
)
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Décimales : 3. Ne pas multiplier la formule par 100 : le format pourcentage s’en charge.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 0,240842171 %.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P06 — Part de réponses 5xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.7 P07 — Volume par fenêtre de collecte — 1 min

Objectif et limite : Axe Time de collecte. Un chargement en bloc peut produire un seul pic ; ce n’est pas le trafic historique du 22 novembre.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[1m]
))
```

#### B. Configurer le calcul et l’affichage

1. Type = Range, puis régler un intervalle minimum de 1s pour cette première lecture ; la fenêtre de comptage reste 1m.
2. Cliquer Run queries.
3. Choisir Time series / Série temporelle.
4. Garder une unité numérique simple et une légende lisible ; la valeur est un compte par fenêtre de 1 minute.
5. Survoler la pointe de collecte et lire l’heure Loki.
6. Si le chargement est bref, dézoomer ou ajuster la période de la référence plutôt que régénérer des logs pour remplir la courbe.
7. Ne pas sommer les points pour retrouver 102972 : le pas et l’alignement des fenêtres doivent être pris en compte.

#### C. Contrôler la valeur et le périmètre

Référence : Une ou plusieurs fenêtres non vides autour du chargement.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P07 — Volume par fenêtre de collecte — 1 min`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.8 P08 — Réponses par code HTTP

Objectif et limite : Les onze séries décrivent les codes réellement présents dans le corpus.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_status) (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 100
| v_status < 600
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Choisir le type Instant puis cliquer Run queries.
2. Choisir Bar gauge / Jauge à barres dans le sélecteur de visualisation.
3. Orientation : horizontale. Calcul : Last not null.
4. Dans Legend / Légende de la requête, saisir `{{v_status}}`.
5. Unité None, zéro décimale ; conserver les libellés de série lisibles.
6. Agrandir l’aperçu si un libellé est tronqué ; les chemins restent consultables dans les détails.
7. Comparer les valeurs et le périmètre au contrôle ci-dessous. Ne pas trier une sélection bornée en la présentant comme un top global recalculé.

#### C. Contrôler la valeur et le périmètre

Référence : 200=91074 ; 206=71 ; 301=7833 ; 302=20 ; 304=1056 ; 400=29 ; 403=88 ; 404=2298 ; 405=3 ; 408=252 ; 500=248.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P08 — Réponses par code HTTP`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.9 P09 — Méthodes reconnues

Objectif et limite : La somme vaut 102705. Les 267 méthodes non extraites restent dans P01 et ne sont pas remplacées par GET.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_method) (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="${nid}"
| src="access"
| v_method!=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Choisir le type Instant puis cliquer Run queries.
2. Choisir Bar gauge / Jauge à barres dans le sélecteur de visualisation.
3. Orientation : horizontale. Calcul : Last not null.
4. Dans Legend / Légende de la requête, saisir `{{v_method}}`.
5. Unité None, zéro décimale ; conserver les libellés de série lisibles.
6. Agrandir l’aperçu si un libellé est tronqué ; les chemins restent consultables dans les détails.
7. Comparer les valeurs et le périmètre au contrôle ci-dessous. Ne pas trier une sélection bornée en la présentant comme un top global recalculé.

#### C. Contrôler la valeur et le périmètre

Référence : GET=61858 ; POST=36988 ; OPTIONS=3221 ; HEAD=635 ; PUT=3.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P09 — Méthodes reconnues`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.10 P10 — Somme des tailles connues — octets

Objectif et limite : Somme des tailles de réponse connues, pas taille de stockage des logs dans Loki.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour la vérification exacte en octets ; le titre donne l’unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.
9. Après vérification du nombre exact, un affichage bytes/IEC peut abréger en KiB ou MiB. Une valeur affichée abrégée n’est pas une nouvelle mesure : vérifier les octets bruts dans Inspect → Data.

#### C. Contrôler la valeur et le périmètre

Référence : 1 293 498 000 octets.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P10 — Somme des tailles connues — octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.11 P11 — Moyenne des tailles connues — octets

Objectif et limite : Le dénominateur est 67987 valeurs connues, pas 102972 lignes. Le tiret Apache ne devient pas zéro.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
(sum (sum_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))) / (sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[$__range]
)))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour la vérification exacte en octets ; le titre donne l’unité.
6. Décimales : 2. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.
9. Après vérification du nombre exact, un affichage bytes/IEC peut abréger en KiB ou MiB. Une valeur affichée abrégée n’est pas une nouvelle mesure : vérifier les octets bruts dans Inspect → Data.

#### C. Contrôler la valeur et le périmètre

Référence : 19 025,66667 octets.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P11 — Moyenne des tailles connues — octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.12 P12 — P95 global des tailles connues — octets

Objectif et limite : Le regroupement by() porte sur la population complète des tailles du lot. Ce n’est ni une latence ni le maximum de P95 locaux.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
quantile_over_time(0.95, 
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
) by ()
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour la vérification exacte en octets ; le titre donne l’unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.
9. Après vérification du nombre exact, un affichage bytes/IEC peut abréger en KiB ou MiB. Une valeur affichée abrégée n’est pas une nouvelle mesure : vérifier les octets bruts dans Inspect → Data.

#### C. Contrôler la valeur et le périmètre

Référence : Référence locale linéaire : 58 043 octets ; comparer à Loki.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P12 — P95 global des tailles connues — octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.13 P13 — Taille maximale connue — octets

Objectif et limite : Le maximum est calculé côté Loki sur la population connue, pas estimé depuis un échantillon affiché.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
max (max_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour la vérification exacte en octets ; le titre donne l’unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.
9. Après vérification du nombre exact, un affichage bytes/IEC peut abréger en KiB ou MiB. Une valeur affichée abrégée n’est pas une nouvelle mesure : vérifier les octets bruts dans Inspect → Data.

#### C. Contrôler la valeur et le périmètre

Référence : 2 017 208 octets.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P13 — Taille maximale connue — octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.14 P14 — Lignes sans taille renseignée

Objectif et limite : Le normaliseur n’ajoute pas bytes quand le champ Apache vaut le tiret.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes=""
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir None / Sans unité.
6. Décimales : 0. Conserver les nombres lisibles sans abréger pendant le contrôle.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 34 985.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P14 — Lignes sans taille renseignée`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.15 P15 — Part des lignes avec taille connue

Objectif et limite : 67987/102972. Indicateur de renseignement du champ, pas de complétude de livraison.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[$__range]
))) / (sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
[$__range]
)))
```

#### B. Configurer le calcul et l’affichage

1. Dans les options de la requête A, choisir Type = Instant. Ne pas laisser Both ou Range pour ce total/statistique de période.
2. Cliquer Run queries et attendre la réponse.
3. Dans le sélecteur de visualisation à droite, choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle. La requête renvoie déjà une valeur de période ; ne pas sommer une courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Décimales : 2. Ne pas multiplier la formule par 100 : le format pourcentage s’en charge.
7. Désactiver la petite courbe de tendance si elle suggère une série que cette requête Instant ne renvoie pas.
8. Garder No data visible ; ne pas convertir automatiquement toute absence en zéro vert.

#### C. Contrôler la valeur et le périmètre

Référence : 66.024745 %.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P15 — Part des lignes avec taille connue`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.16 P16 — Dix IP suivies — sélection documentée

Objectif et limite : Liste bornée issue de l’analyse locale du fichier joint. Ce n’est pas une découverte exhaustive des IP de n’importe quel fichier.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_ip) (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_ip="client_ip"
| __error__=""
| n_id="${nid}"
| src="access"
| v_ip=~"54\\.210\\.20\\.202|::1|148\\.251\\.21\\.227|81\\.22\\.242\\.55|46\\.101\\.48\\.46|104\\.236\\.254\\.104|199\\.21\\.99\\.207|192\\.187\\.98\\.42|148\\.251\\.184\\.139|104\\.154\\.198\\.228"
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Choisir le type Instant puis cliquer Run queries.
2. Choisir Bar gauge / Jauge à barres dans le sélecteur de visualisation.
3. Orientation : horizontale. Calcul : Last not null.
4. Dans Legend / Légende de la requête, saisir `{{v_ip}}`.
5. Unité None, zéro décimale ; conserver les libellés de série lisibles.
6. Agrandir l’aperçu si un libellé est tronqué ; les chemins restent consultables dans les détails.
7. Comparer les valeurs et le périmètre au contrôle ci-dessous. Ne pas trier une sélection bornée en la présentant comme un top global recalculé.

#### C. Contrôler la valeur et le périmètre

Référence : 54.210.20.202=34469 ; ::1=3219 ; autres références dans le rapport local.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P16 — Dix IP suivies — sélection documentée`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.17 P17 — Cinq chemins suivis

Objectif et limite : Ces chemins sont sélectionnés explicitement. Les paramètres éventuels font partie du champ path ; on ne calcule pas un top global sur 30610 chemins.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_path) (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="${nid}"
| src="access"
| v_path=~"/wp\\-login\\.php|/xmlrpc\\.php|/|/feed/|/favicon\\.ico"
[$__range]
))
```

#### B. Configurer le calcul et l’affichage

1. Choisir le type Instant puis cliquer Run queries.
2. Choisir Bar gauge / Jauge à barres dans le sélecteur de visualisation.
3. Orientation : horizontale. Calcul : Last not null.
4. Dans Legend / Légende de la requête, saisir `{{v_path}}`.
5. Unité None, zéro décimale ; conserver les libellés de série lisibles.
6. Agrandir l’aperçu si un libellé est tronqué ; les chemins restent consultables dans les détails.
7. Comparer les valeurs et le périmètre au contrôle ci-dessous. Ne pas trier une sélection bornée en la présentant comme un top global recalculé.

#### C. Contrôler la valeur et le périmètre

Référence : /wp-login.php=7902 ; /xmlrpc.php=5329 ; /=4019 ; /feed/=2816 ; /favicon.ico=1891.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P17 — Cinq chemins suivis`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.18 P18 — Distribution des tailles connues — classes disjointes

Objectif et limite : Les cinq fréquences sont calculées sur tout le corpus. Elles totalisent 67987, pas 102972. Les classes ont des largeurs inégales et sont affichées comme catégories.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

Pour A, puis pour les requêtes B, C, D, E, utiliser respectivement les cinq blocs suivants :

Requête A — libellé `1–999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 1
| v_bytes < 1000
| __error__=""
[$__range]
))
```

Requête B — libellé `1 000–9 999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 1000
| v_bytes < 10000
| __error__=""
[$__range]
))
```

Requête C — libellé `10 000–99 999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 10000
| v_bytes < 100000
| __error__=""
[$__range]
))
```

Requête D — libellé `100 000–999 999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 100000
| v_bytes < 1000000
| __error__=""
[$__range]
))
```

Requête E — libellé `≥ 1 000 000` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
[$__range]
))
```

#### B. Ajouter et configurer les cinq requêtes

1. Après A, cliquer Add query / Ajouter une requête pour B, puis C, D et E. Choisir Code pour chacune et coller son propre bloc.
2. Régler chacune des cinq requêtes en Instant, pas Both ou Range.
3. Dans la légende de chaque requête, saisir le libellé de sa classe indiqué au-dessus du code.
4. Cliquer Run queries / Exécuter les requêtes.
5. Choisir Bar gauge, orientation horizontale, calcul Last not null et format numérique sans unité, zéro décimale.
6. Ne pas choisir un histogramme à classes de largeur uniforme : ces cinq catégories n’ont pas la même largeur.
7. Comparer les cinq nombres au tableau de référence et vérifier leur somme 67987.
8. Ne pas ajouter les 34985 tailles absentes à la première classe : elles ne valent pas zéro.


#### C. Contrôler la valeur et le périmètre

Référence : 16792 ; 21193 ; 28868 ; 1121 ; 13.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P18 — Distribution des tailles connues — classes disjointes`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.19 P19 — Détail des erreurs HTTP — extrait affiché

Objectif et limite : Une table d’investigation n’est pas un compteur de livraison. Les méthodes ou tailles peuvent être absentes.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="${nid}"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 600
| __error__=""
```

#### B. Configurer le calcul et l’affichage

1. Type = Range, limite des logs = 500, puis Run queries.
2. Choisir Table et inspecter le champ qui contient le JSON, généralement Line.
3. Ouvrir Transformations → Add transformation → Extract fields.
4. Source : le champ de ligne JSON, format JSON ; activer Replace all fields et Keep Time.
5. Si plusieurs trames sont renvoyées, utiliser Merge series/tables avant Organize fields et vérifier qu’aucune ligne n’est multipliée par une jointure.
6. Ajouter Filter fields by name ; garder Time, source_line, client_ip, method, path, request_line, status, bytes et apache_time.
7. Ajouter Convert field type pour status et bytes vers Numeric si nécessaire. Une valeur bytes absente doit rester absente.
8. Quand la table est unique, utiliser Organize fields pour placer les colonnes dans cet ordre. Agrandir les colonnes de texte.
9. Cliquer l’en-tête Time pour choisir un tri compréhensible ; rappeler qu’il s’agit de collecte. Le champ apache_time conserve la date écrite.
10. Garder request_line lisible pour les requêtes atypiques, sans inventer une méthode ou un chemin.

#### C. Contrôler la valeur et le périmètre

Référence : Population complète : 2918 erreurs ; la table affiche au plus 500 lignes.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P19 — Détail des erreurs HTTP — extrait affiché`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.20 P20 — Histogramme des tailles — échantillon affiché 500 max

Objectif et limite : Panneau pédagogique de transformation client, explicitement échantillonné. P18 porte la distribution exhaustive ; ne pas comparer leurs fréquences comme des totaux identiques.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
```

#### B. Configurer le calcul et l’affichage

1. Type = Range, limite de logs = 500, puis Run queries. Ne pas tenter de rendre le panneau exhaustif en demandant arbitrairement 100000 lignes au navigateur.
2. Ouvrir la vue tabulaire et repérer le champ de texte JSON, généralement Line.
3. Transformations → Add transformation → Extract fields ; Source = ce champ, format JSON, Replace all fields et Keep Time activés.
4. Ajouter Convert field type : bytes → Numeric.
5. Ajouter Filter fields by name ; garder uniquement bytes.
6. Vérifier dans l’aperçu le nombre réellement renvoyé, au maximum 500 ; tous les événements sélectionnés ont bytes renseigné. Les colonnes status, source_line et dates epoch ne font pas partie de la distribution.
7. Choisir Histogram ; Bucket size = 10000 octets, offset = 0.
8. N’activer Combine series que pour réunir ce même champ bytes, jamais d’autres champs numériques.
9. La fréquence est le nombre d’observations de l’échantillon. Garder cette fréquence sans unité de taille ; le titre indique que l’axe des valeurs est en octets.
10. Vérifier que la somme des fréquences correspond au nombre d’observations renvoyées, pas au total 67987. Pour la distribution complète, lire P18.

#### C. Contrôler la valeur et le périmètre

Référence : Jusqu’à 500 tailles connues affichées, pas les 67987 de la population.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P20 — Histogramme des tailles — échantillon affiché 500 max`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.21 P21 — Heatmap des tailles — échantillon 500 max et collecte

Objectif et limite : Le temps est celui de Loki. Un import bref peut produire une seule colonne ; ne pas inventer un historique source ou des phases.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="${nid}"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
```

#### B. Configurer le calcul et l’affichage

1. Type = Range, limite de logs = 500, puis Run queries. Ne pas tenter de rendre le panneau exhaustif en demandant arbitrairement 100000 lignes au navigateur.
2. Ouvrir la vue tabulaire et repérer le champ de texte JSON, généralement Line.
3. Transformations → Add transformation → Extract fields ; Source = ce champ, format JSON, Replace all fields et Keep Time activés.
4. Ajouter Convert field type : bytes → Numeric.
5. Ajouter Filter fields by name ; garder uniquement Time et bytes.
6. Vérifier dans l’aperçu le nombre réellement renvoyé, au maximum 500 ; tous les événements sélectionnés ont bytes renseigné. Les colonnes status, source_line et dates epoch ne font pas partie de la distribution.
7. Choisir Heatmap ; Calculate from data = Yes, car ces lignes ne sont pas des classes préagrégées.
8. X Bucket : Size = 5s ; Y Bucket : Linear, Size = 10000 octets.
9. Garder l’infobulle et la légende : X = collecte, Y = taille connue, couleur = fréquence dans l’échantillon.
10. Un import rapide peut n’occuper qu’une colonne temporelle. Ne pas l’interpréter comme une absence de trafic historique ni comme trois phases de simulation.

#### C. Contrôler la valeur et le périmètre

Référence : Jusqu’à 500 observations, réparties selon leur temps de collecte.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P21 — Heatmap des tailles — échantillon 500 max et collecte`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

### 9.22 P22 — Access JSON — preuves et champs sources, extrait

Objectif et limite : Conserver le JSON original pour développer raw_line, request_line, status et apache_time. Aucun line_format n’est nécessaire.

#### A. Ajouter un nouveau panneau

1. Ouvrir `[A13bis] Access complet — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si nécessaire.
3. Vérifier la période complète de la référence, le NID réel et l’absence de filtre global temporaire.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou Add visualization selon la version. Ne pas ouvrir la modification de la tuile précédente.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans le sélecteur de source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter ce choix fixe.
7. Dans la requête A, choisir Code, sélectionner le contenu initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json"} |= "${nid}"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="${nid}"
| src="access"
```

#### B. Configurer le calcul et l’affichage

1. Type = Range ; limite = 500 ; cliquer Run queries.
2. Choisir Logs dans les visualisations.
3. Afficher l’heure, les détails, et le retour à la ligne pour le JSON long.
4. Désactiver la déduplication pour l’investigation ; choisir un ordre temporel et le documenter.
5. Développer une entrée, lire raw_line et la date apache_time, puis comparer au champ status.
6. Conserver la ligne JSON originale ; aucun formatage n’est nécessaire pour ce panneau de preuve.
7. Noter la limite : ce panneau n’est pas un compteur exhaustif des 102972 logs.

#### C. Contrôler la valeur et le périmètre

Référence : Des logs du NID choisi, dans la limite de 500 lignes affichées.

Si la référence ne correspond pas, vérifier NID, période, Instant/Range, champs absents et limite d’affichage avant de conclure à une perte. Le rapport local n’est pas une mesure déjà exécutée sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P22 — Access JSON — preuves et champs sources, extrait`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si cette version propose une autre action de retour conservant le panneau, l’utiliser.
3. Sur le dashboard, maintenir le clic sur l’en-tête ou la poignée de déplacement du nouveau panneau, le placer dans un espace libre puis relâcher.
4. Tirer la poignée du coin inférieur pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux précédents sont toujours présents et n’ont pas été remplacés.

## 10. Ajouter les deux textes P00 et P23

### 10.1 P00 — Périmètre, lot et définitions

1. Ouvrir le nouveau dashboard en édition.
2. Cliquer Add visualization et choisir Text ; si une source est demandée pour un panneau sans données, choisir Grafana / Built-in.
3. Mode Markdown. Coller :

```markdown
### Diagnostic du corpus access complet
Lot : ${nid}. Les graphiques principaux utilisent uniquement source_dataset=access.
Les copies JSON, logfmt et brutes ne sont pas additionnées.
Time Loki est la date de collecte ; apache_time est la date écrite dans la source.
Les ratios d’erreur portent sur tous les access logs du lot dans la période.
Les tailles absentes ne valent pas zéro ; les statistiques de taille utilisent seulement les valeurs connues.
```

4. Titre : `P00 — Périmètre et méthode`.
5. Appliquer, faire glisser le panneau en haut du dashboard et lui donner une grande largeur.
6. Enregistrer le dashboard.

### 10.2 P23 — Limites et couverture

1. Toujours dans le nouveau dashboard, cliquer Add visualization pour un nouveau panneau.
2. Choisir Text puis Markdown.
3. Coller :

```markdown
### Limites de lecture
Le contrôle de livraison compare des volumes, pas tous les IDs en ligne.
Les 267 méthodes et 34985 tailles absentes sont conservées dans le total du fichier de référence.
Les IP et chemins suivis sont des sélections bornées documentées, pas une découverte globale recalculée.
La distribution de classes P18 est exhaustive sur les tailles connues.
P19/P20/P21/P22 sont des vues d’investigation ou des échantillons plafonnés ; leurs lignes ne sont pas le total du corpus.
Aucune latence HTTP, session unique, causalité d’incident ou position géographique de personne n’est prouvée.
```

4. Adapter les nombres si votre fichier diffère de la référence jointe.
5. Titre : `P23 — Couverture et limites`.
6. Appliquer, placer sous les logs par glisser de son en-tête, puis enregistrer.

## 11. Assembler et rouvrir le dashboard

```text
Variables : source Loki | NID du corpus
P00 Contexte
P01 Total | P02 2xx | P03 4xx | P04 5xx | P05 Part 4xx | P06 Part 5xx
P07 Collecte temporelle | P08 Codes HTTP | P09 Méthodes reconnues
P10 Somme des tailles | P11 Moyenne | P12 P95 | P13 Maximum
P14 Tailles absentes | P15 Couverture de taille
P16 IP suivies | P17 Chemins suivis
P18 Classes de taille sur toute la population connue
P19 Table des erreurs
P20 Histogramme échantillonné | P21 Heatmap échantillonnée
P22 Logs JSON détaillés
P23 Limites
```

1. En édition, déplacer chaque panneau en maintenant le clic sur son en-tête ou sa poignée.
2. Redimensionner par le coin inférieur ; ne pas réduire tous les tableaux pour tenir sur un seul écran.
3. Agrandir les chemins, la table des erreurs et le panneau Logs.
4. Vérifier le NID et la période ; enregistrer puis revenir à la liste des dashboards.
5. Rouvrir `[A13bis] Access complet — diagnostic Loki` et vérifier la présence des 24 panneaux.
6. Sur les panneaux temporels, consulter le pas réellement exécuté dans Inspect → Query. Un pas trop grand peut manquer un bref chargement placé près de la borne de fin : resserrer autour de la collecte, demander un pas plus fin, ou avancer la borne de fin à une heure déjà atteinte. Ne pas réingérer le fichier pour fabriquer une courbe.

## 12. Contrôler les résultats et l’API sans télécharger les 102972 lignes

### A. Inspecter un calcul

1. Ouvrir le menu `…` de P01 puis Inspect / Inspecter.
2. Dans Query, vérifier le remplacement de `${nid}`, la période et Type Instant.
3. Dans Data, lire le nombre brut avant abréviation ou format pourcentage.
4. Recommencer avec P11 : comparer la somme des tailles et le nombre de valeurs connues ; ne pas diviser par le total des logs.
5. Fermer l’inspecteur sans changer les données.

### B. Vérifier une expression par curl

Le personnaliseur a créé des fichiers sans variables Grafana. Utiliser le contexte du nouveau contrôle :

```bash
export LOKI_URL='http://127.0.0.1:3100'
END_REF=$(python3 -c 'import json; print(json.load(open("reference-normalisation13bis-corpus.json"))["to_ns"])')
curl --fail-with-body -sS -G "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode "query=$(cat supports13bis-corpus-complet/requetes-api/total.logql)" \
  --data-urlencode "time=$END_REF" -o controle_total_access.json
python3 -m json.tool controle_total_access.json
```

Le résultat doit être un vector de valeur 102972 pour ce fichier et ce lot complet. Le nombre de séries du vector n’est pas le nombre de logs ; lire sa valeur. Le contrôle ne dépend pas du plafond 2000 d’une requête de lignes.

### C. Lire les écarts sans les masquer

| Écart | Diagnostic |
|---|---|
| Total 5 | Mauvaise normalisation ou préparation limitée à cinq références |
| Total 29 / compteurs 30 et 27 | Anciennes requêtes de scénario utilisées |
| Résultat 0 ou No data | NID, période et label de flux avant toute nouvelle préparation |
| Compte supérieur au manifeste | Relecture/doublons ou mauvais périmètre ; ne pas déclarer la collecte conforme |
| Seulement 2000 lignes affichées | Liste de logs plafonnée, pas mesure de l’ingestion |
| Somme des méthodes 102705 | 267 méthodes non extraites, résultat cohérent |
| Somme des classes de taille 67987 | Taille absente sur 34985 lignes, résultat cohérent |
| Courbe très courte ou une pointe | Time de collecte en bloc, pas la chronologie source reconstruite |
| Trop de séries | Extraire moins de champs, utiliser les listes bornées ; ne pas lancer un top par 30610 chemins en aveugle |

## 13. Investigation guidée sur des données présentes

1. Lire P01, P03 et P04 ; noter le lot et la période.
2. Dans Explore, exécuter E12 pour les 248 réponses 500.
3. Ouvrir plusieurs lignes et noter les chemins et IP observés, sans leur attribuer une cause.
4. Exécuter E26 pour le chemin /wp-login.php et E27 pour /xmlrpc.php ; comparer le filtre exact au filtre de texte brut E04.
5. Exécuter E24 pour l’IP dominante du fichier et lire les lignes sources, méthodes et statuts.
6. Examiner E19 : conserver les requêtes atypiques dans le diagnostic au lieu de les effacer.
7. Examiner E21 : expliquer pourquoi un tiret de taille n’implique pas une perte de transport.
8. Écrire une conclusion : fait mesuré, périmètre, hypothèse éventuelle et information manquante.
9. Ne pas conclure « attaque confirmée » à partir du seul nom d’un chemin ou d’une IP.

## 14. Correction de secours et anciens scripts

Après l’apprentissage manuel, on peut générer un JSON local de secours :

```bash
python3 construire_dashboard_corpus13bis.py \
  --manifest preparation13bis.json \
  --reference reference-normalisation13bis-corpus.json \
  --output-dir livrables13bis-corpus
```

Le fichier principal est `dashboard13bis-access-corpus.json`. Import manuel : Dashboards → New → Import, charger le JSON, choisir la source dans loki_ds, vérifier nid et période. Ne pas écraser un dashboard utilisé sans accord ; l’UID de secours est distinct de celui du scénario.

Ce constructeur n’envoie rien à l’API Grafana et ne charge aucun log. Le JSON de secours est contrôlé structurellement, pas importé pendant cette rédaction. Vérifier les transformations Line/Time dans votre version.

Ne plus utiliser `construire_dashboard13bis.py`, `construire_exploration13bis.py` et l’ancien personnaliseur pour ce parcours principal : ils ciblent le run et les variables du scénario. La nouvelle notice donne les remplacements.

## 15. Compléments séparés : contrôles, films et scénario

Le contenu pédagogique de l’atelier 11 sur C_VALID/C_BAD/C_MISSING/C_NEGATIVE reste pertinent, mais ces quatre contrôles ne sont pas des accès HTTP. Pour les voir, utiliser le NID du lot et `source_dataset=controls` ; ne pas filtrer src=access. Le logfmt est une seconde représentation et non de nouveaux accès.

Le scénario normal/incident/recovery, les objectifs de complétude 30/29/27/2/1, le retard de 600 s, l’alerte de complétude catalogue et la projection ES des 38 événements restent des exercices optionnels distincts. Ils ne sont plus des prérequis du dashboard access et ne doivent pas être recyclés comme mesures sur ce fichier.

Si le scénario a déjà écrit des sondes dans le brut, les requêtes JSON de cette révision isolent le snapshot normalisé par son NID. Ne pas essayer de « nettoyer » le brut en le tronquant sous un lecteur actif.

## 16. Livrables et portée de la validation

Remettre les deux documents personnalisés, les références locale et Loki, la grille de panneaux complétée, une réponse API de total et des captures après réouverture du dashboard. Conserver source et empreinte ; l’export Grafana ne contient pas les logs.

Ce fichier joint a été analysé intégralement et les nombres ont été recalculés localement. Les nouveaux scripts sont testés localement et leurs vérifications HTTP avec des réponses simulées. Les expressions sont vérifiées structurellement et documentées ; elles n’ont pas été exécutées sur votre instance Loki. Les clics et l’import du dashboard ne sont pas présentés comme validés sur votre version de Grafana. [file:208][web:188][web:186][web:240]
