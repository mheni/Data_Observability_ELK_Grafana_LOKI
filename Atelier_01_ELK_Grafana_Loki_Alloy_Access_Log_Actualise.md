# Atelier 01 — Installation simple d’ELK, Grafana, Loki et Alloy

> Ubuntu 24.04 LTS — installation native.
> Parcours principal : HTTP local, sans certificat ni authentification applicative.
> Variantes de sécurité séparées en fin de document. 

## 1. Objectif et fichiers fournis

```text
                        ┌── Logstash ──► Elasticsearch ──► Kibana
access_log actualisé ────┤
                        └── Alloy ─────► Loki ───────────► Grafana
```

Le paquet de l’atelier contient :

- le présent support ;
- `access_log_actualise` : les 102 972 lignes du fichier d’origine, avec dates remplacées ;
- `access_log_formation` : 1 000 lignes pour le premier test, actualisées séparément sur toute la fenêtre ;

## 2. Prérequis et sécurité du laboratoire

VM Ubuntu neuve dédiée, sudo et Internet. Proposition pédagogique pour les six services : 4 vCPU, 16 Go de RAM et 30 Go libres, à valider sur votre infrastructure.

> Cette configuration sans contrôle d’accès applicatif est réservée à une VM personnelle temporaire, sans utilisateurs locaux non fiables. Les services écoutent sur 127.0.0.1. Ne pas exposer leurs ports publiquement ni remplacer localhost par 0.0.0.0. L’accès distant passe par SSH, qui conserve sa propre authentification.

Les remplacements de configuration supposent une installation neuve, pas une migration de services existants. Les commandes curl sont volontairement simples ; lire les messages d’erreur et ajouter `-i` si vous voulez voir le statut HTTP.

Toutes les commandes s’exécutent dans la VM sauf le transfert de fichiers, le tunnel et le navigateur sur votre poste.

### Préparer le dossier

Copier les fichiers du paquet dans `~/tp01` sur la VM, puis :

```bash
mkdir -p ~/tp01
cd ~/tp01
ls
```

Ne pas commencer la collecte en utilisant un ancien fichier déjà ingéré avec les mêmes positions. La procédure de reprise d’un atelier existant est donnée en partie H.

---

# A — Installer et tester Elasticsearch

## A1 — Préparer Ubuntu et vm.max_map_count

```bash
sudo apt update
sudo apt install -y curl wget gnupg ca-certificates python3 unzip

if [ "$(sysctl -n vm.max_map_count)" -lt 1048576 ]; then
  echo 'vm.max_map_count=1048576' | sudo tee /etc/sysctl.d/99-elasticsearch.conf
  sudo sysctl --system
fi
sysctl vm.max_map_count
```

Ce paramètre limite le nombre de zones mémoire mappées par processus, pas la RAM réservée. Nous visons au moins 1048576, sans abaisser une valeur déjà supérieure. Le fichier sysctl rend le réglage persistant.

## A2 — Ajouter le dépôt Elastic

```bash
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch \
  | sudo gpg --dearmor --yes -o /usr/share/keyrings/elasticsearch-keyring.gpg
sudo chmod 644 /usr/share/keyrings/elasticsearch-keyring.gpg

echo 'deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main' \
  | sudo tee /etc/apt/sources.list.d/elastic-9.x.list
sudo apt update
```

Le même dépôt fournit Elasticsearch, Kibana et Logstash. La clé vérifie les paquets ; signed-by l’associe au dépôt. Ne pas désactiver la validation APT et éviter les dépôts en double.

## A3 — Installer Elasticsearch

```bash
sudo apt install -y elasticsearch
/usr/share/elasticsearch/bin/elasticsearch --version
export STACK_VERSION=$(dpkg-query -W -f='${Version}' elasticsearch)
echo "$STACK_VERSION"
```

La JVM est incluse. Conserver la version exacte pour Kibana et Logstash.

| Élément | Chemin |
|---|---|
| Configuration | /etc/elasticsearch/elasticsearch.yml |
| Données | /var/lib/elasticsearch |
| Journaux | /var/log/elasticsearch |

## A4 — Configurer un nœud de formation

```bash
sudo cp -n /etc/elasticsearch/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml.avant-tp01
sudo tee /etc/elasticsearch/elasticsearch.yml > /dev/null <<'YAML'
cluster.name: formation-elk
node.name: es-lab-01
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 127.0.0.1
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
xpack.security.autoconfiguration.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
YAML
```

single-node évite la découverte d’autres nœuds ; 127.0.0.1 limite l’écoute ; les quatre dernières options désactivent explicitement la sécurité de ce lab.

Une VM déjà sécurisée peut contenir un ancien keystore : repartir du snapshot prévu plutôt qu’en supprimer les secrets au hasard.

