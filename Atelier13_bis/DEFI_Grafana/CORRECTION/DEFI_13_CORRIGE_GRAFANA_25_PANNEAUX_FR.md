# Défi 13 — Corrigé Grafana : construire 25 panneaux à partir des logs OpenSSH

Version cible : Grafana avec source Loki. Les noms des boutons sont ceux couramment rencontrés dans Grafana, avec leur rôle en français ; la version exacte de votre laboratoire doit être confirmée par le formateur.

## 1. Lire ce corrigé

- Cliquer : clic gauche.
- Glisser : maintenir le clic sur l’en-tête ou la poignée, déplacer puis relâcher.
- Les blocs `logql` se saisissent dans l’éditeur de requête Grafana, mode Code.
- Les blocs `bash` se saisissent dans le terminal Linux.
- `${lot}` et `${loki_ds}` sont des variables du dashboard, à créer avant le premier panneau. Elles ne sont pas des marqueurs à remplacer dans le texte de la requête.
- Les valeurs de référence sont désignées par des lettres. Elles sont lues dans `reference_source.json`, produit par la partie 1 sur votre propre fichier.
- Une table Loki affichée n’est pas un compteur : les totaux viennent des panneaux Stat.

Chaque panneau est décrit jusqu’à sa sauvegarde, sans renvoi à une procédure commune.

## 2. Relever les références avant de construire

Depuis le terminal, dans le dossier du défi :

```bash
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path("preparation_defi13/reference_source.json").read_text(encoding="utf-8"))
for k in ["N_nonempty_lines","A_canonical_records","F_failures","S_successes","I_lines_with_ip","U_distinct_ips_all_lines","B_possible_break_in_lines","R_repeat_sum","other_unclassified_lines"]:
    print(k, r[k])
print("types", r["event_type_counts"])
PY
```

| Lettre | Champ de `reference_source.json` | Sens |
|---|---|---|
| N | `N_nonempty_lines` | Lignes non vides du fichier |
| A | `A_canonical_records` | Lignes Failed ou Accepted reconnues |
| F | `F_failures` | Échecs canoniques |
| S | `S_successes` | Succès canoniques |
| I | `I_lines_with_ip` | Lignes avec une IP extraite |
| U | `U_distinct_ips_all_lines` | IP distinctes extraites de toutes les lignes |
| B | `B_possible_break_in_lines` | Lignes `reverse_mapping` ou `address_mismatch` |
| R | `R_repeat_sum` | Somme des N dans « message repeated N times » |

Contrôler F + S = A. Ne pas retenir un chiffre d’un autre fichier OpenSSH : Loghub peut fournir des variantes du corpus, et seul le rapport de votre préparation fait foi.

Le fichier `reference_loki_defi13.json`, produit par `verifier_loki_defi13.py`, confirme que Loki contient les mêmes volumes et les mêmes répartitions de types. Ce contrôle compare des agrégats ; il ne vérifie pas chaque identifiant en ligne.

## 3. Créer le dashboard et ses variables

### A. Créer et enregistrer

1. Dans la navigation, cliquer Dashboards.
2. Cliquer New → New dashboard.
3. Enregistrer sous `[D13] OpenSSH — diagnostic Loki` dans le dossier autorisé du laboratoire.
4. Sélectionner la période autour de la collecte, par exemple `Last 6 hours` si la partie 1 vient d’être exécutée, ou la période absolue `from_utc` / `to_utc` de `reference_loki_defi13.json`. Le journal OpenSSH ne porte pas d’année : la période du dashboard est celle de la collecte dans Loki.
5. Enregistrer le dashboard.

### B. Trouver les paramètres et variables

1. Cliquer Edit / Modifier en haut à droite.
2. Chercher l’icône Dashboard options dans la barre d’outils ; si Grafana propose View all settings, cliquer dessus. Sur une interface plus ancienne, utiliser la roue dentée Dashboard settings.
3. Ouvrir la section Variables. Si le bouton Add variable est visible directement dans le dashboard en édition, il peut être utilisé aussi.

### C. Variable de source

1. Cliquer Add variable / Ajouter une variable.
2. Type : Data source. Name : `loki_ds`. Label : `Source Loki`.
3. Data source type : Loki.
4. Choisir `Loki-Formation` comme valeur courante, confirmer et enregistrer.

### D. Variable du lot

1. Récupérer la valeur dans le terminal :

```bash
python3 - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("preparation_defi13/manifest.json").read_text(encoding="utf-8"))["lot"])
PY
```

2. Ajouter une variable : Type Text box, Name `lot`, Label `Lot OpenSSH`.
3. Valeur par défaut : coller exactement l’identifiant affiché, sans guillemets ni espace.
4. Confirmer, revenir au dashboard, enregistrer, puis vérifier que le champ en haut contient bien la valeur.

