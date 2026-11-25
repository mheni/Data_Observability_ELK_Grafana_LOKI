# Atelier 13 bis — LIRE AVANT : rôle des fichiers et ordre d’utilisation

Ce document remplace le `LIRE_AVANT_ATELIER13BIS.md` du pack. Il explique quels fichiers lire, quels scripts exécuter et quels fichiers seront générés pendant l’atelier.

## 1. Quel document ouvrir pour commencer ?

Le document principal est **`ATELIER_13BIS_MODELE.md`**.

Il contient la progression complète : préparation des fichiers, collecte Alloy vers Loki, contrôles de livraison, exploration dans Grafana, création des variables, construction de chaque panneau, organisation du dashboard et investigation.

Le mot `MODELE` ne signifie pas que le document est incomplet. Il indique que certains identifiants propres à la séance, comme `__RUN__` ou `__NID__`, seront remplacés lors de la personnalisation.

Après l’étape de personnalisation, poursuivre avec `supports13bis/ATELIER_13BIS_PERSONNALISE.md`. Pour les manipulations d’exploration, utiliser son compagnon `supports13bis/GUIDE_60_REQUETES_EXPLORE.md`.

## 2. Repères pour lire les tableaux

| Repère | Signification |
|---|---|
| À lire | Document destiné au participant ou au formateur |
| À exécuter | Script lancé au moment indiqué dans le support |
| Utilisé par un script | Fichier à conserver dans le pack, sans le lancer directement |
| Facultatif | Correction, secours, comparaison ou extension |
| Généré | Fichier créé pendant le TP ; il n’existe pas nécessairement dans le ZIP initial |

Conserver l’arborescence du pack. Certains scripts recherchent leurs modèles et requêtes dans le même dossier qu’eux. Ne pas copier uniquement un script dans un dossier vide.

## 3. Documents de l’atelier fournis dans le pack

| Fichier | Rôle | Quand l’utiliser ? | Usage |
|---|---|---|---|
| `LIRE_AVANT_ATELIER13BIS.md` | Présente le pack, les fichiers et leur ordre d’utilisation. La présente version remplace l’ancienne notice. | Avant de commencer. | À lire |
| `ATELIER_13BIS_MODELE.md` | Support principal, depuis les sources jusqu’au dashboard de 24 panneaux et au dashboard de détail. | Dès le début, puis pendant tout le TP. | À lire ; document principal |
| `GUIDE_60_REQUETES_EXPLORE_MODELE.md` | Guide des 60 manipulations LogQL dans Grafana Explore : code, période, exécution et lecture. Contient des marqueurs avant personnalisation. | Pour comprendre le parcours ; utiliser ensuite sa version personnalisée. | À lire ; complément du support principal |

## 4. Scripts de préparation et de chargement

| Fichier | Ce qu’il fait | Ce qu’il ne fait pas | Utilisation |
|---|---|---|---|
| `preparer_sources13bis.py` | Crée cinq références Apache et cinq films fictifs dans `sources13bis`. Accepte aussi deux fichiers d’entrée fournis par le participant. | Ne collecte rien et n’envoie rien à Loki. | À exécuter au début |
| `normaliser_sources13bis.py` | Lit les références et produit des copies JSON/logfmt. Avec `--with-controls`, ajoute les quatre contrôles de qualité. | Ne confirme pas la livraison dans Loki et ne convertit pas les nouvelles lignes en continu. | À exécuter après la préparation des sources |
| `installer_collecte13bis.sh` | Copie les fichiers dans les chemins de travail dédiés, installe la configuration et le service Alloy de TP, puis démarre la collecte. Refuse d’écraser des ressources existantes. | Ne réinstalle pas Loki/Grafana et ne remplace pas l’ancien service Alloy. | À exécuter une seule fois pour une nouvelle installation de TP, avec `sudo` |
| `verifier_normalisation13bis.py` | Interroge Loki et vérifie les copies JSON et logfmt du lot de normalisation, avec contrôle des IDs par format. Produit une référence temporelle. | Ne crée pas de données et ne corrige pas automatiquement une collecte défaillante. | À exécuter après le démarrage de la collecte |
| `generer_scenario13bis.py` | Ajoute les sondes et événements du scénario normal → incident → recovery. Produit le manifeste et une copie locale des événements JSON du scénario. | Ne répare pas les rejets précédents ; recovery n’est pas un backfill. | À exécuter après le contrôle de normalisation |
| `verifier_scenario13bis.py` | Vérifie dans Loki les trois chemins du scénario : sondes Apache, sondes CSV et événements JSON. Contrôle les IDs et les batches. | Ne construit pas de dashboard. | À exécuter avant les visualisations du scénario |

