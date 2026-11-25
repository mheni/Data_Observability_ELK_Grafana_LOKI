import argparse
import copy
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Generer un JSON Grafana de secours pour le defi 13, sans le publier dans Grafana')
p.add_argument('--manifest', default='preparation_defi13/manifest.json')
p.add_argument('--reference', default='reference_loki_defi13.json')
p.add_argument('--output-dir', default='livrables_defi13')
a = p.parse_args()
m = json.loads(Path(a.manifest).read_text(encoding='utf-8'))
r = json.loads(Path(a.reference).read_text(encoding='utf-8'))
if r['lot'] != m['lot'] or r['source_sha256'] != m['source_sha256']:
    p.error('Manifeste et reference ne decrivent pas le meme lot')
if r['observed'] != {'raw': m['expected_per_stream'], 'json': m['expected_per_stream']}:
    p.error('Les volumes Loki ne sont pas confirmes')
out = Path(a.output_dir)
if out.exists():
    p.error('Dossier de sortie existant')
out.mkdir(parents=True)
registry = json.loads((Path(__file__).resolve().parent / 'registre_panneaux_defi13.json').read_text(encoding='utf-8'))
ds = {'type': 'loki', 'uid': '${loki_ds}'}
variables = [
    {'name': 'loki_ds', 'label': 'Source Loki', 'type': 'datasource', 'query': 'loki', 'current': {}},
    {'name': 'lot', 'label': 'Lot OpenSSH', 'type': 'textbox', 'query': m['lot'], 'current': {'text': m['lot'], 'value': m['lot']}},
]
dash = {'id': None, 'uid': 'd13-openssh-diagnostic', 'title': '[D13] OpenSSH — diagnostic Loki', 'schemaVersion': 39, 'version': 1,
        'editable': True, 'timezone': 'utc', 'refresh': '', 'time': {'from': r['from_utc'], 'to': 'now'},
        'tags': ['formation', 'defi13', 'openssh'], 'templating': {'list': variables}, 'panels': []}
text = ('### Lire ce tableau de bord\n- Source : Loghub OpenSSH_2k.log, SHA-256 ' + m['source_sha256'] + '.\n- Lot Loki : ${lot}.\n'
        '- Temps Loki = collecte ; l’heure syslog est un champ de contenu et le journal n’a pas d’année.\n'
        '- Une ligne n’est ni une session ni une personne ; une IP n’est pas un individu.\n'
        '- Les compteurs Stat portent les totaux ; tables, tops et logs affichent des extraits.\n'
        '- Un suffixe de nom d’hôte n’est pas une géolocalisation.')
