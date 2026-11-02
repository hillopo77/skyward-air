"""Staged native Window41/Belt40/bridge checks, separate from the fresh route.

Parent copies this module to Content/Python and calls start(G) after all actual
runtime installers. This module never installs a gameplay adapter or edits an
asset. Setup pawn/prop poses and ticket flags are explicitly recorded.
"""
import hashlib,importlib,json,math,time,traceback
from pathlib import Path
import unreal as u

G=None
S={}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def requirements(game):
    records=game.D.get('repair38',{}).get('business_belt40',{}).get('records',[])
    if len(records)!=4:raise RuntimeError('Assemblies41 requires all4 actual BusinessBelt40 records')
    if sum(bool(r.get('occupied_npc')) for r in records)!=1:raise RuntimeError('Expected one actually occupied business suite')
    if not game.P.DATA.get('window41_prepared'):raise RuntimeError('Window41 data preparation is absent')
    if not game.P.DATA.get('business_belt40_prepared'):raise RuntimeError('BusinessBelt40 data preparation is absent')
    if game.P.set_control_state is not getattr(game.P,'_business_belt40_setter',None):raise RuntimeError('BusinessBelt40 must install after Flight39')
    if game.P._apply_movable is not getattr(game.P,'_window41_adapter',None):raise RuntimeError('Window41 must install after Window40/Flight39')
    if not getattr(game,'flight39',{}).get('frame'):raise RuntimeError('Actual Flight39 reference frame is required')
    return records


def belt_evidence(game,record,expected):
    """Read native lid transform/visibility as well as the logical index."""
    p=game.P;frame=game.flight39['frame'];state=p.STATE['controls'][record['control']]['state']
    actors=p.STATE['actors'];lid=actors[record['control']]
    hinge=list(game.source(frame.reference(lid.get_actor_location())))
    expected_hinge=record['worn_hinge' if expected==0 else 'stowed_hinge']
    error=math.dist(hinge,expected_hinge)*100
    worn=not bool(actors[record['worn_actor']].get_editor_property('hidden'))
    stowed=not bool(actors[record['stowed_actor']].get_editor_property('hidden'))
    snapshot=p.control_snapshot(record['control'])
    return dict(passed=state==expected and worn==(expected==0) and stowed==(expected==1) and error<.05 and snapshot['passed'],
                state=state,expected=expected,lid_hinge_source_m=hinge,hinge_error_cm=error,
                worn_visible=worn,stowed_visible=stowed,native_control_snapshot=snapshot,
                source_seat=record['seat'],occupied_npc=record.get('occupied_npc'))


def save(status='RUNNING',**extra):
    report=dict(status=status,context=S.get('context'),phase=S.get('phase'),checks=S.get('checks',[]),
                captures=S.get('captures',[]),actions=S.get('actions',[]),setup=S.get('setup',[]),
                setup_pawn_teleports=S.get('pawn_teleports',0),setup_prop_teleports=S.get('prop_teleports',0),
                setup_camera_poses=S.get('camera_poses',0),physical_walk_steps=0,
                scope='Explicit staged native safety/input/pose cases. Does not replace the fresh passenger/flight route.',**extra)
    (G.R/'ArtBible'/S['output']).write_text(json.dumps(report,indent=2),encoding='utf-8')


def check(name,passed,**evidence):
    S['checks'].append(dict(name=name,passed=bool(passed),**evidence));save();return bool(passed)


def action(name,**fields):S['actions'].append(dict(action=name,time_s=time.monotonic()-S['start'],**fields))


def finish(status,**extra):
    global G
    save(status,**extra)
    if S.get('handle'):u.unregister_slate_post_tick_callback(S['handle'])
    quit_when_done=S.get('quit_when_done');world=G.P.STATE['world'];pc=G.P.STATE['pc']
    # Release this review's native cameras/transforms/actor wrappers while the
    # world and Python runtime still exist, rather than during interpreter exit.
    S.clear();G=None
    if quit_when_done:u.SystemLibrary.quit_game(world,pc,u.QuitPreference.QUIT,False)


def advance():
    S['i']+=1;S['since']=time.monotonic();S['phase']=S['steps'][S['i']] if S['i']<len(S['steps']) else 'complete';save()


