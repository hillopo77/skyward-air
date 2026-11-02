"""Isolated coherent cabin-window kits40. Root owns current-master assembly.

One rounded aperture, matching reveal/glass/gasket, an actual retained cassette
and a matching overhead-bin rear service recess. No airframe/black-wing edits.
"""
import math,json

VERSION=1
SWAPS={
 'SM_Plane_WindowWall_L':'SM_AP_W40WindowWallL',
 'SM_Plane_WindowWall_R':'SM_AP_W40WindowWallR',
 'SM_Plane_OuterWindowBarrel':'SM_AP_W40PressureWindows',
 'SM_Plane_CargoBay10':'SM_AP_W40CargoBayWindows',
 'SM_Plane_WindowShadeFrame18_L':'SM_AP_W40ShadeFrameL',
 'SM_Plane_WindowShadeFrame18_R':'SM_AP_W40ShadeFrameR',
 'SM_Plane_Rack_L':'SM_AP_W40RackL',
 'SM_Plane_Rack_R':'SM_AP_W40RackR',
 'SM_Plane_WindowShadeHandle18_L':'SM_AP_W40ShadeHandleL',
 'SM_Plane_WindowShadeHandle18_R':'SM_AP_W40ShadeHandleR',
}
OLD_DERIVED={'SM_Plane_OuterWindowBarrel':'SM_AP_E39WeatherSeals','SM_Plane_WindowShadeFrame18_L':'SM_AP_E39ShadeFrameL','SM_Plane_WindowShadeFrame18_R':'SM_AP_E39ShadeFrameR'}
CLOSED_BASE=2.332
STOW_BASE=2.120
STOW_BOTTOM=2.055
CASSETTE_BOTTOM=2.045
CASSETTE_TOP=2.325


def pressure_x(z):return 2.5*max(.000001,1-abs((z-.55)/2.35)**3.6)**(1/3.6)
def smooth(t):t=max(0.,min(1.,t));return t*t*(3-2*t)
def track_x(z):return CLOSED_BASE-(CLOSED_BASE-STOW_BASE)*smooth((z-1.70)/(STOW_BOTTOM-1.70))


def shade_pose(part,progress):
    f=smooth(progress);i=int(part['window40_index']);side=part['window40_side'];offset=part['window40_offset']
    z=.92+.20*i+(STOW_BOTTOM-(.92+.20*i))*f
    return [offset[0]+side*(track_x(z)+.006*i),part['closed_location'][1],offset[2]+z]


def _matrix(ob):
    from mathutils import Matrix
    return Matrix.LocRotScale(ob.location,ob.rotation_euler.to_quaternion(),ob.scale)


def _loop(w,h,r,zc,half=.675,lo=.2,hi=2.1923077):
    angles=sorted(set([j*math.tau/512 for j in range(512)]+[math.atan2(z-zc,y)%math.tau for y in (-half,half) for z in (lo,hi)]))
    out=[]
    for a in angles:
        dy,dz=math.cos(a),math.sin(a);low,high=0.,4.
        for _ in range(38):
            t=(low+high)*.5;u,v=abs(dy*t)-(w/2-r),abs(dz*t)-(h/2-r)
            sd=math.hypot(max(u,0),max(v,0))+min(max(u,v),0)-r
            if sd>0:high=t
            else:low=t
        t=(low+high)*.5;out.append((dy*t,zc+dz*t,a))
    return out


def _normals(obj,outward):
    import bmesh
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
    # A surface with a hole has no enclosed volume. Fix its overall facing from
    # the real intended pressure/cabin normal rather than an arbitrary volume.
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if sum(f.normal.x*f.calc_area()*outward for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()


def _ringmesh(a,name,rings,material,side,closed=False):
    n=len(rings[0]);v=[p for row in rings for p in row]
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(rings)-1) for i in range(n)]
    ob=a.mesh(name,v,faces,material);_normals(ob,side)
    return ob


def _aliases(a):
    import bpy
    for key,name in [('W40Liner','MI_Plane_Cabin09'),('W40Reveal','MI_Plane_CabinReveal09'),('W40Pearl','MI_Plane_White'),('W40Seal','MI_Plane_Seal08'),('W40Felt','MI_Plane_Graphite'),('W40Glass','MI_Plane_SkyGlass18'),('W40Paint','MI_Plane_Paint09')]:
        m=bpy.data.materials.get(name);assert m,('Original finish missing',name);a.MATS[key]=m


