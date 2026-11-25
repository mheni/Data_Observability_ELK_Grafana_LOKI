# Défi 08 bis — Observer des logs OpenSSH de Loghub avec Elasticsearch et Kibana

Version cible : Elasticsearch / Kibana 9.5.7.

## 1. Fiche pédagogique

| Élément | Choix |
|---|---|
| Place dans le parcours | Après l’atelier 8 : réinvestissement autonome, puis correction guidée |
| Corpus | Loghub, échantillon `OpenSSH/OpenSSH_2k.log` |
| Volume annoncé par le dépôt | 2 000 lignes pour l’échantillon, pas l’intégralité du corpus OpenSSH |
| Durée | Défi : 1 h 30 à 2 h ; correction accompagnée : 2 h à 3 h ; options : 30 à 45 min |
| Index dédié | `defi08b-openssh` |
| Vue de données | `[D08B] OpenSSH Loghub` |
| Tableau de bord | `[D08B] Observabilité OpenSSH — Loghub` |
| Cartographie | Positions issues d’un enrichissement GeoIP réel des IP extraites |
| Prérequis | Atelier 8 terminé, Python 3, git, curl, cluster accessible et droits adaptés |


### Pourquoi ce corpus ?

OpenSSH fournit des messages d’authentification et de connexion avec des IP publiques, des utilisateurs, des ports et des types de messages variés. Le fichier consulté contient notamment des lignes `Failed password`, `Invalid user`, des messages PAM, des déconnexions et des résumés `message repeated`. Cela permet un tableau de bord différent du HTTP tout en réutilisant Bulk, Lens et Cartes. 

Attention : ces logs ne contiennent pas de coordonnées natives. La géolocalisation est ajoutée par GeoIP. Nous choisissons donc un corpus géolocalisable, pas un fichier prétendument déjà muni de latitude/longitude. Le jeu Apache de Loghub est présenté comme un journal d’erreurs, et non comme l’access log de l’atelier 8 : on ne lui attribue pas automatiquement les mêmes champs. 

## 2. Points de vigilance avant de distribuer le défi

### 2.1 Les dépendances obligatoires pour une vraie carte

Le formateur doit valider avant la séance :

- Téléchargement de l’échantillon OpenSSH ou copie locale autorisée.
- Fonctionnement du pipeline GeoIP sur des IP réellement présentes dans cet échantillon.
- Au moins un document avec `source_geo.location` après simulation et après import ; plusieurs positions sont préférables pour enseigner les regroupements.
- Fonctionnement de Cartes et accès au fond cartographique autorisé.
- Droits de lecture/création d’index, gestion du pipeline pour le formateur, vues de données, visualisations et tableaux de bord.

Le processeur GeoIP s’appuie sur une base de géolocalisation ; sa création peut déclencher le téléchargement de la base. Ce téléchargement n’est ni immédiat ni garanti dans un réseau filtré. Une IP publique ne garantit pas non plus une coordonnée disponible. 

Si la VM est isolée, utiliser le cache de véritables résultats GeoIP exporté par le formateur selon la section 18. Le pack ne contient pas de cache géographique réel préfabriqué et ne prétend pas embarquer une base GeoIP. Sans base opérationnelle ni cache réel préparé, le défi cartographique ne peut pas être validé : le reporter plutôt que créer des villes fictives.

### 2.2 Licence et confidentialité

Loghub indique une disponibilité pour la recherche ou le travail académique, avec attribution au dépôt, citation du travail Loghub lorsque pertinente et conservation de la notice dans les copies. Avant un usage commercial ou une redistribution dans une formation payante, vérifier les conditions applicables ; ce document n’accorde pas de droits supplémentaires. Les logs peuvent contenir des IP et des noms d’utilisateurs. Ne pas contacter, scanner ou tester les serveurs correspondant à ces adresses. 

Le pack pédagogique ne redistribue pas l’échantillon complet ni une base GeoIP. Il fournit les scripts et le chemin d’acquisition. Préparer une copie locale autorisée si l’accès GitHub est bloqué pendant la formation.

### 2.3 Dates incomplètes et interprétation

Les lignes consultées commencent par exemple par `Dec 10 06:55:46` : l’année et le fuseau ne sont pas indiqués. Le convertisseur impose une convention explicite : année 2000 et décalage UTC +0000. Ce ne sont pas des métadonnées historiques prouvées. Elles servent à créer un axe temporel reproductible et sont inscrites dans `timestamp_policy`. 

Ne pas réhorodater silencieusement à aujourd’hui. Ne pas inventer une heure différente par numéro de ligne. Pour cet échantillon, nous positionnons les mois/jours/heures tels qu’ils apparaissent sous la convention choisie ; le script ne déduit pas un changement d’année. Si un autre corpus traverse décembre/janvier, définir et documenter une nouvelle politique avant l’import.

### 2.4 Ce que nous comptons

- Un document = une ligne du fichier acceptée par le parseur.
- Une connexion peut produire plusieurs lignes : document n’est pas synonyme de session ou tentative.
- `auth_record:true` désigne uniquement une ligne canonique reconnue `Failed ... for ... from ... port ...` ou `Accepted ...` pour les méthodes gérées par le script.
- Les messages PAM sont conservés mais ne sont pas ajoutés au dénominateur de ce taux.
- `message repeated N times` reste un document de catégorie `message_repeat`, avec `repeat_count=N`. Il n’est pas développé en N fausses lignes horodatées.
- Le taux d’échec porte donc sur les enregistrements canoniques reconnus, pas sur toutes les tentatives réelles du serveur.
- Une géolocalisation actuelle d’une IP ancienne n’établit pas sa localisation au moment du log, ni celle d’une personne.

Ces règles évitent les doubles comptages et les interprétations abusives des messages réellement visibles dans l’échantillon. 

---

# Partie A — Énoncé du défi, sans consulter le corrigé

## 3. Mission

Vous êtes chargé de préparer un tableau de bord d’observabilité pour un service SSH. À partir de l’échantillon OpenSSH de Loghub, vous devez répondre à ces questions :

1. Quel volume de lignes avons-nous réellement indexé ?
2. Quels messages d’authentification canoniques sont des échecs ou des succès ?
3. Quelles IP et quels noms d’utilisateurs contribuent aux échecs observés ?
4. À quels moments les messages sont-ils les plus nombreux ?
5. Quelle part des documents avec IP est géolocalisée ?
6. Que montre une carte des points GeoIP et que ne peut-elle pas prouver ?
7. Quels documents permettent de justifier votre interprétation ?

### Contraintes

