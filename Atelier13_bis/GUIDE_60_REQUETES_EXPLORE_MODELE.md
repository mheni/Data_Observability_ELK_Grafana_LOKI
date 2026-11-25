# Atelier 13 bis — 60 manipulations dans Grafana Explore

Ce support se personnalise avec `personnaliser_support13bis.py`. Ne pas exécuter les marqueurs `__NID__`, `__RUN__` ou `__RANGE_SECONDS__` littéralement. La version personnalisée contient les vrais identifiants et la durée correspondant aux références.

## Préparer l’écran une première fois

1. Ouvrir Grafana et se connecter avec le compte du TP.
2. Dans la navigation, ouvrir **Explore / Explorer**.
3. En haut à gauche de l’espace de requête, sélectionner la source **Loki-Formation**, et non une source Elasticsearch ou Prometheus.
4. Ouvrir le mode **Code**, pas Builder, pour saisir les expressions LogQL.
5. Dans le sélecteur de temps en haut à droite, sélectionner une période absolue. Pour les manipulations normalisation, utiliser la période de `reference-normalisation13bis.json` ; pour le scénario, celle de `reference13bis.json`.
6. Appliquer la période. Dans les options de requête, régler la limite de logs à 2000 pour les petits lots de ce TP, pas 10.
7. Chaque manipulation ci-dessous remplace la requête A : ne pas ajouter 60 requêtes simultanément.

Les libellés anglais sont ceux couramment rencontrés dans Grafana, suivis de leur rôle en français ; la version de Grafana du laboratoire n’a pas été fournie. Le type **Stat** de Grafana n’est pas le menu « Indicateur » de Kibana.

## E01 — flux_bruts_access

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access"}
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 5 references au premier demarrage ; puis 15 sondes de plus apres le scenario.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E02 — flux_bruts_movies

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="movies"}
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Entete CSV + 5 references ; puis 14 sondes de plus.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E03 — json_lot

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 14 lignes dans le format JSON.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E04 — logfmt_lot

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 14 lignes dans le format logfmt.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E05 — texte_ERROR

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__" |= "ERROR"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 3 controles : C_BAD, C_MISSING et C_NEGATIVE.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E06 — texte_sans_unknown

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__" |= "controls" != "unknown"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 3 controles, exclut C_BAD.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E07 — regex_niveaux_texte

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__" |~ "WARN|ERROR"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Recherche dans la ligne entiere, pas une egalite du niveau.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E08 — pattern_apache

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "A13B_SEED"
| pattern `<ip> <_> <_> [<apache_date>] "<method> <path> <protocol>" <status_value> <size_value> "<referer>" "<agent>"`
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 5 references si les seeds autonomes sont utilises.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E09 — pattern_5xx

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "A13B_SEED"
| pattern `<ip> <_> <_> [<apache_date>] "<method> <path> <protocol>" <status_value> <size_value> "<referer>" "<agent>"`
| status_value!="" | status_value >= 500 | status_value < 600 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 1 reference 503 de demonstration.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E10 — regexp_apache

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "A13B_SEED"
| regexp `^(?P<ip_value>\S+) \S+ \S+ \[[^\]]+\] "(?P<request_value>[^"]*)" (?P<status_value>[0-9]{3}) (?P<size_value>[0-9]+|-)`
| status_value="503"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Meme reference 503 que E09.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E11 — octets_bruts

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access"} |= "A13B_SEED"
| pattern `<ip> <_> <_> [<apache_date>] "<method> <path> <protocol>" <status_value> <size_value> "<referer>" "<agent>"`
| size_value!="" | size_value!="-" | size_value >= 1000 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 3 references de taille 1500, 4096 et 8192.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E12 — csv_premier_ID

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="movies"}
| regexp `^(?P<id_value>[0-9]+),` | id_value="1002"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Film B au titre contenant virgule et guillemets.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E13 — csv_pattern_limite

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis_raw",dataset="movies"}
| pattern `<id_value>,<title_value>,<genres_value>`
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Inspecter le titre avec virgule : ce motif ne remplace pas un parseur CSV.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E14 — json_complet

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 14 lignes, dont 4 controles.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E15 — json_movies_alias

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", film="title", movie="movie_id", body_service="service"
| __error__="" | src="movies"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 5 titres complets, dont celui contenant virgule et guillemets.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E16 — json_objet_tableau

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", origin="metadata.origin", genre="genres[0]"
| __error__="" | src="movies"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Premier genre uniquement ; pas de genre invente pour le tableau vide.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E17 — champ_ERROR_exact

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", lvl="level", case_id="test_case"
| __error__="" | src="controls" | lvl="ERROR"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 2 lignes : C_BAD et C_NEGATIVE, contrairement a E05.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E18 — niveaux_logique

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", lvl="level"
| __error__="" | src="controls" | (lvl="WARN" or lvl="ERROR")
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 3 lignes : C_VALID, C_BAD, C_NEGATIVE.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E19 — numeric_valide

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", value="duration_ms", case_id="test_case"
| __error__="" | src="controls" | value!="" | value >= 1000 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 1 ligne C_VALID a 1800 ms.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E20 — conversion_erreur

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", value="duration_ms", case_id="test_case"
| __error__="" | src="controls" | value!="" | value >= 1000 | __error__!=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : C_BAD : valeur unknown non convertible.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E21 — champ_absent

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", value="duration_ms", case_id="test_case"
| __error__="" | src="controls" | value=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : C_MISSING, JSON pourtant valide.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E22 — negatif_metier

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", value="duration_ms", case_id="test_case"
| __error__="" | src="controls" | value!="" | value < 0 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : C_NEGATIVE, -5 convertible mais invalide pour le besoin.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E23 — logfmt_parser

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 14 lignes avec champs scalaires, pas tous les objets/tableaux JSON.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E24 — logfmt_duree

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt | __error__="" | source_dataset="controls" | elapsed!="" | elapsed >= 1s | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : C_VALID avec elapsed=1.8s.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E25 — logfmt_taille

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| logfmt | __error__="" | source_dataset="controls" | payload!="" | payload >= 1MB | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : C_VALID avec payload=2MB.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E26 — mauvais_parser

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="logfmt"} |= "__NID__"
| json | __error__!=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Erreurs de parsing attendues : logfmt n’est pas JSON.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E27 — line_format

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", film="title", movie="movie_id"
| __error__="" | src="movies" | line_format `film={{.movie}} titre={{.film}}`
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 5 lignes reformatees a la requete ; original Loki non modifie.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E28 — label_format

