"""Civil flight procedure using the actual authored cockpit fittings.

Install after Journey38 and Airside38. prepare_plane runs before configure.
No tower/crash mode is modified. All motion comes from flight39_model.step.
"""
import math,json,time
from pathlib import Path
import flight39_model as M
from flight39_frame import Frame

G=None;S={}
PILOT_SEATS=('SM_Plane_Seat.016','SM_Plane_Seat.017')
DOORS=('Aircraft door 1L','Aircraft door 1R','Aircraft door 2L','Aircraft door 2R','Lower cargo stair hatch')
MAP={
 'Cockpit AUX switch12':('battery','MASTER / battery'),
 'Cockpit NAV switch12':('avionics','NAV / avionics'),
 'Cockpit FUEL switch12':('fuel','Engine fuel valves'),
 'Cockpit PUMP switch12':('pumps','Fuel pumps'),
 'Cockpit AIR switch12':('bleed','Start air / bleed'),
 'Cockpit CABIN switch12':('cabin_lights','Cabin lighting'),
 'Cockpit overhead switch 0112':('engine1','Engine1 / OFF START RUN'),
 'Cockpit overhead switch 1012':('engine2','Engine2 / OFF START RUN'),
 'Cockpit overhead switch 0212':('beacon','Anti-collision beacon'),
 'Cockpit overhead switch 0312':('parking','Parking brake'),
 'Cockpit overhead switch 0412':('taxi_lights','Taxi lights'),
 'Cockpit overhead switch 0512':('landing_lights','Landing lights'),
 'Cockpit overhead switch 0612':('navigation_lights','Navigation lights'),
 'Cockpit overhead switch 0712':('seatbelt','Seatbelt signs'),
 'Cockpit overhead switch 0812':('gear','Landing gear'),
 'Cockpit overhead switch 0912':('radar','Weather radar'),
 'Cockpit overhead switch 1112':('map_lights','Captain map lights'),
 'Cockpit overhead switch 1212':('map_lights','First officer map lights'),
 'Cockpit overhead switch 1312':('instrument_lights','Instrument brightness'),
 'Cockpit overhead switch 1412':('cabin_lights','Cabin lighting'),
 'Cockpit overhead switch 1512':('hold_lights','Cargo hold lights'),
 'Cockpit overhead switch 1612':('lav_lights','Lavatory lights'),
 'Cockpit overhead switch 1712':('radio','Radio monitor'),
 'Cockpit overhead switch 1812':('standby','Standby display'),
 'Cockpit quadrant lever 112':('throttle1','Engine1 thrust'),
 'Cockpit quadrant lever 212':('throttle2','Engine2 thrust'),
 'Cockpit quadrant lever 312':('speedbrake','Speedbrake'),
 'Cockpit quadrant lever 412':('flaps','Flaps'),
 'Cockpit side pushbutton 0112':('map_lights','Captain map light'),
 'Cockpit side pushbutton 0412':('map_lights','First officer map light'),
 'Cockpit side pushbutton 0212':('cabin_lights','Cabin lighting'),
 'Cockpit side pushbutton 0512':('cabin_lights','Cabin lighting'),
 'Cockpit side pushbutton 0312':('clearance','Ground / tower radio'),
 'Cockpit side pushbutton 0612':('clearance','Ground / tower radio'),
 'Cockpit status pushlight 112':('close_doors','Crew / close aircraft doors'),
 'Cockpit emergency test 112':('stow_bridge','Ground crew / stow jetbridge'),
 'Cockpit emergency test 212':('abort','Reject takeoff / brake'),
 'Cockpit status pushlight 212':('acknowledge','Acknowledge caution'),
 'Cockpit side rotary 112':('radar','Radar brightness'),
 'Cockpit side rotary 212':('map_lights','Captain practical brightness'),
 'Cockpit side rotary 312':('instrument_lights','Instrument brightness'),
 'Cockpit side rotary 412':('radio','Radio monitor volume'),
 'Cockpit side rotary 512':('map_lights','First officer practical brightness'),
 'Cockpit side rotary 612':('standby','Standby display brightness'),
}
EXTRAS={'cabin_lights','taxi_lights','landing_lights','navigation_lights','seatbelt','radar','map_lights','instrument_lights','hold_lights','lav_lights','radio','standby'}


