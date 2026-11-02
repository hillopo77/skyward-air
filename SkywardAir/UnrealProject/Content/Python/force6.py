"""Force-driven Chaos rigid bodies and breakable structural joints.

An activation window changes intact instanced geometry into equivalent connected
dynamic bodies before contact. Only Chaos breaks the joints during flight.
There is no contact-mask removal, timed breakup or prescribed debris velocity.
"""
import unreal as u,json,time,math,random,hashlib,traceback,copy
from pathlib import Path
import flight5 as view
from flight_layout5 import layout,rotate
R=Path(__file__).resolve().parents[4]/'TwinTowers';D=json.loads((R/'Exports/force_manifest6.json').read_text());S={};view.S=S;view.D=D;AUTO='-Force6Test' in u.SystemLibrary.get_command_line();QUICK='-Force6Quick' in u.SystemLibrary.get_command_line();HEADLESS='-Force6Headless' in u.SystemLibrary.get_command_line();NONE=u.Name('None')
CFG=dict(facade_mass_kg=60,deck_mass_kg=1100,facade_bond_force=2.0e6,facade_boundary_force=1.0e7,deck_bond_force=1.2e7,deck_boundary_force=2.0e7,physics_substep_s=1/120,activation_half_width_cm=2650,activation_half_height_cm=1450,initial_speed_cm_s=8000)
MASS={'Flightdeck':4000,'Nose':3500,'Forward':6500,'Midbody':8500,'Aft':6000,'TailBody':2500,'TailSurfaces':1800,'WingLInner':3500,'WingRInner':3500,'WingLOuter':1200,'WingROuter':1200,'EngineL':1800,'EngineR':1800}
PAIR=[('Nose','Flightdeck',3e5),('Flightdeck','Forward',4e5),('Forward','Midbody',5e5),('Midbody','Aft',5e5),('Aft','TailBody',3e5),('TailBody','TailSurfaces',1.5e5),('Midbody','WingLInner',2e5),('Midbody','WingRInner',2e5),('WingLInner','WingLOuter',8e4),('WingRInner','WingROuter',8e4),('WingLInner','EngineL',1.2e5),('WingRInner','EngineR',1.2e5)]
KEYS={n:view.key(n) for n in ('SpaceBar','P','T','R','V','A','D','W','S','Q','E','F','LeftShift','LeftControl')};BLOCK=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('block'))
def save():(R/'ArtBible'/('ForceHeadless6.json' if HEADLESS else 'ForceTest6.json' if AUTO else 'ForceSession6.json')).write_text(json.dumps(S['report'],indent=2))
view.save=save
def check(name,passed,**data):S['report']['checks'].append(dict(test=name,passed=bool(passed),**copy.deepcopy(data)));save()
def shot(tag):
 if HEADLESS:return
 p=R/'Screenshots'/('Force6_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'HighResShot 1600x1000 filename="'+str(p).replace('\\','/')+'"',S['pc']);S['shots'].append(dict(file=p.name,tag=tag,started=time.time()))
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
 c.set_mobility(u.ComponentMobility.MOVABLE);bi=c.get_editor_property('body_instance');bi.set_editor_property('position_solver_iteration_count',16);bi.set_editor_property('velocity_solver_iteration_count',8);c.set_enable_gravity(kind=='air');c.set_simulate_physics(True);c.set_mass_override_in_kg(NONE,mass,True);c.set_linear_damping(.015 if kind=='air' else .04);c.set_angular_damping(.14);c.set_use_ccd(True);c.set_physics_max_angular_velocity_in_radians(12,False)
 return c
def joint(a,b,point,threshold,kind,key):
 if S.get('defer_joints'):
  S['pending_joints'].append((a,b,point,threshold,kind,key));return
 assert S['free_joints'],'Native joint pool exhausted';actor=S['free_joints'].pop();S['joint_index']+=1;c=actor.get_component_by_class(u.PhysicsConstraintComponent);actor.set_actor_location(point,False,True)
 c.set_linear_x_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_y_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_linear_z_limit(u.LinearConstraintMotion.LCM_LOCKED,0);c.set_angular_swing1_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_angular_swing2_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_angular_twist_limit(u.AngularConstraintMotion.ACM_LOCKED,0);c.set_linear_breakable(True,threshold);c.set_angular_breakable(True,threshold*200);c.set_projection_enabled(False);c.set_disable_collision(True);c.set_constrained_components(a.static_mesh_component,NONE,(b or S['anchor']).static_mesh_component,NONE);q=dict(actor=actor,component=c,a=a,b=b,kind=kind,key=key,threshold=threshold,broken=False,bound_at=time.monotonic(),profile_reapplied=False);S['joints'].append(q);return q
def centre(q):b=q['bounds'];return u.Vector((b[0]+b[1])/2,(b[2]+b[3])/2,(b[4]+b[5])/2)
def activate(q):
 if q.get('active'):return
 assert len(S['active'])<len(S['body_pool']),'Native facade pool exhausted';a=S['body_pool'][len(S['active'])];c=a.static_mesh_component;c.set_static_mesh(mesh(q['asset']));a.set_actor_transform(view.transform(q),False,True);a.set_actor_hidden_in_game(False);collider(a,CFG['deck_mass_kg'] if q['kind']=='roof' else CFG['facade_mass_kg'],'wall');q['component'].update_instance_transform(q['index'],u.Transform(location=u.Vector(0,0,-100000)),False,False,True);S['render_dirty'][id(q['component'])]=(q['component'],q);q.update(active=True,actor=a);S['active'].append(q)
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
def prepare_structure(hit):
 S.update(defer_joints=True,pending_joints=[],pending_wait=3,assembly_ready=False,pending_kind='structure')
 _,spec,p,side=hit;S.update(predicted_tower=spec['tower'],predicted_point=p,predicted_side=side);bb=[p.x-2800,p.x+2800,p.y-2800,p.y+2800,p.z-1450,p.z+1450];candidates={}
 for k in view.bins(bb):
  for q in S['grid'].get(k,()):
   if q['tower']==spec['tower'] and q['kind'] in ('facade','base','corner','roof') and view.overlap(bb,q['bounds']):candidates[(q['tower'],q['tag'],q['index'])]=q
 assert len(candidates)<=1536,len(candidates)
 for q in candidates.values():activate(q)
 flush_instances();nodes={(q.get('side'),q.get('column'),q.get('floor',0)*2+q.get('segment',0)):q for q in S['active'] if q['kind']=='facade'}
 for k,q in nodes.items():
  side,col,row=k;neighbours=[nodes.get((side,col+1,row)),nodes.get((side,col,row+1))]
  for other in neighbours:
   if other:joint(q['actor'],other['actor'],(centre(q)+centre(other))*.5,CFG['facade_bond_force'],'facade',(q['index'],other['index']))
  if any((side,col+dx,row+dz) not in nodes for dx,dz in ((-1,0),(1,0),(0,-1),(0,1))):joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index'])
 for q in S['active']:
  if q['kind'] not in ('facade','roof'):joint(q['actor'],None,centre(q),CFG['facade_boundary_force'],'boundary',q['index'])
 roofs={q['index']:q for q in S['active'] if q['kind']=='roof'}
 for index,q in roofs.items():
  ix,iy=divmod(index,7)
  for j in ((index+7 if ix<6 else -1),(index+1 if iy<6 else -1)):
   if j in roofs:joint(q['actor'],roofs[j]['actor'],(centre(q)+centre(roofs[j]))*.5,CFG['deck_bond_force'],'roof',(index,j))
  if ix in (0,6) or iy in (0,6):joint(q['actor'],None,centre(q),CFG['deck_boundary_force'],'roof_boundary',index)
 # Floors are physically connected before contact, rather than spawned after a hit.
 pitch=spec['floor_pitch']*100;level=int((p.z-2280)/pitch);cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;decks={}
 for i,a in enumerate(S['deck_pool']):
  floor=level-3+i//36;ix=i%36//6;iy=i%6
  if floor<0 or floor>=104:continue
  pos=u.Vector(cx+(ix-2.5)*980,cy+(iy-2.5)*980,2280+floor*pitch);a.set_actor_location(pos,False,True);a.set_actor_rotation(u.Rotator(),False);a.set_actor_scale3d(u.Vector(1,1,1));a.set_actor_hidden_in_game(False);collider(a,CFG['deck_mass_kg'],'deck');decks[(floor,ix,iy)]=a
 for (floor,ix,iy),a in decks.items():
  for k in ((floor,ix+1,iy),(floor,ix,iy+1)):
   b=decks.get(k)
   if b:joint(a,b,(a.get_actor_location()+b.get_actor_location())*.5,CFG['deck_bond_force'],'deck',k)
  if ix in (0,5) or iy in (0,5):joint(a,None,a.get_actor_location(),CFG['deck_boundary_force'],'deck_boundary',(floor,ix,iy))
 for q in S['active']:q['actor'].static_mesh_component.put_rigid_body_to_sleep()
 for a in S['deck_pool']:a.static_mesh_component.put_rigid_body_to_sleep()
 S['report']['prepared_structure']=dict(tower=spec['tower'],face=side,point_cm=list(p.to_tuple()),facade_bodies=len(S['active']),floor_bodies=len(decks),native_joints=len(S['joints']),note='Intact connected bodies replace equivalent instances before contact. Preparing this region does not break joints or delete a hole.');save()
def reset():
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
def ready(preset=0,speed=8000,offset=0,angle=0,roof=False):
 reset();S['preset']=preset%3;spec=next(t for t in D['towers'] if t['tower']==('South' if preset%3==1 else 'North'));side=1 if preset%3==1 else 0;heading=(180 if side==1 else -90)+angle;rad=math.radians(heading);f=u.Vector(math.cos(rad),math.sin(rad),0);x,y=rotate(offset,3185,side);point=u.Vector(spec['centre'][0]*100+x,-spec['centre'][1]*100+y,22000 if side==1 else 17800 if preset%3==0 else 28000);root=S['carrier'];root.set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,u.Vector(0,0,1)),False);root.set_actor_location(point-f*(speed*5+2730),False,True);S.update(heading=heading,pitch=0,bank=0,speed=speed,flight_elapsed=0,view=0,look_yaw=0,look_pitch=0,target=spec['tower'],start_location=root.get_actor_location(),peak_force={},peak_deceleration=0,samples=[])
 if roof:
  S['pitch']=-90;f,up=view.attitude();point=u.Vector(spec['centre'][0]*100,-spec['centre'][1]*100,spec['height']*100);root.set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,up),False);root.set_actor_location(point-f*(speed*5+2730),False,True);S['start_location']=root.get_actor_location()
 hit=predict(root.get_actor_location()+f*2730,f);assert hit,'No structure ahead of approach';prepare_structure(hit);S['pc'].set_view_target_with_blend(S['flight_cams'][0],0);view.camera_tick(.016);S['report']['ready']=dict(preset=preset,speed_m_s=speed/100,target=spec['tower'],angle_degrees=angle,offset_m=offset/100,roof=roof);save()
