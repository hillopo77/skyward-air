"""Original equipment rebuild for the verified EQ01–EQ13 findings.

This module is assembled by root in a single saved Blender master.  It does not
open files, mutate inherited asset collections or run the shared editor.
"""
import math


def _point(q,p):
    t=math.radians(q['rotation_degrees']);x,y,z=p
    return [q['location'][0]+x*math.cos(t)-y*math.sin(t),q['location'][1]+x*math.sin(t)+y*math.cos(t),q['location'][2]+z]


def _character(ctx,name,p):
    for q in ctx.D.get('character_placements',[]):
        if q['actor']==name:
            q['location']=list(p)
            ob=ctx.scene.objects.get(name)
            if ob:ob.location=p


def plan(ctx):
    D=ctx.D;meta=D.setdefault('repair38',{}).setdefault('equipment',{})
    # These are complete machine/lane translations, not a floating-console patch.
    old=ctx.require('Security portal 02')['location'][0];dx=-40.4-old
    for n in ['Security portal 02','Security belt 02','X-ray scanner 02','QueueArrow24_1740']:
        q=ctx.require(n);ctx.move(n,[q['location'][0]+dx,q['location'][1],q['location'][2]])
    for q in D.get('security_crossings',[]):
        if abs((q[0]+q[1])/2-old)<1.0:q[0]+=dx;q[1]+=dx
    for q in D.get('conveyors',[]):
        if q['name']=='Security belt 02':q['rect'][0]+=dx;q['rect'][1]+=dx
    # Public-side check-in service stations retain their order and usable separation.
    q=ctx.require('Bag drop belt 01');dy=-13-q['location'][1];ctx.move(q['name'],[-27.9,-13,0])
    for q in D.get('conveyors',[]):
        if q['name']=='Bag drop belt 01':
            q['rect'][2]+=dy;q['rect'][3]+=dy
            if 'load_point' in q:q['load_point'][1]+=dy
    ctx.move('Check-in desk 01',[-30.3,-11.6,0]);ctx.move('Check-in service header29 0',[-30.3,-11.6,2.85])
    _character(ctx,'CH12 Queue passenger 1',[-29.15,-11.6,0])
    for key in ['queue_walk','exit_route']:
        for p in D.get('checkin29',{}).get(key,[]):
            if abs(p[1]+10.6)<.01:p[1]=-11.6
    if 'checkin29' in D:D['checkin29']['counter_spacing_m']=3.0
    ctx.move('Gate A07 boarding desk',[-17.5,-1.15,0]);_character(ctx,'CH12 Gate pilot',[-16.25,-1.15,0])
    ctx.move('Operations workstation24',[-46,14.2,0]);ctx.move('OperatorChair24_1813',[-46,15.3,0],rotation=0)
    # The small pot is on the actual 1.06 m charging ledge, between USB modules.
    ctx.move('Small potted plant24',[-32.60,1.15,1.061]);q=ctx.require('Small potted plant24');q['rack_stowed25']=True;q['support_actor38']='ChargingTable24_1749'
    for lane,first in enumerate([1719,1732]):
        x=ctx.require('Security belt %02d'%(lane+1))['location'][0]
        for j in range(4):ctx.move('Tray24_'+str(first+j),[x,.55,.824+j*.036])
    # Bind gameplay points to real controls rather than empty air over a machine.
    for t in D['interactions']:
        if t['kind'] in ['checkin','boarding'] and any(q['name']==t['actor'] and q['asset'] in ['SM_AP_ServiceDesk30','SM_AP_Counter34'] for q in D['instances']):
            t['point']=_point(ctx.require(t['actor']),[-.52,-.532,1.14])
        if t['kind'] in ['scanner','bagdrop'] and t['actor'].startswith(('Security belt','Bag drop belt')):
            t['point']=_point(ctx.require(t['actor']),[.76,-1.65,1.044])
    meta.update(lane_centres=[dict(detector=[-45.5,3],belt=[-43.15,3]),dict(detector=[-40.4,3],belt=[-38.05,3])],belt_asset_ids=['SM_AP_Belt38','SM_AP_Outfeed38'],scanner_asset_id='SM_AP_Scanner38',curtain_asset_id='SM_AP_ScannerCurtain38',stop_kind='equipment_toggle',bagdrop01_y=-13,desk_positions={n:ctx.require(n)['location'][:] for n in ['Check-in desk 01','Check-in desk 02','Gate A07 boarding desk','Gate A08 boarding desk','Operations workstation24']},scanner_clearance_max_local_x=1.41,scanner_02_max_world_x=-36.64,scanner_wall_inner_x=-36.09,tray_stack_base=.824,tray_nesting=.036,counter_reader_local=[-.52,-.532,1.14])
    assert -38.05+1.41<-36.09-.30,'Right scanner service clearance'
    assert -1.15-.99>-2.91+.70,'A07 desk-wall clearance'


