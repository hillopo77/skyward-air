"""Small, read-only original/current crown material/winding/normal authority."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
F=Path(__file__).parent;R=F.parents[2];sys.path.insert(0,str(F));import pressure_normals44 as P
report={'sources':{},'authority':{}}
for label,path in [('original',R/'SourceAssets/RecoveryBefore44/Airport_Repaired38.blend'),('current',R/'Airport_Repaired38.blend')]:
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.collections=list(P.IDS)
    cols=dict(zip(P.IDS,dst.collections));rows=[]
    for aid,c in cols.items():
        for o in c.objects:
            if o.type!='MESH' or not o.name.startswith('Fitted pressure crown09'):continue
            me=o.data;T=o.matrix_local
            normals=[list(n.vector) for n in me.corner_normals]
            pn=[]
            for p in me.polygons:
                v=T@me.vertices[p.vertices[0]].co;an=P.analytic_normal(v);pn.append(float((T.to_3x3().inverted().transposed()@p.normal).normalized().dot(an)))
            mats=[]
            for m in me.materials:
                n=m.node_tree.nodes.get('Principled BSDF') if m and m.use_nodes else None
                mats.append({'name':m.name if m else None,'diffuse':list(m.diffuse_color) if m else None,'base':list(n.inputs['Base Color'].default_value) if n else None,'roughness':n.inputs['Roughness'].default_value if n else None})
            row={'asset':aid,'part':o.name,'materials':mats,'bounds':[[min((T@v.co)[i] for v in me.vertices) for i in range(3)],[max((T@v.co)[i] for v in me.vertices) for i in range(3)]],'vertices':len(me.vertices),'faces':len(me.polygons),'loops':len(me.loops),'has_custom_normals':me.has_custom_normals,'attributes':[(a.name,a.data_type,a.domain) for a in me.attributes],'geometric_face_dot_outward_min':min(pn),'geometric_face_dot_outward_max':max(pn),'loop_normals_sha256':hashlib.sha256(json.dumps(normals,separators=(',',':')).encode()).hexdigest(),'first_loop_normal':normals[0]}
            if label=='original':report['authority'][aid]={'normals':normals,'has_custom_normals':me.has_custom_normals,'non_normal_fingerprint':P.fingerprint(c),'part':o.name}
            rows.append(row)
    report['sources'][label]=rows
(F/'Crown44B_Authority.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['sources'],indent=2))
