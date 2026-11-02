"""Root calls after importing and positioning native38 actors. No engine launch."""
def apply_native(ctx):
    u=ctx.u
    child=ctx.actors.get('Small potted plant24')
    support=ctx.actors.get('ChargingTable24_1749')
    if child is None or support is None:
        raise RuntimeError('Equipment38 requires the plant and charging-table native actors')
    child.static_mesh_component.set_simulate_physics(False)
    child.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    child.attach_to_actor(support,u.Name('None'),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    ctx.D['repair38']['equipment']['native_plant_parent']='ChargingTable24_1749'
