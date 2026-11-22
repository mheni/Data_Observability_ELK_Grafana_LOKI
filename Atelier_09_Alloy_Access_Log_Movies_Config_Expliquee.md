# Atelier 09 — Grafana Alloy : collecter access_log et movies.csv vers Loki

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 3, atelier 09 |
| Durée indicative | 2 h à 2 h 30 |
| Environnement | Ubuntu natif ; Loki et Grafana de l’atelier 01 |
| Sources réutilisées | access_log et MovieLens movies.csv des ateliers précédents |
| Collecteur | Grafana Alloy comme service système |
| Livrables | config.alloy commenté, preuves de collecte, sondes et note de choix des labels |

## 1. Introduction et objectifs pédagogiques

L’atelier 08 a exploré les access logs dans Elasticsearch/Kibana. Nous utilisons maintenant les mêmes fichiers de référence pour comprendre une autre chaîne de collecte :

```text
access_log ─► source access ─► traitement access ─┐
                                               ├─► loki.write ─► Loki ─► Grafana Explore
movies.csv ─► source movies ─► traitement CSV ───┘
```

Il ne s’agit pas de relancer un import _bulk ni de réinstaller toute la plateforme.

### Objectifs

- Expliquer producteur, fichier, collecteur, stockage et interface.
- Lire et modifier une configuration Alloy : blocs, attributs, cibles, labels et références receiver.
- Collecter deux formats différents avec des traitements séparés.
- Comprendre les permissions du compte de service et les positions de lecture.
- Choisir des labels bornés, sans IP, titre ou identifiant unique en label de flux.
- Distinguer date d’événement et date de collecte, surtout pour une archive.
- Conserver les lignes originales pour les futurs parsers LogQL.
- Observer collecte initiale, ajout de lignes et reprise après arrêt.
- Vérifier le fonctionnement de bout en bout, pas seulement le statut systemd.

Alloy n’est pas un simple nouveau nom de Promtail. Le parcours utilise Alloy comme collecteur ; les ateliers 10 à 12 approfondiront LogQL sur ces sources.

## 2. Pourquoi collecter aussi movies.csv ?

### Objectif

Comparer un log événementiel et un fichier de données tabulaires, sans inventer un nouveau corpus.

| Source | Une ligne représente | Usage pédagogique |
|---|---|---|
| access_log | Une requête HTTP journalisée | Trafic, codes HTTP, traitement de logs |
| movies.csv | Une ligne du catalogue de films | Lecture d’un fichier texte, en-tête et limites du CSV |

### Explication

Loki reçoit des entrées de log ; collecter un CSV ne le transforme pas en table relationnelle ni en index Elasticsearch. La colonne movieId ne devient pas un _id d’upsert : deux lignes du même film restent des événements de collecte.

En production, une ligne de film n’est pas automatiquement une trace de l’exécution d’un import. Pour observer le pipeline d’import lui-même, l’application devrait aussi produire des événements de démarrage, fin, volume et rejet. Le présent exercice montre les mécaniques de collecte, pas une instrumentation métier complète.

Nous conservons un seul access_log et un seul movies.csv suivis par Alloy. Les scripts préparent des copies de travail et ajoutent des sondes explicitement synthétiques ; ils n’altèrent pas les sources de référence.

## 3. Architecture, adresses et périmètre

| Composant | Responsabilité |
|---|---|
| Fichiers | Données disponibles sur disque |
| Alloy | Lecture continue, traitement et transfert |
| Loki | Réception et stockage des entrées organisées par labels |
| Grafana | Interrogation et présentation |

```text
/var/log/formation-alloy09/access_log
/var/log/formation-alloy09/movies.csv
         │
         ▼
Alloy, utilisateur de service alloy
         │ POST /loki/api/v1/push
         ▼
Loki local :3100
         ▲
         │ requêtes
Grafana local :3000 → navigateur via tunnel SSH
```

Les chemins sont propres à l’atelier 09 : nous ne déplaçons pas les fichiers suivis par Logstash, ni les sources des ateliers précédents. Il n’y a pas de synchronisation automatique entre une copie de travail et son original.

Ce lab ne modifie pas la connexion Elasticsearch : les options ES_CA et elastic ne s’ajoutent pas à l’URL locale Loki. Pour un Loki distant/managé, préparer avec le formateur l’authentification, le TLS et éventuellement le tenant attendus. Ne pas exposer le Loki local sans protection sur Internet.

## 4. Vérifier Loki et Grafana

### Commandes

```bash
sudo systemctl status loki-formation grafana-server --no-pager
curl -fsS http://127.0.0.1:3100/ready
curl -fsS http://127.0.0.1:3000/api/health | python3 -m json.tool
```

### Résultat attendu

Loki prêt, Grafana accessible. Adapter le nom d’unité seulement si votre installation a été préparée autrement.

### Explication

L’URL de la datasource Grafana est la racine http://127.0.0.1:3100. L’URL d’écriture Alloy inclut /loki/api/v1/push. Une réponse ready ne prouve pas que les deux fichiers sont déjà collectés.

## 5. Installer ou vérifier Alloy sans refaire l’atelier 01

### Commandes

