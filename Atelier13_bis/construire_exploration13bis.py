import argparse
import json
import math
from pathlib import Path
p=argparse.ArgumentParser(description='Bibliotheque Explore concrete : aucun placeholder a remplacer a la main')
p.add_argument('--normalisation',default='preparation13bis.json')
p.add_argument('--scenario',default='manifest-scenario13bis.json')
p.add_argument('--reference',default='reference13bis.json')
p.add_argument('--output-dir',default='exploration13bis')
a=p.parse_args()
n=json.loads(Path(a.normalisation).read_text());m=json.loads(Path(a.scenario).read_text());r=json.loads(Path(a.reference).read_text())
if m['run_id']!=r['run_id']:p.error('Run different')
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie existant')
base.mkdir(parents=True)
N=n['normalization_id'];RUN=m['run_id']
J='{job="atelier13bis",format="json"} |= '+json.dumps(N)
L='{job="atelier13bis",format="logfmt"} |= '+json.dumps(N)
R='{job="atelier13bis",format="json"} |= '+json.dumps(RUN)
raw='{job="atelier13bis_raw",dataset="access"} |= "A13B_SEED"'
pat='| pattern `<ip> <_> <_> [<apache_date>] "<method> <path> <protocol>" <status_value> <size_value> "<referer>" "<agent>"`'
queries=[]
def add(name,query,expected,period='normalisation',kind='logs'):
    queries.append({'id':f'E{len(queries)+1:02d}','name':name,'query':query,'expected':expected,'period':period,'kind':kind})
