"""Private current-source terminal unit build, QA and before/after preview.
Factory-empty launch; appends terminal assets only. Never opens/writes master.
"""
import bpy,sys,json,math,ast,copy,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;R=HERE.parents[1];A=R.parent
sys.path[:0]=[str(A/'SourceAssets'),str(R/'SourceAssets'),str(HERE)]
import airport_model as a
import finish43
master=R/'Airport_Repaired38.blend'
D=json.loads((R/'Exports/airport_layout.json').read_text());K=json.loads((R/'Exports/airport_assets.json').read_text())
baseline=copy.deepcopy(D);sourcehash=hashlib.sha256(master.read_bytes()).hexdigest()
# Clear factory cube only; never load or mutate a live/shared scene.
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
struct={'SM_AP_Walls38','SM_AP_Floors38','SM_AP_Ceilings38','SM_AP_Glazing38','SM_AP_Transitions39','SM_AP_RetainedCraft38','SM_AP_RouteHierarchy39','SM_AP_Wayfinding38','SM_AP_Attachments38','SM_AP_Fixtures38','SM_AP_GalleryStair35'}
selected=[q for q in D['instances'] if q['asset'] in struct or (-49<=q['location'][0]<=-14 and -22<=q['location'][1]<=34 and not q['asset'].startswith('SM_AP_P38B'))]
needed=sorted(set(q['asset'] for q in selected))
with bpy.data.libraries.load(str(master),link=False) as (src,dst):
 available=set(src.collections);dst.collections=[name for name in needed if name in available]
missing=sorted(set(needed)-available);assert not missing,missing
scene=bpy.context.scene;scene.name='Finish43_CurrentTerminal_SourceReview'
for mat in bpy.data.materials:
 if mat.name.startswith('MI_AP_'):a.MATS[mat.name[6:]]=mat
for q in selected:
 ob=bpy.data.objects.new(q['name'],None);ob.instance_type='COLLECTION';ob.instance_collection=bpy.data.collections[q['asset']]
 ob.location=q['location'];ob.rotation_euler.z=math.radians(q['rotation_degrees']);ob.scale=q.get('scale',[1,1,1]);scene.collection.objects.link(ob)