def at(point):
    if G.P.STATE.get('seated'):raise RuntimeError('Staged pose cannot silently stand a seated player')
    pawn=G.P.STATE['pawn'];frame=G.flight39['frame'];move=pawn.get_component_by_class(u.FloatingPawnMovement)
    move.stop_movement_immediately();move.set_plane_constraint_enabled(False)
    pawn.set_actor_location(frame.world(G.v(point)),False,True)
    if frame.point_inside(pawn.get_actor_location()):
        if not frame.attached:frame.attach(pawn);frame.attached=True
        frame.floor(0)
    elif frame.attached:frame.detach_pawn()
    G.P.STATE['pc'].reset_ignore_move_input();G.P.STATE['pc'].set_view_target_with_blend(pawn,0)
    S['pawn_teleports']+=1;S['setup'].append(dict(kind='pawn_pose',source_m=point))


def aim_use(item,candidates=None):
    """Only call the normal use dispatcher when the actual target is selected."""
    p=G.P;pc=p.STATE['pc'];attempts=[]
    for point in candidates or [None]:
        if point is not None:at(point)
        target=p.interaction_point(item);pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(p.STATE['pawn'].get_actor_location(),target))
        near=p.nearest();visible=p.interaction_visible(item)
        attempts.append(dict(player=list(G.source(G.flight39['frame'].reference(p.STATE['pawn'].get_actor_location()))),
                             selected=near['actor'] if near else None,visible=bool(visible)))
        if near and near['actor']==item['actor'] and visible:
            result=G.use_nearest(False);action('visible_target_use',actor=item['actor'],result=str(result),attempts=attempts);return True
    action('target_not_reachable',actor=item['actor'],attempts=attempts);return False


def approaches(record,item):
    x,y,_=record['location'];side=1 if x<G.D['aircraft38']['offset'][0] else -1
    points=[item['validation_approach']] if item.get('validation_approach') else []
    return points+[[x+side*.65,y-.65,1.62],[x+side*.8,y-.2,1.62],[x,y-.8,1.62]]


def view(record):
    x,y,_=record['location'];side=1 if x<G.D['aircraft38']['offset'][0] else -1
    return [x+side*.9,y-.95,1.25],[x,y-.28,.72]


def photo(label,eye,target):
    if not S['screenshots']:advance();return
    p=G.P;camera=S['camera'];frame=G.flight39['frame'];pc=p.STATE['pc']
    S['saved_camera']=camera.get_actor_transform()
    position=frame.world(G.v(eye));look=frame.world(G.v(target))
    camera.set_actor_location_and_rotation(position,u.MathLibrary.find_look_at_rotation(position,look),False,True)
    pc.set_view_target_with_blend(camera,0);S['camera_poses']+=1
    S['photo_pending']=dict(label=label,path=G.R/'Screenshots'/(label+'.png'),ready=time.monotonic()+.25)


def photo_tick(now):
    pending=S.get('photo_pending')
    if not pending:return False
    path=pending['path']
    if 'requested' not in pending:
        if now<pending['ready']:return True
        pending['requested']=time.time();pending['deadline']=now+20
        u.SystemLibrary.execute_console_command(G.P.STATE['world'],'Shot -nosuffix filename="'+path.as_posix()+'"',G.P.STATE['pc']);return True
    if path.exists() and path.stat().st_mtime>=pending['requested']:
        S['captures'].append(dict(label=pending['label'],file=str(path),sha256=digest(path),type='genuine native screenshot'))
        camera=S['camera'];saved=S.pop('saved_camera')
        camera.set_actor_location_and_rotation(saved.translation,saved.rotation.rotator(),False,True)
        G.P.STATE['pc'].set_view_target_with_blend(G.P.STATE['pawn'],0);S.pop('photo_pending');advance();return True
    if now>pending['deadline']:raise RuntimeError('Native screenshot timeout '+pending['label'])
    return True


