"""Read saved Airport38 in a separate process; never save or mutate the master."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;R=H.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'Airport_Repaired38.blend'),load_ui=False)
D=json.loads((R/'Exports/airport_layout.json').read_text())
selected=['Vanity34','Toilet34','Scanner38','Counter38','Charging34','CafeTable34','CafeChair34','Bench27','Bench29','Bench34','TableSetting36','Espresso36','Bakery36','POS36','Tea36','Sofa36','OvalTable36','RetainedCraft38','HandDryer','PH_Camera24','ScreenBoard','Information27','Kiosk','Join30','Header130','Header230','Bins36','Recycling38','Trolley','GroundPower34','FireStand11','SafetyStation27','OperatorConsole36','StaffStorage38','TravelStorage38','GalleryStair35','ServingCup38','ServingSaucer38']
report=dict(source=str(R/'Airport_Repaired38.blend'),read_only=True,assets={},instances=[q for q in D['instances'] if q['asset'] in ['SM_AP_'+s for s in selected]])
dg=bpy.context.evaluated_depsgraph_get()
for aid in selected:
    col=bpy.data.collections.get('SM_AP_'+aid)
    if not col:continue
    parts=[]
    for ob in col.objects:
        if ob.get('export_ignore') or ob.type not in ['MESH','FONT','CURVE']:continue
        ev=ob.evaluated_get(dg);pts=[ev.matrix_world@Vector(v) for v in ev.bound_box]
        if not pts:continue
        q=dict(name=ob.name,type=ob.type,min=[min(p[i] for p in pts) for i in range(3)],max=[max(p[i] for p in pts) for i in range(3)],hidden_render=ob.hide_render,materials=[m.name if m else None for m in ob.data.materials])
        if ob.type=='FONT':q['body']=ob.data.body
        parts.append(q)
    report['assets']['SM_AP_'+aid]=parts
(H/'retained_inventory38.json').write_text(json.dumps(report,indent=2))
print('READ_ONLY_PROP_SCAN38',len(report['assets']),sum(len(v) for v in report['assets'].values()))
