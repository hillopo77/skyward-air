"""Coherent full-size game airfield, shared geometry and flight-route contract."""
import math
from flight39_model import SURFACE,RUNWAY,TAXI_WIDTH,taxi_route,HOLD


def clip(poly,axis,limit,keep_greater):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ina=a[axis]>=limit-1e-9 if keep_greater else a[axis]<=limit+1e-9
        inb=b[axis]>=limit-1e-9 if keep_greater else b[axis]<=limit+1e-9
        if ina:out.append(a)
        if ina!=inb:
            t=(limit-a[axis])/(b[axis]-a[axis]);out.append([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t])
    return out


def ribbon(path,width):
    left=[];right=[]
    for i,p in enumerate(path):
        normals=[]
        for a,b in [(path[max(0,i-1)],p),(p,path[min(i+1,len(path)-1)])]:
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length>1e-8:normals.append([-dy/length,dx/length])
        nx=sum(n[0] for n in normals);ny=sum(n[1] for n in normals);length=math.hypot(nx,ny);nx/=length;ny/=length
        denom=max(.65,nx*normals[0][0]+ny*normals[0][1]);offset=width/2/denom
        left.append([p[0]+nx*offset,p[1]+ny*offset]);right.append([p[0]-nx*offset,p[1]-ny*offset])
    return left+right[::-1]


def pavement_polygons():
    taxi=clip(clip(ribbon(taxi_route(),TAXI_WIDTH),0,90,True),0,RUNWAY['centre_x']-RUNWAY['width']/2,False)
    return [dict(id='apron',polygon=[[-14,-130],[90,-130],[90,88],[-14,88]],top=SURFACE),
            dict(id='taxi_alpha',polygon=taxi,top=SURFACE),
            dict(id='runway36',polygon=[[277.5,-2290],[322.5,-2290],[322.5,310],[277.5,310]],top=SURFACE)]


def plan(ctx):
    D=ctx.D
    remove=[]
    for q in list(D['instances']):
        aid=q['asset'];x,y,z=q['location']
        if aid in {'SM_AP_Airfield34','SM_AP_RunwayLight','SM_AP_Runway18','SM_AP_Runway36'} or (aid in {'SM_AP_Asphalt','SM_AP_Marking','SM_AP_YellowMarking'} and x>0):
            remove.append(q['name']);ctx.remove(q['name'])
    D['flight39']=dict(revision=39,surface_z=SURFACE,stand=[16,17.3,0],runway=dict(RUNWAY),
        taxi_width=TAXI_WIDTH,taxi_route=taxi_route(),hold_short=HOLD[:],pavement_polygons=pavement_polygons(),
        ground_support_assets=['SM_AP_F39Pavement','SM_AP_F39FieldExtension'],
        retired_instances=remove,carrier='Flight39 Aircraft carrier',
        gameplay_model='Integrated local civil-flight approximation, not an engineering simulator',
        reference='https://www.boeing.com/content/dam/boeing/boeingdotcom/commercial/airports/acaps/767_REV_K.pdf',
        reference_scope='45m runway and23m taxiway turnpath scale;2600m length is this game level choice')
    # Public navigation continues to use bounded rooms and physical pavement.
    D['floors']=[q for q in D['floors'] if q['name'] not in {'Apron','Service ramp','Level boarding bridge'}]
    D['cameras'].append(dict(name='F39_RunwayOverview',eye=[360,370,90],target=[300,-600,0],fov=72,stage=10))
    return D['flight39']


def _slab(a,name,poly,top,depth,mat):
    # One true top face per continuous pavement footprint; clipped taxi/apron/
    # runway touch at their actual boundaries rather than stacked top faces.
    area=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(poly,poly[1:]+poly[:1]))
    if area<0:poly=poly[::-1]
    n=len(poly);vs=[(x,y,top-depth) for x,y in poly]+[(x,y,top) for x,y in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=a.mesh(name,vs,fs,mat)
    for f in ob.data.polygons:f.use_smooth=False
    return ob


def _paint(a,name,p,q,width,mat='F39White',z=SURFACE+.012):
    dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy)
    if length<.001:return
    o=a.box(name,(0,0,z),(length,width,.004),mat,0);o.location=((p[0]+q[0])/2,(p[1]+q[1])/2,0);o.rotation_euler.z=math.atan2(dy,dx)


