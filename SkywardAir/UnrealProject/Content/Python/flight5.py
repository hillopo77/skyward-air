"""Physical breakaway walls and sectional aircraft penetration prototype.
Controlled approach transitions to separate native rigid bodies at fracture.
"""
import unreal as u,time,json,math,random,hashlib,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[4]/'TwinTowers';D=json.loads((R/'Exports/flight_manifest5.json').read_text());CFG=json.loads((R/'QualitySettings4.json').read_text());CMD=u.SystemLibrary.get_command_line();AUTO='-Flight5Test' in CMD;S={};RNG=random.Random(247)
def key(n):k=u.Key();k.import_text(n);return k
KEYS={n:key(n) for n in ('P','T','V','R','A','D','W','S','Q','E','F','SpaceBar','LeftShift','LeftControl','LeftMouseButton','RightMouseButton')};IGNORE=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore'))
def vec(p):return u.Vector(p[0]*100,-p[1]*100,p[2]*100)
def save():(R/'ArtBible'/('QualityFXProbe.json' if '-QualityFXProbe' in CMD else 'FlightTest5.json' if AUTO else 'FlightSession5.json')).write_text(json.dumps(S['report'],indent=2))
def check(name,passed,**data):S['report']['checks'].append(dict(test=name,passed=bool(passed),**data));save()
def target():
 t=next(t for t in D['towers'] if t['tower']==S['target']);return S['target'],t['centre'][0]*100,-t['front_source_y']*100,17800
def box(a):
 p,e=a.get_actor_bounds(False);return [p.x-e.x,p.x+e.x,p.y-e.y,p.y+e.y,p.z-e.z,p.z+e.z]
def overlap(a,b):return a[0]<b[1] and b[0]<a[1] and a[2]<b[3] and b[2]<a[3] and a[4]<b[5] and b[4]<a[5]
def trace_opening():
 _,x,y,z=target();ignore=[S['carrier'],S['pawn']]+[p['actor'] for p in S['parts']]+[q['actor'] for q in S['cells'] if q['broken']]+S['pool']
 h=u.SystemLibrary.line_trace_single(S['world'],u.Vector(x,y+300,z+120),u.Vector(x,y-1600,z+120),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,u.DrawDebugTrace.NONE,True)
 if not h:return dict(blocking=False)
 v=h.to_tuple();a=v[9];return dict(blocking=bool(v[0]),actor=a.get_actor_label() if a else None,mesh=a.static_mesh_component.static_mesh.get_path_name() if isinstance(a,u.StaticMeshActor) else None,point_cm=list(v[5].to_tuple()))
