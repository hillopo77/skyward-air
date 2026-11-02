import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
p=R.parents[2]/'Airport_Repaired38.blend'
bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False)
print('MATCHING COLLECTIONS',[c.name for c in bpy.data.collections if any(t in c.name.lower() for t in ['analog','exteriorair','cockpit'])],flush=True)
cols=[c for c in bpy.data.collections if any(t in c.name.lower() for t in ['analogdashboard','exteriorairframe'])]
data={}
for c in cols:
 if not c:continue
 bpy.context.scene.collection.children.link(c);bpy.context.view_layer.update()
 data[c.name]=[]
 for o in c.objects:
  if c.name=='SM_Plane_ExteriorAirframe' and not o.name.startswith(('Independent trailing flap','Independent outboard','Separate hinged elevator','Separate vertical rudder')):continue
  if o.type not in {'MESH','FONT'}:continue
  from mathutils import Vector
  pts=[o.matrix_world@Vector(p) for p in o.bound_box]
  data[c.name].append(dict(name=o.name,type=o.type,bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],body=o.data.body if o.type=='FONT' else None))
(R/'cockpit_source_inventory39.json').write_text(json.dumps(data,indent=2))
print('FLIGHT39_INSPECT',[(k,len(v)) for k,v in data.items()])
