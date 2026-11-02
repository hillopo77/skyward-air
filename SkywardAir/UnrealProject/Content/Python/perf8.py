"""Force-driven Chaos rigid bodies and breakable structural joints.

An activation window changes intact instanced geometry into equivalent connected
dynamic bodies before contact. Only Chaos breaks the joints during flight.
There is no contact-mask removal, timed breakup or prescribed debris velocity.
"""
import unreal as u,json,time,math,random,hashlib,traceback,copy
from pathlib import Path
import flight5 as view
from flight_layout5 import layout,rotate
R=Path(__file__).resolve().parents[4]/'TwinTowers';D=json.loads((R/'Exports/force_manifest6.json').read_text());S={};view.S=S;view.D=D;AUTO='-Force8Test' in u.SystemLibrary.get_command_line();QUICK='-Force8Quick' in u.SystemLibrary.get_command_line();HEADLESS='-Force8Headless' in u.SystemLibrary.get_command_line();NONE=u.Name('None')
CFG=dict(facade_mass_kg=60,deck_mass_kg=1100,facade_bond_force=2.0e6,facade_boundary_force=1.0e7,deck_bond_force=1.2e7,deck_boundary_force=2.0e7,physics_substep_s=1/120,activation_half_width_cm=2650,activation_half_height_cm=1450,initial_speed_cm_s=8000)
MASS={'Flightdeck':4000,'Nose':3500,'Forward':6500,'Midbody':8500,'Aft':6000,'TailBody':2500,'TailSurfaces':1800,'WingLInner':3500,'WingRInner':3500,'WingLOuter':1200,'WingROuter':1200,'EngineL':1800,'EngineR':1800}
PAIR=[('Nose','Flightdeck',3e5),('Flightdeck','Forward',4e5),('Forward','Midbody',5e5),('Midbody','Aft',5e5),('Aft','TailBody',3e5),('TailBody','TailSurfaces',1.5e5),('Midbody','WingLInner',2e5),('Midbody','WingRInner',2e5),('WingLInner','WingLOuter',8e4),('WingRInner','WingROuter',8e4),('WingLInner','EngineL',1.2e5),('WingRInner','EngineR',1.2e5)]
KEYS={n:view.key(n) for n in ('SpaceBar','P','T','R','V','A','D','W','S','Q','E','F','LeftShift','LeftControl')};BLOCK=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('block'))
def save():(R/'ArtBible'/('RigidHeadless8.json' if HEADLESS else 'RigidTest8.json' if AUTO else 'RigidSession8.json')).write_text(json.dumps(S['report'],indent=2))
view.save=save
def check(name,passed,**data):S['report']['checks'].append(dict(test=name,passed=bool(passed),**copy.deepcopy(data)));save()
def shot(tag):
 if HEADLESS:return
 p=R/'Screenshots'/('Rigid8_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'HighResShot 1600x1000 filename="'+str(p).replace('\\','/')+'"',S['pc']);S['shots'].append(dict(file=p.name,tag=tag,started=time.time()))
def mesh(aid):
 if aid not in S['meshes']:S['meshes'][aid]=u.load_asset(D.get('native_mesh_overrides',{}).get(aid) or (D['flight_asset_root'] if aid in D['flight_assets']['assets'] else '/Game/TwinTowers/Quality3/Meshes/' if aid.startswith('SM_Q3') else '/Game/TwinTowers/Damage2/Meshes/')+aid)
 return S['meshes'][aid]
def collider(a,mass,kind):
 c=a.static_mesh_component;a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');c.set_collision_object_type(u.CollisionChannel.ECC_VEHICLE if kind=='air' else u.CollisionChannel.ECC_DESTRUCTIBLE)
 c.set_collision_response_to_all_channels(BLOCK)
 if kind=='air':c.set_collision_response_to_channel(u.CollisionChannel.ECC_VEHICLE,view.IGNORE)
 else:
  # Adjacent convex approximations of interlocking cut edges overlap. While the
  # structure is supported, its native joints transfer load and self-contact is
  # filtered. Unsupported groups regain debris and static-world contact.
  c.set_collision_response_to_channel(u.CollisionChannel.ECC_DESTRUCTIBLE,view.IGNORE);c.set_collision_response_to_channel(u.CollisionChannel.ECC_WORLD_STATIC,view.IGNORE)
 c.set_mobility(u.ComponentMobility.MOVABLE);bi=c.get_editor_property('body_instance');bi.set_editor_property('position_solver_iteration_count',8);bi.set_editor_property('velocity_solver_iteration_count',2);c.set_enable_gravity(kind=='air');c.set_simulate_physics(True);c.set_mass_override_in_kg(NONE,mass,True);c.set_linear_damping(.015 if kind=='air' else .04);c.set_angular_damping(.14);c.set_use_ccd(kind=='air');c.set_physics_max_angular_velocity_in_radians(12,False)
 if kind!='air':c.set_physics_linear_velocity(u.Vector(),False);c.set_physics_angular_velocity_in_radians(u.Vector(),False);c.set_collision_profile_name('CrashSupport8')
 return c
def _joint_physics(a,b,point,threshold,kind,key):
 if S.get('defer_joints'):
  S['pending_joints'].append((a,b,point,threshold,kind,key));return
 assert S['free_joints'],'Native joint pool exhausted';unused_actor=S['free_joints'].pop();actor=spawn_joint8(point);S['joint_index']+=1;c=actor.get_component_by_class(u.PhysicsConstraintComponent);actor.set_actor_location(point,False,True)
 c.set_linear_x_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_y_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_z_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_angular_swing1_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_angular_swing2_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_angular_twist_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_linear_breakable(True,threshold);c.set_angular_breakable(True,threshold*200);c.set_projection_enabled(False);c.set_disable_collision(True);c.set_constrained_components(a.static_mesh_component,NONE,(b or S['anchor']).static_mesh_component,NONE);q=dict(actor=actor,component=c,a=a,b=b,kind=kind,key=key,threshold=threshold,broken=False,bound_at=time.monotonic(),profile_reapplied=False);S['joints'].append(q);return q
def centre(q):b=q['bounds'];return u.Vector((b[0]+b[1])/2,(b[2]+b[3])/2,(b[4]+b[5])/2)
def activate(q):
 if q.get('active'):return
 assert len(S['active'])<len(S['body_pool']),'Native facade pool exhausted';a=S['body_pool'][len(S['active'])];c=a.static_mesh_component;c.set_static_mesh(None);c.set_static_mesh(mesh(q['asset']));a.set_actor_transform(view.transform(q),False,True);a.set_actor_hidden_in_game(False);collider(a,CFG['deck_mass_kg'] if q['kind']=='roof' else CFG['facade_mass_kg'],'wall');q['component'].update_instance_transform(q['index'],u.Transform(location=u.Vector(0,0,-100000)),False,False,True);S['render_dirty'][id(q['component'])]=(q['component'],q);q.update(active=True,actor=a);S['active'].append(q)
 if q['kind']=='facade':
  c.set_forced_lod_model(2)
  for i in range(len(c.static_mesh.static_materials)):c.set_material(i,S['surface_materials'][q['tower']])
 else:
  c.set_forced_lod_model(0)
  for i,slot in enumerate(c.static_mesh.static_materials):c.set_material(i,slot.material_interface)
def flush_instances():
 for c,q in S['render_dirty'].values():c.update_instance_transform(q['index'],u.Transform(location=u.Vector(0,0,-100000)),False,True,True)
 S['render_dirty']={}
def predict(point,direction):
 best=None
 for t in D['towers']:
  c=u.Vector(t['centre'][0]*100,-t['centre'][1]*100,0);bounds=[c.x-3185,c.x+3185,c.y-3185,c.y+3185,0,t['height']*100];p=point.to_tuple();v=direction.to_tuple();lo=0;hi=120000;side=0
  for axis in range(3):
   if abs(v[axis])<1e-6:
    if not bounds[axis*2]<=p[axis]<=bounds[axis*2+1]:hi=-1;break
   else:
    a=(bounds[axis*2]-p[axis])/v[axis];b=(bounds[axis*2+1]-p[axis])/v[axis];near=min(a,b)
    if near>lo:lo=near;side=(3 if v[0]>0 else 1) if axis==0 else (2 if v[1]>0 else 0) if axis==1 else 4
    hi=min(hi,max(a,b))
  if hi>=lo and hi>0 and (best is None or lo<best[0]):best=(lo,t,point+direction*lo,side)
 return best
def _reset_physics():
 for q in S.get('joints',[]):
  c=q['component'];c.break_constraint()
 for a in S.get('body_pool',[])+S.get('deck_pool',[]):
  c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);c.set_collision_profile_name('NoCollision');a.set_actor_hidden_in_game(True);a.set_actor_location(u.Vector(0,0,-90000),False,True)
 for q in S.get('active',[]):q['component'].update_instance_transform(q['index'],view.transform(q),False,True,True);q['active']=False
 root=S['carrier'];root.set_actor_rotation(u.Rotator(),False);root.set_actor_location(u.Vector(),False,True)
 for p in S['parts']:
  a=p['actor'];c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(False);c.set_collision_profile_name('NoCollision');a.set_actor_rotation(u.Rotator(),False);o=p['origin'];a.set_actor_location(u.Vector(o[0]*100,-(o[1]-17.3)*100,o[2]*100),False,True);view.attached(a,root);p['released']=False
 for item in S['rig_original']:
  a=item['actor'];a.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);a.set_actor_location(item['local'],False,True);a.set_actor_rotation(item['rotation'],False);view.attached(a,root)
 for q in S['dust']:q['actor'].set_actor_hidden_in_game(True);q['mid'].set_scalar_parameter_value('Opacity',0)
 for q in S['fine']:
  q['actor'].set_actor_hidden_in_game(True)
  for mid in q['mids']:mid.set_scalar_parameter_value('SimTime',-100)
 S.update(joints=[],joint_index=0,free_joints=list(reversed(S['joint_pool'])),active=[],render_dirty={},flying=False,launched=False,impact_time=None,dust_start=None,fx_sources=[],last_poll=0,broken_air=0,broken_wall=0,pending_joints=[],defer_joints=False,assembly_ready=False)
