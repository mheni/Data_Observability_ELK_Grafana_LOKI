# Défi 13 — Du journal OpenSSH au dashboard Grafana : Loki, LogQL et 25 panneaux

## 1. Contexte

Un serveur OpenSSH de laboratoire a enregistré des tentatives de connexion pendant plusieurs semaines. Vous disposez d’un extrait de 2 000 lignes du jeu Loghub, `OpenSSH_2k.log`. Votre mission est d’indexer ce journal dans Loki, puis de construire dans Grafana un dashboard de diagnostic composé de 25 panneaux.

Le défi comporte deux parties :

| Partie | Mission | Résultat attendu |
|---|---|---|
| Partie 1 | Indexer le journal dans Loki avec les scripts et commandes fournis | Un lot vérifié, avec les mêmes volumes dans Loki que dans le fichier |
| Partie 2 | Construire le dashboard de 25 panneaux | Un dashboard enregistré, rouvert et documenté |

La partie 1 est guidée pour que vous puissiez consacrer votre énergie à la partie 2. Ne modifiez pas les scripts pour que les chiffres paraissent corrects.

## 2. Règles de lecture

- Une ligne du journal n’est ni une session, ni une personne.
- Une adresse IP n’est pas un individu.
- Un message `Failed password` est un échec d’authentification reconnu ; les lignes PAM, les déconnexions et les résumés de répétition sont des signaux complémentaires.
- Le journal syslog ne contient pas l’année. Le temps Loki du défi est celui de la collecte ; l’heure écrite dans les lignes est un champ de contenu.
- Aucune géolocalisation n’est fournie. Ne pas déduire un pays d’un nom d’hôte.
- Une table, un top ou un panneau de logs affiche un extrait ; un total se lit dans une requête agrégée.
- Zéro est une valeur correcte quand les données n’en contiennent aucune. Ne pas fabriquer des succès, des utilisateurs ou des événements.

## 3. Prérequis

La VM de laboratoire doit disposer de :

- Ubuntu avec Python 3 ;
- Loki local sur `http://127.0.0.1:3100`, sans authentification ni tenant dédié ;
- Grafana accessible, avec une source Loki nommée `Loki-Formation` ;
- le binaire Alloy et le compte/groupe système `alloy` ;
- le port local `12348` libre.

Les scripts de ce défi ne réinstallent pas Loki ni Grafana et n’écrasent pas un ancien service Alloy. Pour un Loki distant, authentifié ou multi-tenant, le formateur adapte la configuration avant la séance.

## 4. Partie 1 — Indexer OpenSSH_2k.log dans Loki

### Étape 1 : ouvrir le dossier du défi

1. Extraire le ZIP dans un dossier de travail de la VM.
2. Ouvrir un terminal dans le dossier `participant`.
3. Exécuter :

```bash
pwd
ls preparer_openssh13.py installer_collecte_defi13.sh verifier_loki_defi13.py
python3 --version
```

Ne lancez pas les commandes depuis un dossier vide : les scripts utilisent des fichiers situés à côté d’eux.

### Étape 2 : placer le journal OpenSSH

Placer `OpenSSH_2k.log` dans le dossier courant. Le jeu Loghub OpenSSH provient d’un serveur de laboratoire observé pendant plus de 28 jours.

Si la VM a accès à Internet, tenter :

```bash
curl --fail-with-body -sS -L -o OpenSSH_2k.log \
  https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log
```

Si cette commande échoue, télécharger le fichier avec un navigateur depuis le dépôt Loghub, dossier `OpenSSH`, puis le copier dans le dossier courant. Ne pas utiliser un autre journal.

Contrôler :

```bash
ls -lh OpenSSH_2k.log
wc -l OpenSSH_2k.log
head -n 5 OpenSSH_2k.log
```

Le fichier attendu contient environ 2 000 lignes de type syslog avec `sshd[...]`.

### Étape 3 : préparer les copies brute et JSON

```bash
python3 preparer_openssh13.py \
  --source OpenSSH_2k.log \
  --output-dir preparation_defi13
```

