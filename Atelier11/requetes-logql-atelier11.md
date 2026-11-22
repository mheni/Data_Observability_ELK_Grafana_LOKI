# Bibliothèque LogQL — Atelier 11

__NID__ = normalization_id de preparation11.json. __A10_MARKER__ = marker des sondes brutes A10.

Le script construire_requetes11.py remplace ces valeurs ; ne pas copier les placeholders comme des valeurs réelles.

## access_pattern

```logql
{job="atelier09",dataset="access"} |= "__A10_MARKER__"
| pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> <protocol_value>" <status_value> <bytes_value> "<referer_value>" "<agent_value>"`
| method_value!=""
| path_value!=""
| status_value!=""
| status_value >= 500
| status_value < 600
| __error__=""
```

## access_regexp

```logql
{job="atelier09",dataset="access"} |= "__A10_MARKER__"
| regexp `^(?P<client_ip_value>\S+) \S+ \S+ \[[^\]]+\] "(?P<request_value>[^"]*)" (?P<status_value>[0-9]{3}) (?P<bytes_value>[0-9]+|-)`
| status_value!=""
| status_value >= 500
| __error__=""
```

## json_access_5xx

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", status_value="status", path_value="path", body_service="service"
| __error__=""
| kind="access"
| status_value!=""
| status_value >= 500
| status_value < 600
| __error__=""
```

## json_movies

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", movie_id_value="movie_id", film_title="title", year_value="year", body_service="service"
| __error__=""
| kind="movies"
| movie_id_value!=""
| film_title!=""
```

## controls_json_error_levels

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", parsed_level="level", case_id="test_case"
| __error__=""
| kind="controls"
| parsed_level="ERROR"
```

## controls_json_duration_valid

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value >= 1000
| __error__=""
```

## controls_json_conversion_errors

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value >= 1000
| __error__!=""
```

## controls_json_missing

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value=""
```

## controls_json_negative

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"
| __error__=""
| kind="controls"
| duration_value!=""
| duration_value < 0
| __error__=""
```

## controls_logfmt_elapsed

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| logfmt
| __error__=""
| source_dataset="controls"
| elapsed!=""
| elapsed >= 1s
| __error__=""
```

## controls_logfmt_payload

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| logfmt
| __error__=""
| source_dataset="controls"
| payload!=""
| payload >= 1MB
| __error__=""
```

## wrong_json_parser

```logql
{job="atelier11",format="logfmt"} |= "__NID__"
| json
| __error__!=""
```

## json_movies_format

```logql
{job="atelier11",format="json"} |= "__NID__"
| json kind="source_dataset", film_title="title", movie_id_value="movie_id", body_service="service"
| __error__=""
| kind="movies"
| film_title!=""
| line_format `film={{.movie_id_value}} | titre={{.film_title}} | service_contenu={{.body_service}}`
```

