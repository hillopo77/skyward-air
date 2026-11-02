"""Read-only part ownership for native window service-chase edge pixels."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5]
sys.path.insert(0,str(F));import window40 as W
ids=['SM_AP_W42ShadeFrameL','SM_AP_W42WindowWallL']
with bpy.data.libraries.load(str(R/'Airport_Repaired38.blend'),link=False) as (src,dst):dst.collections=ids
cols=dict(zip(ids,dst.collections))
for c in cols.values():bpy.context.scene.collection.children.link(c)
pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
maps={'SM_Plane_WindowWall_L':ids[1],'SM_Plane_WindowShadeFrame18_L':ids[0]};surfaces=[];dg=bpy.context.evaluated_depsgraph_get()
for q in pm['instances']:
    aid=maps.get(q['asset'])
    if not aid or not 11<q['location'][1]<18:continue
    Tq=Matrix.Translation(Vector(q['location'])+Vector((16,0,0)))
    for o in cols[aid].objects:
        if o.type!='MESH':continue
        ev=o.evaluated_get(dg);me=ev.to_mesh();T=Tq@W._matrix(o)
        v=[T@x.co for x in me.vertices];faces=[list(p.vertices) for p in me.polygons]
        surfaces.append((q['name'],o.name,BVHTree.FromPolygons(v,faces,all_triangles=False)))
        ev.to_mesh_clear()
def ray(eye,target,pixel):
    eye=Vector(eye);forward=(Vector(target)-eye).normalized();right=forward.cross(Vector((0,0,1))).normalized();up=right.cross(forward)
    x=(pixel[0]/1920-.5)*2*math.tan(math.radians(78)/2);y=(.5-pixel[1]/1080)*2*math.tan(math.radians(78)/2)/(1920/1080);d=(forward+right*x+up*y).normalized();hits=[]
    for actor,part,bvh in surfaces:
        p,n,i,t=bvh.ray_cast(eye,d,5.)
        if p is not None:hits.append(dict(actor=actor,part=part,point=list(p),distance=t,face_ray_dot=n.dot(d)))
    return dict(pixel=pixel,hits=sorted(hits,key=lambda h:h['distance'])[:4])
r={}
for name,eye,target,pixels in [('85',[14.65,14.15,1.55],[13.72,14.33,1.9],[(1285,365),(1278,360),(1300,374),(1780,406),(1770,420),(1800,435)]),('84',[15,14.55,1.22],[13.73,14.62,1.84],[(1370,350),(1385,380),(1410,370),(920,360)])]:r[name]=[ray(eye,target,p) for p in pixels]
(F/'Chase44_SourceDiagnosis.json').write_text(json.dumps(r,indent=2))
for name,rows in r.items():
    for row in rows:print(name,row['pixel'],[(h['part'],[round(v,5) for v in h['point']],round(h['face_ray_dot'],4)) for h in row['hits'][:2]])
