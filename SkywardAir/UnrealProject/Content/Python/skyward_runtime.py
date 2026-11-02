"""Controls for the uncooked walkthrough; validation exercises these same actions.

Manifest interaction.motion supports source-local rotate {axis, amount_degrees
or amount, duration} and source-world slide {delta, duration}. Mesh pivots are
authored closed hinges; labels/linked parts are parented during native build.
navigation_floors uses source rect [xmin,xmax,ymin,ymax], height or linear slope
{axis,from,to,start,end}, priority, max_step and optional requires_open actor ID.
"""
import unreal as u
import time,json,traceback,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=json.loads((ROOT/'Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
STATE={'pc':None,'pawn':None,'world':None,'seated':None,'door_target':0,
       'began':time.monotonic(),'scan':0,'busy':False,'configured':False,'floor_z':0.,'floor_name':'Cabin deck','movables':{},'screens':{},'controls':{},'inspecting':None}
EYE_HEIGHT=1.62
KEY=u.Key();KEY.import_text('E')
CLICKKEY=u.Key();CLICKKEY.import_text('LeftMouseButton')
VIEWKEY=u.Key();VIEWKEY.import_text('V')
STANDKEY=u.Key();STANDKEY.import_text('SpaceBar')
COMMAND_LINE=u.SystemLibrary.get_command_line()
VALIDATE10='-SkywardValidate10' in COMMAND_LINE or '-SkywardValidate12' in COMMAND_LINE or '-SkywardValidate13' in COMMAND_LINE
VALIDATE=VALIDATE10 or '-SkywardValidate07' in COMMAND_LINE

def vector(p):return u.Vector(p[0]*100,-p[1]*100,p[2]*100)

def actor_name(a):
 for tag in a.tags:
  if str(tag).startswith('Skyward:'):return str(tag)[8:]
 return ''

def write():
 (ROOT/'ArtBible/RuntimeStatus.json').write_text(json.dumps({
  'ready':bool(STATE['pc']),'key':KEY.export_text(),
  'seated':STATE['seated']['title'] if STATE['seated'] else None,
  'door_target':STATE['door_target'],'floor_z_m':STATE['floor_z'],'floor_name':STATE['floor_name'],
  'movables':{name:{'open':item['target']>0,'fraction':round(item['progress'],3)} for name,item in STATE['movables'].items()},
  'screen_pages':{name:item['page'] for name,item in STATE['screens'].items()},
  'controls':{name:{'state':item['state'],'label':item['item']['states'][item['state']]} for name,item in STATE['controls'].items()},
  'inspecting':STATE['inspecting']['item']['title'] if STATE['inspecting'] else None,
  'profile':'1600x900 / 125% render / TAA16 / grain0 / motion blur0'},indent=2))

def _quat_product(a,b):
 return u.Quat(x=a.w*b.x+a.x*b.w+a.y*b.z-a.z*b.y,
               y=a.w*b.y-a.x*b.z+a.y*b.w+a.z*b.x,
               z=a.w*b.z+a.x*b.y-a.y*b.x+a.z*b.w,
               w=a.w*b.w-a.x*b.x-a.y*b.y-a.z*b.z)

def _source_quat(axis,degrees):
 angle=math.radians(float(degrees));sine=math.sin(angle/2)
 return u.Quat(x=-sine if axis=='x' else 0,y=sine if axis=='y' else 0,
               z=-sine if axis=='z' else 0,w=math.cos(angle/2))

def _quat_vector(q,v):
 pure=u.Quat(x=v.x,y=v.y,z=v.z,w=0);inverse=u.Quat(x=-q.x,y=-q.y,z=-q.z,w=q.w)
 result=_quat_product(_quat_product(q,pure),inverse);return u.Vector(result.x,result.y,result.z)

def _apply_movable(item):
 actor=item['actor'];motion=item['item']['motion'];fraction=item['progress']
 stages=motion['stages'] if motion.get('type')=='compound' else [motion]
 origin=item['closed_location'];position=u.Vector(origin.x,origin.y,origin.z);rotation=item['closed_rotation']
 for stage in stages:
  start=float(stage.get('start',0));end=float(stage.get('end',1))
  if end<=start:raise ValueError('Motion stage needs increasing start/end')
  t=max(0.,min(1.,(fraction-start)/(end-start)));t=t*t*(3-2*t)
  kind=stage.get('type','rotate')
  if kind=='rotate':rotation=_quat_product(rotation,_source_quat(stage.get('axis','z').lower(),float(stage.get('amount_degrees',stage.get('amount',90)))*t))
  elif kind=='slide':position=position+vector(stage['delta'])*t
  else:raise ValueError('Unsupported movable motion '+str(kind))
 actor.set_actor_rotation(rotation.rotator(),False);actor.set_actor_location(position,False,False)
 if 'closed_point' in item:item['current_point']=position+_quat_vector(rotation,item['closed_point'])
 for link in item.get('links',[]):
  spec=link['spec'];start=vector(spec['start']);end=position+_quat_vector(rotation,vector(spec['end_local']));delta=end-start;length=delta.length()
  if length<.01:raise ValueError('Kinematic rod has zero length: '+spec['actor'])
  direction=u.Vector(delta.x/length,delta.y/length,delta.z/length)
  if direction.z<-.999999:q=u.Quat(x=1,y=0,z=0,w=0)
  else:
   norm=math.sqrt(direction.x*direction.x+direction.y*direction.y+(1+direction.z)**2)
   q=u.Quat(x=-direction.y/norm,y=direction.x/norm,z=0,w=(1+direction.z)/norm)
  rod=link['actor'];rod.set_actor_location((start+end)*.5,False,False);rod.set_actor_rotation(q.rotator(),False)
  rod.set_actor_scale3d(u.Vector(link['scale'].x,link['scale'].y,length/100));rod.set_actor_enable_collision(False)

def _apply_control(control):
 index=control['state']
 for target in control['targets']:
  spec=target['spec'];actor=target.get('actor');component=target.get('component')
  if 'visible_states' in spec:actor.set_actor_hidden_in_game(index not in spec['visible_states'])
  if spec.get('collision') is False:actor.set_actor_enable_collision(False)
  if 'materials' in target:component.set_material(target['slot'],target['materials'][index])
  if 'intensity_states' in spec:target['light'].light_component.set_intensity(float(spec['intensity_states'][index]))
  if 'rotation_states' in spec:actor.set_actor_rotation(_quat_product(target['rotation'],_source_quat(spec.get('axis','z'),spec['rotation_states'][index])).rotator(),False)
  if 'translation_states' in spec:actor.set_actor_location(target['location']+vector(spec['translation_states'][index]),False,False)

def set_control_state(actor,index):
 control=STATE['controls'][actor];control['state']=int(index)%len(control['item']['states'])
 duration=float(control['item'].get('auto_reset_seconds',0))
 control['reset_at']=time.monotonic()+duration if duration and control['state']!=int(control['item'].get('initial_state',0)) else None
 _apply_control(control);write();return control['state']

def control_snapshot(actor):
 """Read actual native target state for validation, rather than trusting an index."""
 control=STATE['controls'][actor];index=control['state'];checks=[]
 for target in control['targets']:
  spec=target['spec'];a=target.get('actor');c=target.get('component')
  if 'visible_states' in spec:
   hidden=bool(a.get_editor_property('hidden'));checks.append({'property':'visible','actor':spec['actor'],'expected':index in spec['visible_states'],'actual':not hidden,'passed':hidden==(index not in spec['visible_states'])})
  if spec.get('collision') is False:checks.append({'property':'collision','actor':spec['actor'],'actual':a.get_actor_enable_collision(),'passed':not a.get_actor_enable_collision()})
  if 'materials' in target:
   actual=c.get_material(target['slot']).get_name();expected=spec['materials'][index];checks.append({'property':'material','actor':spec['actor'],'actual':actual,'expected':expected,'passed':actual==expected})
  if 'intensity_states' in spec:
   actual=float(target['light'].light_component.get_editor_property('intensity'));expected=float(spec['intensity_states'][index]);checks.append({'property':'light','light':spec['light'],'actual':actual,'expected':expected,'passed':abs(actual-expected)<.01})
  if 'rotation_states' in spec:
   expected=_quat_product(target['rotation'],_source_quat(spec.get('axis','z'),spec['rotation_states'][index])).rotator();actual=a.get_actor_rotation()
   errors=[abs((getattr(actual,k)-getattr(expected,k)+180)%360-180) for k in ('pitch','yaw','roll')]
   checks.append({'property':'rotation','actor':spec['actor'],'error_degrees':max(errors),'passed':max(errors)<.1})
  if 'translation_states' in spec:
   expected=target['location']+vector(spec['translation_states'][index]);error=(a.get_actor_location()-expected).length()
   checks.append({'property':'translation','actor':spec['actor'],'error_cm':error,'passed':error<.02})
 return {'state':index,'targets':checks,'passed':bool(checks) and all(check['passed'] for check in checks)}

def inspect_item(item):
 state=STATE;pc=state['pc'];pawn=state['pawn'];moving=pawn.get_component_by_class(u.FloatingPawnMovement)
 moving.stop_movement_immediately();pc.reset_ignore_move_input();pc.set_ignore_move_input(True)
 saved={'item':item,'view':pc.get_control_rotation(),'opened':{}}
 for name in item.get('open_actors',[]):
  movable=state['movables'][name];saved['opened'][name]=movable['target'];movable['target']=1.
 if item.get('camera'):
  camera=state['cameras'].get(item['camera'])
  if not camera:raise RuntimeError('Inspection camera missing: '+item['camera'])
  pc.set_view_target_with_blend(camera,.25)
 else:raise ValueError('Inspection requires an authored close-up camera: '+item['actor'])
 if item.get('hold'):
  actor=state['actors'][item['actor']];origin=actor.get_actor_location();rotation=actor.get_actor_rotation();hold=item['hold']
  saved['held']={'actor':actor,'location':origin,'rotation':rotation,'collision':actor.get_actor_enable_collision(),'movables':{}}
  camera_rotation=camera.get_actor_rotation();basis=camera_rotation.quaternion();offset=hold.get('offset',[.38,0,-.06])
  new_position=camera.get_actor_location()+_quat_vector(basis,u.Vector(*[float(value)*100 for value in offset]))
  angles=hold.get('rotation',[90,0,0]);new_rotation=_quat_product(basis,u.Rotator(pitch=angles[0],yaw=angles[1],roll=angles[2]).quaternion())
  old=rotation.quaternion();delta=_quat_product(new_rotation,u.Quat(x=-old.x,y=-old.y,z=-old.z,w=old.w))
  actor.set_actor_enable_collision(False);actor.set_actor_location(new_position,False,True);actor.set_actor_rotation(new_rotation.rotator(),False)
  for name in dict.fromkeys(item.get('open_actors',[])+item.get('hold_actors',[])):
   movable=state['movables'][name];saved['held']['movables'][name]=(movable['closed_location'],movable['closed_rotation'],movable['actor'].get_actor_enable_collision())
   movable['closed_location']=new_position+_quat_vector(delta,movable['closed_location']-origin)
   movable['closed_rotation']=_quat_product(delta,movable['closed_rotation']);movable['actor'].set_actor_enable_collision(False);_apply_movable(movable)
 state['inspecting']=saved;write()

def end_inspect():
 saved=STATE.get('inspecting')
 if not saved:return
 held=saved.get('held')
 if held:
  held['actor'].set_actor_location(held['location'],False,True);held['actor'].set_actor_rotation(held['rotation'],False);held['actor'].set_actor_enable_collision(held['collision'])
  for name,(position,rotation,collision) in held['movables'].items():
   movable=STATE['movables'][name];movable['closed_location']=position;movable['closed_rotation']=rotation;movable['actor'].set_actor_enable_collision(collision);_apply_movable(movable)
 for name,target in saved['opened'].items():STATE['movables'][name]['target']=target
 STATE['pc'].set_view_target_with_blend(STATE['pawn'],.25);STATE['pc'].set_control_rotation(saved['view'])
 STATE['pc'].reset_ignore_move_input()
 if STATE['seated']:STATE['pc'].set_ignore_move_input(True)
 STATE['inspecting']=None;write()

def configure():
 w,pc=STATE['world'],STATE['pc']
 for cmd in ['r.ScreenPercentage 125','r.DynamicRes.OperationMode 0','r.TemporalAASamples 16','r.TemporalAACurrentFrameWeight 0.1','r.Tonemapper.Sharpen 0.2','r.MotionBlurQuality 0','r.MaxAnisotropy 16','r.SSR.Quality 4','r.SSR.Temporal 1']:
  u.SystemLibrary.execute_console_command(w,cmd,pc)
 pc.player_camera_manager.set_editor_property('default_fov',80)
 u.SystemLibrary.execute_console_command(w,'fov 0',pc)
 STATE['actors']={actor_name(a):a for a in u.GameplayStatics.get_all_actors_of_class(w,u.StaticMeshActor) if actor_name(a)}
 # Broad standing-body proxies stop the player, while precise interaction rays
 # use the visible model. A box over a seat must not hide its overhead controls.
 for actor in u.GameplayStatics.get_all_actors_of_class(w,u.StaticMeshActor):
  if actor.get_actor_label().startswith(('COL_','MOTION_PROXY ')):
   actor.static_mesh_component.set_collision_response_to_channel(u.CollisionChannel.ECC_VISIBILITY,next(getattr(u.CollisionResponseType,n) for n in dir(u.CollisionResponseType) if n.lower().endswith('ignore')))
 STATE['door']=STATE['actors']['Flightdeck door'];STATE['items']=DATA['interactions']
 STATE['fixed_lever_actors']={item['requires_open'] for item in STATE['items'] if item.get('requires_open') and item['kind']=='seat'}
 STATE['point_bindings']={}
 for item in STATE['items']:
  if item.get('motion') or item.get('point_follows_actor') is False:continue
  actor=STATE['actors'].get(item['actor'])
  if actor is None:continue
  closed=actor.get_actor_rotation().quaternion()
  STATE['point_bindings'][item['actor']]={'actor':actor,'closed_point':_quat_vector(u.Quat(x=-closed.x,y=-closed.y,z=-closed.z,w=closed.w),vector(item['point'])-actor.get_actor_location())}
 STATE['lights']={str(tag)[len('SkywardLight:'):]:a for a in u.GameplayStatics.get_all_actors_of_class(w,u.Light) for tag in a.tags if str(tag).startswith('SkywardLight:')}
 cameras=u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor)
 STATE['cameras']={str(tag)[len('SkywardCamera:'):]:a for a in cameras for tag in a.tags if str(tag).startswith('SkywardCamera:')}
 STATE['movables']={}
 for item in STATE['items']:
  if not item.get('motion'):continue
  actor=STATE['actors'].get(item['actor'])
  if actor is None:raise RuntimeError('Interactive actor is missing: '+item['actor'])
  progress=1. if item.get('initial_open',False) else 0.
  STATE['movables'][item['actor']]={'item':item,'actor':actor,'closed_location':actor.get_actor_location(),
   'closed_rotation':actor.get_actor_rotation().quaternion(),'progress':progress,'target':progress,'links':[]}
  moving=STATE['movables'][item['actor']];closed=moving['closed_rotation']
  moving['closed_point']=_quat_vector(u.Quat(x=-closed.x,y=-closed.y,z=-closed.z,w=closed.w),vector(item['point'])-moving['closed_location'])
  for spec in item.get('kinematic_links',[]):
   rod=STATE['actors'].get(spec['actor'])
   if rod is None:raise RuntimeError('Kinematic rod missing: '+spec['actor'])
   STATE['movables'][item['actor']]['links'].append({'spec':spec,'actor':rod,'scale':rod.get_actor_scale3d()})
  _apply_movable(STATE['movables'][item['actor']])
 STATE['screens']={}
 for item in STATE['items']:
  if item['kind']!='screen':continue
  actor=STATE['actors'][item['actor']];component=actor.static_mesh_component
  names=set(item['pages']+[item['slot_material']]);slot=next((index for index in range(component.get_num_materials()) if component.get_material(index) and component.get_material(index).get_name() in names),None)
  if slot is None:raise RuntimeError('Screen material slot missing on '+item['actor'])
  pages=[u.load_asset('/Game/Art/Materials/Instances/'+name) for name in item['pages']]
  if not all(pages):raise RuntimeError('Screen page material missing on '+item['actor'])
  STATE['screens'][item['actor']]={'item':item,'component':component,'slot':slot,'pages':pages,'page':0}
  component.set_material(slot,pages[0])
 STATE['controls']={}
 for item in STATE['items']:
  if item['kind']!='control':continue
  if len(item.get('states',[]))<2:raise ValueError('Control needs at least two states: '+item['actor'])
  targets=[]
  for spec in item.get('targets',[]):
   target={'spec':spec}
   if 'actor' in spec:
    actor=STATE['actors'].get(spec['actor'])
    if actor is None:raise RuntimeError('Control target missing: '+spec['actor'])
    target.update(actor=actor,component=actor.static_mesh_component,rotation=actor.get_actor_rotation().quaternion(),location=actor.get_actor_location())
   if 'materials' in spec:
    if len(spec['materials'])!=len(item['states']):raise ValueError('One material is needed per control state')
    names=set(spec['materials']+[spec.get('slot_material',spec['materials'][0])]);component=target['component']
    slot=next((i for i in range(component.get_num_materials()) if component.get_material(i) and component.get_material(i).get_name() in names),None)
    if slot is None:raise RuntimeError('Control material slot missing: '+spec['actor'])
    materials=[u.load_asset('/Game/Art/Materials/Instances/'+name) for name in spec['materials']]
    if not all(materials):raise RuntimeError('Control material missing: '+spec['actor'])
    target.update(slot=slot,materials=materials)
   if 'light' in spec:
    if spec['light'] not in STATE['lights']:raise RuntimeError('Control light missing: '+spec['light'])
    target['light']=STATE['lights'][spec['light']]
   for key in ('rotation_states','intensity_states','translation_states'):
    if key in spec and len(spec[key])!=len(item['states']):raise ValueError(key+' needs one value per control state')
   targets.append(target)
  STATE['controls'][item['actor']]={'item':item,'state':int(item.get('initial_state',0)),'targets':targets,'reset_at':None}
  _apply_control(STATE['controls'][item['actor']])
 STATE['review_index']=-1
 STATE['review_cameras']=[]
 for name in ('CAM_Plane_Exterior07','CAM_Plane_FrontOverview07','CAM_Plane_Profile08'):
  match=next((a for a in cameras if any(str(t)=='SkywardCamera:'+name for t in a.tags)),None)
  if match:STATE['review_cameras'].append(match)
 update_floor(0);write()
 if '-SkywardStartExterior' in COMMAND_LINE:toggle_review()
 (ROOT/'ArtBible/RuntimeError.txt').unlink(missing_ok=True)
 if VALIDATE:
  if '-SkywardValidate13' in COMMAND_LINE:
   import skyward_validate13
   STATE['validator']=skyward_validate13.Validator(__import__(__name__))
  elif VALIDATE10:
   import skyward_validate10
   STATE['validator']=skyward_validate10.Validator(__import__(__name__))
  else:
   import skyward_validate07
   STATE['validator']=skyward_validate07.Validator(__import__(__name__))
 STATE['configured']=True
 if '-SkywardFocusTest14' in COMMAND_LINE:
  import focus_test14
  STATE['focus_test']=focus_test14.Tester(__import__(__name__))
 if '-SkywardScan13' in COMMAND_LINE:
  import visibility13
  visibility13.run(__import__(__name__))
 (ROOT/'ArtBible'/('StartupError'+str(DATA.get('layout',{}).get('revision','unknown'))+'.json')).unlink(missing_ok=True)

def floor_at_source(x,y,feet_z=0.):
 """Select a continuous reachable floor; lower holds cannot pull down cabin players."""
 candidates=[]
 # Crossing the top landing after a long frame must not strand the camera at
 # the last stair sample. Only the actual forward portal permits this return.
 stair=next((z for z in DATA.get('layout',{}).get('navigation_floors',[]) if z.get('slope')),None)
 returning=stair and STATE.get('floor_name')==stair['name'] and y<=stair['rect'][2]+.005 and stair['rect'][0]-.35<=x<=stair['rect'][1]+.75 and -.85<feet_z<.28
 if abs(feet_z)<.28 or returning:candidates.append((30 if returning else 0,abs(feet_z),0.,'Cabin deck'))
 for zone in DATA.get('layout',{}).get('navigation_floors',[]):
  xmin,xmax,ymin,ymax=zone['rect']
  if not (xmin-.005<=x<=xmax+.005 and ymin-.005<=y<=ymax+.005):continue
  required=zone.get('requires_open')
  if required and STATE['movables'].get(required,{}).get('progress',0)<.90:continue
  if zone.get('slope'):
   slope=zone['slope'];coordinate=x if slope.get('axis','y')=='x' else y
   denominator=float(slope['to'])-float(slope['from'])
   if abs(denominator)<.001:raise ValueError('Floor slope has zero length: '+zone['name'])
   t=max(0.,min(1.,(coordinate-float(slope['from']))/denominator))
   height=float(slope['start'])+(float(slope['end'])-float(slope['start']))*t
  else:height=float(zone['height'])
  distance=abs(height-feet_z)
  if distance<=float(zone.get('max_step',.28)):
   candidates.append((int(zone.get('priority',10)),distance,height,zone['name']))
 if not candidates:return float(feet_z),STATE.get('floor_name','Current deck')
 priority,distance,height,name=sorted(candidates,key=lambda value:(-value[0],value[1]))[0]
 return height,name

def update_floor(dt):
 if STATE.get('seated') or STATE.get('inspecting') or not STATE.get('pawn'):return
 pawn=STATE['pawn'];position=pawn.get_actor_location()
 floor,name=floor_at_source(position.x/100,-position.y/100,position.z/100-EYE_HEIGHT)
 desired=(floor+EYE_HEIGHT)*100
 # Short collision-swept Z moves follow the slope while the player walks.
 # Collision stays enabled and there is no teleport at the stair entrance.
 if abs(desired-position.z)>.015:
  pawn.set_actor_location(u.Vector(position.x,position.y,desired),True,False)
 actual=pawn.get_actor_location()
 movement=pawn.get_component_by_class(u.FloatingPawnMovement)
 movement.set_plane_constraint_origin(u.Vector(0,0,actual.z))
 movement.set_plane_constraint_enabled(True)
 STATE['floor_z']=actual.z/100-EYE_HEIGHT;STATE['floor_name']=name

def stand():
 saved=STATE['seated'];p=STATE['pawn'];pc=STATE['pc'];move=p.get_component_by_class(u.FloatingPawnMovement)
 if not saved:return
 move.stop_movement_immediately();p.set_actor_location(saved['return'],False,True);p.set_actor_enable_collision(True)
 move.set_plane_constraint_origin(u.Vector(0,0,saved['return'].z));move.set_plane_constraint_enabled(True)
 move.activate(True);pc.reset_ignore_move_input();STATE['seated']=None
 STATE['floor_z']=saved['return'].z/100-EYE_HEIGHT
 update_floor(0);write()

def sit(item):
 p=STATE['pawn'];pc=STATE['pc'];move=p.get_component_by_class(u.FloatingPawnMovement)
 STATE['seated']={**item,'return':p.get_actor_location()};move.stop_movement_immediately();move.set_plane_constraint_enabled(False);move.deactivate()
 if item.get('screen_actor'):
  if item['screen_actor'] not in STATE['screens']:raise RuntimeError('Seat screen mapping missing: '+item['screen_actor'])
  STATE['seated']['screen_actor']=item['screen_actor']
 else:
  choices=[((vector(screen['item']['point'])-vector(item['location'])).length(),name) for name,screen in STATE['screens'].items()]
  choices=[choice for choice in choices if choice[0]<190]
  if choices:STATE['seated']['screen_actor']=min(choices)[1]
 pc.set_ignore_move_input(True);p.set_actor_enable_collision(False);p.set_actor_location(vector(item['location']),False,True)
 facing=item.get('facing');yaw=math.degrees(math.atan2(-facing[1],facing[0])) if facing else 90
 pc.set_control_rotation(u.Rotator(pitch=float(item.get('view_pitch',-5)),yaw=yaw,roll=0));write()

def interaction_point(item):
 """Physical handles follow their leaf; explicitly fixed release controls stay put."""
 if item.get('inside_point'):
  p=STATE['pawn'].get_actor_location();x,y=p.x/100,-p.y/100;r=item['inside_rect']
  if r[0]<=x<=r[1] and r[2]<=y<=r[3]:return vector(item['inside_point'])
 moving=STATE['movables'].get(item['actor']) if item.get('motion') else None
 follows=item.get('point_follows_actor',True)
 if moving:
  fixed=STATE.get('fixed_lever_actors')
  if fixed is None:fixed={seat['requires_open'] for seat in STATE.get('items',[]) if seat.get('requires_open') and seat['kind']=='seat'}
  if item['actor'] in fixed:follows=False
  if follows and 'current_point' in moving:return moving['current_point']
 if follows:
  binding=STATE.get('point_bindings',{}).get(item['actor'])
  if binding:return binding['actor'].get_actor_location()+_quat_vector(binding['actor'].get_actor_rotation().quaternion(),binding['closed_point'])
 return vector(item['point'])

def point_at_item(item):
 STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(STATE['pawn'].get_actor_location(),interaction_point(item)))

