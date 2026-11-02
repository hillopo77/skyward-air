"""Bounded moving-body adapter regressions; not native physics approval."""
import unittest,math,json
from pathlib import Path
from types import SimpleNamespace as N
from flight39_frame import Frame,inherit_current_carrier,simulated_step_time,physics_clock
from flight39_envelope import pressure_envelope

PLANE_DATA=json.loads((Path(__file__).parents[5]/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']


class V:
    def __init__(self,x=0.,y=0.,z=0.):self.x=x;self.y=y;self.z=z
    def __add__(self,b):return V(self.x+b.x,self.y+b.y,self.z+b.z)
    def __sub__(self,b):return V(self.x-b.x,self.y-b.y,self.z-b.z)
    def __mul__(self,n):return V(self.x*n,self.y*n,self.z*n)
    def __truediv__(self,n):return self*(1/n)
    def length(self):return math.sqrt(self.x**2+self.y**2+self.z**2)
    def to_tuple(self):return self.x,self.y,self.z


class Q:
    def __init__(self,x=0,y=0,z=0,w=1):self.x=x;self.y=y;self.z=z;self.w=w
    def rotator(self):return self
    def quaternion(self):return self


class Body:
    def __init__(self,p):self.p=p;self.velocity=V();self.sim=True;self.static_mesh_component=self;self.pose_writes=0
    def get_center_of_mass(self):return self.p
    def get_actor_location(self):return self.p
    def get_actor_rotation(self):return Q()
    def set_actor_location_and_rotation(self,p,*args):self.p=p;self.pose_writes+=1
    def is_simulating_physics(self):return self.sim
    def get_physics_linear_velocity(self):return self.velocity
    def set_physics_linear_velocity(self,v,*args):self.velocity=v


def fixture():
    frame=Frame.__new__(Frame);base=N(translation=V(1600,-1730,0))
    mathlib=N(transform_location=lambda t,p:t.translation+p,inverse_transform_location=lambda t,p:p-t.translation)
    u=N(Vector=V,Quat=Q,Name=lambda n:n,MathLibrary=mathlib,FloatingPawnMovement=object())
    bag=Body(V(1600,-1730,120));outside=Body(V(-4200,1300,120))
    state=dict(physics={'bag':bag,'outside':outside},actors={'bag':bag,'outside':outside},held=None,
               actor_specs={'bag':dict(location=[-42,-13,1.2],asset='SM_AP_Luggage'),'outside':dict(location=[-42,-13,1.2],asset='SM_AP_Luggage')})
    frame.u=u;frame.G=N(u=u,S=state,valid=lambda a:True);frame.P=N(_quat_product=lambda a,b:Q(),_quat_vector=lambda q,v:v)
    frame.base=frame.current=frame.motion_previous=base;frame.motion_dt=0.;frame.delta=Q();frame.prop_records={};frame.prop_scan_clock=0.;frame.prop_scan_count=0;frame.attached=False
    frame.envelope=pressure_envelope(PLANE_DATA,16.)
    def release(throw=False):
        if throw:bag.velocity=bag.velocity+V(900,0,0)
        state['held']=None
    frame.original_release=release
    return frame,bag,outside


class PropsTests(unittest.TestCase):
    def test_actual_position_not_authored_airport_location(self):
        f,bag,outside=fixture();f.refresh_props(.24)
        self.assertFalse(f.prop_records);f.refresh_props(.01)
        self.assertEqual(set(f.prop_records),{'bag'});self.assertEqual(f.prop_scan_count,1)
        outside.p=V(1600,-1730,120);f.refresh_props(.25);self.assertIn('outside',f.prop_records)
        outside.p=V(-4200,1300,120);f.refresh_props(.25)
        # Only the reference-frame transport owns an actual envelope exit;
        # the periodic scan cannot silently discard the velocity conversion.
        f.motion_dt=.1;f._props(f.current,Q(),V());self.assertNotIn('outside',f.prop_records)

    def test_held_newcomer_immediate_and_drop_throw_velocity_once(self):
        f,b,_=fixture();f.current=N(translation=V(2600,-1730,0));f.motion_dt=1.;b.p=V(2600,-1730,120)
        f.G.S['held']='bag';f.refresh_props(.01)
        self.assertIn('bag',f.prop_records);self.assertEqual(b.velocity.x,0.)
        self.assertEqual(f.world_velocity(b).x,1000.)
        f.release(True);self.assertEqual(b.velocity.x,900.);self.assertEqual(f.world_velocity(b).x,1900.);self.assertEqual(b.pose_writes,0)
        f.G.S['held']='bag';b.velocity=V();f.release(False);self.assertEqual(b.velocity.x,0.);self.assertEqual(f.world_velocity(b).x,1000.)

    def test_native_integration_not_double_translated(self):
        f,b,_=fixture();f.refresh_props(0,True);old=f.current;f.current=N(translation=V(1700,-1730,0));f.motion_dt=.1
        f._props(old,Q(),V(1000,0,0));self.assertAlmostEqual(b.p.x,1700);self.assertAlmostEqual(b.velocity.x,0)
        b.p=b.p+b.velocity*.1 # Chaos integrates relative velocity aboard.
        old=f.current;f.current=N(translation=V(1800,-1730,0));f.motion_previous=old
        f._props(old,Q(),V(1000,0,0));self.assertAlmostEqual(b.p.x,1800);self.assertAlmostEqual(b.velocity.x,0)
        self.assertAlmostEqual(f.world_velocity(b).x,1000)

    def test_clamped_native_integration_survives_capture_hitches(self):
        f,b,_=fixture();f.refresh_props(0,True)
        # Deliberately integrate the body on Chaos'33ms cap, rather than
        # assuming native rigid bodies advanced the full render/world delta.
        for world_dt in [1/60,.05,1.,1/60,.2,1/30,.05]*8:
            native_dt=simulated_step_time(world_dt,1/30)
            b.p=b.p+b.velocity*native_dt
            old=f.current;travel=9800*min(world_dt,.05)
            f.current=N(translation=old.translation+V(travel,0,0))
            f.motion_dt=world_dt;f.physics_dt=native_dt;f.motion_previous=old
            f._props(old,Q(),V(travel/world_dt,0,0))
            self.assertIn('bag',f.prop_records)
            self.assertAlmostEqual(b.p.x-f.current.translation.x,0.,places=6)
            self.assertAlmostEqual(b.velocity.x,0.,places=6)
            self.assertAlmostEqual(f.world_velocity(b).x,travel/world_dt,places=6)

    def test_relative_impulse_motion_is_retained_and_exit_inherits_carrier_once(self):
        f,b,_=fixture();f.refresh_props(0,True);b.velocity=V(80,0,0)
        old=f.current;f.current=N(translation=old.translation+V(100,0,0));f.motion_previous=old;f.motion_dt=.1
        b.p=b.p+b.velocity*.033333333
        f._props(old,Q(),V(1000,0,0))
        self.assertAlmostEqual(b.p.x-f.current.translation.x,80*.033333333)
        self.assertAlmostEqual(f.relative_velocity(b).x,80.)
        self.assertAlmostEqual(f.world_velocity(b).x,1080.)
        # Crossing the envelope is driven by a real native body position;
        # the adapter changes velocity space once, never clamps it inside.
        b.p=V(f.current.translation.x+410,-1730,120)
        old=f.current;f.current=N(translation=old.translation+V(100,0,0));f.motion_previous=old
        f._props(old,Q(),V(1000,0,0))
        self.assertNotIn('bag',f.prop_records);self.assertAlmostEqual(b.velocity.x,1080.)
        f._props(f.current,Q(),V(1000,0,0));self.assertAlmostEqual(b.velocity.x,1080.)

    def test_reentry_converts_world_velocity_once_and_external_prop_unchanged(self):
        f,b,outside=fixture();f.current=N(translation=V(2600,-1730,0));f.motion_dt=1.
        b.p=V(2600,-1730,120);b.velocity=V(1080,0,0);outside.velocity=V(250,0,0)
        f.register_prop('bag',b);self.assertAlmostEqual(b.velocity.x,80.)
        f.register_prop('bag',b);self.assertAlmostEqual(b.velocity.x,80.)
        f.refresh_props(0,True);self.assertAlmostEqual(b.velocity.x,80.)
        self.assertNotIn('outside',f.prop_records);self.assertEqual(outside.velocity.x,250.)

    def test_held_spring_uses_local_velocity_only_for_registered_body(self):
        f,b,_=fixture();f.G.S['held']='bag';f.refresh_props(0,True)
        f.update_spring_frame();self.assertEqual(f.G.S['carrier_velocity39'].length(),0.)
        self.assertEqual(f.G.S['held_physics_frame39'],'aircraft-relative')

    def test_physics_clock_uses_active_engine_cap_and_minimum(self):
        settings=N(get_editor_property=lambda n:dict(max_physics_delta_time=.025,min_physics_delta_time=.002)[n])
        g=N(u=N(PhysicsSettings=object(),get_default_object=lambda cls:settings))
        limits=physics_clock(g)
        self.assertEqual(limits['source'],'PhysicsSettings CDO')
        self.assertEqual(simulated_step_time(1.,limits['maximum'],limits['minimum']),.025)
        self.assertEqual(simulated_step_time(.001,limits['maximum'],limits['minimum']),0.)
        self.assertEqual(simulated_step_time(.016,limits['maximum'],limits['minimum']),.016)

    def test_unreal_generic_exception_reads_actual_saved_project_cap(self):
        def unexposed(name):raise Exception('PhysicsSettings property is not exposed')
        g=N(u=N(PhysicsSettings=object(),get_default_object=lambda cls:N(get_editor_property=unexposed)))
        limits=physics_clock(g)
        self.assertTrue(limits['source'].endswith('Config/DefaultEngine.ini') or limits['source'].endswith('Config\\DefaultEngine.ini'))
        self.assertAlmostEqual(limits['maximum'],.033333333)

    def test_current_carrier_is_never_added_twice(self):
        self.assertEqual(inherit_current_carrier([0,0,0],[9000,0,0]),[9000,0,0])
        self.assertEqual(inherit_current_carrier([9000,0,0],[9000,0,0]),[9000,0,0])
        self.assertEqual(inherit_current_carrier([9400,0,0],[9000,0,0]),[9400,0,0])

    def test_spectator_speed_and_walking_restore(self):
        f,_,_=fixture()
        class Movement:
            data=dict(max_speed=600.,acceleration=4000.,deceleration=8000.)
            def get_editor_property(self,n):return self.data[n]
            def set_editor_property(self,n,v):self.data[n]=v
        move=Movement();boost=[False]
        f.P.STATE=dict(pawn=N(get_component_by_class=lambda cls:move),pc=N(is_input_key_down=lambda key:boost[0]))
        f.G.KEY={'LeftShift':'Shift'};f.spectator_movement=None;f.G.S['spectator']=True
        f.spectator_speed();self.assertEqual(move.data['max_speed'],3000.)
        boost[0]=True;f.spectator_speed();self.assertEqual(move.data['max_speed'],20000.)
        f.G.S['spectator']=False;move.data['max_speed']=230.;f.spectator_speed()
        self.assertEqual(move.data['max_speed'],230.);self.assertEqual(move.data['acceleration'],4000.);self.assertEqual(move.data['deceleration'],8000.)


if __name__=='__main__':unittest.main(verbosity=2)
