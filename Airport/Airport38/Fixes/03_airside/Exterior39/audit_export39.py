"""Inspect exact already-exported airplane geometry without either editor."""
from pathlib import Path
from collections import defaultdict,Counter
import json,math
from read_fbx39 import meshes,read,child

F=Path(__file__).parent;R=F.parents[2];E=R/'Exports';REPORT=F/'TaxiGeometryDiagnosis39.json'

def bounds(p):return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def normal(points):
    n=cross(sub(points[1],points[0]),sub(points[2],points[0]));ll=math.sqrt(sum(x*x for x in n))
    return tuple(x/ll for x in n) if ll else (0,0,0)

def components(mesh):
    parent=list(range(len(mesh['vertices'])))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for face in mesh['faces']:
        a=root(face[0])
        for j in face[1:]:parent[root(j)]=a
    groups=defaultdict(list)
    for i in range(len(parent)):groups[root(i)].append(i)
    return [dict(vertices=len(ii),bounds=bounds([mesh['vertices'][i] for i in ii]),ids=ii) for ii in groups.values()]

def run():
    assets=json.loads((E/'airport_assets.json').read_text());asset=next(q for q in assets['assets'] if q['id']=='SM_AP_F39AirframeFixed')
    m=next(meshes(E/'FBX/SM_AP_F39AirframeFixed.fbx'));mats=m['materials'];report=dict(scope='Read exact exported FBX; no Blender or Unreal launch or mutation',airframe=dict(vertices=len(m['vertices']),faces=len(m['faces']),bounds=bounds(m['vertices'])),materials=[])
    for i,name in enumerate(asset['materials']):
        fs=[face for j,face in enumerate(m['faces']) if mats[j if len(mats)>1 else 0]==i]
        if not fs:continue
        pts=[m['vertices'][k] for face in fs for k in face];normals=[normal([m['vertices'][k] for k in face]) for face in fs]
        report['materials'].append(dict(slot=i,name=name,faces=len(fs),bounds=bounds(pts),up_faces=sum(n[2]>.5 for n in normals),down_faces=sum(n[2]<-.5 for n in normals),manifest=assets['materials'].get(name)))
    cc=components(m);report['airframe']['connected_components']=len(cc)
    roof=[q for q in cc if q['bounds'][0][2]>2.84 and max(abs(q['bounds'][0][0]),abs(q['bounds'][1][0]))<2.5]
    report['roof_components']=[{k:v for k,v in q.items() if k!='ids'} for q in roof]
    report['wing_silhouette_components']=[{k:v for k,v in q.items() if k!='ids'} for q in cc if max(abs(q['bounds'][0][0]),abs(q['bounds'][1][0]))>3 and q['bounds'][0][2]>-.9 and q['bounds'][1][1]<27]
    coating=next(q for q in report['materials'] if 'Corroguard' in q['name'])
    normal_node=child(m['node'],'LayerElementNormal');normals=child(normal_node,'Normals')['props'][0];normal_indices=child(normal_node,'NormalsIndex')['props'][0];offset=0;values=[]
    for i,face in enumerate(m['faces']):
        if mats[i]==coating['slot']:values.extend(normals[normal_indices[offset+j]*3+2] for j in range(len(face)))
        offset+=len(face)
    coating['exported_loop_normal_z']=dict(min=min(values),max=max(values),down=sum(v<0 for v in values),count=len(values))
    report['findings']=[dict(issue='Broad dark wing panels',attribution='Conformal upper-wing protective coating15, material '+coating['name'],source_colour=coating['manifest']['color'],normals_up=coating['up_faces'],normals_down=coating['down_faces'],native_material_override_requires_check=True)]
    report['surfaces']=[]
    layout=json.loads((E/'airport_layout.json').read_text())
    for q in layout['flight39']['surface_records']:
        a=next(meshes(E/'FBX'/(q['asset']+'.fbx')));lo,hi=bounds(a['vertices']);world=[[v[i]+q['pivot'][i]-(16 if i==0 else 0) for i in range(3)] for v in a['vertices']]
        report['surfaces'].append(dict(actor=q['actor'],asset=q['asset'],role=q['role'],pivot=q['pivot'],axis=q['axis'],closed_source_bounds=bounds(world),local_bounds=[lo,hi]))
    REPORT.write_text(json.dumps(report,indent=2));print(json.dumps(dict(report=str(REPORT),materials=[dict(name=q['name'],up=q['up_faces'],down=q['down_faces']) for q in report['materials']],roof_components=report['roof_components']),indent=2))
    return report

if __name__=='__main__':run()
