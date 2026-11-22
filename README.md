# Formation Data Observability — Elasticsearch, Kibana, Grafana Alloy, Loki et Grafana

## Présentation

Ce parcours de 13 ateliers apprend à ingérer, structurer, rechercher et exploiter des données, puis à analyser les événements techniques qui permettent d’observer le fonctionnement d’un système d’information.

Il associe deux démarches complémentaires :

1. Rechercher et analyser des données indexées avec Elasticsearch et Kibana.
2. Collecter et analyser des logs, construire des indicateurs et investiguer des anomalies avec Grafana Alloy, Loki et Grafana.

Le choix de deux jeux de données — un catalogue de films MovieLens et un fichier d’access logs — rend cette distinction concrète. Les mêmes références sont réutilisées au fil des ateliers pour concentrer l’apprentissage sur les méthodes et les outils plutôt que sur la découverte permanente de nouveaux corpus.

La finalité est de relier données, événements et indicateurs pour diagnostiquer un incident, en comprenant ce qui est réellement observé, avec quelles limites et sous quelles conditions de sécurité.

## Objectifs du parcours

À l’issue de la formation, les participants doivent savoir :

- Installer et administrer l’environnement de laboratoire sur Ubuntu.
- Comprendre les rôles d’Elasticsearch, Logstash, Kibana, Alloy, Loki et Grafana.
- Définir des mappings, analyseurs et modèles de documents adaptés à la recherche.
- Charger des données par lots et traiter les erreurs d’ingestion.
- Gérer les mises à jour concurrentes et comprendre le contrôle de version optimiste.
- Construire des recherches plein texte, filtres, agrégations, tris et paginations.
- Explorer les données et construire un dashboard interactif dans Kibana.
- Configurer une collecte de fichiers avec Alloy et expliquer sa configuration.
- Interroger Loki avec ou sans l’interface Grafana.
- Extraire des champs, vérifier leur présence et contrôler les erreurs de parsing/conversion.
- Produire des comptages, débits, ratios et agrégations numériques avec LogQL.
- Construire dans Grafana des KPI, chronologies, histogrammes, heatmaps, tables et vues d’investigation.
- Suivre volume, qualité, complétude, fraîcheur et distribution sur un périmètre explicite.
- Corréler des événements entre Loki et Elasticsearch à l’aide d’identifiants communs.
- Distinguer un signal d’alerte, une hypothèse de diagnostic et une preuve de cause racine.

## Public et prérequis

### Public

Data engineers, data analysts, développeurs, administrateurs systèmes, ingénieurs DevOps/SRE et équipes impliquées dans l’exploitation des pipelines de données.

### Prérequis

- Utiliser un terminal Linux et comprendre fichiers, permissions et services.
- Connaître les bases HTTP, JSON et des API REST.
- Comprendre les notions élémentaires de données structurées et de recherche.
- Pouvoir exécuter des commandes Python et lire un script simple.
- Disposer d’un accès SSH et de droits administratifs sur une VM de formation dédiée.

Le programme initial est prévu sur quatre jours. Les durées détaillées, extensions et temps d’installation sont à ajuster au groupe ; préparer les VM, paquets et certificats en amont évite de réduire les temps d’investigation et de restitution.

## Pourquoi utiliser MovieLens et des access logs ?

### MovieLens : rechercher des données métier indexées

Le fichier movies.csv fournit un catalogue compréhensible : identifiant du film, titre et genres. Il permet de travailler sur :

- la différence entre identifiant, texte analysé, valeur exacte et champ numérique ;
- le choix des mappings et des multi-fields ;
- la recherche par titre, la pertinence et la tolérance aux fautes ;
- les filtres et agrégations par catégorie ;
- l’import CSV et la gestion correcte des virgules/guillemets ;
- la modélisation et l’exploration d’un catalogue indexé.

Une ligne de catalogue décrit un film. Elle n’est pas automatiquement un événement technique, ni la preuve qu’un import s’est terminé avec succès.

Les jeux d’exemples et extensions de modélisation précisent leurs propres structures ; ne pas supposer que tous les champs pédagogiques existent directement dans le CSV d’origine.

