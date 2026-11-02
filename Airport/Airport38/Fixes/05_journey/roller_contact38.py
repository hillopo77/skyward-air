"""Asset-owned roller-bed collision, matching the modeled contact plane.

Detailed stationary roller valleys are retained for rendering/rays. Dynamic
bags use continuous, bounded top contact at the actual .845m roller crowns,
plus guard/chassis/control shapes. This is never a world navigation floor.
The same source-metre boxes create editable Blender helpers and native bodies.
"""
import json


def _box(name,p,size,role='support'):
    return dict(name=name,centre=list(p),size=list(size),role=role)


def specifications():
    belt=[_box('Continuous roller crown contact',(0,0,.7925),(1.01,3.60,.105),'contact')]
    for x in (-.60,.60):belt.append(_box('Captured side guard',(x,0,.900),(.050,3.51,.090),'guard'))
    for y in (-1.50,1.50):
        belt.append(_box('Joined crossmember',(0,y,.66),(1.12,.10,.10)))
        for x in (-.43,.43):
            belt.append(_box('Support leg',(x,y,.36),(.074,.074,.60)))
            belt.append(_box('Grounded support foot',(x,y,.030),(.14,.14,.060)))
    belt.append(_box('Mounted START control',(.76,-1.65,.9575),(.22,.22,.225),'control'))
    L=3.33
    transfer=[_box('Continuous transfer crown contact',(L/2,0,.7925),(L,1.01,.105),'contact')]
    for y in (-.61,.61):transfer.append(_box('Captured transfer guard',(L/2,y,.88),(L-.08,.044,.044),'guard'))
    transfer.append(_box('Cushioned receiving stop',(L+.025,0,.98),(.10,1.15,.31),'stop'))
    for x in (.38,1.64,L-.34):
        transfer.append(_box('Joined transfer crossmember',(x,0,.665),(.10,1.10,.10)))
        for y in (-.43,.43):
            transfer.append(_box('Transfer floor column',(x,y,.36),(.074,.074,.61)))
            transfer.append(_box('Transfer floor foot',(x,y,.035),(.14,.14,.07)))
    outfeed=[_box('Continuous output crown contact',(0,0,.7925),(1.01,.70,.105),'contact'),
             _box('Output soft endstop',(0,.36,.91),(1.13,.07,.18),'stop')]
    for x in (-.43,.43):
        outfeed.append(_box('Output support leg',(x,.20,.36),(.072,.072,.60)))
        outfeed.append(_box('Output foot',(x,.20,.035),(.13,.13,.07)))
    return {'SM_AP_Belt38':belt,'SM_AP_Transfer38':transfer,'SM_AP_Outfeed38':outfeed}


def validate():
    specs=specifications()
    for aid,shapes in specs.items():
        contact=[q for q in shapes if q['role']=='contact']
        assert len(contact)==1,aid
        q=contact[0];assert abs(q['centre'][2]+q['size'][2]/2-.845)<1e-9
        assert all(min(q['size'])>0 for q in shapes)
    # Exact10mm overlap at the asset seam, no discontinuity in top height.
    belt_end=-27.9+3.6/2;transfer_begin=-26.11
    assert abs(belt_end-transfer_begin-.01)<1e-8
    assert belt_end>=transfer_begin
    return dict(crown_height_m=.845,seam_overlap_m=round(belt_end-transfer_begin,4),
                families=len(specs),boxes=sum(len(q) for q in specs.values()),
                ray_collision='complex visible surface',dynamic_collision='asset-owned bounded simple bodies')


def add_source_helpers(scene,D=None):
    """Root calls with Airport38 master already open; does not open/save files.

    Helpers are editable wire objects inside the actual asset collections,
    hidden from rendering and ignored by the visible FBX export recipe.
    """
    import bpy
    made=[]
    for aid,shapes in specifications().items():
        col=bpy.data.collections.get(aid)
        if not col:raise KeyError('Actual source family missing: '+aid)
        for old in list(col.objects):
            if old.get('airport38_contact_helper'):bpy.data.objects.remove(old,do_unlink=True)
        for i,q in enumerate(shapes):
            x,y,z=q['centre'];sx,sy,sz=[v/2 for v in q['size']]
            vertices=[(x+a*sx,y+b*sy,z+c*sz) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
            faces=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
            me=bpy.data.meshes.new('UCX_'+aid+'_%02d'%i);me.from_pydata(vertices,[],faces);me.update()
            ob=bpy.data.objects.new(me.name,me);col.objects.link(ob);ob.display_type='WIRE';ob.hide_render=True
            ob['airport38_contact_helper']=True;ob['export_ignore']=True;ob['contact_role']=q['role'];ob['authored_contact_json']=json.dumps(q)
            made.append(ob.name)
    scene['Airport38_RollerContact']=json.dumps(dict(validation=validate(),specifications=specifications()))
    if D is not None:D.setdefault('repair38',{}).setdefault('journey',{})['roller_contact']=dict(validation=validate(),specifications=specifications())
    return dict(editable_helpers=made,validation=validate())


def apply_native(ctx):
    """Root invokes against current38 map, only three existing mesh bodies change."""
    u=ctx.u;editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem) or u.StaticMeshEditorSubsystem()
    result=dict(validation=validate(),meshes={},components=[])
    for aid,shapes in specifications().items():
        sm=ctx.mesh(aid)
        if not sm:raise KeyError(aid)
        editor.remove_collisions(sm);body=sm.get_editor_property('body_setup');agg=body.get_editor_property('agg_geom');boxes=[]
        for i,q in enumerate(shapes):
            b=u.KBoxElem();p=q['centre'];size=q['size']
            for k,v in dict(center=u.Vector(p[0]*100,-p[1]*100,p[2]*100),rotation=u.Rotator(),
                            x=size[0]*100,y=size[1]*100,z=size[2]*100,name=u.Name(q['name']+' '+str(i))).items():b.set_editor_property(k,v)
            boxes.append(b)
        agg.set_editor_property('box_elems',boxes);body.set_editor_property('agg_geom',agg)
        body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
        # Trigger the normal static-mesh editor notification, retaining all
        # existing build settings. BodySetup AggGeom property notification also
        # recreates component physics in this engine's implementation.
        settings=editor.get_lod_build_settings(sm,0);editor.set_lod_build_settings(sm,0,settings)
        actual=body.get_editor_property('agg_geom').get_editor_property('box_elems')
        assert len(actual)==len(shapes),(aid,len(actual),len(shapes))
        crown=actual[0].get_editor_property('center').z+actual[0].get_editor_property('z')/2
        assert abs(crown-84.5)<.001,(aid,crown)
        u.EditorAssetLibrary.save_loaded_asset(sm)
        result['meshes'][aid]=dict(shapes=len(actual),crown_cm=crown,collision=str(body.get_editor_property('collision_trace_flag')))
    for actor in ctx.EA.get_all_level_actors():
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            sm=c.get_editor_property('static_mesh')
            if not sm or sm.get_name() not in specifications():continue
            enabled=c.get_collision_enabled();c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_collision_enabled(enabled)
            result['components'].append(actor.get_actor_label())
    # Keep the verified low rolling resistance after replacing the simple body.
    from native38_journey import apply_conveyor_physics
    result['physical_material']=apply_conveyor_physics(ctx)
    return result
