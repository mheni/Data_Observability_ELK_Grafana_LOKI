# Atelier 12 — Bibliothèque de requêtes

Remplacer __MARKER__ par le marker de scenario12.json, ou utiliser construire_requetes12.py. Les contrôles à référence fixe utilisent T de reference12.json et une fenêtre de cinq minutes.

## 01_count_par_dataset

```logql
sum by (dataset) (
  count_over_time(
    {job="atelier09",dataset=~"access|movies"} |= "__MARKER__"
    [5m]
  )
)
```

## 02_rate_par_dataset

```logql
sum by (dataset) (
  rate(
    {job="atelier09",dataset=~"access|movies"} |= "__MARKER__"
    [5m]
  )
)
```

## 03_count_classes_http

```logql
sum by (status_class) (
  count_over_time(
    {job="atelier09",dataset="access"} |= "__MARKER__"
    [5m]
  )
)
```

## 04_rate_5xx

```logql
sum by (service) (
  rate(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
```

## 05_ratio_5xx

```logql
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
/
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
)
```

## 06_ratio_5xx_zero_present

```logql
(
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class="5xx"} |= "__MARKER__"
    [5m]
  )
)
  or on (service)
  (0 * sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
))
)
/
sum by (service) (
  count_over_time(
    {job="atelier09",dataset="access",status_class=~"[1-5]xx"} |= "__MARKER__"
    [5m]
  )
)
```

## 07_reponse_octets_total

```logql
sum(
  sum_over_time(
    {job="atelier09",dataset="access"} |= "__MARKER__"
    | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
    | response_size!=""
    | response_size!="-"
    | unwrap response_size
    | __error__=""
    [5m]
  )
)
```

## 08_reponse_octets_moyenne

```logql
avg_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
  | response_size!=""
  | response_size!="-"
  | unwrap response_size
  | __error__=""
  [5m]
) by (service)
```

## 09_reponse_octets_max

```logql
max_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  | pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <response_size> "<referer_value>" "<agent_value>"`
  | response_size!=""
  | response_size!="-"
  | unwrap response_size
  | __error__=""
  [5m]
) by (service)
```

## 10_controles_durees_moyenne

```logql
avg_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

## 11_controles_durees_max

```logql
max_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

## 12_controles_durees_p95

```logql
quantile_over_time(
  0.95,
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (metric_group)
```

## 13_controles_durees_p95_global

```logql
quantile_over_time(
  0.95,
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  | unwrap duration_value
  | __error__=""
  [5m]
) by (job)
```

## 14_controles_lents

```logql
sum by (metric_group) (
  count_over_time(
    {job="atelier11",format="json"} |= "__MARKER__"
    | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
    | __error__=""
    | kind="controls_metrics"
    | duration_value!=""
    | duration_value >= 0
    | __error__=""
    | duration_value >= 1000
    | __error__=""
    [5m]
  )
)
```

## 15_controles_total

```logql
sum(count_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  [5m]
))
```

## 16_controles_exploitables

```logql
sum(count_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | duration_value >= 0
  | __error__=""
  [5m]
))
```

## 17_erreur_unwrap_volontaire

```logql
avg_over_time(
  {job="atelier11",format="json"} |= "__MARKER__"
  | json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
  | __error__=""
  | kind="controls_metrics"
  | duration_value!=""
  | unwrap duration_value
  [5m]
) by (metric_group)
```

## 18_diagnostic_unwrap_logs

```logql
{job="atelier11",format="json"} |= "__MARKER__"
| json metric_group="control_group", duration_value="duration_ms", kind="source_dataset"
| __error__=""
| kind="controls_metrics"
| duration_value!=""
| duration_value >= 0
| __error__!=""
```

## 19_absence_sonde

```logql
absent_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  [1m]
)
```

## 20_octets_lignes_loki

```logql
sum(bytes_over_time(
  {job="atelier09",dataset="access"} |= "__MARKER__"
  [5m]
))
```