def _ready_physics(preset=0,speed=8000,offset=0,angle=0,roof=False):
 reset();S['preset']=preset%3;spec=next(t for t in D['towers'] if t['tower']==('South' if preset%3==1 else 'North'));side=1 if preset%3==1 else 0;heading=(180 if side==1 else -90)+angle;rad=math.radians(heading);f=u.Vector(math.cos(rad),math.sin(rad),0);x,y=rotate(offset,3185,side);point=u.Vector(spec['centre'][0]*100+x,-spec['centre'][1]*100+y,22000 if side==1 else 17800 if preset%3==0 else 28000);root=S['carrier'];root.set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,u.Vector(0,0,1)),False);root.set_actor_location(point-f*(speed*5+2730),False,True);S.update(heading=heading,pitch=0,bank=0,speed=speed,flight_elapsed=0,view=0,look_yaw=0,look_pitch=0,target=spec['tower'],start_location=root.get_actor_location(),peak_force={},peak_deceleration=0,samples=[])
 if roof:
  S['pitch']=-90;f,up=view.attitude();point=u.Vector(spec['centre'][0]*100+2000,-spec['centre'][1]*100+1600,spec['height']*100);root.set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,up),False);root.set_actor_location(point-f*(speed*5+2730),False,True);S['start_location']=root.get_actor_location()
 hit=predict(root.get_actor_location()+f*2730,f);assert hit,'No structure ahead of approach';prepare_structure(hit);S['pc'].set_view_target_with_blend(S['flight_cams'][0],0);camera_tick(.016);S['report']['ready']=dict(preset=preset,speed_m_s=speed/100,target=spec['tower'],angle_degrees=angle,offset_m=offset/100,roof=roof);save()
def clamp(v,maximum):n=v.length();return v if n<=maximum or n<1e-8 else v*(maximum/n)
def opening():
 p=S.get('contact_point',S['predicted_point']);side=S.get('contact_side',S['predicted_side']);dx,dy=rotate(0,1,side%4);rx,ry=rotate(1,0,side%4);normal=u.Vector(0,0,1) if side==4 else u.Vector(dx,dy,0);right=u.Vector(1,0,0) if side==4 else u.Vector(rx,ry,0);up=u.Vector(0,1,0) if side==4 else u.Vector(0,0,1);ignored=[S['carrier'],S['pawn']]+([S['air_core']] if S.get('air_core') else [])+[q['actor'] for q in S['parts']]+S['rig'];rays=[]
 for x in (-700,-350,0,350,700):
  for z in (-170,0,170):
   centre=p+right*x+up*z;h=u.SystemLibrary.line_trace_single(S['world'],centre+normal*500,centre-normal*1200,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,u.DrawDebugTrace.NONE,True);v=h.to_tuple() if h else None;rays.append(dict(blocking=bool(v and v[0]),actor=v[9].get_actor_label() if v and v[9] else None))
 return dict(clear=sum(not q['blocking'] for q in rays),total=len(rays),rays=rays)
def _impact_physics(now):
 if S.get('impact_time') or not S['launched']:return
 # Choose an actually moving structural body; this is effect placement only.
 q=max(S['active'],key=lambda q:q['actor'].static_mesh_component.get_physics_linear_velocity().length());p,e=q['actor'].get_actor_bounds(False);S.update(impact_time=now,contact_point=p,contact_side=q.get('side',S['predicted_side']),flying=False);view.burst(p);S['fx_sources']=[a['actor'].get_actor_location() for a in S['active'] if a['actor'].static_mesh_component.get_physics_linear_velocity().length()>100]
 side=S['contact_side']%4
 for fx in S['dust']:
  off=fx['offset'];v=fx['velocity'];x,y=rotate(off.x,off.y,side);vx,vy=rotate(v.x,v.y,side);fx['offset']=u.Vector(x,y,off.z);fx['velocity']=u.Vector(vx,vy,v.z)
 view.set_impact_camera(p,side);S['pc'].set_view_target_with_blend(S['flight_cams'][2],.15);S['view']=2;S['report']['first_physics_failure']=dict(time_after_launch_s=S['flight_elapsed'],point_cm=list(p.to_tuple()),face=S['contact_side'],tower=q['tower'],native_wall_bonds_broken=S['broken_wall'],native_air_joints_broken=S['broken_air'],aircraft_velocity_cm_s=list(S['air_core'].static_mesh_component.get_physics_linear_velocity().to_tuple()));save()
def update_support():
 graph={};supported=set()
 for q in S['joints']:
  if q['kind']=='air' or q['broken']:continue
  a,b=q['a'],q['b']
  if b is None:supported.add(a)
  else:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
 queue=list(supported)
 while queue:
  for b in graph.get(queue.pop(),()):
   if b not in supported:supported.add(b);queue.append(b)
 for a in [q['actor'] for q in S['active']]+S.get('active_decks8',[]):
  if a not in supported:
   c=a.static_mesh_component;c.set_collision_response_to_channel(u.CollisionChannel.ECC_WORLD_STATIC,BLOCK);c.set_collision_response_to_channel(u.CollisionChannel.ECC_DESTRUCTIBLE,BLOCK);c.set_forced_lod_model(1)
   for i,slot in enumerate(c.static_mesh.static_materials):c.set_material(i,slot.material_interface)
 S['report']['unsupported_bodies']=sum(a not in supported for a in [q['actor'] for q in S['active']]+S.get('active_decks8',[]))
def _snapshot7():
 return dict(tower=S['predicted_tower'],speed_m_s=S['report']['launch']['speed_m_s'],ready=S['report']['ready'],broken_wall_bonds=S['broken_wall'],broken_air_joints=S['broken_air'],initial_energy_j=S['initial_energy'],minimum_translational_energy_j=S['minimum_energy'],energy_ratio=S['minimum_energy']/S['initial_energy'],peak_constraint_force=S['peak_force'],failure=S['report'].get('first_physics_failure'),opening=opening(),samples=S['samples'],active_body_count=len(S['active'])+len(S['deck_pool']),joints=len(S['joints']),native_break_events=list(S['report'].get('native_break_events',[])))