def prepare_plane(P,D):
    for q in P.DATA['interactions']:
        if q['actor'] not in MAP:continue
        name,title=MAP[q['actor']];q['title']=title
        if name.startswith('throttle'):q['states']=['Idle','Taxi','Takeoff'];q['initial_state']=0
        elif name.startswith('engine'):q['states']=['Off','Start','Run'];q['initial_state']=0
        elif name=='parking':q['states']=['Set','Set / auto','Released'];q['initial_state']=0
        elif name=='flaps':q['states']=['Up','Takeoff5','Landing15'];q['initial_state']=0
        elif name in {'battery','avionics','fuel','pumps','bleed','beacon'}:q['initial_state']=0
        if name.startswith('throttle'):
            for t in q.get('targets',[]):
                if 'rotation_states' in t:t['rotation_states']=[0.,13.75,55.]
    P.DATA['layout']['flight39']=D['flight39']
    return P


def pilot():return bool(G.P.STATE.get('seated') and G.P.STATE['seated'].get('actor') in PILOT_SEATS)


def context():
    import airport_airside38 as A
    mov=G.P.STATE['movables']
    closed=all(n in mov and mov[n]['progress']<.015 and mov[n]['target']<.015 for n in DOORS)
    return dict(aboard=bool(G.S.get('aboard')),pilot=pilot(),doors_closed=closed,
                bridge_stowed=A.S.get('fraction',0)>.999 and not(A.S.get('moving') or A.S.get('pending_stow')))


def _say(text,okay=True):
    S['state']['last_reason']=text
    G.say(text)
    sound=S.get('click' if okay else 'caution')
    if sound:_play(sound,.25,1.)


def _play(sound,volume=.25,pitch=1.):
    fn=S.get('play_sound')
    if not fn or not sound or S.get('audio_disabled'):return
    try:fn(G.P.STATE['world'],sound,volume,pitch,0.,None,None,False)
    except Exception as exc:
        S['audio_status']='Optional audio unavailable: '+str(exc);S['audio_disabled']=True
        G.u.log_warning(S['audio_status'])


def _effects(name,value):
    s=S['state'];u=G.u
    patterns={'cabin_lights':('Cabin broad','Reading','Business','Passenger'),
              'map_lights':('Cockpit ceiling practical','Cockpit rear entry practical'),
              'hold_lights':('Cargo','Hold','Lower hold'), 'lav_lights':('Lavatory','Lav ')}
    if name in patterns:
        factor=0. if not value else .55 if value==1 else 1.
        for n,a,intensity in S['light_records']:
            if any(p.lower() in n.lower() for p in patterns[name]):a.light_component.set_intensity(intensity*factor)
    if name in ('radar','standby','instrument_lights'):
        a=G.P.STATE['actors'].get('Cockpit radar phosphor graphics12')
        if a and name=='radar':a.set_actor_hidden_in_game(not value or not M.power(s))
        if name=='standby' and S.get('status'):S['status'].set_actor_hidden_in_game(not value)
        if name=='instrument_lights' and S.get('status'):
            f=0. if not value else .5 if value==1 else 1.
            S['status'].get_component_by_class(u.TextRenderComponent).set_text_render_color(u.Color(int(169*f),int(222*f),int(205*f),255))
    if name=='seatbelt' and S.get('caution'):
        _play(S['caution'],.15,1.4)
    # Exterior practicals are cached native actors, not hundreds of new lights.
    for role in ('taxi_lights','landing_lights','navigation_lights'):
        if name==role:
            for a in S.get('exterior_lights',{}).get(role,[]):a.light_component.set_intensity(S['exterior_base'][a]*float(bool(value)))
    s.setdefault('systems',{})[name]=value


