# Changements de la révision corpus complet

- Source principale : fichier access complet, et non cinq références suivies d’un scénario.
- Suppression de run, phase, a13_kind, expected, accepted_count et source_delay_seconds dans les panneaux principaux.
- Population des panneaux : JSON du snapshot désigné par normalization_id exact, source_dataset=access.
- Variables principales : loki_ds et nid uniquement.
- Références recalculées sur le fichier joint, empreinte conservée.
- 34 985 tailles absentes non converties en zéro ; statistiques calculées sur 67 987 valeurs.
- 267 méthodes non extraites conservées dans le total.
- Vérificateur limité à 2000 lignes remplacé par des agrégations ; ses limites de preuve sont explicitées.
- Nouvelle préparation copiant toutes les lignes, sans prélèvement de cinq références ni patch manuel du manifeste.
- Guide de 60 requêtes réécrit ; anciens marqueurs de seed/run retirés du LogQL principal.
- 24 panneaux avec procédure propre d’ouverture, requête, réglage, contrôle, placement et sauvegarde.
- Distribution exhaustive en classes, séparée des histogrammes/heatmaps client échantillonnés.
- Courbes de collecte distinguées des dates Apache écrites ; pas de trafic historique inventé.
- Listes IP/chemins bornées et documentées pour limiter la cardinalité.
- Ancien scénario et ses outils conservés hors du parcours principal, sans réingestion requise.

Ce ZIP ne duplique pas les 23 Mo de logs ni les fichiers d’installation Alloy du pack initial. Pour une séance déjà commencée, la section 0 du nouvel atelier est le point d’entrée.
