import bpy,sys,json,copy,traceback,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
F=Path(__file__).parent;R=F.parents[2];sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a,console_surface43 as M
report=dict(passed=False)
try:
    with bpy.data.libraries.load(str(F/'ConsoleSurface43_UnitKit.blend'),link=False) as (src,dst):assert M.ID in src.collections
    bpy.data.collections.new(M.ID);dummy=bpy.data.collections.new(M.OLD);ob=bpy.data.objects.new('SM_Plane_AnalogDashboard',None);ob.instance_type='COLLECTION';ob.instance_collection=dummy;ob.location=(16,0,0);bpy.context.scene.collection.objects.link(ob)
    D=json.loads((R/'Exports/airport_layout.json').read_text());before=copy.deepcopy(D['flight39']);ctx=NS(a=a,D=D,scene=bpy.context.scene);out=M.apply(ctx);count=len(bpy.data.collections);snapshot=copy.deepcopy(D);M.apply(ctx);assert snapshot==D and count==len(bpy.data.collections)
    assert ob.instance_collection.name!=M.ID and ob.instance_collection.get('console_surface43_asset_id')==M.ID and tuple(ob.location)==(16,0,0)
    assert [key for key in before if before[key]!=D['flight39'][key]]==['dashboard_fixed_asset']
    report.update(passed=True,actual_cold_library=True,name_collision_mapped=True,source_repeat_safe=True,only_flight_metadata_field_changed='dashboard_fixed_asset',all_needle_button_pivot_arrays_preserved=True,source_actor_transform_unchanged=True,asset=M.ID,bundle_sha256=hashlib.sha256((F/'ConsoleSurface43_UnitKit.blend').read_bytes()).hexdigest())
except Exception:report['error']=traceback.format_exc()
(F/'ConsoleSurface43_SavedHookVerification.json').write_text(json.dumps(report,indent=2));print('CONSOLE43_SAVED_HOOK',report['passed'],report.get('error',''),flush=True)
