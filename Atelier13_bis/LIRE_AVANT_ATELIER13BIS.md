# LIRE AVANT — Atelier 13 bis : access logs, Loki et Grafana

## 1. Document principal

Ouvrir `ATELIER_13BIS.md`. Il décrit toutes les étapes : préparation du fichier complet, configuration de collecte Alloy, livraison dans Loki, Explore, LogQL, construction des 24 panneaux et dashboard de détail.

Le fichier fourni est `donnees/access_log_actualise` : nom sans accent et sans extension. Il contient 102972 lignes non vides. Il est inclus dans le ZIP ; aucun téléchargement de corpus n’est nécessaire.

Le dossier contient les fichiers du TP. La VM doit disposer de Python 3, Loki, Grafana, du binaire Alloy et du compte/groupe système alloy. Le service de TP est dédié ; il n’efface aucun stockage Loki.

## 2. Ordre des commandes

Ouvrir un terminal dans le dossier Atelier_13bis, puis suivre le support, sans lancer les scripts depuis un dossier vide :

```bash
python3 preparer_sources13bis.py \
  --source donnees/access_log_actualise --output-dir preparation13bis

sudo bash installer_collecte13bis.sh preparation13bis

export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_loki13bis.py \
  --manifest preparation13bis/manifest.json --output reference13bis.json

python3 generer_livrables13bis.py \
  --manifest preparation13bis/manifest.json --reference reference13bis.json \
  --output-dir livrables13bis
```

Le contrôle doit réussir avant de générer les supports personnalisés. Les dossiers de sortie et ressources système existants sont refusés pour éviter des écrasements ; ne pas effacer des positions de lecture pour contourner une erreur.

## 3. Tableau des fichiers fournis

| Fichier | Rôle | Utilisation |
|---|---|---|
| `ATELIER_13BIS.md` | Support principal, terminal puis clics dans Grafana, panneau par panneau | À lire et suivre |
| `GUIDE_60_REQUETES_EXPLORE.md` | Guide des 60 recherches, périodes, modes et références | Utiliser ensuite sa copie personnalisée |
| `LIRE_AVANT_ATELIER13BIS.md` | Notice et tableau des fichiers | À lire en premier |
| `donnees/access_log_actualise` | Corpus Apache complet | Lu par la préparation ; ne pas modifier pour remplir un graphique |
| `preparer_sources13bis.py` | Prépare toutes les lignes en brut, JSON et logfmt, manifeste et références | Exécuter sans sudo |
| `config13bis.alloy.in` | Modèle des trois sources et du writer Loki ; le lot est inséré par l’installateur | Lire, ne pas exécuter comme Python |
| `alloy-atelier13bis-access.service.in` | Modèle d’unité systemd du collecteur de TP | Utilisé par l’installateur |
| `installer_collecte13bis.sh` | Installe les fichiers, valide la configuration et démarre le collecteur | Exécuter avec sudo bash après les prérequis |
| `verifier_loki13bis.py` | Compte chaque représentation côté Loki et compare les statuts JSON à la source | Exécuter après installation ; aucune limite de téléchargement à 2000 logs |
| `generer_livrables13bis.py` | Produit supports personnalisés, requêtes résolues et JSON Grafana | Exécuter après succès du contrôle |
| `requetes_dashboard13bis.json` | Expressions des panneaux, avec variable Grafana lot | Lu par le générateur ; ce n’est pas un fichier de données à charger |
| `requetes_explore13bis.json` | Index des 60 expressions et références | Lu par le générateur |
| `registre_panneaux13bis.json` | Titres, types, unités et contrôles des 22 panneaux de données | Lu par le générateur ; deux textes sont ajoutés séparément |
| `references/reference_source_fournie.json` | Mesures locales et empreinte du fichier fourni | Comparer aux mesures de la préparation |
| `references/codes_http.csv` | Tableau des 11 codes HTTP présents | Contrôler le graphique des codes |
| `GRILLE_PANNEAUX.csv` | Liste des 24 panneaux à valider | À compléter pendant le TP |
| `VALIDATION_FORMATEUR.json` | Tests exécutés localement et opérations non exécutées sur une stack réelle | Préparation formateur |
| `SHA256SUMS.txt` | Empreintes des fichiers du dossier, sauf ce fichier lui-même | Contrôle d’intégrité après transfert |

## 4. Fichiers générés pendant le TP

| Fichier ou dossier | Produit par | Fonction |
|---|---|---|
| `preparation13bis/access_log` | Préparation | Copie des lignes Apache non vides à collecter |
| `preparation13bis/events.jsonl` | Préparation | Une ligne JSON par accès |
| `preparation13bis/events.logfmt` | Préparation | Même population en logfmt |
| `preparation13bis/manifest.json` | Préparation | Lot, nombre attendu, empreinte et fichiers |
| `preparation13bis/reference_source.json` | Préparation | Statistiques recalculées sur la source utilisée |
| `reference13bis.json` | Vérificateur | Comptes Loki confirmés et période réelle à utiliser |
| `livrables13bis/ATELIER_13BIS_PERSONNALISE.md` | Générateur | Support avec le lot et les bornes de séance |
| `livrables13bis/GUIDE_60_REQUETES_EXPLORE_PERSONNALISE.md` | Générateur | Guide Explore prêt à copier, sans marqueur à remplacer |
| `livrables13bis/requetes-explore/` | Générateur | 60 fichiers E01.logql à E60.logql |
| `livrables13bis/requetes-api/` | Générateur | Expressions sans variable Grafana, utilisables par curl |
| `livrables13bis/dashboard13bis.json` | Générateur | JSON de secours du dashboard principal |
| `livrables13bis/dashboard13bis-detail.json` | Générateur | JSON de secours du dashboard par IP |
| `livrables13bis/CONTEXTE.json` | Générateur | Lot, empreinte, période et quantité attendue |

## 5. Ce qui charge les données et ce qui ne les charge pas

```text
preparer_sources13bis.py
    → crée les trois représentations locales, mais n’envoie rien à Loki

installer_collecte13bis.sh
    → installe/démarre Alloy, qui lit les fichiers et les envoie à Loki

verifier_loki13bis.py
    → lit les comptes et statuts depuis l’API Loki, sans créer de données

generer_livrables13bis.py
    → écrit les documents, requêtes et JSON de dashboards locaux
```

Les dashboards JSON ne sont pas publiés automatiquement. Leur import manuel dans Grafana est facultatif : la construction guidée dans l’interface reste le parcours principal.

## 6. Références et limites

- Attendu par format : 102972. Il s’agit des mêmes accès représentés trois fois, pas de trois populations différentes.
- Statuts : 2xx=91145, 3xx=8909, 4xx=2670, 5xx=248.
- Tailles connues=67987, absentes=34985 ; les absences ne sont pas des zéros.
- Méthodes non extraites=267 ; leurs lignes restent dans le total.
- Les timestamps Loki correspondent à la collecte ; la date Apache est un champ de contenu.
- Le contrôle compare volumes et distribution HTTP, pas chaque ID en ligne.
- P18 porte sur toutes les tailles connues ; les tableaux, l’histogramme et la heatmap d’investigation affichent des extraits limités.
- La configuration fournie vise Loki local mono-tenant non authentifié. Toute adaptation TLS, secrets ou tenant est à préparer par le formateur avant la séance.
- Les tests locaux ne sont pas une validation de livraison réelle, de compilation LogQL ou de clics dans votre version Grafana.