Dans Explore, la variable `${lot}` n’existe pas : utiliser le sélecteur imprimé par `preparer_openssh13.py`, qui contient déjà la valeur réelle du lot. Dans les panneaux du dashboard, laisser `${lot}` tel quel.

## 4. Construire les panneaux

### P01 — Lignes indexées

Objectif : Taille du périmètre observé dans Loki pour ce lot.

Limite : Une ligne n’est ni une session ni une personne.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : N = `N_nonempty_lines`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P01 — Lignes indexées`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P02 — Enregistrements canoniques

Objectif : Dénominateur explicite : seulement les résultats d’authentification Failed/Accepted reconnus.

Limite : Les messages PAM, déconnexions et résumés de répétition ne sont pas ajoutés ici.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record"
| __error__=""
| v_auth="1"
[$__range]
)) or vector(0)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : A = `A_canonical_records`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P02 — Enregistrements canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P03 — Échecs canoniques

Objectif : Nombre d’échecs d’authentification reconnus (méthode Failed …).

Limite : Une ligne d’échec n’est pas forcément une tentative distincte : voir P21 pour les résumés répétés.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_fail="is_failure"
| __error__=""
| v_fail="1"
[$__range]
)) or vector(0)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : F = `F_failures`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P03 — Échecs canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P04 — Succès canoniques

Objectif : Zéro est une valeur correcte si le journal ne contient aucune connexion Accepted.

Limite : Ne pas fabriquer de succès pour remplir le tableau de bord.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_ok="is_success"
| __error__=""
| v_ok="1"
[$__range]
)) or vector(0)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : S = `S_successes`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P04 — Succès canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P05 — IP sources distinctes

Objectif : Diversité des adresses IP extraites, toutes lignes confondues.

Limite : Une IP n’est pas une personne. Cette formule compte des séries : une limite de séries Loki peut la bloquer si le corpus contient beaucoup d’adresses.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
count(
sum by (v_ip) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_ip="source_ip"
| __error__=""
| v_ip!=""
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : U = `U_distinct_ips_all_lines`, calculé sur toutes les lignes ; il peut différer d’un décompte restreint aux échecs.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P05 — IP sources distinctes`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P06 — Part d’échec canonique

Objectif : Échecs rapportés aux seuls enregistrements canoniques.

Limite : Ne pas multiplier par 100 : l’unité pourcentage le fait. Ne pas diviser par toutes les lignes.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
(
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_fail="is_failure"
| __error__=""
| v_fail="1"
[$__range]
)) or vector(0)
)
/
(
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record"
| __error__=""
| v_auth="1"
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : Percent (0.0–1.0).
6. Dans Standard options → Decimals, saisir `2`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.
9. Ne pas ajouter `* 100` à la requête : l’unité pourcentage convertit le ratio pour l’affichage.

#### C. Vérifier avant de sauvegarder

Référence : F / A, soit `F_failures / A_canonical_records` ; afficher le pourcentage avec deux décimales.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P06 — Part d’échec canonique`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P07 — Lignes sans IP extraite

Objectif : Part des lignes dont aucune adresse IP n’a pu être extraite.

Limite : Une absence d’IP est normale pour plusieurs messages PAM ou de service.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
(
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_ip="source_ip"
| __error__=""
| v_ip=""
[$__range]
)) or vector(0)
)
/
(
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : Percent (0.0–1.0).
6. Dans Standard options → Decimals, saisir `2`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.
9. Ne pas ajouter `* 100` à la requête : l’unité pourcentage convertit le ratio pour l’affichage.

#### C. Vérifier avant de sauvegarder

Référence : (N − `I_lines_with_ip`) / N.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P07 — Lignes sans IP extraite`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P08 — Alertes « POSSIBLE BREAK-IN »

Objectif : Messages sshd qui signalent un défaut de correspondance DNS/adresse.

Limite : Cette phrase est émise par sshd : elle n’établit pas à elle seule une intrusion.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_type="event_type"
| __error__=""
| v_type=~"reverse_mapping|address_mismatch"
[$__range]
)) or vector(0)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : B = `B_possible_break_in_lines`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P08 — Alertes « POSSIBLE BREAK-IN »`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P09 — Collecte dans le temps — fenêtre 1 min

Objectif : Visualiser le chargement dans Loki.

Limite : L’axe temps est celui de la collecte, pas l’heure syslog des événements. Voir P11 pour l’heure écrite dans les lignes.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
[1m]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, Min interval = 1s ; la fenêtre de comptage écrite dans LogQL reste 1m.
2. Cliquer Run queries.
3. Choisir Time series.
4. Laisser Unit vide ; la valeur est un nombre de lignes par fenêtre.
5. Dans Tooltip, choisir Single ou All, pas Hidden.
6. Survoler le pic et lire l’heure de collecte. Le pas réellement exécuté se lit dans Inspect → Query.
7. Si la période choisie est trop large, le chargement bref peut paraître minuscule : resserrer la période autour de la collecte.
8. Ne pas sommer les points pour retrouver N.

#### C. Vérifier avant de sauvegarder

Référence : Une ou plusieurs fenêtres non vides au moment du chargement ; aucune valeur unique de référence.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P09 — Collecte dans le temps — fenêtre 1 min`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P10 — Répartition par type d’événement

