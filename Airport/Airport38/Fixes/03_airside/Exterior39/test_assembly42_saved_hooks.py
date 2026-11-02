"""Actual cold saved-library/source apply, with deliberate name collisions."""
import bpy,sys,json,copy,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace as NS
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5];sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import business_belt41 as B
import window42 as W
import aircraft_finish42 as A
report=dict(passed=False)
try:
    groups=[('BusinessBelt41_UnitKits.blend',B.IDS),('Window42_UnitKits.blend',list(W.SWAPS.values())),('AircraftFinish42_UnitKits.blend',list(A.SWAPS.values()))]
    bundles={}
    for file,ids in groups:
        with bpy.data.libraries.load(str(F/file),link=False) as (src,dst):assert set(ids)<=set(src.collections),(file,set(ids)-set(src.collections))
        bundles[file]=dict(assets=ids,sha256=hashlib.sha256((F/file).read_bytes()).hexdigest())
        for name in ids:bpy.data.collections.new(name)
    D=json.loads((R/'Exports/airport_layout.json').read_text());pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];scene=bpy.context.scene
    dummy=bpy.data.collections.new('Original B40 assembly parts')
    for r in D['repair38']['business_belt40']['records']:
        for name in (r['control'],r['worn_actor']):
            o=bpy.data.objects.new(name,None);o.instance_type='COLLECTION';o.instance_collection=dummy;scene.collection.objects.link(o)
    oldcols={n:bpy.data.collections.new(n) for n in W.SWAPS}
    import window40 as W40,window41 as W41
    for q in pm['instances']:
        old=W41.SWAPS.get(W40.SWAPS.get(q['asset']))
        if old not in oldcols:continue
        o=bpy.data.objects.new(q['name'],None);o.instance_type='COLLECTION';o.instance_collection=oldcols[old];o.location=[x+y for x,y in zip(q['location'],D['aircraft38']['offset'])];scene.collection.objects.link(o)
    for q in pm['instances']:
        if q['asset'] not in A.SWAPS:continue
        o=bpy.data.objects.new(q['name'],None);o.instance_type='COLLECTION';o.instance_collection=dummy;o.location=[x+y for x,y in zip(q['location'],D['aircraft38']['offset'])];scene.collection.objects.link(o)
    ctx=NS(a=a,D=D,R=R,scene=scene);outputs=[]
    for module in (B,W,A):
        outputs.append(module.apply(ctx));snapshot=copy.deepcopy(D);count=len(bpy.data.collections);module.apply(ctx);assert snapshot==D and count==len(bpy.data.collections),module.__name__
    assert len(a.ASSETS)==9,len(a.ASSETS)
    assert all(c['collection'].name!=key for key,c in a.ASSETS.items()),'Collision test did not force loaded .001 mapping'
    for r in D['repair38']['business_belt40']['records']:assert r['worn_asset'] in B.IDS and abs(r['worn_hinge'][2]-.622)<1e-6
    (F/'Assembly42_SourceData.json').write_text(json.dumps(D['repair38'],indent=2));report.update(passed=True,bundles=bundles,actual_cold_source_apply=True,canonical_name_collisions=9,source_reapply_stable=True,outputs=outputs)
except Exception:report['error']=traceback.format_exc()
(F/'Assembly42_SavedHooksVerification.json').write_text(json.dumps(report,indent=2));print('ASSEMBLY42_SAVED_HOOKS',report['passed'],report.get('error',''),flush=True)
