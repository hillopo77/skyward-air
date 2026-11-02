"""Read-only saved-master source tests and genuine five-pass source previews.

Run Blender --background --python validate39.py [-- --render]. No shared source,
export, native asset or level is written. Evidence lives beside this script.
"""
import ast, copy, hashlib, json, math, sys, time, traceback
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
R=HERE.parents[2]
A=R.parent
sys.path[:0]=[str(HERE),str(A/'SourceAssets'),str(HERE.parent.parent/'04_rendering')]
import airport_model as a
import flow39, coplanar38
P=R.parents[2]/'outputs/SkywardAir/UnrealProject/Content/Python'
source=R/'Airport_Repaired38.blend'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
report=dict(status='RUNNING',source_sha256=sha,passes=[],renders=[],assertions=[])
REPORT_PATH=HERE/('Validation39.json' if '--render' in sys.argv else 'GeometryValidation39.json')
def flush():
    REPORT_PATH.write_text(json.dumps(report,indent=2))
def note(text):
    print('FLOW39 '+text,flush=True)
def load_context():
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    D=json.loads(bpy.context.scene['layout_json'])
    a.ASSETS.clear();a.MATS.clear()
    for m in bpy.data.materials:
        if m.name.startswith('MI_AP_'):a.MATS[m.name[6:]]=m
    tree=ast.parse((R/'SourceAssets/build_source38.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context')
    env=dict(bpy=bpy,copy=copy,math=math,R=R,A=A,P=P)
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'context39','exec'),env)
    return env['Context'](a,D,bpy.context.scene)
def collect_tree(ctx,assets):
    dg=bpy.context.evaluated_depsgraph_get();vv=[];ff=[];counts={}
    for q in ctx.D['instances']:
        if q['asset'] not in assets:continue
        col=bpy.data.collections[q['asset']]
        transform=(Matrix.Translation(Vector(q['location'])) @
                   Matrix.Rotation(math.radians(q.get('rotation_degrees',0)),4,'Z') @
                   Matrix.Diagonal(Vector(q.get('scale',[1,1,1])+[1])))
        n=0
        for o in col.all_objects:
            if o.type!='MESH' or o.hide_render:continue
            eo=o.evaluated_get(dg);me=eo.to_mesh();wm=transform@o.matrix_world;offset=len(vv)
            pts=[wm@v.co for v in me.vertices]
            assert all(math.isfinite(c) for p in pts for c in p),o.name
            assert all(p.area>1e-12 for p in me.polygons),('Degenerate face',o.name)
            vv+=pts;ff += [tuple(offset+i for i in p.vertices) for p in me.polygons]
            n+=len(me.polygons);eo.to_mesh_clear()
        counts[q['asset']]=n
    return BVHTree.FromPolygons(vv,ff,all_triangles=False),counts

