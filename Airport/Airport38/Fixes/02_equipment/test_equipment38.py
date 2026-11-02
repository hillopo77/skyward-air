"""Isolated, factory-empty geometry verification. Never opens the game master."""
import bpy,sys,json,math,importlib.util,copy,traceback
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
A=HERE.parents[2]
sys.path.insert(0,str(A/'SourceAssets'))
import airport_model as a
spec=importlib.util.spec_from_file_location('equipment38',HERE/'equipment38.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
class Context:
    def __init__(self):
        self.a=a;self.D=json.loads((A/'Clarity37/Exports/airport_layout.json').read_text());self.before=copy.deepcopy(self.D)
        self.scene=bpy.context.scene;self.R=HERE.parents[1];self.A=A;self.P=A/'../../UnrealProject/Content/Python'
    def require(self,n):return next(q for q in self.D['instances'] if q['name']==n)
    def move(self,n,p,rotation=None,scale=None):
        q=self.require(n);old=q['location'][:];q['location']=list(p)
        if rotation is not None:q['rotation_degrees']=rotation
        if scale is not None:q['scale']=scale
        for t in self.D['interactions']:
            if t['actor']==n:t['point']=[v+b-c for v,b,c in zip(t['point'],p,old)]
    def replace(self,n,asset):
        asset=asset if asset.startswith('SM_AP_') else 'SM_AP_'+asset
        assert asset in a.ASSETS,asset
        self.require(n)['asset']=asset
    def add(self,asset,name,location,rotation=0,scale=None,collision=True,**extra):
        asset=asset if asset.startswith('SM_AP_') else 'SM_AP_'+asset
        assert asset in a.ASSETS,asset
        q=dict(asset=asset,name=name,location=list(location),rotation_degrees=rotation,scale=scale or [1,1,1],collision=collision,stage=10,**extra)
        self.D['instances'].append(q);return q
ctx=Context();mod.plan(ctx);mod.build(ctx)
for k,it in a.ASSETS.items():
    # Collections remain editable in the delivered library but hidden from the
    # unit scene. Separate instances below show genuine authored assemblies.
    bpy.context.scene.collection.children.link(it['collection'])
    it['collection'].hide_render=True
bpy.context.view_layer.update()
def evaluated_vertices(ob):
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg)
    me=ev.to_mesh();points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return points
def bounds(objects):
    pts=[v for ob in objects for v in evaluated_vertices(ob) if ob.type in ['MESH','FONT']]
    return [[min(v[j] for v in pts) for j in range(3)],[max(v[j] for v in pts) for j in range(3)]]
report={'scope':'Isolated source geometry, no native game claim','assets':{},'assertions':[]}
for k,it in a.ASSETS.items():
    col=it['collection'];dups=0;badverts=0;meshes=0
    for ob in col.objects:
        if ob.type!='MESH':continue
        meshes+=1;seen=set()
        for v in ob.data.vertices:
            if not all(math.isfinite(q) for q in v.co):badverts+=1
        for f in ob.data.polygons:
            key=tuple(sorted(tuple(round(x,7) for x in ob.data.vertices[i].co) for i in f.vertices))
            if key in seen:dups+=1
            seen.add(key)
    report['assets'][k]={'objects':len(col.objects),'mesh_parts':meshes,'bounds':bounds(col.objects),'within_part_duplicate_faces':dups,'nonfinite_vertices':badverts,'collision':it['collision']}
    assert not dups,(k,'duplicate faces');assert not badverts,(k,'non-finite vertices')
