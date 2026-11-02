"""Small genuine source-model preview, CPU only; no game/master edits."""
import bpy,math
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent
names=['SM_AP_W40WindowWallR','SM_AP_W40PressureWindows','SM_AP_W40ShadeFrameR','SM_AP_W40RackR']
with bpy.data.libraries.load(str(F/'Window40_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(names)
scene=bpy.context.scene
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
for name,col in zip(names,dst.collections):
    ob=bpy.data.objects.new(name+' genuine source instance',None);ob.instance_type='COLLECTION';ob.instance_collection=col;scene.collection.objects.link(ob)
    if 'ShadeFrame' in name:ob.location=(2.3,0,.92)
world=bpy.data.worlds.new('Soft daylight source-review world');world.use_nodes=True;scene.world=world
bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.38,.58,.76,1);bg.inputs['Strength'].default_value=.65
def area(name,position,target,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=position;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Cabin soft source-review key',(-.5,-1.7,3.4),(2.1,0,1.3),180,2.5,(1.,.87,.71))
area('Exterior daylight source-review key',(4,-.6,3.8),(2.2,0,1.4),450,3.,(.78,.9,1.))
camdata=bpy.data.cameras.new('Window40 genuine source camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);cam.location=(.92,-.34,1.56);target=Vector((2.38,0,1.52));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=43;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.transmission_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(F/'Window40_SourcePreview.png');scene.render.film_transparent=False
scene['preview_kind']='Genuine Window40 source geometry preview, not Unreal/game capture'
bpy.ops.render.render(write_still=True)
print('WINDOW40_SOURCE_PREVIEW',scene.render.filepath,flush=True)