def _newcopy(ctx,old,new):
    import bpy
    col=bpy.data.collections.get(new)
    if col:return col,False
    src=bpy.data.collections.get(OLD_DERIVED.get(old,'')) or bpy.data.collections.get(old)
    assert src,('Original kit not loaded',old)
    col=bpy.data.collections.new(new)
    for ob in src.objects:
        q=ob.copy();q.data=ob.data.copy() if ob.data else None;col.objects.link(q)
        if q.type=='MESH':
            spans=[max(v.co[i] for v in q.data.vertices)-min(v.co[i] for v in q.data.vertices) for i in range(3)]
            for mod in q.modifiers:
                if mod.type=='BEVEL':
                    mod.width=min(mod.width,.0015,min(spans)*.18);mod.use_clamp_overlap=True
    col['window40_original']=old;return col,True


def _remove(col,prefixes):
    import bpy
    removed=[]
    for ob in list(col.objects):
        if ob.name.startswith(prefixes):removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
    return removed


def _wall(ctx,col,side):
    a=ctx.a;a.ACTIVE=col
    removed=_remove(col,('Thin formed cabin liner','Continuous tapered window reveal','Fine window interior trim','Laminated passenger glazing','Retractable shade top cassette','Shade recessed grip'))
    # The old liner top exceeded the actual pressure envelope by61mm. Retain
    # fixed kick/escape/ceiling fittings but fit every point to its real skin.
    for ob in col.objects:
        if ob.type!='MESH':continue
        T=_matrix(ob);I=T.inverted()
        for v in ob.data.vertices:
            p=T@v.co;limit=pressure_x(p.z)-.035
            if abs(p.x)>limit:p.x=side*limit;v.co=I@p
        ob.data.update()
    path=_loop(.78,1.10,.18,1.46);rings=[]
    for t in (0,.12,.30,.52,.76,1.):
        row=[]
        for y,z,angle in path:
            dz=z-1.46;scale=min(.675/max(abs(y),1e-9),((2.1923077-1.46) if dz>=0 else 1.46-.2)/max(abs(dz),1e-9))
            yy=y*(1+(scale-1)*t);zz=1.46+dz*(1+(scale-1)*t)
            row.append((side*(pressure_x(zz)-.065),yy,zz))
        rings.append(row)
    _ringmesh(a,'W40 continuous pressure-fitted cabin liner',rings,'W40Liner',-side)
    # All rings share the same angular samples so the rolled reveal joins the
    # liner exactly without coplanar duplicate faces or disconnected elbows.
    specs=[(.78,1.10,.18,.065),(.779,1.099,.1795,.069),(.768,1.088,.175,.073),(.737,1.046,.167,.052),(.705,1.006,.161,.016),(.700,1.000,.160,.008)]
    rings=[]
    for w,h,r,inset in specs:
        rings.append([(side*(pressure_x(z)-inset),y,z) for y,z,_ in _loop(w,h,r,1.46)])
    _ringmesh(a,'W40 continuous rolled rounded window reveal',rings,'W40Reveal',-side)
    pane=_loop(.700,1.000,.160,1.46);v=[(side*(pressure_x(z)-.006),y,z) for y,z,_ in pane]
    # Subdivide into horizontal ruled rows rather than a non-planar giant ngon.
    centre=(side*(pressure_x(1.46)-.006),0,1.46);n=len(v);v.append(centre)
    ob=a.mesh('W40 single curved laminated optical pane',v,[(n,i,(i+1)%n) for i in range(n)],'W40Glass');_normals(ob,side)
    return dict(removed=removed,clear_aperture=dict(width=.70,height=1.,radius=.16,centre_z=1.46),liner_skin_margin_m=.035,pane_count=1)


