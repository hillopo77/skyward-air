import bpy,sys,json,traceback,hashlib
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;ROOT=F.parents[5];R=F.parents[2];sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import aircraft_finish42 as M
import window40 as W
report=dict(passed=False,passes=[])
try:
    ids=list(M.SWAPS)+['SM_Plane_CockpitShell']
    with bpy.data.libraries.load(str(ROOT/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols=dict(zip(ids,dst.collections))
    for c in cols.values():bpy.context.scene.collection.children.link(c)
    result=M.build_units(SimpleNamespace(a=a))
    for n in M.SWAPS.values():bpy.context.scene.collection.children.link(bpy.data.collections[n])
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geo(o):
        ev=o.evaluated_get(dg);me=ev.to_mesh();T=W._matrix(o);vv=[T@v.co for v in me.vertices];ff=[tuple(p.vertices) for p in me.polygons];ev.to_mesh_clear();return vv,ff
    def signature(o):return hashlib.sha256(str((([tuple(v.co) for v in o.data.vertices] if o.type=='MESH' else o.data.body),W._matrix(o))).encode()).hexdigest()
    rows=[];triangles=0;zero=[]
    for old,new in M.SWAPS.items():
        before=cols[old];after=bpy.data.collections[new];preserved=0
        for ob,q in zip(before.objects,after.objects):
            if not ob.name.startswith(('Flexible flat carry-loop webbing15','Zipper tape seated in top seam15','Duffel interlocking zipper tooth15')):assert signature(ob)==signature(q),(old,ob.name);preserved+=1
        allp=[];oldp=[]
        for o in after.objects:
            pp,_=geo(o);allp+=pp;ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);zero.extend((o.name,t.area) for t in me.loop_triangles if t.area<1e-12);ev.to_mesh_clear()
        for o in before.objects:oldp+=geo(o)[0]
        row=dict(asset=new,preserved_geometry_parts=preserved,old_minz=min(p.z for p in oldp),new_minz=min(p.z for p in allp),old_maxz=max(p.z for p in oldp),new_maxz=max(p.z for p in allp));assert abs(row['old_minz']-row['new_minz'])<1e-8,row
        if 'Duffel' in new or 'Weekender' in new:
            body=next(o for o in after.objects if o.name.startswith('Tailored canvas'));vv,ff=geo(body);tree=BVHTree.FromPolygons(vv,ff);gaps=[]
            for o in after.objects:
                if not o.name.startswith('Flexible flat carry-loop'):continue
                pp,_=geo(o)
                for p in pp:
                    h=tree.ray_cast(Vector((p.x,p.y,1)),Vector((0,0,-1)),2)[0]
                    if h:gaps.append(p.z-h.z)
            assert min(gaps)>-.0002 and max(gaps)<.010,(new,min(gaps),max(gaps));row.update(handle_canvas_gap=[min(gaps),max(gaps)])
        rows.append(row)
    assert not zero,zero[:15];report['passes']=[dict(check='Preserved all non-handle geometry and original ground-contact minima',assets=rows),dict(check='Actual evaluated modeled geometry',triangles=triangles,degenerates=0)]
    shell=cols['SM_Plane_CockpitShell'];candidate=[]
    for o in shell.objects:
        if o.type=='MESH' and any(s in o.name.lower() for s in ('cheek','sill','lower','liner','coaming')):
            pp,_=geo(o);candidate.append(dict(name=o.name,materials=[m.name for m in o.data.materials],min=[min(p[i] for p in pp) for i in range(3)],max=[max(p[i] for p in pp) for i in range(3)]))
    report['cockpit_readonly_candidates']=candidate
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'AircraftFinish42_UnitKits.blend'));report.update(passed=True,details=result)
except Exception:report['error']=traceback.format_exc()
(F/'AircraftFinish42_Verification.json').write_text(json.dumps(report,indent=2));print('AIRCRAFT_FINISH42',report['passed'],report.get('error',''),flush=True)
