# Défi 08 bis — Corrigé Kibana enrichi : construire 25 panneaux à partir des logs OpenSSH

Version cible : Kibana 9.5.7 en français. Suite du défi Loghub OpenSSH et de l’atelier 8.

## 1. Ce que remplace ce document

Ce corrigé pour la partie Kibana du défi OpenSSH : préparation de la vue de données, création des graphiques, cartes, contrôles et assemblage. Il ne modifie ni le corpus, ni le mapping, ni les scripts du pack initial. La reprise de la chaîne Bulk est fournie en section 3 pour éviter une dépendance implicite.

Chaque visualisation a son parcours complet, sans renvoi à une procédure commune d’ouverture ou d’enregistrement. Le type de graphique de valeur unique se nomme « Indicateur », conformément à votre interface. Les autres libellés français sont des repères fonctionnels : ils ne sont pas présentés comme une validation de chaque écran de votre instance.

### Règles de lecture

- Cliquer : clic gauche.
- Glisser-déposer : maintenir le clic sur le champ dans la liste de gauche, déplacer vers la zone désignée à droite, relâcher.
- Barre KQL globale : celle du tableau de bord ; elle affecte plusieurs panneaux.
- Filtre local de Lens : celui enregistré avec une visualisation ; ne pas l’appliquer globalement.
- Formule : texte à coller dans l’onglet « Formule » d’un calcul, jamais dans la barre KQL.
- Les noms `[D08B] ...`, les champs et les formules doivent être copiés sans traduction.

Ce niveau de guidage reprend le principe du support de l’atelier 8 fourni : une manipulation suivie jusqu’à l’enregistrement, avec un contrôle du résultat. 

### Durée réaliste

Pour un socle de demi-journée, réaliser P01 à P06, P09, P12, P15, P17, P20, P23 et P25 ; utiliser les autres comme approfondissements. Les cartes P21/P22 sont des variantes de lecture du même corpus, pas de nouvelles sources.

## 2. Tableau de bord cible : 25 panneaux

| ID | Panneau | Type | Utilité |
|---|---|---|---|
| P01 | Documents indexés | Indicateur | Taille du périmètre observé |
| P02 | Enregistrements canoniques | Indicateur | Dénominateur explicite |
| P03 | Échecs canoniques | Indicateur | Volume d’échecs reconnus |
| P04 | Succès canoniques | Indicateur | Ne pas cacher leur éventuelle absence |
| P05 | IP distinctes estimées | Indicateur | Diversité des adresses, pas visiteurs |
| P06 | Part d’échec canonique | Indicateur % | Échecs / enregistrements reconnus |
| P07 | Couverture GeoIP | Indicateur % | Documents localisés / documents avec IP |
| P08 | Documents sans IP extraite | Indicateur % | Qualité / limite du parsing |
| P09 | Messages dans le temps | Barres verticales empilées | Volume et catégories |
| P10 | Échecs et succès dans le temps | Courbes | Deux séries comparables |
| P11 | Répartition des types | Anneau | Vue synthétique du corpus |
| P12 | IP contribuant aux échecs | Barres horizontales | Contributeurs, top 10 |
| P13 | Utilisateurs dans les échecs | Barres horizontales | Noms les plus observés |
| P14 | Pays GeoIP | Barres horizontales | Répartition du seul périmètre localisé |
| P15 | Analyse par IP | Tableau Lens | Volumes, échecs, taux |
| P16 | Analyse par utilisateur | Tableau Lens | Comparaison des noms observés |
| P17 | Temps × type | Carte thermique Lens | Intensités temporelles |
| P18 | IP × issue canonique | Carte thermique Lens | Comparer les contributeurs |
| P19 | Ports sources des enregistrements canoniques | Barres par tranches | Distribution, pas ports du serveur |
| P20 | Points GeoIP | Carte Documents | Lire les positions et attributs |
| P21 | Volumes GeoIP regroupés | Carte Regroupements | Lire des volumes spatiaux |
| P22 | Densité GeoIP | Carte thermique géographique | Lecture de densité, pas matrice Lens |
| P23 | Détail des échecs | Session Découvrir | Revenir aux preuves |
| P24 | Détail des lignes non localisées | Session Découvrir | Comprendre la couverture |
| P25 | Contrat de lecture | Texte Markdown | Source, définitions et limites |

Les tableaux Lens permettent de combiner regroupements, comptages et colonnes de formules. La matrice Lens et la carte de densité géographique sont deux représentations distinctes.

## 3. Reprendre les données du pack initial sans repartir dans une installation

### 3.1 Fichiers réutilisés, non inclus à nouveau ici

Le pack du premier défi reste nécessaire pour les éléments suivants :

```text
preparer_openssh.py
verifier_reponse.py
openssh-mapping.json
openssh-geoip-pipeline.json
openssh-validation-query.json
exporter_cache_geo.py
export-cache-query.json
```

La source est `OpenSSH_2k.log`, provenant de Loghub. Ce journal contient des IP à enrichir, pas des coordonnées natives. Ne pas utiliser les données HTTP de l’atelier 8 pour remplir ces visualisations SSH.

### 3.2 Si l’import du premier défi est déjà réussi

Dans Console, exécuter :

```http
GET defi08b-openssh/_count
GET defi08b-openssh/_field_caps?fields=@timestamp,source_ip,source_geo.location,event_type,auth_record,auth_outcome,user_name,source_port
```

Si le nombre est supérieur à zéro et que les champs ont le schéma attendu, ne pas réimporter pour le seul besoin de ce corrigé. Continuer en section 4.

### 3.3 Si l’import n’a pas encore été réalisé

Dans le dossier du pack initial, réutiliser l’accès Elasticsearch de l’atelier 1. En Bash :

```bash
# Variante sans sécurité uniquement :
export ES_URL='http://localhost:9200'
CURL_ES=(curl --fail-with-body -sS)

# Variante sécurisée : utiliser cette définition à la place de la précédente.
# ES_URL et ES_CA doivent correspondre à votre environnement.
# read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD; printf '\n'
# CURL_ES=(curl --fail-with-body -sS --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD")

python3 preparer_openssh.py OpenSSH_2k.log --outdir preparation --year 2000 --utc-offset +0000
cat preparation/preparation.json
```

Ne pas poursuivre avec zéro document ou une sortie partielle après erreur. Le script emploie une année/fuseau conventionnels car les en-têtes du journal ne les donnent pas. Ne pas les interpréter comme la date historique prouvée.

Créer le mapping seulement si l’index est absent ; si l’index existe, inspecter son contenu et son mapping avant de décider d’un rejeu. Aucune suppression automatique :

```bash
"${CURL_ES[@]}" -X PUT "$ES_URL/defi08b-openssh" \
  -H 'Content-Type: application/json' --data-binary @openssh-mapping.json

"${CURL_ES[@]}" -X PUT "$ES_URL/_ingest/pipeline/defi08b-openssh-geoip" \
  -H 'Content-Type: application/json' --data-binary @openssh-geoip-pipeline.json

"${CURL_ES[@]}" -X POST "$ES_URL/_ingest/pipeline/defi08b-openssh-geoip/_simulate" \
  -H 'Content-Type: application/json' --data-binary @preparation/geo-simulate.json \
  -o geo-simulate-response.json
python3 verifier_reponse.py simulate geo-simulate-response.json --preparation preparation/preparation.json
```

Si le test GeoIP est concluant, importer :

```bash
"${CURL_ES[@]}" -X POST \
  "$ES_URL/defi08b-openssh/_bulk?pipeline=defi08b-openssh-geoip&refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @preparation/openssh.ndjson \
  -o bulk-response.json
python3 verifier_reponse.py bulk bulk-response.json --preparation preparation/preparation.json
```

Si GeoIP ne fonctionne pas, utiliser le parcours de cache réel du premier pack avant de commencer les trois cartes. Ne pas créer de coordonnées fictives pour des IP réelles. Un fond cartographique et une base GeoIP sont deux dépendances différentes. Le parcours hors ligne importe les coordonnées du cache sans appeler le pipeline en ligne.

## 4. Valider les données et relever les références