def shot(tag):
 p=R/'Screenshots'/('Flight5_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'Shot filename="'+str(p).replace('\\','/')+'" -nosuffix',S['pc']);S['shots'].append(dict(file=p.name,tag=tag,started=time.time()));u.log('FLIGHT5_SHOT '+tag)
def mesh_path(aid):return D.get('native_mesh_overrides',{}).get(aid) or ('/Game/TwinTowers/Quality3/Meshes/' if aid.startswith('SM_Q3_') else '/Game/TwinTowers/Damage2/Meshes/')+aid
def burst(point):
 if S.get('dust_start'):return
 S.update(dust_start=time.monotonic(),dust_point=point,fx_sources=[])
 for q in S.get('fine',[]):
  q['actor'].set_actor_location(point,False,True);q['actor'].set_actor_hidden_in_game(False)
  for mid in q['mids']:mid.set_scalar_parameter_value('SimTime',0)
 for j,q in enumerate(S['dust']):
  smoke=q['bank']=='Smoke';rng=random.Random(553+j);q.update(source=None,delay=(.50+(j%128)*.10 if smoke else rng.uniform(0,.85)),offset=u.Vector(rng.uniform(-1100,1100) if smoke else rng.uniform(-450,450),rng.uniform(180,800),rng.uniform(-230,180)),velocity=u.Vector(rng.uniform(-65,65),rng.uniform(25,85),rng.uniform(105,170) if smoke else rng.uniform(-130,-55) if j%3==0 else rng.uniform(25,100)),size=rng.uniform(800,1400) if smoke else rng.uniform(600,1000),phase=rng.uniform(0,6.28),lifetime=rng.uniform(CFG['smoke_duration_s']*.65,CFG['smoke_duration_s']*.82) if smoke else rng.uniform(CFG['dust_duration_s']*.67,CFG['dust_duration_s']),opacity=0);q['mid'].set_vector_parameter_value('Tint',u.LinearColor(.55,.59,.63,1) if smoke else u.LinearColor(.90,.86,.77,1))
def update_dust(now):
 if not S.get('dust_start'):return
 t=now-S['dust_start']
 for q in S.get('fine',[]):
  for mid in q['mids']:mid.set_scalar_parameter_value('SimTime',t)
  if t>20:q['actor'].set_actor_hidden_in_game(True)
 cm=u.GameplayStatics.get_player_camera_manager(S['world'],0);eye=cm.get_camera_location()
 for j,q in enumerate(S['dust']):
  age=t-q['delay'];a=q['actor'];life=q['lifetime'];smoke=q['bank']=='Smoke'
  if age<0 or age>=life:a.set_actor_hidden_in_game(True);q['opacity']=0;continue
  if q['source'] is None:
   sources=S['fx_sources'];q['source']=sources[(j*17)%len(sources)] if sources and not smoke else S['dust_point']
  a.set_actor_hidden_in_game(False);spread=1+min(age,4)*(.11 if smoke else .23);curl=u.Vector(math.sin(age*.53+q['phase'])*min(age*42,300),math.cos(age*.47+q['phase'])*min(age*23,160),math.sin(age*.39+q['phase'])*65);p=q['source']+q['offset']*spread+q['velocity']*age+curl;a.set_actor_location(p,False,True);a.set_actor_rotation(u.MathLibrary.make_rot_from_z(eye-p),False);size=min(4000,q['size']+age*(110 if smoke else 260));a.set_actor_scale3d(u.Vector(size/100,size*(1.15 if smoke else .82)/100,1));fade_in=min(1,age/(1.2 if smoke else .30));fade_out=max(0,1-age/life)**(1.35 if smoke else 1.7);opacity=(.72 if smoke else .65)*fade_in*fade_out;q['opacity']=opacity;q['mid'].set_scalar_parameter_value('Opacity',opacity)
  frame=age*(1.45 if smoke else 2.15)+j*.31;frame=15-abs((frame%30)-15) if smoke else min(15,frame);f0=int(frame);f1=min(15,f0+1)
  for name,index in [('OffsetA',f0),('OffsetB',f1)]:q['mid'].set_vector_parameter_value(name,u.LinearColor((index%4)*.25+.0078125,(index//4)*.25+.0078125,0,0))
  q['mid'].set_scalar_parameter_value('FrameBlend',frame-f0)
def fx_snapshot(age):
 data=[]
 for bank in ('Dust','Smoke'):
  q=[q for q in S['dust'] if q['bank']==bank and q.get('opacity',0)>.01];data.append(dict(bank=bank,visible=len(q),max_opacity=max([x['opacity'] for x in q]+[0]),mean_height_above_impact_m=sum(x['actor'].get_actor_location().z-S['dust_point'].z for x in q)/max(1,len(q))/100))
 S['report'].setdefault('effect_evolution',[]).append(dict(age_s=age,layers=data,fine_batches=len(S.get('fine',[])),fine_pieces=D.get('fine_piece_count',0)));save()
def fx_probe():
 cam=S['cameras']['Entry'];S['pc'].set_view_target_with_blend(cam,0);eye=cam.get_actor_location();f=u.MathLibrary.get_forward_vector(cam.get_actor_rotation());right=u.MathLibrary.get_right_vector(cam.get_actor_rotation());dust=[q for q in S['dust'] if q['bank']=='Dust'];smoke=[q for q in S['dust'] if q['bank']=='Smoke'];chosen=[dust[0],smoke[0],dust[1]];out=[]
 for j,q in enumerate(chosen):
  a=q['actor'];p=eye+f*3500+right*((j-1)*1800);a.set_actor_location(p,False,True);a.set_actor_rotation(u.MathLibrary.make_rot_from_z(eye-p),False);a.set_actor_scale3d(u.Vector(15,15,15));a.set_actor_hidden_in_game(False);c=a.static_mesh_component;c.set_visibility(True);c.set_hidden_in_game(False);c.set_render_in_main_pass(True)
  if j==2:q['mid']=a.static_mesh_component.create_dynamic_material_instance(0,u.load_asset('/Game/TwinTowers/Materials/MI_TT_Aluminium'))
  mid=q['mid'];mid.set_scalar_parameter_value('Opacity',1);mid.set_scalar_parameter_value('FrameBlend',0);mid.set_vector_parameter_value('Tint',u.LinearColor(1,1,1,1));mid.set_vector_parameter_value('OffsetA',u.LinearColor(.0078125,.0078125,0,0));mid.set_vector_parameter_value('OffsetB',u.LinearColor(.0078125,.0078125,0,0));out.append(dict(bank=q['bank'],control=j==2,location=str(p),bounds=box(a),component_visible=a.static_mesh_component.get_editor_property('visible'),opacity=mid.get_scalar_parameter_value('Opacity')))
 S['report']['fx_probe']=out;save()
def shard(point,velocity):
 if S['pool_index']>=len(S['pool']):return
 a=S['pool'][S['pool_index']];S['pool_index']+=1;c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_location(point,False,True);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');c.set_enable_gravity(True);c.set_simulate_physics(True);c.set_mass_override_in_kg(u.Name('None'),9,True);c.set_physics_linear_velocity(velocity*.18+u.Vector(RNG.uniform(-170,170),RNG.uniform(-100,90),RNG.uniform(-130,150)),False);c.set_physics_angular_velocity_in_degrees(u.Vector(RNG.uniform(-100,100),RNG.uniform(-80,80),RNG.uniform(-80,80)),False)
def break_cell(q,velocity):
 if q['broken']:return
 a=q['actor'];c=a.static_mesh_component;c.set_simulate_physics(False);bent=S['bent'].get(q.get('bent_asset',q['asset']+'_Bent'))
 if bent:c.set_static_mesh(bent)
 c.set_collision_profile_name('PhysicsActor');c.set_collision_object_type(u.CollisionChannel.ECC_DESTRUCTIBLE);c.set_collision_response_to_channel(u.CollisionChannel.ECC_VEHICLE,IGNORE);a.set_actor_enable_collision(True);c.set_enable_gravity(True);c.set_simulate_physics(True);c.set_mass_override_in_kg(u.Name('None'),CFG['wall_fragment_mass_game_kg'] if q['kind']=='facade' else CFG['deck_fragment_mass_game_kg'],True);c.set_linear_damping(.28);c.set_angular_damping(.60);c.set_physics_linear_velocity(velocity*CFG['wall_fragment_velocity_fraction']+u.Vector(RNG.uniform(-55,55),RNG.uniform(-60,10),RNG.uniform(-35,55)),False);c.set_physics_angular_velocity_in_degrees(u.Vector(RNG.uniform(-20,20),RNG.uniform(-18,18),RNG.uniform(-24,24)),False);q.update(broken=True,break_time=time.monotonic(),start_z=a.get_actor_location().z)
 if q['kind']=='facade':
  bb=q['bounds'];point=u.Vector((bb[0]+bb[1])/2,(bb[2]+bb[3])/2,(bb[4]+bb[5])/2);S.setdefault('fx_sources',[]).append(point)
  if RNG.random()<.30:shard(point,velocity)
 S['report']['fractured_cells'].append(dict(actor=q['name'],kind=q['kind'],tower=q['tower'],micro=q.get('micro',False),position_cm=list(a.get_actor_location().to_tuple())));S['dirty']=True
def release(p,velocity):
 if p['released']:return
 a=p['actor'];c=a.static_mesh_component;a.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD)
 if p['part']=='Nose' and S['crushed_nose']:c.set_static_mesh(S['crushed_nose'])
 a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');c.set_collision_object_type(u.CollisionChannel.ECC_VEHICLE);c.set_collision_response_to_channel(u.CollisionChannel.ECC_DESTRUCTIBLE,IGNORE);c.set_collision_response_to_channel(u.CollisionChannel.ECC_VEHICLE,IGNORE);c.set_enable_gravity(True);c.set_simulate_physics(True);mass=900 if p['part'].startswith('Engine') else 650 if p['part'].startswith('Wing') else 1100;c.set_mass_override_in_kg(u.Name('None'),mass,True);c.set_linear_damping(CFG['aircraft_fragment_linear_damping']);c.set_angular_damping(.55)
 if hasattr(c,'set_use_ccd'):c.set_use_ccd(True)
 c.set_physics_linear_velocity(velocity*CFG['aircraft_release_velocity_fraction'],False);sign=-1 if 'L' in p['part'] else 1;c.set_physics_angular_velocity_in_degrees(u.Vector(RNG.uniform(-5,5),RNG.uniform(-7,7),sign*RNG.uniform(4,16) if p['part'].startswith('Wing') else RNG.uniform(-3,3)),False);p.update(released=True,release_time=time.monotonic());S['report']['released_parts'].append(p['part']);save()
def launch():
 if S.get('flying'):return
 _,x,y,z=target();a=S['carrier'];c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_rotation(u.Rotator(yaw=180),False);a.set_actor_location(u.Vector(x,y+32000,z),False,True);a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');c.set_collision_response_to_all_channels(IGNORE);c.set_enable_gravity(False);c.set_simulate_physics(True);c.set_linear_damping(0);c.set_physics_linear_velocity(u.Vector(0,-CFG['aircraft_approach_speed_cm_s'],0),False)
 for p in S['parts']:p['actor'].set_actor_hidden_in_game(False)
 S.update(flying=True,launch_time=time.monotonic(),stage='flight',approach_shot=False,entry_shot=False,side_shot=False,breakup_shot=False,deep_shot=False,hole_shot=False,after_shot=False,fx_snap_early=False,fx_snap_late=False);S['report']['opening_before']=trace_opening();before=S['report']['opening_before'];check('Intact breakable facade has actual collision before impact',before['blocking'] and str(before.get('actor','')).startswith('BreakCell '),surface=before);save()
def reset():
 carrier=S['carrier'];carrier.static_mesh_component.set_simulate_physics(False);carrier.set_actor_rotation(u.Rotator(),False);carrier.set_actor_location(u.Vector(0,70000,17800),False,True);carrier.set_actor_enable_collision(False)
 for q in S['cells']:
  a=q['actor'];c=a.static_mesh_component;c.set_simulate_physics(False);c.set_static_mesh(q['mesh']);a.set_actor_transform(q['transform'],False,True);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');q['broken']=False
 for p in S['parts']:
  a=p['actor'];c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);c.set_collision_profile_name('NoCollision');c.set_static_mesh(p['mesh']);a.set_actor_rotation(u.Rotator(),False);o=p['origin'];a.set_actor_location(carrier.get_actor_location()+u.Vector(o[0]*100,-(o[1]-17.3)*100,o[2]*100),False,True);a.attach_to_actor(carrier,u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False);a.set_actor_hidden_in_game(True);p['released']=False
 for a in S['pool']:a.static_mesh_component.set_simulate_physics(False);a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
 for q in S['dust']:q['actor'].set_actor_hidden_in_game(True);q['mid'].set_scalar_parameter_value('Opacity',0)
 for q in S.get('fine',[]):
  q['actor'].set_actor_hidden_in_game(True)
  for mid in q['mids']:mid.set_scalar_parameter_value('SimTime',-100)
 S.update(flying=False,impact_time=None,dust_start=None,pool_index=0,fx_sources=[])
def set_target():
 _,x,y,z=target()
 for tag,off,tgt in [('Entry',(-8000,14500,1800),(0,-1200,0)),('Side',(-13000,9000,2500),(0,-2000,0)),('Hole',(-2500,10000,500),(0,-1600,0))]:
  a=S['cameras'][tag];p=u.Vector(x+off[0],y+off[1],z+off[2]);a.set_actor_location(p,False,True);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(x+tgt[0],y+tgt[1],z+tgt[2])),False)