def _focus_hit(pos,forward):
 hit=u.SystemLibrary.line_trace_single(STATE['world'],pos,pos+forward*300,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[STATE['pawn']],u.DrawDebugTrace.NONE,True)
 if hit is None:return '',None
 values=hit.to_tuple()
 return (actor_name(values[9]) if values[9] else '',values[5]) if values[0] else ('',None)

def nearest(kind=None):
 """Aim at a visible fitting, with assistance for small grips and keys.

 A direct surface hit works across a door/bin/seat, not just its hidden marker.
 Small neighbouring controls still compete by aim angle, never by proximity to
 the player. Every assisted target keeps its own physical visibility test.
 """
 p=STATE['pawn'];pc=STATE['pc'];pos=p.get_actor_location();forward=u.MathLibrary.get_forward_vector(pc.get_control_rotation());choices=[]
 owner,impact=_focus_hit(pos,forward)
 kinds=(kind,) if isinstance(kind,str) else kind
 radii={'control':.09,'inspect':.15,'seat':.34,'screen':.29,'movable':.27,'door':.38}
 surfaces={'control':.16,'inspect':.28,'seat':.68,'screen':.55,'movable':1.40,'door':1.40}
 reaches={'control':2.30,'inspect':2.30,'seat':2.50,'screen':2.60,'movable':2.65,'door':2.65}
 for item in STATE['items']:
  if item.get('activation')=='inspect_only':continue
  if kinds and item['kind'] not in kinds:continue
  if item['kind']=='screen' and STATE['seated'] and item['actor']!=STATE['seated'].get('screen_actor'):continue
  required=item.get('requires_open')
  if required and STATE['movables'].get(required,{}).get('progress',0)<.95:continue
  # This generous coarse bound includes every authored opening sweep/slide.
  # Avoid querying hundreds of distant native transforms every frame.
  source=item['point']
  if (source[0]*100-pos.x)**2+(-source[1]*100-pos.y)**2+(source[2]*100-pos.z)**2>650**2:continue
  point=interaction_point(item);d=point-pos;distance=d.length();category=item['kind']
  dot=(d.x*forward.x+d.y*forward.y+d.z*forward.z)/max(distance,.001)
  if dot<=0:continue
  lateral=distance*math.sqrt(max(0,1-dot*dot))
  reach=float(item.get('reach',reaches.get(category,2.3)))*100
  owns=owner==item['actor'] or owner in item.get('visibility_owners',[]) or owner in item.get('linked_actors',[]) or (category=='seat' and owner==required)
  # A shared centre-pair mesh must resolve to the chair actually under the aim.
  if owns and category=='seat' and owner!=item['actor'] and abs(impact.x-point.x)>=34:owns=False
  surface=owns and (impact-point).length()<=surfaces.get(category,.25)*100 and (impact-pos).length()<reach
  angle=math.degrees(math.acos(max(-1.,min(1.,dot))))
  assisted=distance<reach and angle<(8.0 if category=='control' else 12.0 if category=='inspect' else 14.0) and lateral<float(item.get('focus_radius',radii.get(category,.15)))*100+distance*.055
  if not surface and not assisted:continue
  if not surface and not interaction_visible(item):continue
  # Exact aim beats a broad parent surface. A directly hit small key beats
  # assistance for adjacent keys; large panels do not steal their controls.
  score=angle*(.20 if category=='inspect' else 1.)
  if surface:score=min(score,.10 if category=='control' else .65 if category=='seat' and required else 1.25)
  choices.append((score,distance,item))
 return min(choices,key=lambda value:(value[0],value[1]))[2] if choices else None

