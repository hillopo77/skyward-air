"""Airport38 authoritative passenger flow and real-body service interactions.

Install on the unwrapped airport core plus ext11/characters12/clarity26 and
airside38. Do not install the legacy22/24/27–37 journey/room/queue wrappers.
"""
import math,time,json,hashlib
from pathlib import Path
import journey_logic38 as L

G=None;S={}
FLOW={'checkin','bagdrop','scanner','security','boarding','boardingdoor','equipment_toggle','vending','slide'}


def _bag(n):
    asset=G.S['actor_specs'].get(n,{}).get('asset','')
    return asset.startswith('SM_AP_Bag') or asset=='SM_AP_CarryOn'


def emit(name,**kw):
    S['events'].append(dict(event=name,time_s=time.monotonic()-S['started'],**kw))
    G.event(name,**kw)


def ticket():
    if not S.get('ticket'):
        S['ticket']=dict(id='SW-SA107-LOCAL-38',flight='SA107',gate='A07',destination='Azure Bay',
            seat='03E',cabin='Economy',checked_bags=[],security_cleared=False,gate_scanned=False,aboard=False)
    return S['ticket']


def objective():
    if G.P.STATE.get('seated') and G.S.get('aboard'):return 'Welcome aboard SA107 / seated'
    if G.S.get('aboard'):return 'Economy 03E / right aisle, third row'
    if G.S.get('boarding'):return 'Walk through the enclosed jetbridge to L1'
    if G.S.get('security'):return 'Find Gate A07 / scan your boarding pass'
    if G.S.get('checked_in'):return 'Bag drop optional / scan cabin bag, then walk through detector'
    q=S.get('queue',{})
    if q.get('called'):return 'Check-in desk '+q['called'].rsplit(' ',1)[-1]+' is free / collect your boarding pass'
    if q.get('joined'):return 'Wait at the queue / '+str(len(q.get('waiting',[])))+' passengers ahead'
    return 'Join the check-in queue / optional self-service kiosks'


def visible(q):
    """Only the intended physical control can finish an interaction ray."""
    u=G.u;start=G.P.STATE['pawn'].get_actor_location();end=G.point(q)
    ignored=[G.P.STATE['pawn']]
    if G.S.get('held'):ignored.append(G.S['actors'][G.S['held']])
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],start,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True,ignored,u.DrawDebugTrace.NONE,True)
    if not hit:return True
    h=hit.to_tuple()
    if not h[0]:return True
    actor=h[9]
    if actor==G.S['actors'].get(q['actor']) or actor==G.S['actors'].get(q.get('release_actor')):return True
    if q['kind']=='seat':
        if actor==G.S['actors'].get(q.get('mesh_actor')):return True
        comp=h[10] if len(h)>10 else None
        if comp and isinstance(comp,u.InstancedStaticMeshComponent) and comp.static_mesh and comp.static_mesh.get_name()==q.get('asset'):return True
    return (h[5]-end).length()<10


def usable(q):
    return (G.point(q)-G.P.STATE['pawn'].get_actor_location()).length()<=340 and visible(q)


def nearest():
    original=G.S['targets'];cup=G.D['repair38']['journey']['serving_cup']
    G.S['targets']=[q for q in original if not (q['actor']==cup and not S['coffee']['served'])
                   and not (q.get('kind')=='pickup' and q['actor'] in S['registered_bags'])]
    try:return S['base_nearest']()
    finally:G.S['targets']=original


def _indicator(name,locked):
    u=G.u;m=u.load_asset(G.AP_BASE+'/Materials/Instances/MI_AP_'+('RedLED' if locked else 'GreenLED'))
    for q in G.S['targets']:
        if q['actor']!=name or not q.get('release_actor'):continue
        a=G.S['actors'].get(q['release_actor'])
        if not a:continue
        c=a.static_mesh_component
        for i,slot in enumerate(c.static_mesh.static_materials):
            if str(slot.material_slot_name)=='MI_AP_GreenLED':c.set_material(i,m)


def _door_act(q):
    name=q['actor'];d=G.S['doors'][name];lock=S['wc_locks'].get(name,False)
    inside=q.get('inside_release',False)
    if not L.door_access(q,G.S,lock,inside):
        G.say('Occupied / use another cubicle' if lock else 'Staff access only' if q.get('access24')=='staff24'
              else 'Collect your boarding pass before security' if q.get('access24')=='checked_in'
              else 'Complete screening before entering the concourse')
        emit('Door release denied38',actor=name,locked=lock,requires=q.get('access24'));return False
    to=0 if d['target']>.5 else 1
    if name in S['wc_locks']:
        # Inside close is the privacy lock; inside open always releases it.
        S['wc_locks'][name]=bool(inside and not to)
        _indicator(name,S['wc_locks'][name])
        G.say('Occupied / privacy locked' if S['wc_locks'][name] else 'Vacant / door opening' if to else 'Vacant / door closing')
    G.open_door(name,to);emit('Door release38',actor=name,target=to,locked=S['wc_locks'].get(name,False));return True


def _belt_by_name(name):return next(q for q in G.D['conveyors'] if q['name']==name)


