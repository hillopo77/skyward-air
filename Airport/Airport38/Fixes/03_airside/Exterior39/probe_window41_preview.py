"""Identify actual source owners behind close-review image pixels."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent
text=(F/'render_window41_preview.py').read_text().split("for name,z in [('Standing'")[0]
exec(compile(text,str(F/'render_window41_preview.py'),'exec'))
cam.location=(1.,-.15,1.62);cam.rotation_euler=(Vector((2.38,0,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
frame=cd.view_frame(scene=scene);report=[]
for px,py in [(130,260),(132,320),(139,370),(148,450),(160,540),(540,310),(543,450),(320,200),(320,400)]:
    # Blender view-frame uses top-right,bottom-right,bottom-left,top-left order.
    u=px/640;v=py/800
    lo=frame[3]*(1-u)+frame[0]*u;hi=frame[2]*(1-u)+frame[1]*u;direction=(cam.rotation_euler.to_matrix()@(lo*(1-v)+hi*v)).normalized()
    hit,loc,norm,idx,ob,T=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction)
    report.append(dict(pixel=[px,py],hit=hit,owner=ob.name if ob else None,point=list(loc)))
(F/'Window41_PreviewOwners.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