CASES=[dict(name='Fast_Front',preset=0,speed=8000,offset=0,angle=0),dict(name='Slow_Front',preset=0,speed=2000,offset=0,angle=0),dict(name='Angled_Offset',preset=0,speed=8000,offset=1000,angle=9),dict(name='South_Side',preset=1,speed=8000,offset=0,angle=0),dict(name='Steered',preset=0,speed=8000,offset=0,angle=0,steer=True),dict(name='Roof',preset=2,speed=4000,offset=0,angle=0,roof=True)]
def _initialize_physics(now):
 for w in u.ObjectIterator():
  if isinstance(w,u.World):
   pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_pawn(w,0) if pc else None
   if pc and pawn:S.update(world=w,pc=pc,pawn=pawn);break
 if not S.get('pc'):return False
 S['pawn'].disable_input(S['pc']);S['pc'].set_editor_property('show_mouse_cursor',False);actors=u.GameplayStatics.get_all_actors_of_class(S['world'],u.Actor);by={a.get_actor_label():a for a in actors};S['carrier']=by['Unmanned aircraft carrier2'];S['parts']=[dict(p,actor=by['AirPart '+p['part']],released=False) for p in D['aircraft']];S['nose']=by['AirPart Nose'];S['rig']=[a for a in actors if a.get_actor_label().startswith('Cockpit5 ')];root=S['carrier'].get_actor_location();S['rig_original']=[dict(actor=a,local=a.get_actor_location()-root,rotation=a.get_actor_rotation()) for a in S['rig']];S['body_pool']=sorted([a for a in actors if a.get_actor_label().startswith('BreakPool5 ')],key=lambda a:a.get_actor_label());S['deck_pool']=sorted([a for a in actors if a.get_actor_label().startswith('Deck5 ')],key=lambda a:a.get_actor_label());S['joint_pool']=sorted([a for a in actors if a.get_actor_label().startswith('Joint6 ')],key=lambda a:a.get_actor_label());S['anchor']=next(a for a in actors if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name()=='SM_TT_Plaza');S.update(meshes={},asset_bounds={},grid={},cells=[],active=[],joints=[],render_dirty={})
 for spec in D['towers']:
  a=by['Structure5 '+spec['tower']];cs={str(t):c for c in a.get_components_by_class(u.InstancedStaticMeshComponent) for t in c.component_tags}
  for q in layout(spec,D['flight_assets']):
   q.update(component=cs[q['tag']],active=False);q['bounds']=view.bounds(q);S['cells'].append(q)
   for k in view.bins(q['bounds']):S['grid'].setdefault(k,[]).append(q)
 S['dust']=[dict(actor=a,bank=a.get_actor_label().split()[1],mid=a.static_mesh_component.create_dynamic_material_instance(0)) for a in actors if a.get_actor_label().startswith('FX3 ')];S['fine']=[dict(actor=a,mids=[a.static_mesh_component.create_dynamic_material_instance(i) for i in range(2)]) for a in actors if a.get_actor_label().startswith('FineBatch4 ')]
 for q in S['dust']:
  c=q['actor'].static_mesh_component;c.set_visibility(True);c.set_hidden_in_game(False);c.set_render_in_main_pass(True)
 S['flight_cams']=[by['CAM_Flight5_'+tag] for tag in ('Pilot','Chase','Impact')]+[by['CAM_TT_Hero']];hero=S['flight_cams'][3];hp=u.Vector(-18000,95000,26500);hero.set_actor_location(hp,False,True);hero.set_actor_rotation(u.MathLibrary.find_look_at_rotation(hp,u.Vector(0,0,26500)),False)
 for cmd in ('r.ScreenPercentage 100','r.MotionBlurQuality 0','r.Tonemapper.Sharpen 0','t.MaxFPS 60'):u.SystemLibrary.execute_console_command(S['world'],cmd,S['pc'])
 S['surface_materials']={town:u.load_asset('/Game/TwinTowers/Flight5/Materials/MI_FlightFacade5_'+town) for town in ('North','South')};ready(0);S.update(initialized=True,test_phase='rest',test_after=time.monotonic()+3,case_index=0,test_flags=set(),last_tick=time.monotonic());check('Native force-body pools load',len(S['joint_pool'])==4096 and len(S['body_pool'])==1536 and len(S['parts'])==13,joints_available=len(S['joint_pool']),wall_bodies_available=len(S['body_pool']),active_wall_bodies=len(S['active']));return True
