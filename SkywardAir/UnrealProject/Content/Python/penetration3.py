"""Physical breakaway walls and sectional aircraft penetration prototype.
Controlled approach transitions to separate native rigid bodies at fracture.
"""
import unreal as u,time,json,math,random,hashlib,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[4]/'TwinTowers';D=json.loads((R/'Exports/penetration_manifest3.json').read_text());CFG=json.loads((R/'QualitySettings3.json').read_text());CMD=u.SystemLibrary.get_command_line();AUTO='-TwinTowersImpactTest' in CMD;S={};RNG=random.Random(247)
def key(n):k=u.Key();k.import_text(n);return k
KEYS={n:key(n) for n in ('P','T','V','R','LeftMouseButton')};IGNORE=next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore'))
def vec(p):return u.Vector(p[0]*100,-p[1]*100,p[2]*100)
def save():(R/'ArtBible'/('QualityFXProbe.json' if '-QualityFXProbe' in CMD else 'QualityTest3.json' if AUTO else 'QualitySession3.json')).write_text(json.dumps(S['report'],indent=2))
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
 p=R/'Screenshots'/('Quality3_'+tag+'.png');u.SystemLibrary.execute_console_command(S['world'],'Shot filename="'+str(p).replace('\\','/')+'" -nosuffix',S['pc']);S['shots'].append(dict(file=p.name,tag=tag,started=time.time()));u.log('QUALITY3_SHOT '+tag)
def mesh_path(aid):return ('/Game/TwinTowers/Quality3/Meshes/' if aid.startswith('SM_Q3_') else '/Game/TwinTowers/Damage2/Meshes/')+aid
def burst(point):
 if S.get('dust_start'):return
 S.update(dust_start=time.monotonic(),dust_point=point,fx_sources=[])
 for j,q in enumerate(S['dust']):
  smoke=q['bank']=='Smoke';rng=random.Random(553+j);q.update(source=None,delay=(.65+(j%48)*.17 if smoke else rng.uniform(0,.85)),offset=u.Vector(rng.uniform(-700,700) if smoke else rng.uniform(-450,450),rng.uniform(180,800),rng.uniform(-230,180)),velocity=u.Vector(rng.uniform(-65,65),rng.uniform(25,85),rng.uniform(105,170) if smoke else rng.uniform(-130,-55) if j%3==0 else rng.uniform(25,100)),size=rng.uniform(600,1000) if smoke else rng.uniform(600,1000),phase=rng.uniform(0,6.28),lifetime=rng.uniform(CFG['smoke_duration_s']*.65,CFG['smoke_duration_s']*.82) if smoke else rng.uniform(CFG['dust_duration_s']*.67,CFG['dust_duration_s']),opacity=0);q['mid'].set_vector_parameter_value('Tint',u.LinearColor(.55,.59,.63,1) if smoke else u.LinearColor(.90,.86,.77,1))