### Access logs : comprendre les événements techniques et l’activité du SI

Le fichier access_log représente des requêtes HTTP journalisées. Il permet d’aborder :

- le temps et l’ordre des événements ;
- les méthodes, chemins, statuts HTTP et tailles de réponses ;
- la sélection des erreurs et l’investigation de leurs messages ;
- la collecte continue, les permissions et les positions de lecture ;
- la construction d’indicateurs de volume et de distribution ;
- la distinction entre activité réelle, absence de trafic et absence de collecte.

Une ligne de log est un événement observé. Elle ne prouve pas à elle seule la réussite d’une transaction métier ou la cause d’un incident.

### Deux finalités pédagogiques, pas deux frontières rigides

| Question | Catalogue MovieLens | Access logs et instrumentation |
|---|---|---|
| Que décrit-on ? | Des objets et leurs attributs | Des événements et observations techniques |
| Que cherche-t-on ? | Un film, un titre, une catégorie | Une requête, un statut, une période, un incident |
| Quel enjeu principal ? | Retrouver les bons documents et expliquer la pertinence | Reconstituer une situation et qualifier le fonctionnement du SI |
| Quelle temporalité ? | État du catalogue et mises à jour | Événements datés, collecte et fenêtres d’analyse |
| Quels outils sont approfondis ? | Elasticsearch et Kibana | Alloy, Loki et Grafana |

Cette séparation n’interdit pas d’indexer des logs dans Elasticsearch : l’atelier 08 l’utilise justement pour l’observabilité des access logs dans Kibana.

Inversement, lire movies.csv avec Alloy démontre un mécanisme de collecte de lignes ; cela ne transforme pas Loki en table relationnelle ou en moteur de recherche métier équivalent à l’index MovieLens.

Le choix du jeu de données permet donc de distinguer les usages, pas d’imposer une spécialisation absolue à chaque outil.

## Architecture et rôle des composants

```text
                          RECHERCHE ET ANALYSE DES DONNÉES

MovieLens / documents / access logs
                  │
                  ├──► scripts Python / API Bulk ──► Elasticsearch ──► Kibana
                  │
                  └──► Logstash, selon l’exercice ─► Elasticsearch


                          COLLECTE ET ANALYSE DES LOGS

access_log / movies.csv / instrumentation de laboratoire
                  │
                  ▼
              Grafana Alloy ──► Loki ◄── requêtes LogQL ── Grafana
                                  ▲
                                  └── curl / Python / LogCLI


                          FIL ROUGE DE CORRÉLATION

Événements instrumentés avec run_id / batch_id / event_id
                  ├──► Loki
                  └──► projection Elasticsearch
                               │
                               └──► diagnostic et vues Grafana complémentaires
```

| Composant | Rôle dans la formation |
|---|---|
| Elasticsearch | Stocker des documents indexés, les rechercher et les agréger |
| Logstash | Recevoir, transformer et transmettre les événements des exercices prévus |
| Kibana | Explorer les documents Elasticsearch et construire des dashboards |
| Grafana Alloy | Lire les fichiers, appliquer les traitements configurés et transmettre à Loki |
| Loki | Recevoir, conserver et interroger les logs organisés en flux étiquetés |
| Grafana | Explorer les données et présenter indicateurs, distributions et investigations |
| Python / curl | Préparer les données, tester les API et conserver des preuves hors interface |

Loki fonctionne dans le laboratoire comme un service indépendant de Grafana. Grafana n’est pas le stockage des logs. Les rôles internes de Loki — notamment distributor, ingester et querier — sont expliqués dans l’atelier 10 ; ils ne correspondent pas nécessairement à des services système séparés dans le déploiement monolithique du TP.

## Progression des ateliers 01 à 13

