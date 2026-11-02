"""Actual full-pane clearances; private unit source only, never shared master."""
import bpy,sys,json,math,copy,traceback
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;R=F.parents[2];ROOT=F.parents[5]
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import window40 as W
import window41 as M
report=dict(scope='Private Window40-derived unit source, no shared master/native writes',passes=[])
try:
    ids=list(M.SWAPS)+['SM_AP_W40PressureWindows']
    with bpy.data.libraries.load(str(F/'Window40_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols=dict(zip(ids,dst.collections))
    pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
    psus=[q for q in pm['instances'] if q['name'].startswith(('Passenger service unit 01','Passenger service unit 02','PSU 01 ','PSU 02 '))]
    extra=set(q['asset'] for q in psus)|{'SM_Plane_WindowShadeSlat18_L','SM_Plane_WindowShadeSlat18_R','SM_Plane_WindowShadeHandle18_L','SM_Plane_WindowShadeHandle18_R'}
    with bpy.data.libraries.load(str(ROOT/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=list(extra)
    originals={c.name:c for c in dst.collections if c}
    # The proper recessed moving handles are the frozen Window40 kits.
    with bpy.data.libraries.load(str(F/'Window40_UnitKits.blend'),link=False) as (src,dst):dst.collections=['SM_AP_W40ShadeHandleL','SM_AP_W40ShadeHandleR']
    handles={c.name:c for c in dst.collections if c}
    for c in list(cols.values())+list(originals.values())+list(handles.values()):bpy.context.scene.collection.children.link(c)
    result=M.build_units(SimpleNamespace(a=a));
    for aid in M.SWAPS.values():bpy.context.scene.collection.children.link(bpy.data.collections[aid])
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geometry(col,offset=(0,0,0),filter_fn=lambda o:True):
        vs=[];fs=[];owners=[]
        for ob in col.objects:
            if ob.type!='MESH' or not filter_fn(ob):continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh();T=W._matrix(ob);base=len(vs);vs.extend(T@v.co+Vector(offset) for v in me.vertices);fs.extend(tuple(base+i for i in p.vertices) for p in me.polygons);owners.extend([ob.name]*len(me.polygons));ev.to_mesh_clear()
        return vs,fs,owners
    zero=[];faces=0;skin=-999
    for aid in M.SWAPS.values():
        for ob in bpy.data.collections[aid].objects:
            ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();faces+=len(me.loop_triangles);zero.extend((aid,ob.name,t.area) for t in me.loop_triangles if t.area<1e-12);ev.to_mesh_clear()
        if 'ShadeFrame' not in aid:
            pp,_,_=geometry(bpy.data.collections[aid]);skin=max(skin,max(abs(p.x)-W.pressure_x(p.z) for p in pp))
    assert not zero,zero[:10]
    assert skin<-.003,skin
    report['passes'].append(dict(pass_id=1,check='Every evaluated bucket/liner/cove vertex inside actual pressure skin; no degenerate geometry',triangles=faces,zero_area=len(zero),minimum_inside_skin_m=-skin))
    rays=[];blocks=[]
    for side,suffix in [(-1,'L'),(1,'R')]:
        allv=[];allf=[];own=[]
        items=[(bpy.data.collections['SM_AP_W41WindowWall'+suffix],(0,0,0)),(bpy.data.collections['SM_AP_W41Rack'+suffix],(0,0,0)),(bpy.data.collections['SM_AP_W41ShadeFrame'+suffix],(side*2.3,0,.92))]
        for q in psus:
            if q['location'][0]*side>0:items.append((originals[q['asset']],[q['location'][0],q['location'][1]-14.175,q['location'][2]+M.LIFT]))
        for col,offset in items:
            vv,ff,oo=geometry(col,offset,lambda ob:not any(mat and 'Glass' in mat.name for mat in ob.data.materials));base=len(allv);allv.extend(vv);allf.extend(tuple(base+i for i in p) for p in ff);own.extend(oo)
        tree=BVHTree.FromPolygons(allv,allf)
        for x in (.6,1.2,1.8):
            for y_eye in (-.15,0.,.15):
                for z_eye in (1.22,1.38,1.62):
                    eye=Vector((side*x,y_eye,z_eye))
                    for scale in (.98,.99):
                        for y,z,_ in W._loop(.70,1.,.16,1.46)[::8]:
                            y*=scale;z=1.46+(z-1.46)*scale;target=Vector((side*(W.pressure_x(z)-.005),y,z));d=target-eye;hit=tree.ray_cast(eye,d.normalized(),d.length-.001)
                            row=dict(side=suffix,eye=list(eye),target=list(target),scale=scale,clear=hit[0] is None)
                            if hit[0] is not None:row.update(hit=list(hit[0]),owner=own[hit[2]]);blocks.append(row)
                            rays.append(row)
    assert not blocks,(len(blocks),len(rays),blocks[:15])
    report['passes'].append(dict(pass_id=2,check='Full98and99percent clear-aperture perimeter rays across seated/standing normal eyes; includes actual raised PSU parts',rays=len(rays),clear=len(rays),blocked=0,eye_heights=[1.22,1.38,1.62]))
    # Root/controller pivots/deltas move with the complete side fixtures exactly
    # once. CentralPSUs, ground validation approaches and all rotations stay.
    D=json.loads((R/'Exports/airport_layout.json').read_text());D.setdefault('repair38',{})['window41']=dict(moving_actor_names=sorted(M.moving_names(pm)))
    P=SimpleNamespace(DATA=copy.deepcopy(pm));off=D['aircraft38']['offset']
    for q in P.DATA['instances']:q['location']=[p+d for p,d in zip(q['location'],off)]
    for q in P.DATA['interactions']:
        for key in ('point','location'):
            if key in q:q[key]=[p+d for p,d in zip(q[key],off)]
        for p in q.get('roller_parts',[]):p['closed_location']=[v+d for v,d in zip(p['closed_location'],off)]
    for q in P.DATA['lights']:q['location']=[p+d for p,d in zip(q['location'],off)]
    W.prepare_plane(P,D);before=copy.deepcopy(P.DATA);M.prepare_plane(P,D);snapshot=copy.deepcopy(P.DATA);M.prepare_plane(P,D);assert snapshot==P.DATA
    changed=M.moving_names(pm);old={q['name']:q for q in before['instances']};new={q['name']:q for q in P.DATA['instances']}
    for n in old:
        assert abs(new[n]['location'][2]-old[n]['location'][2]-(M.LIFT if n in changed else 0))<1e-7,n
        assert new[n]['rotation']==old[n]['rotation'] and new[n]['scale']==old[n]['scale']
    approaches_before={q['actor']:q.get('validation_approach') for q in before['interactions']}
    assert all(q.get('validation_approach')==approaches_before[q['actor']] for q in P.DATA['interactions'])
    seats=[q['location'] for q in P.DATA['interactions'] if q['kind']=='seat'];reach=[]
    for q in P.DATA['interactions']:
        if q['actor'] in changed and q['kind']=='control':reach.append(min(math.dist(q['point'],p) for p in seats))
    assert max(reach)<1.2,max(reach)
    report['passes'].append(dict(pass_id=3,check='Complete fixture/pivot data lift once, original movement deltas and standing approaches retained',moving_actor_count=len(changed),maximum_nearest_seated_control_reach_m=max(reach),idempotent=True))
    # The original retained curve is parallel-fitted8mm to give actual1mm C-lip
    # clearance. Full moving geometry stays inside skin and behind the glass.
    pane_gap=999;body_gap=999;skin_gap=999;count=0
    sourceinst={q['name']:q for q in pm['instances']}
    for q in P.DATA['interactions']:
        if not q.get('window41'):continue
        for part in q['roller_parts']:
            aid=sourceinst[part['actor']]['asset'];suffix='L' if aid.endswith('_L') else 'R';col=handles['SM_AP_W40ShadeHandle'+suffix] if 'Handle' in aid else originals[aid];pp,_,_=geometry(col)
            for j in range(21):
                pose=Vector(W.shade_pose(part,j/20));pose.x-=16;pose.x+=part['window40_side']*M.SHADE_FIT
                for p in pp:
                    p=p+pose;gap=W.pressure_x(p.z)-abs(p.x);skin_gap=min(skin_gap,gap);pane_gap=min(pane_gap,gap-.006);count+=1
                    if p.z<1.3566:body_gap=min(body_gap,abs(p.x)-2.32)
    assert skin_gap>.008 and pane_gap>.002 and body_gap>.012,(skin_gap,pane_gap,body_gap)
    report['passes'].append(dict(pass_id=4,check='All48 retained shade curves preserve pressure/glass/business clearance after8mm fit',samples=count,minimum_skin_gap_m=skin_gap,minimum_glass_gap_m=pane_gap,minimum_business_gap_m=body_gap))
    # Exact triangle contacts on the newly modeled mechanics, not only point
    # clearance to skin. Both sides and every distinct moving leaf are tested.
    contacts=[];pair_count=0;cove_pairs=[]
    for side,suffix in [(-1,'L'),(1,'R')]:
        vv,ff,owners=geometry(bpy.data.collections['SM_AP_W41ShadeFrame'+suffix],(side*2.3,0,.92),lambda o:o.name.startswith(('W41 captive guide','W41 thin formed')))
        guide=BVHTree.FromPolygons(vv,ff)
        q=next(q for q in P.DATA['interactions'] if q.get('window41') and q['roller_parts'][0]['window40_side']==side)
        for part in q['roller_parts']:
            aid=sourceinst[part['actor']]['asset'];col=handles['SM_AP_W40ShadeHandle'+suffix] if 'Handle' in aid else originals[aid];pp,pf,_=geometry(col)
            for j in range(21):
                pose=Vector(W.shade_pose(part,j/20));pose.x-=16;pose.x+=side*M.SHADE_FIT
                moving=BVHTree.FromPolygons([p+pose for p in pp],pf);hits=guide.overlap(moving);pair_count+=1
                if hits:contacts.append(dict(side=suffix,part=part['actor'],progress=j/20,count=len(hits),owner=owners[hits[0][0]]))
        vv,ff,_=geometry(bpy.data.collections['SM_AP_W41WindowWall'+suffix],filter_fn=lambda o:o.name.startswith('Continuous acoustic ceiling shoulder09'))
        rr,rf,_=geometry(bpy.data.collections['SM_AP_W41Rack'+suffix])
        hits=BVHTree.FromPolygons(vv,ff).overlap(BVHTree.FromPolygons(rr,rf))
        if hits:cove_pairs.append(dict(side=suffix,count=len(hits)))
    assert not contacts,contacts[:12]
    assert not cove_pairs,cove_pairs
    report['passes'].append(dict(pass_id=5,check='Actual moving leaf triangles clear new captive guides/corner shields; raised rack clear formed ceiling cove',mechanism_pose_pairs=pair_count,triangle_crossings=0,cove_rack_crossings=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'Window41_UnitKits.blend'));report.update(passed=True,assets=list(M.SWAPS.values()))
except Exception:report.update(passed=False,error=traceback.format_exc())
(F/'Window41_Verification.json').write_text(json.dumps(report,indent=2));print('WINDOW41',report['passed'],report.get('error',''),flush=True)