## A5 — Démarrer et activer

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now elasticsearch
sudo systemctl status elasticsearch --no-pager
curl 'http://localhost:9200/?pretty'
```

Attendre le démarrage avant le test curl. enable --now démarre le service et l’active au démarrage de la VM.

Résultat attendu : nœud es-lab-01 et cluster formation-elk dans la réponse JSON.

## A6 — Option sécurité : comprendre les deux formes de requêtes

Ne pas modifier le lab pendant le parcours principal.

Sans sécurité, forme utilisée dans la suite :

```bash
curl 'http://localhost:9200/_cluster/health?pretty'
```

Après activation réelle de HTTPS et de l’authentification :

```bash
curl --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  'https://localhost:9200/_cluster/health?pretty'
```

Ces formes correspondent à deux configurations serveur différentes. L’auto-configuration sécurisée standard a été volontairement désactivée en A4. Remettre une option à true après le premier démarrage ne garantit pas la création automatique des certificats. Voir G1 pour une activation explicite.

## A7 — Vérifier le cluster

```bash
curl 'http://localhost:9200/_cluster/health?pretty'
curl 'http://localhost:9200/_cat/nodes?v'
curl 'http://localhost:9200/_cat/indices?v'
```

Un nœud est attendu. Un index demandant des répliques peut rendre le mono-nœud yellow ; le test ci-dessous utilise zéro réplique.

## A8 — Créer un index et rechercher

```bash
curl -X PUT 'http://localhost:9200/films' \
  -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"properties":{
      "titre":{"type":"text"},"annee":{"type":"integer"},"genre":{"type":"keyword"}
    }}
  }'

curl -X PUT 'http://localhost:9200/films/_doc/1?refresh=wait_for' \
  -H 'Content-Type: application/json' \
  -d '{"titre":"La recherche distribuée","annee":2026,"genre":"formation"}'

curl 'http://localhost:9200/films/_mapping?pretty'
curl 'http://localhost:9200/films/_doc/1?pretty'

curl -X POST 'http://localhost:9200/films/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"titre":"recherche"}}}'
```

text recherche des mots ; keyword sert aux valeurs exactes ; integer stocke un nombre entier. refresh=wait_for attend la visibilité par la recherche. Le document 1 doit être retrouvé.

Si films existe, inspecter le mapping au lieu de supprimer automatiquement l’index.

---

# B — Installer Kibana

## B1 — Installer la même version

```bash
export STACK_VERSION=$(dpkg-query -W -f='${Version}' elasticsearch)
sudo apt install -y kibana="$STACK_VERSION"
```

Faire préparer un jeu de versions commun si cette version n’est plus disponible.

## B2 — Configurer kibana.yml

```bash
sudo cp -n /etc/kibana/kibana.yml /etc/kibana/kibana.yml.avant-tp01
sudo tee /etc/kibana/kibana.yml > /dev/null <<'YAML'
server.name: kibana-formation
server.host: "127.0.0.1"
server.port: 5601
elasticsearch.hosts: ["http://127.0.0.1:9200"]
xpack.security.enabled: false
YAML
sudo systemctl enable --now kibana
```

Kibana utilise HTTP local sans enrôlement ni certificat dans ce parcours.

## B3 — Ouvrir le navigateur

Ouvrir `http://localhost:5601` après initialisation. Pour une VM distante, sur le poste :

```bash
ssh -N \
  -L 5601:127.0.0.1:5601 \
  -L 3000:127.0.0.1:3000 \
  utilisateur@ADRESSE_VM
```

Conserver le tunnel ouvert. Dans Dev Tools → Console :

```http
GET _cluster/health
GET films/_search
```

---

# C — Installer Logstash et préparer access_log

## C1 — Installer et préparer les droits

```bash
export STACK_VERSION=$(dpkg-query -W -f='${Version}' elasticsearch)
sudo apt install -y logstash="$STACK_VERSION"
sudo groupadd -f formation-logs
sudo usermod -aG formation-logs logstash
sudo install -d -m 750 -o root -g formation-logs /var/log/formation
```

Le JDK Logstash est inclus. Le groupe donnera la lecture du fichier aux deux collecteurs, chacun avec son propre état de lecture.

## C2 — Actualiser les dates juste avant l’ingestion

Les dates des fichiers distribués correspondent à leur génération. Même récentes aujourd’hui, elles vieilliront. Exécuter cette commande le jour de chaque session, juste avant d’activer les collecteurs :

```bash
cd ~/tp01
python3 actualiser_access_log.py access_log_actualise access_log_session \
  --limit 1000 --minutes 10

sudo install -m 640 -o root -g formation-logs \
  access_log_session /var/log/formation/access_log
sudo -u logstash test -r /var/log/formation/access_log
wc -l /var/log/formation/access_log
head -n 1 /var/log/formation/access_log
```

Si vous n’avez que l’échantillon, remplacer access_log_actualise par access_log_formation. Le script sait aussi traiter le fichier original access_log.