Objectif : Quels types de messages dominent le fichier ?

Limite : Un type fréquent n’est pas un taux d’attaque : il décrit des catégories de lignes.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_type) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_type="event_type"
| __error__=""
| v_type!=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Dans Options → Legend de la requête A, saisir `{{v_type}}`.
3. Choisir la visualisation Pie chart.
4. Dans Pie chart options, choisir Pie type = Donut.
5. Dans Legend, afficher la liste, placer la légende à droite et ajouter Value et Percent si les options existent.
6. Dans Tooltip, choisir Single, puis survoler une part.
7. Si une catégorie très rare est difficile à voir, lire la valeur dans la légende : une part étroite n’est pas absente.

#### C. Vérifier avant de sauvegarder

Référence : Les parts doivent suivre `event_type_counts`, avec le même ordre de grandeur pour chaque type présent.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P10 — Répartition par type d’événement`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P11 — Messages par heure syslog

Objectif : Répartition des lignes selon l’heure écrite dans le journal.

Limite : Le journal n’indique pas l’année : le graphique utilise seulement l’heure de la journée, sans date historique. La requête affiche au plus 5000 lignes.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_type="event_type"
| __error__=""
```

#### B. Configurer le calcul et la visualisation

1. Dans la requête A, choisir Type = Range puis régler Line limit sur `5000`.
2. Cliquer Run queries.
3. Choisir temporairement la visualisation Table ; repérer le champ qui contient le JSON, généralement Line.
4. Ouvrir l’onglet Transformations → Add transformation → Extract fields. Source = ce champ, Format = JSON, Replace all fields activé, Keep time désactivé.
5. Ajouter Group by : `hour` = Group by ; `record_id` = Calculate → Count.
6. Ajouter Sort by : champ `hour`, ordre croissant.
7. Choisir la visualisation Bar chart ; X Axis = `hour`.
8. Vérifier que seul le champ de comptage reste en série ; retirer les autres champs numériques dans les options.
9. Afficher les valeurs sur les barres si l’option existe.
10. Comparer la somme des barres au nombre de lignes retournées : elle doit valoir N si N ≤ 5000.

#### C. Vérifier avant de sauvegarder

Référence : Les barres doivent suivre `hour_counts`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P11 — Messages par heure syslog`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P12 — Échecs et succès par heure syslog

Objectif : Comparer les deux issues canoniques selon l’heure du journal.

Limite : Si S = 0, la série des succès reste à zéro. Ne pas ajouter une série artificielle.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record"
| __error__=""
| v_auth="1"
```

#### B. Configurer le calcul et la visualisation

1. Dans la requête A, choisir Type = Range puis régler Line limit sur `5000`.
2. Cliquer Run queries.
3. Choisir temporairement la visualisation Table ; repérer le champ qui contient le JSON, généralement Line.
4. Ouvrir l’onglet Transformations → Add transformation → Extract fields. Source = ce champ, Format = JSON, Replace all fields activé, Keep time désactivé.
5. Ajouter Group by : `hour` = Group by ; `is_failure` = Calculate → Total (nom interne `sum`) ; `is_success` = Calculate → Total (nom interne `sum`).
6. Ajouter Sort by : champ `hour`, ordre croissant.
7. Choisir Bar chart ; X Axis = `hour` ; Stacking = Normal.
8. Renommer les séries avec Standard options → Display name ou Organize fields : `Échecs`, `Succès`.
9. Vérifier que la somme des échecs vaut F et celle des succès vaut S.

#### C. Vérifier avant de sauvegarder