def _outer(ctx,col):
    a=ctx.a;a.ACTIVE=col
    removed=_remove(col,('Fitted pressure skin09','E39 continuous swept opaque weather gasket','Flush glazing weather seal09'))
    for side in (-1,1):
        hole=_loop(.70,1.,.16,1.46,lo=-.4,hi=2.8);rings=[]
        for t in (0,.08,.20,.40,.65,1.):
            row=[]
            for y,z,angle in hole:
                dz=z-1.46;scale=min(.675/max(abs(y),1e-9),((2.8-1.46) if dz>=0 else 1.46+.4)/max(abs(dz),1e-9))
                yy=y*(1+(scale-1)*t);zz=1.46+dz*(1+(scale-1)*t);row.append((side*pressure_x(zz),yy,zz))
            rings.append(row)
        _ringmesh(a,'W40 pressure skin with matched rounded aperture',rings,'W40Paint',side)
        _ringmesh(a,'W40 formed aperture return behind optical edge',
                  [[(side*(pressure_x(z)-depth),y,z) for y,z,_ in hole] for depth in (0.,.004,.009)],'W40Seal',side)
        path=[(side*(pressure_x(z)+.001),y,z) for y,z,_ in hole];n=len(path);v=[]
        from mathutils import Vector
        for i,p in enumerate(path):
            p=Vector(p);t=(Vector(path[(i+1)%n])-Vector(path[(i-1)%n])).normalized();e1=Vector((side,0,0));e1=(e1-t*t.dot(e1)).normalized();e2=t.cross(e1).normalized()
            for j in range(12):v.append(p+.0024*(e1*math.cos(j*math.tau/12)+e2*math.sin(j*math.tau/12)))
        faces=[(i*12+j,((i+1)%n)*12+j,((i+1)%n)*12+(j+1)%12,i*12+(j+1)%12) for i in range(n) for j in range(12)]
        ob=a.mesh('W40 gasket follows actual pressure aperture',v,faces,'W40Seal');_normals(ob,side)
    return dict(removed=removed,gasket_radius_m=.0024,matched_actual_aperture=True)


