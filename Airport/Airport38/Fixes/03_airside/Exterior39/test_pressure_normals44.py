"""Private two-kit normal repair/export proof; never opens/saves the master."""
import bpy,sys,json,traceback,copy,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
F=Path(__file__).parent;R=F.parents[2];A=R.parent;sys.path[:0]=[str(F),str(A/'SourceAssets')]
import airport_model as a
import pressure_normals44 as M
report=dict(passed=False,scope='Private two-collection append; source master untouched')
try:
    with bpy.data.libraries.load(str(R/'Airport_Repaired38.blend'),link=False) as (src,dst):dst.collections=list(M.IDS)
    for c in dst.collections:c.use_fake_user=True;bpy.context.scene.collection.children.link(c)
    ctx=NS(a=a,D={});first=M.apply(ctx);geometry={n:M.fingerprint(bpy.data.collections[n]) for n in M.IDS};second=M.apply(ctx);assert geometry=={n:M.fingerprint(bpy.data.collections[n]) for n in M.IDS}
    report.update(passed=True,first_pass=first,repeat_geometry_stable=True,repeat_normal_angle_max=max(p['after_angle_max'] for r in second['collections'] for p in r['parts']))
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'PressureNormals44_UnitKits.blend'))
    out=F/'PressureNormals44_Exports';(out/'Exports/FBX').mkdir(parents=True,exist_ok=True)
    namespace={};code=(A/'Rooms24/SourceAssets/airport_export24.py').read_text().replace("'Airport_Rooms24.blend'","'../PressureNormals44_UnitKits.blend'");exec(compile(code,'private_normal_export44','exec'),namespace);namespace['export'](NS(ASSETS=a.ASSETS,MATS=a.MATS,ROOT=out))
    report['private_exports']=str(out/'Exports');report['editable_kit_sha256']=hashlib.sha256((F/'PressureNormals44_UnitKits.blend').read_bytes()).hexdigest()
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'PressureNormals44_Verification.json').write_text(json.dumps(report,indent=2));print('PRESSURE_NORMALS44',report['passed'],report.get('error',''),flush=True)