Référence : La somme des échecs vaut F et celle des succès vaut S.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P12 — Échecs et succès par heure syslog`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P13 — Top 10 IP — échecs canoniques

Objectif : Contributeurs aux échecs reconnus, limités aux dix premiers.

Limite : La somme du top peut être inférieure à F : d’autres IP et des lignes sans IP existent.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
topk(10,
sum by (v_ip) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_ip="source_ip", v_fail="is_failure"
| __error__=""
| v_ip!=""
| v_fail="1"
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant sur chaque requête, puis Run queries.
2. Dans Legend de la requête, saisir `{{v_ip}}`.
3. Choisir Bar gauge.
4. Orientation = Horizontal ; Calculation = Last * (dernière valeur non nulle).
5. Unit vide, Decimals = 0.
6. Agrandir l’aperçu si les libellés sont tronqués.
7. Trier mentalement ou dans les options de panneau si une option de tri est proposée ; ne pas conclure que la liste est exhaustive.

#### C. Vérifier avant de sauvegarder

Référence : Comparer au classement `top10_failure_ips`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P13 — Top 10 IP — échecs canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P14 — Top 10 utilisateurs — échecs canoniques

Objectif : Noms d’utilisateurs les plus visés dans les échecs reconnus.

Limite : Un nom d’utilisateur peut être invalide : ce n’est pas une preuve de compte compromis.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
topk(10,
sum by (v_user) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_user="user_name", v_fail="is_failure"
| __error__=""
| v_user!=""
| v_fail="1"
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant sur chaque requête, puis Run queries.
2. Dans Legend de la requête, saisir `{{v_user}}`.
3. Choisir Bar gauge.
4. Orientation = Horizontal ; Calculation = Last * (dernière valeur non nulle).
5. Unit vide, Decimals = 0.
6. Agrandir l’aperçu si les libellés sont tronqués.
7. Trier mentalement ou dans les options de panneau si une option de tri est proposée ; ne pas conclure que la liste est exhaustive.

#### C. Vérifier avant de sauvegarder

Référence : Comparer au classement `top10_failure_users`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P14 — Top 10 utilisateurs — échecs canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P15 — Échecs : utilisateur valide ou invalide

Objectif : Distinguer les échecs sur des noms d’utilisateurs invalides des autres échecs.

Limite : « true » signifie que sshd n’a pas signalé un utilisateur invalide ; ce n’est pas une preuve qu’un compte existe côté métier.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_valid) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_valid="user_valid", v_fail="is_failure"
| __error__=""
| v_fail="1"
| v_valid!=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant, puis Run queries.
2. Dans Options → Legend de la requête A, saisir `{{v_valid}}`.
3. Choisir la visualisation Pie chart.
4. Dans Pie chart options, choisir Pie type = Donut.
5. Dans Legend, afficher la liste, placer la légende à droite et ajouter Value et Percent si les options existent.
6. Dans Tooltip, choisir Single, puis survoler une part.
7. Si une catégorie très rare est difficile à voir, lire la valeur dans la légende : une part étroite n’est pas absente.

#### C. Vérifier avant de sauvegarder

Référence : Comparer à `failure_user_validity`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P15 — Échecs : utilisateur valide ou invalide`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P16 — Codes de déconnexion reçus

Objectif : Lire les motifs numériques de déconnexion annoncés par le protocole.

Limite : Les codes se lisent avec le texte du message ; un code ne désigne pas à lui seul une cause.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum by (v_code) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_type="event_type", v_code="disconnect_code"
| __error__=""
| v_type="disconnect_received"
| v_code!=""
[$__range]
))
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant sur chaque requête, puis Run queries.
2. Dans Legend de la requête, saisir `Code {{v_code}}`.
3. Choisir Bar gauge.
4. Orientation = Horizontal ; Calculation = Last * (dernière valeur non nulle).
5. Unit vide, Decimals = 0.
6. Agrandir l’aperçu si les libellés sont tronqués.
7. Trier mentalement ou dans les options de panneau si une option de tri est proposée ; ne pas conclure que la liste est exhaustive.

#### C. Vérifier avant de sauvegarder

Référence : Comparer à `disconnect_codes`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P16 — Codes de déconnexion reçus`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P17 — Analyse par IP

Objectif : Comparer volume, enregistrements canoniques, échecs, succès et part d’échec par IP.

Limite : Un taux de 100 % avec une ligne n’a pas le même poids que 100 % avec cent lignes. Le tableau est calculé sur les 5000 premières lignes renvoyées.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_ip="source_ip"
| __error__=""
| v_ip!=""
```

#### B. Configurer le calcul et la visualisation

1. Dans la requête A, choisir Type = Range puis régler Line limit sur `5000`.
2. Cliquer Run queries.
3. Choisir temporairement la visualisation Table ; repérer le champ qui contient le JSON, généralement Line.
4. Ouvrir l’onglet Transformations → Add transformation → Extract fields. Source = ce champ, Format = JSON, Replace all fields activé, Keep time désactivé.
5. Ajouter Group by : `source_ip` = Group by ; `record_id` = Calculate → Count ; `is_auth_record`, `is_failure`, `is_success` = Calculate → Total (nom interne `sum`).
6. Ajouter Add field from calculation : Mode = Binary operation ; premier champ `is_failure (sum)` ; opérateur `/` ; second champ `is_auth_record (sum)` ; Alias = `Part d’échec`. Si les noms de champs diffèrent dans votre version, copier ceux de l’aperçu.
7. Ajouter Organize fields : renommer `source_ip` en `IP`, `record_id (count)` en `Messages`, `is_auth_record (sum)` en `Canoniques`, `is_failure (sum)` en `Échecs`, `is_success (sum)` en `Succès`.
8. Ajouter Sort by : `Échecs`, ordre décroissant, puis Limit : 10.
9. Choisir Table. Dans Standard options → Unit, utiliser un override sur `Part d’échec` avec l’unité Percent (0.0–1.0) et deux décimales.
10. Pour une ligne dont Canoniques vaut 0, ne pas remplacer une valeur vide ou infinie par zéro ; lire plutôt Messages et Échecs.
11. Relire une ligne : Échecs / Canoniques doit redonner la part affichée.

