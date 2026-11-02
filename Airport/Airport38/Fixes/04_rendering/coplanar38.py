"""Cross-object world-plane overlap checks, independent of renderer and physics.

Scope: visible near-axis-aligned planar triangles of structural assets, in metres.
This detects same-facing overlaid visible surfaces. Opposite-facing shared solid
contacts, touching edges and positive depth separations are not depth conflicts.
It is a geometry acceptance check, never a substitute for native image review.
"""
import math
from collections import defaultdict


def _area(poly):
    return .5*sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))


def _cross(a,b):return a[0]*b[1]-a[1]*b[0]


def _clip(subject, clip):
    """Intersection of convex 2D polygons, including triangles and rectangles."""
    subject=list(subject);clip=list(clip)
    if _area(clip)<0:clip.reverse()
    for a,b in zip(clip,clip[1:]+clip[:1]):
        if not subject:return []
        out=[];prev=subject[-1]
        edge=(b[0]-a[0],b[1]-a[1])
        def signed(p):return _cross(edge,(p[0]-a[0],p[1]-a[1]))
        sp=signed(prev)
        for cur in subject:
            sc=signed(cur)
            if (sc>=-1e-9)!=(sp>=-1e-9):
                t=sp/(sp-sc)
                out.append((prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])))
            if sc>=-1e-9:out.append(cur)
            prev=cur;sp=sc
        subject=out
    return subject


def find_conflicts(faces, plane_tolerance=.00075, minimum_area=.002):
    """Input faces: actor,asset,part,normal,vertices (triangles/convex faces).

    Broad phase groups axis, normal sign and neighbouring depth bins. The narrow
    phase clips the actual polygons; AABB overlap alone cannot establish a fault.
    Returns one accumulated record per two parts AND physical plane/orientation,
    not one noisy row per triangle. Occlusion/solid burial is not inferred here.
    """
    buckets=defaultdict(list);hits={};eligible=0;tested=0
    for face in faces:
        normal=face['normal'];axis=max(range(3),key=lambda i:abs(normal[i]))
        if abs(normal[axis])<.9999:continue
        verts=face['vertices'];depth=sum(p[axis] for p in verts)/len(verts)
        if max(abs(p[axis]-depth) for p in verts)>plane_tolerance:continue
        axes=[i for i in range(3) if i!=axis]
        poly=[(p[axes[0]],p[axes[1]]) for p in verts]
        if abs(_area(poly))<1e-8:continue
        eligible+=1;sign=1 if normal[axis]>0 else -1;depth_bin=round(depth/plane_tolerance)
        lo=[min(p[j] for p in poly) for j in (0,1)];hi=[max(p[j] for p in poly) for j in (0,1)]
        own=(face.get('actor',''),face.get('asset',''),face['part'])
        for b in (depth_bin-1,depth_bin,depth_bin+1):
            for other in buckets[(axis,sign,b)]:
                if own==other['owner'] or abs(depth-other['depth'])>plane_tolerance:continue
                if any(min(hi[j],other['hi'][j])-max(lo[j],other['lo'][j])<=1e-8 for j in (0,1)):continue
                tested+=1;intersection=_clip(poly,other['poly']);area=abs(_area(intersection))
                if area<1e-8:continue
                pair=tuple(sorted((own,other['owner'])))
                # The same two solids may touch at a side plane AND an end
                # plane. Combining them under the first plane is misleading.
                key=(pair,axis,sign,round((depth+other['depth'])/(2*plane_tolerance)))
                world=[]
                for xy in intersection:
                    p=[0.,0.,0.];p[axis]=depth;p[axes[0]]=xy[0];p[axes[1]]=xy[1];world.append(p)
                lower=[min(p[j] for p in world) for j in range(3)]
                upper=[max(p[j] for p in world) for j in range(3)]
                centre=[sum(p[j] for p in world)/len(world) for j in range(3)]
                normal=[0,0,0];normal[axis]=sign
                item=hits.setdefault(key,dict(parts=[dict(actor=v[0],asset=v[1],part=v[2]) for v in pair],
                    axis='xyz'[axis],normal=normal,depth_m=depth,depth_range_m=[min(depth,other['depth']),max(depth,other['depth'])],
                    area_m2=0.,maximum_plane_distance_m=0.,overlap_world_min=lower,overlap_world_max=upper,
                    overlap_sample_points=[],candidate_exposure='UNCLASSIFIED: exact face overlap does not prove visible z-fighting'))
                item['area_m2']+=area
                item['maximum_plane_distance_m']=max(item['maximum_plane_distance_m'],abs(depth-other['depth']))
                item['depth_range_m'][0]=min(item['depth_range_m'][0],depth,other['depth'])
                item['depth_range_m'][1]=max(item['depth_range_m'][1],depth,other['depth'])
                item['overlap_world_min']=[min(item['overlap_world_min'][j],lower[j]) for j in range(3)]
                item['overlap_world_max']=[max(item['overlap_world_max'][j],upper[j]) for j in range(3)]
                if len(item['overlap_sample_points'])<12 and all(sum((p[j]-centre[j])**2 for j in range(3))>.0001 for p in item['overlap_sample_points']):
                    item['overlap_sample_points'].append(centre)
        buckets[(axis,sign,depth_bin)].append(dict(owner=own,depth=depth,poly=poly,lo=lo,hi=hi))
    conflicts=[v for v in hits.values() if v['area_m2']>=minimum_area]
    conflicts.sort(key=lambda v:-v['area_m2'])
    return dict(status='PASS' if not conflicts else 'FAIL',scope='active same-facing axis-planar structural face candidates across different parts; exposure not yet established',
        eligible_faces=eligible,narrow_phase_pairs=tested,plane_tolerance_m=plane_tolerance,
        minimum_area_m2=minimum_area,conflicts=conflicts,
        limits='Sealed interior contacts can be candidates; no visibility suppression applied. Does not prove non-planar/oblique clearance, lighting stability or every aircraft surface.')