Le script refuse d’écraser une destination existante. Choisir un nouveau nom de session plutôt que remplacer un fichier déjà collecté. Le parent du fichier de sortie doit exister.

### Ce que fait le script

- Il conserve les octets des lignes sauf la première date Apache entre crochets.
- Il conserve l’ordre et les éventuelles lignes atypiques.
- Il répartit les timestamps de l’échantillon sur les dix minutes précédant l’heure courante moins trente secondes.
- Les mois sont écrits en anglais et les heures en UTC +0000, quelle que soit la langue d’Ubuntu.
- Les intervalles historiques sont remplacés : ce corpus est une simulation, pas un journal d’audit historique.
- Il vérifie la présence du timestamp avant de publier la sortie et ne modifie pas la source.

Si plusieurs lignes ont la même seconde, c’est normal : le format Apache utilisé n’a pas de sous-secondes.

Pour préparer le corpus complet sur une nouvelle sortie, omettre --limit. Ne pas commencer par les 102 972 lignes pour un premier test de configuration.

## C3 — Créer l’index avec mapping

```bash
curl -X PUT 'http://localhost:9200/atelier01-access' \
  -H 'Content-Type: application/json' \
  -d '{
    "settings":{"number_of_shards":1,"number_of_replicas":0},
    "mappings":{"properties":{
      "@timestamp":{"type":"date"},
      "message":{"type":"text"},
      "service":{"type":"keyword"},
      "clientip":{"type":"keyword"},
      "verb":{"type":"keyword"},
      "request":{"type":"keyword"},
      "response":{"type":"integer"},
      "bytes":{"type":"long"},
      "apache_timestamp":{"type":"keyword"},
      "tags":{"type":"keyword"}
    }}
  }'
```

La date source reste du texte dans apache_timestamp pour la lecture humaine. Sa version normalisée sera dans @timestamp.

## C4 — Configurer le pipeline Logstash

```bash
sudo tee /etc/logstash/conf.d/atelier01-access.conf > /dev/null <<'CONF'
input {
  file {
    path => "/var/log/formation/access_log"
    start_position => "beginning"
    sincedb_path => "/var/lib/logstash/atelier01-access.sincedb"
  }
}
filter {
  grok {
    ecs_compatibility => "disabled"
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
  mutate {
    add_field => { "service" => "web-formation" }
    rename => { "timestamp" => "apache_timestamp" }
    convert => { "response" => "integer" "bytes" => "integer" }
  }
  if [apache_timestamp] {
    date {
      match => ["apache_timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
      locale => "en"
      target => "@timestamp"
    }
  }
}
output {
  elasticsearch {
    hosts => ["http://127.0.0.1:9200"]
    index => "atelier01-access"
    data_stream => false
    ilm_enabled => false
    manage_template => false
  }
}
CONF
```

### Explication de logstash.conf

| Bloc / paramètre | Explication |
|---|---|
| input / file | Lit le fichier indiqué par path |
| start_position | Première lecture depuis le début |
| sincedb_path | Position persistante de lecture, pas un état partagé avec Alloy |
| grok | Extrait les champs selon le format Apache Combined |
| ecs_compatibility disabled | Utilise les noms simples clientip, verb, response pour ce TP |
| mutate / rename | Garde la date source dans apache_timestamp |
| convert | Transforme les champs numériques extraits |
| date | Convertit la date Apache en horodatage Elasticsearch |
| locale en | Interprète les noms anglais de mois : Jan, Nov… |
| target @timestamp | Utilise le temps de l’événement, pas seulement l’heure de collecte |
| output | Envoie vers l’index HTTP local précréé |
| ilm_enabled / manage_template | Évite des mécanismes automatiques inutiles au test |

Le message original est conservé. Un échec Grok produit normalement le tag _grokparsefailure ; un échec du filtre date produit _dateparsefailure. Une ligne non parsée peut garder l’heure de collecte : elle doit être diagnostiquée et n’est pas une preuve d’alignement des deux timestamps.

### Vérifier un seul pipeline de démonstration

Dans /etc/logstash/pipelines.yml :

```yaml
- pipeline.id: main
  path.config: "/etc/logstash/conf.d/*.conf"
```

Retirer du glob actif uniquement les anciens .conf de ce TP après sauvegarde. Plusieurs .conf peuvent être fusionnés et provoquer des doublons.

## C5 — Tester et démarrer

```bash
sudo systemctl stop logstash
sudo install -d -m 750 -o logstash -g logstash /var/lib/logstash/config-test
sudo -u logstash /usr/share/logstash/bin/logstash \
  --path.settings /etc/logstash \
  --path.data /var/lib/logstash/config-test \
  --config.test_and_exit -f /etc/logstash/conf.d/atelier01-access.conf
sudo systemctl enable --now logstash
```