def _test_tick_physics(dt,now):
 phase=S['test_phase'];case=CASES[S['case_index']];prefix=f"{S['case_index']:02d}_{case['name']}_"
 if phase=='rest' and S.get('assembly_ready') and now>S['test_after']:
  displacement=max((q['actor'].get_actor_location()-u.Vector(*q['location'])).length() for q in S['active']);check(case['name']+': connected structure holds at rest',S['broken_wall']==0 and displacement<5,failed_without_impact=S['broken_wall'],maximum_displacement_cm=displacement,peak_constraint_force=S['peak_force']);S['case_rest_failures']=S['broken_wall']+(1 if displacement>=5 else 0);shot(prefix+'Ready');S.update(test_phase='ready_wait',test_after=now+.7)
 elif phase=='ready_wait' and now>S['test_after'] and not S['shots']:launch();S.update(test_phase='run',test_flags=set())
 elif phase=='run':
  t=S['flight_elapsed']
  if case.get('steer') and not S.get('impact_time'):view.steering(dt,.3 if .5<t<1.7 else -.3 if 1.7<t<2.9 else 0)
  if t>1.1 and 'chase' not in S['test_flags'] and not S['shots']:S['pc'].set_view_target_with_blend(S['flight_cams'][1],0);S['view']=1;S['test_flags'].add('chase');S['chase_after']=now+.5
  if 'chase' in S['test_flags'] and 'approach' not in S['test_flags'] and now>S['chase_after']:shot(prefix+'Approach');S['test_flags'].add('approach')
  if S.get('impact_time'):
   age=now-S['impact_time']
   if age>.45 and 'contact' not in S['test_flags'] and not S['shots']:shot(prefix+'Solver_Contact');S['test_flags'].add('contact')
   if age>3.2 and 'debris' not in S['test_flags'] and not S['shots']:shot(prefix+'Momentum_And_Failure');S['test_flags'].add('debris')
   if not QUICK and S['case_index']==0 and age>12 and 'smoke' not in S['test_flags'] and not S['shots']:shot(prefix+'Rising_Smoke');S['test_flags'].add('smoke')
   if age>(5 if QUICK else 13 if S['case_index']==0 else 9) and not S['shots']:S['test_phase']='case_verify'
  elif t>13:S['test_phase']='case_verify'
 elif phase=='case_verify':
  result=snapshot();result['case']=case['name'];result['rest_failures']=S['case_rest_failures'];S['report']['scenarios'].append(result);check(case['name']+': native constraints fail under collision',result['broken_wall_bonds']>0 and S['case_rest_failures']==0,result_summary={k:result[k] for k in ('broken_wall_bonds','broken_air_joints','energy_ratio','failure')});check(case['name']+': collision changes aircraft kinetic energy',result['energy_ratio']<.98,initial_energy_j=result['initial_energy_j'],minimum_translational_energy_j=result['minimum_translational_energy_j']);save()
  if QUICK or S['case_index']==len(CASES)-1:
   if not QUICK:
    first,slow,angled,side,steered,roof=S['report']['scenarios'][:6];check('Speed affects physical failure rather than stamping the same damage',first['broken_wall_bonds']!=slow['broken_wall_bonds'] or first['broken_air_joints']!=slow['broken_air_joints'],fast_wall_bonds=first['broken_wall_bonds'],slow_wall_bonds=slow['broken_wall_bonds'],fast_air_joints=first['broken_air_joints'],slow_air_joints=slow['broken_air_joints']);check('Offset and side approaches use their actual contact regions',angled['failure'] is not None and side['failure'] is not None and side['tower']=='South',offset_contact=angled['failure'],side_contact=side['failure']);early=[q for q in steered['native_break_events'] if q['kind']=='air' and q['sim_time_s']<3.8];check('Steering keeps the airframe intact before impact',not early,early_air_failures=early);check('Aircraft remains rigid through every collision',all(q['fuselage_rigid_error_cm']<.1 and q['broken_air_joints']==0 for q in S['report']['scenarios']),rigid_errors_cm=[q['fuselage_rigid_error_cm'] for q in S['report']['scenarios']]);check('Roof impact also uses native breakable structure',roof['failure'] is not None and roof['failure']['face']==4 and roof['broken_wall_bonds']>0,result=roof['failure'])
   S['report']['status']='SUCCESS' if all(q['passed'] for q in S['report']['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
  else:
   S['case_index']+=1;case=CASES[S['case_index']];S['report']['native_break_events']=[];S['report'].pop('first_physics_failure',None);ready(case['preset'],case['speed'],case['offset'],case['angle'],case.get('roof',False));S.update(test_phase='rest',test_after=time.monotonic()+3)

# Revision7 replaces per-frame constraint scans with native break notifications.
KEYS.update({n:view.key(n) for n in ('Tab','C','MouseScrollUp','MouseScrollDown','LeftAlt')})
def alive(a):
 try:return bool(a and u.SystemLibrary.is_valid(a))
 except Exception:return False
def joint(*args):
 q=_joint_physics(*args)
 if q is None:return
 generation=S.get('generation',0)
 def broken(_index):
  if generation==S.get('generation',0) and not q['broken']:S['break_queue'].append(q)
 q['callback']=broken;q['component'].on_constraint_broken.clear();q['component'].on_constraint_broken.add_callable(broken);S['profile_pending'].append(q);return q
def _reset7():
 S['generation']=S.get('generation',0)+1
 for q in S.get('joints',[]):
  if alive(q['component']):q['component'].on_constraint_broken.clear()
 S.update(break_queue=[],profile_pending=[],unsupported=set(),camera_configured=False,force_sample_cursor=0)
 _reset_physics()
def _ready7(*args,**kwargs):
 preserve=S.get('view')==3 and S.get('free_position') is not None;position=S.get('free_position');rotation=S.get('free_rotation');_ready_physics(*args,**kwargs);configure_cameras()
 if not AUTO:
  if preserve:enter_free(position,rotation)
  else:enter_free(S['flight_cams'][1].get_actor_location(),S['flight_cams'][1].get_actor_rotation())
def _impact7(now):
 free=S.get('view')==3;_impact_physics(now)
 if free:S['view']=3;S['pc'].set_view_target_with_blend(S['flight_cams'][3],0)
 # Fewer overlapping puffs retain the silhouette without the old overdraw cost.
 for i,q in enumerate(q for q in S['dust'] if q['bank']=='Smoke'):q['delay']=.5+i*.13
def _initialize7(now):
 ok=_initialize_physics(now)
 if not ok:return False
 ws=next(a for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.WorldSettings));ws.set_editor_property('enable_world_bounds_checks',False)
 for q in S['dust']:q['actor'].set_actor_hidden_in_game(True)
 dust=[q for q in S['dust'] if q['bank']=='Dust'];smoke=[q for q in S['dust'] if q['bank']=='Smoke'];S['dust']=dust[::3]+smoke[::3];S['report']['render_budget']=dict(dust_layers=len(dust[::3]),smoke_layers=len(smoke[::3]),fine_fragment_batches=len(S['fine']),screen_percentage=100)
 for p in S['parts']:p['actor'].static_mesh_component.set_bounds_scale(1.4)
 glass=u.load_asset('/Game/TwinTowers/Performance7/Materials/M_ClearFlightGlass7');removed=u.load_asset('/Game/TwinTowers/Performance7/Materials/M_RemovedPaneTrim7');assert glass and removed,'Clear glass materials missing; run build_clear_glass7.py'
 changed=[]
 for a in [q['actor'] for q in S['parts'] if q['part'] in ('Nose','Flightdeck')]+[a for a in S['rig'] if isinstance(a,u.StaticMeshActor) and 'CockpitShell' in a.get_actor_label()]:
  c=a.static_mesh_component
  for i,slot in enumerate(c.static_mesh.static_materials):
   name=str(slot.material_slot_name)+' '+(slot.material_interface.get_name() if slot.material_interface else '')
   if 'Windscreen' in name:c.set_material(i,glass);changed.append(dict(actor=a.get_actor_label(),slot=name,operation='clear glazing'))
   elif 'Seal08' in name:c.set_material(i,removed);changed.append(dict(actor=a.get_actor_label(),slot=name,operation='decorative pane lines removed'))
 S['report']['glass_changes']=changed
 S['report']['break_detection']='Native OnConstraintBroken multicast events; force telemetry is sampled, not scanned every frame.';S.update(perf_samples=[],tick_costs=[],frame_index=0,stats_at=time.monotonic())
 if AUTO:S.update(test_phase='camera_setup',test_after=time.monotonic()+2)
 return True
def configure_cameras():
 pilot,chase=S['flight_cams'][:2];nose=S['nose'];origin=next(p['origin'] for p in S['parts'] if p['part']=='Nose');offset=u.Vector(110,2054,160)-u.Vector(origin[0]*100,-(origin[1]-17.3)*100,origin[2]*100);view.attached(pilot,nose);pilot.set_actor_relative_location(offset,False,True);pilot.set_actor_relative_rotation(u.Rotator(yaw=90),False,True)
 main=next(p['actor'] for p in S['parts'] if p['part']=='Midbody');view.attached(chase,main);chase.set_actor_relative_location(u.Vector(0,-9500,2000),False,True);chase.set_actor_relative_rotation(u.Rotator(pitch=-12,yaw=90),False,True);S['camera_configured']=True
def camera_tick(dt):
 if not S.get('camera_configured'):return
 if S.get('view')==3:return
 yaw=math.radians(S['look_yaw']);pitch=math.radians(S['look_pitch']);f=u.Vector(-math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch));S['flight_cams'][0].set_actor_relative_rotation(u.MathLibrary.make_rot_from_xz(f,u.Vector(0,0,1)),False,True)
def enter_free(position=None,rotation=None):
 if position is None:
  manager=u.GameplayStatics.get_player_camera_manager(S['world'],0);position=manager.get_camera_location();rotation=manager.get_camera_rotation()
 cam=S['flight_cams'][3];cam.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);cam.set_actor_location(position,False,True);r=u.Rotator(pitch=max(-89,min(89,rotation.pitch)),yaw=rotation.yaw);cam.set_actor_rotation(r,False);cam.camera_component.set_field_of_view(86);S.update(view=3,free_position=position,free_rotation=r,free_speed=S.get('free_speed',6000));S['pc'].set_view_target_with_blend(cam,0)
def pilot_view():S['view']=0;S['look_yaw']=S['look_pitch']=0;S['pc'].set_view_target_with_blend(S['flight_cams'][0],0)
def spectator_tick(dt,forward=0,right=0,up=0,boost=False,mouse_x=0,mouse_y=0):
 r=S['free_rotation'];r=u.Rotator(pitch=max(-89,min(89,r.pitch+mouse_y*.18)),yaw=r.yaw+mouse_x*.18);direction=u.MathLibrary.get_forward_vector(r)*forward+u.MathLibrary.get_right_vector(r)*right+u.Vector(0,0,up);n=direction.length();direction=direction/max(1,n);speed=S['free_speed']*(3 if boost else 1);p=S['free_position']+direction*speed*dt;cam=S['flight_cams'][3];cam.set_actor_location(p,False,True);cam.set_actor_rotation(r,False);S.update(free_position=p,free_rotation=r)
def poll(now):
 if S['launched']:S['flight_elapsed']=u.GameplayStatics.get_time_seconds(S['world'])-S['launch_sim_time']
 queue=S['break_queue'];S['break_queue']=[];changed=False
 for q in queue:
  if q['broken'] or not alive(q['component']):continue
  if not q['component'].is_broken():S['report']['stale_native_events_ignored8']=S['report'].get('stale_native_events_ignored8',0)+1;continue
  q['broken']=True;changed=True
  if q['kind']=='air':S['broken_air']+=1
  else:S['broken_wall']+=1
  S['report'].setdefault('native_break_events',[]).append(dict(kind=q['kind'],key=q['key'],threshold=q['threshold'],sim_time_s=S.get('flight_elapsed',0),position_cm=list(q['actor'].get_actor_location().to_tuple()),native_is_broken=True,event_driven=True))
 pending=[]
 for q in S['profile_pending']:
  if now-q['bound_at']<.12:pending.append(q);continue
  if not q['broken'] and alive(q['component']):q['component'].set_linear_breakable(True,q['threshold']);q['component'].set_angular_breakable(True,q['threshold']*200)
 S['profile_pending']=pending
 if changed:update_support()
 if S['launched'] and S['broken_wall'] and not S.get('impact_time'):impact(now)
 if now-S.get('telemetry_at',0)>.25:
  S['telemetry_at']=now
  if S['launched']:
   ke=energy();S['minimum_energy']=min(S['minimum_energy'],ke);S['samples'].append(dict(t=S['flight_elapsed'],energy_j=ke,nose_speed_m_s=S['air_core'].static_mesh_component.get_physics_linear_velocity().length()/100,nose_position_cm=list(S['nose'].get_actor_location().to_tuple()),wall_bonds_broken=S['broken_wall'],air_joints_broken=S['broken_air']))
  joints=S['joints'];count=len(joints)
  for j in range(min(12,count)):
   q=joints[(S['force_sample_cursor']+j)%count]
   if not q['broken'] and alive(q['component']):linear,_=q['component'].get_constraint_force();S['peak_force'][q['kind']]=max(S['peak_force'].get(q['kind'],0),linear.length())
  S['force_sample_cursor']=(S['force_sample_cursor']+12)%max(1,count)