def command(name,value=None,announce=True):
    s=S['state'];c=context();okay=True;reason=''
    if not c['pilot']:okay=False;reason='Walk into the flight deck and sit in a pilot seat'
    elif name=='close_doors':
        if s['speed']>.2 or s['airborne']:okay=False;reason='Aircraft doors stay secured while moving'
        else:
            for n in DOORS:G.P.STATE['movables'][n]['target']=0.
            reason='Crew closing all aircraft doors and the lower cargo hatch'
    elif name=='stow_bridge':
        if math.dist(s['position'][:2],M.STAND[:2])>2:okay=False;reason='The jetbridge only operates at the parking stand'
        else:okay,reason=G.airside38['request_bridge'](True)
    elif name=='abort':
        if s['airborne']:okay=False;reason='Reject takeoff is a ground action; reduce thrust using the quadrant'
        else:s['throttle']=[0.,0.];s['controls']['brake']=1.;s['speedbrake']=2;S['abort']=True;reason='Reject takeoff / idle thrust, full speedbrake and braking'
    elif name=='acknowledge':reason='Caution acknowledged';S['acknowledged']=True
    elif name in EXTRAS:
        if name not in ('cabin_lights','lav_lights') and value and not M.power(s):okay=False;reason='Master AUX / battery must be ON first'
        else:_effects(name,value);reason=MAP.get(S.get('operating_actor'),(name,name.replace('_',' ')))[1]+' '+('on' if value else 'off')
    else:
        if name=='parking' and not value and not S.get('departure_released'):
            okay,reason=G.airside38['can_depart']()
            if okay:S['departure_released']=True
        if okay:okay,reason=M.command(s,name,value,c)
    if announce:_say(reason,okay)
    if name=='clearance' and okay and S.get('radio_audio'):
        volume=float(s.get('systems',{}).get('radio',1))*.25
        _play(S['radio_audio'],volume,1.)
    return okay,reason


def _value(name,index):
    if name.startswith('throttle'):return [0.,.25,1.][index]
    if name.startswith('engine'):return index
    if name=='parking':return index!=2
    if name=='gear':return index!=2
    if name in ('flaps','speedbrake'):return index
    if name=='clearance':return 1
    if name in EXTRAS:return index
    return bool(index)


def set_control(actor,index):
    if actor not in MAP:return S['base_control'](actor,index)
    control=G.P.STATE['controls'][actor];index=int(index)%len(control['item']['states']);name=MAP[actor][0]
    # Auto-reset of a momentary modeled button is visual, never a second call.
    if control['item'].get('auto_reset_seconds') and index==0:return S['base_control'](actor,index)
    S['operating_actor']=actor;okay,reason=command(name,_value(name,index))
    if okay:return S['base_control'](actor,index)
    return control['state']


def operate(actor,index):
    """Autoplay and manual fittings share the exact same state/action entry."""
    if actor not in MAP:raise KeyError(actor)
    before=len(S['state']['denials']);result=set_control(actor,index)
    return dict(actor=actor,state=result,reason=S['state']['last_reason'],denials=len(S['state']['denials'])-before)


def _manual(dt):
    if not pilot() or G.S.get('spectator') or S.get('autoplay'):return
    pc=G.P.STATE['pc'];k=S['keys'];s=S['state']
    down=lambda n:float(pc.is_input_key_down(k[n]));pressed=lambda n:pc.was_input_key_just_pressed(k[n])
    s['controls'].update(pitch=down('W')-down('S'),roll=down('D')-down('A'),
        rudder=down('D')-down('A') if not s['airborne'] else down('Right')-down('Left'),brake=down('LeftControl'))
    if pressed('PageUp') or pressed('PageDown'):
        delta=1 if pressed('PageUp') else -1
        for i in (1,2):
            actor='Cockpit quadrant lever '+str(i)+'12';old=G.P.STATE['controls'][actor]['state'];set_control(actor,max(0,min(2,old+delta)))
    for key,actor in S['shortcuts'].items():
        if pressed(key):
            c=G.P.STATE['controls'][actor]
            index=(0 if c['state']==2 else 2) if key in ('P','G') else c['state']+1
            set_control(actor,index)
    if pressed('C'):set_control('Cockpit side pushbutton 0312',1)
    if pressed('Home'):set_control('Cockpit status pushlight 112',1)
    if pressed('End'):set_control('Cockpit emergency test 112',1)


def input_controls(**values):
    if not pilot():return False
    for name,value in values.items():
        if name not in S['state']['controls']:raise KeyError(name)
        M.command(S['state'],name,value,context())
    return True