Le dépôt APT Grafana a été préparé à l’atelier 01 :

```bash
apt-cache policy alloy
sudo apt update
sudo apt install -y alloy
alloy --version
getent passwd alloy
sudo systemctl cat alloy
```

Si le dépôt est absent, faire reprendre sa préparation signée de l’atelier 01. Ne pas désactiver la validation des paquets et ne pas installer un binaire d’une provenance inconnue.

### Explication

Noter la version exacte. Les commandes supposent le paquet Linux avec le compte système alloy. Si le compte ou le service est différent, inspecter l’installation avant d’adapter les permissions.

Un collecteur peut déjà fonctionner : ne pas remplacer sa configuration sans inventaire et sauvegarde. Le parcours de remplacement ci-dessous est réservé à une VM pédagogique dédiée.

## 6. Comprendre le nom alloy.config / config.alloy

### Le fichier utilisé dans ce TP

```text
/etc/alloy/config.alloy
```

C’est le chemin standard du paquet Linux. Un fichier local nommé alloy.config ne sera pas chargé automatiquement parce qu’il porte ce nom : le processus doit recevoir son chemin.

Sur Ubuntu, /etc/default/alloy peut définir CONFIG_FILE et les arguments du service. Vérifier l’unité et le fichier d’environnement effectifs avant de modifier quoi que ce soit.

### Ce n’est pas du YAML

```alloy
logging {
  level = "info"
}
```

- logging est un bloc de configuration globale.
- level est un attribut.
- = affecte une valeur.
- Les accolades délimitent les blocs.
- Les commentaires utilisent // ou /* ... */.
- Les chaînes ordinaires utilisent des guillemets doubles.

Ne pas écrire level: info ou transformer les composants en listes YAML avec des tirets.

### Déclaratif, pas script séquentiel

Les références entre composants définissent le graphe de circulation ; l’ordre textuel des blocs n’est pas ce qui déclenche l’envoi. En revanche, l’ordre des stages dans un même loki.process est important : chaque stage reçoit les résultats du précédent.

## 7. Préparer des copies des mêmes deux sources

### Objectif

Lire un échantillon contrôlé, sans modifier les fichiers déjà utilisés par Elasticsearch et Kibana.

Exemples de sources à adapter :

```text
access_log : copie originale ou actualisée déjà utilisée dans le parcours
movies.csv : ~/tp-movielens/ml-latest-small/movies.csv
```

Créer le dossier de travail et y placer les fichiers joints :

```bash
mkdir -p ~/formation-observabilite/atelier09
cd ~/formation-observabilite/atelier09
```

### Préparer le corpus

```bash
python3 preparer_corpus09.py \
  --access "$HOME/tp01/access_log_actualise" \
  --movies "$HOME/tp-movielens/ml-latest-small/movies.csv" \
  --access-lines 200 --movies-rows 200
```

Adapter le chemin access à votre vrai fichier ; il peut s’appeler access_log, access_log_actualise ou access_log_formation. Aucune nouvelle archive MovieLens n’est nécessaire.

### Ce que fait le script

- Lit au maximum 200 lignes non vides d’access_log, sans réécrire leurs dates.
- Lit 200 enregistrements MovieLens avec csv.DictReader.
- Vérifie l’en-tête movieId,title,genres.
- Réécrit un CSV correct, avec gestion des virgules et guillemets.
- Refuse les titres contenant des sauts de ligne : une entrée Loki de ce TP correspond à une ligne physique.
- Crée corpus09/access_log, corpus09/movies.csv et preparation.json.
- Refuse un dossier de sortie déjà présent pour éviter un écrasement silencieux.

### Résultat attendu

Pour des sources contenant assez de données : 200 lignes Apache, 201 lignes CSV dont l’en-tête ; après filtrage de l’en-tête, 400 entrées candidates pour Loki.

Le rapport contient les nombres réellement préparés. Une source plus courte produit un total plus faible. Ne pas comparer un échantillon Loki de 200 lignes à tout l’index Elasticsearch comme s’il s’agissait du même périmètre.

## 8. Installer les copies avec les bonnes permissions

### Commandes

```bash
sudo install -d -m 2750 -o root -g alloy /var/log/formation-alloy09
sudo ls -l /var/log/formation-alloy09
```

Si les deux fichiers existent déjà, arrêter ici la procédure de copie et examiner leur usage/état de lecture. Ne pas les remplacer pendant une collecte en cours.

Sur un dossier de lab neuf :

```bash
sudo install -m 640 -o root -g alloy corpus09/access_log \
  /var/log/formation-alloy09/access_log
sudo install -m 640 -o root -g alloy corpus09/movies.csv \
  /var/log/formation-alloy09/movies.csv

sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
sudo -u alloy head -n 1 /var/log/formation-alloy09/movies.csv
```

### Explication

Alloy lit les fichiers sans les posséder ni fonctionner en root. Les scripts de sondes seront lancés avec sudo uniquement pour ajouter des données dans ce dossier protégé.

Le compte doit aussi traverser les répertoires parents. Ne pas résoudre un problème de lecture avec chmod -R 777. Le stockage d’état du service, lui, doit être inscriptible par alloy.

## 9. Choisir la politique de temps pour les archives

