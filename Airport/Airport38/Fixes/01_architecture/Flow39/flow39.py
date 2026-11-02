"""Five architectural construction/refinement passes on the CURRENT saved source.

No file I/O, editor launch, baseline reset or aircraft/equipment mutation. Root
calls apply(ctx) once and exports the returned asset IDs. evidence_callback(ctx,
pass_record) is optional and allows a read-only test harness to capture each pass.
"""
import math
import sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import architecture38 as core

TAG = 'architecture_flow39_v1'
M = 'P39F'
STRUCTURAL = ('Floors38', 'Ceilings38', 'Roofs38', 'Walls38', 'Glazing38')


def _reuse(ctx, short, collision='complex'):
    """Clear only an explicitly owned derived kit, preserving its collection ID."""
    import bpy
    aid = 'SM_AP_' + short
    col = bpy.data.collections.get(aid)
    if col is None:
        col = ctx.new_collection(short, collision)
    else:
        for ob in list(col.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        ctx.a.ASSETS[aid] = dict(collection=col, collision=collision)
        ctx.a.ACTIVE = col
    return col


def _register(ctx, aid, collision='complex'):
    import bpy
    c = bpy.data.collections.get(aid)
    if c:
        ctx.a.ASSETS[aid] = dict(collection=c, collision=collision)
    return c


def _materials(a):
    for suffix, color, rough, metal in [
        ('Oak', 'AC8158', .63, 0), ('Navy', '243F4B', .71, 0),
        ('Teal', '5D9290', .82, 0), ('Metal', '758B8C', .49, .30), ('Frame', '758B8C', .49, .30),
        ('Gold', 'D9B66D', .60, .12), ('Stone', 'C9BEA5', .76, 0),
        ('Text', 'F0E6CC', .72, 0), ('Rubber', '304747', .9, 0),
    ]:
        if M + suffix not in a.MATS:
            a.mat(M + suffix, color, rough, metal)


def _frame_box(ax, k, l, h, z0, z1, depth=.08):
    return ((l, h, k-depth/2, k+depth/2, z0, z1) if ax == 'x' else
            (k-depth/2, k+depth/2, l, h, z0, z1))


def _merge_panes(panes):
    """Union matching pane intervals before making either glass or frame pieces."""
    groups = defaultdict(list)
    for s, z0, z1 in panes:
        if z1-z0 > .05:
            key = (s['axis'], round(s['k'], 6), round(z0, 6), round(z1, 6))
            groups[key].append((s['l'], s['h']))
    result = []
    for (ax, k, z0, z1), intervals in sorted(groups.items()):
        merged = []
        for lo, hi in sorted(intervals):
            if merged and lo <= merged[-1][1] + 1e-6:
                merged[-1][1] = max(hi, merged[-1][1])
            else:
                merged.append([lo, hi])
        result += [(ax, k, lo, hi, z0, z1) for lo, hi in merged]
    return result


def _shell(ctx):
    """Remodel whole-shell solid occupancy, including EVERY unequal roof step.

    All wall/plenum/slab solids are unioned BEFORE owner splitting. Glazing frame
    construction uses a second exact union, so adjacent/corner mullions cannot
    retain overlaid faces. We do not put additional boxes over the old shell.
    """
    import bpy
    a, D = ctx.a, ctx.D
    for name in STRUCTURAL:
        _reuse(ctx, name)
    cs = core.cells(D['zones'])
    solids, panes, steps = [], [], []
    for c in cs:
        r = tuple(c['rect'])
        fm = ('Carpet' if c['zone'].startswith('gate') else
              'WCStone' if c['zone'] in {'amenities', 'baggageservice'} else 'Stone')
        solids.extend([(r+(-.14, 0), ('Floors38', fm)),
                       (r+(c['ceiling'], c['ceiling']+.16), ('Ceilings38', 'Ceiling')),
                       (r+(c['roof'], c['roof']+.18), ('Roofs38', 'Roof'))])
    zones = {z['id']: z for z in D['zones']}
    def solid(ax, k, l, h, z0, z1, material, depth=.18):
        if h-l > 1e-6 and z1-z0 > 1e-6:
            solids.append((_frame_box(ax, k, l, h, z0, z1, depth), ('Walls38', material)))
    segments = core.wall_segments(D)
    for s in segments:
        panels, glass = core.wall_panels(D, s)
        ids, ax, k = s['members'], s['axis'], s['k']
        exterior_glazed = s['exterior'] and (
            ('entrancefoyer' in ids and ax == 'y' and k == -49) or
            ('cafe' in ids and (k == -49 if ax == 'y' else k == 34)) or
            ('gate08' in ids and (k == -24 if ax == 'y' else k == 34)) or
            ('gate07' in ids and (k == -14 if ax == 'y' else k == 10)) or
            ('arrivals' in ids and ax == 'y' and k == -14))
        for l, h, z0, z1 in panels:
            if exterior_glazed and z0 >= 1.005-1e-6 and z1-z0 > .2:
                panes.append((dict(s, l=l, h=h), z0, z1-.12))
                solid(ax, k, l, h, z1-.12, z1, 'Frame')
            else:
                mat = ('Rubber' if z1 <= .101 else 'Sage' if z1 <= .941 and 'security' in ids else
                       'Navy' if z1 <= .941 else 'Oak' if z1 <= 1.006 else 'Cream')
                if ax == 'y' and k == -26 and 'checkin' in ids and z0 >= 1.005:
                    mat = 'Oak'
                solid(ax, k, l, h, z0, z1, mat)
        for l, h, z0, z1 in glass:
            panes.append((dict(s, l=l, h=h), z0, z1))
        heights = [zones[i]['ceiling_m'] for i in ids]
        if s['exterior'] or max(heights)-min(heights) > 1e-6:
            # This shared boundary is exterior ABOVE the lower roof. It used to
            # be incorrectly excluded merely because two floor owners touch.
            solid(ax, k, s['l'], s['h'], s['H']+.16, s['H']+.36, 'Roof')
            if not s['exterior']:
                steps.append(dict(axis=ax, k=k, interval=[s['l'], s['h']],
                                  z=[s['H']+.16, s['H']+.36], members=ids))
    # Retain the exact useful WC pocket/cubicle dimensions and leaf clearances.
    for x in (-21, -17.1):
        for ax, k, l, h in [('y', x-1.6, -7.05, -3.3), ('y', x+1.6, -7.05, -3.3),
                           ('x', -3.3, x-1.6, x+1.6), ('x', -7.05, x-1.6, x-.54),
                           ('x', -7.05, x+.54, x+1.6)]:
            solid(ax, k, l, h, 0, 2.8, 'Cream', .14)
            solid(ax, k, l, h, .015, .10, 'Rubber', .15)
        solid('x', -7.05, x-.54, x+.54, 2.17, 2.8, 'Cream', .14)
        solids.append(((x+.56, x+1.78, -7.175, -7.065, -.005, 2.205), ('Walls38', 'Cream')))
    # Previously separate attachment fascias become part of the actual union.
    # Their north heads fit behind the opaque transom, not over its visible face.
    solids.extend([((-41.07, -40.93, 16.09, 34.0, 4.56, 6.68), ('Walls38', 'Ceiling')),
                   ((-41.07, -40.93, 16.09, 33.91, 6.68, 6.8), ('Walls38', 'Ceiling'))])
    attachment = bpy.data.collections.get('SM_AP_Attachments38')
    removed = []
    if attachment:
        for o in list(attachment.objects):
            if o.name.startswith('Gallery dining soffit closed'):
                removed.append(o.name)
                bpy.data.objects.remove(o, do_unlink=True)
        _register(ctx, attachment.name)
    shell = core._solid_union(a, solids, split_owners=True)
    frame_boxes = []
    merged = _merge_panes(panes)
    for ax, k, l, h, z0, z1 in merged:
        for z in (z0, z1):
            frame_boxes.append((_frame_box(ax, k, l-.027, h+.027, z-.026, z+.026), ('Glazing38', 'Frame')))
        count = max(1, math.ceil((h-l)/4.5))
        for j in range(count+1):
            c = l+(h-l)*j/count
            frame_boxes.append((_frame_box(ax, k, c-.027, c+.027, z0, z1), ('Glazing38', 'Frame')))
    a.ACTIVE = a.ASSETS['SM_AP_Glazing38']['collection']
    frames = core._solid_union(a, frame_boxes, split_owners=True)
    for o in frames:
        o.name = 'Single welded perimeter frame39'
        o['construction'] = 'Exact global frame union; shared corners and transoms emitted once'
    for ax, k, l, h, z0, z1 in merged:
        # Recess each glass edge into its actual frame channel by 12mm.
        core._line(a, 'Recessed continuous exterior glass39', ax, k, l+.015, h-.015,
                   z0+.015, z1-.015, 'Glass', .022, 0)
    D['wall_segments24'] = segments
    D['repair38']['ceiling_coverage'] = cs
    D['repair38']['whole_shell_union'] = dict(method='Exact whole-shell union39 including shared roof steps',
        input_solids=len(solids), exposed_faces=sum(len(o.data.polygons) for o in shell),
        buried_faces_removed=True, roof_steps=steps)
    return dict(id=1, name='Structural reconstruction', roof_steps=steps,
                shell_input_solids=len(solids), frame_input_solids=len(frame_boxes),
                welded_frame_objects=len(frames), merged_panes=len(merged),
                removed_attachment_fascias=removed,
                findings=['AT11', 'AT12', 'AT08_integrated'])


def _specs(D):
    """Architectural scales are deliberately different, while sectioning remains."""
    return [
        dict(id='WelcomeCheckin', axis='y', k=-43, c=-15, w=2.6, H=2.8,
             left=.30, right=.30, depth=.28, material='Oak', role='warm wide check-in arrival'),
        dict(id='A07', axis='y', k=-26, c=4, w=3.8, H=3.12,
             left=.32, right=.32, depth=.26, material='Oak', role='broad lounge opening'),
        dict(id='A08', axis='x', k=14, c=-29, w=4.8, H=3.12,
             left=.44, right=.18, depth=.24, material='Navy', role='wide asymmetric north lounge'),
        dict(id='Cafe', axis='y', k=-32, c=12, w=3.6, H=3.12,
             left=.14, right=.43, depth=.27, material='Oak', role='hospitality reveal on turn'),
        dict(id='Recovery', axis='y', k=-32, c=6.5, w=3.2, H=3.4,
             left=.20, right=.20, depth=.22, material='Navy', role='open circulation release'),
        dict(id='WC', axis='y', k=-26, c=-3, w=1.8, H=2.8,
             left=.16, right=.16, depth=.21, material='Metal', role='quiet recessed amenity entrance'),
    ]


def _world(s, u, depth, z):
    return (u, s['k']+depth, z) if s['axis'] == 'x' else (s['k']+depth, u, z)


def _curve(s, inset=0):
    """Continuous floor-to-floor U reveal path; gentle true quarter arcs."""
    left = s['c']-s['w']/2-inset
    right = s['c']+s['w']/2+inset
    H = s['H']+inset
    rl, rr = s['left']+inset, s['right']+inset
    points = [(left, -.005), (left, H-rl)]
    for i in range(1, 13):
        angle = math.pi-i*math.pi/24
        points.append((left+rl+rl*math.cos(angle), H-rl+rl*math.sin(angle)))
    points.append((right-rr, H))
    for i in range(1, 13):
        angle = math.pi/2-i*math.pi/24
        points.append((right-rr+rr*math.cos(angle), H-rr+rr*math.sin(angle)))
    points.append((right, -.005))
    return points


def _extruded_profile(a, name, s, polygon, d0, d1, material):
    k = len(polygon)
    vv = [_world(s, u, d, z) for d in (d0, d1) for u, z in polygon]
    faces = [tuple(reversed(range(k))), tuple(range(k, k*2))]
    faces += [(j, (j+1)%k, (j+1)%k+k, j+k) for j in range(k)]
    # Orient the entire closed mesh consistently, independently of wall axis.
    ob = a.mesh(name, vv, faces, material)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons: p.use_smooth = False
    return ob


def _openings(ctx, specs):
    """Fitted corner masonry changes the real aperture silhouette, no facade cheat.

    Each curved corner occupies only formerly empty aperture volume. Its straight
    rear/top faces bear on existing wall edges, so there are no overlaid wall
    planes. Timber/metal reveals then capture that actual curved construction.
    """
    a = ctx.a
    a.ACTIVE = a.ASSETS['SM_AP_Walls38']['collection']
    corner_names = []
    for s in specs:
        l, r, H = s['c']-s['w']/2, s['c']+s['w']/2, s['H']
        for side, radius in [('left', s['left']), ('right', s['right'])]:
            curve = []
            if side == 'left':
                for i in range(13):
                    t = math.pi-i*math.pi/24
                    curve.append((l+radius+radius*math.cos(t), H-radius+radius*math.sin(t)))
                poly = curve+[(l, H)]
            else:
                for i in range(13):
                    t = math.pi/2-i*math.pi/24
                    curve.append((r-radius+radius*math.cos(t), H-radius+radius*math.sin(t)))
                poly = curve+[(r, H)]
            ob = _extruded_profile(a, s['id']+' constructed curved aperture corner39 '+side,
                                   s, poly, -.09, .09, 'P38ACream')
            ob['construction'] = 'Solid curved corner fitted INSIDE true wall aperture, top and side bearing'
            corner_names.append(ob.name)
    return dict(id=2, name='Distinct natural openings', portals=specs,
                clear_walking_height_m=2.36, shaped_corner_parts=corner_names,
                footprint_changes=False, sightline_sectioning_retained=True)


def _strip(a, name, s, inner, outer, d0, d1, material):
    assert len(inner) == len(outer)
    n = len(inner)
    vv = [_world(s, u, d, z) for d in (d0, d1) for path in (inner, outer) for u, z in path]
    ff = []
    for j in range(n-1):
        ff += [(j, j+1, n+j+1, n+j),
               (2*n+j, 3*n+j, 3*n+j+1, 2*n+j+1),
               (j, 2*n+j, 2*n+j+1, j+1),
               (n+j, n+j+1, 3*n+j+1, 3*n+j)]
    ff += [(0, n, 3*n, 2*n), (n-1, 3*n-1, 4*n-1, 2*n-1)]
    ob = a.mesh(name, vv, ff, material)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    if d1-d0 > .02:
        bevel = ob.modifiers.new('Manufactured reveal edge roll', 'BEVEL')
        bevel.width = .006; bevel.segments = 3
        ob.modifiers.new('Stable fitted reveal normals', 'WEIGHTED_NORMAL')
    for p in ob.data.polygons: p.use_smooth = False
    return ob


def _craft(ctx, specs):
    import bpy
    a, D = ctx.a, ctx.D
    way = _register(ctx, 'SM_AP_Wayfinding38', 'none')
    obsolete = []
    for o in list(way.objects):
        if o.name.startswith(('Threshold fitted oak reveal38', 'Final gold route38')):
            obsolete.append(o.name); bpy.data.objects.remove(o, do_unlink=True)
    _reuse(ctx, 'Transitions39')
    details = []
    for s in specs:
        ob = _strip(a, s['id']+' continuous fitted reveal39', s, _curve(s, -.004), _curve(s, .060),
                    -s['depth']/2, s['depth']/2, M+s['material'])
        ob['construction'] = 'Single continuous U-section, fitted to actual aperture; soft manufactured arris'
        # A narrow inset metal capture strip is recessed relative to main trim,
        # rather than a bright competing second frame around every doorway.
        if s['id'] in {'WelcomeCheckin', 'A07', 'Cafe'}:
            _strip(a, s['id']+' recessed reveal capture39', s, _curve(s, .039), _curve(s, .047),
                   -s['depth']/2-.001, -s['depth']/2+.004, M+'Metal')
        # Real base sockets for the ends. Their inner faces remain OUTSIDE clear
        # width, protecting luggage without creating a new walking obstruction.
        for u in (s['c']-s['w']/2-.035, s['c']+s['w']/2+.035):
            pp = _world(s, u, 0, .075)
            size = (.07, s['depth']+.006, .15) if s['axis']=='x' else (s['depth']+.006, .07, .15)
            a.box(s['id']+' fitted luggage corner socket39', pp, size, M+'Metal', .008)
        details.append(dict(id=s['id'], clear_width=s['w']-.008, lining_depth=s['depth'],
                            top_corner_radii=[s['left'], s['right']]))
    # A low rounded oak ledge belongs on the existing solid café arrival wall,
    # opposite the walking path. It makes the turn a believable place to pause.
    a.pill('Cafe arrival fixed oak ledge39', (-37.84, 14.15, 1.05), (.30, 1.45, .065), M+'Oak', .07)
    for y in (13.65, 14.65):
        a.profile('Cafe ledge folded supported bracket39', [(y-.035, .82), (y+.035, .82),
                  (y+.035, 1.023), (y-.035, 1.023)], -37.97, -37.70, M+'Metal', .004)
    if not any(q['name']=='Airport39 fitted room transitions' for q in D['instances']):
        ctx.add('SM_AP_Transitions39', 'Airport39 fitted room transitions', [0, 0, 0])
    return dict(id=3, name='Modeled fit and craftsmanship', reveals=details,
                removed_obsolete_posts_and_route=obsolete, continuous_manufactured_sections=True)


def _route_mesh(a, route):
    """One welded, mitered inlay with no crossing coplanar strip ends."""
    half = .047
    left, right = [], []
    for i, p in enumerate(route):
        prev, nxt = route[max(i-1, 0)], route[min(i+1, len(route)-1)]
        if i == 0: prev = [2*p[j]-nxt[j] for j in (0, 1)]
        if i == len(route)-1: nxt = [2*p[j]-prev[j] for j in (0, 1)]
        d0 = (p[0]-prev[0], p[1]-prev[1]); d1 = (nxt[0]-p[0], nxt[1]-p[1])
        n0 = (-d0[1]/math.hypot(*d0), d0[0]/math.hypot(*d0))
        n1 = (-d1[1]/math.hypot(*d1), d1[0]/math.hypot(*d1))
        v = (n0[0]+n1[0], n0[1]+n1[1]); den = v[0]*n1[0]+v[1]*n1[1]
        scale = half/max(.25, den)
        left.append((p[0]+v[0]*scale, p[1]+v[1]*scale))
        right.append((p[0]-v[0]*scale, p[1]-v[1]*scale))
    n = len(route);vv = [(*p,z) for z in (.003, .009) for side in (left,right) for p in side]
    ff = []
    for j in range(n-1):
        ff += [(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),
               (j,2*n+j,2*n+j+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j)]
    ff += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    ob = a.mesh('Welded continuous gold navigation inlay39',vv,ff,M+'Gold')
    ob['construction'] = 'One physical mitered inlay; joins welded; no crossing strip faces'
    return ob


def _hierarchy(ctx):
    import bpy
    a, D = ctx.a, ctx.D
    _reuse(ctx, 'RouteHierarchy39', 'none')
    route = D['repair38']['gold_route']
    _route_mesh(a, route)
    # Direction is expressed in a few mounted large cues at actual decision
    # points. No central freestanding directory and no repeated sign clutter.
    signs = [
        dict(id='A08_to_north', p=[-26.12,10.15,2.05], normal=[-1,0], w=1.45,h=.76,
             body=[('A08',.15,.25),('NORTH LOUNGE',-.16,.105)]),
    ]
    way=_register(ctx,'SM_AP_Wayfinding38','none')
    for ob in way.objects:
        if ob.type!='FONT':continue
        if ob.name.startswith('Cafe_welcome COFFEE'):
            ob.data=ob.data.copy();ob.data.body='CLOUD NINE';ob.data.size=.22
        elif ob.name.startswith('Cafe_welcome CAFE'):
            ob.data=ob.data.copy();ob.data.body='COFFEE  /  BAKERY  /  UPPER GALLERY';ob.data.size=.105
    for marker in D['repair38']['marker_probes']:
        if marker['id']=='Cafe_welcome':marker['text']=['CLOUD NINE','COFFEE  /  BAKERY  /  UPPER GALLERY']
    a.ACTIVE=bpy.data.collections['SM_AP_RouteHierarchy39']
    # One readable chevron on that SAME backed plaque shows the actual northward
    # turn into the cafe. It is a real applique, not text hovering in the doorway.
    outline=[(-.18,-.025),(.045,-.025),(.045,-.085),(.20,0),(.045,.085),(.045,.025),(-.18,.025)]
    vv=[(x,14.16+u,1.965+z) for x in (-37.836,-37.829) for u,z in outline]
    n=len(outline);ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    a.mesh('Cafe plaque captured north-turn chevron39',vv,ff,M+'Gold',.001)
    # Reuse the proven backed-sign construction and source-native text export.
    original = core.M
    try:
        core.M = M
        for s in signs:
            core._sign(a,D,s['id'],s['p'],s['normal'],s['w'],s['h'],s['body'])
    finally:
        core.M = original
    # Captive pads behind each new plaque meet real wall bearing planes.
    for s in signs:
        x,y,z=s['p'];nx,ny=s['normal'];rx,ry=-ny,nx
        for u in (-s['w']/2+.09,s['w']/2-.09):
            for dz in (-s['h']/2+.065,s['h']/2-.065):
                a.cyl(s['id']+' wall bearing pad39',(x+rx*u-nx*.03,y+ry*u-ny*.03,z+dz),
                      .014,.03,M+'Metal','X' if nx else 'Y')
    if not any(q['name']=='Airport39 restrained route hierarchy' for q in D['instances']):
        ctx.add('SM_AP_RouteHierarchy39','Airport39 restrained route hierarchy',[0,0,0],collision=False)
    return dict(id=4,name='Route, material and scale hierarchy',route=route,new_mounted_signs=signs,
                retained_room_palette='Warm oak / navy / quiet teal / warm stone',
                airborne_signs_added=0, freestanding_directories_added=0)


def _scrutiny(ctx, specs):
    """Final physical fit pass plus explicit contracts for independent root checks."""
    import bpy
    D=ctx.D
    retained=_register(ctx,'SM_AP_RetainedCraft38')
    gallery=_register(ctx,'SM_AP_GalleryStair35','none')
    fit_repairs=[]
    # Old free-standing scene FONT objects survived outside exported kits after
    # their D.labels records were retired. Reconcile source to the current label
    # list, leaving kit fonts and all aircraft labels untouched.
    valid_labels={q.get('text',q.get('body','')) for q in D.get('labels',[])}
    orphan_labels=[]
    for ob in list(ctx.scene.objects):
        if ob.type!='FONT' or ob.data.body in valid_labels:continue
        if any(c.name.startswith('SM_AP_') for c in ob.users_collection):continue
        x,y,z=ob.location
        if -49.2<x<-13.8 and -22.2<y<34.2:
            orphan_labels.append(dict(name=ob.name,text=ob.data.body,location=list(ob.location)))
            bpy.data.objects.remove(ob,do_unlink=True)
    # The five-pass source views exposed a copied old title in FRONT of the new
    # cafe plaque. Remove only that duplicate, retaining the real menu/POS text.
    for ob in list(retained.objects):
        if ob.type=='FONT' and ob.data.body=='CLOUD NINE' and -38<ob.location.x<-37 and 10<ob.location.y<16:
            fit_repairs.append(dict(part=ob.name,repair='Remove obsolete floating title that overlapped mounted cafe plaque'))
            bpy.data.objects.remove(ob,do_unlink=True)
    # Treads are 130mm thick. Risers belong BELOW the tread underside rather
    # than sharing its top plane; the old3.5mm lip was exposed along every step.
    # Preserve rise, run, nosing, landing and every navigation-floor parameter.
    for ob in gallery.objects:
        if ob.type!='MESH':continue
        if ob.name.startswith('Fitted upper lounge carpet35'):
            for modifier in ob.modifiers:
                if modifier.type=='BEVEL':modifier.width=.003
            fit_repairs.append(dict(part=ob.name,repair='Bound carpet edge radius3mm fits actual15mm thickness, eliminating collapsed bevel faces'))
        if not ob.name.startswith('Closed stair riser35'):continue
        ob.data=ob.data.copy()
        lo=min(v.co.z for v in ob.data.vertices);hi=max(v.co.z for v in ob.data.vertices)
        top=hi-.13
        for v in ob.data.vertices:v.co.z=lo+(v.co.z-lo)*(top-lo)/(hi-lo)
        for modifier in ob.modifiers:
            if modifier.type=='BEVEL':modifier.width=min(modifier.width,.004)
        ob.data.update()
        fit_repairs.append(dict(part=ob.name,repair='Riser terminates at actual tread underside',before_top=hi,after_top=top))
    for ob in retained.objects:
        if ob.type!='MESH':continue
        if ob.name.startswith('Gallery table grounded base35'):
            lo=min(v.co.z for v in ob.data.vertices);hi=max(v.co.z for v in ob.data.vertices)
            # Upper gallery carpet spans3.1505..3.1655; no base penetrates it.
            for v in ob.data.vertices:v.co.z=3.1655+(v.co.z-lo)*(hi-3.1655)/(hi-lo)
            ob.data.update();fit_repairs.append(dict(part=ob.name,repair='Seat base underside on actual carpet top3.1655',before_bottom=lo))
        elif ob.name.startswith('Canopy warm soffit34'):
            lo=min(v.co.x for v in ob.data.vertices);hi=max(v.co.x for v in ob.data.vertices)
            for v in ob.data.vertices:v.co.x=lo+(v.co.x-lo)*(-49-lo)/(hi-lo)
            ob.data.update();fit_repairs.append(dict(part=ob.name,repair='Fit soffit end into wall center, eliminating exposed same-plane end cap',before_end=hi,after_end=-49))
        elif ob.name.startswith('Canopy anchored steel column34'):
            lo=min(v.co.z for v in ob.data.vertices);hi=max(v.co.z for v in ob.data.vertices)
            # Shoes rise to.14; column is captured20mm below the shoe crown.
            for v in ob.data.vertices:v.co.z=.12+(v.co.z-lo)*(hi-.12)/(hi-lo)
            ob.data.update();fit_repairs.append(dict(part=ob.name,repair='Column captured inside actual shoe, no duplicate bottom cap',after_bottom=.12))
    # Full-asset scrutiny found older thin plate bevels clamping to half their
    # thickness (menu backing, carpet and nosings), collapsing faces. Bound every
    # retained/gallery hard-edge roll to a real manufacturing wall thickness.
    # This is not decimation or a material disguise; the evaluated topology is
    # repaired while preserving every broad silhouette and attachment height.
    for col in (retained,gallery):
        for ob in col.objects:
            if ob.type!='MESH' or not ob.data.vertices:continue
            extents=[max(v.co[i] for v in ob.data.vertices)-min(v.co[i] for v in ob.data.vertices) for i in range(3)]
            minimum=min((v for v in extents if v>1e-6),default=0)
            if not minimum:continue
            for modifier in ob.modifiers:
                if modifier.type=='BEVEL' and modifier.width>minimum*.24:
                    old=modifier.width;modifier.width=minimum*.24
                    fit_repairs.append(dict(part=ob.name,repair='Edge roll bounded by actual solid thickness',before_radius=old,after_radius=modifier.width))
            # Older capsule profiles contain duplicate arc endpoints where the
            # straight segment collapses to zero length. Weld those endpoints
            # before evaluating the edge roll; preserve UVs/material assignments.
            import bmesh
            ob.data=ob.data.copy();bm=bmesh.new();bm.from_mesh(ob.data)
            before_vertices=len(bm.verts)
            bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=.000001)
            bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=.0000001)
            bad=[face for face in bm.faces if face.calc_area()<1e-12]
            if bad:bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY')
            removed_vertices=before_vertices-len(bm.verts)
            bm.to_mesh(ob.data);bm.free();ob.data.update()
            if removed_vertices or bad:
                fit_repairs.append(dict(part=ob.name,repair='Weld zero-length capsule endpoints and delete zero-area faces',welded_vertices=removed_vertices,removed_faces=len(bad)))
    # The broad-phase assembly test found socket inner faces exactly coincident
    # with the old bare masonry reveal. Resculpt their fitting offset 7mm toward
    # the aperture, so they physically wrap the lining rather than sharing its
    # buried plane. This small construction clearance preserves >1.78m at WC.
    socket_fits=[]
    collection=bpy.data.collections['SM_AP_Transitions39']
    for s in specs:
        axis=0 if s['axis']=='x' else 1
        for ob in collection.objects:
            if not ob.name.startswith(s['id']+' fitted luggage corner socket39'):continue
            centre=sum(v.co[axis] for v in ob.data.vertices)/len(ob.data.vertices)
            shift=.007 if centre<s['c'] else -.007
            for v in ob.data.vertices:v.co[axis]+=shift
            ob.data.update()
            socket_fits.append(dict(part=ob.name,shift_toward_aperture_m=abs(shift)))
    probes = []
    for s in specs:
        p0 = _world(s,s['c'],-.5,1.62);p1 = _world(s,s['c'],.5,1.62)
        probes.append(dict(id=s['id']+'_clear_eye_height',start=list(p0),end=list(p1),expected='clear'))
        # Two independent head-corner probes verify the silhouette is physically
        # modeled while leaving a generously tall central clear opening.
        p0 = _world(s,s['c']-s['w']/2+.015,-.5,s['H']-.015)
        p1 = _world(s,s['c']-s['w']/2+.015,.5,s['H']-.015)
        probes.append(dict(id=s['id']+'_real_curved_head',start=list(p0),end=list(p1),expected='block'))
    roof_probes = []
    for s in D['repair38']['whole_shell_union']['roof_steps']:
        c=sum(s['interval'])/2;z=sum(s['z'])/2
        p0=(c,s['k']-.5,z) if s['axis']=='x' else (s['k']-.5,c,z)
        p1=(c,s['k']+.5,z) if s['axis']=='x' else (s['k']+.5,c,z)
        roof_probes.append(dict(id='sealed_roof_step_'+str(len(roof_probes)),start=list(p0),end=list(p1),expected='block'))
    # A07/A08 independent corners, real WC east wall and baggage feed cutouts
    # remain part of the final acceptance set. Native QA must read this new set.
    D['repair38']['flow39_probes'] = probes+roof_probes+D['repair38']['perimeter_probes']
    D['repair38']['flow39_portals'] = specs
    D['repair38']['critical_waypoints'] += [
        dict(id='F39_checkin_wide',point=[-44.4,-15,1.62],look=[-40,-14,1.8]),
        dict(id='F39_A08_scale',point=[-29,11.1,1.62],look=[-29,15.5,2]),
        dict(id='F39_cafe_turn',point=[-29.2,12,1.62],look=[-34.5,14.5,1.8]),
    ]
    return dict(id=5,name='Final assembly fit and sightline scrutiny',socket_fits=socket_fits,independent_fit_repairs=fit_repairs,
                removed_orphan_scene_labels=orphan_labels,
                geometry_probes=len(probes),roof_probes=len(roof_probes),
                minimum_central_headroom=min(s['H'] for s in specs),
                minimum_clear_width=min(s['w'] for s in specs)-.014,
                source_scope='Current terminal architecture; aircraft/equipment retained',
                native_validation='Root must import changed assets and recapture actual gameplay')


