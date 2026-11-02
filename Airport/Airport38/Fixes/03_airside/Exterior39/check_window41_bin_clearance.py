"""Read-only source proof of the raised bin leaves at authored open angles."""
import bpy,json,sys,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
F=Path(__file__).parent;ROOT=F.parents[5]
sys.path.insert(0,str(F));import window41 as M;import window40 as W
pm=json.loads((ROOT/'outputs/SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference']
report=dict(scope='Read-only original separate bin leaves and complete PSU vertices against frozenWindow41 geometry',passed=False)
try:
    rows=[q for q in pm['instances'] if q['asset'].startswith('SM_Plane_OverheadBinDoor10_') or (q['name'].startswith(('Passenger service unit ','PSU ')) and abs(q['location'][0])>1.)]
    ids=sorted(set(q['asset'] for q in rows))
    with bpy.data.libraries.load(str(ROOT/'outputs/SkywardAir/Revision18/Plane_Refined18.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols=dict(zip(ids,dst.collections))
    ids=['SM_AP_W41WindowWallL','SM_AP_W41WindowWallR','SM_AP_W41RackL','SM_AP_W41RackR']
    with bpy.data.libraries.load(str(F/'Window41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(ids)
    cols.update(zip(ids,dst.collections))
    for c in cols.values():bpy.context.scene.collection.children.link(c)
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def geom(c,filter_fn=lambda o:True):
        vs=[];fs=[];owners=[]
        for o in c.objects:
            if o.type!='MESH' or not filter_fn(o):continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();T=W._matrix(o);base=len(vs);vs.extend(T@v.co for v in me.vertices);fs.extend(tuple(base+i for i in p.vertices) for p in me.polygons);owners.extend([o.name]*len(me.polygons));ev.to_mesh_clear()
        return vs,fs,owners
    geometry={n:geom(c) for n,c in cols.items()};motions={q['actor']:q for q in pm['interactions'] if q['kind']=='movable'}
    report['actual_roof_spans']=[]
    fails=[];minskin=999;minimum_absx=999;sample_count=0;pairs=0
    for side,suffix in [(-1,'L'),(1,'R')]:
        cv,cf,co=geom(cols['SM_AP_W41WindowWall'+suffix],lambda o:o.name.startswith('Continuous acoustic ceiling shoulder09'))
        # Include the true adjacent central ceiling surface if its kit contains
        # it, rather than inventing a horizontal bounding plane.
        cv2,cf2,co2=geom(cols['SM_AP_W41WindowWall'+suffix],lambda o:'ceiling' in o.name.lower() and not o.name.startswith('Continuous acoustic ceiling shoulder09'))
        base=len(cv);cv+=cv2;cf+=[tuple(base+i for i in p) for p in cf2];co+=co2;tree=BVHTree.FromPolygons(cv,cf)
        span=[min(abs(p.x) for p in cv),max(abs(p.x) for p in cv)]
        report['actual_roof_spans'].append(dict(side=suffix,min_max_absx_m=span,objects=sorted(set(co)),all_kit_objects=[o.name for o in cols['SM_AP_W41WindowWall'+suffix].objects]))
        for row in [q for q in rows if q['location'][0]*side>0]:
            vv,ff,_=geometry[row['asset']];loc=Vector(row['location']);loc.z+=M.LIFT;loc.y=0
            steps=range(41) if 'OverheadBinDoor' in row['asset'] else range(1)
            motion=motions.get(row['name'],{}).get('motion',{});amount=motion.get('amount_degrees',0);axis=motion.get('axis','y').upper()
            for j in steps:
                fraction=j/40 if 'OverheadBinDoor' in row['asset'] else 0;rotation=Matrix.Rotation(math.radians(amount*fraction),4,axis);points=[rotation@p+loc for p in vv]
                minimum_absx=min(minimum_absx,min(abs(p.x) for p in points))
                gap=min(W.pressure_x(p.z)-abs(p.x) for p in points);minskin=min(minskin,gap);sample_count+=len(points)
                if gap<-.0001:fails.append(dict(actor=row['name'],fraction=fraction,kind='pressure skin',gap=gap,point=list(min(points,key=lambda p:W.pressure_x(p.z)-abs(p.x)))))
                hits=tree.overlap(BVHTree.FromPolygons(points,ff));pairs+=1
                if hits:fails.append(dict(actor=row['name'],fraction=fraction,kind='ceiling crossing',count=len(hits),owner=co[hits[0][0]]))
    assert minimum_absx>1.1,('Moving/attached vertices enter unchanged central ceiling strip',minimum_absx)
    report.update(passed=not fails,minimum_pressure_skin_clearance_m=minskin,minimum_absx_of_complete_assemblies_m=minimum_absx,unchanged_central_ceiling_strip_clearance_m=minimum_absx-1.1,vertex_samples=sample_count,ceiling_triangle_pairs=pairs,failures=fails[:100],failure_count=len(fails),actual_motion_axes_and_amounts={q['name']:motions[q['name']]['motion'] for q in rows if 'OverheadBinDoor' in q['asset']})
except Exception:report['error']=traceback.format_exc()
(F/'Window41_BinClearance.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='actual_motion_axes_and_amounts'}),flush=True)