def launch():
 if S['launched'] or not S.get('assembly_ready'):return
 root=S['carrier'];f=u.MathLibrary.get_right_vector(root.get_actor_rotation());velocity=f*S['speed'];by={p['part']:p for p in S['parts']}
 for p in S['parts']:
  a=p['actor'];a.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);c=collider(a,MASS[p['part']],'air');c.set_physics_linear_velocity(velocity,False);c.set_physics_angular_velocity_in_radians(u.Vector(),False)
 S.update(defer_joints=True,pending_joints=[],pending_wait=3,pending_kind='air')
 for pa,pb,force in PAIR:
  a=by[pa]['actor'];b=by[pb]['actor'];joint(a,b,(a.get_actor_location()+b.get_actor_location())*.5,force,'air',(pa,pb))
 for a in S['rig']:view.attached(a,S['nose'])
 S.update(launched=True,flying=True,launch_time=time.monotonic(),launch_sim_time=u.GameplayStatics.get_time_seconds(S['world']),initial_energy=energy(),initial_velocity=velocity,minimum_energy=energy(),last_speed=S['speed']);S['report']['launch']=dict(speed_m_s=S['speed']/100,native_aircraft_bodies=13,aircraft_mass_kg=sum(MASS.values()),kinetic_energy_j=S['initial_energy'],native_air_joints=len(PAIR),method='Initial velocity once at launch; then forces, torque, gravity, collision and native joints control all aircraft bodies.');save()
