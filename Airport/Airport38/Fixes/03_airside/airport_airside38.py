"""Airside38 data translation, genuine bridge articulation and ground parking.

No import-time Unreal dependency: the schema and kinematics are unit tested with
the real saved manifest. Airport38 entry calls prepare_plane before configure.
"""
import copy, math, time
from airside_math38 import *
from flight39_envelope import bridge_overlap

ABSOLUTE_KEYS={'location','point','inside_point','validation_approach','open_validation_approach',
               'start','look_at','eye','position','closed_location'}
G=None
S={}

def _point(v):return isinstance(v,(list,tuple)) and len(v)==3 and all(isinstance(q,(int,float)) for q in v)
def _translate_point(p,dx):return [p[0]+dx,p[1],p[2]]

def _absolute_records(value,dx,counters,path=''):
    """Field-schema translation, deliberately never based on vector length alone.

    Numerical local offsets, end_local, axes, dimensions, basis and all motion
    deltas remain unchanged. 'start' only has point semantics when it is a
    3-vector; motion timing start is scalar and is retained verbatim.
    """
    if isinstance(value,dict):
        for key,v in value.items():
            where=path+'/'+key
            if key in ABSOLUTE_KEYS and _point(v):
                value[key]=_translate_point(v,dx);counters['points']+=1
            elif key in ('rect','inside_rect') and isinstance(v,list) and len(v)==4:
                value[key]=[v[0]+dx,v[1]+dx,v[2],v[3]];counters['rectangles']+=1
            elif key=='polygon' and isinstance(v,list):
                value[key]=[[p[0]+dx,p[1],*p[2:]] for p in v];counters['polygons']+=1
            elif key=='path' and isinstance(v,list) and v and all(_point(p) for p in v):
                value[key]=[_translate_point(p,dx) for p in v];counters['points']+=len(v)
            elif key=='pilot_seat_centres_m':
                value[key]=[_translate_point(p,dx) for p in v];counters['points']+=len(v)
            elif key=='seat_approaches' and isinstance(v,dict):
                for actor,p in v.items():
                    if _point(p):v[actor]=_translate_point(p,dx);counters['points']+=1
            elif key=='slope' and isinstance(v,dict):
                if v.get('axis')=='x':
                    v['from']+=dx;v['to']+=dx;counters['slopes']+=1
            elif key=='closed_range' and value.get('axis')=='x':
                value[key]=[p+dx for p in v];counters['ranges']+=1
            else:_absolute_records(v,dx,counters,where)
    elif isinstance(value,list):
        for v in value:_absolute_records(v,dx,counters,path+'[]')

def translate_plane_data(data,dx=16.):
    existing=data.get('airport38_translation')
    if existing:
        assert existing['offset']==[dx,0,0],existing
        return data
    result=copy.deepcopy(data);counts=dict(points=0,rectangles=0,polygons=0,slopes=0,ranges=0)
    _absolute_records(result,dx,counts)
    result['airport38_translation']=dict(offset=[dx,0,0],counts=counts,version=1)
    return result

def prepare_plane(P,D):
    vector=P.vector
    P.DATA=translate_plane_data(P.DATA,D.get('aircraft38',{}).get('offset',[16,0,0])[0])
    assert P.vector is vector,'Coordinate conversion must not be offset: it converts motion deltas too.'
    D.setdefault('aircraft38',{})['runtime_translation']=P.DATA['airport38_translation']
    return P

def door_closed():
    moving=G.P.STATE.get('movables',{}).get(L1)
    return bool(moving and moving.get('progress',1)<=.015 and moving.get('target',1)<=.015)

