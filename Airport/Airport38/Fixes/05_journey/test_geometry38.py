"""Factory-empty Blender geometry validation, no shared master/editor touched."""
import bpy,sys,json,copy,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;A=HERE.parents[2]
sys.path[:0]=[str(A/'SourceAssets'),str(HERE),str(HERE.parent/'02_equipment')]
import airport_model as a
import equipment38 as E
import journey38 as J
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
class C:
    a=a;scene=bpy.context.scene
    def __init__(self):self.D=json.loads((A/'Clarity37/Exports/airport_layout.json').read_text())
    def require(self,n):return next(q for q in self.D['instances'] if q['name']==n)
    def move(self,n,p,rotation=None,scale=None):
        q=self.require(n);q['location']=list(p)
        if rotation is not None:q['rotation_degrees']=rotation
    def add(self,asset,name,location,rotation=0,scale=None,collision=True,**extra):
        asset=asset if asset.startswith('SM_') else 'SM_AP_'+asset
        q=dict(asset=asset,name=name,location=list(location),rotation_degrees=rotation,scale=scale or [1,1,1],collision=collision,stage=10,**extra)
        self.D['instances'].append(q);return q
ctx=C();E.plan(ctx);J.plan(ctx);J.build(ctx)
for it in a.ASSETS.values():bpy.context.scene.collection.children.link(it['collection'])
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
result=dict(scope='Isolated source geometry, not native game verification',assets={},checks=[])
def check(n,b):assert b,n;result['checks'].append(n)
def bounds(ob):
    ev=ob.evaluated_get(dg);me=ev.to_mesh();points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
for aid,it in a.ASSETS.items():
    dupe=zero=bad=faces=0;zero_parts=[]
    for o in it['collection'].objects:
        ev=o.evaluated_get(dg);me=ev.to_mesh()
        if not me:continue
        seen=set()
        zz=0
        for f in me.polygons:
            faces+=1
            if f.area<1e-12:zero+=1;zz+=1
            k=tuple(sorted(tuple(round(v,8) for v in me.vertices[i].co) for i in f.vertices))
            if k in seen:dupe+=1
            seen.add(k)
        bad+=sum(not all(math.isfinite(x) for x in v.co) for v in me.vertices)
        if zz:zero_parts.append([o.name,zz])
        ev.to_mesh_clear()
    result['assets'][aid]=dict(parts=len(it['collection'].objects),faces=faces,zero_area=zero,duplicate_faces=dupe,nonfinite=bad)
    if zero:print('ZERO PARTS',aid,zero_parts,flush=True)
    check(aid+' has no zero-area evaluated faces',zero==0)
    check(aid+' has no within-partduplicate faces/nonfiniteverts',dupe==bad==0)
col=a.ASSETS['SM_AP_BaggageDetail38']['collection']
rack=[bounds(o) for o in col.objects if o.name.startswith(('Baggage handling rack','Handling rack','Receiving transport tub','Transport tub','Tub painted','Rolled restraint','Restraint'))]
check('Rack north edge clears lane02 guard by>=1.15m',min(b[0][1] for b in rack)>-18.5 and max(b[1][1] for b in rack)<-17.76)
check('Service leaf is on publicface clearofsolidwall',ctx.require('Baggage service door38')['location'][0]-.075/2>-21.91)
check('Both actual transfer openings supplied',len(ctx.D['service_openings38'])==2)
check('Two transfer bodies continue torealreceivers',len([q for q in ctx.D['instances'] if q['asset']=='SM_AP_Transfer38'])==2)
check('No collider spans scanmouth',a.ASSETS['SM_AP_Transfer38']['collision']=='complex')
check('One finitecup only',len([q for q in ctx.D['instances'] if q['asset']=='SM_AP_ServingCup38'])==1)
check('Cup has native-simple collision contract',a.ASSETS['SM_AP_ServingCup38']['collision']=='convex')
check('A08 isinformation',next(q for q in ctx.D['interactions'] if q['actor']=='Gate A08 boarding desk')['kind']=='information')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Journey38_EditableKit.blend'))
(HERE/'geometry_results38.json').write_text(json.dumps(result,indent=2))
(HERE/'planned_journey_layout38.json').write_text(json.dumps(ctx.D,indent=2))
print('JOURNEY38 GEOMETRY PASS',len(result['checks']))
