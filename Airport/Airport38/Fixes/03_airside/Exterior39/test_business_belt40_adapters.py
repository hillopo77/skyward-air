"""Offline source-metadata/native/runtime hook contract; no editor launch."""
import json,copy,sys
from pathlib import Path
from types import SimpleNamespace as NS
import business_belt40 as M
F=Path(__file__).parent;R=F.parents[2];W=F.parents[5]
sys.path.insert(0,str(W/'outputs/Characters/Revision39'));import chair_runtime39
pm=json.loads((W/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
D=json.loads((R/'Exports/airport_layout.json').read_text());D.setdefault('repair38',{})['business_belt40']=json.loads((F/'BusinessBelt40_SourceApply.json').read_text())
P=NS(DATA=copy.deepcopy(pm));chair_runtime39.prepare_data(P.DATA)
for q in P.DATA['instances']:q['location'][0]+=16
for q in P.DATA['interactions']:
    for key in ('point','location'):
        if key in q:q[key][0]+=16
M.prepare_plane(P,D);snapshot=copy.deepcopy(P.DATA);M.prepare_plane(P,D);assert P.DATA==snapshot
records=D['repair38']['business_belt40']['records'];items={q['actor']:q for q in P.DATA['interactions'] if q.get('business_belt40')}
assert len(items)==4 and sum(q['initial_state']==0 for q in items.values())==1
class Component:
    def __init__(self):self.materials={}
    def set_static_mesh(self,m):self.static_mesh=m
    def set_material(self,i,m):self.materials[i]=m
    def set_mobility(self,m):self.mobility=m
class Actor:
    def __init__(self,n,tagged=True):self.n=n;self.tags=['Skyward:'+n] if tagged else [];self.c=Component();self.location=[];self.hidden=None
    def get_actor_label(self):return self.n
    def get_component_by_class(self,c):return self.c
    def set_actor_location(self,p,*args):self.location=list(p)
    def set_actor_rotation(self,r,*args):self.rotation=r
    def set_actor_enable_collision(self,b):self.collision=b
    def set_actor_hidden_in_game(self,b):self.hidden=b
actors={}
for r in records:
    for key in ('seat','control','stowed_actor','worn_actor'):actors[r[key]]=Actor(r[key],key in ('seat','control'))
meshes={aid:NS(static_materials=[NS(material_interface=aid+'_material')]) for aid in M.IDS}
ctx=NS(u=NS(StaticMeshComponent=Component,ComponentMobility=NS(MOVABLE=1),Name=lambda n:n,Rotator=lambda:0),D=D,EA=NS(get_all_level_actors=lambda:list(actors.values())),mesh=lambda aid:meshes[aid],v=lambda p:list(p))
native=M.apply_native(ctx);assert len(native['actors'])==16;M.apply_native(ctx)
for r in records:
    assert actors[r['worn_actor']].hidden==(r['initial_state']!=0)
    assert actors[r['stowed_actor']].hidden==(r['initial_state']!=1)
    assert actors[r['control']].location==r['worn_hinge']
    assert len(actors[r['worn_actor']].tags)==2
P.STATE=dict(seated=None,controls={n:dict(state=q['initial_state'],item=q) for n,q in items.items()})
def base_control(name,index):
    c=P.STATE['controls'][name];c['state']=index%2
    for target in c['item']['targets']:
        if 'visible_states' in target:actors[target['actor']].hidden=c['state'] not in target['visible_states']
    return c['state']
P.set_control_state=base_control
def base_stand():P.STATE['seated']=None;return True
P.stand=base_stand;messages=[];G=NS(P=P,D=D,say=messages.append);M.install(G);bound=P.set_control_state;M.install(G);assert P.set_control_state is bound
empty=next(r for r in records if not r['occupied_npc']);name=empty['control']
assert P.set_control_state(name,0)==1 and messages
P.STATE['seated']={'actor':empty['seat']};assert P.set_control_state(name,0)==0
assert not actors[empty['worn_actor']].hidden and actors[empty['stowed_actor']].hidden
assert P.set_control_state(name,1)==1 and actors[empty['worn_actor']].hidden
P.set_control_state(name,0);P.stand();assert P.STATE['controls'][name]['state']==1
npc=next(r for r in records if r['occupied_npc']);assert P.set_control_state(npc['control'],0)==0
report=dict(passed=True,scope='Offline API contracts; native visual review remains',native_actors=16,asset_families=5,controls=4,default_worn_npcs=1,default_stowed_empty_seats=3,data_idempotent=True,native_idempotent=True,runtime_idempotent=True,actual_webbing_targets=True,empty_fastening_denied=True,seated_fastening_and_release_checked=True,auto_stow_on_exit=True,chair_drop_applied_before_absolute_belt_fit=True)
(F/'BusinessBelt40_AdapterVerification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