| Atelier | Thème | Objectifs et travaux principaux | Résultat / preuve attendue |
|---|---|---|---|
| 01 | Installation native et sécurisation de la plateforme | Installer Elasticsearch, Logstash, Kibana, Loki et Grafana ; configurer les accès locaux, certificats et services ; réaliser les premiers tests API | Services identifiés, connexions vérifiées et premiers événements retrouvés |
| 02 | Mappings, multi-fields et analyseurs | Choisir les types de champs ; distinguer recherche analysée et valeur exacte ; adapter la structure des documents et la recherche MovieLens | Mapping expliqué et recherches cohérentes avec les champs |
| 03 | Chargement en masse avec Python | Préparer les données et le format Bulk ; charger les jeux prévus ; examiner les résultats d’ingestion et erreurs par élément | Chargement contrôlé et volumes vérifiés, pas seulement un statut HTTP global |
| 04 | Concurrence et mises à jour | Comprendre le contrôle optimiste, les conflits et les mises à jour Painless ; raisonner sur les modifications concurrentes | Conflit reproduit puis traité sans écrasement silencieux |
| 05 | Recherche plein texte et pertinence | Comparer les recherches ; utiliser boosts, highlighting et fuzziness ; expliquer pourquoi un résultat apparaît | Requêtes argumentées et lecture de la pertinence sur les documents |
| 06 | Modélisation Elasticsearch | Comparer dénormalisation, nested et parent/child ; relier le modèle aux requêtes et contraintes de mise à jour | Choix de modèle justifié et limites connues |
| 07 | Requêtes, agrégations et pagination | Combiner filtres et recherche ; agréger, trier et paginer ; comprendre l’usage de PIT et de la pagination adaptée | Résultats reproductibles, périmètre explicite et agrégations vérifiées |
| 08 | Dashboard Kibana orienté Data Observability | Utiliser les access logs du parcours ; passer de Discover à Lens, puis à un dashboard interactif et à l’investigation | Tableau de bord trafic/erreurs, distributions et contrôles qualité/temps expliqués |
| 09 | Collecte avec Grafana Alloy | Réutiliser access_log et movies.csv ; expliquer config.alloy, sources, traitements, labels et destination ; vérifier ajouts et reprise | Configuration comprise et lignes réellement retrouvées dans Loki |
| 10 | Loki, architecture et premières requêtes LogQL | Localiser Loki et ses données ; comprendre écriture/lecture et composants ; sélectionner les flux et filtrer les lignes via Explore, curl, Python et éventuellement LogCLI | Même recherche reproduite avec et sans Grafana, sur un périmètre comparable |
| 11 | Parsers et qualité des champs | Parser Apache avec pattern/regexp ; traiter correctement le CSV ; comparer JSON/logfmt sur des copies dérivées ; gérer alias, champs absents et erreurs | Champs contrôlés, valeurs comparées et erreurs visibles plutôt que masquées |
| 12 | Métriques LogQL | Compter, calculer un débit et un ratio ; utiliser unwrap ; comparer somme, moyenne, maximum et quantile ; distinguer Instant/Range et zéro/absence | Indicateurs validés à un instant de référence et unités correctes |
| 13 | Dashboard Grafana et incident fil rouge | Construire KPI, histogrammes, heatmaps, tables et logs ; suivre normal/incident/recovery ; corréler les IDs avec Elasticsearch en extension ; définir une alerte d’exercice | Dashboard interactif, diagnostic fondé sur les événements et compte rendu des limites |

### Lecture du parcours en cinq étapes

1. Ateliers 01 à 03 : installer et maîtriser l’entrée des données.
2. Ateliers 04 à 07 : gérer les documents et interroger efficacement Elasticsearch.
3. Atelier 08 : transformer l’exploration en dashboard Kibana d’observabilité.
4. Ateliers 09 à 12 : collecter les fichiers, comprendre Loki et écrire des requêtes LogQL exploitables.
5. Atelier 13 : réunir indicateurs, visualisations, contrôles et preuves dans une investigation.

Les références de schémas, comptes et commandes restent celles de chaque support. Cette synthèse ne remplace pas les étapes de préparation ou les conditions des résultats attendus.

## Méthode pédagogique commune

Chaque atelier suit autant que possible la même logique :

```text
Objectif → données et prérequis → manipulation → résultat attendu
→ explication → point de contrôle → diagnostic → défi → livrable
```

Les dashboards des ateliers 08 et 13 suivent une progression particulière :

