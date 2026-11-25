# Atelier 13 bis — Charger les access logs dans Loki et construire un dashboard Grafana

## 1. Objectifs et livrables

Cet atelier utilise intégralement le fichier `donnees/access_log_actualise`. Le participant prépare trois représentations des mêmes lignes, les collecte dans Loki avec Alloy, vérifie leur arrivée, explore les champs avec LogQL dans Grafana, puis construit un dashboard complet panneau par panneau.

| Élément | Contenu |
|---|---|
| Données principales | 102972 lignes Apache du fichier fourni |
| Représentations | Apache brut, JSON et logfmt, une ligne par événement source dans chaque format |
| Collecteur | Service dédié alloy-atelier13bis-access |
| Exploration | 60 requêtes avec procédure de saisie, lecture et résultats attendus |
| Dashboard | 24 panneaux : 22 visualisations de données et 2 textes |
| Méthode | Préparer → collecter → vérifier → explorer → construire → organiser → investiguer |
| Prérequis | Ubuntu natif, Python 3, Loki, Grafana, binaire Alloy et compte/groupe système alloy |
| Durée indicative | 1,5 à 2 jours pour le parcours complet avec un groupe débutant |
| Livrables | Référence de collecte, requêtes, dashboard enregistré et rouvert, preuve API et note d’investigation |

### 1.1 Lire les consignes de manipulation

- Les commandes dans les blocs bash s’exécutent dans le terminal Linux, pas dans un fichier Python.
- Les blocs LogQL se saisissent dans Grafana Explore ou dans la requête d’un panneau.
- Les boutons anglais sont accompagnés de leur rôle français. La version Grafana du laboratoire doit être confirmée par le formateur ; certaines traductions et positions peuvent varier.
- Stat est le type Grafana d’un indicateur numérique. Les zones de dépôt et menus de Kibana ne sont pas ceux de Grafana.
- Pour déplacer un panneau : maintenir le clic sur sa poignée ou son en-tête, déplacer, relâcher. Pour le redimensionner : tirer le coin inférieur.
- Revenir au dashboard ne dispense pas d’enregistrer le dashboard.

### 1.2 Les résultats de référence

| Mesure sur le fichier fourni | Valeur |
|---|---:|
| Lignes non vides / préfixes Apache reconnus | 102972 / 102972 |
| Réponses 2xx / 3xx / 4xx / 5xx | 91145 / 8909 / 2670 / 248 |
| Tailles connues / absentes | 67987 / 34985 |
| Méthodes non extraites | 267 |
| Somme des tailles connues | 1293498000 octets |
| Moyenne des tailles connues | 19025,66667 octets |
| P95 local par interpolation linéaire | 58043 octets |
| Taille maximale connue | 2017208 octets |
| IP distinctes | 4540 |
| Chemins distincts, paramètres inclus | 30610 |

L’empreinte SHA-256 du fichier fourni est `09693e55a8bcb1dedd3659c23833aa06a4ad2c8fb5f46b7fd2d9b93ee941c815`. Le script recalcule les références du fichier qu’il prépare. Les nombres ne sont pas à imposer à un fichier différent.

### 1.3 Trois notions à garder distinctes

1. Une ligne de source a trois représentations : brut, JSON et logfmt. Ne pas additionner ces copies comme des accès différents.
2. Un champ de contenu devient exploitable par un parser à la requête ; il n’est pas automatiquement un label d’ingestion.
3. Une valeur absente n’est pas zéro. Le tiret Apache de taille produit un champ bytes absent ; 267 requêtes ne sont pas séparées en méthode/chemin/protocole mais restent conservées dans le total.

Le fichier ne contient pas de mesure de durée HTTP. Aucune taille, date ou vitesse de chargement ne doit être nommée latence. Une IP n’est pas une personne et un chemin évocateur ne prouve pas une attaque.

## 2. Ouvrir le dossier et vérifier les services

### A. Extraire le dossier

1. Extraire le ZIP sur la VM ou y transférer le dossier complet.
2. Ouvrir un terminal dans le dossier `Atelier_13bis` contenant les scripts.
3. Exécuter :

```bash
pwd
ls ATELIER_13BIS.md preparer_sources13bis.py installer_collecte13bis.sh
ls -lh donnees/access_log_actualise
python3 --version
```

Le fichier access est déjà dans le dossier donnees ; ne pas le renommer ni le remplacer par un fichier de cinq exemples.

### B. Vérifier les composants

```bash
command -v alloy
alloy --version
id alloy
getent group alloy
sudo systemctl status grafana-server --no-pager
curl --fail-with-body -sS http://127.0.0.1:3100/ready
curl --fail-with-body -sS http://127.0.0.1:3000/api/health
sudo ss -ltnp | grep -E ':(3000|3100|12347)\b'
```

Le collecteur de l’atelier utilisera 12347 sur l’interface locale ; ce port doit être libre. Les services Loki/Grafana et le binaire Alloy sont des prérequis de la VM ; le pack ne télécharge pas ces serveurs.

La configuration vise Loki mono-tenant local sans authentification sur 127.0.0.1:3100. Pour un déploiement distant/authentifié/multi-tenant, le formateur prépare URL, certificats, secrets et tenant dans le collecteur et le client de contrôle avant la séance. Ne pas désactiver TLS pour contourner une erreur.

### C. Accéder à Grafana

Depuis le poste participant, utiliser l’accès autorisé à Grafana. Si un tunnel SSH est nécessaire :

```bash
ssh -N -L 3000:127.0.0.1:3000 utilisateur@IP_PUBLIQUE_VM
```

Garder ce terminal ouvert et ouvrir http://localhost:3000 dans le navigateur. Se connecter avec le compte du TP ; ne pas activer l’accès anonyme pour éviter un contrôle de droits.

