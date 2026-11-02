"""Compare exact exported neutral actuators to original source vertex positions."""
import json, math
from pathlib import Path
import numpy as np
from read_fbx39 import meshes

F=Path(__file__).parent;R=F.parents[2];W=F.parents[5]

def run():
    old=next(meshes(W/'outputs/SkywardAir/Revision18/Exports/FBX/SM_Plane_ExteriorAirframe.fbx'))
    # Quantised neighbour buckets retain sub0.1mm source equality while avoiding
    # an editor or a third-party mesh import to inspect the already-exported kit.
    quantum=.0001;buckets={}
    for p in old['vertices']:
        k=tuple(round(v/quantum) for v in p);buckets.setdefault(k,[]).append(p)
    d=json.loads((R/'Exports/airport_layout.json').read_text());records=d['flight39']['surface_records'];report=dict(scope='Read-only exact source/actuator FBX comparison',actuators=[],mirror_hinges=[])
    for q in records:
        m=next(meshes(R/'Exports/FBX'/(q['asset']+'.fbx')));points=np.array(m['vertices'])+np.array(q['pivot'])-np.array([16,0,0]);unmatched=[];errors=[]
        for p in points:
            key=tuple(round(float(v)/quantum) for v in p);candidates=[]
            for x in range(-1,2):
                for y in range(-1,2):
                    for z in range(-1,2):candidates.extend(buckets.get((key[0]+x,key[1]+y,key[2]+z),[]))
            best=min((math.dist(p,v) for v in candidates),default=math.inf)
            if best>.0001:unmatched.append(p.tolist())
            else:errors.append(best)
        row=dict(actor=q['actor'],vertices=len(points),unmatched_source_vertices=len(unmatched),max_neutral_reconstruction_error_m=max(errors,default=None),unmatched_examples=unmatched[:6])
        if q['role']=='flap':
            ends=sorted([float(points[:,0].min()),float(points[:,0].max())],key=abs);hinge=[]
            for xx in ends:
                cap=points[abs(points[:,0]-xx)<.0002];yy=cap[:,1].min();near=cap[abs(cap[:,1]-yy)<.0002]
                hinge.append(near.mean(axis=0))
            axis=hinge[1]-hinge[0];axis/=np.linalg.norm(axis)
            row['unique_geometric_hinge']=dict(pivot=(hinge[0]+[16,0,0]).tolist(),axis=axis.tolist())
        report['actuators'].append(row)
    # Only report actual hinge asymmetry; a lower-skin gear aperture can cause
    # asymmetrical vertex multiplicity in a naive leading-edge average.
    left=[q for q in records if q['side']==-1 and q['role']!='rudder'];right=[q for q in records if q['side']==1]
    for a,b in zip(left,right):
        pa=a['pivot'];pb=b['pivot'];ax=a['axis'];bx=b['axis'];expected=[32-pa[0],pa[1],pa[2]]
        mirrored_axis=[-ax[0],ax[1],ax[2]];dot=sum(x*y for x,y in zip(mirrored_axis,bx))
        report['mirror_hinges'].append(dict(left=a['actor'],right=b['actor'],mirrored_pivot_error_m=math.dist(expected,pb),mirrored_axis_error_deg=math.degrees(math.acos(max(-1,min(1,dot)))),left_pivot=pa,right_pivot=pb))
    (F/'TaxiActuatorComparison39.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':run()