Attendre collecte et rafraîchissement. Le démarrage applique aussi les nouveaux groupes du service.

## C6 — Vérifier l’indexation et les dates

```bash
curl 'http://localhost:9200/atelier01-access/_count?pretty'

curl -X POST 'http://localhost:9200/atelier01-access/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d '{"size":3,"sort":[{"@timestamp":"desc"}],"query":{"match_all":{}}}'

curl -X POST 'http://localhost:9200/atelier01-access/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"term":{"response":200}}}'
```

Sur un index neuf : 1 000 documents attendus après rattrapage. Vérifier séparément les échecs :

```bash
curl -X POST 'http://localhost:9200/atelier01-access/_count?pretty' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"terms":{"tags":["_grokparsefailure","_dateparsefailure"]}}}'
```

Examiner les lignes concernées si ce compteur est non nul ; le script d’actualisation ne corrige pas les formats atypiques du contenu.

Dans Kibana : créer la Data View atelier01-access, choisir @timestamp, ouvrir Discover et les quinze dernières minutes. Afficher message, request, response, apache_timestamp et @timestamp.

KQL :

```kql
service : "web-formation" and response : 200
```

La date Apache et @timestamp doivent représenter le même instant pour une ligne correctement parsée. L’affichage Kibana peut utiliser le fuseau du navigateur ; les suffixes UTC/offset expliquent alors l’écart visuel.

---

# D — Installer Grafana et Loki

## D1 — Dépôt et installation des trois paquets Grafana

```bash
sudo install -d -m 755 /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/grafana.asc https://apt.grafana.com/gpg-full.key
sudo chmod 644 /etc/apt/keyrings/grafana.asc

echo 'deb [signed-by=/etc/apt/keyrings/grafana.asc] https://apt.grafana.com stable main' \
  | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana loki alloy
```

Alloy utilise le même dépôt. Si un paquet manque pour l’architecture retenue, faire préparer une variante officielle, sans téléchargement non vérifié.

## D2 — Configuration locale Loki

```bash
if systemctl cat loki.service >/dev/null 2>&1; then
  sudo systemctl disable --now loki.service
fi
if ! id loki >/dev/null 2>&1; then
  sudo useradd --system --home /var/lib/loki --shell /usr/sbin/nologin loki
fi
sudo install -d -m 750 -o root -g loki /etc/loki-formation
sudo install -d -m 750 -o loki -g loki /var/lib/loki-formation

sudo tee /etc/loki-formation/loki.yml > /dev/null <<'YAML'
auth_enabled: false
server:
  http_listen_address: 127.0.0.1
  http_listen_port: 3100
  grpc_listen_address: 127.0.0.1
common:
  instance_addr: 127.0.0.1
  path_prefix: /var/lib/loki-formation
  storage:
    filesystem:
      chunks_directory: /var/lib/loki-formation/chunks
      rules_directory: /var/lib/loki-formation/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
YAML
sudo chown root:loki /etc/loki-formation/loki.yml
sudo chmod 640 /etc/loki-formation/loki.yml
```

La date from configure le schéma, pas les dates des logs. Stockage filesystem et une instance unique sont des choix de lab.

## D3 — Créer le service explicite

Vérifier que la commande affiche un chemin avant de poursuivre :

```bash
LOKI_BIN=$(command -v loki)
echo "$LOKI_BIN"
```

```bash
sudo tee /etc/systemd/system/loki-formation.service > /dev/null <<EOF
[Unit]
Description=Loki local de formation
After=network-online.target
Wants=network-online.target
[Service]
User=loki
Group=loki
WorkingDirectory=/var/lib/loki-formation
ExecStart=$LOKI_BIN -config.file=/etc/loki-formation/loki.yml
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo -u loki "$LOKI_BIN" -config.file=/etc/loki-formation/loki.yml -verify-config=true
sudo systemctl daemon-reload
sudo systemctl enable --now loki-formation
curl 'http://127.0.0.1:3100/ready'
```

Attendre ready. L’unité à diagnostiquer est loki-formation ; l’unité du paquet a été désactivée pour éviter un conflit.

## D4 — Configurer Grafana pour le lab sans login

> Administration anonyme de l’organisation : droits élevés pour quiconque atteint l’interface. VM personnelle et temporaire uniquement. Utiliser G4 si ce mode n’est pas autorisé.

```bash
sudo cp -n /etc/grafana/grafana.ini /etc/grafana/grafana.ini.avant-tp01
sudo tee /etc/grafana/grafana.ini > /dev/null <<'INI'
[server]
http_addr = 127.0.0.1
http_port = 3000
protocol = http
[auth]
disable_login_form = true
[auth.anonymous]
enabled = true
org_name = Main Org.
org_role = Admin
INI
sudo systemctl enable --now grafana-server
sudo systemctl restart grafana-server
curl 'http://127.0.0.1:3000/api/health'
```