## 3. Préparer toutes les lignes et les références

### A. Exécuter le script de préparation

Depuis le terminal dans le dossier du pack :

```bash
python3 preparer_sources13bis.py \
  --source donnees/access_log_actualise \
  --output-dir preparation13bis
```

Le script lit toutes les lignes non vides, sans limite de cinq références. Il ne publie rien dans Loki. Un dossier de sortie déjà présent est refusé pour éviter l’écrasement d’une préparation.

### B. Lire les sorties

```bash
cat preparation13bis/manifest.json
cat preparation13bis/reference_source.json
wc -l preparation13bis/access_log preparation13bis/events.jsonl preparation13bis/events.logfmt
head -n 2 preparation13bis/events.jsonl
```

Attendu : 102972 lignes par fichier. Le manifeste contient le label de lot, le nombre attendu et l’empreinte. La référence contient les comptes HTTP, les valeurs absentes et les statistiques.

| Sortie | Rôle |
|---|---|
| access_log | Lignes Apache pour la collecte brute |
| events.jsonl | Un objet JSON par ligne source, avec les champs extraits |
| events.logfmt | Même population, valeurs scalaires citées correctement |
| manifest.json | Identifiant de lot, quantités et paramètres de préparation |
| reference_source.json | Références de calcul locales sur la source |

Le JSON conserve raw_line, request_line, apache_time, source_line et record_id. Le champ metadata est un objet ; il n’est pas transformé implicitement en tableau logfmt. Les caractères spéciaux du texte source sont échappés, pas découpés à la main.

### C. Comprendre le lot et les horloges

Le lot identifie cette préparation entière, pas chaque ligne. Il est ajouté comme label d’ingestion par Alloy. Les IP, chemins, record_id et textes complets ne sont pas promus en labels de stockage.

La date écrite dans le fichier va du 22 novembre 2026 à 18:51:30 UTC au 22 novembre 2026 à 19:01:30 UTC. Le timestamp Loki du TP est celui de collecte, car aucun stage.timestamp n’est appliqué.

La période Grafana doit inclure la collecte sur la VM. Les courbes montrent le chargement du fichier dans le laboratoire ; elles ne reconstruisent pas automatiquement le trafic historique du serveur. Un chargement rapide peut produire un seul pic.

## 4. Configurer Alloy et charger les logs dans Loki

### A. Lire les fichiers fournis

1. Ouvrir `config13bis.alloy.in` dans un éditeur, sans effacer son contenu.
2. Repérer les cibles des fichiers brut, JSON et logfmt, puis le writer Loki.
3. Repérer le marqueur `__LOT__`. L’installateur le remplace ; ne pas saisir manuellement un autre lot.
4. Repérer tail_from_end=false : le contenu existant est lu quand aucune position n’est enregistrée.
5. Ouvrir `alloy-atelier13bis-access.service.in` : le binaire, les chemins de configuration/état et le port local sont propres au service du TP.

| Représentation | Labels de sélection |
|---|---|
| Brut | job=atelier13bis_raw, dataset=access, format=raw, lot=valeur du manifeste |
| JSON | job=atelier13bis, format=json, lot=valeur du manifeste |
| logfmt | job=atelier13bis, format=logfmt, lot=valeur du manifeste |

### B. Installer et démarrer la collecte

```bash
sudo bash installer_collecte13bis.sh preparation13bis
```

L’installateur vérifie les comptes locaux et le port, copie les fichiers avec des permissions adaptées, génère la configuration réelle et l’unité systemd, valide le fichier avec Alloy, puis démarre le service.

Les ressources déjà présentes sont refusées : ne pas supprimer un stockage ou tronquer un fichier suivi pour contourner cette protection. En cas de validation interrompue, inspecter les ressources créées avec le formateur avant de reprendre les étapes manquantes.

### C. Vérifier le service et les accès

```bash
sudo systemctl status alloy-atelier13bis-access --no-pager
sudo journalctl -u alloy-atelier13bis-access -n 80 --no-pager
sudo -u alloy test -r /var/log/atelier13bis-access/access_log
sudo -u alloy test -r /var/log/atelier13bis-access/events.jsonl
sudo -u alloy test -r /var/log/atelier13bis-access/events.logfmt
```

Le writer envoie des lots de taille limitée et réessaie les erreurs 429 selon sa configuration. Un autre refus HTTP doit être diagnostiqué dans le journal ; le simple état actif du service ne prouve pas la livraison de toutes les lignes.

## 5. Vérifier la livraison et générer les supports de séance

### A. Compter côté Loki, sans télécharger tout le fichier

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_loki13bis.py \
  --manifest preparation13bis/manifest.json \
  --output reference13bis.json
```

Le script attend jusqu’à dix minutes, affiche la progression et compare le nombre de lignes de chaque représentation. Il vérifie aussi la répartition des codes du flux JSON par rapport à la source. Une requête de compte n’est pas limitée à 2000 logs téléchargés.

Attendu pour le lot : raw=102972, json=102972, logfmt=102972. Cela représente trois copies des mêmes accès et non trois fois plus de requêtes HTTP.

Le contrôle compare volumes et distribution HTTP ; il ne prétend pas vérifier en ligne l’identité de chaque record_id. Une perte et un doublon peuvent se compenser dans un compte. Conserver cette limite dans le compte rendu.

### B. Examiner la référence

```bash
cat reference13bis.json
```

Relever lot, from_utc et to_utc. Ces bornes encadrent la préparation/collecte du lot ; elles ne sont pas la date Apache écrite dans la source.

Si le contrôle échoue, lire le journal Alloy, les refus Loki et les permissions. Ne pas augmenter la limite de la liste Grafana comme solution à une erreur de transport.

### C. Générer les documents et requêtes adaptés au lot

```bash
python3 generer_livrables13bis.py \
  --manifest preparation13bis/manifest.json \
  --reference reference13bis.json \
  --output-dir livrables13bis
