"""Targeted contact repair after genuine38 screenshots and actual-source scrutiny.

Root calls apply(ctx) in its existing source patch process. This module never
opens/saves a shared file or contacts an editor itself.
"""
import json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from airside_math38 import *

def _skin_bvh(ctx):
    import bpy
    from mathutils import Matrix,Vector
    from mathutils.bvhtree import BVHTree
    ids={'SM_Plane_ExteriorAirframe','SM_Plane_CabinFinish09','SM_Plane_WindowWall_L','SM_Plane_WindowWall_R',
         'SM_Plane_OuterWindowBarrel','SM_Plane_DoorBay07','SM_Plane_ForwardVestibule','SM_Plane_CockpitShell'}
    path=Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json'
    manifest=json.loads(path.read_text())['scenes']['L_Plane_Reference']
    cols={n:bpy.data.collections.get(n) for n in ids};assert all(cols.values()),'Preserved plane skin collections missing'
    dg=bpy.context.evaluated_depsgraph_get();vv=[];ff=[]
    for ins in manifest['instances']:
        if ins['asset'] not in cols or ins['location'][1]>4:continue
        T=Matrix.Translation(Vector(ins['location']))@Matrix.Rotation(ins['rotation'][2],4,'Z')
        for o in cols[ins['asset']].objects:
            if o.type!='MESH':continue
            e=o.evaluated_get(dg);m=e.to_mesh();n=len(vv);vv += [T@o.matrix_world@v.co for v in m.vertices]
            ff += [tuple(n+i for i in p.vertices) for p in m.polygons];e.to_mesh_clear()
    return BVHTree.FromPolygons(vv,ff)

def _canopy(ctx,col,report):
    import bpy
    from mathutils import Vector
    a=ctx.a;bvh=_skin_bvh(ctx);L=THRESHOLD[0]-NOSE_CAB[0]
    outer=[(-1.19,.04),(-1.19,2.16)]
    outer += [(-.81+.38*math.cos(math.radians(t)),2.16+.38*math.sin(math.radians(t))) for t in range(170,89,-10)]
    outer += [(.81,2.54)]
    outer += [(.81+.38*math.cos(math.radians(t)),2.16+.38*math.sin(math.radians(t))) for t in range(80,-1,-10)]
    outer += [(1.19,.04)]
    inner=[(1.08,.04),(1.08,2.16)]
    inner += [(.81+.27*math.cos(math.radians(t)),2.16+.27*math.sin(math.radians(t))) for t in range(10,91,10)]
    inner += [(-.81,2.43)]
    inner += [(-.81+.27*math.cos(math.radians(t)),2.16+.27*math.sin(math.radians(t))) for t in range(100,181,10)]
    inner += [(-1.08,.04)]
    contacts=[];surface_cache={}
    def surface(y,z):
        key=(round(y,6),round(z,6))
        if key not in surface_cache:
            h=bvh.ray_cast(Vector((-5,y+NOSE_CAB[1],z)),Vector((1,0,0)),10)
            assert h[0] is not None,('No fuselage support under canopy seal',y,z)
            x=h[0].x+16
            surface_cache[key]=x-NOSE_CAB[0]
            contacts.append(dict(y=y+NOSE_CAB[1],z=z,skin_x=x,new_contact_x=x+.012,old_membrane_front_x=13.891))
        return surface_cache[key]
    removed=[]
    for o in list(col.objects):
        if o.name.startswith(('Supported flexible accordion rib','Bellows flexible side membrane','Bellows flexible upper membrane')):
            removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    a.ACTIVE=col;start=2.70
    # Continuous weather membrane reaches the actual curved skin at every U
    # station; it does not stop in a flat plane ahead of the curved upper body.
    rings=[]
    for t in (0,.16,.33,.5,.67,.84,1):
        rings.append([(lerp(start,surface(y,z)+.012,t),y,z) for y,z in outer])
    o=a.loft('39 continuous contoured weather membrane',rings,'P38BRubber',False,False)
    mod=o.modifiers.new('Weatherproof canvas thickness39','SOLIDIFY');mod.thickness=.022
    outline=outer+inner;n=len(outline)
    for j in range(7):
        t=j/6;v=[]
        for depth in (-.018,.018):
            v += [(lerp(start,surface(y,z)+.012,t)+depth,y,z) for y,z in outline]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        a.mesh('39 contoured accordion support rib %02d'%j,v,faces,'P38BRubber',.006)
    # A genuine aperture return joins the broad cab walls to the narrower
    # flexible canopy, so there is no 270mm unsupported lateral opening.
    for side in (-1,1):
        a.box('39 canopy side aperture return',(start-.025,side*1.325,1.31),(.09,.30,2.62),'P38BShell',.018)
    a.box('39 canopy lintel aperture return',(start-.025,0,2.65),(.09,2.92,.22),'P38BShell',.02)
    a.ACTIVE=None
    report['canopy']=dict(asset=col.name,removed=removed,actual_skin_samples=contacts,
        start_world_x=NOSE_CAB[0]+start,terminal_contact_overlap_m=.012,
        previous_top_membrane_gap_m=max(q['skin_x']-q['old_membrane_front_x'] for q in contacts),
        new_max_contact_gap_m=0,door_clear_aperture_width_m=2.16)

