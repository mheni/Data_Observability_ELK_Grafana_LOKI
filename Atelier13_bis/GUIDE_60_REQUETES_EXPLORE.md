# Atelier 13 bis — 60 requêtes LogQL dans Grafana Explore

Corpus : `donnees/access_log_actualise`. Le fichier fourni contient 102972 lignes non vides. Les résultats ci-dessous décrivent ce fichier, sur toute la période du lot. Une table de logs affiche seulement un extrait ; le compteur backend permet de vérifier le total.

## Préparer Explore

1. Exécuter les étapes de préparation, collecte, contrôle et génération des livrables décrites dans `ATELIER_13BIS.md`.
2. Ouvrir le guide personnalisé produit dans `livrables13bis/`. Le script y remplace `__LOT__` par le lot réel et `__DUREE__` par la durée correspondant à la référence de collecte.
3. Dans Grafana, cliquer Explore / Explorer dans la navigation.
4. Choisir Loki-Formation dans le sélecteur de source.
5. Cliquer Code plutôt que Builder.
6. Régler la période absolue sur from_utc et to_utc de `reference13bis.json` et appliquer.
7. Pour les lignes, utiliser Range et une limite de 500 ou 2000 pour l’inspection. Pour les totaux, utiliser Instant et count_over_time, qui ne télécharge pas toutes les lignes.
8. Chaque fiche remplace le texte de la requête A ; ne pas ajouter soixante requêtes simultanées.

## Progression

| Fiches | Objectif |
|---|---|
| E01–E08 | Formats, filtres textuels et extraction du brut |
| E09–E23 | Champs JSON, statuts, méthodes et tailles |
| E24–E33 | IP, chemins, présentation, date source et provenance |
| E34–E36 | logfmt sur le même ensemble de lignes |
| E37–E50 | Comptages, ratios et statistiques côté Loki |
| E51–E60 | Collecte dans le temps, comparaisons bornées et distributions |

L’unité de chaque mesure est explicite. Une taille n’est pas une durée ; une IP n’est pas une personne. Les quatre mille cinq cent quarante IP et les trente mille six cent dix chemins du fichier ne sont pas promus en labels de stockage.

## E01 — Voir le flux Apache brut

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"}
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972 lignes dans la population ; la liste affichée est plafonnée.

Le lot est un label d’ingestion commun aux trois représentations. Le texte reste Apache.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E02 — Voir les lignes JSON

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972 documents JSON, une copie par ligne source.

Les champs ne deviennent pas tous des labels d’ingestion : le parser agit pendant la recherche.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E03 — Voir les lignes logfmt

Format : logfmt ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="logfmt",lot="__LOT__"}
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972 lignes, même population sous un autre format.

Ne pas additionner les copies comme de nouveaux accès.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E04 — Chercher wp-login dans le texte

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"} |= "/wp-login.php"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Des lignes contenant le texte.

Ce motif peut être présent dans plusieurs parties d’une ligne ; le filtre de chemin exact vient ensuite.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E05 — Chercher POST dans le texte

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"} |= "POST"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Des lignes contenant POST.

Une sous-chaîne n’est pas encore une égalité sur method.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E06 — Regex textuelle GET ou HEAD

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"} |~ `"(GET|HEAD) `
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Des lignes présentes dans le fichier.

Le filtre regex cherche du texte. Inspecter ensuite les captures.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E07 — Extraire le début Apache par regexp

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"}
| regexp `^(?P<v_ip>\S+) \S+ \S+ \[[^\]]+\] "(?P<v_request>(?:\\.|[^"\\])*)" (?P<v_status>[0-9]{3}) (?P<v_size>[0-9]+|-)`
| v_status!=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : IP, requête, statut et taille extraits.

La capture size peut valoir le tiret. Cette extraction ne valide pas toute la syntaxe HTTP.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E08 — Extraire la requête entière par pattern

Format : raw ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis_raw",dataset="access",format="raw",lot="__LOT__"}
| pattern `<v_ip> <_> <_> [<v_date>] "<v_request>" <v_status> <v_size> <_>`
| v_status!=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Des lignes reconnues ; ouvrir une requête atypique pour discuter les limites.

Ne pas présumer que chaque request contient méthode/chemin/protocole séparables.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E09 — Parser les champs du JSON

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json src="source_dataset", ok="parse_ok"
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972.