def update_support():
 graph={};supported=set()
 for q in S['joints']:
  if q['kind']=='air' or q['broken']:continue
  a,b=q['a'],q['b']
  if b is None:supported.add(a)
  else:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
 stack=list(supported)
 while stack:
  for b in graph.get(stack.pop(),()):
   if b not in supported:supported.add(b);stack.append(b)
 for a in [q['actor'] for q in S['active']]+S.get('active_decks8',[]):
  if a not in supported and a not in S['unsupported'] and alive(a):
   S['unsupported'].add(a);c=a.static_mesh_component;c.set_collision_profile_name('CrashFragment8');c.set_collision_response_to_all_channels(BLOCK);c.set_collision_response_to_channel(u.CollisionChannel.ECC_WORLD_STATIC,BLOCK);c.set_collision_response_to_channel(u.CollisionChannel.ECC_DESTRUCTIBLE,BLOCK);c.set_use_ccd(False);c.set_forced_lod_model(1)
   for i,slot in enumerate(c.static_mesh.static_materials):c.set_material(i,slot.material_interface)
 S['report']['unsupported_bodies']=len(S['unsupported'])
def hud():
 if S['view']==3:text=f"SPECTATOR | {S['free_speed']/100:.0f} m/s | WASD move | Mouse look | Space/E up | Ctrl/Q down\nShift boost | Wheel speed | Tab/C pilot | P launch | R reset"
 else:text='PILOT | Space/P fly | A/D turn | W/S pitch | Q/E rudder | Shift/Ctrl speed\nTab spectator | C pilot | V camera | F level | R reset'
 u.SystemLibrary.print_string(S['world'],text,True,False,u.LinearColor(.76,.92,1,1),.3,u.Name('FlightHUD'))
def _test_tick7(dt,now):
 phase=S['test_phase']
 if phase=='camera_setup':
  if not S.get('assembly_ready') or now<S['test_after']:return
  enter_free(S['flight_cams'][1].get_actor_location(),S['flight_cams'][1].get_actor_rotation());S.update(camera_start=S['free_position'],camera_started=now,test_phase='camera_move');return
 if phase=='camera_move':
  spectator_tick(dt,forward=1,up=1,boost=True,mouse_x=6)
  if now-S['camera_started']>1.2:
   travelled=(S['free_position']-S['camera_start']).length()/100;check('Spectator camera moves freely at boosted speed',travelled>100,distance_m=travelled,base_speed_m_s=60,boost_speed_m_s=180);check('Flight cameras share the rigid aircraft hierarchy',S['flight_cams'][0].get_attach_parent_actor()==S['nose'] and S['flight_cams'][1].get_attach_parent_actor().get_actor_label()=='AirPart Midbody');p=S['free_position'];r=u.MathLibrary.find_look_at_rotation(p,S['nose'].get_actor_location());S['free_rotation']=r;S['flight_cams'][3].set_actor_rotation(r,False);shot('Free_Spectator_Camera');S.update(test_phase='camera_wait',test_after=now+.6)
  return
 if phase=='camera_wait':
  if now>S['test_after'] and not S['shots']:pilot_view();S.update(test_phase='rest',test_after=now+1)
  return
 _test_tick_physics(dt,now)

# Rigid aircraft with incrementally prepared, force-driven tower connections.
BENCHMARK8='-Force8Benchmark' in u.SystemLibrary.get_command_line()
CFG.update(maximum_physics_step_s=1/30,maximum_substeps=1,maximum_physics_delta_s=1/30);CFG.pop('physics_substep_s',None)
CASES.append(dict(name='Pitch_Climb',preset=0,speed=8000,offset=0,angle=0,pitch_test=True))
if '-Force8PitchOnly' in u.SystemLibrary.get_command_line():CASES[:]=[CASES[-1]]
def save():
 name='RigidBenchmark8.json' if BENCHMARK8 else 'RigidHeadless8.json' if HEADLESS else 'RigidTest8.json' if AUTO else 'RigidSession8.json';(R/'ArtBible'/name).write_text(json.dumps(S['report'],indent=2))
view.save=save
def spawn_joint8(point):
 t=u.Transform(location=point);a=u.GameplayStatics.begin_deferred_actor_spawn_from_class(S['world'],u.PhysicsConstraintActor,t,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None);assert a
 return u.GameplayStatics.finish_spawning_actor(a,t)
def shot(tag):
 if HEADLESS or BENCHMARK8:return
 p=R/'Screenshots'/('Rigid8_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'HighResShot 1600x1000 filename="'+str(p).replace('\\','/')+'"',S['pc']);S['shots'].append(dict(file=p.name,tag=tag,started=time.time()))
def reset():
 S.update(build_job=None,building_structure=False,bind_cursor=0,air_core=None,baseline_offsets={},slice_costs=[],exit_started8=False,outer_bands8={},sync_job8=None,bind_sync8=False)
 if not S.get('core_actor8'):S['core_actor8']=next(a for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.StaticMeshActor) if a.get_actor_label()=='AircraftRigidCore8')
 core=S['core_actor8'];core.static_mesh_component.set_simulate_physics(False);core.set_actor_enable_collision(False);core.static_mesh_component.set_collision_profile_name('NoCollision');core.static_mesh_component.set_visibility(False,False);core.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD)
 S['carrier'].set_actor_enable_collision(False);S['carrier'].static_mesh_component.set_collision_profile_name('NoCollision');S['pawn'].set_actor_enable_collision(False)
 movement=S['pawn'].get_component_by_class(u.CharacterMovementComponent)
 if movement:movement.disable_movement()
 for p in S.get('parts',[]):
  a=p['actor'];a.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD)
 old_joints8=[q['actor'] for q in S.get('joints',[])];bodies,decks=S['body_pool'],S['deck_pool'];S.setdefault('deck_mesh8',decks[0].static_mesh_component.static_mesh);used8=[q['actor'] for q in S.get('active',[])];used_decks8=S.get('active_decks8',[]);S['body_pool']=used8;S['deck_pool']=used_decks8
 try:_reset7()
 finally:S['body_pool'],S['deck_pool']=bodies,decks
 for a in used8+used_decks8:a.static_mesh_component.set_static_mesh(None)
 for a in old_joints8:a.destroy_actor()
 S['active_decks8']=[]
 core.set_actor_location(S['carrier'].get_actor_location(),False,True);core.set_actor_rotation(u.Rotator(),False);view.attached(core,S['carrier'])
def ready(*args,**kwargs):
 _ready7(*args,**kwargs);set_outer_collision();S['report'].pop('first_physics_failure',None);S['report']['native_break_events']=[];S['report']['activation_window_updates']=[]
