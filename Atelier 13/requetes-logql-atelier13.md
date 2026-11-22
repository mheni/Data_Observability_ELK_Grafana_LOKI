# Atelier 13 — Requêtes Grafana / LogQL

Variables : run = identifiant du lot ; dataset et phase = listes avec All personnalisé .* . $__range = fenêtre du dashboard, pour les KPI en Instant.

## 01_observed_records

```logql
sum (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[$__range]
))
```

## 02_expected

```logql
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 03_accepted

```logql
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 04_rejected

```logql
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="rejected_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 05_missing

```logql
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="missing_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 06_completeness

```logql
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
/
sum (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 07_timeline

```logql
sum by (dataset_value) (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
[10s]
))
```

## 08_http_codes

```logql
sum by (status_value) (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
))
```

## 09_http_5xx_ratio

```logql
(
sum (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
| status_value >= 500
| __error__=""
[$__range]
))
 or
 (0 * sum (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
)))
) /
sum (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", status_value="http_status"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
| status_value!=""
| status_value >= 100
| status_value < 600
| __error__=""
[$__range]
))
```

## 10_access_observations

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="access"
```

## 11_movie_observations

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| dataset_value="movies"
```

## 12_max_observed_delay

```logql
max (max_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_delay_seconds"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 13_last_source_timestamp

```logql
1000 * max by (dataset_value) (max_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="source_event_epoch"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 14_completeness_by_dataset

```logql
sum by (dataset_value) (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="accepted_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
/
sum by (dataset_value) (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="expected"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 15_batch_table

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

## 16_rejected_by_reason

```logql
sum by (reason) (count_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", reason="quality_reason", accepted_value="accepted"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| accepted_value="false"
[$__range]
))
```

## 17_investigation_logs

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

## 18_missing_by_dataset

```logql
sum by (dataset_value) (sum_over_time(
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase", numeric_value="missing_count"
| __error__=""
| kind="batch"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
| numeric_value!=""
| unwrap numeric_value
| __error__=""
[$__range]
))
```

## 19_delay_observations

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", dataset_value="source_dataset", phase_value="phase"
| __error__=""
| kind="record"
| dataset_value=~"${dataset:regex}"
| phase_value=~"${phase:regex}"
```

## 20_heartbeat

```logql
{job="atelier11",format="json"} |= "${run}"
| json kind="a13_kind", phase_value="phase"
| __error__=""
| kind="heartbeat"
| phase_value=~"${phase:regex}"
```