def interaction_visible(item):
 """A fitting cannot be selected through opaque physical geometry."""
 pos=STATE['pawn'].get_actor_location();point=interaction_point(item)
 hit=u.SystemLibrary.line_trace_single(STATE['world'],pos,point,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[STATE['pawn']],u.DrawDebugTrace.NONE,True)
 if hit is None:return True
 values=hit.to_tuple()
 if not values[0]:return True
 owner=actor_name(values[9]) if values[9] else ''
 if owner==item['actor']:return True
 if owner in item.get('visibility_owners',[]):
  # A paired seat mesh is shared, but the opposite chair must still obscure
  # the selected logical seat. Each seat is only about0.60m wide.
  return item['kind']!='seat' or abs(values[5].x-point.x)<34
 # A precisely surface-mounted marker can end on the supporting face. A
 # remote fitting behind a wall cannot use a large endpoint allowance.
 return (values[5]-point).length()<=.2

def show_screen_page(actor,index):
 screen=STATE['screens'][actor];index=int(index)%len(screen['pages'])
 screen['component'].set_material(screen['slot'],screen['pages'][index]);screen['page']=index;write();return index

def use_nearest(stand_on_miss=True):
 if STATE.get('inspecting'):end_inspect();return 'return'
 if STATE['seated']:
  item=nearest(('screen','control','inspect'))
  if not item:
   if stand_on_miss:stand();return 'stand'
   return None
 else:item=nearest()
 if not item:return None
 if item.get('motion'):
  lock=item.get('lock_control')
  if lock and STATE['controls'][lock]['state']:
   pos=STATE['pawn'].get_actor_location();inside=item.get('inside_rect')
   x,y=pos.x/100,-pos.y/100
   if inside and inside[0]<=x<=inside[1] and inside[2]<=y<=inside[3]:set_control_state(lock,0)
   else:return 'locked'
  occupied=STATE['seated'] and STATE['seated'].get('requires_open')==item['actor']
  if occupied:return None
  moving=STATE['movables'][item['actor']];moving['target']=0. if moving['target'] else 1.
  write();return 'movable'
 if item['kind']=='door':STATE['door_target']=float(item.get('open_yaw',86)) if STATE['door_target']==0 else 0;write();return 'door'
 if item['kind']=='seat':sit(item);return 'seat'
 if item['kind']=='screen':show_screen_page(item['actor'],STATE['screens'][item['actor']]['page']+1);return 'screen'
 if item['kind']=='control':set_control_state(item['actor'],STATE['controls'][item['actor']]['state']+1);return 'control'
 if item['kind']=='inspect':inspect_item(item);return 'inspect'
 return None