def set_outer_collision(hit=None):
 if not S.get('outer8'):
  S['outer8']={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.StaticMeshActor) if a.get_actor_label().startswith('Collision8 ')}
  if not S['outer8']:return
 if hit is None:S['outer_bands8']={}
 else:S.setdefault('outer_bands8',{})[(hit[1]['tower'],hit[3])]=(hit[2].z-(670 if hit[3]!=S['predicted_side'] else 820),hit[2].z+(670 if hit[3]!=S['predicted_side'] else 1620))
 for spec in D['towers']:
  town=spec['tower'];cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;h=spec['height']*100
  for face in range(4):
   x,y=rotate(0,3064.92,face);band=S['outer_bands8'].get((town,face));lo=max(0,band[0]) if band else 0;hi=min(h,band[1]) if band else 0
   intervals=((0,lo),(hi,h)) if band else ((0,h),(0,0))
   for half,(bottom,top) in zip(('A','B'),intervals):
    a=S['outer8'][f'Collision8 {town} {face} {half}'];a.set_actor_enable_collision(top-bottom>1);a.set_actor_location(u.Vector(cx+x,cy+y,(bottom+top)*.5),False,True);a.set_actor_scale3d(u.Vector(63.4,2,max(.0001,(top-bottom)/100)))
  roof=S['outer8']['Collision8 '+town+' Roof'];roof.set_actor_location(u.Vector(cx,cy,h-100),False,True);roof.set_actor_scale3d(u.Vector(63.4,63.4,2));roof.set_actor_enable_collision((town,4) not in S['outer_bands8'])
def _structure_job(hit):
 # Cleanup and preparation share a frame budget; native contact geometry remains intact.
 S['generation']=S.get('generation',0)+1;S.update(profile_pending=[],break_queue=[],unsupported=set())
 old=list(S['active']);old_joints=list(S['joints']);S['joints']=[]
 for q in old_joints:
  q['component'].on_constraint_broken.clear();q['component'].break_constraint();q['actor'].destroy_actor();yield
 S.update(free_joints=list(reversed(S['joint_pool'])),joint_index=0)
 for a in [q['actor'] for q in old]+S.get('active_decks8',[]):
  c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);c.set_collision_profile_name('NoCollision');a.set_actor_hidden_in_game(True);yield
 dirty={}
 for q in old:
  c=q['component'];c.update_instance_transform(q['index'],view.transform(q),False,False,True);dirty[id(c)]=(c,q);q['active']=False;yield
 for c,q in dirty.values():c.update_instance_transform(q['index'],view.transform(q),False,True,True);yield
 S.update(active=[],render_dirty={},defer_joints=True,pending_joints=[],pending_wait=15,assembly_ready=False,pending_kind='structure',bind_sync8=False,deck_positions8={})
 hit=S.get('requested_hit',hit);_,spec,p,side=hit;S.update(predicted_tower=spec['tower'],predicted_point=p,predicted_side=side,build_phase='activating')
 cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;bb=[cx-3300,cx+3300,cy-3300,cy+3300,p.z-800,p.z+1600];candidates={}
 for k in view.bins(bb):
  for q in S['grid'].get(k,()):
   if q['tower']!=spec['tower'] or q['kind'] not in ('facade','base','corner','roof') or not view.overlap(bb,q['bounds']):continue
   if side==4 and q['kind']!='roof':continue
   if side!=4 and q['kind'] in ('facade','base') and q.get('side')!=side:continue
   if side!=4 and q['kind']=='corner' and q.get('side') not in (side,(side-1)%4):continue
   candidates[(q['tower'],q['tag'],q['index'])]=q
 assert len(candidates)<=1536
 for q in candidates.values():activate(q);yield
 flush_instances();yield
 nodes={(q.get('side'),q.get('column'),q.get('floor',0)*2+q.get('segment',0)):q for q in S['active'] if q['kind']=='facade'}
 for (side1,col,row),q in nodes.items():
  for other in [nodes.get((side1,col,row+1))]:
   if other:joint(q['actor'],other['actor'],(centre(q)+centre(other))*.5,CFG['facade_bond_force'],'facade',(q['index'],other['index']));yield
  if any((side1,col+dx,row+dz) not in nodes for dx,dz in ((-1,0),(1,0),(0,-1),(0,1))):joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index']);yield
 for q in S['active']:
  if q['kind'] not in ('facade','roof'):joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index']);yield
 roofs={q['index']:q for q in S['active'] if q['kind']=='roof'}
 for index,q in roofs.items():
  ix,iy=divmod(index,7)
  for j in ((index+7 if ix<6 else -1),(index+1 if iy<6 else -1)):
   if j in roofs:joint(q['actor'],roofs[j]['actor'],(centre(q)+centre(roofs[j]))*.5,CFG['deck_bond_force'],'roof',(index,j));yield
  if ix in (0,6) or iy in (0,6):joint(q['actor'],None,centre(q),CFG['deck_boundary_force'],'roof_boundary',index);yield
 pitch=spec['floor_pitch']*100;level=int((p.z-2280)/pitch);decks={}
 for i,a in enumerate(S['deck_pool'][:108]):
  floor=level-1+i//36;ix=i%36//6;iy=i%6
  if floor<0 or floor>=104:continue
  pos=u.Vector(cx+(ix-2.5)*980,cy+(iy-2.5)*980,2280+floor*pitch);S['deck_positions8'][a]=pos;a.static_mesh_component.set_static_mesh(None);a.static_mesh_component.set_static_mesh(S['deck_mesh8']);a.set_actor_location(pos,False,True);a.set_actor_rotation(u.Rotator(),False);a.set_actor_scale3d(u.Vector(1,1,1));a.set_actor_hidden_in_game(False);collider(a,CFG['deck_mass_kg'],'deck');decks[(floor,ix,iy)]=a;yield
 for (floor,ix,iy),a in decks.items():
  for k in ((floor,ix+1,iy),(floor,ix,iy+1)):
   b=decks.get(k)
   if b:joint(a,b,(a.get_actor_location()+b.get_actor_location())*.5,CFG['deck_bond_force'],'deck',k);yield
  if ix in (0,5) or iy in (0,5):joint(a,None,a.get_actor_location(),CFG['deck_boundary_force'],'deck_boundary',(floor,ix,iy));yield
 S['active_decks8']=list(decks.values());S['bind_cursor']=0;S['pending_wait']=15
 S['report']['prepared_structure']=dict(tower=spec['tower'],face=side,point_cm=list(p.to_tuple()),facade_bodies=len(S['active']),floor_bodies=len(decks),planned_native_joints=len(S['pending_joints']),note='Intact equivalent bodies and native bonds prepared incrementally before contact; no scripted damage mask.');save()
def prepare_structure(hit):
 set_outer_collision();S.update(build_job=_structure_job(hit),building_structure=True,assembly_ready=False,build_started=time.monotonic(),requested_hit=hit,build_phase='cleanup',exit_started8=False)
def prepare_exit8():
 if S.get('exit_started8') or S['predicted_side']==4:return False
 S['exit_started8']=True;town=S['predicted_tower'];spec=next(q for q in D['towers'] if q['tower']==town);side=(S['predicted_side']+2)%4;entry=S['predicted_point'];normal=u.Vector(*rotate(0,1,S['predicted_side']),0);f,_=view.attitude();denom=abs(f.x*normal.x+f.y*normal.y);point=entry+f*(6305.84/max(.5,denom));point.z=entry.z
 S.update(exit_hit8=(0,spec,point,side),build_job=_exit_job8(spec,point,side),building_structure=True,assembly_ready=False,build_started=time.monotonic(),pending_kind='exit',build_phase='exit')
 return True
def _exit_job8(spec,p,side):
 S.update(defer_joints=True,pending_joints=[],pending_wait=15,bind_cursor=0,bind_sync8=False);cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;bb=[cx-3300,cx+3300,cy-3300,cy+3300,p.z-650,p.z+650];candidates={}
 for k in view.bins(bb):
  for q in S['grid'].get(k,()):
   if q['tower']==spec['tower'] and not q.get('active') and q['kind'] in ('facade','base','corner') and view.overlap(bb,q['bounds']):
    if q['kind'] in ('facade','base') and q.get('side')!=side:continue
    if q['kind']=='corner' and q.get('side') not in (side,(side-1)%4):continue
    candidates[(q['tower'],q['tag'],q['index'])]=q
 assert len(S['active'])+len(candidates)<=len(S['body_pool']),(len(S['active']),len(candidates));new=list(candidates.values());S['exit_new_nodes8']=new
 for q in new:activate(q);yield
 flush_instances();yield
 nodes={(q.get('side'),q.get('column'),q.get('floor',0)*2+q.get('segment',0)):q for q in new if q['kind']=='facade'}
 for (side1,col,row),q in nodes.items():
  other=nodes.get((side1,col,row+1))
  if other:joint(q['actor'],other['actor'],(centre(q)+centre(other))*.5,CFG['facade_bond_force'],'facade',(q['index'],other['index']));yield
  if (side1,col,row-1) not in nodes or (side1,col,row+1) not in nodes:joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index']);yield
 for q in new:
  if q['kind']!='facade':joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index']);yield
 S['report']['exit_region8']=dict(tower=spec['tower'],face=side,point_cm=list(p.to_tuple()),native_bodies=len(new),prepared_before_contact=not bool(S.get('impact_time')),method='Opposite-face intact bodies connected before arrival; only native contact can break their bonds.');S['pending_wait']=15;save()
