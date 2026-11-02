"""Interactive artistic impact sandbox using actual native rigid-body contact.
P: launch aircraft, T: switch tower, click: local panel damage, V: view, R: reset.
"""
import unreal as u,time,json,hashlib,random,math,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[4]/'TwinTowers';AIR=R.parent/'SkywardAir';S={};CFG=json.loads((R/'DamageSettings.json').read_text());COMMAND=u.SystemLibrary.get_command_line();AUTO='-TwinTowersImpactTest' in COMMAND
def key(n):k=u.Key();k.import_text(n);return k
KEYS={n:key(n) for n in ('P','T','V','R','LeftMouseButton')}
def log(s):u.log('TOWER_DAMAGE '+s)
def save():
 (R/'ArtBible'/('ImpactTest.json' if AUTO else 'DamageSession.json')).write_text(json.dumps(S['report'],indent=2))
def register_check(name,passed,**facts):S['report']['checks'].append(dict(test=name,passed=bool(passed),**facts));save()
def spawn(cls,pos,rot=None):
 raise RuntimeError('Runtime uses native actors pre-pooled in the damage map')
def camera(name,p,t,fov=56):
 a=next(a for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.CameraActor) if a.get_actor_label()==name);a.set_actor_location(p,False,True);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,t),False);a.camera_component.set_field_of_view(fov);return a
def mesh_actor(name,mesh,pos,rot=None,physics=False):
 a=S['pool'][S['pool_index']%len(S['pool'])];S['pool_index']+=1;c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_location(pos,False,True);a.set_actor_rotation(rot or u.Rotator(),False);c.set_static_mesh(mesh);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True)
 if physics:
  c.set_collision_profile_name('PhysicsActor');c.set_simulate_physics(True);c.set_mass_override_in_kg(u.Name('None'),CFG['debris_game_mass_kg'],True);c.set_linear_damping(.12);c.set_angular_damping(.22)
 else:c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
 return a
def target_data():
 return ('North',-4200,-1230,17800) if S['target']=='North' else ('South',4200,7570,17800)
def damage(tower,point,secondary=False):
 # A bounded game panel graph loses local health and support links. Its units
 # and thresholds are artistic tuning; there is no engineering stress model.
 radius=CFG['damage_radius_cm']*(1.13 if secondary else 1);n=5;cells=[];rng=random.Random(247+(1 if secondary else 0))
 for row in range(-n,n+1):
  for col in range(-n,n+1):
   x=col*CFG['panel_size_cm'];z=row*CFG['panel_size_cm'];d=math.hypot(x,z)
   if d>radius:continue
   code=f'{tower}:{round((point.x+x)/CFG["panel_size_cm"])}:{round((point.z+z)/CFG["panel_size_cm"])}'
   old=S['panels'].get(code,dict(health=100,support=1,detached=False));loss=max(0,100*(1-d/radius)+65);old['health']=max(0,old['health']-loss);old['support']=0 if old['health']<=0 else .5
   if not old['detached'] and old['health']<=0:old['detached']=True;cells.append((code,x,z))
   S['panels'][code]=old
 for mid in S['mids'][tower]:
  mid.set_vector_parameter_value('DamageCentre',u.LinearColor(point.x,point.y,point.z,1));mid.set_scalar_parameter_value('DamageRadius',radius);mid.set_scalar_parameter_value('DamageActive',1)
 spawned=[]
 for j,(code,dx,dz) in enumerate(cells[:CFG['debris_count_limit']]):
  p=point+u.Vector(dx,140+rng.uniform(20,150),dz-150);piece=mesh_actor('Detached '+code,S['debris_meshes'][j%len(S['debris_meshes'])],p,u.Rotator(pitch=rng.uniform(-25,25),yaw=rng.uniform(-20,20),roll=rng.uniform(-20,20)),True);c=piece.static_mesh_component
  c.set_physics_linear_velocity(u.Vector(rng.uniform(-500,500),CFG['debris_outward_speed_cm_s']*rng.uniform(.7,1.2),rng.uniform(-100,350)),False);c.set_physics_angular_velocity_in_degrees(u.Vector(rng.uniform(-120,120),rng.uniform(-120,120),rng.uniform(-90,90)),False)
  S['debris'].append(dict(actor=piece,start_z=p.z,start=list(p.to_tuple())));spawned.append(code)
 S['report']['damage_events'].append(dict(tower=tower,point_cm=list(point.to_tuple()),radius_cm=radius,detached_cells=spawned,secondary=secondary));save();return len(spawned)
