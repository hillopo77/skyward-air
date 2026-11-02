import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[1];p=R.parent.parent/'SkywardAir/Revision18/Plane_Refined18.blend'
with bpy.data.libraries.load(str(p),link=False) as (src,dst):dst.collections=['SM_Plane_LandingGear']
c=dst.collections[0];bpy.context.scene.collection.children.link(c);bpy.context.view_layer.update();rows=[]
for o in c.objects:
 if o.type!='MESH':continue
 pts=[o.matrix_world@Vector(x) for x in o.bound_box]
 rows.append(dict(name=o.name,min=[min(p[i] for p in pts) for i in range(3)],max=[max(p[i] for p in pts) for i in range(3)]))
(ROOT/'ActualGearContacts39.json').write_text(json.dumps(rows,indent=2))
print(json.dumps([q for q in rows if any(k in q['name'].lower() for k in ('tyre','tire','wheel','oleo','strut'))],indent=1))
