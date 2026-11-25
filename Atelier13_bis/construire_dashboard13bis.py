import argparse
import copy
import json
import math
from pathlib import Path

p=argparse.ArgumentParser(description='Dashboards Grafana A13 et requetes API personnalisees')
p.add_argument('--manifest',default='manifest-scenario13bis.json')
p.add_argument('--reference',default='reference13bis.json')
p.add_argument('--output-dir',default='livrables13bis')
a=p.parse_args()
m=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
r=json.loads(Path(a.reference).read_text(encoding='utf-8'))
if m['run_id']!=r['run_id']:p.error('Run different entre manifest et reference')
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie deja present')
queries=json.loads(Path(__file__).with_name('requetes-templates-atelier13bis.json').read_text(encoding='utf-8'))
base.mkdir(parents=True)
source={'type':'loki','uid':'${loki_ds}'}
variables=[
    {'name':'loki_ds','label':'Source Loki','type':'datasource','query':'loki','refresh':1,'current':{}},
    {'name':'run','label':'Run A13bis','type':'textbox','query':m['run_id'],'current':{'text':m['run_id'],'value':m['run_id']},'skipUrlSync':False},
]
for name,label,values in [('dataset','Jeu de donnees',['access','movies']),('phase','Phase',['normal','incident','recovery'])]:
    variables.append({'name':name,'label':label,'type':'custom','query':','.join(values),'multi':True,
                      'includeAll':True,'allValue':'.*','current':{'text':'All','value':'$__all'},
                      'options':[{'text':'All','value':'$__all','selected':True}]+[{'text':x,'value':x,'selected':False} for x in values]})
dashboard={'id':None,'uid':'a13bis-data-observability','title':'[A13bis] Data Observability — Access et MovieLens',
           'description':'Dashboard autonome A13bis : mesures de collecte et simulation instrumentee ; pas de latence HTTP reelle.',
           'schemaVersion':39,'version':1,'timezone':'utc','editable':True,'refresh':'',
           'time':{'from':r['from_utc'],'to':r['to_utc']},'templating':{'list':variables},
           'tags':['formation','data-observability','a13'],'panels':[]}
def target(expr,instant=False):
    return {'refId':'A','datasource':copy.deepcopy(source),'editorMode':'code','expr':expr,
            'queryType':'instant' if instant else 'range','instant':instant,'range':not instant,'maxLines':2000}
def panel(pid,title,kind,expr,x,y,w=12,h=8,unit='none',instant=False):
    item={'id':pid,'title':title,'type':kind,'datasource':copy.deepcopy(source),
          'gridPos':{'x':x,'y':y,'w':w,'h':h},'targets':[target(expr,instant)],
          'fieldConfig':{'defaults':{'unit':unit,'noValue':'No data'},'overrides':[]},'options':{}}
    dashboard['panels'].append(item);return item
context={'id':1,'title':'P00 — Perimetre et methode','type':'text','gridPos':{'x':0,'y':0,'w':24,'h':4},
         'options':{'mode':'markdown','content':'Sources autonomes et collecte dediee A13bis. Lot **synthetique instrumente** : normal → incident → recovery. Les KPI utilisent la periode selectionnee en Instant ; les heatmaps utilisent les observations individuelles. Aucune latence HTTP n’est fournie. Les variables filtrent uniquement les panneaux qui les referencent.'}}
dashboard['panels'].append(context)
stats=[('P01 — Lignes observees (JSON metier)','01_observed_records','none'),('P02 — Attendues (contrat)','02_expected','none'),('P03 — Validees (simulation)','03_accepted','none'),('P04 — Rejetees','04_rejected','none'),('P05 — Manquantes avant lecture','05_missing','none'),('P06 — Validees / attendues','06_completeness','percentunit')]
for i,(title,key,unit) in enumerate(stats):
    item=panel(i+2,title,'stat',queries[key],i*4,4,w=4,h=4,unit=unit,instant=True)
    item['options']={'reduceOptions':{'calcs':['lastNotNull'],'fields':'','values':False},'colorMode':'value','graphMode':'none'}