table_fields = {'table_ip': ('source_ip', 'IP'), 'table_user': ('user_name', 'Utilisateur')}
y = 0
for number, panel in enumerate(registry, 1):
    kind = panel['kind']
    instant = kind in ('stat', 'piechart', 'bargauge')
    h = 5 if kind == 'stat' else 9
    wide = kind in ('timeseries', 'barchart', 'table', 'logs', 'text', 'bargauge')
    item = {'id': number, 'title': panel['id'] + ' — ' + panel['title'], 'description': panel['limit'], 'type': kind,
            'gridPos': {'x': 0, 'y': y, 'w': 24 if wide else 12, 'h': h}, 'options': {}, 'fieldConfig': {'defaults': {'noValue': 'No data'}, 'overrides': []}}
    y += h
    if kind == 'text':
        item['options'] = {'mode': 'markdown', 'content': text}
        dash['panels'].append(item)
        continue
    item['datasource'] = copy.deepcopy(ds)
    targets = []
    for i, query in enumerate(panel['queries']):
        t = {'refId': chr(65 + i), 'datasource': copy.deepcopy(ds), 'editorMode': 'code', 'expr': query['expr'],
             'queryType': 'instant' if query['type'] == 'instant' else 'range', 'instant': query['type'] == 'instant', 'range': query['type'] != 'instant',
             'maxLines': panel.get('logs_limit') or 500}
        if query.get('legend'):
            t['legendFormat'] = query['legend']
        if kind == 'timeseries':
            t['interval'] = '1s'
        targets.append(t)
    item['targets'] = targets
    item['fieldConfig']['defaults'].update({'unit': panel['unit'], 'decimals': panel['decimals']})
    if kind == 'stat':
        item['options'] = {'reduceOptions': {'calcs': ['lastNotNull'], 'values': False}, 'graphMode': 'none', 'colorMode': 'value'}
    elif kind == 'bargauge':
        item['options'] = {'orientation': 'horizontal', 'reduceOptions': {'calcs': ['lastNotNull'], 'values': False}}
    elif kind == 'piechart':
        item['options'] = {'pieType': 'donut', 'legend': {'displayMode': 'list', 'placement': 'right', 'values': ['value', 'percent']}, 'tooltip': {'mode': 'single'}}
    elif kind == 'logs':
        item['options'] = {'showTime': True, 'enableLogDetails': True, 'wrapLogMessage': True, 'dedupStrategy': 'none', 'sortOrder': 'Ascending'}
    elif kind in ('barchart', 'table'):
        transform = panel['extra']['transform']
        item['transformations'] = [{'id': 'extractFields', 'options': {'source': 'Line', 'format': 'json', 'replace': True, 'keepTime': False}}]
        if transform == 'hour_count':
            item['transformations'] += [
                {'id': 'groupBy', 'options': {'fields': {'hour': {'operation': 'groupby'}, 'record_id': {'operation': 'aggregate', 'aggregations': ['count']}}}},
                {'id': 'sortBy', 'options': {'sort': [{'field': 'hour'}]}}]
            item['options'] = {'xField': 'hour', 'orientation': 'auto', 'showValue': 'auto', 'stacking': 'none'}
        elif transform == 'hour_outcome':
            item['transformations'] += [
                {'id': 'groupBy', 'options': {'fields': {'hour': {'operation': 'groupby'}, 'is_failure': {'operation': 'aggregate', 'aggregations': ['sum']}, 'is_success': {'operation': 'aggregate', 'aggregations': ['sum']}}}},
                {'id': 'sortBy', 'options': {'sort': [{'field': 'hour'}]}}]
            item['options'] = {'xField': 'hour', 'orientation': 'auto', 'showValue': 'auto', 'stacking': 'normal'}
        else:
            key, label = table_fields[transform]
            item['transformations'] += [
                {'id': 'groupBy', 'options': {'fields': {key: {'operation': 'groupby'}, 'record_id': {'operation': 'aggregate', 'aggregations': ['count']},
                                                          'is_auth_record': {'operation': 'aggregate', 'aggregations': ['sum']},
                                                          'is_failure': {'operation': 'aggregate', 'aggregations': ['sum']},
                                                          'is_success': {'operation': 'aggregate', 'aggregations': ['sum']}}}},
                {'id': 'calculateField', 'options': {'mode': 'binary', 'binary': {'left': 'is_failure (sum)', 'operator': '/', 'right': 'is_auth_record (sum)'}, 'alias': 'Part d’échec'}},
                {'id': 'organize', 'options': {'renameByName': {key: label, 'record_id (count)': 'Messages', 'is_auth_record (sum)': 'Canoniques', 'is_failure (sum)': 'Échecs', 'is_success (sum)': 'Succès'}}},
                {'id': 'sortBy', 'options': {'sort': [{'field': 'Échecs', 'desc': True}]}},
                {'id': 'limit', 'options': {'limitField': 10}}]
            item['fieldConfig']['overrides'] = [{'matcher': {'id': 'byName', 'options': 'Part d’échec'}, 'properties': [{'id': 'unit', 'value': 'percentunit'}, {'id': 'decimals', 'value': 2}]}]
    dash['panels'].append(item)
assert len(dash['panels']) == 25
(out / 'dashboard_defi13.json').write_text(json.dumps(dash, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'file': str(out / 'dashboard_defi13.json'), 'panels': len(dash['panels']), 'grafana_published': False}, indent=2))
