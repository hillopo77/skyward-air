"""Use the separately saved revision17 aircraft without changing legacy modes."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def install(P):
 P.DATA=copy.deepcopy(json.loads((ROOT/'Revision17/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']);base=P.nearest
 def nearest(kind=None):
  if P.STATE.get('seated') and isinstance(kind,tuple):kind=kind+('movable',)
  return base(kind)
 P.nearest=nearest
 return P

def start():
 import skyward_runtime as P;install(P);P.start()