def launch():
 if S.get('aircraft'):return
 tower,x,y,z=target_data();start=u.Vector(x,y+30000,z);body=S['plane_body'];c=body.static_mesh_component;c.set_simulate_physics(False);c.set_collision_profile_name('PhysicsActor');body.set_actor_enable_collision(True);c.set_visibility(False);c.set_cast_shadow(False);visuals=S['plane_visuals']
 for a in visuals:a.set_actor_hidden_in_game(False)
 body.set_actor_rotation(u.Rotator(yaw=180),False);body.set_actor_location(start,False,True);c.set_notify_rigid_body_collision(True);c.set_enable_gravity(False);c.set_simulate_physics(True);c.set_mass_override_in_kg(u.Name('None'),CFG['aircraft_game_mass_kg'],True);c.set_linear_damping(.01);c.set_angular_damping(.15)
 if hasattr(c,'set_use_ccd'):c.set_use_ccd(True)
 S.update(aircraft=body,visuals=visuals,flight_started=time.monotonic(),plane_start=list(start.to_tuple()),last_plane=start);c.set_physics_linear_velocity(u.Vector(0,-CFG['aircraft_speed_cm_s'],0),False)
 S['report']['aircraft']=dict(mesh='Existing detailed SkywardAir exterior',visual_actors=len(visuals),collision='Compound convex aircraft proxy',start_cm=list(start.to_tuple()),velocity_cm_s=[0,-CFG['aircraft_speed_cm_s'],0],game_mass_kg=CFG['aircraft_game_mass_kg']);save()
