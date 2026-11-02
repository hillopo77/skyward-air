"""Five bounded source/policy/control passes; native tests are separate."""
import unittest,math,json
from pathlib import Path
import flight39_model as M
import airfield39 as A
from flight39_driver import Driver
from airport_flight39 import MAP,_value,DOORS,PILOT_SEATS
from flight39_frame import occupied_reference


def ready():
    s=M.fresh();c=dict(aboard=True,pilot=True,doors_closed=True,bridge_stowed=True)
    for n in ('battery','avionics','fuel','pumps','bleed','beacon'):assert M.command(s,n,1,c)[0]
    for n in ('engine1','engine2'):assert M.command(s,n,1,c)[0]
    for _ in range(120):M.step(s,.05,c)
    return s,c


class FlightTests(unittest.TestCase):
    def test_native_zero_default_quaternion_boundary(self):
        # Some UE Python UStruct constructors default all fields to0. A zero
        # quaternion silently turns every composed door pose into rotation0.
        from types import SimpleNamespace as N
        from flight39_frame import Frame
        class NativeQuat:
            def __init__(self,x=0.,y=0.,z=0.,w=0.):self.x=x;self.y=y;self.z=z;self.w=w
        manifest=Path(__file__).parents[5]/'SkywardAir/Revision18/Exports/manifest.json'
        p=N(STATE={'door':N(get_actor_rotation=lambda:N(yaw=0.))},DATA=json.loads(manifest.read_text())['scenes']['L_Plane_Reference'])
        for name in ['_apply_movable','_apply_control','interaction_point','nearest','sit','stand','update_floor','update_door','point_at','inspect_item','end_inspect','control_snapshot']:setattr(p,name,lambda *args:None)
        g=N(P=p,u=N(Quat=NativeQuat,Vector=lambda *args:args),S={},toggle_spectator=lambda:None)
        frame=Frame(g,N(get_actor_transform=lambda:object()))
        self.assertEqual(frame.door_q.w,1.);self.assertEqual(frame.delta.w,1.)
    def test_occupied_seat_guard_survives_frame(self):
        npc=dict(animation='PassengerSeated',location=[17.868,15.425,.03])
        self.assertTrue(occupied_reference(dict(location=[17.868,15.425,1.6]),[npc]))
        self.assertFalse(occupied_reference(dict(location=[17.1,15.425,1.6]),[npc]))
        self.assertFalse(occupied_reference(dict(location=[17.868,15.425,1.6]),[dict(npc,animation='Idle')]))
    def test_basis_and_reference_roundtrip(self):
        for h in (0,45,90,180,270,359):
            for p in (-20,0,15):
                for b in (-35,0,35):
                    f,z=M.native_basis(h,p,b)
                    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
                    cross=lambda a,b:[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
                    x=cross(f,z)
                    self.assertAlmostEqual(dot(f,z),0,places=10);self.assertAlmostEqual(dot(f,f),1,places=10);self.assertAlmostEqual(dot(z,z),1,places=10)
                    local=[.72,-21.8,1.62];position=[300,200,91]
                    world=[position[i]+x[i]*local[0]+f[i]*local[1]+z[i]*local[2] for i in range(3)]
                    delta=[world[i]-position[i] for i in range(3)];recovered=[dot(delta,axis) for axis in (x,f,z)]
                    for a,v in zip(local,recovered):self.assertAlmostEqual(a,v,places=10)
            f,_=M.native_basis(h,0,0);delta=[-math.sin(math.radians(h)),math.cos(math.radians(h)),0]
            for a,v in zip(f,delta):self.assertAlmostEqual(a,v)
    def test_pass1_runway_dimensions_and_route(self):
        self.assertEqual(M.RUNWAY['length'],2600);self.assertEqual(M.RUNWAY['width'],45);self.assertEqual(M.TAXI_WIDTH,23)
        p=M.taxi_route();self.assertEqual(p[0],M.STAND[:2]);self.assertGreater(M.closest_path(p[-1],p)['along'],700)
        self.assertAlmostEqual(M.heading_to(p[0],p[1]),0);self.assertTrue(M.runway_position(p[-1],0))
        for q in A.pavement_polygons():
            self.assertGreater(len(q['polygon']),3);self.assertEqual(q['top'],-3.689)

    def test_pass2_cold_start_and_denials(self):
        s=M.fresh();c=dict(aboard=True,pilot=True,doors_closed=True,bridge_stowed=True)
        self.assertFalse(M.command(s,'engine1',1,c)[0]);self.assertFalse(M.command(s,'avionics',1,c)[0]);self.assertFalse(M.command(s,'gear',False,c)[0])
        for n in ('battery','avionics','fuel','pumps','bleed','beacon'):self.assertTrue(M.command(s,n,1,c)[0])
        for field in ('aboard','pilot','doors_closed','bridge_stowed'):
            denied=dict(c);denied[field]=False;self.assertFalse(M.command(s,'engine1',1,denied)[0])
        self.assertTrue(M.command(s,'engine1',1,c)[0]);self.assertFalse(M.command(s,'engine1',2,c)[0])
        for _ in range(81):M.step(s,.05,c)
        self.assertTrue(s['engines'][0]['running']);self.assertFalse(s['engines'][1]['running'])
        self.assertFalse(M.command(s,'parking',False,c)[0]);self.assertFalse(M.command(s,'throttle1',1,c)[0])

    def test_pass3_interlocks_and_braking(self):
        s,c=ready();M.command(s,'clearance',1,c);self.assertTrue(M.command(s,'parking',False,c)[0]);M.command(s,'throttle1',.25,c);M.command(s,'throttle2',.25,c)
        for _ in range(180):M.step(s,.05,c)
        self.assertGreater(s['speed'],2);self.assertLess(s['speed'],8)
        denied=dict(c,doors_closed=False);M.step(s,.05,denied);self.assertTrue(s['parking'])
        for _ in range(60):M.step(s,.05,c)
        self.assertEqual(s['speed'],0);self.assertFalse(M.command(s,'clearance',1,c)[0])

    def test_isolated_rudder_pitch_and_parked_steering(self):
        s,c=ready();s['controls']['rudder']=1
        before=s['heading']
        for _ in range(20):M.step(s,.05,c)
        self.assertEqual(s['heading'],before,'Locked stationary wheels cannot rotate the aircraft on the spot')
        # Explicit isolated unit setup, never used by native journey/driver.
        s.update(airborne=True,position=[300,-800,100],speed=90,pitch=3,parking=False)
        s['controls'].update(roll=0,pitch=0,rudder=1)
        before=s['heading']
        for _ in range(20):M.step(s,.05,c)
        self.assertAlmostEqual(M.angle_error(s['heading'],before),3.,places=6)
        self.assertEqual(s['bank'],0)
        s['controls'].update(rudder=0,pitch=1);before=s['pitch']
        for _ in range(20):M.step(s,.05,c)
        self.assertAlmostEqual(s['pitch']-before,9.,places=6)

    def test_pass4_actual_authored_control_ids(self):
        manifest=Path(__file__).parents[5]/'SkywardAir/Revision18/Exports/manifest.json'
        data=json.loads(manifest.read_text())['scenes']['L_Plane_Reference'];items={q['actor']:q for q in data['interactions']}
        self.assertTrue(set(MAP)<=set(items));self.assertTrue(set(DOORS)<=set(items));self.assertTrue(set(PILOT_SEATS)<=set(items))
        self.assertEqual(len(MAP),44)
        for n in MAP:self.assertEqual(items[n]['kind'],'control')

    def test_pass5_end_to_end_integrated_control_driver(self):
        s=M.fresh();c=dict(aboard=True,pilot=True,doors_closed=False,bridge_stowed=False);timers={};history=[]
        def command(n,v=None,announce=True):
            history.append((n,v))
            if n in ('close_doors','stow_bridge'):timers[n]=s['elapsed'];return True,'Physical request simulated by unit adapter'
            return M.command(s,n,v,c)
        def operate(actor,index):
            name=MAP[actor][0];ok,reason=command(name,_value(name,index));return dict(reason=reason,state=index,okay=ok)
        def inputs(**v):
            for n,value in v.items():M.command(s,n,value,c)
        api=dict(state=s,context=lambda:c,command=command,operate=operate,inputs=inputs);d=Driver(api)
        samples=[]
        for i in range(8000):
            if 'close_doors' in timers and s['elapsed']-timers['close_doors']>3:c['doors_closed']=True
            if 'stow_bridge' in timers and s['elapsed']-timers['stow_bridge']>8:c['bridge_stowed']=True
            d.tick(.05);M.step(s,.05,c)
            if i%20==0:samples.append(dict(t=s['elapsed'],position=s['position'][:],heading=s['heading'],speed=s['speed'],phase=s['phase']))
            if d.done:break
        result=d.snapshot();result['samples']=samples;result['test_scope']='Pure deterministic model plus request adapter; NOT native collision/visual proof'
        Path(__file__).with_name('ModelFlightPasses39.json').write_text(json.dumps(result,indent=2))
        self.assertIsNone(d.failed,result);self.assertTrue(s['airborne']);self.assertGreater(s['position'][2],90);self.assertLess(d.max_cross_track,3.5)
        self.assertGreater(d.control_responses['bank'],10);self.assertLess(d.control_responses['left_bank'],-10);self.assertGreater(d.control_responses['heading_change'],1)
        self.assertLess(d.control_responses['pitch_after_down'],d.control_responses['pitch']);self.assertFalse(s['gear_down'])
        self.assertTrue(any(e[0]=='clearance' for e in history));self.assertGreater(s['distance'],2000)
        hold=next(e for e in d.events if e['stage']=='runway_entry')
        self.assertLess(hold['position'][1]+28.,M.HOLD[1]-.45,'Actual nose must remain before the first hold-short paint line')


if __name__=='__main__':unittest.main(verbosity=2)
