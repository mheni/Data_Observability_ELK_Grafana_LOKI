import argparse
import copy
import json
import math
import re
from pathlib import Path

p=argparse.ArgumentParser(description='Generer supports personnalises, requetes et JSON Grafana sans publier dans Grafana')
p.add_argument('--manifest',default='preparation13bis/manifest.json')
p.add_argument('--reference',default='reference13bis.json')
p.add_argument('--output-dir',default='livrables13bis')
a=p.parse_args();mp=Path(a.manifest);m=json.loads(mp.read_text());r=json.loads(Path(a.reference).read_text());lot=m['lot']
if not re.fullmatch(r'[A-Za-z0-9_.:-]+',lot):p.error('Lot invalide')
if r['lot']!=lot or r['source_sha256']!=m['source_sha256']:p.error('Manifeste/reference : lot ou empreinte differents')
if any(r.get('observed',{}).get(k)!=m['expected_per_format'] for k in ['raw','json','logfmt']):p.error('Les trois volumes ne sont pas confirmes')
seconds=math.ceil((int(r['to_ns'])-int(r['from_ns']))/1e9)
if seconds<1:p.error('Periode invalide')
base=Path(a.output_dir)
if base.exists():p.error('Dossier de sortie existant ; choisir un autre nom')
base.mkdir(parents=True)
here=Path(__file__).resolve().parent
ref=json.loads((mp.parent/m['reference_file']).read_text())
q=json.loads((here/'requetes_dashboard13bis.json').read_text());entries=json.loads((here/'requetes_explore13bis.json').read_text())
registry=json.loads((here/'registre_panneaux13bis.json').read_text())
context='\n\n> Lot : '+lot+' ; periode de collecte : '+r['from_utc']+' a '+r['to_utc']+' ; attendu par format : '+str(m['expected_per_format'])+'.\n\n'
for name in ['ATELIER_13BIS.md','GUIDE_60_REQUETES_EXPLORE.md']:
    text=(here/name).read_text(encoding='utf-8').replace('__LOT__',lot).replace('__DUREE__',str(seconds)+'s')
    first,sep,rest=text.partition('\n')
    (base/name.replace('.md','_PERSONNALISE.md')).write_text(first+context+rest,encoding='utf-8')
api=base/'requetes-api';api.mkdir();explore=base/'requetes-explore';explore.mkdir()
for key,expr in q.items():
    (api/(key+'.logql')).write_text(expr.replace('${lot}',lot).replace('$__range',str(seconds)+'s')+'\n',encoding='utf-8')
for e in entries:
    (explore/(e['id']+'.logql')).write_text(e['query'].replace('__LOT__',lot).replace('$__range',str(seconds)+'s')+'\n',encoding='utf-8')
# Build Grafana JSON files. Imports remain a manual action in Grafana.
ds={'type':'loki','uid':'${loki_ds}'}
variables=[{'name':'loki_ds','label':'Source Loki','type':'datasource','query':'loki','current':{}},
           {'name':'lot','label':'Lot access','type':'textbox','query':lot,'current':{'text':lot,'value':lot}}]
d={'id':None,'uid':'a13bis-access-dashboard','title':'[A13bis] Access logs — diagnostic Loki','schemaVersion':39,'version':1,'editable':True,
   'timezone':'utc','refresh':'','time':{'from':r['from_utc'],'to':r['to_utc']},'templating':{'list':variables},'tags':['formation','a13bis','access'],'panels':[]}
