"""Read-only saved-assembly inspection. Writes evidence only in this folder."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=R/'Airport_Repaired38.blend';bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False)
D=json.loads(bpy.context.scene['layout_json']);dg=bpy.context.evaluated_depsgraph_get()
records=[];vertices=[];faces=[];owners=[]
for q in D['instances']:
 col=bpy.data.collections.get(q['asset'])
 if not col:continue
 world=Matrix.Translation(Vector(q['location']))@Matrix.Rotation(math.radians(q.get('rotation_degrees',0)),4,'Z')@Matrix.Diagonal(Vector(list(q.get('scale',[1,1,1]))+[1]))
 for o in col.all_objects:
  if o.hide_render or o.type not in ['MESH','FONT']:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh()
  if not me or not me.vertices:continue
  me.calc_loop_triangles();wm=world@o.matrix_world;vv=[wm@v.co for v in me.vertices]
  lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
  rec=dict(actor=q['name'],asset=q['asset'],part=o.name,type=o.type,min=lo,max=hi,
           center=[(lo[i]+hi[i])/2 for i in range(3)],dimensions=[hi[i]-lo[i] for i in range(3)])
  if o.type=='FONT':rec['text']=o.data.body;rec['normal']=list((wm.to_3x3()@Vector([0,0,1])).normalized())
  offset=len(vertices);owner=len(records);vertices += vv
  for t in me.loop_triangles:faces.append(tuple(offset+i for i in t.vertices));owners.append(owner)
  records.append(rec);eo.to_mesh_clear()
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
def cast(point,direction,own,range_=1.2):
 pos=Vector(point);direction=Vector(direction);used=0
 for j in range(24):
  loc,norm,index,d=tree.ray_cast(pos,direction,range_-used)
  if index is None:return None
  used+=d
  if owners[index]!=own:
   hit=records[owners[index]]
   return dict(distance=used,point=list(loc),asset=hit['asset'],actor=hit['actor'],part=hit['part'])
  step=.001;pos=loc+direction*step;used+=step
 return dict(error='self traversal exhausted')
keywords=('art','panel','sign','backing','beam','mount','soffit','ceiling','fixture','header','graphic','shelf','board','clock','frame','lamp','light','fascia')
for index,r in enumerate(records):
 dims=r['dimensions'];axis=min(range(3),key=lambda i:dims[i]);name=r['part'].lower()
 if not any(k in name for k in keywords) or r['type']=='FONT':continue
 if dims[axis]>.25 or max(dims)<.25:continue
 r['contacts']={}
 for sign in [-1,1]:
  point=r['center'][:];point[axis]=r['max'][axis]+.001 if sign==1 else r['min'][axis]-.001
  direction=[0,0,0];direction[axis]=sign
  r['contacts']['xyz'[axis]+('+' if sign>0 else '-')]=cast(point,direction,index)
 r['floor_below']=cast([r['center'][0],r['center'][1],r['min'][2]-.001],[0,0,-1],index,8)
 r['ceiling_above']=cast([r['center'][0],r['center'][1],r['max'][2]+.001],[0,0,1],index,8)
out=dict(source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),parts=records,
         active_instances=len(D['instances']),rays='Actual evaluated meshes; center rays are evidence, not an exhaustive attachment proof')
(HERE/'AssemblyInventory38.json').write_text(json.dumps(out,indent=2))
print('READ-ONLY INVENTORY',len(records),'parts',len(faces),'triangles')
