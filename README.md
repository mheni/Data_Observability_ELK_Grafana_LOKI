# Parcours de travaux pratiques — Elasticsearch, Logstash, Kibana et Python

## Introduction

Ce parcours de douze travaux pratiques accompagne progressivement les participants dans la découverte, la mise en œuvre et l’exploitation d’une chaîne de données avec Elasticsearch et l’Elastic Stack.

La progression commence par l’installation d’Elasticsearch et la manipulation de documents. Elle aborde ensuite la recherche, la concurrence, la modélisation et l’ingestion Python. Les participants découvrent alors Kibana pour explorer les données et construire des tableaux de bord, puis Logstash et Filebeat pour collecter et structurer les journaux web.

Le parcours se termine par un projet de clôture : collecter périodiquement les données de l’API JCDecaux avec Python, les indexer avec un mapping géographique et construire un dashboard Kibana interactif avec actualisation automatique.

Ce README sert de guide de lecture et de navigation. Les commandes, configurations, scripts et corrigés détaillés se trouvent dans chaque TP.

## Objectif général

À l’issue du parcours, les participants seront capables de construire une chaîne complète de collecte, transformation, indexation, recherche et visualisation des données, puis de la mettre en application dans un projet intégrateur.

## Objectifs pédagogiques

- Installer Elasticsearch et Kibana et vérifier leur fonctionnement.
- Utiliser une connexion authentifiée et la validation des certificats lorsque TLS est activé.
- Concevoir un index et un mapping adaptés aux données et aux recherches attendues.
- Manipuler des documents avec les API REST : création, lecture, mise à jour et suppression.
- Protéger des écritures concurrentes et interpréter un conflit de version.
- Comprendre l’analyse textuelle, les champs `text` et `keyword` et l’autocomplétion.
- Construire des recherches avec filtres, tris et pagination.
- Choisir une stratégie de modélisation : dénormalisation, objets imbriqués ou relation parent-enfant.
- Automatiser un chargement de données avec Python et contrôler les erreurs Bulk.
- Explorer les documents dans Discover et interroger Elasticsearch avec Dev Tools.
- Construire des visualisations Lens et un dashboard interactif.
- Collecter et parser des logs web avec Logstash et Filebeat, en distinguant leurs rôles.
- Réaliser un projet API → Python → Elasticsearch → Kibana avec données géographiques.

## Public cible

Administrateurs système, DevOps, data engineers, développeurs, consultants techniques et professionnels souhaitant acquérir une pratique de l’Elastic Stack.

## Prérequis

- Connaissances de base de Linux et de la ligne de commande.
- Compréhension des principes HTTP, JSON et des API REST.
- Notions de Python pour les TPs 07 et 12.
- Environnement de laboratoire disposant des ressources nécessaires aux services installés.
- Accès Internet pour les téléchargements et l’API JCDecaux.
- Droits d’administration sur les machines du laboratoire.
- Compte développeur et clé API JCDecaux pour le projet de clôture.

Les versions exactes, ressources matérielles et paramètres de connexion doivent être fixés par le formateur avant le démarrage. Conserver une combinaison compatible des composants Elastic et du client Python.

## Vue d’ensemble : le fil des TPs

```text
TP 01 — Installer Elasticsearch
   ↓
TP 02 — Définir un mapping et manipuler MovieLens
   ↓
TP 03 — Sécuriser les mises à jour concurrentes
   ↓
TP 04 — Comprendre la recherche plein texte et les analyseurs
   ↓
TP 05 — Construire un moteur de recherche
   ↓
TP 06 — Modéliser les relations entre documents
   ↓
TP 07 — Charger des données avec Python
   ↓
TP 08 — Installer Kibana et explorer les données
   ↓
TP 09 — Construire des visualisations et dashboards Lens
   ↓
TP 10 — Ingérer, parser et enrichir les logs avec Logstash
   ↓
TP 11 — Collecter les logs avec Filebeat et comparer les approches
   ↓
TP 12 — Réaliser le projet de clôture JCDecaux
```