def physics_tick(dt,now):
 begin=time.perf_counter()
 if S.get('build_job') is not None:
  try:
   for _ in range(140):
    next(S['build_job'])
    if time.perf_counter()-begin>.004:break
  except StopIteration:S.update(build_job=None,building_structure=False)
 elif S.get('pending_joints'):
  if S['pending_wait']>0:S['pending_wait']-=1
  elif not S.get('bind_sync8'):
   if S.get('sync_job8') is None:
    nodes=S.get('exit_new_nodes8',[]) if S['pending_kind']=='exit' else S['active'];targets=[(q['actor'],view.transform(q)) for q in nodes]
    if S['pending_kind']!='exit':targets += [(a,u.Transform(location=S['deck_positions8'][a])) for a in S.get('active_decks8',[])]
    S['sync_job8']=iter(targets)
   try:
    for _ in range(60):
     a,t=next(S['sync_job8']);a.set_actor_transform(t,False,True);c=a.static_mesh_component;c.set_physics_linear_velocity(u.Vector(),False);c.set_physics_angular_velocity_in_radians(u.Vector(),False)
     if time.perf_counter()-begin>.004:break
   except StopIteration:S.update(sync_job8=None,bind_sync8=True,pending_wait=3)
  else:
   plans=S['pending_joints'];S['defer_joints']=False
   for _ in range(64):
    if S['bind_cursor']>=len(plans):break
    joint(*plans[S['bind_cursor']]);S['bind_cursor']+=1
    if time.perf_counter()-begin>.004:break
   if S['bind_cursor']>=len(plans):
    is_exit=S['pending_kind']=='exit';set_outer_collision(S['exit_hit8'] if is_exit else (0,next(q for q in D['towers'] if q['tower']==S['predicted_tower']),S['predicted_point'],S['predicted_side']))
    targets=[q['actor'] for q in S.get('exit_new_nodes8',[])] if is_exit else [q['actor'] for q in S['active']]+S.get('active_decks8',[])
    for a in targets:a.static_mesh_component.set_enable_gravity(True);a.static_mesh_component.wake_all_rigid_bodies()
    S.update(assembly_ready=True,pending_joints=[],test_after=time.monotonic()+2,sleep_intact_at=now+1)
    S['report']['last_preparation']=dict(seconds=now-S['build_started'],joints=len(S['joints']),facade_bodies=len(S['active']),floor_bodies=len(S.get('active_decks8',[])),maximum_frame_slice_ms=max(S.get('slice_costs',[0]) or [0]));save()
    if not is_exit:prepare_exit8()
 cost=(time.perf_counter()-begin)*1000;S.setdefault('slice_costs',[]).append(cost);S['slice_costs']=S['slice_costs'][-300:]
 if S.get('sleep_intact_at') and now>S['sleep_intact_at'] and not S.get('impact_time') and S.get('assembly_ready'):
  S['sleep_intact_at']=None
  for a in [q['actor'] for q in S['active']]+S.get('active_decks8',[]):a.static_mesh_component.put_rigid_body_to_sleep()
 forces();poll(now);adaptive_structure(now);view.update_dust(now);camera_tick(dt)
 if '-Force8Profile' in u.SystemLibrary.get_command_line() and S.get('launched'):
  if not S.get('csv_started8'):u.SystemLibrary.execute_console_command(S['world'],'csvprofile start',S['pc']);S['csv_started8']=True
  if not S.get('csv_stopped8') and ((S.get('impact_time') and now-S['impact_time']>2.5) or S['flight_elapsed']>10):u.SystemLibrary.execute_console_command(S['world'],'csvprofile stop',S['pc']);S['csv_stopped8']=True
def adaptive_structure(now):
 if not S['launched'] or S.get('impact_time') or now-S.get('prediction_at',0)<.15:return
 S['prediction_at']=now;c=S['air_core'].static_mesh_component;v=c.get_physics_linear_velocity();speed=v.length()
 if speed<100:return
 hit=predict(S['nose'].get_actor_location(),v/speed)
 if S.get('build_job'):
  if hit and S.get('build_phase')=='cleanup':S['requested_hit']=hit
  return
 if not S.get('assembly_ready'):return
 if not hit or hit[0]<15000:return
 if hit[1]['tower']==S['predicted_tower'] and hit[3]==S['predicted_side'] and abs(hit[2].z-S['predicted_point'].z)<850:return
 S['report'].setdefault('activation_window_updates',[]).append(dict(time_s=S['flight_elapsed'],tower=hit[1]['tower'],face=hit[3],point_cm=list(hit[2].to_tuple())));prepare_structure(hit)
def launch():
 if S['launched'] or not S.get('assembly_ready'):return
 core=S['core_actor8'];S['air_core']=core;velocity=u.MathLibrary.get_right_vector(S['carrier'].get_actor_rotation())*S['speed']
 core.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);c=collider(core,sum(MASS.values()),'air')
 for p in S['parts']:
  a=p['actor']
  a.static_mesh_component.set_simulate_physics(False);a.set_actor_enable_collision(False);a.static_mesh_component.set_collision_profile_name('NoCollision');view.attached(a,core)
 c.set_physics_linear_velocity(velocity,False);c.set_physics_angular_velocity_in_radians(u.Vector(),False);c.set_use_ccd(True);S['native_air_mass']=c.get_mass()
 for a in S['rig']:view.attached(a,S['nose'])
 S['baseline_offsets']={p['part']:u.MathLibrary.inverse_transform_location(core.get_actor_transform(),p['actor'].get_actor_location()) for p in S['parts']};S.update(launched=True,flying=True,launch_time=time.monotonic(),launch_sim_time=u.GameplayStatics.get_time_seconds(S['world']),initial_velocity=velocity,minimum_energy=1e99,last_speed=S['speed'],case_frame_times8=[]);S['initial_energy']=energy();S['minimum_energy']=S['initial_energy'];S['report']['launch']=dict(speed_m_s=S['speed']/100,native_aircraft_bodies=1,compound_convex_shapes=13,visible_aircraft_sections=13,aircraft_mass_kg=S['native_air_mass'],kinetic_energy_j=S['initial_energy'],native_air_joints=0,method='One prebuilt compound collision body carries every aircraft render section. Initial velocity once; forces, torque, gravity and contact thereafter.');save()
def energy():
 if not S.get('air_core'):return 0
 return .5*S['native_air_mass']*S['air_core'].static_mesh_component.get_physics_linear_velocity().length()**2/10000
def rigid_error():
 if not S.get('air_core'):return 0
 t=S['air_core'].get_actor_transform();return max((u.MathLibrary.inverse_transform_location(t,p['actor'].get_actor_location())-S['baseline_offsets'][p['part']]).length() for p in S['parts'])
def forces():
 if not S['launched'] or S.get('impact_time'):return
 core=S['air_core'];c=core.static_mesh_component;f,up=view.attitude();rot=core.get_actor_rotation();omega=c.get_physics_angular_velocity_in_radians();alpha=clamp(u.MathLibrary.get_right_vector(rot).cross(f)*2+u.MathLibrary.get_up_vector(rot).cross(up)*1.6-omega*.9,1.1);accel=clamp((f*S['speed']-c.get_physics_linear_velocity())*.65,600)+u.Vector(0,0,980);c.add_force(accel*c.get_mass(),NONE,False);c.add_torque_in_radians(alpha,NONE,True)
def impact(now):
 f,_=view.attitude()
 for q in S['fine']:
  for mid in q['mids']:mid.set_vector_parameter_value('BurstNormal',u.LinearColor(-f.x,-f.y,-f.z,1))
 _impact_physics(now)
 for i,q in enumerate(q for q in S['dust'] if q['bank']=='Smoke'):q['delay']=.5+i*.13
 if not AUTO or S.get('benchmark8'):
  p=S['contact_point'];f,_=view.attitude();right=u.Vector(-f.y,f.x,0);eye=p-f*14500-right*8500+u.Vector(0,0,3000);cam=S['flight_cams'][2];cam.set_actor_location(eye,False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye,p),False);S['view']=2;S['pc'].set_view_target_with_blend(cam,.25)
 S['report']['impact_aircraft_rigid_error_cm']=rigid_error()