item=panel(8,'P07 — Lignes par corpus, fenetre 10s','timeseries',queries['07_timeline'],0,8,w=12,h=8)
item['targets'][0].update(legendFormat='{{dataset_value}}',interval='10s')
item=panel(9,'P08 — Reponses HTTP par code','bargauge',queries['08_http_codes'],12,8,w=6,h=8,instant=True)
item['targets'][0]['legendFormat']='{{status_value}}'
item['options']={'orientation':'horizontal','displayMode':'gradient','reduceOptions':{'calcs':['lastNotNull'],'fields':'','values':False}}
item=panel(10,'P09 — 5xx / statuts HTTP reconnus','stat',queries['09_http_5xx_ratio'],18,8,w=6,h=8,unit='percentunit',instant=True)
item['options']={'reduceOptions':{'calcs':['lastNotNull'],'fields':'','values':False},'graphMode':'none'}
def extract_numeric(item,field,keep_time):
    names=['Time',field] if keep_time else [field]
    item['transformations']=[{'id':'extractFields','options':{'source':'Line','format':'json','replace':True,'keepTime':True}},
       {'id':'convertFieldType','options':{'conversions':[{'targetField':field,'destinationType':'number'}]}},
       {'id':'filterFieldsByName','options':{'include':{'names':names}}}]
