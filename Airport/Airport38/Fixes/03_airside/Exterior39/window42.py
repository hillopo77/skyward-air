"""Monotone molded inner window return; preserve frozenWindow41 mechanics."""
from pathlib import Path
import window40 as W
import window41 as B
F=Path(__file__).parent
SWAPS={'SM_AP_W41WindowWallL':'SM_AP_W42WindowWallL','SM_AP_W41WindowWallR':'SM_AP_W42WindowWallR','SM_AP_W41ShadeFrameL':'SM_AP_W42ShadeFrameL','SM_AP_W41ShadeFrameR':'SM_AP_W42ShadeFrameR'}

def build_units(ctx):
    import bpy
    from mathutils import Vector
    a=ctx.a;W._aliases(a);result={}
    for old,new in SWAPS.items():
        c=bpy.data.collections.new(new);c.use_fake_user=True;c['window42_asset_id']=new;c['window42_version']=1
        for ob in bpy.data.collections[old].objects:
            if ob.name.startswith('W41 continuous rolled collar shields actual guide channels'):continue
            if 'ShadeFrame' in new and ob.name.startswith('W41 thin formed upper-corner mechanism shield'):continue
            o=ob.copy();o.data=ob.data.copy();c.objects.link(o)
        a.ACTIVE=c
        rings=[];side=-1 if new.endswith('L') else 1
        if 'ShadeFrame' in new:
            for ob in c.objects:
                if ob.name.startswith('W41 captive guide'):
                    ob.data.materials.clear();ob.data.materials.append(a.MATS['W40Felt'])
                    # Section4's extra24mm stack offset put its rear face1mm
                    # into the retained rear wear lip. Widen only the rear wall
                    #4mm, preserving the front capture lip and all shade paths.
                    for v in ob.data.vertices:
                        if v.index%8 in (0,1,6,7):v.co.x+=side*.010
                        # The old straight channel continued below the rounded
                        # sill and visibly protruded as two loose dark feet.
                        # Its retained stop now terminates behind the lower
                        # side reveal; the closed leaf remains captured above.
                        if v.co.z+.92<1.025:v.co.z=1.025-.92
                    ob.data.update()
                if ob.name.startswith('W40 retained curved cassette with actual feed mouth'):
                    T=W._matrix(ob);inv=T.inverted()
                    for v in ob.data.vertices:
                        p=T@v.co;z=p.z+.92;absolute=abs(side*2.3+p.x)
                        if absolute>2.08:p.x=side*(W.pressure_x(z)-.0055-2.3);v.co=inv@p
                    ob.data.update()
                    for m in ob.modifiers:
                        if m.type=='SOLIDIFY':m.thickness=.002
            def local(x,y,z):return (side*(x-2.3),y,z-.92)
            rows=[]
            for z in (2.002,2.005,2.011,2.023,2.038,2.049,2.055,2.058):
                x=2.102-.042*W.smooth((z-2.005)/.050)
                rows.append([local(x,-.416,z),local(x,.416,z)])
            hood=a.loft('W42 short rounded cassette feed cowl',rows,'W40Pearl',False,False);solid=hood.modifiers.new('Formed cowl wall gauge','SOLIDIFY');solid.thickness=.003;solid.offset=0
            bevel=hood.modifiers.new('Feed cowl rolled safe edges','BEVEL');bevel.width=.0012;bevel.segments=3
            a.ASSETS[new]=dict(collection=c,collision='complex');result[new]=dict(pointed_shields_removed=2,captive_channel_positions_unchanged=True,short_rounded_feed_cowl=True);continue
        specs=[(.96,1.28,.24,'root'),(.948,1.272,.236,'roll15'),(.925,1.25,.230,'roll50'),(.889,1.218,.216,'roll86'),(.86,1.19,.207,'front'),(.690,1.00,.160,'front')]
        for width,height,radius,role in specs:
            row=[]
            for y,z,_ in W._loop(width,height,radius,1.46):
                root=W.pressure_x(z)-.065;x=root if role=='root' else root+(B.cover_x(z)-root)*int(role[4:])/100 if role.startswith('roll') else B.cover_x(z)
                row.append((side*x,y,z))
            rings.append(row)
        # One ruled, strictly monotone return. No narrow .680 waist and no
        # .704 overshoot back beyond the .700 actual aperture. Matching angular
        # rays are interpolated directly, avoiding competing rounded contours.
        front=rings[-1];edge=[(side*(W.pressure_x(z)-.008),y,z) for y,z,_ in W._loop(.700,1.,.160,1.46)]
        for t in (.10,.23,.40,.60,.77,.90,1.):rings.append([tuple(Vector(p).lerp(Vector(q),t)) for p,q in zip(front,edge)])
        ob=W._ringmesh(a,'W42 continuous monotone rolled window reveal',rings,'W40Reveal',-side)
        # The shade lives between inner bezel and outer pressure reveal. A
        # continuous fake return through that space clips the moving corners.
        # Form a real2mm molded wall and cut its hidden service chase from a
        # conservative continuous swept envelope, retaining the front lip.
        bpy.context.scene.collection.children.link(c)
        solid=ob.modifiers.new('Actual formed reveal gauge','SOLIDIFY');solid.thickness=.002;solid.offset=0
        bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.modifier_apply(modifier=solid.name)
        levels=[.90+i*(2.34-.90)/144 for i in range(145)];rows=[]
        for z in levels:
            inner=W.track_x(z)-.0005;outer=W.track_x(z-.255)+.0405
            rows.append([(side*inner,-.3525,z),(side*outer,-.3525,z),(side*outer,.3525,z),(side*inner,.3525,z)])
        cutter=a.loft('W42 temporary exact swept shade service chase',rows,'W40Pearl',True,True)
        import bmesh
        bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(cutter.data);bm.free();cutter.data.update()
        mod=ob.modifiers.new('Actual enclosed shade service relief','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);ob.select_set(False);bpy.context.scene.collection.children.unlink(c)
        c['window42_details']='Single monotone .690 to .700 inner return with enclosed shade service chase; full normal-eye pressure-aperture view and mechanics unchanged';a.ASSETS[new]=dict(collection=c,collision='complex');result[new]=dict(inner_widths=[.690,.700],no_reverse_profile=True,actual_pressure_aperture=[.70,1.])
    return result

def apply(ctx):
    import bpy
    ids=tuple(SWAPS.values());existing={n:next((c for c in bpy.data.collections if c.get('window42_asset_id')==n),None) for n in ids};requested=tuple(n for n in ids if not existing[n])
    if requested:
        with bpy.data.libraries.load(str(F/'Window42_UnitKits.blend'),link=False) as (src,dst):
            assert set(ids)<=set(src.collections);dst.collections=list(requested)
        loaded=dict(zip(requested,dst.collections))
    else:loaded={}
    for old,new in SWAPS.items():
        c=existing[new] or loaded[new];c.use_fake_user=True;ctx.a.ASSETS[new]=dict(collection=c,collision='complex')
        for ob in c.objects:
            for mat in ob.data.materials:
                if mat:ctx.a.MATS[mat.name]=mat
        for ob in ctx.scene.objects:
            if ob.instance_type=='COLLECTION' and ob.instance_collection and (ob.instance_collection.name==old or ob.instance_collection.get('window42_asset_id')==new):ob.instance_collection=c
        for q in ctx.D['instances']:
            if q['asset']==old:q['asset']=new
    result=dict(version=1,assets=list(ids),source_only_reveal_profile=True,all_window41_mechanics_and_transforms_unchanged=True);ctx.D.setdefault('repair38',{})['window42']=result;return result

def prepare_plane(P,D):
    for q in P.DATA['instances']:
        if q['asset'] in SWAPS:q['asset']=SWAPS[q['asset']]
    P.DATA['window42_prepared']=1

def apply_native(ctx):
    import json
    pm=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];targets={q['name']:SWAPS[B.SWAPS[W.SWAPS[q['asset']]]] for q in pm['instances'] if W.SWAPS.get(q['asset']) in B.SWAPS and B.SWAPS[W.SWAPS[q['asset']]] in SWAPS};changed=[]
    for actor in ctx.EA.get_all_level_actors():
        key=next((str(t)[8:] for t in actor.tags if str(t).startswith('Skyward:')),None)
        if key not in targets:continue
        c=actor.get_component_by_class(ctx.u.StaticMeshComponent);mesh=ctx.mesh(targets[key]);c.set_static_mesh(mesh)
        for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
        changed.append(key)
    assert len(changed)==96,len(changed);return dict(status='APPLIED_REQUIRES_NATIVE_CORNER_REVIEW',swapped=changed,movement_or_controls_changed=False)