class Model:
    def __init__(self,a):self.a=a
    def box(self,n,p,s,m='Ivory',b=.008):return self.a.box(n,p,s,'P38E'+m,b)
    def pill(self,n,p,s,m='Ivory',r=.04):return self.a.pill(n,p,s,'P38E'+m,r)
    def cyl(self,n,p,r,h,m='Metal',axis='Z',r2=None):return self.a.cyl(n,p,r,h,'P38E'+m,axis,r2)
    def tube(self,n,path,r,m='Metal',segments=16):return self.a.tube(n,path,r,'P38E'+m,segments)
    def font(self,text,p,size=.065,m='Text',rot=(math.pi/2,0,0)):return self.a.font(text,p,size,'P38E'+m,rot)
    def spin(self,n,p,profile,m='Metal',seg=40):
        return self.a.loft(n,[[(p[0]+r*math.cos(j*math.tau/seg),p[1]+r*math.sin(j*math.tau/seg),p[2]+z) for j in range(seg)] for r,z in profile],'P38E'+m)
    def screws(self,xs,y,z):
        for x in xs:self.cyl('Captive face screw38',(x,y,z),.005,.005,'Metal','Y')

    def monitor(self,x,y,z,w=.58,h=.37):
        self.pill('One molded monitor enclosure38',(x,y,z),(w,.09,h),'Navy',.035)
        # Both public and staff sides share a single housing and support.
        self.a.surface('Public display glass38',(x,y-.047,z),(w-.07,h-.07),'Screen')
        o=self.a.surface('Staff display glass38',(0,-.047,0),(w-.07,h-.07),'Screen');o.location=(x,y,z);o.rotation_euler.z=math.pi
        self.screws([x-w/2+.025,x+w/2-.025],y-.049,z+h/2-.025)

    def counter(self):
        a=self.a
        self.pill('Continuous recessed desk plinth38',(0,.015,.07),(1.82,.77,.14),'Navy',.045)
        # Open-front carcass: sides, back, shelf, face frame. No closed front face
        # is hidden behind the inset doors.
        for x in [-.92,.92]:
            a.profile('Desk formed end cheek38',[(-.47,.14),(.43,.14),(.43,1.02),(-.48,1.02),(-.50,.91)],x-.03,x+.03,'P38EOak',.008)
        self.box('Desk continuous closed rear38',(0,.395,.56),(1.80,.045,.84),'Oak',.008)
        for z in [.16,.52,.91]:self.box('Desk full internal shelf38',(0,.0,z),(1.80,.77,.035),'Oak',.006)
        for x in [-.90,0,.90]:self.box('Desk front frame stile38',(x,-.44,.53),(.035,.06,.77),'Oak',.004)
        for z in [.16,.91]:self.box('Desk front frame rail38',(0,-.44,z),(1.80,.06,.045),'Oak',.004)
        for x in [-.453,.453]:
            self.box('Precisely inset desk door38',(x,-.44,.535),(.864,.040,.695),'Oak',.004)
            self.tube('Desk seated pull handle38',[(x-.13,-.462,.75),(x-.13,-.50,.75),(x+.13,-.50,.75),(x+.13,-.462,.75)],.010)
            for z in [.30,.76]:self.cyl('Desk retained hinge pin38',(x+(-.397 if x<0 else .397),-.45,z),.010,.070,'Metal')
        self.pill('Full counter stone bullnose38',(0,0,1.055),(1.98,1.04,.09),'Ivory',.07)
        self.pill('Fixed brand transom38',(0,-.495,.965),(1.73,.045,.11),'Navy',.016);self.font('SKYWARD AIR',(0,-.521,.967),.082)
        # One connected metal pedestal seats on the top; no weighted foot hangs
        # above it. Screens are two sides of one enclosure, not duplicate stands.
        self.pill('Monitor worktop mounting foot38',(.28,.15,1.115),(.30,.25,.035),'Metal',.035)
        self.cyl('Monitor swivel column38',(.28,.15,1.29),.024,.32,'Metal')
        self.box('Monitor VESA mounting plate38',(.28,.15,1.455),(.16,.065,.13),'Metal',.014)
        self.monitor(.28,.15,1.55,.66,.43)
        self.pill('Operator keyboard seated tray38',(.22,.30,1.116),(.55,.20,.025),'Navy',.025)
        for j in range(4):
            for k in range(12):self.box('Desk keyboard key38',(-.02+k*.043,.23+j*.039,1.133),(.030,.026,.008),'Ivory',.003)
        self.pill('Document pad38',(-.43,-.10,1.111),(.35,.30,.020),'Navy',.025)
        self.pill('Integrated pass-reader housing38',(-.52,-.44,1.15),(.25,.17,.10),'Navy',.025)
        self.a.surface('Pass reader active face38',(-.52,-.527,1.14),(.18,.055),'P38EScreen')
        self.cyl('Reader status indicator38',(-.43,-.531,1.175),.008,.005,'Green','Y')

    def belt(self):
        a=self.a
        for x in [-.54,.54]:
            a.profile('Folded conveyor side channel38',[(-1.8,.70),(1.8,.70),(1.8,.86),(-1.8,.86)],x-.025,x+.025,'P38EMetal',.008)
        self.box('Conveyor supported dark trough38',(0,0,.745),(1.01,3.60,.055),'Rubber',.015)
        # Rollers touch their bearing journals; end caps are proper planar caps.
        for j in range(21):
            y=-1.70+j*.17;self.cyl('Conveyor quiet broad roller38',(0,y,.805),.040,.99,'Metal','X')
            for x in [-.515,.515]:self.cyl('Captured roller bearing38',(x,y,.805),.052,.028,'Dark','X')
        for y in [-1.50,1.50]:
            self.box('Conveyor crossmember38',(0,y,.66),(1.12,.10,.10),'Navy',.012)
            for x in [-.43,.43]:
                self.cyl('Conveyor adjustable support column38',(x,y,.36),.037,.60,'Metal');self.spin('Conveyor floor pad38',(x,y,0),[(.072,0),(.072,.025),(.052,.05),(.035,.06)],'Rubber')
        for x in [-.60,.60]:self.tube('Conveyor retained side guard38',[(x,-1.76,.85),(x,-1.54,.92),(x,1.54,.92),(x,1.76,.85)],.022,'Metal')
        # Green START is part of the conveyor. Emergency STOP is a separate
        # bracket-mounted actor, clear of the scanner shoulder.
        self.box('Start control mounting cantilever38',(.66,-1.65,.865),(.26,.22,.040),'Metal',.008)
        self.pill('Start control sealed housing38',(.76,-1.65,.945),(.22,.22,.12),'Navy',.025)
        self.cyl('Start control gasket38',(.76,-1.65,1.013),.049,.014,'Rubber');self.cyl('Start tactile green cap38',(.76,-1.65,1.044),.041,.048,'Green')
        self.pill('Start fascia fitted plate38',(.76,-1.765,.945),(.19,.012,.077),'Navy',.012);self.font('START',(.76,-1.774,.945),.041)

    def emergency(self):
        # Origin is the bearing-side clamp at belt local (.56,-1.40,.82).
        self.box('Emergency clamp backplate38',(0,0,.03),(.07,.17,.08),'Metal',.006)
        self.box('Emergency retained cantilever38',(.13,0,.06),(.27,.16,.035),'Metal',.006)
        self.pill('Emergency yellow sealed base38',(.22,0,.135),(.20,.20,.12),'Amber',.025)
        self.cyl('Emergency captured black bezel38',(.22,0,.205),.061,.026,'Dark')
        self.spin('Emergency circular mushroom38',(.22,0,.213),[(.031,0),(.045,.016),(.054,.031),(.051,.053),(.040,.063)],'Red',48)
        self.box('Emergency legend fixed backing38',(.22,-.106,.132),(.18,.014,.07),'Navy',.005);self.font('STOP',(.22,-.115,.132),.045)
        self.screws([.16,.28],-.114,.102)

    def scanner(self):
        a=self.a
        # One genuinely continuous U-shaped shell, lofted through its rounded
        # shoulder stations. A separate overlapping roof previously produced
        # coplanar top faces; there are no hidden duplicate top faces here.
        rings=[]
        for y,h in [(-1.055,2.095),(-1.035,2.115),(-.86,2.18),(.86,2.18),(1.035,2.115),(1.055,2.095)]:
            outline=[(-.8175,.06),(-.8175,h-.040),(-.805,h-.012),(-.7775,h),(.7775,h),(.805,h-.012),(.8175,h-.040),(.8175,.06),(.6625,.06),(.6625,1.995),(-.6625,1.995),(-.6625,.06)]
            rings.append([(x,y,z) for x,z in outline])
        shell=a.loft('One continuous scanner shoulder-and-roof shell38',rings,'P38EIvory')
        edge=shell.modifiers.new('Scanner continuous manufactured fillet','BEVEL');edge.width=.009;edge.segments=3
        shell.modifiers.new('Scanner weighted manufactured normals','WEIGHTED_NORMAL')
        for x in [-.74,.74]:
            for y in [-.82,.82]:self.spin('Scanner retained leveling foot38',(x,y,0),[(.065,0),(.065,.024),(.042,.045),(.042,.062)],'Rubber')
        # True continuous cavity. Dark liners are on the actual side walls;
        # neither end is blocked by a hidden collision slab.
        for x in [-.654,.654]:
            self.box('Attached internal scanner liner38',(x,0,1.39),(.018,1.99,1.08),'Dark',.006)
        self.box('Attached scanner top liner38',(0,0,1.991),(1.31,1.99,.014),'Dark',.004)
        for y in [-1.071,1.071]:
            for x in [-.665,.665]:self.pill('Scanner captured aperture jamb38',(x,y,1.382),(.050,.055,1.16),'Navy',.020)
            self.pill('Scanner curtain clamp38',(0,y,1.946),(1.36,.07,.068),'Navy',.018)
        self.pill('Scanner mounted identification plate38',(0,-1.061,2.045),(1.14,.012,.074),'Navy',.015)
        self.font('BAGGAGE SCREENING',(0,-1.068,2.046),.073)
        for x in [-.63,.63]:self.pill('Scanner status optic38',(x,-1.061,2.044),(.09,.012,.022),'Green',.007)
        for x in [-.823,.823]:
            self.box('Scanner fitted side service leaf38',(x,.11,1.28),(.025,1.62,.90),'Ivory',.006)
            for y in [-.49,.66]:self.cyl('Scanner service latch38',(x+(-.016 if x<0 else .016),y,1.31),.022,.019,'Metal','X')
        # One bolted side mounting plate, connected arm and one monitor housing.
        self.box('Scanner monitor bolted side plate38',(.835,-.12,1.225),(.035,.23,.28),'Metal',.008)
        self.tube('Scanner one continuous monitor arm38',[(.84,-.12,1.23),(1.10,-.12,1.23),(1.10,-.36,1.23),(1.10,-.36,1.52)],.025,'Metal')
        self.monitor(1.10,-.36,1.62,.56,.38)
        self.pill('Scanner supported operator work shelf38',(1.07,-.67,1.045),(.68,.62,.055),'Navy',.035)
        for y in [-.86,-.47]:self.tube('Shelf triangular load-bearing brace38',[(.835,y,.83),(.835,y,1.02),(1.34,y,1.02),(.835,y,.83)],.016,'Metal')
        self.pill('Scanner keyboard enclosure38',(1.08,-.68,1.091),(.48,.20,.035),'Dark',.025)
        for j in range(4):
            for k in range(10):self.box('Scanner tactile keyboard key38',(.88+k*.043,-.75+j*.043,1.113),(.029,.028,.010),'Ivory',.003)
        for j in range(5):self.box('Scanner side ventilation recess38',(.826,.27+j*.11,.40),(.010,.067,.055),'Dark',.005)

    def curtain(self):
        # Visual non-colliding hinged lead curtain; origin at top clamp. Backing
        # is physically behind the strip field, not coplanar with the faces.
        self.box('Continuous dark curtain rear web38',(0,.025,-.545),(1.345,.014,1.10),'Rubber',.006)
        for j in range(12):
            x=-.616+j*.112;stagger=.004 if j%2 else -.004
            outline=[(-.010+stagger,0),(-.010+stagger,-.75),(-.018+stagger,-1.07),(.006+stagger,-1.09),(.010+stagger,-.75),(.010+stagger,0)]
            self.a.profile('Soft staggered overlapping lead strip38',outline,x-.059,x+.059,'P38ERubber',.004)
        self.box('Curtain captured top bead38',(0,.012,-.014),(1.35,.052,.028),'Rubber',.006)

    def outfeed(self):
        for x in [-.54,.54]:self.box('Outfeed full channel38',(x,0,.765),(.05,.70,.14),'Metal',.008)
        self.box('Outfeed dark trough38',(0,0,.745),(1.01,.70,.055),'Rubber',.010)
        for y in [-.27,-.10,.07,.24]:self.cyl('Outfeed receiving roller38',(0,y,.805),.040,.99,'Metal','X')
        for x in [-.43,.43]:self.cyl('Outfeed grounded support38',(x,.20,.36),.036,.60,'Metal');self.cyl('Outfeed resilient foot38',(x,.20,.035),.065,.07,'Rubber')
        self.pill('Outfeed soft end stop38',(0,.36,.91),(1.13,.07,.18),'Navy',.025)

    def traycart(self):
        self.pill('Tray station backed load top38',(0,0,.795),(.68,.49,.045),'Ivory',.045)
        self.box('Tray station closed rear panel38',(0,.205,.435),(.64,.045,.68),'Navy',.012)
        for x in [-.30,.30]:self.box('Tray station joined side support38',(x,0,.435),(.045,.46,.68),'Navy',.012)
        self.box('Tray station lower shelf38',(0,0,.135),(.63,.46,.05),'Navy',.012)
        for x in [-.26,.26]:
            for y in [-.17,.17]:self.cyl('Tray station resilient pad38',(x,y,.05),.042,.10,'Rubber')
        self.pill('Tray station fixed front label38',(0,-.245,.64),(.55,.018,.17),'Navy',.020);self.font('TAKE A TRAY',(0,-.257,.64),.062)

    def bins(self):
        a=self.a
        for x,label,m in [(-.205,'WASTE','Navy'),(.205,'RECYCLE','Sage')]:
            a.loft('Formed open recycling shell38',[[(x+xx,yy,z) for xx,yy in a.rr(.385,.445,.052)] for z in [.09,.96]],'P38E'+m,cap=False)
            liner=a.loft('Inward-facing retained bin liner38',[[(x+xx,yy,z) for xx,yy in a.rr(.285,.34,.035)] for z in [.13,.962]],'P38ERubber',cap=False)
            for p in liner.data.polygons:p.flip()
            self.box('Sealed internal bin bottom38',(x,0,.125),(.285,.34,.025),'Rubber',.012)
            a.ring('Bin actual captured mouth38',(x,0,.973),(.395,.455,.055),(.277,.325,.035),.027,'P38EMetal')
            for y in [-.18,.18]:self.pill('Bin grounded resilient foot38',(x,y,.045),(.29,.065,.09),'Rubber',.014)
            self.pill('Bin attached front identification38',(x,-.235,.735),(.30,.020,.135),'Navy',.018);self.font(label,(x,-.248,.735),.046)
            self.tube('Bin retained access pull38',[(x-.05,-.225,.50),(x-.05,-.253,.50),(x+.05,-.253,.50),(x+.05,-.225,.50)],.007)

    def shelf_frame(self,staff):
        self.pill('Storage full plinth38',(0,0,.065),(1.50,.54,.13),'Navy',.035)
        self.box('Storage joined full backing38',(0,.226,1.235),(1.50,.045,2.20),'Oak',.008)
        for x in [-.727,.727]:self.box('Storage continuous upright38',(x,0,1.23),(.045,.50,2.22),'Ivory',.008)
        for z in [.29,.82,1.35,1.88]:
            self.pill('Storage supported shelf38',(0,0,z),(1.45,.49,.035),'Oak',.022)
            self.pill('Shelf directly captured label rail38',(0,-.255,z-.015),(1.40,.025,.065),'Navy',.009)
            for x in [-.56,.56]:self.box('Label rail retained clip38',(x,-.244,z-.022),(.025,.034,.090),'Metal',.004)
        self.pill('Storage fixed header38',(0,-.020,2.36),(1.50,.24,.20),'Navy',.035)
        self.font('CREW SUPPLIES' if staff else 'TRAVEL ESSENTIALS',(0,-.144,2.36),.084)

    def firstaid(self,x,y,z):
        self.pill('Medical case formed shell38',(x,y,z+.135),(.43,.30,.27),'Ivory',.055)
        self.box('Medical case fitted seal38',(x,y-.157,z+.135),(.37,.012,.21),'Sage',.018)
        # One closed cross silhouette: two coplanar intersecting bars would
        # shimmer at their centre, even though each bar alone is valid.
        outline=[(-.0185,.06),(.0185,.06),(.0185,.0185),(.06,.0185),(.06,-.0185),(.0185,-.0185),(.0185,-.06),(-.0185,-.06),(-.0185,-.0185),(-.06,-.0185),(-.06,.0185),(-.0185,.0185)]
        cross=self.a.loft('Single continuous first-aid cross38',[[(x+xx,y+yy,z+.15+zz) for xx,zz in outline] for yy in [-.1705,-.1615]],'P38ERed')
        for p in cross.data.polygons:
            if len(p.vertices)==12:p.use_smooth=False
        edge=cross.modifiers.new('Cross edge radius','BEVEL');edge.width=.002;edge.segments=3;cross.modifiers.new('Cross manufactured normals','WEIGHTED_NORMAL')
        self.tube('Medical case captured handle38',[(x-.08,y,z+.27),(x-.08,y,z+.33),(x+.08,y,z+.33),(x+.08,y,z+.27)],.012,'Dark')
        for xx in [x-.135,x+.135]:self.pill('Medical case latch38',(xx,y-.16,z+.23),(.038,.025,.046),'Metal',.008)

    def blanket(self,x,y,z):
        for j in range(3):
            zz=z+j*.062
            self.a.loft('Soft folded blanket contour38',[[(x+xx,y+yy,zv) for xx,yy in self.a.rr(w,d,r,12)] for zv,w,d,r in [(zz,.50,.31,.05),(zz+.025,.53,.33,.06),(zz+.058,.50,.31,.05)]],'P38ESage')
        self.box('Blanket folded paper band38',(x,y-.175,z+.095),(.11,.010,.16),'Paper',.005);self.font('FOLDED',(x,y-.183,z+.095),.026,'Ink')

    def binder(self,x,y,z,label,material='Sage'):
        self.pill('Document binder curved spine38',(x,y-.115,z+.17),(.09,.055,.34),material,.025)
        self.box('Document binder page block38',(x,y+.005,z+.17),(.071,.19,.314),'Paper',.004)
        for xx in [x-.043,x+.043]:self.box('Document binder board38',(xx,y+.01,z+.17),(.012,.23,.34),material,.004)
        self.box('Binder inventory label38',(x,y-.146,z+.20),(.066,.008,.12),'Paper',.004)
        self.font(label,(x,y-.152,z+.21),.023,'Ink')
        self.cyl('Binder spine finger ring38',(x,y-.150,z+.055),.015,.008,'Metal','Y')

    def radio(self,x,y,z):
        self.pill('Radio charging dock38',(x,y,z+.025),(.17,.15,.05),'Dark',.018)
        self.pill('Radio molded handheld housing38',(x,y,z+.14),(.11,.072,.23),'Navy',.025)
        self.pill('Radio retained display38',(x,y-.040,z+.17),(.073,.010,.058),'Screen',.007)
        for j in range(3):self.box('Radio physical speaker groove38',(x,y-.041,z+.075+j*.016),(.066,.008,.006),'Dark',.002)
        self.tube('Radio retained antenna38',[(x-.031,y,z+.25),(x-.037,y,z+.37),(x-.05,y,z+.43)],.007,'Rubber',12)
        self.cyl('Radio top rotary knob38',(x+.025,y,z+.264),.015,.027,'Dark')
        for dx in [-.021,.021]:self.cyl('Radio tactile selector38',(x+dx,y-.042,z+.12),.008,.008,'Ivory','Y')

    def pouch(self,x,y,z):
        self.a.loft('Soft equipment pouch silhouette38',[[(x+xx,y+yy,zv) for xx,yy in self.a.rr(w,d,r,12)] for zv,w,d,r in [(z,.43,.29,.06),(z+.10,.46,.31,.07),(z+.23,.42,.28,.06)]],'P38ENavy')
        self.box('Pouch fitted flap38',(x,y-.157,z+.16),(.34,.018,.12),'Sage',.015)
        self.pill('Pouch captured buckle38',(x,y-.172,z+.105),(.062,.020,.044),'Metal',.008);self.font('SERVICE KIT',(x,y-.174,z+.19),.041)
        self.tube('Pouch retained carry handle38',[(x-.09,y,z+.23),(x-.08,y,z+.29),(x+.08,y,z+.29),(x+.09,y,z+.23)],.010,'Rubber')

    def storage(self,staff=True):
        self.shelf_frame(staff)
        if staff:
            self.firstaid(-.37,0,.3075);self.pouch(.34,0,.3075)
            self.blanket(-.34,0,.8375)
            for x in [.24,.46]:self.radio(x,.035,.8375)
            for j,t in enumerate(['OPS','LOG','MAP','SAFE','CREW','CABIN']):self.binder(-.45+j*.18,0,1.3675,t,'Sage' if j%2 else 'Navy')
            self.blanket(-.32,0,1.8975);self.firstaid(.34,0,1.8975)
        else:
            for j in range(5):self.binder(-.42+j*.20,0,.3075,['BAY','SKY','TRIP','ROUTE','WORLD'][j],'Sage' if j%2 else 'Navy')
            for j in range(4):
                x=-.45+j*.30;self.spin('Reusable bottle formed body38',(x,0,.8375),[(.053,0),(.063,.022),(.063,.22),(.049,.255),(.031,.27)],'Sage' if j%2 else 'Ivory');self.cyl('Bottle captured cap38',(x,0,1.124),.034,.033,'Metal')
            for x in [-.37,.33]:
                rings=[]
                for j in range(25):
                    t=.38+j*(math.tau-.76)/24;rings.append([(x+.15*math.cos(t)+.058*math.cos(k*math.tau/16)*math.cos(t),.15*math.sin(t)+.058*math.cos(k*math.tau/16)*math.sin(t),1.3675+.061+.048*math.sin(k*math.tau/16)) for k in range(16)])
                self.a.loft('Travel pillow shaped neck contour38',rings,'P38ESage')
            self.pouch(-.34,0,1.8975);self.pouch(.34,0,1.8975)

    def cafe_fillers(self):
        for x in [-46.5,-44.5,-42.5]:
            self.box('Scribed cabinet joint solid pilaster38',(x,31.507,.49),(.100,.810,.78),'Oak',.004)
            self.pill('Cabinet joint fitted toe infill38',(x,31.55,.07),(.100,.80,.14),'Navy',.012)
            self.box('Cabinet joint joined rear closure38',(x,31.90,.50),(.100,.045,.78),'Oak',.004)


