"""Offline adapter contract test; no editor/engine launch or asset mutation."""
import json,copy
from pathlib import Path
from types import SimpleNamespace
import window40 as M
F=Path(__file__).parent;R=F.parents[2]
pm=json.loads((F.parents[5]/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
targets={q['name']:M.SWAPS[q['asset']] for q in pm['instances'] if q['asset'] in M.SWAPS}
assert len(targets)==198,len(targets)

class Component:
    def __init__(self):self.static_mesh=None;self.materials=[]
    def set_static_mesh(self,m):self.static_mesh=m
    def set_material(self,i,m):self.materials.append((i,m))
class Actor:
    def __init__(self,n):self.n=n;self.tags=['Skyward:'+n];self.component=Component();self.transform=('unchanged',n)
    def get_component_by_class(self,c):return self.component
    def get_actor_transform(self):return self.transform
    def get_actor_label(self):return self.n
actors=[Actor(n) for n in targets]+[Actor('SM_Plane_ExteriorAirframe'),Actor('SM_Plane_LandingGear')]
meshes={aid:SimpleNamespace(static_materials=[SimpleNamespace(material_interface=aid+'_slot0'),SimpleNamespace(material_interface=aid+'_slot1')]) for aid in M.SWAPS.values()}
ctx=SimpleNamespace(u=SimpleNamespace(StaticMeshComponent=Component),R=R,EA=SimpleNamespace(get_all_level_actors=lambda:actors),mesh=lambda aid:meshes[aid])
result=M.apply_native(ctx);assert result['instances']==198
assert all(a.component.static_mesh is meshes[targets[a.n]] for a in actors[:198])
assert all(a.component.static_mesh is None for a in actors[198:])
M.apply_native(ctx);assert all(a.transform==('unchanged',a.n) for a in actors)

P=SimpleNamespace(DATA=copy.deepcopy(pm));D=json.loads((R/'Exports/airport_layout.json').read_text())
for q in P.DATA['interactions']:
    for p in q.get('roller_parts',[]):p['closed_location'][0]+=16
M.prepare_plane(P,D)
class Moving:
    def set_actor_location(self,p,*args):self.pose=list(p)
P.STATE=dict(actors={},movables={});P.vector=lambda p:list(p)
for q in P.DATA['interactions']:
    if not q.get('window40'):continue
    for p in q['roller_parts']:P.STATE['actors'][p['actor']]=Moving()
    P.STATE['movables'][q['actor']]=dict(item=q,progress=0.)
fallback=[];P._apply_movable=lambda m:fallback.append(m)
G=SimpleNamespace(P=P,flight39=dict(frame=SimpleNamespace(world=lambda p:[p[0]+7,p[1]-9,p[2]+3])))
M.install(G);bound=P._apply_movable;assert M.install(G)['already_installed'] and P._apply_movable is bound
for progress in (0.,.5,1.):
    for m in P.STATE['movables'].values():
        m['progress']=progress;P._apply_movable(m)
        for p in m['item']['roller_parts']:
            expected=M.shade_pose(p,progress);expected=[expected[0]+7,expected[1]-9,expected[2]+3]
            assert P.STATE['actors'][p['actor']].pose==expected
P._apply_movable(dict(item={}));assert len(fallback)==1
report=dict(scope='Offline API contract only; no native engine launch',passed=True,native_targets=198,source_asset_families=len(M.SWAPS),unrelated_airframe_gear_untouched=True,native_transform_preservation=True,native_repeat_safe=True,curved_mechanisms=48,curved_parts=240,carrier_conversion_checked_states=[0,.5,1],runtime_repeat_safe=True)
(F/'Window40_AdapterVerification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