GRID=(300,600,210)
def bins(bb):
 return ((x,y,z) for x in range(math.floor(bb[0]/GRID[0]),math.floor(bb[1]/GRID[0])+1) for y in range(math.floor(bb[2]/GRID[1]),math.floor(bb[3]/GRID[1])+1) for z in range(math.floor(bb[4]/GRID[2]),math.floor(bb[5]/GRID[2])+1))
def build_grid():
 S['grid']={}
 for q in S['cells']:
  for k in bins(q['bounds']):S['grid'].setdefault(k,[]).append(q)
def fracture_samples(p,velocity,lookahead):
 a=p['actor'];o=a.get_actor_location();r=a.get_actor_rotation();ax=u.MathLibrary.get_forward_vector(r);ay=u.MathLibrary.get_right_vector(r);az=u.MathLibrary.get_up_vector(r);radius=CFG['surface_probe_radius_cm'];dx,dy,dz=velocity.x*lookahead,velocity.y*lookahead,velocity.z*lookahead
 for lx,ly,lz in p['fracture_samples_cm']:
  x=o.x+ax.x*lx+ay.x*ly+az.x*lz;y=o.y+ax.y*lx+ay.y*ly+az.y*lz;z=o.z+ax.z*lx+ay.z*ly+az.z*lz;bb=(x+min(0,dx)-radius,x+max(0,dx)+radius,y+min(0,dy)-radius,y+max(0,dy)+radius,z+min(0,dz)-radius,z+max(0,dz)+radius)
  for k in bins(bb):
   for q in S['grid'].get(k,()):
    if not q['broken'] and q['tower']==S['target'] and overlap(bb,q['bounds']):break_cell(q,velocity)
