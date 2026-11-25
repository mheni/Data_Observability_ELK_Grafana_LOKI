# Atelier 13 bis — 60 requêtes Explore sur le corpus access complet

Révision du guide fourni : les recherches principales ne ciblent plus les cinq seeds ni le scénario. Les valeurs attendues sont calculées localement sur `access_log_actualise` : 102 972 lignes, SHA-256 `09693e55a8bcb1dedd3659c23833aa06a4ad2c8fb5f46b7fd2d9b93ee941c815`. Un fichier différent ou une collecte partielle donne d’autres comptes. [file:208]

## Avant la première recherche

1. Ne pas réimporter les logs déjà présents et ne pas supprimer les positions Alloy.
2. Mettre en place le vérificateur corrigé puis générer la référence et les deux supports personnalisés selon la section « Reprendre la séance en cours » de l’atelier révisé.
3. Ouvrir la version personnalisée de ce guide. `__NID__` doit y être remplacé par le normalization_id réel et `__DUREE__` par la durée correspondant à la référence. Aucun manifeste de scénario n’est nécessaire.
4. Dans Grafana, ouvrir Explore, sélectionner Loki-Formation puis Code.
5. Régler la période absolue sur `from_utc` et `to_utc` du contrôle de normalisation. Cette période est celle de collecte, pas automatiquement le 22 novembre écrit dans les logs.
6. Pour les logs, choisir Range et une limite 500 ou 2000 pour examiner un sous-ensemble. Pour les totaux, choisir Instant et les expressions count_over_time : elles ne sont pas plafonnées à 2000 lignes téléchargées. [web:186]
7. Garder la même période de référence pour comparer les résultats ; ne pas additionner les copies JSON, logfmt et brutes comme des événements distincts.

## Nouvelle progression

| Plage | Objectif |
|---|---|
| E01–E08 | Flux présents, filtres textuels et Apache brut |
| E09–E23 | Champs JSON du corpus, statuts, méthodes et tailles manquantes |
| E24–E33 | IP, chemins, texte source, date écrite et provenance |
| E34–E36 | Comparaison JSON/logfmt du même corpus |
| E37–E50 | Totaux, ratios et statistiques calculés côté Loki |
| E51–E60 | Temps de collecte, comparaisons bornées et distributions |

Les quatre contrôles et les films restent disponibles dans leur lot mais ne sont plus les données du dashboard principal. Les exercices de conversion fictive ne sont pas utilisés pour inventer une latence HTTP.

## E01 — Voir les lignes Apache brutes

Périmètre : Brut access ; période de collecte. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"}
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des lignes du fichier ; l’affichage est plafonné, il ne prouve pas le total..

Aucun parser ne transforme encore la ligne. Si des sondes ont déjà été ajoutées, ce flux peut aussi les contenir.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E02 — Voir le lot JSON sans le scénario

Périmètre : Tout le lot JSON normalisé. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 102 981 lignes préparées au total si le lot contient 102 972 access + 5 films + 4 contrôles ; affichage limité..

Ce premier filtre voit toutes les sources du lot normalisé. Les requêtes suivantes isolent source_dataset=access.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E03 — Voir le lot logfmt

Périmètre : Tout le lot logfmt normalisé. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Même lot sous un autre format, pas de nouveaux événements métier..

Le marqueur sert à isoler une normalisation et non un run de simulation.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E04 — Recherche textuelle wp-login.php

Périmètre : Brut access. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "/wp-login.php"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des lignes présentes ; le texte peut apparaître dans plusieurs parties de la ligne..

Une recherche textuelle n’est pas encore une égalité sur le chemin de requête.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E05 — Recherche textuelle POST

Périmètre : Brut access. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "POST"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des lignes contenant POST, pas nécessairement la population exacte des méthodes POST..

Comparer ensuite avec E16, fondée sur le champ extrait.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E06 — Regex textuelle GET ou HEAD

Périmètre : Brut access. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"} |~ `"(GET|HEAD) `
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des requêtes contenant ce motif..

Le filtre de ligne regex recherche du texte ; il ne garantit pas une validation HTTP complète.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E07 — Extraire le début Apache avec regexp

Périmètre : Brut access. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"}
| regexp `^(?P<v_ip>\S+) \S+ \S+ \[[^\]]+\] "(?P<v_request>(?:\\.|[^"\\])*)" (?P<v_status>[0-9]{3}) (?P<v_size>[0-9]+|-)`
| v_status!=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Statut, IP, requête et taille extraits sur le fichier joint..

La taille peut valoir le tiret. Ne pas la convertir en zéro. Les captures sont des labels de résultat, pas des labels ajoutés à l’index.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E08 — Lire avec pattern sans supposer une requête standard

