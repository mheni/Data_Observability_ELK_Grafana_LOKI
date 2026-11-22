# Atelier 11 — LogQL : parser access_log et MovieLens, comparer les champs et contrôler les erreurs

## Fiche pédagogique

| Rubrique | Description |
|---|---|
| Parcours | Data Observability — jour 4, atelier 11 |
| Durée indicative | 2 h à 2 h 30 |
| Infrastructure | Ubuntu, Alloy, Loki et Grafana des ateliers précédents |
| Prérequis | Collecte des deux fichiers A09, requêtes API/Explore A10 |
| Corpus brut conservé | access_log et movies.csv |
| Prolongement structuré | Copies dérivées JSON et logfmt des mêmes données |
| Livrable | Requêtes structurées, diagnostic de parsing et comparaison brut/normalisé |

## 1. Introduction et objectifs

L’atelier 10 recherchait surtout des chaînes dans une ligne. Nous allons maintenant demander : « le champ statut vaut-il 503 ? », « quel est le titre complet du film ? », « cette valeur peut-elle être convertie en nombre ? ».

```text
Sélecteur de flux → filtre de ligne justifié → parser
→ contrôle des erreurs → présence des champs → comparaison/conversion
→ présentation du résultat
```

### Objectifs pédagogiques conservés et adaptés

- Distinguer labels d’ingestion et champs extraits à la requête.
- Parser les access logs avec pattern et regexp.
- Comprendre pourquoi une regex naïve ne suffit pas pour tout le CSV.
- Utiliser json et logfmt sur des vues dérivées explicitement préparées.
- Créer des alias et comprendre les collisions de noms.
- Comparer chaînes, nombres, durées et tailles avec les bonnes unités.
- Distinguer erreur de format, champ absent, conversion impossible et valeur métier incohérente.
- Utiliser __error__ et line_format sans masquer les problèmes.
- Exécuter les mêmes recherches dans Grafana et par l’API de l’atelier 10.
- Préparer les bases d’un unwrap fiable pour l’atelier 12, sans calculer encore de métrique.

Nous ne rétablissons pas l’ancien générateur de douze logs JSON applicatifs. Les exemples restent liés aux access logs et aux films déjà utilisés.

## 2. Continuité avec Alloy et Loki

### Les deux sources originales restent inchangées

```text
/var/log/formation-alloy09/access_log ─► job=atelier09, dataset=access
/var/log/formation-alloy09/movies.csv ─► job=atelier09, dataset=movies
```

Elles continuent de passer par la configuration Alloy de l’atelier 09. Dans le parcours principal, leur timestamp Loki reste l’heure de collecte.

### Pourquoi ajouter deux vues dérivées ?

Apache et CSV ne sont pas du JSON ou du logfmt. Appliquer | json au CSV ne le convertit pas correctement. Pour conserver les objectifs JSON/logfmt, nous préparons deux représentations explicites des mêmes enregistrements :

```text
Sources de référence A09, lues seulement
       │ Python : regex Apache limitée + vrai module csv
       ├─► events.jsonl ──► job=atelier11, format=json
       └─► events.logfmt ─► job=atelier11, format=logfmt
```

Ce sont des copies de démonstration, pas un nouveau système de vérité ni des formats que Loki aurait reconnus automatiquement. Les événements dérivés portent un normalization_id et conservent leur source_dataset.

Ne pas additionner leurs compteurs aux sources brutes : chaque enregistrement est volontairement représenté deux fois, une fois par format.

## 3. Vérifier la collecte et choisir la période

### Commandes

```bash
sudo systemctl status alloy loki-formation grafana-server --no-pager
curl -fsS http://127.0.0.1:3100/ready
sudo -u alloy test -r /var/log/formation-alloy09/access_log
sudo -u alloy test -r /var/log/formation-alloy09/movies.csv
```

### Dans Explore

```logql
{job="atelier09",dataset="access"}
```

```logql
{job="atelier09",dataset="movies"}
```

Choisir la période couvrant leur collecte, pas forcément Last 15 minutes. La fenêtre absolue enregistrée à l’atelier 10 peut retrouver les six sondes A10 même si leur collecte est maintenant ancienne.

Le marqueur des sondes A10 se trouve dans scenario10.json. Les requêtes sur le brut peuvent le réutiliser pour attendre quatre access logs et deux films, sans effacer les anciens événements.

### Dépannage

Une absence totale de lignes avant parsing se diagnostique d’abord par période, labels et chaîne de collecte. Changer de parser ne résout pas un fichier illisible ou une destination Loki incorrecte.

## 4. Labels d’ingestion et champs de requête

| Élément | Origine | Utilisation |
|---|---|---|
| job, dataset, format, service | Configuration Alloy | Sélecteur de flux dans les accolades |
| status_class sur access | Extraction/promu à l’ingestion A09 | Sélection de familles HTTP |
| method_value, status_value | Parser LogQL | Filtres après le parser |
| movie_id, title dans JSON dérivé | Contenu de la ligne JSON | Extraction à la requête |
| normalization_id | Contenu des copies dérivées | Isolation d’un lot de préparation |

Un parser produit des labels de résultat pendant la recherche. Il ne réécrit pas l’index d’ingestion et ne crée pas rétroactivement un stream stocké par film ou par IP.

