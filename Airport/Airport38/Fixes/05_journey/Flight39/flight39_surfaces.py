"""Promote the existing carefully modeled aircraft parts to real actuators.

Copies inherited source collections; never edits the preserved source library.
Root applies any nose refinement before this build or to F39AirframeFixed.
"""
import math


def _points(ob):
    return [ob.matrix_world@v.co for v in ob.data.vertices]


def _centre(ob):
    from mathutils import Vector
    p=[ob.matrix_world@Vector(q) for q in ob.bound_box]
    return Vector([(min(v[i] for v in p)+max(v[i] for v in p))/2 for i in range(3)])


def _clone(ctx,col,ob,pivot=None):
    import bpy,bmesh
    from mathutils import Matrix
    cp=ob.copy();cp.data=ob.data.copy();cp.parent=None;matrix=ob.matrix_world.copy()
    if pivot is not None:matrix=Matrix.Translation(-pivot)@matrix
    # Bevel/tessellation can generate collinear cap triangles even when the
    # original loft has no zero-area polygon. Canonicalise just those copies
    # after evaluation. The preserved linked source retains editable fonts and
    # modifiers; fixed copies retain the source name/body as metadata.
    deps=ctx._flight39_depsgraph
    ev=ob.evaluated_get(deps);probe=ev.to_mesh();probe.calc_loop_triangles()
    # Bake nontrivial modifiers before world-matrix conversion. Otherwise a
    # source object's scale is baked into vertices while its bevel width stays
    # unscaled, changing the manufactured edge radius (monitor bezel included).
    needs_cleanup=ob.type=='FONT' or bool(ob.modifiers) or any(t.area<1e-12 for t in probe.loop_triangles)
    if needs_cleanup:
        data=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
        old=cp;cp=bpy.data.objects.new(ob.name+' clean39',data)
        if ob.type=='FONT':cp['source_text39']=ob.data.body
        bpy.data.objects.remove(old)
    ev.to_mesh_clear()
    if cp.type=='MESH':
        cp.data.transform(matrix);cp.matrix_world=Matrix.Identity(4)
        # Inherited loft poles sometimes duplicate a ring at radius zero.
        # Repair only our editable copies; preserve UV loops/material slots.
        bm=bmesh.new();bm.from_mesh(cp.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,dist=1e-8,edges=list(bm.edges))
        if needs_cleanup:bmesh.ops.triangulate(bm,faces=list(bm.faces))
        degenerate=[f for f in bm.faces if f.calc_area()<1e-12]
        if degenerate:bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY')
        bm.to_mesh(cp.data);bm.free();cp.data.update()
    else:cp.matrix_world=matrix
    col.objects.link(cp)
    for mat in cp.data.materials:
        if mat:ctx.a.MATS[mat.name]=mat
    return cp


def _hinge(ob,vertical=False):
    from mathutils import Vector
    pts=_points(ob);axisindex=2 if vertical else 0
    if ob.name.startswith('Independent trailing flap'):
        # The gear aperture clips lower-skin polygons into several faces, so
        # those shared corner vertices occur repeatedly in the inherited mesh.
        # A raw average biased the two inner flap hinges in opposite directions.
        # Fit the actual geometric leading-edge endpoints once per position;
        # the evaluated neutral loft and all other surface hinges are untouched.
        pts=list({tuple(round(float(v),6) for v in p):p for p in pts}.values())
    ends=[min(p[axisindex] for p in pts),max(p[axisindex] for p in pts)]
    if not vertical and abs(ends[0])>abs(ends[1]):ends.reverse()
    hinge=[]
    for edge in ends:
        row=[p for p in pts if abs(p[axisindex]-edge)<.0002]
        y=min(p.y for p in row);near=[p for p in row if abs(p.y-y)<.0002]
        hinge.append(sum(near,Vector())/len(near))
    return hinge[0],(hinge[1]-hinge[0]).normalized()