Le fichier `controle_dashboard_25_panneaux.json` joint à ce corrigé fournit une recherche complète. Depuis un terminal configuré avec `CURL_ES` :

```bash
"${CURL_ES[@]}" -X POST "$ES_URL/defi08b-openssh/_search" \
  -H 'Content-Type: application/json' --data-binary @controle_dashboard_25_panneaux.json \
  -o controle-dashboard.json
python3 -m json.tool controle-dashboard.json
```

Une réponse avec `error`, `timed_out:true` ou `_shards.failed` supérieur à zéro n’est pas une référence fiable. Vérifier le volume avec `preparation/preparation.json`. Ne pas charger un autre corpus dans le même index pendant la construction.

| Lettre | Valeur à relever |
|---|---|
| N | `hits.total.value` avec `relation:eq` |
| A | `aggregations.auth_records.doc_count` |
| F | `aggregations.failures.doc_count` |
| S | `aggregations.successes.doc_count` |
| I | `aggregations.with_ip.doc_count` |
| G | `aggregations.located.doc_count` |
| U | `aggregations.unique_ips.value`, estimation |
| Première / dernière date | `first_event.value_as_string` / `last_event.value_as_string` |
| Types présents | `event_types.buckets` |
| Pays disponibles | `countries.buckets` |

Contrôler F + S = A pour le schéma du parseur fourni. La couverture est G / I si I > 0 ; la part d’échec est F / A si A > 0. N - I compte les documents sans IP extraite. Certaines catégories peuvent légitimement être absentes, notamment les succès.

Les champs `message_repeat` et `pam_failure` ne sont pas comptés comme des authentifications canoniques ; une ligne n’est ni une personne, ni une session, ni nécessairement une tentative distincte.

## 5. Préparer la vue de données et l’espace de travail

### 5.1 Créer ou vérifier la vue

1. Ouvrir la recherche de navigation en haut de Kibana.
2. Rechercher « Vues de données » et ouvrir la page correspondante.
3. Si `[D08B] OpenSSH Loghub` existe, l’ouvrir et vérifier son modèle `defi08b-openssh` et son champ temporel `@timestamp`.
4. Sinon, cliquer l’action de création d’une vue de données.
5. Dans le nom, saisir `[D08B] OpenSSH Loghub`.
6. Dans le modèle d’index, saisir exactement `defi08b-openssh`.
7. Dans le champ d’horodatage, sélectionner `@timestamp`.
8. Enregistrer la vue de données.

### 5.2 Vérifier l’affichage des documents

1. Ouvrir « Découvrir ».
2. Sélectionner `[D08B] OpenSSH Loghub` en mode KQL/vue de données, pas ES|QL.
3. Vider la barre KQL et retirer les filtres temporaires.
4. Cliquer le sélecteur de temps en haut à droite.
5. Choisir une période absolue qui inclut le minimum et le maximum relevés, avec une marge.
6. Tenir compte de l’année conventionnelle 2000 et du fuseau du navigateur.
7. Appliquer la période puis actualiser.
8. Ouvrir un document avec sa flèche de détail. Repérer `event_type`, `auth_record`, `source_ip`, `geo_status`, `message` et `timestamp_policy`.

Ne pas commencer les panneaux avec « Aucune donnée ». Revenir aux contrôles d’index et de période ; le mode « 15 dernières minutes » ne retrouvera pas ce corpus.

## 6. Construire les huit indicateurs

Les huit procédures sont indépendantes : chacune ajoute une nouvelle tuile. Toujours garder la période complète et aucun filtre d’échec global pendant les vérifications initiales. Les valeurs uniques peuvent être obtenues par agrégation ou par formule Lens. [web:154]

### 6.1 P01 — Documents indexés

But : Nombre de lignes indexées, pas nombre de sessions.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir « Tableaux de bord » dans la navigation Kibana.
2. Cliquer « Créer un tableau de bord ». Si `[D08B] Observabilité OpenSSH — Loghub` existe déjà, l’ouvrir plutôt que créer un doublon.
3. Enregistrer sous `[D08B] Observabilité OpenSSH — Loghub`, puis cliquer « Modifier ».
4. Régler la période complète du corpus, vider la barre KQL et retirer les filtres de test.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count()
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Documents indexés`.
6. Dans les réglages de format de valeur, choisir « Nombre » et zéro décimale si proposé.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à N. 

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P01 — Documents indexés` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P01` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.2 P02 — Enregistrements canoniques

But : Seulement les lignes Failed/Accepted reconnues comme canoniques par le parseur.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='auth_record: true')
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Enregistrements canoniques`.
6. Dans les réglages de format de valeur, choisir « Nombre » et zéro décimale si proposé.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à A. 

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P02 — Enregistrements canoniques` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P02` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.3 P03 — Échecs canoniques

But : Les messages PAM ne sont pas ajoutés une seconde fois à ce compteur.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='auth_outcome: "failure"')
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Échecs canoniques`.
6. Dans les réglages de format de valeur, choisir « Nombre » et zéro décimale si proposé.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à F. 

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P03 — Échecs canoniques` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P03` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.4 P04 — Succès canoniques

But : Zéro est une valeur correcte si aucun succès canonique n’a été observé.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='auth_outcome: "success"')
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Succès canoniques`.
6. Dans les réglages de format de valeur, choisir « Nombre » et zéro décimale si proposé.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à S. 

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P04 — Succès canoniques` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P04` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.5 P05 — IP distinctes estimées

But : Une IP n’est pas une personne ; la cardinalité est une estimation.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
unique_count(source_ip)
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `IP distinctes estimées`.
6. Dans les réglages de format de valeur, choisir « Nombre » et zéro décimale si proposé.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à U. 

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P05 — IP distinctes estimées` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P05` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.6 P06 — Part d’échec canonique

But : Ne pas calculer un taux d’échec sur toutes les lignes ; si A = 0, investiguer au lieu de présenter un faux zéro.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='auth_outcome: "failure"') / count(kql='auth_record: true')
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Part d’échec canonique`.
6. Dans les réglages de format de valeur, choisir « Pourcentage » et deux décimales ; ne pas ajouter `* 100` à la formule.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à F / A, si A > 0. Pour la vérification manuelle, multiplier le ratio par 100 pour le comparer à l’affichage en pourcentage.

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P06 — Part d’échec canonique` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P06` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.7 P07 — Couverture GeoIP — documents avec IP

But : Le dénominateur est l’ensemble des documents avec IP extraite, pas uniquement les IP publiques.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='source_geo.location: *') / count(kql='source_ip: *')
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Couverture GeoIP — documents avec IP`.
6. Dans les réglages de format de valeur, choisir « Pourcentage » et deux décimales ; ne pas ajouter `* 100` à la formule.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à G / I, si I > 0. Pour la vérification manuelle, multiplier le ratio par 100 pour le comparer à l’affichage en pourcentage.

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P07 — Couverture GeoIP — documents avec IP` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P07` affiche la valeur dans le même contexte de dates et de filtres que les références.

### 6.8 P08 — Documents sans IP extraite

But : Absence d’IP extraite ne signifie pas forcément erreur de collecte : certaines catégories n’en contiennent pas.

#### A. Ouvrir le tableau de bord et ajouter Lens

1. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans « Tableaux de bord ».
2. Cliquer « Modifier » si le tableau de bord n’est plus en édition.
3. Vérifier la période complète du corpus.
4. Vider la barre KQL et retirer les filtres de test ; ne pas restreindre globalement aux échecs.
5. Cliquer « Créer une visualisation », ou ouvrir « Ajouter » puis « Nouvelle visualisation » si le bouton est dans un menu.
6. Choisir Lens si Kibana propose plusieurs éditeurs.
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un éditeur de requête ES|QL apparaît, revenir au mode de construction par champs et dimensions.
9. Ouvrir le menu du type de graphique, puis cliquer « Indicateur ».

#### B. Configurer la valeur

1. À droite, cliquer la dimension de la valeur principale. Si elle est vide, cliquer la zone invitant à déposer un champ ; si elle est préremplie, cliquer le calcul existant pour le modifier.
2. Dans le volet de configuration, ouvrir l’onglet « Formule ».
3. Sélectionner tout le contenu du champ de formule et le remplacer par :

