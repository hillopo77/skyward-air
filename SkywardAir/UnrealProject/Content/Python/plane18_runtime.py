"""Use the separately saved revision17 aircraft without changing legacy modes."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def install(P):
 P.DATA=copy.deepcopy(json.loads((ROOT/'Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']);base=P.nearest
 def nearest(kind=None):
  if P.STATE.get('seated') and isinstance(kind,tuple):kind=kind+('movable',)
  return base(kind)
 P.nearest=nearest;original_apply=P._apply_movable
 def apply(m):
  q=m['item']
  if q.get('motion',{}).get('type')!='roller_shade18':return original_apply(m)
  if m.get('last_shade18')==m['progress']:return
  m['last_shade18']=m['progress'];f=m['progress'];f=f*f*(3-2*f)
  for part in q['roller_parts']:
   a=P.STATE['actors'][part['actor']];a.set_actor_location(P.vector(part['closed_location'])+P.vector(part['delta'])*f,False,True)
  m['closed_point']=P.vector(q['point'])-m['actor'].get_actor_location()
 P._apply_movable=apply
 return P

def start():
 import skyward_runtime as P;install(P);P.start()
