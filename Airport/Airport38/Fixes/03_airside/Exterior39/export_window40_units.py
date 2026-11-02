"""Export ONLY the private Window40 unit source into its isolated package."""
import bpy,json,sys
from pathlib import Path
from types import SimpleNamespace
F=Path(__file__).parent;R=F.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(F/'Window40_UnitKits.blend'),load_ui=False)
sys.path.insert(0,str(F));import window40
target=F/'Window40Package';(target/'Exports/FBX').mkdir(parents=True,exist_ok=True)
assets={n:dict(collection=bpy.data.collections[n],collision='complex') for n in window40.SWAPS.values()};materials={}
for aid,spec in assets.items():
    for ob in spec['collection'].objects:
        if not ob.data or not hasattr(ob.data,'materials'):continue
        for index,m in enumerate(ob.data.materials):
            if m is None:
                assert not any(p.material_index==index for p in ob.data.polygons),(aid,ob.name,index)
                ob.data.materials[index]=bpy.data.materials['MI_Plane_Cabin09'];m=ob.data.materials[index]
            materials[m.name]=m
source=R.parent/'Rooms24/SourceAssets/airport_export24.py';code=source.read_text().replace("(a.ROOT/'Airport_Rooms24.blend')","(F/'Window40_UnitKits.blend')")
ns=dict(F=F);exec(compile(code,str(source),'exec'),ns);ns['export'](SimpleNamespace(ASSETS=assets,MATS=materials,ROOT=target))
manifest=json.loads((target/'Exports/airport_assets.json').read_text());assert len(manifest['assets'])==10
print('WINDOW40_PACKAGE',len(manifest['assets']),target,flush=True)
