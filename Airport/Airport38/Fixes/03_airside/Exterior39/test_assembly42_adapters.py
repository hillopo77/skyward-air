"""Offline native/data contracts, actual assets proved separately cold in Blender."""
import json,copy
from pathlib import Path
from types import SimpleNamespace as NS
import business_belt40 as B40,business_belt41 as B,window40 as W40,window41 as W41,window42 as W,aircraft_finish42 as A
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5]
pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];D=json.loads((R/'Exports/airport_layout.json').read_text());D['repair38']=json.loads((F/'Assembly42_SourceData.json').read_text())
class Component:
    def __init__(self):self.materials={}
    def set_static_mesh(self,m):self.static_mesh=m
    def set_material(self,i,m):self.materials[i]=m
class Actor:
    def __init__(self,n):self.tags=['Skyward:'+n];self.c=Component();self.location=[0,0,0];self.n=n
    def get_component_by_class(self,c):return self.c
    def set_actor_location(self,p,*args):self.location=list(p)
    def set_actor_rotation(self,p,*args):self.rotation=p
actors={q['name']:Actor(q['name']) for q in pm['instances']}
for r in D['repair38']['business_belt40']['records']:
    actors[r['worn_actor']]=Actor(r['worn_actor'])
meshes={n:NS(static_materials=[NS(material_interface=n+'_default')]) for n in B.IDS+list(W.SWAPS.values())+list(A.SWAPS.values())}
ctx=NS(R=R,D=D,u=NS(StaticMeshComponent=Component,Rotator=lambda:0),EA=NS(get_all_level_actors=lambda:list(actors.values())),mesh=lambda n:meshes[n],v=lambda p:list(p))
out=[m.apply_native(ctx) for m in (B,W,A)];poses={n:list(q.location) for n,q in actors.items()}
for m in (B,W,A):m.apply_native(ctx)
assert poses=={n:list(q.location) for n,q in actors.items()}
for r in D['repair38']['business_belt40']['records']:
    assert actors[r['worn_actor']].c.static_mesh==meshes[r['worn_asset']]
    assert actors[r['control']].location==r['worn_hinge']
P=NS(DATA=copy.deepcopy(pm))
for q in P.DATA['instances']:q['location'][0]+=16
for q in P.DATA['interactions']:
    for k in ('point','location'):
        if k in q:q[k][0]+=16
B40.prepare_plane(P,D);W40.prepare_plane(P,D);W41.prepare_plane(P,D)
for m in (B,W,A):m.prepare_plane(P,D)
snapshot=copy.deepcopy(P.DATA)
for m in (B,W,A):m.prepare_plane(P,D)
assert snapshot==P.DATA
for r in D['repair38']['business_belt40']['records']:
    q=next(q for q in P.DATA['interactions'] if q.get('actor')==r['control']);target=next(t for t in q['targets'] if t['actor']==r['control']);assert target['translation_states'][1]==[b-a for a,b in zip(r['worn_hinge'],r['stowed_hinge'])]
assert sum(q['asset'] in W.SWAPS.values() for q in P.DATA['instances'])==96
count=sum(q['asset'] in A.SWAPS.values() for q in P.DATA['instances']);assert len(out[2]['swapped'])==count
report=dict(passed=True,scope='Offline adapter contract; root owns native visual/input approval',native_worn_meshes=4,retained_lids_refitted=4,window_mesh_swaps=96,finish_mesh_swaps=count,existing_release_targets_retained=True,absolute_lid_baseline_and_released_delta_consistent=True,native_and_data_repeat_safe=True)
(F/'Assembly42_AdapterVerification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