Si un nom extrait existe déjà comme label original, le résultat peut utiliser un suffixe _extracted. Employer des alias explicites rend la requête plus facile à lire.

Les valeurs extraites sont utilisées comme labels dans le pipeline LogQL ; le fait qu’un champ JSON soit numérique n’évite pas les conversions nécessaires lors d’un filtre numérique ou d’un futur unwrap.

## 5. Parser les access logs bruts avec pattern

### Objectif

Retrouver un vrai champ statut au lieu d’un nombre présent n’importe où dans le texte.

Requête sur les sondes A10 ; remplacer __A10_MARKER__ par leur vrai marker :

```logql
{job="atelier09",dataset="access"} |= "__A10_MARKER__"
| pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <bytes_value> "<referer_value>" "<agent_value>"`
| method_value!=""
| path_value!=""
| status_value!=""
| status_value >= 500
| status_value < 600
| __error__=""
```

### Résultat attendu sur le lot A10

La sonde 503, pas le 200 dont le message dit recovered after timeout.

### Explication du motif

- Les captures <nom> donnent des champs utilisables après le parser.
- <_> ignore une partie non utile.
- Les espaces, crochets et guillemets du motif correspondent à la structure Apache.
- Le motif est ancré au début par défaut.
- La date entre crochets peut contenir un espace et reste capturée grâce au séparateur suivant.
- Les alias évitent de confondre le statut complet avec le label status_class de l’ingestion.

pattern convient aux formats stables, mais ne constitue pas une implémentation complète de toute requête HTTP possible. Une requête atypique peut manquer une capture ; vérifier les champs requis, pas seulement __error__.

Pour ignorer un préfixe, une capture initiale <_> peut être utilisée si un littéral fiable suit. Elle ne rend pas le parser sémantique.

## 6. Utiliser regexp quand le motif l’exige

```logql
{job="atelier09",dataset="access"} |= "__A10_MARKER__"
| regexp `^(?P<client_ip_value>\S+) \S+ \S+ \[[^\]]+\] "(?P<request_value>[^"]*)" (?P<status_value>[0-9]{3}) (?P<bytes_value>[0-9]+|-)`
| status_value!=""
| status_value >= 500
| __error__=""
```

### Explication

Les groupes nommés (?P<nom>...) créent les champs extraits. L’expression est écrite en chaîne brute entre backticks ; on ne double pas les antislashs comme dans un JSON contenant la requête.

Ce motif reconnaît le début de la ligne Apache ; il ne prétend pas valider tout le référent ou l’agent utilisateur. Des guillemets échappés et formats atypiques demandent un motif testé et maintenu.

Les expressions reposent sur RE2 : ne pas copier des fonctionnalités PCRE comme les lookarounds en supposant qu’elles seront acceptées.

### Point de contrôle

Comparer pattern et regexp sur la même période et les mêmes sondes. Si un résultat manque, examiner la ligne exacte et la capture absente avant d’ajouter un filtre plus strict.

## 7. Octets : une absence ne vaut pas zéro

Après le pattern de la section 5, une taille inconnue peut être représentée par le caractère '-'. Pour rechercher de grandes réponses :

```logql
{job="atelier09",dataset="access"}
| pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <bytes_value> "<referer_value>" "<agent_value>"`
| bytes_value!=""
| bytes_value!="-"
| bytes_value >= 1000
| __error__=""
```

1000 signifie ici mille octets, car le champ source exprime une taille. Ce n’est pas une durée. Sans filtre de présence et exclusion du tiret, une conversion peut échouer.

Dans le jeu A10, chaque sonde possède 128 octets : zéro résultat à ce seuil est normal. Sur l’archive réelle, les nombres dépendent du corpus.

L’access log de base n’a toujours pas de durée de requête : ne pas calculer une « latence HTTP » à partir de bytes ou du temps de collecte.

## 8. CSV MovieLens : montrer le piège avant la solution

### Extraction limitée à un premier champ simple

```logql
{job="atelier09",dataset="movies"}
| regexp `^(?P<movie_id_value>[0-9]+),`
| movie_id_value="9001001"
```

Cette requête est adaptée au premier champ numérique non cité des fichiers préparés A09. Elle ne parse pas toutes les colonnes CSV.

### Mauvaise généralisation à discuter

```logql
{job="atelier09",dataset="movies"}
| pattern `<movie_id_value>,<title_value>,<genres_value>`
```

Le titre de sonde A10 contient une virgule et des guillemets CSV. Le motif peut s’arrêter à une virgule interne et produire une capture title_value tronquée, voire une capture genres_value incohérente, sans que l’absence de __error__ garantisse une ligne correcte.

### Solution retenue

Utiliser csv.DictReader dans la préparation des vues JSON/logfmt. On conserve le titre complet comme une valeur unique ; aucun split(',') ni parser regexp prétendument universel n’est présenté comme solution générale au CSV.

## 9. Préparer les copies structurées sans toucher aux originaux

### Objectif

Comparer plusieurs parsers sur les mêmes données et disposer de contrôles de qualité explicites.