def _frame(ctx,col,side):
    a=ctx.a;a.ACTIVE=col
    removed=_remove(col,('E39 continuous formed open C guide','E39 retained guide felt','E39 curved hollow shade pocket','E39 rounded pocket feed lip','E39 pocket end cap','Shade captive guide','Shade retained upper','Shade pocket dark'))
    for ob in col.objects:
        if ob.type!='MESH' or not ob.name.startswith('Window shade fixed switch mounting18'):continue
        # Preserve the real switch face/interaction point, but give its tapered
        # rear a physical overlap with the captive side-channel return. The old
        #26mm block was hanging in front of both wall and guide.
        T=_matrix(ob);I=T.inverted()
        for v in ob.data.vertices:
            p=T@v.co;x=side*(side*2.3+p.x);t=max(0,min(1,(x-2.273)/.026))
            p.x=side*((2.273+.090*t)-2.3);p.y=.433+(p.y-.433)*(1+.15*t);v.co=I@p
        ob.data.update()
    def local(x,y,z):return (side*(x-2.30),y,z-.92)
    zvals=[.905,1.30,1.65,1.70,1.76,1.82,1.90,1.975,2.045,2.12,2.20,2.28,2.325]
    for edge in (-1,1):
        rows=[]
        for z in zvals:
            inner=max(2.105,track_x(z)-.008);outer=min(pressure_x(z)-.012,track_x(z-.255)+.042)
            inner=min(inner,outer-.024)
            cross=[(outer,.348),(outer,.398),(inner,.398),(inner,.348),(inner+.005,.348),(inner+.005,.387),(outer-.005,.387),(outer-.005,.348)]
            rows.append([local(x,edge*y,z) for x,y in cross])
        ob=a.loft('W40 integrated captive shade side channel',rows,'W40Pearl',True,True)
        b=ob.modifiers.new('Small manufactured channel edge roll','BEVEL');b.width=.0006;b.segments=3
    zvals=[CASSETTE_BOTTOM,2.09,2.14,2.19,2.235,2.28,CASSETTE_TOP];rows=[]
    for z in zvals:
        outside=pressure_x(z)-.025
        rows.append([local(x,y,z) for x,y in [(2.06,-.415),(outside,-.415),(outside,.415),(2.06,.415)]])
    n=4;v=[p for row in rows for p in row];faces=[(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(len(rows)-1) for j in range(n)]+[tuple((len(rows)-1)*n+j for j in range(n))]
    ob=a.mesh('W40 retained curved cassette with actual feed mouth',v,faces,'W40Pearl')
    solid=ob.modifiers.new('Cassette manufactured wall thickness','SOLIDIFY');solid.thickness=.008;solid.offset=0
    _normals(ob,-side)
    a.tube('W40 recessed cassette felt feed lip',[local(2.068,-.404,CASSETTE_BOTTOM+.004),local(2.068,.404,CASSETTE_BOTTOM+.004)],.003,'W40Felt',10)
    return dict(removed=removed,feed_z=CASSETTE_BOTTOM,top_z=CASSETTE_TOP,open_below=True,full_aperture_top=1.96,switch_face_preserved=True,tapered_switch_mount_attaches_to_guide=True)


def _rack(ctx,col,side):
    changed=[]
    for ob in col.objects:
        if ob.type!='MESH' or not ob.name.startswith(('Fixed overhead cavity10 curved crown','Fixed overhead cavity10 end cheek','Fixed overhead cavity10 service underbody','Bin fixed luggage floor10')):continue
        T=_matrix(ob);I=T.inverted()
        for v in ob.data.vertices:
            p=T@v.co;x=abs(p.x)
            # The actual PSU mounting footprint ends1.9955m outboard. Preserve
            # its entire surface, then taper the unused rear218mm to a retained
            # formed return at2.025m. This creates a real service chase rather
            # than running the moving shade leaves through the bucket floor.
            if x>2.01:p.x=side*(2.01+(x-2.01)*(.015/.2181816))
            v.co=I@p
        for mod in ob.modifiers:
            if mod.type=='BEVEL':mod.width=min(mod.width,.0004)
        ob.data.update();changed.append(ob.name)
    assert len(changed)==5,('Expected crown,2 end cheeks, underbody and retained floor only',changed)
    return dict(changed=changed,hinges_doors_contents_psu_mounts_unchanged=True,unchanged_psu_interface_absx_max=2.01,rear_upper_limit_x=2.025,cassette_service_gap_m=.035)


def _handle(ctx,col,side):
    a=ctx.a;a.ACTIVE=col
    removed=_remove(col,('Formed overlapping window shade section18','Retained shade finger pull18'))
    # The inherited pull protruded35.5mm into the business-side console. Form a
    # genuine4mm recess into the existing12mm leaf instead of another raised box.
    inner=_loop(.12,.040,.010,.055);outer=[]
    for y,z,angle in inner:
        dy,dz=math.cos(angle),math.sin(angle);lo,hi=0.,2.
        for _ in range(38):
            t=(lo+hi)/2;yy=dy*t;zz=.055+dz*t
            u,v=abs(yy)-(.35-.025),abs(zz-.1275)-(.1275-.025)
            sdf=math.hypot(max(u,0),max(v,0))+min(max(u,v),0)-.025
            if sdf>0:hi=t
            else:lo=t
        t=(lo+hi)/2;outer.append((dy*t,.055+dz*t))
    n=len(outer);front=[(-side*.006,y,z) for y,z in outer];back=[(side*.006,y,z) for y,z in outer]
    hole=[(-side*.006,y,z) for y,z,_ in inner];deep=[(-side*.002,y*.95,.055+(z-.055)*.85) for y,z,_ in inner]
    ob=a.mesh('W40 shade leaf with actual recessed finger pocket',front+back+hole+deep+[(side*.006,0,.1275)],
        [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]+[(i,2*n+i,2*n+(i+1)%n,(i+1)%n) for i in range(n)]+[(2*n+i,3*n+i,3*n+(i+1)%n,2*n+(i+1)%n) for i in range(n)]+[(4*n,n+i,n+(i+1)%n) for i in range(n)],'W40Pearl')
    _normals(ob,-side)
    a.mesh('W40 recessed finger-pocket lining',deep+[(-side*.002,0,.055)],[(n,i,(i+1)%n) for i in range(n)],'W40Felt')
    return dict(removed=removed,actual_recess_depth_m=.004,leaf_thickness_m=.012,raised_pull_removed=True)


def apply(ctx):
    import bpy
    a=ctx.a;_aliases(a);active=a.ACTIVE;report=dict(version=VERSION,changed_assets=[],kit_details={},source_instances=[])
    for old,new in SWAPS.items():
        col,fresh=_newcopy(ctx,old,new)
        if fresh:
            side=-1 if old.endswith('_L') else 1
            detail=_wall(ctx,col,side) if 'WindowWall' in old else _outer(ctx,col) if old in ('SM_Plane_OuterWindowBarrel','SM_Plane_CargoBay10') else _frame(ctx,col,side) if 'ShadeFrame' in old else _handle(ctx,col,side) if 'ShadeHandle' in old else _rack(ctx,col,side)
            col['window40_version']=VERSION;col['window40_details']=json.dumps(detail)
        report['kit_details'][new]=json.loads(col['window40_details']);report['changed_assets'].append(new)
        a.ASSETS[new]=dict(collection=col,collision='complex')
        for ob in col.objects:
            for m in ob.data.materials if ob.data and hasattr(ob.data,'materials') else []:
                if m:a.MATS[m.name]=m
        previous={old,OLD_DERIVED.get(old),new}
        for ob in ctx.scene.objects:
            if ob.instance_type=='COLLECTION' and ob.instance_collection and ob.instance_collection.name in previous:
                ob.instance_collection=col;report['source_instances'].append(dict(actor=ob.name,asset=new))
        for q in ctx.D.get('instances',[]):
            if q['asset'] in previous:q['asset']=new
    # Source remains editable at the same48 named closed positions used by the
    # runtime data preparation. Only32mm of outboard fit is introduced below.
    offset=ctx.D['aircraft38']['offset'];count=0
    for ob in ctx.scene.objects:
        if not ob.name.startswith('Window shade ') or ob.name.endswith(' frame') or ob.instance_type!='COLLECTION':continue
        suffix='L' if ' L18' in ob.name else 'R';side=-1 if suffix=='L' else 1
        i=int(ob.name.rsplit(' section ',1)[1]) if ' section ' in ob.name else 0
        if not(0<=i<=4):continue
        z=.92+.20*i;ob.location.x=offset[0]+side*(track_x(z)+.006*i);count+=1
    a.ACTIVE=active;report['source_shade_parts_fitted']=count
    ctx.D.setdefault('repair38',{})['window40']=report;return report


def prepare_plane(P,D):
    """After airside/E39 preparation; before configure/Flight39 preparation."""
    if P.DATA.get('window40_prepared'):return
    offset=list(D['aircraft38']['offset']);count=0
    for q in P.DATA['interactions']:
        if q.get('motion',{}).get('type')!='roller_shade18':continue
        side=-1 if ' L18' in q['actor'] else 1;q['window40']=True
        for i,part in enumerate(q['roller_parts']):
            part.update(window40_index=i,window40_side=side,window40_offset=offset)
            part['closed_location']=shade_pose(part,0.);opened=shade_pose(part,1.);part['delta']=[b-a for a,b in zip(part['closed_location'],opened)]
        count+=1
    assert count==48,count
    P.DATA['window40_prepared']=dict(version=VERSION,mechanisms=count,actual_retained_curved_stow=True,original_actor_labels_switch_points_preserved=True)


def install(G):
    """After flight39.install(G), retaining its current moving carrier frame."""
    P=G.P
    if P._apply_movable is getattr(P,'_window40_adapter',None):return dict(installed=True,already_installed=True)
    base=P._apply_movable
    def apply_movable(m):
        q=m['item']
        if not q.get('window40'):return base(m)
        frame=getattr(G,'flight39',{}).get('frame')
        for part in q['roller_parts']:
            pos=P.vector(shade_pose(part,m['progress']));pos=frame.world(pos) if frame else pos
            P.STATE['actors'][part['actor']].set_actor_location(pos,False,False)
    P._apply_movable=apply_movable;P._window40_adapter=apply_movable
    for m in P.STATE['movables'].values():
        if m['item'].get('window40'):apply_movable(m)
    return dict(installed=True,mechanisms=48,carrier_aware=True)


def apply_native(ctx):
    from pathlib import Path
    u=ctx.u;pm=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];targets={q['name']:SWAPS[q['asset']] for q in pm['instances'] if q['asset'] in SWAPS};done=[]
    for actor in ctx.EA.get_all_level_actors():
        name=next((str(t)[8:] for t in actor.tags if str(t).startswith('Skyward:')),None)
        if name not in targets:continue
        c=actor.get_component_by_class(u.StaticMeshComponent);assert c,name;before=actor.get_actor_transform();mesh=ctx.mesh(targets[name]);c.set_static_mesh(mesh)
        for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
        assert before==actor.get_actor_transform(),name;done.append(name)
    assert len(done)==len(targets),(len(done),len(targets));return dict(status='SWAPPED_REQUIRES_VISUAL_REVIEW',instances=len(done),glazing='Run root glass39 after mesh swap')