### Choix principal du TP : heure de collecte

La configuration de base ne contient pas stage.timestamp. Elle conserve l’heure attachée à chaque entrée par la source lors de sa collecte.

| Source | Date visible dans la ligne | Timestamp Loki du parcours principal |
|---|---|---|
| access_log historique | Date Apache originale, inchangée | Heure de collecte par Alloy |
| movies.csv | Année de sortie parfois dans le titre | Heure de collecte par Alloy |

Le label time_basis=collection documente ce choix. Dans Grafana, sélectionner une période couvrant le démarrage de la collecte, par exemple Last 15 minutes si le test vient d’être réalisé.

### Pourquoi ce choix ?

Un access_log ancien peut être refusé par les limites temporelles de Loki si l’on force directement son horodatage historique. Le CSV n’a pas de date d’événement de collecte ; son année de sortie n’est pas un timestamp d’ingestion.

Ce choix rend l’exercice reproductible sans modifier les archives ni désactiver globalement les protections Loki. Il ne simule pas une mesure de fraîcheur de production et ne prétend pas que les requêtes de 2017 viennent d’être servies.

La variante en fin de TP montre comment prendre la date Apache lorsque les événements sont récents et que cette sémantique est voulue.

## 10. Lire la configuration complète avant de l’activer

Le fichier config.alloy joint contient :

```alloy
// Configuration de laboratoire : deux fichiers, deux traitements, une destination.
logging {
  level = "info"
}

loki.source.file "access" {
  targets = [
    {
      __path__    = "/var/log/formation-alloy09/access_log",
      job         = "atelier09",
      service     = "web-formation",
      environment = "formation",
      dataset     = "access",
      format      = "apache_combined",
      time_basis  = "collection",
    },
  ]
  tail_from_end = false
  forward_to    = [loki.process.access.receiver]
}

loki.process "access" {
  // Extraction illustrative : la ligne Apache originale reste intacte.
  stage.regex {
    expression = `^(?P<client_ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] "(?P<request_line>[^"]*)" (?P<status>(?P<status_class>[1-5])\d{2}) (?P<bytes>\d+|-)`
  }

  // Transformer la famille numerique en libelle : 5 -> 5xx.
  stage.template {
    source   = "status_class"
    template = "{{ if .Value }}{{ .Value }}xx{{ end }}"
  }

  stage.labels {
    values = {
      status_class = "status_class",
    }
  }

  forward_to = [loki.write.local.receiver]
}

loki.source.file "movies" {
  targets = [
    {
      __path__    = "/var/log/formation-alloy09/movies.csv",
      job         = "atelier09",
      service     = "movielens-import",
      environment = "formation",
      dataset     = "movies",
      format      = "csv",
      time_basis  = "collection",
    },
  ]
  tail_from_end = false
  forward_to    = [loki.process.movies.receiver]
}

loki.process "movies" {
  // L'en-tete n'est pas un film.
  stage.drop {
    expression          = `^movieId,title,genres\r?$`
    drop_counter_reason = "movies_csv_header"
  }

  // Pas de stage.output : on conserve le CSV pour les recherches de lignes.
  forward_to = [loki.write.local.receiver]
}