Périmètre : Brut access. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis_raw",dataset="access"}
| pattern `<v_ip> <_> <_> [<v_date>] "<v_request>" <v_status> <v_size> <_>`
| v_status!=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des lignes reconnues ; inspecter les cas atypiques plutôt que prétendre valider tout le format..

Capturer la requête entière évite de supposer que chaque ligne possède déjà méthode, chemin et protocole séparables.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E09 — Isoler les access logs JSON

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 102972.

Le double filtre normalization_id exact et source_dataset=access écarte les films, contrôles et événements de simulation.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E10 — Réponses 200

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status="200"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 91074.

Un code n’est pas un mot libre dans le message.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E11 — Réponses 404

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status="404"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 2298.

Le fichier contient bien des 404 ; ne pas chercher les 404 du scénario.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E12 — Réponses 500

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status="500"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 248.

Le corpus contient des 500 ; la simulation utilisait des 503. Ne pas conserver ce code synthétique comme seul filtre.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E13 — Famille 4xx

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status >= 400
| v_status < 500
| __error__=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 2670.

Deux bornes définissent la famille de codes.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E14 — Famille 5xx

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status >= 500
| v_status < 600
| __error__=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 248.

Dans ce fichier, les 5xx sont les 248 réponses 500.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E15 — Méthode GET

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method="GET"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 61858.

Le filtre s’applique au champ reconnu par le normaliseur ; les requêtes atypiques sans méthode extraite restent hors de ce sous-ensemble.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E16 — Méthode POST

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method="POST"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 36988.

Le filtre s’applique au champ reconnu par le normaliseur ; les requêtes atypiques sans méthode extraite restent hors de ce sous-ensemble.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E17 — Méthode HEAD

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method="HEAD"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 635.

Le filtre s’applique au champ reconnu par le normaliseur ; les requêtes atypiques sans méthode extraite restent hors de ce sous-ensemble.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E18 — Méthode OPTIONS

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method="OPTIONS"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 3221.

Le filtre s’applique au champ reconnu par le normaliseur ; les requêtes atypiques sans méthode extraite restent hors de ce sous-ensemble.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E19 — Méthode non extraite

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 267.

Un début Apache reconnu ne garantit pas une requête HTTP découpable en trois parties ; ne pas perdre silencieusement ces lignes.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E20 — Tailles connues

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 67987.

Le normaliseur omet bytes quand la source vaut « - ».

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E21 — Tailles absentes

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 34985.

Absence de taille n’est ni zéro octet ni une erreur JSON.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E22 — Tailles au moins 100000 octets

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 100000
| __error__=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 1134.

La comparaison est numérique et porte sur des octets, pas sur une durée.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E23 — Tailles au moins 1000000 octets

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 13.

La comparaison est numérique et porte sur des octets, pas sur une durée.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E24 — Adresse 54.210.20.202

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_ip="client_ip"
| __error__=""
| n_id="__NID__"
| src="access"
| v_ip="54.210.20.202"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 34469.

Une IP n’est pas une personne ; ::1 est une adresse de boucle locale, pas un pays à inventer.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E25 — Adresse ::1

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_ip="client_ip"
| __error__=""
| n_id="__NID__"
| src="access"
| v_ip="::1"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 3219.

Une IP n’est pas une personne ; ::1 est une adresse de boucle locale, pas un pays à inventer.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E26 — Chemin exact /wp-login.php

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_path="/wp-login.php"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 7902.

Égalité sur le chemin extrait, paramètres éventuels inclus ; le corpus ne prouve pas une intention hostile.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E27 — Chemin exact /xmlrpc.php

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_path="/xmlrpc.php"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 5329.

Égalité sur le chemin extrait, paramètres éventuels inclus ; le corpus ne prouve pas une intention hostile.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E28 — Chemin exact /

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_path="/"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 4019.

Égalité sur le chemin extrait, paramètres éventuels inclus ; le corpus ne prouve pas une intention hostile.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E29 — Chemin exact /robots.txt

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_path="/robots.txt"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 1005.

Égalité sur le chemin extrait, paramètres éventuels inclus ; le corpus ne prouve pas une intention hostile.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E30 — Revenir au texte Apache depuis le JSON

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", original="raw_line"
| __error__=""
| n_id="__NID__"
| src="access"
| line_format `{{.original}}`
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Le texte Apache devient la ligne affichée..

line_format ne change pas le stockage. Un parser JSON placé ensuite ne recevrait plus le document JSON initial.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E31 — Afficher méthode, statut et chemin

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method", v_status="status", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method!=""
| line_format `{{.v_method}} {{.v_status}} {{.v_path}}`
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 102705.

Les 267 lignes sans méthode reconnue sont exclues explicitement de cette présentation, pas du total global.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E32 — Lire la date écrite dans la source

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_date="apache_time"
| __error__=""
| n_id="__NID__"
| src="access"
| v_date=~"22/Nov/2026:18:5.*"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 87526.