def apply(ctx):
    import bpy
    from airside38 import _bounds
    D,a=ctx.D,ctx.a;report=dict(changed_assets=[],sleeves=[],characters=[],bevel_contact_clamps=[])
    for bank,count in [('A',4),('B',5)]:
        for index in range(count):
            aid='SM_AP_P38B_%s%02d'%(bank,index);col=bpy.data.collections.get(aid);assert col,aid
            w=(3.08 if bank=='A' else 2.98)-index*.075
            if not col.get('airside_contact39'):
                for o in col.objects:
                    if o.type!='MESH':continue
                    if o.name.startswith('Folded load bearing deck'):
                        o.data=o.data.copy()
                        for v in o.data.vertices:v.co.y*=(w+.10)/(w-.14)
                        o.data.update()
                    elif o.name.startswith('Fitted non-slip floor'):
                        o.data=o.data.copy()
                        for v in o.data.vertices:v.co.y*=(w-.09)/(w-.23)
                        o.data.update()
                    elif index==0 and o.name.startswith('Sealed telescoping bearing'):
                        # First sleeve is trimmed 1.14m away from the bend. Its
                        # bearing belongs at that supported wall start, not .08m
                        # from the pivot centre in the middle of the landing.
                        o.data=o.data.copy()
                        for v in o.data.vertices:v.co.x+=1.14
                        o.data.update()
                col['airside_contact39']=True
            a.ASSETS[aid]=dict(collection=col,collision='complex');report['changed_assets'].append(aid)
            report['sleeves'].append(dict(asset=aid,deck_width=w+.10,carpet_width=w-.09,wall_inner_half_width=w/2-.0375,
                old_open_floor_to_wall_gap_m=.0325,new_deck_under_wall_overlap_m=.0875,
                carpet_under_kick_seal_overlap_m=.0195,bearing_reseated=index==0))
    col=bpy.data.collections.get('SM_AP_P38B_docking_cab');assert col
    if not col.get('airside_contact39'):
        _canopy(ctx,col,report);col['airside_contact39']=True;col['airside_canopy39']=json.dumps(report['canopy'])
    else:report['canopy']=json.loads(col['airside_canopy39'])
    a.ASSETS[col.name]=dict(collection=col,collision='complex');report['changed_assets'].append(col.name)
    # Thin painted strips/gaskets inherited a bevel wider than half their
    # thickness. Blender clamped those corners to zero-area polygons. Bound
    # the fillet to 20% of the smallest real mesh dimension before export.
    for aid in report['changed_assets']:
        for o in bpy.data.collections[aid].objects:
            if o.type!='MESH' or not o.data.vertices:continue
            extents=[max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in range(3)]
            limit=min(extents)*.20
            for mod in o.modifiers:
                if mod.type=='BEVEL' and mod.width>limit:
                    report['bevel_contact_clamps'].append(dict(asset=aid,part=o.name,old=mod.width,new=limit));mod.width=limit
    for q in D.get('character_placements',[]):
        if q['actor'].startswith('CH12 Cabin passenger ') or q['actor']=='CH12 Business passenger':
            if not q.get('aircraft_offset_applied38'):
                q['location'][0]+=16;q['aircraft_offset_applied38']=True
            o=ctx.scene.objects.get(q['actor'])
            if o:o.location=q['location']
            report['characters'].append(dict(actor=q['actor'],location=q['location']))
    assert len(report['characters'])==7,report['characters']
    # Ground power is static: its model's lowest wheel vertex is +40mm, so
    # unlike the dynamic tug it cannot settle that gap through physics.
    for q in D['instances']:
        if q['name']=='GroundPower12_1954':
            q['location'][2]=-3.74;o=ctx.scene.objects.get(q['name'])
            if o:o.location=q['location']
            report['ground_power_base']=dict(actor=q['name'],actor_z=-3.74,wheel_local_min_z=.04,pad_top_z=-3.7,gap_m=0)
    _gear(ctx,report)
    # The final carrier stands on the decorative poured slab rather than the
    # lower underlying terrain. Synchronize true parked source/native poses.
    poses0=bridge_pose(0)
    for q in D['instances']:
        if q['name'] not in poses0:continue
        pose=poses0[q['name']];q['location']=list(pose['location'])
        if 'scale' in pose:q['scale']=pose['scale']
        o=ctx.scene.objects.get(q['name'])
        if o:o.location=q['location'];o.scale=q.get('scale',[1,1,1])
    D['aircraft38']['bounds']=[list(p) for p in AIRCRAFT_BOUNDS]
    D['aircraft38']['body_bounds']=[list(p) for p in BODY_AIRCRAFT_BOUNDS]
    bpy.context.view_layer.update()
    # Refresh the complete component bounds used by native departure validation;
    # wider decks and the longer upper canopy must never bypass that contract.
    obstacles=[];bridge=D['aircraft38']['bridge'];poses=bridge_pose(1)
    for q in bridge['components']:
        col=bpy.data.collections.get(q['asset']);assert col,q['asset']
        if q['asset'] in report['changed_assets']:q['bounds']=_bounds(col)
        if q['role']=='parking':continue
        pose=poses.get(q['name'])
        if q['name']=='Bridge38 cab mitre':pose=poses['Bridge38 docking cab']
        if not pose:
            ins=next(i for i in D['instances'] if i['name']==q['name']);pose=dict(location=ins['location'],rotation=ins['rotation_degrees'],scale=ins.get('scale',[1,1,1]))
        bb=posed_bounds(q['bounds'],pose)
        assert bb[1][0]<-9.75,(q['name'],bb)
        obstacles.append(dict(name=q['name'],bounds=bb))
    bridge['source_stowed_obstacles']=obstacles;bridge['source_sweep']=validate_sweep(obstacles)
    assert bridge['source_sweep']['clear'],bridge['source_sweep']
    report['stowed_sweep']=bridge['source_sweep'];report['max_stowed_x']=max(q['bounds'][1][0] for q in obstacles)
    D['aircraft38']['contact_refinement39']=report
    return report

