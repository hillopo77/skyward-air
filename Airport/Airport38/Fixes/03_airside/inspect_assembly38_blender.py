"""Read actual38 library data; measure joinery without opening/editing its master."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[1]
sys.path.insert(0,str(ROOT));from airside_math38 import *
D=json.loads((R/'Exports/airport_layout.json').read_text());path=R/'Airport_Repaired38.blend'
ids={q['asset'] for q in D['aircraft38']['bridge']['components']}
with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.collections=[n for n in src.collections if n in ids]
cols={c.name:c for c in dst.collections if c}
for c in cols.values():bpy.context.scene.collection.children.link(c)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
vertices=[];polygons=[];parts=[]
for inst in D['instances']:
 if inst['asset'] not in cols:continue
 T=Matrix.Translation(Vector(inst['location']))@Matrix.Rotation(math.radians(inst['rotation_degrees']),4,'Z')@Matrix.Diagonal(Vector([*inst['scale'],1]))
 for o in cols[inst['asset']].objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();M=T@o.matrix_world;n=len(vertices)
  pts=[M@v.co for v in m.vertices];vertices+=pts;polygons += [tuple(n+i for i in p.vertices) for p in m.polygons]
  parts.append(dict(instance=inst['name'],asset=inst['asset'],part=o.name,min=[min(p[i] for p in pts) for i in range(3)],max=[max(p[i] for p in pts) for i in range(3)]))
  e.to_mesh_clear()
bvh=BVHTree.FromPolygons(vertices,polygons)
missing_floor=[];missing_roof=[];floor_samples=0;roof_samples=0
for zone in D['aircraft38']['bridge']['floor_polygons']:
 x0,x1,y0,y1=zone['rect'];x=x0+.12
 while x<x1-.1:
  y=y0+.12
  while y<y1-.1:
   # Do not mistake a wall-foot bevel for the central pedestrian surface.
   if in_polygon((x,y),zone['polygon']):
    hit=bvh.ray_cast(Vector((x,y,.35)),Vector((0,0,-1)),.70)
    floor_samples+=1
    if hit[0] is None:missing_floor.append([round(x,3),round(y,3),zone['name']])
    hit=bvh.ray_cast(Vector((x,y,1.65)),Vector((0,0,1)),1.45)
    roof_samples+=1
    if hit[0] is None:missing_roof.append([round(x,3),round(y,3),zone['name']])
   y+=.14
  x+=.14
plane_path=R.parent.parent/'SkywardAir/Revision18/Plane_Refined18.blend'
skin_ids={'SM_Plane_ExteriorAirframe','SM_Plane_CabinFinish09','SM_Plane_WindowWall_L','SM_Plane_WindowWall_R','SM_Plane_OuterWindowBarrel','SM_Plane_DoorBay07','SM_Plane_ForwardVestibule','SM_Plane_CockpitShell','SM_Plane_LandingGear'}
with bpy.data.libraries.load(str(plane_path),link=False) as (src,dst):dst.collections=list(skin_ids)
skin_cols={c.name:c for c in dst.collections if c}
for c in skin_cols.values():bpy.context.scene.collection.children.link(c)
bpy.context.view_layer.update();vv=[];ff=[]
PM=json.loads((plane_path.parent/'Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
for ins in PM['instances']:
 if ins['asset'] not in skin_cols or ins['location'][1]>4:continue
 T=Matrix.Translation(Vector(ins['location']))@Matrix.Rotation(ins['rotation'][2],4,'Z')
 for o in skin_cols[ins['asset']].objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();n=len(vv);vv += [T@o.matrix_world@v.co for v in m.vertices];ff += [tuple(n+i for i in p.vertices) for p in m.polygons];e.to_mesh_clear()
skin_bvh=BVHTree.FromPolygons(vv,ff)
seal=[]
for y in (-.465,1.815):
 for z in (.04,.5,1.,1.5,2.,2.16,2.4,2.54):
  h=skin_bvh.ray_cast(Vector((-5,y,z)),Vector((1,0,0)),10)
  seal.append(dict(y=y,z=z,skin_x=h[0].x+16 if h[0] else None,current_last_rib_x=13.839,gap_m=(h[0].x+16-13.839) if h[0] else None))
for y in (-.135,.675,1.485):
 h=skin_bvh.ray_cast(Vector((-5,y,2.54)),Vector((1,0,0)),10)
 seal.append(dict(y=y,z=2.54,skin_x=h[0].x+16 if h[0] else None,current_last_rib_x=13.839,gap_m=(h[0].x+16-13.839) if h[0] else None))
report=dict(source=str(path),collections=list(cols),evaluated_faces=len(polygons),floor_samples=floor_samples,roof_samples=roof_samples,missing_floor=missing_floor,missing_roof=missing_roof,parts=parts,dock_skin_contacts=seal)
(ROOT/'ActualAssemblyScrutiny38.json').write_text(json.dumps(report,indent=2))
print('ASSEMBLY38',floor_samples,'floor-misses',len(missing_floor),'roof-misses',len(missing_roof),flush=True)
print('FLOOR SAMPLE',missing_floor[:20]);print('ROOF SAMPLE',missing_roof[:20])
print('SEAL CONTACT',seal)
