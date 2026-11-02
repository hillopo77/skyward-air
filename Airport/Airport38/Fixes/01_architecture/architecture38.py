"""Airport38 architecture: single-owner shell, deliberate thresholds, mounted wayfinding.

Source units are metres. This module never opens/saves a file or edits inherited
asset data. plan() is pure layout orchestration; build() creates fresh collections.
"""
import copy
import math
from collections import defaultdict

EPS = 1e-6
M = 'P38A'


def _rect_zone(id_, rect, H, title, **extra):
    return dict(id=id_, rect=list(rect), ceiling_m=H, title=title,
                fill='#d6cbb5', description=title, **extra)


def _portal(fr, to, point, axis, width, height=2.8, **extra):
    return dict(zone=to, from_zone=fr, to_zone=to, point=list(point),
                axis=axis, width_m=width, height_m=height,
                kind='deliberate threshold', controlled=False, **extra)


def _inside(rect, x, y):
    return rect[0] + EPS < x < rect[1] - EPS and rect[2] + EPS < y < rect[3] - EPS


def _owner(zones, x, y):
    hits = [q for q in zones if _inside(q['rect'], x, y)]
    assert len(hits) <= 1, ('Overlapping floor owners', x, y, [q['id'] for q in hits])
    return hits[0] if hits else None


def cells(zones):
    # Include the café's gallery/soffit edge so ceiling cells never straddle it.
    xs = sorted({v for q in zones for v in q['rect'][:2]} | {-41.0})
    ys = sorted({v for q in zones for v in q['rect'][2:]})
    result = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            z = _owner(zones, (x0+x1)/2, (y0+y1)/2)
            if z:
                H = z['ceiling_m']
                ceiling = 4.4 if z['id'] == 'cafe' and x0 >= -41-EPS else H
                result.append(dict(rect=[x0,x1,y0,y1], zone=z['id'], ceiling=ceiling, roof=H+.36))
    return result


def _legacy_remove(q):
    asset, x, y, _ = q['asset'], *q['location']
    families = ('SM_AP_Room37_', 'SM_AP_Room34_', 'SM_AP_Ceiling24_', 'SM_AP_Floor24_')
    if asset.startswith(families): return True
    if asset in {'SM_AP_Walls37','SM_AP_Roof35','SM_AP_Fixtures37','SM_AP_FixturesRetained37',
                 'SM_AP_Envelope27','SM_AP_Transitions27','SM_AP_Floor27','SM_AP_CheckinRoom33',
                 'SM_AP_Welcome27','SM_AP_Details27','SM_AP_Fittings27','SM_AP_ArrivalFlow31',
                 'SM_AP_Identity37','SM_AP_Exterior34'}: return True
    if asset in {'SM_AP_Facade12','SM_AP_Roof12','SM_AP_Pillar12'}:
        if asset=='SM_AP_Roof12' and -62<x<-49 and -23<y<0:return True
        if asset=='SM_AP_Pillar12' and x<-49 and -23<y<0:return True
        return -49.2 < x < -13.8 and -22.2 < y < 34.2
    if asset == 'SM_AP_Tile': return -49.2 < x < -13.8 and -22.2 < y < 34.2
    if asset == 'SM_AP_Slab' and -49 < x < -14: return True
    if q['name'].startswith('Sign24_'): return True
    return False


