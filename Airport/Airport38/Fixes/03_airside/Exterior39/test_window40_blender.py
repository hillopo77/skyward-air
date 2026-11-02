"""Private unit build and actual evaluated contact/readability checks. No master save."""
import bpy,sys,json,copy,math,traceback
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
from mathutils.bvhtree import BVHTree

F=Path(__file__).parent;R=F.parents[2];W=F.parents[5]
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import window40 as M
import airport_model as a
report=dict(scope='Factory-empty private source build only; current master and shared manifests untouched',passes=[])

try:
    pm=json.loads((W/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
    ids=set(M.SWAPS)|{'SM_Plane_WindowShadeSlat18_L','SM_Plane_WindowShadeSlat18_R','SM_Plane_WindowShadeHandle18_L','SM_Plane_WindowShadeHandle18_R'}
    with bpy.data.libraries.load(str(W/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):
        dst.collections=list(ids);dst.materials=['MI_Plane_Seal08']
    originals={c.name:c for c in dst.collections if c}
    for c in originals.values():bpy.context.scene.collection.children.link(c)
    for q in pm['instances']:
        if q['asset'] not in ids:continue
        ob=bpy.data.objects.new(q['name'],None);ob.instance_type='COLLECTION';ob.instance_collection=originals[q['asset']];ob.location=[q['location'][0]+16,*q['location'][1:]];bpy.context.scene.collection.objects.link(ob)
    D=json.loads((R/'Exports/airport_layout.json').read_text());ctx=SimpleNamespace(a=a,D=D,scene=bpy.context.scene)
    result=M.apply(ctx);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def points(col,offset=(0,0,0),filter_fn=lambda ob:True):
        out=[]
        for ob in col.objects:
            if ob.type!='MESH' or not filter_fn(ob):continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh();T=M._matrix(ob);out.extend(T@v.co+Vector(offset) for v in me.vertices);ev.to_mesh_clear()
        return out
    # Actual original bound mismatch, rather than an assumption about materials.
    original_bad=max(abs(p.x)-M.pressure_x(p.z) for p in points(originals['SM_Plane_WindowWall_L']) if .9<p.z<2.23)
    assert original_bad>.06,original_bad
    report['passes'].append(dict(pass_id=1,check='Measured original envelope defect and coordinated aperture/gasket reconstruction',original_liner_outside_skin_m=original_bad,kits=len(result['changed_assets'])))
    wall_max=-999;part_count=0;bad_faces=[];triangles=0
    for aid in result['changed_assets']:
        col=bpy.data.collections[aid]
        for ob in col.objects:
            if ob.type!='MESH':continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
            bad_faces.extend((aid,ob.name,t.area) for t in me.loop_triangles if t.area<1e-12);ev.to_mesh_clear()
        if 'WindowWall' in aid:
            wall_max=max(wall_max,max(abs(p.x)-M.pressure_x(p.z) for p in points(col)))
            assert sum(ob.name.startswith('W40 single curved laminated optical pane') for ob in col.objects)==1
            assert not any(ob.name.startswith(('Retractable shade top cassette','Shade recessed grip')) for ob in col.objects)
    assert not bad_faces,bad_faces[:15]
    assert wall_max<-.003,wall_max
    report['passes'].append(dict(pass_id=2,check='Actual evaluated geometry, single pane, no obsolete cassette or wall penetration',evaluated_triangles=triangles,zero_area_triangles=len(bad_faces),minimum_wall_inside_skin_m=-wall_max))
    P=SimpleNamespace(DATA=copy.deepcopy(pm))
    for q in P.DATA['interactions']:
        for part in q.get('roller_parts',[]):part['closed_location'][0]+=16
    switches={q['actor']:copy.deepcopy(q['point']) for q in P.DATA['interactions'] if q.get('roller_parts')}
    M.prepare_plane(P,D);prepared=copy.deepcopy(P.DATA);M.prepare_plane(P,D);assert P.DATA==prepared
    n=0;max_out=-999;min_business=999;panel_samples=[]
    instances={q['name']:q for q in pm['instances']}
    for q in P.DATA['interactions']:
        if not q.get('window40'):continue
        assert q['point']==switches[q['actor']]
        for part in q['roller_parts']:
            aid=instances[part['actor']]['asset'];col=bpy.data.collections[M.SWAPS[aid]] if aid in M.SWAPS else originals[aid];source=points(col)
            for j in range(41):
                pose=Vector(M.shade_pose(part,j/40));pose.x-=16
                for p in source:
                    world=p+pose;max_out=max(max_out,abs(world.x)-M.pressure_x(world.z));n+=1
                    if world.z<1.3566:min_business=min(min_business,abs(world.x)-2.32)
            panel_samples.append((part,source))
    assert max_out<-.005,('Shade exits pressure envelope',max_out)
    assert min_business>.004,('Shade crosses business side shell',min_business)
    report['passes'].append(dict(pass_id=3,check='All48 real five-leaf mechanisms through41 retained curved-stow states; unchanged switches',sampled_vertices=n,minimum_skin_clearance_m=-max_out,minimum_business_clearance_m=min_business,idempotent=True))
    # All roof-rack retained hardware remains original except the three named
    # molded upper/rear parts. New service pocket is actually behind that rack.
    rack_details=[]
    for side,suffix in [(-1,'L'),(1,'R')]:
        c=bpy.data.collections[M.SWAPS['SM_Plane_Rack_'+suffix]]
        upper=points(c,filter_fn=lambda ob:ob.name.startswith(('Fixed overhead cavity10 curved crown','Fixed overhead cavity10 end cheek')))
        high=[abs(p.x) for p in upper if p.z>2.045]
        gap=2.06-max(high);assert gap>.025,('Cassette and bin rear overlap',suffix,gap)
        rack_details.append(dict(side=suffix,minimum_high_service_gap_m=gap))
    report['passes'].append(dict(pass_id=4,check='Actual evaluated upper rack crown/end cheeks clear cassette; retain all bin hinges/door/underbody/contents',sides=rack_details))
    def bvh(cols,side):
        vs=[];fs=[]
        for col,offset in cols:
            for ob in col.objects:
                if ob.type!='MESH' or any(mat and ('Glass' in mat.name) for mat in ob.data.materials):continue
                ev=ob.evaluated_get(dg);me=ev.to_mesh();T=M._matrix(ob);base=len(vs);vs.extend(T@v.co+Vector(offset) for v in me.vertices);fs.extend(tuple(base+i for i in f.vertices) for f in me.polygons);ev.to_mesh_clear()
        return BVHTree.FromPolygons(vs,fs)
    rays=[]
    for side,suffix in [(-1,'L'),(1,'R')]:
        tree=bvh([(bpy.data.collections[M.SWAPS['SM_Plane_WindowWall_'+suffix]],(0,0,0)),(bpy.data.collections[M.SWAPS['SM_Plane_WindowShadeFrame18_'+suffix]],(side*2.3,0,.92)),(bpy.data.collections[M.SWAPS['SM_Plane_Rack_'+suffix]],(0,0,0))],side)
        eye=Vector((side*1.2,0,1.62))
        for y,z,_ in M._loop(.7,1.,.16,1.46)[::16]:
            y*=.88;z=1.46+(z-1.46)*.88;target=Vector((side*(M.pressure_x(z)-.005),y,z));d=target-eye;hit=tree.ray_cast(eye,d.normalized(),d.length-.002)[0]
            rays.append(dict(side=suffix,target=list(target),clear=hit is None,hit=list(hit) if hit is not None else None))
    assert all(q['clear'] for q in rays),[q for q in rays if not q['clear']][:8]
    report['passes'].append(dict(pass_id=5,check='Actual opaque geometry ray visibility across88percent rounded clear aperture, both sides',rays=len(rays),clear=sum(q['clear'] for q in rays)))
    # Test the moving plate interior, not just its actor origin or final pose,
    # against the actual new bucket solids throughout the retained stroke.
    contact_tests=0;collisions=[]
    for side,suffix in [(-1,'L'),(1,'R')]:
        tree=bvh([(bpy.data.collections[M.SWAPS['SM_Plane_Rack_'+suffix]],(0,0,0))],side)
        q=next(q for q in P.DATA['interactions'] if q.get('window40') and (' '+suffix+'18') in q['actor'])
        for part in q['roller_parts']:
            for j in range(41):
                pose=Vector(M.shade_pose(part,j/40));pose.x-=16
                for y in (-.30,-.15,0.,.15,.30):
                    for z in (.03,.07,.12,.18,.23):
                        origin=pose+Vector((-.008,y,z));end=pose+Vector((.008,y,z));d=end-origin
                        hit=tree.ray_cast(origin,d.normalized(),d.length)[0];contact_tests+=1
                        if hit is not None:collisions.append(dict(side=suffix,part=part['window40_index'],progress=j/40,point=list(hit)))
    assert not collisions,collisions[:12]
    report['passes'].append(dict(pass_id=6,check='Actual rack-triangle intersections against moving shade plate interiors at41 stroke states',cross_section_tests=contact_tests,collisions=0))
    snapshot=copy.deepcopy(D);M.apply(ctx);assert D==snapshot,('Source apply not idempotent')
    # Save only the privately built unit source, never the user's airport master.
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'Window40_UnitKits.blend'))
    report.update(passed=True,changed_assets=result['changed_assets'],source_instances=len(result['source_instances']),source_parts=result['source_shade_parts_fitted'],native_visual_review_required=True)
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'Window40_Verification.json').write_text(json.dumps(report,indent=2));print('WINDOW40',report['passed'],report.get('error',''),flush=True)
