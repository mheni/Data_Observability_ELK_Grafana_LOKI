# LIRE AVANT — Défi 13 : OpenSSH, Loki et Grafana

## Contenu du dossier

| Dossier | Public | Contenu |
|---|---|---|
| `participant/` | Stagiaires | Énoncé en deux parties, scripts d’indexation, modèles de configuration et grille de validation |
| `formateur/` | Formateur | Corrigé de 25 panneaux, registre de requêtes, générateur de JSON de secours et grille de correction |

Ne pas donner le dossier `formateur/` avant la fin du défi.

## Ordre pour les participants

1. Ouvrir `participant/DEFI_13_ENONCE.md`.
2. Exécuter la partie 1 depuis le dossier `participant`.
3. Construire le dashboard de la partie 2.
4. Remplir `GRILLE_VALIDATION_PARTICIPANT.csv`.

## Rôle des fichiers participants

| Fichier | Rôle | Utilisation |
|---|---|---|
| `DEFI_13_ENONCE.md` | Énoncé, dictionnaire de données, cahier des charges, livrables et barème | À lire |
| `preparer_openssh13.py` | Lit `OpenSSH_2k.log`, crée la copie brute, les événements JSON, le manifeste et les références | À exécuter sans sudo |
| `config_defi13.alloy.in` | Modèle de collecte vers Loki ; le lot est inséré par l’installateur | À lire, ne pas lancer |
| `alloy-defi13.service.in` | Modèle de service systemd dédié, port local 12348 | Utilisé par l’installateur |
| `installer_collecte_defi13.sh` | Copie les fichiers, génère la configuration, valide quand possible et démarre `alloy-defi13` | À exécuter une fois avec `sudo bash` |
| `verifier_loki_defi13.py` | Compte les lignes dans Loki, compare les types d’événements et les comptes canoniques | À exécuter après le démarrage |
| `GRILLE_VALIDATION_PARTICIPANT.csv` | Liste des 25 panneaux à valider | À compléter |

## Rôle des fichiers formateur

| Fichier | Rôle | Utilisation |
|---|---|---|
| `DEFI_13_CORRIGE_GRAFANA_25_PANNEAUX_FR.md` | Corrigé guidé : ouvrir, saisir, configurer, vérifier, placer et enregistrer chaque panneau | À lire |
| `registre_panneaux_defi13.json` | Requêtes, types et options des panneaux | Lu par le générateur |
| `construire_dashboard_defi13.py` | Génère un JSON Grafana de secours après la partie 1 | Facultatif ; ne publie rien dans Grafana |
| `GRILLE_CORRECTION_FORMATEUR.csv` | Références et limites à faire expliquer | À compléter |
| `VALIDATION_FORMATEUR.json` | Tests réalisés et vérifications non exécutées | À lire avant la séance |

## Fichiers générés pendant le défi

| Fichier ou dossier | Produit par | Fonction |
|---|---|---|
| `preparation_defi13/openssh.log` | Préparation | Copie brute collectée |
| `preparation_defi13/events.jsonl` | Préparation | Un événement JSON par ligne |
| `preparation_defi13/manifest.json` | Préparation | Lot, volumes attendus, empreinte |
| `preparation_defi13/reference_source.json` | Préparation | N, A, F, S, B, R, répartitions et tops de votre fichier |
| `reference_loki_defi13.json` | Vérificateur | Volumes constatés dans Loki et période de collecte |
| `livrables_defi13/dashboard_defi13.json` | Générateur formateur | JSON de secours à importer manuellement |

## Limites à connaître

- Le journal syslog n’a pas d’année ; Loki utilise la date de collecte.
- Les références sont calculées sur le fichier fourni au script. Un autre extrait donne d’autres chiffres.
- Le vérificateur compare des volumes et répartitions, pas chaque identifiant.
- Les tests locaux ont utilisé un journal synthétique au format syslog OpenSSH, parce que l’extrait Loghub n’était pas disponible. Le formateur doit exécuter la partie 1 sur le vrai fichier et lire `other_unclassified_lines` avant la séance.
- Alloy, Loki et Grafana ne sont ni installés ni modifiés par ces scripts, hors le service dédié `alloy-defi13`.