def plan(ctx):
    D = ctx.D
    repair = D.setdefault('repair38', {})
    if repair.get('architecture_planned'): return
    old = {z['id']:copy.deepcopy(z) for z in D['zones']}
    removed_zones = {'gate07foyer','gate08foyer','arrivals'}
    D['zones'] = [q for q in D['zones'] if q['id'] not in removed_zones]
    Z = {q['id']:q for q in D['zones']}
    Z['gate08']['rect'] = [-32,-24,14,34]
    Z['gate08']['merge_group'] = 'gate08'
    Z['gate07']['merge_group'] = 'gate07'
    Z['cafe']['merge_group'] = Z['cafefoyer']['merge_group'] = 'cafe'
    Z['amenitylobby']['rect'] = [-26,-23,-12,-1]
    # The service bay reclaims a half-metre corner of the former broad return
    # rectangle. An L-shaped public exit remains continuous without overlap.
    Z['publicreturn']['rect'] = [-49,-26,-22,-18]
    Z['publicreturn']['merge_group'] = 'publicreturn'
    D['zones'] += [
        _rect_zone('gate07entry',[-26,-23,-1,10],3.4,'A07 LOUNGE ARRIVAL',merge_group='gate07'),
        _rect_zone('baggageservice',[-26,-22,-18.5,-12],3.2,'BAGGAGE HANDLING',staff_only=True),
        _rect_zone('arrivals',[-22,-14,-22,-12],3.6,'ARRIVALS & RECLAIM',merge_group='arrivals'),
        _rect_zone('arrivalsreturn',[-25,-22,-22,-18.5],3.6,'ARRIVALS EXIT',merge_group='arrivals'),
        _rect_zone('publicreturneast',[-26,-25,-22,-18.5],3.2,'PUBLIC EXIT CONNECTOR',merge_group='publicreturn'),
    ]
    remove_pairs = {
        ('concourse','gate07foyer'),('gate07foyer','gate07'),
        ('concourse','gate08foyer'),('gate08foyer','gate08'),
        ('concourse','cafefoyer'),('arrivals','publicreturn'),
    }
    D['portals'] = [p for p in D['portals'] if (p['from_zone'],p['to_zone']) not in remove_pairs]
    D['portals'] += [
        _portal('concourse','gate07entry',[-26,4],'y',3.8,3.12),
        _portal('concourse','gate08',[-29,14],'x',4.8,3.12),
        _portal('concourse','cafefoyer',[-32,12],'y',3.6,3.12),
        _portal('arrivalsreturn','publicreturneast',[-25,-20],'y',2.4,2.9),
        _portal('arrivalsreturn','arrivals',[-22,-20],'y',2.6,3.0),
        _portal('arrivals','baggageservice',[-22,-17.65],'y',1.15,2.6, staff_only=True),
    ]
    # Remove every obsolete structural generation, not just its visible façade.
    remove = [q for q in D['instances'] if _legacy_remove(q)]
    repair['architecture_removed_instances'] = [q['name'] for q in remove]
    repair['architecture_removed_asset_ids'] = sorted({q['asset'] for q in remove})
    for q in remove: ctx.remove(q['name'])
    # Keep the gallery navigation deck and physical stairs. Airside replaces bridge.
    drop_floors = {'Compact terminal','North terminal35','Service ramp','Level boarding bridge'}
    D['floors'] = [q for q in D['floors'] if q['name'] not in drop_floors and not q['name'].startswith('Room38 ')]
    for z in D['zones']:
        D['floors'].append(dict(name='Room38 '+z['id'], rect=z['rect'][:], height=0,
                                priority=15, max_step=.3, zone=z['id']))
    for name, dest in [('Plant1224_1771',[-25.0,17.4,0]),
                       ('Plant1224_1773',[-31.0,17.4,0]),
                       ('Plant1224_1828',[-15.0,9.25,0])]:
        if any(q['name']==name for q in D['instances']): ctx.move(name,dest)
    repair.update(architecture_planned=True,
        architecture_zone_cells=cells(D['zones']),
        architecture_single_owners=True,
        architecture_floor_area_m2=sum((q['rect'][1]-q['rect'][0])*(q['rect'][3]-q['rect'][2]) for q in D['zones']),
        gold_route=[[-38,6.5],[-29,6.5],[-29,4],[-26,4],[-22.2,4],[-19,1.8],[-15.9,.675],[-14,.675]],
        critical_waypoints=[
            dict(id='security_exit',point=[-35.4,6.5,1.62],look=[-29,6.5,1.7]),
            dict(id='A07_approach',point=[-29,6.5,1.62],look=[-26,7.5,2.1]),
            dict(id='A07_threshold',point=[-26,4,1.62],look=[-20,3.7,1.7]),
            dict(id='A08_approach',point=[-29,10.8,1.62],look=[-29,14,3.0]),
            dict(id='A08_inside',point=[-29,18,1.62],look=[-29,28,1.5]),
            dict(id='cafe_approach',point=[-29,10,1.62],look=[-32,12,2]),
            dict(id='WC_approach',point=[-29,0,1.62],look=[-26,-1.2,2]),
            dict(id='baggage_service',point=[-24,-17.5,1.6],look=[-26,-16,1.4]),
        ],
        perimeter_probes=[
            dict(id='L02_east_WC',start=[-15,-3.8,1],end=[-12,-3.8,1],expected='block'),
            dict(id='L03_west_security',start=[-48,-4.25,1],end=[-50,-4.25,1],expected='block'),
            dict(id='L07_no_y18_partition',start=[-29,17,1.5],end=[-29,19,1.5],expected='clear'),
            dict(id='L09_no_A07_inner_wall',start=[-24,4,1.5],end=[-22,4,1.5],expected='clear'),
            dict(id='baggage_window01',start=[-26.8,-13,1.25],end=[-25.2,-13,1.25],expected='clear'),
            dict(id='baggage_window02',start=[-26.8,-16,1.25],end=[-25.2,-16,1.25],expected='clear'),
            dict(id='baggage_wall_below',start=[-26.8,-16,.3],end=[-25.2,-16,.3],expected='block'),
        ],
        forbidden_architecture_assets=sorted({q['asset'] for q in remove}),
        slab_separation_m=.20,
        marker_probes=[])
    validate_plan(D)


def validate_plan(D):
    zs = D['zones']; cs = cells(zs)
    area = sum((q['rect'][1]-q['rect'][0])*(q['rect'][3]-q['rect'][2]) for q in zs)
    cellarea = sum((q['rect'][1]-q['rect'][0])*(q['rect'][3]-q['rect'][2]) for q in cs)
    assert abs(area-cellarea)<EPS, ('Floor union coverage',area,cellarea)
    assert not any(q['id'] in {'gate07foyer','gate08foyer'} for q in zs)
    assert _owner(zs,-14.04,-3.8)['id']=='amenities'
    assert _owner(zs,-48.96,-4.25)['id']=='landsidecorridor'
    assert _owner(zs,-24.5,-16)['id']=='baggageservice'
    assert _owner(zs,-24.5,-20)['id']=='arrivalsreturn'
    assert _owner(zs,-24.5,4)['merge_group']=='gate07'
    assert all(q['roof']-q['ceiling']>=.36-EPS for q in cs)
    return dict(zones=len(zs),cells=len(cs),area_m2=area,overlap_m2=0)


