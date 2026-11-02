"""Room-bound access controls and current airport position, scoped to the24 map."""
import unreal as u,time,json
from pathlib import Path
G=None;S={};R=Path(__file__).resolve().parents[4]/'Airport/Rooms24'
def act(q):
 access=q.get('access24')
 if access and not G.S.get(access,False):
  G.say('Collect your boarding pass before security' if access=='checked_in' else 'Walk through screening first' if access=='security' else 'Staff access only');G.event('Room access denied',actor=q['actor'],requires=access);return
 return S['base_act'](q)
def physics(dt):
 S['base_physics'](dt);pawn=G.P.STATE['pawn'];p=pawn.get_actor_location()
 for q in S['access']:
  door=G.S['doors'][q['actor']];door['target']=1 if G.S.get(q['access24'],False) and (p-door['closed']).length()<430 else 0
 if time.monotonic()-S.get('last_write',0)>1:
  S['last_write']=time.monotonic();x,y,z=G.source(p);zone=next((q['id'] for q in G.D['zones'] if q['rect'][0]<x<q['rect'][1] and q['rect'][2]<y<q['rect'][3]),None)
  (R/'ArtBible'/('RoomSession37.json' if '-AirportClarity37' in G.CMD else 'RoomSession36.json' if '-AirportDetail36' in G.CMD else 'RoomSession35.json' if '-AirportFlow35' in G.CMD else 'RoomSession34.json' if '-AirportTerminal34' in G.CMD else 'RoomSession33.json' if '-AirportWarm33' in G.CMD else 'RoomSession32.json' if '-AirportLighting32' in G.CMD else 'RoomSession31.json' if '-AirportArrival31' in G.CMD else 'RoomSession30.json' if '-AirportCheckin30' in G.CMD else 'RoomSession29.json' if '-AirportCheckin29' in G.CMD else 'RoomSession28.json' if '-AirportCheckin28' in G.CMD else 'RoomSession27.json' if '-AirportPrototype27' in G.CMD else 'RoomSession26.json' if '-AirportClarity26' in G.CMD else 'RoomSession25.json' if '-AirportFoyer25' in G.CMD else 'RoomSession24.json')).write_text(json.dumps(dict(status='READY',map=G.D.get('map','/Game/Airport24/L_Airport_Rooms24'),zone=zone,player=[x,y,z],journey={k:G.S.get(k,False) for k in ['checked_in','security','boarding','aboard']},controlled_doors={q['actor']:G.S['doors'][q['actor']]['fraction'] for q in S['access']},updated=time.time()),indent=2),encoding='utf-8')
def initialize(game):
 global G,R;G=game;R=G.R;S.update(base_act=G.act,base_physics=G.physics,access=[q for q in G.S['targets'] if q.get('access24')]);G.act=act;G.physics=physics
 G.event('Room-based airport24 ready',zones=len(G.D['zones']),controlled_leaves=len(S['access']))