loki.write "local" {
  endpoint {
    url = "http://127.0.0.1:3100/loki/api/v1/push"
  }
}
```

### Vue d’ensemble

- Deux loki.source.file : un par fichier et jeu de labels.
- Deux loki.process : formats et transformations séparés.
- Un loki.write partagé : destination commune.
- Un logging global : journaux internes d’Alloy.

Le TP utilise des chemins exacts. Il n’y a donc pas besoin d’un glob ou d’un composant de découverte pour ces deux fichiers fixes.

## 11. Expliquer le bloc logging

```alloy
logging {
  level = "info"
}
```

### Explication

Configure les logs internes du collecteur, visibles notamment avec journalctl. Ce n’est pas un filtre sur les statuts HTTP ou les lignes MovieLens.

Passer temporairement à debug peut aider à diagnostiquer, mais produit plus de journaux et peut exposer des informations. Revenir au niveau normal après l’investigation.

## 12. Expliquer les blocs loki.source.file

### Exemple

```alloy
loki.source.file "access" {
  targets = [
    {
      __path__ = "/var/log/formation-alloy09/access_log",
      job      = "atelier09",
      dataset  = "access",
    },
  ]
  tail_from_end = false
  forward_to    = [loki.process.access.receiver]
}
```

Cet extrait illustre la structure ; la configuration complète inclut les autres labels. Ne pas l’ajouter comme un deuxième composant de même nom.

### Chaque partie a un rôle

| Partie | Signification |
|---|---|
| loki.source.file | Type du composant : lire des entrées dans des fichiers |
| "access" | Nom de cette instance dans la configuration |
| targets | Liste des fichiers et de leurs labels associés |
| __path__ | Attribut technique de cible indiquant le chemin absolu |
| job / dataset / service | Labels attachés aux lignes de cette cible |
| tail_from_end false | Sans position connue, commencer au début du fichier |
| forward_to | Liste des destinations de sortie |
| loki.process.access.receiver | Entrée publiée par l’instance de traitement access |

Le nom du composant n’est pas automatiquement un label Loki. dataset=access est explicitement déclaré pour sélectionner ce corpus dans Explore.

Un chemin dans le répertoire personnel peut être illisible par le compte de service ; copier vers le dossier dédié évite d’ouvrir tout le home.

### Positions de lecture

tail_from_end=false ne relit pas tout à chaque restart : une position déjà enregistrée est prioritaire. Identifier le --storage.path réellement utilisé dans l’unité. Ne pas lancer simultanément une instance manuelle avec le même stockage.

## 13. Expliquer loki.process access et ses stages

### stage.regex : extraire sans remplacer la ligne

La regex illustrative lit le début du format Apache Combined et extrait : client_ip, apache_time, request_line, status, status_class et bytes.

Les noms (?P<...>) créent des champs dans une map temporaire partagée entre stages. La regex est écrite entre backticks : les barres inverses ne nécessitent pas le double échappement d’une chaîne entre guillemets doubles.

### Limites du parseur

Ce motif est volontairement simple. Certaines requêtes malformées ou contenant des guillemets échappés peuvent ne pas correspondre. Une ligne non reconnue reste conservée ; elle peut simplement ne pas recevoir status_class.

Ce traitement n’est pas une validation exhaustive de tout HTTP ou du CSV. Ne pas confondre regex non correspondante et ligne supprimée.

### stage.template : construire une classe lisible

La regex capture d’abord le premier chiffre du statut dans status_class. Le stage.template transforme cette valeur, par exemple 5 en 5xx, dans la map extraite. La condition évite de fabriquer une classe si l’extraction n’a pas fourni de valeur.

Le stage doit être placé entre regex et labels : promouvoir le chiffre avant sa transformation ne donne pas le label 5xx attendu par les requêtes. .Value désigne ici la valeur extraite ciblée par source ; ce n’est pas toute la ligne.

### stage.labels : promouvoir un choix limité

```alloy
stage.labels {
  values = {
    status_class = "status_class",
  }
}
```

La clé à gauche est le label Loki ; la chaîne à droite désigne le champ extrait. Extraire client_ip ne le transforme pas automatiquement en label.

status_class prend normalement quelques valeurs : 1xx à 5xx. Nous ne promouvons pas IP, chemin, date ou requête complète. Aucun stage.output n’est présent : le log Apache complet est envoyé à Loki.

### Données extraites et interrogation future

La map temporaire des extractions n’est pas une table de colonnes persistée automatiquement. Les champs non promus restent disponibles via leur texte dans la ligne ; les ateliers LogQL pourront les extraire à la requête.

## 14. Expliquer loki.process movies et les limites du CSV

### stage.drop : supprimer l’en-tête seulement

```alloy
stage.drop {
  expression          = `^movieId,title,genres\r?$`
  drop_counter_reason = "movies_csv_header"
}
```

Le motif ancré vise la ligne d’en-tête exacte, avec éventuel retour chariot. Le script de préparation normalise le CSV en UTF-8 sans BOM. drop_counter_reason donne une raison identifiable dans les métriques de suppression, si celles-ci sont collectées.

Il ne supprime pas tous les films et ne fait pas une validation de schéma générale.

### Pourquoi pas un split sur les virgules ?

```csv
movieId,title,genres
9000901,"Un titre, avec virgule (2026)",Drama
```

Une virgule peut appartenir au titre. Les guillemets CSV peuvent aussi être échappés par doublement. Une regex naïve ou un split(',') ne suffit pas pour parser toutes les colonnes.

Le TP envoie donc les lignes CSV complètes, sans prétendre les convertir en JSON dans Alloy. Le module Python csv assure la préparation correcte. Si l’on veut des champs JSON robustes dans Loki, concevoir explicitement une étape CSV → JSON avec un vrai parseur et documenter cette nouvelle source ; ce n’est pas nécessaire à la collecte des deux fichiers demandée ici.

Loki reste ligne par ligne dans ce parcours. Un CSV contenant un champ multiligne doit être normalisé avant la collecte ; le script le refuse plutôt que d’annoncer un enregistrement correct alors qu’il serait fragmenté.

## 15. Expliquer loki.write et la connexion entre blocs

```alloy
loki.write "local" {
  endpoint {
    url = "http://127.0.0.1:3100/loki/api/v1/push"
  }
}
```

### Explication

loki.write reçoit les entrées via son receiver et les envoie à l’endpoint Loki. local est un nom d’instance libre, pas une garantie de stockage sur disque local.

forward_to est une liste, même avec une seule destination. Une référence receiver n’est pas une URL : Alloy résout la relation entre composants.

```text
source.access.forward_to → process.access.receiver
process.access.forward_to → write.local.receiver
write.local.endpoint.url → API HTTP Loki
```

Le même writer est partagé par les deux sources. Le composant peut regrouper les envois ; attendre quelques secondes avant de conclure à une perte.

Une file d’attente ou des retries n’équivalent pas à une garantie d’exactement-une-fois. En production, examiner persistance, options WAL, capacité, comportement sur panne et politique de rejet selon la version.

## 16. Choisir les labels pour la Data Observability

| Champ | Choix du TP | Justification |
|---|---|---|
| job | atelier09 | Isoler le TP |
| environment | formation | Dimension stable |
| service | web-formation / movielens-import | Deux producteurs logiques |
| dataset | access / movies | Séparer les corpus |
| format | apache_combined / csv | Distinguer le format à traiter |
| time_basis | collection | Documenter le sens du timestamp |
| status_class | Valeurs bornées pour access | Distinguer les familles HTTP |
| filename | Peut être ajouté par la source | Deux chemins fixes dans ce TP |
| client_ip / path / titre / movieId | Dans le contenu | Cardinalité forte ou variable |
| marqueur de sonde | Dans le contenu | Recherche ponctuelle, pas un nouveau flux par test |

Une combinaison de labels définit un stream Loki. Le nom interne du composant et un identifiant de film ne doivent pas être confondus avec les dimensions nécessaires à la collecte.

Un label peu cardinal peut être légitime, mais chaque dimension augmente les combinaisons possibles. Une faible cardinalité ne dispense pas d’un besoin de recherche clair.

## 17. Valider avant d’activer

### Objectif

Séparer préparation, validation et remplacement contrôlé.

Installer une copie candidate et la valider avec le compte de service :

```bash
sudo install -m 640 -o root -g alloy config.alloy /etc/alloy/atelier09-candidate.alloy
sudo -u alloy alloy validate /etc/alloy/atelier09-candidate.alloy
```

### Explication

La validation contrôle notamment syntaxe, composants et propriétés ; elle ne prouve ni l’accès aux fichiers, ni la publication effective dans Loki.

Optionnel : utiliser alloy fmt selon l’aide de la version pour harmoniser le format du fichier local. Ne pas confondre formatage et test de fonctionnement.

Si l’utilisateur alloy ne peut pas traverser /etc/alloy, vérifier les permissions du paquet plutôt que lancer tout le service en root.

### Activer sur une VM de lab dédiée

Après accord, vérifier que le service utilise bien /etc/alloy/config.alloy. S’il utilise CONFIG_FILE ailleurs, adapter explicitement le chemin ou modifier cette variable de façon contrôlée, puis redémarrer.

```bash
sudo systemctl stop alloy
sudo cp /etc/alloy/config.alloy "/etc/alloy/config.alloy.before-atelier09-$(date +%Y%m%dT%H%M%S)"
sudo install -m 640 -o root -g alloy config.alloy /etc/alloy/config.alloy
sudo -u alloy alloy validate /etc/alloy/config.alloy
sudo systemctl enable --now alloy
sudo systemctl status alloy --no-pager
sudo journalctl -u alloy -n 100 --no-pager
```

Le backup suppose qu’une configuration existante est présente ; si le paquet n’en a pas créé, vérifier l’installation et conserver au moins les arguments du service avant le premier démarrage.

Si Alloy collecte déjà des sources utiles, ne pas exécuter ce remplacement tel quel : fusionner les composants sans doublon de nom et valider, ou utiliser une VM séparée. Les noms d’instance doivent être uniques pour un même type de composant.

## 18. Observer la collecte initiale dans Grafana

### Accès

Depuis le poste participant si nécessaire :

```bash
ssh -N -L 3000:127.0.0.1:3000 utilisateur@IP_PUBLIQUE_VM
```

Dans Grafana → Explore → datasource Loki-Formation, choisir la période de collecte et le mode Code.

### Requêtes

```logql
{job="atelier09"}
```

```logql
{job="atelier09", dataset="access"}
```

```logql
{job="atelier09", dataset="movies"}
```

```logql
{job="atelier09", dataset="access", status_class="5xx"}
```

```logql
{job="atelier09", dataset="movies"} |= "Toy Story"
```

### Résultat attendu

Les deux formats sont visibles et l’en-tête MovieLens n’est pas envoyé. Sur une première collecte sans ancien état, les entrées candidates correspondent au rapport preparation.json, sous réserve de l’absence de rejets et de la période/limite de requête.

Un échantillon sans 5xx retourne normalement zéro résultat pour cette sélection. Le test de sonde suivant ajoute un 503 explicite pour vérifier cette branche.

### Point de contrôle

Développer une ligne : identifier timestamp Loki, labels et texte original. Pour une archive, la date Apache dans le texte peut différer de la date Loki ; c’est le choix de la section 9, pas une corruption invisible du fichier.

## 19. Ajouter des lignes sans redémarrer Alloy

### Objectif

Prouver la collecte continue des deux fichiers suivis, pas seulement leur lecture initiale.

```bash
sudo python3 ajouter_sondes09.py --kind both
```

Le script ajoute :

- une requête Apache synthétique, statut 503, chemin /atelier09/probe/ suivi d’un marqueur unique ;
- une ligne CSV synthétique avec un titre contenant une virgule et des guillemets, et le même marqueur.

Il ne réécrit pas les sources de référence. Copier le marker affiché dans une recherche :

```logql
{job="atelier09", dataset="access"} |= "MARQUEUR_AFFICHE"
```

```logql
{job="atelier09", dataset="movies"} |= "MARQUEUR_AFFICHE"
```

### Résultat attendu

Une nouvelle ligne par corpus pour cette invocation ; l’access log porte status_class=5xx si l’extraction correspond. Aucun redémarrage d’Alloy n’est nécessaire.

Le movieId de sonde est un identifiant de test réutilisé volontairement. Loki ne remplace pas l’ancienne ligne lorsque ce même ID revient : contrairement à index avec _id dans Elasticsearch, il s’agit de nouvelles entrées de collecte.

### Explication

Le bouton Refresh de Grafana relance la recherche ; il n’écrit pas de sonde et ne pousse pas le fichier. Le script, le collecteur, le stockage et la requête sont quatre étapes distinctes.

## 20. Vérifier par l’API Loki

### Objectif

Contrôler la chaîne sans dépendre seulement de l’interface.

```bash
END=$(python3 -c 'import time; print(time.time_ns())')
START=$(python3 -c 'import time; print(time.time_ns() - 15*60*10**9)')

