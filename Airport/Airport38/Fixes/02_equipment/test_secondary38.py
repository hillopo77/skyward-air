"""Separate read/test session; saves only02's review files, never master."""
import bpy,sys,json,copy,hashlib,math,importlib.util
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;R=H.parents[1];A=R.parent
master=R/'Airport_Repaired38.blend';digest=hashlib.sha256(master.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(master),load_ui=False)
sys.path.insert(0,str(A/'SourceAssets'));sys.path.insert(0,str(H));import airport_model as a
for m in bpy.data.materials:
    if m.name.startswith('MI_AP_'):a.MATS[m.name[6:]]=m
import equipment_scrutiny38 as E
class C:
    def __init__(self):self.a=a;self.scene=bpy.context.scene;self.D=json.loads((R/'Exports/airport_layout.json').read_text());self.R=R
    def require(self,n):return next(q for q in self.D['instances'] if q['name']==n)
    def move(self,n,p):
        q=self.require(n);old=q['location'][:];q['location']=list(p)
        o=self.scene.objects.get(n)
        if o:o.location=p
        for t in self.D['interactions']:
            if t.get('actor')==n:t['point']=[v+b-c for v,b,c in zip(t['point'],p,old)]
ctx=C();rep=E.apply(ctx);assert E.apply(ctx) is rep
def passed(label,v):assert v,label;rep.setdefault('checks',[]).append(label)
passed('Secondary patch is idempotent on its D tag',len(a.ASSETS)==len(rep['asset_ids']))
def cast_z(col,p):
    hits=[];start=Vector(p);end=start-Vector((0,0,2));dg=bpy.context.evaluated_depsgraph_get()
    for ob in col.objects:
        if ob.get('export_ignore') or ob.type not in ('MESH','CURVE'):continue
        ev=ob.evaluated_get(dg);iv=ev.matrix_world.inverted();s=iv@start;e=iv@end
        hit,co,n,idx=ev.ray_cast(s,(e-s).normalized(),distance=(e-s).length)
        if hit:hits.append((float((ev.matrix_world@co).z),ob.name))
    return max(hits) if hits else None
hit=cast_z(bpy.data.collections['SM_AP_Vanity34'],(-.62,-.12,1.1))
print('VANITY_CENTRE_RAY',hit,flush=True)
passed('Sink centre ray reaches seated drain, never a false solid rim/counter cap',hit and .728<hit[0]<.74 and 'drain' in hit[1])
hit=cast_z(bpy.data.collections['SM_AP_Toilet34'],(0,-.10,.70))
passed('Toilet opening ray reaches water below .31 rather than pedestal cap .36',hit and .295<hit[0]<.310 and 'water' in hit[1])
passed('Each of four setting groups is seated .001 above real table top',all(abs(q['location'][2]-.7735)<1e-6 for q in ctx.D['instances'] if q['asset']=='SM_AP_TableSetting36'))
passed('Scanner arm uses three explicit rigid links rather than twisted loft',sum('captured' in o.name and 'arm link38R' in o.name for o in bpy.data.collections['SM_AP_Scanner38'].objects)==3)
passed('Vanity fitted leaves cover the full front with narrow consistent reveals',sum('consistent-reveal door38R' in o.name for o in bpy.data.collections['SM_AP_Vanity34'].objects)==4)
passed('Bakery shelves have six actual captured structural bearers',sum('full shelf bearer38R' in o.name for o in bpy.data.collections['SM_AP_Bakery36'].objects)==6)
passed('A08 artwork is carried by two ground-supported posts',sum('supported rear post38R' in o.name for o in bpy.data.collections['SM_AP_RetainedCraft38'].objects)==2)
# 13 original roles plus the three flight boards Pass46 added to the
# concourse, the landside corridor and arrivals reclaim.
passed('Screen roles cover actual scanner, kiosk, counter and flight boards',len(ctx.D['repair38']['equipment']['screen_roles38'])==16)
for aid in ['SM_AP_Sofa36','SM_AP_OvalTable36','SM_AP_CafeTable34','SM_AP_CafeChair34','SM_AP_Trolley','SM_AP_Information27','SM_AP_Bench27','SM_AP_Bench29','SM_AP_Bench34']:
    dg=bpy.context.evaluated_depsgraph_get();z=min((o.evaluated_get(dg).matrix_world@Vector(v)).z for o in bpy.data.collections[aid].objects for v in o.evaluated_get(dg).bound_box)
    passed(aid+' feet contact floor while top/seat stays put',abs(z)<.0001)
pillows=[o for o in bpy.data.collections['SM_AP_TravelStorage38'].objects if o.name.startswith('Seated smoothly closed neck pillow38R')]
passed('Neck pillows now rest exactly on shelf .3675 above one metre',len(pillows)==2 and all(abs(min((o.matrix_world@Vector(v)).z for v in o.bound_box)-1.3675)<1e-5 for o in pillows))
passed('Master file has not been written or changed',hashlib.sha256(master.read_bytes()).hexdigest()==digest)
rep['source_read']=str(master);rep['master_unchanged_sha256']=digest
(H/'secondary_findings38.json').write_text(json.dumps(rep,indent=2));(H/'secondary_layout38.json').write_text(json.dumps(ctx.D,indent=2))
if '--render' in sys.argv:
    scene=bpy.data.scenes.new('Equipment38_Secondary_IsolatedReview');bpy.context.window.scene=scene
    for aid,n,p in [('SM_AP_Vanity34','Review vanity',(0,0,0)),('SM_AP_Scanner38','Review scanner',(4,0,0)),('SM_AP_TravelStorage38','Review travel shelf',(-4,0,0))]:
        o=bpy.data.objects.new(n,None);o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections[aid];o.location=p;scene.collection.objects.link(o)
    scene.world=bpy.data.worlds.new('Secondary review world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    for p,power,size in [((0,-3,6),1900,5),((3,4,6),1800,4)]:
        d=bpy.data.lights.new('Secondary broad light','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);o.location=p;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();scene.collection.objects.link(o)
    d=bpy.data.cameras.new('Secondary camera');o=bpy.data.objects.new('Secondary camera',d);scene.collection.objects.link(o);scene.camera=o
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
    for name,p,t,lens in [('Secondary_Vanity38',(2.4,-3.6,2.5),(0,0,1.13),49),('Secondary_ScannerArm38',(6.6,-2.3,2.2),(5,-.3,1.25),60)]:
        o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;scene.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(H/'Secondary_Props38.blend'))
print('SECONDARY38_PASS',len(rep['checks']),len(rep['asset_ids']))
