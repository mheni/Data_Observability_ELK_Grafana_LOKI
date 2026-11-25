# Défi 08 bis — Observer des logs OpenSSH de Loghub avec Elasticsearch et Kibana

Version cible : Elasticsearch / Kibana 9.5.7, interface française.

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

Le format suit l’atelier 8 joint : manipulations détaillées, interface française, type de graphique « Indicateur », validation des données et enregistrement explicite des panneaux. Les intitulés traduits autres que « Indicateur » sont des repères à confirmer sur le Space de formation ; ce document n’est pas un test de chaque écran 9.5.7. 

### Pourquoi ce corpus ?

OpenSSH fournit des messages d’authentification et de connexion avec des IP publiques, des utilisateurs, des ports et des types de messages variés. Le fichier consulté contient notamment des lignes `Failed password`, `Invalid user`, des messages PAM, des déconnexions et des résumés `message repeated`. Cela permet un tableau de bord différent du HTTP tout en réutilisant Bulk, Lens et Cartes. 

Attention : ces logs ne contiennent pas de coordonnées natives. La géolocalisation est ajoutée par GeoIP. Nous choisissons donc un corpus géolocalisable, pas un fichier prétendument déjà muni de latitude/longitude. Le jeu Apache de Loghub est présenté comme un journal d’erreurs, et non comme l’access log de l’atelier 8 : on ne lui attribue pas automatiquement les mêmes champs. 

## 2. Points de vigilance avant de distribuer le défi

### 2.1 Les dépendances obligatoires pour une vraie carte

Valider avant de commencer :

- Téléchargement de l’échantillon OpenSSH ou copie locale autorisée.
- Fonctionnement du pipeline GeoIP sur des IP réellement présentes dans cet échantillon.
- Au moins un document avec `source_geo.location` après simulation et après import ; plusieurs positions sont préférables pour enseigner les regroupements.
- Fonctionnement de Cartes et accès au fond cartographique autorisé.
- Droits de lecture/création d’index, gestion du pipeline, vues de données, visualisations et tableaux de bord.

Le processeur GeoIP s’appuie sur une base de géolocalisation ; sa création peut déclencher le téléchargement de la base. Ce téléchargement n’est ni immédiat ni garanti dans un réseau filtré. Une IP publique ne garantit pas non plus une coordonnée disponible.


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