item=panel(11,'P10 — Histogramme des tailles HTTP observees','histogram',queries['10_access_observations'],0,16,w=12,h=9,unit='bytes')
extract_numeric(item,'response_bytes',False);item['options']={'bucketSize':1000,'bucketOffset':0,'combine':True}
item=panel(12,'P11 — Heatmap tailles HTTP / temps de collecte','heatmap',queries['10_access_observations'],12,16,w=12,h=9,unit='bytes')
extract_numeric(item,'response_bytes',True)
item['options']={'calculate':True,'calculation':{'xBuckets':{'mode':'size','value':'5s'},'yBuckets':{'mode':'size','value':'1000'}},'cellGap':1}
item=panel(13,'P12 — Heatmap retard source simule / collecte','heatmap',queries['19_delay_observations'],0,25,w=12,h=9,unit='s')
extract_numeric(item,'source_delay_seconds',True)
item['options']={'calculate':True,'calculation':{'xBuckets':{'mode':'size','value':'5s'},'yBuckets':{'mode':'size','value':'60'}},'cellGap':1}
item=panel(14,'P13 — Retard source max observe, non actuel','stat',queries['12_max_observed_delay'],12,25,w=4,h=9,unit='s',instant=True)
item['options']={'reduceOptions':{'calcs':['lastNotNull'],'values':False},'graphMode':'none'}
item=panel(15,'P14 — Derniere date source observee','stat',queries['13_last_source_timestamp'],16,25,w=8,h=9,unit='dateTimeAsIso',instant=True)
item['targets'][0]['legendFormat']='{{dataset_value}}'
item['options']={'reduceOptions':{'calcs':['lastNotNull'],'values':False},'graphMode':'none'}
item=panel(16,'P15 — Validees / attendues par corpus','bargauge',queries['14_completeness_by_dataset'],0,34,w=8,h=9,unit='percentunit',instant=True)
item['targets'][0]['legendFormat']='{{dataset_value}}'
item['options']={'orientation':'horizontal','reduceOptions':{'calcs':['lastNotNull'],'values':False}}
item=panel(17,'P16 — Batches et contrat de donnees','table',queries['15_batch_table'],8,34,w=16,h=9)
keep=['Time','phase','source_dataset','batch_id','expected','attempted','accepted_count','rejected_count','missing_count','source_delay_seconds']
item['transformations']=[{'id':'extractFields','options':{'source':'Line','format':'json','replace':True,'keepTime':True}}, {'id':'filterFieldsByName','options':{'include':{'names':keep}}}]
item['fieldConfig']['overrides']=[{'matcher':{'id':'byName','options':'batch_id'},'properties':[{'id':'links','value':[{'title':'Investiguer ce batch','url':'/d/a13bis-investigation/detail?var-run=${run}&var-event_id=${__data.fields.batch_id}&from=${__from}&to=${__to}','targetBlank':False}]}]}]
item=panel(18,'P17 — Rejets par regle de qualite','bargauge',queries['16_rejected_by_reason'],0,43,w=12,h=8,instant=True)
item['targets'][0]['legendFormat']='{{reason}}';item['options']={'orientation':'horizontal','reduceOptions':{'calcs':['lastNotNull'],'values':False}}
item=panel(19,'P18 — Temps du generateur par batch (pas HTTP)','histogram',queries['15_batch_table'],12,43,w=12,h=8,unit='ms')
extract_numeric(item,'processing_duration_ms',False);item['options']={'bucketSize':100,'bucketOffset':0,'combine':True}
item=panel(20,'P19 — Investigation des evenements','logs',queries['17_investigation_logs'],0,51,w=24,h=11)
item['options']={'showTime':True,'showLabels':False,'enableLogDetails':True,'sortOrder':'Ascending','dedupStrategy':'none','wrapLogMessage':True}
dashboard['panels'].append({'id':21,'title':'P20 — Lecture et limites','type':'text','gridPos':{'x':0,'y':62,'w':24,'h':5},'options':{'mode':'markdown','content':'Complétude = validées/attendues du contrat, pas garantie de chargement dans une destination externe. Retard mesuré à l’observation ≠ fraîcheur actuelle. Les bornes, limites de lignes et doublons doivent être contrôlés. Cliquer un batch ouvre le dashboard de détail. Elasticsearch est une extension du support.'}})
item=panel(22,'P21 — Somme des octets des sondes HTTP','stat',queries['23_bytes_total'],0,67,w=6,h=5,unit='bytes',instant=True)
item['options']={'reduceOptions':{'calcs':['lastNotNull'],'values':False},'graphMode':'none'}
item=panel(23,'P22 — Debit de records, fenetre 10s','timeseries',queries['22_rate_by_dataset'],6,67,w=12,h=8,unit='ops')
item['targets'][0].update(legendFormat='{{dataset_value}}',interval='10s')
item=panel(24,'P23 — Decisions par record','bargauge',queries['24_record_status'],18,67,w=6,h=8,instant=True)
item['targets'][0]['legendFormat']='accepted={{accepted_value}}'
item['options']={'orientation':'horizontal','reduceOptions':{'calcs':['lastNotNull'],'values':False}}
(base/'dashboard13bis-grafana.json').write_text(json.dumps(dashboard,ensure_ascii=False,indent=2),encoding='utf-8')
detail=copy.deepcopy(dashboard)
detail.update(uid='a13bis-investigation',title='[A13bis] Investigation par evenement ou batch')
detail['templating']['list']=[copy.deepcopy(variables[0]),copy.deepcopy(variables[1]),{'name':'event_id','label':'Evenement ou prefixe de batch','type':'textbox','query':'','current':{'text':'','value':''}}]
detail['panels']=[{'id':1,'title':'JSON et logs bruts correles','type':'logs','datasource':source,'gridPos':{'x':0,'y':0,'w':24,'h':18},
                   'targets':[target('{job=~"atelier13bis_raw|atelier13bis"} |= "${run}" |= "${event_id}"')],
                   'options':{'showTime':True,'enableLogDetails':True,'wrapLogMessage':True,'dedupStrategy':'none','sortOrder':'Ascending'}}]
(base/'dashboard13bis-investigation.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2),encoding='utf-8')
resolved=base/'requetes-api';resolved.mkdir()
seconds=math.ceil((int(r['to_ns'])-int(r['from_ns']))/1_000_000_000)
for name,expr in queries.items():
    expr=expr.replace('${run}',m['run_id']).replace('${dataset:regex}','.*').replace('${phase:regex}','.*').replace('$__range',f'{seconds}s')
    (resolved/(name+'.logql')).write_text(expr+'\n',encoding='utf-8')
print(json.dumps({'dashboard':str(base/'dashboard13bis-grafana.json'),'panels':len(dashboard['panels']),'api_queries':len(queries),'time_window_seconds':seconds,'note':'JSON genere ; import et transformations a verifier sur Grafana'},indent=2))
