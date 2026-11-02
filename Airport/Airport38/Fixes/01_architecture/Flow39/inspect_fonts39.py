import bpy,json
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;R=HERE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'Airport_Repaired38.blend'),load_ui=False)
out=[]
for o in bpy.context.scene.objects:
 if o.type=='FONT':
  out.append(dict(name=o.name,text=o.data.body,location=list(o.location),collections=[c.name for c in o.users_collection],render=o.hide_render))
(HERE/'DirectFontInventory39.json').write_text(json.dumps(out,indent=2))
print('DIRECT_FONTS39',len(out),json.dumps([p for p in out if 'A07' in p['text'] or 'CAFE' in p['text']]))