def _axis_quat(axis,degrees):
    a=math.radians(degrees)*.5;f=math.sin(a);return G.u.Quat(x=-axis[0]*f,y=axis[1]*f,z=-axis[2]*f,w=math.cos(a))


def _actuators():
    s=S['state'];P=G.P;u=G.u
    for q,a,base in S['surfaces']:
        role=q['role'];side=q['side']
        angle=-side*[0,5,15][s['flaps']] if role=='flap' else -s['controls']['roll']*18 if role=='aileron' else side*s['controls']['pitch']*18 if role=='elevator' else s['controls']['rudder']*18
        a.set_actor_relative_rotation(P._quat_product(base,_axis_quat(q['axis'],angle)).rotator(),False,False)
    values=dict(airspeed=M.clamp(s['speed']*1.94384/340,0,1),altitude=M.clamp(s['position'][2]*3.28084/10000,0,1),
                fuel=.88,temperature=sum(e['n1'] for e in s['engines'])/2,
                vertical_speed=M.clamp(.5+s['vertical_speed']*196.85/6000,0,1),
                engine_rpm=sum(e['n1'] for e in s['engines'])/2,oil_pressure=.72 if all(e['running'] for e in s['engines']) else 0)
    for q,a,base in S['needles']:
        beta=-140+280*values[q['role']] if M.power(s) else -140
        a.set_actor_relative_rotation(P._quat_product(base,_axis_quat(q['axis'],beta-q['initial_angle'])).rotator(),False,False)
    desired=0. if s['gear_down'] else 1.;S['gear_fraction']+=max(-.025,min(.025,desired-S['gear_fraction']))
    f=S['gear_fraction'];smooth=f*f*(3-2*f)
    for q,a,base in S.get('gear',[]):
        # Doors stay fully open while the oleos swing; close over the final
        # third, instead of vanishing or rotating one combined gear object.
        fraction=max(0,min(1,(smooth-.65)/.35)) if 'door' in q['role'] else min(1,smooth/.78)
        a.set_actor_relative_rotation(P._quat_product(base,_axis_quat(q['axis'],q['retracted_angle']*fraction)).rotator(),False,False)
    text=S.get('status')
    if text:
        lines=['POWER OFF'] if not M.power(s) else ['IAS %03d KT'%(s['speed']*1.94384),'ALT %05d FT'%(s['position'][2]*3.28084),'N1 %02d / %02d'%tuple(e['n1']*100 for e in s['engines']),s['phase'].replace('_',' ').upper(),'BELTS '+('ON' if s.get('systems',{}).get('seatbelt') else 'OFF')]
        text.get_component_by_class(u.TextRenderComponent).set_text('\n'.join(lines))
    beacon=S.get('beacon')
    if beacon:beacon.light_component.set_intensity((850 if int(s['elapsed']*2)%2==0 else 0) if s['beacon'] and M.power(s) else 0)
    for i,n in enumerate(('Cockpit overhead switch 0112','Cockpit overhead switch 1012')):
        c=P.STATE['controls'][n]
        if s['engines'][i]['running'] and c['state']==1:S['base_control'](n,2)
    if S.get('engine_audio'):
        n1=sum(e['n1'] for e in s['engines'])/2;S['engine_audio'].set_volume_multiplier(.03+n1*.22 if n1>.01 else 0);S['engine_audio'].set_pitch_multiplier(.55+n1*.8)


def checklist():
    s=S['state'];c=context()
    if not c['doors_closed']:return 'HOME / crew close doors, then wait for the door lamps'
    if not c['bridge_stowed']:return 'END / ground crew stow the empty jetbridge'
    for k,title in [('battery','M / MASTER battery'),('avionics','N / NAV avionics'),('fuel','U / fuel valves'),('pumps','J / fuel pumps'),('bleed','K / start air'),('beacon','L / beacon')]:
        if not s[k]:return title+' ON'
    if not all(e['running'] for e in s['engines']):return '1 and2 / select START; wait for both engines to idle'
    if not s['taxi_clear']:return 'C / request taxi clearance'
    if s['parking']:return 'P / release parking brake'
    if not s['runway_clear']:return 'Taxi the yellow Alpha line; stop at ALPHA1 and press C'
    if not M.runway_position(s['position'],s['heading']) and not s['airborne']:return 'Follow the broad Alpha turn onto runway36; align with the white centreline'
    if s['flaps']!=1 and not s['airborne']:return 'F / takeoff flaps5; X / speedbrake retracted'
    if not s['airborne']:return 'PageUp / takeoff thrust; at140kt hold W to rotate'
    return 'W/S pitch / A/D bank / arrows yaw / G gear / F flaps / V view / Tab free camera'