curl --fail-with-body -G http://127.0.0.1:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="atelier09",dataset="access"}' \
  --data-urlencode "start=$START" --data-urlencode "end=$END" \
  --data-urlencode 'direction=forward' --data-urlencode 'limit=1000' \
  -o loki-access-response.json
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('loki-access-response.json').read_text())
if r.get('status') != 'success':
    raise SystemExit(str(r))
result = r['data']['result']
print('Flux :',len(result))
print('Lignes recues :',sum(len(s.get('values',[])) for s in result))
for s in result:
    print(s['stream'])
PY
```

Adapter dataset pour movies et la fenêtre si la collecte est plus ancienne. La limite 1000 plafonne les lignes reçues ; ce n’est pas une preuve de comptage exhaustif à grande échelle. Les requêtes métriques LogQL des ateliers suivants serviront à analyser les volumes.

## 21. Tester la reprise après arrêt

### Procédure

1. Attendre que les premières sondes soient visibles.
2. Arrêter le collecteur.
3. Ajouter une nouvelle sonde pendant l’arrêt.
4. Redémarrer et rechercher ce marqueur.

```bash
sudo systemctl stop alloy
sudo python3 ajouter_sondes09.py --kind both
sudo systemctl start alloy
sudo journalctl -u alloy -n 100 --no-pager
```

### Résultat attendu et limites

Les lignes restées dans les fichiers sont collectées lors de la reprise si fichiers, permissions, stockage d’état et destination restent disponibles. Les positions évitent normalement de tout reprendre depuis le début à chaque restart.

Ce test ne démontre pas une livraison exactement-une-fois dans tous les scénarios de panne. Ne pas effacer /var/lib/alloy ou changer --storage.path pour forcer une réingestion : cela peut produire des relectures et des doublons. En cas de problème, examiner les journaux et l’état avant d’intervenir.

## 22. Variante : utiliser la date d’événement Apache

### Objectif

Comprendre comment la map extraite peut alimenter un autre stage.

Seulement si le fichier contient des dates récentes acceptées par votre Loki et si vous souhaitez cette sémantique, ajouter après stage.regex, dans loki.process access :

```alloy
stage.timestamp {
  source            = "apache_time"
  format            = "02/Jan/2006:15:04:05 -0700"
  action_on_failure = "skip"
}
```

Puis adapter le label time_basis de cette source en event, valider et appliquer la modification. Ne pas ajouter ce stage au traitement CSV : l’année du titre n’est pas une date de collecte.

### Explication

- source vise le champ extrait apache_time, pas un label Loki.
- Le format suit les conventions de date Go, pas %d/%b/%Y de Python.
- Si le parsing échoue avec skip, le timestamp préexistant est conservé ; la ligne n’est pas forcément supprimée.
- Une date correctement parsée mais trop ancienne peut ensuite être refusée par Loki : ce n’est pas un échec de parsing.

Le label time_basis=event décrit alors une intention ; avec un fallback skip, toutes les lignes ne sont pas garanties de disposer d’un timestamp événement correctement extrait. Examiner les cas non reconnus si cette distinction est importante.

Ne pas relire brutalement une archive ancienne après ce changement, ne pas désactiver toutes les limites Loki pour faire disparaître le symptôme. Préparer un rejeu explicitement réhorodaté si nécessaire et garder sa provenance de simulation. Un même document dans Elasticsearch et une ligne Loki ne deviennent pas automatiquement corrélés dans le temps parce qu’ils viennent du même fichier.

## 23. Extension : découverte de fichiers

Les chemins fixes du TP n’en ont pas besoin. Pour un véritable ensemble de fichiers rotatifs, la documentation actuelle propose la découverte intégrée à loki.source.file via file_match, ou le composant local.file_match.

Étudier la version installée avant d’ajouter un bloc récent. Un glob trop large peut lire fichiers d’état, copies ou sauvegardes et ingérer plusieurs fois le même corpus.

Ne pas copier les exemples de découverte en plus des sources actuelles sur les mêmes chemins sans revoir le graphe : deux lecteurs indépendants peuvent envoyer deux copies des lignes.

## 24. Observabilité du collecteur et diagnostic

| Symptôme | Vérification prioritaire |
|---|---|
| Alloy ne démarre pas | alloy validate et journalctl |
| Service actif sans logs | Chemins, permissions, données, positions et forward_to |
| Un seul corpus visible | Source spécifique, traitement, dataset et fenêtre |
| CSV tronqué ou décalé | CSV multiligne ou mauvais parsing ; garder un vrai parseur en préparation |
| Pas de label status_class | Regex non correspondante ; ligne brute toujours disponible |
| Erreurs d’écriture Loki | URL, /ready, limites, journaux de Loki |
| Rejet de dates | Différencier archive, parsing et politique d’acceptation |
| Trop de flux | IP, titre, ID ou chemin libre devenus labels |
| Compteur supérieur au rapport | Sondes, ancien état, relectures, autres tests et limites de période |
| Fichier original change mais rien n’arrive | Alloy suit la copie dédiée, pas l’original |

### Commandes utiles

```bash
sudo systemctl status alloy loki-formation grafana-server --no-pager
sudo journalctl -u alloy -n 100 --no-pager
sudo journalctl -u loki-formation -n 100 --no-pager
sudo -u alloy head -n 1 /var/log/formation-alloy09/access_log
sudo -u alloy head -n 1 /var/log/formation-alloy09/movies.csv
```

L’interface et les métriques internes Alloy peuvent être disponibles sur son adresse HTTP de diagnostic, souvent le port 12345 selon le service. Vérifier les arguments réellement configurés ; ne pas ouvrir ce port sur Internet pour le TP.

Un collecteur actif, une configuration valide et un endpoint ready sont des indices nécessaires, mais la preuve de bout en bout est une sonde écrite puis retrouvée dans Loki.

## 25. Défi final

### Énoncé

Avec les deux mêmes fichiers suivis :

1. Expliquer chaque flèche du graphe et le rôle des cinq composants.
2. Vérifier les deux fichiers comme utilisateur alloy.
3. Montrer les deux corpus dans Explore sans l’en-tête CSV.
4. Ajouter une sonde access seule, sans modifier movies.csv.
5. Ajouter une sonde movies seule, sans modifier access_log.
6. Retrouver leurs marqueurs et identifier le 503 par status_class.
7. Tester une reprise sans effacer l’état.
8. Justifier pourquoi movieId et client_ip restent dans le contenu.
9. Expliquer le timestamp utilisé et pourquoi il ne mesure pas ici la fraîcheur réelle du serveur web.

## 26. Corrigé guidé

```bash
sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
sudo -u alloy alloy validate /etc/alloy/config.alloy
sudo python3 ajouter_sondes09.py --kind access
sudo python3 ajouter_sondes09.py --kind movies
```

Après quelques secondes, rechercher chaque marqueur retourné dans son dataset. La sonde access correspond à :

```logql
{job="atelier09",dataset="access",status_class="5xx"} |= "MARQUEUR_ACCESS"
```

La sonde MovieLens correspond à :

```logql
{job="atelier09",dataset="movies"} |= "MARQUEUR_MOVIES"
```

Pour une sonde de chaque type, deux lignes nouvelles sont attendues au total, pas deux mises à jour d’anciens objets. Les invocations répétées produisent de nouveaux marqueurs et de nouvelles entrées.

### Réponses attendues

- Deux sources permettent des labels et traitements indépendants.
- Les stages s’exécutent dans l’ordre dans chaque process.
- Les références receiver relient le graphe ; l’ordre des blocs globaux n’est pas un script d’exécution.
- Un champ extrait n’est pas automatiquement un label.
- CSV correctement écrit n’implique pas champs CSV automatiquement parsés dans Loki.
- Une archive lue maintenant reçoit le timestamp de collecte dans le parcours principal.
- Les preuves sont les lignes retrouvées, pas seulement systemctl active.

## 27. Checklist et livrables

- Version Alloy et fichier de configuration effectif documentés.
- Deux sources de référence identifiées ; copies de travail et rapport conservés.
- Permissions et compte de service vérifiés.
- config.alloy expliqué : logging, source, process, write, targets et forward_to.
- Choix des labels et politique de temps justifiés.
- En-tête CSV filtré, lignes de contenu conservées.
- Deux sondes retrouvées dans Grafana/API.
- Reprise testée sans suppression de l’état.
- Aucune donnée sensible ou clé dans les captures.

Livrer config.alloy expurgé, preparation.json, scripts, marqueurs observés et une courte note : ce qui a été collecté, quand, avec quelles limites.

## 28. Conservation et suite du parcours

Conserver les deux fichiers, Alloy, Loki et Grafana pour les ateliers 10 à 12. Ne pas annoncer les anciens totaux du générateur JSON de l’atelier initial : ce corpus les remplace.

Au début d’un nouvel atelier, ajouter une sonde ou choisir une période couvrant la collecte précédente. Un CSV statique n’émet pas spontanément de nouvelles lignes et Grafana Refresh n’en crée pas.

La source JSON des anciens exercices n’est plus un prérequis de cet atelier. Les futurs exercices de parser JSON devront être adaptés explicitement ou accompagnés d’une nouvelle source instrumentée, pas supposés applicables au CSV brut.

Pour suspendre la collecte : sudo systemctl stop alloy. Pour reprendre : sudo systemctl start alloy. Garder le stockage d’état. Toute restauration de config doit être contrôlée, validée et documentée.

## Annexes — Scripts complets

### preparer_corpus09.py

```python
import argparse
import csv
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Copies de travail access_log et MovieLens pour Alloy')
p.add_argument('--access', required=True)
p.add_argument('--movies', required=True)
p.add_argument('--output-dir', default='corpus09')
p.add_argument('--access-lines', type=int, default=200)
p.add_argument('--movies-rows', type=int, default=200)
a = p.parse_args()
if a.access_lines < 1 or a.movies_rows < 1:
    p.error('Les tailles doivent etre positives')