```

Le script produit les documents personnalisés, les fichiers LogQL d’Explore et de contrôle API et un JSON de dashboard de secours. Il ne publie pas automatiquement dans Grafana.

Ouvrir ensuite `livrables13bis/ATELIER_13BIS_PERSONNALISE.md` et `livrables13bis/GUIDE_60_REQUETES_EXPLORE_PERSONNALISE.md`. Le présent support reste le parcours principal ; les versions personnalisées contiennent le lot et les bornes réels au lieu des marqueurs.

## 6. Configurer Grafana et explorer les premières lignes

### A. Ajouter la source Loki

1. Ouvrir Grafana, se connecter et ouvrir Connections → Data sources / Sources de données.
2. Si Loki-Formation existe, l’ouvrir et vérifier sa configuration ; sinon Add new data source → Loki.
3. Nom : Loki-Formation.
4. URL : http://127.0.0.1:3100 pour les services natifs de la même VM. Ne pas mettre /loki/api/v1/push.
5. Cliquer Save & test et lire la réponse. Si Grafana est conteneurisé, faire adapter l’URL serveur par le formateur.

### B. Voir le brut dans Explore

1. Cliquer Explore / Explorer dans la navigation.
2. Choisir Loki-Formation en haut de la requête.
3. Cliquer Code plutôt que Builder.
4. Dans la requête A, coller le bloc suivant depuis le support personnalisé :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"}
```

5. Dans le sélecteur temporel, choisir une période absolue avec from_utc/to_utc de reference13bis.json, puis appliquer.
6. Type Range, limite d’affichage 500, puis Run query / Exécuter.
7. Développer une ligne et lire job, lot, format et son texte Apache.
8. Ne pas comparer le nombre de lignes affichées au total 102972 : la liste est volontairement limitée.

### C. Filtrer le statut 500 dans le JSON

Remplacer A par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status="500"
```

1. Conserver la période de collecte et le mode Range.
2. Cliquer Run query.
3. Ouvrir plusieurs lignes : le fichier comporte 248 réponses 500 sur sa population complète.
4. Lire bytes éventuel, client_ip, raw_line et apache_time. Ces champs ne sont pas tous des labels d’ingestion.
5. Poursuivre avec les 60 fiches du guide personnalisé. Faire au minimum E09, E12, E19, E21, E37, E41 et E42 avant le dashboard.

## 7. Créer le dashboard et ses deux variables

### A. Créer et enregistrer le dashboard

1. Dans la navigation, cliquer Dashboards.
2. Cliquer New → New dashboard.
3. Enregistrer sous `[A13bis] Access logs — diagnostic Loki` dans le dossier autorisé du laboratoire.
4. Ouvrir Settings / Paramètres et choisir UTC pour l’affichage temporel, puis conserver les paramètres.
5. Régler la période absolue sur from_utc/to_utc de reference13bis.json et appliquer.

### B. Variable de source

1. Settings → Variables → Add variable.
2. Name : loki_ds ; Label : Source Loki.
3. Type : Data source ; type de source recherché : Loki.
4. Choisir Loki-Formation comme valeur courante, confirmer la variable puis revenir au dashboard.
5. Enregistrer le dashboard.

### C. Variable de lot

1. Retourner dans Settings → Variables → Add variable.
2. Name : lot ; Label : Lot access.
3. Type : Text box.
4. Valeur : `__LOT__` dans le document personnalisé, donc le lot réel du manifeste, sans guillemets ajoutés.
5. Confirmer, revenir au dashboard et enregistrer.

Les requêtes de panneau utilisent `${lot}` : Grafana le remplace par la valeur de la variable. Une variable n’applique pas un filtre magique ; chaque requête la référence dans le sélecteur de flux.

## 8. Construire les panneaux un par un

Vérifier toute la période du lot et l’absence de filtre temporaire global avant chaque comparaison aux références. Un ratio d’erreur utilise tous les accès comme dénominateur. Les blocs suivants sont destinés aux panneaux Grafana ; les expressions API seront générées sans variable.

### 8.1 P01 — Nombre de logs access

Question et limite : Toutes les lignes JSON de ce lot, sans additionner les autres formats.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 102 972.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P01 — Nombre de logs access`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.2 P02 — Réponses HTTP 2xx

Question et limite : Inclut les réponses 200 et 206.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 200
| v_status < 300
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 91 145.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P02 — Réponses HTTP 2xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.3 P03 — Réponses HTTP 4xx

Question et limite : Erreurs HTTP côté requête, pas rejets d’un import de catalogue.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 2 670.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P03 — Réponses HTTP 4xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.4 P04 — Réponses HTTP 5xx

Question et limite : Dans ce fichier, le code de cette famille est 500.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 248.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P04 — Réponses HTTP 5xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.5 P05 — Part de réponses 4xx

Question et limite : Rapport sur tous les access logs du lot dans la période.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
((sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[$__range]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
))))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
)))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Régler les décimales à 3. Ne pas ajouter *100 : le format pourcentage convertit le ratio pour l’affichage.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 2,592937886 %.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P05 — Part de réponses 4xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.6 P06 — Part de réponses 5xx

