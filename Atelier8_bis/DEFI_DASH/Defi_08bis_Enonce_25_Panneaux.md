# Défi 08 bis — Énoncé révisé : tableau de bord OpenSSH à 25 panneaux

Cible : Kibana 9.5.7 en français. Le type de valeur unique s’appelle « Indicateur ».

## Préparation

Réutiliser le premier pack du défi OpenSSH Loghub : scripts, mapping, pipeline et fichier OpenSSH_2k.log acquis selon sa notice. Ne pas changer le schéma pour remplir les graphiques. Les coordonnées sont issues d’un enrichissement GeoIP réel ou d’un cache réel préparé par le formateur, jamais de villes inventées.

## Mission

Indexer les logs par la commande Bulk du pack, valider chaque item, puis construire les 25 panneaux suivants. Répondre à une question différente par panneau, conserver les documents bruts et expliciter les limites de chaque taux et de la carte. Le corrigé détaillé joint explique chaque construction jusqu’à son enregistrement.

| ID | Titre / fonction | Type |
|---|---|---|
| P01 | Documents indexés | Indicateur |
| P02 | Enregistrements canoniques | Indicateur |
| P03 | Échecs canoniques | Indicateur |
| P04 | Succès canoniques | Indicateur |
| P05 | IP distinctes estimées | Indicateur |
| P06 | Part d’échec canonique | Indicateur |
| P07 | Couverture GeoIP — documents avec IP | Indicateur |
| P08 | Documents sans IP extraite | Indicateur |
| P09 | Messages dans le temps par type | Barres verticales empilées |
| P10 | Échecs et succès canoniques dans le temps | Courbes |
| P11 | Répartition des types de messages | Anneau |
| P12 | Top 10 IP — échecs canoniques | Barres horizontales |
| P13 | Top utilisateurs — échecs canoniques | Barres horizontales |
| P14 | Pays — messages géolocalisés | Barres horizontales |
| P15 | Analyse par IP — volume et taux canonique | Tableau Lens |
| P16 | Analyse par utilisateur — volume et taux canonique | Tableau Lens |
| P17 | Intensité des messages — temps × type | Carte thermique Lens |
| P18 | IP × issue des enregistrements canoniques | Carte thermique Lens |
| P19 | Ports sources — enregistrements canoniques | Barres par filtres |
| P20 | Points GeoIP et détails | Carte Documents |
| P21 | Volumes GeoIP regroupés | Carte de regroupements |
| P22 | Densité des échecs géolocalisés | Carte de densité |
| P23 | Détail des échecs canoniques | Session Découvrir |
| P24 | IP sans coordonnées | Session Découvrir |
| P25 | Contrat de lecture | Texte Markdown |

## Contrôles attendus

- Type de message, IP source, utilisateur observé et pays GeoIP.
- Période absolue couvrant les données sous la convention d’année 2000/UTC.
- Filtres temporaires retirés avant comparaison des chiffres globaux.
- Chaque panneau et le tableau de bord sont enregistrés puis réouverts.

## Critères de qualité

- Une ligne n’est pas une session ni une personne.
- Le taux d’échec porte sur les seules lignes canoniques reconnues, sans double compter PAM et résumés répétés.
- La couverture porte sur les documents avec IP et doit être nommée comme telle.
- Les tops ne sont pas exhaustifs et les catégories absentes ne sont pas inventées.
- Les points géographiques sont des estimations GeoIP, pas des positions personnelles ni historiques prouvées.
- Un zéro légitime est conservé ; une absence de dénominateur n’est pas transformée en faux zéro.
- Les cartes P20/P21/P22 sont préparées avant la séance ; une base indisponible ne doit pas devenir un piège de clics.

## Livrables

Capture et réouverture du tableau de bord, trois cartes enregistrées si le prérequis est disponible, contrôles, fichier de validation rempli, réponses Bulk contrôlées, preuve documentaire d’une investigation et conclusion prudente.

## Organisation pédagogique

Tout réaliser prend deux demi-journées pour un groupe débutant. Pour une demi-journée : P01 à P06, P09, P12, P15, P17, P20, P23 et P25. Les autres visualisations constituent l’approfondissement ou se répartissent entre binômes. La quantité ne remplace pas la cohérence et la qualité de lecture.
