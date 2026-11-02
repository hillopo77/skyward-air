"""Scoped modeled fittings39. Current-master source apply + native/data hooks.

Keeps aircraft dimensions, six actual windscreen apertures, glazing meshes,
interactive actor labels, pivots, targets and closed shade poses unchanged.
"""
import json,math,copy
from pathlib import Path

SWAPS={
 'SM_Plane_CockpitShell':'SM_AP_E39CockpitShellClean',
 'SM_Plane_WindowShadeFrame18_L':'SM_AP_E39ShadeFrameL',
 'SM_Plane_WindowShadeFrame18_R':'SM_AP_E39ShadeFrameR',
 'SM_Plane_OuterWindowBarrel':'SM_AP_E39WeatherSeals',
 'SM_Plane_PassengerDoor07_L':'SM_AP_E39PassengerDoorL',
 'SM_Plane_PassengerDoor07_R':'SM_AP_E39PassengerDoorR',
}
STOW_INBOARD=.12

def pressure_x(z):
    return 2.5*max(.000001,1-abs((z-.55)/2.35)**3.6)**(1/3.6)

def _matrix(obj):
    from mathutils import Matrix
    return Matrix.LocRotScale(obj.location,obj.rotation_euler.to_quaternion(),obj.scale)

def _clone(ctx,old,new):
    import bpy
    col=bpy.data.collections.get(new)
    if col:return col,False
    src=bpy.data.collections.get(old);assert src,('Preserved fitting asset missing',old)
    col=bpy.data.collections.new(new)
    for ob in src.objects:
        q=ob.copy()
        if ob.data:q.data=ob.data.copy()
        col.objects.link(q)
        if q.type in ('MESH','FONT'):
            for m in q.data.materials:
                if m:ctx.a.MATS['E39Borrowed_'+m.name]=m
    col['exterior39_from']=old
    return col,True

def _material_aliases(a):
    import bpy
    for short,name in [('E39Pearl','MI_Plane_White'),('E39Seal','MI_Plane_Seal08'),('E39Felt','MI_Plane_Graphite')]:
        m=bpy.data.materials.get(name)
        assert m,('Preserved material missing',name)
        a.MATS[short]=m

def _shade_pocket(ctx,col,side):
    """Formed hollow pocket and retained C guides, inside the curved pressure skin."""
    import bpy
    a=ctx.a;before=[]
    prefixes=('Shade captive guide channel18','Shade retained upper pocket18','Shade pocket dark felt mouth18')
    for o in list(col.objects):
        if o.name.startswith(prefixes):before.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    active=a.ACTIVE;a.ACTIVE=col
    def local(x,y,z):return (side*(x-2.3),y,z-.92)
    # C-guide cross-sections are real open channels. The .34..37m groove
    # captures the .35m slat edge throughout its inboard stow stroke.
    for edge in (-1,1):
        rings=[]
        for z in (.905,1.30,1.70,1.975,2.015):
            outer=min(2.36,pressure_x(z)-.035);inner=2.15
            cross=[(outer,.34),(outer,.384),(inner,.384),(inner,.34),
                   (inner+.014,.34),(inner+.014,.37),(outer-.014,.37),(outer-.014,.34)]
            rings.append([local(x,edge*y,z) for x,y in cross])
        o=a.loft('E39 continuous formed open C guide',rings,'E39Pearl',True,True)
        b=o.modifiers.new('Guide edge roll39','BEVEL');b.width=.002;b.segments=3
        # A thin felt wear strip seats on the channel back, not on the glass.
        a.loft('E39 retained guide felt',[ [local(2.17,edge*y,z) for y in (.371,.378)] for z in (.91,2.01)],'E39Felt',False,False)
    # The curved shell has separate inner/outer skins and closed ends/top.
    # The underside is the genuine feed aperture for five telescoping sections.
    zvals=[1.975,2.02,2.065,2.11,2.155,2.20,2.25]
    loops=[]
    for z in zvals:
        out=pressure_x(z)-.045;inside=min(2.155,out-.13)
        loops.append([local(x,y,z) for x,y in [(inside,-.415),(out,-.415),(out,.415),(inside,.415)]])
    n=4;verts=[p for loop in loops for p in loop]
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(loops)-1) for i in range(n)]
    faces.append(tuple((len(loops)-1)*n+i for i in range(n)))
    o=a.mesh('E39 curved hollow shade pocket shell',verts,faces,'E39Pearl',.003)
    # Give the shell actual wall thickness without closing its feed opening.
    mod=o.modifiers.new('Pocket formed thickness39','SOLIDIFY');mod.thickness=.012
    # Captive top support and recessed felt mouth are fitted to the opening.
    a.tube('E39 rounded pocket feed lip',[local(2.155,-.405,1.978),local(2.155,.405,1.978)],.006,'E39Felt',10)
    for y in (-.385,.385):
        a.loft('E39 pocket end cap return',[
            [local(2.155,y,1.975),local(pressure_x(1.975)-.045,y,1.975)],
            [local(pressure_x(2.25)-.175,y,2.25),local(pressure_x(2.25)-.045,y,2.25)]],
            'E39Pearl',False,False)
    a.ACTIVE=active
    return dict(removed=before,pressure_skin_clearance_m=.035,pocket_top_z=2.25,
                cavity_open_below=True,guide_retains_slat_edge_y=.35,stow_inboard_m=STOW_INBOARD)

