"""Airport38 airside replacement. Source authoring and native assembly hooks.

Nothing in this module edits legacy source exports or a running editor.
"""
import copy, json, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from airside_math38 import *

def _manifest(ctx):
    airport=Path(getattr(ctx,'A',Path(ctx.R).parent))
    return json.loads((airport.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text(encoding='utf-8'))['scenes']['L_Plane_Reference']

def _remove(ctx,name):
    if any(q['name']==name for q in ctx.D['instances']):ctx.remove(name)

def plan(ctx):
    D=ctx.D
    removed=[]
    for q in list(D['instances']):
        if (q['asset'] in ('SM_AP_BridgeFloor','SM_AP_BridgeWall','SM_AP_BridgeRoof','SM_AP_ServicePath12')
            or q['name'] in ('Jetbridge crafted fittings34','Pillar1212_1624','Pillar1212_1625')
            or q['name'].startswith('Service ramp automatic leaf')):
            removed.append(q['name']);ctx.remove(q['name'])
    D['floors']=[q for q in D.get('floors',[]) if q.get('name') not in ('Level boarding bridge','Service ramp') and not q.get('name','').startswith('Bridge38 ')]
    D['floors'].extend(floor_polygons())
    if any(q['name']=='Physical luggage 05' for q in D['instances']):
        ctx.move('Physical luggage 05',[-27.5,25.8,.04],rotation=165)
        ctx.require('Physical luggage 05')['parking38']='supported A08 luggage nook; remains pickable'
    # The abandoned station followed the removed exterior terrace; its portable
    # extinguisher is moved with its interaction, not left as a floating target.
    for q in list(D['instances']):
        if q['name']=='Safety station 3':ctx.move(q['name'],[-29.45,32.6,0],rotation=180)
        if 'extinguisher' in q['name'].lower() and -17<q['location'][0]<-13 and 15<q['location'][1]<19:
            ctx.move(q['name'],[-29.15,32.55,.1],rotation=180)
    vehicles=[q for q in D['instances'] if q['asset'] in ('SM_AP_Tug','SM_AP_Dolly','SM_AP_Tug34','SM_AP_Dolly34')]
    vehicles.sort(key=lambda q:('Dolly' in q['asset'],q['name']))
    assert len(vehicles)<=3,'Unexpected additional ground vehicles: author a separate parking bay.'
    for i,q in enumerate(vehicles):
        ctx.move(q['name'],[-11,56+i*4,-3.7],rotation=0)
        q.update(parked38=True,parking_group38='BAY38',departure_clear38=True)
    for q in D['instances']:
        if q['asset']=='SM_AP_MobileStairs':ctx.move(q['name'],[-11,77,-3.7],rotation=0);q['parking_group38']='BAY38'
        if q['asset']=='SM_AP_GroundPower34':ctx.move(q['name'],[-11,69.5,-3.7],rotation=0);q['parking_group38']='BAY38'
    D['aircraft38']=dict(offset=list(OFFSET),door=L1,door_state_key="P.STATE['movables']['Aircraft door 1L']",door_closed_progress_max=.015,
        bounds=[list(q) for q in AIRCRAFT_BOUNDS],start_aboard=[15.2,.675,1.62],
        crossing=dict(axis='x',threshold=14.1,inside=[14.1,18.4,-.3,2.0],direction=1),
        bridge=dict(portal=[-14,.675],path=[[-14,.675],list(PIVOT),list(ELBOW),list(NOSE_CAB),list(THRESHOLD)],
            floor_polygons=floor_polygons(),default_state='deployed',stow_duration_s=12.,
            max_stowed_x=-9.75,aircraft_min_x=AIRCRAFT_BOUNDS[0][0],
            supports_follow_pose=True,interlock='No occupied bridge; L1 fully closed; terminal doors closed before retraction; all moving parts stowed before departure'),
        parking=dict(vehicles=[q['name'] for q in vehicles],bay=[-12.5,-9.5,53.5,82],surface_z=-3.7,physics='sleep while unoccupied; wake before drive/tow; brake to rest before sleep'),
        departure=dict(direction=[0,-1,0],distance_m=180,sweep_method='continuous conservative full-aircraft AABB',requires=['bridge stowed','L1 closed','clear transformed native bounds'],prototype_flight='interlock API; no fabricated airport flight controller'))
    D.setdefault('repair38',{})['airside']=dict(removed=removed,source_aircraft_shift_m=list(OFFSET),native_shift_once=True,
        assigned_findings=['A3-01','A3-02','A3-03','A3-05','A3-06','A3-07'],delegated={'A3-04':'fix2 boarding desk','A3-05 base floor policy':'fix5'})

def _materials(a):
    for q in [('P38BShell','D9E0DC',.55),('P38BTrim','283E49',.49),('P38BTeal','2B7179',.64),
              ('P38BDeck','49676D',.88),('P38BSteel','9DAEB5',.32,.75),('P38BRubber','283238',.87),
              ('P38BGold','D9B66A',.48),('P38BMark','DED5BD',.71),('P38BAsphalt','455258',.92),
              ('P38BLED','FFEAC5',.38,0,2.4),('P38BGreen','77C5A2',.4,0,1.2),('P38BRed','C85E43',.52)]:
        a.mat(*q)
    a.mat('P38BGlass','CDE0E4',.22,0,0,True)

def _beam(a,n,start,end,width,depth,mat):
    from mathutils import Vector
    vec=Vector(end)-Vector(start);mid=(Vector(start)+Vector(end))/2
    o=a.box(n,mid,(vec.length,width,depth),mat,.018)
    o.rotation_euler=vec.to_track_quat('X','Z').to_euler()
    return o

def _sleeve(a,bank,index,count):
    L=SLEEVE_LENGTH;w=(3.08 if bank=='A' else 2.98)-index*.075;h=2.82-index*.025
    z=index*.006;left=1.14 if index==0 else .07;right=L-(1.14 if index==count-1 else .07)
    # Deck ownership is explicitly nested at 6mm steps; no coplanar carpet sheets.
    a.box('Folded load bearing deck', (L/2,0,z-.095),(L,w-.14,.19),'P38BTrim',.025)
    a.box('Fitted non-slip floor',(L/2,0,z+.006),(L-.035,w-.23,.012),'P38BDeck',.008)
    for side in (-1,1):
        y=side*w/2
        a.box('Lower formed side panel',((left+right)/2,y,z+.46),(right-left,.075,.88),'P38BShell',.025)
        a.box('Continuous kick rail',((left+right)/2,y-side*.052,z+.10),(right-left,.025,.14),'P38BTrim',.008)
        a.box('Shoulder rail',((left+right)/2,y,z+.94),(right-left,.085,.09),'P38BSteel',.012)
        a.box('Window lintel',((left+right)/2,y,h-.16),(right-left,.10,.30),'P38BShell',.025)
        # Actual glazed aperture in the wall, not a pane over an opaque slab.
        a.box('Clear laminated side glazing',((left+right)/2,y,z+1.67),(right-left-.03,.016,1.34),'P38BGlass',.006)
        for x in (left,right):
            a.box('Rounded extruded upright',(x,y,1.78),(.075,.105,1.70),'P38BSteel',.014)
        a.tube('Supported interior handrail',[(left,y-side*.12,1.01),(right,y-side*.12,1.01)],.027,'P38BSteel')
        for x in (left+.13,right-.13):
            a.tube('Handrail bracket',[(x,y-side*.025,.94),(x,y-side*.12,.94),(x,y-side*.12,1.01)],.014,'P38BSteel')
        a.box('Airline teal sill',((left+right)/2,y+side*.041,.58),(right-left,.016,.18),'P38BTeal',.008)
        a.box('Fine warm identity band',((left+right)/2,y+side*.052,.72),(right-left,.012,.025),'P38BGold',.005)
    # Upper/lower roof skins are real boxed construction, with covered sleeve ends.
    a.box('Weather roof cassette',(L/2,0,h),(L,w+.05,.14),'P38BShell',.04)
    a.box('Warm acoustic ceiling',(L/2,0,h-.09),(L-.02,w-.15,.045),'P38BShell',.018)
    for y in (-.70,.70):
        a.pill('Recessed diffuser surround',(L/2,y,h-.125),(L-.38,.17,.032),'P38BTrim',.05)
        a.pill('Warm diffuse linear lamp',(L/2,y,h-.146),(L-.46,.105,.018),'P38BLED',.04)
    for side in (-1,1):
        a.box('Sealed telescoping bearing',(.08,side*(w/2+.025),.03),(.16,.075,.17),'P38BRubber',.016)
    # Boundary gasket stands proud only 2mm, rather than doubled carpet.
    a.box('Replaceable expansion gasket',(L-.018,0,z+.014),(.026,w-.26,.004),'P38BRubber',.003)

def _chamber(a,incoming,outgoing,width=2.85):
    """Convex mitred chamber between two trimmed tube ends, with open portals."""
    cut=1.14
    p0=along((0,0),incoming,-cut);p1=along((0,0),outgoing,cut)
    def pair(p,ang):
        r=math.radians(ang)
        return [(p[0]-math.sin(r)*width/2,p[1]+math.cos(r)*width/2),(p[0]+math.sin(r)*width/2,p[1]-math.cos(r)*width/2)]
    aa,bb=pair(p0,incoming),pair(p1,outgoing);poly=hull(aa+bb)
    for z,depth,mat in [(-.085,.17,'P38BTrim'),(.008,.016,'P38BDeck'),(2.77,.14,'P38BShell'),(2.68,.04,'P38BShell')]:
        verts=[(x,y,z-depth/2) for x,y in poly]+[(x,y,z+depth/2) for x,y in poly];n=len(poly)
        a.mesh('Mitred continuous chamber '+mat,verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,.009)
    openings=[set(aa),set(bb)]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        if any({p,q}==ends for ends in openings):continue
        for z,height,mat in [(.48,.9,'P38BShell'),(1.69,1.45,'P38BGlass'),(2.59,.19,'P38BShell')]:
            _beam(a,'Fitted bend return',(*p,z),(*q,z),.09,height,mat)
        _beam(a,'Continuous bend grab rail',(*p,1.02),(*q,1.02),.045,.045,'P38BSteel')
    a.cyl('Rotary bearing plate',(0,0,-.2),.58,.1,'P38BSteel')
    a.pill('Joint warm diffuser',(0,0,2.645),(.6,.32,.02),'P38BLED',.08)

def _cab(a):
    # Dock body is long enough for L1's outward swing (minimum x~12.44).
    L=THRESHOLD[0]-NOSE_CAB[0];w=2.92
    a.box('Dock chassis',(L/2,0,-.12),(L,w,.24),'P38BTrim',.04)
    a.box('Dock non-slip floor',(L/2,0,.007),(L-.02,w-.12,.014),'P38BDeck',.008)
    # First 1.14m is occupied by bank B's mitred connector chamber.
    for side in (-1,1):
        y=side*w/2
        a.box('Cab lower return',((1.14+L-.48)/2,y,.51),(L-.48-1.14,.10,1.02),'P38BShell',.035)
        a.box('Cab clear side',((1.14+L-.48)/2,y,1.78),(L-.48-1.14,.028,1.43),'P38BGlass',.008)
        a.box('Cab roof side rail',((1.14+L-.48)/2,y,2.58),(L-.48-1.14,.12,.2),'P38BShell',.025)
        a.box('Cab corner post',(L-.48,y,1.36),(.12,.12,2.7),'P38BSteel',.025)
        a.tube('Cab safety rail',[(1.14,y-side*.1,1.05),(L-.50,y-side*.1,1.05)],.025,'P38BSteel')
    a.box('Weather sealed cab roof',(L/2,0,2.77),(L,w+.06,.16),'P38BShell',.04)
    a.box('Threshold underplate',(L-.18,0,-.035),(.39,1.86,.07),'P38BSteel',.012)
    a.box('Threshold footplate',(L-.17,0,.014),(.37,1.83,.018),'P38BSteel',.005)
    # Flexible accordion U seals stop outside the fuselage; centre is a genuine aperture.
    for j in range(7):
        x=L-.49+j*.065
        outer=[(-1.19,.04),(-1.19,2.16)]
        outer += [(-.81+.38*math.cos(math.radians(t)),2.16+.38*math.sin(math.radians(t))) for t in range(170,89,-10)]
        outer += [(.81,2.54)]
        outer += [(.81+.38*math.cos(math.radians(t)),2.16+.38*math.sin(math.radians(t))) for t in range(80,-1,-10)]
        outer += [(1.19,.04)]
        inner=[(1.08,.04),(1.08,2.16)]
        inner += [(.81+.27*math.cos(math.radians(t)),2.16+.27*math.sin(math.radians(t))) for t in range(10,91,10)]
        inner += [(-.81,2.43)]
        inner += [(-.81+.27*math.cos(math.radians(t)),2.16+.27*math.sin(math.radians(t))) for t in range(100,181,10)]
        inner += [(-1.08,.04)]
        # One continuous U profile with no flipped tangent-frame tube corners.
        a.profile('Supported flexible accordion rib',outer+inner,x-.023,x+.023,'P38BRubber',.008)
    # Side curtains cover the spaces between ribs, but do not seal over the door opening.
    for side in (-1,1):a.box('Bellows flexible side membrane',(L-.28,side*1.14,1.15),(.51,.045,2.22),'P38BRubber',.018)
    a.box('Bellows flexible upper membrane',(L-.28,0,2.54),(.51,2.22,.075),'P38BRubber',.018)
    a.pill('Emergency bumper',(L-.035,0,-.20),(.12,2.42,.15),'P38BRubber',.055)
    a.pill('Cab warm diffuser',(L/2,0,2.66),(1.6,.15,.025),'P38BLED',.04)
    # Precision dock panel mounted on the outside of the cab, with protected stop.
    a.pill('Dock operator box',(1.8,-1.52,1.15),(.46,.12,.54),'P38BTeal',.045)
    for i,m in enumerate(('P38BGreen','P38BRed')):a.cyl('Mounted docking pushbutton',(1.69+i*.22,-1.59,1.16),.034,.025,m,'Y')
    a.tube('Protected emergency stop shroud',[(1.80,-1.60,1.32),(1.93,-1.60,1.32),(1.93,-1.60,1.44),(1.80,-1.60,1.44)],.012,'P38BSteel')

def _truck(a):
    a.box('Cross-axle carriage',(0,0,.36),(1.80,1.22,.25),'P38BTrim',.04)
    for x in (-.68,.68):
        a.cyl('Caster kingpin',(x,0,.30),.095,.32,'P38BSteel')
        for y in (-.55,.55):
            a.cyl('Ground contact pneumatic tyre',(x,y,.25),.25,.18,'P38BRubber','Y')
            a.cyl('Recessed wheel hub',(x,y*1.12,.25),.12,.025,'P38BSteel','Y')
    a.cyl('Hydraulic base shoe',(0,0,.49),.35,.18,'P38BSteel')

def _lift(a):
    a.cyl('Telescoping hydraulic pedestal',(0,0,.50),.17,1.,'P38BSteel')
    a.cyl('Lower hydraulic collar',(0,0,.08),.225,.16,'P38BTrim')
    a.cyl('Upper weather collar',(0,0,.92),.20,.12,'P38BRubber')
    a.box('Dock bearing support',(0,0,.98),(.90,.55,.055),'P38BTrim',.025)

def _console(a):
    a.pill('Wall mounted bridge control',(0,0,1.18),(.36,.15,.52),'P38BTeal',.045)
    a.pill('Recessed status glass',(0,-.085,1.30),(.28,.025,.16),'P38BTrim',.01)
    a.font('BRIDGE',(0,-.102,1.30),.045,'P38BMark')
    for x,m in [(-.09,'P38BGreen'),(.09,'P38BRed')]:
        a.cyl('Button mounting bezel',(x,-.091,1.11),.043,.025,'P38BSteel','Y')
        a.cyl('Round supported button',(x,-.112,1.11),.029,.025,m,'Y')
    a.font('DEPLOY / STOW',(0,-.083,.99),.022,'P38BMark')

def _bounds(collection):
    from mathutils import Vector
    points=[o.matrix_world@Vector(p) for o in collection.objects if o.type=='MESH' for p in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]

def build(ctx):
    a,D=ctx.a,ctx.D;_materials(a);meta=D['aircraft38']['bridge'];poses=bridge_pose(0);components=[]
    def asset(n,callback):
        col=a.asset(n,callback);return col.name,col
    def place(asset_id,name,p,r=0,role='moving',**extra):
        q=ctx.add(asset_id,name,p,rotation=r,collision=True,bridge38=role,**extra)
        col=a.ASSETS[asset_id]['collection'];components.append(dict(name=name,asset=asset_id,bounds=_bounds(col),role=role))
        return q
    for bank,count in [('A',4),('B',5)]:
        for i in range(count):
            aid,_=asset('P38B_%s%02d'%(bank,i),lambda b=bank,j=i,c=count:_sleeve(a,b,j,c))
            name='Bridge38 bank %s sleeve %02d'%(bank,i);pose=poses[name];place(aid,name,pose['location'],pose['rotation'])
    for name,incoming,outgoing,p,role in [
        ('pivot chamber',0,angle(PIVOT,ELBOW),PIVOT,'fixed'),
        ('elbow chamber',angle(PIVOT,ELBOW),angle(ELBOW,NOSE_CAB),ELBOW,'moving')]:
        aid,_=asset('P38B_'+name.replace(' ','_'),lambda i=incoming,o=outgoing:_chamber(a,i,o))
        place(aid,'Bridge38 '+name,[*p,0],0,role)
    # Terminal neck is short, permanent, and fully west of the aircraft sweep.
    aid,_=asset('P38B_terminal_neck',lambda:_neck(a))
    place(aid,'Bridge38 terminal neck',[-14,.675,0],0,'fixed')
    aid,_=asset('P38B_docking_cab',lambda:_cab(a));place(aid,'Bridge38 docking cab',[*NOSE_CAB,0])
    aid,_=asset('P38B_cab_joint',lambda:_chamber(a,angle(ELBOW,NOSE_CAB),0))
    # Cab joint moves with the cab, including its roof and both mitered returns.
    name='Bridge38 cab mitre';place(aid,name,[*NOSE_CAB,0]);poses[name]=poses['Bridge38 docking cab'].copy()
    for which in ('A','B'):
        for typ,fn in [('truck',_truck),('lift',_lift)]:
            aid='SM_AP_P38B_'+typ
            if aid not in a.ASSETS:asset('P38B_'+typ,lambda fn=fn:fn(a))
            name='Bridge38 %s %s'%(which,typ);pose=poses[name]
            place(aid,name,pose['location'],pose['rotation'],scale=pose.get('scale',[1,1,1]))
            if pose.get('ground_normal'):
                from mathutils import Vector,Matrix
                x=Vector(pose['forward']).normalized();z=Vector(pose['ground_normal']);y=z.cross(x).normalized()
                o=ctx.scene.objects.get(name)
                if o:o.rotation_euler=Matrix((x,y,z)).transposed().to_euler()
                ctx.require(name)['ground_pose38']=pose
    aid,_=asset('P38B_bridge_control',lambda:_console(a));place(aid,'Bridge38 departure control',[-14.1,-.95,0],-90,'fixed')
    D['interactions'].append(dict(kind='bridgecontrol38',actor='Bridge38 departure control',point=[-14.28,-.95,1.13],title='Jetbridge · deploy / stow',range_m=2.5))
    aid,_=asset('P38B_parking_pad',lambda:_parking(a));place(aid,'Ground crew parking bay38',[-11,67.75,-3.7],0,'parking')
    meta['components']=components;meta['moving_names']=[q['name'] for q in components if q['role']=='moving']
    meta['fixed_names']=[q['name'] for q in components if q['role']=='fixed']
    meta['deployed_poses']=poses
    # The entire source aircraft is a linked set of collection-instance roots.
    # Shift local instance empties, never the linked meshes inside those assets.
    manifest=_manifest(ctx);names={q['name'] for q in manifest['instances']};assets={q['asset'] for q in manifest['instances']}
    shifted=[]
    for o in ctx.scene.objects:
        if o.instance_type=='COLLECTION' and o.instance_collection and (o.name in names or o.instance_collection.name in assets):
            if not o.get('airport38_plane_shifted'):
                o.location.x+=16;o['airport38_plane_shifted']=True
            shifted.append(o.name)
    assert len(shifted)>=1100,('Expected complete linked aircraft root set',len(shifted))
    D['repair38']['airside']['source_shifted_roots']=len(shifted)
    # Native validation uses true imported bounds; this source assertion catches
    # any forgotten fixed cab/rail/pier before import.
    obstacles=[]
    for q in components:
        if q['role']=='parking':continue
        pose=bridge_pose(1).get(q['name'])
        if q['name']=='Bridge38 cab mitre':pose=bridge_pose(1)['Bridge38 docking cab']
        if not pose:
            inst=next(i for i in D['instances'] if i['name']==q['name'])
            pose=dict(location=inst['location'],rotation=inst['rotation_degrees'],scale=inst.get('scale',[1,1,1]))
        bb=posed_bounds(q['bounds'],pose);obstacles.append(dict(name=q['name'],bounds=bb))
        assert bb[1][0]<-9.75,(q['name'],bb)
    meta['source_stowed_obstacles']=obstacles
    meta['source_sweep']=validate_sweep(obstacles)
    assert meta['source_sweep']['clear']
    # Practical lights physically follow their corresponding sleeve during stow.
    for bank,count in [('A',4),('B',5)]:
        for i in range(count):
            name='Bridge38 bank %s sleeve %02d'%(bank,i);pose=poses[name]
            p=world([SLEEVE_LENGTH/2,0,2.42],pose['location'],pose['rotation'])
            D.setdefault('lights',[]).append(dict(name='Bridge38 warm practical %s%d'%(bank,i),type='AREA',position=list(p),location=list(p),rotation=[0,0,0],watts=350,width=135,height=22,energy=45,color=[1,.86,.67],size=1.4,follow_actor=name,local_point=[SLEEVE_LENGTH/2,0,2.42],role='bridge_practical'))
    # Source module returns metadata for an isolated harness as well.
    return meta

def _neck(a):
    L=1.9;w=2.88
    a.box('Terminal neck deck',(L/2,0,-.08),(L,w,.16),'P38BTrim',.02)
    a.box('Neck fitted floor',(L/2,0,.006),(L-.02,w-.18,.012),'P38BDeck',.006)
    for s in (-1,1):
        a.box('Portal side return',(L/2,s*w/2,1.35),(L,.12,2.7),'P38BShell',.03)
        a.tube('Neck grab rail',[(.05,s*(w/2-.12),1.02),(L-.05,s*(w/2-.12),1.02)],.026,'P38BSteel')
    a.box('Portal roof weather seal',(L/2,0,2.76),(L,w,.16),'P38BShell',.03)
    a.pill('Neck warm lamp',(L/2,0,2.65),(1.2,.14,.02),'P38BLED',.04)

def _parking(a):
    a.box('Continuous supported service pad',(0,0,-.12),(3.0,28.5,.24),'P38BAsphalt',.04)
    for x in (-1.25,1.25):a.box('Parking side stripe',(x,0,.006),(.065,28,.012),'P38BMark',.005)
    for y in (-14,-9.75,-5.75,-1.75,4.25,14):a.box('Defined parking bay line',(0,y,.008),(2.5,.07,.016),'P38BGold',.005)
    # Stops mounted at far end, never under the tug chassis.
    for x in (-.75,.75):a.pill('Anchored wheel stop',(x,14,.07),(.55,.18,.14),'P38BTrim',.04)

def apply_native(ctx):
    """Translate every aircraft root once; children, proxies and labels follow."""
    u,EA,D=ctx.u,ctx.EA,ctx.D;manifest=_manifest(ctx)
    names={q['name'] for q in manifest['instances']}
    labels={'Label '+str(i)+' '+q['text'][:40] for i,q in enumerate(manifest['labels'])}
    bounds={q['name'] for q in manifest.get('navigation_bounds',[])}
    selected=[]
    for a in EA.get_all_level_actors():
        label=a.get_actor_label();tags={str(t) for t in a.tags}
        if any(t.startswith(('Skyward:','SkywardLight:','SkywardCamera:')) for t in tags) or label in labels|bounds or label.startswith('MOTION_PROXY ') and label.removeprefix('MOTION_PROXY ') in names:
            selected.append(a)
    selected_set=set(selected);moved=[];already=[]
    for a in selected:
        parent=a.get_attach_parent_actor();attached=False
        while parent:
            if parent in selected_set:attached=True;break
            parent=parent.get_attach_parent_actor()
        if attached:continue
        if any(str(t)=='Airport38PlaneShift16' for t in a.tags):already.append(a.get_actor_label());continue
        a.set_actor_location(a.get_actor_location()+u.Vector(1600,0,0),False,True)
        a.tags=list(a.tags)+[u.Name('Airport38PlaneShift16')];moved.append(a.get_actor_label())
    # Correct L1's old unrotated world-offset proxy against its actual closed mesh.
    bylabel={a.get_actor_label():a for a in EA.get_all_level_actors()}
    door=next((a for a in selected if 'Skyward:'+L1 in {str(t) for t in a.tags}),None)
    proxy=bylabel.get('MOTION_PROXY '+L1)
    if door and proxy:
        centre,extent=door.get_actor_bounds(False)
        proxy.set_actor_location(centre,False,True)
        # Retain the correctly oriented proxy dimensions and its attachment.
        proxy.tags=list(proxy.tags)+[u.Name('Airport38L1ProxyRemounted')]
    bridge=D['aircraft38']['bridge'];moving=set(bridge['moving_names'])
    for name in moving:
        a=bylabel.get(name)
        if a:
            a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
            pose=bridge_pose(0).get(name)
            if pose and pose.get('ground_normal'):
                a.set_actor_rotation(u.MathLibrary.make_rot_from_xz(ctx.v(pose['forward']),ctx.v(pose['ground_normal'])),False)
    D['repair38']['airside']['native_translation']=dict(selected=len(selected),roots_shifted=len(moved),roots_already_shifted=len(already),source_offset=list(OFFSET))
    assert len(selected)>1300,('Aircraft selection incomplete',len(selected))
    # Transform native imported mesh bounds through all stow stages, then through
    # the complete forward swept box. Every component is included, not just tubes.
    obstacles=[]
    for q in bridge['components']:
        a=bylabel.get(q['name'])
        if not a or q['role']=='parking':continue
        poses=bridge_pose(1);pose=poses.get(q['name'])
        if q['name']=='Bridge38 cab mitre':pose=poses['Bridge38 docking cab']
        old=a.get_actor_transform()
        if pose:
            a.set_actor_location(ctx.v(pose['location']),False,True)
            rotation=u.MathLibrary.make_rot_from_xz(ctx.v(pose['forward']),ctx.v(pose['ground_normal'])) if pose.get('ground_normal') else u.Rotator(yaw=-pose['rotation'])
            a.set_actor_rotation(rotation,False)
            if 'scale' in pose:a.set_actor_scale3d(u.Vector(*pose['scale']))
        c,e=a.get_actor_bounds(False)
        lo=[(c.x-e.x)/100,-(c.y+e.y)/100,(c.z-e.z)/100]
        hi=[(c.x+e.x)/100,-(c.y-e.y)/100,(c.z+e.z)/100]
        obstacles.append(dict(name=q['name'],bounds=[lo,hi]))
        a.set_actor_transform(old,False,True)
    bridge['native_bridge_sweep']=validate_sweep(obstacles)
    assert bridge['native_bridge_sweep']['clear'],bridge['native_bridge_sweep']
    from airport_airside38 import collect_airport_obstacles
    scenery=collect_airport_obstacles(u,EA.get_all_level_actors(),ignore_names={q['name'] for q in bridge['components']},ground_support_assets=D.get('flight39',{}).get('ground_support_assets',[]))
    # Exact graded-ground function is flat at -3.78 across this swept X range;
    # its whole-map AABB alone would produce a false positive up at terminal Z0.
    ground_clear=BODY_AIRCRAFT_BOUNDS[0][2]-apron_height(AIRCRAFT_BOUNDS[0][0],0)
    assert ground_clear>.20,ground_clear
    D['aircraft38']['departure']['native_scene_sweep']=validate_sweep(obstacles+scenery,margin=.20)
    D['aircraft38']['departure']['graded_ground_clearance_m']=ground_clear
    assert D['aircraft38']['departure']['native_scene_sweep']['clear'],D['aircraft38']['departure']['native_scene_sweep']
    if D['aircraft38'].get('gear_contact39'):
        from refine_contacts39 import apply_gear_native
        D['aircraft38']['gear_contact39']['native']=apply_gear_native(ctx)
    return D['repair38']['airside']['native_translation']