### Données utilisées par défaut

Les références autonomes sont explicitement synthétiques. Les films de démonstration ne sont pas présentés comme un extrait authentique de MovieLens, et les lignes Apache ne sont pas du trafic réel. L’atelier fonctionne sans télécharger un ancien corpus ni réaliser l’atelier 11.

## 5. Configuration Alloy et service de collecte

| Fichier fourni | Rôle | Faut-il le lancer directement ? |
|---|---|---|
| `config-atelier13bis.alloy` | Définit les quatre sources de fichiers : Apache, CSV, JSON et logfmt, ainsi que leur destination Loki. | Non. Le lire puis laisser l’installateur le copier et le valider. |
| `alloy-atelier13bis.service.in` | Modèle du service systemd. L’installateur remplace le marqueur du chemin du binaire Alloy. | Non. Ce n’est pas encore l’unité installée. |
| `installer_collecte13bis.sh` | Installe les fichiers précédents et démarre le service `alloy-atelier13bis`. | Oui, au moment indiqué, après vérification de la configuration. |

Le service utilise un répertoire de positions dédié. Ne pas supprimer cet état pour tenter de retrouver les compteurs d’un premier lancement. Ne pas concaténer cette configuration dédiée à la configuration Alloy des anciens ateliers.

## 6. Scripts pour les requêtes, les supports et les dashboards

| Fichier | Rôle précis | Fichiers produits | Statut dans le parcours |
|---|---|---|---|
| `construire_requetes_base13bis.py` | Prépare les exemples LogQL de base, adaptés au lot de normalisation. | Dossier `requetes13bis-base/` contenant des fichiers `.logql`. | Complément pratique ; suivre la commande du support |
| `construire_exploration13bis.py` | Prépare les 60 expressions d’Explore avec les vrais identifiants du lot et du run, sans variables de dashboard à remplacer à la main. | Dossier `exploration13bis/`, fichiers `.logql`, `index.json` et `BIBLIOTHEQUE_EXPLORE.md`. | À exécuter pour disposer des requêtes prêtes à copier |
| `personnaliser_support13bis.py` | Remplace les marqueurs dans les deux supports Markdown par les identifiants et la durée de la séance. | Dossier `supports13bis/`, deux documents personnalisés et `CONTEXTE.json`. | À exécuter après génération et contrôle du scénario |
| `construire_dashboard13bis.py` | Construit les définitions JSON des dashboards de secours et les requêtes de contrôle API résolues. | Dossier `livrables13bis/` : deux dashboards JSON et `requetes-api/`. | Facultatif pour construire manuellement ; utilisé pour le contrôle API proposé |
| `requetes-templates-atelier13bis.json` | Bibliothèque de 24 expressions utilisées par les constructeurs. Contient les variables prévues pour Grafana. | Rien par lui-même : il est lu par les scripts. | À conserver à côté des constructeurs ; ne pas exécuter |

### Ne pas confondre les trois constructions

```text
construire_exploration13bis.py
    → prépare des requêtes à copier dans Grafana Explore

personnaliser_support13bis.py
    → prépare des documents Markdown avec les identifiants de votre séance

construire_dashboard13bis.py
    → prépare des fichiers JSON à importer dans Grafana et des requêtes pour l’API Loki
```

