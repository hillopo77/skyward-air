"""Deterministic civil-airport flight game model, source metres and seconds.

This is a documented gameplay approximation, not a certified aerodynamic model.
It integrates the real stand/taxi/runway route without repositioning shortcuts.
"""
import math,copy

SURFACE=-3.689
STAND=[16.,17.3,0.]
RUNWAY=dict(name='36',centre_x=300.,south=310.,north=-2290.,length=2600.,width=45.,shoulder=7.5,
            surface_z=SURFACE,lineup=[300.,190.],heading=0.)
TAXI_WIDTH=23.
HOLD=[120.,140.]


def clamp(v,a,b):return max(a,min(b,v))
def angle_error(want,actual):return (want-actual+180)%360-180
def heading_to(a,b):return math.degrees(math.atan2(-(b[0]-a[0]),-(b[1]-a[1])))%360


def native_basis(heading,pitch,bank):
    """Native root localY points forward; h90 is source/native-X.

    Positive pitch raises the nose and positive bank lowers the pilot's right
    wing (native-X at heading0). Vectors are orthogonal for arbitrary poses.
    """
    h,p,b=map(math.radians,(heading,pitch,bank))
    forward=[-math.sin(h)*math.cos(p),math.cos(h)*math.cos(p),math.sin(p)]
    right=[-math.cos(h),-math.sin(h),0.]
    upright=[math.sin(h)*math.sin(p),-math.cos(h)*math.sin(p),math.cos(p)]
    up=[upright[i]*math.cos(b)+right[i]*math.sin(b) for i in range(3)]
    return forward,up


def taxi_route():
    p=[[16.,17.3],[16.,-70.]]
    def arc(cx,cy,r,start,end,steps):
        p.extend([[cx+r*math.cos(math.radians(start+(end-start)*i/steps)),
                   cy+r*math.sin(math.radians(start+(end-start)*i/steps))] for i in range(1,steps+1)])
    arc(51,-70,35,180,270,18);p.append([90.,-105.]);arc(90,-75,30,270,360,18)
    p.extend([HOLD[:],[120.,190.]])
    arc(210,190,90,180,0,60)
    p.append([300.,100.])
    return p


