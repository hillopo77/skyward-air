"""Factory-empty5-pass fitting regression using the exact linked source assets."""
import bpy,json,sys,copy,math
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(R.parent/'SourceAssets'))
import exterior39 as E
import airport_model as a
PM=json.loads((R.parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
ids=set(E.SWAPS)|{'SM_Plane_DoorBay07','SM_Plane_WindowShadeSlat18_L','SM_Plane_WindowShadeSlat18_R','SM_Plane_WindowShadeHandle18_L','SM_Plane_WindowShadeHandle18_R'}
with bpy.data.libraries.load(str(R.parent.parent/'SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=list(ids)
cols={c.name:c for c in dst.collections if c}
for c in cols.values():bpy.context.scene.collection.children.link(c)
bpy.context.view_layer.update()
def points(col):return [E._matrix(o)@v.co for o in col.objects if o.type=='MESH' for v in o.data.vertices]
passes=[]
old_caps=[]
for side,suffix in [(-1,'L'),(1,'R')]:
 o=next(o for o in cols['SM_Plane_WindowShadeFrame18_'+suffix].objects if o.name.startswith('Shade retained upper pocket18'))
 p=[E._matrix(o)@v.co for v in o.data.vertices]
 violations=[abs(side*2.3+q.x)-E.pressure_x(q.z+.92) for q in p]
 old_caps+=violations
passes.append(dict(pass_id=1,actual='Original linked source diagnosis',maximum_pocket_outside_skin_m=max(old_caps),redundant_cockpit_tubes=sum(o.name.startswith('Fitted rounded pearl glazing reveal18') for o in cols['SM_Plane_CockpitShell'].objects)))
assert max(old_caps)>.1
D=json.loads((R/'Exports/airport_layout.json').read_text())
ctx=SimpleNamespace(a=a,D=D,R=R,scene=bpy.context.scene)
for ins in PM['instances']:
 if ins['asset'] not in E.SWAPS:continue
 o=bpy.data.objects.new(ins['name'],None);o.instance_type='COLLECTION';o.instance_collection=cols[ins['asset']];o.location=[ins['location'][0]+16,*ins['location'][1:]];bpy.context.scene.collection.objects.link(o)
out=E.apply(ctx);bpy.context.view_layer.update()
assert len(out['changed_assets'])==6
new=bpy.data.collections[E.SWAPS['SM_Plane_CockpitShell']]
assert not any(o.name.startswith('Fitted rounded pearl glazing reveal18') for o in new.objects)
old_panes=[o for o in cols['SM_Plane_CockpitShell'].objects if o.name.startswith('Fitted curved cockpit glazing11')]
new_panes=[o for o in new.objects if o.name.startswith('Fitted curved cockpit glazing11')]
assert len(old_panes)==len(new_panes)==6
for x,y in zip(old_panes,new_panes):assert [tuple(p) for p in points(SimpleNamespace(objects=[x]))]==[tuple(p) for p in points(SimpleNamespace(objects=[y]))]
passes.append(dict(pass_id=2,actual='Source model removed redundant framing; six exact pressure-shell panes retained',tube_count_after=0,unchanged_glazing_vertices=sum(len(o.data.vertices) for o in new_panes)))
# Pocket shells/guides are evaluated, including bevel and physical thickness.
dg=bpy.context.evaluated_depsgraph_get();max_skin=-999;eval_points=0;lower_clearance=[]
for side,suffix in [(-1,'L'),(1,'R')]:
 c=bpy.data.collections[E.SWAPS['SM_Plane_WindowShadeFrame18_'+suffix]]
 for ob in c.objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh()
  for v in me.vertices:
   p=E._matrix(ob)@v.co;x=abs(side*2.3+p.x);z=p.z+.92
   max_skin=max(max_skin,x-E.pressure_x(z));eval_points+=1
   if ob.name.startswith(('E39 continuous formed open C guide','E39 retained guide felt')) and z<1.3566:lower_clearance.append(x-2.32)
  ev.to_mesh_clear()
assert max_skin<-.015,('New pocket still pierces outer skin',max_skin)
assert lower_clearance and min(lower_clearance)>.012,('Guide reintroduces business side-shell intersection',min(lower_clearance))
passes.append(dict(pass_id=3,actual='Curved pocket/C-guide pressure-skin and business-shell fit after actual model evaluation',evaluated_vertices=eval_points,minimum_inside_skin_m=-max_skin,minimum_business_shell_clearance_m=min(lower_clearance)))
class Plane:
 DATA=copy.deepcopy(PM)
P=Plane()
for q in P.DATA['interactions']:
 for part in q.get('roller_parts',[]):part['closed_location'][0]+=16
closed={q['actor']:copy.deepcopy(q.get('roller_parts')) for q in P.DATA['interactions'] if q.get('roller_parts')}
E.prepare_plane(P,D)
assert P.DATA['exterior39_shades']['interactions']==48
positions=0;outside=-999
byname={q['name']:q for q in PM['instances']}
for q in P.DATA['interactions']:
 if not q.get('roller_parts'):continue
 for old,newpart in zip(closed[q['actor']],q['roller_parts']):
  assert old['closed_location']==newpart['closed_location']
  src=cols[byname[newpart['actor']]['asset']]
  pp=points(src)
  for i in range(21):
   f=i/20
   for p in pp:
    x=p.x+newpart['closed_location'][0]-16+newpart['delta'][0]*f
    z=p.z+newpart['closed_location'][2]+newpart['delta'][2]*f
    outside=max(outside,abs(x)-E.pressure_x(z));positions+=1
assert outside<-.015,('Shade stroke exits the pressure shell',outside)
snapshot=copy.deepcopy(P.DATA);E.prepare_plane(P,D);assert snapshot==P.DATA
passes.append(dict(pass_id=4,actual='All48 shade mechanisms over21 stroke positions with unchanged closed poses/targets',sampled_slat_vertices=positions,minimum_inside_skin_m=-outside,idempotent=True))
bad=[];faces=0
for aid in out['changed_assets']:
 c=bpy.data.collections[aid]
 for ob in c.objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh();me.update();faces+=len(me.polygons)
  for p in me.polygons:
   if p.area<1e-13:bad.append((aid,ob.name,p.index,p.area))
  ev.to_mesh_clear()
assert not bad,bad[:25]
bindings=copy.deepcopy(out['source_instances'])
E.finalize(ctx);assert bindings==ctx.D['repair38']['exterior39']['source_instances']
for aid in ['SM_AP_E39ShadeFrameL','SM_AP_E39ShadeFrameR']:assert bpy.data.collections[aid]['e39_guidefit_version']==2
# Reproduce the actual already-derived version1 starting state in this private
# factory-empty test, then exercise finalize rather than assuming fresh apply.
for side,suffix in [(-1,'L'),(1,'R')]:
 aid='SM_AP_E39ShadeFrame'+suffix
 bpy.data.collections.remove(bpy.data.collections[aid])
 col,_=E._clone(ctx,'SM_Plane_WindowShadeFrame18_'+suffix,aid)
 col['exterior39_details']=json.dumps(E._shade_pocket(ctx,col,side));col['e39_guidefit_version']=1
E.finalize(ctx);bpy.context.view_layer.update()
for side,suffix in [(-1,'L'),(1,'R')]:
 col=bpy.data.collections['SM_AP_E39ShadeFrame'+suffix]
 assert col['e39_guidefit_version']==2
 for ob in col.objects:
  if not ob.name.startswith(('E39 continuous formed open C guide','E39 retained guide felt')):continue
  for p in points(SimpleNamespace(objects=[ob])):
   if p.z+.92<1.3566:assert abs(side*2.3+p.x)>2.3339
for old,newid in E.SWAPS.items():
 if 'PassengerDoor' not in old:continue
 # The actual leaf's source aperture vertices and origin remain identical;
 # manufacturing radius lives in a nondestructive modifier.
 a0=next(o for o in cols[old].objects if o.name.startswith('Pressure door formed leaf'))
 b0=next(o for o in bpy.data.collections[newid].objects if o.name.startswith('Pressure door formed leaf'))
 assert [tuple(v.co) for v in a0.data.vertices]==[tuple(v.co) for v in b0.data.vertices]
seals=bpy.data.collections[E.SWAPS['SM_Plane_OuterWindowBarrel']]
assert sum(o.name.startswith('E39 continuous swept opaque weather gasket') for o in seals.objects)==2
assert all(all(m==a.MATS['E39Seal'] for m in o.data.materials) for o in seals.objects if o.name.startswith('E39 continuous swept opaque weather gasket'))
passes.append(dict(pass_id=5,actual='Evaluated doors, weather seals, surfaces, all bindings and actual version1-to2 upgrade',evaluated_faces=faces,zero_area_faces=len(bad),doors_aperture_vertices_unchanged=True,source_instances=len(out['source_instances']),version1_upgrade_tested=True))
report=dict(status='PASS',passes=passes,changed_assets=out['changed_assets'],native_swap_instances=len(out['source_instances']),source_master_modified=False,native_visual_review='required after root import')
(ROOT/'Exterior39_FivePasses.json').write_text(json.dumps(report,indent=2))
print('EXTERIOR39 PASS',len(passes),'actual passes',faces,'faces',len(out['source_instances']),'placements',flush=True)
