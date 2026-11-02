import unreal as u,json,time
G=None;S={}
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('write',0)<1:return
 S['write']=time.monotonic();(G.R/'ArtBible/Session37.json').write_text(json.dumps(dict(status='READY',map=G.D['map'],player=list(G.source(G.P.STATE['pawn'].get_actor_location())),viewport=list(G.P.STATE['pc'].get_viewport_size()),updated=time.time()),indent=2))
def initialize(game):
 global G;G=game;S['base']=G.physics;G.physics=tick
 if '-Clarity37ExitPreview' in G.CMD:
  import airport_journey22 as J
  G.S.update(checked_in=True,bag_accepted=True,security=True);J.ticket();pawn=G.P.STATE['pawn'];pawn.set_actor_location(G.v([-37.05,6.5,1.62]),False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.v([-37.05,6.5,1.62]),G.v([-24,6.5,1.7])))
 if '-Clarity37Photos' in G.CMD or '-Clarity37QA' in G.CMD:
  import clarity37_review;clarity37_review.start(G,'-Clarity37QA' in G.CMD)
 u.SystemLibrary.execute_console_command(G.P.STATE['world'],'r.Tonemapper.Sharpen 0.1',G.P.STATE['pc'])
 G.event('Clarity37 ready',screening_exit='aligned and clear',cafe_bins=3,sofas=2)