def _request_deposit(q):
    name=G.S.get('held')
    if not name or not _bag(name):return False
    belt=_belt_by_name(q['actor']);receiver=next((r for r in G.D['repair38']['journey']['bag_receivers'] if r['feed']==q['actor']),None)
    if receiver and S['receiver_occupants'].get(receiver['name']):
        G.say('This receiving bay contains a checked suitcase; use the other bag-drop belt.');return False
    x0,x1,y0,y1=belt['rect']
    goal=belt.get('load_point',[(x0+x1)/2,y0+.70,belt['height']+.53])
    if belt['kind']=='security':
        # Release on the supported input rollers BEFORE the scanner mouth.
        # y1.9 put the held bag's leading half through the curtain/header while
        # its COM was still approaching the release point.
        fronts=[q for q in G.D['repair38']['equipment']['curtains']
                if q['lane']==(0 if belt['name'].endswith('01') else 1) and 'front' in q['actor']]
        front=min(q['hinge'][1] for q in fronts) if fronts else y0+.725
        load_y=max(y0+.15,min(y0+.20,front-.50))
        goal=[(x0+x1)/2,load_y,belt['height']+.53]
    # Native spring carrying moves the bag to this reachable load point, then
    # releases it to gravity. No actor transform is assigned by the transfer.
    G.S['deposit_goal']=G.v(goal);S['deposit']=dict(actor=name,belt=belt['name'],goal=list(goal),began=time.monotonic())
    S['powered'][belt['name']]=True
    if receiver:S['bag_states'][name]=dict(state='loading',feed=belt['name'],receiver=receiver['name'])
    G.say('Placing suitcase on the belt / E cancels before release');emit('Native bag placement requested38',actor=name,belt=belt['name']);return True


def _coffee(q):
    coffee=S['coffee'];cup=coffee['actor'];a=G.S['actors'][cup];c=a.static_mesh_component
    if coffee['served']:
        if G.S.get('held')==cup:
            goal=G.D['repair38']['journey']['cup_station'];G.S['deposit_goal']=G.v([goal[0],goal[1],goal[2]+.08])
            S['returning_cup']=time.monotonic();G.say('Returning the cup to its saucer');return True
        G.say('One coffee is ready on the saucer / pick it up before ordering again');return False
    # A single existing cup is revealed on a real supported station; no repeated
    # spawning or overlapping cup pile is possible.
    coffee.update(served=True,sips=3);a.set_actor_hidden_in_game(False);a.set_actor_enable_collision(True)
    c.set_simulate_physics(True);c.wake_all_rigid_bodies()
    G.say('Coffee served on the saucer / E pick up, left mouse sip');emit('Coffee physically served38',actor=cup)
    return True


def act(q):
    kind=q['kind'];name=q['actor']
    if kind in FLOW and not usable(q):G.say('Move closer and face the actual control');return False
    if name==G.D['repair38']['journey']['queue']['marker']:
        queue=S['queue']
        if not queue['joined']:
            queue['joined']=True;emit('Check-in queue joined38',ahead=len(queue['waiting']))
        G.say(objective());return True
    if kind=='checkin':
        queue=S['queue']
        if name.startswith('Check-in desk ') and not G.S.get('checked_in') and queue.get('called')!=name:
            G.say('Join the queue first / we will call a free numbered desk');return False
        G.S['checked_in']=True;ticket();G.screen(G.S['actors'].get(name),'CheckedIn');G.cue('Ticket',q['point'])
        G.say('SA107 / Azure Bay / Economy03E / Gate A07 / B shows your pass');emit('Boarding pass issued38',actor=name)
        return True
    if kind=='slide':return _door_act(q)
    if kind=='equipment_toggle':
        belt=q['conveyor'];S['powered'][belt]=not S['powered'].get(belt,True)
        G.say(belt+(' running' if S['powered'][belt] else ' stopped / press again to reset'))
        emit('Conveyor power38',belt=belt,running=S['powered'][belt]);return True
    if kind=='bagdrop':
        if not G.S.get('checked_in'):G.say('Check in before loading a checked suitcase');return False
        G.S['bag_drop_armed']=True;S['powered'][name]=True
        if G.S.get('held'):
            if not _bag(G.S['held']):G.say('Only a suitcase belongs on the checked baggage belt');return False
            return _request_deposit(q)
        G.say('Place a suitcase on the running belt; it is accepted only inside the receiving bay')
        return True
    if kind in ('scanner','security'):
        if not G.S.get('checked_in'):G.say('Collect a boarding pass before screening');return False
        lane=q.get('lane',0);belt='Security belt %02d'%(lane+1);S['powered'][belt]=True
        G.S['screening_armed']=True;S['armed_lanes'].add(lane)
        if G.S.get('held') and _bag(G.S['held']):
            _request_deposit(dict(q,actor=belt));return True
        G.say('Place your cabin bag on the belt, collect it after the scanner, then walk through the detector')
        emit('Screening lane ready38',lane=lane);return True
    if kind in ('boarding','boardingdoor'):
        if q.get('gate','A07')!='A07':G.say('A08 north lounge / SA107 boards at A07');return True
        if not G.S.get('checked_in') or not G.S.get('security'):
            G.say('A valid boarding pass and completed screening are required');emit('Boarding denied38');return False
        airside=G.airside38
        if not airside['floor_enabled']():G.say('The jetbridge must be deployed and docked first');return False
        G.S['boarding']=True;ticket()['gate_scanned']=True
        for n in G.S['doors']:
            if n.startswith('A07 boarding'):G.open_door(n,1)
        G.screen(G.S['actors'].get(name),'Boarding');G.cue('GateOpen',q['point'])
        G.say('SA107 boarding / follow the enclosed jetbridge to L1');emit('A07 pass validated38');return True
    if kind=='information':
        G.say('A08 north lounge / SA107 boards at A07: turn south, then left into A07' if q.get('gate')=='A08' else objective())
        emit('Airport information38',actor=name,gate=q.get('gate'));return True
    if kind=='npc' and name in G.D['repair38']['journey']['queue']['npc_order']:
        G.say(q.get('dialogue','We are waiting for a free check-in desk.'));return True
    if kind=='vending':return _coffee(q)
    if kind=='pickup' and name in S['registered_bags']:
        G.say('This suitcase is safely checked in the baggage receiving bay');return False
    if kind=='pickup' and name==S['coffee']['actor'] and not S['coffee']['served']:
        G.say('Order your coffee at the espresso machine');return False
    return S['base_act'](q)