JSON bien formé n’est pas synonyme de requête HTTP complète. parse_ok décrit la reconnaissance du début Apache.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E10 — Réponses 200

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status="200"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 91074.

Égalité sur le statut extrait, pas sur un nombre trouvé dans le texte.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E11 — Réponses 404

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status="404"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 2298.

Égalité sur le statut extrait, pas sur un nombre trouvé dans le texte.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E12 — Réponses 500

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status="500"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 248.

Égalité sur le statut extrait, pas sur un nombre trouvé dans le texte.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E13 — Famille 4xx

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 2670.

Le deuxième filtre d’erreur est après la comparaison numérique.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E14 — Famille 5xx

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 248.

Le deuxième filtre d’erreur est après la comparaison numérique.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E15 — Méthode GET

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method="GET"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 61858.

Une méthode n’est disponible que si la requête a pu être découpée par le normaliseur.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E16 — Méthode POST

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method="POST"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 36988.

Une méthode n’est disponible que si la requête a pu être découpée par le normaliseur.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E17 — Méthode HEAD

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method="HEAD"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 635.

Une méthode n’est disponible que si la requête a pu être découpée par le normaliseur.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E18 — Méthode OPTIONS

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method="OPTIONS"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 3221.

Une méthode n’est disponible que si la requête a pu être découpée par le normaliseur.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E19 — Méthode non extraite

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 267.

Les lignes restent dans le total et conservent request_line/raw_line. Ne pas les supprimer silencieusement.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E20 — Tailles connues

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 67987.

Le champ bytes est absent quand la source vaut le tiret.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E21 — Tailles absentes

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 34985.

Une absence ne vaut pas zéro octet et ne signifie pas un document perdu.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E22 — Taille au moins 100000 octets

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 100000
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 1134.

La valeur source est en octets, pas en millisecondes.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E23 — Taille au moins 1000000 octets

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 13.

La valeur source est en octets, pas en millisecondes.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E24 — Adresse exacte 54.210.20.202

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_ip="client_ip"
| __error__=""
| v_ip="54.210.20.202"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 34469.

Une IP n’est pas une personne. ::1 est la boucle locale, à ne pas géolocaliser.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E25 — Adresse exacte ::1

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_ip="client_ip"
| __error__=""
| v_ip="::1"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 3219.

Une IP n’est pas une personne. ::1 est la boucle locale, à ne pas géolocaliser.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E26 — Chemin exact /wp-login.php

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_path="path"
| __error__=""
| v_path="/wp-login.php"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 7902.

Les paramètres éventuels restent dans path. Cette présence seule ne prouve pas une attaque.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E27 — Chemin exact /xmlrpc.php

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_path="path"
| __error__=""
| v_path="/xmlrpc.php"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 5329.

Les paramètres éventuels restent dans path. Cette présence seule ne prouve pas une attaque.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E28 — Chemin exact /

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_path="path"
| __error__=""
| v_path="/"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 4019.

Les paramètres éventuels restent dans path. Cette présence seule ne prouve pas une attaque.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E29 — Chemin exact /robots.txt

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_path="path"
| __error__=""
| v_path="/robots.txt"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 1005.

Les paramètres éventuels restent dans path. Cette présence seule ne prouve pas une attaque.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E30 — Afficher la ligne Apache depuis le JSON

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json original="raw_line"
| __error__=""
| line_format `{{.original}}`
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Les lignes affichées reprennent le texte source.

line_format modifie le résultat visible, pas le document conservé. Un parser JSON placé après ne reçoit plus le JSON initial.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E31 — Afficher méthode, statut et chemin

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method", v_status="status", v_path="path"
| __error__=""
| v_method!=""
| line_format `{{.v_method}} {{.v_status}} {{.v_path}}`
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102705.

La présentation exclut explicitement les 267 méthodes absentes ; le total général ne les exclut pas.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E32 — Filtrer la date écrite dans la source

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_date="apache_time"
| __error__=""
| v_date=~"22/Nov/2026:18:5.*"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 87526.

Filtre de contenu, pas changement de l’horloge Loki. La période globale reste celle de collecte.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E33 — Objet imbriqué et alias

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="json",lot="__LOT__"}
| json origin="metadata.origin", body_service="service"
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : origin=atelier13bis_access ; body_service=web-formation.

Utiliser des alias explicites pour éviter de masquer une collision avec un label portant le même nom.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E34 — Parser logfmt de façon ciblée

Format : logfmt ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="logfmt",lot="__LOT__"}
| logfmt v_status="status", v_method="method"
| __error__=""
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972.

