import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description='Verifier chaque resultat de la reponse Bulk')
p.add_argument('response')
p.add_argument('--preparation', required=True)
a = p.parse_args()
response = json.loads(Path(a.response).read_text(encoding='utf-8'))
expected = json.loads(Path(a.preparation).read_text(encoding='utf-8'))['documents']
if not isinstance(response.get('items'), list) or not isinstance(response.get('errors'), bool):
    raise SystemExit('Reponse non Bulk ou incomplete : ' + json.dumps(response, ensure_ascii=False)[:1500])
success = 0
errors = []
for item in response['items']:
    operation, detail = next(iter(item.items()))
    if 200 <= detail.get('status', 0) < 300 and not detail.get('error'):
        success += 1
    else:
        errors.append({'operation':operation, **detail})
report = {'expected':expected,'returned_items':len(response['items']),
          'success':success,'failed':len(errors),'errors_flag':response['errors']}
Path('bulk-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
Path('bulk-rejets.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
for item in errors[:3]:
    print(json.dumps(item, ensure_ascii=False, indent=2))
if errors or response['errors'] or len(response['items']) != expected:
    raise SystemExit(1)
