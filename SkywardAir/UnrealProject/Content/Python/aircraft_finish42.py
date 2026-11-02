"""Quiet readable PSU faces and genuinely draped soft-luggage handles."""
import math,json
from pathlib import Path
F=Path(__file__).parent
SWAPS={'SM_Plane_PSUCarrier12':'SM_AP_A42PSUCarrier','SM_Plane_Cargo15_ExpeditionDuffel':'SM_AP_A42ExpeditionDuffel','SM_Plane_Cargo15_Weekender':'SM_AP_A42Weekender'}
def build_units(ctx):
    import bpy,bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    import window40 as W
    a=ctx.a;a.mat('A42WarmSatin','C7C3B7',.56,.04);report={}
    for old,new in SWAPS.items():
        c=bpy.data.collections.new(new);c.use_fake_user=True;c['aircraft_finish42_asset_id']=new
        for ob in bpy.data.collections[old].objects:
            q=ob.copy();q.data=ob.data.copy();c.objects.link(q)
        for o in c.objects:
            if o.type!='MESH' or not o.data.vertices:continue
            span=[max(v.co[k] for v in o.data.vertices)-min(v.co[k] for v in o.data.vertices) for k in range(3)]
            for mod in o.modifiers:
                if mod.type=='BEVEL':mod.width=min(mod.width,min(span)*.18);mod.use_clamp_overlap=True
        if 'PSUCarrier' in old:
            changed=[];clamps=[]
            for o in c.objects:
                if o.type=='MESH' and o.data.vertices:
                    span=[max(v.co[k] for v in o.data.vertices)-min(v.co[k] for v in o.data.vertices) for k in range(3)]
                    for mod in o.modifiers:
                        if mod.type=='BEVEL':
                            width=min(mod.width,min(span)*.18)
                            if width<mod.width:clamps.append(dict(part=o.name,old=mod.width,new=width))
                            mod.width=width;mod.use_clamp_overlap=True
                if o.type=='MESH' and o.name.startswith(('PSU continuous formed perimeter','PSU bored gasper face','PSU bored optic face','PSU through key aperture')):
                    o.data.materials.clear();o.data.materials.append(a.MATS['A42WarmSatin']);changed.append(o.name)
            assert len(changed)==5,changed
            report[new]=dict(warm_satin_faces=changed,thin_plenum_edge_rolls=clamps,dimensions_pivots_recesses_nozzles_unchanged=True)
        else:
            body=next(o for o in c.objects if o.name.startswith('Tailored canvas body with compressed end folds15'));T=W._matrix(body);pp=[T@v.co for v in body.data.vertices];tree=BVHTree.FromPolygons(pp,[tuple(p.vertices) for p in body.data.polygons]);length=max(p.y for p in pp)-min(p.y for p in pp);width=max(p.x for p in pp)-min(p.x for p in pp);height=max(p.z for p in pp)/.96;changed=[];gaps=[];zipper=[]
            for o in c.objects:
                if o.name.startswith(('Zipper tape seated in top seam15','Duffel interlocking zipper tooth15')):
                    tape=o.name.startswith('Zipper tape');T=W._matrix(o);inv=T.inverted();base=height*(.965 if tape else .973)
                    for v in o.data.vertices:
                        p=T@v.co;hit=tree.ray_cast(Vector((p.x,p.y,1)),Vector((0,0,-1)),2)[0];assert hit is not None
                        p.z=hit.z+(.0025 if tape else .0047)+(p.z-base);v.co=inv@p
                    o.data.update();zipper.append(o.name)
                if not o.name.startswith('Flexible flat carry-loop webbing15'):continue
                T=W._matrix(o);inv=T.inverted();pts=[T@v.co for v in o.data.vertices];cx=sum(p.x for p in pts)/len(pts);side=1 if cx>0 else -1
                for v in o.data.vertices:
                    p=T@v.co;t=max(0,min(1,(p.y+length*.17)/(length*.34)));s=math.sin(math.pi*t);p.x+=side*width*.22*s**.8
                    hit=tree.ray_cast(Vector((p.x,p.y,1.)),Vector((0,0,-1)),2)[0];assert hit is not None,(old,list(p))
                    end=min(t,1-t);u=max(0,min(1,end/.12));u=u*u*(3-2*u);middle=.0025+.004*(1-u);depth=-.002 if v.index%4 in (0,1) else .002;p.z=hit.z+middle+depth;gaps.append(middle+depth);v.co=inv@p
                o.data.update();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();changed.append(o.name)
            assert len(changed)==2,changed
            report[new]=dict(draped_handles=changed,canvas_fitted_existing_zipper_parts=len(zipper),minimum_canvas_gap_m=min(gaps),maximum_canvas_gap_m=max(gaps),unchanged_body_and_ground_contacts=True)
        a.ASSETS[new]=dict(collection=c,collision='complex')
    return report