Période : normalisation. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__NID__"
| json src="source_dataset", body_service="service"
| __error__="" | label_format service_lu="{{.body_service}}"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Label de resultat, pas indexation retroactive.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E29 — scenario_tout

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 38 JSON : 29 records, 6 batches et 3 heartbeats.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E30 — scenario_movies_incident

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind", ds="source_dataset", ph="phase"
| __error__="" | k="record" | ds="movies" | ph="incident"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 4 records dont 2 rejetes.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E31 — scenario_rejetes

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind", ok="accepted"
| __error__="" | k="record" | ok="false"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 2 records movies rejetes.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E32 — scenario_5xx

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind", st="http_status"
| __error__="" | k="record" | st!="" | st >= 500 | st < 600 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 2 records access avec 503.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E33 — scenario_retard

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind", delay="source_delay_seconds"
| __error__="" | k="record" | delay!="" | delay >= 600 | __error__=""
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 4 records movies incident.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E34 — scenario_summaries

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind" | __error__="" | k="batch"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 6 resumes distincts des records.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E35 — scenario_heartbeats

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind" | __error__="" | k="heartbeat"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 3 lignes de controle, pas des films.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E36 — scenario_recovery

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json k="a13_kind", ph="phase" | __error__="" | k="record" | ph="recovery"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : 10 records, pas preuve de backfill.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E37 — metrique_01_observed_records

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E38 — metrique_02_expected

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E39 — metrique_03_accepted

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E40 — metrique_04_rejected

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="rejected_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E41 — metrique_05_missing

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="missing_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E42 — metrique_06_completeness

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
/
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E43 — metrique_07_timeline

