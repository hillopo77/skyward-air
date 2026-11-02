"""Screen-resolution next-step guidance and a motion-clear rendering profile."""
import unreal as u,json,time
from pathlib import Path
G=None;S={}
PROFILES={
 'OriginalTAA':['r.AntiAliasingMethod 2','r.ScreenPercentage 100','r.TemporalAASamples 16','r.TemporalAACurrentFrameWeight .08','r.TemporalAAFilterSize 1'],
 'ClearNative':['r.AntiAliasingMethod 1','r.FXAA.Quality 5','r.ScreenPercentage 100'],
 'Clear115':['r.AntiAliasingMethod 1','r.FXAA.Quality 5','r.ScreenPercentage 115'],
 'FastTAA':['r.AntiAliasingMethod 2','r.ScreenPercentage 100','r.TemporalAASamples 4','r.TemporalAACurrentFrameWeight .30','r.TemporalAAFilterSize .70']}
COMMON=['r.DynamicRes.OperationMode 0','r.Tonemapper.Sharpen 0','r.MotionBlurQuality 0','r.DepthOfFieldQuality 0','r.SceneColorFringeQuality 0','r.MaxAnisotropy 16']
def apply_profile(name):
 for cmd in COMMON+PROFILES[name]:u.SystemLibrary.execute_console_command(G.P.STATE['world'],cmd,G.P.STATE['pc'])
 S['profile']=name
def phase():
 import airport_journey22 as J
 if G.P.STATE.get('seated') and G.S.get('aboard'):return 'Complete'
 if G.S.get('aboard'):return 'Seat'
 if G.S.get('boarding'):return 'Board'
 if G.S.get('security'):return 'Gate'
 if G.S.get('checked_in'):
  if G.S.get('held') and not G.S.get('bag_accepted') and G.S['actor_specs'][G.S['held']]['asset'].startswith(('SM_AP_Bag','SM_AP_CarryOn')):return 'BagDrop'
  return 'Security'
 return 'CheckIn'
def objective():return S['titles'][phase()][0]
def info_act(q):
 if q['kind']=='information' and q['actor'].startswith('Foyer information'):
  S.update(notice='Guide_'+phase(),notice_until=time.monotonic()+3);G.say(S['titles'][phase()][1]);G.event('Arrival directions requested',next_step=phase());return
 if q['kind']=='npc' and q['actor'].endswith('Information host'):
  S.update(notice='Guide_'+phase(),notice_until=time.monotonic()+3);q=dict(q,dialogue=S['titles'][phase()][1])
 return S['base_act'](q)
def physics(dt):
 S['base_physics'](dt);now=time.monotonic()
 if now-S.get('last',0)<.10:return
 S['last']=now;current=phase();hint='None';q=None
 if G.P.STATE.get('seated'):hint='Stand'
 elif not G.QA and not G.CAPTURE:
  q=G.nearest();lookup={'checkin':'CheckIn','bagdrop':'BagDrop','scanner':'Security','security':'Security','boarding':'Boarding','boardingdoor':'Boarding','information':'Information','seat':'Seat','pickup':'Pickup','extinguisher':'Extinguisher','slide':'Slide','npc':'Npc'}
  if G.S.get('held'):
   hint=lookup.get(q['kind'],'Held') if q and q['kind'] in ['checkin','bagdrop','scanner','security','boarding','boardingdoor'] else 'HeldExt' if 'extinguisher' in G.S['held'].lower() else 'Held'
  else:hint=lookup.get(q['kind'],'None') if q else 'None'
 if now<S.get('notice_until',0) and ('-AirportPrototype27' not in G.CMD or hint in ['None','Information','Npc']):hint=S['notice']
 if current!=S.get('phase'):S['mid'].set_texture_parameter_value('Journey',S['textures']['Journey_'+current]);S['phase']=current
 if hint!=S.get('hint'):S['mid'].set_texture_parameter_value('Hint',S['textures']['Hint_'+hint]);S['hint']=hint
 show=not G.CAPTURE or bool(G.S.get('show_hands_in_capture'))
 if G.QA:show=False
 if show!=S.get('show'):S['volume'].add_or_update_blendable(S['mid'],1. if show else 0.);S['show']=show
 if now-S.get('written',0)>1:
  S['written']=now;keys=['r.AntiAliasingMethod','r.ScreenPercentage','r.Tonemapper.Sharpen','r.MotionBlurQuality','r.DepthOfFieldQuality','EnableHighDPIAwareness']
  keys+=['r.TemporalAACurrentFrameWeight','r.TemporalAASamples','r.TemporalAAFilterSize'];values={k:u.SystemLibrary.get_console_variable_float_value(k) for k in keys};vp=G.P.STATE['pc'].get_viewport_size()
  (G.R/'ArtBible/ClaritySession26.json').write_text(json.dumps(dict(status='READY',profile=S['profile'],phase=current,hint=hint,viewport=list(vp),settings=values,hud_after_tonemapping=True,initial_departure_exit='checkin',updated=time.time()),indent=2),encoding='utf-8')
def initialize(game):
 global G;G=game;world=G.P.STATE['world'];hud=json.loads((G.R/'Exports/Hud26.json').read_text(encoding='utf-8'));root=u.load_asset('/Game/Airport26/UI/M_Journey26');assert root
 volume=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.PostProcessVolume) if a.get_actor_label()=='Airport26 journey overlay');mid=u.MaterialLibrary.create_dynamic_material_instance(world,root);volume.add_or_update_blendable(root,0.);volume.add_or_update_blendable(mid,1.)
 S.update(mid=mid,volume=volume,titles=hud['stages'],textures={name:u.load_asset('/Game/Airport26/UI/T26_'+name) for name in hud['textures']},base_physics=G.physics,base_act=G.act)
 G.physics=physics;G.act=info_act;import airport_journey22 as J;J.objective=objective
 old_hint=G.P._hint;G.P._hint=lambda item:old_hint(item) if G.S.get('aboard') else ''
 apply_profile('FastTAA');G.P.STATE['pc'].player_camera_manager.set_editor_property('default_fov',78.)
 # Saved window/DPI state can override launch dimensions. Apply the actual
 # client resolution after the viewport exists, rather than upscaling it.
 rx=next((p.split('=',1)[1] for p in G.CMD.split() if p.lower().startswith('-resx=')),'1920');ry=next((p.split('=',1)[1] for p in G.CMD.split() if p.lower().startswith('-resy=')),'1080')
 u.SystemLibrary.execute_console_command(world,'r.SetRes '+rx+'x'+ry+'w',G.P.STATE['pc']);S['requested_viewport']=[int(rx),int(ry)]
 G.event('Clear arrival26 ready',initial_exit='checkin',high_dpi='project enabled',profile=S['profile'])
 if '-ClarityCompare26' in G.CMD:
  import clarity26_compare;clarity26_compare.start(G,__import__(__name__))
 elif '-ArrivalQA26' in G.CMD:
  import arrival26_qa;arrival26_qa.start(G,__import__(__name__))
