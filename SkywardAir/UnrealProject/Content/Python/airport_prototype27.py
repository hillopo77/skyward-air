"""Entrance-specific crisp-distance tuning; legacy maps retain their own profiles."""
import unreal as u,json,time
G=None;C=None;S={}
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('last',0)<1:return
 S['last']=time.monotonic()
 (G.R/'ArtBible/PrototypeSession27.json').write_text(json.dumps(dict(status='READY',level=S['level'],map=G.D['map'],viewport=list(G.P.STATE['pc'].get_viewport_size()),profile=C.S['profile'],phase=C.phase(),distance_normal_fade_m=[2.5,8],essential_prints_never_stream=True,updated=time.time()),indent=2),encoding='utf-8')
def initialize(game):
 global G,C;G=game;import airport_clarity26 as clarity;C=clarity
 level=int(next((p.split('=',1)[1] for p in G.CMD.split() if p.startswith('-PrototypeLevel=')),'5'));C.PROFILES['Distance27']=['r.AntiAliasingMethod 2','r.ScreenPercentage 100','r.TemporalAASamples 4','r.TemporalAACurrentFrameWeight .45','r.TemporalAAFilterSize .65','r.TemporalAA.Quality 2']
 if level>=3:C.apply_profile('Distance27')
 for cmd in ['r.MipMapLODBias 0','r.MaxAnisotropy 16','r.ViewDistanceScale 1']:u.SystemLibrary.execute_console_command(G.P.STATE['world'],cmd,G.P.STATE['pc'])
 S.update(base=G.physics,level=level);G.physics=tick
 if '-Prototype27QA' in G.CMD:
  import arrival27_qa;arrival27_qa.start(G,C)
 if '-Prototype27Distance' in G.CMD:
  import distance27;distance27.start(G,C)
 G.event('Entrance prototype27 ready',level=level,profile=C.S['profile'])
