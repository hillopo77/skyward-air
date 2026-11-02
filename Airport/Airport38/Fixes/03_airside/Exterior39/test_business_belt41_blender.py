import bpy,sys,json,traceback,hashlib,copy
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5];C=ROOT/'outputs/Characters/Revision39'
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import business_belt40 as B
import business_belt41 as M
report=dict(passed=False,source_sha256=hashlib.sha256((C/'Characters39.blend').read_bytes()).hexdigest(),passes=[])
try:
    names=['CHAR39_PassengerCrew_LuxurySeated','CHAR39_PassengerHoodie_LuxurySeated']
    with bpy.data.libraries.load(str(C/'Characters39.blend'),link=False) as (src,dst):dst.collections=list(names)
    chars=dict(zip(('Crew','Hoodie'),dst.collections))
    for c in chars.values():bpy.context.scene.collection.children.link(c)
    with bpy.data.libraries.load(str(F/'BusinessBelt40_UnitKits.blend'),link=False) as (src,dst):dst.collections=['SM_AP_B40LuxurySeatBase','SM_AP_B40ReleaseLid','SM_AP_B40LapStowed']
    base,lid,stow=dst.collections
    for c in dst.collections:bpy.context.scene.collection.children.link(c)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geo(c):
        vv=[];ff=[]
        for o in c.objects:
            if o.type!='MESH':continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();T=B._matrix(o) if not o.parent else o.matrix_world;offset=len(vv);vv.extend(T@v.co for v in me.vertices);ff.extend(tuple(offset+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
        return vv,ff
    bodies={};fits={};arms={}
    for k,c in chars.items():
        o=next(o for o in c.objects if o.type=='MESH');ev=o.evaluated_get(dg);me=ev.to_mesh();vv=[o.matrix_world@v.co for v in me.vertices];groups={g.index:g.name for g in o.vertex_groups};upper={i for i,n in groups.items() if any(s in n.lower() for s in ('hand','finger','thumb','forearm','upperarm','lowerarm','wrist'))};ids={v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in upper)>.025};ff=[tuple(p.vertices) for p in me.polygons]
        bodies[k]=BVHTree.FromPolygons(vv,ff);fits[k]=BVHTree.FromPolygons(vv,[p for p in ff if not any(i in ids for i in p)]);arms[k]=BVHTree.FromPolygons(vv,[p for p in ff if any(i in ids for i in p)]);ev.to_mesh_clear()
    meta=M.build_units(SimpleNamespace(a=a),fits);bpy.context.view_layer.update();(F/'BusinessBelt41_Model.json').write_text(json.dumps(meta,indent=2))
    report['passes'].append(dict(check='True low-hip route fit to body-only surfaces',meta=meta))
    results=[];bad=[]
    for kind,aid in zip(('Crew','Generic'),M.IDS):
        col=bpy.data.collections[aid];pp,ff=geo(col);probes=list(pp);probes.extend(sum((pp[i] for i in face),Vector())/len(face) for face in ff);probes.extend((pp[p[j]]+pp[p[(j+1)%len(p)]])*.5 for p in ff for j in range(len(p)));targets=('Crew',) if kind=='Crew' else ('Crew','Hoodie');minimum=999;armgap=999;inside=[]
        for p in probes:
            for k in targets:
                h=bodies[k].find_nearest(p);signed=(p-h[0]).dot(h[1]);minimum=min(minimum,signed);armgap=min(armgap,arms[k].find_nearest(p)[3])
                if signed<-.0015:inside.append(dict(p=list(p),body=k,signed=signed))
        result=dict(kind=kind,probes=len(probes),minimum_full_body_signed_m=minimum,minimum_arm_distance_m=armgap,inside=len(inside));results.append(result)
        if inside:bad.append(dict(**result,examples=inside[:8]))
        # The actual retained lid is tested at its new absolute hinge as well.
        vv,faces=geo(lid);origin=Vector(meta['worn'][kind]['hinge']);lp=[p+origin for p in vv]
        for p in lp:
            for k in targets:
                h=bodies[k].find_nearest(p);assert (p-h[0]).dot(h[1])>-.0005,(kind,'lid/body',list(p))
    assert not bad,bad
    report['passes'].append(dict(check='Complete band/buckle vertex-edge-face contact against full final body including arms/hands',results=results))
    triangles=0;zero=[]
    for aid in M.IDS:
        c=bpy.data.collections[aid];c.use_fake_user=True;bpy.context.scene.collection.children.link(c)
        for o in c.objects:
            ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);zero.extend(t.area for t in me.loop_triangles if t.area<1e-12);ev.to_mesh_clear()
    assert not zero;report['passes'].append(dict(check='Actual modeled geometry',triangles=triangles,degenerates=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'BusinessBelt41_UnitKits.blend'));report['passed']=True
except Exception:report['error']=traceback.format_exc()
(F/'BusinessBelt41_Verification.json').write_text(json.dumps(report,indent=2));print('BELT41',report['passed'],report.get('error',''),flush=True)