def _gear(ctx,report):
    import bpy
    from mathutils import Vector
    a=ctx.a;aid='SM_AP_P38B_GearContact39';col=bpy.data.collections.get(aid)
    if not col:
        source=bpy.data.collections.get('SM_Plane_LandingGear');assert source,'Preserved landing gear missing'
        col=bpy.data.collections.new(aid)
        for src in source.objects:
            obj=src.copy()
            if src.data:obj.data=src.data.copy()
            col.objects.link(obj)
        wheels=[]
        for obj in col.objects:
            if obj.type!='MESH':continue
            T=obj.matrix_world.copy();inv=T.inverted()
            before=[T@v.co for v in obj.data.vertices]
            for v,p in zip(obj.data.vertices,before):
                # Uniform wheel/hub translation below the gland, smoothly
                # shortening oleos/braces while fixed top mounts stay fixed.
                t=clamp((-p.z-1.0)/1.7);p.z+=.511*t;v.co=inv@p
            obj.data.update()
            if obj.name.startswith('Revolved aircraft tire'):
                after=[T@v.co for v in obj.data.vertices]
                z0=min(p.z for p in before);z1=min(p.z for p in after)
                old_d=max(p.z for p in before)-z0;new_d=max(p.z for p in after)-z1
                assert abs(old_d-new_d)<2e-6,(obj.name,old_d,new_d)
                assert abs(z1+3.689)<3e-6,(obj.name,z1)
                cx=(min(p.x for p in after)+max(p.x for p in after))/2+16
                cy=(min(p.y for p in after)+max(p.y for p in after))/2
                wheels.append(dict(part=obj.name,old_bottom=z0,new_bottom=z1,diameter=old_d,contact_source=[cx,cy,z1]))
            for m in obj.data.materials:
                if m:a.MATS['Gear39_'+m.name]=m
        assert len(wheels)==10,len(wheels)
        col['gear_contact39']=json.dumps(dict(asset=aid,wheels=wheels,top_mounts_retained=True,oleo_compression_m=.511,tyre_diameters_preserved=True,contact_surface='Poured apron panel34 top -3.689'))
    meta=json.loads(col['gear_contact39']);a.ASSETS[aid]=dict(collection=col,collision='complex')
    obj=ctx.scene.objects.get('SM_Plane_LandingGear')
    if obj and obj.instance_type=='COLLECTION':obj.instance_collection=col
    report['changed_assets'].append(aid);report['gear']=meta;ctx.D['aircraft38']['gear_contact39']=meta
    ctx.D['aircraft38']['ground_contact39']=dict(gear_actor='SM_Plane_LandingGear',gear_asset=aid,
        tyre_bottom_z=-3.689,visual_apron_z=-3.689,body_lowest_z=BODY_AIRCRAFT_BOUNDS[0][2],
        body_to_apron_clearance_m=BODY_AIRCRAFT_BOUNDS[0][2]+3.689,
        fixed_cabin_floor_z=0,upper_gear_mounts_unchanged=True,rolling_contact=True,
        tyre_contacts=[q['contact_source'] for q in meta['wheels']],
        intent='Complete swept aircraft envelope includes gear. Tyres touch the supporting pavement; the body remains clear. A flight controller must treat support contact separately from lateral obstructions.')

def apply_gear_native(ctx):
    meta=ctx.D['aircraft38']['gear_contact39'];actors={a.get_actor_label():a for a in ctx.EA.get_all_level_actors()}
    actor=next((a for a in actors.values() if any(str(t)=='Skyward:SM_Plane_LandingGear' for t in a.tags)),actors.get('SM_Plane_LandingGear'))
    assert actor,'Original tagged gear actor missing'
    actor.static_mesh_component.set_static_mesh(ctx.mesh(meta['asset']))
    c,e=actor.get_actor_bounds(False);bottom=(c.z-e.z)/100
    assert abs(bottom+3.689)<.003,('Native gear/apron contact mismatch',bottom)
    return dict(actor=actor.get_actor_label(),asset=meta['asset'],bottom_z=bottom,visual_apron_z=-3.689,contact_error_m=abs(bottom+3.689))
