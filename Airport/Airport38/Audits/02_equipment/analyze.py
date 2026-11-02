from pathlib import Path
import json,re,math
R=Path(__file__).resolve().parent; A=R.parent
D=json.loads((A.parents[1]/'Clarity37/Exports/airport_layout.json').read_text())
N=json.loads((A/'AuditInventory38.json').read_text())
S=json.loads((A/'SourceInventory38.json').read_text())
relevant=re.compile('desk|scanner|belt|shelf|storage|kiosk|charging|coffee|bakery|tea|recycl|trolley|tray|carousel|vanity|toilet|exting|planter|plant|counter|portal',re.I)
rows=[q for q in D['instances'] if relevant.search(q['name']+' '+q['asset'])]
(R/'placements.json').write_text(json.dumps(rows,indent=2))
for q in rows:
 print(q['name'],q['asset'],q['location'],'r',q['rotation_degrees'],'s',q['scale'])
print('CONVEYORS',json.dumps(D['conveyors']))
print('SOURCE ASSET KEYS',S['assets'][0].keys())
for q in S['assets']:
 if relevant.search(q['asset']):
  print('ASSET',q['asset'],'parts',len(q['parts']),'keys',q.keys())