def _weather_seals(ctx,col):
    import bpy,bmesh
    from mathutils import Vector
    a=ctx.a;active=a.ACTIVE;a.ACTIVE=col;records=[]
    for old in list(col.objects):
        if old.type!='MESH' or not old.name.startswith('Flush glazing weather seal09'):continue
        T=_matrix(old);raw=[]
        assert len(old.data.vertices)%8==0
        for i in range(0,len(old.data.vertices),8):
            raw.append(sum((T@old.data.vertices[j].co for j in range(i,i+8)),Vector())/8)
        path=[]
        for p in raw:
            if not path or (p-path[-1]).length>.0003:path.append(p)
        if (path[-1]-path[0]).length<.0003:path.pop()
        verts=[];normals=[];count=len(path)
        for i,p in enumerate(path):
            t=(path[(i+1)%count]-path[(i-1)%count]).normalized();side=1 if p.x>0 else -1
            outward=Vector((side,0,0));e1=(outward-t*outward.dot(t)).normalized();e2=t.cross(e1).normalized()
            for j in range(12):
                n=e1*math.cos(j*math.tau/12)+e2*math.sin(j*math.tau/12)
                verts.append(p+n*.003);normals.append(n)
        faces=[(i*12+j,((i+1)%count)*12+j,((i+1)%count)*12+(j+1)%12,i*12+(j+1)%12) for i in range(count) for j in range(12)]
        obj=a.mesh('E39 continuous swept opaque weather gasket',verts,faces,'E39Seal')
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
        score=sum(p.normal.dot(normals[p.vertices[0]])*p.area for p in obj.data.polygons)
        if score<0:
            bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
        obj.data.normals_split_custom_set([normals[l.vertex_index] for l in obj.data.loops])
        records.append(dict(replaced=old.name,original_path_samples=len(raw),clean_path_samples=count,profile_radius_m=.003,stable_radial_frame=True))
        bpy.data.objects.remove(old,do_unlink=True)
    a.ACTIVE=active;assert len(records)==2,records
    return records