Question et limite : Le dénominateur ne doit pas être restreint globalement aux erreurs.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
((sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[$__range]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
))))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
)))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Régler les décimales à 3. Ne pas ajouter *100 : le format pourcentage convertit le ratio pour l’affichage.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 0,240842171 %.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P06 — Part de réponses 5xx`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.7 P07 — Volume dans le temps de collecte, fenêtre 1 min

Question et limite : Ne pas interpréter cette courbe comme la chronologie historique des requêtes du serveur.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[1m]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, intervalle minimum 1s ; la fenêtre de comptage écrite dans LogQL reste 1m.
2. Cliquer Run queries.
3. Choisir Time series / Série temporelle.
4. Choisir une unité numérique simple et conserver l’infobulle.
5. Survoler le pic et lire son heure de collecte. Le pas réellement exécuté est consultable dans Inspect → Query.
6. Un pas trop grand peut manquer un chargement très bref près de la borne de fin : resserrer la période autour de la collecte, demander un pas plus fin ou avancer la borne de fin à une heure déjà atteinte.
7. Ne pas sommer les points pour retrouver 102972 : l’alignement et le recouvrement des fenêtres comptent.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Un pic ou plusieurs fenêtres de collecte.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P07 — Volume dans le temps de collecte, fenêtre 1 min`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.8 P08 — Répartition par code HTTP

Question et limite : Onze codes réellement présents.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_status) (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Choisir Bar gauge / Jauge à barres dans les visualisations.
3. Orientation horizontale, calcul Last not null.
4. Dans Legend de la requête, saisir `{{v_status}}`.
5. Unité None, zéro décimale. Garder le nom de chaque série visible.
6. Agrandir le graphique si les libellés sont tronqués ; ne pas remplacer une IP ou un chemin par une catégorie inventée.
7. Comparer les valeurs et le périmètre ci-dessous. Une sélection bornée triée n’est pas une découverte globale recalculée.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 200=91074 ; 206=71 ; 301=7833 ; 302=20 ; 304=1056 ; 400=29 ; 403=88 ; 404=2298 ; 405=3 ; 408=252 ; 500=248.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P08 — Répartition par code HTTP`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.9 P09 — Méthodes reconnues

Question et limite : La somme vaut 102705 ; les 267 méthodes non extraites restent dans le total.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_method) (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_method="method"
| __error__=""
| v_method!=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Choisir Bar gauge / Jauge à barres dans les visualisations.
3. Orientation horizontale, calcul Last not null.
4. Dans Legend de la requête, saisir `{{v_method}}`.
5. Unité None, zéro décimale. Garder le nom de chaque série visible.
6. Agrandir le graphique si les libellés sont tronqués ; ne pas remplacer une IP ou un chemin par une catégorie inventée.
7. Comparer les valeurs et le périmètre ci-dessous. Une sélection bornée triée n’est pas une découverte globale recalculée.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : GET=61858 ; POST=36988 ; OPTIONS=3221 ; HEAD=635 ; PUT=3.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P09 — Méthodes reconnues`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.10 P10 — Somme des tailles connues, en octets

Question et limite : Ce n’est pas la taille de stockage des logs dans Loki.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum(sum_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.
9. Après le contrôle exact, un format bytes peut abréger en KiB/MiB. Lire les octets bruts dans Inspect → Data pour comparer à la référence, sans confondre unité abrégée et nombre source.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 1 293 498 000 octets.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P10 — Somme des tailles connues, en octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.11 P11 — Moyenne des tailles connues, en octets

Question et limite : Moyenne pondérée par les 67987 valeurs connues, pas par les 102972 lignes.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
(sum(sum_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[$__range]
)))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 2. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.
9. Après le contrôle exact, un format bytes peut abréger en KiB/MiB. Lire les octets bruts dans Inspect → Data pour comparer à la référence, sans confondre unité abrégée et nombre source.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 19 025,66667 octets.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P11 — Moyenne des tailles connues, en octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.12 P12 — P95 global des tailles connues, en octets

Question et limite : Comparer la convention de quantile de Loki ; ce n’est pas une latence HTTP.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
quantile_over_time(0.95, 
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
) by ()
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.
9. Après le contrôle exact, un format bytes peut abréger en KiB/MiB. Lire les octets bruts dans Inspect → Data pour comparer à la référence, sans confondre unité abrégée et nombre source.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Référence locale linéaire : 58 043 octets.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P12 — P95 global des tailles connues, en octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.13 P13 — Taille maximale connue, en octets

Question et limite : Maximum calculé côté Loki, pas estimé sur un échantillon affiché.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
max(max_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.
9. Après le contrôle exact, un format bytes peut abréger en KiB/MiB. Lire les octets bruts dans Inspect → Data pour comparer à la référence, sans confondre unité abrégée et nombre source.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 2 017 208 octets.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P13 — Taille maximale connue, en octets`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.14 P14 — Lignes sans taille renseignée

Question et limite : Le tiret Apache correspond à une absence de taille, pas à zéro octet.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir None / Sans unité pour lire le nombre exact.
6. Régler les décimales à 0. Le titre précise les octets lorsque la valeur est une taille.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 34 985.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P14 — Lignes sans taille renseignée`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.15 P15 — Part des lignes avec taille connue

Question et limite : Renseignement du champ, pas indicateur de livraison du transport.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
(sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[$__range]
))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
[$__range]
)))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de A, sélectionner Type = Instant, pas Both ou Range pour un total/statistique de période.
2. Cliquer Run queries / Exécuter les requêtes.
3. Ouvrir le sélecteur de visualisation à droite et choisir Stat.
4. Dans les options de valeur, choisir Last not null / Dernière non nulle : la requête fournit déjà la statistique, il ne faut pas sommer des points de courbe.
5. Dans Standard options → Unit, choisir Percent (0.0–1.0).
6. Régler les décimales à 3. Ne pas ajouter *100 : le format pourcentage convertit le ratio pour l’affichage.
7. Désactiver la petite courbe de tendance si elle suggère une série qui n’est pas renvoyée par cette requête Instant.
8. Garder No data visible : ne pas transformer toute absence en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 66.024745 %.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P15 — Part des lignes avec taille connue`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.16 P16 — Dix IP suivies

Question et limite : Liste bornée documentée depuis l’analyse locale pour maîtriser le nombre de séries. Ce n’est pas une découverte exhaustive sur un autre fichier.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_ip) (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_ip="client_ip"
| __error__=""
| v_ip=~"54\\.210\\.20\\.202|::1|148\\.251\\.21\\.227|81\\.22\\.242\\.55|46\\.101\\.48\\.46|104\\.236\\.254\\.104|199\\.21\\.99\\.207|192\\.187\\.98\\.42|148\\.251\\.184\\.139|104\\.154\\.198\\.228"
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Choisir Bar gauge / Jauge à barres dans les visualisations.
3. Orientation horizontale, calcul Last not null.
4. Dans Legend de la requête, saisir `{{v_ip}}`.
5. Unité None, zéro décimale. Garder le nom de chaque série visible.
6. Agrandir le graphique si les libellés sont tronqués ; ne pas remplacer une IP ou un chemin par une catégorie inventée.
7. Comparer les valeurs et le périmètre ci-dessous. Une sélection bornée triée n’est pas une découverte globale recalculée.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 54.210.20.202=34469 ; ::1=3219 ; autres valeurs dans la référence.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P16 — Dix IP suivies`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.17 P17 — Cinq chemins suivis