```text
count(kql='not source_ip: *') / count()
```

4. Attendre la validation. En cas de soulignement rouge, vérifier parenthèses, apostrophes droites et noms de champs. Ne pas déplacer ce texte dans la barre KQL.
5. Dans le libellé de la dimension, saisir `Documents sans IP extraite`.
6. Dans les réglages de format de valeur, choisir « Pourcentage » et deux décimales ; ne pas ajouter `* 100` à la formule.
7. Fermer uniquement le volet de la dimension avec sa croix ou son bouton de fermeture. Ne pas quitter Lens.
8. Lire l’aperçu central et comparer à (N - I) / N, si N > 0. Pour la vérification manuelle, multiplier le ratio par 100 pour le comparer à l’affichage en pourcentage.

#### C. Ajouter le panneau et enregistrer

1. Cliquer « Enregistrer et revenir » en haut de Lens.
2. Si Kibana demande un titre, saisir `[D08B] P08 — Documents sans IP extraite` et confirmer.
3. De retour sur le tableau de bord, si aucun titre n’a été demandé, ouvrir le menu `…` de la nouvelle tuile, choisir l’action de modification des paramètres du panneau, saisir ce même titre et confirmer.
4. Vérifier que les panneaux précédents sont toujours présents.
5. Cliquer « Enregistrer » en haut du tableau de bord et confirmer si nécessaire.

Résultat attendu : une nouvelle tuile `P08` affiche la valeur dans le même contexte de dates et de filtres que les références.

## 7. Temps et répartition : trois visualisations

### 7.1 P09 — Messages dans le temps par catégorie

Question : à quels moments les lignes sont-elles présentes, et de quels types sont-elles ?

#### A. Ajouter le graphique

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Ouvrir le menu des graphiques et choisir des barres verticales.

#### B. Déposer les champs dans les axes

1. Dans la recherche des champs à gauche, saisir `@timestamp`.
2. Maintenir le clic sur le champ trouvé, le déplacer vers « Axe horizontal » à droite et relâcher.
3. Cliquer cette dimension et vérifier l’opération « Histogramme de dates ».
4. Pour le premier affichage, conserver l’intervalle automatique. Si la période mesurée est courte, réduire le minimum d’intervalle ; ne pas supposer un historique de plusieurs jours.
5. Fermer ce volet.
6. Cliquer la zone « Axe vertical » ; sélectionner le comptage des documents, sans champ, puis libeller `Lignes par intervalle`.
7. Rechercher `event_type` dans les champs à gauche.
8. Glisser `event_type` vers la zone de ventilation/répartition des séries à droite.
9. Ouvrir cette dimension, choisir les valeurs les plus fréquentes et afficher 10 valeurs ou davantage selon les catégories de la référence.
10. Dans les options de style des barres, choisir l’empilement normal, pas l’empilement en pourcentage.
11. Conserver la légende visible.
12. Survoler deux barres et lire l’intervalle, la catégorie et le nombre de documents.

#### C. Vérifier et enregistrer

Vérifier qu’aucun filtre d’échec local n’est actif. Une ligne d’un type rare peut être difficile à voir sans être absente. Si une seule barre apparaît, examiner l’intervalle et les bornes avant de réimporter les données.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P09 — Messages dans le temps par type` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P09 — Messages dans le temps par type` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 7.2 P10 — Courbes des échecs et succès canoniques

Question : les lignes canoniques d’échec et de succès sont-elles présentes aux mêmes périodes ?

#### A. Ouvrir une nouvelle visualisation

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir le graphique « Courbe » dans le menu des types.

#### B. Construire la première série

1. Rechercher `@timestamp` et le glisser sur « Axe horizontal ».
2. Ouvrir la dimension et choisir « Histogramme de dates » ; conserver une granularité comparable à P09, puis fermer le volet.
3. Cliquer le calcul de l’axe vertical. S’il est déjà prérempli, le modifier au lieu de créer un doublon.
4. Ouvrir « Formule » et saisir :

```text
count(kql='auth_outcome: "failure"')
```

5. Libellé : `Échecs canoniques`, format Nombre.
6. Fermer le volet et observer la première courbe.

#### C. Ajouter la deuxième série

1. Dans la même couche, cliquer l’ajout d’une valeur supplémentaire sur l’axe vertical, et non l’ajout d’une deuxième dimension de temps.
2. Ouvrir « Formule » et saisir :

```text
count(kql='auth_outcome: "success"')
```

3. Libellé : `Succès canoniques`, format Nombre.
4. Fermer le volet et garder la légende visible.
5. Ne pas appliquer `auth_outcome:failure` dans la recherche locale ou globale : cela supprimerait les succès de leur propre périmètre.
6. Survoler un point pour lire les deux séries. Si S = 0, l’absence de hausse de la série des succès est attendue ; ne pas fabriquer des succès pour remplir le graphique.

#### D. Enregistrer

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P10 — Échecs et succès canoniques dans le temps` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P10 — Échecs et succès canoniques dans le temps` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 7.3 P11 — Anneau de répartition des catégories

Question : quels types de lignes dominent le fichier ?

#### A. Ajouter l’anneau

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Dans le menu des graphiques, choisir « Anneau ». Si le menu regroupe les secteurs, choisir le secteur puis son style en anneau.

#### B. Configurer le découpage

1. Dans la liste de gauche, rechercher `event_type`.
2. Glisser le champ sur la zone des catégories de l’anneau, c’est-à-dire la zone qui définit les parts, pas la valeur numérique.
3. Ouvrir cette dimension et choisir les valeurs les plus fréquentes.
4. Afficher au moins autant de valeurs que les catégories de `event_types.buckets`, dans la limite raisonnable de ce corpus.
5. Si une option regroupe les valeurs restantes dans « Autre », décider de la conserver ou de la désactiver après vérification que toutes les catégories sont affichées. Ne pas laisser une catégorie cachée sans explication.
6. Dans la dimension numérique, choisir le comptage des documents.
7. Garder la légende visible ; activer les libellés de parts seulement s’ils restent lisibles.
8. Survoler une part et comparer son nombre au bucket correspondant dans la référence.

#### C. Enregistrer

Ne pas nommer ce graphique « taux d’attaque » : il décrit des catégories de lignes, y compris du bruit technique et des répétitions.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P11 — Répartition des types de messages` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P11 — Répartition des types de messages` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

## 8. Contributeurs : trois graphiques à barres horizontales

### 8.1 P12 — Top 10 IP — échecs canoniques

Question : comparer les IP extraites des seules lignes canoniques d’échec.

#### A. Ouvrir Lens

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir des barres horizontales.

#### B. Construire les catégories et les volumes

1. Dans la recherche des champs à gauche, saisir `source_ip`.
2. Glisser ce champ vers l’axe des catégories, généralement « Axe vertical » pour des barres horizontales.
3. Cliquer la dimension créée ; choisir les valeurs les plus fréquentes et régler le nombre de valeurs à 10.
4. Classer par nombre de documents décroissant, puis fermer le volet.
5. Cliquer l’axe numérique horizontal ; choisir le comptage des documents sans champ.
6. Libeller cette valeur `Échecs canoniques`, format Nombre.
7. Dans la barre de recherche locale de Lens, saisir exactement :

```kql
auth_outcome: "failure"
```

8. Appliquer la recherche. Vérifier que vous êtes toujours dans Lens, et non dans la barre globale du tableau de bord.
9. Survoler une barre pour vérifier son nombre et sa catégorie.
10. Si les libellés sont trop longs, agrandir l’aperçu ou garder les détails dans l’infobulle, sans renommer les données.

#### C. Contrôler le périmètre et enregistrer

La somme du top peut être inférieure à F, à cause de la limite de dix valeurs ou des catégories manquantes. Une adresse peut être partagée ou représenter un relais ; le top 10 ne représente pas des personnes.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P12 — Top 10 IP — échecs canoniques` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P12 — Top 10 IP — échecs canoniques` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 8.2 P13 — Top utilisateurs — échecs canoniques

Question : comparer les noms présents dans les seules lignes canoniques d’échec.

