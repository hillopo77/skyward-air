"""Isolated read-only current-master verification. Never saves a blend/export."""
import bpy,json,sys,copy,math,traceback
from pathlib import Path
from types import SimpleNamespace
from mathutils import Matrix,Vector

F=Path(__file__).parent;R=F.parents[2]
sys.path[:0]=[str(F),str(R/'Fixes/05_journey/Flight39')]
import flap_hinge_patch39 as H
import flight39_surfaces as B
report=dict(scope='Private Blender process reads current saved master; no master/export writes',saved_master=False,passes=[])

try:
    bpy.ops.wm.open_mainfile(filepath=str(R/'Airport_Repaired38.blend'),load_ui=False)
    scene=bpy.context.scene;D=json.loads(scene.get('layout_json') or (R/'Exports/airport_layout.json').read_text())
    ctx=SimpleNamespace(a=SimpleNamespace(ASSETS={},MATS={}),D=D,scene=scene)
    records={q['actor']:q for q in D['flight39']['surface_records']}
    source=bpy.data.collections['SM_Plane_ExteriorAirframe']
    if source.name not in scene.collection.children:scene.collection.children.link(source)
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def points(aid,pivot):
        out=[]
        for ob in bpy.data.collections[aid].objects:
            ev=ob.evaluated_get(dg);me=ev.to_mesh();T=H._matrix(ob)
            out.extend(T@v.co+Vector(pivot) for v in me.vertices);ev.to_mesh_clear()
        return out
    before={n:points(records[n]['asset'],records[n]['pivot']) for n in H.ACTORS}
    source_points={}
    for n in H.ACTORS:
        q=records[n];ob=source.objects[q['original_part']];T=H._matrix(ob);ev=ob.evaluated_get(dg);me=ev.to_mesh()
        source_points[n]=[T@v.co+Vector(D['aircraft38']['offset']) for v in me.vertices];ev.to_mesh_clear()
    first=H.apply(ctx);bpy.context.view_layer.update()
    expected=set(H.ASSET_IDS)
    assert set(first['changed_assets'])==expected or (not first['changed_assets'] and D['flight39'].get('physical_flap_hinge_fit39')),first
    unchanged=[];source_errors=[];total=0
    for n in H.ACTORS:
        q=records[n];after=points(q['asset'],q['pivot']);assert len(after)==len(before[n])
        error=max((p-q).length for p,q in zip(before[n],after));assert error<2e-6,(n,error);total+=len(after)
        src=source_points[n];source_error=max(min((p-s).length for s in src) for p in after);assert source_error<2e-6,(n,source_error)
        original=source.objects[q['original_part']];p,a=B._hinge(original);p+=Vector(D['aircraft38']['offset'])
        assert (p-Vector(q['pivot'])).length<2e-6,(n,'fresh build/current upgrade pivot disagreement',p,q['pivot'])
        assert (a-Vector(q['axis'])).length<2e-6,(n,'fresh build/current upgrade axis disagreement')
        unchanged.append(dict(actor=n,vertices=len(after),max_neutral_world_error_m=error,max_original_evaluated_geometry_error_m=source_error))
    report['passes'].append(dict(pass_id=1,check='Original evaluated neutral shape and current derived shape retained through recenter',vertices=total,results=unchanged))
    mirror=[]
    for l,r in [(H.ACTORS[0],H.ACTORS[2]),(H.ACTORS[1],H.ACTORS[3])]:
        a,b=records[l],records[r];p=Vector(a['pivot']);p.x=32-p.x;axis=Vector(a['axis']);axis.x=-axis.x
        error=(p-Vector(b['pivot'])).length;ae=(axis-Vector(b['axis'])).length
        assert error<2e-6 and ae<2e-6
        # Actual geometric surfaces also preserve mirrored deflection. Use
        # leading/trailing edges away from the gear well's open lower apertures.
        left=points(a['asset'],a['pivot']);right=points(b['asset'],b['pivot']);errors=[]
        for deg in (0,5,15):
            lm=Matrix.Rotation(math.radians(-a['side']*deg),4,Vector(a['axis']));rm=Matrix.Rotation(math.radians(-b['side']*deg),4,Vector(b['axis']))
            transformed=[rm@(v-Vector(b['pivot']))+Vector(b['pivot']) for v in right]
            pp=[]
            # Probe only vertices with true mirrored original counterparts.
            for v in left:
                vm=v.copy();vm.x=32-vm.x
                if min((vm-w).length for w in right)>2e-6:continue
                v=lm@(v-Vector(a['pivot']))+Vector(a['pivot']);v.x=32-v.x
                pp.append(min((v-w).length for w in transformed))
            e=max(pp);assert e<3e-6,(l,r,deg,e);errors.append(dict(angle=deg,max_mirrored_surface_error_m=e,points=len(pp)))
        mirror.append(dict(left=l,right=r,pivot_error_m=error,axis_vector_error=ae,deflected_geometry=errors))
    report['passes'].append(dict(pass_id=2,check='Physical hinge symmetry plus actual neutral/5deg/15deg mirrored deflected vertices',pairs=mirror))
    snap=copy.deepcopy(D);geometry={n:[tuple(v) for v in points(records[n]['asset'],records[n]['pivot'])] for n in H.ACTORS};again=H.apply(ctx)
    assert again['changed_assets']==[] and D==snap
    assert geometry=={n:[tuple(v) for v in points(records[n]['asset'],records[n]['pivot'])] for n in H.ACTORS}
    report['passes'].append(dict(pass_id=3,check='Repeated current-master upgrade leaves metadata and all evaluated neutral vertices identical',idempotent=True))
    report.update(passed=True,changed_assets=first['changed_assets'],patch=first)
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'FlapHinge39_Verification.json').write_text(json.dumps(report,indent=2));print('FLAP_HINGE39',report['passed'],report.get('changed_assets'),report.get('error',''),flush=True)