add('flux_bruts_access','{job="atelier13bis_raw",dataset="access"}','5 references au premier demarrage ; puis 15 sondes de plus apres le scenario')
add('flux_bruts_movies','{job="atelier13bis_raw",dataset="movies"}','Entete CSV + 5 references ; puis 14 sondes de plus')
add('json_lot',J,'14 lignes dans le format JSON')
add('logfmt_lot',L,'14 lignes dans le format logfmt')
add('texte_ERROR',J+' |= "ERROR"','3 controles : C_BAD, C_MISSING et C_NEGATIVE')
add('texte_sans_unknown',J+' |= "controls" != "unknown"','3 controles, exclut C_BAD')
add('regex_niveaux_texte',J+' |~ "WARN|ERROR"','Recherche dans la ligne entiere, pas une egalite du niveau')
add('pattern_apache',raw+'\n'+pat,'5 references si les seeds autonomes sont utilises')
add('pattern_5xx',raw+'\n'+pat+'\n| status_value!="" | status_value >= 500 | status_value < 600 | __error__=""','1 reference 503 de demonstration')
add('regexp_apache',raw+'\n| regexp `^(?P<ip_value>\\S+) \\S+ \\S+ \\[[^\\]]+\\] "(?P<request_value>[^"]*)" (?P<status_value>[0-9]{3}) (?P<size_value>[0-9]+|-)`\n| status_value="503"','Meme reference 503 que E09')
add('octets_bruts',raw+'\n'+pat+'\n| size_value!="" | size_value!="-" | size_value >= 1000 | __error__=""','3 references de taille 1500, 4096 et 8192')
add('csv_premier_ID','{job="atelier13bis_raw",dataset="movies"}\n| regexp `^(?P<id_value>[0-9]+),` | id_value="1002"','Film B au titre contenant virgule et guillemets')
add('csv_pattern_limite','{job="atelier13bis_raw",dataset="movies"}\n| pattern `<id_value>,<title_value>,<genres_value>`','Inspecter le titre avec virgule : ce motif ne remplace pas un parseur CSV')
add('json_complet',J+'\n| json | __error__=""','14 lignes, dont 4 controles')
add('json_movies_alias',J+'\n| json src="source_dataset", film="title", movie="movie_id", body_service="service"\n| __error__="" | src="movies"','5 titres complets, dont celui contenant virgule et guillemets')
add('json_objet_tableau',J+'\n| json src="source_dataset", origin="metadata.origin", genre="genres[0]"\n| __error__="" | src="movies"','Premier genre uniquement ; pas de genre invente pour le tableau vide')
add('champ_ERROR_exact',J+'\n| json src="source_dataset", lvl="level", case_id="test_case"\n| __error__="" | src="controls" | lvl="ERROR"','2 lignes : C_BAD et C_NEGATIVE, contrairement a E05')
add('niveaux_logique',J+'\n| json src="source_dataset", lvl="level"\n| __error__="" | src="controls" | (lvl="WARN" or lvl="ERROR")','3 lignes : C_VALID, C_BAD, C_NEGATIVE')
add('numeric_valide',J+'\n| json src="source_dataset", value="duration_ms", case_id="test_case"\n| __error__="" | src="controls" | value!="" | value >= 1000 | __error__=""','1 ligne C_VALID a 1800 ms')
add('conversion_erreur',J+'\n| json src="source_dataset", value="duration_ms", case_id="test_case"\n| __error__="" | src="controls" | value!="" | value >= 1000 | __error__!=""','C_BAD : valeur unknown non convertible')
add('champ_absent',J+'\n| json src="source_dataset", value="duration_ms", case_id="test_case"\n| __error__="" | src="controls" | value=""','C_MISSING, JSON pourtant valide')
add('negatif_metier',J+'\n| json src="source_dataset", value="duration_ms", case_id="test_case"\n| __error__="" | src="controls" | value!="" | value < 0 | __error__=""','C_NEGATIVE, -5 convertible mais invalide pour le besoin')
add('logfmt_parser',L+'\n| logfmt | __error__=""','14 lignes avec champs scalaires, pas tous les objets/tableaux JSON')
add('logfmt_duree',L+'\n| logfmt | __error__="" | source_dataset="controls" | elapsed!="" | elapsed >= 1s | __error__=""','C_VALID avec elapsed=1.8s')
add('logfmt_taille',L+'\n| logfmt | __error__="" | source_dataset="controls" | payload!="" | payload >= 1MB | __error__=""','C_VALID avec payload=2MB')
add('mauvais_parser',L+'\n| json | __error__!=""','Erreurs de parsing attendues : logfmt n’est pas JSON')
add('line_format',J+'\n| json src="source_dataset", film="title", movie="movie_id"\n| __error__="" | src="movies" | line_format `film={{.movie}} titre={{.film}}`','5 lignes reformatees a la requete ; original Loki non modifie')
add('label_format',J+'\n| json src="source_dataset", body_service="service"\n| __error__="" | label_format service_lu="{{.body_service}}"','Label de resultat, pas indexation retroactive')
add('scenario_tout',R,'38 JSON : 29 records, 6 batches et 3 heartbeats','scenario')
add('scenario_movies_incident',R+'\n| json k="a13_kind", ds="source_dataset", ph="phase"\n| __error__="" | k="record" | ds="movies" | ph="incident"','4 records dont 2 rejetes','scenario')
add('scenario_rejetes',R+'\n| json k="a13_kind", ok="accepted"\n| __error__="" | k="record" | ok="false"','2 records movies rejetes','scenario')
add('scenario_5xx',R+'\n| json k="a13_kind", st="http_status"\n| __error__="" | k="record" | st!="" | st >= 500 | st < 600 | __error__=""','2 records access avec 503','scenario')
add('scenario_retard',R+'\n| json k="a13_kind", delay="source_delay_seconds"\n| __error__="" | k="record" | delay!="" | delay >= 600 | __error__=""','4 records movies incident','scenario')
add('scenario_summaries',R+'\n| json k="a13_kind" | __error__="" | k="batch"','6 resumes distincts des records','scenario')
add('scenario_heartbeats',R+'\n| json k="a13_kind" | __error__="" | k="heartbeat"','3 lignes de controle, pas des films','scenario')
add('scenario_recovery',R+'\n| json k="a13_kind", ph="phase" | __error__="" | k="record" | ph="recovery"','10 records, pas preuve de backfill','scenario')
templates=json.loads(Path(__file__).with_name('requetes-templates-atelier13bis.json').read_text())
seconds=math.ceil((int(r['to_ns'])-int(r['from_ns']))/1e9)
for name,query in templates.items():
    q=query.replace('${run}',RUN).replace('${dataset:regex}','.*').replace('${phase:regex}','.*').replace('$__range',f'{seconds}s')
    islogs=name in ['10_access_observations','11_movie_observations','15_batch_table','17_investigation_logs','19_delay_observations','20_heartbeat']
    kind='logs' if islogs else ('metric_range' if name in ['07_timeline','22_rate_by_dataset'] else 'metric_instant')
    add('metrique_'+name,q,'Voir la fiche panneau et le manifeste de controle','scenario',kind)
index=['# Bibliotheque Explore A13bis personnalisee','',f'Normalisation : {N}',f'Run : {RUN}','',
       'Choisir la periode normalisation ou scenario correspondante. Les expressions sont resolues, sans variable de dashboard.']
for item in queries:
    (base/(item['id']+'_'+item['name']+'.logql')).write_text(item['query']+'\n',encoding='utf-8')
    index.extend(['',f'## {item["id"]} — {item["name"]}',f'Periode : {item["period"]} ; type : {item["kind"]}',
                  '', '```logql',item['query'],'```','', 'Attendu : '+item['expected']])
(base/'BIBLIOTHEQUE_EXPLORE.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
(base/'index.json').write_text(json.dumps(queries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'queries':len(queries),'output_dir':str(base)},indent=2))