def wall_segments(D):
    """Boundary union, correctly handling T junctions and unequal ceiling heights."""
    zones=D['zones']; edge_ranges=defaultdict(list)
    for z in zones:
        x0,x1,y0,y1=z['rect']
        for ax,k,l,h in [('x',y0,x0,x1),('x',y1,x0,x1),('y',x0,y0,y1),('y',x1,y0,y1)]:
            edge_ranges[ax,k].append((l,h))
    seg=[]
    for (ax,k), intervals in edge_ranges.items():
        cuts=sorted({c for ab in intervals for c in ab})
        for lo,hi in zip(cuts,cuts[1:]):
            c=(lo+hi)/2
            if not any(l-EPS<c<h+EPS for l,h in intervals):continue
            neg=_owner(zones,c,k-.001) if ax=='x' else _owner(zones,k-.001,c)
            pos=_owner(zones,c,k+.001) if ax=='x' else _owner(zones,k+.001,c)
            mem=[q for q in (neg,pos) if q]
            if not mem:continue
            same=(len(mem)==2 and mem[0].get('merge_group',mem[0]['id'])==mem[1].get('merge_group',mem[1]['id']))
            lower=min(q['ceiling_m'] for q in mem) if same else 0
            H=max(q['ceiling_m'] for q in mem)
            if same and H-lower<EPS:continue
            seg.append(dict(axis=ax,k=k,l=lo,h=hi,H=H,low=lower,
                            members=[q['id'] for q in mem],exterior=len(mem)==1,
                            negative=neg['id'] if neg else None,positive=pos['id'] if pos else None))
    return seg


def _openings(D,s):
    ans=[]
    for p in D['portals']:
        ax=p['axis'];k=p['point'][1] if ax=='x' else p['point'][0]
        if ax!=s['axis'] or abs(k-s['k'])>.001:continue
        c=p['point'][0] if ax=='x' else p['point'][1]
        ans.append(dict(centre=c,width=p['width_m'],z0=0,z1=p.get('height_m',2.8),kind='portal'))
    for p in D.get('service_openings38',[]):
        if p['axis']==s['axis'] and abs(p['k']-s['k'])<.001:
            ans.append(dict(p,kind='service'))
    # The staff bay can be seen from reclaim without opening public access.
    if s['axis']=='y' and abs(s['k']+22)<.001:
        ans.append(dict(centre=-14.7,width=2.4,z0=1.05,z1=2.12,kind='window'))
    return ans


def wall_panels(D,s):
    """Return disjoint opaque rectangles plus intentionally glazed apertures."""
    gaps=_openings(D,s); lo,hi,H=s['l'],s['h'],s['H']
    cuts=sorted({lo,hi}|{max(lo,min(hi,g['centre']+d*g['width']/2)) for g in gaps for d in (-1,1)})
    panels=[]; glasses=[]
    for l,h in zip(cuts,cuts[1:]):
        if h-l<EPS:continue
        c=(l+h)/2; hit=[g for g in gaps if abs(c-g['centre'])<g['width']/2-EPS]
        zcuts=sorted({s.get('low',0),H,.10,.94,1.005}|{v for g in hit for v in (g['z0'],g['z1'])})
        for z0,z1 in zip(zcuts,zcuts[1:]):
            if z0<s.get('low',0)-EPS or z1>H+EPS or z1-z0<EPS:continue
            inside=next((g for g in hit if g['z0']-EPS<(z0+z1)/2<g['z1']+EPS),None)
            if inside:
                if inside['kind']=='window':glasses.append((l,h,z0,z1))
            else:panels.append((l,h,z0,z1))
    return panels,glasses


def _aabb(o):
    from mathutils import Vector
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]


def _clone_details(ctx):
    import bpy
    # Explicit whitelist: no old hidden caps, walls, floors or lamps survive.
    selections={
        'Identity37':('Preparation worktop','Preparation support foot','Preparation table closed support',
                      'Preparation instruction','Lounge radiused timber table','Lounge side table',
                      'Gallery quiet reading table','Gallery table','Lounge original travel art',
                      'Lounge travel art solid backing','Original Azure Bay','Azure Bay artwork',
                      'Lounge stowage','Cafe supported menu backing','Cloud Nine beam fascia','Gate timber feature'),
        'CheckinRoom33':('Self-service timber backing','Self-service oak module','Self-service sign inset bezel',
                         'Unstretched self-service title','Bound waiting-bay acoustic panel',
                         'Waiting poster retained frame','Aspect-correct original destination art','Inset quiet waiting carpet'),
        'Welcome27':('Side-table','Round oak side-table','Honed side-table','Bound acoustic wall panel',
                     'Acoustic panel edge welt','Travel guide','Printed guide cover','Guide page layers',
                     'Power module','Recessed USB-C','Power module retained fixing'),
        'Details27':('Mounted clock','Clock dial','Clock index','Clock minute','Clock hour'),
        'Exterior34':('Canopy anchored steel column','Canopy column base','Canopy warm soffit',
                      'Column ground shoe','Entrance weather canopy','Forecourt bollard','Bollard warm optic','Warm canopy downlight'),
    }
    kept=[]
    texts={'1  PREPARE YOUR BELONGINGS','2  WALK THROUGH     3  REPACK  >','AZURE BAY',
           'YOUR NEXT CHAPTER','BAGS & MAGAZINES','CLOUD NINE',
           'COFFEE   /   TEA   /   FRESH BAKERY','ESPRESSO   3','CLOUD NINE  /  COFFEE & BAKERY'}
    col=ctx.new_collection('RetainedCraft38','complex')
    for source,prefixes in selections.items():
        src=bpy.data.collections.get('SM_AP_'+source)
        if not src:continue
        for o in src.objects:
            if not o.name.startswith(prefixes) and not (source=='Identity37' and o.type=='FONT' and o.data.body in texts):continue
            ob=o.copy(); ob.data=o.data.copy();col.objects.link(ob)
            # Wall artwork has a structural mounting shoe rather than a floating gap.
            if source=='CheckinRoom33':
                if o.name.startswith('Self-service'):ob.location.y+=.07
                elif any(t in o.name for t in ('waiting-bay','poster','destination art')):ob.location.y-=.07
            if source in {'Welcome27','Details27'}:
                if _aabb(o)[0][1]<-17.5:ob.location.y-=.07
            kept.append(dict(source=source,part=o.name))
    # The retained foyer wall objects were authored on an older, inset lining.
    # Actual continuous mounting shoes bridge the resulting shallow setback.
    ctx.a.box('Foyer acoustic-panel mounting substrate38',(-46.55,-17.89,2.03),(3.08,.04,2.04),M+'Oak',.004)
    ctx.a.box('Foyer power-module retained mounting shoe38',(-44.72,-17.846,.68),(.36,.128,.17),M+'Housing',.008)
    ctx.add('SM_AP_RetainedCraft38','Airport38 retained crafted furniture and artwork',[0,0,0])
    ctx.D['repair38']['retained_parts']=kept