- Ne pas modifier les index des ateliers précédents.
- Préparer un NDJSON et utiliser explicitement `curl` avec l’API `_bulk`.
- Définir le mapping avant le chargement, dont `source_ip: ip` et `source_geo.location: geo_point`.
- Utiliser des identifiants stables et contrôler chaque opération Bulk.
- Conserver les messages bruts, les lignes non reconnues dans un fichier de rejet et la provenance du fichier.
- Ne pas inventer de coordonnées, de succès d’authentification ou de durée de session.
- Utiliser les vraies dates de jour/heure sous une convention d’année/fuseau déclarée.
- Ne jamais présenter une IP ou un pays comme la preuve d’une attaque ou l’identité de son auteur.

## 4. Livrables attendus

| Panneau | Mesure / dimension attendue |
|---|---|
| Indicateur 1 | Nombre de documents |
| Indicateur 2 | Nombre d’échecs canoniques |
| Indicateur 3 | IP distinctes estimées |
| Indicateur 4 | Part d’échec parmi les enregistrements canoniques |
| Indicateur 5 | Part des documents avec IP qui ont des coordonnées |
| Histogramme temporel | Documents par temps et type de message |
| Barres horizontales | Top 10 IP par nombre d’échecs canoniques |
| Table agrégée | Utilisateur, volume de messages, échecs canoniques |
| Carte thermique | Temps × type de message, couleur = nombre de documents |
| Table documentaire | Lignes d’échec et détails consultables |
| Carte principale | Points des documents GeoIP réels, infobulles et regroupements si disponibles |
| Contrôles | Type de message, utilisateur ; pays si plusieurs pays sont présents |
| Texte de contexte | Source, convention de dates, définition du taux, couverture et limites GeoIP |

À remettre : Markdown de compte rendu, mapping, pipeline, NDJSON, rapports de préparation et Bulk, capture du tableau de bord, carte enregistrée et trois observations justifiées.

## 5. Critères de réussite

1. Le nombre de documents préparés correspond aux opérations Bulk réussies et au total de l’index neuf.
2. Les compteurs d’échecs et d’authentification sont cohérents entre préparation locale et Elasticsearch.
3. La période de Kibana inclut le minimum et le maximum mesurés, sous l’année conventionnelle.
4. Le calcul des taux utilise le bon dénominateur, sans multiplication par 100 quand le format est Pourcentage.
5. La carte utilise `source_geo.location`, pas l’IP seule, et montre au moins un document géolocalisé.
6. Les panneaux et le tableau de bord sont enregistrés puis réouverts.
7. Le compte rendu distingue fait observé, hypothèse et limite des données.

---

# Partie B — Correction détaillée et guidée

## 6. Préparer le dossier et récupérer les logs

### 6.1 Extraire le pack

1. Extraire le pack du défi sur la VM de formation.
2. Ouvrir un terminal dans le dossier qui contient `preparer_openssh.py` et les fichiers JSON.
3. Vérifier :

```bash
pwd
ls preparer_openssh.py verifier_reponse.py openssh-mapping.json openssh-geoip-pipeline.json
python3 --version
git --version
curl --version
```

Les commandes suivantes sont à lancer depuis ce dossier. Un fichier de réponse JSON n’existe qu’après exécution de la commande qui le crée.

### 6.2 Télécharger l’échantillon, pas tout le corpus historique

