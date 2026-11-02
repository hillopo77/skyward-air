"""Read-only exported-geometry/normal diagnosis; no DCC/editor launch."""
from pathlib import Path
from math import sqrt,acos,degrees
import json
from read_fbx39 import meshes,child
F=Path(__file__).parent;R=F.parents[2];K=json.loads((R/'Exports/airport_assets.json').read_text());report=dict(scope='Read-only exact exported FBX arrays; no editor/DCC/source mutation',assets=[])
def normal(p):
    x,y,z=p;v=[(1 if x>=0 else -1)*(abs(x)/2.5)**2.6/2.5,0,(1 if z>=.55 else -1)*(abs((z-.55)/2.35))**2.6/2.35];l=sqrt(sum(a*a for a in v));return [a/l for a in v]
for aid in ('SM_AP_W40PressureWindows','SM_AP_W40CargoBayWindows'):
    spec=next(q for q in K['assets'] if q['id']==aid);m=next(meshes(R/'Exports/FBX'/(aid+'.fbx')));layer=child(m['node'],'LayerElementNormal');values=child(layer,'Normals')['props'][0];indices=child(layer,'NormalsIndex')['props'][0];offset=0;angles=[];ny=[];examples=[];polys=0
    for i,face in enumerate(m['faces']):
        slot=m['materials'][i if len(m['materials'])>1 else 0];name=spec['materials'][slot];pp=[m['vertices'][j] for j in face]
        selected='Paint09' in name and all(p[2]>1.96 and abs(p[0])>1.5 for p in pp)
        if selected:
            polys+=1
            for k,p in enumerate(pp):
                v=values[indices[offset+k]*3:indices[offset+k]*3+3];a=normal(p);angle=degrees(acos(max(-1,min(1,sum(q*r for q,r in zip(v,a))))));angles.append(angle);ny.append(abs(v[1]))
                if abs(v[1])>.02 or angle>10:examples.append(dict(position=p,exported_normal=list(v),analytic_extruded_body_normal=a,angle_degrees=angle))
        offset+=len(face)
    angles.sort();ny.sort();report['assets'].append(dict(asset=aid,shoulder_faces=polys,shoulder_corners=len(angles),normal_angle_max=max(angles),normal_angle_p95=angles[int(len(angles)*.95)],normal_y_max=max(ny),normal_y_p95=ny[int(len(ny)*.95)],corners_over10deg=sum(a>10 for a in angles),examples=sorted(examples,key=lambda r:-r['angle_degrees'])[:8]))
(F/'Shoulder44_FBXDiagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in row.items() if k!='examples'} for row in report['assets']],indent=2))