Question et limite : Sélection explicite de chemins ; les paramètres éventuels font partie de path.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_path) (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_path="path"
| __error__=""
| v_path=~"/wp\\-login\\.php|/xmlrpc\\.php|/|/feed/|/favicon\\.ico"
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Choisir Bar gauge / Jauge à barres dans les visualisations.
3. Orientation horizontale, calcul Last not null.
4. Dans Legend de la requête, saisir `{{v_path}}`.
5. Unité None, zéro décimale. Garder le nom de chaque série visible.
6. Agrandir le graphique si les libellés sont tronqués ; ne pas remplacer une IP ou un chemin par une catégorie inventée.
7. Comparer les valeurs et le périmètre ci-dessous. Une sélection bornée triée n’est pas une découverte globale recalculée.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : /wp-login.php=7902 ; /xmlrpc.php=5329 ; /=4019 ; /feed/=2816 ; /favicon.ico=1891.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P17 — Cinq chemins suivis`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.18 P18 — Classes de taille sur toutes les valeurs connues

Question et limite : Cinq classes disjointes, somme 67987 ; leurs largeurs diffèrent, donc barres catégorielles.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

Utiliser les cinq requêtes A à E suivantes, une par classe.

Requête A — légende `1-999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1
| v_bytes < 1000
| __error__=""
[$__range]
))
```

Requête B — légende `1000-9999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1000
| v_bytes < 10000
| __error__=""
[$__range]
))
```

Requête C — légende `10000-99999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 10000
| v_bytes < 100000
| __error__=""
[$__range]
))
```

Requête D — légende `100000-999999` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 100000
| v_bytes < 1000000
| __error__=""
[$__range]
))
```

Requête E — légende `>=1000000` :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
[$__range]
))
```

#### B. Configurer les cinq calculs et les barres

1. Après A, cliquer Add query pour ajouter B, C, D puis E. Pour chaque requête, choisir Code et coller son propre bloc.
2. Régler le type Instant pour chacune des cinq requêtes.
3. Dans Legend de chaque requête, saisir le libellé de classe indiqué au-dessus de son bloc.
4. Cliquer Run queries et attendre les cinq résultats.
5. Choisir Bar gauge, orientation horizontale, calcul Last not null, unité None, zéro décimale.
6. Conserver les cinq catégories visibles et agrandir l’aperçu si nécessaire.
7. Vérifier les fréquences : 16792, 21193, 28868, 1121, 13 ; leur somme vaut 67987.
8. Les classes ont des largeurs inégales : ce sont des barres catégorielles, pas un histogramme à classes uniformes.
9. Ne pas ajouter les 34985 tailles absentes à la première classe : elles ne valent pas zéro.


#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : 16792 ; 21193 ; 28868 ; 1121 ; 13.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P18 — Classes de taille sur toutes les valeurs connues`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.19 P19 — Table des erreurs HTTP, extrait

