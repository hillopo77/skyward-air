"""Explicitly staged native negative cases, separate from the fresh journey."""
import unreal as u,json,time,traceback,math,hashlib
G=None;S={}
def save(status='RUNNING',**extra):
 (G.R/'ArtBible/SafetyQA38.json').write_text(json.dumps(dict(status=status,context=S.get('context'),step=S['i'],checks=S['checks'],captures=S['captures'],scenario_setup_teleports=S['teleports'],staged_prop_poses=S.get('prop_poses',[]),physical_walk_steps=0,setup='Independent staged negative cases; never described as the fresh passenger route',**extra),indent=2))
def check(n,b,**kw):S['checks'].append(dict(name=n,passed=bool(b),**kw));save()
def advance():S['i']+=1;S['since']=time.monotonic();S.pop('begun',None);save()
def stop(status,**kw):save(status,**kw);u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_game(G.P.STATE['world'],G.P.STATE['pc'],u.QuitPreference.QUIT,False)
def at(p):
 pawn=G.P.STATE['pawn'];pawn.get_component_by_class(u.FloatingPawnMovement).stop_movement_immediately();pawn.set_actor_location(G.v(p),False,True);S['teleports']+=1
def targ(name,**fields):return next(q for q in G.S['targets'] if q['actor']==name and all(q.get(k,False if isinstance(v,bool) else None)==v for k,v in fields.items()))
def operate(q):
 p=G.source(G.point(q));G.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(G.P.STATE['pawn'].get_actor_location(),G.v(p)))
 visible=G.visible(q);check('Physical control visible '+q['actor'],visible,point=list(p))
 if visible:return G.act(q)
 return False