def _materials(a):
    for n,h,r,metal,em in [
        ('Cream','D9D0BC',.83,0,0),('Navy','183E45',.82,0,0),('Sage','678E85',.82,0,0),
        ('Ceiling','A8A99C',.92,0,0),('Roof','6F7B77',.87,0,0),('Oak','AE8456',.64,0,0),
        ('Frame','637673',.68,.15,0),('Stone','C9BEA5',.72,0,0),('Carpet','477A78',.91,0,0),
        ('WCStone','C0C4B6',.75,0,0),('Rubber','263A39',.87,0,0),('Text','F2E5BF',.72,0,0),
        ('Gold','DCB85D',.66,.08,0),('Opal','FFE9C4',.65,0,3),('Housing','3C5759',.72,.1,0)]:
        a.mat(M+n,h,r,metal,em)
    a.mat(M+'Glass','B7D0D2',.18,0,0,True)


def _line(a,n,ax,k,l,h,z0,z1,mat,depth=.18,bevel=.006):
    if h-l<EPS or z1-z0<EPS:return None
    p=((l+h)/2,k,(z0+z1)/2) if ax=='x' else (k,(l+h)/2,(z0+z1)/2)
    size=(h-l,depth,z1-z0) if ax=='x' else (depth,h-l,z1-z0)
    return a.box(n,p,size,M+mat,bevel)


def _solid_union(a, boxes, split_owners=False):
    """Exact rectilinear solid union, with no buried/coplanar contact faces.

    Only exterior cells contribute faces. Greedy merging keeps long architectural
    planes simple. Unlike joining box objects, this removes their intersections.
    Input boxes are bounds plus a material; coordinates retain true aperture cuts.
    """
    if not boxes:return
    axes=[sorted({round(b[i],6) for b,m in boxes for i in (ax*2,ax*2+1)}) for ax in range(3)]
    maps=[{p:i for i,p in enumerate(v)} for v in axes]
    records=[]
    for b,m in boxes:
        records.append(([maps[ax][round(b[ax*2+e],6)] for ax in range(3) for e in (0,1)],m))
    layers=[]
    for iz in range(len(axes[2])-1):
        layer={}
        for (ix0,ix1,iy0,iy1,iz0,iz1),mat in records:
            if iz0<=iz<iz1:
                for ix in range(ix0,ix1):
                    for iy in range(iy0,iy1):layer[ix,iy]=mat
        layers.append(layer)
    planes=defaultdict(set)
    for iz,layer in enumerate(layers):
        prev=layers[iz-1] if iz else {};nxt=layers[iz+1] if iz+1<len(layers) else {}
        for (ix,iy),mat in layer.items():
            if (ix-1,iy) not in layer:planes[0,ix,-1,mat].add((iy,iz))
            if (ix+1,iy) not in layer:planes[0,ix+1,1,mat].add((iy,iz))
            if (ix,iy-1) not in layer:planes[1,iy,-1,mat].add((ix,iz))
            if (ix,iy+1) not in layer:planes[1,iy+1,1,mat].add((ix,iz))
            if (ix,iy) not in prev:planes[2,iz,-1,mat].add((ix,iy))
            if (ix,iy) not in nxt:planes[2,iz+1,1,mat].add((ix,iy))
    vv=[];ff=[];mi=[];verts={};materials=[]
    def vertex(p):
        if p not in verts:verts[p]=len(vv);vv.append(p)
        return verts[p]
    for (axis,depth,sign,mat),remaining in sorted(planes.items()):
        if mat not in materials:materials.append(mat)
        material_index=materials.index(mat);other=[i for i in range(3) if i!=axis]
        while remaining:
            u0,v0=min(remaining,key=lambda p:(p[1],p[0]));u1=u0+1
            while (u1,v0) in remaining:u1+=1
            v1=v0+1
            while all((u,v1) in remaining for u in range(u0,u1)):v1+=1
            for u in range(u0,u1):
                for v in range(v0,v1):remaining.remove((u,v))
            quad=[]
            for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]:
                p=[0.,0.,0.];p[axis]=axes[axis][depth]
                p[other[0]]=axes[other[0]][u];p[other[1]]=axes[other[1]][v]
                quad.append(vertex(tuple(p)))
            # Coordinates ordered in projected axes yield +X, -Y, +Z.
            if sign != (-1 if axis==1 else 1):quad.reverse()
            ff.append(tuple(quad));mi.append(material_index)
    grouped=defaultdict(list)
    for face,matindex in zip(ff,mi):
        material=materials[matindex]
        owner,mat=material if split_owners else ('Walls38',material)
        grouped[owner].append((face,mat))
    result=[]
    for owner,faces in grouped.items():
        if split_owners:a.ACTIVE=a.ASSETS['SM_AP_'+owner]['collection']
        localverts=[];mapping={};localfaces=[];localmaterials=[];matids=[]
        for face,mat in faces:
            quad=[]
            for index in face:
                if index not in mapping:mapping[index]=len(localverts);localverts.append(vv[index])
                quad.append(mapping[index])
            localfaces.append(tuple(quad))
            if mat not in localmaterials:localmaterials.append(mat)
            matids.append(localmaterials.index(mat))
        ob=a.mesh('Exposed '+owner+' structure union38',localverts,localfaces,None)
        for mat in localmaterials:ob.data.materials.append(a.MATS[M+mat])
        for polygon,index in zip(ob.data.polygons,matids):
            polygon.material_index=index;polygon.use_smooth=False
        ob['construction']='Exact whole-shell solid union; faces split by structural owner only after occluded faces are removed'
        ob['input_solids']=len(boxes);result.append(ob)
    return result


