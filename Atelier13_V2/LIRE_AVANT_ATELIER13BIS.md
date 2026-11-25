# LIRE AVANT — Révision de l’atelier 13 bis pour le corpus access complet

## 1. Ce que cette révision remplace

Les documents principaux sont `ATELIER_13BIS_MODELE.md` et `GUIDE_60_REQUETES_EXPLORE_MODELE.md`. Ils ont été parcourus et réécrits pour analyser les access logs complets, et non les 29 records du scénario. Conserver une copie des anciens supports si l’extension synthétique est utile.

Le fichier joint analysé contient 102972 lignes non vides, pas 109203 ni 109230. Sa référence locale complète est dans `reference_access_fichier_joint.json`. Le nombre de votre fichier sur VM doit être recalculé, pas imposé à la main.

Le ZIP est une révision à utiliser avec le pack initial. Il ne réinstalle pas Alloy/Loki/Grafana et ne vide aucun stockage. Les fichiers de configuration et l’installateur Alloy du pack initial restent inchangés. Le jeu de logs complet n’est pas dupliqué dans ce ZIP : utiliser le fichier déjà fourni.

## 2. Séance déjà commencée : commencer ici

1. Copier les fichiers de révision dans le dossier du pack après sauvegarde des versions précédentes.
2. Ne pas relancer préparation, installation de collecte ou génération synthétique si vos données sont déjà chargées.
3. Suivre la section 0 de l’atelier : référence locale, nouveau contrôle de volumes, personnalisation, puis nouveau dashboard.
4. Le script `verifier_normalisation13bis.py` de cette révision remplace l’ancien script limité à 2000 logs. Le terminal reste le bon endroit pour l’exécuter.

```bash
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_normalisation13bis.py \
  --manifest preparation13bis.json --corpus corpus13bis \
  --source sources13bis/access_log \
  --output reference-normalisation13bis-corpus.json

python3 personnaliser_support_corpus13bis.py \
  --manifest preparation13bis.json \
  --reference reference-normalisation13bis-corpus.json \
  --output-dir supports13bis-corpus-complet
```

Si la sortie existe, choisir un autre nom et adapter la commande suivante. Ne pas supprimer des références ni des positions pour faire disparaître l’erreur.

## 3. Tableau des fichiers de cette révision

| Fichier | Rôle | Action du participant |
|---|---|---|
| `ATELIER_13BIS_MODELE.md` | Support complet révisé, reprise en cours et 24 panneaux clic par clic | Lire, puis utiliser la version personnalisée |
| `GUIDE_60_REQUETES_EXPLORE_MODELE.md` | 60 expressions réécrites avec références du fichier complet | Utiliser la version personnalisée dans Explore |
| `LIRE_AVANT_ATELIER13BIS.md` | Présente cette révision et les remplacements | Lire en premier |
| `preparer_corpus_access13bis.py` | Copie tout le fichier access et crée le manifeste sans prélèvement de cinq lignes | Première préparation seulement, pas pour rejouer une collecte existante |
| `normaliser_sources13bis.py` | Normalisation complète JSON/logfmt selon le schéma utilisé dans les requêtes | Nouvelle préparation seulement |
| `analyser_access13bis.py` | Calcule les comptes/références sur votre fichier réel, sans publication | Exécuter pour comparer votre source |
| `verifier_normalisation13bis.py` | Vérifie les volumes total/access dans JSON et logfmt par métriques Loki | Remplace l’ancien vérificateur |
| `personnaliser_support_corpus13bis.py` | Remplace NID et durée, produit deux documents et les requêtes résolues sans scénario | Remplace l’ancien personnaliseur pour ce parcours |
| `requetes_dashboard_corpus13bis.json` | Expressions des nouveaux panneaux | Lu par les scripts, ne pas importer comme logs |
| `requetes_explore_corpus13bis.json` | Index des 60 nouvelles recherches et références | Lu par le personnaliseur |
| `registre_panneaux_corpus13bis.json` | Titres, types et options des 22 panneaux de données, les deux textes étant ajoutés séparément | Lu par le constructeur |
| `construire_dashboard_corpus13bis.py` | Produit un JSON Grafana de secours de 24 panneaux | Facultatif, pas de publication API automatique |
| `reference_access_fichier_joint.json` | Statistiques recalculées sur le fichier joint et SHA-256 | Comparer avec votre propre référence |
| `references_codes_http.csv` | Comptes exacts par code dans le fichier joint | Vérifier les graphiques |
| `grille_panneaux_corpus13bis.csv` | Liste de validation des panneaux | Compléter pendant le TP |
| `validation_revision_corpus13bis.json` | Tests réellement effectués et limites | Lire pour préparer la séance |

## 4. Fichiers générés : ne pas les confondre

| Nom | Provenance | Usage |
|---|---|---|
| `sources13bis/sources-manifest.json` | Préparation des sources | Nombre/empreinte/provenance, pas preuve de livraison |
| `preparation13bis.json` | Normaliseur et tee | NID réel, access, per_format ; entrée du vérificateur |
| `reference-normalisation13bis-corpus.json` | Nouveau vérificateur | Volumes et bornes de collecte du lot |
| `supports13bis-corpus-complet/ATELIER_13BIS_PERSONNALISE.md` | Nouveau personnaliseur | Atelier avec NID/durée réels |
| `supports13bis-corpus-complet/GUIDE_60_REQUETES_EXPLORE_PERSONNALISE.md` | Nouveau personnaliseur | Guide prêt à copier dans Explore |
| `supports13bis-corpus-complet/requetes-explore/` | Nouveau personnaliseur | 60 fichiers E01.logql à E60.logql |
| `supports13bis-corpus-complet/requetes-api/` | Nouveau personnaliseur | Expressions sans variables Grafana pour curl |
| `livrables13bis-corpus/dashboard13bis-access-corpus.json` | Nouveau constructeur | Dashboard à importer manuellement si nécessaire |

## 5. Ce qui devient une extension et ne pilote plus le dashboard

- Les cinq films et les quatre contrôles restent hors du filtre source_dataset=access.
- `generer_scenario13bis.py` et son vérificateur concernent le scénario, pas le corpus complet.
- Les anciens constructeurs `construire_dashboard13bis.py` et `construire_exploration13bis.py`, les anciens modèles et l’ancien personnaliseur ciblent toujours le run synthétique : ne pas les utiliser pour le nouveau dashboard access.
- Ne pas employer reference13bis.json ou les variables run/phase pour la révision access.
- Les compteurs 30/29/27/2/1 n’ont aucun rôle dans les KPI du fichier complet.

## 6. Points de vigilance

Les références du fichier ne sont pas une certification de votre collecte. Le nouveau vérificateur prouve une égalité de volumes, pas l’identité de chaque événement en ligne. Les séries temporelles portent sur Time de collecte. P18 utilise des agrégations sur toutes les tailles connues ; les histogrammes/heatmaps client sont explicitement échantillonnés à 500 observations maximum.

Le JSON de secours n’envoie rien à Grafana. Aucune exécution Loki réelle, validation UI Grafana ou nouvelle livraison Alloy n’est revendiquée par les tests locaux du pack. La version Grafana n’était pas fournie ; les noms anglais des fonctions sont expliqués en français.