Ouvrir http://localhost:3000 via le tunnel si nécessaire. Main Org. est l’organisation d’une installation neuve. Le rôle Admin est celui de l’organisation, pas une administration globale de l’instance.

## D5 — Premier test Loki puis connexion Grafana

```bash
TS=$(python3 -c 'import time; print(time.time_ns())')
curl -i -X POST 'http://127.0.0.1:3100/loki/api/v1/push' \
  -H 'Content-Type: application/json' \
  --data-raw "{\"streams\":[{\"stream\":{\"job\":\"atelier01-test\"},\"values\":[[\"$TS\",\"Premier test Loki\"]]}]}"
```

Résultat attendu : HTTP 204, sans corps. Ce job distinct ne pollue pas le comptage access_log.

Dans Grafana : Connections → Data sources → Add data source → Loki. Nom : Loki-Formation. URL : http://127.0.0.1:3100. Ni certificat ni authentification. Save & test.

Explore → Loki-Formation → quinze dernières minutes :

```logql
{job="atelier01-test"}
```

L’URL datasource est la racine Loki, pas /loki/api/v1/push. Si votre version/politique interdit l’ajout de sources en session anonyme, réactiver le login G4.

---

# E — Configurer Alloy et ingérer le même fichier

## E1 — Installation et droits

```bash
sudo apt install -y alloy
alloy --version
sudo usermod -aG formation-logs alloy
sudo -u alloy test -r /var/log/formation/access_log
```

Le paquet est normalement déjà installé en D1. Le test de lecture doit réussir.

## E2 — Source, extraction de date et sortie Loki


```bash
sudo systemctl stop alloy
sudo cp -n /etc/alloy/config.alloy /etc/alloy/config.alloy.avant-tp01

sudo tee /etc/alloy/config.alloy > /dev/null <<'ALLOY'
loki.source.file "access_log" {
  targets = [
    {
      __path__ = "/var/log/formation/access_log",
      job      = "atelier01-access",
      service  = "web-formation",
    },
  ]
  tail_from_end = false
  forward_to    = [loki.process.access_log.receiver]
}

loki.process "access_log" {
  stage.regex {
    expression = `^\S+ \S+ \S+ \[(?P<apache_time>[^\]]+)\] `
  }

  stage.timestamp {
    source            = "apache_time"
    format            = "02/Jan/2006:15:04:05 -0700"
    action_on_failure = "skip"
  }

  forward_to = [loki.write.local.receiver]
}

loki.write "local" {
  endpoint {
    url = "http://127.0.0.1:3100/loki/api/v1/push"
  }
}
ALLOY

sudo alloy fmt /etc/alloy/config.alloy > /dev/null && echo "syntaxe OK"

sudo find /var/lib/alloy -name 'positions.yml' -delete

sudo chmod o+r /var/log/formation/access_log

sudo systemctl start alloy
sudo systemctl status alloy --no-pager
sudo journalctl -u alloy -n 30 --no-pager

curl -s -G http://127.0.0.1:3100/loki/api/v1/query \
  --data-urlencode 'query=count_over_time({job="atelier01-access"}[7d])'
curl -s -X POST http://127.0.0.1:3100/flush
```

dans /etc/loki/local-config.yaml

```bash
ingester:
  chunk_idle_period: 1m
  max_chunk_age: 5m

querier:
  query_ingesters_within: 0
  ```

### Explication

| Élément | Rôle |
|---|---|
| loki.source.file | Suit le fichier partagé |
| __path__ | Chemin à lire |
| job / service | Labels de faible cardinalité pour LogQL |
| tail_from_end false | Première lecture depuis le début sans position connue |
| forward_to | Relie la source au traitement puis à la sortie |
| stage.regex | Extrait la date entre crochets dans apache_time |
| stage.timestamp | Remplace l’horodatage de lecture par celui de la ligne |
| format | Référence de format Go ; ce n’est pas une date à recopier dans le fichier |
| action_on_failure skip | Garde l’horodatage initial si l’extraction/conversion échoue ; ne supprime pas la ligne |
| loki.write | Publie à l’API Loki locale |

Pas d’IP, de chemin URL ou de timestamp comme label de flux. Le message reste intact. Si un timestamp ne peut pas être extrait, le fallback n’est pas une preuve de parsing réussi : examiner les entrées atypiques.

Le format Go d’Alloy est différent du format date de Logstash, mais les deux interprètent la même date Apache.

## E3 — Valider et démarrer

```bash
sudo -u alloy alloy validate /etc/alloy/config.alloy
sudo systemctl enable --now alloy
sudo systemctl status alloy --no-pager
sudo journalctl -u alloy -n 50 --no-pager
```

Le démarrage renouvelle les groupes du service. Ses positions sont persistantes : un redémarrage ne force pas une réingestion. Ne pas supprimer l’état de collecte.

## E4 — Rechercher les lignes et contrôler les temps