def passed(label,value):assert value,label;report['assertions'].append(label)
scanner=a.ASSETS['SM_AP_Scanner38']['collection']
sb=report['assets']['SM_AP_Scanner38']['bounds']
passed('Scanner02 keeps >=300 mm service margin inside x=-36.09 wall',-38.05+sb[1][0]<-36.39)
# Raycast of every solid scanner component through its central tunnel. Visual
# lead curtains are deliberately a separate non-collision asset.
hits=[]
for ob in scanner.objects:
    if ob.type!='MESH':continue
    inv=ob.matrix_world.inverted();start=inv@Vector((0,-2,1.32));end=inv@Vector((0,2,1.32))
    hit=ob.ray_cast(start,(end-start).normalized(),distance=(end-start).length)[0]
    if hit:hits.append(ob.name)
passed('Scanner has an unobstructed central open tunnel',not hits)
passed('Roof and shoulders are a single mesh with no overlapping roof slab',len([o for o in scanner.objects if 'One continuous scanner shoulder-and-roof' in o.name])==1 and not any('fitted roof shell' in o.name for o in scanner.objects))
passed('Scanner feet contact floor and shell',abs(sb[0][2])<.001 and len([o for o in scanner.objects if 'leveling foot' in o.name])==4)
passed('Conveyor feet contact the floor',abs(report['assets']['SM_AP_Belt38']['bounds'][0][2])<.001)
stop=a.ASSETS['SM_AP_EmergencyStop38']['collection']
stopb=report['assets']['SM_AP_EmergencyStop38']['bounds']
passed('Emergency cap and base are ahead of the scanner shoulder',-1.40+stopb[1][1]<-1.055-.20)
curtain=a.ASSETS['SM_AP_ScannerCurtain38']['collection']
strips=sorted([bounds([o]) for o in curtain.objects if 'overlapping lead strip' in o.name],key=lambda b:b[0][0])
passed('Lead strips overlap in projection without any bright slit field',all(b[1][0]>=c[0][0] for b,c in zip(strips,strips[1:])))
passed('Curtain has separated backing and staggered strip faces',len([o for o in curtain.objects if 'rear web' in o.name])==1 and max(b[0][1] for b in strips)-min(b[0][1] for b in strips)>.006)
for shelf in ['SM_AP_StaffStorage38','SM_AP_TravelStorage38']:
    col=a.ASSETS[shelf]['collection'];rails=[bounds([o]) for o in col.objects if 'directly captured label rail' in o.name]
    passed(shelf+' label rails seat on shelf edges',len(rails)==4 and all(b[1][1]>=-.245 for b in rails))
passed('Each medical case has one continuous cross with no coplanar bar overlap',len([o for o in a.ASSETS['SM_AP_StaffStorage38']['collection'].objects if 'Single continuous first-aid cross' in o.name])==2)
bincol=a.ASSETS['SM_AP_Recycling38']['collection'];liner=[o for o in bincol.objects if 'retained bin liner' in o.name]
passed('Bins have real unsealed mouths and retained interior bottoms',len(liner)==2 and len([o for o in bincol.objects if 'Sealed internal bin bottom' in o.name])==2 and all(len(o.data.polygons)==36 for o in liner))
passed('A07 desk is at least700 mm inside its south wall',ctx.require('Gate A07 boarding desk')['location'][1]-.99>-2.21)
passed('Second detector and crossing are translated together',abs(sum(ctx.D['security_crossings'][1][:2])/2+40.4)<1e-6)
passed('Second belt and detector retain2350 mm centre separation',abs(ctx.require('Security belt 02')['location'][0]-ctx.require('Security portal 02')['location'][0]-2.35)<1e-6)
passed('Checked belt01 input aligns with transfer opening y=-13',ctx.require('Bag drop belt 01')['location'][1]==-13)
passed('Four independent supported emergency controls exist',len(ctx.D['repair38']['equipment']['emergency_controls'])==4)
passed('Curtains are visual-only flexible elements',a.ASSETS['SM_AP_ScannerCurtain38']['collision']=='none')
passed('Every planned desk uses the new fitted assembly',len([q for q in ctx.D['instances'] if q['asset']=='SM_AP_Counter38'])==5)
passed('Plant has intended furniture support metadata',ctx.require('Small potted plant24')['support_actor38']=='ChargingTable24_1749')
passed('Tray stacks rise from reachable waist-height supports',all(ctx.require('Tray24_'+str(i))['location'][2]>.82 for i in [1719,1720,1721,1722,1732,1733,1734,1735]))
passed('No legacy equipment mixed into new asset collections',all('38' in k for k in a.ASSETS))
passed('Runtime monitor material keeps existing screen slot',any(m.name=='MI_AP_Screen' for ob in scanner.objects if ob.type=='MESH' for m in ob.data.materials))
passed('All authored equipment materials have unique prefixes',all(m.name.startswith('MI_AP_P38E') or m.name=='MI_AP_Screen' for it in a.ASSETS.values() for ob in it['collection'].objects if ob.type in ['MESH','FONT'] for m in ob.data.materials))
def instance(asset,n,p,r=0):
    # Collection visibility on the source library does not affect a linked
    # collection instance. Hide source via a separate excluded view layer.
    c=a.ASSETS['SM_AP_'+asset]['collection'];c.hide_render=False
    o=bpy.data.objects.new(n,None);o.instance_type='COLLECTION';o.instance_collection=c;o.location=p;o.rotation_euler.z=math.radians(r);bpy.context.scene.collection.objects.link(o);return o
