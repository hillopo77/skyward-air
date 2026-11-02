"""Read-only exact source FBX contact probe for cabin parts crossing the crown."""
from pathlib import Path
import json, math
import numpy as np
from read_fbx39 import meshes

F=Path(__file__).parent;W=F.parents[5];E=W/'outputs/SkywardAir/Revision18/Exports'

def rotate(points,r):
    x,y,z=r;cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return points@(rz@ry@rx).T

def run():
    d=json.loads((E/'manifest.json').read_text());instances=d['scenes']['L_Plane_Reference']['instances'];cache={};rows=[]
    excluded=('ExteriorAirframe','OuterWindowBarrel','DoorBay07','CargoBay10','CargoHold','LandingGear','WindowShade','PassengerDoor','Case','Cart','Cargo15','Cargo13')
    selected=[q for q in instances if not any(t in q['asset'] for t in excluded)]
    for q in selected:
        aid=q['asset']
        if aid not in cache:
            path=E/'FBX'/(aid+'.fbx')
            cache[aid]=np.concatenate([np.array(a['vertices']) for a in meshes(path)]) if path.exists() else np.empty((0,3))
        points=rotate(cache[aid]*q['scale'],q['rotation'])+q['location']
        if not len(points):continue
        # Only crown/upper shoulder in the straight pressure cabin. The lower
        # portion has deliberate floor/wing/keel penetrations and is irrelevant.
        p=points[(points[:,1]>=0)&(points[:,1]<=34.425)&(points[:,2]>2.65)]
        if not len(p):continue
        amount=(np.abs(p[:,0])/2.5)**3.6+(np.abs((p[:,2]-.55)/2.35))**3.6-1
        beyond=p[amount>.0005]
        if len(beyond):rows.append(dict(actor=q['name'],asset=aid,vertices_outside=len(beyond),top=float(beyond[:,2].max()),min=beyond.min(axis=0).tolist(),max=beyond.max(axis=0).tolist(),max_implicit_outside=float(amount.max())))
    report=dict(scope='Read-only original Revision18 source FBX upper pressure-shell contact probe',assets_read=len(cache),instances_checked=len(selected),candidates=rows)
    (F/'TaxiRoofDiagnosis39.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':run()