def _upgrade_guides(col,side):
    """Version2: outboard lower shoes clear the business suite side shell."""
    import bmesh
    from mathutils import Vector
    if col.get('e39_guidefit_version',0)>=2:return False
    for obj in col.objects:
        if obj.type!='MESH' or not obj.name.startswith(('E39 continuous formed open C guide','E39 retained guide felt')):continue
        obj.data=obj.data.copy();bm=bmesh.new();bm.from_mesh(obj.data)
        # Create a true manufactured knee at1.40m, above the suite shell top.
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,
                              plane_co=Vector((0,0,.48)),plane_no=Vector((0,0,1)),clear_inner=False,clear_outer=False)
        bm.to_mesh(obj.data);bm.free();T=_matrix(obj);inv=T.inverted()
        for v in obj.data.vertices:
            p=T@v.co;z=p.z+.92;x=abs(side*2.3+p.x);outer=min(2.36,pressure_x(z)-.035)
            inner=2.334 if z<=1.4 else max(2.15,2.334-(z-1.4)*(.184/.52))
            t=(x-2.15)/(outer-2.15);xx=inner+t*(outer-inner)
            p.x=side*(xx-2.3);v.co=inv@p
        obj.data.update()
        for m in obj.modifiers:
            if m.type=='BEVEL':m.width=min(m.width,.0006)
        if obj.name.startswith('E39 continuous formed open C guide'):
            bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    col['e39_guidefit_version']=2
    return True

def prepare_plane(P,D):
    """After airside +16 translation, before flight-frame/configure.

    Changes only the stow displacement; all original closed poses, target points,
    names and current interaction semantics remain untouched.
    """
    data=P.DATA;changed=0
    if data.get('exterior39_shades'):return
    offset=D.get('aircraft38',{}).get('offset',[16,0,0])[0]
    for q in data.get('interactions',[]):
        if not q.get('roller_parts'):continue
        side=1 if q['roller_parts'][0]['closed_location'][0]-offset>0 else -1
        for part in q['roller_parts']:
            part['delta'][0]=-side*STOW_INBOARD
        q['exterior39_stow']=True;changed+=1
    data['exterior39_shades']=dict(interactions=changed,inboard_stow_m=STOW_INBOARD,closed_poses_preserved=True)
    assert changed>=30,('Expected all passenger shades',changed)
    D.setdefault('repair38',{}).setdefault('exterior39',{})['runtime_shades']=data['exterior39_shades']