Le script normaliser_sources11.py joint lit les deux fichiers A09 et produit deux fichiers dérivés. Depuis le dossier de l’atelier, avec les scripts fournis :

```bash
mkdir -p ~/formation-observabilite/atelier11
cd ~/formation-observabilite/atelier11
set -o pipefail

sudo python3 normaliser_sources11.py \
  --access /var/log/formation-alloy09/access_log \
  --movies /var/log/formation-alloy09/movies.csv \
  --output-dir corpus11 --with-controls | tee preparation11.json

sudo test -s corpus11/manifest.json
```

Ne pas poursuivre si la préparation échoue. Le dossier existant est refusé. En cas d’échec après création, une sortie partielle peut exister sans manifest valide ; ne pas l’installer comme un corpus réussi.

### Ce que fait le code

| Partie | Fonction |
|---|---|
| Lecture access_log | Conserve raw_line et extrait un ensemble de champs Apache |
| parse_ok | Indique si le début de la ligne a été reconnu, pas une certification HTTP complète |
| csv.DictReader | Reconstruit les enregistrements CSV avec leurs virgules et guillemets |
| movie_id / title / genres | Champs explicites ; genres est un tableau JSON |
| genres_text | Version textuelle simple pour logfmt |
| year | Ajouté seulement si une année est reconnue en fin de titre |
| normalization_id / record_id | Identifie le lot et ses copies ; pas de nouveaux labels d’ingestion |
| metadata | Petit objet imbriqué pour une extraction JSON ciblée |
| Deux sorties | JSON par ligne et logfmt avec valeurs citées correctement |

Les objets/tableaux ne sont pas sérialisés comme colonnes logfmt implicites ; les valeurs scalaires utiles, dont genres_text, y sont présentes. Un titre multiligne éventuel peut être réencodé dans une chaîne JSON/logfmt échappée ; cela ne rend pas le CSV brut multiligne compatible avec la lecture ligne par ligne d’A09.

Les lignes Apache non reconnues restent représentées avec parse_ok=false et raw_line ; elles ne disparaissent pas silencieusement de la copie JSON.

### Unités d’observation et provenance

source_line désigne une ligne physique pour access et le numéro d’enregistrement logique pour movies. Les champs source ne deviennent pas automatiquement une durée ou un niveau de log applicatif.

La préparation est un instantané : de nouvelles lignes ajoutées à A09 ensuite ne sont pas automatiquement normalisées. Il ne s’agit pas d’un convertisseur continu de production.

## 10. Contrôles synthétiques : ce qui est testé, et ce qui ne l’est pas

Avec --with-controls, quatre enregistrements supplémentaires sont créés dans chaque format :

| test_case | level | duration_ms | elapsed | payload | Rôle |
|---|---|---|---|---|---|
| C_VALID | WARN | 1800 | 1.8s | 2MB | Conversions valides |
| C_BAD | ERROR | unknown | unknown | unknown | Conversion impossible |
| C_MISSING | INFO | absent | absent | absent | Champ manquant sans JSON invalide |
| C_NEGATIVE | ERROR | -5 | -5ms | 1KB | Nombre valide, sens métier incohérent |

C_MISSING contient aussi le mot ERROR dans son message, pour comparer recherche textuelle et égalité du champ level.

Ces quatre lignes sont explicitement synthetic=true et source_dataset=controls. Elles ne proviennent pas des requêtes réelles ; elles ne fournissent pas une mesure de latence du serveur web.

### Comptage attendu

Pour A lignes access et M enregistrements movies : A + M + 4 entrées par format, soit deux fois ce nombre pour les deux fichiers. Le manifeste contient les valeurs effectivement préparées.

Ne pas présenter ce volume doublé comme un nombre de requêtes HTTP ou d’imports métiers. Toujours préciser le format et la source_dataset dans une requête de contrôle.

## 11. Ajouter deux sources dérivées à Alloy, sans remplacer A09

### Installer les sorties sur un répertoire neuf

```bash
sudo install -d -m 2750 -o root -g alloy /var/log/formation-alloy11
sudo ls -l /var/log/formation-alloy11
```

Si les fichiers y existent et sont déjà suivis, ne pas les écraser. Pour une première installation :

```bash
sudo install -m 640 -o root -g alloy corpus11/events.jsonl /var/log/formation-alloy11/events.jsonl
sudo install -m 640 -o root -g alloy corpus11/events.logfmt /var/log/formation-alloy11/events.logfmt
sudo -u alloy test -r /var/log/formation-alloy11/events.jsonl
sudo -u alloy test -r /var/log/formation-alloy11/events.logfmt
```

Le dossier de préparation est volontairement protégé ; utiliser sudo pour lire ses fichiers. preparation11.json est le rapport affiché, sans les contenus de logs.

### Composant additionnel fourni

```alloy
// Ajout A11 : vues derivees seulement ; ne remplace pas les deux sources A09.
// Necessite loki.write "local" deja defini dans config.alloy.
loki.source.file "atelier11_normalises" {
  targets = [
    {
      __path__    = "/var/log/formation-alloy11/events.jsonl",
      job         = "atelier11",
      service     = "normalisation-lab",
      environment = "formation",
      dataset     = "normalised",
      format      = "json",
      time_basis  = "collection",
    },
    {
      __path__    = "/var/log/formation-alloy11/events.logfmt",
      job         = "atelier11",
      service     = "normalisation-lab",
      environment = "formation",
      dataset     = "normalised",
      format      = "logfmt",
      time_basis  = "collection",
    },
  ]
  tail_from_end = false
  forward_to    = [loki.write.local.receiver]
}
```