def physics_tick(dt,now):
 if not S.get('flying'):return
 _,x,front,z=target();carrier_v=S['carrier'].static_mesh_component.get_physics_linear_velocity();margin=CFG['fracture_contact_margin_cm'];age=now-S['impact_time'] if S.get('impact_time') else 0
 if age<12:
  for p in S['parts']:
   a=p['actor'];bb=box(a);v=a.static_mesh_component.get_physics_linear_velocity() if p['released'] else carrier_v;lookahead=min(.04,max(dt,.016))*1.25;leading=bb[2]+min(0,v.y)*lookahead-margin
   if not S.get('impact_time') and leading<=front+30 and bb[3]>=front-500 and bb[0]<x+3100 and bb[1]>x-3100:S['impact_time']=now;S['report']['first_fracture_time_s']=now-S['launch_time'];S['report']['contact_part']=p['part'];burst(u.Vector(x,front+80,z));save()
   if S.get('impact_time') and leading<front+1200:
    fracture_samples(p,v,lookahead)
    if not p['released'] and bb[2]<=front+margin:release(p,carrier_v)
 update_dust(now)
 if S.get('dirty'):save();S['dirty']=False
 if now-S['launch_time']>12 and not S.get('impact_time'):raise RuntimeError('Aircraft never reached the breakaway facade')

# Flight5: the field is instanced for draw efficiency, with native bodies for failures.
from flight_layout5 import layout,rotate
CFG.update(start_distance_cm=43000,initial_speed_cm_s=8000,minimum_speed_cm_s=6500,maximum_speed_cm_s=10500,maximum_bank_degrees=30,maximum_pitch_degrees=16,notes='Artistic flight and fracture simulation. Full-height removable exterior fields on both towers, localized floor decks around actual contact, native main fragments and shader-batched fine debris. No engineering failure prediction or fluid solver.')
def mesh_path(aid):return D['flight_asset_root']+aid if aid in D['flight_assets']['assets'] else D.get('native_mesh_overrides',{}).get(aid) or ('/Game/TwinTowers/Quality3/Meshes/' if aid.startswith('SM_Q3_') else '/Game/TwinTowers/Damage2/Meshes/')+aid
def transform(q):return u.Transform(location=u.Vector(*q['location']),rotation=u.Rotator(yaw=q['yaw']),scale=u.Vector(*q['scale']))
def attached(a,parent):a.attach_to_actor(parent,u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
def local_to_world(a,p):
 r=a.get_actor_rotation();return a.get_actor_location()+u.MathLibrary.get_forward_vector(r)*p.x+u.MathLibrary.get_right_vector(r)*p.y+u.MathLibrary.get_up_vector(r)*p.z
def bounds(q):
 aid=q['asset']
 if aid not in S['asset_bounds']:
  b=u.load_asset(mesh_path(aid)).get_bounding_box();S['asset_bounds'][aid]=list(b.min.to_tuple())+list(b.max.to_tuple())
 b=S['asset_bounds'][aid];sx,sy,sz=q['scale'];side=int(round(-q['yaw']/90))%4;pts=[rotate(x*sx,y*sy,side) for x in (b[0],b[3]) for y in (b[1],b[4])];x,y,z=q['location'];return [x+min(p[0] for p in pts),x+max(p[0] for p in pts),y+min(p[1] for p in pts),y+max(p[1] for p in pts),z+b[2]*sz,z+b[5]*sz]
def add_grid(q):
 for k in bins(q['bounds']):S['grid'].setdefault(k,[]).append(q)
def mark_field():
 for c,q in S.get('field_dirty',{}).values():c.update_instance_transform(q['index'],u.Transform(location=u.Vector(0,0,-100000)),False,True,True)
 S['field_dirty']={}
def break_cell(q,velocity):
 if q['broken']:return
 q.update(broken=True,break_time=time.monotonic());S['broken'].append(q)
 if q.get('component'):
  c=q['component'];c.update_instance_transform(q['index'],u.Transform(location=u.Vector(0,0,-100000)),False,False,True);S['field_dirty'][id(c)]=(c,q)
  if S['break_index']<len(S['break_pool']):a=S['break_pool'][S['break_index']];S['break_index']+=1
  else:a=None
 else:a=q['actor']
 point=u.Vector(*q['location']);bb=q['bounds'];centre=u.Vector((bb[0]+bb[1])/2,(bb[2]+bb[3])/2,(bb[4]+bb[5])/2)
 if a:
  c=a.static_mesh_component;c.set_simulate_physics(False);c.set_static_mesh(S['bent'][q['bent_asset']]);a.set_actor_transform(transform(q),False,True);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True);c.set_collision_profile_name('PhysicsActor');c.set_collision_object_type(u.CollisionChannel.ECC_DESTRUCTIBLE);c.set_collision_response_to_channel(u.CollisionChannel.ECC_VEHICLE,IGNORE);c.set_enable_gravity(True);c.set_simulate_physics(True);c.set_mass_override_in_kg(u.Name('None'),1800 if q['kind'] in ('deck','roof') else 180,True);c.set_linear_damping(.28);c.set_angular_damping(.6);c.set_physics_linear_velocity(velocity*.13+u.Vector(RNG.uniform(-60,60),RNG.uniform(-60,60),RNG.uniform(-35,55)),False);c.set_physics_angular_velocity_in_degrees(u.Vector(RNG.uniform(-25,25),RNG.uniform(-25,25),RNG.uniform(-25,25)),False)
 if q['kind']=='facade':S.setdefault('fx_sources',[]).append(centre)
 S['report']['fractured_cells'].append(dict(tower=q['tower'],kind=q['kind'],side=q.get('side'),floor=q.get('floor'),position_cm=list(centre.to_tuple())));S['dirty']=True
