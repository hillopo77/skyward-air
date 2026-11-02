"""Low hip/lap belt routing; arm surfaces are never fitting authority."""
import math,json
from pathlib import Path
import business_belt40 as B
F=Path(__file__).parent
IDS=['SM_AP_B41LapWornCrew','SM_AP_B41LapWornGeneric']
VERSION=2

def _ribbon(a,edges,normals,trees):
    from mathutils import Vector
    vertices=[];width=5
    for (left,right),normal in zip(edges,normals):
        normal=Vector(normal).normalized();row=[B._clear_clothing(Vector(left).lerp(Vector(right),j/(width-1)),trees) for j in range(width)]
        for depth in (-.0014,.0014):vertices.extend(p+normal*depth for p in row)
    faces=[]
    for i in range(len(edges)-1):
        k=i*2*width;n=(i+1)*2*width
        for j in range(width-1):faces.extend([(k+j,n+j,n+j+1,k+j+1),(k+width+j,k+width+j+1,n+width+j+1,n+width+j)])
        faces.extend([(k,k+width,n+width,n),(k+width-1,n+width-1,n+2*width-1,k+2*width-1)])
    for k in (0,(len(edges)-1)*2*width):faces.extend((k+j,k+j+1,k+width+j+1,k+width+j) for j in range(width-1))
    a.mesh('B41 continuous low hip lap webbing',vertices,faces,'B40Web')
    for i in range(0,len(edges)-1,2):
        for side in (0,1):
            p=B._clear_clothing(Vector(edges[i][side])*.96+Vector(edges[i][1-side])*.04,trees)+Vector(normals[i]).normalized()*.0019
            q=B._clear_clothing(Vector(edges[i+1][side])*.96+Vector(edges[i+1][1-side])*.04,trees)+Vector(normals[i]).normalized()*.0019;d=q-p
            if d.length>.0005:a.tube('B41 sewn selvage stitch',[p,p+d.normalized()*min(.005,d.length)],.00045,'B40Stitch',6)

def build_units(ctx,bodytrees):
    import bpy
    from mathutils import Vector
    a=ctx.a;B._aliases(a);meta=dict(version=VERSION,assets=IDS,worn={},fitting_authority='Pelvis/spine/thigh/trouser triangles only; all arm/hand/finger weighted triangles excluded',side_anchors=B.ANCHORS)
    for kind,aid in zip(('Crew','Generic'),IDS):
        c=bpy.data.collections.new(aid);c.use_fake_user=True;c['belt41_asset_id']=aid;c['belt41_version']=VERSION;a.ACTIVE=c;a.ASSETS[aid]=dict(collection=c,collision='none')
        trees=[bodytrees['Crew']] if kind=='Crew' else list(bodytrees.values());zcentre=.600
        hits=[B._body_hit(t,x,z)[0] for t in trees for x in (-.065,-.035,0,.035,.065) for z in (zcentre-.024,zcentre,zcentre+.024)]
        centre=[0,min(p.y for p in hits)-.015,zcentre];meta['worn'][kind]=dict(buckle_centre=centre,hinge=[0,centre[1]-.011,zcentre+.022],complete_buckle_footprint_body_ray_fit=True)
        for side in (-1,1):
            edges=[];normals=[]
            for j in range(129):
                theta=math.radians(side*(120-(120-12)*j/128));direction=Vector((math.sin(theta),-math.cos(theta),0));row=[];nn=[]
                for z in (zcentre-.019,zcentre+.019):
                    origin=Vector((0,-.135,z));best=None
                    for tree in trees:
                        h=tree.ray_cast(origin+direction*.8,-direction,.8)
                        if h[0] is not None and (best is None or (h[0]-origin).length>(best[0]-origin).length):best=h
                    assert best is not None,(kind,side,j,z)
                    n=best[1].normalized()
                    if n.dot(direction)<0:n=-n
                    row.append(B._clear_clothing(best[0]+n*.006,trees));nn.append(n)
                edges.append(row);normals.append((nn[0]+nn[1]).normalized())
            tail=[[(x,y,z-.019),(x,y,z+.019)] for x,y,z in [(side*.325,.15,.50),(side*.327,.105,.535),(side*.315,.055,.570),(side*.290,.015,.595)]]
            edges=tail+edges;normals=[Vector((side,0,0))]*len(tail)+normals
            x=-.036 if side<0 else .055;edges.append([(x,centre[1],zcentre-.019),(x,centre[1],zcentre+.019)]);normals.append(Vector((0,-1,0)));_ribbon(a,edges,normals,trees)
        B._female(a,centre);B._male(a,centre)
    return meta