#### A. Ouvrir Lens

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir des barres horizontales.

#### B. Construire les catégories et les volumes

1. Dans la recherche des champs à gauche, saisir `user_name`.
2. Glisser ce champ vers l’axe des catégories, généralement « Axe vertical » pour des barres horizontales.
3. Cliquer la dimension créée ; choisir les valeurs les plus fréquentes et régler le nombre de valeurs à 10.
4. Classer par nombre de documents décroissant, puis fermer le volet.
5. Cliquer l’axe numérique horizontal ; choisir le comptage des documents sans champ.
6. Libeller cette valeur `Échecs canoniques`, format Nombre.
7. Dans la barre de recherche locale de Lens, saisir exactement :

```kql
auth_outcome: "failure"
```

8. Appliquer la recherche. Vérifier que vous êtes toujours dans Lens, et non dans la barre globale du tableau de bord.
9. Survoler une barre pour vérifier son nombre et sa catégorie.
10. Si les libellés sont trop longs, agrandir l’aperçu ou garder les détails dans l’infobulle, sans renommer les données.

#### C. Contrôler le périmètre et enregistrer

La somme du top peut être inférieure à F, à cause de la limite de dix valeurs ou des catégories manquantes. Ne pas parler de comptes réels compromis : les noms peuvent correspondre à des utilisateurs invalides.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P13 — Top utilisateurs — échecs canoniques` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P13 — Top utilisateurs — échecs canoniques` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 8.3 P14 — Pays — messages géolocalisés

Question : comparer les noms de pays disponibles pour les documents avec coordonnées.

#### A. Ouvrir Lens

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir des barres horizontales.

#### B. Construire les catégories et les volumes

1. Dans la recherche des champs à gauche, saisir `source_geo.country_name`.
2. Glisser ce champ vers l’axe des catégories, généralement « Axe vertical » pour des barres horizontales.
3. Cliquer la dimension créée ; choisir les valeurs les plus fréquentes et régler le nombre de valeurs à 10.
4. Classer par nombre de documents décroissant, puis fermer le volet.
5. Cliquer l’axe numérique horizontal ; choisir le comptage des documents sans champ.
6. Libeller cette valeur `Messages géolocalisés`, format Nombre.
7. Dans la barre de recherche locale de Lens, saisir exactement :

```kql
source_geo.location: *
```

8. Appliquer la recherche. Vérifier que vous êtes toujours dans Lens, et non dans la barre globale du tableau de bord.
9. Survoler une barre pour vérifier son nombre et sa catégorie.
10. Si les libellés sont trop longs, agrandir l’aperçu ou garder les détails dans l’infobulle, sans renommer les données.

#### C. Contrôler le périmètre et enregistrer

La somme du top peut être inférieure à G, à cause de la limite de dix valeurs ou des catégories manquantes. Un pays peut manquer même si des coordonnées existent. Les pays des IP ne prouvent ni nationalité ni identité.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P14 — Pays — messages géolocalisés` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P14 — Pays — messages géolocalisés` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

## 9. Deux tableaux analytiques

Les valeurs des colonnes sont des calculs ; les catégories sont définies dans la zone des lignes. Déposer un champ n’assure pas automatiquement le calcul souhaité : ouvrir chaque dimension pour vérifier sa fonction.

### 9.1 P15 — Analyse par IP — volume et taux canonique

#### A. Créer les lignes du tableau

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir le type de graphique « Tableau ».
7. Rechercher `source_ip` à gauche et le glisser dans la zone des lignes du tableau.
8. Ouvrir la dimension créée ; choisir les valeurs les plus fréquentes, 10 valeurs et un ordre décroissant par nombre de documents.
9. Libellé de la ligne : `IP`. Fermer le volet.

#### B. Ajouter les colonnes, une par une

1. Dans la zone des valeurs/calculs, cliquer la première valeur vide ou celle déjà préremplie.
2. Ouvrir « Formule », saisir `count()`, libeller `Messages`, choisir le format Nombre et fermer le volet.
3. Cliquer l’ajout d’un calcul supplémentaire dans la zone des valeurs, pas l’ajout d’une nouvelle ligne.
4. Ouvrir « Formule », saisir `count(kql='auth_record: true')`, libeller `Canoniques`, choisir Nombre et fermer le volet.
5. Ajouter une autre valeur → « Formule » : `count(kql='auth_outcome: "failure"')` ; libellé `Échecs`, format Nombre, puis fermer.
6. Ajouter une autre valeur → « Formule » : `count(kql='auth_outcome: "success"')` ; libellé `Succès`, format Nombre, puis fermer.
7. Ajouter une dernière valeur → « Formule » :

```text
count(kql='auth_outcome: "failure"') / count(kql='auth_record: true')
```

8. Libellé : `Part d’échec canonique`. Format Pourcentage, deux décimales, sans multiplier par 100.
9. Fermer le volet pour lire le tableau.
10. Pour une ligne avec dénominateur nul, conserver l’absence de valeur du ratio ; ne pas la transformer en faux zéro.
11. Sur une ligne où Canoniques > 0, vérifier manuellement Échecs / Canoniques.
12. Trier sur Échecs décroissants si le tri du tableau est disponible. Ce tri s’applique aux lignes présentes dans le top sélectionné ; il ne transforme pas automatiquement ce top de volume en top global des échecs.

#### C. Enregistrer

Les documents sans `source_ip` n’apparaissent pas comme une catégorie ordinaire. Un taux de 100 % avec une ligne n’a pas le même poids que 100 % avec cent lignes : toujours lire le taux et le volume ensemble.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P15 — Analyse par IP — volume et taux canonique` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P15 — Analyse par IP — volume et taux canonique` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 9.2 P16 — Analyse par utilisateur — volume et taux canonique

#### A. Créer les lignes du tableau

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir le type de graphique « Tableau ».
7. Rechercher `user_name` à gauche et le glisser dans la zone des lignes du tableau.
8. Ouvrir la dimension créée ; choisir les valeurs les plus fréquentes, 10 valeurs et un ordre décroissant par nombre de documents.
9. Libellé de la ligne : `Utilisateur`. Fermer le volet.

#### B. Ajouter les colonnes, une par une

1. Dans la zone des valeurs/calculs, cliquer la première valeur vide ou celle déjà préremplie.
2. Ouvrir « Formule », saisir `count()`, libeller `Messages`, choisir le format Nombre et fermer le volet.
3. Cliquer l’ajout d’un calcul supplémentaire dans la zone des valeurs, pas l’ajout d’une nouvelle ligne.
4. Ouvrir « Formule », saisir `count(kql='auth_record: true')`, libeller `Canoniques`, choisir Nombre et fermer le volet.
5. Ajouter une autre valeur → « Formule » : `count(kql='auth_outcome: "failure"')` ; libellé `Échecs`, format Nombre, puis fermer.
6. Ajouter une autre valeur → « Formule » : `count(kql='auth_outcome: "success"')` ; libellé `Succès`, format Nombre, puis fermer.
7. Ajouter une dernière valeur → « Formule » :

```text
count(kql='auth_outcome: "failure"') / count(kql='auth_record: true')
```

8. Libellé : `Part d’échec canonique`. Format Pourcentage, deux décimales, sans multiplier par 100.
9. Fermer le volet pour lire le tableau.
10. Pour une ligne avec dénominateur nul, conserver l’absence de valeur du ratio ; ne pas la transformer en faux zéro.
11. Sur une ligne où Canoniques > 0, vérifier manuellement Échecs / Canoniques.
12. Trier sur Échecs décroissants si le tri du tableau est disponible. Ce tri s’applique aux lignes présentes dans le top sélectionné ; il ne transforme pas automatiquement ce top de volume en top global des échecs.

#### C. Enregistrer

Les documents sans `user_name` n’apparaissent pas comme une catégorie ordinaire. Un taux de 100 % avec une ligne n’a pas le même poids que 100 % avec cent lignes : toujours lire le taux et le volume ensemble.

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P16 — Analyse par utilisateur — volume et taux canonique` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P16 — Analyse par utilisateur — volume et taux canonique` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

## 10. Deux cartes thermiques Lens et une distribution de ports