def make_decks(point,town):
 spec=next(t for t in D['towers'] if t['tower']==town);pitch=spec['floor_pitch']*100;floor=int((point.z-2280)/pitch);cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100
 for i,a in enumerate(S['decks']):
  level=floor-3+i//36;ix=(i%36)//6;iy=i%6;aid='SM_TT2_Deck';q=dict(actor=a,name=a.get_actor_label(),asset=aid,bent_asset='SM_Q3_Deck_Torn'+str(i%3),tower=town,kind='deck',location=[cx+(ix-2.5)*980,cy+(iy-2.5)*980,max(2280,min(spec['height']*100-20,2280+level*pitch))],yaw=0,scale=[1,1,1],broken=False,floor=level,side=4);a.set_actor_transform(transform(q),False,True);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True);a.static_mesh_component.set_collision_profile_name('PhysicsActor');q['bounds']=box(a);S['active_decks'].append(q);add_grid(q)
def start_impact(q,point,part,now):
 if S.get('impact_time'):return
 S.update(impact_time=now,impact_point=point,hit_tower=q['tower'],hit_side=q.get('side',0));make_decks(point,q['tower']);burst(point)
 # Fine fragments and smoke use the actual face orientation, not the old fixed test site.
 side=q.get('side',0)%4
 for fx in S['dust']:
  o=fx['offset'];v=fx['velocity'];x,y=rotate(o.x,o.y,side);vx,vy=rotate(v.x,v.y,side);fx['offset']=u.Vector(x,y,o.z);fx['velocity']=u.Vector(vx,vy,v.z)
 S['report'].update(first_contact=dict(tower=q['tower'],face=side,part=part,point_cm=list(point.to_tuple()),elapsed_s=S['flight_elapsed'],speed_m_s=S['speed']/100,bank_degrees=S['bank'],pitch_degrees=S['pitch']),opening_before=trace_hit(point,side));save()
 for a in S['rig']:attached(a,S['nose'])
 set_impact_camera(point,side);S['view']=2;S['pc'].set_view_target_with_blend(S['flight_cams'][2],.20)
def trace_hit(p,side):
 dx,dy=rotate(0,1,side%4);start=p+u.Vector(dx*400,dy*400,30);end=p-u.Vector(dx*900,dy*900,-30);ignore=[S['carrier'],S['pawn']]+[p['actor'] for p in S['parts']]+S['rig']+S['break_pool']+S['pool']
 h=u.SystemLibrary.line_trace_single(S['world'],start,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,u.DrawDebugTrace.NONE,True)
 if not h:return dict(blocking=False)
 v=h.to_tuple();a=v[9];return dict(blocking=bool(v[0]),actor=a.get_actor_label() if a else None,point_cm=list(v[5].to_tuple()))
def fracture_samples(p,velocity,lookahead):
 a=p['actor'];o=a.get_actor_location();r=a.get_actor_rotation();ax=u.MathLibrary.get_forward_vector(r);ay=u.MathLibrary.get_right_vector(r);az=u.MathLibrary.get_up_vector(r);radius=CFG['surface_probe_radius_cm'];dx,dy,dz=velocity.x*lookahead,velocity.y*lookahead,velocity.z*lookahead;hits=0
 for lx,ly,lz in p['fracture_samples_cm']:
  x=o.x+ax.x*lx+ay.x*ly+az.x*lz;y=o.y+ax.y*lx+ay.y*ly+az.y*lz;z=o.z+ax.z*lx+ay.z*ly+az.z*lz;bb=(x+min(0,dx)-radius,x+max(0,dx)+radius,y+min(0,dy)-radius,y+max(0,dy)+radius,z+min(0,dz)-radius,z+max(0,dz)+radius)
  for k in bins(bb):
   for q in list(S['grid'].get(k,())):
    if not q['broken'] and overlap(bb,q['bounds']):
     if not S.get('impact_time'):
      qb=q['bounds'];point=u.Vector(max(qb[0],min(x,qb[1])),max(qb[2],min(y,qb[3])),max(qb[4],min(z,qb[5])));start_impact(q,point,p['part'],time.monotonic())
     break_cell(q,velocity);hits+=1
 return hits
def set_impact_camera(p,side):
 x,y=rotate(-12500,12500,side%4);eye=p+u.Vector(x,y,2800);a=S['flight_cams'][2];a.set_actor_location(eye,False,True);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye,p+u.Vector(0,0,100)),False)
def attitude():
 alpha=math.radians(S['heading']);theta=math.radians(S['pitch']);phi=math.radians(S['bank']);f=u.Vector(math.cos(theta)*math.cos(alpha),math.cos(theta)*math.sin(alpha),math.sin(theta));r=u.Vector(-math.sin(alpha),math.cos(alpha),0);up=u.Vector(-math.sin(theta)*math.cos(alpha),-math.sin(theta)*math.sin(alpha),math.cos(theta));return f,up*math.cos(phi)+r*math.sin(phi)
def steering(dt,roll=0,pitch=0,rudder=0,throttle=0,level=False):
 S['bank']+=(roll*30-S['bank'])*min(1,dt*2.8);S['pitch']+=(pitch*16-S['pitch'])*min(1,dt*2.1);S['speed']=max(6500,min(10500,S['speed']+throttle*1400*dt));S['heading']+=(math.sin(math.radians(S['bank']))*32+rudder*9)*dt
 if level:S['bank']*=max(0,1-dt*5);S['pitch']*=max(0,1-dt*5)
def ready(preset=0):
 reset();S['preset']=preset%3;spec=next(t for t in D['towers'] if t['tower']==('South' if preset%3==1 else 'North'));cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;side=1 if preset%3==1 else 0;x,y=rotate(0,3152.92+43000,side);heading=180 if side==1 else -90;z=22000 if side==1 else 17800 if preset%3==0 else 28000
 S.update(target=spec['tower'],heading=heading,pitch=0,bank=0,speed=8000,flight_elapsed=0,flying=False,flight_velocity=u.Vector(),view=0,look_yaw=0,look_pitch=0,start_location=u.Vector(cx+x,cy+y,z));f,up=attitude();S['carrier'].set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,up),False);S['carrier'].set_actor_location(S['start_location'],False,True);S['pc'].set_view_target_with_blend(S['flight_cams'][0],0);camera_tick(.016);S['report']['ready']=dict(preset=S['preset'],tower=S['target'],side=side,distance_root_to_facade_m=430,speed_m_s=80,estimated_nose_contact_s=(430-27.3)/80);save()
