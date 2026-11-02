"""Pure metre-space cabin volumes derived from the actual aircraft manifest."""
import math

CONTACT_TOLERANCE_M=.03


def pressure_envelope(data,offset=16.):
    layout=data['layout'];translated=data.get('airport38_translation')
    centre=float(translated['offset'][0] if translated else offset);shift=0. if translated else centre
    ceiling=float(layout['ceiling_max_inner_height_m'])
    def interior_faces(prefix,default):
        walls=[q for q in data.get('navigation_bounds',[]) if q['name'].startswith(prefix)]
        left=[q['location'][0]+shift+q['size'][0]/2 for q in walls if q['location'][0]+shift<centre]
        right=[q['location'][0]+shift-q['size'][0]/2 for q in walls if q['location'][0]+shift>centre]
        return [max(left) if left else centre-default,min(right) if right else centre+default]
    half=float(layout['interior_width_m'])/2
    cabin=interior_faces('COL_CabinSide',half)
    cockpit=interior_faces('COL_CockpitSide',half)
    cells=[dict(name='Cabin deck',rect=[*cabin,float(layout['crew_room'][0]),float(layout['rear_service_end_y_m'])],
                floor=0.,ceiling=ceiling,provenance='layout interior_width/crew_room/rear_service_end/ceiling + navigation side-wall inner faces'),
           dict(name='Cockpit deck',rect=[*cockpit,float(layout['cockpit_front_y_m']),float(layout['crew_room'][0])],
                floor=0.,ceiling=ceiling,provenance='layout cockpit_front/ceiling + navigation cockpit side-wall inner faces')]
    for q in layout['navigation_floors']:
        if q['name'] not in ('Forward lower cargo hold','Lower cargo stair'):continue
        rect=list(q['rect']);rect[:2]=[x+shift for x in rect[:2]]
        cell=dict(name=q['name'],rect=rect,provenance='layout navigation_floors '+q['name'])
        if 'slope' in q:
            cell.update(slope=dict(q['slope']),ceiling=ceiling)
            if cell['slope'].get('axis')=='x':
                for key in ('from','to'):cell['slope'][key]+=shift
        else:
            floor=float(q['height']);cell.update(floor=floor,ceiling=floor+float(layout['cargo_hold_clear_m'][2]))
        cells.append(cell)
    if len(cells)!=4:raise ValueError('Flight39 requires the actual cabin, cockpit, hold and stair floor metadata')
    return dict(cells=cells,contact_tolerance_m=CONTACT_TOLERANCE_M,source='Revision18 layout + navigation_bounds',centre_x=centre)


def cell_interval(cell,x,y,tolerance):
    x0,x1,y0,y1=cell['rect']
    if not(x0<=x<=x1 and y0<=y<=y1):return None
    floor=cell.get('floor')
    if floor is None:
        s=cell['slope'];value=x if s['axis']=='x' else y
        t=max(0.,min(1.,(value-s['from'])/(s['to']-s['from'])))
        floor=s['start']+(s['end']-s['start'])*t
    return floor-tolerance,cell['ceiling']+tolerance


def contains_point(envelope,p):
    x,y,z=p;tol=envelope['contact_tolerance_m']
    return any(interval and interval[0]<=z<=interval[1] for interval in
               (cell_interval(cell,x,y,tol) for cell in envelope['cells']))


def contains_box(envelope,bounds):
    """Conservative complete box coverage, including gaps between floor cells.

    Partition at real floor boundaries. On each horizontal partition the floor
    is linear, so endpoint and midpoint interval checks cover slopes and union
    seams; checking only eight corners could miss a structural-deck gap.
    """
    lo,hi=bounds
    def axis_values(axis):
        cuts={lo[axis],hi[axis]}
        for cell in envelope['cells']:
            for edge in cell['rect'][axis*2:axis*2+2]:
                if lo[axis]<edge<hi[axis]:cuts.add(edge)
        ordered=sorted(cuts)
        return ordered+[(a+b)/2 for a,b in zip(ordered,ordered[1:])]
    tol=envelope['contact_tolerance_m']
    for x in axis_values(0):
        for y in axis_values(1):
            intervals=sorted(i for i in (cell_interval(c,x,y,tol) for c in envelope['cells']) if i)
            covered=lo[2]
            for a,b in intervals:
                if a>covered+1e-8:break
                covered=max(covered,b)
                if covered>=hi[2]-1e-8:break
            if covered<hi[2]-1e-8:return False
    return True


def box_polygon_overlap(bounds,polygon):
    """SAT intersection of a source XY box and the convex authored bridge deck."""
    lo,hi=bounds;box=[(x,y) for x in (lo[0],hi[0]) for y in (lo[1],hi[1])]
    axes=[(1.,0.),(0.,1.)]+[(b[1]-a[1],a[0]-b[0]) for a,b in zip(polygon,polygon[1:]+polygon[:1])]
    for ax,ay in axes:
        if abs(ax)+abs(ay)<1e-10:continue
        a=[p[0]*ax+p[1]*ay for p in box];b=[p[0]*ax+p[1]*ay for p in polygon]
        if max(a)<min(b)-1e-8 or max(b)<min(a)-1e-8:return False
    return True


def bridge_overlap(bounds,zones):
    for zone in zones:
        floor=float(zone.get('height',zone.get('z',0.)))
        # The same walkable column used by existing bridge pawn occupancy.
        # Baggage under the apron is not occupying an elevated walkway.
        if bounds[1][2]<floor-.03 or bounds[0][2]>floor+3.4:continue
        if box_polygon_overlap(bounds,zone['polygon']):return True
    return False


def boarding_threshold_overlap(bounds,crossing):
    rect=crossing['inside'];lo,hi=bounds
    return lo[0]<float(crossing['threshold']) and lo[1]<=rect[3] and hi[1]>=rect[2] and hi[2]>=-.03 and lo[2]<=3.4