```text
Explorer les événements → valider les requêtes → créer les visualisations
→ assembler → ajouter les contrôles → investiguer → vérifier par l’API
```

Un dashboard prêt à importer est un corrigé ou une aide, pas une preuve de compréhension. Les participants doivent pouvoir expliquer une valeur et retrouver les événements qui la composent.

## Sécurité du laboratoire

### 1. Environnement dédié et périmètre maîtrisé

- Utiliser une VM de formation dédiée, locale ou hébergée dans le cloud, sans données de production.
- L’installation de référence est native sur Ubuntu, sans Docker ; elle n’est pas un service managé Elastic Cloud ou Grafana Cloud.
- Préparer les sauvegardes/snapshots nécessaires et un accès de secours avant les changements administratifs.
- Vérifier les configurations existantes avant toute copie, fusion ou modification.
- Documenter les versions réellement installées et la compatibilité des composants.

Le dimensionnement proposé à l’atelier 01 — 4 vCPU, 16 Go de RAM et 30 Go disponibles — est une recommandation de laboratoire, pas un minimum garanti pour une charge de production.

### 2. Réseau : ne pas exposer les services applicatifs

| Port de référence | Service | Accès prévu |
|---:|---|---|
| 22 | SSH | Accès autorisé depuis les postes/réseaux prévus |
| 9200 | Elasticsearch | HTTPS local, authentifié |
| 5601 | Kibana | Boucle locale, accès navigateur via SSH |
| 8080 | Entrée HTTP Logstash de test | Local uniquement |
| 3100 | Loki | Local uniquement |
| 3000 | Grafana | Boucle locale, accès navigateur via SSH |
| 12345, si configuré | Diagnostic Alloy | Local uniquement ; ne pas ouvrir pour le TP |

Ne pas ouvrir les ports applicatifs sur Internet. Vérifier aussi les autres écoutes effectives, notamment celles du transport Elasticsearch, au lieu de considérer ce tableau comme un inventaire exhaustif.

Exemple de tunnel depuis le poste participant :

```bash
ssh -N \
  -L 5601:127.0.0.1:5601 \
  -L 3000:127.0.0.1:3000 \
  utilisateur@IP_PUBLIQUE_VM
```

Les interfaces sont alors consultées localement sur le poste, via le tunnel. HTTP dans ce tunnel est un choix de laboratoire ; il ne remplace pas une architecture TLS applicative de bout en bout.

Le profil Loki du TP est sans couche d’authentification externe et doit rester isolé. Une ouverture à d’autres machines exige un dispositif réseau, TLS et de contrôle d’accès adapté. Les identifiants de session Grafana ne protègent pas automatiquement une API Loki exposée séparément.

### 3. Authentification, certificats et privilèges

- Conserver la sécurité Elasticsearch activée.
- Vérifier les certificats avec la bonne autorité de certification et un nom d’hôte compatible.
- Ne pas utiliser curl -k ou désactiver TLS pour contourner une erreur.
- Réserver le compte elastic aux étapes administratives du laboratoire ; utiliser des identités techniques limitées pour les connexions permanentes.
- Utiliser une clé d’écriture adaptée pour Logstash et une identité de lecture pour les datasources de visualisation.
- Ne pas réutiliser indifféremment les droits de création d’index, d’ingestion et de lecture.
- Changer le mot de passe administrateur initial de Grafana lors de l’installation.

### 4. Secrets et dépôts de fichiers

Ne jamais publier dans les scripts, README, captures, exports ou dépôts :

- mots de passe, clés API, jetons et en-têtes Authorization ;
- clés privées, keystores contenant des secrets et fichiers d’environnement réels ;
- sorties brutes de commandes d’authentification ;
- URL contenant des identifiants ou liens donnant involontairement accès au laboratoire.

Utiliser les mécanismes prévus, notamment le keystore Logstash, les saisies protégées et les paramètres sécurisés des datasources. Un export de dashboard ou une capture doit être relu avant diffusion.

Révoquer les clés temporaires et supprimer les copies de secrets inutiles à la fin de la formation. Publier seulement des exemples de configuration sans secret réel.

### 5. Comptes de service et permissions