def apply(ctx, evidence_callback=None):
    import bpy
    a,D=ctx.a,ctx.D
    state=D.setdefault('repair38',{})
    if state.get(TAG):
        for aid in state[TAG]['asset_ids']:
            _register(ctx,aid,'none' if aid in {'SM_AP_Wayfinding38','SM_AP_RouteHierarchy39','SM_AP_GalleryStair35'} else 'complex')
        return state[TAG]
    for mat in bpy.data.materials:
        if mat.name.startswith('MI_AP_'): a.MATS[mat.name[6:]]=mat
    _materials(a)
    # The first room's approach becomes wider; its furniture size and queue
    # start stay unchanged. There is still a turn and a screened next room.
    portal=next(p for p in D['portals'] if p['from_zone']=='entrancefoyer' and p['to_zone']=='checkin')
    old_width=portal['width_m'];portal['width_m']=2.6
    specs=_specs(D)
    records=[]
    for fn in (lambda:_shell(ctx),lambda:_openings(ctx,specs),lambda:_craft(ctx,specs),
               lambda:_hierarchy(ctx),lambda:_scrutiny(ctx,specs)):
        record=fn();records.append(record)
        if evidence_callback:evidence_callback(ctx,record)
    core.validate_plan(D)
    ctx.a.ACTIVE=None
    changed=['SM_AP_'+s for s in STRUCTURAL]+['SM_AP_Wayfinding38','SM_AP_Transitions39','SM_AP_RouteHierarchy39',
                                           'SM_AP_RetainedCraft38','SM_AP_GalleryStair35']
    if bpy.data.collections.get('SM_AP_Attachments38'):changed.append('SM_AP_Attachments38')
    result=dict(status='IMPLEMENTED_SOURCE_REQUIRES_NATIVE_VALIDATION',asset_ids=sorted(changed),
                passes=records,first_checkin_opening=dict(before_m=old_width,after_m=2.6),
                updated_collision_assets=['SM_AP_Walls38','SM_AP_Glazing38','SM_AP_Transitions39'],
                rebuilt_derived_ids=True,whole_map_footprints_preserved=True,
                targeted_native_removal='Replace meshes in listed existing structural families; add two new derived actors; regenerate native labels for changed/new FONT templates',
                unresolved_native='In-engine lighting/text rendering and actual character traversal require root review')
    state[TAG]=result
    return result