def use(stand_on_miss=True):
    held=G.S.get('held');q=G.nearest()
    if held and held==S['coffee']['actor'] and G.P.STATE['pc'].was_input_key_just_pressed(G.KEY['LeftMouseButton']):
        if S['coffee']['sips']>0:
            S['coffee']['sips']-=1;G.say('Coffee / '+str(S['coffee']['sips'])+' sips left' if S['coffee']['sips'] else 'Coffee finished / return the cup to Cloud Nine')
            emit('Coffee used38',sips_left=S['coffee']['sips'])
        else:G.say('The cup is empty / return it at Cloud Nine')
        return True
    if held and q and q['kind'] in FLOW|{'bridgecontrol38'}:act(q);return True
    if held and not G.P.STATE['pc'].was_input_key_just_pressed(G.KEY['LeftMouseButton']):
        if q and q['kind']=='seat':G.act(q);return True
        item=G.P.nearest()
        if item and item['kind'] in {'seat','door','movable','control','screen','inspect'}:
            return G.S['original_use'](stand_on_miss=False)
    if not held and not q:
        item=G.P.nearest()
        if item and item.get('actor')==G.D['aircraft_door'] and not G.airside38['floor_enabled']():
            G.say('Dock the jetbridge before opening L1');return True
    return S['base_use'](stand_on_miss)


def supported_on_belt(c,belt):
    u=G.u;com=c.get_center_of_mass()
    # Query the same bounded simple bed used by dynamic bag contacts. Complex
    # visual rays hit the individual roller flanks and are reserved for aiming.
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],com,com-u.Vector(0,0,170),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,
        [c.get_owner(),G.P.STATE['pawn']],u.DrawDebugTrace.NONE,True)
    if not hit:return False
    h=hit.to_tuple();comp=h[10] if len(h)>10 else None
    supported=bool(h[0] and comp and isinstance(comp,u.StaticMeshComponent) and comp.static_mesh
                   and comp.static_mesh.get_name() in S['support_assets'])
    owner=c.get_owner().get_actor_label()
    if _bag(owner):
        S.setdefault('support_debug',{})[owner]=dict(supported=supported,belt=belt.get('name'),
            actor=h[9].get_actor_label() if h[9] else None,mesh=comp.static_mesh.get_name() if comp and isinstance(comp,u.StaticMeshComponent) and comp.static_mesh else None,
            impact=list(G.source(h[5])) if h[0] else None,normal=list(h[7].to_tuple()) if h[0] else None,query='simple dynamic contact')
    return supported


