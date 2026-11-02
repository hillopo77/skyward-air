"""Independent corrected-gear extraction: actual retained mounts and door axes."""
import math
from flight39_surfaces import _clone,_centre


def build(ctx):
    import bpy
    from mathutils import Vector
    src=bpy.data.collections.get('SM_AP_P38B_GearContact39');assert src,'Run airside corrected10-tyre contact source first'
    ctx._flight39_depsgraph=bpy.context.evaluated_depsgraph_get();meta=ctx.D['flight39']
    fixed=ctx.new_collection('F39GearFixed','complex');groups={n:[] for n in ('main_L','main_R','nose','main_door_L','main_door_R','nose_door_L','nose_door_R')}
    for ob in src.objects:
        name=ob.name;c=_centre(ob)
        if name.startswith(('Upper trunnion bearing saddle','Gear door upper retained hinge','Nose gear bay upper bearing structure','Nose bay pinned hinge')):
            _clone(ctx,fixed,ob);continue
        side='R' if c.x>0 else 'L'
        role='nose_door_'+side if name.startswith(('Nose bay formed side door','Nose door inner pressed hat stiffener')) else 'main_door_'+side if name.startswith(('Main gear formed door','Door inner formed stiffener')) else 'nose' if c.y<0 else 'main_'+side
        groups[role].append(ob)
    records=[]
    for role,objects in groups.items():
        assert objects,role;side=1 if role.endswith('R') else -1
        if role=='nose':pivot=Vector((0,-6.12,-.55));axis=Vector((1,0,0));angle=90.
        elif role.startswith('main_door'):pivot=Vector((side*5.13,17.6,-1.18));axis=Vector((0,1,0));angle=side*88.
        elif role.startswith('nose_door'):
            hinges=[o for o in src.objects if o.name.startswith('Nose bay pinned hinge') and _centre(o).x*side>0]
            assert len(hinges)==2,(role,len(hinges));points=sorted([_centre(o) for o in hinges],key=lambda p:p.y)
            pivot=points[0];axis=(points[1]-points[0]).normalized();angle=side*88.
        else:pivot=Vector((side*4.45,17.6,-1.05));axis=Vector((0,1,0));angle=side*88.
        col=ctx.new_collection('F39Gear_'+role,'complex')
        for ob in objects:_clone(ctx,col,ob,pivot)
        name='Flight39 gear '+role;location=[pivot.x+16,pivot.y,pivot.z]
        ctx.add(col.name,name,location,collision=False,flight39_actuator=True,native_individual=True)
        records.append(dict(actor=name,asset=col.name,role=role,pivot=location,axis=list(axis),retracted_angle=angle,parts=len(objects)))
        meta['moving_names'].append(name)
    meta['gear_fixed_asset']=fixed.name;meta['gear_records']=records
    ob=ctx.scene.objects.get('SM_Plane_LandingGear')
    if ob:ob.instance_collection=fixed
    return dict(parts=sum(len(g) for g in groups.values()),moving_assemblies=len(records),fixed_upper_mounts=len(fixed.objects),contact_z=-3.689)
