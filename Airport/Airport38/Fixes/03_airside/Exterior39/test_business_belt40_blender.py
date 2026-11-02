"""Private candidate-chair/body contact proof, no shared source/native writes."""
import bpy,sys,json,math,traceback,copy,hashlib
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];W=F.parents[5];C=W/'outputs/Characters/Revision39'
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import business_belt40 as M
pose_source=C/'Characters39.blend'
report=dict(scope='Private final frozen character append; no airport/character master/native writes',source=str(pose_source),source_sha256=hashlib.sha256(pose_source.read_bytes()).hexdigest(),passes=[])
try:
    names=['CHAR39_PassengerCrew_LuxurySeated','CHAR39_PassengerHoodie_LuxurySeated','SM_Plane_LuxurySeat_Ergonomic39']
    with bpy.data.libraries.load(str(pose_source),link=False) as (src,dst):dst.collections=list(names)
    cols=dict(zip(names,dst.collections))
    for col in cols.values():bpy.context.scene.collection.children.link(col)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geometry(col,filter_fn=lambda o:True):
        vs=[];fs=[]
        for ob in col.objects:
            if ob.type!='MESH' or not filter_fn(ob):continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh();base=len(vs);vs.extend(ob.matrix_world@v.co for v in me.vertices);fs.extend(tuple(base+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
        return vs,fs
    def tree(col,filter_fn=lambda o:True):return BVHTree.FromPolygons(*geometry(col,filter_fn))
    chair=cols[names[2]];bodies={'Crew':tree(cols[names[0]]),'Hoodie':tree(cols[names[1]])};cushion=tree(chair,lambda o:o.name.startswith('Suite deep plum seat cushion11') and 'stitch' not in o.name)
    meta=M.build_units(SimpleNamespace(a=a),chair,bodies,cushion);bpy.context.view_layer.update()
    (F/'BusinessBelt40_Model.json').write_text(json.dumps(meta,indent=2))
    # Persist the complete asset library before the real apply preflight. The
    # base and separate lid deliberately have no preview instances in this unit.
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'BusinessBelt40_UnitKits.blend'))
    report['passes'].append(dict(pass_id=1,check='Actual static ownership removed from ergonomic chair and new body-fitted lap buckle',removed=len(meta['removed_old_fixed_parts']),worn_buckles=meta['worn'],side_anchors=meta['anchor_points']))
    zero=[];triangles=0
    for aid in M.IDS:
        col=bpy.data.collections[aid]
        for ob in col.objects:
            ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);zero.extend((aid,ob.name,t.area) for t in me.loop_triangles if t.area<1e-12);ev.to_mesh_clear()
    assert not zero,zero[:15]
    report['passes'].append(dict(pass_id=2,check='Actual evaluated manufactured geometry',triangles=triangles,zero_area=len(zero)))
    fitted=[];bad=[]
    for key,aid in [('Crew',M.IDS[2]),('Generic',M.IDS[3])]:
        tests=['Crew'] if key=='Crew' else ['Crew','Hoodie']
        points,faces=geometry(bpy.data.collections[aid]);minimum=999;inside=[]
        probes=list(points)
        probes.extend(sum((points[i] for i in face),Vector())/len(face) for face in faces)
        probes.extend((points[face[j]]+points[face[(j+1)%len(face)]])*.5 for face in faces for j in range(len(face)))
        for p in probes:
            if p.z<.48 or abs(p.x)>.34:continue
            for kind in tests:
                hit=bodies[kind].find_nearest(p)
                if hit[0] is None:continue
                signed=(p-hit[0]).dot(hit[1]);minimum=min(minimum,signed)
                if signed<-.0015:inside.append(dict(point=list(p),body=kind,signed=signed))
        if inside:bad.append(dict(kind=key,inside_count=len(inside),examples=inside[:12]))
        fitted.append(dict(kind=key,minimum_signed_clothing_clearance_m=minimum,inside_probes=len(inside),vertices_edges_facecentres_checked=len(probes)))
    assert not bad,bad
    report['passes'].append(dict(pass_id=3,check='Actual candidate lap/body clearance, not semantic anchor guesses',fits=fitted))
    # The stowed webbing is fitted to the true cushion; assembled hardware must
    # stay between arm carriers, with a clear central occupant footprint.
    stowed=bpy.data.collections[M.IDS[1]];pp,_=geometry(stowed);assert max(abs(p.x) for p in pp)<.334, max(abs(p.x) for p in pp)
    web,_=geometry(stowed,lambda o:o.name.startswith('B40 stowed webbing follows outer pan edge'));dist=[]
    for p in web:
        hit=cushion.ray_cast(Vector((p.x,p.y,.9)),Vector((0,0,-1)),.7)[0]
        if hit:dist.append(p.z-hit.z)
    assert min(dist)>0.0005 and max(dist)<.008,(min(dist),max(dist))
    report['passes'].append(dict(pass_id=4,check='Stowed halves supported on actual pan edges; receiver/tongue clear arm walls',minimum_cushion_gap_m=min(dist),maximum_cushion_gap_m=max(dist),maximum_abs_x=max(abs(p.x) for p in pp)))
    lid_points,lid_faces=geometry(bpy.data.collections[M.IDS[4]]);lid_results=[]
    for key,body in bodies.items():
        worn=meta['worn']['Crew' if key=='Crew' else 'Generic'];hinge=Vector(worn['hinge']);stow=Vector(meta['stowed_hinge'])
        for state,origin,rotation in [(0,hinge,Matrix.Identity(4)),(1,stow,Matrix.Rotation(math.radians(-155),4,'X'))]:
            pts=[origin+rotation@p for p in lid_points];pts+= [sum((pts[i] for i in face),Vector())/len(face) for face in lid_faces]
            clearance=min((p-body.find_nearest(p)[0]).dot(body.find_nearest(p)[1]) for p in pts)
            assert clearance>-.0005,(key,state,clearance)
            assert max(abs(p.x) for p in pts)<.334,(key,state,'Arm contact')
            lid_results.append(dict(body=key,state=state,minimum_body_clearance_m=clearance,probes=len(pts)))
    report['passes'].append(dict(pass_id=5,check='Actual separate retained lid in both worn and side-parked released poses',poses=lid_results))
    D=json.loads((R/'Exports/airport_layout.json').read_text());ctx=SimpleNamespace(a=a,D=D,R=R,scene=bpy.context.scene)
    def add(asset,name,location,**kwargs):
        q=dict(asset=asset,name=name,location=list(location),rotation_degrees=0.,scale=[1,1,1]);q.update(kwargs);D['instances'].append(q)
        o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections[asset];o.location=location;bpy.context.scene.collection.objects.link(o)
    def move(name,location):
        next(q for q in D['instances'] if q['name']==name)['location']=list(location);bpy.context.scene.objects[name].location=location
    ctx.add=add;ctx.move=move;source_apply=M.apply(ctx);snapshot=copy.deepcopy(D);M.apply(ctx);assert D==snapshot
    assert len(source_apply['records'])==4 and sum(bool(q['occupied_npc']) for q in source_apply['records'])==1
    (F/'BusinessBelt40_SourceApply.json').write_text(json.dumps(source_apply,indent=2))
    report['passes'].append(dict(pass_id=6,check='Current-source assembly metadata/overlay placement repeat-safe with existing four controls',assets=len(source_apply['assets']),records=4,default_worn_npcs=1))
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'BusinessBelt40_UnitKits.blend'))
    report.update(passed=True,assets=M.IDS)
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'BusinessBelt40_Verification.json').write_text(json.dumps(report,indent=2));print('BUSINESS_BELT40',report['passed'],report.get('error',''),flush=True)