sources = [Path(a.access).resolve(),Path(a.movies).resolve()]
if not all(x.is_file() for x in sources):
    p.error('Un fichier source est absent')
target = Path(a.output_dir)
if target.exists():
    p.error('Le dossier de sortie existe deja : choisir un nouveau nom')
access = []
with sources[0].open(encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        access.append(line.rstrip('\r\n'))
        if len(access) == a.access_lines:
            break
movies = []
with sources[1].open(encoding='utf-8-sig',newline='') as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != ['movieId','title','genres']:
        p.error('Entete MovieLens attendu : movieId,title,genres')
    for row in reader:
        if None in row or any(row.get(key) is None for key in reader.fieldnames):
            p.error('Ligne CSV incomplete ou colonnes en trop')
        if any('\n' in value or '\r' in value for value in row.values()):
            p.error('Champ CSV multiligne : non adapte a une collecte Loki ligne par ligne')
        int(row['movieId'])
        movies.append(row)
        if len(movies) == a.movies_rows:
            break
if not access or not movies:
    p.error('Les deux sources doivent contenir des donnees')
target.mkdir(parents=True)
(target/'access_log').write_text('\n'.join(access)+'\n',encoding='utf-8')
with (target/'movies.csv').open('w',encoding='utf-8',newline='') as f:
    writer = csv.DictWriter(f,fieldnames=['movieId','title','genres'],lineterminator='\n')
    writer.writeheader()
    writer.writerows(movies)
report = {
    'access_source':str(sources[0]),'movies_source':str(sources[1]),
    'access_lines':len(access),'movies_records':len(movies),
    'movies_file_lines_including_header':len(movies)+1,
    'expected_loki_entries_before_probes':len(access)+len(movies),
    'note':'Copies echantillonnees, sources intactes ; horodatage Loki = collecte'
}
(target/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
```

### ajouter_sondes09.py

```python
import argparse
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Ajoute des sondes synthetiques aux deux fichiers de lab')
p.add_argument('--directory', default='/var/log/formation-alloy09')
p.add_argument('--kind', choices=['access','movies','both'], default='both')
a = p.parse_args()
base = Path(a.directory)
paths = [base/'access_log'] if a.kind == 'access' else [base/'movies.csv'] if a.kind == 'movies' else [base/'access_log',base/'movies.csv']
for path in paths:
    if not path.is_file():
        p.error('Fichier de lab absent : '+str(path))
    with path.open('rb') as f:
        f.seek(0,2)
        size=f.tell()
        if size:
            f.seek(-1,2)
            if f.read(1)!=b'\n':
                p.error('Fichier sans saut de ligne final : '+str(path))
now=datetime.now(timezone.utc)
marker=now.strftime('A09-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
if a.kind in ['access','both']:
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    stamp=f'{now.day:02d}/{months[now.month-1]}/{now.year:04d}:'+now.strftime('%H:%M:%S')+' +0000'
    line=f'127.0.0.1 - - [{stamp}] "GET /atelier09/probe/{marker} HTTP/1.1" 503 128 "-" "Alloy-formation-probe"'
    with (base/'access_log').open('a',encoding='utf-8') as f:
        f.write(line+'\n')
if a.kind in ['movies','both']:
    title=f'Alloy probe {marker}, edition "test" (2026)'
    with (base/'movies.csv').open('a',encoding='utf-8',newline='') as f:
        csv.writer(f,lineterminator='\n').writerow([9000901,title,'Documentary|Sci-Fi'])
print(json.dumps({'marker':marker,'kind':a.kind,'synthetic':True,
                  'movie_id_note':'ID de test repete volontairement ; Loki conserve les lignes, sans upsert'},ensure_ascii=False,indent=2))
```

## Sources et validation formateur

Support révisé à partir de l’atelier 09 fourni, en réutilisant access_log et MovieLens des ateliers précédents. Références Grafana : syntaxe Alloy, configuration Linux, loki.source.file, loki.process, loki.write et commande validate.

Les scripts Python ont été vérifiés syntaxiquement et exécutés localement sur des fichiers de test, dont un échantillon du vrai access_log et un CSV avec virgules/guillemets. Les cas de refus de sortie existante et CSV multiligne ont été testés. Les motifs d’extraction ont été contrôlés sur les lignes échantillonnées avec les limites décrites.

Le binaire Alloy, le service systemd et l’envoi Loki n’ont pas été exécutés dans l’environnement de génération. Le formateur doit utiliser alloy validate puis répéter les tests d’ingestion sur les versions installées. Le fichier joint n’est pas annoncé comme validé par le compilateur Alloy.
