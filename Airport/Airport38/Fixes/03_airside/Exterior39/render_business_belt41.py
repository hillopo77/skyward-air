"""Actual final source body/chair/belt silhouette, CPU render only."""
import bpy,json
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent
names=['CHAR39_PassengerCrew_LuxurySeated','SM_AP_B40LuxurySeatBase','SM_AP_B40ReleaseLid','SM_AP_B41LapWornCrew']
with bpy.data.libraries.load(str(F/'BusinessBelt41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(names)
scene=bpy.context.scene
for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
meta=json.loads((F/'BusinessBelt41_Model.json').read_text())
for n,c in zip(names,dst.collections):
    c.hide_render=False;c.hide_viewport=False
    for part in c.objects:part.hide_render=False;part.hide_viewport=False
    o=bpy.data.objects.new(n+' genuine source',None);o.instance_type='COLLECTION';o.instance_collection=c;scene.collection.objects.link(o)
    if 'ReleaseLid' in n:o.location=meta['worn']['Crew']['hinge']
w=bpy.data.worlds.new('Source silhouette studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.30,.35,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;scene.world=w
def area(name,p,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,-.2,.8))-o.location).to_track_quat('-Z','Y').to_euler()
area('Soft source key',(1,-2,3),200,2);area('Soft source fill',(-1,0,2),100,2)
cd=bpy.data.cameras.new('Actual lap camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);cam.location=(1.15,-1.55,1.25);cam.rotation_euler=(Vector((0,-.17,.78))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=62;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(F/'BusinessBelt41_SourceSilhouette.png');bpy.ops.render.render(write_still=True)
