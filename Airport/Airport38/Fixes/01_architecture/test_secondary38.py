"""Read current saved master, apply in-memory patch, evaluate actual contacts; no save."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;R=HERE.parents[1];A=R.parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(A/'SourceAssets'))
import airport_model as a
from test_architecture38 import Context
import secondary_patch38
p=R/'Airport_Repaired38.blend';sha=hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False);D=json.loads(bpy.context.scene['layout_json'])
for mat in bpy.data.materials:
 if mat.name.startswith('MI_AP_'):a.MATS[mat.name[6:]]=mat
ctx=Context(D,a);ctx.scene=bpy.context.scene
def original_structure_tree():
 vv=[];ff=[];dg=bpy.context.evaluated_depsgraph_get()
 for aid in ['SM_AP_Walls38','SM_AP_Ceilings38','SM_AP_Roofs38']:
  for o in bpy.data.collections[aid].objects:
   if o.type!='MESH':continue
   eo=o.evaluated_get(dg);me=eo.to_mesh();offset=len(vv)
   vv += [o.matrix_world@v.co for v in me.vertices]
   ff += [tuple(offset+i for i in p.vertices) for p in me.polygons];eo.to_mesh_clear()
 return BVHTree.FromPolygons(vv,ff,all_triangles=False)
before=original_structure_tree()
assets={'SM_AP_Walls38','SM_AP_Ceilings38','SM_AP_Roofs38','SM_AP_Glazing38',
        'SM_AP_RetainedCraft38','SM_AP_Wayfinding38','SM_AP_GalleryStair35',
        'SM_AP_Floors38','SM_AP_Attachments38','SM_AP_ScreenBoard'}
sys.path.insert(0,str(HERE.parent/'04_rendering'));import coplanar38
def structural(name):return name in assets and name!='SM_AP_ScreenBoard'
baseline_overlap=coplanar38.find_conflicts(coplanar38.blender_faces(D,structural))
gap_rays=[dict(id='AT08_open_soffit_side',start=[-41.5,29,5.5],direction=[1,0,0],distance=1),
          dict(id='AT11_open_roof_step',start=[-45,15.5,7.06],direction=[0,1,0],distance=1)]
was_patched=bool(D.get('repair38',{}).get(secondary_patch38.TAG))
for ray in gap_rays:
 ray['before_hit']=before.ray_cast(Vector(ray['start']),Vector(ray['direction']),ray['distance'])[0] is not None
 if not was_patched:assert not ray['before_hit'],('Prepatch gap premise',ray)
result=secondary_patch38.apply(ctx)
# Test idempotence without adding duplicate collections/actors.
assert secondary_patch38.apply(ctx) is result
dg=bpy.context.evaluated_depsgraph_get();trees={};bounds={}
assets={'SM_AP_Walls38','SM_AP_Ceilings38','SM_AP_Roofs38','SM_AP_Glazing38',
        'SM_AP_RetainedCraft38','SM_AP_Wayfinding38','SM_AP_GalleryStair35',
        'SM_AP_Floors38','SM_AP_Attachments38','SM_AP_ScreenBoard'}
for q in D['instances']:
 if q['asset'] not in assets:continue
 col=bpy.data.collections[q['asset']];wm=Matrix.Translation(Vector(q['location']))@Matrix.Rotation(math.radians(q.get('rotation_degrees',0)),4,'Z')@Matrix.Diagonal(Vector(list(q.get('scale',[1,1,1]))+[1]))
 vv=[];ff=[]
 for o in col.all_objects:
  if o.type not in ['MESH','FONT'] or o.hide_render:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();world=wm@o.matrix_world
  pts=[world@v.co for v in me.vertices];offset=len(vv);vv+=pts
  ff += [tuple(offset+i for i in p.vertices) for p in me.polygons]
  if pts:
   bounds[q['name'],o.name]=([min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)])
  eo.to_mesh_clear()
 trees[q['name']]=BVHTree.FromPolygons(vv,ff,all_triangles=False)
def distance(actor,point):
 hit=trees[actor].find_nearest(Vector(point),1)
 assert hit[0] is not None,(actor,point)
 return hit[3]
tests=[]
def contact(id_,actor,point,tol=.002):
 d=distance(actor,point);assert d<=tol,(id_,actor,point,d)
 tests.append(dict(id=id_,actor=actor,point=point,distance_m=d,passed=True))
for id_,x,y,top,H in [('A07',-14.3,5.8,2.9386,3.4),('A08',-24.35,26.8,2.9886,3.8)]:
 for yy in (y-.65,y+.65):
  contact(id_+'_hanger_upper','Airport38 coherent ceiling union',[x+.025,yy,H])
  contact(id_+'_hanger_lower','Gate '+id_+' flight display',[x+.025,yy,top],.003)
contact('menu_floor','Airport38 coherent bounded floors',[-44.3,33.90,0])
contact('menu_deck','Crafted GalleryStair35',[-44.3,33.938,2.87])
for x in (-47.5,-42):contact('fascia_deck','Crafted GalleryStair35',[x,31.35,2.87])
contact('soffit_lower','Airport38 coherent ceiling union',[-40.965,25,4.56])
contact('soffit_upper','Airport38 coherent ceiling union',[-41.035,25,6.8])
for key,(lo,hi) in bounds.items():
 if key[0]=='Airport38 mounted legible route cues' and key[1].startswith('A08 '):assert hi[2]<3.38,('A08 crop',key,hi)
display=ctx.require('Compact departures display');assert display['rotation_degrees']==90
assert abs(display['location'][0]+42.847)<1e-6
contact('departures_back_wall','Airport38 complete physical perimeter and partitions',[-42.91,-10.2,2.2])
for ray in gap_rays:
 ray['after_hit']=trees['Airport38 verified architectural attachments'].ray_cast(Vector(ray['start']),Vector(ray['direction']),ray['distance'])[0] is not None
 if ray['id']=='AT08_open_soffit_side':assert ray['after_hit'],('Gap remains open',ray)
 else:ray['status']='UNRESOLVED; next architecture repair must close roof steps by union'
# The candidate checker is applied to the actual existing structural context plus
# the new attachment parts, not just an isolated new mesh.
sys.path.insert(0,str(HERE.parent/'04_rendering'));import coplanar38
def structural(name):return name in assets and name!='SM_AP_ScreenBoard'
overlap=coplanar38.find_conflicts(coplanar38.blender_faces(D,structural))
def conflictkey(c):return tuple((p['actor'],p['asset'],p['part']) for p in c['parts'])+(c['axis'],round(c['depth_m'],4))
oldkeys={conflictkey(c) for c in baseline_overlap['conflicts']}
introduced=[c for c in overlap['conflicts'] if conflictkey(c) not in oldkeys]
(HERE/'SecondaryCoplanarity38.json').write_text(json.dumps(overlap,indent=2))
out=dict(status='PATCH_CONTACTS_PASS_WITH_REMAINING_BASELINE_FINDINGS' if not introduced else 'NEW_CANDIDATES_REQUIRE_SCRUTINY',source_sha256=sha,
         result=result,contacts=tests,gap_rays=gap_rays,coplanarity=overlap,
         baseline_candidate_count=len(baseline_overlap['conflicts']),introduced_candidates=introduced,
         unchanged_master=hashlib.sha256(p.read_bytes()).hexdigest()==sha,
         native_validation='NOT RUN. Root must import targeted assets, update actor, and recapture.')
(HERE/'SecondaryValidation38.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
assert out['unchanged_master']