def stage_bag(point):
    if G.S.get('held'):G.release(False)
    a=S['bag'];c=a.static_mesh_component;frame=G.flight39['frame']
    # An explicit staged setup, not an accepted baggage transfer or fresh walk.
    if S['bag_name'] in frame.prop_records:frame._leave_prop(S['bag_name'],frame.prop_records[S['bag_name']])
    desired=frame.world(G.v(point));a.set_actor_location(desired-c.get_center_of_mass()+a.get_actor_location(),False,True)
    c.set_physics_linear_velocity(u.Vector(),False,G.NONE);c.set_physics_angular_velocity_in_radians(u.Vector(),False,G.NONE)
    c.wake_all_rigid_bodies();S['prop_teleports']+=1
    S['setup'].append(dict(kind='prop_pose',actor=S['bag_name'],source_com_m=point,physics_simulating=c.is_simulating_physics()))


def window_evidence(q,expected):
    import window40
    frame=G.flight39['frame'];m=G.P.STATE['movables'][q['actor']];errors=[]
    for part in q['roller_parts']:
        wanted=window40.shade_pose(part,expected);wanted[0]+=part['window40_side']*.008
        actual=G.P.STATE['actors'][part['actor']].get_actor_location()
        errors.append(dict(actor=part['actor'],error_cm=(actual-frame.world(G.v(wanted))).length()))
    return dict(passed=abs(m['progress']-expected)<.01 and all(r['error_cm']<.05 for r in errors),
                progress=m['progress'],target=m['target'],expected=expected,actual_parts=errors)


def bin_evidence(q,expected):
    p=G.P;frame=G.flight39['frame'];m=p.STATE['movables'][q['actor']];a=m['actor'];closed=m['closed_rotation']
    axis=q['motion'].get('axis','z');declared=float(q['motion']['amount_degrees'])
    expected_q=frame.rotation(p._quat_product(closed,p._source_quat(axis,declared*expected))).rotator();actual=a.get_actor_rotation()
    error=max(abs((getattr(actual,k)-getattr(expected_q,k)+180)%360-180) for k in ('pitch','yaw','roll'))
    current=frame.reference_rotation(actual.quaternion());inverse=u.Quat(x=-closed.x,y=-closed.y,z=-closed.z,w=closed.w)
    relative=p._quat_product(inverse,current)
    angle=math.degrees(2*math.atan2(getattr(relative,axis),relative.w))*(-1 if axis in ('x','z') else 1)
    angle=(angle+180)%360-180
    hinge_error=(a.get_actor_location()-frame.world(m['closed_location'])).length()
    return dict(passed=abs(declared)==78 and abs(m['progress']-expected)<.01 and error<.15 and hinge_error<.05,
                progress=m['progress'],target=m['target'],declared_open_angle_degrees=declared,
                measured_relative_angle_degrees=angle,rotation_error_degrees=error,hinge_error_cm=hinge_error)


def phase_error(error):
    phase=S.get('phase','unknown');check('Native phase error '+phase,False,error=error)
    if phase=='sit':S['seat_failed']=True
    if phase.startswith('bridge'):S['bridge_unsafe']=True
    # A screenshot failure must not strand the camera or hide later independent
    # geometry/safety findings behind a repeated pending request.
    if S.pop('photo_pending',None):
        saved=S.pop('saved_camera',None)
        if saved:
            S['camera'].set_actor_location_and_rotation(saved.translation,saved.rotation.rotator(),False,True)
        G.P.STATE['pc'].set_view_target_with_blend(G.P.STATE['pawn'],0)
    advance()