def update_dust(now):
 if not S.get('dust_start'):return
 t=now-S['dust_start'];cm=u.GameplayStatics.get_player_camera_manager(S['world'],0);eye=cm.get_camera_location()
 for j,q in enumerate(S['dust']):
  age=t-q['delay'];a=q['actor'];life=q['lifetime'];smoke=q['bank']=='Smoke'
  if age<0 or age>=life:a.set_actor_hidden_in_game(True);q['opacity']=0;continue
  if q['source'] is None:
   sources=S['fx_sources'];q['source']=sources[(j*17)%len(sources)] if sources and not smoke else S['dust_point']
  a.set_actor_hidden_in_game(False);spread=1+min(age,4)*(.11 if smoke else .23);curl=u.Vector(math.sin(age*.53+q['phase'])*min(age*42,300),math.cos(age*.47+q['phase'])*min(age*23,160),math.sin(age*.39+q['phase'])*65);p=q['source']+q['offset']*spread+q['velocity']*age+curl;a.set_actor_location(p,False,True);a.set_actor_rotation(u.MathLibrary.make_rot_from_z(eye-p),False);size=min(2800,q['size']+age*(110 if smoke else 260));a.set_actor_scale3d(u.Vector(size/100,size*(1.15 if smoke else .82)/100,1));fade_in=min(1,age/(1.2 if smoke else .30));fade_out=max(0,1-age/life)**(1.35 if smoke else 1.7);opacity=(.72 if smoke else .65)*fade_in*fade_out;q['opacity']=opacity;q['mid'].set_scalar_parameter_value('Opacity',opacity)
  frame=age*(1.45 if smoke else 2.15)+j*.31;frame=15-abs((frame%30)-15) if smoke else min(15,frame);f0=int(frame);f1=min(15,f0+1)
  for name,index in [('OffsetA',f0),('OffsetB',f1)]:q['mid'].set_vector_parameter_value(name,u.LinearColor((index%4)*.25+.0078125,(index//4)*.25+.0078125,0,0))
  q['mid'].set_scalar_parameter_value('FrameBlend',frame-f0)
def fx_snapshot(age):
 data=[]
 for bank in ('Dust','Smoke'):
  q=[q for q in S['dust'] if q['bank']==bank and q.get('opacity',0)>.01];data.append(dict(bank=bank,visible=len(q),max_opacity=max([x['opacity'] for x in q]+[0]),mean_height_above_impact_m=sum(x['actor'].get_actor_location().z-S['dust_point'].z for x in q)/max(1,len(q))/100))
 S['report'].setdefault('effect_evolution',[]).append(dict(age_s=age,layers=data));save()
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
def start():
 S.update(after=time.monotonic()+18,phase='init',target='North',shots=[],pool_index=0,report=dict(status='RUNNING' if AUTO else 'INTERACTIVE',revision='3',method='Aircraft surface probes drive narrow irregular physical fractures. Volume-rendered flipbooks produce separate rolling dust and lofting smoke layers. Controlled approach transitions to 13 native bodies; game-tuned resistance, no engineering prediction.',checks=[],captures=[],fractured_cells=[],released_parts=[],source_sha256=D['source_sha256'],runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),settings=CFG))
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
    actors=u.GameplayStatics.get_all_actors_of_class(S['world'],u.StaticMeshActor);by={a.get_actor_label():a for a in actors};S['carrier']=by['Unmanned aircraft carrier2'];S['parts']=[];S['cells']=[]
    for p in D['aircraft']:
     a=by['AirPart '+p['part']];S['parts'].append(dict(p,actor=a,mesh=a.static_mesh_component.static_mesh,released=False))
    for q in D['cells']:
     a=by[q['name']];S['cells'].append(dict(q,actor=a,bounds=box(a),mesh=a.static_mesh_component.static_mesh,transform=a.get_actor_transform(),broken=False))
    S['pool']=sorted([a for a in actors if a.get_actor_label().startswith('DamagePool ')],key=lambda a:a.get_actor_label());S['bent']={aid:u.load_asset(mesh_path(aid)) for aid in {q['bent_asset'] for q in D['cells']}};S['crushed_nose']=u.load_asset('/Game/TwinTowers/Damage2/Meshes/SM_TT2_Air_Nose_Crushed');S['dust']=[dict(actor=a,bank=a.get_actor_label().split()[1],mid=a.static_mesh_component.create_dynamic_material_instance(0)) for a in actors if a.get_actor_label().startswith('FX3 ')]
    for q in S['dust']:
     c=q['actor'].static_mesh_component;c.set_visibility(True);c.set_hidden_in_game(False);c.set_render_in_main_pass(True)
    cameras=u.GameplayStatics.get_all_actors_of_class(S['world'],u.CameraActor);S['cameras']={tag:next(a for a in cameras if a.get_actor_label()=='CAM_Penetration_'+tag) for tag in ('Entry','Side','Hole')};S['hero']=next(a for a in cameras if a.get_actor_label()=='CAM_TT_Hero');hp=u.Vector(-22000,115000,27500);S['hero'].set_actor_location(hp,False,True);S['hero'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(hp,u.Vector(0,0,25000)),False);S['hero'].camera_component.set_field_of_view(60);set_target();S['pc'].set_view_target_with_blend(S['hero'] if AUTO else S['cameras']['Entry'],0)
    for cmd in ('r.ScreenPercentage 125','r.TemporalAASamples 16','r.MotionBlurQuality 0','t.MaxFPS 60'):u.SystemLibrary.execute_console_command(S['world'],cmd,S['pc'])
    build_grid();check('Irregular physical cells, surface probes and separate aircraft sections load',len(S['cells'])==len(D['cells']) and len(S['parts'])==13,cells=len(S['cells']),aircraft_sections=len(S['parts']),surface_probes=sum(len(p['fracture_samples_cm']) for p in S['parts']),micro_cells=sum(q.get('micro',False) for q in S['cells']));S.update(phase='hero_shot' if AUTO else 'interactive',after=now+3)
    if not AUTO:u.SystemLibrary.print_string(S['world'],'P: impact | T: tower | V: view | R: reset | Click: break panel',True,False,u.LinearColor(1,.9,.6,1),120)
   if '-QualityFXProbe' in CMD and S['phase']=='hero_shot':fx_probe();S.update(phase='probe_shot',after=now+2);return
   for q in list(S['shots']):
    p=R/'Screenshots'/q['file']
    if p.exists() and p.stat().st_mtime>=q['started'] and p.stat().st_size>5000:S['report']['captures'].append(dict(file=p.name,tag=q['tag'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()));S['shots'].remove(q);save()
   physics_tick(dt,now)
   phase=S['phase']
   if phase=='probe_shot':shot('FX_Probe');S['phase']='probe_wait'
   elif phase=='probe_wait' and not S['shots']:S['report']['status']='PROBE_COMPLETE';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
   elif phase=='hero_shot':shot('00_Overview');S['phase']='hero_wait'
   elif phase=='hero_wait' and not S['shots']:S['pc'].set_view_target_with_blend(S['cameras']['Entry'],0);S.update(phase='before',after=now+2)
   elif phase=='before':shot('01_Before');S['phase']='before_wait'
   elif phase=='before_wait' and not S['shots']:launch();S['phase']='run'
   elif phase=='run':
    if not S['approach_shot'] and now-S['launch_time']>3.35:shot('02_Approach');S['approach_shot']=True
    if S.get('impact_time'):
     age=now-S['impact_time']
     if not S['entry_shot'] and age>.12:shot('03_Entry');S['entry_shot']=True
     if not S['side_shot'] and age>.60:S['pc'].set_view_target_with_blend(S['cameras']['Side'],0);S['side_shot']=True
     if not S['breakup_shot'] and age>1.15:shot('04_Penetration_Breakup');S['breakup_shot']=True
     if not S['deep_shot'] and age>3.6:shot('05_Rolling_Dust');S['deep_shot']=True
     if not S['fx_snap_early'] and age>3.8:fx_snapshot(age);S['fx_snap_early']=True
     if not S['hole_shot'] and age>11:S['pc'].set_view_target_with_blend(S['cameras']['Hole'],0);S['hole_shot']=True
     if not S['fx_snap_late'] and age>12.2:shot('06_Lofting_Smoke');fx_snapshot(age);S['fx_snap_late']=True
     if not S['after_shot'] and age>20:shot('07_Torn_Opening');S['after_shot']=True;S.update(phase='verify',after=now+.8)
   elif phase=='verify' and not S['shots']:
    _,x,front,z=target();inside=[p for p in S['parts'] if p['released'] and p['actor'].get_actor_location().y<front-1000];broken=[q for q in S['cells'] if q['broken']];opening=trace_opening();sim=[p for p in S['parts'] if p['released'] and p['actor'].static_mesh_component.is_simulating_physics()]
    check('Aircraft breaks into separately simulated bodies',len(sim)==13,count=len(sim));check('Multiple actual aircraft sections penetrate more than 10m beyond the facade',len(inside)>=5,parts=[p['part'] for p in inside]);check('Both facade and interior deck geometry fracture',any(q['kind']=='facade' for q in broken) and any(q['kind']=='deck' for q in broken),facade=sum(q['kind']=='facade' for q in broken),deck=sum(q['kind']=='deck' for q in broken));check('The former intact wall leaves a physical collision opening',not opening['blocking'],trace=opening)
    check('Dust and smoke have independent opacity and height evolution',len(S['report'].get('effect_evolution',[]))==2 and all(any(q['bank']==b and q['visible']>0 for q in S['report']['effect_evolution'][0]['layers']) for b in ('Dust','Smoke')),effect_evolution=S['report'].get('effect_evolution'));S['report']['aircraft_final']=[dict(part=p['part'],location_cm=list(p['actor'].get_actor_location().to_tuple()),velocity_cm_s=list(p['actor'].static_mesh_component.get_physics_linear_velocity().to_tuple()),depth_inside_m=(front-p['actor'].get_actor_location().y)/100,simulating=p['actor'].static_mesh_component.is_simulating_physics()) for p in S['parts']];S['report']['status']='SUCCESS' if all(q['passed'] for q in S['report']['checks']) else 'FAILED';save();u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
   elif phase=='interactive':
    pc=S['pc']
    if pc.was_input_key_just_pressed(KEYS['P']):launch()
    if pc.was_input_key_just_pressed(KEYS['R']):reset()
    if pc.was_input_key_just_pressed(KEYS['T']) and not S.get('flying'):S['target']='South' if S['target']=='North' else 'North';set_target()
    if pc.was_input_key_just_pressed(KEYS['V']):S['view']=(S.get('view',0)+1)%4;pc.set_view_target_with_blend([S['cameras']['Entry'],S['cameras']['Side'],S['cameras']['Hole'],S['hero']][S['view']],.25)
    if pc.was_input_key_just_pressed(KEYS['LeftMouseButton']):
     cm=u.GameplayStatics.get_player_camera_manager(S['world'],0);p=cm.get_camera_location();f=u.MathLibrary.get_forward_vector(cm.get_camera_rotation());h=u.SystemLibrary.line_trace_single(S['world'],p,p+f*100000,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[S['pawn']],u.DrawDebugTrace.NONE,True)
     if h:
      v=h.to_tuple();a=v[9]
      if v[0] and a:
       q=next((q for q in S['cells'] if q['actor']==a),None)
       if q:break_cell(q,u.Vector(0,-2000,0))
  except Exception:
   S['report'].update(status='FAILED',error=traceback.format_exc());save();u.log_error(S['report']['error']);u.unregister_slate_post_tick_callback(S['handle'])
   if AUTO and S.get('pc'):u.SystemLibrary.quit_game(S['world'],S['pc'],u.QuitPreference.QUIT,False)
 S['handle']=u.register_slate_post_tick_callback(tick);save()