def reset():
 carrier=S['carrier'];carrier.static_mesh_component.set_simulate_physics(False);carrier.set_actor_rotation(u.Rotator(),False);carrier.set_actor_location(u.Vector(),False,True);carrier.set_actor_enable_collision(False)
 for q in S.get('broken',[]):
  if q.get('component'):q['component'].update_instance_transform(q['index'],transform(q),False,True,True)
  q['broken']=False
 for q in S.get('active_decks',[]):
  for k in bins(q['bounds']):
   if k in S['grid']:S['grid'][k]=[x for x in S['grid'][k] if x is not q]
 for a in S.get('break_pool',[])+S.get('decks',[])+S['pool']:
  a.static_mesh_component.set_simulate_physics(False);a.set_actor_enable_collision(False);a.static_mesh_component.set_collision_profile_name('NoCollision');a.set_actor_hidden_in_game(True);a.set_actor_location(u.Vector(0,0,-70000),False,True)
 for p in S['parts']:
  a=p['actor'];c=a.static_mesh_component;c.set_simulate_physics(False);a.set_actor_enable_collision(False);c.set_collision_profile_name('NoCollision');c.set_static_mesh(p['mesh']);a.set_actor_rotation(u.Rotator(),False);o=p['origin'];a.set_actor_location(u.Vector(o[0]*100,-(o[1]-17.3)*100,o[2]*100),False,True);attached(a,carrier);a.set_actor_hidden_in_game(False);p['released']=False
 for item in S['rig_original']:
  a=item['actor'];a.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD);a.set_actor_location(item['local'],False,True);a.set_actor_rotation(item['rotation'],False);attached(a,carrier)
 for q in S['dust']:q['actor'].set_actor_hidden_in_game(True);q['mid'].set_scalar_parameter_value('Opacity',0)
 for q in S.get('fine',[]):
  q['actor'].set_actor_hidden_in_game(True)
  for m in q['mids']:m.set_scalar_parameter_value('SimTime',-100)
 S.update(flying=False,impact_time=None,dust_start=None,pool_index=0,break_index=0,fx_sources=[],broken=[],active_decks=[],field_dirty={});S['report'].update(fractured_cells=[],released_parts=[])
def launch():
 if S.get('flying') or S.get('impact_time'):return
 S.update(flying=True,launch_time=time.monotonic(),flight_elapsed=0);S['report']['launch_time_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
def camera_tick(dt):
 root=S['carrier'];after=bool(S.get('impact_time'));basis=S['nose'] if after else root;seat=u.Vector(110,2054,160)
 if after:
  o=next(p['origin'] for p in S['parts'] if p['part']=='Nose');seat-=u.Vector(o[0]*100,-(o[1]-17.3)*100,o[2]*100)
 eye=local_to_world(basis,seat);r=basis.get_actor_rotation();f=u.MathLibrary.get_right_vector(r);right=-u.MathLibrary.get_forward_vector(r);up=u.MathLibrary.get_up_vector(r);ya=math.radians(S['look_yaw']);pi=math.radians(S['look_pitch']);forward=f*math.cos(ya)*math.cos(pi)+right*math.sin(ya)*math.cos(pi)+up*math.sin(pi);cam=S['flight_cams'][0];cam.set_actor_location(eye,False,True);cam.set_actor_rotation(u.MathLibrary.make_rot_from_xz(forward,up),False)
 if not after:
  p=root.get_actor_location();chase=S['flight_cams'][1];desired=p-f*7500+u.Vector(0,0,1900);old=chase.get_actor_location();pos=desired if not S.get('flying') else old+(desired-old)*min(1,dt*6);chase.set_actor_location(pos,False,True);chase.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,p+f*1200),False)
def physics_tick(dt,now):
 if S.get('flying'):
  S['flight_elapsed']+=dt;f,up=attitude();v=f*S['speed'];S['flight_velocity']=v;carrier=S['carrier'];carrier.set_actor_rotation(u.MathLibrary.make_rot_from_yz(f,up),False);carrier.set_actor_location(carrier.get_actor_location()+v*dt,False,True)
  # Scan only around actual aircraft surface samples, on all four faces of both towers.
  if not S.get('impact_time') or now-S['impact_time']<10:
   for p in S['parts']:
    v=p['actor'].static_mesh_component.get_physics_linear_velocity() if p['released'] else S['flight_velocity'];hits=fracture_samples(p,v,min(.045,max(dt,.016)))
    if hits and not p['released']:release(p,S['flight_velocity'])
   mark_field()
  if S.get('impact_time'):
   age=now-S['impact_time']
   if age>.7:
    for p in S['parts']:
     if not p['released']:release(p,S['flight_velocity']*.72)
   if age>2:S['flying']=False
  if S['carrier'].get_actor_location().z<0 or S['flight_elapsed']>45:S['flying']=False
 update_dust(now);camera_tick(dt)
 if S.get('dirty') and now-S.get('last_save',0)>.5:save();S.update(dirty=False,last_save=now)
def hud():
 state='IMPACT - R RESET' if S.get('impact_time') else 'FLYING' if S.get('flying') else 'READY - SPACE TO FLY'
 text=f"{state}    {S['speed']*.036:.0f} km/h    ALT {S['carrier'].get_actor_location().z/100:.0f} m    BANK {S['bank']:+.0f} deg\nA/D bank + turn | W/S climb/dive | Q/E rudder | Shift/Ctrl speed\nMouse look | F level | V pilot/chase/impact/overview | T approach | R reset"
 u.SystemLibrary.print_string(S['world'],text,True,False,u.LinearColor(.76,.92,1,1),.25,u.Name('FlightHUD'))