Le script lit toutes les lignes non vides. Il écrit la copie brute, une ligne JSON par événement, un manifeste et un rapport de références. Il n’envoie rien à Loki et refuse un dossier de sortie existant.

Lire ensuite :

```bash
cat preparation_defi13/manifest.json
cat preparation_defi13/reference_source.json
wc -l preparation_defi13/openssh.log preparation_defi13/events.jsonl
```

Attendu : les deux fichiers contiennent le même nombre de lignes. Noter le lot affiché, `N_nonempty_lines`, `other_unclassified_lines` et les types d’événements.

### Étape 4 : démarrer la collecte vers Loki

Lire d’abord `config_defi13.alloy.in` sans le modifier : il décrit deux sources de fichiers, un flux brut `defi13_openssh_raw`, un flux JSON `defi13_openssh` et l’envoi vers Loki.

Puis exécuter une seule fois :

```bash
sudo bash installer_collecte_defi13.sh preparation_defi13
```

Le script vérifie Loki, le compte `alloy`, le port 12348 et les ressources existantes. Il copie les fichiers dans `/var/log/defi13-openssh`, génère la configuration, valide Alloy quand cette commande existe, puis démarre `alloy-defi13`.

Contrôler :

```bash
sudo systemctl status alloy-defi13 --no-pager
sudo journalctl -u alloy-defi13 -n 80 --no-pager
sudo -u alloy test -r /var/log/defi13-openssh/openssh.log
sudo -u alloy test -r /var/log/defi13-openssh/events.jsonl
```

Si une ressource existe déjà, arrêtez-vous : ne supprimez pas un état de lecture pour contourner la protection. Demandez au formateur de décider du traitement.

### Étape 5 : vérifier la livraison dans Loki

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_loki_defi13.py \
  --manifest preparation_defi13/manifest.json \
  --output reference_loki_defi13.json
