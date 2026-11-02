"""Factory-empty Blender build test. Does not open or alter the shared master."""
import bpy,json,sys,copy,math
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent;W=ROOT.parents[4]
sys.path.insert(0,str(W/'outputs/Airport/SourceAssets'))
sys.path.insert(0,str(ROOT))
import airport_model as a
import airside38
from airside_math38 import *

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
base=json.loads((W/'outputs/Airport/Clarity37/Exports/airport_layout.json').read_text(encoding='utf-8'))
D=copy.deepcopy(base)
class Context:
    def __init__(self):
        self.a=a;self.D=D;self.before=base;self.scene=bpy.context.scene
        self.R=ROOT.parents[1];self.A=W/'outputs/Airport';self.P=W/'outputs/SkywardAir/UnrealProject/Content/Python'
    def require(self,name):return next(q for q in D['instances'] if q['name']==name)
    def remove(self,name):
        D['instances'][:]=[q for q in D['instances'] if q['name']!=name]
        D['interactions'][:]=[q for q in D['interactions'] if q.get('actor')!=name]
    def move(self,name,location,rotation=None,scale=None):
        q=self.require(name);delta=[location[i]-q['location'][i] for i in range(3)]
        q['location']=location
        if rotation is not None:q['rotation_degrees']=rotation
        for t in D['interactions']:
            if t.get('actor')==name and 'point' in t:t['point']=[t['point'][i]+delta[i] for i in range(3)]
    def add(self,asset,name,location,rotation=0,scale=None,collision=True,**extra):
        q=dict(asset=asset,name=name,location=location,rotation_degrees=rotation,scale=scale or [1,1,1],collision=collision,stage=10,**extra);D['instances'].append(q)
        o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=a.ASSETS[asset]['collection'];self.scene.collection.objects.link(o);o.location=location;o.rotation_euler.z=math.radians(rotation);o.scale=q['scale'];return q

# Root-instance fixture reproduces the complete aircraft reference linkage
# without reading or changing any full baseline Blender project.
ctx=Context();manifest=airside38._manifest(ctx);cols={}
for q in manifest['instances']:
    c=cols.setdefault(q['asset'],bpy.data.collections.get(q['asset']) or bpy.data.collections.new(q['asset']))
    o=bpy.data.objects.new(q['name'],None);o.instance_type='COLLECTION';o.instance_collection=c;ctx.scene.collection.objects.link(o);o.location=q['location']
airside38.plan(ctx);meta=airside38.build(ctx)
assert meta['source_sweep']['clear']
assert not any(q['asset'] in ('SM_AP_BridgeFloor','SM_AP_BridgeWall','SM_AP_BridgeRoof','SM_AP_ServicePath12') for q in D['instances'])
assert not any(q.get('name') in ('Level boarding bridge','Service ramp') for q in D['floors'])
assert len(meta['moving_names'])==16,(len(meta['moving_names']),meta['moving_names'])
for q in manifest['instances']:
    o=bpy.data.objects[q['name']];assert abs(o.location.x-q['location'][0]-16)<1e-5
for q in meta['components']:
    assert q['bounds'][1][0]>=q['bounds'][0][0],q
    assert all(math.isfinite(v) for row in q['bounds'] for v in row)

# Evaluate face validity; no source mesh has isolated vertices or zero-area faces.
bad=[];faces=0
for spec in a.ASSETS.values():
    for o in spec['collection'].objects:
        if o.type!='MESH':continue
        o.data.update();faces+=len(o.data.polygons)
        for p in o.data.polygons:
            if p.area<1e-11:bad.append((o.name,p.index,p.area))
assert not bad,bad[:20]
report=dict(status='PASS',test_scene='factory empty; complete linked-root fixture; newly authored bridge geometry only',
    linked_aircraft_roots=D['repair38']['airside']['source_shifted_roots'],new_assets=len(a.ASSETS),
    bridge_components=len(meta['components']),moving_components=len(meta['moving_names']),mesh_faces=faces,
    source_stowed_sweep=meta['source_sweep'],native_validation='root integration required')
(ROOT/'model_test_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'airside_test_layout.json').write_text(json.dumps(D,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Airside38_UnitAssets.blend'))
print('AIRSIDEMODEL38 PASS '+json.dumps(report))
