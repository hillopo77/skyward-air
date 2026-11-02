"""Constructed baggage transfer, controlled service doorway and finite café service.

No shared scene is opened here. Root's single assembly owns saving and export.
"""
import math


def plan(ctx):
    D=ctx.D
    D.setdefault('service_openings38',[])
    for lane,y in enumerate((-13.,-16.),1):
        op=dict(axis='y',k=-26.,centre=y,width=1.45,z0=.55,z1=1.95)
        if op not in D['service_openings38']:D['service_openings38'].append(op)
    for q in D['interactions']:
        if q.get('actor')=='Gate A08 boarding desk':q.update(kind='information',title='A08 lounge / flight information',gate='A08')
        if q.get('kind')=='scanner':q['title']='Start / load cabin-bag screening'
        if q.get('actor','').startswith(('Screening entry24','Screening exit24')):q['automatic']=True
        if q.get('kind')=='vending':q['title']='Order a Cloud Nine coffee'
    # Keep a completely clear staff aisle south of lane02 and no loose bag in
    # the controlled doorway. The baggage bay is visible from public reclaim.
    if any(q['name']=='Physical luggage 07' for q in D['instances']):
        ctx.move('Physical luggage 07',[-16.0,-18.8,.04])
    D.setdefault('repair38',{})['journey']=dict(
        revision=38,service_door='Baggage service door38',
        serving_cup='Cloud Nine serving cup38',cup_station=[-46.70,31.17,1.008],
        bag_receivers=[dict(lane=i,name='Bag receiving bed38 %02d'%i,
                           feed='Bag drop belt %02d'%i,transfer='Bag transfer38 %02d'%i,
                           rect=[-24.40,-22.78,y-.49,y+.49],height=.845,
                           receive_x=-24.15,stop_x=-23.30,max_bags=1)
                       for i,y in enumerate((-13.,-16.),1)],
        queue=dict(marker=D['checkin30']['queue_actor'],npc_order=D['checkin30']['npc_order'][:],
                   desks=['Check-in desk 02','Check-in desk 01'],
                   service_points={'Check-in desk 01':[-31.85,-11.6,0],
                                   'Check-in desk 02':[-31.85,-14.6,0]},
                   exit_points=[[-32.05,-8.8,0],[-33.1,-6.1,0]],service_s=1.8),
        support_asset_ids=['SM_AP_Transfer38','SM_AP_Belt38','SM_AP_Outfeed38','SM_AP_Carousel'],
        cup_controls='E pick up / put down; left mouse sip; service button returns and refills the one cup',
        physical_acceptance='after wall crossing, receiving support trace and settled native body')


def _materials(a):
    for n,h,r,m,e in [('Cream','DDD3BD',.78,0,0),('Navy','29484D',.76,0,0),
                       ('Steel','9DA9A2',.61,.45,0),('Rubber','263834',.92,0,0),
                       ('Gold','D4AC61',.69,.05,0),('Paper','EEE0C3',.84,0,0),
                       ('Coffee','3B2920',.74,0,0),('Text','F0E3BE',.83,0,0),
                       ('Green','5D9275',.62,0,0)]:a.mat('P38J'+n,h,r,m,e)


def _transfer(a):
    # Local +X is actual luggage direction. First roller is .18m after the
    # previous input roller; there is no missing deck behind the wall opening.
    start,end=-26.11,-22.78;L=end-start
    a.box('Full supported transfer trough38',(L/2,0,.746),(L,1.01,.054),'P38JRubber',.012)
    for side in (-1,1):
        a.box('Folded transfer side channel38',(L/2,side*.54,.775),(L,.05,.15),'P38JSteel',.009)
        a.tube('Receiver retained continuous safety rail38',[(.04,side*.61,.88),(L-.04,side*.61,.88)],.022,'P38JSteel')
    n=19
    for j in range(n):
        x=.09+j*(L-.18)/(n-1)
        a.cyl('Quiet baggage transfer roller38',(x,0,.805),.040,1.0,'P38JSteel','Y')
        for y in (-.523,.523):a.cyl('Transfer captured bearing38',(x,y,.805),.053,.028,'P38JNavy','Y')
    for x in (.38,1.64,L-.34):
        a.box('Transfer joined crossmember38',(x,0,.665),(.10,1.10,.10),'P38JNavy',.009)
        for y in (-.43,.43):
            a.cyl('Adjustable transfer floor column38',(x,y,.36),.037,.61,'P38JSteel')
            a.cyl('Grounded transfer resilient foot38',(x,y,.035),.070,.07,'P38JRubber')
    a.pill('Receiver cushioned physical endstop38',(L+.025,0,.98),(.10,1.15,.31),'P38JNavy',.04)
    a.box('Supported receiver identification plate38',(L-.36,-.625,.67),(.66,.026,.19),'P38JNavy',.004)
    a.font('SA107 / RECEIVE',(L-.36,-.642,.67),.058,'P38JText')