def _slab(a,name,cs,top,bottom,material):
    """A welded surface union. No cell side walls on shared equal-height edges."""
    verts=[];faces=[];lookup={};edges={}
    def vi(v):
        key=tuple(round(x,6) for x in v)
        if key not in lookup:lookup[key]=len(verts);verts.append(v)
        return lookup[key]
    for c in cs:
        x0,x1,y0,y1=c['rect'];t=top(c);b=bottom(c)
        xy=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        faces.append(tuple(vi((x,y,t)) for x,y in xy))
        faces.append(tuple(vi((x,y,b)) for x,y in reversed(xy)))
        for p,q in zip(xy,xy[1:]+xy[:1]):
            key=tuple(sorted((p,q)))
            edges.setdefault(key,[]).append((p,q,b,t))
    for key,ee in edges.items():
        if len(ee)==2 and abs(ee[0][2]-ee[1][2])<EPS and abs(ee[0][3]-ee[1][3])<EPS:continue
        for index,(p,q,b,t) in enumerate(ee):
            # Only the interval outside the neighboring slab is exposed.
            visible=[(b,t)]
            if len(ee)==2:
                other=ee[1-index];ob,ot=other[2],other[3]
                visible=[]
                if b<ob-EPS:visible.append((b,min(t,ob)))
                if t>ot+EPS:visible.append((max(b,ot),t))
            for bb,tt in visible:
                if tt-bb>EPS:faces.append((vi((*p,bb)),vi((*q,bb)),vi((*q,tt)),vi((*p,tt))))
    ob=a.mesh(name,verts,faces,M+material)
    for p in ob.data.polygons:p.use_smooth=False
    return ob


def _make_shell(ctx):
    a,D=ctx.a,ctx.D;cs=cells(D['zones']);Z={q['id']:q for q in D['zones']};structural=[]
    ctx.new_collection('Floors38','complex')
    for c in cs:
        mat='Carpet' if c['zone'].startswith('gate') else 'WCStone' if c['zone'] in {'amenities','baggageservice'} else 'Stone'
        structural.append((tuple(c['rect'])+(-.14,0),('Floors38',mat)))
    ctx.add('SM_AP_Floors38','Airport38 coherent bounded floors',[0,0,0])
    ctx.new_collection('Ceilings38','complex')
    for c in cs:structural.append((tuple(c['rect'])+(c['ceiling'],c['ceiling']+.16),('Ceilings38','Ceiling')))
    ctx.add('SM_AP_Ceilings38','Airport38 coherent ceiling union',[0,0,0])
    ctx.new_collection('Roofs38','complex')
    for c in cs:structural.append((tuple(c['rect'])+(c['roof'],c['roof']+.18),('Roofs38','Roof')))
    ctx.add('SM_AP_Roofs38','Airport38 coherent roof union',[0,0,0])
    ctx.new_collection('Walls38','complex');segs=wall_segments(D);glazing=[];solids=[]
    def solid(ax,k,l,h,z0,z1,mat,depth=.18):
        if h-l<EPS or z1-z0<EPS:return
        bounds=(l,h,k-depth/2,k+depth/2,z0,z1) if ax=='x' else (k-depth/2,k+depth/2,l,h,z0,z1)
        solids.append((bounds,mat))
    for s in segs:
        panels,glass=wall_panels(D,s)
        ids=s['members'];ax,k=s['axis'],s['k']
        # Outside-only broad panes; no nested internal glass partitions.
        exterior_glazed=s['exterior'] and (
            ('entrancefoyer' in ids and ax=='y' and k==-49) or
            ('cafe' in ids and (k==-49 if ax=='y' else k==34)) or
            ('gate08' in ids and (k==-24 if ax=='y' else k==34)) or
            ('gate07' in ids and (k==-14 if ax=='y' else k==10)) or
            ('arrivals' in ids and ax=='y' and k==-14))
        for l,h,z0,z1 in panels:
            if exterior_glazed and z0>=1.005-EPS and z1<=s['H']+EPS:
                if z1-z0>.2:
                    glazing.append((dict(s,l=l,h=h),max(1.005,z0),z1-.12))
                    solid(ax,k,l,h,z1-.12,z1,'Frame',.18)
                    continue
            mat='Rubber' if z1<=.101 else 'Sage' if z1<=.941 and 'security' in ids else 'Navy' if z1<=.941 else 'Oak' if z1<=1.006 else 'Cream'
            if ax=='y' and k==-26 and 'checkin' in ids and z0>=1.005:mat='Oak'
            solid(ax,k,l,h,z0,z1,mat)
        for l,h,z0,z1 in glass:glazing.append((dict(s,l=l,h=h),z0,z1))
        if s['exterior']:
            # Plenum infill touches ceiling top and roof underside. It does not
            # repeat either slab's side/end planes or extend through the slabs.
            solid(ax,k,s['l'],s['h'],s['H']+.16,s['H']+.36,'Roof',.18)
    # Complete two self-contained WC cubicles, pocket and mounted door header.
    for x in (-21,-17.1):
        for ax,k,l,h in [('y',x-1.6,-7.05,-3.3),('y',x+1.6,-7.05,-3.3),
                         ('x',-3.3,x-1.6,x+1.6),('x',-7.05,x-1.6,x-.54),('x',-7.05,x+.54,x+1.6)]:
            solid(ax,k,l,h,0,2.8,'Cream',.14)
            solid(ax,k,l,h,.015,.10,'Rubber',.15)
        solid('x',-7.05,x-.54,x+.54,2.17,2.8,'Cream',.14)
        a.pill('WC visible pocket shell38',(x+1.17,-7.12,1.10),(1.22,.11,2.21),M+'Cream',.035)
    structural += [(bounds,('Walls38',material)) for bounds,material in solids]
    union_objects=_solid_union(a,structural,split_owners=True)
    D['repair38']['whole_shell_union']=dict(method='Exact rectilinear solid union before ownership split',
        input_solids=len(structural),exposed_faces=sum(len(o.data.polygons) for o in union_objects),
        plenum_infill_interval_above_ceiling=[.16,.36],buried_faces_removed=True)
    ctx.add('SM_AP_Walls38','Airport38 complete physical perimeter and partitions',[0,0,0])
    ctx.new_collection('Glazing38','complex')
    for s,z0,z1 in glazing:
        if z1-z0<.05:continue
        ax,k,l,h=s['axis'],s['k'],s['l'],s['h']
        _line(a,'Broad clear exterior pane38',ax,k,l+.015,h-.015,z0+.015,z1-.015,'Glass',.022,0)
        for z in (z0,z1):_line(a,'Quiet pane retaining rail38',ax,k,l,h,z-.026,z+.026,'Frame',.08,.006)
        count=max(1,math.ceil((h-l)/4.5))
        for j in range(count+1):
            c=l+(h-l)*j/count
            _line(a,'Widely spaced matte mullion38',ax,k,c-.027,c+.027,z0,z1,'Frame',.08,.006)
    ctx.add('SM_AP_Glazing38','Airport38 exterior glazing and observation panes',[0,0,0])
    D['wall_segments24']=segs
    D['repair38']['architecture_wall_segments']=len(segs)
    D['repair38']['ceiling_coverage']=cs
    return cs


