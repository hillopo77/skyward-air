"""One explicit38 initialization sequence, after the retained HUD/character layer."""
import unreal as u
def initialize(G):
 # Airport queue walkers move their real collision bodies as well as the rigs.
 # The inherited map had retained STATIC on these invisible dynamic proxies.
 for name,actor in G.S.get('actors',{}).items():
  if name.startswith('CH12COLL ') and actor.root_component:actor.root_component.set_mobility(u.ComponentMobility.MOVABLE)
 import airport_airside38 as A
 import airport_journey38 as J
 import airport_rendering38 as R
 import equipment_displays38 as E
 A.install(G);J.install(G)
 if G.D.get('flight39'):
  import airport_flight39 as F
  F.install(G)
 if G.D.get('repair38',{}).get('window40'):
  import window40;window40.install(G)
 if G.D.get('repair38',{}).get('window41'):
  import window41;window41.install(G)
 if G.D.get('repair38',{}).get('business_belt40'):
  import business_belt40;business_belt40.install(G)
 import locomotion40;locomotion40.install(G)
 E.install(G);R.install(G)
 import lifecycle43;lifecycle43.install(G)
 # Pass47 terminal ambience: room tone, crowd, outdoor, apron and PA loops
 # mixed by position. Returns at once under -NoSound, so no QA run changes;
 # any failure is logged and the game carries on silent, as before.
 try:
  import ambience47;ambience47.start(G)
 except Exception as exc:u.log_warning('Ambience47 unavailable: '+str(exc))
 if '-AirportStartAboard' in G.CMD:
  G.P.STATE['pawn'].set_actor_location(G.v(G.D['aircraft38']['start_aboard']),False,True)
  G.P.STATE['pc'].set_control_rotation(u.Rotator(yaw=90))
  G.S.update(checked_in=True,security=True,boarding=True,aboard=True)
 if '-Repair38Photos' in G.CMD or '-Repair38QA' in G.CMD:
  import repair38_review;repair38_review.start(G,qa='-Repair38QA' in G.CMD)
 if '-Repair38Safety' in G.CMD:
  import safety38_review;safety38_review.start(G)
 if '-Repair38Scanner' in G.CMD:
  import journey38_review;journey38_review.start(G,scanner=True)
 if '-Repair38MountPhotos' in G.CMD:
  import repair38_review;repair38_review.start(G,mount=True)
 if '-Repair38AssemblyPhotos' in G.CMD:
  import repair38_review;repair38_review.start(G,assembly=True)
 if '-Repair39DetailPhotos' in G.CMD:
  import repair38_review;repair38_review.start(G,details=True)
 if '-Repair40PosturePhotos' in G.CMD:
  import repair38_review;repair38_review.start(G,postures=True)
 if '-Repair39Performance' in G.CMD:
  import performance39_review;performance39_review.start(G)
 if '-Repair39Flight' in G.CMD:
  import journey38_review;journey38_review.start(G,flight=True)
 if '-Repair39FlightDebug' in G.CMD:
  import journey38_review;journey38_review.start(G,flight=True,debug=True)
 if '-Repair39BagPhysics' in G.CMD:
  import bag_physics39_review;bag_physics39_review.start(G)
 if '-Repair41Assemblies' in G.CMD:
  import assemblies41_review;assemblies41_review.start(G)
 if '-Repair43Normals' in G.CMD:
  import normals43_review;normals43_review.start(G)
 # Pass45 read-only entrance exposure probe. New flag; no existing mode is
 # reachable through it and no other dispatch is affected.
 if '-Exposure45Probe' in G.CMD:
  import exposure45_review;exposure45_review.start(G)
 if '-Audit45' in G.CMD:
  import audit45_review;audit45_review.start(G)
 if '-Collision45' in G.CMD:
  import collision45_probe;collision45_probe.start(G)
 if '-Deck45' in G.CMD:
  import deck45_probe;deck45_probe.start(G)
 if '-Wall45' in G.CMD:
  import wall45_probe;wall45_probe.start(G)
 if '-Verify45' in G.CMD:
  import verify45_probe;verify45_probe.start(G)
 if '-Walkoff45' in G.CMD:
  import walkoff45_probe;walkoff45_probe.start(G)
 if '-Support45' in G.CMD:
  import support45_probe;support45_probe.start(G)
 # Pass46 whole-game inventory audit. New flag, read-only; no existing mode
 # is reachable through it and no other dispatch is affected.
 if '-Inventory46' in G.CMD:
  import inventory46_probe;inventory46_probe.start(G)
 # Pass46 capture pass. Read-only: settled stills of the improved rooms.
 if '-Capture46' in G.CMD:
  import capture46_probe;capture46_probe.start(G)
 # Pass46 P46-015 collision verification. Read-only, and it has to live here
 # rather than beside the change: no physics query answers under
 # -run=pythonscript -NullRHI, proven by a control trace onto a known floor
 # coming back empty. Traces only answer in -game.
 if '-Collide46Verify' in G.CMD:
  import verify46_probe;verify46_probe.start(G)
 # Pass46 P46-017 gallery deck experiment. Toggles the deck's collision for
 # this session only and undoes it; nothing is saved to the level.
 if '-Deck46' in G.CMD:
  import deck46_probe;deck46_probe.start(G)
 # Pass46 P46-017 acceptance: drop a real luggage body on the deck. The bag
 # is restored afterwards and nothing is saved.
 if '-Drop46' in G.CMD:
  import drop46_probe;drop46_probe.start(G)
 # Pass46 P46-006/007 roof survey and aerial stills. Read-only.
 if '-Roof46' in G.CMD:
  import roof46_probe;roof46_probe.start(G)
 # Pass46 P46-020 ground-edge heights for the skirt. Read-only.
 if '-Edge46' in G.CMD:
  import edge46_probe;edge46_probe.start(G)
 # Pass47 player-view critique: reachability flood-fill and stills. Read-only.
 if '-Critique47' in G.CMD:
  import critique47_probe;critique47_probe.start(G)
 # Pass47 one still per distinct model. Read-only.
 if '-Models47' in G.CMD:
  import models47_probe;models47_probe.start(G)
 # Pass47 ambience check: needs sound on. Read-only.
 if '-Audio47Verify' in G.CMD:
  import verify_audio47_probe;verify_audio47_probe.start(G)
 # Pass47 panel trace and live ceiling-emission trial. Nothing saved.
 if '-Look47' in G.CMD:
  import look47_probe;look47_probe.start(G)
 # Pass47 verification stills and road-line ground trace. Read-only.
 if '-Final47' in G.CMD:
  import final47_probe;final47_probe.start(G)
 # Pass47 aircraft floor collision map. Read-only.
 if '-Floor47' in G.CMD:
  import floor47_probe;floor47_probe.start(G)
 # Pass47 round-2 stills and airside survey. Read-only.
 if '-Verify2_47' in G.CMD:
  import verify2_47_probe;verify2_47_probe.start(G)
 if '-Verify3_47' in G.CMD:
  import verify3_47_probe;verify3_47_probe.start(G)
 if '-Look48' in G.CMD:
  import look48_probe;look48_probe.start(G)
 # Pass48: any -P48_<module> flag starts that probe module (read-only probes).
 import re as _re,importlib as _il
 for _m in _re.findall(r'-P48_(\w+)',G.CMD):
  _il.import_module(_m).start(G)
 G.event('Airport38 integrated',reviews=5,fix_assignments=5)
