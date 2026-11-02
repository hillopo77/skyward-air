from pathlib import Path
import json,math,collections
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;Q=json.loads((R/'BaselineCapture38.json').read_text());inv=json.loads((R/'AuditInventory38.json').read_text());source=json.loads((R/'SourceInventory38.json').read_text());groups=collections.defaultdict(list)
for q in inv['actors']:
 if q['visible'] and not q['hidden']:groups[(q['mesh'],tuple(q['location']),tuple(q['rotation']))].append(q['actor'])
dupes=[dict(mesh=k[0],location=k[1],actors=v) for k,v in groups.items() if len(v)>1]
motion={}
for q in Q['samples']:
 for n,o in q['objects'].items():motion.setdefault(n,[]).append(o)
motion={n:dict(samples=len(xs),maximum_speed_m_s=max(v['speed'] for v in xs),range_m=[max(v['position'][i] for v in xs)-min(v['position'][i] for v in xs) for i in range(3)]) for n,xs in motion.items()}
variance={}
for prefix in ['33_CurtainHold','34_CeilingHold']:
 files=sorted((R/'BaselineScreenshots').glob(prefix+'*.png'));arr=[np.asarray(Image.open(p).convert('RGB'),dtype=np.float32) for p in files];d=[np.abs(a-b) for a,b in zip(arr[2:],arr[3:])];variance[prefix]=dict(frames=len(files),mean_absolute_rgb_delta_0_255=float(np.mean(d)),p99_rgb_delta_0_255=float(np.quantile(d,.99)),note='Native temporal image difference; does not itself prove physical movement or isolate AA/shadows.')
report=dict(exact_duplicate_placements=dupes,static_and_physics_motion=motion,frame_variance=variance,world_traces=Q['traces'],source_duplicate_face_parts=[dict(asset=q['asset'],part=p['name'],duplicates=p.get('duplicate_faces',0)) for q in source['assets'] for p in q['parts'] if p.get('duplicate_faces',0)])
(R/'BaselineAnalysis38.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(duplicate_placements=len(dupes),duplicate_face_parts=len(report['source_duplicate_face_parts']),motion=motion,variance=variance,traces=Q['traces']),indent=2))
