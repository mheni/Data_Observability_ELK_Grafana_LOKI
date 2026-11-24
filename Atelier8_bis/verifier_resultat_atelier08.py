import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description="Verifier une reponse Elasticsearch de l'atelier 8")
p.add_argument('mode', choices=['simulate', 'reindex', 'bornes', 'bulk'])
p.add_argument('response')
p.add_argument('--expected', type=int)
a = p.parse_args()
try:
    r = json.loads(Path(a.response).read_text(encoding='utf-8'))
    if not isinstance(r, dict) or 'error' in r:
        raise ValueError('Erreur globale ou reponse non objet : ' + str(r)[:2000])
    if r.get('_shards', {}).get('failed', 0):
        raise ValueError('Une ou plusieurs recherches de shard ont echoue')
    if r.get('timed_out', False):
        raise ValueError('Requete expiree : resultat potentiellement incomplet')
    if a.mode == 'simulate':
        results = r.get('docs')
        if not isinstance(results, list) or not results:
            raise ValueError('Aucun resultat de simulation')
        for i, item in enumerate(results):
            if 'error' in item or not isinstance(item.get('doc'), dict):
                raise ValueError(f'Simulation document {i}: {item}')
            s = item['doc'].get('_source', {})
            for field in ['ingested_at', 'dataset', 'status_class', 'url_path']:
                if field not in s:
                    raise ValueError(f'Document {i}: champ attendu absent: {field}')
        summary = {'documents_simules': len(results)}
    elif a.mode == 'reindex':
        if not all(k in r for k in ['total', 'created', 'failures', 'version_conflicts']):
            raise ValueError('Reponse synchrone de reindexation incomplete')
        if r['failures'] or r['version_conflicts']:
            raise ValueError('Echec partiel/conflit : ne pas relancer aveuglement. ' + json.dumps(r)[:4000])
        if r['total'] < 1 or r['created'] != r['total'] or r.get('updated', 0):
            raise ValueError('Source vide, documents non crees ou mise a jour inattendue')
        if a.expected is not None and r['created'] != a.expected:
            raise ValueError('Nombre cree different du nombre source attendu')
        summary = {k: r[k] for k in ['total', 'created', 'version_conflicts']}
    elif a.mode == 'bornes':
        aggs = r.get('aggregations', {})
        for key in ['premier_evenement', 'dernier_evenement']:
            if not aggs.get(key, {}).get('value_as_string'):
                raise ValueError('Date absente pour ' + key)
        summary = {k: aggs[k]['value_as_string'] for k in ['premier_evenement', 'dernier_evenement']}
    else:
        items = r.get('items')
        if not isinstance(items, list) or not items or not isinstance(r.get('errors'), bool):
            raise ValueError('Reponse Bulk vide ou incomplete')
        errors = []
        for item in items:
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError('Item Bulk non reconnu')
            detail = next(iter(item.values()))
            if not 200 <= detail.get('status', 0) < 300 or detail.get('error'):
                errors.append(detail)
        if r['errors'] or errors:
            raise ValueError('Echecs Bulk : ' + json.dumps(errors[:3])[:4000])
        if a.expected is not None and len(items) != a.expected:
            raise ValueError('Nombre operations Bulk incorrect')
        summary = {'operations_reussies': len(items)}
except (OSError, ValueError, KeyError, TypeError) as exc:
    raise SystemExit('ECHEC : ' + str(exc))
print(json.dumps({'validation': 'OK', 'mode': a.mode, **summary}, ensure_ascii=False, indent=2))