### 10.1 P17 — Temps × type de message

#### A. Ajouter la matrice

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Ouvrir le menu de graphique et choisir « Carte thermique ».

#### B. Définir les deux axes et la couleur

1. Rechercher `@timestamp` à gauche et le glisser sur « Axe horizontal ».
2. Ouvrir la dimension ; choisir « Histogramme de dates » et une granularité comparable à P09, puis fermer.
3. Rechercher `event_type` et le glisser sur « Axe vertical ».
4. Ouvrir cette dimension ; choisir les valeurs les plus fréquentes, 10 valeurs ou davantage selon les catégories, puis fermer.
5. Cliquer la zone de valeur de cellule et choisir le comptage des documents.
6. Libeller `Lignes par cellule`, format Nombre, puis fermer.
7. Ouvrir les réglages de couleur du graphique et choisir un dégradé séquentiel lisible ; garder la légende.
8. Survoler une case et lire les trois informations : temps, type et nombre de lignes.
9. Vérifier qu’une catégorie dominante peut masquer visuellement une catégorie rare ; cela ne prouve pas une absence de données.

#### C. Enregistrer

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P17 — Intensité des messages — temps × type` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P17 — Intensité des messages — temps × type` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 10.2 P18 — IP × issue canonique

But : comparer deux issues par contributeur. Une seule colonne colorée peut être normale si aucun succès n’existe.

#### A. Ajouter une nouvelle carte thermique Lens

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir « Carte thermique » dans le menu des graphiques.

#### B. Configurer les catégories

1. Dans la barre KQL locale de Lens, saisir `auth_record: true` et appliquer. Ne pas filtrer uniquement sur failure : nous voulons voir les issues reconnues.
2. Rechercher `source_ip` à gauche et le glisser sur « Axe vertical ».
3. Ouvrir cette dimension ; choisir les valeurs les plus fréquentes, 10 valeurs, classement par volume décroissant, puis fermer.
4. Rechercher `auth_outcome` et le glisser sur « Axe horizontal ».
5. Ouvrir cette dimension ; choisir les valeurs les plus fréquentes, 2 valeurs, puis fermer.
6. Dans la valeur de cellule, choisir le comptage des documents.
7. Conserver une palette séquentielle et la légende visible.
8. Survoler une cellule et vérifier qu’elle représente un nombre de lignes pour une IP et une issue, pas un pourcentage.
9. Si seule failure est présente dans les données, noter explicitement « aucun succès dans cet échantillon » plutôt que fabriquer une deuxième colonne.

#### C. Enregistrer

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P18 — IP × issue des enregistrements canoniques` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P18 — IP × issue des enregistrements canoniques` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

### 10.3 P19 — Ports sources par tranches

But : visualiser les ports sources extraits des lignes canoniques. Il ne s’agit ni des ports d’écoute du serveur ni d’un histogramme de temps de réponse.

#### A. Ouvrir le graphique

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
2. Cliquer « Modifier » et vérifier la période complète, sans filtre temporaire global.
3. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » suivant le menu.
4. Choisir Lens si nécessaire, puis la vue `[D08B] OpenSSH Loghub`.
5. Vérifier que les champs sont visibles à gauche et les dimensions à droite ; quitter le mode ES|QL si nécessaire.

6. Choisir des barres verticales.

#### B. Construire des catégories déterministes

1. Dans la barre locale Lens, saisir `auth_record: true and source_port: *` puis appliquer.
2. Cliquer la dimension de l’axe horizontal, sans y déposer un champ.
3. Choisir la fonction de regroupement « Filtres ».
4. Ajouter les quatre expressions KQL et libellés ci-dessous avec le bouton d’ajout de filtre. Remplacer le filtre par défaut plutôt que le conserver en plus s’il ne correspond à aucune tranche.

| Expression | Libellé |
|---|---|
| `source_port >= 0 and source_port < 1024` | `0–1 023` |
| `source_port >= 1024 and source_port < 32768` | `1 024–32 767` |
| `source_port >= 32768 and source_port < 49152` | `32 768–49 151` |
| `source_port >= 49152 and source_port <= 65535` | `49 152–65 535` |

5. Fermer la dimension horizontale.
6. Dans l’axe vertical, choisir le comptage des documents ; libellé `Enregistrements canoniques avec port`.
7. Lire les quatre catégories. Des catégories à zéro sont possibles.
8. Ne pas afficher ces tranches comme un histogramme à classes égales : les largeurs diffèrent. Ce sont des barres catégorielles par plages choisies.

#### C. Enregistrer

1. Cliquer « Enregistrer et revenir ».
2. Si le titre est demandé, saisir `[D08B] P19 — Ports sources — enregistrements canoniques` puis confirmer.
3. Si aucun titre n’est demandé, de retour sur le tableau de bord ouvrir le menu `…` du nouveau panneau, puis ses paramètres ; renseigner `[D08B] P19 — Ports sources — enregistrements canoniques` comme titre et confirmer.
4. Redimensionner le panneau si les libellés sont tronqués.
5. Cliquer « Enregistrer » sur le tableau de bord.

## 11. Trois cartes géographiques complètes

Les trois cartes utilisent le même `source_geo.location` et la même vue de données que les autres panneaux. Ce sont trois objets enregistrés séparément, pas trois sources de données ni trois couches superposées dans un unique panneau. Cela permet de comparer une lecture documentaire, une agrégation spatiale et une densité. Cartes permet ces représentations et leur intégration au tableau de bord. 

### 11.1 Vérification obligatoire avant de tracer

Dans Outils de développement → Console, exécuter séparément :

```http
GET defi08b-openssh/_field_caps?fields=source_geo.location

POST defi08b-openssh/_count
{
  "query": {"exists": {"field": "source_geo.location"}}
}

POST defi08b-openssh/_search
{
  "size": 2,
  "_source": ["source_ip", "source_geo", "geo_source", "geo_reference_at"],
  "query": {"exists": {"field": "source_geo.location"}}
}
```

Attendu : un champ `geo_point`, au moins un document avec coordonnées et une provenance GeoIP déclarée. Si aucune coordonnée n’existe, arrêter P20 à P22 et réparer le prérequis avec le formateur. Ajouter une vue de données ou changer le fond de carte ne crée pas de coordonnées.

### 11.2 P20 — Carte de documents : points et infobulles

Question : quels documents sont associés aux positions disponibles ?

#### A. Créer une carte de points

1. Ouvrir la recherche de navigation Kibana et rechercher « Cartes ».
2. Cliquer l’application Cartes, puis l’action de création d’une carte.
3. Cliquer le sélecteur de temps en haut à droite et choisir la période absolue complète relevée dans la référence. Vérifier l’année conventionnelle 2000 et le fuseau.
4. Appliquer la période, vider la recherche KQL et supprimer les filtres temporaires.
5. Cliquer « Ajouter une couche ».
6. Dans les sources de données Elasticsearch, choisir « Documents ».
7. Dans le sélecteur de vue de données, choisir `[D08B] OpenSSH Loghub`.
8. Si un champ géographique est demandé, sélectionner `source_geo.location` ; ne pas choisir `source_ip`.
9. Poursuivre vers les paramètres de couche et nommer cette couche `Documents GeoIP — positions estimées`.
10. Confirmer l’ajout de la couche avec le bouton proposé par le volet.
11. Utiliser l’action d’ajustement de la vue aux données. Si elle n’est pas visible, dézoomer manuellement jusqu’à voir les points.

#### B. Ajouter les attributs à consulter

1. Dans la liste des couches, cliquer la couche `Documents GeoIP — positions estimées`, puis ouvrir ses paramètres.
2. Repérer la zone des champs d’infobulle et cliquer sur l’action d’ajout.
3. Ajouter `source_ip`.
4. Ajouter `source_geo.country_name` et `source_geo.city_name` s’ils sont proposés.
5. Ajouter `event_type`, `auth_outcome`, `user_name`, `geo_source` et `geo_reference_at` selon les champs disponibles.
6. Confirmer les changements du volet.
7. Survoler ou cliquer un point, suivant l’interaction de la carte, pour ouvrir son infobulle.
8. Lire son IP, son type de message et sa provenance géographique. Une ville absente ne doit pas être remplacée par une ville inventée.
9. Zoomer sur une région, puis revenir à l’étendue du corpus. Des points peuvent se superposer à la même coordonnée.