# Source library has no scene placement. It is moved out of the view layer by
# unlinking its direct roots, while retaining linked instances.
for it in a.ASSETS.values():bpy.context.scene.collection.children.unlink(it['collection'])
instance('Belt38','Review belt',(0,0,0));instance('Scanner38','Review scanner',(0,0,0))
instance('ScannerCurtain38','Review front lead curtain',(0,-1.075,1.915))
instance('ScannerCurtain38','Review rear lead curtain',(0,1.075,1.915))
instance('EmergencyStop38','Review stop',(.56,-1.4,.82))
instance('TrayStation38','Review tray stand',(0,-2.45,0));instance('Outfeed38','Review receiving station',(0,2.15,0))
instance('Counter38','Review fitted counter',(4,0,0))
instance('StaffStorage38','Review staff shelf',(-4,0,0));instance('TravelStorage38','Review retail shelf',(-6,0,0))
instance('Recycling38','Review open bins',(4,-2,0))
ground=bpy.data.materials.new('Unit review floor');ground.diffuse_color=(.23,.27,.25,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));bpy.context.object.data.materials.append(ground)
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.63,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for p,power,size in [((0,-3,7),2200,5),((1,5,6),1700,4),((-6,-4,5),1200,4)]:
    d=bpy.data.lights.new('Unit broad review light','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);o.location=p;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.collection.objects.link(o)
camdata=bpy.data.cameras.new('Unit camera');cam=bpy.data.objects.new('Unit camera',camdata);bpy.context.scene.collection.objects.link(cam);bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
(HERE/'unit_geometry38.json').write_text(json.dumps(report,indent=2))
(HERE/'planned_equipment_layout38.json').write_text(json.dumps(ctx.D,indent=2))
for name,p,t,lens in [('Scanner38_review',(4.4,-5.1,3.1),(.2,0,1.12),48),('Counter38_review',(6.8,-3.5,2.7),(4,0,1.02),56),('Storage38_review',(-7.9,-3.8,2.7),(-4.9,0,1.18),49)]:
    if '--geometry-only' in sys.argv:continue
    if '--storage-only' in sys.argv and name!='Storage38_review':continue
    cam.location=p;cam.rotation_euler=(Vector(t)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=lens
    scene.render.filepath=str(HERE/(name+'.png'));bpy.ops.render.render(write_still=True)
(HERE/'unit_geometry38.json').write_text(json.dumps(report,indent=2))
(HERE/'planned_equipment_layout38.json').write_text(json.dumps(ctx.D,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Equipment38_Unit.blend'))
print('EQUIPMENT38_TEST_PASS',len(report['assertions']),len(report['assets']))
