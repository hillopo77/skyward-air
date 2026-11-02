"""Isolated targeted-patch test using actual saved38 collections, never saving it."""
import bpy,sys,json,runpy,copy,math
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(R.parent/'SourceAssets'))
ns=runpy.run_path(str(ROOT/'inspect_assembly38_blender.py'))
import airport_model as a
for m in bpy.data.materials:
 if m.name.startswith('MI_AP_'):a.MATS[m.name[6:]]=m
from refine_contacts39 import apply
D=ns['D'];original=copy.deepcopy(D['character_placements'])
ctx=SimpleNamespace(a=a,D=D,R=R,scene=bpy.context.scene)
report=apply(ctx)
assert len(report['changed_assets'])==11
assert report['canopy']['previous_top_membrane_gap_m']>.10
assert report['canopy']['new_max_contact_gap_m']==0
assert report['stowed_sweep']['clear']
assert report['max_stowed_x']<-9.75
for q in report['characters']:
 old=next(v for v in original if v['actor']==q['actor'])
 assert abs(q['location'][0]-old['location'][0]-16)<1e-8
 assert q['location'][1:]==old['location'][1:]
before=copy.deepcopy(D['character_placements']);again=apply(ctx)
assert before==D['character_placements'],'Second patch must not shift passengers twice'
assert report['changed_assets']==again['changed_assets']
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();bad=[];faces=0
for spec in a.ASSETS.values():
 for o in spec['collection'].objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();m.update();faces+=len(m.polygons)
  for p in m.polygons:
   if p.area<1e-11:bad.append((o.name,p.index,p.area))
  e.to_mesh_clear()
assert not bad,bad[:20]
report.update(status='PASS',evaluated_faces_checked=faces,zero_area_faces=len(bad),idempotent=True,
 source_master_modified=False,source_read=str(R/'Airport_Repaired38.blend'))
(ROOT/'ContactRefinement39_Test.json').write_text(json.dumps(report,indent=2))
print('CONTACT39 PASS',len(report['changed_assets']),'assets',len(report['characters']),'NPCs',faces,'evaluated-faces',flush=True)