def _conveyors(dt):
    u=G.u
    for n,a in G.S['physics'].items():
        if n==G.S.get('held') or n in S['registered_bags'] or 'Tug' in n or 'dolly' in n:continue
        c=a.static_mesh_component;p=G.source(c.get_center_of_mass())
        for belt in G.D['conveyors']:
            if belt['stage']>G.STAGE or not belt['height']+.015<p[2]<belt['height']+1.3:continue
            feed=belt.get('feed',belt['name'])
            if not S['powered'].get(feed,True):
                if belt.get('rect') and L.in_rect(p,belt['rect']) and supported_on_belt(c,belt):
                    vel=c.get_physics_linear_velocity();c.add_force(G.u.Vector(-vel.x*18,-vel.y*18,0)*c.get_mass(),G.NONE,False)
                continue
            if belt['kind']=='security' and (not G.S.get('screening_armed') or (0 if belt['name'].endswith('01') else 1) not in S['armed_lanes']):continue
            if belt['kind']=='bagdrop' and (not _bag(n) or not G.S.get('bag_drop_armed') or not G.S.get('checked_in')):continue
            if belt['kind']=='transfer38' and not _bag(n):continue
            if belt['kind']=='carousel':
                contact=L.carousel_tangent(p,S['carousel_paths'][belt['name']])
                if not contact:continue
                sx,sy=contact['tangent'];tx,ty=contact['point']
                restore=G.v(((tx-p[0])*2,(ty-p[1])*2,0));speed=belt['speed']
            else:
                if not L.in_rect(p,belt['rect']):continue
                sx,sy=belt['direction'];speed=belt['speed'];restore=u.Vector()
                if not supported_on_belt(c,belt):continue
                if belt['kind']=='bagdrop':
                    r=next(r for r in G.D['repair38']['journey']['bag_receivers'] if r['feed']==belt['name'])
                    if S['receiver_occupants'].get(r['name']):continue
                    state=S['bag_states'].setdefault(n,dict(feed=belt['name'],receiver=r['name']))
                    if p[0]<-26.30:state['seen_input']=True
                    state['state']='loaded'
                if belt['kind']=='transfer38':
                    r=next(r for r in G.D['repair38']['journey']['bag_receivers'] if r['transfer']==belt['name'])
                    state=S['bag_states'].get(n,{})
                    if state.get('feed')!=feed or not state.get('seen_input'):continue
                    # A broad receiving section gently brakes to a standstill.
                    speed=max(0.,min(speed,(r['stop_x']-p[0])*.9))
                    S['bag_states'].setdefault(n,dict(feed=feed,receiver=r['name']))['state']='receiving' if p[0]>=r['receive_x'] else 'transferring'
                if belt['kind']=='security' and _bag(n):
                    lane=0 if belt['name'].endswith('01') else 1
                    process=S['scan_transit'].setdefault(n,dict(lane=lane,entered=False,middle=False,elapsed=0.,previous=list(p)))
                    if process['lane']!=lane:process.update(lane=lane,entered=False,middle=False,elapsed=0.,previous=list(p))
                    if math.dist(p,process['previous'])>.60:process.update(entered=False,middle=False,elapsed=0.)
                    if p[1]<2.10:process['entered']=True
                    if process['entered']:
                        process['elapsed']+=dt
                        if 2.20<p[1]<4.10:process['middle']=True
                    process['previous']=list(p)
                    if process['entered'] and process['middle'] and process['elapsed']>.75 and p[1]>4.25 and n not in S['scanned_bags']:
                        S['scanned_bags'].add(n);G.screen(G.S['actors'][belt['name']],'Scanned')
                        G.say('Cabin bag screened / collect it from the receiving rollers');emit('Cabin bag physically screened38',actor=n,lane=lane)
                    # Screened output rollers are a stationary collection bed.
                    if p[1]>4.65:speed=max(0,min(speed,(5.05-p[1])*.9))
            if not supported_on_belt(c,belt):continue
            want=u.Vector(sx*speed*100,-sy*speed*100,0);vel=c.get_physics_linear_velocity()
            acc=(want-u.Vector(vel.x,vel.y,0))*9+restore
            # Resting rolling resistance compensation diminishes at the end.
            if speed>.04:acc+=u.Vector(sx*55,-sy*55,0)
            length=acc.length();c.add_force(acc*(min(length,1100)/max(length,1))*c.get_mass(),G.NONE,False)
            if _bag(n):S.setdefault('motor_debug',{})[n]=dict(belt=belt['name'],position=list(p),
                desired_velocity_cm_s=list(want.to_tuple()),actual_velocity_cm_s=list(vel.to_tuple()),
                acceleration_cm_s2=list((acc*(min(length,1100)/max(length,1))).to_tuple()),mass_kg=c.get_mass())
            break


def _baggage():
    for n,a in G.S['physics'].items():
        if not _bag(n) or n in S['registered_bags'] or n==G.S.get('held'):continue
        c=a.static_mesh_component;p=G.source(c.get_center_of_mass())
        for r in G.D['repair38']['journey']['bag_receivers']:
            if S['receiver_occupants'].get(r['name']):continue
            state=S['bag_states'].get(n,{})
            if state.get('receiver')!=r['name']:continue
            if L.receiver_complete(p,r,supported_on_belt(c,dict(name=r['transfer'])),c.get_physics_linear_velocity().length()):
                stable=state.get('stable_time',0)+S['dt'];state['stable_time']=stable
                if stable<.65:continue
                S['registered_bags'].add(n);S['receiver_occupants'][r['name']]=n;state['state']='safely_received'
                ticket()['checked_bags'].append(n);G.S['bag_accepted']=True;S['powered'][r['feed']]=False
                # The body reached the bed through native forces; put the
                # settled body to sleep rather than assigning a new transform.
                c.set_linear_damping(4.);c.set_angular_damping(6.);c.put_rigid_body_to_sleep(G.NONE)
                G.say('Suitcase safely received / SA107 checked bag confirmed');emit('Checked bag safely received38',actor=n,receiver=r['name'],position=list(p))
            else:state['stable_time']=0


def _deposit():
    d=S.get('deposit')
    if not d:return
    name=d['actor'];c=G.S['actors'][name].static_mesh_component;goal=G.S.get('deposit_goal')
    if G.S.get('held')!=name or not goal or time.monotonic()-d['began']>7 or (G.P.STATE['pawn'].get_actor_location()-goal).length()>340:
        G.S.pop('deposit_goal',None);S.pop('deposit',None);return
    if (c.get_center_of_mass()-goal).length()<14 and c.get_physics_linear_velocity().length()<120:
        G.release(False);G.S.pop('deposit_goal',None);S.pop('deposit',None);emit('Bag physically released onto belt38',actor=name,belt=d['belt'])


