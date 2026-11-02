"""Read-only parked/runtime exterior audit. Root calls apply(G) in its session.

No actor transforms, materials, control states or assets are changed. The only
write is the evidence JSON under ArtBible/ExteriorNative39.json.
"""
import json, math, traceback


def _path(ob):return ob.get_path_name() if ob else None
def _vec(v):return [float(v.x),float(v.y),float(v.z)]
def _quat(q):return [float(q.x),float(q.y),float(q.z),float(q.w)]


def _material(u,mat):
    if not mat:return None
    out=dict(path=_path(mat),name=mat.get_name(),type=mat.get_class().get_name(),vectors={},scalars={})
    try:out['parent']=_path(mat.get_editor_property('parent'))
    except Exception:pass
    ML=u.MaterialEditingLibrary
    for name in ('BaseColor','Color','Tint'):
        try:
            c=ML.get_material_instance_vector_parameter_value(mat,name)
            out['vectors'][name]=[float(c.r),float(c.g),float(c.b),float(c.a)]
        except Exception as e:out['vectors'][name]=dict(unavailable=str(e))
    for name in ('Roughness','Metallic','Emission','NormalStrength','Specular'):
        try:out['scalars'][name]=float(ML.get_material_instance_scalar_parameter_value(mat,name))
        except Exception as e:out['scalars'][name]=dict(unavailable=str(e))
    return out


def _axisquat(u,axis,degrees):
    r=math.radians(degrees)*.5;s=math.sin(r)
    return u.Quat(x=-axis[0]*s,y=axis[1]*s,z=-axis[2]*s,w=math.cos(r))


def _angle_error(a,b):
    dot=abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)
    return math.degrees(2*math.acos(max(-1.,min(1.,dot))))


