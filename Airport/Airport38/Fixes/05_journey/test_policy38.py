"""Meaningful negative policy checks; no native-game success claim."""
import json,math,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import journey_logic38 as L

checks=[]
def test(name,value):
    assert value,name
    checks.append(name)

for req in ('checked_in','security','staff24'):
    spec=dict(access24=req,automatic=True)
    test(req+' denied before proximity animation',L.auto_target(spec,{},0)==0)
    test(req+' permission enables nearby proximity',L.auto_target(spec,{req:True},200)==1)
    test(req+' permission does not hold distant leaf open',L.auto_target(spec,{req:True},600)==0)
test('Locked WC outside control refuses',not L.door_access({}, {},locked=True,inside=False))
test('Locked WC inside control always releases',L.door_access({}, {},locked=True,inside=True))
r=dict(receive_x=-24.15,rect=[-24.4,-22.78,-13.49,-12.51],height=.845)
test('Frontend bag is not accepted',not L.receiver_complete([-27,-13,1.2],r,True,0))
test('Crossing wall alone is not accepted',not L.receiver_complete([-25.8,-13,1.2],r,True,0))
test('Unsupported receiver bag is not accepted',not L.receiver_complete([-23.4,-13,1.2],r,False,0))
test('Fast receiver bag is not accepted',not L.receiver_complete([-23.4,-13,1.2],r,True,80))
test('Held receiver bag is not accepted',not L.receiver_complete([-23.4,-13,1.2],r,True,0,True))
test('Settled supported receiver bag qualifies',L.receiver_complete([-23.4,-13,1.2],r,True,5))
test('Unscanned held bag denied',not L.legal_screening('bag1',set(),set()))
test('Scanned held bag allowed',L.legal_screening('bag1',{'bag1'},set()))
test('Empty handed traversal allowed',L.legal_screening(None,set(),set()))
test('Side entry cannot clear detector',L.traversal([-2,3,1.62],[0,3.6,1.62],[-.5,.5,2.75,3.3],False,3)==(False,False))
test('Teleport across detector cannot clear',L.traversal([0,1,1.62],[0,3.6,1.62],[-.5,.5,2.75,3.3],False,1)==(False,False))
armed,done=L.traversal([0,2.6,1.62],[0,2.9,1.62],[-.5,.5,2.75,3.3],False,1)
test('Natural entrance arms detector',armed and not done)
armed,done=L.traversal([0,3.1,1.62],[0,3.6,1.62],[-.5,.5,2.75,3.3],armed,1)
test('Natural complete traverse clears',done and not armed)

floors=[dict(name='Bounded cabin',rect=[13.602,18.398,0,35.1],height=0,priority=0),
        dict(name='Lower stair',rect=[13.9,15.35,1.2,3.5],slope=dict(axis='y',**{'from':1.2,'to':3.5,'start':0,'end':-2.05}),priority=20,requires_open='hatch',max_step=.28),
        dict(name='Lower hold',rect=[14.6,17.4,1.3,34.65],height=-2.05,priority=10,max_step=.28)]
test('Outside arbitraryXY has no invisiblezero floor',L.choose_floor(0,10,0,floors)[0] is None)
test('Outdated north-east ramp has nozero floor',L.choose_floor(-17,20,0,floors)[0] is None)
test('Cabin bound valid',L.choose_floor(16,10,0,floors)==(0.,'Bounded cabin'))
test('Closed hatch preserves cabin deck',L.choose_floor(14.7,1.3,0,floors,{'hatch':dict(progress=0)})==(0.,'Bounded cabin'))
h,name=L.choose_floor(14.7,1.3,0,floors,{'hatch':dict(progress=1)})
test('Open hatch selects real descending stair',name=='Lower stair' and h<0)
test('Lowerhold cannot pull down cabin',L.choose_floor(16,12,0,floors)[0]==0)
test('Lowerhold remains supported when inside',L.choose_floor(16,12,-2.05,floors)==(-2.05,'Lower hold'))
test('Naturalstairreturn recovers fulleyeheight',L.choose_floor(14.7,1.18,-.12,floors,{'hatch':dict(progress=1)})[0]==0)
bridge=dict(name='bridge',polygon=[[-2,-1],[2,-1],[2,1],[-2,1]],height=0,priority=16)
test('Polygon boundary is included with no seam',L.choose_floor(-2,0,0,[],extra=[bridge])[0]==0)
test('PolygonAABB corner does not create phantom floor',L.choose_floor(2.1,0,0,[],extra=[bridge])[0] is None)
carousel=L.carousel_geometry(dict(location=[-19.4,-17,0],rotation_degrees=0,scale=[.48,.75,1]))
test('Carousel follows all84matching actualslat samples',len(carousel['path'])==len(carousel['outer'])==len(carousel['inner'])==84)
test('Carousel centreline exact4.08x1.875m',abs(max(p[0] for p in carousel['path'])-min(p[0] for p in carousel['path'])-4.08)<1e-9 and abs(max(p[1] for p in carousel['path'])-min(p[1] for p in carousel['path'])-1.875)<1e-9)
test('Carousel centreline stays inside measurednativeouterbounds',all(-21.727<p[0]<-17.073 and -18.386<p[1]<-15.614 for p in carousel['path']))
test('Carousel excludes machineryisland',L.carousel_tangent([-19.4,-17],carousel) is None)
test('Carousel excludes exterior offbeltpoint',L.carousel_tangent([-22,-17],carousel) is None)
upper=L.carousel_tangent([-19.4,-17+.9375],carousel);lower=L.carousel_tangent([-19.4,-17-.9375],carousel)
test('Carousel north branch moveswest alongmodeledslats',upper['tangent'][0]<-.999 and abs(upper['tangent'][1])<1e-6)
test('Carousel south branch moveseast alongmodeledslats',lower['tangent'][0]>.999 and abs(lower['tangent'][1])<1e-6)
right=L.carousel_tangent([-19.4+2.04,-17],carousel)
test('Carousel eastend turnsnorth on actualshortendsegment',right['tangent'][1]>.999 and abs(right['tangent'][0])<1e-6)
test('Carousel centreline hasactualslatmiddleheight',abs(carousel['height']-.415)<1e-9)
(HERE/'policy_results38.json').write_text(json.dumps(dict(scope='Isolated policy and math tests; native movement still required',passed=len(checks),checks=checks),indent=2))
print('POLICY38 PASS',len(checks))