def tick(dt):
    try:
        now=time.monotonic()
        if photo_tick(now):return
        if S['i']>=len(S['steps']):finish('PASS' if all(c['passed'] for c in S['checks']) else 'FAIL');return
        phase=S['steps'][S['i']];S['phase']=phase;elapsed=now-S['since'];p=G.P;frame=G.flight39['frame'];record=S['empty'];q=S['belt_item']
        if S.get('bridge_unsafe') and phase.startswith('bridge'):
            check('Unsafe bridge case skipped '+phase,False,skipped=True,reason='L1/bridge setup failed; no unsafe stow action performed');advance();return
        if S.get('seat_failed') and phase in ('fasten','release','refasten','fastened_photo','released_photo','stand'):
            check('Dependent seated case skipped '+phase,False,skipped=True,reason='Actual visible suite occupation failed; window/bridge cases continue');advance();return
        if phase=='defaults':
            prepared=[i for i in p.STATE['items'] if i.get('window41')]
            check('All48 retained window mechanisms have Window41 data',len(prepared)==48,count=len(prepared))
            bindings=[]
            for instance in p.DATA['instances']:
                if not instance['asset'].startswith(('SM_AP_W41','SM_AP_W42')):continue
                actor=p.STATE['actors'].get(instance['name']);component=actor.static_mesh_component if actor else None
                mesh=component.static_mesh.get_name() if component and component.static_mesh else None
                bindings.append(dict(actor=instance['name'],expected=instance['asset'],actual=mesh,passed=mesh==instance['asset']))
            check('Actual native Window41 wall/frame/rack bindings',len(bindings)==126 and all(b['passed'] for b in bindings),count=len(bindings),bindings=bindings)
            for r in S['records']:
                evidence=belt_evidence(G,r,r['initial_state']);check('Actual default suite belt '+r['seat'],evidence['passed'],evidence=evidence)
            check('Exactly one occupied default fastened and three empty stowed',sum(r['initial_state']==0 and bool(r['occupied_npc']) for r in S['records'])==1 and sum(r['initial_state']==1 and not r['occupied_npc'] for r in S['records'])==3)
        elif phase=='npc_photo':photo('Assemblies41_NPCFastened',*view(S['npc']));return
        elif phase=='empty_photo':photo('Assemblies41_EmptyStowed',*view(record));return
        elif phase=='outside_denied':
            used=aim_use(q,approaches(record,q));after=belt_evidence(G,record,1)
            check('Empty suite cannot fasten while player stands outside',used and not p.STATE.get('seated') and after['passed'],visible_normal_use=used,evidence=after)
            if not used:
                # Negative API check is explicit; inability to target remains a
                # failed input check and is never silently treated as success.
                p.set_control_state(record['control'],0);action('direct_guard_api_probe',actor=record['control'],requested_state=0)
                check('Outside direct API guard also denies fastening',belt_evidence(G,record,1)['passed'])
        elif phase=='sit':
            seat=next(i for i in p.STATE['items'] if i['actor']==record['seat'] and i['kind']=='seat')
            used=aim_use(seat,approaches(record,seat))
            okay=used and p.STATE.get('seated') and p.STATE['seated'].get('actor')==record['seat']
            check('Player occupies actual empty suite via visible seat',okay)
            if not okay:S['seat_failed']=True
        elif phase in ('fasten','release','refasten'):
            expected=1 if phase=='release' else 0;used=aim_use(q);evidence=belt_evidence(G,record,expected)
            check('Player '+phase+' drives actual lid and webbing',used and evidence['passed'],evidence=evidence,visible_normal_use=used)
        elif phase=='fastened_photo':photo('Assemblies41_PlayerFastened',*view(record));return
        elif phase=='released_photo':photo('Assemblies41_PlayerReleased',*view(record));return
        elif phase=='stand':
            saved=p.STATE.get('seated');expected_return=saved.get('return') if saved else None
            if expected_return is not None and saved.get('return_frame39'):expected_return=frame.world(expected_return)
            p.stand();action('normal_stand_api');evidence=belt_evidence(G,record,1)
            check('Normal stand auto-stows actual suite belt',not p.STATE.get('seated') and evidence['passed'],evidence=evidence)
            actual=p.STATE['pawn'].get_actor_location();local=list(G.source(frame.reference(actual)))
            returned=(actual-expected_return).length() if expected_return is not None else None
            check('Normal suite stand returns actual eye height and saved position',not p.STATE.get('seated') and abs(local[2]-p.EYE_HEIGHT)<.03 and returned is not None and returned<2.,
                  local_eye_m=local,expected_eye_height_m=p.EYE_HEIGHT,return_error_cm=returned)
        elif phase=='window_close':
            w=S['window'];m=p.STATE['movables'][w['actor']]
            used=aim_use(w,S['window_approaches']) if m['target']>.5 else False
            check('Actual Window41 shade close control is reachable',used and m['target']==0.)
        elif phase in ('window_closed','window_opened'):
            expected=0. if phase=='window_closed' else 1.;evidence=window_evidence(S['window'],expected)
            if abs(evidence['progress']-expected)>.01 and elapsed<6:return
            check('Actual Window41 curved parts '+phase,evidence['passed'],evidence=evidence)
        elif phase in ('window_closed_photo','window_open_photo'):
            w=S['window'];x,y,z=w['point'];side=1 if x<16 else -1
            photo('Assemblies41_WindowClosed' if 'closed' in phase else 'Assemblies41_WindowOpen',[x+side*1.15,y-.1,1.62],[x,y,1.5]);return
        elif phase=='window_open':
            used=aim_use(S['window'],S['window_approaches']);check('Actual Window41 shade open control is reachable',used and p.STATE['movables'][S['window']['actor']]['target']==1.)
        elif phase in ('bin_open','bin_close'):
            expected=1. if phase=='bin_open' else 0.;item=S['bin'];moving=p.STATE['movables'][item['actor']]
            used=aim_use(item,S['bin_approaches']) if moving['target']!=expected else False
            check('Actual overhead bin '+phase+' control is reachable',used and moving['target']==expected,actor=item['actor'])
        elif phase in ('bin_opened','bin_closed'):
            expected=1. if phase=='bin_opened' else 0.;evidence=bin_evidence(S['bin'],expected)
            if abs(evidence['progress']-expected)>.01 and elapsed<6:return
            check('Actual retained overhead bin '+phase+' pose',evidence['passed'],evidence=evidence)
        elif phase=='bin_photo':
            item=S['bin'];x,y,z=item['point'];side=1 if x<16 else -1
            photo('Assemblies41_BinOpen78',[x+side*.9,y-.65,1.62],[x,y,2.05]);return
        elif phase=='bridge_setup':
            at([-16.8,2.2,1.62]);moving=p.STATE['movables'][G.D['aircraft_door']];moving['target']=0.
            S['setup'].append(dict(kind='direct_close_target_for_staged_bridge_safety',actor=G.D['aircraft_door'],target=0.,progress_not_injected=True))
        elif phase=='bridge_ready':
            if not G.airside38['door_closed']() and elapsed<6:return
            check('Real L1 animation closed before bridge prop cases',G.airside38['door_closed']())
            if not G.airside38['door_closed']():S['bridge_unsafe']=True
        elif phase=='bridge_loose':
            stage_bag([12.5,.675,.75]);occupied=G.airside38['bridge_occupied']();okay,reason=G.airside38['request_bridge'](True)
            check('Loose physical bag on docking cab blocks stow',occupied and not okay,reason=reason,body_fully_inside=frame.body_fully_inside(S['bag']))
            if okay:G.airside38['request_bridge'](False);action('cancel_unexpected_stow_via_normal_deploy_api')
        elif phase=='bridge_photo':photo('Assemblies41_BridgeBagBlocked',[11.,-.25,1.6],[12.5,.675,.75]);return
        elif phase=='bridge_aboard_setup':stage_bag([16,2.2,.75])
        elif phase=='bridge_aboard':
            if elapsed<.4:return
            inside=frame.body_fully_inside(S['bag']);occupied=G.airside38['bridge_occupied']();okay,reason=G.airside38['request_bridge'](True)
            check('Complete body aboard allows bridge stow request',inside and not occupied and okay,reason=reason,whole_body_inside=inside,bridge_occupied=occupied,source_bounds_m=frame.body_source_bounds(S['bag']),
                  setup_location='Clear central business-entry aisle; not intersecting the cockpit pedestal')
            if okay:
                reset,why=G.airside38['request_bridge'](False);action('normal_deploy_request_cancels_staged_pending_stow',accepted=reset,reason=why)
        elif phase=='bridge_deployed':
            if not G.airside38['floor_enabled']() and elapsed<6:return
            check('Bridge remains deployed before doorway straddle case',G.airside38['floor_enabled']())
        elif phase=='bridge_straddle':
            stage_bag([14.15,.675,.75]);bounds=frame.body_source_bounds(S['bag']);inside=frame.body_inside(S['bag']);full=frame.body_fully_inside(S['bag'])
            clearance=G.airside38['departure_clearance']();blocked=[b['name'] for b in clearance['blocking'] if b['name']==S['bag_name'] or b['name'].startswith(S['bag_name']+' instance ')]
            check('Door-straddling body cannot receive departure exemption',inside and not full and bool(blocked),source_bounds_m=bounds,centre_inside=inside,whole_body_inside=full,actual_blocking_entries=blocked,
                  method='Immediate actual native collision bounds after an explicitly recorded staged pose; no simulated settlement claim')
        else:raise RuntimeError('Unknown Assemblies41 phase '+phase)
        advance()
    except Exception:
        error=traceback.format_exc()
        try:phase_error(error)
        except Exception:finish('ERROR',error=error,recovery_error=traceback.format_exc())