def energy():return sum(.5*MASS[p['part']]*p['actor'].static_mesh_component.get_physics_linear_velocity().length()**2/10000 for p in S['parts'])
def clamp(v,maximum):n=v.length();return v if n<=maximum or n<1e-8 else v*(maximum/n)
def forces():
 if not S['launched'] or S.get('impact_time'):return
 f,up=view.attitude();main=next(p['actor'] for p in S['parts'] if p['part']=='Midbody');rot=main.get_actor_rotation();cur_f=u.MathLibrary.get_right_vector(rot);cur_up=u.MathLibrary.get_up_vector(rot);omega=main.static_mesh_component.get_physics_angular_velocity_in_radians();alpha=clamp(cur_f.cross(f)*2+cur_up.cross(up)*1.6-omega*.9,1.5)
 centre=main.static_mesh_component.get_center_of_mass()
 for p in S['parts']:
  c=p['actor'].static_mesh_component;v=c.get_physics_linear_velocity();offset=c.get_center_of_mass()-centre;accel=clamp((f*S['speed']-v)*.65,600)+u.Vector(0,0,980)+alpha.cross(offset)+omega.cross(omega.cross(offset));c.add_force(accel*MASS[p['part']],NONE,False);c.add_torque_in_radians(alpha,NONE,True)