def apply(ctx):
    import bpy
    from mathutils import Vector
    _material_aliases(ctx.a)
    result=dict(passes=[],swaps=SWAPS,changed_assets=[],source_instances=[])
    result['passes'].append(dict(pass_id=1,work='Measured linked source fittings and real screenshots; identified 6 redundant windscreen tubes, protruding shade pockets and glass-assigned rubber weather seals.'))
    for old,new in SWAPS.items():
        col,fresh=_clone(ctx,old,new)
        if fresh:
            if old=='SM_Plane_CockpitShell':
                panes=[o for o in col.objects if o.name.startswith('Fitted curved cockpit glazing11')]
                pane_points={o.name:[tuple(_matrix(o)@v.co) for v in o.data.vertices] for o in panes}
                removed=[]
                for o in list(col.objects):
                    if o.name.startswith('Fitted rounded pearl glazing reveal18'):
                        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
                assert len(removed)==6,removed
                assert len(panes)==6
                assert all(pane_points[o.name]==[tuple(_matrix(o)@v.co) for v in o.data.vertices] for o in panes)
                col['exterior39_details']=json.dumps(dict(removed=removed,actual_panes=6,glazing_vertices_unchanged=True))
            elif 'WindowShadeFrame18' in old:
                details=_shade_pocket(ctx,col,-1 if old.endswith('_L') else 1)
                col['exterior39_details']=json.dumps(details)
            elif old=='SM_Plane_OuterWindowBarrel':
                fixed=_weather_seals(ctx,col)
                col['exterior39_details']=json.dumps(dict(opaque_weather_seals=fixed,previous_incorrect_material='MI_Plane_SkyGlass18'))
            else:
                leaf=next(o for o in col.objects if o.name.startswith('Pressure door formed leaf with bored viewport'))
                b=leaf.modifiers.new('Pressure leaf manufactured edge roll39','BEVEL');b.width=.004;b.segments=3;b.limit_method='ANGLE';b.angle_limit=math.radians(28)
                leaf.modifiers.new('Pressure leaf weighted normals39','WEIGHTED_NORMAL')
                col['exterior39_details']=json.dumps(dict(door_pivot_unchanged=True,viewport_aperture_unchanged=True,edge_radius_m=.004))
            # Thin inherited closed-box bevels previously collapse corners at
            # half thickness. Limit actual fillets without changing dimensions.
            clamps=[]
            for o in col.objects:
                if o.type!='MESH':continue
                ext=[max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in range(3)] if o.data.vertices else []
                if not ext:continue
                for m in o.modifiers:
                    if m.type=='BEVEL' and min(ext)>0 and m.width>min(ext)*.18:
                        clamps.append(dict(part=o.name,old=m.width,new=min(ext)*.18));m.width=min(ext)*.18
            col['exterior39_clamps']=json.dumps(clamps)
        if 'WindowShadeFrame18' in old:
            _upgrade_guides(col,-1 if old.endswith('_L') else 1)
            details=json.loads(col['exterior39_details']);details.update(guidefit_version=2,lower_guide_inner_abs_x=2.334,business_shell_top_z=1.3565,guide_knee_z=1.40)
            col['exterior39_details']=json.dumps(details)
        ctx.a.ASSETS[new]=dict(collection=col,collision='complex')
        result['changed_assets'].append(new)
        result.setdefault('details',{})[new]=json.loads(col.get('exterior39_details','{}'))
    result['passes'].append(dict(pass_id=2,work='Removed only the6 added pearl tube outlines; retained6 real curved panes and true pressure-shell aperture edges at exact coordinates.'))
    result['passes'].append(dict(pass_id=3,work='Remodeled curved hollow shade pockets, actual open C guide channels, supported felt mouths/end returns; specified coherent inboard stow stroke.'))
    result['passes'].append(dict(pass_id=4,work='Restored opaque rubber for2 weather seals, rolled both bored pressure-door leaf edges, clamped collapsed thin bevels.'))
    manifest=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
    for ins in manifest['instances']:
        if ins['asset'] not in SWAPS:continue
        o=ctx.scene.objects.get(ins['name'])
        if o:
            o.instance_collection=bpy.data.collections[SWAPS[ins['asset']]]
            o['exterior39_from']=ins['asset'];result['source_instances'].append(ins['name'])
    result['passes'].append(dict(pass_id=5,work='Refreshed source instance bindings and exact original actor swap map; evaluated fit/stroke/viewport tests are recorded separately, native visual approval remains required.'))
    ctx.D.setdefault('repair38',{})['exterior39']=result
    return result

def finalize(ctx):
    """Safe current-master upgrade, including frames already derived by v1."""
    return apply(ctx)

def apply_native(ctx):
    u=ctx.u
    manifest=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
    replacements={q['name']:SWAPS[q['asset']] for q in manifest['instances'] if q['asset'] in SWAPS}
    actors=ctx.EA.get_all_level_actors();done=[]
    for actor in actors:
        key=next((str(t)[8:] for t in actor.tags if str(t).startswith('Skyward:')),None)
        if key not in replacements:continue
        c=actor.get_component_by_class(u.StaticMeshComponent);assert c,actor.get_actor_label()
        old=actor.get_actor_transform();mesh=ctx.mesh(replacements[key]);c.set_static_mesh(mesh)
        # Prior glass39 component overrides would otherwise keep the rebuilt
        # rubber-seal slot translucent after replacing the mesh underneath it.
        for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
        assert actor.get_actor_transform()==old,('Fitting swap changed an interactive pivot',key)
        done.append(dict(actor=key,asset=replacements[key]))
    assert len(done)==len(replacements),(len(done),len(replacements))
    return dict(status='SWAPPED_REQUIRES_NATIVE_VISUAL_REVIEW',instances=done,actor_transforms_preserved=True,glazing_materials='Root glass39 must run after this import for the inherited glass slot roles.')