def tick(dt):
 try:
  t=time.monotonic()-S['since'];j=G.journey38['state'];op=S['steps'][S['i']] if S['i']<len(S['steps']) else 'end'
  if op=='end':stop('SUCCESS' if all(c['passed'] for c in S['checks']) else 'FAILED');return
  if op=='fresh_denied_setup':
   G.S.update(checked_in=False,security=False,boarding=False,aboard=False);at([-42,-4.8,1.62])
  elif op=='entry_denied':
   if t<2:return
   doors=[d for n,d in G.S['doors'].items() if n.startswith('Screening entry24')]
   check('No ticket: proximity does not open security entry',len(doors)==2 and all(d['fraction']<.01 and d['target']==0 for d in doors))
  elif op=='exit_setup':G.S['checked_in']=True;G.journey38['ticket']();at([-37.2,6.5,1.62])
  elif op=='exit_denied':
   if t<1.5:return
   doors=[d for n,d in G.S['doors'].items() if n.startswith('Screening exit24')]
   check('No clearance: proximity does not open screening exit',len(doors)==2 and all(d['fraction']<.01 and d['target']==0 for d in doors))
  elif op=='boarding_denied':
   at([-18.4,-1,1.62]);operate(targ('Gate A07 boarding desk',kind='boarding'));check('Boarding denied without security',not G.S['boarding'])
  elif op=='wc_setup':
   G.S['security']=True;at([-20.55,-8.25,1.62]);operate(targ('Terminal WC 0',inside_release=False))
  elif op=='wc_inside_lock':
   if t<1.4:return
   at([-20.55,-5.95,1.62]);operate(targ('Terminal WC 0',inside_release=True))
  elif op=='wc_outside_denied':
   if t<1.4:return
   check('Inside close establishes WC privacy lock',j['wc_locks']['Terminal WC 0'])
   at([-20.55,-8.25,1.62]);operate(targ('Terminal WC 0',inside_release=False));d=G.S['doors']['Terminal WC 0'];check('Outside release cannot open occupied WC',d['target']==0 and j['wc_locks']['Terminal WC 0'])
   colors=[]
   for q in G.S['targets']:
    if q['actor']=='Terminal WC 0' and q.get('release_actor'):
     c=G.S['actors'][q['release_actor']].static_mesh_component
     colors += [c.get_material(i).get_name() for i,s in enumerate(c.static_mesh.static_materials) if str(s.material_slot_name)=='MI_AP_GreenLED']
   check('Both occupied indicators are red',len(colors)==2 and all(n=='MI_AP_RedLED' for n in colors),materials=colors)
  elif op=='wc_inside_exit':
   at([-20.55,-5.95,1.62]);operate(targ('Terminal WC 0',inside_release=True));check('Inside exit always releases privacy',not j['wc_locks']['Terminal WC 0'] and G.S['doors']['Terminal WC 0']['target']==1)
  elif op=='a08':
   q=targ('Gate A08 boarding desk');check('A08 is honest information action',q['kind']=='information' and 'information' in q['title'].lower());at([-28.0,19.4,1.62]);operate(q)
  elif op=='coffee_order':
   at([-46.7,29.45,1.62]);q=next(q for q in G.S['targets'] if q['kind']=='vending');operate(q)
  elif op=='coffee_pickup':
   if t<1.1:return
   n=j['coffee']['actor'];a=G.S['actors'][n];check('Coffee has one real visible serving',j['coffee']['served'] and not a.get_editor_property('hidden'));operate(targ(n,kind='pickup'));check('Coffee native pickup works',G.S['held']==n)
  elif op=='coffee_release':G.release(False)
  elif op=='belt_stop':
   q=next(q for q in G.S['targets'] if q['kind']=='equipment_toggle' and q['conveyor']=='Security belt 01');at([-41.9,.6,1.62]);old=j['powered']['Security belt 01'];operate(q);check('Actual emergency control switches conveyor off',old and not j['powered']['Security belt 01']);operate(q);check('Actual emergency control resets conveyor',j['powered']['Security belt 01'])
  elif op=='bridge_open_denial':
   at([-16.8,2.2,1.62]);okay,reason=G.airside38['request_bridge'](True);check('Open L1 prevents stow',not okay,reason=reason);okay,reason=G.airside38['can_depart']();check('Docked bridge prevents departure',not okay,reason=reason)
  elif op=='bridge_close_l1':G.P.STATE['movables'][G.D['aircraft_door']]['target']=0
  elif op=='bridge_occupied':
   if t<3:return
   at([-10,.0,1.62]);okay,reason=G.airside38['request_bridge'](True);check('Occupied bridge cannot stow',not okay and 'empty' in reason,reason=reason)
  elif op=='bridge_stow':
   at([-16.8,2.2,1.62]);okay,reason=G.airside38['request_bridge'](True);check('Empty bridge with closed L1 can stow',okay,reason=reason)
  elif op=='bridge_departure':
   if t<14:return
   okay,reason=G.airside38['can_depart']();check('Complete native stowed bridge has clear forward departure envelope',okay,reason=reason)
  elif op=='external_obstruction':
   n='Physical luggage 05';a=G.S['actors'][n];c=a.static_mesh_component;f=G.flight39['frame'];point=[14.15,.675,.75]
   if n in f.prop_records:f._leave_prop(n,f.prop_records[n])
   target=f.world(G.v(point));a.set_actor_location(target-c.get_center_of_mass()+a.get_actor_location(),False,True)
   c.set_physics_linear_velocity(u.Vector(),False,G.NONE);c.set_physics_angular_velocity_in_radians(u.Vector(),False,G.NONE)
   S.setdefault('prop_poses',[]).append(dict(actor=n,source_com_m=point,scope='Explicit exterior/L1-straddling obstruction setup; not a carried-baggage journey'))
   clear=G.airside38['departure_clearance']();blocked=[b['name'] for b in clear['blocking'] if b['name']==n or b['name'].startswith(n+' instance ')]
   okay,reason=G.airside38['can_depart']()
   check('Genuine exterior obstruction prevents departure after bridge stow',not okay and bool(blocked) and not f.body_fully_inside(a),reason=reason,blocking=blocked,source_bounds_m=f.body_source_bounds(a))
  else:raise RuntimeError(op)
  advance()
 except Exception:stop('ERROR',error=traceback.format_exc())
def start(game):
 global G;G=game;G.QA=True;G.CAPTURE=False
 S.update(i=0,context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text()),since=time.monotonic(),teleports=0,checks=[],captures=[],steps=['fresh_denied_setup','entry_denied','exit_setup','exit_denied','boarding_denied','wc_setup','wc_inside_lock','wc_outside_denied','wc_inside_exit','a08','coffee_order','coffee_pickup','coffee_release','belt_stop','bridge_open_denial','bridge_close_l1','bridge_occupied','bridge_stow','bridge_departure'])
 S['steps'].append('external_obstruction')
 S['handle']=u.register_slate_post_tick_callback(tick);save()