Dans Explore, choisir les quinze dernières minutes, puis actualiser :

```logql
{job="atelier01-access"}
```

Exemple de filtre :

```logql
{job="atelier01-access"} |= "/docs/triton/pages.html"
```

Exemple d’extraction à la requête :

```logql
{job="atelier01-access"}
| pattern `<client_ip> <_> <_> [<apache_time>] "<method> <url> <protocol>" <status> <bytes> <_>`
| __error__=""
| status="200"
```

Vérifier sur une ligne que l’heure affichée par Grafana correspond à celle du message, compte tenu du fuseau d’affichage.

Pour compter la fenêtre, en mode Instant :

```logql
sum(count_over_time({job="atelier01-access"}[30m]))
```

Dans le scénario neuf, 1 000 lignes sont attendues après collecte complète, avant l’ajout de test et tant que la fenêtre inclut tout le corpus. Cette mesure n’est pas un compteur permanent du fichier. Une limite d’affichage Explore ne prouve pas une ingestion incomplète.

Si vous consultez plus tard, élargir la période aux heures du fichier ou préparer une nouvelle session selon H. Ne pas modifier les limites d’ancienneté Loki pour dissimuler un fichier non actualisé.

---

# F — Tester la progression et valider

## F1 — Ajouter une ligne commune avec l’heure actuelle

```bash
MARKER="tp01-$(date +%s)"
APACHE_DATE=$(LC_ALL=C date -u '+%d/%b/%Y:%H:%M:%S +0000')
printf '127.0.0.1 - - [%s] "GET /%s HTTP/1.1" 200 123 "-" "Atelier01"\n' \
  "$APACHE_DATE" "$MARKER" | sudo tee -a /var/log/formation/access_log
echo "$MARKER"
```

Après collecte :

```bash
curl -X POST 'http://localhost:9200/atelier01-access/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d "{\"query\":{\"term\":{\"request\":\"/$MARKER\"}}}"
```

Dans Explore, remplacer la valeur réelle :

```logql
{job="atelier01-access"} |= "MARQUEUR_REEL"
```

Les deux chemins doivent contenir le même message et la même date d’événement pour cette ligne correctement parsée. Sur un scénario neuf avec un seul ajout, le fichier contient 1 001 lignes ; les compteurs peuvent varier après rejeux ou sortie de fenêtre.

## F2 — Vérifier les six services

```bash
sudo systemctl status elasticsearch kibana logstash grafana-server loki-formation alloy --no-pager
sudo ss -ltnp | grep -E ':(9200|9300|5601|3000|3100|9095|12345)\b'
```

Valider : API Elasticsearch, index films, Discover access_log, Loki ready, Alloy sans erreur de publication, Explore et ligne marqueur retrouvée dans les deux destinations. Toutes les écoutes applicatives doivent rester sur la boucle locale.

## F3 — Dépannage rapide

| Symptôme | Vérification |
|---|---|
| Les deux collectes vides | Fichier, groupe formation-logs, droits des dossiers |
| Documents visibles seulement en élargissant le temps | Dates du fichier ou session préparée trop tôt |
| Grok/date en échec | Tags _grokparsefailure et _dateparsefailure, message réel |
| Loki rejette l’ancienneté | Corpus non actualisé juste avant ingestion |
| Alloy permission refusée | Groupe et redémarrage après usermod |
| Relecture absente | Position connue ; ajouter une ligne ou suivre H |
| Comptage différent | Fenêtre, collecte en cours, rejeux, erreurs de parsing/publication |
| Kibana demande enrôlement | Configuration réellement chargée, hosts en HTTP pour ce lab |
| Port Loki occupé | Unité du paquet encore active en parallèle |

```bash
sudo journalctl -u elasticsearch -n 40 --no-pager
sudo journalctl -u kibana -n 40 --no-pager
sudo journalctl -u logstash -n 40 --no-pager
sudo journalctl -u alloy -n 40 --no-pager
sudo journalctl -u loki-formation -n 40 --no-pager
```

Ne pas supprimer les données, les positions ou appliquer chmod 777 pour masquer une erreur.

## F4 — Arrêter et reprendre(optionnel): laisser active pour le TP suivant

```bash
sudo systemctl stop alloy logstash kibana grafana-server loki-formation elasticsearch
```

Pour reprendre :

```bash
sudo systemctl start elasticsearch loki-formation
curl 'http://localhost:9200'
curl 'http://127.0.0.1:3100/ready'
# Une fois les destinations disponibles :
sudo systemctl start kibana grafana-server logstash alloy
```

Pour les anciens TP en HTTPS, adapter en HTTP seulement si vous restez dans ce mode sans sécurité : enlever --cacert et les identifiants. Les TP de rôles et clés API nécessitent une sécurité réellement activée.

---

# G — Sécurité optionnelle, hors parcours principal