#### C. Vérifier avant de sauvegarder

Référence : Comparer les premières lignes à `rows_by_ip_top10_failures`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P17 — Analyse par IP`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P18 — Analyse par utilisateur

Objectif : Même lecture, avec le nom d’utilisateur observé.

Limite : Les lignes sans nom d’utilisateur sont absentes de cette table, pas supprimées du total.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_user="user_name"
| __error__=""
| v_user!=""
```

#### B. Configurer le calcul et la visualisation

1. Dans la requête A, choisir Type = Range puis régler Line limit sur `5000`.
2. Cliquer Run queries.
3. Choisir temporairement la visualisation Table ; repérer le champ qui contient le JSON, généralement Line.
4. Ouvrir l’onglet Transformations → Add transformation → Extract fields. Source = ce champ, Format = JSON, Replace all fields activé, Keep time désactivé.
5. Ajouter Group by : `user_name` = Group by ; `record_id` = Calculate → Count ; `is_auth_record`, `is_failure`, `is_success` = Calculate → Total (nom interne `sum`).
6. Ajouter Add field from calculation : Mode = Binary operation ; premier champ `is_failure (sum)` ; opérateur `/` ; second champ `is_auth_record (sum)` ; Alias = `Part d’échec`. Si les noms de champs diffèrent dans votre version, copier ceux de l’aperçu.
7. Ajouter Organize fields : renommer `user_name` en `Utilisateur`, `record_id (count)` en `Messages`, `is_auth_record (sum)` en `Canoniques`, `is_failure (sum)` en `Échecs`, `is_success (sum)` en `Succès`.
8. Ajouter Sort by : `Échecs`, ordre décroissant, puis Limit : 10.
9. Choisir Table. Dans Standard options → Unit, utiliser un override sur `Part d’échec` avec l’unité Percent (0.0–1.0) et deux décimales.
10. Pour une ligne dont Canoniques vaut 0, ne pas remplacer une valeur vide ou infinie par zéro ; lire plutôt Messages et Échecs.
11. Relire une ligne : Échecs / Canoniques doit redonner la part affichée.

#### C. Vérifier avant de sauvegarder

Référence : Comparer les premières lignes à `rows_by_user_top10_failures`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P18 — Analyse par utilisateur`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P19 — Ports sources des enregistrements canoniques

Objectif : Distribution des ports sources par plages choisies.

Limite : Ce sont les ports côté client, pas les ports d’écoute du serveur ; les largeurs sont inégales, donc barres par catégories.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

Requête A — légende `0–1 023` :

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record", v_port="source_port"
| __error__=""
| v_auth="1"
| v_port!=""
| v_port>=0
| v_port<1024
[$__range]
))
```

Requête B — légende `1 024–32 767` :

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record", v_port="source_port"
| __error__=""
| v_auth="1"
| v_port!=""
| v_port>=1024
| v_port<32768
[$__range]
))
```

Requête C — légende `32 768–49 151` :

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record", v_port="source_port"
| __error__=""
| v_auth="1"
| v_port!=""
| v_port>=32768
| v_port<49152
[$__range]
))
```

Requête D — légende `49 152–65 535` :

```logql
sum (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_auth="is_auth_record", v_port="source_port"
| __error__=""
| v_auth="1"
| v_port!=""
| v_port>=49152
| v_port<65536
[$__range]
))
```

Après A, cliquer Add query pour créer B, C et D. Pour chacune, choisir Code et coller son bloc.

#### B. Configurer le calcul et la visualisation

1. Type = Instant sur chaque requête, puis Run queries.
2. Pour chaque requête, saisir dans Legend le libellé indiqué sous son bloc.
3. Choisir Bar gauge.
4. Orientation = Horizontal ; Calculation = Last * (dernière valeur non nulle).
5. Unit vide, Decimals = 0.
6. Agrandir l’aperçu si les libellés sont tronqués.
7. Trier mentalement ou dans les options de panneau si une option de tri est proposée ; ne pas conclure que la liste est exhaustive.

#### C. Vérifier avant de sauvegarder

Référence : Comparer aux quatre valeurs de `port_bins_canonical` ; une catégorie à zéro est possible.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P19 — Ports sources des enregistrements canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P20 — Suffixes des noms d’hôte distants

Objectif : Indice DNS pour les lignes qui mentionnent un nom d’hôte, jamais une géolocalisation.

