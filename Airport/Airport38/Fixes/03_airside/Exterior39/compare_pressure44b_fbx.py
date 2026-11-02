"""Raw source geometry/material equality plus original crown-normal equality."""
from pathlib import Path
import array,hashlib,json
from read_fbx39 import read,meshes,child
F=Path(__file__).parent;R=F.parents[2]
namespace={'__file__':str(F/'compare_pressure44_fbx.py')}
exec(compile((F/'compare_pressure44_fbx.py').read_text().split('report=dict(passed=True')[0],'raw_fingerprint44_helpers','exec'),namespace)
fingerprint=namespace['fingerprint'];report=dict(passed=True,scope='Raw FBX arrays/material/model payloads exact; only normal layer excluded; crown normals compared per polygon corner',assets=[])
def split_normals(path):
    m=next(meshes(path));layer=child(m['node'],'LayerElementNormal');vals=child(layer,'Normals')['props'][0];indices=child(layer,'NormalsIndex')['props'][0];offset=0;crown=[];other=[]
    for face in m['faces']:
        pp=[m['vertices'][i] for i in face];target=crown if all(p[2]>=2.79999 and abs(p[0])<1.462 for p in pp) and any(p[2]>2.80001 for p in pp) else other
        for k in range(len(face)):target.extend(vals[indices[offset+k]*3:indices[offset+k]*3+3])
        offset+=len(face)
    return crown,other
for aid in ('SM_AP_W40PressureWindows','SM_AP_W40CargoBayWindows'):
    before=R/'SourceAssets/RecoveryBefore44/FBX'/(aid+'.fbx');wrong=R/'Exports/FBX'/(aid+'.fbx');after=F/'PressureNormals44B_Exports/Exports/FBX'/(aid+'.fbx')
    b=fingerprint(before);a=fingerprint(after);cn,other=split_normals(after);oldcn,_=split_normals(before);_,prior=split_normals(wrong)
    row=dict(asset=aid,identical_all_non_normal_payload=b==a,before=b,after=a,crown_corners=len(cn)//3,crown_normals_exactly_original=cn==oldcn,side_and_all_other_normals_exactly_prior44=other==prior,crown_normal_max_original_abs_error=max(abs(x-y) for x,y in zip(cn,oldcn)))
    report['assets'].append(row);report['passed']&=b==a and len(cn)==384*3 and cn==oldcn and other==prior
(F/'PressureNormals44B_RawFBXVerification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(passed=report['passed'],assets=[{k:v for k,v in r.items() if k not in ('before','after')} for r in report['assets']]),indent=2))
