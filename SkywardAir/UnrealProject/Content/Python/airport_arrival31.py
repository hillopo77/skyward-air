"""An arrival pause before the existing live check-in process."""
import unreal as u,time,json
G=None;S={}
def nearest():
 q=S['nearest']()
 if q and q['actor']==G.D['checkin30']['queue_actor'] and (G.point(q)-G.P.STATE['pawn'].get_actor_location()).length()>G.D['arrival31']['join_range_m']*100:return None
 return q
def tick(dt):
 S['base'](dt)
 import airport_checkin30 as Q
 import airport_clarity26 as C
 x,y,z=G.source(G.P.STATE['pawn'].get_actor_location())
 key='Find' if x<-43 else 'Arrival' if x<G.D['arrival31']['queue_cue_x'] else 'JoinQueue'
 if not Q.S['joined'] and not G.S.get('checked_in'):
  if key!=S.get('shown'):C.S['mid'].set_texture_parameter_value('Journey',S['textures'][key]);S['shown']=key
 if time.monotonic()-S.get('written',0)>.5:
  S['written']=time.monotonic();(G.R/'ArtBible/ArrivalSession31.json').write_text(json.dumps(dict(status='READY',zone=key,joined=Q.S['joined'],called=Q.S['called'],profile=C.S['profile'],viewport=list(G.P.STATE['pc'].get_viewport_size()),updated=time.time()),indent=2))
def initialize(game):
 global G;G=game
 import airport_clarity26 as C
 C.PROFILES['Calm31']=['r.AntiAliasingMethod 2','r.ScreenPercentage 100','r.TemporalAASamples 8','r.TemporalAACurrentFrameWeight .35','r.TemporalAAFilterSize .8','r.TemporalAA.Quality 2']
 C.apply_profile('Calm31')
 S.update(base=G.physics,nearest=G.nearest,textures={k:u.load_asset('/Game/Airport31/Textures/T31_HUD_'+k) if k!='JoinQueue' else u.load_asset('/Game/Airport30/Textures/T30_HUD_JoinQueue') for k in ['Find','Arrival','JoinQueue']})
 G.physics=tick;G.nearest=nearest
 if '-CheckinPreview31' in G.CMD:
  p=G.v([-42,-13,1.62]);G.P.STATE['pawn'].set_actor_location(p,False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(p,G.v([-36.6,-14.4,1.35])))
 # Modest player lens; no depth-of-field, motion blur or sharpen filter.
 cam=G.P.STATE['pawn'].get_component_by_class(u.CameraComponent)
 if cam:cam.set_field_of_view(76.)
 if '-Arrival31QA' in G.CMD:
  import arrival31_qa;arrival31_qa.start(G)
 G.event('Arrival31 ready',buffer_m=4.1,queue_starts_ahead=True)