Il envoie directement les lignes vers le writer déjà présent. Aucun parser JSON/logfmt d’ingestion n’est ajouté : le but est de les appliquer à la requête.

### Fusion contrôlée

Vérifier d’abord que le nom atelier11_normalises n’est pas déjà présent. Sur la VM de lab utilisant /etc/alloy/config.alloy :

```bash
sudo install -m 640 -o root -g alloy ajout_atelier11.alloy /etc/alloy/atelier11-addition.alloy
sudo cp /etc/alloy/config.alloy "/etc/alloy/config.alloy.before-atelier11-$(date +%Y%m%dT%H%M%S)"
sudo sh -c 'cat /etc/alloy/config.alloy /etc/alloy/atelier11-addition.alloy > /etc/alloy/atelier11-candidate.alloy'
sudo chown root:alloy /etc/alloy/atelier11-candidate.alloy
sudo chmod 640 /etc/alloy/atelier11-candidate.alloy
sudo -u alloy alloy validate /etc/alloy/atelier11-candidate.alloy
```

Seulement après succès :

```bash
sudo install -m 640 -o root -g alloy /etc/alloy/atelier11-candidate.alloy /etc/alloy/config.alloy
sudo systemctl restart alloy
sudo journalctl -u alloy -n 100 --no-pager
```

Ne pas ajouter un deuxième loki.write local et ne pas exécuter la concaténation plusieurs fois. Si le service charge un autre chemin ou un répertoire entier, adapter l’organisation : les fichiers candidate/addition ne doivent pas être chargés simultanément comme doublons.

### Premier contrôle dans Explore

```logql
{job="atelier11",format="json"}
```

```logql
{job="atelier11",format="logfmt"}
```

Les timestamps sont ceux de la collecte de ces copies. Ils ne prétendent pas préserver la même chronologie de collecte que les lignes brutes A09.

## 12. Isoler le lot et préparer les fichiers de requêtes

### Procédure

```bash
python3 construire_requetes11.py --manifest preparation11.json \
  --scenario10 "$HOME/formation-observabilite/atelier10/scenario10.json" \
  --output-dir requetes11
```

--scenario10 est facultatif : sans ce fichier, seules les requêtes sur les copies normalisées sont créées. Le script remplace les placeholders par les vrais marqueurs ; il ne teste pas le langage sur Loki.

Les blocs du support utilisent __NID__ pour normalization_id et __A10_MARKER__ pour les sondes brutes. Ne pas copier ces textes littéralement : utiliser les fichiers générés ou remplacer les valeurs.

### Période

Choisir une fenêtre couvrant la collecte des fichiers A11. Elle peut être postérieure à l’heure de préparation. Isoler le normalization_id évite de mélanger plusieurs normalisations sans supprimer de données.

Pour les requêtes brutes sur A10, conserver une période incluant la collecte A10 ; ce n’est pas forcément la même fenêtre que celle des copies A11.

## 13. Parser le JSON complet puis comparer un champ

### Observer

```logql
{job="atelier11",format="json"} |= "__NID__"
| json
```

Développer les résultats pour observer source_dataset, movie_id, title, status ou test_case selon le type d’enregistrement.

### Filtrer les vrais champs

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", parsed_level="level", case_id="test_case"
| __error__=""
| kind="controls"
| parsed_level="ERROR"
```

Sur les contrôles, deux lignes ont réellement level=ERROR : C_BAD et C_NEGATIVE.

Un simple filtre |= "ERROR" sur ces mêmes contrôles peut aussi retrouver C_MISSING, dont le niveau est INFO et le message mentionne ERROR. La comparaison structurée ne s’appuie pas sur une convention de mots à exclure.

### Explication

| json transforme les propriétés exploitables en labels de résultat. Les objets imbriqués peuvent être aplatis ; les tableaux ne deviennent pas automatiquement un champ multivalué équivalent à Elasticsearch.

Le JSON original stocké n’est pas modifié. Retirer le parser ou le formatage permet de revoir la ligne initiale.

## 14. Extraction ciblée, alias et collisions

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", movie_id_value="movie_id", film_title="title", year_value="year", body_service="service"
| __error__=""
| kind="movies"
| movie_id_value!=""
| film_title!=""
```

### Lire la syntaxe

Les noms à gauche sont les alias utilisés ensuite. Les expressions à droite désignent des champs du JSON. body_service évite la collision avec le label service=normalisation-lab posé par Alloy.

Ici, service du flux décrit la chaîne de normalisation ; body_service décrit le producteur représenté, par exemple movielens-import. Leur différence est volontaire et n’est pas automatiquement une incohérence de source.

