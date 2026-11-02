from pathlib import Path
import json,math
R=Path(__file__).resolve().parent;A=R.parents[2];D=json.loads((A/'Clarity37/Exports/airport_layout.json').read_text());N=json.loads((R.parent/'AuditInventory38.json').read_text());S=json.loads((R.parent/'SourceInventory38.json').read_text())
def key(q):return any(x in q.get('actor','').lower() for x in ['bridge','tug','dolly','ramp','welcome','boarding desk']) or any(x in q.get('mesh','') for x in ['ExteriorAirframe','ServicePath','Ground12','Counter34'])
native=[q for q in N['actors'] if key(q)]
source=[q for q in S['assets'] if q['asset'] in ['SM_AP_BridgeFloor','SM_AP_BridgeWall','SM_AP_BridgeRoof','SM_AP_Jetbridge34','SM_AP_ServicePath12','SM_Plane_ExteriorAirframe','SM_AP_Counter34']]
(R/'selected_inventory.json').write_text(json.dumps(dict(native=native,source=source),indent=2))
for q in native:
 print(q['actor'],q.get('instance'),q.get('bounds_min'),q.get('bounds_max'),'hidden',q.get('hidden'),'physics',q.get('simulate_physics'))
print('AIRFRAME PARTS')
for q in source:
 if q['asset']=='SM_Plane_ExteriorAirframe':
  for p in q['parts']:
   if any(k in p['name'].lower() for k in ['wing','forebody','nose','tail']):print(p['name'],p['min'],p['max'])