#### C. Enregistrer la carte puis le tableau de bord

1. Cliquer « Enregistrer » dans l’application Cartes.
2. Saisir `[D08B] P20 — Points GeoIP et détails` et confirmer l’enregistrement dans la bibliothèque.
3. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` dans Tableaux de bord.
4. Cliquer « Modifier ».
5. Ouvrir le menu d’ajout d’un panneau depuis la bibliothèque.
6. Dans la recherche de la bibliothèque, saisir `P20` et sélectionner la carte enregistrée.
7. Fermer le volet d’ajout puis agrandir la carte avec sa poignée de redimensionnement.
8. Vérifier que la période du tableau de bord inclut les données.
9. Cliquer « Enregistrer » sur le tableau de bord.

Contrôle : le panneau P20 est présent et ses infobulles permettent de lire les informations des documents. Le nombre de symboles visibles n’est pas un compteur fiable de toutes les lignes géolocalisées, en raison des superpositions et éventuelles limites d’affichage des documents.

### 11.3 P21 — Carte de regroupements : volumes par zone

Question : où se concentrent les volumes de lignes géolocalisées lorsque l’on agrège spatialement ?

#### A. Créer une carte indépendante

1. Ouvrir « Cartes » dans la navigation Kibana.
2. Cliquer « Créer une carte ». Ne pas rouvrir P20 pour le remplacer.
3. Régler la période absolue complète, retirer les filtres temporaires et vider la recherche KQL.
4. Cliquer « Ajouter une couche ».
5. Choisir la source de regroupements de points/agrégats spatiaux dans les couches Elasticsearch. Le libellé traduit peut varier : chercher l’option qui agrège les points par cellule géographique, plutôt que la couche Documents.
6. Choisir `[D08B] OpenSSH Loghub` comme vue de données.
7. Sélectionner `source_geo.location` comme champ géographique.
8. Dans les calculs de la couche, conserver le nombre de documents comme mesure. Ne pas choisir un dénombrement d’IP si le titre parle de lignes.
9. Nommer la couche `Messages géolocalisés par zone` et confirmer son ajout.

#### B. Associer les symboles aux volumes

1. Ouvrir les paramètres de style de cette couche.
2. Repérer la taille des symboles.
3. Choisir une taille pilotée par une valeur de mesure plutôt qu’une taille uniforme, si ce choix est proposé.
4. Sélectionner la mesure de comptage des documents.
5. Si une étiquette numérique est disponible, choisir le même comptage comme étiquette.
6. Garder une couleur simple et contrastée ; ne pas nommer une couleur « attaque confirmée ».
7. Confirmer les paramètres de couche.
8. Ajuster la carte aux données.
9. Survoler un regroupement et lire son nombre de documents.
10. Zoomer d’un ou deux niveaux puis observer le découpage en sous-groupes ; dézoomer ensuite.

Si la couche de regroupements n’est pas proposée dans ce déploiement, ne pas prétendre que des points individuels en sont l’équivalent. Le formateur vérifie le type de source disponible et prépare cette étape sur sa version ; conserver P20 et documenter cette limite en attendant.

#### C. Enregistrer et intégrer

1. Cliquer « Enregistrer » dans Cartes.
2. Nommer `[D08B] P21 — Volumes GeoIP regroupés` et confirmer.
3. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` et cliquer « Modifier ».
4. Ouvrir l’ajout depuis la bibliothèque ; rechercher `P21`.
5. Cliquer la carte enregistrée pour l’ajouter, puis fermer le volet.
6. Placer ce panneau à côté ou sous P20 et agrandir sa zone.
7. Enregistrer le tableau de bord.

Contrôle : les symboles représentent des volumes agrégés de documents et changent avec le zoom ; ils ne désignent ni une IP unique ni un nombre de personnes. Les agrégations spatiales sous-jacentes regroupent les documents dans une grille. 

### 11.4 P22 — Carte de densité des échecs géolocalisés

Question : quelle est la concentration spatiale des lignes d’échec pour lesquelles des coordonnées sont disponibles ?

#### A. Vérifier qu’il existe des échecs géolocalisés

Dans le fichier de contrôle, lire `aggregations.located_failures.doc_count`. Si cette valeur est nulle mais G > 0, réaliser la même carte sans filtre d’échec et utiliser le titre de repli indiqué ci-dessous. Ne pas inventer d’événement.

#### B. Créer la couche de densité

1. Ouvrir « Cartes », puis cliquer « Créer une carte » pour créer un objet indépendant de P20 et P21.
2. Régler la période complète sur les bornes du corpus et retirer les filtres temporaires.
3. Cliquer « Ajouter une couche ».
4. Sélectionner la couche « Carte thermique » géographique dans les sources proposées.
5. Choisir la vue `[D08B] OpenSSH Loghub`.
6. Sélectionner `source_geo.location` comme champ géographique.
7. Conserver une pondération par nombre de documents ; ne pas utiliser `repeat_count` pour simuler des tentatives distinctes.
8. Donner à la couche le nom `Densité des échecs géolocalisés`.
9. Confirmer l’ajout de couche.
10. Si des échecs géolocalisés existent, saisir dans la barre KQL de cette carte `auth_outcome: "failure"` et appliquer. La carte sera enregistrée avec ce filtre ; le titre doit donc indiquer le périmètre d’échec.
11. Si aucun échec géolocalisé n’existe, garder la barre KQL vide et renommer la couche `Densité des messages géolocalisés`.

#### C. Régler et lire la densité

1. Ouvrir les paramètres de style de la couche.
2. Choisir un dégradé lisible allant des concentrations faibles aux concentrations fortes.
3. Si un rayon d’influence est proposé, le modifier légèrement pour voir son effet visuel, puis choisir un réglage documenté et lisible.
4. Ajuster l’étendue de la carte pour couvrir les données.
5. Zoomer puis dézoomer : la perception de densité dépend de l’échelle et du style.
6. Ne pas comparer une couleur rouge à une valeur absolue de risque. Cette représentation est une densité de documents, pas un taux normalisé d’activité hostile.

#### D. Enregistrer puis ajouter au tableau de bord

1. Cliquer « Enregistrer ».
2. Si le filtre d’échec est actif, saisir `[D08B] P22 — Densité des échecs géolocalisés`.
3. Dans le cas de repli sans échecs géolocalisés, saisir `[D08B] P22 — Densité des messages géolocalisés`.
4. Confirmer la sauvegarde de la carte.
5. Ouvrir le tableau de bord en modification.
6. Ajouter un panneau depuis la bibliothèque, rechercher `P22` et cliquer la carte.
7. Fermer le volet, agrandir le panneau puis enregistrer le tableau de bord.

Contrôle : la couche est bien géographique. Elle ne contient pas les axes temps/type de P17 ; les deux « cartes thermiques » ne mesurent pas la même chose. [web:155]

### 11.5 Géolocalisation et filtre de temps : limites à afficher

- Une adresse publique peut ne pas être géolocalisée ; les documents sans point ne sont pas représentés.
- Une position GeoIP est approximative et peut représenter un fournisseur ou une sortie réseau.
- La date de référence GeoIP n’est pas la date historique de l’événement.
- Une carte ne prouve ni la position d’une personne ni sa nationalité ou son intention.
- Si le fond est vide, vérifier le service de fond cartographique autorisé sans confondre cette panne avec l’absence de coordonnées. Ne pas désactiver TLS.

## 12. Ajouter deux tables documentaires pour lire les preuves

### 12.1 P23 — Détail des échecs canoniques

#### A. Construire la table dans Découvrir