def blender_faces(D, asset_predicate=None):
    """Extract effective visible active instances from final Blender layout.

    Call after ALL source builds, especially architecture. Uses evaluated meshes,
    instance placement/scale and each part transform. No scene mutations/saves.
    """
    import bpy
    from mathutils import Matrix,Vector
    structural=('Ceiling','Roof','Floor','Wall','Room','Envelope','Facade','Wayfinding')
    if asset_predicate is None:asset_predicate=lambda name:any(s in name for s in structural)
    dg=bpy.context.evaluated_depsgraph_get();result=[]
    for q in D['instances']:
        if not asset_predicate(q['asset']):continue
        col=bpy.data.collections.get(q['asset'])
        if col is None:raise RuntimeError('Missing active source collection '+q['asset'])
        instance=(Matrix.Translation(Vector(q['location'])) @
                  Matrix.Rotation(math.radians(q.get('rotation_degrees',0)),4,'Z') @
                  Matrix.Diagonal(Vector(list(q.get('scale',[1,1,1]))+[1])))
        for obj in col.all_objects:
            if obj.type!='MESH' or obj.hide_render:continue
            evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
            try:
                mesh.calc_loop_triangles();world=instance@obj.matrix_world
                normals=world.to_3x3().inverted().transposed()
                for tri in mesh.loop_triangles:
                    normal=(normals@tri.normal).normalized()
                    if max(abs(v) for v in normal)<.9999:continue
                    result.append(dict(actor=q['name'],asset=q['asset'],part=obj.name,
                        normal=list(normal),vertices=[list(world@mesh.vertices[i].co) for i in tri.vertices]))
            finally:evaluated.to_mesh_clear()
    return result


def audit_blender_layout(D, output=None):
    report=find_conflicts(blender_faces(D))
    if output:
        import json
        from pathlib import Path
        Path(output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def old_conflict_fixture(inventory):
    """Audited old cap/ceiling planar bounds, for regression-test reproduction.

    Bounds are a fixture of the four already-verified flat surfaces, NOT a
    general method of inferring face conflicts from arbitrary mesh AABBs.
    """
    selected={'SM_AP_Roof35':{'Weather-sealed roof cap35.002','Weather-sealed roof cap35.003'},
        'SM_AP_Room37_gate08foyer':{'Fitted acoustic room ceiling35.020'},
        'SM_AP_Room37_cafefoyer':{'Fitted acoustic room ceiling35.022'}}
    result=[]
    for asset in inventory['assets']:
        if asset['asset'] not in selected:continue
        for p in asset['parts']:
            if p['name'] not in selected[asset['asset']]:continue
            lo,hi=p['min'],p['max'];z=lo[2]
            result.append(dict(actor=asset['asset'],asset=asset['asset'],part=p['name'],normal=[0,0,-1],
                vertices=[[lo[0],lo[1],z],[lo[0],hi[1],z],[hi[0],hi[1],z],[hi[0],lo[1],z]]))
    if len(result)!=4:raise ValueError('Expected exact four audited old plane fixtures')
    return result