def _curtains(dt):
    u=G.u
    bags=[]
    for n,a in G.S['physics'].items():
        # Curtains are visual flexible leaves, and react to the actual nearby
        # bag even while it is being positioned. Scanning still excludes held
        # bodies and requires supported complete native transit.
        if _bag(n) or G.S['actor_specs'].get(n,{}).get('asset')=='SM_AP_Tray':bags.append(G.source(a.static_mesh_component.get_center_of_mass()))
    for spec in G.D['repair38']['equipment']['curtains']:
        a=G.S['actors'].get(spec['actor'])
        if not a:continue
        want=1. if any(L.in_rect(p,spec['trigger_rect']) and spec['height_range'][0]<p[2]<spec['height_range'][1] for p in bags) else 0.
        f=S['curtain_fraction'].get(spec['actor'],0.);f+=max(-dt*3,min(dt*3,want-f));S['curtain_fraction'][spec['actor']]=f
        a.set_actor_rotation(u.Rotator(roll=spec['open_angle_degrees']*f),False)


def _doors_before_motion():
    p=G.P.STATE['pawn'].get_actor_location()
    for name,q in S['door_specs'].items():
        d=G.S['doors'][name]
        if q.get('automatic'):
            d['target']=L.auto_target(q,G.S,(p-d['closed']).length(),S['wc_locks'].get(name,False))
        elif not L.door_access(q,G.S,S['wc_locks'].get(name,False)) and name not in S['wc_locks']:d['target']=0


def _screen_and_board(dt):
    pawn=G.P.STATE['pawn'];p=G.source(pawn.get_actor_location());prev=S['previous']
    walking=not(G.S.get('spectator') or G.S.get('driving') or G.P.STATE.get('seated'))
    max_step=max(1.,min(dt,.8)*pawn.get_component_by_class(G.u.FloatingPawnMovement).get_editor_property('max_speed')/100+.25)
    if walking and G.S.get('checked_in') and not G.S.get('security'):
        for i,rect in enumerate(G.D['security_crossings']):
            armed,finished=L.traversal(prev,p,rect,S['lane_armed'].get(i,False),max_step);S['lane_armed'][i]=armed
            if finished:
                held=G.S.get('held')
                # Any unscanned cabin baggage, including a released bag waiting
                # on the input, must complete its physical scanner transit.
                pending=any(n not in S['scanned_bags'] and n not in S['registered_bags'] for n in S['passenger_bags'])
                if not L.legal_screening(held,S['scanned_bags'],S['registered_bags']) or pending:
                    G.say('Your cabin bag still needs screening / load it on the scanner belt');emit('Security denied unscanned baggage38',held=held);continue
                G.S['security']=True;ticket()['security_cleared']=True;G.cue('ScannerReady',p)
                G.say('Security cleared / turn right for Gate A07');emit('Security cleared by full traversal38',lane=i)
    else:S['lane_armed']={}
    crossing=G.D['aircraft38']['crossing']
    threshold=crossing.get('threshold',crossing.get('threshold_x',14.1))
    if walking and G.S.get('boarding') and G.S.get('security') and not G.S.get('aboard'):
        r=crossing.get('inside',crossing.get('inside_rect',[14.1,18.4,-.3,2.0]))
        if prev[0]<=threshold<p[0] and L.in_rect(p,r) and 1.25<p[2]<2.1 and math.dist(prev[:2],p[:2])<1:
            G.S['aboard']=True;ticket()['aboard']=True;G.say('Welcome aboard / Economy03E via right aisle')
            emit('Aircraft boarded at actual L1 threshold38',position=list(p))
    S['previous']=p


def _animate(name,clip):
    if S['queue']['clips'].get(name)==clip:return
    import characters12_runtime as CH
    a=G.S['actors'].get(name);anim=CH.CLIPS.get(clip)
    if a and anim:a.skeletal_mesh_component.play_animation(anim,True);S['queue']['clips'][name]=clip


def _move_character(name,goal,dt):
    import characters12_runtime as CH
    if name in CH.S.get('greetings',{}):
        S['queue']['clips'].pop(name,None);return False
    u=G.u;a=G.S['actors'].get(name)
    if not a:return True
    d=G.v(goal)-a.get_actor_location();d.z=0
    if d.length()<8:_animate(name,'Idle');return True
    for other in [G.P.STATE['pawn']]+[G.S['actors'].get(n) for n in S['queue']['waiting'] if n!=name]:
        if not other:continue
        delta=other.get_actor_location()-a.get_actor_location();delta.z=0
        if delta.length()<73 and delta.x*d.x+delta.y*d.y>0:_animate(name,'Idle');return False
    a.set_actor_location(a.get_actor_location()+d/max(d.length(),.01)*min(d.length(),115*dt),False,True)
    a.set_actor_rotation(u.Rotator(yaw=math.degrees(math.atan2(d.y,d.x))-90),False);_animate(name,'Walk')
    spec=next((q for q in G.D.get('character_placements',[]) if q['actor']==name),None)
    proxy=G.S['actors'].get('CH12COLL '+spec['name']) if spec else None
    if proxy:proxy.set_actor_location(a.get_actor_location()+u.Vector(0,0,90),False,True)
    return False


