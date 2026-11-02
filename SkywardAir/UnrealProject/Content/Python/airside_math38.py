"""Pure source-metre geometry shared by authoring, native validation and runtime."""
import math

OFFSET = (16.0, 0.0, 0.0)
L1 = 'Aircraft door 1L'
PIVOT = (-12.1, .675)
ELBOW = (-1.5, -3.6)
NOSE_CAB = (10.5, .675)
THRESHOLD = (13.916, .675)
ORIGINAL_BOUNDS = ((-22.668164, -8.76, -3.434), (22.668164, 43.38, 7.8))
BODY_AIRCRAFT_BOUNDS = ((-6.668164, -8.76, -3.434), (38.668164, 43.38, 7.8))
# Complete deployed aircraft includes rolling gear, not just the exterior body.
# Contact39 preserves wheel diameters and seats its tyres on the visible apron.
AIRCRAFT_BOUNDS = ((-6.668164, -8.76, -3.689), (38.668164, 43.38, 7.8))
SLEEVE_LENGTH = 3.36
COUNTS = (4, 5)

def lerp(a,b,t): return a+(b-a)*t
def smooth(t): return t*t*(3-2*t)
def clamp(t): return max(0.,min(1.,t))
def length(a,b): return math.hypot(b[0]-a[0],b[1]-a[1])
def angle(a,b): return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
def add(p,d): return tuple(p[i]+d[i] for i in range(len(p)))
def along(p,a,d):
    r=math.radians(a)
    return (p[0]+d*math.cos(r),p[1]+d*math.sin(r))
def world(p,origin,a):
    r=math.radians(a);c,s=math.cos(r),math.sin(r)
    return (origin[0]+p[0]*c-p[1]*s,origin[1]+p[0]*s+p[1]*c,*p[2:])
def rectangle(start,end,width):
    a=math.radians(angle(start,end));dx=-math.sin(a)*width/2;dy=math.cos(a)*width/2
    return [[start[0]+dx,start[1]+dy],[end[0]+dx,end[1]+dy],
            [end[0]-dx,end[1]-dy],[start[0]-dx,start[1]-dy]]
def in_polygon(p,poly):
    x,y=p[:2];inside=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        cross=(x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross)<1e-8 and min(a[0],b[0])-1e-8<=x<=max(a[0],b[0])+1e-8 and min(a[1],b[1])-1e-8<=y<=max(a[1],b[1])+1e-8:return True
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside
def hull(points):
    p=sorted(set(tuple(x) for x in points))
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for q in p:
        while len(lower)>=2 and cross(lower[-2],lower[-1],q)<=0:lower.pop()
        lower.append(q)
    for q in reversed(p):
        while len(upper)>=2 and cross(upper[-2],upper[-1],q)<=0:upper.pop()
        upper.append(q)
    return lower[:-1]+upper[:-1]
def chamber_polygon(incoming,outgoing,width=2.85,cut=1.14):
    pts=[]
    for ang,d in ((incoming,-cut),(outgoing,cut)):
        p=along((0,0),ang,d);r=math.radians(ang)
        pts += [(p[0]-math.sin(r)*width/2,p[1]+math.cos(r)*width/2),
                (p[0]+math.sin(r)*width/2,p[1]-math.cos(r)*width/2)]
    return hull(pts)
def polygon_zone(name,poly,z=0,**extra):
    return dict(name=name,rect=[min(q[0] for q in poly),max(q[0] for q in poly),min(q[1] for q in poly),max(q[1] for q in poly)],polygon=poly,z=z,**extra)
def apron_height(x,y):
    hx=-3.7*clamp((x+14)/5)
    hy=-3.7*clamp((y-18)/35) if x>=-20 else 0.
    base=min(hx,hy)-.08
    # Actual34 poured apron panels sit 91mm above the underlying terrain mesh.
    if 4.01<x<75.99 and -33.99<y<73.99:base=max(base,-3.689)
    # The38 ground-equipment parking bay is an authored load-bearing pad.
    if -12.5<x<-9.5 and 53.5<y<82:base=max(base,-3.7)
    return base