- Exécuter les services avec leurs comptes dédiés, pas avec root par commodité.
- Donner à Alloy la lecture des fichiers suivis et les droits nécessaires sur son stockage d’état, pas un accès général en écriture aux données sources.
- Vérifier la traversée des répertoires parents et la lecture effective comme utilisateur du service.
- Ne pas résoudre un refus de permission avec chmod -R 777.
- Réserver sudo aux opérations de préparation et d’administration qui le nécessitent.

### 6. Protection des données utilisées

Les access logs peuvent contenir des IP, URL, paramètres, agents utilisateurs et autres informations sensibles. Leur présence dans un support d’exercice ne les rend pas automatiquement publiables sans examen.

- Utiliser uniquement des données autorisées pour la formation.
- Masquer les informations sensibles avant capture ou partage.
- Respecter les conditions d’utilisation et d’attribution des jeux MovieLens ; leur fourniture ne vaut pas autorisation de redistribution sans contrôle.
- Distinguer les références initiales, copies de travail et sondes synthétiques.
- Ne pas attribuer de position géographique fictive à une IP réelle.
- Si une géolocalisation est illustrée, utiliser un enrichissement validé avec ses limites, ou un jeu synthétique séparé et annoncé.

### 7. Sauvegarde, modifications et nettoyage

- Sauvegarder une configuration avant modification et la valider avant redémarrage.
- Ne pas supprimer un index, une Data View, un dashboard ou une source partagée sans vérifier ses dépendances.
- Ne pas effacer le stockage d’état Alloy pour obtenir artificiellement un compte de lignes attendu.
- Ne pas confondre arrêt d’un service et suppression de ses données persistantes.
- Avant la fin de session, conserver les livrables utiles, révoquer les secrets temporaires et arrêter les ressources cloud devenues inutiles.

## Règles d’interprétation des données et indicateurs

### Temps : quatre notions à séparer

1. Date de l’événement source.
2. Date d’émission de l’instrumentation.
3. Date de collecte/horodatage retenu par le pipeline.
4. Période et instant d’évaluation de la requête.

Une archive lue aujourd’hui ne devient pas un trafic utilisateur actuel. Le parcours Alloy de base conserve l’heure de collecte pour faciliter les exercices sur des archives ; les variantes de date événement doivent être explicites.

### Volumes et duplications

Une relecture, une nouvelle sonde ou une copie dans un autre format peut créer de nouvelles entrées. Les fichiers JSON et logfmt dérivés de l’atelier 11 ne sont pas deux populations métier indépendantes.

Dans Elasticsearch, un document peut être remplacé si l’on réutilise son _id. Dans Loki, ajouter de nouveau une ligne n’est pas l’équivalent d’un upsert. Les comptes doivent donc être comparés sur une unité et un périmètre cohérents.

### Qualité et complétude

Ne pas confondre :

- structure impossible à parser ;
- champ absent ;
- valeur non convertible ;
- valeur convertible mais incohérente pour le métier ;
- référence attendue mais jamais reçue.

Un compteur de lignes reçues ne suffit pas à mesurer la complétude : il faut connaître l’attendu. Un contrat de batch émis ne détecte pas seul un batch dont le résumé n’a jamais été émis ; un inventaire ou contrôle indépendant est nécessaire.

### Métriques et visualisations

- Un ratio doit préciser numérateur, dénominateur, fenêtre et filtres.
- Zéro erreur observée n’est pas la même chose qu’aucune télémétrie.
- Un histogramme de moyennes n’est pas un histogramme des observations individuelles.
- Une heatmap temporelle n’est pas une carte géographique.
- Une moyenne de p95 n’est pas le p95 global.
- Quelques échantillons synthétiques ne suffisent pas à démontrer un SLO réel.
- L’access log de référence ne contient pas de durée permettant de calculer une latence HTTP ; les contrôles de durée restent explicitement pédagogiques.

## Organisation et continuité des fichiers

Organisation proposée pour rassembler les livrables ; elle est à adapter aux noms réellement fournis et ne décrit pas un dépôt déjà assemblé automatiquement :

