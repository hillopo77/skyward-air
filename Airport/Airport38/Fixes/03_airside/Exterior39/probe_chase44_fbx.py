"""Read-only ray ownership at actual native window-top pixels."""
from pathlib import Path
import json,math,sys
import numpy as np
from read_fbx39 import meshes
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5];K=json.loads((R/'Exports/airport_assets.json').read_text());pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
maps={'SM_Plane_WindowWall_L':'SM_AP_W42WindowWallL','SM_Plane_WindowShadeFrame18_L':'SM_AP_W42ShadeFrameL','SM_Plane_Rack_L':'SM_AP_W41RackL','SM_Plane_OuterWindowBarrel':'SM_AP_W40PressureWindows'}
cache={};triangles=[];owners=[]
for q in pm['instances']:
    aid=maps.get(q['asset'])
    if not aid or not 11<q['location'][1]<18:continue
    if aid not in cache:
        spec=next(a for a in K['assets'] if a['id']==aid);m=next(meshes(R/'Exports/FBX'/(aid+'.fbx')));cache[aid]=(spec,m)
    spec,m=cache[aid];pos=np.array(q['location'])+np.array([16,0,0]);vs=np.array(m['vertices'])
    for i,face in enumerate(m['faces']):
        mi=m['materials'][i if len(m['materials'])>1 else 0];mat=spec['materials'][mi]
        if 'Glass' in mat:continue
        for j in range(1,len(face)-1):triangles.append(vs[[face[0],face[j],face[j+1]]]+pos);owners.append(dict(actor=q['name'],asset=aid,material=mat))
tri=np.array(triangles);a=tri[:,0];e1=tri[:,1]-a;e2=tri[:,2]-a
def ray(eye,target,pixel):
    eye=np.array(eye);forward=np.array(target)-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward);x=(pixel[0]/1920-.5)*2*math.tan(math.radians(78)/2);y=(.5-pixel[1]/1080)*2*math.tan(math.radians(78)/2)/(1920/1080);d=forward+right*x+up*y;d/=np.linalg.norm(d)
    p=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,p);inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-10);s=eye-a;u=np.einsum('ij,ij->i',s,p)*inv;tq=np.cross(s,e1);v=np.einsum('j,ij->i',d,tq)*inv;t=np.einsum('ij,ij->i',e2,tq)*inv;ok=(abs(det)>1e-10)&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>.001)&(t<5);indices=np.nonzero(ok)[0];order=indices[np.argsort(t[indices])][:5];hits=[]
    for i in order:
        n=np.cross(e1[i],e2[i]);n/=np.linalg.norm(n);hits.append(dict(**owners[i],distance=float(t[i]),point=(eye+d*t[i]).tolist(),face_ray_dot=float(n.dot(d))))
    return dict(pixel=pixel,hits=hits)
report=dict(scope='Exact current native camera78deg rays through exported opaque meshes; read-only, noDCC/editor',views={})
for name,eye,target,pixels in [('85',[14.65,14.15,1.55],[13.72,14.33,1.9],[(1285,365),(1278,360),(1300,374),(1780,406),(1770,420),(1800,435)]),('84',[15,14.55,1.22],[13.73,14.62,1.84],[(1370,350),(1385,380),(1410,370),(920,360)])]:report['views'][name]=[ray(eye,target,p) for p in pixels]
(F/'Chase44_RayDiagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
