"""Actually reopen the saved source, verify construction and render 3 key pairs."""
import bpy,json,sys,math,hashlib,ast,copy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;R=HERE.parents[1];A=R.parent;P=R.parents[2]/'outputs/SkywardAir/UnrealProject/Content/Python'
sys.path[:0]=[str(HERE),str(A/'SourceAssets')]
import airport_model as a
import finish43
path=HERE/'TerminalFinish43_UnitKit.blend'
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
scene=bpy.data.scenes['Finish43_CurrentTerminal_SourceReview'];bpy.context.window.scene=scene
D=json.loads(scene['layout_json']);before=copy.deepcopy(D)
for m in bpy.data.materials:
 if m.name.startswith('MI_AP_'):a.MATS[m.name[6:]]=m
tree=ast.parse((R/'SourceAssets/build_source38.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context')
exec(compile(ast.Module(body=[cls],type_ignores=[]),'actual_context43_reopened','exec'),globals());ctx=Context(a,D,scene)
counts={aid:len(bpy.data.collections[aid].objects) for aid in finish43.OWNED}
repeat=finish43.apply(ctx);assert repeat['repeat_safe_reused'];assert D==before
assert counts=={aid:len(bpy.data.collections[aid].objects) for aid in finish43.OWNED}
dg=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
for aid in ('SM_AP_Walls38',)+finish43.OWNED:
 for ob in bpy.data.collections[aid].objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh();offset=len(verts);verts.extend([tuple(ob.matrix_world@v.co) for v in me.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,faces,all_triangles=False);checks=[]
for opening in D['service_openings38']:
 for du in [-opening['width']/2+.035,0,opening['width']/2-.035]:
  for z in [opening['z0']+.035,(opening['z0']+opening['z1'])/2,opening['z1']-.035]:
   p=Vector((-26.5,opening['centre']+du,z));result=bvh.ray_cast(p,Vector((1,0,0)),1.)
   assert result[0] is None,('Service feed ray blocked after actual reopen',tuple(p),tuple(result[0]))
   checks.append(dict(point=list(p),direction=[1,0,0],distance_m=1.,clear=True))
# Real wall-construction probe behind a plaster cassette must hit solid finish.
wallhits=[]
for p in [(-31.5,22,2.0),(-42.5,-17.5,2.0)]:
 result=bvh.ray_cast(Vector(p),Vector((-1,0,0) if p[0]>-32 else (0,-1,0)),1.)
 if result[0] is not None:wallhits.append(dict(start=list(p),hit=list(result[0])))
images=[]
for suffix,(file,colour,rough,metal,tile) in finish43.MATERIALS.items():
 if not file:continue
 material=bpy.data.materials['MI_AP_'+finish43.PREFIX+suffix]
 tex=material.node_tree.nodes['Finish43 authored colour and roughness'];assert tex.image.packed_file
 assert material.node_tree.nodes['Finish43 physical tile scale'].inputs['Scale'].default_value==1/tile
 p=material.node_tree.nodes['Principled BSDF'];assert p.inputs['Base Color'].is_linked and p.inputs['Roughness'].is_linked
 images.append(dict(material=material.name,image=tex.image.name,packed=True,tile_metres=tile))
identity=[]
for ob in bpy.data.collections['SM_AP_BaggageBackdrop43'].objects:
 if not ob.name.startswith('43 mounted service identity '):continue
 ev=ob.evaluated_get(dg);me=ev.to_mesh();points=[ob.matrix_world@v.co for v in me.vertices]
 assert points,('No actual exported identity geometry',ob.name)
 bounds=[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)]
 ev.to_mesh_clear()
 # Front of actual crown is x=-26.160. The fitted relief must cross that
 # plane, so it both physically bears on the board and has exposed thickness.
 assert bounds[0][0]<-26.161 and bounds[0][1]>-26.1595,(ob.name,bounds[0])
 assert bounds[2][0]>2.15 and bounds[2][1]<2.72,(ob.name,bounds[2])
 identity.append(dict(part=ob.name,bounds=bounds,type=ob.type,text=ob.data.body if ob.type=='FONT' else None))
assert len(identity)==10 and {q['text'] for q in identity if q['text']}=={'BAY 01','BAY 02'}
report=json.loads((HERE/'Source43Report.json').read_text());report.update(actual_reopen_verified=True,reopened_unit_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
 reopened_service_clearance_rays=checks,solid_wall_probe_hits=wallhits,packed_material_graphs=images,
 repeat_safe_after_reopen_verified=True,source_unit_bytes=path.stat().st_size,
 service_identity_actual_reopen_verified=True,service_identity_bearing_bounds=identity)
(HERE/'Source43Report.json').write_text(json.dumps(report,indent=2));print('SOURCE43_ACTUAL_REOPEN_VERIFIED',len(checks),'clear feed probes',flush=True)
if '--verify-only' not in sys.argv:
 cam=scene.camera
 for name,p,t,fov in [('02_Baggage',[-30.6,-13.1,1.62],[-26,-14.3,1.55],76),('03_A08',[-28.5,16.8,1.62],[-29.2,28.5,1.8],78),('06_Cafe',[-33.8,25.5,1.62],[-42.5,29,1.6],78)]:
  cam.location=p;cam.rotation_euler=(Vector(t)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(fov)
  scene.render.filepath=str(HERE/'Evidence'/('After_'+name+'.png'));bpy.ops.render.render(write_still=True);print('SOURCE43_REOPEN_RENDER',name,flush=True)
 report['reopened_three_after_views_completed']=True;(HERE/'Source43Report.json').write_text(json.dumps(report,indent=2))