# Source Context comes from its actual current definition, without invoking any
# original assembler side effects or read/write of its build report.
tree=ast.parse((R/'SourceAssets/build_source38.py').read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context')
P=R.parents[2]/'outputs/SkywardAir/UnrealProject/Content/Python'
exec(compile(ast.Module(body=[cls],type_ignores=[]),'actual_source_context43','exec'),globals())
ctx=Context(a,D,scene)
world=bpy.data.worlds.new('Source review daylight43');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.61,.73,.85,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
# Fixed neutral source-review lighting, identical before and after; these are
# inspection views and do not claim Unreal's actual lighting result.
for i,q in enumerate(D['lights']):
 pos=q.get('position')
 if not pos or not(-50<pos[0]<-13 and -23<pos[1]<35):continue
 ld=bpy.data.lights.new('Unchanged source-review practical %03d'%i,'AREA');ld.energy=q.get('lumens',3000)/12
 ld.shape='RECTANGLE';ld.size=max(.4,q.get('width',180)/100);ld.size_y=max(.25,q.get('height',25)/100)
 ld.color=(1.,.93,.82) if q.get('temperature',4000)<3800 else (1.,.97,.91)
 ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.location=pos
# Glass openings get clear daylight from large exterior areas.
for i,(p,t,size,power) in enumerate([((-21,22,4.5),(-29,23,1.4),10,1800),((-53,25,5),(-43,25,1.2),10,2300),((-20,-19,3),(-27,-15,1.4),6,900)]):
 ld=bpy.data.lights.new('Unchanged source-review daylight %d'%i,'AREA');ld.energy=power;ld.size=size;ld.color=(.84,.93,1.)
 ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Fixed terminal finish review camera43');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.cycles.max_bounces=4;scene.cycles.transmission_bounces=4;scene.render.threads_mode='FIXED';scene.render.threads=3
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
views=[('01_Checkin',[-38.0,-14.8,1.62],[-26,-13.1,1.7],75),
       ('02_Baggage',[-30.6,-13.1,1.62],[-26,-14.3,1.55],76),
       ('03_A08',[-28.5,16.8,1.62],[-29.2,28.5,1.8],78),
       ('04_Concourse',[-29,6.7,1.62],[-29,15.3,1.7],78),
       ('05_WC',[-24,-10.0,1.62],[-18.0,-9,1.5],78),
       ('06_Cafe',[-33.8,25.5,1.62],[-42.5,29,1.6],78)]
if '--three' in sys.argv:views=[v for v in views if v[0] in {'02_Baggage','03_A08','06_Cafe'}]
def render(prefix):
 for name,p,t,fov in views:
  cam.location=p;cam.rotation_euler=(Vector(t)-cam.location).to_track_quat('-Z','Y').to_euler();cd.angle=math.radians(fov)
  scene.render.filepath=str(HERE/'Evidence'/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
  print('SOURCE43_RENDER',prefix,name,flush=True)
if '--no-before' not in sys.argv:render('Before')
report=finish43.apply(ctx)
# Clear aperture ray probes are evaluated against finish geometry itself, in
# addition to unchanged authoritative portal dimensions and shell topology.
def bounds(col):
 return {ob.name:len(ob.data.vertices) for ob in col.objects if ob.type=='MESH'}
before_repeat={aid:bounds(bpy.data.collections[aid]) for aid in finish43.OWNED}
first_instances=len(D['instances']);repeat=finish43.apply(ctx)
assert repeat['repeat_safe_reused'] and first_instances==len(D['instances'])
assert before_repeat=={aid:bounds(bpy.data.collections[aid]) for aid in finish43.OWNED}
assert D['interactions']==baseline['interactions'] and D['portals']==baseline['portals'] and D['zones']==baseline['zones']
assert D['service_openings38']==baseline['service_openings38']
assert sourcehash==hashlib.sha256(master.read_bytes()).hexdigest()
owned=bpy.data.collections['SM_AP_BaggageBackdrop43']
for opening in D['service_openings38']:
 # Bounds of the exact clear rectangle must have zero opaque finish vertices
 # inside it, irrespective of the rays' height within the feed opening.
 for ob in owned.objects:
  if ob.type!='MESH':continue
  for v in ob.data.vertices:
   p=ob.matrix_world@v.co
   assert not (abs(p.y-opening['centre'])<opening['width']/2-1e-6 and opening['z0']+1e-6<p.z<opening['z1']-1e-6),('Finish intrudes feed aperture',ob.name,tuple(p))
kit=bpy.data.scenes.new('Finish43_EditableUnitKit')
for aid in finish43.OWNED+finish43.STRUCTURAL:kit.collection.children.link(bpy.data.collections[aid])
scene['layout_json']=json.dumps(D);scene['finish43_master_sha']=sourcehash
for image in bpy.data.images:
 if image.filepath and '06_visual_finish43' in image.filepath:image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'TerminalFinish43_UnitKit.blend'))
(HERE/'Unit43Layout.json').write_text(json.dumps(D,indent=2))
report.update(source_master_sha256=sourcehash,private_source_only=True,selected_terminal_instances=len(selected),
              repeat_safe_verified=True,service_opening_vertex_clearance_verified=True,
              unit_blend='TerminalFinish43_UnitKit.blend',native_verified=False)
(HERE/'Source43Report.json').write_text(json.dumps(report,indent=2))
print('SOURCE43_READY',json.dumps(dict(panels=report['wall_panels']['panels'],selected_instances=len(selected),new_parts=sum(len(bpy.data.collections[aid].objects) for aid in finish43.OWNED))),flush=True)
if '--build-only' not in sys.argv:render('After')