def _queue(dt):
    queue=S['queue'];cfg=G.D['repair38']['journey']['queue'];now=time.monotonic()
    if not queue['joined'] or G.S.get('checked_in'):return
    active=queue.get('active')
    if active:
        route=active['route'];index=active['index']
        if index<len(route):
            p=route[index]
            if isinstance(p,(float,int)):
                active.setdefault('until',now+p)
                if now>=active['until']:active.pop('until');active['index']+=1
            elif _move_character(active['actor'],p,dt):active['index']+=1
        else:
            emit('Counter genuinely vacated38',desk=active['desk'],actor=active['actor'])
            queue['busy'].pop(active['desk'],None);queue['active']=None
    elif queue['waiting']:
        n=queue['waiting'].pop(0);desk=cfg['desks'][queue['served']%len(cfg['desks'])];queue['served']+=1
        p=cfg['service_points'][desk]
        # Served parties wait in the spacious check-in side bay. The old end
        # points parked them IN the only narrow route to security; once their
        # collision correctly followed them they physically blocked the player.
        wait_x=-34.4-(queue['served']-1)*1.3
        end=[wait_x,-9.2,0]
        route=[[-32.05,-13,0],[-32.05,p[1],0],p,cfg['service_s'],[-32.05,p[1],0],
               [-32.05,-9.2,0],end]
        queue['active']=dict(actor=n,desk=desk,index=0,route=route);queue['busy'][desk]=n
        emit('Counter assigned to queue passenger38',desk=desk,actor=n)
    elif not queue.get('called'):
        desk='Check-in desk 01';point=cfg['service_points'][desk];occupied=False
        for n in cfg['npc_order']:
            a=G.S['actors'].get(n)
            if a:
                p=G.source(a.get_actor_location());occupied|=math.dist(p[:2],point[:2])<1.15
        if not occupied and not queue['busy']:
            queue['called']=desk;G.say('Desk01 is free / follow the open counter approach');emit('Player called to free desk38',desk=desk)
    for i,n in enumerate(queue['waiting']):_move_character(n,[-34.2-i*1.5,-13,0],dt)


def _floors():
    # The global cabin fallback is replaced by two real bounded deck footprints.
    dx=G.D['aircraft38']['offset'][0]
    floors=[q for q in G.P.DATA['layout']['navigation_floors'] if q.get('name') not in {'Compact terminal','Service ramp','Level boarding bridge','Apron'} and not q.get('name','').startswith('Bridge38 ')]
    extra=[dict(name='Bounded cabin deck38',rect=[dx-2.398,dx+2.398,0,35.1],height=0,priority=0,max_step=.30),
           dict(name='Bounded cockpit deck38',rect=[dx-1.99,dx+1.99,-5.40,0],height=0,priority=0,max_step=.30)]
    if G.airside38['floor_enabled']():
        for i,z in enumerate(G.D['aircraft38']['bridge']['floor_polygons']):
            extra.append(dict(name='Deployed bridge38 '+str(i),polygon=z['polygon'],height=z.get('height',z.get('z',0)),priority=16,max_step=.32))
    return floors,extra


def floor_at_source(x,y,feet_z=0.):
    floors,extra=_floors()
    return L.choose_floor(x,y,feet_z,floors,G.P.STATE.get('movables',{}),extra)


def update_floor(dt):
    if G.S.get('spectator') or G.S.get('driving') or G.P.STATE.get('seated') or G.P.STATE.get('inspecting'):return
    u=G.u;P=G.P;pawn=P.STATE.get('pawn')
    if not pawn:return
    p=pawn.get_actor_location();x,y,z=G.source(p);feet=z-P.EYE_HEIGHT
    floor,name=floor_at_source(x,y,feet)
    if floor is None:
        # Physical terrain/steps may support outside our authored room floors.
        # There is no Current deck fallback in empty air.
        start=G.v([x,y,feet+.25]);end=G.v([x,y,feet-.42])
        h=u.SystemLibrary.line_trace_single(P.STATE['world'],start,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True)
        h=h.to_tuple() if h else None
        if h and h[0]:floor=G.source(h[5])[2];name='Physical supporting surface38'
    move=pawn.get_component_by_class(u.FloatingPawnMovement)
    if floor is None:
        S['fall_velocity']=max(-16.,S.get('fall_velocity',0.)-9.8*min(dt,.08))
        desired=p.z+S['fall_velocity']*min(dt,.08)*100
        name='Falling to physical ground38'
    else:S['fall_velocity']=0.;desired=(floor+P.EYE_HEIGHT)*100
    if abs(desired-p.z)>.015:pawn.set_actor_location(u.Vector(p.x,p.y,desired),True,False)
    actual=pawn.get_actor_location();move.set_plane_constraint_origin(u.Vector(0,0,actual.z));move.set_plane_constraint_enabled(True)
    P.STATE.update(floor_z=actual.z/100-P.EYE_HEIGHT,floor_name=name)


def _seated_hold_goal():
    # Pass46 / P46-011: seated in an aircraft seat, the core carry goal is
    # 1.25 m ahead of the camera - inside the instrument panel on the flight
    # deck. The bag pressed into it, lost to the capped spring under taxi and
    # takeoff acceleration, and wedged at the side console; on standing it
    # stayed there, so the in-flight carry check found it 3 m away, or the
    # departure sweep saw it poking out of the cockpit cell. While seated, hold
    # it where the passenger stood just before sitting down instead: a spot
    # they had just occupied with this same bag, and where stand() puts them
    # back. Aircraft seats only; nothing changes anywhere else.
    seated=G.P.STATE.get('seated')
    if not seated or not G.S.get('held') or not seated.get('return_frame39'):return None
    frame=getattr(G,'flight39',{}).get('frame') if isinstance(getattr(G,'flight39',None),dict) else None
    if frame is None or seated.get('return') is None:return None
    return frame.world(seated['return'])+G.u.Vector(0,0,-14)