def shot(tag):
 p=R/'Screenshots'/('Damage_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'Shot filename="'+str(p).replace('\\','/')+'" -nosuffix',S['pc']);S['shots_wait'].append(dict(file=p.name,tag=tag,started=time.time()));log('Screenshot '+tag)
def reset_damage():
 for a in S.get('plane_visuals',[]):a.set_actor_hidden_in_game(True)
 for a in S['pool']:
  a.static_mesh_component.set_simulate_physics(False);a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
 if S.get('aircraft'):S['aircraft'].static_mesh_component.set_simulate_physics(False);S['aircraft'].set_actor_enable_collision(False)
 for mids in S['mids'].values():
  for m in mids:m.set_scalar_parameter_value('DamageActive',0)
 S.update(aircraft=None,visuals=[],debris=[],panels={},impact=False,secondary=False,pending_hit=None,pool_index=0)
def start():
 S.update(after=time.monotonic()+20,phase='init',target='North',panels={},debris=[],mids={'North':[],'South':[]},shots_wait=[],report=dict(status='RUNNING' if AUTO else 'INTERACTIVE',method='Native rigid-body aircraft collision and gravity/rotation of detached game facade pieces. Local panel-health/support graph, bounded material cutaway. Not a measured structural simulation.',checks=[],damage_events=[],captures=[],tower_source_sha256=hashlib.sha256((R/'TwinTowers.blend').read_bytes()).hexdigest(),damage_asset_sha256=hashlib.sha256((R/'DamageAssets.blend').read_bytes()).hexdigest(),settings=CFG))
 def tick(dt):
  now=time.monotonic()
  if now<S['after']:return
  try:
   if S['phase']=='init':
    for w in u.ObjectIterator():
     if isinstance(w,u.World):
      pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_pawn(w,0) if pc else None
      if pc and pawn:S.update(world=w,pc=pc,pawn=pawn);break
    if not S.get('pc'):return
    actors=u.GameplayStatics.get_all_actors_of_class(S['world'],u.StaticMeshActor)
    S['pool']=sorted([a for a in actors if a.get_actor_label().startswith('DamagePool ')],key=lambda a:a.get_actor_label());S['pool_index']=0;assert len(S['pool'])==128,'Expected 128 pooled debris actors; found '+str(len(S['pool']));S['plane_body']=next(a for a in actors if a.get_actor_label()=='Unmanned aircraft rigid body');S['plane_visuals']=[a for a in actors if a.get_actor_label().startswith('Aircraft visual ')]
    for a in actors:
     label=a.get_actor_label();tower='North' if 'North' in label else 'South' if 'South' in label else None
     if not tower:continue
     c=a.static_mesh_component
     for k in range(c.get_num_materials()):S['mids'][tower].append(c.create_dynamic_material_instance(k))
    S['debris_meshes']=[u.load_asset('/Game/TwinTowers/Damage/Meshes/SM_TT_Debris_'+str(k)) for k in range(5)];assert all(S['debris_meshes'])
    _,x,y,z=target_data();S['impact_view']=camera('CAM_Damage_Impact',u.Vector(x+14000,y+23000,z+5000),u.Vector(x,y,z),58);S['overview']=next(a for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.CameraActor) if a.get_actor_label()=='CAM_TT_Hero');S['pc'].set_view_target_with_blend(S['impact_view'],0)
    for c in ('r.ScreenPercentage 125','r.TemporalAASamples 16','r.MotionBlurQuality 0','t.MaxFPS 60'):u.SystemLibrary.execute_console_command(S['world'],c,S['pc'])
    register_check('Both towers expose independent damage material instances',all(S['mids'][q] for q in ('North','South')),north=len(S['mids']['North']),south=len(S['mids']['South']));S.update(phase='hero' if AUTO else 'interactive',after=now+3)
    if not AUTO:u.SystemLibrary.print_string(S['world'],'P: launch aircraft | T: switch tower | Click: panel damage | V: view | R: reset',True,False,u.LinearColor(1,.9,.6,1),120)
   for q in list(S['shots_wait']):
    p=R/'Screenshots'/q['file']
    if p.exists() and p.stat().st_mtime>=q['started'] and p.stat().st_size>5000:S['report']['captures'].append(dict(file=p.name,tag=q['tag'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S['shots_wait'].remove(q);save()
   if S.get('aircraft') and not S.get('impact'):
    body=S['aircraft'];p=body.get_actor_location();velocity=body.static_mesh_component.get_physics_linear_velocity();travel=(p-u.Vector(*S['plane_start'])).length()
    if travel>25000 and velocity.y>-CFG['aircraft_speed_cm_s']*.65:
     hit=u.SystemLibrary.line_trace_single(S['world'],p,p+u.Vector(0,-4500,0),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[body],u.DrawDebugTrace.NONE,True)
     if hit:
      values=hit.to_tuple();a=values[9]
      if values[0] and a and any(t in a.get_actor_label() for t in ('North','South')):S['pending_hit']=(a,values[5],velocity)
   if S.get('pending_hit') and not S.get('impact'):
    other,p,impulse=S.pop('pending_hit');tower='North' if 'North' in other.get_actor_label() else 'South';S.update(impact=True,impact_time=now,impact_point=p,impact_tower=tower);S['aircraft'].static_mesh_component.set_enable_gravity(True);n=damage(tower,p)
    register_check('Native aircraft contact damages the struck tower',n>0,other_actor=other.get_actor_label(),contact_cm=list(p.to_tuple()),velocity_at_contact_cm_s=list(impulse.to_tuple()) if impulse is not None else None,contact_method='Native rigid-body slowdown plus matching tower surface trace',detached=n);S['report']['impact_time_s']=now-S['flight_started'];shot('02_Impact');S.update(phase='impact_wait' if AUTO else 'interactive',after=now+.10)
   if S.get('impact') and not S.get('secondary') and now-S['impact_time']>CFG['progressive_damage_delay_s']:
    S['secondary']=True;damage(S['impact_tower'],S['impact_point'],True)
   phase=S['phase']
   if phase=='hero':S['pc'].set_view_target_with_blend(S['overview'],0);S.update(phase='hero_shot',after=now+3)
   elif phase=='hero_shot':shot('Overview');S.update(phase='hero_wait',after=now+.5)
   elif phase=='hero_wait' and not S['shots_wait']:S['pc'].set_view_target_with_blend(S['impact_view'],0);S.update(phase='before',after=now+3)
   elif phase=='before':shot('00_Before');S.update(phase='launch_wait',after=now+.5)
   elif phase=='launch_wait' and not S['shots_wait']:launch();S.update(phase='flight',after=now+1.3)
   elif phase=='flight':
    if not S.get('approach_photo'):shot('01_Approach');S['approach_photo']=True
    if now-S['flight_started']>14 and not S.get('impact'):raise RuntimeError('Aircraft did not make native contact within the test window')
   elif phase=='impact_wait' and now-S['impact_time']>1.2:shot('03_Detached_Debris');S.update(phase='settle',after=now+8)
   elif phase=='settle':
    shot('04_After');moved=[d for d in S['debris'] if d['start_z']-d['actor'].get_actor_location().z>1000];simulated=[d for d in S['debris'] if d['actor'].static_mesh_component.is_simulating_physics()]
    register_check('Detached pieces use native rigid-body simulation',len(simulated)==len(S['debris']) and len(simulated)>0,count=len(simulated));register_check('Gravity moves debris downward after contact',len(moved)>len(S['debris'])*.5,dropped_more_than_10m=len(moved),total=len(S['debris']));register_check('Native aircraft moved before impact',(S['aircraft'].get_actor_location()-u.Vector(*S['plane_start'])).length()>10000)
    S['report']['debris_samples']=[dict(start_cm=d['start'],end_cm=list(d['actor'].get_actor_location().to_tuple()),velocity_cm_s=list(d['actor'].static_mesh_component.get_physics_linear_velocity().to_tuple())) for d in S['debris'][:8]];S.update(phase='finish',after=now+3)
   elif phase=='finish' and not S['shots_wait']:
    S['report']['status']='SUCCESS' if all(q['passed'] for q in S['report']['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
   elif phase=='interactive':
    pc=S['pc']
    if pc.was_input_key_just_pressed(KEYS['P']):launch()
    if pc.was_input_key_just_pressed(KEYS['T']):
     S['target']='South' if S['target']=='North' else 'North';_,x,y,z=target_data();p=u.Vector(x+14000,y+23000,z+5000);S['impact_view'].set_actor_location(p,False,True);S['impact_view'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(x,y,z)),False);u.SystemLibrary.print_string(S['world'],'Target: '+S['target'],True,False,u.LinearColor(1,.8,.2,1),3)
    if pc.was_input_key_just_pressed(KEYS['V']):S['view_index']=(S.get('view_index',0)+1)%3;pc.set_view_target_with_blend([S['impact_view'],S['overview'],S['pawn']][S['view_index']],.3)
    if pc.was_input_key_just_pressed(KEYS['R']):reset_damage()
    if pc.was_input_key_just_pressed(KEYS['LeftMouseButton']):
     cm=u.GameplayStatics.get_player_camera_manager(S['world'],0);p=cm.get_camera_location();d=u.MathLibrary.get_forward_vector(cm.get_camera_rotation());hit=u.SystemLibrary.line_trace_single(S['world'],p,p+d*150000,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[S['pawn']],u.DrawDebugTrace.NONE,True)
     if hit:
      v=hit.to_tuple();a=v[9]
      if v[0] and a and any(t in a.get_actor_label() for t in ('North','South')):damage('North' if 'North' in a.get_actor_label() else 'South',v[5])
  except Exception as e:
   S['report'].update(status='FAILED',error=traceback.format_exc());save();log('FAILED '+str(e));u.unregister_slate_post_tick_callback(S['handle'])
   if AUTO and S.get('pc'):u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
 S['handle']=u.register_slate_post_tick_callback(tick);save()
