import bpy,sys,json,hashlib,traceback,bmesh
from pathlib import Path
from types import SimpleNamespace as NS
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import console_surface43 as M
report=dict(passed=False)
try:
    with bpy.data.libraries.load(str(R/'Airport_Repaired38.blend'),link=False) as (src,dst):dst.collections=[M.OLD]
    old=dst.collections[0];bpy.context.scene.collection.children.link(old);result=M.build_unit(NS(a=a));new=bpy.data.collections[M.ID];bpy.context.scene.collection.children.link(new);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    originals=[o for o in old.objects if not o.name.startswith('Hollow switch tray casting')];copies=[o for o in new.objects if not o.name.startswith('C43 formed')];assert len(originals)==len(copies)
    def sig(o):return hashlib.sha256(str(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],tuple(tuple(row) for row in o.matrix_world),[m.name if m else None for m in o.data.materials])).encode()).hexdigest()
    assert all(sig(o)==sig(q) for o,q in zip(originals,copies)),'Unrelated dashboard object changed'
    ob=next(o for o in new.objects if o.name.startswith('C43 formed'));ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();pp=[v.co.copy() for v in me.vertices];ff=[tuple(p.vertices) for p in me.polygons];assert all(t.area>1e-12 for t in me.loop_triangles);tree=BVHTree.FromPolygons(pp,ff);pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and not set(ff[i])&set(ff[j])];assert not pairs,pairs[:8]
    bm=bmesh.new();bm.from_mesh(me);assert all(e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free();assert volume>0
    bounds=[[min(p[i] for p in pp) for i in range(3)],[max(p[i] for p in pp) for i in range(3)]];assert max(abs(x-y) for a1,a2 in zip(bounds,result['bounds_before']) for x,y in zip(a1,a2))<1e-6
    front=[];dots=[];hi=bounds[1][1]
    for p in me.polygons:
        if p.normal.y>.999 and abs(p.center.y-hi)<1e-5:
            front.append(p.index);dots.extend(me.corner_normals[i].vector.dot(Vector((0,1,0))) for i in p.loop_indices)
    assert front and min(dots)>.999,(len(front),min(dots) if dots else None)
    bores=[]
    for x in (-.1728,0,.1728):
        hit=tree.ray_cast(Vector((x,hi+.02,.966)),Vector((0,-1,0)),1);assert hit[0] is not None and hit[3]>.3,(x,hit);bores.append(hit[3])
    for x in (-.30,-.08,.08,.30):
        hit=tree.ray_cast(Vector((x,hi+.02,1.010)),Vector((0,-1,0)),1);assert hit[0] is not None and abs(hit[3]-.02)<1e-5,(x,hit)
    report.update(passed=True,result=result,preserved_other_parts=len(copies),bounds=bounds,triangles=len(me.loop_triangles),degenerates=0,self_crossings=0,nonmanifold_edges=0,signed_volume_m3=volume,front_planar_faces=len(front),minimum_front_corner_normal_dot=min(dots),three_real_vent_depths=bores);ev.to_mesh_clear();bpy.ops.wm.save_as_mainfile(filepath=str(F/'ConsoleSurface43_UnitKit.blend'))
except Exception:report['error']=traceback.format_exc()
(F/'ConsoleSurface43_Verification.json').write_text(json.dumps(report,indent=2));print('CONSOLE_SURFACE43',report['passed'],report.get('error',''),flush=True)
