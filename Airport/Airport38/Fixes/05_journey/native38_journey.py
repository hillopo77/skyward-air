"""Native preparation; root calls after importing the new mesh families."""
def apply_conveyor_physics(ctx):
    """Roller-contact material for real-body velocity control and braking.

    Default architectural static friction can exceed the conveyor motor's
    whole drive acceleration. The rollers need their own contact properties,
    rather than a teleport or an early registration escape hatch.
    """
    u=ctx.u;path=ctx.B+'/Physics/PM_AP38_ConveyorRollers'
    pm=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else u.AssetToolsHelpers.get_asset_tools().create_asset(
        'PM_AP38_ConveyorRollers',ctx.B+'/Physics',u.PhysicalMaterial,u.PhysicalMaterialFactoryNew())
    mode=next(getattr(u.FrictionCombineMode,n) for n in dir(u.FrictionCombineMode) if n.lower()=='min')
    for k,v in dict(friction=.045,static_friction=.055,restitution=0.,
                    override_friction_combine_mode=True,friction_combine_mode=mode,
                    override_restitution_combine_mode=True,restitution_combine_mode=mode).items():pm.set_editor_property(k,v)
    assert abs(pm.get_editor_property('friction')-.045)<1e-6
    assert pm.get_editor_property('override_friction_combine_mode')
    u.EditorAssetLibrary.save_loaded_asset(pm)
    aids={'SM_AP_Belt38','SM_AP_Transfer38','SM_AP_Outfeed38'}
    meshes=[]
    for aid in aids:
        sm=ctx.mesh(aid)
        if not sm:continue
        sm.get_editor_property('body_setup').set_editor_property('phys_material',pm)
        u.EditorAssetLibrary.save_loaded_asset(sm);meshes.append(aid)
    components=[]
    for actor in ctx.EA.get_all_level_actors():
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            sm=c.get_editor_property('static_mesh')
            if sm and sm.get_name() in aids:
                c.set_phys_material_override(pm);components.append(actor.get_actor_label())
    return dict(material=path,friction=.045,static_friction=.055,combine='MIN',restitution=0.,meshes=sorted(meshes),components=components)


def apply_native(ctx):
    u=ctx.u
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem) or u.StaticMeshEditorSubsystem()
    sm=ctx.mesh('SM_AP_ServingCup38')
    editor.remove_collisions(sm)
    editor.add_simple_collisions(sm,u.ScriptingCollisionShapeType.NDOP26)
    sm.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_DEFAULT)
    u.EditorAssetLibrary.save_loaded_asset(sm)
    names={q['actor'] for q in ctx.D['repair38']['equipment']['curtains']}
    names|={'Baggage service door38','Cloud Nine serving cup38'}
    for n in names:
        a=ctx.actors.get(n)
        if a:a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    from roller_contact38 import apply_native as apply_roller_contact
    return dict(dynamic_cup_convex=True,movable_actors=sorted(names),conveyor_contact=apply_roller_contact(ctx))
