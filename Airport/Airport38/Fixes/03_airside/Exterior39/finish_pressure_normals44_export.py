"""Finish only the private manifest after its original FBXs exported cleanly."""
import bpy,sys,json,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
F=Path(__file__).parent;A=F.parents[3];sys.path[:0]=[str(F),str(A/'SourceAssets')]
import airport_model as a
import pressure_normals44 as M
with bpy.data.libraries.load(str(F/'PressureNormals44_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(M.IDS)
for aid,c in zip(M.IDS,dst.collections):
    bpy.context.scene.collection.children.link(c);a.ASSETS[aid]=dict(collection=c,collision='complex')
    for ob in c.objects:
        for mat in ob.data.materials:
            if mat:a.MATS[mat.name]=mat
out=F/'PressureNormals44_Exports';namespace={};code=(A/'Rooms24/SourceAssets/airport_export24.py').read_text().replace("'Airport_Rooms24.blend'","'../PressureNormals44_UnitKits.blend'");exec(compile(code,'private_normal_export44','exec'),namespace);namespace['export'](NS(ASSETS=a.ASSETS,MATS=a.MATS,ROOT=out))
report=json.loads((F/'PressureNormals44_Verification.json').read_text());assert all(q['before_fingerprint_excluding_custom_normals']==q['after_fingerprint_excluding_custom_normals'] for q in report['first_pass']['collections']);assert report['repeat_geometry_stable']
if 'error' in report:report['initial_private_manifest_filename_error']=report.pop('error')
report.update(passed=True,private_exports=str(out/'Exports'),editable_kit_sha256=hashlib.sha256((F/'PressureNormals44_UnitKits.blend').read_bytes()).hexdigest());(F/'PressureNormals44_Verification.json').write_text(json.dumps(report,indent=2));print('PRESSURE_NORMALS44_PRIVATE_EXPORT_COMPLETE',flush=True)
