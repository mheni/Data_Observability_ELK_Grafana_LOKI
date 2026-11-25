import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser(description='Personnalise les exemples LogQL de base A13bis')
p.add_argument('--manifest',default='preparation13bis.json')
p.add_argument('--raw-marker',default='A13B_SEED',help='Marqueur des lignes brutes de reference')
p.add_argument('--output-dir',default='requetes13bis-base')
a=p.parse_args()
report=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
marker=report['normalization_id']
base=Path(a.output_dir)
if base.exists():
    p.error('Dossier de requetes deja present')
a10=a.raw_marker
queries={'access_pattern': '{job="atelier13bis_raw",dataset="access"} |= "__A10_MARKER__"\n'
                   '| pattern `<client_ip_value> <_> <_> [<apache_time_value>] "<method_value> <path_value> '
                   '<protocol_value>" <status_value> <bytes_value> "<referer_value>" "<agent_value>"`\n'
                   '| method_value!=""\n'
                   '| path_value!=""\n'
                   '| status_value!=""\n'
                   '| status_value >= 500\n'
                   '| status_value < 600\n'
                   '| __error__=""',
 'access_regexp': '{job="atelier13bis_raw",dataset="access"} |= "__A10_MARKER__"\n'
                  '| regexp `^(?P<client_ip_value>\\S+) \\S+ \\S+ \\[[^\\]]+\\] "(?P<request_value>[^"]*)" '
                  '(?P<status_value>[0-9]{3}) (?P<bytes_value>[0-9]+|-)`\n'
                  '| status_value!=""\n'
                  '| status_value >= 500\n'
                  '| __error__=""',
 'json_access_5xx': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                    '| json kind="source_dataset", status_value="status", path_value="path", '
                    'body_service="service"\n'
                    '| __error__=""\n'
                    '| kind="access"\n'
                    '| status_value!=""\n'
                    '| status_value >= 500\n'
                    '| status_value < 600\n'
                    '| __error__=""',
 'json_movies': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                '| json kind="source_dataset", movie_id_value="movie_id", film_title="title", '
                'year_value="year", body_service="service"\n'
                '| __error__=""\n'
                '| kind="movies"\n'
                '| movie_id_value!=""\n'
                '| film_title!=""',
 'controls_json_error_levels': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                               '| json kind="source_dataset", parsed_level="level", case_id="test_case"\n'
                               '| __error__=""\n'
                               '| kind="controls"\n'
                               '| parsed_level="ERROR"',
 'controls_json_duration_valid': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                                 '| json kind="source_dataset", duration_value="duration_ms", '
                                 'case_id="test_case"\n'
                                 '| __error__=""\n'
                                 '| kind="controls"\n'
                                 '| duration_value!=""\n'
                                 '| duration_value >= 1000\n'
                                 '| __error__=""',
 'controls_json_conversion_errors': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                                    '| json kind="source_dataset", duration_value="duration_ms", '
                                    'case_id="test_case"\n'
                                    '| __error__=""\n'
                                    '| kind="controls"\n'
                                    '| duration_value!=""\n'
                                    '| duration_value >= 1000\n'
                                    '| __error__!=""',
 'controls_json_missing': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                          '| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"\n'
                          '| __error__=""\n'
                          '| kind="controls"\n'
                          '| duration_value=""',
 'controls_json_negative': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                           '| json kind="source_dataset", duration_value="duration_ms", case_id="test_case"\n'
                           '| __error__=""\n'
                           '| kind="controls"\n'
                           '| duration_value!=""\n'
                           '| duration_value < 0\n'
                           '| __error__=""',
 'controls_logfmt_elapsed': '{job="atelier13bis",format="logfmt"} |= "__NID__"\n'
                            '| logfmt\n'
                            '| __error__=""\n'
                            '| source_dataset="controls"\n'
                            '| elapsed!=""\n'
                            '| elapsed >= 1s\n'
                            '| __error__=""',
 'controls_logfmt_payload': '{job="atelier13bis",format="logfmt"} |= "__NID__"\n'
                            '| logfmt\n'
                            '| __error__=""\n'
                            '| source_dataset="controls"\n'
                            '| payload!=""\n'
                            '| payload >= 1MB\n'
                            '| __error__=""',
 'wrong_json_parser': '{job="atelier13bis",format="logfmt"} |= "__NID__"\n| json\n| __error__!=""',
 'json_movies_format': '{job="atelier13bis",format="json"} |= "__NID__"\n'
                       '| json kind="source_dataset", film_title="title", movie_id_value="movie_id", '
                       'body_service="service"\n'
                       '| __error__=""\n'
                       '| kind="movies"\n'
                       '| film_title!=""\n'
                       '| line_format `film={{.movie_id_value}} | titre={{.film_title}} | '
                       'service_contenu={{.body_service}}`'}
base.mkdir(parents=True)
written=[]
for name,query in queries.items():
    if '__A10_MARKER__' in query and a10 is None:
        continue
    query=query.replace('__NID__',marker).replace('__A10_MARKER__',a10 or '')
    (base/(name+'.logql')).write_text(query+'\n',encoding='utf-8')
    written.append(name)
print(json.dumps({'output':str(base),'queries':written},indent=2))
