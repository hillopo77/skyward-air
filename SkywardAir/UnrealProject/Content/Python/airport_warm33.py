"""Runtime evidence for the source-driven lighting revision."""
import unreal as u,time,json
G=None;S={}
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('written',0)<1:return
 S['written']=time.monotonic();(G.R/'ArtBible/WarmSession33.json').write_text(json.dumps(dict(status='READY',map=G.D['map'],viewport=list(G.P.STATE['pc'].get_viewport_size()),fixture_sources=len(S['lights']),source_positions_match=all((a.get_actor_location()-G.v(q['position'])).length()<1 for a,q in S['lights']),panels_face_down=all(a.get_actor_forward_vector().z<-.99 for a,q in S['lights'][5:7]),updated=time.time()),indent=2))
def initialize(game):
 global G;G=game;world=G.P.STATE['world'];by={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.RectLight)};specs=[q for q in G.D['lights'] if q.get('revision')==33];S.update(base=G.physics,lights=[(by[q['native_actor']],q) for q in specs]);G.physics=tick
 if '-Warm33QA' in G.CMD:
  import warm33_qa;warm33_qa.start(G)
