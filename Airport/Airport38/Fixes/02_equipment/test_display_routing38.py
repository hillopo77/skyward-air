"""Unit contract for display routing; does not claim native rendering success."""
from pathlib import Path
from types import SimpleNamespace as N
import json,sys
import equipment_displays38 as E
H=Path(__file__).resolve().parent
class Component:
    def __init__(self):self.static_mesh=N(static_materials=[N(material_slot_name='MI_AP_Screen.001'),N(material_slot_name='MI_AP_P38EScreen')]);self.applied={}
    def set_material(self,j,m):self.applied[j]=m
class Actor:
    def __init__(self,n):self.n=n;self.static_mesh_component=Component()
    def get_actor_label(self):return self.n
actors={n:Actor(n) for n in ['Security belt 01','X-ray scanner 01','Self-service kiosk24 0','Gate A08 boarding desk']}
events=[]
G=N(screen=lambda actor,key:events.append((actor,key)),physics=lambda dt:None,valid=bool,u=N(load_asset=lambda p:p),D={'repair38':{'equipment':{'screen_roles38':{'X-ray scanner 01':'Scanner','Self-service kiosk24 0':'Checkin','Gate A08 boarding desk':'A08'}}}},S={'actors':actors})
J=N(S={'powered':{'Security belt 01':True}});sys.modules['airport_journey38']=J
E.install(G);checks=[]
def ok(n,v):assert v,n;checks.append(n)
ok('Inherited .001 screen slot receives real default UI',actors['Self-service kiosk24 0'].static_mesh_component.applied[0].endswith('MI_AP_UI38_Checkin'))
ok('Reader lens material is not mistaken for the display',1 not in actors['Self-service kiosk24 0'].static_mesh_component.applied)
G.screen(actors['Security belt 01'],'Scanned')
ok('Belt scan completion routes to actual X-ray monitor',actors['X-ray scanner 01'].static_mesh_component.applied[0].endswith('MI_AP_UI38_Scanned'))
J.S['powered']['Security belt 01']=False;E.S['last']=0;G.physics(.016)
ok('Stopped motor sets actual monitor STOPPED UI',actors['X-ray scanner 01'].static_mesh_component.applied[0].endswith('MI_AP_UI38_Stopped'))
J.S['powered']['Security belt 01']=True;E.S['last']=0;G.physics(.016)
ok('Reset motor restores ready scanner UI',actors['X-ray scanner 01'].static_mesh_component.applied[0].endswith('MI_AP_UI38_Scanner'))
G.screen(actors['Gate A08 boarding desk'],'Boarding')
ok('A08 cannot display a false A07 boarding-open state',actors['Gate A08 boarding desk'].static_mesh_component.applied[0].endswith('MI_AP_UI38_A08'))
show=G.screen;E.install(G);ok('Display install is idempotent',G.screen is show)
(H/'display_routing_results38.json').write_text(json.dumps(dict(scope='Unit routing only; native material/readability check remains',checks=checks,passed=True),indent=2))
print('DISPLAY_ROUTING38_PASS',len(checks))