def snapshot():
 d=_snapshot7();d['fuselage_rigid_error_cm']=rigid_error();d['native_aircraft_body_count']=1;d['exit_region']=copy.deepcopy(S['report'].get('exit_region8'));side=(S['predicted_side']+2)%4;d['opposite_face_displaced_cells']=sum(q['kind']=='facade' and q.get('side')==side and (q['actor'].get_actor_location()-u.Vector(*q['location'])).length()>10 for q in S['active']) if S['predicted_side']!=4 else 0;return d
def initialize(now):
 ok=_initialize7(now)
 if not ok:return False
 for a in S['joint_pool']:a.get_component_by_class(u.PhysicsConstraintComponent).break_constraint()
 S['report']['field_collision_disabled']=True
 for a in u.GameplayStatics.get_all_actors_of_class(S['world'],u.Actor):
  if not a.get_actor_label().startswith('Structure5 '):continue
  for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
   if c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION:c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
 mats=[u.load_asset('/Game/TwinTowers/Rigid8/Materials/M_Rigid8_FineAlloy'),u.load_asset('/Game/TwinTowers/Rigid8/Materials/M_Rigid8_FineGlass')];assert all(mats)
 for q in S['fine']:q['mids']=[q['actor'].static_mesh_component.create_dynamic_material_instance(i,m) for i,m in enumerate(mats)]
 for a in S['rig']:
  if a.get_actor_label().startswith('Cockpit5 Fill'):a.light_component.set_intensity(8500)
 S.update(frame_times8={},slice_costs=[],last_stats8=now,benchmark8='-Force8Benchmark' in u.SystemLibrary.get_command_line());S['report']['revision']=8;S['report']['performance_method']='All frames sampled including stalls above one second; phase-specific p95/p99 and maximum, not only median FPS.';S['report']['method']='Rigid compound aircraft with frame-budgeted native structural preparation and contact-driven joint failure.'
 return True
def test_tick(dt,now):
 if CASES[S['case_index']].get('pitch_test') and S.get('launched') and not S.get('impact_time'):
  t=S['flight_elapsed'];view.steering(dt,0,.8 if .35<t<2 else 0)
 if S.get('launched') and not S.get('impact_time'):
  S['report']['maximum_preimpact_rigid_error_cm']=max(S['report'].get('maximum_preimpact_rigid_error_cm',0),rigid_error())
 phase=S['test_phase']
 if phase=='case_verify':
  check(CASES[S['case_index']]['name']+': aircraft tube remains rigid through contact',rigid_error()<.1,maximum_relative_displacement_cm=rigid_error(),native_body_count=1)
  if CASES[S['case_index']].get('pitch_test'):
   save_performance();values=S.get('case_frame_times8',[]);check('Sustained pitch does not cause blocking physics rebuilds',bool(values) and max(values)<150,maximum_controlled_flight_frame_ms=max(values) if values else None,frames_over_50ms=sum(x>50 for x in values),updates=len(S['report'].get('activation_window_updates',[])))
 _test_tick7(dt,now)
def record_performance(raw_dt,cost):
 if S.get('launched') and not S.get('impact_time'):S.setdefault('case_frame_times8',[]).append(raw_dt*1000)
 phase='preparing' if not S.get('assembly_ready') else 'impact' if S.get('impact_time') else 'flight' if S.get('launched') else 'spectator'
 values=S['frame_times8'].setdefault(phase,[]);values.append(raw_dt*1000)
 if len(values)>2000:del values[0]
 S.setdefault('tick_costs8',[]).append(cost);S['tick_costs8']=S['tick_costs8'][-2000:]
def save_performance():
 phases={}
 for phase,values in S.get('frame_times8',{}).items():
  v=sorted(values);n=len(v)
  if n:phases[phase]=dict(frames=n,median_ms=v[n//2],p95_ms=v[int((n-1)*.95)],p99_ms=v[int((n-1)*.99)],maximum_ms=max(v),frames_over_50ms=sum(x>50 for x in v),frames_over_100ms=sum(x>100 for x in v),frames_over_1000ms=sum(x>1000 for x in v))
 S['report']['frame_statistics8']=phases
def start():
 S.update(after=time.monotonic()+10,initialized=False,shots=[],report=dict(status='RUNNING' if AUTO else 'INTERACTIVE_READY',revision=8,method='Rigid compound aircraft; frame-budgeted local native structural simulation.',checks=[],scenarios=[],captures=[],native_break_events=[],runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),settings=CFG))
 save()
 def tick(dt):
  now=time.monotonic();begin=time.perf_counter()
  if now<S['after']:return
  try:
   if not S['initialized']:initialize(now);return
   if not alive(S.get('pc')):u.unregister_slate_post_tick_callback(S['handle']);return
   raw_dt=now-S['last_tick'];dt=min(.05,max(.001,raw_dt));S['last_tick']=now
   for q in list(S['shots']):
    p=R/'Screenshots'/q['file']
    if p.exists() and p.stat().st_mtime>=q['started'] and p.stat().st_size>5000:S['report']['captures'].append(dict(file=p.name,tag=q['tag'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S['shots'].remove(q);save()
    elif time.time()-q['started']>20:raise RuntimeError('Native screenshot did not arrive: '+q['file'])
   if AUTO:test_tick(dt,now)
   else:
    pc=S['pc'];pressed=lambda k:pc.was_input_key_just_pressed(KEYS[k]);down=lambda k:pc.is_input_key_down(KEYS[k])
    if pressed('R'):ready(S['preset'])
    if pressed('T'):ready(S['preset']+1)
    if pressed('Tab'):
     if S['view']==3:pilot_view()
     else:enter_free()
    if pressed('C'):pilot_view()
    if pressed('V'):
     target=(S['view']+1)%4
     if target==3:enter_free()
     else:S['view']=target;pc.set_view_target_with_blend(S['flight_cams'][target],0)
    mx,my=pc.get_input_mouse_delta()
    if S['view']==3:
     if pressed('MouseScrollUp'):S['free_speed']=min(60000,S['free_speed']*1.35)
     if pressed('MouseScrollDown'):S['free_speed']=max(500,S['free_speed']/1.35)
     spectator_tick(dt,int(down('W'))-int(down('S')),int(down('D'))-int(down('A')),int(down('SpaceBar') or down('E'))-int(down('LeftControl') or down('Q')),down('LeftShift'),mx,my)
     if pressed('P'):launch()
    else:
     if pressed('SpaceBar') or pressed('P'):launch()
     if S['flying']:view.steering(dt,int(down('D'))-int(down('A')),int(down('W'))-int(down('S')),int(down('E'))-int(down('Q')),int(down('LeftShift'))-int(down('LeftControl')),down('F'))
     S['look_yaw']+=mx*.18;S['look_pitch']=max(-89,min(89,S['look_pitch']+my*.18))
     if pressed('F'):S['look_yaw']=S['look_pitch']=0
   physics_tick(dt,now)
   if not AUTO and now-S.get('hud_at',0)>.3:hud();S['hud_at']=now
   record_performance(raw_dt,(time.perf_counter()-begin)*1000)
   if now-S.get('saved_at',0)>3:
    save_performance();S['report']['live']=dict(flying=S['flying'],launched=S['launched'],elapsed_s=S['flight_elapsed'],broken_wall_bonds=S['broken_wall'],broken_air_joints=0,view=S['view'],spectator_speed_m_s=S.get('free_speed',6000)/100,assembly_ready=S.get('assembly_ready'),rigid_error_cm=rigid_error());save();S['saved_at']=now
  except Exception:
   S['report'].update(status='FAILED',error=traceback.format_exc());save();u.log_error(S['report']['error']);u.unregister_slate_post_tick_callback(S['handle'])
   if AUTO:u.SystemLibrary.quit_game(S.get('world'),S.get('pc'),u.QuitPreference.QUIT,False)
 S['handle']=u.register_slate_post_tick_callback(tick)