Question et limite : Une table d’investigation n’est pas un compteur exhaustif.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json",lot="${lot}"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 600
| __error__=""
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, limite de logs = 500, puis Run queries.
2. Choisir Table et repérer dans l’aperçu le champ contenant le JSON, généralement Line.
3. Ouvrir Transformations → Add transformation → Extract fields.
4. Source : le champ de texte JSON ; format JSON ; activer Replace all fields et Keep Time.
5. Si plusieurs trames sont renvoyées, ajouter Merge series/tables et vérifier qu’aucune ligne n’est multipliée. Ne pas utiliser une jointure un-à-plusieurs pour créer la table.
6. Ajouter Filter fields by name ; garder Time, source_line, client_ip, method, path, request_line, status, bytes et apache_time.
7. Ajouter Convert field type pour status et bytes vers Numeric si nécessaire. Une valeur absente doit rester absente.
8. Si la table est unique, Organize fields permet de régler l’ordre des colonnes et masquer les autres champs.
9. Cliquer l’en-tête Time pour le tri choisi et tirer les séparations de colonnes pour lire le texte.
10. Garder request_line lisible pour les requêtes atypiques, même sans méthode extraite. Le tableau est limité ; le compteur backend porte le total.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Population 2918 ; affichage limité à 500 lignes.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P19 — Table des erreurs HTTP, extrait`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.20 P20 — Histogramme des tailles, échantillon 500 max

Question et limite : Exercice de transformation côté navigateur. La distribution de population complète est P18.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, limite = 500, puis Run queries. Le navigateur ne doit pas télécharger arbitrairement tout le corpus pour cet exercice.
2. Ouvrir la vue tabulaire et repérer le champ JSON, généralement Line.
3. Transformations → Add transformation → Extract fields : Source = ce champ, format JSON, Replace all fields et Keep Time.
4. Ajouter Convert field type : bytes → Numeric.
5. Ajouter Filter fields by name : garder seulement bytes.
6. Vérifier l’aperçu : au plus 500 valeurs connues ; status, source_line et les autres nombres ne doivent pas entrer dans cette distribution.
7. Choisir Histogram ; Bucket size = 10000 octets et offset = 0.
8. Si plusieurs trames sont combinées, confirmer qu’elles contiennent toutes le même champ bytes et aucun autre champ numérique.
9. La fréquence est un nombre d’observations ; ne pas lui attribuer une unité d’octets. Le titre précise l’unité des tailles.
10. La somme des fréquences doit correspondre au nombre réellement affiché, pas à 67987. P18 montre les classes sur toute la population connue.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Au plus 500 valeurs connues affichées.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P20 — Histogramme des tailles, échantillon 500 max`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.21 P21 — Heatmap des tailles et de la collecte, échantillon

Question et limite : Un chargement bref peut occuper une seule colonne. Ce n’est pas un historique source reconstruit.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json",lot="${lot}"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, limite = 500, puis Run queries. Le navigateur ne doit pas télécharger arbitrairement tout le corpus pour cet exercice.
2. Ouvrir la vue tabulaire et repérer le champ JSON, généralement Line.
3. Transformations → Add transformation → Extract fields : Source = ce champ, format JSON, Replace all fields et Keep Time.
4. Ajouter Convert field type : bytes → Numeric.
5. Ajouter Filter fields by name : garder seulement Time et bytes.
6. Vérifier l’aperçu : au plus 500 valeurs connues ; status, source_line et les autres nombres ne doivent pas entrer dans cette distribution.
7. Choisir Heatmap ; Calculate from data = Yes, car ces valeurs ne sont pas déjà des classes.
8. X Bucket : Size = 5s ; Y Bucket : Linear, Size = 10000 octets.
9. Garder légende et infobulle : X = collecte, Y = taille, couleur = fréquence de l’échantillon.
10. Une seule colonne temporelle peut être correcte si le chargement est rapide. Ne pas inventer des phases ni attribuer cet axe à apache_time.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Au plus 500 observations ; temps de collecte.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P21 — Heatmap des tailles et de la collecte, échantillon`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

### 8.22 P22 — Logs JSON détaillés, extrait

Question et limite : Développer raw_line et request_line pour lire la preuve source.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[A13bis] Access logs — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période complète du lot, la valeur de lot et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Choisir Loki-Formation pour ouvrir l’éditeur.
6. Dans la liste des sources de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver Loki-Formation et noter le choix fixe.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="atelier13bis",format="json",lot="${lot}"}
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, limite = 500, puis Run queries.
2. Choisir Logs.
3. Activer heure, détails et retour à la ligne pour les longs JSON.
4. Désactiver la déduplication pendant l’investigation et choisir un ordre d’affichage documenté.
5. Développer une entrée et lire raw_line, request_line, apache_time et status.
6. Garder le JSON original ; aucun line_format n’est nécessaire pour ce panneau de preuves.
7. Ne pas utiliser le nombre de lignes affichées comme total du lot.

#### C. Vérifier avant de sauvegarder

Référence du fichier fourni : Au plus 500 logs du lot choisi.

Comparer dans le même lot et toute la période de collecte. Si une valeur diffère, vérifier les paramètres et l’éventuelle limite d’affichage avant de conclure à une perte. Les références locales ne sont pas des mesures déjà exécutées sur votre serveur.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P22 — Logs JSON détaillés, extrait`.
2. Cliquer Apply / Appliquer pour revenir au dashboard. Si l’interface utilise une autre action de retour qui conserve le panneau, l’utiliser.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre et relâcher.
4. Tirer le coin inférieur du panneau pour rendre les valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer la sauvegarde.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.

## 9. Ajouter les deux panneaux de texte

### 9.1 P00 — Périmètre et définitions

1. Ouvrir le dashboard en édition, cliquer Add visualization et choisir Text.
2. Si une source est demandée pour un panneau sans requête, choisir Grafana / Built-in.
3. Choisir le mode Markdown et coller :

```markdown
### Diagnostic du corpus access
Lot : ${lot}. Les panneaux principaux utilisent uniquement le flux JSON de ce lot.
Les représentations brute, JSON et logfmt ne sont pas additionnées comme des accès distincts.
Time Loki = collecte. apache_time = date écrite dans la source.
Les taux d’erreur portent sur tous les accès de la période.
Les statistiques de taille utilisent les valeurs connues ; absence ne vaut pas zéro.
```

4. Titre : `P00 — Périmètre et méthode`.
5. Appliquer, faire glisser le panneau en haut, lui donner une grande largeur et enregistrer le dashboard.

### 9.2 P23 — Couverture et limites

1. Depuis le dashboard en édition, ajouter un nouveau panneau Text, sans ouvrir P00.
2. Mode Markdown ; coller :