Les TPs 01 à 07 constituent le socle Elasticsearch. Les TPs 08 et 09 transforment les données en outils d’exploration et de visualisation. Les TPs 10 et 11 complètent la chaîne d’ingestion. Le TP 12 mobilise les acquis dans un projet autonome.

## Programme détaillé

### TP 01 — Installer et prendre en main Elasticsearch sécurisé sur Ubuntu

**Objectif :** disposer d’une instance de laboratoire opérationnelle et comprendre les premières vérifications d’exploitation.

- Préparer Ubuntu et les paramètres système nécessaires.
- Installer Elasticsearch depuis le dépôt officiel.
- Configurer un environnement mono-nœud.
- Démarrer et contrôler le service.
- Tester l’API, l’authentification et la connexion HTTPS.
- Réaliser les premières opérations sur les documents.

**Résultat attendu :** une instance accessible et une checklist de validation complétée.

**Lien avec la suite :** environnement commun aux ateliers d’indexation et de recherche.

### TP 02 — MovieLens : mapping, documents et chargement Bulk

**Objectif :** transformer des métadonnées de films en documents Elasticsearch structurés.

- Explorer les fichiers du jeu MovieLens.
- Définir les types de champs et créer un mapping explicite.
- Préparer les données pour l’API Bulk.
- Créer, lire, modifier et supprimer un film.
- Vérifier les volumes et les erreurs d’import.

**Résultat attendu :** un index de films exploitable pour les exercices de recherche.

**Lien avec la suite :** fournit le contexte métier et les données des ateliers suivants.

### TP 03 — Gérer la concurrence avec Elasticsearch

**Objectif :** comprendre et éviter les pertes de mises à jour entre clients concurrents.

- Observer `_seq_no` et `_primary_term`.
- Réaliser une écriture conditionnelle.
- Reproduire et interpréter un conflit HTTP 409.
- Incrémenter un compteur avec un script Painless.
- Étudier les usages et limites de `retry_on_conflict`.

**Résultat attendu :** une démonstration reproductible de conflit et une mise à jour scriptée contrôlée.

**Lien avec la suite :** apporte les bases d’une application qui modifie des données en parallèle.

### TP 04 — Recherche plein texte, analyseurs et champs keyword

**Objectif :** comprendre comment le mapping et l’analyse influencent les résultats de recherche.

- Distinguer `text`, `keyword` et les multi-champs.
- Observer les tokens avec `_analyze`.
- Comparer `match`, `operator: and` et `match_phrase`.
- Utiliser `minimum_should_match`.
- Combiner recherche textuelle et filtres exacts.

**Résultat attendu :** des requêtes dont le comportement est expliqué à partir des champs et des tokens.

**Lien avec la suite :** prépare les fonctionnalités d’un moteur de recherche plus complet.

### TP 05 — Construire un moteur de recherche avec Elasticsearch

**Objectif :** assembler recherche, filtres, tri, pagination et autocomplétion.

- Construire des requêtes booléennes et des recherches de phrase.
- Trier sur des champs numériques et des sous-champs `keyword`.
- Utiliser `from`/`size`, puis PIT et `search_after`.
- Tester la tolérance aux fautes de frappe.
- Mettre en œuvre `search_as_you_type`.

**Résultat attendu :** un ensemble de requêtes réutilisables pour une interface de recherche de films.

**Lien avec la suite :** relie le mapping aux besoins fonctionnels d’une application.

### TP 06 — Modéliser les données et les relations

**Objectif :** choisir une représentation adaptée aux accès et aux cycles de vie des documents.

- Comparer dénormalisation, `nested` et relation parent-enfant.
- Définir une relation `franchise → film` avec un champ `join`.
- Indexer les enfants avec le routage approprié.
- Utiliser `parent_id`, `has_parent` et `has_child`.
- Discuter les limites et coûts du modèle choisi.

