"""Pure policy/geometry shared by the native runtime and isolated assertions."""
import math


def in_rect(p,r,pad=0.):return r[0]-pad<=p[0]<=r[1]+pad and r[2]-pad<=p[1]<=r[3]+pad


def in_polygon(p,polygon):
    # Boundary inclusive: two joined walk surfaces have no 1-frame void seam.
    x,y=p[:2];inside=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];cross=(x-a[0])*dy-(y-a[1])*dx
        if abs(cross)<1e-7 and min(a[0],b[0])-1e-7<=x<=max(a[0],b[0])+1e-7 and min(a[1],b[1])-1e-7<=y<=max(a[1],b[1])+1e-7:return True
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def door_access(spec,state,locked=False,inside=False):
    if locked and not inside:return False
    requirement=spec.get('access24')
    return not requirement or bool(state.get(requirement,False))


def auto_target(spec,state,distance_cm,locked=False,inside=False):
    return float(door_access(spec,state,locked,inside) and distance_cm<430)


def receiver_complete(position,receiver,supported,speed,held=False):
    return bool(not held and position[0]>=receiver['receive_x'] and in_rect(position,receiver['rect'])
                and receiver['height']+.015<position[2]<receiver['height']+1.35 and supported and speed<20)


def legal_screening(held,scanned,registered):
    return not held or held in scanned or held in registered


def floor_candidates(x,y,feet,floors,movables=None,extra=None):
    out=[];movables=movables or {}
    for q in list(floors)+list(extra or []):
        if 'rect' in q and not in_rect((x,y),q['rect'],.005):continue
        if 'polygon' in q and not in_polygon((x,y),q['polygon']):continue
        req=q.get('requires_open')
        if req and movables.get(req,{}).get('progress',0)<.90:continue
        slope=q.get('slope')
        if slope:
            coord=x if slope.get('axis','y')=='x' else y
            d=slope['to']-slope['from']
            if abs(d)<1e-6:raise ValueError('Zero length floor slope: '+q['name'])
            t=max(0,min(1,(coord-slope['from'])/d));h=slope['start']+(slope['end']-slope['start'])*t
        else:h=float(q.get('height',q.get('z',0)))
        distance=abs(h-feet)
        if distance<=q.get('max_step',.30):out.append((q.get('priority',10),distance,h,q['name']))
    return sorted(out,key=lambda q:(-q[0],q[1]))


def choose_floor(x,y,feet,floors,movables=None,extra=None):
    candidates=floor_candidates(x,y,feet,floors,movables,extra)
    return (candidates[0][2],candidates[0][3]) if candidates else (None,'No supported walk surface')


def traversal(previous,current,rect,armed,max_step):
    """Complete south→north walk, rejecting fly-in/teleport/side entry."""
    x0,x1,y0,y1=rect
    if math.dist(previous[:2],current[:2])>max_step or not 1.25<current[2]<2.1:return False,False
    x,y=current[:2]
    if not x0<x<x1 or y<y0-.10:return False,False
    if previous[1]<=y0<y:armed=True
    if armed and previous[1]<=y1<y:return False,True
    return armed,False


def carousel_geometry(instance):
    """Exact sampled slat rings from airport_model.carousel / Carousel34.

    The original outer/inner round-rectangle outlines use matching corner
    samples. Their average is the actual centre of every slat, and the placed
    instance's nonuniform scale is essential to derive its world path.
    """
    def rr(w,d,r):
        pts=[]
        for cx,cy,a in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
            for j in range(21):
                t=math.radians(a+j*90/20);pts.append([cx+r*math.cos(t),cy+r*math.sin(t)])
        return pts
    angle=math.radians(instance['rotation_degrees']);c,s=math.cos(angle),math.sin(angle)
    sx,sy=instance.get('scale',[1,1,1])[:2];x,y=instance['location'][:2]
    def pose(p):
        xx,yy=p[0]*sx,p[1]*sy
        return [x+xx*c-yy*s,y+xx*s+yy*c]
    out,inside=rr(9.6,3.6,1.75),rr(7.4,1.4,.67)
    mid=[[(a[0]+b[0])/2,(a[1]+b[1])/2] for a,b in zip(out,inside)]
    return dict(outer=[pose(p) for p in out],inner=[pose(p) for p in inside],path=[pose(p) for p in mid],
                source='Carousel34 cloned annular slats; matching84sample outlines',height=.415*instance.get('scale',[1,1,1])[2]+instance['location'][2])


def carousel_tangent(position,geometry):
    if not in_polygon(position,geometry['outer']) or in_polygon(position,geometry['inner']):return None
    path=geometry['path'];best=None
    for a,b in zip(path,path[1:]+path[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];length2=dx*dx+dy*dy
        if length2<1e-12:continue
        t=max(0,min(1,((position[0]-a[0])*dx+(position[1]-a[1])*dy)/length2))
        q=[a[0]+dx*t,a[1]+dy*t];distance=(position[0]-q[0])**2+(position[1]-q[1])**2
        if best is None or distance<best[0]:
            length=math.sqrt(length2);best=(distance,q,[dx/length,dy/length])
    return dict(point=best[1],tangent=best[2],distance_m=math.sqrt(best[0])) if best else None
