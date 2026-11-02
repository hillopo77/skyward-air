import unreal as u,json,math
def run(r):
 out=[];pawn=r.STATE['pawn'];pc=r.STATE['pc']
 for name,progress in [(n,p) for n in ('Mid_meals_cart','Rear_L_meal_cart','Lavatory R waste flap12','Lavatory L waste flap12','Lavatory R toilet lid12','Lavatory L toilet lid12') for p in (0.,1.)]:
  q=next(q for q in r.STATE['items'] if q['actor']==name);moving=r.STATE['movables'][name];moving['target']=moving['progress']=progress;r._apply_movable(moving)
  r.reposition(list(r.vector(q['validation_approach']).to_tuple()));r.point_at_item(q);p=pawn.get_actor_location();target=r.interaction_point(q);v=target-p;f=u.MathLibrary.get_forward_vector(pc.get_control_rotation());dot=(v.x*f.x+v.y*f.y+v.z*f.z)/v.length();hit=u.SystemLibrary.line_trace_single(r.STATE['world'],p,target,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None;selected=r.nearest()
  record=dict(actor=name,progress=progress,pawn=list(p.to_tuple()),target=list(target.to_tuple()),rotation=list(pc.get_control_rotation().to_tuple()),distance=v.length(),dot=dot,lateral=v.length()*math.sqrt(max(0,1-dot*dot)),visible=r.interaction_visible(q),selected=selected['actor'] if selected else None,hit_owner=r.actor_name(h[9]) if h and h[9] else None,hit_label=h[9].get_actor_label() if h and h[9] else None,impact=list(h[5].to_tuple()) if h else None,hit_gap=(h[5]-target).length() if h else None)
  candidates=[]
  for dz in (0,.015,.030,.05):
   for dy in (-.025,-.015,0,.015):
    test=dict(q);test['point']=list(q['point']);test['point'][1]+=dy;test['point'][2]+=dz;test['point_follows_actor']=False
    if r.interaction_visible(test):candidates.append(dict(delta=[0,dy,dz],visible=True))
  record['candidate_offsets']=candidates;out.append(record)
 (r.ROOT/'ArtBible/CartFocusProbe13.json').write_text(json.dumps(out,indent=2));u.SystemLibrary.quit_game(r.STATE['world'],pc,u.QuitPreference.QUIT,False)