### Objet imbriqué et tableau

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", origin="metadata.origin", first_genre="genres[0]"
| __error__=""
| kind="movies"
```

origin décrit la préparation ; first_genre est uniquement le premier élément s’il existe, pas l’ensemble des genres. Les films sans genre produisent normalement une extraction absente, pas un genre inventé.

### Contrôle d’un titre avec virgule

Chercher la copie de la sonde MovieLens A10 avec son identifiant, par exemple movie_id_value="9001001" après extraction. title doit conserver la virgule et les guillemets, contrairement au pattern CSV naïf de la section 8.

## 15. Filtrer les champs Apache normalisés

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", status_value="status", path_value="path", body_service="service"
| __error__=""
| kind="access"
| status_value!=""
| status_value >= 500
| status_value < 600
| __error__=""
```

Le statut est comparé numériquement après extraction. Les deux bornes évitent de confondre tout nombre supérieur à 500 avec un code HTTP valide 5xx.

Le nombre de résultats dépend de l’archive et de ses sondes. Le normalization_id isole la copie ; il ne remplace pas le besoin de préciser source_dataset=access.

Pour vérifier les lignes Apache non reconnues à la préparation :

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", parsed_ok="parse_ok", reason="parse_reason"
| __error__=""
| kind="access"
| parsed_ok="false"
```

Cette information vient du normaliseur, pas d’une erreur JSON. Une ligne JSON syntaxiquement valide peut décrire une ligne source que le parseur Apache n’a pas reconnue.

## 16. Comparaisons numériques, présence et unités

### Nombre brut exprimé en millisecondes — contrôles uniquement

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value >= 1000
| __error__=""
```

Attendu : C_VALID, 1800 ms. L’unité vient de la définition du contrôle, pas du suffixe du nom de champ qui déclencherait une conversion implicite.

### Ordre des vérifications

1. Parser.
2. Contrôler les erreurs de parsing.
3. Vérifier la présence du champ.
4. Faire la comparaison/conversion.
5. Contrôler les erreurs éventuellement produites par cette conversion.

Le second __error__="" n’est pas redondant : une étape numérique peut introduire une erreur après un parsing réussi.

### Chaîne versus nombre

- duration_value="1800" cherche une égalité de valeur extraite.
- duration_value >= 1000 demande une comparaison numérique.
- duration_value >= 1s suppose une représentation de durée compatible, pas un simple nombre 1800 dont le nom finit par _ms.

Pour le vrai access log, bytes se compare numériquement en octets. Les champs duration_ms de contrôle ne constituent pas une mesure de latence HTTP réelle.

## 17. Parser logfmt et comparer durées/tailles

### Observer

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| logfmt
```

Le normaliseur cite correctement les valeurs contenant espaces, guillemets ou caractères échappés. Une valeur comme message="Un texte avec espaces" est un champ unique.

### Durée explicite

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| logfmt
| __error__=""
| source_dataset="controls"
| elapsed!=""
| elapsed >= 1s
| __error__=""
```

Attendu : C_VALID, elapsed=1.8s.

### Taille explicite

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| logfmt
| __error__=""
| source_dataset="controls"
| payload!=""
| payload >= 1MB
| __error__=""
```

Attendu : C_VALID, payload=2MB.

### Explication

Une durée avec unité, un nombre brut et une taille sont trois représentations distinctes. Ne pas comparer un nombre de millisecondes à 1MB ni supposer que tout texte peut être converti.

Les parsers logfmt peuvent être permissifs selon options/version. Inspecter les champs requis ; une ligne partiellement interprétée n’est pas une preuve de complétude. Les objets/tableaux JSON ne sont pas reconstruits automatiquement depuis cette représentation scalaire.

## 18. Comprendre __error__ sans supprimer les preuves

### Appliquer exprès un mauvais parser

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| json
| __error__!=""
```

Les lignes logfmt ne sont pas des documents JSON. Une erreur de parsing, généralement JSONParserErr, est attendue sur la sélection.

Lorsqu’une étape produit une erreur, la ligne peut être conservée avec __error__ et éventuellement __error_details__. Elle n’est pas nécessairement supprimée automatiquement.

### Attention

- __error__="" garde les résultats sans erreur à ce point du pipeline.
- __error__!="" sert au diagnostic des erreurs présentes.
- Une étape suivante peut créer une nouvelle erreur.
- Un champ absent ne génère pas forcément une erreur de parsing.
- Un pattern non reconnu ne doit pas être jugé valide uniquement parce que __error__ est absent.

Conserver une requête d’erreurs en plus de la requête « résultats propres ». Sinon une évolution du format source peut disparaître silencieusement de l’analyse utile.

## 19. Distinguer les quatre catégories de qualité

### A — Erreur de format

Mauvais parser sur logfmt, section 18. La structure attendue n’est pas celle de la ligne.

### B — Erreur de conversion

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value >= 1000
| __error__!=""
```

Attendu : C_BAD. unknown est une chaîne valide en JSON mais pas un nombre comparable. Le label d’erreur est généralement LabelFilterErr ; vérifier les valeurs renvoyées par votre version.

### C — Champ manquant

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value=""
```

Attendu : C_MISSING. Son JSON est valide ; l’absence de duration_ms ne doit pas être transformée arbitrairement en zéro.