1. Ouvrir « Découvrir » dans la navigation Kibana.
2. Choisir `[D08B] OpenSSH Loghub` en mode vue de données/KQL.
3. Régler la période absolue complète, supprimer les filtres temporaires.
4. Dans la barre KQL, saisir `auth_outcome: "failure"` et appliquer.
5. Dans la recherche de champs à gauche, saisir `source_ip`.
6. Survoler le champ puis cliquer son action d’ajout en colonne.
7. Effacer la recherche de champ et recommencer pour `user_name`, `auth_method`, `source_geo.country_name`, `geo_status` et `message`.
8. Conserver la colonne `@timestamp`.
9. Déplacer les en-têtes par glisser-déposer pour obtenir : date, IP, utilisateur, méthode, pays, état géographique, message.
10. Agrandir la colonne du message en faisant glisser sa bordure si nécessaire.
11. Cliquer l’en-tête de date pour obtenir le tri voulu et lire plusieurs lignes.
12. Ouvrir une ligne avec sa flèche de détail et vérifier qu’elle correspond à une authentification canonique reconnue, pas à un résumé de répétition.

#### B. Enregistrer la session et l’ajouter

1. Cliquer « Enregistrer » dans Découvrir.
2. Saisir `[D08B] P23 — Détail des échecs canoniques` et confirmer.
3. Éviter de conserver une période locale différente de celle du tableau de bord si le choix est proposé.
4. Ouvrir `[D08B] Observabilité OpenSSH — Loghub` puis cliquer « Modifier ».
5. Ouvrir l’ajout depuis la bibliothèque et rechercher `P23` ; choisir la session de Découvrir.
6. Fermer le volet, agrandir le panneau pour plusieurs lignes lisibles puis enregistrer le tableau de bord.

Contrôle : cette table contient ses propres échecs, mais le total P01 continue à porter sur le corpus global en l’absence de filtre global.

### 12.2 P24 — Lignes avec IP mais sans coordonnées

Question : quelles informations sont absentes de la carte alors que nous avons extrait une IP ?

#### A. Créer la table de diagnostic

1. Ouvrir « Découvrir » et choisir `[D08B] OpenSSH Loghub`.
2. Reprendre la période complète et retirer les filtres de la session précédente.
3. Remplacer la barre KQL par :

```kql
source_ip: * and not source_geo.location: *
```

4. Appliquer la recherche.
5. Ajouter les colonnes, une à une depuis les champs à gauche : `source_ip`, `source_ip_public`, `geo_status`, `geo_source`, `tags`, `event_type`, `message`, en conservant la date.
6. Pour chaque ajout, rechercher le champ puis cliquer l’action de mise en colonne ; effacer la recherche avant le champ suivant.
7. Réordonner les colonnes en faisant glisser leurs en-têtes.
8. Ouvrir plusieurs documents. Distinguer une IP non publique d’une IP publique sans résultat, et rechercher les tags d’erreur.
9. Si cette recherche ne retourne rien et que G = I, ce résultat est cohérent : tous les documents avec IP ont des coordonnées dans ce périmètre.

#### B. Enregistrer et intégrer

1. Cliquer « Enregistrer » dans Découvrir.
2. Nommer `[D08B] P24 — IP sans coordonnées` et confirmer.
3. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` en modification.
4. Ajouter depuis la bibliothèque la session trouvée en recherchant `P24`.
5. Agrandir le panneau, puis enregistrer le tableau de bord.

Ne pas nommer ce panneau « erreurs de parsing » : l’absence de coordonnées peut être légitime ou liée à la base GeoIP, même lorsque l’extraction de l’IP est correcte.

## 13. P25 — Texte de contexte obligatoire

1. Ouvrir le tableau de bord et cliquer « Modifier ».
2. Cliquer « Ajouter » et choisir le panneau de texte/Markdown.
3. Dans l’éditeur de texte, copier le bloc suivant puis remplacer les éléments entre crochets par vos valeurs :

```markdown
### Lire ce tableau de bord
- Source : Loghub, OpenSSH_2k.log ; révision [révision], SHA-256 [empreinte].
- Période affichée : [début] à [fin], fuseau [fuseau].
- Année 2000 et UTC : conventions de parsing, année/fuseau non donnés par la source.
- Un document est une ligne, pas une session ni une personne.
- Taux canonique : F / A, avec F = [valeur], A = [valeur].
- Les messages PAM et les résumés répétés ne sont pas ajoutés au dénominateur canonique.
- Couverture GeoIP : G / I, avec G = [valeur], I = [valeur].
- GeoIP : estimation à la date de référence, pas preuve d’une localisation historique.
- La carte ne montre pas les documents sans coordonnées.
- Les tops ne sont pas des listes exhaustives ; les filtres changent tous les dénominateurs concernés.
```

4. Prévisualiser si le bouton existe et vérifier que tous les éléments entre crochets ont été remplacés.
5. Confirmer l’ajout du panneau ; titre `[D08B] P25 — Contrat de lecture`.
6. Placer ce texte sous les contrôles en le faisant glisser par son en-tête.
7. Enregistrer le tableau de bord.

## 14. Ajouter quatre contrôles interactifs

Les contrôles ne sont pas comptés parmi les 25 panneaux. Ils pilotent le périmètre de lecture et sont à réinitialiser avant comparaison aux références globales. [web:156]

### 14.1 Liste « Type de message »

1. Ouvrir le tableau de bord en modification.
2. Ouvrir le menu de gestion/ajout des contrôles et cliquer l’action d’ajout d’un contrôle.
3. Choisir `[D08B] OpenSSH Loghub` comme vue.
4. Choisir `event_type` comme champ.
5. Choisir une liste d’options et saisir `Type de message` comme libellé.
6. Autoriser plusieurs valeurs si ce réglage est proposé.
7. Enregistrer le contrôle.
8. Dans la nouvelle liste, sélectionner un type réellement présent et observer les panneaux.
9. Effacer la sélection avant de créer les autres contrôles.

### 14.2 Liste « IP source »

1. Toujours en modification, ajouter un nouveau contrôle.
2. Vue : `[D08B] OpenSSH Loghub` ; champ : `source_ip`.
3. Choisir une liste d’options ; libellé `IP source`.
4. Enregistrer.
5. Sélectionner une IP présente dans P12, vérifier le changement des volumes et consulter P23.
6. Effacer la sélection.

### 14.3 Liste « Utilisateur observé »

1. Ajouter un nouveau contrôle dans le même tableau de bord.
2. Choisir `[D08B] OpenSSH Loghub`, puis le champ `user_name`.
3. Choisir une liste d’options, libeller `Utilisateur observé` et enregistrer.
4. Sélectionner un nom présent dans P13, lire P16 puis effacer la sélection.
5. Noter que les documents sans ce champ sont exclus lorsque l’on sélectionne un utilisateur.

### 14.4 Liste « Pays GeoIP »

1. Ajouter un quatrième contrôle.
2. Choisir la vue du défi, puis `source_geo.country_name`.
3. Choisir une liste d’options et saisir `Pays GeoIP`.
4. Enregistrer et choisir un pays disponible.
5. Observer la carte et le KPI de couverture. Un filtre de pays élimine les documents sans pays et change le dénominateur ; il ne signifie pas que la couverture globale du corpus s’est améliorée.
6. Effacer le pays sélectionné et enregistrer le tableau de bord sans filtre de test.

Si aucune valeur n’existe pour un champ, contrôler les données ; ne pas créer des valeurs fictives pour remplir une liste.

## 15. Assembler un tableau de bord lisible

### 15.1 Disposition proposée

```text
Contrôles : type | IP | utilisateur | pays
P25 Contrat de lecture

P01 Documents | P02 Canoniques | P03 Échecs | P04 Succès
P05 IP estimées | P06 Part d’échec | P07 Couverture | P08 Sans IP

P09 Volume temporel, grande largeur
P10 Échecs/succès dans le temps | P11 Anneau des types
P12 IP des échecs | P13 Utilisateurs des échecs | P14 Pays
P15 Tableau IP | P16 Tableau utilisateurs
P17 Temps × type | P18 IP × issue
P19 Ports sources par tranches

P20 Points GeoIP, grande largeur
P21 Regroupements | P22 Densité