def toggle_review():
 if STATE.get('inspecting'):end_inspect()
 pc=STATE['pc'];cams=STATE['review_cameras'];i=STATE['review_index']+1
 if i>=len(cams):i=-1
 STATE['review_index']=i
 STATE['pawn'].get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately()
 if i<0:
  pc.set_view_target_with_blend(STATE['pawn'],.3)
  if not STATE['seated']:pc.reset_ignore_move_input()
 else:
  pc.set_view_target_with_blend(cams[i],.3);pc.reset_ignore_move_input();pc.set_ignore_move_input(True)
 return i

def update_door(dt):
 a=STATE['door'];rotation=a.get_actor_rotation();target=-STATE['door_target'];delta=target-rotation.yaw
 if abs(delta)>.02:
  yaw=rotation.yaw+math.copysign(min(abs(delta),dt*100),delta)
  a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False)
 for item in STATE['movables'].values():
  change=item['target']-item['progress']
  if abs(change)>.0001:
   duration=max(.1,float(item['item']['motion'].get('duration',1.)))
   item['progress']+=math.copysign(min(abs(change),dt/duration),change)
   _apply_movable(item)
 now=time.monotonic()
 for name,control in STATE['controls'].items():
  if control['reset_at'] is not None and now>=control['reset_at']:set_control_state(name,int(control['item'].get('initial_state',0)))