### D — Valeur métier incohérente

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value < 0
| __error__=""
```

Attendu : C_NEGATIVE. -5 est numériquement convertible ; cela ne rend pas une durée négative valide pour notre besoin.

### Synthèse

```text
Syntaxe reconnue ≠ champs complets ≠ types convertibles ≠ sens métier correct
```

Cette séparation constitue un contrôle de qualité des données, pas seulement un exercice de grammaire LogQL. Les taux et percentiles de l’atelier 12 devront être fondés sur un périmètre et des valeurs validés.

## 20. Égalité, regex et logique sur champs extraits

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", parsed_level="level", case_id="test_case"
| __error__=""
| kind="controls"
| (parsed_level="WARN" or parsed_level="ERROR")
```

Attendu : C_VALID, C_BAD et C_NEGATIVE. Une variante parsed_level=~"WARN|ERROR" exprime le même choix pour ces valeurs.

Les noms extraits ne vont pas rétroactivement dans le sélecteur initial. Un filtre négatif doit être accompagné d’un contrôle de présence si le besoin exige une valeur renseignée.

Pour une recherche exacte de record_id, extraire cet alias puis comparer sa valeur complète ; un filtre de sous-chaîne du titre peut retrouver plusieurs films ou plusieurs copies.

## 21. Formatage : line_format et label_format

### Afficher un titre complet

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", film_title="title", movie_id_value="movie_id", body_service="service"
| __error__=""
| kind="movies"
| film_title!=""
| line_format `film={{.movie_id_value}} | titre={{.film_title}} | service_contenu={{.body_service}}`
```

line_format transforme la ligne du résultat de recherche, pas la ligne stockée dans Loki. Retirer cette étape pour revoir le JSON.

Une étape de parser suivante reçoit la ligne telle qu’elle circule dans le pipeline. Si elle a été remplacée par un résumé lisible, un | json placé ensuite ne doit plus supposer qu’il reçoit le document JSON initial.

### Étiquette de résultat facultative

Après extraction de body_service :

```logql
| label_format service_lu="{{.body_service}}"
```

Cette étiquette est une transformation du résultat de requête, pas l’ajout d’un label indexé dans tous les anciens streams. Employer des noms explicites ; ne pas masquer une collision en écrasant les labels sans comprendre leur provenance.

## 22. Préfiltrer sans changer le besoin métier

Le filtre |= "__NID__" est justifié ici : toutes les lignes de cette préparation portent ce marqueur. Il réduit les lignes à parser sans retirer une partie du lot voulu.

Un filtre |= "timeout" serait au contraire trop restrictif si l’objectif est « toutes les réponses 5xx », dont le message peut employer un autre mot.

L’ordre utile est généralement : période et labels précis, filtre textuel sémantiquement sûr, parser, filtres sur champs, affichage. Une requête plus rapide qui élimine les bonnes preuves n’est pas une meilleure investigation.

## 23. Exécuter dans Grafana et sans Grafana

### Grafana Explore

- Datasource Loki-Formation et mode Code.
- Période couvrant la collecte A11.
- Ouvrir un fichier de requetes11 et copier son LogQL exact.
- Inspecter les labels du résultat, les champs extraits et __error__ quand présent.

### curl sur la VM

```bash
export LOKI_URL='http://127.0.0.1:3100'
START=$(python3 -c 'import json; print(json.load(open("preparation11.json"))["start_ns"])')
END=$(python3 -c 'import time; print(time.time_ns())')

curl --fail-with-body -G "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode "query=$(cat requetes11/controls_json_duration_valid.logql)" \
  --data-urlencode "start=$START" --data-urlencode "end=$END" \
  --data-urlencode 'direction=forward' --data-urlencode 'limit=100' \
  -o resultat11.json
```

### Contrôler le JSON

```bash
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('resultat11.json').read_text())
if r.get('status')!='success' or r.get('data',{}).get('resultType')!='streams':
    raise SystemExit('Reponse Loki inattendue : '+str(r))
print('Lignes recues :',sum(len(s.get('values',[])) for s in r['data']['result']))
for stream in r['data']['result']:
    print(stream['stream'])
    for value in stream.get('values',[]):
        print(value[0],value[1])
