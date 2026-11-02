"""Small isolated W42 collar proof; actual W41 mechanisms unchanged."""
import bpy,sys,json,traceback,copy
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;ROOT=F.parents[5];R=F.parents[2]
sys.path[:0]=[str(F),str(R.parent/'SourceAssets')]
import airport_model as a
import window40 as W
import window41 as B
import window42 as M
report=dict(passed=False,passes=[])
try:
    ids=list(B.SWAPS.values())+['SM_AP_W40PressureWindows','SM_AP_W40ShadeHandleL','SM_AP_W40ShadeHandleR']
    with bpy.data.libraries.load(str(F/'Window41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols=dict(zip(ids,dst.collections));pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];psus=[q for q in pm['instances'] if q['name'].startswith(('Passenger service unit 01','Passenger service unit 02','PSU 01 ','PSU 02 '))]
    ids=sorted(set(q['asset'] for q in psus)|{'SM_Plane_WindowShadeSlat18_L','SM_Plane_WindowShadeSlat18_R'})
    with bpy.data.libraries.load(str(ROOT/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols.update(zip(ids,dst.collections))
    for c in cols.values():
        if c:bpy.context.scene.collection.children.link(c)
    result=M.build_units(SimpleNamespace(a=a))
    for n in M.SWAPS.values():bpy.context.scene.collection.children.link(bpy.data.collections[n])
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geo(c,offset=(0,0,0),filter_fn=lambda o:True):
        vv=[];ff=[];owners=[]
        for ob in c.objects:
            if ob.type!='MESH' or not filter_fn(ob):continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh();T=W._matrix(ob);base=len(vv);vv.extend(T@v.co+Vector(offset) for v in me.vertices);ff.extend(tuple(base+i for i in p.vertices) for p in me.polygons);owners.extend([ob.name]*len(me.polygons));ev.to_mesh_clear()
        return vv,ff,owners
    temp=SimpleNamespace(DATA=copy.deepcopy(pm));W.prepare_plane(temp,dict(aircraft38=dict(offset=[0,0,0])))
    rays=0;blocks=[];skin=999;selfpairs=[];crossings=[];poses=0
    for side,suffix in [(-1,'L'),(1,'R')]:
        c=bpy.data.collections['SM_AP_W42WindowWall'+suffix];pp,ff,owners=geo(c,filter_fn=lambda o:o.name.startswith('W42 continuous monotone'))
        skin=min(skin,min(W.pressure_x(p.z)-abs(p.x) for p in pp));tree=BVHTree.FromPolygons(pp,ff)
        selfpairs.extend((suffix,i,j) for i,j in tree.overlap(tree) if i<j and not set(ff[i])&set(ff[j]))
        vv=[];faces=[];own=[]
        items=[(c,(0,0,0)),(cols['SM_AP_W41Rack'+suffix],(0,0,0)),(bpy.data.collections['SM_AP_W42ShadeFrame'+suffix],(side*2.3,0,.92))]
        items.extend((cols[q['asset']],[q['location'][0],q['location'][1]-14.175,q['location'][2]+B.LIFT]) for q in psus if q['location'][0]*side>0)
        for cc,offset in items:
            v,f,o=geo(cc,offset,lambda ob:not any(mat and 'Glass' in mat.name for mat in ob.data.materials));base=len(vv);vv+=v;faces.extend(tuple(base+i for i in p) for p in f);own+=o
        opaque=BVHTree.FromPolygons(vv,faces)
        for x in (.6,1.2,1.8):
            for ye in (-.15,0,.15):
                for ze in (1.22,1.38,1.62):
                    eye=Vector((side*x,ye,ze))
                    for scale in (.98,.99):
                        for y,z,_ in W._loop(.70,1.,.16,1.46)[::8]:
                            y*=scale;z=1.46+(z-1.46)*scale;target=Vector((side*(W.pressure_x(z)-.005),y,z));d=target-eye;hit=opaque.ray_cast(eye,d.normalized(),d.length-.001);rays+=1
                            if hit[0] is not None:blocks.append(dict(side=suffix,owner=own[hit[2]],point=list(hit[0])))
        # The collar itself must clear full leaves throughout the existing21
        # actual W41 shade poses, not merely have a smooth visible outline.
        q=next(q for q in temp.DATA['interactions'] if q.get('window40') and (' L18' in q['actor'])==(side<0))
        gv,gf,go=geo(bpy.data.collections['SM_AP_W42ShadeFrame'+suffix],(side*2.3,0,.92));gb=len(pp);mechanical=BVHTree.FromPolygons(pp+gv,ff+[tuple(gb+i for i in p) for p in gf]);mechanical_owners=owners+go
        skin=min(skin,min(W.pressure_x(p.z)-abs(p.x) for p in gv))
        for part in q['roller_parts']:
            aid='SM_AP_W40ShadeHandle'+suffix if 'Handle' in part['actor'] else 'SM_Plane_WindowShadeSlat18_'+suffix;v,f,_=geo(cols[aid])
            for j in range(21):
                pos=Vector(W.shade_pose(part,j/20));pos.x+=side*B.SHADE_FIT;pos.y=0;leaf=BVHTree.FromPolygons([p+pos for p in v],f);hits=mechanical.overlap(leaf);poses+=1
                if hits:crossings.append(dict(side=suffix,part=part['actor'],progress=j/20,count=len(hits),owners=sorted(set(mechanical_owners[h[0]] for h in hits))))
    assert not selfpairs,selfpairs[:10]
    assert not blocks,blocks[:10]
    assert not crossings,crossings[:10]
    assert skin>.0015,skin
    report['passes']=[dict(check='Monotone collar actual geometry no disjoint-face self crossings',self_crossings=len(selfpairs),minimum_skin_clearance_m=skin),dict(check='Full98–99% aperture normal seated/standing eyes with actualPSUs',rays=rays,blocked=len(blocks)),dict(check='New collar versus retained actual shade parts throughout travel',pose_pairs=poses,triangle_crossings=len(crossings))]
    bpy.ops.wm.save_as_mainfile(filepath=str(F/'Window42_UnitKits.blend'));report.update(passed=True,assets=result)
except Exception:report['error']=traceback.format_exc()
(F/'Window42_Verification.json').write_text(json.dumps(report,indent=2));print('WINDOW42',report['passed'],report.get('error',''),flush=True)