def follow_carrier():
 if not S['launched']:return
 a=S['nose'];r=a.get_actor_rotation();p=next(p for p in S['parts'] if p['part']=='Nose');o=p['origin'];local=u.Vector(o[0]*100,-(o[1]-17.3)*100,o[2]*100);offset=u.MathLibrary.get_forward_vector(r)*local.x+u.MathLibrary.get_right_vector(r)*local.y+u.MathLibrary.get_up_vector(r)*local.z;S['carrier'].set_actor_location(a.get_actor_location()-offset,False,True);S['carrier'].set_actor_rotation(r,False)
def opening():
 p=S.get('contact_point',S['predicted_point']);side=S.get('contact_side',S['predicted_side']);dx,dy=rotate(0,1,side%4);rx,ry=rotate(1,0,side%4);normal=u.Vector(0,0,1) if side==4 else u.Vector(dx,dy,0);right=u.Vector(1,0,0) if side==4 else u.Vector(rx,ry,0);up=u.Vector(0,1,0) if side==4 else u.Vector(0,0,1);ignored=[S['carrier'],S['pawn']]+[q['actor'] for q in S['parts']]+S['rig'];rays=[]
 for x in (-700,-350,0,350,700):
  for z in (-170,0,170):
   centre=p+right*x+up*z;h=u.SystemLibrary.line_trace_single(S['world'],centre+normal*500,centre-normal*1200,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,u.DrawDebugTrace.NONE,True);v=h.to_tuple() if h else None;rays.append(dict(blocking=bool(v and v[0]),actor=v[9].get_actor_label() if v and v[9] else None))
 return dict(clear=sum(not q['blocking'] for q in rays),total=len(rays),rays=rays)
def impact(now):
 if S.get('impact_time') or not S['launched']:return
 # Choose an actually moving structural body; this is effect placement only.
 q=max(S['active'],key=lambda q:q['actor'].static_mesh_component.get_physics_linear_velocity().length());p,e=q['actor'].get_actor_bounds(False);S.update(impact_time=now,contact_point=p,contact_side=q.get('side',S['predicted_side']),flying=False);view.burst(p);S['fx_sources']=[a['actor'].get_actor_location() for a in S['active'] if a['actor'].static_mesh_component.get_physics_linear_velocity().length()>100]
 side=S['contact_side']%4
 for fx in S['dust']:
  off=fx['offset'];v=fx['velocity'];x,y=rotate(off.x,off.y,side);vx,vy=rotate(v.x,v.y,side);fx['offset']=u.Vector(x,y,off.z);fx['velocity']=u.Vector(vx,vy,v.z)
 view.set_impact_camera(p,side);S['pc'].set_view_target_with_blend(S['flight_cams'][2],.15);S['view']=2;S['report']['first_physics_failure']=dict(time_after_launch_s=S['flight_elapsed'],point_cm=list(p.to_tuple()),face=S['contact_side'],tower=q['tower'],native_wall_bonds_broken=S['broken_wall'],native_air_joints_broken=S['broken_air'],aircraft_velocity_cm_s=list(S['nose'].static_mesh_component.get_physics_linear_velocity().to_tuple()));save()
