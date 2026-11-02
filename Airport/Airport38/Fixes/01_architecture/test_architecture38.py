"""Run with ordinary Python for plan assertions, or factory-empty Blender for mesh QA.

blender --background --factory-startup --python test_architecture38.py
No shared file is opened, saved or modified. Art-detail copying is exercised by
root's saved-master build, because this deliberately empty test has no old assets.
"""
import copy,json,sys,math
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
AIRPORT=HERE.parents[2]
sys.path.insert(0,str(HERE))
import architecture38 as mod


class Context:
    def __init__(self,D,a=None):
        self.D=D;self.before=copy.deepcopy(D);self.a=a
        self.R=AIRPORT/'Airport38';self.A=AIRPORT;self.scene=None
    def require(self,name):return next(q for q in self.D['instances'] if q['name']==name)
    def remove(self,name):
        self.D['instances']=[q for q in self.D['instances'] if q['name']!=name]
        self.D['labels']=[q for q in self.D['labels'] if q.get('parent')!=name]
        self.D['interactions']=[q for q in self.D['interactions'] if q.get('object')!=name and q.get('parent')!=name]
    def move(self,name,location,rotation=None,scale=None):
        q=self.require(name);q['location']=location
        if rotation is not None:q['rotation_degrees']=rotation
        if scale is not None:q['scale']=scale
    def add(self,asset,name,location,rotation=0,scale=None,collision=True,**extra):
        self.D['instances'].append(dict(asset=asset,name=name,location=location,rotation_degrees=rotation,
                                      scale=scale or [1,1,1],stage=10,collision=collision,**extra))
    def new_collection(self,name,collision='complex'):
        import bpy
        c=bpy.data.collections.new('SM_AP_'+name);self.a.ACTIVE=c
        self.a.ASSETS[c.name]=dict(collection=c,collision=collision)
        bpy.context.scene.collection.children.link(c)
        return c


def trace_panels(D,p,q):
    """Analytic perpendicular wall trace through final panels, excluding furnishings."""
    hits=[]
    for s in mod.wall_segments(D):
        fixed=1 if s['axis']=='x' else 0; along=1-fixed
        den=q[fixed]-p[fixed]
        if abs(den)<1e-9:continue
        t=(s['k']-p[fixed])/den
        if not 0<=t<=1:continue
        c=p[along]+t*(q[along]-p[along]);z=p[2]+t*(q[2]-p[2])
        if not s['l']<=c<=s['h']:continue
        panels,glass=mod.wall_panels(D,s)
        if any(l-1e-6<=c<=h+1e-6 and z0-1e-6<=z<=z1+1e-6 for l,h,z0,z1 in panels+glass):
            hits.append(s)
    return hits


def run():
    D=json.loads((AIRPORT/'Clarity37/Exports/airport_layout.json').read_text())
    c=Context(D);mod.plan(c)
    D['service_openings38']=[dict(axis='y',k=-26,centre=y,width=1.45,z0=.55,z1=1.95) for y in (-13,-16)]
    result=mod.validate_plan(D)
    probes=[]
    for pr in D['repair38']['perimeter_probes']:
        hit=bool(trace_panels(D,pr['start'],pr['end']))
        assert hit==(pr['expected']=='block'),(pr,hit)
        probes.append(dict(id=pr['id'],passed=True,hit=hit))
    for z in D['zones']:
        assert z['rect'][0]<z['rect'][1] and z['rect'][2]<z['rect'][3]
    # Sampling full service opening profiles detects old hidden wall/backing errors
    # in the authored layer. Root repeats physical sweeps against the native scene.
    for y in (-13,-16):
        for yy in (y-.60,y,y+.60):
            for zz in (.7,1.2,1.8):
                assert not trace_panels(D,[-26.4,yy,zz],[-25.6,yy,zz]),('Feed blocked',yy,zz)
    assert not any(mod._legacy_remove(q) for q in D['instances'])
    source_test=False;counts={}
    try:import bpy
    except ImportError:bpy=None
    if bpy:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        sys.path.insert(0,str(AIRPORT/'SourceAssets'))
        import airport_model as a
        c.a=a;c.scene=bpy.context.scene;mod.build(c)
        from mathutils import Vector
        from mathutils.bvhtree import BVHTree
        # Evaluate each solid to detect degenerate topology and create independent BVHs.
        deps=bpy.context.evaluated_depsgraph_get();trees=[];mesh_objects=0
        for rec in a.ASSETS.values():
            collection=rec['collection'];nv=nf=0
            for ob in collection.objects:
                if ob.type!='MESH':continue
                eo=ob.evaluated_get(deps);me=eo.to_mesh();nv+=len(me.vertices);nf+=len(me.polygons)
                assert all(math.isfinite(v) for vv in me.vertices for v in vv.co)
                assert all(p.area>1e-12 for p in me.polygons),('Zero area face',collection.name,ob.name)
                if rec['collision']=='complex' and len(me.polygons):
                    vv=[ob.matrix_world@v.co for v in me.vertices]
                    trees.append((collection.name,BVHTree.FromPolygons(vv,[tuple(p.vertices) for p in me.polygons],all_triangles=False)))
                eo.to_mesh_clear();mesh_objects+=1
            counts[collection.name]=dict(vertices=nv,faces=nf,objects=len(collection.objects))
        # Physical source ray probes, independent of plan math.
        for pr in D['repair38']['perimeter_probes']:
            p=Vector(pr['start']);delta=Vector(pr['end'])-p;distance=delta.length;direction=delta.normalized()
            hit=any(t.ray_cast(p,direction,distance)[0] is not None for _,t in trees)
            assert hit==(pr['expected']=='block'),('Mesh source ray',pr['id'],hit)
        # Run the SAME cross-part structural overlap checker used by root. This
        # catches interfaces that a topology or wall-ray test cannot establish.
        sys.path.insert(0,str(HERE.parent/'04_rendering'))
        import coplanar38
        eligible=lambda name:name in a.ASSETS and any(s in name for s in ('Floor','Ceiling','Roof','Wall','Wayfinding','Canopy'))
        overlap=coplanar38.find_conflicts(coplanar38.blender_faces(D,eligible))
        (HERE/'coplanarity_test_result.json').write_text(json.dumps(overlap,indent=2))
        assert not overlap['conflicts'],('New structural overlap candidates',len(overlap['conflicts']))
        source_test=True
        counts['mesh_object_count']=mesh_objects
    output=dict(status='PASS',validation='Factory-empty source build' if source_test else 'Pure plan assertions',
                plan=result,probes=probes,collections=counts,
                native_validation='NOT RUN; root must inspect the assembled Unreal scene and collision')
    (HERE/'test_result.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))


if __name__=='__main__':run()