Période : scenario. Type : requête métrique, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (dataset_value) (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
[10s]
))
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E44 — metrique_08_http_codes

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (status_value) (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E45 — metrique_09_http_5xx_ratio

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
(
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
| status_value >= 500
| __error__=""
[__RANGE_SECONDS__s]
))
 or
 (0 * sum (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[__RANGE_SECONDS__s]
)))
) /
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E46 — metrique_10_access_observations

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E47 — metrique_11_movie_observations

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="movies"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E48 — metrique_12_max_observed_delay

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
max (max_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_delay_seconds"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E49 — metrique_13_last_source_timestamp

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
1000 * max by (dataset_value) (max_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_event_epoch"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E50 — metrique_14_completeness_by_dataset

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (dataset_value) (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
/
sum by (dataset_value) (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E51 — metrique_15_batch_table

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E52 — metrique_16_rejected_by_reason

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (reason) (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", reason="quality_reason", accepted_value="accepted"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| accepted_value="false"
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E53 — metrique_17_investigation_logs

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| dataset_value=~".*"
| phase_value=~".*"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E54 — metrique_18_missing_by_dataset

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (dataset_value) (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="missing_count"
| __error__=""
| kind="batch"
| dataset_value=~".*"
| phase_value=~".*"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E55 — metrique_19_delay_observations

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E56 — metrique_20_heartbeat

Période : scenario. Type : requête de lignes, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", phase_value="phase"
| __error__=""
| kind="heartbeat"
| phase_value=~".*"
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels du flux puis les champs extraits par le parser ; repérer les alias créés.
3. Comparer une ligne à l’expression : quel filtre a permis de la garder ?
4. Si aucune ligne n’apparaît, retirer progressivement les filtres finaux, sans changer de source ni de période, pour localiser le premier point où le résultat disparaît.
5. Ne pas relancer le générateur à chaque écran vide : vérifier d’abord les marqueurs et les contrôles de collecte.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E57 — metrique_21_accepted_records

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", accepted_value="accepted"
| __error__=""
| kind="record"
| accepted_value="true"
| dataset_value=~".*"
| phase_value=~".*"
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E58 — metrique_22_rate_by_dataset

Période : scenario. Type : requête métrique, mode Range / Plage.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (dataset_value) (rate(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
[10s]
))
```

4. Choisir Range / Plage dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E59 — metrique_23_bytes_total

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum (sum_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
| dataset_value="access"
| json byte_value="response_bytes"
| byte_value!=""
| unwrap byte_value
| __error__=""
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

## E60 — metrique_24_record_status

Période : scenario. Type : requête métrique, mode Instant.

### A. Saisir et exécuter

1. Dans Explore, vérifier la source Loki-Formation.
2. Régler la période absolue correspondant au lot indiqué ci-dessus ; ne pas reprendre une ancienne période sans la vérifier.
3. Cliquer dans la zone de texte de la requête A, sélectionner son contenu et le remplacer par :

```logql
sum by (accepted_value) (count_over_time(
{job="atelier13bis",format="json"} |= "__RUN__"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", accepted_value="accepted"
| __error__=""
| kind="record"
| dataset_value=~".*"
| phase_value=~".*"
[__RANGE_SECONDS__s]
))
```

4. Choisir Instant dans les options de requête si ce choix est affiché.
5. Cliquer **Run query / Exécuter la requête** ; ne pas seulement enregistrer l’expression dans un fichier.

### B. Lire et vérifier

Attendu : Voir la fiche panneau et le manifeste de controle.

1. Examiner le résultat numérique ou les séries ; si nécessaire ouvrir l’affichage tabulaire.
2. Lire les labels de regroupement et l’unité de la valeur, pas seulement sa couleur.
3. Comparer à la fiche du panneau correspondant et au manifeste ; une somme de points de fenêtres glissantes n’est pas le total des logs.
4. Si une erreur de pipeline est signalée, vérifier le filtre `__error__=""` après la conversion ou `unwrap` ; ne pas confondre ce diagnostic avec un zéro métier.

### C. Conserver la preuve

Noter l’identifiant de cette manipulation, le périmètre choisi, le résultat et une phrase d’explication. Pour tester la manipulation suivante, remplacer le texte de la requête A, pas la configuration de la source de données.

