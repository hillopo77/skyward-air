import bpy,json,sys,hashlib,collections
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;A=R.parents[1];D=json.loads((A/'Clarity37/Exports/airport_layout.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(A/'Clarity37/Airport_Clarity37.blend'),load_ui=False);rows=[]
ids={q['asset'] for q in D['instances']};dg=bpy.context.evaluated_depsgraph_get()
for col in bpy.data.collections:
 if col.name not in ids:continue
 parts=[]
 for o in col.objects:
  pts=[o.matrix_world@Vector(v) for v in o.bound_box];mn=[min(p[k] for p in pts) for k in range(3)];mx=[max(p[k] for p in pts) for k in range(3)]
  q=dict(name=o.name,type=o.type,min=[round(v,6) for v in mn],max=[round(v,6) for v in mx],materials=[m.name for m in getattr(o.data,'materials',[]) if m])
  if o.type=='FONT':q.update(text=o.data.body,location=list(o.location),rotation=list(o.rotation_euler))
  if o.type=='MESH':
   coords=[tuple(round(v,5) for v in o.matrix_world@p.co) for p in o.data.vertices];faces=[tuple(sorted(coords[i] for i in f.vertices)) for f in o.data.polygons];cnt=collections.Counter(faces);q.update(polygons=len(faces),duplicate_faces=sum(n-1 for n in cnt.values() if n>1))
  parts.append(q)
 rows.append(dict(asset=col.name,parts=parts))
(R/'SourceInventory38.json').write_text(json.dumps(dict(source=str(A/'Clarity37/Airport_Clarity37.blend'),assets=rows),indent=2));print('AUDIT38 source assets',len(rows))