P23 Détail des échecs, grande largeur
P24 IP sans coordonnées, grande largeur
```

### 15.2 Placer chaque panneau

1. Passer le tableau de bord en modification.
2. Repérer le panneau par son identifiant P01, P02, etc. dans son titre.
3. Maintenir le clic sur son en-tête, le déplacer dans la grille puis relâcher à la position voulue.
4. Redimensionner avec la poignée du coin inférieur pour lire titres et légendes.
5. Donner plus de largeur à l’histogramme, aux cartes et aux tables documentaires.
6. Garder une hauteur suffisante aux listes IP/utilisateurs ; éviter les grandes zones vides autour des petits indicateurs.
7. Vérifier que les filtres temporaires sont retirés et que la période complète est rétablie.
8. Enregistrer, revenir à la liste des tableaux de bord puis rouvrir celui-ci.
9. Vérifier la présence des 25 panneaux. En cas d’étape cartographique indisponible, conserver la fiche de limitation, sans la compter comme une carte fonctionnelle.

## 16. Vérifier et inspecter sans deviner les chiffres

### 16.1 Grille de validation

| Panneau | Contrôle dans le contexte complet |
|---|---|
| P01 | Égal à N si toutes les dates sont présentes et incluses |
| P02 | Égal à A |
| P03/P04 | F et S ; F + S = A |
| P05 | Cardinalité estimée U, différence locale éventuelle explicitée |
| P06 | F / A, format pourcentage, A > 0 |
| P07 | G / I, I > 0 |
| P08 | (N - I) / N, N > 0 |
| P09/P10 | Même période et granularité documentée ; zéro succès possible |
| P11 | Types réellement présents, restes/Autre expliqués |
| P12/P13/P14 | Filtres locaux et champs manquants explicités |
| P15/P16 | Ratios recalculables pour les lignes présentes, tops non exhaustifs |
| P17/P18 | Deux regroupements et un comptage, pas un faux pourcentage |
| P19 | Ports sources, tranches non chevauchantes, pas latence |
| P20/P21/P22 | Coordonnées réelles disponibles, périodes compatibles, couches nommées |
| P23 | Recherche locale d’échec, preuve documentaire accessible |
| P24 | I - G documents, si tous les localisés sont dans le périmètre avec IP |
| P25 | Convention de date, provenance et limites renseignées |

### 16.2 Utiliser l’inspecteur d’un panneau Lens

1. Sur le tableau de bord, ouvrir le menu `…` du panneau P09.
2. Choisir l’action d’inspection. Si elle est dans l’éditeur, ouvrir la visualisation puis le menu complémentaire d’inspection.
3. Dans l’inspecteur, consulter les données renvoyées puis les requêtes.
4. Repérer le filtre temporel et les regroupements.
5. Comparer au périmètre utilisé dans la référence ; ne pas comparer une fenêtre réduite au total global.
6. Fermer l’inspecteur et revenir au tableau de bord.

Les actions d’inspection et d’export varient selon le type de panneau ; ne pas supposer que le menu d’une carte est identique à celui d’un graphique Lens. [web:156]

## 17. Investigation guidée : passer d’un graphique à une preuve

1. Sans filtre, noter P01, P03, P06 et P07.
2. Dans P09, repérer une fenêtre contenant des messages.
3. Sélectionner une courte fenêtre par cliquer-glisser horizontal sur le graphique, si l’interaction est proposée ; sinon utiliser le sélecteur de temps pour la définir explicitement.
4. Dans le contrôle Type, choisir `auth_failure` si cette catégorie existe.
5. Lire les IP de P12 et sélectionner l’une d’elles dans le contrôle IP source.
6. Lire P15 puis les documents P23 pour cette adresse.
7. Ouvrir un document et relever le texte brut, la méthode et le nom observé.
8. Examiner P20/P21 : une position apparaît-elle ? Si non, lire la couverture et le diagnostic sans supposer une absence de trafic.
9. Écrire quatre lignes : fait observé, périmètre, hypothèse, preuve manquante.
10. Effacer les filtres de contrôle et restaurer la période complète.
11. Vérifier le retour des chiffres de référence avant de sauvegarder.

Exemple de conclusion prudente : « Dans cette fenêtre et pour cette IP, nous observons X lignes canoniques d’échec et les noms présents dans les messages. Une position GeoIP est disponible / absente. Ces éléments ne prouvent pas l’identité ou la localisation historique d’une personne. Une analyse d’incident nécessiterait d’autres journaux et le contexte du serveur. »

## 18. Dépannage des manipulations, pas seulement des concepts

| Blocage | Action concrète |
|---|---|
| Je vois un éditeur ES|QL | Revenir au mode de création par champs/dimensions avant de glisser les champs |
| Le champ est déposé au mauvais endroit | Retirer la dimension créée puis glisser sur l’axe nommé ; ne pas modifier la source |
| La fonction proposée n’est pas celle demandée | Cliquer la dimension et choisir explicitement le calcul au lieu de garder la suggestion |
| Je ne vois pas « Indicateur » | Vérifier le menu de type de graphique dans Lens, pas l’ajout de couche dans Cartes |
| Une formule apparaît en rouge | Ouvrir l’onglet Formule ; contrôler champs, parenthèses et apostrophes droites |
| La recherche KQL refuse count(...) | Déplacer cette expression vers une dimension Formule ; la barre KQL attend un filtre |
| Un indicateur affiche une absence de valeur | Vérifier le dénominateur et la présence de données ; ne pas forcer un faux zéro |
| Tous les taux passent à 100 % | Retirer le filtre d’échec global et revoir le périmètre |
| Une barre unique remplit le temps | Vérifier les bornes réelles, puis réduire le minimum d’intervalle si utile |
| Un top manque une IP connue | Vérifier son filtre local, les dix premières catégories et les champs absents |
| Le pays n’est pas affiché alors que le point existe | Une coordonnée peut exister sans ce libellé ; conserver l’absence |
| Une carte est vide | G, type geo_point, vue exacte, année 2000, fuseau et filtres |
| La carte a des points mais pas de fond | Faire vérifier le service de tuiles autorisé, pas le parsing de l’IP |
| Les points semblent trop peu nombreux | Vérifier superposition, limite de documents affichés et lecture agrégée P21 |
| Je ne trouve plus mon panneau | Vérifier l’enregistrement Lens/Cartes puis l’enregistrement du tableau de bord |
| P22 ne montre aucun échec localisé | Contrôler located_failures ; utiliser la densité de tous les localisés et adapter le titre |

## 19. Livrables et évaluation

Remettre :

- Capture lisible de l’organisation générale et de chaque carte.
- Tableau de validation des valeurs de référence complété.
- Tableau de bord rouvert après enregistrement.
- Fichiers de préparation et réponse Bulk du pack initial.
- Révision et SHA-256 du fichier source, convention de date et mode GeoIP utilisé.
- Une investigation avec preuve documentaire et limites, sans cause inventée.
- Export des objets Kibana si les droits le permettent ; rappeler qu’il ne contient pas les documents Elasticsearch ni nécessairement les secrets/configurations externes.

| Domaine | Points |
|---|---:|
| Données, mapping, Bulk et qualité | 4 |
| Huit indicateurs et dénominateurs | 4 |
| Temps, contributeurs, tableaux et matrices | 4 |
| Trois lectures cartographiques, provenance et couverture | 4 |
| Détails documentaires, contrôles et investigation | 2 |
| Lisibilité, enregistrement et réouverture | 2 |
| Total | 20 |

La quantité seule n’est pas l’objectif : un panneau sans donnée réelle ni question clairement nommée ne reçoit pas automatiquement des points. Le formateur adapte le nombre de cartes exigibles à l’environnement préparé, sans pénaliser un stagiaire pour une base GeoIP non disponible avant la séance.

## 20. Portée de cette révision

Ce document enrichit le parcours de visualisation en conservant le schéma du premier pack et les préférences d’interface de l’atelier 8. Le JSON de contrôle a été vérifié syntaxiquement, de même que la cohérence des noms de champs et la liste des 25 panneaux. Aucun chiffre de production n’est inventé : ils sont à relever sur le corpus effectivement importé.

Les opérations Elasticsearch, le service GeoIP et les clics exacts de votre instance Kibana 9.5.7 n’ont pas été exécutés pendant cette rédaction. Les fonctions de tableaux, indicateurs, cartes thermiques, cartes multicouches et filtres sont appuyées sur la documentation ; 