**Résultat attendu :** une relation fonctionnelle et une justification du choix de modélisation.

**Lien avec la suite :** encourage à concevoir le modèle avant d’industrialiser l’ingestion.

### TP 07 — Chargement massif dans Elasticsearch avec Python

**Objectif :** automatiser un import CSV avec des scripts lisibles, relançables et contrôlés.

- Préparer un environnement virtuel Python.
- Configurer le client Elasticsearch et la connexion sécurisée.
- Créer les mappings avant l’import.
- Lire les CSV avec des générateurs.
- Utiliser `streaming_bulk` et contrôler chaque résultat.
- Vérifier les films, notes et tags importés.

**Résultat attendu :** des scripts d’import et des compteurs de réussite/erreur vérifiables.

**Lien avec la suite :** les données importées deviennent explorables dans Kibana ; les principes Python sont réutilisés au TP 12.

### TP 08 — Kibana : installation, Discover, Data Views et Dev Tools

**Objectif :** utiliser Kibana comme interface d’exploration et d’interrogation.

- Installer Kibana et le connecter à Elasticsearch.
- Vérifier le service et diagnostiquer l’accès web.
- Créer des Data Views avec ou sans champ temporel.
- Explorer les données dans Discover.
- Utiliser KQL, les filtres et les recherches sauvegardées.
- Exécuter des requêtes REST dans Dev Tools.
- Introduire la distinction entre KQL, Query DSL et ES|QL.

**Résultat attendu :** des Data Views fonctionnelles et une investigation sauvegardée.

**Lien avec la suite :** prépare les visualisations et les tableaux de bord.

### TP 09 — Kibana : dashboards et visualisations Lens

**Objectif :** construire une vue synthétique et interactive des événements applicatifs.

- Définir les questions auxquelles doit répondre le dashboard.
- Créer des métriques, séries temporelles, barres et tableaux agrégés.
- Calculer un taux d’erreurs avec une formule Lens.
- Ajouter des contrôles de service, niveau et durée.
- Organiser les panneaux et sauvegarder le dashboard.
- Passer de la détection d’un problème au détail dans Discover.

**Résultat attendu :** un dashboard de supervision applicative avec filtres interactifs.

**Lien avec la suite :** les mêmes principes s’appliquent aux logs web et au projet géographique final.

### TP 10 — Logstash : installation, ingestion, Grok/Dissect et enrichissement

**Objectif :** construire progressivement un pipeline de traitement de logs Nginx/Apache.

- Installer Logstash et tester `stdin → stdout`.
- Lire un fichier de logs web.
- Comparer Dissect et Grok sur un format Combined.
- Convertir les types et interpréter l’horodatage.
- Ajouter des enrichissements et une classification des statuts HTTP.
- Configurer la sortie Elasticsearch et vérifier les événements dans Kibana.
- Rendre les échecs de parsing visibles.

**Résultat attendu :** un pipeline validé et des événements HTTP structurés et interrogeables.

**Lien avec la suite :** fournit une référence pour comparer le traitement explicite Logstash aux modules Filebeat.

### TP 11 — Filebeat : installation, ingestion et parsing de logs Apache/Nginx

**Objectif :** mettre en place une collecte légère de fichiers de logs et expliquer sa complémentarité avec Logstash.

- Installer Filebeat et configurer la connexion Elasticsearch.
- Activer et adapter le module web retenu.
- Charger les assets et pipelines nécessaires.
- Tester la configuration et démarrer la collecte.
- Explorer les champs parsés et vérifier l’arrivée de nouvelles lignes.
- Comparer la sortie directe Elasticsearch et l’architecture via Logstash.

**Résultat attendu :** une collecte continue fonctionnelle et un choix d’architecture argumenté.

**Lien avec la suite :** complète la compréhension des stratégies d’ingestion, avant le projet autonome par API.

