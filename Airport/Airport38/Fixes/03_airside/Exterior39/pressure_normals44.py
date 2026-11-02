"""Normal-only correction for the two retained exterior pressure-window kits.

No vertices/faces/UVs/materials/transforms/interactions are changed. Root applies
this directly to its existing collections so current glazing aliases survive.
Version2 retains outward analytic side skins but restores the crown's exact
RecoveryBefore44 inward computed corner normals; its winding is not changed.
"""
from pathlib import Path
import math,json,hashlib
IDS=('SM_AP_W40PressureWindows','SM_AP_W40CargoBayWindows')
F=Path(__file__).parent
CROWN_ORIGINAL_NORMALS_SHA256='565fba262c5e2699e1f33bd421f0a79ac988ee9ab6885f439025a3c94629f53a'

def analytic_normal(point):
    from mathutils import Vector
    x,y,z=point
    n=Vector(((1 if x>=0 else -1)*(abs(x)/2.5)**2.6/2.5,0.,(1 if z>=.55 else -1)*abs((z-.55)/2.35)**2.6/2.35));return n.normalized()

def _plain(value):
    if isinstance(value,(str,bool,int,float)) or value is None:return value
    try:return [_plain(x) for x in value]
    except TypeError:return str(value)

def snapshot(col):
    """All stored topology/attributes/UVs/slots/transforms except custom normals."""
    rows=[]
    for o in col.objects:
        me=o.data;attributes=[]
        if o.type=='MESH':
            for attr in me.attributes:
                if attr.name in ('custom_normal','.custom_normal') or attr.data_type=='INT16_2D' and 'normal' in attr.name:continue
                vals=[]
                for v in attr.data:
                    vals.append({p.identifier:_plain(getattr(v,p.identifier)) for p in v.bl_rna.properties if p.identifier!='rna_type'})
                attributes.append((attr.name,attr.data_type,attr.domain,vals))
        rows.append(dict(name=o.name,type=o.type,matrix=_plain(o.matrix_local),parent=o.parent.name if o.parent else None,materials=[m.name if m else None for m in me.materials],
          vertices=[list(v.co) for v in me.vertices] if o.type=='MESH' else None,
          edges=[(tuple(e.vertices),e.use_seam,e.use_edge_sharp) for e in me.edges] if o.type=='MESH' else None,
          faces=[(tuple(p.vertices),p.material_index,p.use_smooth) for p in me.polygons] if o.type=='MESH' else None,
          loops=[(v.vertex_index,v.edge_index) for v in me.loops] if o.type=='MESH' else None,attributes=attributes,
          uv=[(u.name,[list(v.uv) for v in u.data]) for u in me.uv_layers] if o.type=='MESH' else None,
          modifiers=[(m.name,m.type,[(p.identifier,_plain(getattr(m,p.identifier))) for p in m.bl_rna.properties if p.identifier not in ('rna_type',) and p.type in ('INT','FLOAT','BOOLEAN','STRING','ENUM')]) for m in o.modifiers]))
    return rows