Ce filtre porte sur le texte apache_time. Il ne change pas le timestamp de collecte utilisé par la frise Grafana.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E33 — Lire la provenance du normaliseur

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", origin="metadata.origin", body_service="service"
| __error__=""
| n_id="__NID__"
| src="access"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Champs origin et body_service lisibles sur les access logs..

Un alias évite la collision avec service=normalisation-lab posé par Alloy. Cette extraction ne mesure aucune latence.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E34 — Parser logfmt de façon ciblée

Périmètre : logfmt access du même lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 102972.

Même ensemble d’access logs dans une seconde représentation. Ne pas additionner les volumes JSON et logfmt.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E35 — Méthode POST dans logfmt

Périmètre : logfmt access du même lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method="POST"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 36988.

Comparer à E16 sur la même période et le même lot.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E36 — Statut 500 dans logfmt

Périmètre : logfmt access du même lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status="500"
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 248.

Le parser change, pas la population attendue.

Les nombres annoncés décrivent la population du fichier, pas une promesse que la table affiche toutes les lignes. Une table limitée à 500/2000 lignes n’est pas une preuve de perte ; utiliser les métriques du guide pour contrôler un total.

1. Développer une ligne et lire les champs extraits, puis le JSON ou le texte source.
2. Identifier quel filtre porte sur du texte et lequel porte sur une valeur de champ.
3. Si le résultat est vide, retirer le dernier filtre pour diagnostiquer, mais conserver le bon lot et vérifier la période avant toute nouvelle ingestion.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E37 — Compter tout le corpus

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 102972.

Un seul résultat numérique, pas 2000 lignes téléchargées.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E38 — Compter les 2xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 200
| v_status < 300
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 91145.

Les 206 sont inclus avec les 200.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E39 — Compter les 4xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 2670.

Le total inclut 400,403,404,405,408.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E40 — Compter les 5xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 248.

Le code présent est 500.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E41 — Part de 4xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
(
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[__DUREE__]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
))))
) / (
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
))
)
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 0,02592937886 = 2,592937886 %.

Dénominateur : tous les access logs du lot dans la période.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E42 — Part de 5xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
(
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[__DUREE__]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
))))
) / (
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
))
)
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 0,002408421707 = 0,240842171 %.

Ne pas appliquer un filtre 5xx global au dénominateur.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E43 — Répartition des codes

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum by (v_status) (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 100
| v_status < 600
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Voir le tableau des 11 codes dans la référence locale..

Extraire uniquement le statut évite les milliers de séries inutiles liées aux IDs.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E44 — Répartition des méthodes reconnues

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum by (v_method) (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method!=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : GET=61858, POST=36988, OPTIONS=3221, HEAD=635, PUT=3..

La somme vaut 102705 ; les 267 méthodes non extraites sont expliquées à E19.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E45 — Somme des tailles connues

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 1293498000.

Octets de réponses selon le champ source ; pas taille des lignes JSON dans Loki.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E46 — Moyenne des tailles connues

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
(sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[__DUREE__]
)))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 19025,66667 octets.

Moyenne pondérée : somme des valeurs / nombre de valeurs connues, pas moyenne de moyennes de séries.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E47 — P95 global des tailles connues

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
quantile_over_time(0.95, 
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
) by ()
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Référence locale linéaire : 58043 octets ; comparer l’implémentation Loki..

Regroupement by() : global au lot, pas maximum de P95 par IP.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E48 — Taille maximale connue

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
max (max_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 2017208.

La valeur vient du fichier, pas de l’histogramme d’un échantillon.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E49 — Compter les tailles absentes

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 34985.

Ne pas remplacer les tailles manquantes par zéro.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E50 — Couverture des tailles

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
)))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 0.6602474459, soit 66.024745 %.

Ce n’est pas la couverture de collecte ; le fichier contient des tirets légitimes.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E51 — Volume dans le temps de collecte

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[1m]
))
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Des fenêtres contenant le chargement ; aucune courbe historique de production n’est déduite..

L’axe utilise Time Loki, pas apache_time. Un import en bloc peut donner un pic unique.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E52 — Débit de collecte