### TP 12 — Projet de clôture : API JCDecaux, Python, Elasticsearch et Kibana

**Objectif :** réaliser une chaîne de données géographiques actualisée périodiquement.

- Obtenir une clé API et découvrir les contrats disponibles.
- Inspecter la réponse JSON des stations.
- Créer un mapping avec `station.location` de type `geo_point` avant l’indexation.
- Collecter, valider et transformer les données avec Python.
- Indexer les observations avec l’API Bulk et planifier la collecte.
- Construire une carte des stations et une représentation thermique.
- Ajouter des indicateurs Lens et des contrôles interactifs.
- Configurer l’actualisation automatique du dashboard.
- Distinguer l’historique des observations du dernier état connu de chaque station.

**Résultat attendu :** une démonstration API → Python → Elasticsearch → Kibana, accompagnée d’une note d’architecture et de preuves de validation.

**Livrables du projet :** mapping, script Python, planification, dashboard, contrôles d’ingestion et note de synthèse.

## Jeux de données et continuité pédagogique

| Bloc | Données | Finalité |
|---|---|---|
| TPs 02 à 07 | Films, franchises, notes et tags ; jeux de démonstration isolés | Comprendre indexation, recherche, modélisation et import Python |
| TPs 08 et 09 | Logs applicatifs de démonstration ; index MovieLens disponibles | Explorer, investiguer et visualiser |
| TPs 10 et 11 | Logs d’accès web Apache/Nginx | Comparer parsing explicite et collecte standardisée |
| TP 12 | Stations JCDecaux, coordonnées et disponibilités | Intégrer les acquis dans un projet géographique périodique |

Les index de laboratoire peuvent être distincts d’un TP à l’autre. Vérifier systématiquement le nom d’index, le mapping, le volume attendu et la Data View avant un exercice. La progression est conceptuelle : tous les TPs ne partagent pas un unique index.

## Méthode de travail

Chaque TP doit être parcouru dans l’ordre suivant :

1. Lire l’objectif et les prérequis.
2. Préparer les fichiers, variables et jeux de données.
3. Exécuter les commandes ou suivre les manipulations d’interface.
4. Comparer le résultat observé au résultat attendu.
5. Expliquer ce qui a été réalisé et pourquoi.
6. Effectuer les points de contrôle.
7. Diagnostiquer les écarts avec la section Dépannage.
8. Réaliser le défi final avant de consulter son corrigé.
9. Conserver les livrables utiles au TP suivant.

La réussite ne se limite pas à obtenir un service démarré ou un graphique visible : le participant doit pouvoir expliquer les champs, les requêtes, les flux et les vérifications effectuées.

## Convention d’environnement

Les ateliers utilisent, selon les cas, les variables suivantes :

```bash
export ES_URL='https://localhost:9200'
export ES_CA='/chemin/vers/http_ca.crt'
```

Le secret Elasticsearch doit être fourni par un mécanisme adapté au laboratoire. Le TP 12 ajoute une clé API JCDecaux et un nom de contrat. Ne jamais publier les valeurs des secrets.

Vérifier également :

- les versions exactes des composants ;
- les ports disponibles et l’absence de conflit entre services locaux et conteneurs ;
- la lisibilité des certificats par l’utilisateur ou le service concerné ;
- les droits de lecture des fichiers de logs ;
- le fuseau horaire et la période sélectionnée dans Kibana ;
- la présence des modèles d’index et pipelines requis avant l’ingestion.

## Précautions importantes pour le formateur

Ces points doivent être vérifiés dans les supports et configurations avant une session :