Limite : Un suffixe de domaine ne prouve ni le pays ni l’identité de l’émetteur.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
topk(10,
sum by (v_tld) (count_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_tld="source_host_tld"
| __error__=""
| v_tld!=""
[$__range]
))
)
```

#### B. Configurer le calcul et la visualisation

1. Type = Instant sur chaque requête, puis Run queries.
2. Dans Legend de la requête, saisir `.{{v_tld}}`.
3. Choisir Bar gauge.
4. Orientation = Horizontal ; Calculation = Last * (dernière valeur non nulle).
5. Unit vide, Decimals = 0.
6. Agrandir l’aperçu si les libellés sont tronqués.
7. Trier mentalement ou dans les options de panneau si une option de tri est proposée ; ne pas conclure que la liste est exhaustive.

#### C. Vérifier avant de sauvegarder

Référence : Comparer à `hostname_tld_counts_top10`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P20 — Suffixes des noms d’hôte distants`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P21 — Répétitions résumées par sshd

Objectif : Additionner les répétitions annoncées dans « message repeated N times ».

Limite : Cette somme n’est pas ajoutée à F : elle sert à signaler des tentatives que le journal a résumées.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
sum(
  sum_over_time(
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_type="event_type", v_n="repeat_count"
| __error__=""
| v_type="message_repeat"
| v_n!=""
| unwrap v_n
| __error__=""
[$__range]
  )
) or vector(0)
```

#### B. Configurer le calcul et la visualisation

1. Dans les options de la requête A, choisir Type = Instant, pas Both ni Range.
2. Cliquer Run queries / Exécuter les requêtes.
3. Choisir la visualisation Stat.
4. Dans Value options → Calculation, choisir Last * / Dernière valeur non nulle. La requête renvoie déjà la valeur finale : il ne faut pas sommer une courbe.
5. Dans Standard options → Unit : laisser le champ Unit vide (nombre sans unité).
6. Dans Standard options → Decimals, saisir `0`.
7. Dans Stat styles, régler Graph mode sur None pour ne pas suggérer une série que la requête ne renvoie pas.
8. Laisser No data visible ; ne pas transformer une absence de données en zéro vert.

#### C. Vérifier avant de sauvegarder

Référence : R = `R_repeat_sum`.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P21 — Répétitions résumées par sshd`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P22 — Détail des échecs canoniques

Objectif : Revenir à la ligne source des échecs reconnus.

Limite : Le panneau affiche un extrait ; le nombre total est P03.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_fail="is_failure", v_type="event_type", raw="raw_line"
| __error__=""
| v_fail="1"
| line_format "{{.raw}}"
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, Line limit = 500, puis Run queries.
2. Choisir Logs.
3. Activer Time, Unique labels/Details et Wrap lines.
4. Désactiver la déduplication pendant l’investigation.
5. Développer une ligne : le texte affiché est le journal brut grâce à `line_format`, les champs extraits restent visibles dans les détails.
6. Ne pas utiliser le nombre de lignes affichées comme total : seul le compteur du panneau Stat correspondant sert de référence.

#### C. Vérifier avant de sauvegarder

Référence : Au plus 500 lignes affichées parmi F.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P22 — Détail des échecs canoniques`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P23 — Lignes non classées

Objectif : Inspecter ce que le classeur n’a pas reconnu.

Limite : Zéro est une valeur correcte. Ces lignes ne doivent pas être supprimées ni renommées pour faire coïncider les totaux.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_fail="is_failure", v_type="event_type", raw="raw_line"
| __error__=""
| v_type="other"
| line_format "{{.raw}}"
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, Line limit = 500, puis Run queries.
2. Choisir Logs.
3. Activer Time, Unique labels/Details et Wrap lines.
4. Désactiver la déduplication pendant l’investigation.
5. Développer une ligne : le texte affiché est le journal brut grâce à `line_format`, les champs extraits restent visibles dans les détails.
6. Ne pas utiliser le nombre de lignes affichées comme total : seul le compteur du panneau Stat correspondant sert de référence.

#### C. Vérifier avant de sauvegarder

Référence : Le nombre de lignes correspond à `other_unclassified_lines` ; zéro est une valeur correcte.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P23 — Lignes non classées`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P24 — Détail des alertes « POSSIBLE BREAK-IN »

Objectif : Lire les messages DNS/adresse qui ont déclenché P08.

Limite : Le message provient de sshd ; il ne remplace pas une analyse d’incident.

