import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser(description='Verification bloquante des reponses du defi OpenSSH')
p.add_argument('mode',choices=['bulk','simulate','validation'])
p.add_argument('response')
p.add_argument('--preparation',required=True)
a=p.parse_args()
try:
    r=json.loads(Path(a.response).read_text(encoding='utf-8'))
    prep=json.loads(Path(a.preparation).read_text(encoding='utf-8'))
    if 'error' in r or r.get('timed_out') or r.get('_shards',{}).get('failed',0):
        raise ValueError('Erreur globale, timeout ou shard en echec : '+str(r)[:1800])
    if a.mode=='bulk':
        items=r.get('items')
        if not isinstance(items,list) or not isinstance(r.get('errors'),bool):
            raise ValueError('Reponse non Bulk')
        bad=[]
        for item in items:
            d=next(iter(item.values()))
            if not 200<=d.get('status',0)<300 or d.get('error'):
                bad.append(d)
        if bad or r['errors'] or len(items)!=prep['documents']:
            raise ValueError(f'Items={len(items)}, attendus={prep["documents"]}, erreurs={bad[:3]}')
        print(json.dumps({'OK':True,'operations':len(items)},indent=2))
    elif a.mode=='simulate':
        docs=r.get('docs',[])
        if not docs:
            raise ValueError('Simulation vide : aucune IP publique extraite ?')
        if any('error' in d or 'doc' not in d for d in docs):
            raise ValueError('Erreur dans une simulation : '+str(docs)[:1800])
        located=sum(bool(d['doc'].get('_source',{}).get('source_geo',{}).get('location')) for d in docs)
        tags=sorted({t for d in docs for t in d['doc'].get('_source',{}).get('tags',[])})
        print(json.dumps({'documents_simules':len(docs),'geolocalises':located,'tags':tags},indent=2))
        if not located:
            raise ValueError('Aucune coordonnee : preparer la base GeoIP ou utiliser le cache reel avant le TP')
    else:
        total=r['hits']['total']
        if total['relation']!='eq' or total['value']!=prep['documents']:
            raise ValueError('Volume destination different du rapport : index non vide ou import incomplet')
        ag=r['aggregations']
        if ag['missing_date']['doc_count']:
            raise ValueError('Documents sans date')
        if not ag['located']['doc_count']:
            raise ValueError('Aucune coordonnee : la carte du defi ne peut pas etre validee')
        local=prep['event_types_and_quality']
        expected_auth=local.get('auth_failure',0)+local.get('auth_success',0)
        for name,expect in [('auth_records',expected_auth),('failures',local.get('auth_failure',0)),('successes',local.get('auth_success',0)),('with_ip',local.get('with_ip',0))]:
            if ag[name]['doc_count']!=expect:
                raise ValueError('Ecart de compteur : '+name)
        print(json.dumps({'OK':True,'documents':total['value'],'first_event':ag['first_event'].get('value_as_string'),'last_event':ag['last_event'].get('value_as_string'),'located':ag['located']['doc_count'],'with_ip':ag['with_ip']['doc_count']},indent=2))
except (ValueError,KeyError,TypeError,OSError,StopIteration) as exc:
    raise SystemExit('ECHEC : '+str(exc))