- **TP 03 :** dans une mise à jour scriptée, placer les modifications souhaitées dans le script ; ne pas compter sur un bloc `doc` envoyé en parallèle du script. Dans une requête curl JSON standard, conserver le code `source` sur une seule ligne ou échapper correctement les retours à la ligne.
- **TP 05 :** pour `search_after`, recopier le tableau `sort` complet du dernier résultat, y compris la valeur technique ajoutée lors d’une recherche avec PIT. Réutiliser le dernier identifiant PIT retourné.
- **TP 06 :** conserver le routage parent pour les enfants. Une mise à jour avec une valeur identique peut produire `noop` ; cela n’est pas un échec.
- **TP 07 :** fixer une version de client Python compatible avec le serveur. Utiliser des chemins de scripts explicites et des identifiants déterministes adaptés à chaque fichier, sans collision entre tags distincts.
- **TP 09 :** le jeu initial du TP 08 contient cinq événements : deux INFO, un WARN et deux ERROR. Le taux d’erreurs global attendu est donc 40 %. Une table Lens est agrégée ; utiliser une recherche Discover sauvegardée pour afficher les messages document par document.
- **TP 10 :** ne pas laisser tous les fichiers de test actifs simultanément dans un même `conf.d`. Isoler les pipelines ; ne pas lancer le service et une instance manuelle avec le même répertoire de données. Les secrets définis pour systemd ne sont pas automatiquement disponibles dans une exécution manuelle. Conserver l’événement brut en cas d’échec de parsing.
- **TP 11 :** vérifier l’utilisateur réel du service Filebeat ; ne pas supposer qu’un compte ou groupe `filebeat` existe. Le certificat de Kibana peut différer de celui d’Elasticsearch. Vérifier la commande explicite de chargement des pipelines du module avec la version utilisée.
- **TP 12 :** éviter de sommer plusieurs snapshots d’une même station pour représenter un état courant. Utiliser de préférence un index courant à identifiant stable pour les cartes et KPI, et un index historique pour les tendances. Une heat map historique représente des observations cumulées, pas automatiquement le dernier état des stations.

Cette liste signale des vérifications et corrections à reporter dans les supports détaillés ; elle ne signifie pas que les fichiers de TP existants ont été automatiquement modifiés.

## Validation des acquis

| Jalon | Critère de réussite |
|---|---|
| Après TP 01–02 | Instance accessible, mapping connu, documents créés et recherchés |
| Après TP 03–05 | Conflit expliqué, analyse textuelle observée, recherche et pagination maîtrisées |
| Après TP 06–07 | Modèle argumenté, import Python contrôlé et relançable |
| Après TP 08–09 | Exploration sauvegardée et dashboard interactif utilisable |
| Après TP 10–11 | Collecte continue vérifiée, parsing contrôlé, choix Filebeat/Logstash expliqué |
| Après TP 12 | Projet bout en bout démontré avec géolocalisation, collecte périodique et visualisations cohérentes |

## Organisation suggérée des livrables

```text
parcours-elastic/
├── README.md
├── tp01-installation-elasticsearch/
├── tp02-mapping-movielens/
├── tp03-concurrence/
├── tp04-recherche-plein-texte/
├── tp05-moteur-recherche/
├── tp06-modelisation/
├── tp07-python-bulk/
├── tp08-kibana-exploration/
├── tp09-kibana-lens-dashboards/
├── tp10-logstash/
├── tp11-filebeat/
└── tp12-projet-jcdecaux/
```

Cette arborescence est une proposition de rangement, pas un inventaire de fichiers fournis avec ce README. Chaque dossier peut contenir le support du TP, les configurations, scripts, exemples, corrigés et preuves de validation. Aucun fichier de secrets ne doit être versionné.

## Limites du parcours

Le parcours construit un socle pratique de recherche, ingestion et visualisation. Il ne remplace pas un parcours complet d’administration de production : cluster multi-nœud, dimensionnement, rétention, sauvegardes/restauration, haute disponibilité et sécurité avancée peuvent faire l’objet d’ateliers complémentaires.

La recherche vectorielle, sémantique et hybride constitue également un prolongement possible ; elle ne fait pas partie des douze TPs présentés ici.
