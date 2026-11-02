"""Cold saved-library inventory and actual source apply with name collisions."""
import bpy,sys,json,copy,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5]
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import business_belt40 as M
import window41 as W
report=dict(passed=False)
try:
    for file,ids in [('BusinessBelt40_UnitKits.blend',M.IDS),('Window41_UnitKits.blend',list(W.SWAPS.values()))]:
        with bpy.data.libraries.load(str(F/file),link=False) as (src,dst):
            names=list(src.collections);assert set(ids)<=set(names),(file,set(ids)-set(names))
        report[file]=dict(required=ids,actual_saved_names_present=True,sha256=hashlib.sha256((F/file).read_bytes()).hexdigest())
    # Unrelated canonical names deliberately collide with every requested kit.
    # Actual appended collection objects must be mapped by immutable source ID.
    for name in M.IDS:bpy.data.collections.new(name)
    D=json.loads((R/'Exports/airport_layout.json').read_text());scene=bpy.context.scene
    dummy=bpy.data.collections.new('Old original source chair/lid library')
    for name in M.SEATS+['Business belt release '+str(i)+'12' for i in range(1,5)]:
        o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=dummy;scene.collection.objects.link(o)
    ctx=SimpleNamespace(a=a,D=D,R=R,scene=scene)
    def add(asset,name,location,**kwargs):
        D['instances'].append(dict(asset=asset,name=name,location=list(location),rotation_degrees=0.,scale=[1,1,1],**kwargs))
        o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=a.ASSETS[asset]['collection'];o.location=location;scene.collection.objects.link(o)
    def move(name,location):
        next(q for q in D['instances'] if q['name']==name)['location']=list(location);scene.objects[name].location=location
    ctx.add=add;ctx.move=move
    out=M.apply(ctx);count=len(bpy.data.collections);snapshot=copy.deepcopy(D);M.apply(ctx);assert count==len(bpy.data.collections) and D==snapshot
    for aid in M.IDS:
        c=a.ASSETS[aid]['collection'];assert c.name!=aid and c.get('business_belt40_asset_id')==aid and len(c.objects)>0,(aid,c.name,c.get('business_belt40_asset_id'),len(c.objects),c.use_fake_user)
    assert all(scene.objects[n].instance_collection==a.ASSETS[M.IDS[0]]['collection'] for n in M.SEATS)
    assert all(scene.objects['Business belt release '+str(i)+'12'].instance_collection==a.ASSETS[M.IDS[4]]['collection'] for i in range(1,5))
    report.update(passed=True,real_cold_apply=True,canonical_name_collisions=5,retained_kit_objects={n:len(a.ASSETS[n]['collection'].objects) for n in M.IDS},reapply_stable=True,records=len(out['records']))
except Exception:report['error']=traceback.format_exc()
(F/'BusinessBelt40_SavedLibraryVerification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
