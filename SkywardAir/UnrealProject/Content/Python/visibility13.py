"""Live-world ray diagnostics; a known wall proves queries are effective."""
import unreal as u,json
def run(r,quit_after=True):
 if '-SkywardProbe13' in r.COMMAND_LINE:
  import probe13
  return probe13.run(r)
 world=r.STATE['world'];pawn=r.STATE['pawn'];assets={x['name']:x['asset'] for x in r.DATA['instances']}
 def trace(p,t):
  v=u.SystemLibrary.line_trace_single(world,r.vector(p),r.vector(t),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True)
  if v is None:return dict(blocking=False)
  v=v.to_tuple();return dict(blocking=bool(v[0]),owner=r.actor_name(v[9]) if v[9] else '',label=v[9].get_actor_label() if v[9] else '',impact=[v[5].x/100,-v[5].y/100,v[5].z/100],gap_cm=round((v[5]-r.vector(t)).length(),4))
 wall=trace([0,15,1.62],[3,15,1.62]);rows=[]
 for q in r.STATE['items']:
  if q.get('requires_open') or q.get('activation')=='inspect_only':continue
  if q['kind']=='screen':fallback=[q['point'][0],q['point'][1]+.36,1.62]
  elif q['kind']=='control':fallback=[q['point'][0]*.65,q['point'][1],1.62]
  elif q['kind']=='seat':fallback=[q['point'][0],q['point'][1]+.85,1.62]
  else:fallback=[q['point'][0]*.55,q['point'][1],1.62]
  p=r.DATA['layout']['validation'].get('seat_approaches',{}).get(q['actor'],q.get('validation_approach',fallback));hit=trace(p,q['point'])
  valid=not hit['blocking'] or hit.get('owner')==q['actor'] or hit.get('owner') in q.get('visibility_owners',[]) or hit.get('gap_cm',0)<=.2
  record=dict(actor=q['actor'],kind=q['kind'],clear=valid,approach=p,point=q['point'],asset=assets.get(hit.get('owner')),**hit)
  if not valid and 'side pushbutton' in q['actor']:
   candidates=[]
   for dx in (-.6,-.4,-.2,0,.2,.4,.6):
    for dy in (-.7,-.5,-.3,0,.3,.5,.7):
     a=[p[0]+dx,p[1]+dy,1.62]
     if abs(a[0])>1.50 or a[1]<-4.55:continue
     body=u.SystemLibrary.capsule_trace_single_by_profile(world,r.vector([a[0],a[1],.86]),r.vector([a[0],a[1],.86]),20,86,u.Name('Pawn'),True,[pawn],u.DrawDebugTrace.NONE,True)
     if body is not None and body.to_tuple()[0]:continue
     h=trace(a,q['point'])
     if not h['blocking'] or h.get('owner')==q['actor'] or h.get('gap_cm',0)<=.2:candidates.append(a)
   record['clear_standing_approaches']=candidates
  rows.append(record)
 (r.ROOT/'ArtBible/VisibilityDiagnostics13.json').write_text(json.dumps(dict(known_wall=wall,positive_control_passed=wall['blocking'],blocked=[q for q in rows if not q['clear']],clear_count=sum(q['clear'] for q in rows),all=rows),indent=2))
 if quit_after:u.SystemLibrary.quit_game(world,r.STATE['pc'],u.QuitPreference.QUIT,False)
 return dict(positive_control_passed=wall['blocking'],blocked=[q for q in rows if not q['clear']],clear_count=sum(q['clear'] for q in rows))
