"""Section-specific guidance and focused circulation verification."""
import unreal as u,time,json
G=None;S={}
def floor_at(x,y,feet=0):
 previous=G.P.STATE.get('floor_name','');connected=previous.startswith('Gallery35')
 for q in G.D['floors']:
  if not q['name'].startswith('Gallery35'):continue
  x0,x1,y0,y1=q['rect']
  if not x0-.01<=x<=x1+.01 or not y0-.01<=y<=y1+.01:continue
  h=q['height']
  if q.get('slope'):
   s=q['slope'];t=max(0,min(1,(y-s['from'])/(s['to']-s['from'])));h=s['start']+(s['end']-s['start'])*t
  if connected or abs(h-feet)<.8:return h,q['name']
 if connected and -47.9<x<-45.1 and 17.0<y<17.8:return 0.,'Cafe lower stair landing35'
 return S['floor'](x,y,feet)
def tick(dt):
 S['base'](dt)
 if time.monotonic()-S.get('write',0)<1:return
 S['write']=time.monotonic();x,y,z=G.source(G.P.STATE['pawn'].get_actor_location());zone=next((q['id'] for q in G.D['zones'] if q['rect'][0]<x<q['rect'][1] and q['rect'][2]<y<q['rect'][3]),None)
 if zone!=S.get('zone'):
  messages={'security':'Prepare your belongings at the left bench, then walk through lane 01 or 02','recovery':'Repack here. Turn right for Gate A07; follow the gate signs','concourse':'A07 on the right. Cloud Nine cafe left ahead. A08 straight ahead','cafefoyer':'Cloud Nine cafe and upstairs gallery: continue through the timber opening','gate08foyer':'A08 North Lounge. SA107 boards from A07'}
  if '-AirportDetail36' in G.CMD:messages.update(recovery='Follow the gold line straight ahead for A07. Repacking is in the side alcove',concourse='Gold leads to A07. Turn left onto terracotta for Cloud Nine; sage continues to A08')
  if zone in messages:G.say(messages[zone])
  S['zone']=zone
 (G.R/'ArtBible/Session35.json').write_text(json.dumps(dict(status='READY',map=G.D['map'],zone=zone,player=[x,y,z],viewport=list(G.P.STATE['pc'].get_viewport_size()),updated=time.time()),indent=2))
def initialize(game):
 global G;G=game;S['base']=G.physics;G.physics=tick;S['floor']=G.P.floor_at_source;G.P.floor_at_source=floor_at
 if '-SecurityPreview35' in G.CMD:
  import airport_journey22 as J
  G.S['checked_in']=True;J.ticket();G.P.STATE['pawn'].set_actor_location(G.v([-42,-5.3,1.62]),False,True);G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.v([-42,-5.3,1.62]),G.v([-42,2,1.62])))
 if '-Flow35Photos' in G.CMD:
  import flow35_review;flow35_review.start(G,False)
 if '-Flow35QA' in G.CMD:
  import flow35_review;flow35_review.start(G,True)
 G.event('Circulation35 ready',cafe_m2=306,gallery_m2=72,stair_width_m=2.4)
