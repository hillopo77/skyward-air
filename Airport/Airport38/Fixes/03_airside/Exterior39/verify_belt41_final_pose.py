"""Read-only frozen Belt41 versus the final current posed character surfaces."""
import bpy,sys,json,hashlib,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;C=F.parents[5]/'outputs/Characters/Revision39';source=C/'Characters39.blend';before=hashlib.sha256(source.read_bytes()).hexdigest();report=dict(passed=False,source_sha256=before,read_only=True)
sys.path.insert(0,str(F));import business_belt40 as B
try:
    ids=['CHAR39_PassengerCrew_LuxurySeated','CHAR39_PassengerHoodie_LuxurySeated']
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.collections=list(ids)
    chars=dict(zip(('Crew','Hoodie'),dst.collections))
    ids=['SM_AP_B41LapWornCrew','SM_AP_B41LapWornGeneric']
    with bpy.data.libraries.load(str(F/'BusinessBelt41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(ids)
    belts=dict(zip(('Crew','Generic'),dst.collections))
    with bpy.data.libraries.load(str(F/'BusinessBelt40_UnitKits.blend'),link=False) as (src,dst):dst.collections=['SM_AP_B40ReleaseLid']
    lid=dst.collections[0]
    for c in list(chars.values())+list(belts.values())+[lid]:bpy.context.scene.collection.children.link(c)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geo(c,character=False):
        vv=[];ff=[]
        for o in c.objects:
            if o.type!='MESH':continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();T=o.matrix_world if character else B._matrix(o);base=len(vv);vv.extend(T@v.co for v in me.vertices);ff.extend(tuple(base+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
        return vv,ff
    body={};arm={}
    for key,c in chars.items():
        vv,ff=geo(c,True);body[key]=BVHTree.FromPolygons(vv,ff);o=next(o for o in c.objects if o.type=='MESH');vg={g.index:g.name for g in o.vertex_groups};ids={i for i,n in vg.items() if any(s in n.lower() for s in ('hand','finger','thumb','forearm','upperarm','lowerarm','wrist'))};vertices={v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in ids)>.025};arm[key]=BVHTree.FromPolygons(vv,[p for p in ff if any(i in vertices for i in p)])
    meta=json.loads((F/'BusinessBelt41_Model.json').read_text());results=[]
    for kind,col in belts.items():
        pp,ff=geo(col);probes=list(pp);probes.extend(sum((pp[i] for i in face),Vector())/len(face) for face in ff);probes.extend((pp[p[j]]+pp[p[(j+1)%len(p)]])*.5 for p in ff for j in range(len(p)));minimum=999;armgap=999;inside=0;targets=('Crew',) if kind=='Crew' else ('Crew','Hoodie')
        for p in probes:
            for key in targets:
                h=body[key].find_nearest(p);signed=(p-h[0]).dot(h[1]);minimum=min(minimum,signed);armgap=min(armgap,arm[key].find_nearest(p)[3]);inside+=int(signed<-.0015)
        assert inside==0,(kind,inside,minimum);assert armgap>.001,(kind,armgap)
        vv,_=geo(lid);origin=Vector(meta['worn'][kind]['hinge']);lidmin=999
        for p in vv:
            p+=origin
            for key in targets:
                h=body[key].find_nearest(p);lidmin=min(lidmin,(p-h[0]).dot(h[1]))
        assert lidmin>-.0005,(kind,lidmin);results.append(dict(kind=kind,probes=len(probes),minimum_full_body_clearance_m=minimum,minimum_arm_distance_m=armgap,lid_minimum_clearance_m=lidmin,inside=inside))
    assert before==hashlib.sha256(source.read_bytes()).hexdigest(),'Character source changed during proof'
    report.update(passed=True,results=results,belt_bundle_sha256=hashlib.sha256((F/'BusinessBelt41_UnitKits.blend').read_bytes()).hexdigest(),no_source_or_bundle_writes=True)
except Exception:report['error']=traceback.format_exc()
(F/'BusinessBelt41_FinalPoseVerification.json').write_text(json.dumps(report,indent=2));print('BELT41_FINAL_POSE',report['passed'],report.get('error',''),flush=True)