def _tick(dt):
    dt=min(max(dt,.001),.05);s=S['state'];S['frame_times'].append(dt);S['frame_times']=S['frame_times'][-600:]
    if S.get('driver'):S['driver'].tick(dt)
    if S.get('driver') and S['driver'].done:S['autoplay']=False
    _manual(dt)
    if S.get('abort') and not s['airborne']:
        s['controls']['brake']=1.
        if s['speed']<.05:s['parking']=True;S['abort']=False
    M.step(s,dt,context())
    if S['frame'].pose(s['position'],s['heading'],s['pitch'],s['bank'],dt):s['root_writes']+=1
    S['accumulator']+=dt
    if S['accumulator']>=.1:S['accumulator']=0;_actuators()
    if pilot() and not G.S.get('spectator'):
        text='SA107 / '+s['phase'].replace('_',' ').upper()+' / %03d kt / %04d ft\n'%(s['speed']*1.94384,s['position'][2]*3.28084)+checklist()
        G.u.SystemLibrary.print_string(G.P.STATE['world'],text,True,False,G.u.LinearColor(.97,.87,.66,1),.1,G.u.Name('Flight39Procedure'))
    if time.monotonic()-S.get('written',0)>.5:write();S['written']=time.monotonic()


def write():
    d=M.snapshot(S['state']);d.update(ready=True,pilot=pilot(),context=context(),checklist=checklist(),root_writes=S['state']['root_writes'],
        attached_roots=len(S['frame'].attached_roots),dynamic_props=len(S['frame'].prop_records),surface_count=len(S['surfaces']),needle_count=len(S['needles']),
        events=S['state']['events'],denials=S['state']['denials'],model='local game flight approximation',carrier_frame='one native parent / frozen manifest reference',
        driver=S['driver'].snapshot() if S.get('driver') else None,audio_status=S.get('audio_status'),
        mobility_promoted=S['frame'].mobility_audit,native_warning_actor=S['frame'].native_warning_actor,
        actual_flightdeck_door=S['frame'].door_diagnostics())
    (G.R/'ArtBible/FlightSession39.json').write_text(json.dumps(d,indent=2),encoding='utf-8');return d


