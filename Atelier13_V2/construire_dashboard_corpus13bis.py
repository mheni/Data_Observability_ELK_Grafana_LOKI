import argparse
import copy
import json
from pathlib import Path
p=argparse.ArgumentParser(description='JSON de secours du dashboard access complet ; ne publie pas dans Grafana')
p.add_argument('--manifest',default='preparation13bis.json')
p.add_argument('--reference',default='reference-normalisation13bis-corpus.json')
p.add_argument('--output-dir',default='livrables13bis-corpus')
a=p.parse_args()
m=json.loads(Path(a.manifest).read_text());r=json.loads(Path(a.reference).read_text())
if m['normalization_id']!=r['normalization_id']:p.error('NID different')
if int(m['access'])<10000:p.error('Manifeste sans le corpus complet attendu')
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie existant')
base.mkdir(parents=True)
here=Path(__file__).resolve().parent
q=json.loads((here/'requetes_dashboard_corpus13bis.json').read_text())
registry=json.loads((here/'registre_panneaux_corpus13bis.json').read_text())
ds={'type':'loki','uid':'${loki_ds}'}
d={'id':None,'uid':'a13bis-access-corpus','title':'[A13bis] Access complet — diagnostic Loki','schemaVersion':39,'version':1,'timezone':'utc',
   'editable':True,'refresh':'','tags':['formation','a13bis','access-complet'],
   'time':{'from':r['from_utc'],'to':r['to_utc']},
   'templating':{'list':[{'name':'loki_ds','label':'Source Loki','type':'datasource','query':'loki','current':{}},
                         {'name':'nid','label':'Lot access normalisé','type':'textbox','query':m['normalization_id'],
                          'current':{'text':m['normalization_id'],'value':m['normalization_id']}}]},'panels':[]}
def textpanel(pid,title,content,y):
    return {'id':pid,'title':title,'type':'text','gridPos':{'x':0,'y':y,'w':24,'h':5},'options':{'mode':'markdown','content':content}}
d['panels'].append(textpanel(100,'P00 — Périmètre et méthode','Corpus access complet du lot ${nid}. Les copies JSON/logfmt/brutes ne sont pas additionnées. Time Loki = collecte ; apache_time = date source. Aucune latence HTTP mesurée.',0))
y=5
for index,panel in enumerate(registry,1):
    kind=panel['kind'];instant=kind in ['stat','bargauge','bins']
    kindmap={'bins':'bargauge','table':'table','logs':'logs','stat':'stat','timeseries':'timeseries','bargauge':'bargauge','histogram':'histogram','heatmap':'heatmap'}
    def target(expr,refid='A',legend=None):
        t={'refId':refid,'datasource':copy.deepcopy(ds),'editorMode':'code','expr':expr,'queryType':'instant' if instant else 'range','instant':instant,'range':not instant,'maxLines':500}
        if legend:t['legendFormat']=legend
        if kind=='timeseries':t['interval']='1s'
        return t
    targets=[target(q[panel['key']],legend=panel.get('legend'))] if kind!='bins' else [target(q['bin_'+str(i)],chr(64+i),label) for i,label in enumerate(['1–999','1000–9999','10000–99999','100000–999999','≥1000000'],1)]
    if kind=='stat':
        position={'x':((index-1)%6)*4,'y':y,'w':4,'h':5}
        if index==1 or registry[index-2]['kind']!='stat':position['x']=0
        if index>1 and registry[index-2]['kind']=='stat' and (index-1)%6==0:y+=5;position['y']=y
    else:position={'x':0,'y':y,'w':24,'h':9}
    # Explicit vertical flow is robust even if not as compact as the manual layout.
    position={'x':0,'y':y,'w':24 if kind in ['bins','table','logs','timeseries'] else 12,'h':5 if kind=='stat' else 9}
    y+=position['h']
    item={'id':index,'title':panel['id']+' — '+panel['title'],'type':kindmap[kind],'datasource':copy.deepcopy(ds),'gridPos':position,
          'description':panel['note'],'targets':targets,'options':{},'fieldConfig':{'defaults':{'unit':panel['unit'] if panel['unit']=='percentunit' else 'none','decimals':panel['dec'],'noValue':'No data'},'overrides':[]}}
    if kind=='stat':item['options']={'reduceOptions':{'calcs':['lastNotNull'],'values':False},'graphMode':'none','colorMode':'value'}
    if kind in ['bargauge','bins']:item['options']={'orientation':'horizontal','reduceOptions':{'calcs':['lastNotNull'],'values':False}}
    if kind in ['table','histogram','heatmap']:
        fields=['Time','source_line','client_ip','method','path','request_line','status','bytes','apache_time'] if kind=='table' else (['Time','bytes'] if kind=='heatmap' else ['bytes'])
        item['transformations']=[{'id':'extractFields','options':{'source':'Line','format':'json','replace':True,'keepTime':True}}]
        if kind=='table':item['transformations'].append({'id':'merge','options':{}})
        item['transformations'].extend([{'id':'convertFieldType','options':{'conversions':[{'targetField':'bytes','destinationType':'number'}]}},
                                       {'id':'filterFieldsByName','options':{'include':{'names':fields}}}])
    if kind=='histogram':item['options']={'bucketSize':10000,'bucketOffset':0,'combine':True}
    if kind=='heatmap':item['options']={'calculate':True,'calculation':{'xBuckets':{'mode':'size','value':'5s'},'yBuckets':{'mode':'size','value':'10000'}}}
    if kind=='logs':item['options']={'showTime':True,'showLabels':False,'enableLogDetails':True,'wrapLogMessage':True,'dedupStrategy':'none','sortOrder':'Ascending'}
    d['panels'].append(item)
d['panels'].append(textpanel(123,'P23 — Limites','Volumes contrôlés par agrégations, pas identité de chaque ID en ligne. IP/chemins suivis = listes bornées. P18 = classes exhaustives des tailles connues ; P19/P20/P21/P22 = vues plafonnées. Les méthodes et tailles absentes ne sont pas des pertes de collecte.',y))
assert len(d['panels'])==24
(base/'dashboard13bis-access-corpus.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file':str(base/'dashboard13bis-access-corpus.json'),'panels':len(d['panels']),'grafana_published':False},indent=2))
