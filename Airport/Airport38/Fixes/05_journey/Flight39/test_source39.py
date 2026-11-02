"""Read-only master load, isolated39 builds, evaluated geometry checks. No save."""
import bpy,sys,json,ast,copy,math,traceback
from pathlib import Path
F=Path(__file__).parent;R=F.parents[2];A=R.parent
sys.path[:0]=[str(F),str(A/'SourceAssets')]
report=dict(scope='Independent background source evaluation only; shared master never saved',checks=[])
try:
    bpy.ops.wm.open_mainfile(filepath=str(R/'Airport_Repaired38.blend'),load_ui=False)
    import airport_model as a
    for m in bpy.data.materials:
        if m.name.startswith('MI_AP_'):a.MATS[m.name[6:]]=m
    tree=ast.parse((R/'SourceAssets/build_source38.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context')
    env=dict(bpy=bpy,copy=copy,math=math,R=R,A=A,P=R);exec(compile(ast.Module(body=[node],type_ignores=[]),'contextclass','exec'),env)
    D=json.loads((R/'Exports/airport_layout.json').read_text());ctx=env['Context'](a,D,bpy.context.scene)
    import airfield39,flight39_surfaces,flight39_gear
    airfield39.plan(ctx);airfield39.build(ctx);flight39_surfaces.build(ctx);flight39_gear.build(ctx)
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    for aid,spec in a.ASSETS.items():
        count=0;zero=0;bad=0;badobjects=[]
        for ob in spec['collection'].objects:
            if ob.type not in ('MESH','FONT'):continue
            ev=ob.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();count+=len(mesh.loop_triangles)
            z=sum(t.area<1e-12 for t in mesh.loop_triangles);zero+=z
            if z:badobjects.append(dict(name=ob.name,zero_area=z))
            bad+=sum(not all(math.isfinite(c) for c in v.co) for v in mesh.vertices);ev.to_mesh_clear()
        report['checks'].append(dict(asset=aid,triangles=count,zero_area=zero,nonfinite_vertices=bad,bad_objects=badobjects,passed=count>0 and zero==0 and bad==0))
    report['metadata']=D['flight39'];report['passed']=all(q['passed'] for q in report['checks'])
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'SourceGeometryPass39.json').write_text(json.dumps(report,indent=2));print('FLIGHT39_SOURCE',report['passed'],[(q['asset'],q['zero_area']) for q in report['checks']],report.get('error',''),flush=True)