def _sign(a,D,id_,center,normal,width,height,lines,arrow=None):
    """Mounted laminate panel, actual backing and 3-D arrow; fonts face approach."""
    x,y,z=center;nx,ny=normal;right=(-ny,nx)
    size=(width,.045,height) if ny else (.045,width,height)
    a.box(id_+' wall-mounted oak backing',(x,y,z),size,M+'Oak',.004)
    front=(x+nx*.031,y+ny*.031,z)
    size=(width-.07,.024,height-.07) if ny else (.024,width-.07,height-.07)
    a.box(id_+' navy laminated face',front,size,M+'Navy',.003)
    rot=(math.pi/2,0,math.atan2(ny,nx)+math.pi/2)
    direction=1 if arrow=='right' else -1
    # Pass47: the arrow sits .34 in from the edge and .20 below centre, which on
    # signs under ~1.9 m wide lands on the second text line ('START HERE /
    # CHECK-IN' had it across 'IN'). With an arrow, any text line in the
    # arrow's band moves .26 away from it, so the two can never overlap.
    shift=-direction*.26 if arrow and width<2.4 else 0.
    for text,dz,font in lines:
        s=shift if (dz-font/2<-.085 and dz+font/2>-.315) else 0.  # only lines in the arrow's band move
        a.font(text,(x+nx*.046+right[0]*s,y+ny*.046+right[1]*s,z+dz),font,M+'Text',rot,name=id_+' '+text)
    if arrow:
        # Seven-sided closed extruded arrow, supported on sign face.
        outline=[(-.23,-.035),(.06,-.035),(.06,-.115),(.24,0),(.06,.115),(.06,.035),(-.23,.035)]
        u=width/2-.34
        verts=[]
        for depth in (.044,.053):
            for du,dz in outline:
                uu=u+direction*du
                verts.append((x+right[0]*uu+nx*depth,y+right[1]*uu+ny*depth,z-.20+dz))
        faces=[tuple(reversed(range(7))),tuple(range(7,14))]+[(j,(j+1)%7,(j+1)%7+7,j+7) for j in range(7)]
        a.mesh(id_+' solid directional arrow',verts,faces,M+'Gold',.002)
    D['repair38']['marker_probes'].append(dict(id=id_,center=list(center),normal=list(normal),width=width,height=height,
        text=[s[0] for s in lines],mounted=True))


