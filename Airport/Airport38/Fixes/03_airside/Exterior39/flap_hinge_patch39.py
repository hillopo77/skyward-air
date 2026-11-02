"""Current-master flap hinge upgrade. Root owns save/export/native placement.

Recenter four existing derived actuator meshes and their instance origins
together, preserving every evaluated neutral world vertex. No fixed airframe,
dashboard, glass, runtime code, control mapping or interaction is rebuilt.
"""
import math

ACTORS=('Flight39 flap 00','Flight39 flap 01','Flight39 flap 06','Flight39 flap 07')
ASSET_IDS=('SM_AP_F39Surface_00','SM_AP_F39Surface_01','SM_AP_F39Surface_06','SM_AP_F39Surface_07')
VERSION=1


def _matrix(ob):
    from mathutils import Matrix
    return Matrix.LocRotScale(ob.location,ob.rotation_euler.to_quaternion(),ob.scale)


def _physical_hinge(ob):
    from mathutils import Vector
    T=_matrix(ob);points=list({tuple(round(float(v),6) for v in T@p.co):T@p.co for p in ob.data.vertices}.values())
    ends=sorted([min(p.x for p in points),max(p.x for p in points)],key=abs);fit=[]
    for x in ends:
        row=[p for p in points if abs(p.x-x)<.0002];y=min(p.y for p in row)
        near=[p for p in row if abs(p.y-y)<.0002];fit.append(sum(near,Vector())/len(near))
    return fit[0],(fit[1]-fit[0]).normalized()


def apply(ctx):
    import bpy
    from mathutils import Vector
    src=bpy.data.collections.get('SM_Plane_ExteriorAirframe')
    if src is None:raise RuntimeError('Original modeled aircraft collection is required for physical flap centreline fit')
    records={q['actor']:q for q in ctx.D['flight39']['surface_records']};instances={q['name']:q for q in ctx.D['instances']}
    offset=Vector(ctx.D['aircraft38']['offset']);report=dict(version=VERSION,changed_assets=[],records=[],scope='Only four existing inner flap actuators; neutral evaluated vertices retained')
    for name,aid in zip(ACTORS,ASSET_IDS):
        q=records[name];col=bpy.data.collections.get(aid)
        if col is None:raise RuntimeError('Existing derived flap kit required: '+aid)
        original=src.objects.get(q['original_part'])
        if original is None:raise RuntimeError('Modeled source flap missing: '+q['original_part'])
        pivot,axis=_physical_hinge(original);pivot+=offset;old=Vector(q['pivot']);delta=old-pivot
        neutral_error=0.;verts=0
        changed=delta.length>1e-7 or (Vector(q['axis'])-axis).length>1e-7
        if changed:
            for ob in col.objects:
                if ob.type!='MESH':raise AssertionError(('Unexpected derived flap object type',ob.name,ob.type))
                assert not ob.modifiers,('Derived evaluated actuator must have baked modifiers',ob.name)
                T=_matrix(ob);inv=T.inverted();ob.data=ob.data.copy()
                for v in ob.data.vertices:
                    world=T@v.co+old;v.co=inv@(T@v.co+delta)
                    neutral_error=max(neutral_error,(T@v.co+pivot-world).length);verts+=1
                ob.data.update()
            q['pivot']=list(pivot);q['axis']=list(axis);instances[name]['location']=list(pivot)
            obj=ctx.scene.objects.get(name)
            if obj:obj.location=pivot
            report['changed_assets'].append(aid)
        col['f39_physical_flap_hinge_version']=VERSION
        ctx.a.ASSETS[aid]=dict(collection=col,collision='none')
        for ob in col.objects:
            for mat in ob.data.materials:
                if mat:ctx.a.MATS[mat.name]=mat
        assert neutral_error<2e-6,('Neutral actuator geometry moved',name,neutral_error)
        report['records'].append(dict(actor=name,asset=aid,old_pivot=list(old),pivot=list(pivot),axis=list(axis),neutral_world_error_m=neutral_error,vertices_checked=verts,changed=changed))
    # This is the measured defect: exact mirror positions and axes must agree.
    for ln,rn in [('Flight39 flap 00','Flight39 flap 06'),('Flight39 flap 01','Flight39 flap 07')]:
        a,b=records[ln],records[rn];pa=Vector(a['pivot'])-offset;pb=Vector(b['pivot'])-offset
        pa.x=-pa.x;aa=Vector(a['axis']);aa.x=-aa.x
        assert (pa-pb).length<2e-6,('Physical flap hinge mirror failed',ln,rn,pa,pb)
        assert (aa-Vector(b['axis'])).length<2e-6,('Physical flap axis mirror failed',ln,rn)
    previous=ctx.D['flight39'].get('physical_flap_hinge_fit39')
    if not report['changed_assets'] and previous:
        report['already_applied']=True
        return report
    ctx.D['flight39']['physical_flap_hinge_fit39']=report
    return report