```markdown
### Limites
Le contrôle de livraison compare les volumes et la distribution HTTP, pas tous les IDs en ligne.
Les 267 méthodes non extraites et les 34985 tailles absentes restent dans le total du fichier fourni.
Les IP et chemins suivis sont des sélections bornées documentées.
P18 porte sur toutes les tailles connues ; P19/P20/P21/P22 sont des vues ou échantillons plafonnés.
Une IP n’est pas une personne. Un chemin n’est pas une preuve de causalité ou d’attaque.
Aucune latence HTTP ni géolocalisation personnelle n’est mesurée.
```

3. Si le fichier fourni est remplacé lors d’une autre séance, utiliser les valeurs calculées dans reference_source.json plutôt que forcer ces nombres.
4. Titre : `P23 — Couverture et limites`.
5. Appliquer, placer sous les logs et enregistrer le dashboard.

## 10. Assembler, placer et rouvrir le dashboard

```text
Variables : Source Loki | Lot access
P00 Contexte
P01 Total | P02 2xx | P03 4xx | P04 5xx | P05 Part 4xx | P06 Part 5xx
P07 Volume temporel | P08 Codes | P09 Méthodes
P10 Somme des tailles | P11 Moyenne | P12 P95 | P13 Maximum
P14 Tailles absentes | P15 Part de tailles connues
P16 IP suivies | P17 Chemins suivis
P18 Classes de taille, population complète connue
P19 Table des erreurs
P20 Histogramme échantillonné | P21 Heatmap échantillonnée
P22 Logs JSON détaillés
P23 Limites
```

1. Cliquer Edit et repérer chaque panneau par son numéro.
2. Maintenir le clic sur sa poignée ou son en-tête, glisser dans la grille et relâcher à la position voulue.
3. Tirer le coin inférieur pour régler la taille ; donner de la largeur aux chemins, tableaux et logs.
4. Ne pas essayer de rendre les 24 panneaux visibles sur un seul écran au détriment des libellés.
5. Vérifier lot, période et absence de filtre temporaire, puis Save dashboard.
6. Revenir à la liste des dashboards et rouvrir `[A13bis] Access logs — diagnostic Loki`.
7. Vérifier que les 24 panneaux, les variables et la période sont conservés.

## 11. Créer un dashboard de détail par IP

### A. Créer le dashboard et ses variables

1. Dashboards → New → New dashboard.
2. Enregistrer sous `[A13bis] Détail access par IP`.
3. Dans Settings → Variables, créer `loki_ds` de type Data source, type Loki, choix Loki-Formation.
4. Ajouter `lot` de type Text box, valeur `__LOT__` du document personnalisé.
5. Ajouter `ip` de type Text box, valeur initiale `54.210.20.202`.
6. Confirmer, choisir la période de collecte, puis enregistrer le dashboard.

### B. Ajouter les logs de cette IP

1. Cliquer Add visualization, choisir Loki-Formation puis Code.
2. Coller :

```logql
{job="atelier13bis",format="json",lot="${lot}"}
| json v_ip="client_ip"
| __error__=""
| v_ip="${ip}"
```

3. Type Range, limite 500, puis Run queries.
4. Choisir Logs, activer heure et détails, conserver le JSON et désactiver la déduplication pour l’investigation.
5. Titre : `Preuves access pour l’IP sélectionnée`.
6. Appliquer, agrandir puis enregistrer le dashboard.
7. Tester une autre IP présente, par exemple ::1, et observer le changement des lignes.

### C. Relier P19 au détail

1. Copier l’URL du dashboard de détail, notamment son chemin `/d/UID/nom`.
2. Revenir au dashboard principal, menu de P19 → Edit.
3. Dans les options de champs, ajouter un Override sur le champ `client_ip`.
4. Ajouter la propriété Data links, puis Add link.
5. Titre : `Voir les logs de cette IP`.
6. URL : utiliser le chemin réel copié et les paramètres :

```text
/d/UID_REEL/nom?var-lot=${lot}&var-ip=${__data.fields.client_ip}&from=${__from}&to=${__to}
```

7. Remplacer le chemin par celui de votre dashboard manuel ; laisser les variables Grafana interprétées au clic. Les IP du fichier sont des valeurs IPv4/IPv6 adaptées à cet exemple de paramètre.
8. Confirmer le lien, appliquer le panneau et enregistrer le dashboard principal.
9. Cliquer une IP de la table et ouvrir le lien, puis vérifier IP, lot et période du détail.

Un lien partage un contexte, pas des droits. Ne pas activer l’anonymat pour le faire fonctionner.

## 12. Vérifier les valeurs et la requête réellement exécutée

### A. Utiliser l’inspecteur

1. Dans le dashboard principal, ouvrir le menu de P01 puis Inspect / Inspecter.
2. Dans Query, vérifier la substitution du lot, la source Loki et les bornes.
3. Vérifier Type Instant pour un total ; lire la valeur brute dans Data.
4. Recommencer avec P05/P06 : la valeur avant formatage est un ratio entre 0 et 1, pas déjà un pourcentage.
5. Recommencer avec P11 : dénominateur 67987 valeurs connues, pas 102972.
6. Sur P07, lire le pas réel de calcul ; la fenêtre LogQL reste 1 minute.

### B. Contrôler le total avec l’API Loki

Le générateur a résolu les variables dans les fichiers d’API :

```bash
export LOKI_URL='http://127.0.0.1:3100'
END_REF=$(python3 -c 'import json; print(json.load(open("reference13bis.json"))["to_ns"])')
curl --fail-with-body -sS -G "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode "query=$(cat livrables13bis/requetes-api/total.logql)" \
  --data-urlencode "time=$END_REF" -o controle_total_access.json
python3 -m json.tool controle_total_access.json
```

