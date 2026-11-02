"""Replace only the failed fixed toggle-tray fascia; keep Flight39 instruments."""
from pathlib import Path
import math
F=Path(__file__).parent
OLD='SM_AP_F39DashboardFixed';ID='SM_AP_C43DashboardFixed'

def build_unit(ctx):
    import bpy,bmesh
    from mathutils import Vector
    a=ctx.a;src=bpy.data.collections[OLD];old=next(o for o in src.objects if o.name.startswith('Hollow switch tray casting'));points=[old.matrix_world@v.co for v in old.data.vertices];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    c=bpy.data.collections.new(ID);c.use_fake_user=True;c['console_surface43_asset_id']=ID
    for ob in src.objects:
        if ob==old:continue
        q=ob.copy();q.data=ob.data.copy();c.objects.link(q)
    panel=next(m for m in old.data.materials if m and m.name.startswith('MI_Plane_Panel'));a.MATS['C43Panel']=panel;a.MATS['C43Dark']=next(m for m in old.data.materials if m and m.name.startswith('MI_Plane_CutoutDark'));a.ACTIVE=c
    w=hi[0]-lo[0];depth=hi[1]-lo[1];cy=(lo[1]+hi[1])/2;outer=a.rr(w,depth,.018,16);inner=a.rr(w-.0432,depth-.040,.012,16);n=len(outer)
    vertices=[(x,y+cy,z) for loop,z in [(outer,lo[2]),(outer,hi[2]),(inner,hi[2]),(inner,lo[2])] for x,y in loop];faces=[(k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j) for k in range(4) for j in range(n)]
    ob=a.mesh('C43 formed hollow toggle-tray casting with planar fascia',vertices,faces,'C43Panel');bpy.context.scene.collection.children.link(c)
    def recalc(obj):
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
    recalc(ob)
    for x in (-.1728,0,.1728):
        loop=a.rr(.108,.015,.006,12);nn=len(loop);vv=[(x+xx,hi[1]+y,.966+z) for y in (-.040,.040) for xx,z in loop];ff=[tuple(reversed(range(nn))),tuple(nn+i for i in range(nn))]+[(j,(j+1)%nn,nn+(j+1)%nn,nn+j) for j in range(nn)]
        cutter=a.mesh('C43 temporary actual rounded vent bore',vv,ff,'C43Dark');recalc(cutter);mod=ob.modifiers.new('Actual front ventilation bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    recalc(ob)
    # Broad faces are genuinely planar with flat corner normals. Only the real
    # rounded vertical corners are smooth; Boolean triangles cannot pull a
    # whole fascia's highlight into an inverted diamond.
    for p in ob.data.polygons:p.use_smooth=abs(p.normal.x)>1e-4 and abs(p.normal.y)>1e-4
    bevel=ob.modifiers.new('Safe1.5mm manufactured tray edge rolls','BEVEL');bevel.width=.0015;bevel.segments=3;bevel.use_clamp_overlap=True;bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(28);ob.select_set(False);bpy.context.scene.collection.children.unlink(c)
    a.ASSETS[ID]=dict(collection=c,collision='complex');return dict(asset=ID,only_replaced_part=old.name,bounds_before=[lo,hi],vent_centres=[[-.1728,hi[1],.966],[0,hi[1],.966],[.1728,hi[1],.966]],all_other_objects_preserved=len(c.objects)-1)

def apply(ctx):
    import bpy
    c=next((c for c in bpy.data.collections if c.get('console_surface43_asset_id')==ID),None)
    if c is None:
        with bpy.data.libraries.load(str(F/'ConsoleSurface43_UnitKit.blend'),link=False) as (src,dst):
            assert ID in src.collections;dst.collections=[ID]
        c=dst.collections[0]
    c.use_fake_user=True;ctx.a.ASSETS[ID]=dict(collection=c,collision='complex')
    for o in c.objects:
        for m in o.data.materials:
            if m:ctx.a.MATS[m.name]=m
    ob=ctx.scene.objects.get('SM_Plane_AnalogDashboard');assert ob is not None;ob.instance_collection=c
    for q in ctx.D['instances']:
        if q['asset']==OLD:q['asset']=ID
    ctx.D['flight39']['dashboard_fixed_asset']=ID
    report=dict(version=1,asset=ID,exact_fixed_fascia_only=True,flight39_dashboard_metadata_updated=True);ctx.D.setdefault('repair38',{})['console_surface43']=report;return report

def prepare_plane(P,D):
    for q in P.DATA['instances']:
        if q['name']=='SM_Plane_AnalogDashboard':q['asset']=ID
    P.DATA['console_surface43_prepared']=1

def apply_native(ctx):
    matches=[a for a in ctx.EA.get_all_level_actors() if any(str(t)=='Skyward:SM_Plane_AnalogDashboard' for t in a.tags)];assert len(matches)==1
    actor=matches[0];c=actor.get_component_by_class(ctx.u.StaticMeshComponent);mesh=ctx.mesh(ID);c.set_static_mesh(mesh)
    for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
    assert ctx.D['flight39']['dashboard_fixed_asset']==ID
    return dict(status='APPLIED_REQUIRES_NATIVE_FASCIA_REVIEW',asset=ID,needle_button_pivot_label_actors_unchanged=True)
