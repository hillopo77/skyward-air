"""Genuine source view of the repaired fascia and retained controls."""
import bpy
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent
with bpy.data.libraries.load(str(F/'ConsoleSurface43_UnitKit.blend'),link=False) as (src,dst):dst.collections=['SM_AP_C43DashboardFixed']
s=bpy.context.scene
for ob in list(s.objects):bpy.data.objects.remove(ob,do_unlink=True)
c=dst.collections[0];c.hide_render=False
for ob in c.objects:ob.hide_render=False
o=bpy.data.objects.new('C43 actual source dashboard',None);o.instance_type='COLLECTION';o.instance_collection=c;s.collection.objects.link(o)
w=bpy.data.worlds.new('Source studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.29,.34,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.65;s.world=w
for p,power in [((.4,-3,2.5),180),((-1.4,-4.0,2),70)]:
 d=bpy.data.lights.new('Soft actual source light','AREA');d.energy=power;d.size=1.8;ob=bpy.data.objects.new(d.name,d);s.collection.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector((0,-4.4,1.1))-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('C43 fascia source camera');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);cam.location=(.28,-3.20,1.36);cam.rotation_euler=(Vector((0,-4.43,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=57;s.camera=cam
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=900;s.render.resolution_y=650;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(F/'ConsoleSurface43_SourcePreview.png');bpy.ops.render.render(write_still=True)