```

Le script attend jusqu’à cinq minutes. Il compare, côté Loki, le nombre de lignes brutes, le nombre de lignes JSON, la répartition des types d’événements et les comptes canoniques avec le rapport local. Il ne télécharge pas les logs.

Attendu : `observed.raw` et `observed.json` égaux à `expected_per_stream`. Le fichier `reference_loki_defi13.json` contient aussi `from_utc` et `to_utc`.

Limite à expliquer : une égalité de volumes et de répartitions ne prouve pas que chaque identifiant a été contrôlé en ligne.

### Étape 6 : première lecture dans Grafana Explore

1. Ouvrir Grafana et cliquer Explore / Explorer.
2. Choisir `Loki-Formation` comme source.
3. Cliquer Code plutôt que Builder.
4. Copier le sélecteur JSON imprimé à l’étape 3, qui contient votre lot réel. Il ressemble à `{job="defi13_openssh",format="json",lot="D13-..."}` ; utiliser la valeur affichée par votre propre exécution.
5. Choisir une période qui inclut la collecte, par exemple `Last 6 hours`.
6. Cliquer Run query, développer une ligne et repérer les champs `event_type`, `source_ip`, `user_name`, `is_auth_record`, `is_failure`, `hour` et `raw_line`.

Ne passez pas à la partie 2 tant que les deux volumes sont différents de N.

### Dépannage de la partie 1

| Problème | Action |
|---|---|
| Fichier source absent | Vérifier le dossier courant et le nom exact `OpenSSH_2k.log` |
| Dossier de préparation déjà présent | Lire son manifeste ; ne pas l’écraser pendant que le service lit ses copies |
| Alloy ou compte `alloy` absent | Arrêter : l’infrastructure doit être préparée avant le défi |
| Port 12348 occupé | Identifier le service avec `ss`, sans l’arrêter au hasard |
| Aucun log dans Explore | Vérifier le lot, la période et le journal Alloy |
| Volumes inférieurs à N | Attendre, relancer le vérificateur avec un autre nom de sortie |
| Volumes supérieurs à N | Chercher une double collecte ; ne pas additionner deux lots |
| Beaucoup de lignes `other` | Lire `first_unclassified_examples` ; ne pas modifier le journal |

## 5. Dictionnaire des données

Chaque événement JSON conserve la ligne source et ajoute des champs de lecture.

| Champ | Contenu |
|---|---|
| `raw_line` | Ligne OpenSSH d’origine |
| `source_line` / `record_id` | Position dans le fichier / identifiant du lot |
| `syslog_time`, `date_key`, `hour` | Heure et date écrites dans le journal, sans année ; `hour` est un texte sur deux chiffres |
| `event_type` | Catégorie calculée par le script |
| `is_auth_record` | 1 pour un `Failed password` ou `Accepted password/publickey` reconnu, sinon 0 |
| `is_failure`, `is_success` | 1 pour un échec ou un succès canonique, sinon 0 |
| `auth_outcome` | `failure` ou `success` quand l’événement est canonique |
| `user_name`, `user_valid` | Nom observé et indicateur d’utilisateur non signalé invalide par sshd |
| `source_ip`, `source_port` | IP et port source extraits lorsqu’ils sont présents |
| `source_host`, `source_host_tld` | Nom d’hôte distant et suffixe de domaine quand le message en contient un |
| `disconnect_code` | Code numérique des messages `Received disconnect` |
| `repeat_count`, `repeat_of` | Nombre annoncé dans « message repeated N times » et type du message répété |

Labels de flux : `job="defi13_openssh"` avec `format="json"` pour les événements, `job="defi13_openssh_raw"` avec `format="raw"` pour les lignes d’origine, et un label `lot`. Les IP, utilisateurs et chemins ne sont pas des labels de stockage.

Types d’événements possibles : `auth_failure`, `auth_success`, `failed_none`, `invalid_user`, `invalid_user_request`, `pam_failure`, `pam_more_failures`, `pam_unknown_user`, `pam_max_retries`, `pam_session`, `reverse_mapping`, `address_mismatch`, `disconnect_received`, `connection_closed`, `too_many_failures`, `max_auth_exceeded`, `no_identification`, `protocol_error`, `message_repeat`, `other`.

## 6. Partie 2 — Construire le dashboard de 25 panneaux

### Cahier des charges général

1. Créer le dashboard `[D13] OpenSSH — diagnostic Loki`.
2. Créer les variables `loki_ds` (source Loki) et `lot` (valeur exacte du lot).
3. Chaque panneau doit avoir son identifiant et son titre, par exemple `P03 — Échecs canoniques`.
4. Les panneaux interrogent Loki ; seul P25 est un texte.
5. Utiliser des requêtes agrégées pour les totaux et des extraits plafonnés pour les tables et logs.
6. Garder un résultat vide ou nul visible quand les données n’en contiennent pas.
7. Enregistrer, quitter puis rouvrir le dashboard : les 25 panneaux doivent être présents.

### Panneaux demandés

| ID | Panneau | Type attendu | Question à traiter |
|---|---|---|---|
| P01 | Lignes indexées | Stat | Quel est le périmètre du lot ? |
| P02 | Enregistrements canoniques | Stat | Combien de résultats d’authentification sont reconnus ? |
| P03 | Échecs canoniques | Stat | Combien d’échecs sont reconnus ? |
| P04 | Succès canoniques | Stat | Y a-t-il des succès ? Zéro doit rester lisible |
| P05 | IP sources distinctes | Stat | Combien d’adresses différentes apparaissent ? |
| P06 | Part d’échec canonique | Stat en pourcentage | Quelle part des enregistrements canoniques est en échec ? |
| P07 | Lignes sans IP extraite | Stat en pourcentage | Quelle part du journal n’a pas d’IP ? |
| P08 | Alertes « POSSIBLE BREAK-IN » | Stat | Combien de messages DNS/adresse sont signalés par sshd ? |
| P09 | Collecte dans le temps | Time series | Comment le lot est-il arrivé dans Loki ? |
| P10 | Répartition par type d’événement | Donut | Quels types dominent ? |
| P11 | Messages par heure syslog | Bar chart | Comment les lignes se répartissent-elles selon l’heure écrite ? |
| P12 | Échecs et succès par heure syslog | Bar chart empilé | Comment comparer les deux issues par heure ? |
| P13 | Top 10 IP — échecs canoniques | Bar gauge | Quelles IP contribuent le plus aux échecs ? |
| P14 | Top 10 utilisateurs — échecs canoniques | Bar gauge | Quels noms sont les plus visés ? |
| P15 | Échecs : utilisateur valide ou invalide | Donut | Les échecs portent-ils sur des utilisateurs signalés invalides ? |
| P16 | Codes de déconnexion reçus | Bar gauge | Quels codes numériques de déconnexion apparaissent ? |
| P17 | Analyse par IP | Table | Quel est le volume, le nombre d’échecs et la part d’échec par IP ? |
| P18 | Analyse par utilisateur | Table | Même analyse par nom d’utilisateur |
| P19 | Ports sources des enregistrements canoniques | Bar gauge par plages | Comment se répartissent les ports côté client ? |
| P20 | Suffixes des noms d’hôte distants | Bar gauge | Quels suffixes DNS apparaissent, sans parler de pays ? |
| P21 | Répétitions résumées par sshd | Stat | Quelle somme annoncent les messages « message repeated N times » ? |
| P22 | Détail des échecs canoniques | Logs | Quelles lignes sources prouvent les échecs ? |
| P23 | Lignes non classées | Logs | Que n’a pas reconnu le classeur ? |
| P24 | Détail des alertes « POSSIBLE BREAK-IN » | Logs | Quelles lignes ont déclenché P08 ? |
| P25 | Contrat de lecture | Text | Quelles sont les sources, définitions et limites ? |

### Aides sans solution complète

- Les requêtes de comptage utilisent des agrégations sur la période du dashboard ; une requête de lignes sert à lire des preuves.
- Le mode **Instant** convient aux valeurs de période ; **Range** convient aux séries temporelles et aux extraits de logs.
- LogQL peut extraire les champs JSON à la requête avec `| json`. Après un parser, le filtre `__error__=""` permet de contrôler les erreurs.
- Pour les tableaux et graphiques par heure, Grafana peut extraire les champs d’une ligne JSON et regrouper ensuite avec les transformations **Extract fields** et **Group by**.
- Une requête qui renvoie une série vide ne produit pas toujours un zéro : décidez explicitement comment afficher l’absence de données.
- Pour les listes bornées, ne cherchez pas à afficher toutes les IP à l’écran.

## 7. Investigation finale

À partir du dashboard, rédiger une note de quatre lignes sur une IP fortement présente dans les échecs :

1. fait observé ;
2. périmètre et limites ;
3. hypothèse prudente ;
4. preuve ou source qui manquerait pour conclure.

Cette note ne doit contenir ni nom de personne, ni pays déduit d’un nom d’hôte, ni affirmation de compromission sans preuve supplémentaire.

## 8. Livrables

- Résultat de l’étape 5 : `reference_loki_defi13.json`.
- Rapport local `reference_source.json` avec N, A, F, S, B et R relevés.
- Dashboard enregistré, rouvert et capturé avec les 25 panneaux.
- Tableau de validation des panneaux complété.
- Note d’investigation de quatre lignes.
- Liste des écarts rencontrés et de la façon dont ils ont été diagnostiqués.

## 9. Barème indicatif

| Domaine | Points |
|---|---:|
| Partie 1 : préparation, collecte et vérification | 4 |
| Variables, lot et période | 2 |
| Huit panneaux Stat, ratios et zéro lisible | 4 |
| Répartitions, tops, tables et transformations | 5 |
| Logs, texte de contexte et limites | 3 |
| Investigation prudente et dashboard rouvert | 2 |
| Total | 20 |

Un panneau sans question claire, sans unité cohérente ou avec une valeur inventée ne reçoit pas tous ses points.