PY
```

Les labels du résultat peuvent contenir des champs parsés, sans qu’ils soient devenus des labels d’ingestion. Un même stream stocké peut produire plusieurs groupes de résultat selon les extractions.

Le nombre de lignes reçues est borné par limit ; il ne prouve pas un comptage exhaustif au-delà du plafond. Pour ce contrôle, un seul C_VALID est attendu dans le lot normalisé sélectionné.

### Client Python de l’atelier 10

Réutiliser interroger_loki.py fourni dans l’archive A10 : il envoie le LogQL tel quel et accepte donc aussi les parsers. Copier le fichier depuis cette archive si nécessaire, sans modifier sa logique.

Figer des bornes communes à partir du start_ns de preparation11.json et d’une fin postérieure à la collecte avant de comparer exactement l’API à Explore. Ne pas réutiliser aveuglément les anciennes bornes A10 pour A11.

## 24. Défi final

### Énoncé

1. Sur le brut access, extraire méthode, chemin et statut de la sonde A10 503.
2. Sur movies, montrer pourquoi une séparation naïve par virgule ne préserve pas le titre cité.
3. Sur la copie JSON, afficher le titre complet de ce même enregistrement.
4. Retrouver uniquement les contrôles level=ERROR, pas l’INFO qui mentionne ERROR.
5. Isoler la durée numérique valide >=1000 ms, puis la valeur non convertible.
6. Distinguer le champ manquant de la durée négative.
7. Refaire la comparaison de durée explicite sur logfmt.
8. Présenter une ligne compacte, puis revenir au brut en retirant line_format.
9. Conserver une réponse API avec la même logique que la requête Explore.

Pour chaque requête : corpus, format, période, marqueur, champs requis, résultat et limites.

## 25. Corrigé et valeurs de référence

Les requêtes correspondantes sont générées dans requetes11 et documentées dans la bibliothèque jointe.

| Besoin | Fichier / procédure | Résultat attendu |
|---|---|---|
| Access 503 brut | access_pattern.logql | Une sonde si le lot A10 est couvert |
| Titre MovieLens complet | json_movies.logql puis filtre sur son movie_id | Titre intact avec virgule/guillemets |
| Contrôles ERROR | controls_json_error_levels.logql | C_BAD et C_NEGATIVE |
| Nombre >=1000 | controls_json_duration_valid.logql | C_VALID |
| Conversion impossible | controls_json_conversion_errors.logql | C_BAD |
| Champ absent | controls_json_missing.logql | C_MISSING |
| Valeur négative | controls_json_negative.logql | C_NEGATIVE |
| Durée explicite >=1s | controls_logfmt_elapsed.logql | C_VALID |
| Taille explicite >=1MB | controls_logfmt_payload.logql | C_VALID |

Ces références supposent une seule normalisation identifiée par son normalization_id et l’option --with-controls. Les requêtes sur l’archive complète n’ont pas de compte arbitraire imposé.

### Justification attendue

Les parsers extraient ; les filtres sélectionnent ; les conversions vérifient des représentations ; une règle métier juge ensuite le sens. Le formatage améliore la lecture sans modifier le stockage. Les erreurs ne doivent pas être exclues de toutes les vues au point de devenir invisibles.

## 26. Tableau de choix et dépannage

| Format / besoin | Outil | Vigilance |
|---|---|---|
| Apache assez stable | pattern | Captures requises, requêtes atypiques |
| Début Apache ou premier ID CSV | regexp ciblé | RE2, limites du motif, pas un CSV universel |
| CSV complet | Vrai parseur CSV en préparation | Virgules, guillemets, enregistrements logiques |
| JSON | json, alias ciblés | Champs absents, objets/tableaux et collisions |
| Paires clé=valeur | logfmt | Citation, parsing partiel et valeurs non convertibles |
| Présentation | line_format | Étapes suivantes ne voient plus le même texte |

### Erreurs fréquentes

- Rien avant parsing : vérifier collecte/période, pas le parser.
- Champ suffixé _extracted : collision ; préférer un alias clair.
- Pas d’erreur mais champ vide : JSON incomplet ou capture non reconnue.
- Conversion qui échoue malgré un premier __error__ vide : contrôler après l’étape numérique.
- Nombre de lignes doublé : formats dérivés additionnés ou nouvelle normalisation mélangée.
- Durée HTTP supposée : aucun champ de durée réelle n’a été ajouté aux vrais access logs.

## 27. Checklist, livrables et conservation

- Deux fichiers bruts A09 conservés et toujours collectés.
- Pattern/regexp interprétés avec leurs limites.
- CSV cité correctement traité par Python.
- Copies dérivées clairement identifiées et non additionnées au volume réel.
- Extraction JSON ciblée et logfmt testées.
- Quatre catégories de qualité distinguées.
- Filtres sur présence et conversions compris.
- Réponse API et recherche Explore comparées.
- Formatage distinct du stockage.

Livrer les requêtes, manifest/rapport, exemples de résultats et une note de qualité. Ne pas publier les IP, URL et raw_line sans contrôle.

Conserver les fichiers normalisés et la configuration additionnelle pour l’atelier 12. Pour un nouveau lot, préparer un nouveau dossier, puis ajouter ses sorties aux fichiers suivis de manière contrôlée ; ne pas les remplacer pendant la lecture et ne pas effacer les positions Alloy.

L’atelier 12 pourra utiliser les vrais logs pour les volumes et tailles, et les contrôles synthétiques de durée pour apprendre les conversions/unwrap. Ne pas présenter ces derniers comme des observations de latence réelle du serveur.

## Annexe — normaliser_sources11.py

```python
import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser(description='Vues JSON/logfmt des deux fichiers de A09, sans les modifier')
p.add_argument('--access',required=True)
p.add_argument('--movies',required=True)
p.add_argument('--output-dir',default='corpus11')
p.add_argument('--with-controls',action='store_true')
a=p.parse_args()
base=Path(a.output_dir)
if base.exists():
    p.error('Dossier de sortie deja present : choisir un nouveau nom')
access_path=Path(a.access)
movies_path=Path(a.movies)
if not access_path.is_file() or not movies_path.is_file():
    p.error('Source absente')
