import unreal as u,json,math,time
from pathlib import Path
R=Path(__file__).resolve().parent;assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Airport37/L_Airport_Clarity37');rows=[];lights=[]
def src(v):return [round(v.x/100,6),round(-v.y/100,6),round(v.z/100,6)]
for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if isinstance(actor,(u.RectLight,u.PointLight,u.SpotLight,u.DirectionalLight,u.SkyLight)):
  lc=actor.get_component_by_class(u.LightComponent);lights.append(dict(actor=actor.get_actor_label(),type=actor.get_class().get_name(),position=src(actor.get_actor_location()),intensity=lc.get_editor_property('intensity') if lc else None))
 for c in actor.get_components_by_class(u.StaticMeshComponent):
  sm=c.get_editor_property('static_mesh')
  if not sm:continue
  ts=[c.get_instance_transform(i,True) for i in range(c.get_instance_count())] if isinstance(c,u.InstancedStaticMeshComponent) else [c.get_world_transform()]
  b=sm.get_bounds();materials=[m.get_path_name() if m else None for m in c.get_materials()]
  for i,t in enumerate(ts):
   pts=[u.MathLibrary.transform_location(t,b.origin+u.Vector(sx*b.box_extent.x,sy*b.box_extent.y,sz*b.box_extent.z)) for sx in [-1,1] for sy in [-1,1] for sz in [-1,1]];ps=[src(p) for p in pts];mn=[min(p[k] for p in ps) for k in range(3)];mx=[max(p[k] for p in ps) for k in range(3)]
   rows.append(dict(actor=actor.get_actor_label(),component=c.get_name(),instance=i if isinstance(c,u.InstancedStaticMeshComponent) else None,mesh=sm.get_path_name(),location=src(t.translation),rotation=[t.rotation.rotator().pitch,t.rotation.rotator().yaw,t.rotation.rotator().roll],bounds_min=mn,bounds_max=mx,visible=c.get_editor_property('visible'),hidden=c.get_editor_property('hidden_in_game'),collision=str(c.get_collision_enabled()),profile=str(c.get_collision_profile_name()),simulating=c.is_simulating_physics(),mobility=str(c.get_editor_property('mobility')),materials=materials))
(R/'AuditInventory38.json').write_text(json.dumps(dict(map='/Game/Airport37/L_Airport_Clarity37',actors=rows,lights=lights),indent=2));print('AUDIT38 native rows',len(rows))