def _bay_details(a):
    # Flat face gaskets belong to the real cut opening and do not span it.
    for y in (-13.,-16.):
        for yy in (y-.725,y+.725):
            a.box('Baggage aperture retained jamb38',(-25.895,yy,1.25),(.035,.055,1.40),'P38JSteel',.007)
        a.box('Baggage aperture retained lintel38',(-25.895,y,1.975),(.035,1.50,.05),'P38JSteel',.007)
        a.box('Baggage safety legend backing38',(-25.88,y,2.16),(.04,1.4,.24),'P38JNavy',.004)
        a.font('CHECKED BAG TRANSFER',(-25.852,y,2.16),.069,'P38JText',(math.pi/2,0,math.pi/2))
    # Inventory racks are against the north bay lining, with actual shelf,
    # side/back support and room to reach the door at the south end.
    rack_start=set(a.ACTIVE.objects)
    a.box('Baggage handling rack backed panel38',(-23.95,-12.14,1.24),(2.7,.08,2.28),'P38JNavy',.013)
    for x in (-25.25,-22.65):a.box('Handling rack joined upright38',(x,-12.41,1.2),(.07,.60,2.28),'P38JSteel',.009)
    for z in (.15,.62,1.24,1.88):a.pill('Handling rack supported shelf38',(-23.95,-12.41,z),(2.67,.60,.045),'P38JSteel',.018)
    # Rolled straps and molded shallow transport tubs have distinct silhouettes.
    for i,x in enumerate((-24.75,-23.95,-23.15)):
        a.box('Receiving transport tub bottom38',(x,-12.42,.675),(.62,.45,.065),'P38JCream',.02)
        for y in (-12.64,-12.20):a.box('Transport tub long retained side38',(x,y,.79),(.62,.025,.23),'P38JCream',.01)
        for xx in (x-.30,x+.30):a.box('Transport tub captured end38',(xx,-12.42,.79),(.025,.45,.23),'P38JCream',.01)
        a.box('Tub painted inventory marker38',(x,-12.659,.79),(.19,.008,.09),'P38JNavy',.001)
        a.font('0'+str(i+1),(x,-12.666,.79),.048,'P38JText')
    for x in (-24.9,-24.45,-24.):
        a.cyl('Rolled restraint webbing38',(x,-12.42,1.38),.105,.18,'P38JGold','X')
        a.cyl('Restraint captured roll bore38',(x-.095,-12.42,1.38),.035,.016,'P38JRubber','X')
    # Rotate the WHOLE rack to the south wall, including the contents and front
    # labels. North of lane01 there is only .39m: a .60m rack would intersect it.
    for ob in set(a.ACTIVE.objects)-rack_start:
        ob.location.x=2*(-23.95)-ob.location.x
        ob.location.y=-30.50-ob.location.y
        ob.rotation_euler.z+=math.pi
    a.box('Staff west wall tool mounting board38',(-25.87,-17.65,1.56),(.04,1.45,.72),'P38JNavy',.018)
    a.font('BAGGAGE HANDLING',(-25.842,-17.65,1.77),.09,'P38JText',(math.pi/2,0,math.pi/2))
    # A compact wall-mounted dispatch clipboard, not a floating text sign.
    a.box('Dispatch clipboard retained backing38',(-25.83,-17.65,1.41),(.035,.40,.38),'P38JSteel',.004)
    a.box('Clipped dispatch sheet38',(-25.807,-17.65,1.40),(.008,.32,.29),'P38JPaper',.004)
    for z in (1.46,1.41,1.36):a.box('Dispatch printed ruled line38',(-25.801,-17.65,z),(.003,.22,.004),'P38JNavy',0)
    a.pill('Service door retained surface track38',(-21.82,-17.07,2.68),(.17,2.45,.12),'P38JSteel',.018)
    for y in (-18.20,-17.65,-16.52):
        a.box('Service track wall mounting shoe38',(-21.88,y,2.68),(.07,.09,.09),'P38JNavy',.009)
    a.pill('Service door lower guide38',(-21.82,-17.09,.025),(.10,2.38,.05),'P38JSteel',.01)