def start(game,screenshots=True,quit_when_done=True,output='Assemblies41QA.json'):
    global G;G=game
    if S.get('handle'):raise RuntimeError('Assemblies41 harness already started')
    records=requirements(G);G.QA=True;G.CAPTURE=False
    empty=next(r for r in records if not r['occupied_npc']);npc=next(r for r in records if r['occupied_npc'])
    p=G.P;item=next(q for q in p.STATE['items'] if q['actor']==empty['control']);centre=G.D['aircraft38']['offset'][0]
    windows=[q for q in p.STATE['items'] if q.get('window41') and q['point'][0]<centre]
    window=min(windows,key=lambda q:abs(q['point'][1]-empty['location'][1]))
    x,y,z=window['point'];approach=window.get('validation_approach',[x+.8,y,1.62])
    bins=[q for q in p.STATE['items'] if q.get('motion') and q['actor'].startswith('Overhead bin ') and q['point'][0]<centre]
    overhead=min(bins,key=lambda q:abs(q['point'][1]-window['point'][1]));bx,by,bz=overhead['point']
    bag_name=next(n for n in ['Physical luggage 05',*G.S['physics']] if n in G.S['physics'] and n not in G.journey38['state']['registered_bags'] and G.S['actor_specs'][n]['asset'].startswith(('SM_AP_Bag','SM_AP_CarryOn')))
    context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text())
    source_path=G.R/'ArtBible/Assemblies41Source.json';context['assemblies41_source']=json.loads(source_path.read_text())['source_sha256']
    context['harness_sha256']=digest(__file__);context['live_runtime_sha256']={}
    for name in ('flight39_frame','flight39_envelope','airport_airside38','window40','window41','business_belt40','chair_runtime39','characters39_runtime'):
        module=importlib.import_module(name);context['live_runtime_sha256'][name+'.py']=digest(module.__file__)
    steps=['defaults','npc_photo','empty_photo','outside_denied','sit','fasten','fastened_photo','release','released_photo','refasten','stand',
           'window_close','window_closed','window_closed_photo','window_open','window_opened','window_open_photo',
           'bin_open','bin_opened','bin_photo','bin_close','bin_closed',
           'bridge_setup','bridge_ready','bridge_loose','bridge_photo','bridge_aboard_setup','bridge_aboard','bridge_deployed','bridge_straddle']
    camera=G.flight39['runtime'].get('chase') or next((c for c in p.STATE.get('review_cameras',[]) if c.get_actor_label()=='Flight39 Chase'),None)
    if screenshots and camera is None:raise RuntimeError('Assemblies41 needs the actual native Flight39 chase camera for screenshots')
    S.update(i=0,phase=steps[0],since=time.monotonic(),start=time.monotonic(),records=records,empty=empty,npc=npc,belt_item=item,
             window=window,window_approaches=[approach,[x+1.,y-.4,1.62],[x+1.2,y+.2,1.62]],
             bin=overhead,bin_approaches=[[bx+.7,by-.3,1.62],[bx+.9,by+.25,1.62]],steps=steps,
             bag_name=bag_name,bag=G.S['actors'][bag_name],checks=[],captures=[],actions=[],setup=[],pawn_teleports=0,prop_teleports=0,camera_poses=0,
             context=context,camera=camera,screenshots=bool(screenshots),quit_when_done=bool(quit_when_done),output=output)
    G.S.update(checked_in=True,security=True,boarding=True,aboard=True)
    S['setup'].append(dict(kind='direct_journey_flags_for_independent_staged_cases',checked_in=True,security=True,boarding=True,aboard=True))
    S['handle']=u.register_slate_post_tick_callback(tick);save();return dict(output=str(G.R/'ArtBible'/output),phases=len(steps),source_context=context)