Les objets imbriqués JSON ne sont pas implicitement reconstruits dans le logfmt.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E35 — Méthode POST dans logfmt

Format : logfmt ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="logfmt",lot="__LOT__"}
| logfmt v_method="method"
| __error__=""
| v_method="POST"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 36988.

Même compte que dans JSON si le lot complet est collecté.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E36 — Réponses 500 dans logfmt

Format : logfmt ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
{job="atelier13bis",format="logfmt",lot="__LOT__"}
| logfmt v_status="status"
| __error__=""
| v_status="500"
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 248.

Le parser change, pas les lignes métier représentées.

1. Développer une ligne avec sa flèche de détail.
2. Lire les labels job/format/lot puis les champs extraits ; distinguer stockage et parsing à la requête.
3. Comparer la ligne au filtre saisi et noter ce qui justifie sa présence.
4. Le nombre annoncé pour la population ne signifie pas que la table doit afficher toutes les lignes : sa limite de 500/2000 est un réglage d’affichage. Utiliser les métriques pour un total.
5. Si aucune ligne n’apparaît, vérifier lot et période, puis retirer progressivement les filtres finaux pour diagnostiquer ; ne pas modifier les données pour remplir le graphique.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E37 — Compter tous les accès

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 102972.

Compte backend, non limité au nombre de lignes affichées.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E38 — Compter les 2xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 200
| v_status < 300
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 91145.

200 et 206 sont inclus.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E39 — Compter les 4xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 2670.

Famille 400 à 499.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E40 — Compter les 5xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 248.

Famille 500 à 599 ; le fichier contient des 500.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E41 — Part de 4xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
((sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 500
| __error__=""
[__DUREE__]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
))))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
)))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 0,02592937886, soit 2,592937886 %.

Le dénominateur est tous les access logs du lot.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E42 — Part de 5xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
((sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 500
| v_status < 600
| __error__=""
[__DUREE__]
))) or (0 * (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
))))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
)))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 0,002408421707, soit 0,240842171 %.

Pas de filtre global 5xx sur le dénominateur.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E43 — Codes HTTP par valeur

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum by (v_status) (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Onze séries ; voir le tableau des codes.

Extraire seulement le statut pour limiter la cardinalité.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E44 — Méthodes reconnues par valeur

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum by (v_method) (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method!=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : GET=61858 ; POST=36988 ; OPTIONS=3221 ; HEAD=635 ; PUT=3.

Les méthodes absentes ne sont pas inventées.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E45 — Somme des tailles connues

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum(sum_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 1293498000 octets.

Somme des tailles de réponse, pas taille des fichiers Loki.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E46 — Moyenne des tailles connues

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
(sum(sum_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[__DUREE__]
)))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 19025,66667 octets.

Somme divisée par 67987 valeurs connues, pas moyenne de moyennes.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E47 — P95 global des tailles connues

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
quantile_over_time(0.95, 
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
) by ()
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Référence locale linéaire : 58043 octets.

Le by() est global, pas un maximum de P95 par IP. Comparer la convention Loki.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E48 — Maximum des tailles connues

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
max(max_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
| unwrap v_bytes
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 2017208 octets.

Ce maximum ne dépend pas de l’échantillon d’histogramme.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E49 — Compter les tailles absentes

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 34985.

Absent ne devient pas zéro.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E50 — Part de tailles connues

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
(sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 0
| __error__=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
)))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 0.6602474459.

Renseignement du champ, pas preuve de livraison.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E51 — Volume dans le temps de collecte

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[1m]
))
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Un pic ou des fenêtres près du chargement.

Une fenêtre 1 min ne doit pas être présentée comme historique des requêtes source.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E52 — Débit de collecte