def reposition(pos):
 p=STATE['pawn'];movement=p.get_component_by_class(u.FloatingPawnMovement)
 movement.stop_movement_immediately();p.consume_movement_input_vector();p.set_actor_location(u.Vector(*pos),False,True)
 movement.set_plane_constraint_origin(u.Vector(0,0,pos[2]));STATE['floor_z']=pos[2]/100-EYE_HEIGHT

def point_at(p):
 pc=STATE['pc'];pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(STATE['pawn'].get_actor_location(),vector(p)))

def _hint(item):
 if STATE.get('inspecting'):return 'E — Return from '+STATE['inspecting']['item']['title']
 if item and item['kind']=='control':
  control=STATE['controls'][item['actor']];return 'E — '+item['title']+' · '+str(item['states'][control['state']])
 if item and item['kind']=='inspect':return 'E — Inspect '+item['title']
 if STATE['seated']:
  return 'E — Next entertainment page' if item and item['kind']=='screen' else 'E — Stand up'
 if not item:return ''
 if item.get('motion'):
  opened=STATE['movables'][item['actor']]['target']>0
  if any(seat.get('requires_open')==item['actor'] for seat in STATE['items'] if seat['kind']=='seat'):
   return 'E — '+('Fold crew jumpseat' if opened else 'Unfold crew jumpseat')
  return 'E — '+('Close ' if opened else 'Open ')+item['title']
 if item['kind']=='door':return 'E — '+('Open flight deck' if STATE['door_target']==0 else 'Close flight deck')
 if item['kind']=='seat':return 'E — Sit in '+item['title']
 if item['kind']=='screen':return 'E — Next entertainment page'
 return ''

