"""Visual details only; no body, collision, velocity or constraint changes."""
import unreal as u
def start(game):
 state={'pairs':None}
 def tick(dt):
  if not game.S.get('initialized'):return
  if state['pairs'] is None:
   actors=u.GameplayStatics.get_all_actors_of_class(game.S['world'],u.StaticMeshActor);details=sorted([a for a in actors if a.get_actor_label().startswith('DeckVisual6 ')],key=lambda a:a.get_actor_label());state['pairs']=[dict(parent=p,detail=d,shown=None) for p,d in zip(game.S['deck_pool'],details)]
  for pair in state['pairs']:
   parent=pair['parent'];shown=parent.static_mesh_component.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION
   if shown!=pair['shown']:pair['detail'].set_actor_hidden_in_game(not shown);parent.static_mesh_component.set_visibility(not shown,False);pair['shown']=shown
 state['handle']=u.register_slate_post_tick_callback(tick)
