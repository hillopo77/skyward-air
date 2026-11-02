import unreal as u,json,time
G=None;S={}
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('write',0)<1:return
 S['write']=time.monotonic();(G.R/'ArtBible/Session36.json').write_text(json.dumps(dict(status='READY',map=G.D['map'],player=list(G.source(G.P.STATE['pawn'].get_actor_location())),viewport=list(G.P.STATE['pc'].get_viewport_size()),updated=time.time()),indent=2))
def initialize(game):
 global G;G=game;S['base']=G.physics;G.physics=tick
 if '-Detail36Photos' in G.CMD or '-Detail36QA' in G.CMD:
  import detail36_review;detail36_review.start(G,'-Detail36QA' in G.CMD)
 G.event('Detail36 ready',screening_exit='aligned and clear',cafe_bins=3,sofas=2)