def tick(dt):
 if STATE['busy']:return
 STATE['busy']=True
 try:
  now=time.monotonic()
  if not STATE['pc']:
   if now<STATE['scan']:return
   STATE['scan']=now+2
   for o in u.ObjectIterator():
    if isinstance(o,u.World):
     pc=u.GameplayStatics.get_player_controller(o,0)
     pawn=u.GameplayStatics.get_player_pawn(o,0) if pc else None
     if pc and pawn:STATE.update(world=o,pc=pc,pawn=pawn);configure();break
   return
  update_door(dt);update_floor(dt)
  if VALIDATE:STATE['validator'].tick(dt)
  else:
   if STATE['pc'].was_input_key_just_pressed(VIEWKEY):toggle_review()
   if STATE.get('focus_test'):
    STATE['focus_test'].tick(dt);return
   if STATE['review_index']>=0:
    u.SystemLibrary.print_string(STATE['world'],'V — Next exterior view / Return to cabin',True,False,u.LinearColor(.8,.9,1,1),.1,u.Name('SkywardHint'));return
   if STATE['seated'] and STATE['pc'].was_input_key_just_pressed(STANDKEY):stand()
   elif STATE['pc'].was_input_key_just_pressed(KEY):use_nearest()
   elif STATE['pc'].was_input_key_just_pressed(CLICKKEY):use_nearest(stand_on_miss=False)
   item=nearest(('screen','control','inspect')) if STATE['seated'] else nearest()
   hint=_hint(item)
   if item or STATE.get('inspecting'):hint=hint.replace('E —','E / Click —')
   if STATE['seated']:hint+=' · Space — Stand'
   if hint:u.SystemLibrary.print_string(STATE['world'],hint,True,False,u.LinearColor(.8,.9,1,1),.1,u.Name('SkywardHint'))
 except Exception:
  error=traceback.format_exc();u.log_error(error);(ROOT/'ArtBible/RuntimeError.txt').write_text(error)
  if not STATE.get('configured'):
   revision=str(DATA.get('layout',{}).get('revision','unknown'))
   failure={'revision':revision,'status':'FAILED','runtime_startup':True,'error':error,'captures':[],'interactions':[],'navigation':[],'configuration':[],'barriers':[],'body_clearance':[],
            'capture_count':0,'walking_routes_passed':0,'walking_routes_total':len(DATA.get('layout',{}).get('walk_tests',[])),'validation_started':False,'failure_stage':'runtime.configure before validator initialization'}
   (ROOT/'ArtBible'/('StartupError'+revision+'.json')).write_text(json.dumps(failure,indent=2))
   if VALIDATE:(ROOT/'ArtBible/EngineValidation.json').write_text(json.dumps(failure,indent=2))
  if VALIDATE and STATE.get('validator'):STATE['validator'].fail(error)
  elif VALIDATE and STATE['pc']:
   u.unregister_slate_post_tick_callback(STATE['handle']);u.SystemLibrary.quit_game(STATE['world'],STATE['pc'],u.QuitPreference.QUIT,False)
  else:u.unregister_slate_post_tick_callback(STATE['handle'])
 finally:STATE['busy']=False

def start():
 if STATE.get('handle') is not None:return STATE['handle']
 STATE['handle']=u.register_slate_post_tick_callback(tick);u.log('SKYWARD_RUNTIME10_STARTED')
 return STATE['handle']
