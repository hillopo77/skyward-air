"""Read candidate posture and existing restraint geometry in a private process."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;W=F.parents[5];C=W/'outputs/Characters/Revision39'
with bpy.data.libraries.load(str(C/'Characters39_PostureCandidate.blend'),link=False) as (src,dst):
    print('BUSINESS_CANDIDATE_COLLECTIONS',[n for n in src.collections if 'Luxury' in n],flush=True)
    dst.collections=[n for n in src.collections if n in {'CHAR39_PassengerCrew_LuxurySeated','CHAR39_PassengerHoodie_LuxurySeated','SM_Plane_LuxurySeat_Ergonomic39'}]
cols={c.name:c for c in dst.collections if c}
if 'SM_Plane_LuxurySeat_Ergonomic39' not in cols:
    with bpy.data.libraries.load(str(W/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=['SM_Plane_LuxurySeat']
    sys.path.insert(0,str(C));import luxury_fit39
    col,meta=luxury_fit39.corrected_collection(dst.collections[0]);cols[col.name]=col
for c in cols.values():bpy.context.scene.collection.children.link(c)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def data(col,filter_fn=lambda ob:True):
    pts=[];faces=[];parts=[]
    for ob in col.objects:
        if ob.type!='MESH' or not filter_fn(ob):continue
        ev=ob.evaluated_get(dg);me=ev.to_mesh();T=ob.matrix_world;offset=len(pts);vv=[T@v.co for v in me.vertices];pts+=vv;faces.extend(tuple(offset+i for i in f.vertices) for f in me.polygons)
        parts.append(dict(name=ob.name,vertices=len(vv),bounds=[[min(p[i] for p in vv) for i in range(3)],[max(p[i] for p in vv) for i in range(3)]],materials=[m.name if m else None for m in me.materials]));ev.to_mesh_clear()
    return BVHTree.FromPolygons(pts,faces),parts
report=dict(candidate=str(C/'Characters39_PostureCandidate.blend'),postures={},chair_parts=[])
for n,c in cols.items():
    tree,parts=data(c)
    if n.startswith('CHAR39'):
        rays=[]
        for x in (-.25,-.2,-.15,-.1,0,.1,.15,.2,.25):
            for z in (.60,.64,.66,.68,.70):
                hit=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)[0];rays.append(dict(x=x,z=z,front_y=hit.y if hit else None))
        report['postures'][n]=dict(parts=parts,front_lap=rays)
    else:
        report['chair_parts']=parts;report['chair_collection']=n
        rays=[]
        for x,y,z in [(-.325,.15,1),(.325,.15,1),(-.31,-.15,1),(.31,-.15,1),(0,-.2,1)]:
            hit=tree.ray_cast(Vector((x,y,z)),Vector((0,0,-1)),1)[0];rays.append(dict(x=x,y=y,top_z=hit.z if hit else None))
        report['chair_ray_contacts']=rays
(F/'BusinessBelt40_SourceDiagnosis.json').write_text(json.dumps(report,indent=2));print('BUSINESS_BELT_DIAGNOSIS',report['chair_collection'],len(report['chair_parts']),report['chair_ray_contacts'],flush=True)
for n,p in report['postures'].items():print(n,[q for q in p['front_lap'] if q['x']==0],flush=True)