def poll(now):
 if now-S.get('last_poll',0)<.04:return
 S['last_poll']=now
 new_break=False
 for q in S['joints']:
  c=q['component'];broken=c.is_broken()
  if not q['profile_reapplied'] and now-q['bound_at']>.12:
   c.set_linear_breakable(True,q['threshold']);c.set_angular_breakable(True,q['threshold']*200);q['profile_reapplied']=True
   if q['kind']=='air':
    S['report'].setdefault('air_joint_profiles',[]).append(dict(key=q['key'],linear_breakable=str(u.ConstraintInstanceBlueprintLibrary.get_linear_breakable(c.get_constraint())),linear_limits=str(u.ConstraintInstanceBlueprintLibrary.get_linear_limits(c.get_constraint())),components=[str(x) for x in c.get_constrained_components()]))
  if not broken:
   linear,angular=c.get_constraint_force();force=linear.length();S['peak_force'][q['kind']]=max(S['peak_force'].get(q['kind'],0),force)
  elif not q['broken']:
   q['broken']=True
   new_break=True
   if q['kind']=='air':S['broken_air']+=1
   else:S['broken_wall']+=1
   S['report'].setdefault('native_break_events',[]).append(dict(kind=q['kind'],key=q['key'],threshold=q['threshold'],sim_time_s=S.get('flight_elapsed',0),position_cm=list(q['actor'].get_actor_location().to_tuple()),native_is_broken=True))
 if new_break:update_support()
 if S['launched']:
  S['flight_elapsed']=u.GameplayStatics.get_time_seconds(S['world'])-S['launch_sim_time'];ke=energy();S['minimum_energy']=min(S['minimum_energy'],ke)
  if S['broken_wall'] and not S.get('impact_time'):impact(now)
  if now-S.get('last_sample',0)>.2:
   S['samples'].append(dict(t=S['flight_elapsed'],energy_j=ke,nose_speed_m_s=S['nose'].static_mesh_component.get_physics_linear_velocity().length()/100,nose_position_cm=list(S['nose'].get_actor_location().to_tuple()),wall_bonds_broken=S['broken_wall'],air_joints_broken=S['broken_air']));S['last_sample']=now
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
 for a in [q['actor'] for q in S['active']]+S['deck_pool']:
  if a not in supported:
   c=a.static_mesh_component;c.set_collision_response_to_channel(u.CollisionChannel.ECC_WORLD_STATIC,BLOCK);c.set_collision_response_to_channel(u.CollisionChannel.ECC_DESTRUCTIBLE,BLOCK);c.set_forced_lod_model(1)
   for i,slot in enumerate(c.static_mesh.static_materials):c.set_material(i,slot.material_interface)
 S['report']['unsupported_bodies']=sum(a not in supported for a in [q['actor'] for q in S['active']]+S['deck_pool'])
def snapshot():
 return dict(tower=S['predicted_tower'],speed_m_s=S['report']['launch']['speed_m_s'],ready=S['report']['ready'],broken_wall_bonds=S['broken_wall'],broken_air_joints=S['broken_air'],initial_energy_j=S['initial_energy'],minimum_translational_energy_j=S['minimum_energy'],energy_ratio=S['minimum_energy']/S['initial_energy'],peak_constraint_force=S['peak_force'],failure=S['report'].get('first_physics_failure'),opening=opening(),samples=S['samples'],active_body_count=len(S['active'])+len(S['deck_pool']),joints=len(S['joints']),native_break_events=list(S['report'].get('native_break_events',[])))
def physics_tick(dt,now):
 if S.get('pending_joints'):
  if S['pending_wait']>0:S['pending_wait']-=1
  else:
   plans=S['pending_joints'];S.update(pending_joints=[],defer_joints=False)
   for args in plans:joint(*args)
   if S['pending_kind']=='structure':
    for a in [q['actor'] for q in S['active']]+S['deck_pool']:a.static_mesh_component.set_enable_gravity(True);a.static_mesh_component.wake_all_rigid_bodies()
    S.update(assembly_ready=True,test_after=time.monotonic()+3)
   S['report']['bound_native_joints']=len(S['joints']);save()
 forces();follow_carrier();poll(now);adaptive_structure(now);view.update_dust(now);view.camera_tick(dt)