Format : json ; mode : Range.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum(rate(
{job="atelier13bis",format="json",lot="__LOT__"}
[1m]
))
```

4. Dans les options de requête, choisir Range.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : Valeurs en lignes par seconde.

Pas une latence, ni nécessairement le débit du serveur source.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E53 — Comparer dix IP suivies

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum by (v_ip) (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_ip="client_ip"
| __error__=""
| v_ip=~"54\\.210\\.20\\.202|::1|148\\.251\\.21\\.227|81\\.22\\.242\\.55|46\\.101\\.48\\.46|104\\.236\\.254\\.104|199\\.21\\.99\\.207|192\\.187\\.98\\.42|148\\.251\\.184\\.139|104\\.154\\.198\\.228"
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 54.210.20.202=34469 ; ::1=3219.

Liste bornée, choisie depuis l’analyse locale.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E54 — Comparer cinq chemins suivis

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum by (v_path) (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_path="path"
| __error__=""
| v_path=~"/wp\\-login\\.php|/xmlrpc\\.php|/|/feed/|/favicon\\.ico"
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 7902 ; 5329 ; 4019 ; 2816 ; 1891.

Sélection explicite, pas top global recalculé sur 30610 chemins.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E55 — Classe de taille 1 à 999 octets

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1
| v_bytes < 1000
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 16792.

Classe disjointe, les absences ne sont pas incluses.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E56 — Classe de taille au moins un million d’octets

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_bytes="bytes"
| __error__=""
| v_bytes!=""
| v_bytes >= 1000000
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 13.

Un Mo décimal ici, pas un MiB.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E57 — Part des méthodes extraites

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
(sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method!=""
[__DUREE__]
))) / (sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
[__DUREE__]
)))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 0.9974070621.

Ne pas appeler cet indicateur taux de livraison.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E58 — Protocoles reconnus

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum by (v_protocol) (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_protocol="protocol"
| __error__=""
| v_protocol!=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : HTTP/1.1=93595 ; HTTP/1.0=9110.

267 lignes sans découpage complet restent dans le total.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E59 — Compter les méthodes absentes

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_method="method"
| __error__=""
| v_method=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 267.

La conversion JSON est réussie, mais ce découpage est absent.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## E60 — Compter toutes les erreurs 4xx et 5xx

Format : json ; mode : Instant.

### A. Saisir et exécuter

1. Ouvrir Explore, choisir Loki-Formation et vérifier la période de référence.
2. Cliquer Code dans la requête A.
3. Sélectionner tout le contenu de A puis le remplacer par :

```logql
sum (count_over_time(
{job="atelier13bis",format="json",lot="__LOT__"}
| json v_status="status"
| __error__=""
| v_status!=""
| v_status >= 400
| v_status < 600
| __error__=""
[__DUREE__]
))
```

4. Dans les options de requête, choisir Instant.
5. Cliquer Run query / Exécuter la requête et attendre la réponse.

### B. Lire les résultats

Référence du fichier fourni : 2918.

Une erreur HTTP n’est pas un visiteur unique ni une cause racine établie.

1. Lire la valeur brute ou les séries, avec leur label de regroupement.
2. Si nécessaire ouvrir la vue tabulaire ; ne pas confondre nombre de séries et valeur d’une série.
3. Pour les ratios, une valeur 0–1 doit recevoir le format Percent (0.0–1.0) dans un panneau, sans multiplication supplémentaire par 100.
4. Pour les fenêtres temporelles, lire le pas exécuté et la fenêtre ; ne pas sommer aveuglément les points pour reconstruire un total.
5. Si Loki signale trop de séries, extraire seulement les champs nécessaires et utiliser les sélections bornées des exercices.

### C. Conserver la preuve

Noter l’identifiant de la fiche, le lot, la période, le résultat, l’unité et l’éventuelle limite d’affichage. Pour la fiche suivante, remplacer le contenu de A, sans changer la source de données.

## Contrôles de compréhension

- Comparer E05 et E16 : recherche du texte POST ou égalité du champ method.
- Comparer E12 et E36 : même code 500, JSON puis logfmt, sans doubler la population.
- Comparer E19 et E59 : des lignes sans méthode restent dans la population totale.
- Comparer E20/E21 et E45/E46 : les tailles absentes sont exclues des statistiques de valeurs, pas transformées en zéros.
- Comparer E26 et E04 : chemin exact ou mot présent dans la ligne.
- Expliquer pourquoi E51/E52 utilisent la collecte et non la chronologie source reconstruite.
- Justifier la sélection bornée d’IP et de chemins avant de créer les panneaux correspondants.

## Lecture des erreurs

Un parser peut produire __error__. Une conversion numérique peut créer une erreur après un parsing réussi : vérifier l’erreur après la conversion/unwrap. Un champ absent ne provoque pas nécessairement une erreur de parsing. Le résultat doit conserver la distinction entre syntaxe, présence, type et sens métier.

Les nombres de référence sont calculés localement sur le fichier fourni. La compilation et l’exécution LogQL dans l’environnement du participant font partie des contrôles du TP.