def closest_path(p,path):
    best=None;distance_along=0
    for i,(a,b) in enumerate(zip(path,path[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
        if ll<1e-12:continue
        t=clamp(((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll,0,1);q=[a[0]+t*dx,a[1]+t*dy]
        d=math.dist(p[:2],q);length=math.sqrt(ll)
        if best is None or d<best['distance']:best=dict(distance=d,point=q,segment=i,t=t,along=distance_along+t*length,heading=heading_to(a,b))
        distance_along+=length
    return best


def path_at(path,distance):
    for a,b in zip(path,path[1:]):
        length=math.dist(a,b)
        if distance<=length:
            t=clamp(distance/max(length,.001),0,1);return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]
        distance-=length
    return path[-1][:]


def runway_position(p,heading):
    return bool(abs(p[0]-RUNWAY['centre_x'])<=RUNWAY['width']/2-3 and
                RUNWAY['north']<p[1]<RUNWAY['south'] and abs(angle_error(0,heading))<12)


def fresh():
    return dict(phase='gate',position=STAND[:],heading=0.,pitch=0.,bank=0.,speed=0.,vertical_speed=0.,
        airborne=False,battery=False,avionics=False,fuel=False,pumps=False,bleed=False,beacon=False,
        engines=[dict(running=False,starting=False,start_time=0.,n1=0.) for _ in range(2)],
        throttle=[0.,0.],parking=True,flaps=0,speedbrake=0,gear_down=True,taxi_clear=False,runway_clear=False,
        elapsed=0.,distance=0.,root_writes=0,denials=[],events=[],last_reason='Board, close doors and stow the jetbridge',
        controls=dict(roll=0.,pitch=0.,rudder=0.,brake=0.),v1=66.,vr=72.,v2=78.,stall_speed=55.,
        ground_reference_z=0.,engine_out=False)


def power(s):return s['battery'] or any(e['running'] for e in s['engines'])


def prerequisites(s,c,engines=False):
    if not c.get('aboard'):return False,'Board the aircraft through A07 first'
    if not c.get('pilot'):return False,'Sit in a pilot seat to operate the aircraft'
    if not c.get('doors_closed'):return False,'Close all four aircraft doors and the cargo hatch'
    if not c.get('bridge_stowed'):return False,'The empty jetbridge must be fully stowed'
    if not s['battery']:return False,'Master AUX / battery must be ON'
    if not s['avionics']:return False,'NAV / avionics must be ON'
    if not s['beacon']:return False,'Select the beacon before engine start'
    if engines and not all(e['running'] for e in s['engines']):return False,'Both engines must reach idle before taxi'
    return True,'Ready'


def command(s,name,value,c=None):
    c=c or {};okay=True;reason=''
    if name in ('battery','avionics','fuel','pumps','bleed','beacon'):
        if name!='battery' and bool(value) and not power(s):okay,reason=False,'Master AUX / battery must be ON first'
        else:s[name]=bool(value)
    elif name.startswith('engine'):
        i=int(name[-1])-1;e=s['engines'][i]
        if int(value)==0:e.update(running=False,starting=False);reason='Engine '+str(i+1)+' shutting down'
        elif int(value)==1:
            okay,reason=prerequisites(s,c)
            if okay and not (s['fuel'] and s['pumps'] and s['bleed']):okay,reason=False,'FUEL, PUMP and AIR must be ON before START'
            if okay:e.update(starting=True,start_time=0.);reason='Engine '+str(i+1)+' starting'
        elif not e['running']:okay,reason=False,'Select START and wait for the engine to reach idle'
    elif name=='parking':
        if not value:
            okay,reason=prerequisites(s,c,True)
            if okay and not s['taxi_clear']:okay,reason=False,'Request taxi clearance on the radio'
        if okay:s['parking']=bool(value)
    elif name=='clearance':
        if not power(s) or not s['avionics']:okay,reason=False,'Power NAV / avionics before calling ground'
        elif not s['taxi_clear']:s['taxi_clear']=True;reason='Taxi via Alpha; hold short of runway36 at Alpha1'
        elif math.dist(s['position'][:2],HOLD)<30 and s['speed']<.8:
            s['runway_clear']=True;reason='Runway36 cleared for entry and takeoff'
        elif s['runway_clear']:reason='Runway36 clearance remains valid'
        else:okay,reason=False,'Stop at Alpha1 hold-short and call for runway clearance'
    elif name.startswith('throttle'):
        i=int(name[-1])-1;v=clamp(float(value),0,1)
        if v>.55:
            okay,reason=prerequisites(s,c,True)
            if okay and not s['runway_clear']:okay,reason=False,'Hold short and obtain runway clearance'
            if okay and not (s['airborne'] or runway_position(s['position'],s['heading'])):okay,reason=False,'Line up with runway36 before takeoff thrust'
            if okay and not s['airborne'] and (s['flaps']!=1 or s['speedbrake']!=0):okay,reason=False,'Set takeoff flaps5 and retract the speedbrake'
        if okay:s['throttle'][i]=v
    elif name=='flaps':s['flaps']=int(value)%3
    elif name=='speedbrake':s['speedbrake']=int(value)%3
    elif name=='gear':
        if not value and not s['airborne']:okay,reason=False,'The landing gear remains down on the ground'
        else:s['gear_down']=bool(value)
    elif name in s['controls']:s['controls'][name]=clamp(float(value),0,1) if name=='brake' else clamp(float(value),-1,1)
    else:okay,reason=False,'Unknown flight control '+name
    if not reason:reason=(name.replace('_',' ').title()+' '+str(value))
    s['last_reason']=reason
    if not okay:s['denials'].append(dict(time=s['elapsed'],control=name,reason=reason));s['denials']=s['denials'][-60:]
    else:s['events'].append(dict(time=s['elapsed'],control=name,value=value));s['events']=s['events'][-200:]
    return okay,reason


def step(s,dt,c=None):
    dt=clamp(float(dt),.001,.05);s['elapsed']+=dt;c=c or {}
    for i,e in enumerate(s['engines']):
        if e['starting']:
            if not (power(s) and s['fuel'] and s['pumps'] and s['bleed']):e['starting']=False
            else:
                e['start_time']+=dt
                if e['start_time']>=4.:e.update(starting=False,running=True)
        if e['running'] and not s['fuel']:e['running']=False
        target=.22+.78*s['throttle'][i] if e['running'] else .22*clamp(e['start_time']/4,0,1) if e['starting'] else 0.
        e['n1']+=(target-e['n1'])*min(1,dt*(1.1 if target>e['n1'] else .75))
    inp=s['controls'];v=s['speed'];before=s['position'][:]
    # A dock/door is a hard ground interlock, evaluated every frame.
    interlocked=not (c.get('doors_closed',False) and c.get('bridge_stowed',False))
    if interlocked and not s['airborne']:s['parking']=True
    if not s['airborne']:
        yaw_rate=24./(1+v*.075)*inp['rudder']*clamp(v/1.5,0,1);s['heading']=(s['heading']+yaw_rate*dt)%360
        desired_pitch=clamp(inp['pitch']*10.,-1,10.) if v>=s['vr'] else 0.
        s['pitch']+=(desired_pitch-s['pitch'])*min(1,dt*1.4);s['bank']=0.
    else:
        desired_bank=inp['roll']*35.;s['bank']+=(desired_bank-s['bank'])*min(1,dt*1.8)
        s['pitch']=clamp(s['pitch']+inp['pitch']*9*dt,-22,25)
        turn=math.degrees(9.81*math.tan(math.radians(s['bank']))/max(v,25))+inp['rudder']*3.
        s['heading']=(s['heading']+turn*dt)%360
    thrust=sum(max(0,(e['n1']-.22)/.78) if e['running'] else 0 for e in s['engines'])/2
    flight_path=math.radians(clamp(s['pitch']-3.,-28,22)) if s['airborne'] else 0.
    drag=.08+.00018*v*v+s['flaps']*.13+s['speedbrake']*.75+(.18 if s['airborne'] and s['gear_down'] else 0)
    braking=8. if s['parking'] else 7.*inp['brake']
    accel=3.2*thrust-drag-braking-9.81*math.sin(flight_path)
    if s['parking'] and v<.04:accel=min(0,accel)
    s['speed']=clamp(v+accel*dt,0,170.)
    if not s['airborne'] and v>=s['vr'] and s['pitch']>3.5:
        s['airborne']=True;s['vertical_speed']=max(.8,v*math.sin(math.radians(s['pitch']-2)))
        s['events'].append(dict(time=s['elapsed'],control='liftoff',value=s['speed']))
    if s['airborne']:
        target=s['speed']*math.sin(flight_path)
        if s['speed']<s['stall_speed']:target-=min(18,(s['stall_speed']-s['speed'])*.65)
        s['vertical_speed']+=(target-s['vertical_speed'])*min(1,dt*1.5)
        s['position'][2]+=s['vertical_speed']*dt
        if s['position'][2]<0:
            s['position'][2]=0.;s['airborne']=False;s['vertical_speed']=0.;s['pitch']=0.
    else:
        # Main-gear pivot contact: aft axle remains on the exact pavement while
        # the nose rises. The native airframe remains one rigid hierarchy.
        p=math.radians(s['pitch']);s['position'][2]=max(0,math.sin(p)-3.689*(1-math.cos(p)))
        s['vertical_speed']=0.
    h=math.radians(s['heading']);horizontal=s['speed']*math.cos(flight_path)
    s['position'][0]-=math.sin(h)*horizontal*dt;s['position'][1]-=math.cos(h)*horizontal*dt
    s['distance']+=math.dist(before,s['position'])
    if s['airborne']:s['phase']='climb' if s['position'][2]<300 else 'flight'
    elif runway_position(s['position'],s['heading']):s['phase']='takeoff_roll' if s['speed']>18 else 'lineup'
    elif s['speed']>.2:s['phase']='taxi'
    elif any(e['starting'] for e in s['engines']):s['phase']='starting'
    elif all(e['running'] for e in s['engines']):s['phase']='ready_taxi'
    else:s['phase']='gate'
    s['engine_out']=s['airborne'] and not all(e['running'] for e in s['engines'])
    return s


def snapshot(s):
    return {k:copy.deepcopy(s[k]) for k in ['phase','position','heading','pitch','bank','speed','vertical_speed','airborne','battery','avionics','fuel','pumps','bleed','beacon','engines','throttle','parking','flaps','speedbrake','gear_down','taxi_clear','runway_clear','elapsed','distance','last_reason','engine_out']}
