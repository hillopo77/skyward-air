"""Lightweight visual updates with safe level-shutdown handling."""
import unreal as u,time
def start(game):
 state={'pairs':None,'after':0}
 def tick(dt):
  if not game.S.get('initialized') or time.monotonic()<state['after']:return
  state['after']=time.monotonic()+.2
  if not game.alive(game.S.get('pc')):
   u.unregister_slate_post_tick_callback(state['handle']);return
  if state['pairs'] is None:
   actors=u.GameplayStatics.get_all_actors_of_class(game.S['world'],u.StaticMeshActor);details=sorted([a for a in actors if a.get_actor_label().startswith('DeckVisual6 ')],key=lambda a:a.get_actor_label());state['pairs']=[dict(parent=p,detail=d,shown=None) for p,d in zip(game.S['deck_pool'],details)]
  for pair in state['pairs']:
   parent=pair['parent'];detail=pair['detail']
   if not game.alive(parent) or not game.alive(detail):continue
   shown=parent.static_mesh_component.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION
   if shown!=pair['shown']:detail.set_actor_hidden_in_game(not shown);parent.static_mesh_component.set_visibility(not shown,False);pair['shown']=shown
 state['handle']=u.register_slate_post_tick_callback(tick)
