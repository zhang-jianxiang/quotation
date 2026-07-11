import json

with open('genset_price_catalog.json', encoding='utf-8') as f:
    data = json.load(f)

kws = sorted(set(r['genset_kw'] for r in data if r.get('genset_kw')))

def fmt(k):
    return str(int(k)) if k == int(k) else str(k)

with open('power_list.txt', 'w', encoding='utf-8') as f:
    f.write(', '.join(fmt(k) for k in kws))

print(f"Extracted {len(kws)} unique power values")