def apply(ctx):
    import bpy
    meta=json.loads((F/'BusinessBelt41_Model.json').read_text());existing={n:next((c for c in bpy.data.collections if c.get('belt41_asset_id')==n and c.get('belt41_version')==VERSION),None) for n in IDS};requested=tuple(n for n in IDS if not existing[n])
    if requested:
        with bpy.data.libraries.load(str(F/'BusinessBelt41_UnitKits.blend'),link=False) as (src,dst):
            assert set(IDS)<=set(src.collections),('Incomplete B41 source bundle',src.collections);dst.collections=list(requested)
        loaded=dict(zip(requested,dst.collections))
    else:loaded={}
    cols={n:existing[n] or loaded[n] for n in IDS}
    for aid,c in cols.items():
        c.use_fake_user=True;ctx.a.ASSETS[aid]=dict(collection=c,collision='none')
        for ob in c.objects:
            for mat in ob.data.materials:
                if mat:ctx.a.MATS[mat.name]=mat
    records=ctx.D['repair38']['business_belt40']['records']
    for r in records:
        kind=r['worn_kind'];r['worn_asset']=IDS[0] if kind=='Crew' else IDS[1];r['worn_hinge']=[x+y for x,y in zip(r['location'],meta['worn'][kind]['hinge'])]
        for q in ctx.D['instances']:
            if q['name']==r['worn_actor']:q['asset']=r['worn_asset']
        ob=ctx.scene.objects.get(r['worn_actor'])
        if ob:ob.instance_collection=cols[r['worn_asset']]
        ob=ctx.scene.objects.get(r['control'])
        if ob:ob.location=r['worn_hinge'];ob.rotation_euler=(0,0,0)
    result=dict(version=VERSION,assets=IDS,route='Actual low hip/lap, beneath/behind resting hands; arm geometry excluded from fit',records=len(records));ctx.D['repair38']['business_belt41']=result;return result

def prepare_plane(P,D):
    if P.DATA.get('business_belt41_prepared'):return
    by={q['name']:q for q in P.DATA['instances']}
    for r in D['repair38']['business_belt40']['records']:
        by[r['control']]['location']=list(r['worn_hinge']);q=next(q for q in P.DATA['interactions'] if q.get('actor')==r['control']);q['point']=[r['worn_hinge'][0],r['worn_hinge'][1]-.004,r['worn_hinge'][2]-.02]
        target=next(t for t in q['targets'] if t['actor']==r['control']);target['translation_states']=[[0,0,0],[b-a for a,b in zip(r['worn_hinge'],r['stowed_hinge'])]]
    P.DATA['business_belt41_prepared']=VERSION

def apply_native(ctx):
    u=ctx.u;by={str(t)[8:]:a for a in ctx.EA.get_all_level_actors() for t in a.tags if str(t).startswith('Skyward:')};changed=[]
    for r in ctx.D['repair38']['business_belt40']['records']:
        actor=by[r['worn_actor']];c=actor.get_component_by_class(u.StaticMeshComponent);mesh=ctx.mesh(r['worn_asset']);c.set_static_mesh(mesh)
        for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
        lid=by[r['control']];lid.set_actor_location(ctx.v(r['worn_hinge']),False,True);lid.set_actor_rotation(u.Rotator(),False);changed.append(r['worn_actor'])
    return dict(status='APPLIED_REQUIRES_NATIVE_SILHOUETTE_REVIEW',version=VERSION,worn_assemblies=changed,retained_original_lids_and_stowed_halves=True)