def _cabin_carry_goal():
    # Pass47: walking aboard, the core carry goal (1.25 m ahead, chest high)
    # swings the bag into seat backs, suites and bins on every turn of a 0.5 m
    # aisle; the capped spring cannot pull it free, and the passenger walks on
    # "holding" a bag left behind (seen at the business suites, y 9.3). Aboard
    # and on foot, hold it the way people carry a cabin bag in an aisle: 0.7 m
    # ahead, level, at hip height. Same spring, a closer target; no teleport.
    if G.P.STATE.get('seated') or not G.S.get('held'):return None
    fl=getattr(G,'flight39',None);frame=fl.get('frame') if isinstance(fl,dict) else None
    if frame is None or not frame.aboard():return None
    f=G.u.MathLibrary.get_forward_vector(G.P.STATE['pc'].get_control_rotation());f.z=0.
    n=f.length()
    if n<1e-3:return None
    return G.P.STATE['pawn'].get_actor_location()+f*(70./n)+G.u.Vector(0,0,-40)


def _coffee_tick(dt):
    cup=S['coffee']['actor']
    seated_goal=_seated_hold_goal()
    if seated_goal is None:seated_goal=_cabin_carry_goal()
    if G.S.get('held')==cup and not S.get('returning_cup'):
        pc=G.P.STATE['pc'];f=G.u.MathLibrary.get_forward_vector(pc.get_control_rotation());r=G.u.MathLibrary.get_right_vector(pc.get_control_rotation())
        G.S['deposit_goal']=G.P.STATE['pawn'].get_actor_location()+f*65+r*24+G.u.Vector(0,0,-20)
    elif seated_goal is not None and not S.get('deposit') and not S.get('returning_cup'):G.S['deposit_goal']=seated_goal
    elif not S.get('deposit') and not S.get('returning_cup'):G.S.pop('deposit_goal',None)
    if S.get('returning_cup'):
        c=G.S['actors'][cup].static_mesh_component;goal=G.S.get('deposit_goal')
        if G.S.get('held')!=cup or time.monotonic()-S['returning_cup']>7:
            S.pop('returning_cup',None);G.S.pop('deposit_goal',None)
        elif goal and (c.get_center_of_mass()-goal).length()<7 and c.get_physics_linear_velocity().length()<50:
            G.release(False);G.S.pop('deposit_goal',None);S.pop('returning_cup',None)
            S['coffee']['sips']=3;G.say('Cup returned / coffee refilled');emit('Coffee returned and refilled38')


def _ui():
    now=time.monotonic()
    if G.P.STATE['pc'].was_input_key_just_pressed(S['pass_key']):S['pass_visible']=not S.get('pass_visible')
    # Reuse the existing approved screen-resolution HUD artwork, with actual
    # queue occupancy and an actually free Desk01 call.
    if not G.S.get('checked_in'):
        import airport_clarity26 as C
        queue=S['queue'];ahead=len(queue['waiting'])+int(bool(queue.get('active')))
        key='Called' if queue.get('called') else 'Queue'+str(max(1,min(3,ahead))) if queue['joined'] else 'JoinQueue'
        if key!=S.get('queue_hud') and C.S.get('mid'):
            texture=G.u.load_asset('/Game/Airport30/Textures/T30_HUD_'+key)
            if texture:C.S['mid'].set_texture_parameter_value('Journey',texture);S['queue_hud']=key
    if G.CAPTURE or G.QA:return
    q=G.nearest();msg=G.S.get('message','') if now<G.S.get('message_until',0) else ''
    prompt=('E / '+q.get('title',q['kind'])) if q else ''
    if G.S.get('held')==S['coffee']['actor']:prompt='Left mouse / sip coffee     E / put down     face machine + E / return'
    if msg:prompt=msg
    G.u.SystemLibrary.print_string(G.P.STATE['world'],prompt,True,False,G.u.LinearColor(.96,.88,.69,1),.12,G.u.Name('Airport38Action'))
    if S.get('pass_visible'):
        t=S.get('ticket');text='Collect your boarding pass at check-in' if not t else 'SKYWARD AIR / SA107 / AZURE BAY / A07 / ECONOMY03E\nChecked bags '+str(len(t['checked_bags']))+' / Security '+('cleared' if t['security_cleared'] else 'pending')+' / B close'
        G.u.SystemLibrary.print_string(G.P.STATE['world'],text,True,False,G.u.LinearColor(.8,.9,1,1),.12,G.u.Name('Airport38Pass'))