def adaptive_structure(now):
 if not S['launched'] or S.get('impact_time') or not S.get('assembly_ready') or S.get('pending_joints') or now-S.get('prediction_at',0)<.3:return
 S['prediction_at']=now;velocity=S['nose'].static_mesh_component.get_physics_linear_velocity();speed=velocity.length()
 if speed<100:return
 hit=predict(S['nose'].get_actor_location(),velocity/speed)
 if not hit or hit[0]<12000:return
 if hit[1]['tower']==S['predicted_tower'] and hit[3]==S['predicted_side'] and (hit[2]-S['predicted_point']).length()<500:return
 # Rebuild the intact simulation window while still safely away from contact.
 # These removals are setup changes; no failed structure is restored here.
 keep=[]
 for q in S['joints']:
  if q['kind']=='air':keep.append(q)
  else:q['component'].break_constraint();S['free_joints'].append(q['actor'])
 S['joints']=keep;S['joint_index']=len(keep)
 for a in [q['actor'] for q in S['active']]+S['deck_pool']:
  c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);c.set_collision_profile_name('NoCollision');a.set_actor_hidden_in_game(True)
 dirty={}
 for q in S['active']:
  c=q['component'];c.update_instance_transform(q['index'],view.transform(q),False,False,True);dirty[id(c)]=(c,q);q['active']=False
 for c,q in dirty.values():c.update_instance_transform(q['index'],view.transform(q),False,True,True)
 S['active']=[];prepare_structure(hit);S['report'].setdefault('activation_window_updates',[]).append(dict(time_s=S['flight_elapsed'],tower=hit[1]['tower'],face=hit[3],point_cm=list(hit[2].to_tuple())));save()
def hud():
 speed=S['nose'].static_mesh_component.get_physics_linear_velocity().length()/100 if S['launched'] else S['speed']/100;state='IMPACT - R RESET' if S.get('impact_time') else 'FLYING' if S['launched'] else 'READY - SPACE TO FLY' if S.get('assembly_ready') else 'PREPARING PHYSICS';text=f"{state} | {speed*3.6:.0f} km/h | ALT {S['nose'].get_actor_location().z/100:.0f} m\nA/D turn + bank | W/S climb/dive | Q/E rudder | Shift/Ctrl speed | Mouse look\nF level | V camera | T approach | R reset"
 u.SystemLibrary.print_string(S['world'],text,True,False,u.LinearColor(.76,.92,1,1),.25,u.Name('FlightHUD'))
CASES=[dict(name='Fast_Front',preset=0,speed=8000,offset=0,angle=0),dict(name='Slow_Front',preset=0,speed=2000,offset=0,angle=0),dict(name='Angled_Offset',preset=0,speed=8000,offset=1000,angle=9),dict(name='South_Side',preset=1,speed=8000,offset=0,angle=0),dict(name='Steered',preset=0,speed=8000,offset=0,angle=0,steer=True),dict(name='Roof',preset=2,speed=4000,offset=0,angle=0,roof=True)]
def initialize(now):
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
 for cmd in ('r.ScreenPercentage 110','r.MotionBlurQuality 0','r.Tonemapper.Sharpen 0','t.MaxFPS 60'):u.SystemLibrary.execute_console_command(S['world'],cmd,S['pc'])
 S['surface_materials']={town:u.load_asset('/Game/TwinTowers/Flight5/Materials/MI_FlightFacade5_'+town) for town in ('North','South')};ready(0);S.update(initialized=True,test_phase='rest',test_after=time.monotonic()+3,case_index=0,test_flags=set(),last_tick=time.monotonic());check('Native force-body pools load',len(S['joint_pool'])==4096 and len(S['body_pool'])==1536 and len(S['parts'])==13,joints_available=len(S['joint_pool']),wall_bodies_available=len(S['body_pool']),active_wall_bodies=len(S['active']));return True