def _wayfinding(ctx):
    a,D=ctx.a,ctx.D
    ctx.new_collection('Wayfinding38','none')
    S=lambda *args,**kwargs:_sign(a,D,*args,**kwargs)
    S('A07',[-26.12,7.5,2.05],[-1,0],2.9,1.35,
      [('GATE A07',.27,.33),('BOARDING  /  TURN RIGHT',-.15,.115)],arrow='right')
    # Header is part of actual wall above opening, not a second decorative arch.
    S('A08',[-29,13.88,3.26],[0,-1],4.65,.22,[('A08   NORTH LOUNGE',0,.18)])
    S('Cafe_concourse',[-31.88,9.00,2.15],[1,0],1.75,1.2,
      [('CAFE',.24,.30),('CLOUD NINE',-.08,.12)],arrow='right')
    S('Cafe_welcome',[-37.88,13.1,1.95],[1,0],3.05,1.15,
      [('COFFEE  /  BAKERY',.22,.19),('CAFE & UPPER GALLERY',-.15,.135)])
    S('WC',[-26.12,-1.55,2.05],[-1,0],.92,.88,[('WC',.15,.27),('TOILETS',-.17,.11)])
    S('WC_approach',[-26.12,.15,2.1],[-1,0],1.4,.73,[('TOILETS',.13,.18)],arrow='right')
    S('Staff',[-47.15,9.88,1.92],[0,-1],.84,.50,[('STAFF ONLY',0,.11)])
    S('Security_exit',[-42.1,9.88,2.14],[0,-1],5.8,.84,
      [('AFTER SCREENING: TURN RIGHT',.15,.22),('GATES  /  CAFE  /  TOILETS',-.17,.145)],arrow='right')
    S('Exit_return',[-24.88,-20,3.08],[1,0],2.30,.30,[('EXIT  /  FORECOURT',0,.17)])
    S('Baggage_staff',[-21.88,-17.65,2.84],[1,0],1.10,.28,[('STAFF ACCESS',0,.105)])
    S('Checkin_next',[-30,-8.12,3.11],[0,-1],3.1,.45,[('AFTER CHECK-IN  /  SECURITY',0,.14)])
    S('Welcome',[-46,-8.12,1.95],[0,-1],2.8,1.3,
      [('WELCOME ABOARD',.32,.24),('01 CHECK IN',-.01,.19),('02 SECURITY   03 GATE',-.35,.15)])
    S('Terminal_exterior',[-49.12,-12.5,3.15],[-1,0],3.5,.46,
      [('SKYWARD AIR  /  DEPARTURES',0,.18)])
    S('Terminal_interior',[-48.88,-12.5,3.15],[1,0],3.5,.46,
      [('WELCOME TO SKYWARD AIR',0,.20)])
    S('Checkin_start',[-43.12,-12.6,1.95],[-1,0],1.7,.9,
      [('START HERE',.22,.20),('CHECK-IN',-.12,.19)],arrow='right')
    for x,no in [(-21,'01'),(-17.1,'02')]:
        S('WC_'+no,[x,-7.16,2.45],[0,-1],.94,.34,[('TOILET '+no,0,.12)])
    # Purposeful thresholds: warm flush linings, not another obstacle in the aisle.
    for ax,k,c,w,H in [('y',-43,-15,1.9,3.2),('y',-32,12,3.6,3.3),('y',-26,4,3.8,3.3)]:
        for v in (c-w/2-.055,c+w/2+.055):_line(a,'Threshold fitted oak reveal38',ax,k,v-.045,v+.045,-.005,H,'Oak',.20)
    # Floor guidance is a single restrained inlay: welded straight runs, no old route.
    route=D['repair38']['gold_route']
    verts=[];faces=[]
    for p,q in zip(route,route[1:]):
        dx,dy=q[0]-p[0],q[1]-p[1];ln=math.hypot(dx,dy)
        nx,ny=-dy/ln*.055,dx/ln*.055;i=len(verts)
        verts += [(p[0]+nx,p[1]+ny,.012),(p[0]-nx,p[1]-ny,.012),(q[0]-nx,q[1]-ny,.012),(q[0]+nx,q[1]+ny,.012)]
        faces.append(tuple(range(i,i+4)))
    a.mesh('Final gold route38',verts,faces,M+'Gold')
    ctx.add('SM_AP_Wayfinding38','Airport38 mounted legible route cues',[0,0,0],collision=False)


def _forecourt(ctx):
    a=ctx.a
    ctx.new_collection('Canopy38','complex')
    # One coherent cover replaces six overlapping original barrel modules. Its
    # higher west plane meets the existing lower welcome canopy as a weather lap.
    a.pill('Forecourt continuous weather canopy38',(-56.975,-12.25,3.77),(8.05,17.5,.16),M+'Roof',.12)
    for x in (-60.4,-53.6):
        for y in (-20.1,-4.4):
            a.pill('Forecourt supported rounded column38',(x,y,1.845),(.18,.18,3.69),M+'Frame',.035)
            a.pill('Forecourt anchored column shoe38',(x,y,.035),(.30,.30,.08),M+'Frame',.035)
    ctx.add('SM_AP_Canopy38','Airport38 coherent covered forecourt',[0,0,0])