def _staff_leaf(a):
    # In its closed state this leaf occupies the service aperture. It slides
    # along +Y onto a clear bay-side pocket, with controls on both sides.
    a.pill('Service door continuous formed slab38',(0,0,1.28),(.075,1.10,2.56),'P38JCream',.025)
    for side in (-1,1):
        a.box('Service door inset face panel38',(side*.043,0,1.47),(.014,.87,1.40),'P38JNavy',.012)
        a.box('Service leaf kick plate38',(side*.046,0,.26),(.016,.92,.29),'P38JSteel',.002)
        a.tube('Captured service door pull38',[(side*.057,-.33,1.03),(side*.102,-.33,1.03),(side*.102,-.33,1.25),(side*.057,-.33,1.25)],.014,'P38JSteel')
    a.box('Captured upper sliding bearing38',(0,0,2.58),(.10,.93,.04),'P38JSteel',.008)


def _cup(a):
    N=48
    prof=[(.001,.003),(.039,.003),(.043,.015),(.055,.124),(.053,.132),(.047,.132),(.045,.122),(.035,.018),(.001,.018)]
    a.loft('Continuous open porcelain cup38',[[(r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for i in range(N)] for r,z in prof],'P38JCream')
    a.tube('Cup continuous joined ceramic handle38',[(.049+.035*math.cos(t),0,.073+.043*math.sin(t)) for t in [-math.pi/2+j*math.pi/32 for j in range(33)]],.008,'P38JCream',16)
    a.cyl('Served coffee visible meniscus38',(0,0,.111),.044,.003,'P38JCoffee')


def _saucer(a):
    N=48
    a.loft('Fitted porcelain serving saucer38',[[(r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for i in range(N)] for r,z in [(.001,.001),(.068,.001),(.09,.008),(.095,.016),(.088,.022),(.060,.008),(.001,.008)]],'P38JCream')
    a.pill('Mounted café pickup legend38',(0,-.14,-.04),(.39,.026,.077),'P38JNavy',.009)
    a.font('PICK UP / RETURN',(0,-.156,-.04),.032,'P38JText')


def build(ctx):
    a,D=ctx.a,ctx.D;_materials(a)
    for n,fn,col in [('Transfer38',lambda:_transfer(a),'complex'),('BaggageDetail38',lambda:_bay_details(a),'complex'),
                     ('ServiceDoor38',lambda:_staff_leaf(a),'complex'),('ServingCup38',lambda:_cup(a),'convex'),
                     ('ServingSaucer38',lambda:_saucer(a),'complex')]:a.asset(n,fn,col)
    for r in D['repair38']['journey']['bag_receivers']:
        y=(r['rect'][2]+r['rect'][3])/2
        ctx.add('Transfer38',r['name'],[-26.11,y,0])
        D['conveyors'].append(dict(name=r['transfer'],actor=r['name'],rect=[-26.12,-22.78,y-.49,y+.49],
                                  direction=[1,0],height=.845,speed=.46,kind='transfer38',feed=r['feed'],stage=10))
    ctx.add('BaggageDetail38','Baggage handling fitted details38',[0,0,0])
    ctx.add('ServiceDoor38','Baggage service door38',[-21.87,-17.65,0])
    for side in (-1,1):
        D['interactions'].append(dict(kind='slide',actor='Baggage service door38',point=[-21.87+side*.11,-17.98,1.14],
            title='Staff baggage handling',delta=[0,1.16,0],automatic=False,access24='staff24',fixed_release=True))
    station=D['repair38']['journey']['cup_station']
    ctx.add('ServingSaucer38','Cloud Nine supported cup saucer38',[station[0],station[1],1.0])
    ctx.add('ServingCup38','Cloud Nine serving cup38',station,physics=True,mass=.18,rack_stowed25=True,service_cup38=True)
    D['interactions'].append(dict(kind='pickup',actor='Cloud Nine serving cup38',point=[station[0],station[1],station[2]+.07],title='Pick up served coffee'))
    D['repair38']['journey']['source_families']=['Transfer38','BaggageDetail38','ServiceDoor38','ServingCup38','ServingSaucer38']
    return D['repair38']['journey']