Attendu : résultat vectoriel contenant une valeur 102972. Le nombre de séries du vector n’est pas le nombre d’accès. Le compte ne dépend pas de la limite 500/2000 des vues de logs.

### C. Références de contrôle

| Contrôle | Résultat du fichier |
|---|---:|
| Total JSON du lot | 102972 |
| 2xx + 3xx + 4xx + 5xx | 102972 |
| Erreurs 4xx + 5xx | 2918 |
| Méthodes reconnues + absentes | 102705 + 267 |
| Tailles connues + absentes | 67987 + 34985 |
| Somme des cinq classes de taille | 67987 |

Une égalité de comptes ne certifie pas les identités de chaque événement. Les références source, l’empreinte et les contrôles de distribution apportent des preuves complémentaires, avec cette limite à expliquer.

## 13. Investigation guidée sur le corpus

1. Noter lot et période, puis lire P01/P03/P04.
2. Dans Explore, exécuter E12 pour examiner les 248 réponses 500 du fichier.
3. Ouvrir plusieurs lignes : relever IP, requête, statut, taille éventuelle et date écrite.
4. Exécuter E26 et E27 sur les chemins /wp-login.php et /xmlrpc.php ; comparer avec la simple recherche de texte E04.
5. Exécuter E24 sur l’IP dominante et suivre des lignes dans le dashboard de détail.
6. Exécuter E19 : lire les requêtes non séparées en méthode/chemin/protocole, sans les supprimer du total.
7. Exécuter E21 : expliquer la taille absente sans l’assimiler à une perte de transport.
8. Écrire une conclusion courte : fait mesuré, périmètre, hypothèse éventuelle et information manquante.
9. Ne pas affirmer « attaque confirmée » à partir d’un seul chemin ou d’une adresse ; un diagnostic réel demande du contexte supplémentaire.

## 14. Utiliser les JSON de correction

Le générateur fournit `livrables13bis/dashboard13bis.json` et `livrables13bis/dashboard13bis-detail.json`. Ils servent de correction ou de secours après la construction manuelle.

1. Dans Grafana, Dashboards → New → Import.
2. Charger le détail puis le principal, sans écraser un objet utilisé sans accord.
3. Choisir Loki-Formation dans la variable de source, vérifier lot et période.
4. Les exports utilisent des UID de laboratoire fixes. Le dashboard de détail généré a l’UID a13bis-access-detail ; un dashboard créé manuellement peut avoir un autre UID.
5. Vérifier dans P19/P20/P21 le champ de ligne JSON nommé Line et le champ Time sur cette version de Grafana.
6. Ajuster les transformations si le connecteur utilise un autre libellé, puis refaire les contrôles de compte.
7. Enregistrer et rouvrir les dashboards.

Les fichiers JSON sont générés localement et ne sont pas envoyés automatiquement à l’API Grafana. Un JSON valide syntaxiquement n’est pas une preuve d’import UI validé.

## 15. Dépannage concret

| Symptôme | Vérification |
|---|---|
| Fichier source absent | Être dans le dossier du pack ; vérifier donnees/access_log_actualise |
| Dossier de préparation déjà présent | Lire son manifeste ; ne pas écraser une préparation utilisée |
| Installation refusée, ressource présente | Inspecter service/configuration/état existants ; ne pas supprimer les positions |
| Port 12347 occupé | Identifier le service concerné avec ss ; ne pas le stopper arbitrairement |
| Service actif mais comptes incomplets | Lire journalctl et les refus HTTP, vérifier droits et destination |
| 429 dans le writer | Laisser agir le backoff configuré et vérifier les limites du laboratoire ; ne pas relancer la collecte en doublon |
| Refus HTTP non récupérable | Corriger la cause avant toute décision sur une réémission ; conserver les preuves |
| Explore vide | Source Loki, lot, période de collecte, puis filtres de contenu |
| Seulement 500/2000 lignes dans l’écran | Limite d’affichage ; utiliser count_over_time pour le total |
| Ratio fois cent trop grand | Percent (0.0–1.0), sans multiplication supplémentaire |
| Somme des méthodes 102705 | 267 méthodes absentes, cohérent avec le fichier |
| Somme des classes 67987 | 34985 tailles absentes, ne pas les transformer en zéros |
| Histogramme compte des IDs ou des dates | Garder uniquement bytes dans Filter fields by name |
| Organize fields refuse plusieurs trames | Filtrer les champs pour toutes les trames ; fusion contrôlée pour la table si nécessaire |
| Une seule colonne de heatmap | Chargement bref et axe de collecte, pas forcément une erreur |
| Trop de séries | Extraire uniquement les champs utiles et utiliser les listes bornées du TP |
| Les dates semblent différentes | Distinguer apache_time du timestamp Loki de collecte |

## 16. Conserver les livrables et qualifier les résultats

1. Enregistrer et rouvrir les dashboards principal et de détail.
2. Compléter la grille des panneaux avec valeurs et captures.
3. Conserver préparation, référence de livraison, empreinte, requêtes et réponse API.
4. Exporter les dashboards avec les droits autorisés. L’export ne contient ni les logs Loki ni les secrets de source.
5. Ne pas supprimer les fichiers d’état de lecture ni tronquer les fichiers suivis. Un arrêt autorisé du collecteur se fait par `sudo systemctl stop alloy-atelier13bis-access`, sans effacer les données Loki.

Les scripts de préparation et les références sont contrôlés localement sur le fichier fourni. Le rapport `VALIDATION_FORMATEUR.json` distingue tests locaux, réponses HTTP simulées et opérations à confirmer dans le laboratoire. Aucun chargement Loki réel, validation par un binaire Alloy ou clic Grafana n’est présenté comme déjà effectué pendant la fabrication du pack.
