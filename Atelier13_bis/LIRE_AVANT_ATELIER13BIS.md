# Atelier 13 bis — Démarrage du pack autonome

## Lire dans cet ordre

1. ATELIER_13BIS_MODELE.md : parcours principal, préparation et 24 panneaux détaillés.
2. Après chargement et contrôle : exécuter personnaliser_support13bis.py comme indiqué. Lire les deux supports personnalisés dans supports13bis.
3. GUIDE_60_REQUETES_EXPLORE_MODELE.md : modèle du guide ; sa version personnalisée est fournie par le script précédent.

Le document principal est volontairement complet : chaque panneau indique ouverture, code, Instant/Range, choix de graphique, champs, transformations, unités, vérification, placement et sauvegarde. Le type Grafana est Stat, et non le menu Indicateur de Kibana.

## Ce qui ne dépend plus des anciens ateliers

Sources autonomes, normalisation JSON/logfmt, contrôles de qualité, configuration Alloy dédiée, générateur de scénario, vérificateurs de livraison, 60 requêtes, dashboards de secours et extension ES sont ici. Les données par défaut sont explicitement synthétiques ; les titres de film ne prétendent pas être ceux du véritable jeu MovieLens. Une variante permet de fournir ses propres références.

## Prérequis restant

Ubuntu natif avec Loki et Grafana déjà opérationnels, binaire Alloy et compte/groupe alloy, accès administrateur pour le service dédié. Loki local mono-tenant non authentifié sur 127.0.0.1:3100 est le périmètre de configuration fourni. Préparer toute adaptation TLS/authentification/tenant avant la séance.

## Commandes de démarrage, à lire avec le support

```bash
set -o pipefail
python3 preparer_sources13bis.py --output-dir sources13bis
python3 normaliser_sources13bis.py --access sources13bis/access_log --movies sources13bis/movies.csv --output-dir corpus13bis --with-controls | tee preparation13bis.json
sudo bash installer_collecte13bis.sh sources13bis corpus13bis
export LOKI_URL='http://127.0.0.1:3100'
python3 verifier_normalisation13bis.py --manifest preparation13bis.json --corpus corpus13bis --output reference-normalisation13bis.json
sudo python3 generer_scenario13bis.py --raw-dir /var/log/formation13bis/raw --events /var/log/formation13bis/json/events.jsonl --output-dir scenario13bis --phase-wait 15 --pace 0.05 | tee manifest-scenario13bis.json
python3 verifier_scenario13bis.py --manifest manifest-scenario13bis.json --output reference13bis.json
python3 construire_exploration13bis.py --normalisation preparation13bis.json --scenario manifest-scenario13bis.json --reference reference13bis.json --output-dir exploration13bis
python3 personnaliser_support13bis.py --normalisation preparation13bis.json --scenario manifest-scenario13bis.json --reference reference13bis.json --output-dir supports13bis
```

Les commandes ne sont pas une opération idempotente de réinitialisation. Les dossiers existants et ressources système existantes sont refusés pour éviter l’écrasement. Ne pas effacer les positions Alloy pour retrouver les comptes initiaux. Conserver les références d’un run et utiliser un nouveau dossier pour un nouvel essai volontaire.

## Étapes de contrôle

- 14 JSON et 14 logfmt du lot de normalisation, IDs contrôlés par format.
- 15 sondes Apache, 14 CSV et 38 JSON du scénario : 67 représentations, mais seulement 29 records métier observés.
- 30 attendues, 27 validées, 2 rejetées et 1 manquante ; complétude 90 %.
- Les répertoires de préparation sous le compte utilisateur et ceux du scénario sous sudo n’ont pas les mêmes droits : les manifestes visibles via tee servent aux scripts de lecture utilisateur.

## Limites de validation

validation_locale13bis.json décrit des tests Python, JSON, Bash et des réponses HTTP simulées. Aucune validation de configuration par un vrai binaire Alloy, livraison Loki, compilation LogQL ou import Grafana n’est revendiquée ici. La version de Grafana n’était pas fournie ; les libellés anglais avec explications françaises sont à confirmer dans le laboratoire. L’export JSON de secours ne remplace pas le parcours manuel.