def render(ctx,pass_record):
    if '--render' not in sys.argv:return
    scene=ctx.scene
    # New preview lights/camera are local test-scene objects; not deliverable kits.
    # Use the actual assembled airport, with existing practical roles transcribed.
    if not scene.get('flow39_preview_ready'):
        for ob in list(scene.objects):
            if ob.type=='LIGHT':bpy.data.objects.remove(ob,do_unlink=True)
        for i,q in enumerate(ctx.D.get('lights',[])):
            if q.get('follow_actor'):continue
            pos=q.get('position')
            if not pos:continue
            ld=bpy.data.lights.new('QA practical39 '+str(i),'AREA')
            ld.energy=min(160, q.get('lumens',2500)/24)
            ld.shape='RECTANGLE';ld.size=max(.7,q.get('width',150)/100);ld.size_y=max(.2,q.get('height',25)/100)
            ld.color=(1.0,.88,.70)
            ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.location=pos
        # Quiet readable fill and daylight. The preview does not claim UE parity.
        world=scene.world or bpy.data.worlds.new('QA source sky39');scene.world=world
        world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.72,.83,1)
        world.node_tree.nodes['Background'].inputs[1].default_value=.32
        ld=bpy.data.lights.new('QA daylight39','SUN');ld.energy=1.4;ld.angle=.18
        ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.rotation_euler=(.55,-.6,-.4)
        cd=bpy.data.cameras.new('QA source camera39');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam
        scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
        scene.cycles.max_bounces=4;scene.cycles.transmission_bounces=3
        scene.render.resolution_x=960;scene.render.resolution_y=600;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
        scene['flow39_preview_ready']=True
    views={
        1:('RoofFrameConstruction',[-4,45,25],[-32,12,2.5],29),
        2:('A08NaturalOpening',[-29,10.4,1.62],[-29,17,2.05],20),
        3:('CafeFittedTurn',[-29.6,12,1.62],[-35.3,13.0,1.85],22),
        4:('CheckinWelcomeScale',[-44.8,-15.4,1.62],[-39.8,-14.5,1.8],22),
        5:('ConcourseRouteRead',[-32.4,6.5,1.62],[-26.4,8.0,1.9],21),
    }
    name,p,target,lens=views[pass_record['id']]
    cam=scene.camera;cam.location=p;cam.rotation_euler=(Vector(target)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    # Parent Context.add creates actual collection instances; originals stay in a
    # separate library scene. Newly rebuilt collections retain their old links.
    path=HERE/('Pass%02d_'%pass_record['id']+name+'.png')
    hidden=[]
    if pass_record['id']==1:
        architecture_names={q['name'] for q in ctx.D['instances'] if q['asset'] in {'SM_AP_'+s for s in flow39.STRUCTURAL}}
        for ob in scene.objects:
            if ob.type in {'LIGHT','CAMERA'} or ob.name in architecture_names:continue
            if not ob.hide_render:hidden.append(ob);ob.hide_render=True
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    for ob in hidden:ob.hide_render=False
    report['renders'].append(dict(pass_id=pass_record['id'],path=str(path),kind='Genuine Blender source render; not native Unreal gameplay'))
    flush()

def final_views(ctx):
    if '--render' not in sys.argv:return
    scene=ctx.scene;cam=scene.camera
    for name,p,target,lens in [
        ('Final06_CafeTurn',[-29.6,12,1.62],[-35.3,13.0,1.85],22),
        ('Final07_A07Arrival',[-27.9,3.7,1.62],[-20.8,4.4,1.9],23),
        ('Final08_GalleryStairFit',[-43.8,26.0,4.77],[-46.5,21.5,1.6],25),
    ]:
        cam.location=p;cam.rotation_euler=(Vector(target)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
        path=HERE/(name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        report['renders'].append(dict(pass_id='final',path=str(path),kind='Genuine final Blender source render; not native Unreal gameplay'))
        flush()

try:
    ctx=load_context()
    before_footprints=copy.deepcopy(ctx.D['zones'])
    before_interactions=copy.deepcopy(ctx.D['interactions'])
    baseline=coplanar38.find_conflicts(coplanar38.blender_faces(ctx.D,lambda n:n in {'SM_AP_Glazing38'}))
    report['glazing_before_candidates']=len(baseline['conflicts']);flush()
    note('loaded current source; baseline glazing candidates '+str(report['glazing_before_candidates']))
    def callback(c,record):
        report['passes'].append(record);flush();note('pass '+str(record['id'])+' '+record['name'])
        render(c,record)
    result=flow39.apply(ctx,callback)
    assert flow39.apply(ctx) is result
    assert a.ASSETS['SM_AP_GalleryStair35']['collision']=='none','Idempotence changed retained stair collision contract'
    assert before_footprints==ctx.D['zones'],'Changed room footprints'
    assert before_interactions==ctx.D['interactions'],'Architecture altered interaction semantics'
    # All named kits reuse original collection IDs. No stale .001 shell remains.
    for name in flow39.STRUCTURAL:
        assert a.ASSETS['SM_AP_'+name]['collection'].name=='SM_AP_'+name
    tree,counts=collect_tree(ctx,{'SM_AP_'+s for s in flow39.STRUCTURAL}|{'SM_AP_Transitions39','SM_AP_GalleryStair35','SM_AP_RetainedCraft38'})
    rays=[]
    for p in ctx.D['repair38']['flow39_probes']:
        v=Vector(p['start']);delta=Vector(p['end'])-v
        hit=tree.ray_cast(v,delta.normalized(),delta.length)
        blocked=hit[0] is not None
        # Original baggage aperture probes deliberately exclude glazing. Their
        # public-to-service hole remains open; WC and exterior include glass.
        assert blocked==(p['expected']=='block'),('Physical probe failed',p,tuple(hit[0]) if blocked else None)
        rays.append(dict(id=p['id'],passed=True,hit=blocked))
    # Explicitly repeat the original AT11 proof, independent of generated probes.
    v=Vector([-45,15.5,7.06]);assert tree.ray_cast(v,Vector([0,1,0]),1)[0] is not None,'AT11 gap remains'
    report['assertions'] += [dict(id='AT11_original_physical_proof',passed=True),dict(id='Footprints_retained',passed=True),
                            dict(id='Interaction_semantics_retained',passed=True),dict(id='Idempotent',passed=True)]
    predicate=lambda n:n in {'SM_AP_'+s for s in flow39.STRUCTURAL}|{'SM_AP_Transitions39','SM_AP_RouteHierarchy39','SM_AP_Wayfinding38','SM_AP_Attachments38','SM_AP_RetainedCraft38','SM_AP_GalleryStair35'}
    overlap=coplanar38.find_conflicts(coplanar38.blender_faces(ctx.D,predicate))
    (HERE/'Coplanarity39.json').write_text(json.dumps(overlap,indent=2))
    report.update(result=result,physical_probes=rays,mesh_faces=counts,coplanarity_candidates=len(overlap['conflicts']),
                  unchanged_master=hashlib.sha256(source.read_bytes()).hexdigest()==sha)
    assert report['unchanged_master'],'Master changed unexpectedly'
    assert not overlap['conflicts'],('Structural overlap candidate',len(overlap['conflicts']))
    final_views(ctx)
    report['status']='PASS_SOURCE_GEOMETRY_AND_RECORDED_PREVIEWS'
    flush();note('PASS '+str(len(rays))+' physical probes; zero structural/frame coplanar candidates')
except Exception:
    report.update(status='FAIL',error=traceback.format_exc(),unchanged_master=hashlib.sha256(source.read_bytes()).hexdigest()==sha)
    flush();raise
