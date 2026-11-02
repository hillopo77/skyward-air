"""Read-only targeted library inspection of current modeled aircraft fittings."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[2]
IDS=['SM_Plane_WindowWall_L','SM_Plane_WindowWall_R','SM_Plane_OuterWindowBarrel','SM_Plane_DoorBay07',
     'SM_Plane_PassengerDoor07_L','SM_Plane_PassengerDoor07_R','SM_Plane_ExitHingeHardware12','SM_Plane_CabinFinish09','SM_Plane_CockpitShell']
with bpy.data.libraries.load(str(R/'Airport_Repaired38.blend'),link=False) as (src,dst):dst.collections=[n for n in IDS if n in src.collections]
loaded=list(dst.collections);missing=[n for n in IDS if n not in {c.name for c in loaded if c}]
if missing:
 with bpy.data.libraries.load(str(R.parent.parent/'SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=missing
 loaded+=list(dst.collections)
rows=[]
for c in loaded:
 if not c:continue
 bpy.context.scene.collection.children.link(c)
 for o in c.objects:
  if o.type!='MESH':continue
  points=[o.matrix_world@Vector(p) for p in o.bound_box]
  rows.append(dict(asset=c.name,name=o.name,vertices=len(o.data.vertices),faces=len(o.data.polygons),
   min=[min(p[i] for p in points) for i in range(3)],max=[max(p[i] for p in points) for i in range(3)],
   materials=[m.name for m in o.data.materials if m],modifiers=[dict(type=m.type,name=m.name,width=m.width if m.type=='BEVEL' else None) for m in o.modifiers]))
(ROOT/'SourceFittingsInventory39.json').write_text(json.dumps(rows,indent=2))
print('FITTINGS39',len(rows),'mesh parts')
for q in rows:
 if q['asset']=='SM_Plane_CockpitShell' or q['asset']=='SM_Plane_WindowWall_L':print(q['asset'],q['name'],q['min'],q['max'],q['modifiers'])