def apply(G):
    u=G.u;P=G.P;D=G.D;flight=getattr(G,'flight39',{});runtime=flight.get('runtime',{});frame=flight.get('frame');state=flight.get('state',{})
    report=dict(scope='Read-only existing native game session, no actor/asset/control mutations',
                parked_rest=state.get('speed',0)<.02 and not state.get('airborne',False),
                flight_state={k:state.get(k) for k in ('phase','position','heading','pitch','bank','speed','flaps','gear_down')},materials={},actors=[],actuators=[],rays=[],shades=[],warnings=[])
    actors=list(u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.Actor));byname={a.get_actor_label():a for a in actors}
    manifest=json.loads((G.R/'Exports/airport_assets.json').read_text());specs={q['id']:q for q in manifest['assets']}
    def reference(p):return frame.reference(p) if frame else p
    def world(p):return frame.world(P.vector(p)) if frame else P.vector(p)
    def source(p):return list(G.source(reference(p)))
    def actor(a):
        row=dict(actor=a.get_actor_label(),object=a.get_name(),location_reference=source(a.get_actor_location()),rotation=_quat(a.get_actor_rotation().quaternion()),parent=a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None,components=[])
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh=c.static_mesh
            if not mesh:continue
            name=mesh.get_name();expected=specs.get(name,{}).get('materials',[])
            cr=dict(component=c.get_name(),mesh=_path(mesh),expected_slot_names=expected,slots=[])
            try:cr['override_materials']=[_path(m) for m in c.get_editor_property('override_materials')]
            except Exception as e:cr['override_read_error']=str(e)
            try:defaults=list(mesh.get_editor_property('static_materials'))
            except Exception:defaults=[]
            for i in range(c.get_num_materials()):
                effective=c.get_material(i);default=defaults[i].material_interface if i<len(defaults) else None
                cr['slots'].append(dict(index=i,expected=expected[i] if i<len(expected) else None,effective=_path(effective),mesh_default=_path(default),differs_from_mesh_default=effective!=default))
                if effective and _path(effective) not in report['materials']:report['materials'][_path(effective)]=_material(u,effective)
                if i<len(expected) and effective and effective.get_name()!=expected[i]:report['warnings'].append(dict(issue='Material interface differs from exported slot name',actor=row['actor'],slot=i,expected=expected[i],actual=effective.get_name()))
            row['components'].append(cr)
        return row
    relevant=[]
    for a in actors:
        n=a.get_actor_label();tags=[str(t) for t in a.tags]
        if any(t=='Skyward:SM_Plane_ExteriorAirframe' for t in tags) or n.startswith(('Flight39 flap ','Flight39 aileron ','Flight39 elevator ','Flight39 rudder ')):
            relevant.append(a)
    report['actors']=[actor(a) for a in relevant]
    # Compare actual authored pivots and rotations to the exact current carrier
    # reference. An attractive silhouette alone cannot prove actuator alignment.
    for q in D.get('flight39',{}).get('surface_records',[]):
        a=byname.get(q['actor']);row=dict(actor=q['actor'],asset=q['asset'],role=q['role'],axis=q['axis'],intended_pivot=q['pivot'])
        if a:
            actual=source(a.get_actor_location());row.update(actual_pivot_reference=actual,pivot_error_m=math.dist(actual,q['pivot']),parent=a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None)
            actual_binding=next((r for r in runtime.get('surfaces',[]) if r[0]['actor']==q['actor']),None)
            if actual_binding and actual_binding[2] is not None:
                base=actual_binding[2];role=q['role'];side=q['side'];controls=state.get('controls',{})
                angle=-side*[0,5,15][state.get('flaps',0)] if role=='flap' else -controls.get('roll',0)*18 if role=='aileron' else side*controls.get('pitch',0)*18 if role=='elevator' else controls.get('rudder',0)*18
                expected=P._quat_product(base,_axisquat(u,q['axis'],angle));actual_rotation=a.root_component.get_editor_property('relative_rotation').quaternion()
                row.update(expected_angle_deg=angle,actual_relative_quaternion=_quat(actual_rotation),expected_relative_quaternion=_quat(expected),rotation_error_deg=_angle_error(actual_rotation,expected))
            if row['pivot_error_m']>.005:report['warnings'].append(dict(issue='Actuator pivot differs from carrier-relative intended point',actor=q['actor'],error_m=row['pivot_error_m']))
            if row.get('rotation_error_deg',0)>.25:report['warnings'].append(dict(issue='Actuator relative rotation differs from current control state',actor=q['actor'],error_deg=row['rotation_error_deg']))
        else:row['missing']=True;report['warnings'].append(dict(issue='Missing authored actuator',actor=q['actor']))
        report['actuators'].append(row)
    # Full collision trace records identify broad-panel and shoulder/roof owners.
    # This queries collision geometry: render-only fasteners may not block rays.
    rays=[]
    for side in (-1,1):
        for span,y in ((5,16.5),(10,18.3),(16,20.1)):
            rays.append(('wing_%s_%s'%(side,span),[16+side*span,y,5],[16+side*span,y,-2]))
        for y in (2.7,7.4,13.5,22.8,25.4,31.6):
            rays.append(('shoulder_%s_%s'%(side,y),[16+side*1.8,y,4],[16+side*1.8,y,1.8]))
    for y in (3.4,7.4,13.5,22.8,25.4,31.6):rays.append(('crown_'+str(y),[16,y,4.5],[16,y,2.55]))
    for label,start,end in rays:
        row=dict(name=label,start_reference=start,end_reference=end)
        try:
            hit=u.SystemLibrary.line_trace_single(P.STATE['world'],world(start),world(end),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[P.STATE['pawn']],u.DrawDebugTrace.NONE,True)
            h=hit.to_tuple() if hit else [];owner=h[9] if len(h)>9 else None;c=h[10] if len(h)>10 else None
            row.update(blocking=bool(h and h[0]),owner=owner.get_actor_label() if owner else None,component=c.get_name() if c else None,mesh=c.static_mesh.get_name() if c and getattr(c,'static_mesh',None) else None,impact_reference=source(h[5]) if len(h)>5 else None)
            if hit:
                try:row['face_index']=int(hit.get_editor_property('face_index'))
                except Exception:row['hit_tuple_types']=[type(v).__name__ for v in h]
                if c and row.get('face_index',-1)>=0 and hasattr(c,'get_material_from_collision_face_index'):
                    try:result=c.get_material_from_collision_face_index(row['face_index']);row['hit_material']=_path(result[0]);row['hit_material_slot']=int(result[1])
                    except Exception as e:row['face_material_error']=str(e)
        except Exception as e:row['error']=str(e)
        report['rays'].append(row)
    for key,m in P.STATE.get('movables',{}).items():
        if not key.startswith('Window shade '):continue
        item=m.get('item',{});parts=item.get('roller_parts',[])
        report['shades'].append(dict(actor=key,progress=m.get('progress'),target=m.get('target'),part_deltas=[p.get('delta') for p in parts],actual_actor_reference=source(m['actor'].get_actor_location()) if m.get('actor') else None))
    report['shade_prepare_marker']=P.DATA.get('exterior39_shades')
    report['complete']=True
    path=G.R/'ArtBible/ExteriorNative39.json';path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return dict(path=str(path),parked_rest=report['parked_rest'],actors=len(report['actors']),actuators=len(report['actuators']),rays=len(report['rays']),warnings=report['warnings'])
