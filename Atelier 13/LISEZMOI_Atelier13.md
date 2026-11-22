# Atelier 13 — Contenu et ordre de travail

Le support Markdown est le parcours principal : construction manuelle, panneau par panneau, selon la méthode de l’atelier 08.

## Préparation

Conserver les sources Alloy A09 (access_log, movies.csv) et A11 (events.jsonl). Aucune réinstallation de Loki/Grafana, aucun nouveau writer Alloy.
Extraire tous les fichiers dans le même dossier ; construire_dashboard13.py lit requetes-templates-atelier13.json à côté de lui.

## Commandes principales sur la VM de formation

```bash
set -o pipefail
sudo python3 generer_scenario13.py --output-dir scenario13 --phase-wait 15 --pace 0.05 | tee preparation13.json
python3 verifier_scenario13.py --manifest preparation13.json --output reference13.json
python3 construire_dashboard13.py --manifest preparation13.json --reference reference13.json --output-dir livrables13
```

Le générateur ajoute des sondes explicitement synthétiques aux copies de travail et à la source JSON A11. Il n’efface ni archives ni positions. Une phase recovery n’effectue pas de backfill des anomalies précédentes.

Le vérificateur exige 67 entrées Loki : 15 access, 14 CSV et 38 événements JSON. Le constructeur produit les deux dashboards personnalisés et les requêtes API.

## Modèles JSON

Les fichiers dashboard13-modele-*.json sont des modèles statiques avec RUN_A13_A_REMPLACER et une période relative. Préférer les exports construits depuis votre manifeste/référence, ou régler manuellement run, temps et datasource après import.

21 panneaux dans le principal, dont deux histogrammes, deux heatmaps, KPI, chronologie, comparaisons, table et logs. Le second dashboard reçoit un event_id ou préfixe de batch par lien.

Les noms de champs de logs (Line/Time), options et transformations peuvent varier selon la version Grafana. Aucun import UI n’a été exécuté pendant la génération. Refaire les contrôles numériques du support.

## Extension Elasticsearch

mapping-atelier13-events.json et publier_elasticsearch13.py projettent les mêmes 38 événements avec _id=event_id. Ils ne publient rien sans exécution explicite sur votre VM. TLS et authentification sont requis ; aucun secret n’est fourni.

## Validation et limites

validation_atelier13.json décrit les tests locaux et HTTP simulés. references-validation-atelier13.csv contient les contrôles par batch. Le rapport ne certifie pas une exécution réelle sur votre stack.
Les distributions et retards sont ceux d’une simulation instrumentée ; aucune latence HTTP ou position géographique n’est attribuée artificiellement aux vraies archives.