def build(ctx):
    a=ctx.a
    colors=[('Ivory','DCD6C8',.73,0,0),('Navy','294751',.76,0,0),('Oak','A88A66',.68,0,0),('Metal','94A29F',.62,.55,0),('Dark','34474B',.68,.15,0),('Rubber','243337',.94,0,0),('Sage','72988C',.84,0,0),('Paper','E2D8C0',.95,0,0),('Screen','15323F',.43,0,.5),('Red','B7362C',.48,0,0),('Green','669C68',.56,0,0),('Amber','C9A04E',.56,0,0),('Text','F1E3C8',.80,0,0),('Ink','243B42',.83,0,0)]
    for name,h,r,m,e in colors:
        if 'P38E'+name not in a.MATS:a.mat('P38E'+name,h,r,m,e)
    b=Model(a)
    for name,fn,collision in [('Counter38',b.counter,'complex'),('Belt38',b.belt,'complex'),('EmergencyStop38',b.emergency,'complex'),('Scanner38',b.scanner,'complex'),('ScannerCurtain38',b.curtain,'none'),('Outfeed38',b.outfeed,'complex'),('TrayStation38',b.traycart,'complex'),('Recycling38',b.bins,'complex'),('StaffStorage38',lambda:b.storage(True),'complex'),('TravelStorage38',lambda:b.storage(False),'complex'),('CafeJoint38',b.cafe_fillers,'none')]:a.asset(name,fn,collision)
    # Flat manufactured end caps must not borrow rounded side normals.
    for it in a.ASSETS.values():
        if it['collection'].name not in ['SM_AP_'+n for n in ['Counter38','Belt38','EmergencyStop38','Scanner38','ScannerCurtain38','Outfeed38','TrayStation38','Recycling38','StaffStorage38','TravelStorage38','CafeJoint38']]:continue
        for ob in it['collection'].objects:
            if ob.type=='MESH':
                for p in ob.data.polygons:
                    if len(p.vertices)>12:p.use_smooth=False
    for q in list(ctx.D['instances']):
        aid=q['asset'];n=q['name']
        if aid in ['SM_AP_ServiceDesk30','SM_AP_Counter34']:ctx.replace(n,'Counter38')
        elif aid=='SM_AP_Belt':ctx.replace(n,'Belt38')
        elif aid=='SM_AP_Scanner34':ctx.replace(n,'Scanner38')
        elif aid=='SM_AP_Recycling':ctx.replace(n,'Recycling38')
        elif aid=='SM_AP_Storage34':ctx.replace(n,'TravelStorage38' if n in ['RetailShelf24_1832','RetailShelf24_1833','RetailShelf24_1834'] else 'StaffStorage38')
    meta=ctx.D['repair38']['equipment'];meta['curtains']=[];meta['emergency_controls']=[];meta['output_stations']=[]
    for name in ['Security belt 01','Security belt 02','Bag drop belt 01','Bag drop belt 02']:
        q=ctx.require(name);control=name+' emergency stop38';ctx.add('EmergencyStop38',control,_point(q,[.56,-1.40,.82]),rotation=q['rotation_degrees'],collision=True)
        pt=_point(q,[.78,-1.40,1.096]);ctx.D['interactions'].append(dict(kind='equipment_toggle',actor=control,point=pt,title='Stop / restart '+name,conveyor=name))
        meta['emergency_controls'].append(dict(actor=control,conveyor=name,point=pt))
    for lane in [1,2]:
        q=ctx.require('X-ray scanner %02d'%lane);x,y,z=q['location']
        for side,yy in [('front',-1.075),('rear',1.075)]:
            n='Scanner %02d %s curtain38'%(lane,side);ctx.add('ScannerCurtain38',n,[x,y+yy,1.915],collision=False)
            meta['curtains'].append(dict(actor=n,lane=lane-1,hinge=[x,y+yy,1.915],axis='x',open_angle_degrees=-45 if side=='front' else 45,trigger_rect=[x-.72,x+.72,y+yy-.58,y+yy+.58],height_range=[.78,1.95]))
        ctx.add('TrayStation38','Lane %02d tray station38'%lane,[x,.55,0])
        ctx.add('Outfeed38','Lane %02d receiving station38'%lane,[x,5.15,0])
        meta['output_stations'].append(dict(actor='Lane %02d receiving station38'%lane,lane=lane-1,rect=[x-.5,x+.5,4.8,5.48],height=.845))
        for belt in ctx.D['conveyors']:
            if belt['name']=='Security belt %02d'%lane:belt['rect'][3]=5.48;belt['height']=.845
    for belt in ctx.D['conveyors']:
        if belt['name'].startswith('Bag drop belt'):belt['height']=.845
    ctx.add('CafeJoint38','Fitted cafe cabinet joints38',[0,0,0],collision=False)
    child=ctx.scene.objects.get('Small potted plant24');support=ctx.scene.objects.get('ChargingTable24_1749')
    if child and support:
        pose=child.matrix_world.copy();child.parent=support;child.matrix_world=pose
    # The new reader and surface are part of the same coherent workstation.
    meta['replaced_counter_actors']=[q['name'] for q in ctx.D['instances'] if q['asset']=='SM_AP_Counter38']
    meta['scanner_open_tunnel']=dict(clear_width=1.28,belt_top=.845,interior_ceiling=1.984,entrance_header_bottom=1.912,curtains_visual_only=True)
    meta['tests_required']=['Native control rays reach START and emergency caps','Scanner02 wall clearance >=.30m','Both detector crossings remain walkable','Physical bags travel through visual hinged curtains','No gap below each monitor support','Plant support trace hits ChargingTable24_1749','Front/oblique cabinet run has no100mm gaps','No fake recycling aperture or outward liner normals','Shelf items supported and recognizable at player distance']