def write():
    d=dict(status='READY',revision=38,ticket=S.get('ticket'),journey={k:G.S.get(k) for k in ['checked_in','bag_accepted','security','boarding','aboard']},
           player=list(G.source(G.P.STATE['pawn'].get_actor_location())),registered_bags=sorted(S['registered_bags']),scanned_bags=sorted(S['scanned_bags']),
           bag_states=S['bag_states'],conveyor_power=S['powered'],privacy_locks=S['wc_locks'],queue={k:v for k,v in S['queue'].items() if k!='clips'},
           coffee=S['coffee'],events=S['events'],objective=objective(),conveyor_support=S.get('support_debug',{}),
           conveyor_motors=S.get('motor_debug',{}),runtime_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (G.R/'ArtBible/JourneySession38.json').write_text(json.dumps(d,indent=2))


def physics(dt):
    S['dt']=dt;_doors_before_motion();_coffee_tick(dt)
    conveyors=G.D['conveyors'];G.D['conveyors']=[]
    try:S['base_physics'](dt)
    finally:G.D['conveyors']=conveyors
    _deposit();_conveyors(dt);_baggage();_curtains(dt);_screen_and_board(dt);_queue(dt);_ui()
    if time.monotonic()-S.get('written',0)>.5:S['written']=time.monotonic();write()


def install(game):
    global G;G=game
    if S.get('installed'):return
    u=G.u;cfg=G.D['repair38']['journey'];now=time.monotonic()
    S.update(installed=True,started=now,events=[],ticket=None,registered_bags=set(),scanned_bags=set(),
        bag_states={},receiver_occupants={},scan_transit={},passenger_bags=set(),armed_lanes=set(),lane_armed={},curtain_fraction={},
        powered={q['name']:True for q in G.D['conveyors']},wc_locks={n:False for n in G.S['doors'] if n.startswith('Terminal WC ')},
        queue=dict(joined=False,waiting=cfg['queue']['npc_order'][:],active=None,busy={},called=None,served=0,clips={}),
        coffee=dict(actor=cfg['serving_cup'],served=False,sips=0),support_assets=set(cfg['support_asset_ids'])|{'SM_AP_Carousel34'},
        carousel_paths={q['name']:L.carousel_geometry(G.S['actor_specs'][q['name']]) for q in G.D['conveyors'] if q['kind']=='carousel'},
        base_act=G.act,base_use=G.use_nearest,base_nearest=G.nearest,base_physics=G.physics,
        base_sit=G.P.sit,base_stand=G.P.stand,pass_key=G.key('B'),door_specs={})
    # Save each automatic/access policy once. Core proximity assignment is
    # disabled, and policy is evaluated BEFORE the core interpolates any leaf.
    for q in G.S['targets']:
        if q['kind'] in ('slide','boardingdoor') and q['actor'] in G.S['doors']:
            S['door_specs'].setdefault(q['actor'],dict(q));G.S['doors'][q['actor']]['automatic']=False
    G.act=act;G.nearest=nearest;G.visible=visible;G.use_nearest=use;G.P.use_nearest=use;G.physics=physics;G.supported_on_belt=supported_on_belt
    import characters12_runtime as CH
    for name in cfg['queue']['npc_order']:
        CH.S.get('walkers',{}).pop(name,None)
        CH.S.get('greetings',{}).pop(name,None)
    G.P.floor_at_source=floor_at_source;G.P.update_floor=update_floor
    G.S['original_floor']=update_floor
    # Remember passenger-carried baggage: dropping an unscanned bag outside the
    # detector cannot make the security requirement disappear.
    base_act=S['base_act']
    def tracked_base(q):
        if q['kind']=='pickup' and _bag(q['actor']):S['passenger_bags'].add(q['actor'])
        return base_act(q)
    S['base_act']=tracked_base
    aircraft_seats={q['actor'] for q in G.P.STATE['items'] if q['kind']=='seat'}
    def sit(q):
        if q.get('actor') in aircraft_seats and not G.S.get('aboard'):G.say('Board through Gate A07 first');return False
        out=S['base_sit'](q)
        if q.get('actor') in aircraft_seats and G.P.STATE.get('seated'):emit('Aircraft seat occupied38',actor=q['actor'])
        return out
    G.P.sit=sit
    cup=G.S['actors'][cfg['serving_cup']];cup.set_actor_hidden_in_game(True);cup.set_actor_enable_collision(False)
    cup.static_mesh_component.set_simulate_physics(False)
    for n in S['wc_locks']:_indicator(n,False)
    # Preserve rendered guidance, but its text now follows the authoritative38
    # state rather than importing/initing the obsolete journey controller.
    import airport_journey22 as oldJ
    oldJ.objective=objective
    if '-AirportStartAboard' not in G.CMD:
        p=G.v(G.D['start']);G.P.STATE['pawn'].set_actor_location(p,False,True)
        target=G.v(G.D.get('look_at',[-46,-12.5,1.62]))
        G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(p,target))
    S['previous']=G.source(G.P.STATE['pawn'].get_actor_location())
    # HUD26's stale boarding hint for A08 is gone because its actual target kind
    # is information. Unknown custom controls use the live action line above.
    G.journey38=dict(state=S,ticket=ticket,objective=objective,write=write,
                     supported_on_belt=supported_on_belt,floor_at_source=floor_at_source,
                     receiver_complete=L.receiver_complete,usable=usable)
    emit('Authoritative journey38 installed',automatic_doors=len(S['door_specs']),receiver_bays=len(cfg['bag_receivers']))
    write();return G.journey38
