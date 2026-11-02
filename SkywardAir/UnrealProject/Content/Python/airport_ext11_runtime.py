"""Pickup, pressure charge, soft animated powder, and return-to-bracket behavior."""
import unreal as u,math,time
G=None;CHARGE={};HOMES={};FX=None;MID=None

def initialize(game):
 global G,FX,MID;G=game
 for q in G.D['instances']:
  if q['asset']=='SM_AP_Extinguisher11':
   a=G.S['actors'][q['name']];HOMES[q['name']]=a.get_actor_transform();CHARGE[q['name']]=10.;a.static_mesh_component.set_simulate_physics(False)
 FX=G.S['actors']['Extinguisher powder effect'];FX.set_actor_hidden_in_game(True);MID=FX.static_mesh_component.create_dynamic_material_instance(0)

def is_ext(name):return name in CHARGE

def stow():
 n=G.S['held']
 if not is_ext(n):return
 a=G.S['actors'][n]
 if (a.get_actor_location()-HOMES[n].translation).length()>300:G.say('Return near the wall bracket to stow');return
 G.release(False);a.static_mesh_component.set_simulate_physics(False);a.set_actor_transform(HOMES[n],False,True);CHARGE[n]=10.;G.event('Extinguisher stowed',actor=n)

def tick(dt,manual=False):
 if not FX:return
 n=G.S['held'];active=is_ext(n) and (manual or G.P.STATE['pc'].is_input_key_down(G.KEY['LeftMouseButton'])) and CHARGE[n]>0
 FX.set_actor_hidden_in_game(not active);G.S['spray_active']=bool(active)
 if not is_ext(n):return
 pc=G.P.STATE['pc'];a=G.S['actors'][n];c=a.static_mesh_component;r=pc.get_control_rotation();want=u.Rotator(pitch=0,yaw=r.yaw-90,roll=r.pitch);delta=u.MathLibrary.normalized_delta_rotator(want,a.get_actor_rotation());omega=c.get_physics_angular_velocity_in_radians();c.add_torque_in_radians(u.Vector(-math.radians(delta.roll),-math.radians(delta.pitch),math.radians(delta.yaw))*20-omega*6,G.NONE,True)
 if pc.was_input_key_just_pressed(G.KEY['R']):stow();return
 if not active:return
 CHARGE[n]=max(0,CHARGE[n]-dt);f=u.MathLibrary.get_forward_vector(r);start=a.get_actor_location()+u.MathLibrary.get_forward_vector(a.get_actor_rotation())*7+u.MathLibrary.get_right_vector(a.get_actor_rotation())*20+u.MathLibrary.get_up_vector(a.get_actor_rotation())*62+f*4;hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],start,start+f*300,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[a,G.P.STATE['pawn']],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;distance=h[3] if h and h[0] else 300;reach=max(.04,min(1,(distance-8)/300));FX.set_actor_location(start,False,False);FX.set_actor_rotation(want,False);FX.set_actor_scale3d(u.Vector(1,reach,1));MID.set_scalar_parameter_value('Reach',reach)
 if G.S['ticks']%15==0:G.say('Powder charge %.1f s · E drop · R return to bracket'%CHARGE[n])
 G.S['spray_active']=True;G.S['extinguisher_charge']=CHARGE[n]
