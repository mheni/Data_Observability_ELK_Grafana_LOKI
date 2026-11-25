# Défi 08 bis — pack d’accompagnement

## Par où commencer

- Participants : Defi_08bis_Enonce_Participants.md.
- Formateur / correction : Defi_08bis_OpenSSH_Loghub_Corrige.md.
- Version cible : Kibana / Elasticsearch 9.5.7, interface française ; le type Metric s’appelle Indicateur.

## Important avant la séance

L’échantillon OpenSSH contient des IP, pas des coordonnées. La carte obligatoire utilise un enrichissement réel GeoIP. Tester le pipeline et la carte avant la séance ou préparer un cache réel daté avec exporter_cache_geo.py. Aucune base GeoIP ni cache réel n’est inclus. Ne pas remplacer des résultats indisponibles par des villes inventées.

Le fichier .log distant n’est pas redistribué dans ce pack. L’acquisition et la conservation de la licence sont décrites dans le support. Vérifier les conditions pour l’usage envisagé, notamment une formation commerciale.

## Fichiers

- preparer_openssh.py : parsing, classification, dates conventionnelles explicites, IP, NDJSON, provenance et rejets.
- openssh-mapping.json : schéma strict et geo_point.
- openssh-geoip-pipeline.json : enrichissement côté Elasticsearch.
- openssh-validation-query.json : références chiffrées sur serveur.
- verifier_reponse.py : contrôle des simulations, items Bulk et références.
- exporter_cache_geo.py et export-cache-query.json : préparation d’un cache réel sur un poste connecté.
- validation_locale_pack.json : portée et résultats des tests locaux, pas preuve du cluster.

Les scripts Python n’ont pas besoin de dépendances supplémentaires et ne font pas d’appel réseau. Les commandes HTTP visibles restent exécutées avec curl par le participant. Les chemins des fichiers et les noms d’index sont documentés ; aucune suppression automatique n’est prévue.
