"""Bounded room-one movement/clearance proof; no full airport walking loop."""
import unreal as u,time,json,traceback
G=None;S={}
def save(status='RUNNING',**kw):
 (G.R/'ArtBible/FoyerQA25.json').write_text(json.dumps(dict(status=status,checks=S['checks'],step=S['i'],elapsed_s=time.monotonic()-S['start'],**kw),indent=2),encoding='utf-8')
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save()
def stop(status,**kw):
 save(status,**kw)
 for h in [S.get('handle'),G.S.get('handle'),G.P.STATE.get('handle')]:
  if h:
   try:u.unregister_slate_post_tick_callback(h)
   except Exception:pass
 u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def face(p):G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
def tick(dt):
 try:
  now=time.monotonic();pawn=G.P.STATE['pawn'];t=now-S['since']
  if t<.15:return
  if S['i']>=len(S['steps']):stop('SUCCESS' if all(q['passed'] for q in S['checks']) else 'FAILED');return
  op,p=S['steps'][S['i']];done=False
  if op=='wait':done=t>p
  elif op=='walk':
   delta=G.v(p)-pawn.get_actor_location();delta.z=0
   if delta.length()<18:
    pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();check('Clear passage to '+str(p[:2]),True,eye_height_m=pawn.get_actor_location().z/100);done=True
   elif t>12:
    check('Clear passage to '+str(p[:2]),False,position=list(G.source(pawn.get_actor_location())));stop('FAILED');return
   else:face(p);pawn.add_movement_input(delta/max(delta.length(),.001),1.)
  elif op=='use':
   q=next(q for q in G.S['targets'] if q['kind']==p and (q['actor'].startswith('Foyer') if p in ['seat','information'] else q['actor']=='Physical luggage 01'));face(G.source(G.point(q)));nearest=G.nearest();check('Aim selects '+p,bool(nearest and nearest['kind']==p and nearest['actor']==q['actor']),selected=nearest['actor'] if nearest else None,visible=G.visible(q));G.use_nearest();done=True
  elif op=='assert':
   if p=='seat':check('Foyer seat is usable',bool(G.P.STATE.get('seated')))
   elif p=='height':check('Standing restores 1.62m eye height',not G.P.STATE.get('seated') and abs(pawn.get_actor_location().z/100-1.62)<.04)
   elif p=='bag':check('Rack suitcase is a usable native physics body',G.S['held']=='Physical luggage 01' and G.S['actors']['Physical luggage 01'].static_mesh_component.is_simulating_physics())
   done=True
  elif op=='stand':G.P.stand();done=True
  elif op=='release':G.release();done=True
  elif op=='trace':
   # Lateral line traces at walking-body height, clear 2m-wide route envelope.
   for name,start,end in [('Entry centre',[-48.6,-12.5,.9],[-44.8,-12.5,.9]),('Check-in entrance',[-46,-15,.9],[-42,-15,.9]),('North route left',[-46.8,-12,.9],[-46.8,-7.6,.9]),('North route right',[-45.0,-12,.9],[-45.0,-7.6,.9])]:
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(start),G.v(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;check(name+' is unobstructed',not h or not h[0],blocker=h[9].get_actor_label() if h and h[0] and h[9] else None)
   for name,start,end in [('Check-in queue hidden from entrance',[-48.5,-12.5,1.62],[-39,-14,1.62]),('Security hidden from foyer',[-46,-10,1.62],[-46,-4,1.62]),('Scanner hidden from entry angle',[-48.5,-12.5,1.62],[-37.4,0,1.62]),('Scanner hidden from welcome angle',[-47.7,-13.65,1.62],[-37.4,0,1.62]),('Scanner hidden beside corridor entrance',[-44.8,-8.6,1.62],[-37.4,0,1.62])]:
    hit=u.SystemLibrary.line_trace_single(G.P.STATE['world'],G.v(start),G.v(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;blocker=h[9].get_actor_label() if h and h[0] and h[9] else None;impact=list(G.source(h[5])) if h and h[0] else None
    # The extreme entry ray can meet the retained opaque north-east
    # door jamb before reaching the new return. Only that solid part
    # of Walls24 qualifies, not its glazed gate-enclosure sections.
    retained_opaque_jamb=blocker=='Walls24 modeled architecture' and impact and -44.65<impact[0]<-43 and -8.3<impact[1]<-7.7
    check(name,blocker in ['Foyer warm envelope25','Foyer screened approaches25'] or retained_opaque_jamb,blocker=blocker,impact=impact)
   done=True
  if done:S['i']+=1;S['since']=now;save()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game
 S.update(start=time.monotonic(),since=time.monotonic(),i=0,checks=[],steps=[('wait',2),('walk',[-48.5,-12.5,1.62]),('walk',[-46,-12.5,1.62]),('trace',None),('walk',[-46,-15.9,1.62]),('walk',[-47.25,-16.0,1.62]),('use','seat'),('assert','seat'),('stand',None),('assert','height'),('walk',[-45.7,-16.0,1.62]),('use','pickup'),('assert','bag'),('release',None),('walk',[-46,-15,1.62]),('walk',[-42,-15,1.62]),('walk',[-42,-13,1.62]),('walk',[-40.5,-13,1.62]),('walk',[-42,-13,1.62]),('walk',[-42,-15,1.62]),('walk',[-46,-15,1.62]),('walk',[-46,-10.05,1.62]),('use','information'),('walk',[-46,-8.5,1.62]),('walk',[-45.2,-7.2,1.62]),('walk',[-40.4,-7.2,1.62]),('walk',[-40.4,-5.9,1.62])]);S['handle']=u.register_slate_post_tick_callback(tick);save()
