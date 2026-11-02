"""Two small genuine source-asset appearance checks; no shared edits."""
import bpy,math
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent;names=['SM_AP_A42ExpeditionDuffel','SM_AP_A42Weekender','SM_AP_A42PSUCarrier']
with bpy.data.libraries.load(str(F/'AircraftFinish42_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(names)
cols=dict(zip(names,dst.collections));s=bpy.context.scene
for ob in list(s.objects):bpy.data.objects.remove(ob,do_unlink=True)
w=bpy.data.worlds.new('Soft source-review environment');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.29,.32,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;s.world=w
for p,power,size in [((0,-2,2.5),100,2),((1,1,1.5),60,1.5)]:
    d=bpy.data.lights.new('Soft actual-source light','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,.1))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual-source inspection camera');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);s.camera=cam
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=800;s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
def inst(name,p,rot=0):
    c=cols[name];c.hide_render=False
    for ob in c.objects:ob.hide_render=False
    o=bpy.data.objects.new(name+' source preview',None);o.instance_type='COLLECTION';o.instance_collection=c;o.location=p;o.rotation_euler.x=rot;s.collection.objects.link(o);return o
objects=[inst(names[0],(-.24,0,0)),inst(names[1],(.40,.04,0))];cam.location=(1.0,-1.2,.92);cam.rotation_euler=(Vector((.05,0,.18))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=58;s.render.filepath=str(F/'AircraftFinish42_DrapedHandles.png');bpy.ops.render.render(write_still=True)
for o in objects:bpy.data.objects.remove(o,do_unlink=True)
inst(names[2],(0,0,0),math.pi);cam.location=(.40,-.48,.55);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=58;s.render.filepath=str(F/'AircraftFinish42_PSUFace.png');bpy.ops.render.render(write_still=True)
