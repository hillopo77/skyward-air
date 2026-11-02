"""Exact raw FBX non-normal payload comparison; no editor/DCC launch."""
from pathlib import Path
import array,hashlib,json
from read_fbx39 import read,meshes
F=Path(__file__).parent;R=F.parents[2];IDS=('SM_AP_W40PressureWindows','SM_AP_W40CargoBayWindows')
def canonical(n):
    if n['name']=='LayerElementNormal':return None
    def prop(p):
        if isinstance(p,array.array):return dict(typecode=p.typecode,length=len(p),sha256=hashlib.sha256(p.tobytes()).hexdigest())
        if isinstance(p,bytes):return dict(bytes_sha256=hashlib.sha256(p).hexdigest(),length=len(p))
        return p
    return dict(name=n['name'],props=[prop(p) for p in n['props']],children=[v for c in n['children'] if (v:=canonical(c)) is not None])
def fingerprint(path):
    m=next(meshes(path));node=m['node'];payload=[v for child in node['children'] if (v:=canonical(child)) is not None]
    raw_arrays=[]
    def walk(n):
        if n['name']=='LayerElementNormal':return
        for i,p in enumerate(n['props']):
            if isinstance(p,array.array):raw_arrays.append(dict(path=n['name'],index=i,typecode=p.typecode,length=len(p),sha256=hashlib.sha256(p.tobytes()).hexdigest()))
        for c in n['children']:walk(c)
    walk(node)
    nodes=read(path);objects=next(n for n in nodes if n['name']=='Objects');materials=[];models=[]
    for n in objects['children']:
        if n['name'] in ('Material','Model'):
            data=dict(kind=n['name'],name=n['props'][1],type=n['props'][-1],children=[canonical(c) for c in n['children']]);(materials if n['name']=='Material' else models).append(data)
    digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(non_normal_geometry_payload_sha256=digest(payload),raw_non_normal_arrays=raw_arrays,material_payload_sha256=digest(materials),model_transform_payload_sha256=digest(models),vertices=len(m['vertices']),polygons=len(m['faces']))
report=dict(passed=True,scope='Exact raw FBX geometry/topology/UV/material-index/smoothing arrays and material/model payloads; only LayerElementNormal excluded. Volatile document/header/UID metadata is not part of the mesh payload.',assets=[])
for aid in IDS:
    before=fingerprint(R/'SourceAssets/RecoveryBefore44/FBX'/(aid+'.fbx'));after=fingerprint(F/'PressureNormals44_Exports/Exports/FBX'/(aid+'.fbx'));same=before==after;report['passed']&=same;report['assets'].append(dict(asset=aid,identical_non_normal_payload=same,before=before,after=after))
(F/'PressureNormals44_RawFBXVerification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=report['passed'],assets=[dict(asset=q['asset'],identical_non_normal_payload=q['identical_non_normal_payload']) for q in report['assets']]),indent=2))
