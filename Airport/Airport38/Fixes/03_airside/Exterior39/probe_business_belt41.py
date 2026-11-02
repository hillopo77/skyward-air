"""Read-only actual final hand/low-abdomen route diagnosis; no asset writes."""
import bpy,sys,json,traceback,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;C=F.parents[5]/'outputs/Characters/Revision39';source=C/'Characters39.blend'
report=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),postures={})
try:
    names=['CHAR39_PassengerCrew_LuxurySeated','CHAR39_PassengerHoodie_LuxurySeated']
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.collections=list(names)
    for n,c in zip(names,dst.collections):
        bpy.context.scene.collection.children.link(c)
        bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ob=next(o for o in c.objects if o.type=='MESH');ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();vs=[ob.matrix_world@v.co for v in me.vertices]
        assert len(vs)==len(ob.data.vertices),(len(vs),len(ob.data.vertices))
        vg={g.index:g.name for g in ob.vertex_groups};groups=sorted(vg.values());print(n,groups,flush=True)
        upper=lambda name:any(s in name.lower() for s in ('hand','finger','thumb','forearm','upperarm','lowerarm','arm.','wrist'))
        excluded={i for i,name in vg.items() if upper(name)}
        armids={v.index for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in excluded)>.025}
        handgroups={i for i,name in vg.items() if any(s in name.lower() for s in ('hand','finger','thumb','wrist'))}
        handids={v.index for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in handgroups)>.25}
        fullfaces=[tuple(p.vertices) for p in me.polygons];bodyfaces=[p for p in fullfaces if not any(i in armids for i in p)]
        body=BVHTree.FromPolygons(vs,bodyfaces);full=BVHTree.FromPolygons(vs,fullfaces);front=[]
        arm=BVHTree.FromPolygons(vs,[p for p in fullfaces if any(i in armids for i in p)])
        for z in (.64,.66,.68,.70,.72,.74,.76,.78,.80):
            for x in (-.25,-.20,-.15,-.10,-.05,0,.05,.10,.15,.20,.25):
                a=body.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)[0];b=full.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)[0]
                front.append(dict(x=x,z=z,body_y=a.y if a else None,full_y=b.y if b else None))
        hands={}
        for side in (-1,1):
            pp=[vs[i] for i in handids if vs[i].x*side>0]
            hands[str(side)]=dict(vertices=len(pp),min=[min(p[i] for p in pp) for i in range(3)],max=[max(p[i] for p in pp) for i in range(3)])
        candidates=[]
        for side_z in (.60,.62,.64,.66,.70,.72,.74,.76,.78):
            for front_z in (.60,.62,.64,.66,.68,.705):
                points=[];missing=0
                for side in (-1,1):
                    for j in range(129):
                        angle=120-(120-12)*j/128;theta=math.radians(side*angle);direction=Vector((math.sin(theta),-math.cos(theta),0));t=max(0,min(1,(35-angle)/23));s=t*t*(3-2*t);zc=side_z+(front_z-side_z)*s
                        for z in (zc-.019,zc+.019):
                            origin=Vector((0,-.135,z));h=body.ray_cast(origin+direction*.8,-direction,.8)
                            if h[0] is None:missing+=1;continue
                            normal=h[1].normalized()
                            if normal.dot(direction)<0:normal=-normal
                            points.append(h[0]+normal*.006)
                signed=[];armdist=[]
                for p in points:
                    h=full.find_nearest(p);signed.append((p-h[0]).dot(h[1]));armdist.append(arm.find_nearest(p)[3])
                si=min(range(len(signed)),key=lambda i:signed[i]);ai=min(range(len(armdist)),key=lambda i:armdist[i])
                candidates.append(dict(side_z=side_z,front_z=front_z,minimum_full_body_signed=min(signed),minimum_arm_distance=min(armdist),worst_body_point=list(points[si]),closest_arm_point=list(points[ai]),missing=missing))
        report['postures'][n]=dict(groups=groups,excluded_groups=[vg[i] for i in excluded],excluded_arm_vertices=len(armids),body_triangles=len(bodyfaces),hands=hands,front_grid=front,candidates=candidates)
        ev.to_mesh_clear()
    report['passed']=True
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'BusinessBelt41_RouteDiagnosis.json').write_text(json.dumps(report,indent=2));print('BELT41_ROUTE',report.get('passed'),report.get('error',''),flush=True)
