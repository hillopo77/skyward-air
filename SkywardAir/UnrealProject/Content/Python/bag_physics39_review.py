"""Explicit staged diagnostic; never substitutes for the fresh airport journey."""
import json,time,math,traceback
import unreal as u
G=None;S={}

def finish(status,**extra):
 d=dict(status=status,context=S['context'],setup='Staged diagnostic: airborne state, pawn and one suitcase positioned once before normal native holding/release. Not fresh-route evidence.',
        setup_teleports=3,samples=S['samples'],checks=S['checks'],registry_diagnostics=S.get('registry_diagnostics',[]),physics_clock=G.flight39['frame'].physics_clock,**extra)
 (G.R/'ArtBible/BagPhysics39.json').write_text(json.dumps(d,indent=2))
 u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)

def tick(dt):
 try:
  now=time.perf_counter();elapsed=now-S['start'];frame=G.flight39['frame'];pawn=G.P.STATE['pawn'];c=S['bag'].static_mesh_component
  local=list(G.source(frame.reference(c.get_center_of_mass())));distance=(c.get_center_of_mass()-pawn.get_actor_location()).length()/100
  if now-S.get('sampled',0)>.1:
   S['sampled']=now;S['samples'].append(dict(t=elapsed,distance_m=distance,local_com=local,registered=S['name'] in frame.prop_records,
     held=G.S.get('held'),pawn_local=list(G.source(frame.reference(pawn.get_actor_location()))),native_local=list(u.MathLibrary.inverse_transform_location(frame.current,c.get_center_of_mass()).to_tuple()),
     native_relative_velocity=list(c.get_physics_linear_velocity().to_tuple()),world_velocity=list(frame.world_velocity(c).to_tuple()),carrier_velocity=list(frame.point_velocity(c.get_center_of_mass()).to_tuple()),motion_dt=frame.motion_dt,physics_dt=frame.physics_dt))
  if elapsed>12 and not S.get('released'):
   S['checks'].append(dict(name='Held native bag remains within two metres at20FPS',passed=distance<2.,distance_m=distance))
   S.update(released=now,drop_local=local);G.release(False)
  if S.get('released') and now-S['released']>3:
   relative=frame.relative_velocity(c).length()/100
   drift=math.dist(local[:2],S['drop_local'][:2]);okay=S['name'] in frame.prop_records and drift<4 and -.15<local[2]<2 and relative<12
   S['checks'].append(dict(name='Normal release retains local support',passed=okay,local_drift_m=drift,local_com=local,relative_speed_m_s=relative))
   finish('PASS' if all(q['passed'] for q in S['checks']) else 'FAIL')
 except Exception:finish('ERROR',error=traceback.format_exc())

def start(game):
 global G;G=game;G.QA=True;G.CAPTURE=False
 frame=G.flight39['frame'];state=G.flight39['state'];pawn=G.P.STATE['pawn'];pc=G.P.STATE['pc']
 G.S.update(checked_in=True,security=True,boarding=True,aboard=True)
 state.update(position=[16,17.3,100],speed=90.,airborne=True,parking=False,pitch=3.,bank=0.,heading=0.,vertical_speed=0.)
 frame.pose(state['position'],0,3,0,.016)
 # The initial altitude is an explicit setup teleport, not a6250m/s flight.
 # Reset the reference clock before introducing the diagnostic body.
 frame.pose(state['position'],0,3,0,.016)
 pawn.set_actor_location(frame.world(G.v([16,-1.5,1.62])),False,True);pc.set_control_rotation(u.Rotator(yaw=90))
 move=pawn.get_component_by_class(u.FloatingPawnMovement);move.stop_movement_immediately();move.set_plane_constraint_enabled(False)
 frame.attach(pawn);frame.attached=True;frame.floor(0)
 name='Physical luggage 01';bag=G.S['actors'][name];c=bag.static_mesh_component
 desired=pawn.get_actor_location()+u.Vector(0,80,-40)
 bag.set_actor_location(desired-c.get_center_of_mass()+bag.get_actor_location(),False,True)
 G.act(next(q for q in G.S['targets'] if q['actor']==name and q['kind']=='pickup'))
 assert G.S.get('held')==name,('Diagnostic pickup did not hold suitcase',G.S.get('held'))
 assert frame.register_prop(name,bag),('Diagnostic suitcase not inside cabin',G.source(frame.reference(c.get_center_of_mass())),u.MathLibrary.inverse_transform_location(frame.current,c.get_center_of_mass()).to_tuple())
 u.SystemLibrary.execute_console_command(G.P.STATE['world'],'t.MaxFPS 20',pc)
 S.update(start=time.perf_counter(),context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text()),name=name,bag=bag,samples=[],checks=[])
 def diagnostic(phase):
  rec=frame.prop_records.get(name)
  return dict(phase=phase,registered=rec is not None,held=G.S.get('held'),world_com=list(c.get_center_of_mass().to_tuple()),
   native_local=list(u.MathLibrary.inverse_transform_location(frame.current,c.get_center_of_mass()).to_tuple()),
   pawn_local=list(G.source(frame.reference(pawn.get_actor_location()))),carrier=list(rec['carrier_velocity'].to_tuple()) if rec else None,
   velocity_mode=rec.get('velocity_space') if rec else None,physics_dt=frame.physics_dt,motion_dt=frame.motion_dt)
 original_refresh=frame.refresh_props;original_props=frame._props
 def refresh(*args,**kwargs):
  before=diagnostic('refresh_before');out=original_refresh(*args,**kwargs)
  if before['registered'] and name not in frame.prop_records:S.setdefault('registry_diagnostics',[]).extend([before,diagnostic('refresh_after')])
  return out
 def props(*args,**kwargs):
  before=diagnostic('props_before');out=original_props(*args,**kwargs)
  if before['registered'] and name not in frame.prop_records:S.setdefault('registry_diagnostics',[]).extend([before,diagnostic('props_after')])
  return out
 frame.refresh_props=refresh;frame._props=props
 S['handle']=u.register_slate_post_tick_callback(tick)