def fingerprint(col):return hashlib.sha256(json.dumps(snapshot(col),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def apply(ctx):
    import bpy
    report=dict(version=2,assets=list(IDS),normal_only=True,geometry_uv_material_transform_interactions_unchanged=True,collections=[])
    interactions=json.dumps(ctx.D.get('interactions',[]),sort_keys=True)
    for aid in IDS:
        col=bpy.data.collections.get(aid);assert col,('Retained pressure collection absent',aid);before=fingerprint(col);before_rows=snapshot(col);parts=[]
        for ob in col.objects:
            if ob.type!='MESH' or not ob.name.startswith(('W40 pressure skin with matched rounded aperture','Fitted pressure crown09')):continue
            if ob.name.startswith('Fitted pressure crown09'):
                # This retained strip has inward geometric winding and had NO
                # custom normal layer in RecoveryBefore44. Do not impose the
                # pressure side skin's outward field on it. Removing only the
                #44-added layer restores the original buffer exactly, including
                # the original smooth boundary treatment. Hash the actual
                # resulting384 corner vectors against the preserved authority.
                me=ob.data;had_custom=me.has_custom_normals
                for attr in list(me.attributes):
                    if attr.name in ('custom_normal','.custom_normal') or attr.data_type=='INT16_2D' and 'normal' in attr.name:me.attributes.remove(attr)
                me.update();normals=[list(n.vector) for n in me.corner_normals]
                digest=hashlib.sha256(json.dumps(normals,separators=(',',':')).encode()).hexdigest()
                assert not me.has_custom_normals and digest==CROWN_ORIGINAL_NORMALS_SHA256,('Original crown normal authority mismatch',ob.name,digest)
                assert len(me.vertices)==194 and len(me.polygons)==96 and len(me.loops)==384
                assert all((ob.matrix_local.to_3x3().inverted().transposed()@p.normal).normalized().dot(analytic_normal(ob.matrix_local@me.vertices[p.vertices[0]].co))<-.9999 for p in me.polygons)
                parts.append(dict(part=ob.name,loops=len(normals),method='Restore exact RecoveryBefore44 computed INWARD crown normals',removed_added_custom_normal_layer=had_custom,after_original_normal_sha256=digest,after_angle_max=0.,geometry_winding_material_unchanged=True));continue
            me=ob.data;had_sharp_edge='sharp_edge' in me.attributes;T=ob.matrix_local;N=T.to_3x3().transposed();new=[];oldangles=[];newangles=[];oldy=[];newy=[]
            for loop in me.loops:
                p=T@me.vertices[loop.vertex_index].co;implicit=(abs(p.x)/2.5)**3.6+abs((p.z-.55)/2.35)**3.6;assert abs(implicit-1)<2e-5,(ob.name,list(p),implicit)
                expected=analytic_normal(p);old=(T.to_3x3().inverted().transposed()@me.corner_normals[loop.index].vector).normalized();oldangles.append(math.degrees(math.acos(max(-1,min(1,old.dot(expected))))));oldy.append(abs(old.y));new.append((N@expected).normalized())
            me.normals_split_custom_set(new);me.update()
            restored_schema=False
            if not had_sharp_edge and 'sharp_edge' in me.attributes:
                attr=me.attributes['sharp_edge'];assert not any(v.value for v in attr.data),'Setter changed actual edge smoothing'
                me.attributes.remove(attr);me.update();restored_schema=True
            for loop in me.loops:
                expected=analytic_normal(T@me.vertices[loop.vertex_index].co);actual=(T.to_3x3().inverted().transposed()@me.corner_normals[loop.index].vector).normalized();newangles.append(math.degrees(math.acos(max(-1,min(1,actual.dot(expected))))));newy.append(abs(actual.y))
            assert max(newangles)<.05 and max(newy)<.001,(ob.name,max(newangles),max(newy))
            parts.append(dict(part=ob.name,loops=len(new),before_angle_max=max(oldangles),after_angle_max=max(newangles),before_normal_y_max=max(oldy),after_normal_y_max=max(newy),removed_new_all_false_sharp_edge_attribute=restored_schema))
        assert len(parts)==3,(aid,[p['part'] for p in parts])
        after=fingerprint(col)
        if before!=after:
            differences=[]
            for old,new in zip(before_rows,snapshot(col)):
                keys=[k for k in old if old[k]!=new[k]]
                if keys:differences.append(dict(part=old['name'],keys=keys,old_attributes=[(q[0],q[1],q[2]) for q in old['attributes']],new_attributes=[(q[0],q[1],q[2]) for q in new['attributes']],old_edges=old['edges'][:3],new_edges=new['edges'][:3]))
            (F/'PressureNormals44_FingerprintDiff.json').write_text(json.dumps(differences,indent=2))
        assert before==after,('Non-normal data changed',aid,before,after)
        ctx.a.ASSETS[aid]=dict(collection=col,collision='complex')
        for ob in col.objects:
            for m in ob.data.materials:
                if m:ctx.a.MATS[m.name]=m
        report['collections'].append(dict(asset=aid,before_fingerprint_excluding_custom_normals=before,after_fingerprint_excluding_custom_normals=after,parts=parts))
    assert interactions==json.dumps(ctx.D.get('interactions',[]),sort_keys=True)
    return report