Le script `construire_dashboard13bis.py` du pack ne publie pas automatiquement dans Grafana. Il ne contacte pas l’API Grafana pour créer le dashboard. Il faut importer les JSON générés si l’on choisit cette voie de secours.

Le parcours pédagogique principal reste la construction manuelle, panneau par panneau, dans l’interface Grafana.

## 7. Contrôles, grilles et extensions

| Fichier fourni | Utilité | Quand l’utiliser ? | Statut |
|---|---|---|---|
| `grille_panneaux13bis.csv` | Liste les 24 panneaux, leur type et les vérifications attendues. Permet de noter les résultats. | Pendant et après la création du dashboard. | À compléter |
| `references_validation13bis.csv` | Donne les totaux attendus selon le corpus et la phase : attendues, records, validées, rejetées, manquantes et complétude. | Lors du test des variables et de l’investigation. | À consulter |
| `validation_locale13bis.json` | Décrit les tests locaux effectués pendant la préparation du pack et les tests non exécutés sur une vraie stack. | Préparation formateur et qualification du pack. | À consulter ; ce n’est pas le rapport de votre serveur |
| `regle-alert-atelier13bis.logql` | Expression LogQL de l’exercice d’alerte sur la complétude movies. | Lors de l’extension Grafana Alerting. | Facultatif ; n’active aucune alerte à lui seul |
| `mapping-atelier13-events.json` | Mapping de la projection des événements du scénario dans Elasticsearch. | Seulement pour l’extension Elasticsearch. | Facultatif ; utilisé par le script de publication |
| `publier_elasticsearch13.py` | Publie la copie des événements JSON dans Elasticsearch lorsque vous l’exécutez explicitement avec les paramètres nécessaires. | Après le parcours Loki, si l’extension est retenue. | Facultatif ; ce n’est pas un script d’envoi vers Loki ou Grafana |

Les noms des deux fichiers de l’extension Elasticsearch conservent `13` dans ce pack. Ce n’est pas une erreur de commande : leur utilisation avec le scénario 13 bis est décrite dans le support.

## 8. Sous-dossier `references_autonomes/`

| Fichier | Contenu | Usage |
|---|---|---|
| `references_autonomes/access_log` | Exemple des cinq références Apache synthétiques. | Inspection ou comparaison ; le parcours recommandé régénère les références dans `sources13bis/`. |
| `references_autonomes/movies.csv` | Exemple des cinq films fictifs, avec en-tête CSV. | Inspection du CSV, notamment des virgules et guillemets. |
| `references_autonomes/sources-manifest.json` | Description et provenance synthétique de ces exemples. | Traçabilité et lecture. |

Ne pas confondre ce sous-dossier fourni avec `sources13bis/`, le dossier généré pendant votre propre séance.

## 9. Sous-dossier `originaux/` : comparaison seulement

Les versions précédentes sont conservées pour comprendre les adaptations. Ne pas les exécuter à la place des scripts 13 bis : certaines conservent les chemins ou labels des anciens ateliers.

| Fichier conservé | Origine et intérêt |
|---|---|
| `originaux/normaliser_sources11.py` | Ancien normaliseur de l’atelier 11. |
| `originaux/construire_requetes11.py` | Ancien constructeur des requêtes de base de l’atelier 11. |
| `originaux/generer_scenario13.py` | Ancien générateur du scénario de l’atelier 13. |
| `originaux/verifier_scenario13.py` | Ancien vérificateur du scénario. |
| `originaux/construire_dashboard13.py` | Ancien constructeur des dashboards. |
| `originaux/requetes-templates-atelier13.json` | Ancienne bibliothèque de requêtes. |
| `originaux/references-validation-atelier13.csv` | Anciennes références de validation. |
| `originaux/regle-alert-atelier13.logql` | Ancienne expression d’alerte. |
| `originaux/publier_elasticsearch13.py` | Version d’origine du script d’extension Elasticsearch. |
| `originaux/mapping-atelier13-events.json` | Mapping d’origine de cette extension. |