def _bridge_occupied():
    p=G.source(G.P.STATE['pawn'].get_actor_location())
    # Full route + all mitred joint landing polygons; never broad bounding box.
    if -.35<p[2]<3.4 and any(in_polygon(p,q['polygon']) for q in G.D['aircraft38']['bridge']['floor_polygons']):return True
    # Airport NPCs are normally seated; if a movable passenger enters, its world
    # centre prevents retracting the walkway underneath it as well.
    for q in G.D.get('instances',[]):
        if not q.get('bridge_passenger38'):continue
        a=G.S['actors'].get(q['name'])
        if a and any(in_polygon(G.source(a.get_actor_location()),z['polygon']) for z in G.D['aircraft38']['bridge']['floor_polygons']):return True
    # Query only the known physical props on a stow request / pending close,
    # never every scene actor. A held suitcase is still a real bridge load.
    frame=getattr(G,'flight39',{}).get('frame')
    candidates=dict(G.S.get('physics',{}));held=G.S.get('held')
    if held and G.S.get('actors',{}).get(held):candidates[held]=G.S['actors'][held]
    for name,a in candidates.items():
        if hasattr(G,'valid') and not G.valid(a):continue
        if hasattr(a,'get_actor_enable_collision') and not a.get_actor_enable_collision():continue
        if frame and frame.body_fully_inside(a):continue
        if bridge_overlap(_actor_bounds(a),G.D['aircraft38']['bridge']['floor_polygons']):return True
    return False

def _close_terminal():
    for name in G.S.get('doors',{}):
        if name.startswith('A07 boarding'):G.open_door(name,0)

def _terminal_closed():
    leaves=[d for n,d in G.S.get('doors',{}).items() if n.startswith('A07 boarding')]
    return bool(leaves and all(d.get('fraction',1)<.015 for d in leaves))

def request_bridge(stow=True):
    if S.get('moving'):return False,'The jetbridge is moving; wait for the status lamp.'
    if stow:
        if _bridge_occupied():return False,'The jetbridge must be empty before stowing.'
        if not door_closed():return False,'Close aircraft door L1 before stowing the bridge.'
        _close_terminal();S.update(pending_stow=True)
        G.say('Closing the terminal doors, then retracting the bridge.')
        return True,'Terminal doors closing'
    S.update(target=0.,moving=True,pending_stow=False)
    G.say('Jetbridge deploying. Keep clear of the moving equipment.')
    return True,'Deploying'

def _actor_bounds(a):
    c,e=a.get_actor_bounds(True)
    return [[(c.x-e.x)/100,-(c.y+e.y)/100,(c.z-e.z)/100],
            [(c.x+e.x)/100,-(c.y-e.y)/100,(c.z+e.z)/100]]

def collect_airport_obstacles(u,actors,ignore_names=None,ground_support_assets=None):
    """Read actual placed native meshes, including every individual ISM instance.

    Uses the same verified API as Airport38's read-only native inventory. Airport
    ground is treated by its explicit analytical grade, not a misleading global
    mesh AABB that also contains the raised terminal forecourt hundreds of metres
    away. All other collision geometry contributes its complete placed bounds.
    """
    ignore_names=ignore_names or set();out=[]
    supports=set(ground_support_assets or (G.D.get('flight39',{}).get('ground_support_assets',[]) if G else []))|{'SM_AP_Ground12','SM_AP_Asphalt'}
    for a in actors:
        name=a.get_actor_label()
        if name in ignore_names:continue
        if any(str(t).startswith('Skyward:') for t in a.tags):continue
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh')
            if not mesh or '/Game/Airport' not in mesh.get_path_name():continue
            if mesh.get_name() in supports:continue
            if 'NO_COLLISION' in str(c.get_collision_enabled()) or not c.get_editor_property('visible') or c.get_editor_property('hidden_in_game'):continue
            transforms=[c.get_instance_transform(i,True) for i in range(c.get_instance_count())] if isinstance(c,u.InstancedStaticMeshComponent) else [c.get_world_transform()]
            b=mesh.get_bounds()
            for index,t in enumerate(transforms):
                points=[u.MathLibrary.transform_location(t,b.origin+u.Vector(sx*b.box_extent.x,sy*b.box_extent.y,sz*b.box_extent.z)) for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)]
                points=[(p.x/100,-p.y/100,p.z/100) for p in points]
                bb=[[min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]]
                out.append(dict(name=name+(' instance '+str(index) if len(transforms)>1 else ''),mesh=mesh.get_name(),bounds=bb))
    return out