## G1 — Elasticsearch : activer explicitement HTTPS après le TP

Une installation standard neuve peut auto-configurer la sécurité ; A4 la désactive ici. Pour convertir le lab, arrêter les clients et générer les certificats. Première création uniquement : ne pas écraser une CA existante.

```bash
sudo systemctl stop kibana logstash elasticsearch
sudo install -d -m 700 /root/tp01-tls
sudo /usr/share/elasticsearch/bin/elasticsearch-certutil ca \
  --silent --pem --out /root/tp01-tls/ca.zip
sudo unzip -q /root/tp01-tls/ca.zip -d /root/tp01-tls
sudo /usr/share/elasticsearch/bin/elasticsearch-certutil cert \
  --silent --pem --ca-cert /root/tp01-tls/ca/ca.crt \
  --ca-key /root/tp01-tls/ca/ca.key --name es-http \
  --dns localhost --ip 127.0.0.1 --out /root/tp01-tls/http.zip
sudo unzip -q /root/tp01-tls/http.zip -d /root/tp01-tls
sudo install -d -m 750 -o root -g elasticsearch /etc/elasticsearch/tp01-certs
sudo install -m 640 -o root -g elasticsearch /root/tp01-tls/es-http/es-http.crt /etc/elasticsearch/tp01-certs/http.crt
sudo install -m 640 -o root -g elasticsearch /root/tp01-tls/es-http/es-http.key /etc/elasticsearch/tp01-certs/http.key
sudo install -m 640 -o root -g elasticsearch /root/tp01-tls/ca/ca.crt /etc/elasticsearch/tp01-certs/http_ca.crt
```

Remplacer les options concernées dans elasticsearch.yml, sans doublons :

```yaml
xpack.security.enabled: true
xpack.security.autoconfiguration.enabled: false
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.certificate: tp01-certs/http.crt
xpack.security.http.ssl.key: tp01-certs/http.key
xpack.security.http.ssl.certificate_authorities: ["tp01-certs/http_ca.crt"]
xpack.security.transport.ssl.enabled: false
```

Conserver l’écoute locale et single-node. Cette variante protège l’API HTTP d’un nœud local, pas le transport d’un cluster de production multi-nœuds.

```bash
sudo systemctl start elasticsearch
# Attendre le demarrage :
sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic -i
install -d -m 700 "$HOME/.config/elastic-lab"
sudo cat /etc/elasticsearch/tp01-certs/http_ca.crt > "$HOME/.config/elastic-lab/http_ca.crt"
chmod 600 "$HOME/.config/elastic-lab/http_ca.crt"
export ES_CA="$HOME/.config/elastic-lab/http_ca.crt"
read -rsp 'Mot de passe elastic : ' ELASTIC_PASSWORD
printf '\n'
export ELASTIC_PASSWORD
```

Avec CA, réussite attendue :

```bash
curl --cacert "$ES_CA" -u "elastic:$ELASTIC_PASSWORD" \
  'https://localhost:9200/films/_search?pretty'
```

Sans CA explicite, erreur attendue si le système ne fait pas déjà confiance à cette CA :

```bash
curl -u "elastic:$ELASTIC_PASSWORD" 'https://localhost:9200/films/_search?pretty'
```

Ne pas utiliser -k. Ne distribuer aucune clé privée. Adapter Kibana et Logstash avant leur reprise ; les index restent présents.

## G2 — Kibana : connexion technique sécurisée

Copier la CA et définir le mot de passe technique :

```bash
sudo install -d -m 750 -o root -g kibana /etc/kibana/certs
sudo install -m 640 -o root -g kibana "$ES_CA" /etc/kibana/certs/http_ca.crt
sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana_system -i
```

Remplacer dans kibana.yml :

```yaml
elasticsearch.hosts: ["https://localhost:9200"]
elasticsearch.username: "kibana_system"
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/certs/http_ca.crt"]
xpack.security.enabled: true
```

```bash
sudo /usr/share/kibana/bin/kibana-keystore add elasticsearch.password
sudo systemctl restart kibana
```

Saisir le mot de passe kibana_system. Créer le keystore d’abord avec kibana-keystore create seulement s’il n’existe pas. Le compte technique n’est pas le compte de connexion navigateur.

Pour HTTPS côté navigateur, fournir d’abord les fichiers lisibles par Kibana puis ajouter server.ssl.enabled, server.ssl.certificate et server.ssl.key. Forme du test :

```bash
curl --cacert /CHEMIN/ca-kibana.crt -I 'https://localhost:5601'
```

Les chemins d’exemple de cette partie supposent des certificats réellement préparés ; sinon garder HTTP dans SSH.

## G3 — Logstash : sortie HTTPS et clé limitée

Faire préparer une clé API limitée à atelier01-access avec les droits d’écriture et monitor nécessaires. Copier la CA dans /etc/logstash/certs/http_ca.crt, lisible par le service. Stocker la forme id:api_key dans le keystore sous LS_API_KEY, pas dans le pipeline.