os.umask(0o077)
base.mkdir(parents=True)
start_ns=time.time_ns()-5_000_000_000
normalization_id=datetime.now(timezone.utc).strftime('N11-%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
counts={'access':0,'movies':0,'controls':0,'access_parse_failures':0}
pattern=re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<apache_time>[^\]]+)\] "(?P<request>(?:\\.|[^"\\])*)" (?P<status>\d{3}) (?P<size>\d+|-)')

def emit(source_dataset,source_line,fields,raw_line=None):
    event={'normalization_id':normalization_id,
           'record_id':f'{normalization_id}-{source_dataset}-{source_line}',
           'source_dataset':source_dataset,'source_line':source_line,
           'metadata':{'origin':'atelier11_normalisation','version':1},**fields}
    if raw_line is not None:
        event['raw_line']=raw_line
    json_out.write(json.dumps(event,ensure_ascii=False)+'\n')
    pairs=[]
    for key,value in event.items():
        if isinstance(value,(list,dict)) or value is None:
            continue
        if isinstance(value,bool):
            encoded='true' if value else 'false'
        elif isinstance(value,(int,float)):
            encoded=str(value)
        else:
            encoded=json.dumps(str(value),ensure_ascii=False)
        pairs.append(key+'='+encoded)
    logfmt_out.write(' '.join(pairs)+'\n')

with (base/'events.jsonl').open('x',encoding='utf-8') as json_out, \
     (base/'events.logfmt').open('x',encoding='utf-8') as logfmt_out:
    with access_path.open(encoding='utf-8') as src:
        for number,line in enumerate(src,1):
            raw=line.rstrip('\r\n')
            if not raw.strip():
                continue
            match=pattern.match(raw)
            fields={'service':'web-formation','parse_ok':bool(match)}
            if match:
                fields.update(client_ip=match['ip'],apache_time=match['apache_time'],
                              request_line=match['request'],status=int(match['status']))
                if match['size']!='-':
                    fields['bytes']=int(match['size'])
                request=match['request'].split(' ',2)
                if len(request)==3 and request[2].startswith('HTTP/'):
                    fields.update(method=request[0],path=request[1],protocol=request[2])
            else:
                fields['parse_reason']='Debut Apache non reconnu'
                counts['access_parse_failures']+=1
            emit('access',number,fields,raw)
            counts['access']+=1
    with movies_path.open(encoding='utf-8-sig',newline='') as src:
        reader=csv.DictReader(src)
        if reader.fieldnames!=['movieId','title','genres']:
            raise ValueError('Entete movies.csv inattendu')
        for number,row in enumerate(reader,1):
            if None in row or any(row.get(k) is None for k in reader.fieldnames):
                raise ValueError('CSV incomplet ou colonnes en trop')
            title=row['title']
            genres=[] if row['genres']=='(no genres listed)' else row['genres'].split('|')
            fields={'service':'movielens-import','parse_ok':True,
                    'movie_id':int(row['movieId']),'title':title,
                    'genres':genres,'genres_text':row['genres']}
            year=re.fullmatch(r'.* \((\d{4})\)',title)
            if year:
                fields['year']=int(year[1])
            emit('movies',number,fields)
            counts['movies']+=1
    if a.with_controls:
        controls=[
            {'test_case':'C_VALID','level':'WARN','duration_ms':1800,'elapsed':'1.8s','payload':'2MB','message':'Synthetic duration control'},
            {'test_case':'C_BAD','level':'ERROR','duration_ms':'unknown','elapsed':'unknown','payload':'unknown','message':'Synthetic invalid numeric value'},
            {'test_case':'C_MISSING','level':'INFO','message':'INFO mentions ERROR only as text'},
            {'test_case':'C_NEGATIVE','level':'ERROR','duration_ms':-5,'elapsed':'-5ms','payload':'1KB','message':'Synthetic negative duration'}
        ]
        for number,fields in enumerate(controls,1):
            emit('controls',number,{'service':'synthetic-controls','synthetic':True,**fields})
            counts['controls']+=1
report={'normalization_id':normalization_id,'start_ns':str(start_ns),**counts,
        'per_format':counts['access']+counts['movies']+counts['controls'],
        'expected_total_both_formats':2*(counts['access']+counts['movies']+counts['controls']),
        'sources_unchanged':True,'state':'Preparation only; no Loki delivery confirmed'}
(base/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
```

Le script construire_requetes11.py et la bibliothèque requetes-logql-atelier11.md sont également joints. Les composants Alloy additionnels doivent être validés avec la version installée avant activation.

## Sources et validation formateur

Objectifs repris de l’atelier 11 fourni : JSON/logfmt/pattern, champs extraits, valeurs numériques, erreurs et présentation. Alignement sur les deux sources conservées des ateliers 09/10.

Références Grafana : Log queries, Query examples, LogQL template functions et diagnostic des erreurs de pipeline.

Les scripts Python ont été vérifiés syntaxiquement et exécutés sur un échantillon du fichier access_log fourni et un CSV de test avec virgules/guillemets. Les comptes des contrôles synthétiques, l’intégrité des sources et la préparation des requêtes ont été contrôlés localement. Aucun parseur LogQL n’a été exécuté sur Loki et le fragment Alloy n’a pas été validé par le binaire Alloy pendant la génération. Valider les syntaxes, labels d’erreur et résultats sur la version du lab avant formation.