def apply(ctx):
    import bpy
    ids=tuple(SWAPS.values());existing={n:next((c for c in bpy.data.collections if c.get('aircraft_finish42_asset_id')==n),None) for n in ids};requested=tuple(n for n in ids if not existing[n])
    if requested:
        with bpy.data.libraries.load(str(F/'AircraftFinish42_UnitKits.blend'),link=False) as (src,dst):
            assert set(ids)<=set(src.collections);dst.collections=list(requested)
        loaded=dict(zip(requested,dst.collections))
    else:loaded={}
    pm=json.loads((ctx.R.parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];targets={q['name']:SWAPS[q['asset']] for q in pm['instances'] if q['asset'] in SWAPS}
    for new in ids:
        c=existing[new] or loaded[new];c.use_fake_user=True;ctx.a.ASSETS[new]=dict(collection=c,collision='complex')
        for o in c.objects:
            for m in o.data.materials:
                if m:ctx.a.MATS[m.name]=m
    for o in ctx.scene.objects:
        if o.name in targets and o.instance_type=='COLLECTION':o.instance_collection=ctx.a.ASSETS[targets[o.name]]['collection']
    for q in ctx.D['instances']:
        if q['asset'] in SWAPS:q['asset']=SWAPS[q['asset']]
    result=dict(version=1,assets=list(ids),targeted_instances=len(targets),palette_and_draped_handles_only=True);ctx.D.setdefault('repair38',{})['aircraft_finish42']=result;return result

def prepare_plane(P,D):
    carriers=set()
    for q in P.DATA['instances']:
        if q['asset'] in SWAPS:q['asset']=SWAPS[q['asset']]
        if q['asset']=='SM_AP_A42PSUCarrier':carriers.add(q['name'])
    # The satin carrier no longer has the former emissive optic-face material
    # slot. Reading-light controls already own a separate visible indicator
    # and practical light; retain both and leave the neutral housing neutral.
    retired={'MI_Plane_DetailOff12','MI_Plane_DetailWarm12'}
    for item in P.DATA.get('interactions',[]):
        if item.get('kind')!='control':continue
        item['targets']=[target for target in item.get('targets',[]) if not(target.get('actor') in carriers and set(target.get('materials',[]))==retired)]
    P.DATA['aircraft_finish42_prepared']=1

def apply_native(ctx):
    pm=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];targets={q['name']:SWAPS[q['asset']] for q in pm['instances'] if q['asset'] in SWAPS};changed=[]
    for actor in ctx.EA.get_all_level_actors():
        key=next((str(t)[8:] for t in actor.tags if str(t).startswith('Skyward:')),None)
        if key not in targets:continue
        c=actor.get_component_by_class(ctx.u.StaticMeshComponent);mesh=ctx.mesh(targets[key]);c.set_static_mesh(mesh)
        for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
        changed.append(key)
    assert len(changed)==len(targets),(len(changed),len(targets));return dict(status='APPLIED_REQUIRES_NATIVE_PALETTE_HANDLE_REVIEW',swapped=changed,actor_contacts_pivots_and_interactions_unchanged=True)