def departure_clearance():
    """Authoritative conservative check of actual placed native scenery.

    Excludes the aircraft itself, ambient sky and navigation support surfaces.
    The complete current aircraft box is swept forward continuously, not merely
    tested at its parked wing width or at a few disconnected sample positions.
    """
    u=G.u if hasattr(G,'u') else __import__('unreal')
    actors=u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.Actor)
    # A carry-on already inside the cabin travels with the aircraft. Treating
    # its current Airport mesh bounds as apron scenery falsely blocks taxi.
    # Registered bodies must still be physically inside; external bags and all
    # ground vehicles retain the normal obstruction check.
    frame=getattr(G,'flight39',{}).get('frame');aboard=set()
    if frame:
        candidates=set(frame.prop_records)
        if G.S.get('held'):candidates.add(G.S['held'])
        for name in candidates:
            actor=G.S['actors'].get(name)
            if actor and frame.body_fully_inside(actor):aboard.add(name)
    obstacles=collect_airport_obstacles(u,actors,ignore_names=aboard)
    return validate_sweep(obstacles, G.D['aircraft38']['departure']['distance_m'],.20)

def can_depart():
    if S.get('fraction',0)<.999 or S.get('moving') or S.get('pending_stow'):
        return False,'Stow the entire jetbridge before departure.'
    if not door_closed():return False,'Close aircraft door L1 before departure.'
    result=departure_clearance();S['last_clearance']=result
    if not result['clear']:return False,'Departure path blocked: '+', '.join(q['name'] for q in result['blocking'][:3])
    return True,'Bridge stowed, L1 closed and complete forward aircraft envelope clear.'

def guard_departure(callback,*args,**kwargs):
    """Flight/tug controllers must call this rather than bypassing the dock."""
    okay,reason=can_depart()
    if not okay:G.say(reason);G.event('Departure refused38',reason=reason);return False
    G.event('Departure released38',clearance=S['last_clearance'])
    return callback(*args,**kwargs)

def _apply_pose(fraction):
    u=G.u if hasattr(G,'u') else __import__('unreal');poses=bridge_pose(fraction)
    poses['Bridge38 cab mitre']=poses['Bridge38 docking cab'].copy()
    for name in G.D['aircraft38']['bridge']['moving_names']:
        a=G.S['actors'].get(name);pose=poses.get(name)
        if not a or not pose:continue
        a.set_actor_location(G.v(pose['location']),False,True)
        rotation=u.MathLibrary.make_rot_from_xz(G.v(pose['forward']),G.v(pose['ground_normal'])) if pose.get('ground_normal') else u.Rotator(yaw=-pose['rotation'])
        a.set_actor_rotation(rotation,False)
        if 'scale' in pose:a.set_actor_scale3d(u.Vector(*pose['scale']))
    for actor,spec in S.get('following_lights',[]):
        pose=poses.get(spec['follow_actor'])
        if pose:actor.set_actor_location(G.v(world(spec['local_point'],pose['location'],pose['rotation'])),False,True)

def _set_parking(parked):
    u=G.u if hasattr(G,'u') else __import__('unreal')
    for name in G.D['aircraft38']['parking']['vehicles']:
        a=G.S['actors'].get(name)
        if not a:continue
        c=a.static_mesh_component
        c.set_linear_damping(6.5 if parked else .8);c.set_angular_damping(9. if parked else 1.3)
        if parked:
            # Sleep real bodies after braking; constraints remain bound and can
            # wake normally. No vehicle gets pinned by a per-frame teleport.
            c.set_physics_linear_velocity(u.Vector(),False,G.NONE)
            c.set_physics_angular_velocity_in_radians(u.Vector(),False,G.NONE)
            c.put_rigid_body_to_sleep(G.NONE)
        else:c.wake_all_rigid_bodies()
    S['vehicles_parked']=parked

def _park_tick(dt):
    if G.S.get('driving') or S.get('vehicles_parked'):return
    names=G.D['aircraft38']['parking']['vehicles']
    max_speed=max([G.S['actors'][n].static_mesh_component.get_physics_linear_velocity().length() for n in names if G.S['actors'].get(n)]+[0])
    max_omega=max([G.S['actors'][n].static_mesh_component.get_physics_angular_velocity_in_radians().length() for n in names if G.S['actors'].get(n)]+[0])
    S['quiet_time']=S.get('quiet_time',0)+dt if max_speed<8 and max_omega<.08 else 0
    if S['quiet_time']>.65:_set_parking(True)