```bash
# Seulement si aucun keystore n'existe :
sudo /usr/share/logstash/bin/logstash-keystore --path.settings /etc/logstash create
sudo /usr/share/logstash/bin/logstash-keystore --path.settings /etc/logstash add LS_API_KEY
sudo chown root:logstash /etc/logstash/logstash.keystore
sudo chmod 640 /etc/logstash/logstash.keystore
```

Remplacer la sortie Elasticsearch par :

```ruby
elasticsearch {
  hosts => ["https://localhost:9200"]
  ssl_enabled => true
  ssl_certificate_authorities => ["/etc/logstash/certs/http_ca.crt"]
  api_key => "${LS_API_KEY}"
  index => "atelier01-access"
  data_stream => false
  ilm_enabled => false
  manage_template => false
}
```

Tester puis redémarrer ; la lecture et le parsing de date ne changent pas.

## G4 — Grafana : réactiver le login

Modifier les sections existantes de grafana.ini :

```ini
[auth]
disable_login_form = false
[auth.anonymous]
enabled = false
```

Redémarrer grafana-server. Sur une installation neuve, utiliser les identifiants initiaux prévus par le paquet, généralement admin / admin, puis changer immédiatement le mot de passe.

Pour HTTPS applicatif, installer les fichiers lisibles par grafana puis définir dans [server] protocol=https, cert_file et cert_key. Le test devient :

```bash
curl --cacert /CHEMIN/ca-grafana.crt 'https://localhost:3000/api/health'
```

## G5 — Loki : protection externe

Loki ne fournit pas de login utilisateur natif. auth_enabled true active les exigences multi-tenant, pas une authentification par mot de passe.

Pour un accès réseau, préparer un proxy HTTPS authentifiant devant Loki. Exemple d’appel avec URL et CA réellement configurées :

```bash
curl --cacert /CHEMIN/ca-proxy-loki.crt -u participant \
  'https://loki.exemple.test/ready'
```

La datasource Grafana doit alors utiliser l’URL, l’authentification et la CA du proxy. Le déploiement de ce proxy est distinct du TP simple.

## G6 — Alloy : sortie HTTPS optionnelle

La source et le parsing restent identiques. Avec un proxy Loki préparé, installer sa CA dans /etc/alloy/certs/loki-ca.crt et un mot de passe dans /etc/alloy/loki-password, fichiers root:alloy en 640 dans des dossiers 750. Ne pas versionner le secret.

Remplacer le writer local, en gardant son nom :

```alloy
local.file "loki_password" {
  filename = "/etc/alloy/loki-password"
  is_secret = true
}
loki.write "local" {
  endpoint {
    url = "https://loki.exemple.test/loki/api/v1/push"
    basic_auth {
      username = "participant"
      password = string.trim_space(local.file.loki_password.content)
    }
    tls_config {
      ca_file = "/etc/alloy/certs/loki-ca.crt"
    }
  }
}
```

Valider puis redémarrer. Garder l’interface de diagnostic Alloy locale ou passer par SSH ; ne pas exposer son port publiquement.

---

# H — Si vous avez déjà réalisé l’ancienne version du TP

## Ne pas écraser le fichier déjà suivi

Modifier les timestamps d’un fichier actif ne provoque pas automatiquement sa relecture. Cela peut aussi mélanger les données déjà collectées à l’heure d’ingestion et les nouvelles données à l’heure d’événement.

Pour une nouvelle session propre, sans supprimer les anciennes données :

1. Arrêter Logstash et Alloy.
2. Générer une sortie locale au nouveau nom avec le script, juste avant la reprise.
3. Installer cette sortie sous un nouveau chemin, par exemple /var/log/formation/access_log_session02.
4. Créer un nouvel index atelier01-access-session02 avec le même mapping.
5. Adapter dans Logstash : path, sincedb_path distinct et index de sortie.
6. Adapter dans Alloy : chemin, nom de composant source distinct et job atelier01-access-session02. Ajouter le traitement de timestamp si absent. Ne pas conserver en parallèle l’ancienne source du TP si vous voulez l’arrêter.
7. Valider les configurations et démarrer les collecteurs.
8. Utiliser la nouvelle Data View, le nouveau job et la bonne période dans les contrôles.

Exemple de préparation après arrêt des deux lecteurs :

```bash
cd ~/tp01
python3 actualiser_access_log.py access_log_actualise access_log_session02 --limit 1000
sudo install -m 640 -o root -g formation-logs \
  access_log_session02 /var/log/formation/access_log_session02
```

Ne pas supprimer globalement le sincedb ni le stockage Alloy pour forcer un rejeu. Une nouvelle source, une nouvelle destination de test et des contrôles explicites sont plus faciles à expliquer et à auditer.

---