def install(game):
    global G;G=game;u=G.u;P=G.P
    if S.get('installed'):return G.flight39
    actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.Actor)}
    carrier=actors.get(G.D['flight39']['carrier'])
    if not carrier:raise RuntimeError('Flight39 native carrier was not built')
    frame=Frame(G,carrier)
    S.update(installed=True,state=M.fresh(),frame=frame,base_control=P.set_control_state,base_physics=G.physics,
             surfaces=[],needles=[],gear=[],gear_fraction=0.,accumulator=0,frame_times=[],light_records=[],exterior_lights={},exterior_base={},status=actors.get('Flight39 Status'),beacon=actors.get('Flight39 Beacon'))
    G.S['flight39']=S['state']
    for key,field in [('surface_records','surfaces'),('instrument_records','needles'),('gear_records','gear')]:
        for q in G.D['flight39'].get(key,[]):
            a=actors.get(q['actor'])
            if not a:raise RuntimeError('Flight39 authored actuator missing: '+q['actor'])
            S[field].append((q,a,None))
    frame.bind()
    for field in ('surfaces','needles','gear'):S[field]=[(q,a,a.root_component.get_editor_property('relative_rotation').quaternion()) for q,a,_ in S[field]]
    S['light_records']=[(n,a,float(a.light_component.get_editor_property('intensity'))) for n,a in P.STATE.get('lights',{}).items() if not isinstance(a,u.DirectionalLight)]
    for role,prefix in [('taxi_lights','Flight39 Taxi'),('landing_lights','Flight39 Landing'),('navigation_lights','Flight39 Nav')]:
        S['exterior_lights'][role]=[a for n,a in actors.items() if n.startswith(prefix)]
        for a in S['exterior_lights'][role]:S['exterior_base'][a]=float(a.light_component.get_editor_property('intensity'));a.light_component.set_intensity(0)
    S['keys']={n:G.key(n) for n in ['W','S','A','D','Left','Right','LeftControl','PageUp','PageDown','P','F','G','X','C','M','N','U','J','K','L','One','Two','Home','End']}
    S['shortcuts']={'M':'Cockpit AUX switch12','N':'Cockpit NAV switch12','U':'Cockpit FUEL switch12','J':'Cockpit PUMP switch12','K':'Cockpit AIR switch12','L':'Cockpit overhead switch 0212',
        'One':'Cockpit overhead switch 0112','Two':'Cockpit overhead switch 1012','P':'Cockpit overhead switch 0312','F':'Cockpit quadrant lever 412','G':'Cockpit overhead switch 0812','X':'Cockpit quadrant lever 312'}
    P.set_control_state=set_control
    base_use=G.use_nearest
    def use(stand_on_miss=True):
        item=P.nearest()
        if item and item.get('actor') in DOORS and (S['state']['speed']>.15 or S['state']['airborne']):
            G.say('External aircraft doors remain secured while moving');return 'flight_interlock'
        lock=item.get('lock_control') if item else None
        if lock and P.STATE['controls'][lock]['state']:
            inside=item.get('inside_rect');p=G.source(S['frame'].reference(P.STATE['pawn'].get_actor_location()))
            if inside and inside[0]<=p[0]<=inside[1] and inside[2]<=p[1]<=inside[3]:P.set_control_state(lock,0)
            else:G.say('Lavatory occupied / privacy lock');return 'locked'
        return base_use(stand_on_miss)
    G.use_nearest=use;P.use_nearest=use
    # The flight deck view and an attached exterior chase are the only V views.
    chase=actors.get('Flight39 Chase')
    S['chase']=chase
    if chase:P.STATE['review_cameras']=[chase];P.STATE['review_index']=-1
    base_request=G.airside38['request_bridge']
    def request(stow=True):
        if not stow and (S['state']['speed']>.05 or math.dist(S['state']['position'][:2],M.STAND[:2])>2):return False,'Return to the parking stand before deploying the bridge'
        return base_request(stow)
    G.airside38['request_bridge']=request
    def physics(dt):
        S['base_physics'](dt);_tick(dt)
    G.physics=physics
    G.flight39=dict(state=S['state'],runtime=S,command=command,operate=operate,inputs=input_controls,context=context,
                    checklist=checklist,write=write,frame=frame,pilot=pilot,control_map=MAP)
    # Original short loop recordings authored for this project, optional if a
    # root build deliberately excludes audio; no external downloads needed.
    for key,name in [('click','Click39'),('caution','Caution39'),('radio_audio','Radio39')]:S[key]=u.load_asset('/Game/Airport38/Flight39/Audio/'+name)
    wave=u.load_asset('/Game/Airport38/Flight39/Audio/Engine39')
    S['play_sound']=next((getattr(u.GameplayStatics,n) for n in ('play_sound2d','play_sound_2d') if hasattr(u.GameplayStatics,n)),None)
    spawn=next((getattr(u.GameplayStatics,n) for n in ('spawn_sound2d','spawn_sound_2d') if hasattr(u.GameplayStatics,n)),None)
    S['audio_disabled']='-nosound' in G.CMD.lower();S['audio_status']='Disabled for NoSound QA' if S['audio_disabled'] else 'Ready' if spawn and S['play_sound'] else 'Optional2D audio API unavailable'
    if wave and spawn and not S['audio_disabled']:
        try:
            S['engine_audio']=spawn(P.STATE['world'],wave,0.,1.,0.,None,False,False)
            if not S['engine_audio']:S['audio_status']='No audio device / optional engine loop skipped'
        except Exception as exc:S['audio_status']='Optional engine audio unavailable: '+str(exc);u.log_warning(S['audio_status'])
    _actuators();write();return G.flight39