Périmètre : JSON access du lot. Mode : Range.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (rate(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[1m]
))
```

4. Choisir le type Range dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : Un débit en lignes/s sur une fenêtre de 1 minute..

Ce débit reflète le chargement du TP, pas la charge du serveur le 22 novembre.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E53 — Comparer dix IP candidates

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum by (v_ip) (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_ip="client_ip"
| __error__=""
| n_id="__NID__"
| src="access"
| v_ip=~"54\\.210\\.20\\.202|::1|148\\.251\\.21\\.227|81\\.22\\.242\\.55|46\\.101\\.48\\.46|104\\.236\\.254\\.104|199\\.21\\.99\\.207|192\\.187\\.98\\.42|148\\.251\\.184\\.139|104\\.154\\.198\\.228"
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : IP 54.210.20.202=34469 ; autres valeurs dans la référence..

Liste bornée choisie depuis l’analyse locale pour rester sous les limites de séries. Ce panneau n’est pas une découverte exhaustive du top global.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E54 — Comparer cinq chemins suivis

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum by (v_path) (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_path="path"
| __error__=""
| n_id="__NID__"
| src="access"
| v_path=~"/wp\\-login\\.php|/xmlrpc\\.php|/|/feed/|/favicon\\.ico"
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : /wp-login.php=7902, /xmlrpc.php=5329, /=4019, /feed/=2816, /favicon.ico=1891..

Sélection de chemins, pas top calculé sur les 30610 chemins différents.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E55 — Classe de tailles 1 à 999 octets

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 1
| v_bytes < 1000
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 16792.

Classe disjointe ; la distribution complète utilise cinq requêtes.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E56 — Classe de tailles au moins 1 Mo décimal

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_bytes="bytes"
| __error__=""
| n_id="__NID__"
| src="access"
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 13.

1 000 000 octets, pas 1 MiB.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E57 — Part de méthodes extraites

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
(sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method!=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset"
| __error__=""
| n_id="__NID__"
| src="access"
[__DUREE__]
)))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 0.9974070621.

Couverture de ce découpage de requête, pas validité sémantique de tout HTTP.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E58 — Protocoles reconnus

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum by (v_protocol) (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_protocol="protocol"
| __error__=""
| n_id="__NID__"
| src="access"
| v_protocol!=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : HTTP/1.1=93595 ; HTTP/1.0=9110..

Les 267 requêtes atypiques ne sont pas complétées artificiellement.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E59 — Compter les méthodes absentes

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_method="method"
| __error__=""
| n_id="__NID__"
| src="access"
| v_method=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 267.

Le total du corpus reste 102972, même si des dimensions ne sont pas disponibles.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## E60 — Compter toutes les erreurs HTTP 4xx et 5xx

Périmètre : JSON access du lot. Mode : Instant.

### A. Saisir et lancer dans Explore

1. Ouvrir Explore / Explorer et choisir Loki-Formation ; ne pas rester dans Kibana ni sélectionner Elasticsearch.
2. Vérifier la période absolue de la référence de collecte.
3. Dans la requête A, choisir Code et remplacer tout le texte précédent par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__NID__"
| json n_id="normalization_id", src="source_dataset", v_status="status"
| __error__=""
| n_id="__NID__"
| src="access"
| v_status!=""
| v_status >= 400
| v_status < 600
| __error__=""
[__DUREE__]
))
```

4. Choisir le type Instant dans les options de requête.
5. Cliquer Run query / Exécuter et attendre la réponse.

### B. Lire les résultats

Référence locale : 2918.

Cette somme ne prouve ni sessions distinctes ni attaques confirmées.

1. Lire la valeur brute ou les séries et leurs labels ; utiliser la vue tabulaire si nécessaire.
2. Pour un ratio, comparer la valeur 0–1 à l’unité pourcentage ; ne pas confondre 0,024 et 2,4 %.
3. Pour une fenêtre de 1 minute, ne pas sommer les points pour reconstruire le nombre de logs du fichier.
4. Si Loki signale trop de séries, ne pas augmenter toutes les limites aveuglément : extraire uniquement les champs utiles et utiliser les candidats bornés du TP.

### C. Conserver une preuve

Noter la période, l’identifiant du lot, l’expression, le résultat et la limite d’affichage éventuelle. Remplacer ensuite la requête A pour la manipulation suivante, sans créer 60 requêtes simultanées.

## Annexe — Pourquoi les anciennes requêtes ne montraient rien

- `A13B_SEED` ne figure pas dans le corpus complet ; il ne faut plus l’exiger.
- Le `run_id` synthétique n’appartient pas aux copies normalisées du corpus.
- `a13_kind=record`, `phase=incident`, `accepted_count` et `source_delay_seconds` appartiennent à l’instrumentation du scénario, pas aux champs Apache disponibles ici.
- Le fichier contient 248 réponses 500 ; un filtre limité à 503, conservé de la simulation, n’est pas le bon exemple pour cette source.
- 34 985 lignes n’ont pas de taille connue ; une moyenne divisée par 102 972 au lieu de 67 987 serait biaisée.
- 267 requêtes n’ont pas été séparées en méthode/chemin/protocole par le normaliseur. Elles restent dans le total access.

Ces expressions sont écrites selon la documentation LogQL et vérifiées structurellement. Le fichier et les références sont analysés localement ; aucune exécution de ces requêtes sur votre Loki n’est prétendue. [web:188][web:186]
