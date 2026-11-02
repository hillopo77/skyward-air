"""Targeted secondary repairs against the CURRENT38 scene; never reset37."""
import math,json
from pathlib import Path

TAG='equipment_secondary_scrutiny_38'

def apply(ctx):
    import bpy
    from mathutils import Vector
    if ctx.D.setdefault('repair38',{}).get(TAG):return ctx.D['repair38'][TAG]
    a=ctx.a;changed=set();repairs=[]
    def col(aid):
        c=bpy.data.collections[aid];a.ASSETS[aid]=dict(collection=c,collision='complex');changed.add(aid);return c
    def active(aid):
        c=col(aid);a.ACTIVE=c;return c
    def bounds(c):
        bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
        for ob in c.objects:
            if ob.get('export_ignore') or ob.type not in ('MESH','FONT','CURVE'):continue
            ev=ob.evaluated_get(dg);pts.extend(ev.matrix_world@Vector(v) for v in ev.bound_box)
        return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
    def remove(c,prefixes):
        for ob in list(c.objects):
            if ob.name.startswith(prefixes):c.objects.unlink(ob)
    def note(id,asset,detail,before):repairs.append(dict(id=id,asset=asset,detail=detail,before_bounds=before,after_bounds=bounds(bpy.data.collections[asset])))
    def box(n,p,s,m='Ivory',b=.008):return a.box(n,p,s,'P38E'+m,b)
    def pill(n,p,s,m='Ivory',r=.035):return a.pill(n,p,s,'P38E'+m,r)
    def cyl(n,p,r,h,m='Metal',axis='Z'):return a.cyl(n,p,r,h,'P38E'+m,axis)
    def spin(n,p,profile,m='Metal',seg=40):return a.loft(n,[[(p[0]+r*math.cos(j*math.tau/seg),p[1]+r*math.sin(j*math.tau/seg),p[2]+z) for j in range(seg)] for r,z in profile],'P38E'+m)
    def curve(n,points,r,m='Metal'):
        d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=20;d.bevel_depth=r;d.bevel_resolution=4;d.resolution_u=16
        sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
        for bp,p in zip(sp.bezier_points,points):bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
        ob=bpy.data.objects.new(n,d);a.ACTIVE.objects.link(ob);d.materials.append(a.MATS['P38E'+m]);return ob
    # Explicit rigid mechanical links avoid the axial frame twist seen in the
    # genuine native close-up09. Each link penetrates a captured pivot housing.
    c=active('SM_AP_Scanner38');before=bounds(c);remove(c,('Scanner one continuous monitor arm38',))
    cyl('Scanner captured first arm link38R',(.963,-.12,1.23),.027,.268,'Metal','X')
    cyl('Scanner captured offset arm link38R',(1.10,-.24,1.23),.027,.24,'Metal','Y')
    cyl('Scanner captured upright arm link38R',(1.10,-.36,1.365),.027,.29)
    for p in [(1.10,-.12,1.23),(1.10,-.36,1.23)]:
        cyl('Scanner retained pivot barrel38R',p,.047,.075,'Dark')
        cyl('Scanner pivot retaining fastener38R',(p[0],p[1],p[2]+.040),.020,.008)
    pill('Scanner VESA connected carrier38R',(1.10,-.36,1.49),(.16,.065,.15),'Metal',.015)
    note('S2E01','SM_AP_Scanner38','Replace twisted multi-bend loft with three rigid links and captured pivots',before)

    # Preserve both physical sink centres and actual apertures, but rebuild
    # the wrongly sized door/frame bays and close the plumbing/mirror chase.
    c=active('SM_AP_Vanity34');before=bounds(c)
    for ob in list(c.objects):c.objects.unlink(ob)
    pill('Vanity continuous recessed grounded plinth38R',(0,.08,.07),(2.40,1.08,.14),'Navy',.04)
    for x in [-1.18,0,1.18]:box('Vanity full-depth carcass partition38R',(x,.08,.53),(.04,1.16,.82))
    box('Vanity continuous closed plumbing back38R',(0,.65,.53),(2.36,.04,.82))
    for z in [.16,.54]:box('Vanity backed internal shelf38R',(0,.08,z),(2.34,1.10,.035))
    for x in [-1.16,0,1.16]:box('Vanity narrow front frame stile38R',(x,-.455,.53),(.034,.055,.78))
    for z in [.15,.92]:box('Vanity front frame rail38R',(0,-.455,z),(2.36,.055,.035))
    for x in [-.87,-.29,.29,.87]:
        pill('Vanity fitted consistent-reveal door38R',(x,-.46,.535),(.568,.045,.735),'Ivory',.014)
        for xx in [x-.08,x+.08]:cyl('Vanity retained pull standoff38R',(xx,-.493,.80),.011,.025,'Metal','Y')
        cyl('Vanity captured straight pull38R',(x,-.515,.80),.010,.16,'Metal','X')
    top=pill('Vanity single full-depth stone top38R',(0,.08,.96),(2.50,1.24,.08),'Ivory',.085)
    for x in [-.62,.62]:
        cut=cyl('Vanity true bowl aperture cutter38R',(x,-.12,.97),.285,.48,'Ivory');cut['export_ignore']=True;cut.hide_render=True;cut.hide_viewport=True
        mod=top.modifiers.new('True cutout through continuous stone38R','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
        # The original bowl stopped at a110 mm radius, around a48 mm drain:
        # an actual open annulus. This closed inner contour reaches the drain.
        rings=[]
        for z,r in [(.96,.28),(.92,.265),(.80,.21),(.74,.11),(.727,.044),(.727,.001)]:rings.append([(x+r*math.cos(j*math.tau/48),-.12+r*math.sin(j*math.tau/48),z) for j in range(48)])
        bowl=a.loft('Continuous recessed basin to drain38R',rings,'P38EIvory',cap=False);bowl.modifiers.new('Ceramic basin wall38R','SOLIDIFY').thickness=.012
        rp=[(.274,0),(.292,.002),(.292,.014),(.274,.016),(.274,0)]
        a.loft('Vanity actual annular ceramic rim38R',[[(x+r*math.cos(j*math.tau/48),-.12+r*math.sin(j*math.tau/48),.952+z) for j in range(48)] for r,z in rp],'P38EIvory',cap=False)
        cyl('Vanity seated drain flange38R',(x,-.12,.731),.046,.008)
        cyl('Vanity actual dark drain38R',(x,-.12,.736),.022,.004,'Dark')
        cyl('Vanity seated tap foot38R',(x,.22,1.009),.044,.022)
        curve('Vanity smoothly cast supported faucet38R',[(x,.22,1.008),(x,.22,1.20),(x,.13,1.27),(x,-.015,1.27),(x,-.06,1.22)],.020)
        cyl('Vanity faucet aerator38R',(x,-.06,1.215),.023,.020)
        cyl('Vanity retained tap control38R',(x+.12,.22,1.018),.031,.03)
        cyl('Vanity captured tap lever38R',(x+.12,.176,1.045),.009,.10,'Metal','Y')
        pill('Vanity supported soap body38R',(x+.34,.18,1.105),(.105,.11,.21),'Navy',.025)
        curve('Vanity soap pump retained spout38R',[(x+.34,.18,1.20),(x+.34,.18,1.26),(x+.23,.18,1.26)],.011)
    box('Vanity closed mirror-and-plumbing riser38R',(0,.68,1.64),(2.40,.062,1.30),'Navy',.008)
    if 'P38EMirror' not in a.MATS:a.mat('P38EMirror','B8C7CA',.08,1.0,0)
    for x in [-.62,.62]:
        pill('Vanity attached mirror frame38R',(x,.633,1.66),(1.01,.050,1.04),'Metal',.035)
        pill('Vanity seated polished mirror38R',(x,.606,1.66),(.95,.006,.98),'Mirror',.022)
        box('Vanity mirror lamp supported arm38R',(x,.632,2.205),(.60,.10,.025),'Metal',.006)
        pill('Vanity captured warm mirror optic38R',(x,.582,2.21),(.85,.07,.055),'Ivory',.016)
    note('S2E02','SM_AP_Vanity34','Fitted doors; closed carcass and mirror chase; fully formed drain bowls and seated hardware',before)

    c=active('SM_AP_Toilet34');before=bounds(c)
    for ob in c.objects:
        if ob.name.startswith('Molded toilet pedestal'):
            ob.data=ob.data.copy();me=ob.data
            verts=[tuple(v.co) for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons if not (len(p.vertices)>12 and all(abs(me.vertices[i].co.z-.36)<1e-4 for i in p.vertices))]
            mats=list(me.materials);fresh=bpy.data.meshes.new('Hollow supporting toilet pedestal38R');fresh.from_pydata(verts,[],faces);fresh.update();ob.data=fresh
            for m in mats:fresh.materials.append(m)
            for p in fresh.polygons:p.use_smooth=len(p.vertices)<12
    note('S2E03','SM_AP_Toilet34','Remove the solid pedestal cap occluding the real recessed bowl and water',before)

    c=active('SM_AP_Bakery36');before=bounds(c)
    for x in [-.865,.865]:
        cyl('Bakery real rear load upright38R',(x,.345,1.365),.016,.66)
        for z in [1.07,1.29,1.49]:
            box('Bakery captured full shelf bearer38R',(x, .08,z-.022),(.038,.56,.030),'Metal',.006)
            box('Bakery captive shelf mounting shoe38R',(x,.345,z-.040),(.060,.050,.10),'Metal',.006)
    # Cabinet identities belong to the fixed rail, not both moving leaves.
    for ob in c.objects:
        if ob.name.startswith('Bakery front identity plaque36'):
            ob.scale.z=.5;ob.location.z=.94-.46*.5;ob.location.y=-.066
        elif ob.type=='FONT' and ob.data.body=='FRESH BAKERY':ob.data=ob.data.copy();ob.data.size=.055;ob.location.z=.94;ob.location.y=-.493
    note('S2E04','SM_AP_Bakery36','Support all three shelves from base and move the identity plaque onto fixed transom',before)
    for aid,prefix,text in [('SM_AP_POS36','Retained order plaque36','ORDER & PAY'),('SM_AP_Tea36','Retained tea plaque36','TEA & HOT WATER')]:
        c=active(aid);before=bounds(c)
        for ob in c.objects:
            if ob.name.startswith(prefix):ob.scale.z=.6;ob.location.z=.94-.46*.6;ob.location.y=-.053
            elif ob.type=='FONT' and ob.data.body==text:ob.data=ob.data.copy();ob.data.size=.050;ob.location.z=.94;ob.location.y=-.493
        note('S2E04',aid,'Mount identification on fixed stone front rather than bridging both cabinet doors',before)

    c=active('SM_AP_TravelStorage38');before=bounds(c);remove(c,('Travel pillow shaped neck contour38',))
    for ob in c.objects:
        if ob.type=='FONT' and ob.data.body=='SERVICE KIT':ob.data=ob.data.copy();ob.data.body='TRAVEL KIT'
    for x in [-.37,.33]:
        rings=[];ts=[.38,.46,.55,.63]+[.63+j*(math.tau-1.26)/24 for j in range(1,24)]+[math.tau-.63,math.tau-.55,math.tau-.46,math.tau-.38]
        for i,t in enumerate(ts):
            f=[.015,.60,.88,1.0][min(i,len(ts)-1-i,3)]
            rings.append([(x+.15*math.cos(t)+.058*f*math.cos(k*math.tau/20)*math.cos(t),.15*math.sin(t)+.058*f*math.cos(k*math.tau/20)*math.sin(t),1.3675+.048+.048*f*math.sin(k*math.tau/20)) for k in range(20)])
        a.loft('Seated smoothly closed neck pillow38R',rings,'P38ESage')
    note('S2E05','SM_AP_TravelStorage38','Lower neck pillows13 mm onto shelves and round their closed tips',before)

    c=active('SM_AP_TableSetting36');before=bounds(c);remove(c,('Supported teaspoon handle36','Small spoon bowl36'))
    curve('Teaspoon resting on napkin and table38R',[(.10,-.19,.025),(.14,-.19,.025),(.238,-.19,.007)],.004)
    spin('Teaspoon bowl seated on table38R',(.25,-.19,0),[(.001,0),(.012,.001),(.019,.005),(.018,.007),(.001,.003)])
    for q in ctx.D['instances']:
        if q['asset']=='SM_AP_TableSetting36':ctx.move(q['name'],[q['location'][0],q['location'][1],.7735])
    note('S2E06','SM_AP_TableSetting36','Seat settings on actual .7725 tops and support spoon at napkin/table contacts',before)

    # Feet alone move: table tops, seat contours, characters and interaction
    # heights are preserved. Each adjusted pad still overlaps its support.
    feet=[('SM_AP_Sofa36','Sofa resilient floor pad36',.0125),('SM_AP_OvalTable36','Lounge table weighted foot36',.020),('SM_AP_CafeTable34','Weighted table base',.0075),('SM_AP_CafeChair34','Cafe chair resilient foot34',.0075),('SM_AP_Trolley','Trolley caster',.010),('SM_AP_Trolley','Trolley hub',.010),('SM_AP_Information27','Information station leveling foot27',.005)]
    feet_before={}
    for aid,prefix,dz in feet:
        c=active(aid);feet_before.setdefault(aid,bounds(c))
        for ob in c.objects:
            if ob.name.startswith(prefix):ob.location.z-=dz
    for aid,b in feet_before.items():note('S2E07',aid,'Seat actual resilient feet/casters on the floor without moving tops or seat shells',b)
    for aid,prefix in [('SM_AP_Bench27','Floor anchored seat shoe27'),('SM_AP_Bench29','Floor anchored seat shoe27'),('SM_AP_Bench34','Floor anchored foot')]:
        c=active(aid);before=bounds(c)
        for ob in c.objects:
            if not ob.name.startswith(prefix):continue
            ob.data=ob.data.copy();pts=[ob.matrix_world@v.co for v in ob.data.vertices];lo=min(p.z for p in pts);hi=max(p.z for p in pts);iv=ob.matrix_world.inverted()
            for v in ob.data.vertices:
                p=ob.matrix_world@v.co;p.z=hi+(p.z-hi)*hi/(hi-lo);v.co=iv@p
            ob.data.update()
        if aid=='SM_AP_Bench34':
            for x in [-.80,.80]:pill('Bench pedestal captured load-bearing shim38R',(x,.02,.07875),(.13,.30,.0125),'Metal',.012)
        note('S2E07',aid,'Extend shoe underside to floor while retaining top fixing height and supported seat geometry',before)

    c=active('SM_AP_RetainedCraft38');before=bounds(c)
    # A08 rear artwork is retained in front of exterior glazing; proper posts
    # carry it independently of the glass, with clamps behind the frame.
    for x in [-28.65,-26.55]:
        pill('A08 artwork grounded fixing shoe38R',(x,33.83,.025),(.18,.27,.05),'Metal',.025)
        box('A08 artwork supported rear post38R',(x,33.87,.85),(.055,.055,1.68),'Metal',.008)
        box('A08 artwork captured frame bracket38R',(x,33.88,1.59),(.12,.07,.18),'Metal',.008)
    for x,y in [(-21.9,9.3),(-30.5,26.5)]:
        for xx in [x-.52,x+.52]:
            for yy in [y-.16,y+.16]:pill('Lounge stowage grounded retained foot38R',(xx,yy,.022),(.06,.08,.044),'Rubber',.012)
    for ob in c.objects:
        if ob.name.startswith('Side-table floor shoe25'):ob.location.z-=.010
    note('S2E08','SM_AP_RetainedCraft38','Support A08 art independently of glazing, ground storage racks and foyer side-table shoe',before)
    for name,p in [('HandDryer24_1809',[-14.2,-8.9,1.1]),('Security camera24',[-39.2,9.91,2.85]),('Concourse camera24',[-26.09,9.6,3.02])]:
        old=ctx.require(name)['location'][:];ctx.move(name,p);repairs.append(dict(id='S2E09',actor=name,before_location=old,after_location=p,detail='Seat mounting rear against actual room inner wall face'))

    c=active('SM_AP_OperatorConsole36');before=bounds(c)
    remove(c,('Control monitor readable surface36',))
    for ob in list(c.objects):
        if ob.type=='FONT' and ob.data.body in ['LANE 01','LANE 02','SCANNING']:c.objects.unlink(ob)
    for x in [-.35,.35]:a.surface('Control monitor exact active UV face38R',(x,.143,1.53),(.54,.32),'Screen')
    note('S2E10','SM_AP_OperatorConsole36','Replace static painted monitor text with correctly UV-mapped active display faces',before)
    a.ACTIVE=None
    result=dict(applied=True,asset_ids=sorted(changed),findings=repairs,display_hook='native_equipment_displays38.apply_native(ctx)',runtime='equipment_displays38.install(G)',ignored='39 intentionally hidden conveyor contact helpers are not rendered props')
    ctx.D['repair38'][TAG]=result
    ctx.D['repair38']['equipment']['screen_roles38']={'Check-in desk 01':'Checkin','Check-in desk 02':'Checkin','Gate A07 boarding desk':'A07','Gate A08 boarding desk':'A08','Operations workstation24':'Operations','X-ray scanner 01':'Scanner','X-ray scanner 02':'Scanner','Security operator24 0':'ScreeningControl','Self-service kiosk24 0':'Checkin','Self-service kiosk24 1':'Checkin','Compact departures display':'Departures','Gate A07 flight display':'A07','Gate A08 flight display':'A08','Concourse departures board46':'Departures','Landside departures board46':'Departures','Arrivals reclaim board46':'Arrivals'}
    return result
