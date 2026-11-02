"""Repair already-outward crown state; exact original buffers and raw arrays."""
import bpy,sys,json,traceback,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
F=Path(__file__).parent;R=F.parents[2];A=R.parent;sys.path[:0]=[str(F),str(A/'SourceAssets')]
import airport_model as a
import pressure_normals44 as M
report=dict(passed=False,scope='Private append from already-applied44 master; master untouched')
try:
    with bpy.data.libraries.load(str(R/'Airport_Repaired38.blend'),link=False) as (src,dst):dst.collections=list(M.IDS)
    for c in dst.collections:c.use_fake_user=True;bpy.context.scene.collection.children.link(c)
    ctx=NS(a=a,D={});first=M.apply(ctx);geometry={n:M.fingerprint(bpy.data.collections[n]) for n in M.IDS};before_normals={n:[[list(v.vector) for v in o.data.corner_normals] for o in bpy.data.collections[n].objects] for n in M.IDS}
    second=M.apply(ctx)
    assert geometry=={n:M.fingerprint(bpy.data.collections[n]) for n in M.IDS}
    assert before_normals=={n:[[list(v.vector) for v in o.data.corner_normals] for o in bpy.data.collections[n].objects] for n in M.IDS}
    report.update(first_pass=first,repeat_full_normal_buffers_identical=True,repeat_geometry_stable=True)
    kit=F/'PressureNormals44B_UnitKits.blend';bpy.ops.wm.save_as_mainfile(filepath=str(kit))
    out=F/'PressureNormals44B_Exports';(out/'Exports/FBX').mkdir(parents=True,exist_ok=True)
    namespace={};code=(A/'Rooms24/SourceAssets/airport_export24.py').read_text().replace("'Airport_Rooms24.blend'","'../PressureNormals44B_UnitKits.blend'");exec(compile(code,'private_normal_export44b','exec'),namespace);namespace['export'](NS(ASSETS=a.ASSETS,MATS=a.MATS,ROOT=out))
    report.update(passed=True,private_exports=str(out/'Exports'),editable_kit_sha256=hashlib.sha256(kit.read_bytes()).hexdigest())
except Exception:report.update(error=traceback.format_exc())
(F/'PressureNormals44B_Verification.json').write_text(json.dumps(report,indent=2));print('PRESSURE_NORMALS44B',report['passed'],report.get('error',''),flush=True)