def build(ctx):
    import bpy
    from mathutils import Vector
    D=ctx.D;meta=D['flight39'];src=bpy.data.collections.get('SM_Plane_ExteriorAirframe')
    # Capture once before copying. Repeated evaluated_depsgraph_get inside
    # hundreds of copies would force a full airport evaluation for each part.
    ctx._flight39_depsgraph=bpy.context.evaluated_depsgraph_get()
    if src is None:raise KeyError('Loaded editable aircraft source collection missing')
    moving=[o for o in src.objects if o.type=='MESH' and o.name.startswith(('Independent trailing flap','Independent outboard aileron','Separate hinged elevator','Separate vertical rudder'))]
    assert len(moving)==13,('Actual modeled flight surfaces',len(moving))
    fixed=ctx.new_collection('F39AirframeFixed','complex')
    for ob in src.objects:
        if ob not in moving:_clone(ctx,fixed,ob)
    meta['airframe_fixed_asset']=fixed.name;meta['surface_records']=[];meta['moving_names']=[]
    for i,ob in enumerate(moving):
        role='flap' if ob.name.startswith('Independent trailing flap') else 'aileron' if ob.name.startswith('Independent outboard') else 'elevator' if ob.name.startswith('Separate hinged') else 'rudder'
        pivot,axis=_hinge(ob,role=='rudder');side=1 if pivot.x>0 else -1
        aid='F39Surface_%02d'%i;col=ctx.new_collection(aid,'none');_clone(ctx,col,ob,pivot)
        actor='Flight39 '+role+' %02d'%i
        location=[pivot.x+16,pivot.y,pivot.z]
        ctx.add(col.name,actor,location,collision=False,flight39_actuator=True,native_individual=True)
        meta['surface_records'].append(dict(actor=actor,asset=col.name,role=role,side=side,pivot=location,axis=list(axis),original_part=ob.name))
        meta['moving_names'].append(actor)
    ob=ctx.scene.objects.get('SM_Plane_ExteriorAirframe')
    if ob:ob.instance_collection=fixed

    dashboard=bpy.data.collections.get('SM_Plane_AnalogDashboard')
    assert dashboard,'Editable analog dashboard missing'
    hubs=[o for o in dashboard.objects if o.name.startswith('Needle hub')]
    needles=[o for o in dashboard.objects if o.name.startswith('Instrument needle')]
    glasses=[o for o in dashboard.objects if o.name.startswith('Instrument cover glass')]
    mapping=[('airspeed',[.48116,-4.7464,1.18]),('altitude',[.48115,-4.74635,.93]),
             ('fuel',[.4922,-4.8019,1.33]),('temperature',[1.0611,-4.5576,.975]),
             ('vertical_speed',[-.56281,-4.72962,1.26]),('engine_rpm',[-.76416,-4.67248,1.15]),
             ('oil_pressure',[-1.19123,-4.55582,1.22])]
    selected=[];meta['instrument_records']=[]
    for i,(role,expected) in enumerate(mapping):
        point=Vector(expected);hub=min(hubs,key=lambda o:(_centre(o)-point).length);pivot=_centre(hub)
        needle=min([n for n in needles if n not in selected],key=lambda o:(_centre(o)-pivot).length);selected.append(needle)
        assert (_centre(needle)-pivot).length<.08,(role,needle.name)
        glass=min(glasses,key=lambda o:(_centre(o)-pivot).length);axis=(_centre(glass)-pivot).normalized()
        if axis.y<0:axis=-axis
        up=(Vector((0,0,1))-axis*axis.z).normalized();right=axis.cross(up).normalized()
        radial=max(_points(needle),key=lambda p:(p-pivot).length)-pivot
        alpha=math.degrees(math.atan2(radial.dot(right),radial.dot(up)))
        col=ctx.new_collection('F39Needle_%02d'%i,'none');_clone(ctx,col,needle,pivot)
        actor='Flight39 instrument '+role;loc=[pivot.x+16,pivot.y,pivot.z]
        ctx.add(col.name,actor,loc,collision=False,flight39_actuator=True,native_individual=True)
        meta['instrument_records'].append(dict(actor=actor,asset=col.name,role=role,pivot=loc,axis=list(axis),initial_angle=alpha))
        meta['moving_names'].append(actor)
    fixed_dash=ctx.new_collection('F39DashboardFixed','complex');removed_words=[]
    for ob in dashboard.objects:
        if ob in selected:continue
        if ob.type=='FONT' and ob.data.body in {'CABIN','READY','DOORS','SECURE','FLIGHT','NORMAL'}:
            p=_centre(ob)
            if 2.16<p.z<2.36 and abs(p.y+4.26)<.03:removed_words.append(ob.data.body);continue
        _clone(ctx,fixed_dash,ob)
    assert len(removed_words)==6,('False static flight-status words removed',removed_words)
    meta['dashboard_fixed_asset']=fixed_dash.name;meta['removed_static_status_words']=removed_words
    ob=ctx.scene.objects.get('SM_Plane_AnalogDashboard')
    if ob:ob.instance_collection=fixed_dash
    meta['status_text_position']=[15.76,-4.249,2.29]
    meta['status_text_normal']=[0,1,0]
    meta['modeled_actuators']=dict(surfaces=len(moving),instrument_needles=len(selected),original_parts_preserved=True)
    return meta['modeled_actuators']