def snapshot():return dict(tower=S.get('hit_tower'),contact=S['report'].get('first_contact'),fractured=len(S['broken']),facade=sum(q['kind']=='facade' for q in S['broken']),deck=sum(q['kind']=='deck' for q in S['broken']),released=[p['part'] for p in S['parts'] if p['released']],opening=trace_hit(S['impact_point'],S['hit_side']),travel_m=(S['carrier'].get_actor_location()-S['start_location']).length()/100)
def test_tick(dt,now):
 phase=S['test_phase']
 if phase=='ready' and now>S['test_after'] and not S['shots']:shot('00_Seated_Captain');S.update(test_phase='pilot_wait',test_after=now+.7)
 elif phase=='pilot_wait' and not S['shots'] and now>S['test_after']:launch();S['test_phase']='flight'
 elif phase=='flight':
  t=S['flight_elapsed'];steering(dt,roll=.24 if .4<t<1.45 else -.24 if 1.45<t<2.5 else 0)
  if t>1.2 and 'bank' not in S['test_flags']:shot('01_Banking_From_Seat');S['test_flags'].add('bank');S['report']['steering_sample']=dict(bank=S['bank'],heading=S['heading'],location_cm=list(S['carrier'].get_actor_location().to_tuple()))
  if t>2.7 and 'chase' not in S['test_flags'] and not S['shots']:S['view']=1;S['pc'].set_view_target_with_blend(S['flight_cams'][1],0);S['test_flags'].add('chase');S['test_after']=now+.6
  if 'chase' in S['test_flags'] and 'chaseshot' not in S['test_flags'] and now>S['test_after']:shot('02_Flyable_Exterior');S['test_flags'].add('chaseshot')
  if S.get('impact_time'):S.update(test_phase='impact',test_after=now+.5)
  elif t>12:raise RuntimeError('Flight test missed its tower')
 elif phase=='impact':
  age=now-S['impact_time']
  if age>.5 and 'entry' not in S['test_flags'] and not S['shots']:shot('03_Player_Path_Impact');S['test_flags'].add('entry')
  if age>4 and 'dust' not in S['test_flags'] and not S['shots']:shot('04_Fine_Debris_And_Smoke');fx_snapshot(age);S['test_flags'].add('dust')
  if age>12 and 'smoke' not in S['test_flags'] and not S['shots']:shot('05_Rising_Smoke');fx_snapshot(age);S['test_flags'].add('smoke')
  if age>16 and not S['shots']:
   first=snapshot();S['report']['scenarios']=[first];check('Five-second pilot approach reaches the actual facade',3.9<first['contact']['elapsed_s']<6.5,contact=first['contact']);check('Bank controls change aircraft attitude',abs(S['report']['steering_sample']['bank'])>2,sample=S['report']['steering_sample']);check('Native parts and localized facade/deck fracture at contact',len(first['released'])==13 and first['facade']>50 and first['deck']>0,result=first);check('The wall has a physical opening after impact',not first['opening']['blocking'],trace=first['opening']);save();ready(1);S.update(test_phase='second_ready',test_after=now+1)
 elif phase=='second_ready' and now>S['test_after'] and not S['shots']:shot('06_Second_Approach_South_Side');S.update(test_phase='second_wait',test_after=now+.6)
 elif phase=='second_wait' and now>S['test_after'] and not S['shots']:launch();S['test_phase']='second_flight';S['view']=1;S['pc'].set_view_target_with_blend(S['flight_cams'][1],0)
 elif phase=='second_flight':
  steering(dt)
  if S.get('impact_time'):S.update(test_phase='second_impact',test_after=now+4)
  elif S['flight_elapsed']>12:raise RuntimeError('Second flight missed tower')
 elif phase=='second_impact' and now>S['test_after'] and not S['shots']:shot('07_Different_Impact_Location');S.update(test_phase='overview_wait',test_after=now+1)
 elif phase=='overview_wait' and not S['shots'] and now>S['test_after']:S['pc'].set_view_target_with_blend(S['flight_cams'][3],0);S.update(test_phase='overview',test_after=now+2)
 elif phase=='overview' and not S['shots'] and now>S['test_after']:shot('08_Filtered_Facade_Overview');S.update(test_phase='finish',test_after=now+1)
 elif phase=='finish' and not S['shots'] and now>S['test_after']:
  second=snapshot();S['report']['scenarios'].append(second);check('Damage follows a different tower, face and height',second['tower']=='South' and second['contact']['face']==1 and second['contact']['point_cm'][2]>21000 and second['facade']>50,result=second);check('Second impact also opens actual collision geometry',not second['opening']['blocking'],trace=second['opening']);check('Requested fine debris and enlarged smoke pools loaded',len(S['fine'])==8 and len(S['dust'])==248,fine_piece_count=2400,layers=len(S['dust']));S['report']['status']='SUCCESS' if all(q['passed'] for q in S['report']['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
def initialize(now):
 for w in u.ObjectIterator():
  if isinstance(w,u.World):
   pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_pawn(w,0) if pc else None
   if pc and pawn:S.update(world=w,pc=pc,pawn=pawn);break
 if not S.get('pc'):return False
 S['pawn'].disable_input(S['pc']);S['pc'].set_editor_property('show_mouse_cursor',False)
 actors=u.GameplayStatics.get_all_actors_of_class(S['world'],u.Actor);by={a.get_actor_label():a for a in actors};S['carrier']=by['Unmanned aircraft carrier2'];S['parts']=[]
 for p in D['aircraft']:
  a=by['AirPart '+p['part']];S['parts'].append(dict(p,actor=a,mesh=a.static_mesh_component.static_mesh,released=False))
 S['nose']=by['AirPart Nose'];S['rig']=[a for a in actors if a.get_actor_label().startswith('Cockpit5 ')];origin=S['carrier'].get_actor_location();S['rig_original']=[dict(actor=a,local=a.get_actor_location()-origin,rotation=a.get_actor_rotation()) for a in S['rig']]
 S['pool']=sorted([a for a in actors if a.get_actor_label().startswith('DamagePool ')],key=lambda a:a.get_actor_label());S['break_pool']=sorted([a for a in actors if a.get_actor_label().startswith('BreakPool5 ')],key=lambda a:a.get_actor_label());S['decks']=sorted([a for a in actors if a.get_actor_label().startswith('Deck5 ')],key=lambda a:a.get_actor_label());S.update(asset_bounds={},cells=[],grid={},broken=[],active_decks=[],field_dirty={})
 for spec in D['towers']:
  a=by['Structure5 '+spec['tower']];cs={str(t):c for c in a.get_components_by_class(u.InstancedStaticMeshComponent) for t in c.component_tags}
  for q in layout(spec,D['flight_assets']):q.update(component=cs[q['tag']],broken=False);q['bounds']=bounds(q);S['cells'].append(q);add_grid(q)
 S['bent']={aid:u.load_asset(mesh_path(aid)) for aid in {q['bent_asset'] for q in S['cells']}|{'SM_Q3_Deck_Torn0','SM_Q3_Deck_Torn1','SM_Q3_Deck_Torn2'}};S['crushed_nose']=u.load_asset('/Game/TwinTowers/Damage2/Meshes/SM_TT2_Air_Nose_Crushed');S['dust']=[dict(actor=a,bank=a.get_actor_label().split()[1],mid=a.static_mesh_component.create_dynamic_material_instance(0)) for a in actors if a.get_actor_label().startswith('FX3 ')];S['fine']=[dict(actor=a,mids=[a.static_mesh_component.create_dynamic_material_instance(i) for i in range(2)]) for a in actors if a.get_actor_label().startswith('FineBatch4 ')]
 for q in S['dust']:
  c=q['actor'].static_mesh_component;c.set_visibility(True);c.set_hidden_in_game(False);c.set_render_in_main_pass(True)
 S['flight_cams']=[by['CAM_Flight5_'+tag] for tag in ('Pilot','Chase','Impact')]+[by['CAM_TT_Hero']];hero=S['flight_cams'][3];hp=u.Vector(-18000,95000,26500);hero.set_actor_location(hp,False,True);hero.set_actor_rotation(u.MathLibrary.find_look_at_rotation(hp,u.Vector(0,0,26500)),False)
 for cmd in ('r.ScreenPercentage 110','r.TemporalAASamples 16','r.MotionBlurQuality 0','r.Tonemapper.Sharpen 0','r.TemporalAAFilterSize 0.8','t.MaxFPS 60'):u.SystemLibrary.execute_console_command(S['world'],cmd,S['pc'])
 check('Both full-height towers and the seated cockpit load',len(S['cells'])==99562 and len(S['parts'])==13 and len(S['rig'])>=284,field_pieces=len(S['cells']),aircraft_sections=len(S['parts']),cockpit_actors=len(S['rig']));ready(0);S.update(initialized=True,test_phase='ready',test_after=now+3,test_flags=set(),last_tick=now);return True
def start():
 S.update(after=time.monotonic()+15,shots=[],initialized=False,report=dict(status='RUNNING' if AUTO else 'INTERACTIVE_READY',revision='5',method='Pilot-controlled arcade flight, full-height individually removable instanced facades and native rigid-body aircraft/fragments. Artistic gameplay simulation, not an engineering model.',checks=[],captures=[],fractured_cells=[],released_parts=[],runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),settings=CFG))
 def tick(dt):
  now=time.monotonic()
  if now<S['after']:return
  try:
   if not S['initialized']:
    initialize(now);return
   dt=min(.05,max(.001,now-S['last_tick']));S['last_tick']=now
   for q in list(S['shots']):
    p=R/'Screenshots'/q['file']
    if p.exists() and p.stat().st_mtime>=q['started'] and p.stat().st_size>5000:S['report']['captures'].append(dict(file=p.name,tag=q['tag'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S['shots'].remove(q);save()
   if AUTO:test_tick(dt,now)
   else:
    pc=S['pc'];down=lambda k:pc.is_input_key_down(KEYS[k]);pressed=lambda k:pc.was_input_key_just_pressed(KEYS[k])
    if pressed('R'):ready(S['preset'])
    if pressed('T'):ready(S['preset']+1)
    if pressed('P') or pressed('SpaceBar'):launch()
    if pressed('V'):S['view']=(S['view']+1)%4;pc.set_view_target_with_blend(S['flight_cams'][S['view']],.25)
    if S.get('flying') and not S.get('impact_time'):
     steering(dt,int(down('D'))-int(down('A')),int(down('W'))-int(down('S')),int(down('E'))-int(down('Q')),int(down('LeftShift'))-int(down('LeftControl')),down('F'))
     if any(down(k) for k in ('A','D','W','S','Q','E','LeftShift','LeftControl')):S['report'].setdefault('manual_input_samples',[]).append(dict(keys=[k for k in ('A','D','W','S','Q','E','LeftShift','LeftControl') if down(k)],bank=S['bank'],pitch=S['pitch'],heading=S['heading'],elapsed_s=S['flight_elapsed']));S['report']['manual_input_samples']=S['report']['manual_input_samples'][-100:]
    mx,my=pc.get_input_mouse_delta();S['look_yaw']=max(-110,min(110,S['look_yaw']+mx*.12));S['look_pitch']=max(-65,min(70,S['look_pitch']+my*.12))
    if pressed('F'):S['look_yaw']=S['look_pitch']=0
   physics_tick(dt,now)
   if not AUTO and now-S.get('hud_time',0)>.1:hud();S['hud_time']=now
   if not AUTO and now-S.get('live_time',0)>1:
    S['report']['live']=dict(flying=S['flying'],elapsed_s=S['flight_elapsed'],bank=S['bank'],pitch=S['pitch'],heading=S['heading'],speed_m_s=S['speed']/100,location_cm=list(S['carrier'].get_actor_location().to_tuple()),view=S['view']);save();S['live_time']=now
  except Exception:
   S['report'].update(status='FAILED',error=traceback.format_exc());save();u.log_error(S['report']['error']);u.unregister_slate_post_tick_callback(S['handle'])
   if AUTO:u.SystemLibrary.quit_game(S.get('world'),S.get('pc'),u.QuitPreference.QUIT,False)
 S['handle']=u.register_slate_post_tick_callback(tick)
