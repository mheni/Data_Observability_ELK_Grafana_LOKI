# Bibliothèque Atelier 10 — compléter MARQUEUR_REEL avec scenario10.json

Tous les exemples utilisent la chaîne Alloy de l'atelier 09 et sa fenêtre de collecte.

## Lot complet : 6 lignes
```logql
{job="atelier09"} |= "MARQUEUR_REEL"
```

## Access : 4 lignes
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL"
```

## Movies : 2 lignes
```logql
{job="atelier09",dataset="movies"} |= "MARQUEUR_REEL"
```

## Timeout : 2 lignes
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL" |= "timeout"
```

## Timeout hors rétablissement : 1 ligne
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL" |= "timeout" != "recovered"
```

## Alternative OR : 3 lignes
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL" |~ "timeout|missing"
```

## AND des deux mots : 0 ligne
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL" |= "timeout" |= "missing"
```

## Classes d'erreur : 2 lignes
```logql
{job="atelier09",dataset="access",status_class=~"4xx|5xx"} |= "MARQUEUR_REEL"
```

## Casse ignorée : 2 lignes
```logql
{job="atelier09",dataset="access"} |= "MARQUEUR_REEL" |~ "(?i)TIMEOUT"
```

Ces comptes sont conditionnés au lot de six sondes reçu une fois et couvert par la période. Ils ne décrivent pas le total des archives access_log et MovieLens.