def textpanel(pid,title,body,y):return {'id':pid,'title':title,'type':'text','gridPos':{'x':0,'y':y,'w':24,'h':5},'options':{'mode':'markdown','content':body}}
d['panels'].append(textpanel(100,'P00 — Périmètre et méthode','Lot ${lot}. Les panneaux principaux utilisent le JSON de ce lot. Les trois représentations ne sont pas additionnées. Time Loki = collecte ; apache_time = date source. Aucune latence HTTP mesurée.',0))
y=5
for i,panel in enumerate(registry,1):
    kind=panel['kind'];instant=kind in ['stat','bargauge','bins']
    def target(expr,refid='A',legend=None):
        t={'refId':refid,'datasource':copy.deepcopy(ds),'editorMode':'code','expr':expr,'queryType':'instant' if instant else 'range','instant':instant,'range':not instant,'maxLines':500}
        if legend:t['legendFormat']=legend
        if kind=='timeseries':t['interval']='1s'
        return t
    targets=[target(q[panel['key']],legend=panel.get('legend'))] if kind!='bins' else [target(q['bin_'+str(k)],chr(64+k),b['label']) for k,b in enumerate(ref['size_bins'],1)]
    height=5 if kind=='stat' else 9
    item={'id':i,'title':panel['id']+' — '+panel['title'],'description':panel['note'],
          'type':'bargauge' if kind=='bins' else kind,'datasource':copy.deepcopy(ds),'targets':targets,
          'gridPos':{'x':0,'y':y,'w':12 if kind=='stat' else 24,'h':height},
          'fieldConfig':{'defaults':{'unit':panel['unit'],'noValue':'No data','decimals':3 if panel['unit']=='percentunit' else (2 if panel['key']=='bytes_mean' else 0)},'overrides':[]},'options':{}}
    y+=height
    if kind=='stat':item['options']={'reduceOptions':{'calcs':['lastNotNull'],'values':False},'graphMode':'none','colorMode':'value'}
    if kind in ['bargauge','bins']:item['options']={'orientation':'horizontal','reduceOptions':{'calcs':['lastNotNull'],'values':False}}
    if kind in ['table','histogram','heatmap']:
        names=['Time','source_line','client_ip','method','path','request_line','status','bytes','apache_time'] if kind=='table' else (['Time','bytes'] if kind=='heatmap' else ['bytes'])
        item['transformations']=[{'id':'extractFields','options':{'source':'Line','format':'json','replace':True,'keepTime':True}}]
        if kind=='table':item['transformations'].append({'id':'merge','options':{}})
        item['transformations'].extend([{'id':'convertFieldType','options':{'conversions':[{'targetField':'bytes','destinationType':'number'}]}},
                                       {'id':'filterFieldsByName','options':{'include':{'names':names}}}])
    if kind=='table':
        item['fieldConfig']['overrides']=[{'matcher':{'id':'byName','options':'client_ip'},'properties':[{'id':'links','value':[{'title':'Voir les logs de cette IP','url':'/d/a13bis-access-detail/detail?var-lot=${lot}&var-ip=${__data.fields.client_ip}&from=${__from}&to=${__to}','targetBlank':False}]}]}]
    if kind=='histogram':item['options']={'bucketSize':10000,'bucketOffset':0,'combine':True}
    if kind=='heatmap':item['options']={'calculate':True,'calculation':{'xBuckets':{'mode':'size','value':'5s'},'yBuckets':{'mode':'size','value':'10000'}}}
    if kind=='logs':item['options']={'showTime':True,'showLabels':False,'enableLogDetails':True,'wrapLogMessage':True,'dedupStrategy':'none','sortOrder':'Ascending'}
    d['panels'].append(item)
d['panels'].append(textpanel(123,'P23 — Couverture et limites','Volumes et distribution contrôlés, pas chaque ID en ligne. Tailles absentes ≠ zéro. IP/chemins suivis = sélections bornées. P18 = classes de la population connue ; P19/P20/P21/P22 = extraits ou échantillons.',y))
assert len(d['panels'])==24
(base/'dashboard13bis.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
detail=copy.deepcopy(d);detail.update(uid='a13bis-access-detail',title='[A13bis] Détail access par IP')
detail['templating']['list']=copy.deepcopy(variables)+[{'name':'ip','label':'IP source','type':'textbox','query':'54.210.20.202','current':{'text':'54.210.20.202','value':'54.210.20.202'}}]
expr='{job="atelier13bis",format="json",lot="${lot}"} | json v_ip="client_ip" | __error__="" | v_ip="${ip}"'
detail['panels']=[{'id':1,'title':'Preuves access pour l IP sélectionnée','type':'logs','datasource':copy.deepcopy(ds),'gridPos':{'x':0,'y':0,'w':24,'h':18},
 'targets':[{'refId':'A','datasource':copy.deepcopy(ds),'editorMode':'code','expr':expr,'queryType':'range','range':True,'instant':False,'maxLines':500}],
 'options':{'showTime':True,'enableLogDetails':True,'wrapLogMessage':True,'dedupStrategy':'none','sortOrder':'Ascending'}}]
(base/'dashboard13bis-detail.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'CONTEXTE.json').write_text(json.dumps({'lot':lot,'source_sha256':m['source_sha256'],'from_utc':r['from_utc'],'to_utc':r['to_utc'],'expected_per_format':m['expected_per_format'],'grafana_published':False},indent=2)+'\n')
print(json.dumps({'output_dir':str(base),'explore_queries':len(entries),'dashboard_panels':len(d['panels']),'grafana_published':False},indent=2))
