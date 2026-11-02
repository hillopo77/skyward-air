"""Genuine frozen-unit source previews, CPU only; no main project mutation."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent;W=F.parents[5]
names=['SM_AP_W41WindowWallR','SM_AP_W40PressureWindows','SM_AP_W41ShadeFrameR','SM_AP_W41RackR']
pm=json.loads((W/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];psus=[q for q in pm['instances'] if q['name'].startswith(('Passenger service unit 02','PSU 02 '))]
names+=sorted(set(q['asset'] for q in psus))
with bpy.data.libraries.load(str(F/'Window41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(names)
cols=dict(zip(names,dst.collections));scene=bpy.context.scene
sys.path.insert(0,str(W/'outputs/Airport/Airport38/SourceAssets'))
import glass39
from types import SimpleNamespace
# Use the parent's actual approved source-glass finish; the original export
# unit is opaque before this normal parent integration step.
glass39.apply_source(SimpleNamespace(D={}))
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
def instance(name,col,pos=(0,0,0)):
    ob=bpy.data.objects.new(name,None);ob.instance_type='COLLECTION';ob.instance_collection=col;ob.location=pos;scene.collection.objects.link(ob);return ob
for name in names[:4]:instance(name+' genuine source',cols[name],(2.3,0,.92) if 'ShadeFrame' in name else(0,0,0))
for q in psus:instance(q['name'],cols[q['asset']],[q['location'][0],q['location'][1]-14.175,q['location'][2]+.150])
world=bpy.data.worlds.new('Soft daylight source-review world');world.use_nodes=True;scene.world=world;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.38,.58,.76,1);bg.inputs['Strength'].default_value=.65
def area(name,p,target,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Cabin soft source-review key',(-.5,-1.7,3.4),(2.1,0,1.3),180,2.5,(1.,.87,.71));area('Exterior source-review key',(4,-.6,3.8),(2.2,0,1.4),450,3.,(.78,.9,1.))
cd=bpy.data.cameras.new('Window41 genuine source camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.lens=32
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.transmission_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for name,z in [('Standing',1.62),('Seated',1.38)]:
    cam.location=(1.0,-.15,z);cam.rotation_euler=(Vector((2.38,0,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(F/('Window41_SourcePreview_'+name+'.png'));bpy.ops.render.render(write_still=True)
    print('WINDOW41_SOURCE_PREVIEW',scene.render.filepath,flush=True)
