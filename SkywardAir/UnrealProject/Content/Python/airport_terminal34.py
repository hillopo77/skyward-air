"""Complete-terminal version metadata, gallery and one end-to-end proof."""
import unreal as u,time,json
G=None;S={}
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('written',0)<1:return
 S['written']=time.monotonic();(G.R/'ArtBible/TerminalSession34.json').write_text(json.dumps(dict(status='READY',map=G.D['map'],viewport=list(G.P.STATE['pc'].get_viewport_size()),journey={k:G.S.get(k,False) for k in ['checked_in','bag_accepted','security','boarding','aboard']},updated=time.time()),indent=2))
def initialize(game):
 global G;G=game;S['base']=G.physics;G.physics=tick
 if '-Terminal34QA' in G.CMD:
  import terminal34_qa;terminal34_qa.start(G)
 if '-Terminal34Photos' in G.CMD:
  import terminal34_photos;terminal34_photos.start(G)
 G.event('Complete terminal34 ready',sections=17,approved_lighting='warm33')
