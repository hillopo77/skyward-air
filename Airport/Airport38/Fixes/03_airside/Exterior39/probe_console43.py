"""Read-only small current-master tray/slot geometry diagnostic."""
import bpy,bmesh,sys,json,traceback,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];source=R/'Airport_Repaired38.blend';report=dict(passed=False,source=str(source))
try:
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        names=[n for n in src.collections if n in ('SM_Plane_AnalogDashboard','SM_Plane_Controls','SM_AP_F39DashboardFixed','SM_AP_F39ControlsFixed')];report['available_matching']=[n for n in src.collections if 'Dashboard' in n or 'Controls' in n];dst.collections=list(names)
    for c in dst.collections:bpy.context.scene.collection.children.link(c)
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rows=[]
    for c in dst.collections:
        for o in c.objects:
            if o.type!='MESH' or not any(n in o.name.lower() for n in ('toggle control tray','tray front slot','switch tray')):continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();p=[o.matrix_world@v.co for v in me.vertices];ff=[tuple(q.vertices) for q in me.polygons];tree=BVHTree.FromPolygons(p,ff);pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and not set(ff[i])&set(ff[j])];bm=bmesh.new();bm.from_mesh(me)
            row=dict(collection=c.name,part=o.name,raw_vertices=len(o.data.vertices),evaluated_vertices=len(p),triangles=len(me.loop_triangles),zero_triangles=sum(t.area<1e-12 for t in me.loop_triangles),self_crossing_pairs=len(pairs),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),signed_volume=bm.calc_volume(signed=True),min=[min(v[k] for v in p) for k in range(3)],max=[max(v[k] for v in p) for k in range(3)],materials=[m.name if m else None for m in me.materials],modifiers=[dict(name=m.name,type=m.type,width=getattr(m,'width',None),clamp=getattr(m,'use_clamp_overlap',None)) for m in o.modifiers],custom_normals=me.has_custom_normals)
            bm.free();ev.to_mesh_clear();rows.append(row)
    report.update(passed=True,parts=rows,all_object_names={c.name:[o.name for o in c.objects] for c in dst.collections})
except Exception:report['error']=traceback.format_exc()
(F/'Console43_Diagnosis.json').write_text(json.dumps(report,indent=2));print('CONSOLE43',report.get('passed'),report.get('error',''),report.get('parts'),flush=True)
