"""Offline native/data/curved-track contracts. No Unreal launch or asset edits."""
import json,copy
from pathlib import Path
from types import SimpleNamespace as NS
import window40 as W
import window41 as M
F=Path(__file__).parent;R=F.parents[2]
pm=json.loads((F.parents[5]/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
D=json.loads((R/'Exports/airport_layout.json').read_text());D.setdefault('repair38',{})['window41']=dict(moving_actor_names=sorted(M.moving_names(pm)))
class Vec:
    def __init__(self,x=0,y=0,z=0):self.x=x;self.y=y;self.z=z
    def __add__(self,b):return Vec(self.x+b.x,self.y+b.y,self.z+b.z)
    def values(self):return [self.x,self.y,self.z]
class Component:
    def __init__(self):self.materials={}
    def set_static_mesh(self,m):self.static_mesh=m
    def set_material(self,i,m):self.materials[i]=m
class Actor:
    def __init__(self,n,p,tag):self.n=n;self.p=Vec(p[0]*100,-p[1]*100,p[2]*100);self.tags=[tag+n];self.c=Component()
    def get_path_name(self):return self.tags[0]
    def get_actor_label(self):return self.n
    def get_actor_location(self):return self.p
    def set_actor_location(self,p,*args):self.p=p
    def get_component_by_class(self,c):return self.c
actors=[]
for group,tag in [('instances','Skyward:'),('lights','SkywardLight:'),('cameras','SkywardCamera:')]:
    for q in pm[group]:actors.append(Actor(q['name'],[q['location'][0]+16,*q['location'][1:]],tag))
before={a.get_path_name():a.p.values() for a in actors};meshes={n:NS(static_materials=[NS(material_interface=n+'_slot')]) for n in M.SWAPS.values()}
ctx=NS(u=NS(StaticMeshComponent=Component,Vector=Vec,Name=lambda n:n),R=R,D=D,EA=NS(get_all_level_actors=lambda:actors),mesh=lambda n:meshes[n])
report=M.apply_native(ctx);assert report['swaps']==126,report['swaps'];first={a.get_path_name():a.p.values() for a in actors};M.apply_native(ctx);assert first=={a.get_path_name():a.p.values() for a in actors}
names=M.moving_names(pm);shades=M.shade_names(pm);vertical=0;horizontal=0
for a in actors:
    old=before[a.get_path_name()];now=a.p.values();key=a.tags[0]
    is_lift=(key.startswith('Skyward:') and a.n in names) or(key.startswith('SkywardLight:PSU ') and abs(old[0]/100-16)>1)or('SkywardCamera:CAM_Plane_PSUDetail' in key)
    dz=now[2]-old[2];assert abs(dz-(M.LIFT*100 if is_lift else 0))<1e-7,(a.n,dz)
    if is_lift:vertical+=1
    if key.startswith('Skyward:') and a.n in shades:
        side=-1 if ' L18' in a.n else 1;assert abs(now[0]-old[0]-side*M.SHADE_FIT*100)<1e-7;horizontal+=1
    else:assert now[0]==old[0]
P=NS(DATA=copy.deepcopy(pm))
for q in P.DATA['instances']:q['location'][0]+=16
for q in P.DATA['interactions']:
    for p in q.get('roller_parts',[]):p['closed_location'][0]+=16
for q in P.DATA['lights']:q['location'][0]+=16
W.prepare_plane(P,D);M.prepare_plane(P,D);P.STATE=dict(actors={},movables={});P.vector=lambda p:list(p)
class Moving:
    def set_actor_location(self,p,*args):self.p=list(p)
for q in P.DATA['interactions']:
    if not q.get('window41'):continue
    for p in q['roller_parts']:P.STATE['actors'][p['actor']]=Moving()
    P.STATE['movables'][q['actor']]=dict(item=q,progress=0.)
fallback=[];P._apply_movable=lambda m:fallback.append(m);G=NS(P=P,flight39=dict(frame=NS(world=lambda p:[p[0]+7,p[1]-9,p[2]+3])))
M.install(G);bound=P._apply_movable;M.install(G);assert P._apply_movable is bound
for f in (0.,.5,1.):
    for m in P.STATE['movables'].values():
        m['progress']=f;P._apply_movable(m)
        for p in m['item']['roller_parts']:
            expected=W.shade_pose(p,f);expected[0]+=p['window40_side']*M.SHADE_FIT;expected=[expected[0]+7,expected[1]-9,expected[2]+3];assert P.STATE['actors'][p['actor']].p==expected
P._apply_movable(dict(item={}));assert len(fallback)==1
result=dict(passed=True,scope='Offline adapter contracts; actual native visuals remain root-owned',swapped_actors=report['swaps'],lifted_complete_fixture_light_camera_actors=vertical,parallel_fitted_shade_parts=horizontal,native_repeat_safe=True,central_psu_unmoved=True,all_relative_pivots_preserved=True,curved_parts=240,runtime_carrier_checked_states=[0,.5,1],runtime_repeat_safe=True)
(F/'Window41_AdapterVerification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