def build(ctx):
    a,D=ctx.a,ctx.D
    for n,h,r,metal,e in [('Asphalt','45565A',.96,0,0),('Apron','929D96',.94,0,0),('Shoulder','717D72',.98,0,0),
                         ('Field','70885E',1.,0,0),('White','E4E4CF',.91,0,0),('Gold','D8B55B',.86,0,0),
                         ('Blue','3C83B2',.45,0,1.6),('Green','81B28C',.52,0,1.5),('Red','C86F57',.58,0,1.4),
                         ('Metal','80908C',.71,.25,0),('Navy','263F45',.80,0,0)]:a.mat('F39'+n,h,r,metal,e)
    def surfaces():
        for q in pavement_polygons():_slab(a,'Continuous '+q['id']+' pavement39',q['polygon'],SURFACE,.18,'F39Apron' if q['id']=='apron' else 'F39Asphalt')
        for x0,x1 in [(270,277.5),(322.5,330)]:_slab(a,'Runway load shoulder39',[[x0,-2290],[x1,-2290],[x1,310],[x0,310]],SURFACE-.020,.18,'F39Shoulder')
    a.asset('F39Pavement',surfaces,'complex');ctx.add('F39Pavement','Flight39 coherent physical apron taxiway runway',[0,0,0],flight39_ground=True)
    def extension():
        def height(x,y):
            hx=-3.7*max(0,min(1,(x+14)/5));hy=-3.7*max(0,min(1,(y-18)/35)) if x>=-20 else 0
            return min(hx,hy)-.08
        for xs,ys in [([-200,-80,-70,-62,-49,-20,-18.5,-15.5,-14,-9,0,200,350,500],[-2600,-800]),([350,500],[-800,800])]:
            vs=[(x,y,height(x,y)) for y in ys for x in xs];nx=len(xs)
            ob=a.mesh('Non-overlapping graded field extension39',vs,[(i,i+1,nx+i+1,nx+i) for i in range(nx-1)],'F39Field')
            for f in ob.data.polygons:f.use_smooth=False
    a.asset('F39FieldExtension',extension,'complex');ctx.add('F39FieldExtension','Flight39 extended graded airfield',[0,0,0],flight39_ground=True)
    def markings():
        # Genuine runway-scale paint, restrained simple materials and spaced
        # modeled frangible optics; no dense thin bright railing fields.
        for x in (278.0,322.0):_paint(a,'Runway continuous edge39',[x,-2287],[x,307],.30)
        for y in range(-2250,280,50):_paint(a,'Runway30m centre dash39',[300,y],[300,y+30],.90)
        for end,direction,label in [(310,-1,'36'),(-2290,1,'18')]:
            y=end+direction*12
            for side in (-1,1):
                for j in range(6):a.box('Threshold piano key39',(300+side*(3.0+j*2.6),y+direction*15,SURFACE+.012),(1.8,30,.004),'F39White',0)
            a.font(label,(300,end+direction*64,SURFACE+.013),9.,'F39White',(0,0,math.pi if direction<0 else 0))
            for side in (-1,1):a.box('Aiming point39',(300+side*9.5,end+direction*300,SURFACE+.012),(5.5,32,.004),'F39White',0)
        path=taxi_route()
        for p,q in zip(path,path[1:]):
            if p[0]<278 and q[0]<278:_paint(a,'Taxi Alpha guided centre39',p,q,.18,'F39Gold',SURFACE+.016)
        for y in (HOLD[1]-.45,HOLD[1]):_paint(a,'Hold short solid39',[108.5,y],[131.5,y],.15,'F39Gold')
        for y in (HOLD[1]+.45,HOLD[1]+.9):
            for x in range(109,132,2):_paint(a,'Hold short broken39',[x,y],[x+.9,y],.15,'F39Gold')
        for y in range(-2280,301,60):
            for x in (276.5,323.5):
                a.cyl('Inset runway optic foundation39',(x,y,SURFACE+.028),.12,.056,'F39Metal')
                a.cyl('Frangible runway optic neck39',(x,y,SURFACE+.12),.025,.13,'F39Metal')
                a.cyl('Rounded runway edge optic39',(x,y,SURFACE+.21),.055,.06,'F39White')
        for x in range(280,321,5):
            for y,m in [(309,'F39Green'),(-2289,'F39Red')]:a.cyl('Threshold/end optic39',(x,y,SURFACE+.055),.065,.08,m)
        for x in (105,135):
            a.box('Hold-short sign joined casing39',(x,140,SURFACE+.63),(2.8,.17,.70),'F39Navy',.035)
            for xx in (x-.95,x+.95):a.cyl('Hold sign frangible support39',(xx,140,SURFACE+.27),.045,.50,'F39Metal')
            a.font('A1  |  36',(x,139.905,SURFACE+.64),.25,'F39Gold')
    a.asset('F39Markings',markings,'none');ctx.add('F39Markings','Flight39 runway taxi markings and optics',[0,0,0],collision=False)
    D['flight39']['modelled_runway_m']=[45,2600];D['flight39']['modelled_aircraft_m']=[45.336328,52.14]
    D['flight39']['surface_contact']='10 existing tyre bottoms at-3.689; actual new pavement also-3.689'
    return D['flight39']