#### A. Ajouter une nouvelle visualisation

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` dans Dashboards.
2. Cliquer Edit / Modifier si le dashboard n’est pas en édition.
3. Vérifier la période qui contient la collecte, la valeur de la variable `lot` et l’absence de filtre temporaire global.
4. Cliquer Add / Ajouter → Visualization / Visualisation, ou directement Add visualization. Ne pas ouvrir la modification du panneau précédent.
5. Si Grafana demande une source, choisir `Loki-Formation` pour ouvrir l’éditeur.
6. Dans le sélecteur Data source de l’éditeur, choisir `${loki_ds}` si la variable est proposée ; sinon conserver `Loki-Formation`.
7. Dans la requête A, cliquer Code, sélectionner le texte initial et le remplacer par le bloc ci-dessous.

```logql
{job="defi13_openssh",format="json",lot="${lot}"}
| json v_fail="is_failure", v_type="event_type", raw="raw_line"
| __error__=""
| v_type=~"reverse_mapping|address_mismatch"
| line_format "{{.raw}}"
```

#### B. Configurer le calcul et la visualisation

1. Type = Range, Line limit = 500, puis Run queries.
2. Choisir Logs.
3. Activer Time, Unique labels/Details et Wrap lines.
4. Désactiver la déduplication pendant l’investigation.
5. Développer une ligne : le texte affiché est le journal brut grâce à `line_format`, les champs extraits restent visibles dans les détails.
6. Ne pas utiliser le nombre de lignes affichées comme total : seul le compteur du panneau Stat correspondant sert de référence.

#### C. Vérifier avant de sauvegarder

Référence : Au plus 500 lignes affichées parmi B.

Comparer sur la même période et avec le même lot. Si l’écart persiste, vérifier le lot, la période, Instant/Range et la limite de lignes avant de conclure à une perte. Les références viennent de votre préparation locale ; elles ne sont pas des mesures du dashboard tant que vous ne les avez pas lues.

#### D. Placer et enregistrer

1. Dans Panel options / Options du panneau, saisir le titre `P24 — Détail des alertes « POSSIBLE BREAK-IN »`.
2. Cliquer Apply / Appliquer, ou l’action de retour qui conserve le panneau.
3. Maintenir le clic sur l’en-tête ou la poignée du nouveau panneau, le glisser dans une zone libre puis relâcher.
4. Tirer le coin inférieur du panneau pour rendre valeurs, axes et légendes lisibles.
5. Cliquer Save dashboard / Enregistrer et confirmer.
6. Vérifier que les panneaux déjà créés sont toujours présents et n’ont pas été remplacés.


### P25 — Contrat de lecture

Objectif : Placer les définitions, limites et références dans le tableau de bord.

Limite : Le texte n’est pas une donnée Loki.

#### A. Générer le texte avec les vraies valeurs

Dans le terminal, depuis le dossier du défi :

```bash
python3 - <<'PY'
import json
from pathlib import Path
b = Path("preparation_defi13")
m = json.loads((b / "manifest.json").read_text(encoding="utf-8"))
r = json.loads((b / "reference_source.json").read_text(encoding="utf-8"))
print(f"""### Lire ce tableau de bord
- Source : Loghub OpenSSH_2k.log, SHA-256 {r['source_sha256']}.
- Lot Loki : {m['lot']}.
- Les lignes syslog ne contiennent pas d'année : le temps Loki est celui de la collecte, et P11/P12 lisent seulement l'heure écrite.
- N = {r['N_nonempty_lines']}, A = {r['A_canonical_records']}, F = {r['F_failures']}, S = {r['S_successes']}, B = {r['B_possible_break_in_lines']}.
- Une ligne n'est ni une session ni une personne ; une IP n'est pas un individu.
- Les messages PAM, déconnexions et répétitions ne sont pas ajoutés aux enregistrements canoniques.
- Le suffixe d'un nom d'hôte n'est pas une géolocalisation.
- Les tops, tables et logs affichent des extraits ; les compteurs Stat portent le total.""")
PY
```

#### B. Ajouter le panneau Text

1. Ouvrir `[D13] OpenSSH — diagnostic Loki` et cliquer Edit / Modifier.
2. Cliquer Add / Ajouter → Visualization / Visualisation, puis choisir la visualisation Text. Si une source est demandée, choisir Grafana / Built-in ou ne pas en choisir pour ce panneau.
3. Mode Markdown. Coller le texte généré par le terminal.
4. Dans Panel options / Options du panneau, saisir le titre `P25 — Contrat de lecture`.
5. Cliquer Apply / Appliquer.
6. Maintenir le clic sur l’en-tête du panneau, le glisser sous les contrôles ou en haut de la grille, puis agrandir sa largeur.
7. Cliquer Save dashboard / Enregistrer et vérifier que les autres panneaux sont toujours présents.


## 5. Assembler le dashboard

```text
Variables : Source Loki | Lot OpenSSH
P25 Contrat de lecture

P01 Lignes | P02 Canoniques | P03 Échecs | P04 Succès
P05 IP distinctes | P06 Part d’échec | P07 Sans IP | P08 BREAK-IN
P21 Répétitions résumées