def test_tick(dt,now):
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
    first,slow,angled,side,steered,roof=S['report']['scenarios'];check('Speed affects physical failure rather than stamping the same damage',first['broken_wall_bonds']!=slow['broken_wall_bonds'] or first['broken_air_joints']!=slow['broken_air_joints'],fast_wall_bonds=first['broken_wall_bonds'],slow_wall_bonds=slow['broken_wall_bonds'],fast_air_joints=first['broken_air_joints'],slow_air_joints=slow['broken_air_joints']);check('Offset and side approaches use their actual contact regions',angled['failure'] is not None and side['failure'] is not None and side['tower']=='South',offset_contact=angled['failure'],side_contact=side['failure']);early=[q for q in steered['native_break_events'] if q['kind']=='air' and q['sim_time_s']<3.8];check('Steering keeps the airframe intact before impact',not early,early_air_failures=early);check('Collision causes native aircraft joint failure',sum(s['broken_air_joints'] for s in S['report']['scenarios'])>0,air_joint_failures=[s['broken_air_joints'] for s in S['report']['scenarios']]);check('Roof impact also uses native breakable structure',roof['failure'] is not None and roof['failure']['face']==4 and roof['broken_wall_bonds']>0,result=roof['failure'])
   S['report']['status']='SUCCESS' if all(q['passed'] for q in S['report']['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
  else:
   S['case_index']+=1;case=CASES[S['case_index']];S['report']['native_break_events']=[];S['report'].pop('first_physics_failure',None);ready(case['preset'],case['speed'],case['offset'],case['angle'],case.get('roof',False));S.update(test_phase='rest',test_after=time.monotonic()+3)
def start():
 S.update(after=time.monotonic()+15,initialized=False,shots=[],report=dict(status='RUNNING' if AUTO else 'INTERACTIVE_READY',revision=6,method='Native Chaos rigid bodies connected with breakable six-degree-of-freedom joints. Native collision forces determine failure; aircraft is driven by bounded forces/torques. No flight-time contact mask removal, prescribed penetration or timed aircraft release.',checks=[],scenarios=[],captures=[],native_break_events=[],runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),settings=CFG))
 save()
 def tick(dt):
  now=time.monotonic()
  if now<S['after']:return
  try:
   if not S['initialized']:initialize(now);return
   dt=min(.05,max(.001,now-S['last_tick']));S['last_tick']=now
   for q in list(S['shots']):
    p=R/'Screenshots'/q['file']
    if p.exists() and p.stat().st_mtime>=q['started'] and p.stat().st_size>5000:S['report']['captures'].append(dict(file=p.name,tag=q['tag'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S['shots'].remove(q);save()
    elif time.time()-q['started']>15:raise RuntimeError('Native screenshot did not arrive: '+q['file'])
   if AUTO:test_tick(dt,now)
   else:
    pc=S['pc'];pressed=lambda k:pc.was_input_key_just_pressed(KEYS[k]);down=lambda k:pc.is_input_key_down(KEYS[k])
    if pressed('R'):S['report']['native_break_events']=[];S['report'].pop('first_physics_failure',None);ready(S['preset'])
    if pressed('T'):S['report']['native_break_events']=[];S['report'].pop('first_physics_failure',None);ready(S['preset']+1)
    if pressed('SpaceBar') or pressed('P'):launch()
    if pressed('V'):S['view']=(S['view']+1)%4;pc.set_view_target_with_blend(S['flight_cams'][S['view']],.2)
    if S['flying']:view.steering(dt,int(down('D'))-int(down('A')),int(down('W'))-int(down('S')),int(down('E'))-int(down('Q')),int(down('LeftShift'))-int(down('LeftControl')),down('F'))
    mx,my=pc.get_input_mouse_delta();S['look_yaw']=max(-110,min(110,S['look_yaw']+mx*.12));S['look_pitch']=max(-65,min(70,S['look_pitch']+my*.12))
    if pressed('F'):S['look_yaw']=S['look_pitch']=0
   physics_tick(dt,now)
   if not AUTO and now-S.get('hud_at',0)>.1:hud();S['hud_at']=now
   if now-S.get('saved_at',0)>1:S['report']['live']=dict(flying=S['flying'],launched=S['launched'],elapsed_s=S['flight_elapsed'],broken_wall_bonds=S['broken_wall'],broken_air_joints=S['broken_air'],view=S['view'],peak_constraint_force=S['peak_force']);save();S['saved_at']=now
  except Exception:
   S['report'].update(status='FAILED',error=traceback.format_exc());save();u.log_error(S['report']['error']);u.unregister_slate_post_tick_callback(S['handle'])
   if AUTO:u.SystemLibrary.quit_game(S.get('world'),S.get('pc'),u.QuitPreference.QUIT,False)
 S['handle']=u.register_slate_post_tick_callback(tick)