```text
formation-data-observability/
├── README.md
├── atelier-01/ ... atelier-07/
├── atelier-08/       # Kibana et access logs
├── atelier-09/       # config Alloy et copies des deux sources
├── atelier-10/       # architecture Loki, LogQL et clients API
├── atelier-11/       # parsers et copies structurées
├── atelier-12/       # métriques, référence temporelle et contrôles
├── atelier-13/       # dashboard, scénario et corrélation
└── exemples/         # configurations expurgées uniquement
```

Les chemins opérationnels du laboratoire restent ceux des supports, notamment :

| Usage | Repère de référence |
|---|---|
| Configuration Alloy | /etc/alloy/config.alloy, sauf autre chemin explicitement configuré |
| Sources brutes A09 | /var/log/formation-alloy09/access_log et movies.csv |
| Vues structurées A11 | /var/log/formation-alloy11/events.jsonl et events.logfmt |
| Configuration Loki | /etc/loki-formation/loki.yml |
| Stockage Loki | /var/lib/loki-formation |
| Service Loki du parcours | loki-formation |

Les fichiers source ne sont pas à recopier dans un dépôt public par défaut. Les copies de travail et données générées doivent rester identifiées et protégées selon leur contenu.

### Révisions à utiliser

Ce README décrit la version harmonisée du parcours :

- atelier 08 recentré sur les access logs et la Data Observability ;
- atelier 09 fondé sur Alloy, access_log et movies.csv ;
- ateliers 10 à 12 adaptés à ces sources et à leurs copies structurées ;
- atelier 13 organisé autour du dashboard Grafana et de la simulation instrumentée.

Les anciens passages fondés uniquement sur douze logs JSON de trois services ou sur Promtail ne doivent pas être combinés tels quels avec les versions actualisées. Les compteurs et sélecteurs doivent correspondre au support effectivement utilisé.

## Livrables attendus

Au fil du parcours, conserver :

- les versions et éléments de configuration non sensibles ;
- mappings, scripts d’import et résultats de contrôle ;
- bibliothèques de requêtes Elasticsearch et LogQL ;
- objets de visualisation et exports autorisés ;
- manifestes de génération et périodes de référence ;
- réponses API utiles et exemples expurgés ;
- notes sur les choix de modèle, labels, unités et dénominateurs ;
- compte rendu du fil rouge avec faits, hypothèses, limites et actions proposées.

Un dashboard exporté ne contient pas les données de ses sources. Un import réussi ne prouve pas que les requêtes, certificats et contrôles fonctionneront sans adaptation dans un autre environnement.

## Validation avant une session

- Vérifier les versions des composants et les menus des interfaces.
- Répéter l’installation et les contrôles d’accès de l’atelier 01.
- Vérifier les chemins, comptes de service et permissions.
- Confirmer les formats, mappings et labels réellement utilisés.
- Tester le parcours sur un lot identifié et une période documentée.
- Comparer les chiffres des interfaces aux réponses API.
- Tester la collecte initiale, les ajouts et la reprise sans réinitialiser arbitrairement l’état.
- Valider les transformations des histogrammes/heatmaps sur la version Grafana retenue.
- Distinguer les tests locaux/simulés d’une validation de bout en bout sur la stack.

Les supports et scripts ne sont pas présentés comme une certification de production. Les configurations, extensions et visualisations doivent être validées par le formateur sur l’environnement réellement utilisé.

## Résultat attendu en fin de formation

Le participant doit pouvoir expliquer et démontrer la chaîne suivante :

```text
Données et événements
→ ingestion maîtrisée et accès protégés
→ recherche de documents / analyse de logs
→ contrôles de qualité, volume, temps et complétude
→ visualisations interprétables
→ corrélation et investigation
→ restitution argumentée et pistes d’amélioration
```

MovieLens apprend à retrouver et exploiter les données. Les access logs apprennent à observer des événements techniques. Leur utilisation conjointe montre comment rapprocher le contenu des données du fonctionnement des systèmes qui les transportent et les exposent, sans confondre mesure, simulation et preuve.

-- Support de cours et de TP créer par Dr. Ing. Maher HENI pour l'équipe de Bouygues Telecom Novembre 2026- All Rights Reserved
