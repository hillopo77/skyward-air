"""Match the authored planted-foot cycle to actual airport walking and pauses."""
WALK_REFERENCE_M_S=.580645
G=None;S={}

def install(game):
 global G;G=game
 import characters12_runtime as C
 if S.get('installed'):return
 S.update(installed=True,base=C.tick,characters=C,last={})
 C.tick=tick

def _apply(name,actor,clip,speed):
 C=S['characters'];key=(clip,round(min(2.5,max(.35,speed/WALK_REFERENCE_M_S)) if clip=='Walk' else 1.,3))
 previous=S['last'].get(name)
 if previous==key:return
 c=actor.skeletal_mesh_component
 if previous is None or previous[0]!=clip:c.play_animation(C.CLIPS[clip],True)
 c.set_play_rate(key[1]);S['last'][name]=key

def tick(dt):
 C=S['characters'];walkers=C.S.get('walkers',{})
 before={n:C.ACTORS[n].get_actor_location() for n in walkers if n in C.ACTORS}
 S['base'](dt)
 greetings=C.S.get('greetings',{})
 for name in greetings:
  if name in C.ACTORS:
   C.ACTORS[name].skeletal_mesh_component.set_play_rate(1.)
   S.setdefault('queue_rates',{}).pop(name,None)
 for name,origin in before.items():
  if G.QA:continue
  if name in greetings:S['last'].pop(name,None);continue
  actor=C.ACTORS[name];delta=actor.get_actor_location()-origin
  speed=(delta.x*delta.x+delta.y*delta.y)**.5/max(dt,.001)/100
  _apply(name,actor,'Walk' if speed>.03 else 'Idle',speed)
 # The staffed queue has its own measured115cm/s path and pause policy.
 for name,clip in getattr(G,'journey38',{}).get('state',{}).get('queue',{}).get('clips',{}).items():
  if name in C.ACTORS and name not in greetings:
   rate=round(1.15/WALK_REFERENCE_M_S,3) if clip=='Walk' else 1.
   if S.setdefault('queue_rates',{}).get(name)!=rate:
    C.ACTORS[name].skeletal_mesh_component.set_play_rate(rate);S['queue_rates'][name]=rate