def bridge_pose(stowed=0.):
    """Retract banks first, then pivot the complete contracted bridge south.

    All moving parts, including bend chambers, cab, bellows and trucks, use
    these poses. No dock furniture is left at the aircraft when retracted.
    """
    t=clamp(stowed);retract=smooth(clamp(t/.6));turn=smooth(clamp((t-.6)/.4))
    a0=angle(PIVOT,ELBOW);b0=angle(ELBOW,NOSE_CAB)
    a=lerp(a0,-90,turn);b=lerp(b0,-90,turn)
    la=lerp(length(PIVOT,ELBOW),SLEEVE_LENGTH,retract)
    lb=lerp(length(ELBOW,NOSE_CAB),SLEEVE_LENGTH,retract)
    j=along(PIVOT,a,la);end=along(j,b,lb)
    ca=lerp(0,-90,turn)
    poses={}
    for bank,(origin,ang,dist,count) in enumerate(((PIVOT,a,la,4),(j,b,lb,5))):
        step=(dist-SLEEVE_LENGTH)/(count-1)
        for i in range(count):
            p=along(origin,ang,step*i)
            poses['Bridge38 bank %s sleeve %02d'%('A' if bank==0 else 'B',i)]=dict(location=[*p,0],rotation=ang)
    poses['Bridge38 elbow chamber']=dict(location=[*j,0],rotation=b-b0)
    poses['Bridge38 docking cab']=dict(location=[*end,0],rotation=ca)
    for name,p in [('A',j),('B',end)]:
        ground=apron_height(*p)
        # Align the wheeled carrier with the graded apron, rather than placing
        # four coplanar wheels half underground on the terminal-side slope.
        eps=.002
        sx=(apron_height(p[0]+eps,p[1])-apron_height(p[0]-eps,p[1]))/(2*eps)
        sy=(apron_height(p[0],p[1]+eps)-apron_height(p[0],p[1]-eps))/(2*eps)
        ang=a if name=='A' else b;r=math.radians(ang)
        normal=[-sx,-sy,1.];nn=math.sqrt(sum(x*x for x in normal));normal=[x/nn for x in normal]
        forward=[math.cos(r),math.sin(r),sx*math.cos(r)+sy*math.sin(r)]
        poses['Bridge38 %s truck'%name]=dict(location=[*p,ground],rotation=ang,ground_normal=normal,forward=forward)
        # Hydraulic lift column modeled to a one-metre datum, scaled to ground.
        base=[p[0]+normal[0]*.34,p[1]+normal[1]*.34,ground+normal[2]*.34]
        poses['Bridge38 %s lift'%name]=dict(location=base,rotation=0,scale=[1,1,max(.1,-.20-base[2])])
    return poses

def floor_polygons():
    # Each deck spans only its bank. The fitted joint overlaps 8mm vertically,
    # so no same-plane duplicated carpet is exported.
    zones=[polygon_zone('Bridge38 terminal neck',rectangle((-14,.675),PIVOT,2.50))]
    zones += [polygon_zone('Bridge38 bank A',rectangle(PIVOT,ELBOW,2.46)),
              polygon_zone('Bridge38 bank B',rectangle(ELBOW,NOSE_CAB,2.26)),
              polygon_zone('Bridge38 docking cab',rectangle(NOSE_CAB,THRESHOLD,2.50))]
    for name,centre,aa,bb in [('pivot',PIVOT,0,angle(PIVOT,ELBOW)),
                              ('elbow',ELBOW,angle(PIVOT,ELBOW),angle(ELBOW,NOSE_CAB)),
                              ('cab mitre',NOSE_CAB,angle(ELBOW,NOSE_CAB),0)]:
        poly=[[centre[0]+p[0],centre[1]+p[1]] for p in chamber_polygon(aa,bb)]
        zones.append(polygon_zone('Bridge38 '+name,poly,.008))
    return zones

def source_box_corners(lo,hi):
    return [[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
def posed_bounds(bounds,pose):
    local=[[p[i]*pose.get('scale',[1,1,1])[i] for i in range(3)] for p in source_box_corners(*bounds)]
    if pose.get('ground_normal'):
        x=pose['forward'];n=math.sqrt(sum(t*t for t in x));x=[t/n for t in x];z=pose['ground_normal']
        y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
        points=[[pose['location'][i]+p[0]*x[i]+p[1]*y[i]+p[2]*z[i] for i in range(3)] for p in local]
    else:
        points=[world(p,pose['location'],pose['rotation']) for p in local]
        points=[[p[0],p[1],p[2]+pose['location'][2]] for p in points]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
def intersects(a,b,margin=0.):
    return all(a[0][i]-margin<b[1][i] and b[0][i]-margin<a[1][i] for i in range(3))
def swept_bounds(distance=180.):
    lo,hi=AIRCRAFT_BOUNDS
    return [[lo[0],lo[1]-distance,lo[2]],[hi[0],hi[1],hi[2]]]
def validate_sweep(obstacles,distance=180.,margin=.25):
    sweep=swept_bounds(distance)
    hits=[dict(name=q['name'],bounds=q['bounds']) for q in obstacles if intersects(sweep,q['bounds'],margin)]
    return dict(clear=not hits,method='conservative complete-aircraft AABB swept continuously along source -Y',distance_m=distance,margin_m=margin,swept_bounds=sweep,blocking=hits)