def _fixtures(ctx,cs):
    a,D=ctx.a,ctx.D;Z={q['id']:q for q in D['zones']}
    ctx.new_collection('Fixtures38','none');lights=[]
    roles={
        'entrancefoyer':('welcome',3300,3000,False), 'checkin':('checkin_task',3500,3900,True),
        'publicreturn':('exit_circulation',3400,2800,False),'publicreturneast':('exit_circulation',3400,1200,False),
        'landsidecorridor':('circulation',3400,3200,False),
        'security':('screening_task',3700,4000,True),'recovery':('repack_task',3500,3000,True),
        'concourse':('wayfinding',3400,3300,False),'gate07':('lounge',3300,3200,True),
        'gate07entry':('lounge_arrival',3300,2800,False),'gate08':('lounge',3300,3500,True),
        'cafefoyer':('cafe_welcome',3200,2500,False),'cafe':('cafe_dining',3200,4000,True),
        'amenitylobby':('amenity_circulation',3400,2300,False),'amenities':('washroom',3500,2600,False),
        'arrivals':('reclaim_task',3500,3900,True),'arrivalsreturn':('exit_circulation',3400,2300,False),
        'operations':('staff_task',3500,2500,False),'baggageservice':('baggage_task',3600,2800,False),
    }
    for id_,z in Z.items():
        x0,x1,y0,y1=z['rect'];nx=max(1,math.ceil((x1-x0)/6.8));ny=max(1,math.ceil((y1-y0)/6.8))
        role,temp,lm,shadow=roles.get(id_,('circulation',3400,2600,False))
        for ix in range(nx):
            for iy in range(ny):
                x=x0+(ix+.5)*(x1-x0)/nx;y=y0+(iy+.5)*(y1-y0)/ny;H=z['ceiling_m']
                if id_=='cafe':H=4.4 if x>=-41 else 2.98 if y>25 else 6.8
                zh=H-.075;length=min(1.9,(x1-x0)*.52)
                # Back plate touches ceiling. The lens points DOWN and is never on upper face.
                a.pill('Down-facing '+role+' luminaire38',(x,y,zh),(length,.36,.15),M+'Housing',.035)
                a.pill('Recessed warm opal downward lens38',(x,y,zh-.079),(length-.12,.25,.014),M+'Opal',.025)
                if H<z['ceiling_m']-.2:
                    for xx in (-length*.35,length*.35):
                        support=3.10 if id_=='cafe' and x<-41 and y>25 else H+.03
                        a.tube('Actual pendant suspension38',[(x+xx,y,zh+.075),(x+xx,y,support)],.004,M+'Frame',8)
                lights.append(dict(zone=id_,position=[x,y,zh-.094],lumens=lm,watts=lm,
                    width=(length-.12)*100,height=25,temperature=temp,role=role,
                    direction=[0,0,-1],casts_shadows=shadow,shadow_intent='soft task/contact' if shadow else 'soft circulation fill',
                    fixture='SM_AP_Fixtures38',source='opal underside',revision=38))
                if id_=='cafe' and x<-41 and y>25:
                    hh=z['ceiling_m']-.075
                    a.pill('Gallery flush fixture38',(x,y,hh),(length,.36,.15),M+'Housing',.035)
                    a.pill('Gallery down-facing lens38',(x,y,hh-.079),(length-.12,.25,.014),M+'Opal',.025)
                    lights.append(dict(zone=id_,position=[x,y,hh-.094],lumens=3100,watts=3100,
                        width=(length-.12)*100,height=25,temperature=3200,role='gallery_reading',direction=[0,0,-1],
                        casts_shadows=True,shadow_intent='soft reading/contact',fixture='SM_AP_Fixtures38',revision=38))
    # Exterior retained canopy optics have equally explicit native light ownership.
    for y in (-14.2,-12.5,-10.8):
        lights.append(dict(zone='forecourt',position=[-51.1,y,3.49],lumens=1700,watts=1700,width=80,height=16,
            temperature=3200,role='entrance_canopy',direction=[0,0,-1],casts_shadows=False,
            shadow_intent='welcoming sheltered fill',fixture='SM_AP_RetainedCraft38',revision=38))
    for x in (-58.7,-55.2):
        for y in (-18,-12.5,-6.5):
            a.pill('Covered forecourt flush luminaire38',(x,y,3.615),(1.65,.30,.15),M+'Housing',.035)
            a.pill('Covered forecourt downward lens38',(x,y,3.536),(1.53,.20,.014),M+'Opal',.025)
            lights.append(dict(zone='forecourt',position=[x,y,3.521],lumens=1800,watts=1800,width=153,height=20,
                temperature=3300,role='covered_forecourt',direction=[0,0,-1],casts_shadows=False,
                shadow_intent='soft sheltered circulation',fixture='SM_AP_Fixtures38',revision=38))
    ctx.add('SM_AP_Fixtures38','Airport38 role-based down-facing practical fixtures',[0,0,0],collision=False)
    # Articulated bridge practicals have separate ownership and follow their
    # sleeve roots. The terminal shell must not discard that source metadata.
    D['lights']=lights+[q for q in D.get('lights',[]) if q.get('follow_actor')]
    D['repair38']['fixture_roles']={k:dict(role=v[0],temperature=v[1],lumens=v[2],shadows=v[3]) for k,v in roles.items()}


def build(ctx):
    if not ctx.D.get('repair38',{}).get('architecture_planned'):plan(ctx)
    _materials(ctx.a)
    _clone_details(ctx)
    cs=_make_shell(ctx)
    _forecourt(ctx)
    _wayfinding(ctx)
    _fixtures(ctx,cs)
    result=validate_plan(ctx.D)
    ctx.D['repair38']['architecture_source_validation']=result
    ctx.D['repair38']['architecture_issue_map']={
        'L01':'Roof35 and all Room37 ceilings removed; separated unified ceiling/roof cells',
        'L02':'Complete east WC exterior from final zone boundary',
        'L03':'Complete west landside corridor/security exterior from final boundary',
        'L04':'Staff plaque mounted beside opening, door passage clear',
        'L05':'WC identifier mounted north of door and faces west to concourse',
        'L06':'A08 header is readable from south; both plants moved away from threshold',
        'L07':'A08 foyer and y18 partition removed, one lounge and entrance',
        'L08':'Freestanding directory removed; mounted A07/cafe/WC directions and final route',
        'L09':'A07 intermediate cell merged; cafe preserves a deliberate high-room transition',
        'L10':'No-overlap/coverage assertions, perimeter probes and marker metadata provided'}
    return result