## 10. Fichiers générés pendant le TP : ne pas les chercher dans le ZIP initial

Les noms ci-dessous correspondent aux commandes du support. Si vous choisissez un autre `--output-dir`, le nom du dossier change.

| Fichier ou dossier généré | Produit par | À quoi sert-il ensuite ? |
|---|---|---|
| `sources13bis/access_log` et `sources13bis/movies.csv` | `preparer_sources13bis.py` | Références lues par le normaliseur puis copiées vers les chemins de collecte. |
| `sources13bis/sources-manifest.json` | `preparer_sources13bis.py` | Décrit les références préparées. |
| `corpus13bis/events.jsonl` et `corpus13bis/events.logfmt` | `normaliser_sources13bis.py` | Copies structurées installées pour la collecte. |
| `corpus13bis/manifest.json` | `normaliser_sources13bis.py` | Manifeste local du lot de normalisation. |
| `preparation13bis.json` | Sortie du normaliseur enregistrée avec `tee` | Rapport de préparation utilisé par les vérificateurs et constructeurs. |
| `reference-normalisation13bis.json` | `verifier_normalisation13bis.py` | Confirmation de livraison des deux formats et période à afficher dans Explore. |
| `scenario13bis/produced_events.jsonl` | `generer_scenario13bis.py` | Copie exacte des 38 événements JSON du scénario ; utilisable pour l’extension ES. |
| `scenario13bis/manifest13.json` | `generer_scenario13bis.py` | Manifeste local du scénario. Le nom interne `manifest13.json` est conservé. |
| `manifest-scenario13bis.json` | Sortie du générateur enregistrée avec `tee` | Manifeste accessible aux scripts de contrôle et de génération. |
| `reference13bis.json` | `verifier_scenario13bis.py` | Run vérifié et bornes réelles pour le dashboard et les requêtes. |
| `requetes13bis-base/` | `construire_requetes_base13bis.py` | Exemples LogQL de base personnalisés. |
| `exploration13bis/` | `construire_exploration13bis.py` | Les 60 requêtes résolues, leur index et leur bibliothèque de lecture. |
| `supports13bis/ATELIER_13BIS_PERSONNALISE.md` | `personnaliser_support13bis.py` | Document principal avec les vrais identifiants de la séance. |
| `supports13bis/GUIDE_60_REQUETES_EXPLORE.md` | `personnaliser_support13bis.py` | Guide Explore avec les identifiants personnalisés. |
| `supports13bis/CONTEXTE.json` | `personnaliser_support13bis.py` | Rappel du contexte utilisé pour les deux documents. |
| `livrables13bis/dashboard13bis-grafana.json` | `construire_dashboard13bis.py` | Dashboard principal de secours, à importer si nécessaire. |
| `livrables13bis/dashboard13bis-investigation.json` | `construire_dashboard13bis.py` | Dashboard de détail de secours, à importer si nécessaire. |
| `livrables13bis/requetes-api/` | `construire_dashboard13bis.py` | Expressions LogQL sans variables Grafana, prêtes pour les contrôles API. |
| `controle-completude13bis.json` | Commande `curl` du support | Réponse de contrôle du ratio de complétude. |

Les fichiers ne sont pas tous créés au début. Le script suivant peut avoir besoin de la sortie du précédent : respecter l’ordre du support.

## 11. Ordre d’exécution recommandé