Le dépôt expose l’échantillon dans `OpenSSH/OpenSSH_2k.log`. Le corpus complet OpenSSH couvre plus de 28 jours ; cette durée ne doit pas être attribuée automatiquement à l’échantillon de 2 000 lignes. 

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/logpai/loghub.git loghub-source
git -C loghub-source sparse-checkout set OpenSSH
cp loghub-source/OpenSSH/OpenSSH_2k.log ./OpenSSH_2k.log
cp loghub-source/LICENSE ./LICENSE_LOGHUB_SOURCE.txt
git -C loghub-source rev-parse HEAD > loghub-commit.txt
wc -l OpenSSH_2k.log
head -n 8 OpenSSH_2k.log
```

Si `loghub-source` existe déjà, ne pas recloner dans ce dossier : vérifier son origine et sa révision, puis reprendre la copie. Si le proxy refuse le clonage partiel, le formateur prépare une copie autorisée ; il conserve la révision, le SHA-256 et la notice de licence. Ne pas télécharger les tableaux CSV structurés à la place du fichier `.log` pour ce défi de parsing.

Résultat attendu annoncé par le dépôt : 2 000 lignes. Le rapport du script et le fichier réellement récupéré sont les références de contrôle ; une page HTML ou un fichier vide n’est pas un corpus valide. 

### 6.3 Configurer l’accès Elasticsearch

Réutiliser le choix de sécurité de l’atelier 1. Dans le terminal Bash, préparer un tableau d’options pour ne pas oublier l’authentification sur certaines commandes.

Variante sans sécurité uniquement :

```bash
export ES_URL='http://localhost:9200'
CURL_ES=(curl --fail-with-body -sS)
```

Variante sécurisée, en conservant votre chemin de certificat réel :

```bash
export ES_URL='https://localhost:9200'
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD; printf '\n'
CURL_ES=(curl --fail-with-body -sS --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD")
```

Tester :

```bash
"${CURL_ES[@]}" "$ES_URL/"
```

Ne pas utiliser `-k` et ne pas publier les secrets. Le tableau Bash n’est disponible que dans le terminal où il est défini : le redéfinir après reconnexion. Les commandes Console ne doivent contenir ni `curl`, ni mot de passe.

## 7. Préparer le NDJSON et connaître le corpus

### 7.1 Exécuter la préparation

```bash
python3 preparer_openssh.py OpenSSH_2k.log --outdir preparation --year 2000 --utc-offset +0000
cat preparation/preparation.json
head -n 4 preparation/openssh.ndjson
wc -l preparation/rejets.ndjson
```

Le script ne contacte aucun serveur et ne modifie pas la source. Il crée :

| Fichier | Rôle |
|---|---|
| `preparation/openssh.ndjson` | Paires action/document pour Bulk |
| `preparation/preparation.json` | Comptages, bornes, SHA-256, convention de date et rejets |
| `preparation/rejets.ndjson` | Lignes refusées et causes |
| `preparation/geo-simulate.json` | Jusqu’à 50 documents avec des IP publiques distinctes réellement extraites pour tester GeoIP |

### 7.2 Comprendre le traitement

1. Le script reconnaît l’en-tête mois/jour/heure/hôte/programme/PID.
2. Il construit `@timestamp` avec l’année et le décalage explicitement choisis.
3. Il classe le contenu, sans assimiler toutes les lignes à des tentatives.
4. Il extrait une IP littérale dans des contextes connus : `from`, `by`, `rhost=` et avertissement DNS. Il ne résout pas les noms d’hôtes en adresses actuelles et ne propage pas une IP d’une ligne voisine.
5. Il conserve `message`, `content`, `line_number` et `source_file_sha256`.
6. Il utilise un identifiant déterministe issu du fichier, de la politique de date et du numéro de ligne.
7. Sans cache GeoIP, il n’invente aucune coordonnée.

Changer l’année, le fuseau ou le fichier change les identifiants : ne pas mélanger des variantes dans le même index si vous souhaitez conserver des comptes comparables. Le même fichier avec les mêmes paramètres produit les mêmes identifiants.

### 7.3 Compléter les références avant de poursuivre

| Référence | Où lire la valeur |
|---|---|
| N, documents préparés | `documents` |
| Rejets | `rejected` |
| Échecs canoniques | `event_types_and_quality.auth_failure`, ou 0 si absent |
| Succès canoniques | `event_types_and_quality.auth_success`, ou 0 si absent |
| A, enregistrements canoniques | Échecs + succès |
| I, documents avec IP | `event_types_and_quality.with_ip`, ou 0 |
| IP distinctes exactes locales | `distinct_ips_exact_local` |
| Dates minimale et maximale | `first_event`, `last_event` |
| Résumés de répétition | `event_types_and_quality.message_repeat`, ou 0 |

Ne pas exiger un nombre de succès supérieur à zéro. Si aucun succès n’est présent dans l’échantillon, le KPI de succès vaut zéro et le taux d’échec peut valoir 100 % parmi les seuls enregistrements reconnus. Il ne décrit pas la disponibilité de SSH.

Arrêter si N = 0. En cas de rejet, lire le message et décider avec le formateur : corriger le parseur ou documenter le périmètre exclu. Ne pas envoyer un NDJSON partiellement écrit après une exception Python.

## 8. Définir le mapping et tester GeoIP avant le chargement

### 8.1 Comprendre les champs utiles

| Champ | Type | Utilisation |
|---|---|---|
| `@timestamp` | date | Axe temporel sous convention déclarée |
| `timestamp_policy` | keyword | Transparence sur année/fuseau |
| `event_type` | keyword | Classement, contrôles, ventilation |
| `auth_record` | boolean | Dénominateur des enregistrements canoniques |
| `auth_outcome` | keyword | failure / success / not_applicable |
| `user_name` | keyword | Regroupement par nom observé |
| `source_ip` | ip | Recherche et cardinalité des adresses |
| `source_ip_public` | boolean | Classification par la bibliothèque Python ipaddress |
| `source_geo.location` | geo_point | Tracé des points dans Cartes |
| `source_geo.country_name` | keyword | Regroupement géographique |
| `geo_status` | keyword | located / not_located / no_ip |
| `geo_source` | keyword | elasticsearch_geoip / geoip_cache / none |
| `geo_reference_at` | date | Date du calcul ou de l’export de référence |
| `repeat_count` | integer | Nombre annoncé par une ligne de résumé, sans expansion |
| `message` | text | Preuve documentaire brute |

Les objets géographiques doivent être mappés explicitement : deux nombres seuls ne suffisent pas à définir un `geo_point`. [web:118]

### 8.2 Vérifier l’existence de l’index

Dans Console :

```http
GET defi08b-openssh/_count
GET defi08b-openssh/_mapping
```

- Index absent : créer ci-dessous.
- Index existant et compatible, uniquement même corpus : examiner son contenu et décider d’un rejeu contrôlé.
- Index d’une autre session ou incompatible : choisir un nouvel index avec le formateur et adapter toutes les commandes et la vue de données. Ne rien supprimer automatiquement.

Dans le terminal, seulement si l’index est absent :

```bash
"${CURL_ES[@]}" -X PUT "$ES_URL/defi08b-openssh" \
  -H 'Content-Type: application/json' --data-binary @openssh-mapping.json
```

Attendre la confirmation avant de charger : sinon Elasticsearch pourrait créer automatiquement un mapping inadapté.

### 8.3 Enregistrer le pipeline réel

```bash
"${CURL_ES[@]}" -X PUT "$ES_URL/_ingest/pipeline/defi08b-openssh-geoip" \
  -H 'Content-Type: application/json' --data-binary @openssh-geoip-pipeline.json
```

Cette commande enregistre les traitements ; elle n’importe aucun document. Le pipeline date l’ingestion, tente de géolocaliser les IP publiques non issues d’un cache et renseigne `geo_status`. Les erreurs du processeur sont taguées ; un succès HTTP ne garantit pas des coordonnées. La base requise est téléchargée ou installée suivant le déploiement. 

Dans Console, le formateur peut examiner :

```http
GET _ingest/geoip/stats
```

### 8.4 Simuler sur des IP du vrai fichier

```bash
"${CURL_ES[@]}" -X POST "$ES_URL/_ingest/pipeline/defi08b-openssh-geoip/_simulate" \
  -H 'Content-Type: application/json' --data-binary @preparation/geo-simulate.json \
  -o geo-simulate-response.json

python3 verifier_reponse.py simulate geo-simulate-response.json --preparation preparation/preparation.json
```

Attendu : au moins un document contient `source_geo.location`. La simulation ne les indexe pas.

Si aucune position n’est produite :

1. Lire les tags dans la réponse et les statistiques GeoIP.
2. Si le téléchargement est en cours, attendre puis relancer le test ; ne pas annoncer le succès avant apparition des coordonnées.
3. Faire vérifier par l’administrateur le réseau sortant, la base et les règles du déploiement.
4. Sinon, basculer vers le cache réel préparé en section 18 ; ne pas inventer un point pour une IP.

Ces contrôles sont un prérequis du défi complet avec carte, et non une option à découvrir après deux heures de construction.

## 9. Importer explicitement avec la commande Bulk

### 9.1 Envoyer les documents

Parcours en ligne, seulement après simulation GeoIP concluante :

```bash
"${CURL_ES[@]}" -X POST \
  "$ES_URL/defi08b-openssh/_bulk?pipeline=defi08b-openssh-geoip&refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @preparation/openssh.ndjson \
  -o bulk-response.json

python3 verifier_reponse.py bulk bulk-response.json --preparation preparation/preparation.json
```

Le paramètre `pipeline` applique le traitement avant indexation, `refresh=wait_for` attend la visibilité en recherche pour ce petit chargement pédagogique. Le vérificateur examine les statuts de tous les items, pas uniquement le code HTTP global. [web:143]

### 9.2 Vérifier le volume et les coordonnées

```bash
"${CURL_ES[@]}" -X POST "$ES_URL/defi08b-openssh/_search" \
  -H 'Content-Type: application/json' --data-binary @openssh-validation-query.json \
  -o validation.json

python3 verifier_reponse.py validation validation.json --preparation preparation/preparation.json
python3 -m json.tool validation.json
```

Le contrôle refuse un total différent de N, des dates absentes, des compteurs d’authentification incohérents ou zéro document géolocalisé. Reporter :

| Référence | Réponse Elasticsearch |
|---|---|
| N | `hits.total.value`, relation `eq` |
| A | `aggregations.auth_records.doc_count` |
| F | `aggregations.failures.doc_count` |
| S | `aggregations.successes.doc_count` |
| I | `aggregations.with_ip.doc_count` |
| G | `aggregations.located.doc_count` |
| Minimum / maximum | `aggregations.first_event.value_as_string` / `last_event.value_as_string` |

### 9.3 Comprendre le rejeu

Les actions sont `index` avec un identifiant explicite : un rejeu du même fichier et des mêmes paramètres remplace les documents de même ID au lieu de les multiplier. En ligne, il peut recalculer la géolocalisation et `ingested_at`. Ce n’est donc pas une absence d’écriture. Ne pas changer les paramètres d’année ou de source dans un index de référence existant. Une réponse Bulk peut contenir des succès et des échecs : rien n’annule automatiquement les opérations déjà réussies. [web:143]

## 10. Créer la vue de données et explorer les documents

### 10.1 Vue de données

1. Rechercher « Vues de données » dans la navigation Kibana et ouvrir cette page.
2. Cliquer sur l’action de création d’une vue.
3. Nom : `[D08B] OpenSSH Loghub`.
4. Modèle d’index exact : `defi08b-openssh`.
5. Champ d’horodatage : `@timestamp`.
6. Enregistrer. Si une vue équivalente existe, vérifier le motif et la réutiliser.

### 10.2 Explorer dans Découvrir

1. Ouvrir « Découvrir ».
2. Choisir la vue `[D08B] OpenSSH Loghub`, en mode vue de données/KQL, pas ES|QL.
3. Cliquer le sélecteur de temps en haut à droite.
4. Choisir une période absolue couvrant les bornes de `validation.json` avec une marge ; attention, l’année conventionnelle est 2000.
5. Convertir correctement si le navigateur affiche un autre fuseau que UTC.
6. Vider la barre KQL, retirer les filtres temporaires, actualiser.
7. Dans les champs à gauche, rechercher `event_type` puis cliquer son icône d’ajout en colonne.
8. Recommencer pour `auth_outcome`, `source_ip`, `user_name`, `source_geo.country_name`, `geo_status`, `message` ; conserver la date.
9. Cliquer la flèche de début d’une ligne pour ouvrir ses détails.
10. Lire `timestamp_policy`, `content` et les coordonnées éventuelles.

Tester séparément, dans la barre KQL, en remplaçant l’expression à chaque fois :

```kql
auth_record: true
```

```kql
auth_outcome: "failure"
```

```kql
event_type: "message_repeat"
```

```kql
source_geo.location: *
```

```kql
source_ip: * and not source_geo.location: *
```

Résultat zéro est acceptable pour une catégorie absente. Le script et les références chiffrées disent quelles catégories sont réellement disponibles.

### 10.3 Enregistrer le détail documentaire des échecs

1. Saisir `auth_outcome: "failure"` et appliquer.
2. Garder les colonnes utiles : date, IP, utilisateur, pays, message.
3. Cliquer « Enregistrer ».
4. Nom : `[D08B] Détail des échecs canoniques`.
5. Confirmer. Revenir ensuite à une recherche KQL vide avant de créer les autres panneaux.

## 11. Créer le tableau de bord et les cinq indicateurs

Ne pas filtrer globalement sur les échecs pendant cette construction : le total et le dénominateur doivent rester ceux du corpus complet.

### 11.1 Premier indicateur : documents indexés

1. Ouvrir « Tableaux de bord » → « Créer un tableau de bord ».
2. Enregistrer sous `[D08B] Observabilité OpenSSH — Loghub`, puis cliquer « Modifier ».
3. Régler la période absolue sur toutes les données et vider les filtres temporaires.
4. Cliquer « Créer une visualisation », ou « Ajouter » puis « Nouvelle visualisation » selon le menu.
5. Choisir Lens si demandé, puis `[D08B] OpenSSH Loghub`.
6. Si un éditeur ES|QL apparaît, revenir au mode de configuration par champs/dimensions.
7. Ouvrir le menu des graphiques et sélectionner « Indicateur ».
8. À droite, cliquer la dimension principale vide ou déjà préremplie.
9. Choisir la fonction rapide de comptage des documents, « Nombre d’enregistrements ». Ne pas sélectionner de champ.
10. Libellé : `Documents` ; format Nombre, zéro décimale si le réglage est disponible.
11. Fermer le volet de dimension pour voir l’aperçu et comparer à N.
12. Cliquer « Enregistrer et revenir ».
13. Titre : `[D08B] Documents indexés`. Si le titre n’a pas été demandé, ouvrir le menu `…` du nouveau panneau sur le tableau de bord, puis l’action de modification de ses paramètres et saisir ce titre.
14. Enregistrer le tableau de bord.

Résultat attendu : une première tuile affiche N. La manipulation suivante ajoute une tuile sans remplacer celle-ci.

### 11.2 Ajouter l’indicateur « Échecs canoniques »

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` et cliquer « Modifier » si nécessaire.
2. Vérifier la période complète, la barre KQL vide et l’absence de filtre d’échec global.
3. Cliquer « Créer une visualisation » ou « Ajouter » → « Nouvelle visualisation ». Ne pas modifier le panneau précédent.
4. Choisir Lens et la vue `[D08B] OpenSSH Loghub`.
5. Sélectionner le type « Indicateur » dans le menu des graphiques.
6. Cliquer la dimension de la valeur principale à droite.
7. Choisir l’onglet « Formule » et remplacer son contenu par :

```text
count(kql='auth_outcome: "failure"')
```

8. Attendre la validation de la formule. Vérifier les apostrophes droites, guillemets et parenthèses en cas d’erreur ; ne pas coller cette formule dans la barre KQL.
9. Libellé : `Échecs canoniques`.
10. Choisir le format Nombre, zéro décimale si proposé.
11. Fermer le volet et comparer l’aperçu à F.
12. Cliquer « Enregistrer et revenir ».
13. Nommer `[D08B] Échecs canoniques`. Si le titre n’est pas demandé dans Lens, ouvrir le menu `…` du panneau ajouté puis modifier son titre dans ses paramètres.
14. Enregistrer le tableau de bord et vérifier que les tuiles précédentes sont toujours présentes.

### 11.3 Ajouter l’indicateur « IP distinctes estimées »

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` et cliquer « Modifier » si nécessaire.
2. Vérifier la période complète, la barre KQL vide et l’absence de filtre d’échec global.
3. Cliquer « Créer une visualisation » ou « Ajouter » → « Nouvelle visualisation ». Ne pas modifier le panneau précédent.
4. Choisir Lens et la vue `[D08B] OpenSSH Loghub`.
5. Sélectionner le type « Indicateur » dans le menu des graphiques.
6. Cliquer la dimension de la valeur principale à droite.
7. Choisir l’onglet « Formule » et remplacer son contenu par :

```text
unique_count(source_ip)
```

8. Attendre la validation de la formule. Vérifier les apostrophes droites, guillemets et parenthèses en cas d’erreur ; ne pas coller cette formule dans la barre KQL.
9. Libellé : `IP distinctes estimées`.
10. Choisir le format Nombre, zéro décimale si proposé.
11. Fermer le volet et comparer l’aperçu à la cardinalité Elasticsearch ; la référence locale est exacte alors que cette valeur est estimée.
12. Cliquer « Enregistrer et revenir ».
13. Nommer `[D08B] IP distinctes estimées`. Si le titre n’est pas demandé dans Lens, ouvrir le menu `…` du panneau ajouté puis modifier son titre dans ses paramètres.
14. Enregistrer le tableau de bord et vérifier que les tuiles précédentes sont toujours présentes.

### 11.4 Ajouter l’indicateur « Part d’échec — enregistrements canoniques »

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` et cliquer « Modifier » si nécessaire.
2. Vérifier la période complète, la barre KQL vide et l’absence de filtre d’échec global.
3. Cliquer « Créer une visualisation » ou « Ajouter » → « Nouvelle visualisation ». Ne pas modifier le panneau précédent.
4. Choisir Lens et la vue `[D08B] OpenSSH Loghub`.
5. Sélectionner le type « Indicateur » dans le menu des graphiques.
6. Cliquer la dimension de la valeur principale à droite.
7. Choisir l’onglet « Formule » et remplacer son contenu par :

```text
count(kql='auth_outcome: "failure"') / count(kql='auth_record: true')
```

8. Attendre la validation de la formule. Vérifier les apostrophes droites, guillemets et parenthèses en cas d’erreur ; ne pas coller cette formule dans la barre KQL.
9. Libellé : `Part d’échec — enregistrements canoniques`.
10. Choisir le format Pourcentage, deux décimales, sans multiplier par 100.
11. Fermer le volet et comparer l’aperçu à F / A si A > 0.
12. Cliquer « Enregistrer et revenir ».
13. Nommer `[D08B] Part d’échec — enregistrements canoniques`. Si le titre n’est pas demandé dans Lens, ouvrir le menu `…` du panneau ajouté puis modifier son titre dans ses paramètres.
14. Enregistrer le tableau de bord et vérifier que les tuiles précédentes sont toujours présentes.

### 11.5 Ajouter l’indicateur « Couverture GeoIP — documents avec IP »

1. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub` et cliquer « Modifier » si nécessaire.
2. Vérifier la période complète, la barre KQL vide et l’absence de filtre d’échec global.
3. Cliquer « Créer une visualisation » ou « Ajouter » → « Nouvelle visualisation ». Ne pas modifier le panneau précédent.
4. Choisir Lens et la vue `[D08B] OpenSSH Loghub`.
5. Sélectionner le type « Indicateur » dans le menu des graphiques.
6. Cliquer la dimension de la valeur principale à droite.
7. Choisir l’onglet « Formule » et remplacer son contenu par :

```text
count(kql='source_geo.location: *') / count(kql='source_ip: *')
```

8. Attendre la validation de la formule. Vérifier les apostrophes droites, guillemets et parenthèses en cas d’erreur ; ne pas coller cette formule dans la barre KQL.
9. Libellé : `Couverture GeoIP — documents avec IP`.
10. Choisir le format Pourcentage, deux décimales, sans multiplier par 100.
11. Fermer le volet et comparer l’aperçu à G / I si I > 0.
12. Cliquer « Enregistrer et revenir ».
13. Nommer `[D08B] Couverture GeoIP — documents avec IP`. Si le titre n’est pas demandé dans Lens, ouvrir le menu `…` du panneau ajouté puis modifier son titre dans ses paramètres.
14. Enregistrer le tableau de bord et vérifier que les tuiles précédentes sont toujours présentes.

Les ratios Lens sont calculés dans le contexte du panneau et des filtres. Si A ou I vaut zéro, ne pas remplacer une division sans dénominateur par un faux zéro : investiguer les données. La formule de couverture retenue porte sur les documents ayant une IP, pas uniquement les IP publiques ; elle doit donc être nommée ainsi. [web:145]

### 11.6 Disposer les tuiles

1. Sur le tableau de bord, rester en modification.
2. Déplacer les cinq tuiles par leur en-tête pour les mettre en première ligne ou sur deux lignes lisibles.
3. Ajuster leur largeur avec la poignée du coin inférieur.
4. Vérifier les titres et enregistrer.

## 12. Histogramme temporel par type de message

1. Depuis le tableau de bord en modification, ajouter une nouvelle visualisation Lens.
2. Sélectionner `[D08B] OpenSSH Loghub`.
3. Choisir le graphique à barres verticales.
4. À gauche, rechercher `@timestamp` et le glisser sur « Axe horizontal » à droite.
5. Cliquer la dimension créée et vérifier « Histogramme de dates ».
6. Pour un premier affichage, conserver l’intervalle automatique ; lire ensuite les bornes du corpus. Choisir un minimum d’une minute pour une fenêtre de quelques heures, ou adapter sans supposer que l’échantillon couvre 28 jours.
7. Fermer ce volet.
8. Cliquer « Axe vertical » et choisir le comptage des documents, sans champ ; libellé `Lignes par intervalle`.
9. Rechercher `event_type` à gauche et le glisser sur la zone de ventilation/répartition.
10. Ouvrir cette dimension → valeurs les plus fréquentes → 10 valeurs ou davantage selon les catégories mesurées.
11. Dans les paramètres de style, choisir les barres empilées, pas l’empilement en pourcentage.
12. Garder la légende visible ; vérifier plusieurs infobulles.
13. Cliquer « Enregistrer et revenir » ; titre `[D08B] Messages dans le temps par type`.
14. Si le titre n’est pas demandé, le renseigner dans les paramètres du panneau ajouté. Enregistrer le tableau de bord.

Contrôle : une barre correspond à un intervalle, pas à une session. Un intervalle vide ne prouve pas une panne de collecte ; nous ne connaissons pas ici l’exhaustivité de toute la source.

## 13. Barres horizontales : IP contribuant aux échecs

1. Sur le tableau de bord, cliquer « Modifier » puis ajouter une nouvelle visualisation Lens.
2. Choisir `[D08B] OpenSSH Loghub`, puis des barres horizontales.
3. Glisser `source_ip` dans l’axe des catégories, généralement l’axe vertical dans cette orientation.
4. Ouvrir la dimension → valeurs les plus fréquentes → 10 valeurs.
5. Choisir un classement décroissant par nombre de documents.
6. Dans l’axe numérique horizontal, choisir le comptage des documents.
7. Dans la barre KQL locale de Lens, saisir `auth_outcome: "failure"` puis appliquer. Ne pas saisir ce filtre dans la barre globale du tableau de bord.
8. Vérifier que les libellés sont des IP réellement présentes et que les barres représentent des lignes d’échec canoniques.
9. Enregistrer et revenir ; titre `[D08B] Top 10 IP — échecs canoniques`.
10. Si nécessaire, renseigner le titre dans les paramètres du panneau ; enregistrer le tableau de bord.

Un top 10 n’est pas exhaustif. Pour les ex æquo, l’ordre peut varier. Le nombre de lignes n’est pas le nombre de personnes et ne permet pas d’attribuer l’origine humaine d’une activité.

## 14. Table par utilisateur

1. Ajouter une nouvelle visualisation Lens depuis le tableau de bord en modification.
2. Choisir `[D08B] OpenSSH Loghub` et le type « Tableau ».
3. Rechercher `user_name` à gauche et le glisser sur la zone des lignes.
4. Ouvrir cette dimension → valeurs les plus fréquentes → 10 valeurs.
5. Dans les valeurs/calculs, cliquer pour ajouter le comptage des documents ; libellé `Messages avec cet utilisateur`.
6. Ajouter un second calcul → « Formule » :

```text
count(kql='auth_outcome: "failure"')
```

7. Libellé `Échecs canoniques`, format Nombre sans décimale.
8. Ajouter un troisième calcul → « Formule » :

```text
count(kql='auth_record: true')
```

9. Libellé `Enregistrements canoniques`, format Nombre.
10. Ne pas ajouter un taux par utilisateur si son dénominateur est nul ; les deux comptages restent lisibles.
11. Trier par échecs décroissants si le tri est proposé ; sinon garder le tri documenté de la dimension.
12. Enregistrer et revenir ; titre `[D08B] Utilisateurs observés — messages et échecs`.
13. Renseigner le titre dans les paramètres du panneau si nécessaire et enregistrer le tableau de bord.

Les messages sans `user_name` ne figurent pas dans les lignes de cette table. Ne pas comparer la somme du top 10 au total de toutes les lignes comme si les périmètres étaient identiques.

## 15. Carte thermique : temps et catégories de messages

1. Depuis le tableau de bord en modification, ajouter une nouvelle visualisation Lens.
2. Choisir `[D08B] OpenSSH Loghub` puis le type « Carte thermique ».
3. Glisser `@timestamp` sur l’axe horizontal → Histogramme de dates ; choisir une granularité comparable à l’histogramme temporel.
4. Glisser `event_type` sur l’axe vertical → valeurs les plus fréquentes → 10 valeurs ou plus selon le rapport.
5. Dans la valeur de cellule, choisir le comptage des documents.
6. Choisir une palette de dégradé séquentiel, garder la légende visible.
7. Survoler une cellule : lire période, catégorie et nombre de lignes.
8. Enregistrer et revenir ; titre `[D08B] Intensité des messages — temps × type`.
9. Ajuster le titre dans les paramètres du panneau si nécessaire puis enregistrer le tableau de bord.

Cette matrice n’est pas une carte géographique. Nous allons maintenant créer cette dernière dans une autre application : Cartes.

## 16. Construire la carte GeoIP, puis l’intégrer au tableau de bord

### 16.1 Vérifier ce que la carte pourra représenter

Dans Console :

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

Attendu : `geo_point`, G supérieur à zéro et des positions provenant réellement du pipeline ou du cache réel. Vérifier que `geo_source` ne décrit pas une simulation. Une IP seule ne fournit pas un point à Maps : c’est le `geo_point` qu’il faut sélectionner. [web:118]

### 16.2 Créer la couche de points

1. Dans la recherche de navigation Kibana, rechercher « Cartes » et ouvrir l’application.
2. Cliquer « Créer une carte ».
3. Avant d’ajouter les points, régler le sélecteur de temps sur la période absolue complète relevée dans `validation.json`, année conventionnelle 2000.
4. Vider la recherche et retirer les filtres temporaires.
5. Cliquer « Ajouter une couche ».
6. Choisir « Documents » dans les sources de couche.
7. Sélectionner la vue de données `[D08B] OpenSSH Loghub`.
8. Si plusieurs champs géographiques sont proposés, choisir `source_geo.location`.
9. Poursuivre vers les paramètres de la couche, puis confirmer son ajout selon le bouton proposé.
10. Nommer la couche `Positions GeoIP des messages OpenSSH`.
11. Utiliser l’action d’ajustement de la vue aux données, ou dézoomer jusqu’à voir l’ensemble des points.

Résultat attendu : des points géographiques apparaissent. Leur nombre visuel peut être inférieur à G car plusieurs documents se superposent sur une même coordonnée.

### 16.3 Configurer les infobulles

1. Ouvrir les paramètres de la couche de documents si le volet a été fermé.
2. Repérer les champs d’infobulle et cliquer l’action d’ajout.
3. Ajouter `source_ip`.
4. Ajouter `source_geo.country_name` et `source_geo.city_name` si ces valeurs sont disponibles.
5. Ajouter `event_type`, `user_name`, `auth_outcome` et `geo_source`.
6. Confirmer les modifications.
7. Cliquer ou survoler un point suivant l’interaction proposée et lire ses informations.
8. Si une ville est absente mais une coordonnée existe, ne pas inventer le nom manquant.

Les couches de documents et les infobulles rendent la position vérifiable à partir des attributs du document ; elles ne rendent pas cette position précise à l’échelle d’une personne. 

### 16.4 Ajouter une couche de regroupements

1. Cliquer de nouveau « Ajouter une couche ».
2. Sélectionner la couche de regroupements/agrégats de points si elle est disponible.
3. Choisir la même vue `[D08B] OpenSSH Loghub` et `source_geo.location`.
4. Utiliser le nombre de documents comme mesure.
5. Dans le style des symboles, associer la taille au nombre de documents si l’option est proposée.
6. Nommer la couche `Nombre de messages géolocalisés par zone`.
7. Confirmer.
8. Dans la liste des couches, masquer temporairement la couche de documents pour lire les regroupements sans superposition.
9. Zoomer puis dézoomer ; observer que les regroupements et leurs comptes changent selon le niveau géographique.

Les regroupements agrègent les documents par cellule spatiale ; le symbole n’est pas une IP unique et ne doit pas être nommé « nombre de visiteurs ». Si un seul lieu est disponible, conserver cette limite au lieu d’ajouter artificiellement d’autres villes. [web:108]

### 16.5 Extension facultative : densité géographique

1. Dans l’éditeur de la carte, cliquer « Ajouter une couche ».
2. Choisir la couche « Carte thermique » géographique.
3. Choisir `[D08B] OpenSSH Loghub` et `source_geo.location`.
4. Conserver un comptage non pondéré pour ce premier exercice.
5. Nommer `Densité des messages géolocalisés` et confirmer.
6. Masquer les couches de points/regroupements pour observer uniquement la densité, puis les réactiver selon votre préférence.

Cette couche montre une densité spatiale. Elle est différente de la matrice temps × type construite dans Lens. Le regroupement visuel ne mesure pas un taux d’attaque. 

### 16.6 Enregistrer la carte

1. Cliquer « Enregistrer » dans Cartes.
2. Nommer la carte `[D08B] Positions GeoIP OpenSSH — couverture partielle`.
3. Enregistrer dans la bibliothèque si le choix est proposé.
4. Ouvrir le tableau de bord `[D08B] Observabilité OpenSSH — Loghub`.
5. Cliquer « Modifier ».
6. Ouvrir l’ajout d’un panneau depuis la bibliothèque.
7. Rechercher le nom de la carte et cliquer dessus pour l’ajouter.
8. Fermer le volet d’ajout et agrandir la carte avec sa poignée.
9. Vérifier la période du tableau de bord ; les filtres globaux peuvent modifier les couches Elasticsearch.
10. Enregistrer le tableau de bord.

La carte doit utiliser le même index que les panneaux principaux, ce qui permet des filtres cohérents, contrairement à une carte de simulation indépendante. Les filtres temporels et de recherche affectent les couches Elasticsearch. [web:121]

### 16.7 Tester une interaction sans perdre le contexte

1. Noter la couverture GeoIP et le nombre total de documents.
2. Sur le tableau de bord, appliquer `auth_outcome: "failure"` dans la barre KQL.
3. Observer les points ou regroupements encore présents : ils concernent maintenant les échecs canoniques géolocalisés.
4. Observer aussi que le taux d’échec peut atteindre 100 % dans ce périmètre filtré.
5. Effacer le filtre et appliquer de nouveau.
6. Vérifier le retour aux références globales avant d’enregistrer.

## 17. Finaliser le tableau de bord complet

### 17.1 Ajouter les contrôles

1. Ouvrir le tableau de bord → « Modifier ».
2. Ouvrir le menu d’ajout de contrôle.
3. Choisir la vue `[D08B] OpenSSH Loghub`.
4. Choisir `event_type` comme champ.
5. Choisir une liste d’options et saisir le libellé `Type de message`.
6. Enregistrer le contrôle.
7. Recommencer avec `user_name`, libellé `Utilisateur observé`.
8. Si des pays existent, ajouter une liste sur `source_geo.country_name`, libellé `Pays GeoIP`.
9. Sélectionner une catégorie et vérifier les panneaux ; effacer la sélection ensuite.

Un contrôle de pays exclut les documents sans pays : noter cette modification de périmètre avant d’interpréter le taux global ou la couverture.

### 17.2 Ajouter la table documentaire

1. Depuis le tableau de bord en modification, ouvrir l’ajout depuis la bibliothèque.
2. Rechercher `[D08B] Détail des échecs canoniques`.
3. Ajouter la session enregistrée de Découvrir.
4. Agrandir le panneau pour lire plusieurs lignes.
5. Vérifier qu’il contient sa recherche locale d’échecs, sans filtrer tous les autres panneaux.
6. Enregistrer le tableau de bord.

### 17.3 Ajouter le contexte explicatif

1. Ajouter un panneau texte/Markdown.
2. Saisir le texte suivant en complétant les références chiffrées :

```markdown
### Contrat de lecture
- Source : Loghub, OpenSSH_2k.log ; révision et SHA-256 conservés.
- Une tuile Documents compte des lignes, pas des sessions ni des personnes.
- Année 2000 et UTC : conventions explicites, année/fuseau absents du journal source.
- Taux d’échec : échecs / enregistrements canoniques reconnus par le parseur.
- Les messages PAM et les résumés répétés ne sont pas ajoutés à ce dénominateur.
- GeoIP : estimation à la date de référence, pas preuve de localisation historique.
- Couverture : G documents géolocalisés parmi I documents avec IP, à compléter.
- Les pays et IP n’établissent ni identité, ni intention, ni cause racine.
```

3. Enregistrer le panneau et le placer sous les contrôles.
4. Placer les cinq indicateurs en haut, l’histogramme sur une grande ligne, les barres et la table côte à côte, puis la carte thermique, la carte géographique et les documents détaillés.
5. Enregistrer le tableau de bord.
6. Revenir à la liste des tableaux de bord et rouvrir le vôtre pour vérifier la conservation des panneaux et de la période.

## 18. Parcours hors ligne : utiliser un cache GeoIP réel préparé par le formateur

Ce parcours exige un poste de préparation sur lequel le même échantillon a été enrichi avec succès par le pipeline. Il conserve de véritables résultats GeoIP mais les fige à une date de référence. Ce n’est pas un service de géolocalisation inventé et ce cache n’est pas inclus par défaut dans le pack.

### 18.1 Exporter les coordonnées sur le poste connecté

Après import et validation en ligne, dans son terminal configuré avec `CURL_ES`, le formateur exécute :

```bash
"${CURL_ES[@]}" -X POST "$ES_URL/defi08b-openssh/_search" \
  -H 'Content-Type: application/json' --data-binary @export-cache-query.json \
  -o export-cache-response.json

python3 exporter_cache_geo.py export-cache-response.json geo-cache.json
```

L’exporteur vérifie que la réponse contient tous les documents demandés et que leur origine est `elasticsearch_geoip`. Il conserve une entrée par IP et la date d’export. La version de base n’est pas déduite du résultat : le formateur en conserve la référence si disponible. Cet export local ne constitue pas une preuve cryptographique de provenance ; il faut maîtriser sa chaîne de préparation.

Le cache doit couvrir le même échantillon et respecter les conditions des sources et de la base GeoIP. Ne pas y ajouter manuellement des coordonnées attribuées à des IP réelles. Distribuer la notice et les métadonnées de provenance autorisées avec le cache.

### 18.2 Préparer sur la VM isolée

Copier `geo-cache.json` avec les scripts et la source autorisée, puis :

```bash
python3 preparer_openssh.py OpenSSH_2k.log --outdir preparation \
  --year 2000 --utc-offset +0000 --geo-cache geo-cache.json
cat preparation/preparation.json
```

Vérifier `event_types_and_quality.located_from_cache` supérieur à zéro. Le script inscrit `geo_source:geoip_cache`, la date de référence et le SHA-256 du cache dans le rapport.

### 18.3 Charger sans dépendre d’un téléchargement GeoIP

Après création contrôlée du mapping, envoyer le Bulk sans le pipeline en ligne :

```bash
"${CURL_ES[@]}" -X POST "$ES_URL/defi08b-openssh/_bulk?pipeline=_none&refresh=wait_for" \
  -H 'Content-Type: application/x-ndjson' --data-binary @preparation/openssh.ndjson \
  -o bulk-response.json

python3 verifier_reponse.py bulk bulk-response.json --preparation preparation/preparation.json

"${CURL_ES[@]}" -X POST "$ES_URL/defi08b-openssh/_search" \
  -H 'Content-Type: application/json' --data-binary @openssh-validation-query.json \
  -o validation.json
python3 verifier_reponse.py validation validation.json --preparation preparation/preparation.json
```

Ne pas créer le pipeline GeoIP en ligne dans ce parcours : sa création peut tenter de télécharger la base même si le cache suffit. Le paramètre `_none` désactive un éventuel pipeline par défaut ; il ne désactive pas un pipeline final imposé par une autre configuration, que le formateur doit vérifier. [web:143]

La suite des clics est identique : mêmes champs, même vue et même carte. Indiquer dans le texte du tableau de bord la date de référence du cache. Le champ `ingested_at` n’est pas produit dans ce parcours sans pipeline ; aucun panneau obligatoire n’en dépend.

## 19. Corrigé d’investigation : formuler une conclusion prudente

### 19.1 Travail guidé

1. Noter N, A, F, S, I et G dans le contexte global.
2. Observer l’histogramme et choisir une fenêtre comportant des messages.
3. Restreindre la période à cette fenêtre.
4. Lire les IP du top des échecs et les noms d’utilisateurs observés.
5. Sélectionner une IP réellement affichée avec un filtre KQL `source_ip: "ADRESSE"`, en remplaçant ADRESSE par la valeur observée.
6. Lire plusieurs messages bruts pour cette IP, y compris des catégories différentes.
7. Vérifier si cette IP a des coordonnées et si des messages répétés sont présents.
8. Rédiger une observation et une limite, sans affirmer qu’il s’agit d’une session unique ou d’une personne localisée.
9. Retirer les filtres et restaurer la période complète.

### 19.2 Exemple de réponse attendue, sans chiffres inventés

« Dans la fenêtre choisie, l’IP sélectionnée contribue à F_local lignes canoniques d’échec. Les noms observés sont ceux des documents consultés. Une position GeoIP est disponible / indisponible. Cette position est une estimation à la date de référence ; elle n’établit pas l’identité de l’acteur. Les messages PAM et les résumés de répétitions montrent qu’une ligne n’équivaut pas automatiquement à une tentative. Une conclusion sur une attaque nécessiterait d’autres preuves et une connaissance du service. »

### 19.3 Vérifier l’effet d’un filtre sur le taux

1. Lire le taux global F/A, s’il est défini.
2. Filtrer globalement sur `auth_outcome: "failure"`.
3. Si des échecs existent, vérifier que le ratio devient 100 % : le dénominateur s’applique lui aussi au sous-ensemble.
4. Retirer le filtre et retrouver le taux global.
5. Expliquer pourquoi cet effet ne signifie pas que la formule a changé.

## 20. Barème et livrables

| Critère | Points | Preuve |
|---|---:|---|
| Acquisition et provenance | 2 | Révision, SHA-256, notice de licence |
| Préparation et qualité | 3 | NDJSON, types, dates explicites, rejets et résumés conservés |
| Import Bulk | 3 | Mapping préalable, vérification item par item, volume et rejeu expliqués |
| Indicateurs et taux | 3 | Définition de F/A et G/I, cohérence avec Elasticsearch |
| Visualisations non géographiques | 3 | Temps, barres, table, carte thermique, détails |
| Carte GeoIP | 4 | Coordonnées réelles, couche, infobulles, intégration, couverture expliquée |
| Investigation et lisibilité | 2 | Filtres réinitialisés, tableau de bord rouvert, conclusion prudente |
| Total | 20 | |

Un dessin cartographique sans coordonnées réelles du corpus ne valide pas les quatre points de carte. Un blocage de base GeoIP non préparée relève d’un prérequis d’environnement, pas d’une faute de clic du participant : prévoir le cache avant la séance.

## 21. Dépannage ciblé

| Symptôme | Diagnostic et action |
|---|---|
| Fichier de logs introuvable | Vérifier `pwd`, le clonage et la copie du bon `.log` |
| Tous les documents rejetés | Ouvrir les premières lignes ; vérifier qu’il ne s’agit pas d’un HTML/CSV |
| Script interrompu | Ne pas charger une sortie partielle ; corriger puis relancer la préparation |
| Aucun succès reconnu | Peut être réel dans l’échantillon ; ne pas en créer artificiellement |
| Trop de « tentatives » annoncées | Distinguer lignes, enregistrements canoniques, PAM et répétitions |
| Bulk HTTP 200 mais documents absents | Lire tous les `items` avec `verifier_reponse.py` |
| Compteur différent de N | Index d’une autre session, rejets ou import partiel ; ne pas supprimer automatiquement |
| Aucune donnée dans Kibana | Vue exacte, année conventionnelle 2000, période, fuseau et filtres |
| Taux incohérent | Même périmètre, bon dénominateur, format Pourcentage sans `*100` |
| IP non géolocalisée | Peut ne pas exister dans la base ; contrôler couverture et tags |
| Base GeoIP indisponible | Point d’arrêt formateur ; réparer selon politique réseau ou cache réel |
| `source_geo.location` non proposé | Contrôler `geo_point`, bons index et vue de données |
| Couche vide | Coordonnées présentes, période de l’année 2000, filtres et réponse des requêtes |
| Carte sans fond | Dépendance au service de tuiles distincte de la présence des points |
| Un seul point visible | Superposition ou une seule position ; inspecter les documents et les regroupements |
| Cache hors ligne absent | Ne pas remplacer par une carte fictive ; préparer une vraie référence avant séance |


## 22. Rappels de provenance et attribution

Corpus : Loghub, dépôt `logpai/loghub`, échantillon OpenSSH. Le dépôt présente OpenSSH comme un journal de serveur collecté dans son laboratoire sur plus de 28 jours, distinct de l’échantillon 2k utilisé ici. Conserver la notice de licence source et citer, lorsque pertinent : Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu, « Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics », ISSRE 2023. 