P09 Collecte dans le temps, grande largeur
P10 Types d’événement | P15 Utilisateur valide ou invalide
P11 Messages par heure | P12 Échecs et succès par heure
P13 Top IP | P14 Top utilisateurs | P16 Codes de déconnexion
P17 Analyse par IP | P18 Analyse par utilisateur
P19 Ports sources | P20 Suffixes d’hôtes

P22 Détail des échecs, grande largeur
P23 Lignes non classées, grande largeur
P24 Détail des alertes BREAK-IN, grande largeur
```

1. Cliquer Edit / Modifier.
2. Repérer chaque panneau par son identifiant dans son titre.
3. Maintenir le clic sur son en-tête ou sa poignée, le déplacer dans la grille et relâcher.
4. Tirer le coin inférieur pour régler la taille ; donner plus de largeur aux tables, aux tops et aux logs.
5. Vérifier la variable `lot`, la période et l’absence de filtre temporaire.
6. Cliquer Save dashboard / Enregistrer, revenir à la liste des dashboards, rouvrir `[D13] OpenSSH — diagnostic Loki` et compter 25 panneaux.

## 6. Contrôler les valeurs

| Panneau | Contrôle |
|---|---|
| P01 | N |
| P02 à P04 | A, F, S ; F + S = A |
| P05 | U, avec la limite de séries Loki si l’erreur apparaît |
| P06 | F / A avec deux décimales |
| P07 | (N − I) / N |
| P08 et P24 | B ; P24 affiche au plus 500 lignes |
| P09 | pic ou fenêtres de collecte, sans valeur de référence unique |
| P10 | `event_type_counts` |
| P11 et P12 | `hour_counts`, F et S par heure |
| P13 et P14 | classements `top10_failure_ips` et `top10_failure_users` |
| P15 à P16 | `failure_user_validity` et `disconnect_codes` |
| P17 et P18 | premières lignes de `rows_by_ip_top10_failures` et `rows_by_user_top10_failures` |
| P19 | `port_bins_canonical` |
| P20 | `hostname_tld_counts_top10` |
| P21 | R |
| P22 | extrait des F échecs |
| P23 | `other_unclassified_lines`, zéro accepté |
| P25 | texte avec lot, empreinte et limites renseignés |

Si un panneau Stat est vide, vérifier d’abord le lot copié dans la variable, puis la période, puis le mode Instant. Ne pas relancer l’indexation pour corriger un écran vide.

## 7. Investigation guidée

1. Noter N, A, F, S et B.
2. Lire P10 pour repérer les types dominants.
3. Lire P13 et choisir l’IP la plus fréquente.
4. Dans Explore, remplacer le sélecteur par celui imprimé en partie 1 et ajouter un filtre sur cette IP :

```logql
{job="defi13_openssh",format="json",lot="VALEUR_REELLE_DU_LOT"}
| json v_ip="source_ip", raw="raw_line"
| __error__=""
| v_ip="IP_CHOISIE"
| line_format "{{.raw}}"
```

Remplacer les deux valeurs en majuscules par le lot affiché en partie 1 et par l’IP lue dans P13.

5. Lire les lignes dans l’ordre : message DNS, utilisateur invalide, échec, déconnexion.
6. Écrire une conclusion en quatre lignes : fait observé, périmètre, hypothèse, preuve manquante.
7. Ne pas écrire « attaque confirmée », « compte compromis » ou « pays d’origine » sans autre source.

## 8. Dépannage

| Symptôme | Action |
|---|---|
| Stat vide | Variable `lot`, période, type Instant ; tester `{job="defi13_openssh",format="json"}` dans Explore |
| Valeur `Infinity` ou vide dans un ratio | Un dénominateur vaut zéro ou n’a pas de série : lire A ou N |
| P05 signale trop de séries | Noter la limite de Loki ; ne pas augmenter les limites du serveur pendant le défi |
| Bar chart sans barres | Revenir à Table, vérifier Extract fields puis les noms exacts après Group by |
| Table avec des noms de colonnes différents | Utiliser les noms affichés dans l’aperçu pour Organize fields et le calcul binaire |
| Logs affichés en JSON | Vérifier `line_format "{{.raw}}"` en fin de requête |
| Dates inattendues | Le journal n’a pas d’année ; le temps Loki est celui de la collecte |
| Total supérieur à N | Double collecte ou ancien lot dans la sélection : vérifier `lot` |
| Total inférieur à N | Attendre la collecte, lire `journalctl -u alloy-defi13`, relancer le vérificateur |

## 9. Portée des vérifications

Les scripts de préparation et de vérification ont été testés localement avec des journaux au format syslog OpenSSH et des réponses Loki simulées. Le fichier OpenSSH_2k.log de Loghub n’était pas disponible pour ce test : le nombre de lignes classées `other` du fichier réel doit donc être lu dans `reference_source.json` avant la séance. Aucune ingestion Alloy, requête LogQL sur un serveur Loki ou manipulation Grafana n’a été exécutée pendant la rédaction.