| Étape | Action | Résultat à vérifier avant de poursuivre |
|---|---|---|
| 1 | Lire `ATELIER_13BIS_MODELE.md` et vérifier Loki, Grafana et Alloy. | Infrastructure disponible ; port local du collecteur dédié libre. |
| 2 | Exécuter `preparer_sources13bis.py`. | Cinq références access et cinq films. |
| 3 | Exécuter `normaliser_sources13bis.py` avec `--with-controls`. | 14 événements JSON et 14 logfmt préparés. |
| 4 | Exécuter l’installateur de collecte après lecture de sa configuration. | Service dédié actif, fichiers lisibles et destination Loki accessible. |
| 5 | Exécuter `verifier_normalisation13bis.py`. | Les deux formats et leurs IDs sont livrés ; référence créée. |
| 6 | Exécuter `generer_scenario13bis.py`. | Nouveau run et manifeste final présents. |
| 7 | Exécuter `verifier_scenario13bis.py`. | 15 sondes Apache, 14 CSV et 38 JSON contrôlés pour le run. |
| 8 | Générer les requêtes et personnaliser les supports. | Guide et expressions avec les bons identifiants. |
| 9 | Exécuter les recherches dans Grafana Explore. | Compréhension des champs, filtres, erreurs et métriques. |
| 10 | Construire les panneaux et les dashboards manuellement. | Panneaux enregistrés, filtres et valeurs contrôlés. |
| 11 | Générer les fichiers de secours et les expressions API si nécessaire. | JSON disponibles et contrôle API réalisé. |
| 12 | Réaliser l’alerte ou l’extension ES si elles sont retenues. | Résultat documenté sans confondre les périmètres. |

## 12. Valeurs de référence à ne pas confondre

| Périmètre | Valeur attendue | Signification |
|---|---:|---|
| Normalisation JSON | 14 | 5 access + 5 movies + 4 contrôles |
| Normalisation logfmt | 14 | Même lot sous une deuxième représentation |
| Scénario : sondes brutes | 29 | 15 Apache + 14 CSV |
| Scénario : événements JSON | 38 | 29 records + 6 batches + 3 heartbeats |
| Scénario : représentations livrées | 67 | 29 sondes brutes + 38 JSON ; pas 67 événements métier |
| Contrat du scénario | 30 | Références attendues |
| Records observés | 29 | Références effectivement tentées |
| Validées | 27 | Décisions de validation de la simulation |
| Rejetées | 2 | Titre manquant et ID dupliqué |
| Manquante avant lecture | 1 | Référence attendue non traitée |
| Complétude globale | 90 % | 27 validées / 30 attendues |

## 13. Questions fréquentes

### Dois-je lancer tous les fichiers Python ?

Non. Exécuter les scripts au moment indiqué. Les scripts de construction préparent des supports ou des objets de secours ; l’extension Elasticsearch reste facultative. Les versions dans `originaux/` servent à la comparaison.

### Le script de dashboard crée-t-il directement le dashboard dans Grafana ?

Non, pas dans ce pack. Il produit des fichiers JSON locaux. L’import dans Grafana reste une action séparée. Une publication par l’API Grafana demanderait une étape supplémentaire, non incluse dans ce script.

### Les modèles de requêtes JSON se chargent-ils dans Loki ?

Non. `requetes-templates-atelier13bis.json` contient du LogQL utilisé par les scripts, pas les logs à ingérer.

### Puis-je remplacer les fichiers de collecte par les fichiers d’un nouveau run ?

Ne pas écraser les fichiers suivis ni supprimer les positions. Le générateur ajoute des sondes et identifie chaque nouvel essai par un run distinct. Les dossiers de sortie existants sont refusés volontairement.

### Pourquoi certains fichiers du scénario demandent-ils sudo ?

Le générateur du scénario est lancé avec sudo pour écrire dans les copies de travail protégées. Sa copie locale peut donc être protégée aussi. Les rapports enregistrés avec `tee` servent aux scripts de lecture exécutés par le participant. Ne pas appliquer de droits ouverts à tous pour contourner le problème.

### Qu’est-ce qui a réellement été testé ?

Le pack a fait l’objet de tests locaux Python, de vérifications JSON/Bash, de contrôles des comptes et distributions, et de tests HTTP simulés. Le fichier `validation_locale13bis.json` distingue ces tests des validations non réalisées : vraie configuration Alloy, livraison Loki, compilation serveur du LogQL et manipulations dans Grafana.

Le formateur doit répéter le parcours sur les versions et paramètres de son laboratoire avant la séance.