def _tick(dt):
    S['physics_base'](dt)
    if G.S.get('ticks',0)>=6 and not S.get('initial_park_applied'):
        _set_parking(True);S['initial_park_applied']=True
    if S.get('pending_stow'):
        # Occupancy is rechecked after the gate leaves have finished closing.
        if _bridge_occupied() or not door_closed():S['pending_stow']=False
        elif _terminal_closed():S.update(target=1.,moving=True,pending_stow=False)
    if S.get('moving'):
        speed=dt/G.D['aircraft38']['bridge']['stow_duration_s'];f=S['fraction'];t=S['target']
        f=max(t,f-speed) if t<f else min(t,f+speed);S['fraction']=f;_apply_pose(f)
        if abs(f-t)<1e-6:
            S['moving']=False;G.S['bridge38_state']='stowed' if f>.99 else 'deployed'
            G.event('Jetbridge position38',state=G.S['bridge38_state'])
            if f<.01:G.say('Jetbridge docked. Gate A07 is ready for boarding.')
    _park_tick(dt)

def install(game):
    global G
    G=game
    if S.get('installed'):return
    u=G.u if hasattr(G,'u') else __import__('unreal')
    S.update(installed=True,fraction=0.,target=0.,moving=False,pending_stow=False,vehicles_parked=False,physics_base=G.physics)
    G.physics=_tick;G.S['bridge38_state']='deployed'
    # Existing driver and towing controls are retained, merely waking/braking the
    # parked group on actual entry/exit.
    base_drive,base_exit,base_act,base_open=G.drive,G.exit_drive,G.act,G.open_door
    def drive(q):_set_parking(False);S['quiet_time']=0;return base_drive(q)
    def leave():
        out=base_exit()
        for n in G.D['aircraft38']['parking']['vehicles']:
            a=G.S['actors'].get(n)
            if a:a.static_mesh_component.set_linear_damping(6.5);a.static_mesh_component.set_angular_damping(9.)
        S['quiet_time']=0;return out
    def act(q):
        if q['kind']=='bridgecontrol38':
            okay,reason=request_bridge(S['fraction']<.5);G.say(reason);return okay
        if q['kind'] in ('boarding','boardingdoor') and (S['fraction']>.001 or S['moving'] or S['pending_stow']):
            G.say('Deploy and dock the jetbridge before boarding.');return False
        return base_act(q)
    def open_gate(name,value=1):
        if name.startswith('A07 boarding') and value>0 and (S['fraction']>.001 or S['moving'] or S['pending_stow']):return
        return base_open(name,value)
    G.drive,G.exit_drive,G.act,G.open_door=drive,leave,act,open_gate
    # An auto-open terminal door must obey the same physical dock interlock.
    for n,d in G.S.get('doors',{}).items():
        if n.startswith('A07 boarding'):d['automatic']=False
    # Close/open the aircraft through its real compound hinge, preserving the
    # aircraft's existing animation. While stowed, L1 may not open into open air.
    old_use=G.P.use_nearest
    def plane_use(*args,**kwargs):
        q=G.P.nearest()
        if q and q.get('actor')==L1 and (S['fraction']>.001 or S['moving']):
            G.say('Dock the jetbridge before opening L1.');return True
        return old_use(*args,**kwargs)
    G.P.use_nearest=plane_use
    # Root installs an authoritative journey module after this one. That module
    # should call this API when authorising boarding or any future flight mode.
    G.airside38=dict(request_bridge=request_bridge,can_depart=can_depart,guard_departure=guard_departure,
                     door_closed=door_closed,bridge_occupied=_bridge_occupied,departure_clearance=departure_clearance,
                     floor_enabled=lambda:S['fraction']<.001 and not S['moving'] and not S['pending_stow'])
    native_lights=list(u.GameplayStatics.get_all_actors_of_class(G.P.STATE['world'],u.Light))
    following=[]
    for spec in G.D.get('lights',[]):
        if not spec.get('follow_actor'):continue
        light=next((a for a in native_lights if spec['name'] in a.get_actor_label()),None)
        if light:following.append((light,spec))
    S['following_lights']=following
    G.event('Airside38 installed',aircraft_offset_m=[16,0,0],bridge_components=len(G.D['aircraft38']['bridge']['moving_names']),interlock=True)
    return G.airside38
