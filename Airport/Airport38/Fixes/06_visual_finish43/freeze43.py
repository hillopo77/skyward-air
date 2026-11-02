"""Freeze exact final source, hook, textures, verification report and unit hashes."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'Source43Report.json').read_text())
assert report['actual_reopen_verified'] and report['repeat_safe_after_reopen_verified']
assert report['service_identity_actual_reopen_verified']
assert len(report['reopened_service_clearance_rays'])==18
assert len(report['service_identity_bearing_bounds'])==10
master=HERE.parents[1]/'Airport_Repaired38.blend'
mastersha=hashlib.sha256(master.read_bytes()).hexdigest()
assert mastersha==report['source_master_sha256']
files=['finish43.py','native_finish43.py','make_textures43.py','source_unit43.py','reopen_unit43.py','freeze43.py',
       'README.md','Integration43.json','Source43Report.json','Unit43Layout.json','TerminalFinish43_UnitKit.blend']
files+=['Textures/'+p.name for p in sorted((HERE/'Textures').glob('*.png'))]
frozen={name:dict(bytes=(HERE/name).stat().st_size,sha256=hashlib.sha256((HERE/name).read_bytes()).hexdigest()) for name in files}
out=dict(status='FROZEN_SOURCE_ACTUALLY_REOPENED_NATIVE_PENDING',files=frozen,
 source_master_sha256_unchanged=mastersha,service_identity=['BAY 01','BAY 02'],
 expected_native_material_graphs=13,packed_texture_roles=7,
 final_source_parts=596,wall_cassettes=298,feed_clearance_rays=18,
 native_integration='Integration43.json',
 prior_source_comparison_images='Evidence/*After* precede the final identity-only addition; no new render requested',
 jobs_closed=True,native_verified=False)
(HERE/'Frozen43.json').write_text(json.dumps(out,indent=2))
print('FROZEN43',json.dumps(dict(unit_sha256=frozen['TerminalFinish43_UnitKit.blend']['sha256'],
 source_sha256=frozen['finish43.py']['sha256'],native_hook_sha256=frozen['native_finish43.py']['sha256'],files=len(files))))
