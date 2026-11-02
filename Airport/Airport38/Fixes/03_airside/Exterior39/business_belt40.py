"""Modeled restrained/stowed business belts. Isolated source/native/data hooks.

Existing four control names now change actual webbing/buckle assemblies; the
separate lid remains a real hinged part. Parent owns assembly/import/runtime.
"""
import math,json
from pathlib import Path
F=Path(__file__).parent
IDS=['SM_AP_B40LuxurySeatBase','SM_AP_B40LapStowed','SM_AP_B40LapWornCrew','SM_AP_B40LapWornGeneric','SM_AP_B40ReleaseLid']
SEATS=['Business 01 A','Business 01 K','Business 02 A','Business 02 K']
ANCHORS=[[-.325,.15,.50],[.325,.15,.50]]

def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)


def _matrix(o):
    from mathutils import Matrix
    return Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)


def _aliases(a):
    import bpy
    for short,name in [('B40Web','MI_Plane_DetailWeb12'),('B40Stitch','MI_Plane_DetailStitch12'),('B40Steel','MI_Plane_DetailSteel12'),('B40Dark','MI_Plane_SuiteDark11'),('B40Leather','MI_Plane_SuiteLeather11')]:
        m=bpy.data.materials.get(name);assert m,('Original belt finish missing',name);a.MATS[short]=m


def _ring(a,name,p,w,h,r,thick,material):
    # True open stamped rectangular receiver in theXZ plane, thickness alongY.
    x,y,z=p;outside=a.rr(w,h,r,10);inside=a.rr(w-.014,h-.014,max(.002,r-.004),10);n=len(outside)
    v=[(x+xx,y+yy,z+zz) for yy in (-thick/2,thick/2) for loop in (outside,inside) for xx,zz in loop]
    faces=[]
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,j,2*n+j,2*n+i),(n+i,3*n+i,3*n+j,n+j),(i,n+i,n+j,j),(2*n+i,2*n+j,3*n+j,3*n+i)])
    return a.mesh(name,v,faces,material,.0008)


def _female(a,centre,rotation=0):
    from mathutils import Matrix,Vector
    before=set(a.ACTIVE.objects);_ring(a,'B40 pressed female receiver with real throat',centre,.080,.044,.010,.016,'B40Steel')
    x,y,z=centre
    a.box('B40 receiver retained pivot shoulder',(x,y-.006,z+.021),(.072,.009,.009),'B40Steel',.002)
    a.cyl('B40 receiver captive hinge spindle',(x,y-.011,z+.022),.0035,.080,'B40Steel',axis='X')
    for sx in (-1,1):a.cyl('B40 receiver flush spindle retainer',(x+sx*.038,y-.011,z+.022),.005,.002,'B40Dark',axis='X')
    if rotation:
        T=Matrix.Translation(Vector(centre));rot=T@Matrix.Rotation(rotation,4,'X')@T.inverted()
        for ob in set(a.ACTIVE.objects)-before:
            M=_matrix(ob);inv=M.inverted()
            for v in ob.data.vertices:v.co=inv@(rot@(M@v.co))
    return list(set(a.ACTIVE.objects)-before)


def _male(a,centre,rotation=0):
    from mathutils import Matrix,Vector
    before=set(a.ACTIVE.objects);x,y,z=centre
    _ring(a,'B40 polished male tongue with actual engagement slot',(x+.025,y,z),.068,.032,.006,.004,'B40Steel')
    a.box('B40 male tongue retained webbing crossbar',(x+.055,y,z),(.012,.010,.035),'B40Steel',.0015)
    if rotation:
        T=Matrix.Translation(Vector(centre));rot=T@Matrix.Rotation(rotation,4,'X')@T.inverted()
        for ob in set(a.ACTIVE.objects)-before:
            M=_matrix(ob);inv=M.inverted()
            for v in ob.data.vertices:v.co=inv@(rot@(M@v.co))


def _ribbon(a,name,edges,normals,bodytrees=None):
    from mathutils import Vector
    v=[];width_samples=5 if bodytrees else 2
    for (l,r),normal in zip(edges,normals):
        normal=Vector(normal).normalized()
        row=[]
        for j in range(width_samples):
            p=Vector(l).lerp(Vector(r),j/(width_samples-1))
            if bodytrees and p.z>=.64:p=_clear_clothing(p,bodytrees)
            row.append(p)
        for depth in (-.0014,.0014):v.extend([p+normal*depth for p in row])
    faces=[]
    for i in range(len(edges)-1):
        k=i*2*width_samples;n=(i+1)*2*width_samples
        for j in range(width_samples-1):faces.extend([(k+j,n+j,n+j+1,k+j+1),(k+width_samples+j,k+width_samples+j+1,n+width_samples+j+1,n+width_samples+j)])
        faces.extend([(k,k+width_samples,n+width_samples,n),(k+width_samples-1,n+width_samples-1,n+2*width_samples-1,k+2*width_samples-1)])
    for k in (0,(len(edges)-1)*2*width_samples):
        faces.extend((k+j,k+j+1,k+width_samples+j+1,k+width_samples+j) for j in range(width_samples-1))
    ob=a.mesh(name,v,faces,'B40Web')
    # Real short sewn selvage stitches on both edges; quiet inherited material.
    for i in range(0,len(edges)-1,2):
        for side in (0,1):
            p=Vector(edges[i][side]);q=Vector(edges[i+1][side]);n=Vector(normals[i]).normalized()
            p=p*.96+Vector(edges[i][1-side])*.04+n*.0019;q=q*.96+Vector(edges[i+1][1-side])*.04+n*.0019
            d=q-p
            if d.length>.0005:a.tube('B40 sewn selvage stitch',[p,p+d.normalized()*min(.005,d.length)],.00045,'B40Stitch',6)
    return ob


def _body_hit(tree,x,z):
    from mathutils import Vector
    hit=tree.ray_cast(Vector((x,-1.,z)),Vector((0,1,0)),2.)
    assert hit[0] is not None,('No actual front lap surface',x,z)
    return hit[0],hit[1]


def _clear_clothing(point,trees):
    # The posed mesh has real garment overlaps and fingers near the lap. A
    # radial section can clear one triangle and still meet its neighbour. Relax
    # only the flexible cloth edge against all actual local candidate surfaces.
    p=point.copy()
    for _ in range(12):
        changed=False
        for tree in trees:
            hit=tree.find_nearest(p)
            if hit[0] is None:continue
            signed=(p-hit[0]).dot(hit[1])
            if signed<.0075:p+=hit[1]*(.0075-signed);changed=True
        if not changed:break
    return p


def build_units(ctx,chair,bodytrees,cushion):
    """Called only by private source build; bodytrees are evaluated candidate BVHs."""
    import bpy
    from mathutils import Vector,Matrix
    a=ctx.a;_aliases(a);metadata=dict(assets=IDS,anchor_points=ANCHORS,worn={})
    def col(name):
        c=bpy.data.collections.new(name);c.use_fake_user=True;c['business_belt40_asset_id']=name;c['business_belt40_version']=1;a.ACTIVE=c;a.ASSETS[name]=dict(collection=c,collision='none');return c
    base=col(IDS[0]);a.ASSETS[IDS[0]]['collision']='complex';removed=[]
    for ob in chair.objects:
        if ob.name.startswith(('Suite surface fitted woven restraint12','Suite buckle genuinely open tongue frame12','Suite buckle retained hinge pin12')):removed.append(ob.name);continue
        q=ob.copy();q.data=ob.data.copy();base.objects.link(q)
    assert len(removed)==8,('Actual ergonomic-chair fixed belt ownership changed',removed)
    for side in (-1,1):
        a.box('B40 anchor plate seated on arm chassis',(side*.334,.15,.50),(.006,.079,.058),'B40Steel',.002)
        ring=_ring(a,'B40 retained webbing anchor D loop',(0,0,0),.064,.045,.007,.006,'B40Steel');ring.rotation_euler.z=math.pi/2;ring.location=(side*.328,.15,.50)
        for y in (.125,.175):a.cyl('B40 captive anchor bolt',(side*.329,y,.50),.0055,.008,'B40Dark',axis='X')
        a.box('B40 side buckle parking clip attached to arm',(side*.327,-.18,.507),(.023,.083,.026),'B40Dark',.004)
    metadata['removed_old_fixed_parts']=removed
    # Fitted pan-edge resting halves. Every edge is sampled on real cushion.
    stowed=col(IDS[1]);clips=[]
    for side in (-1,1):
        centres=[];edges=[]
        for j in range(39):
            t=j/38;x=side*(.305+.003*math.sin(t*math.pi));y=.15-.33*t;row=[]
            for xx in (x-.019,x+.019):
                hit=cushion.ray_cast(Vector((xx,y,.9)),Vector((0,0,-1)),.7)[0];assert hit is not None,(xx,y);row.append((xx,y,hit.z+.003))
            edges.append(row)
        _ribbon(a,'B40 stowed webbing follows outer pan edge',edges,[(0,0,1)]*len(edges))
        hit=cushion.ray_cast(Vector((side*.318,-.18,.9)),Vector((0,0,-1)),.7)[0];assert hit is not None
        centre=[-.290 if side<0 else .270,-.18,hit.z+.011]
        if side<0:_female(a,centre,-math.pi/2)
        else:_male(a,centre,-math.pi/2)
        clips.append(centre)
    metadata['stowed_receiver_centre']=clips[0]
    metadata['stowed_hinge']=[clips[0][0],clips[0][1]+.022,clips[0][2]+.011]
    for key,aid in [('Crew',IDS[2]),('Generic',IDS[3])]:
        c=col(aid);trees=[bodytrees['Crew']] if key=='Crew' else list(bodytrees.values())
        buckle_z=.705
        hits=[_body_hit(t,x,z)[0] for t in trees for x in (-.065,-.035,0,.035,.065) for z in (buckle_z-.024,buckle_z,buckle_z+.024)]
        front=min(p.y for p in hits);centre=[0.,front-.015,buckle_z]
        metadata['worn'][key]=dict(buckle_centre=centre,hinge=[0.,centre[1]-.011,buckle_z+.022],complete_buckle_footprint_body_ray_fit=True)
        # Each ribbon edge follows the actual posed body section, with thickness
        # and a small clothing clearance. Rear tails connect to true chassis D loops.
        for side in (-1,1):
            edges=[];normals=[]
            for j in range(129):
                angle=120-(120-12)*j/128;theta=math.radians(side*angle);direction=Vector((math.sin(theta),-math.cos(theta),0));row=[];nn=[]
                centre_z=.665+.040*smooth((120-angle)/108)
                for z in (centre_z-.019,centre_z+.019):
                    origin=Vector((0,-.135,z));best=None
                    for tree in trees:
                        result=tree.ray_cast(origin+direction*.8,-direction,.8)
                        if result[0] is not None and (best is None or (result[0]-origin).length>(best[0]-origin).length):best=result
                    assert best is not None,(key,side,j,z)
                    n=best[1].normalized()
                    if n.dot(direction)<0:n=-n
                    row.append(_clear_clothing(best[0]+n*.006,trees));nn.append(n)
                edges.append(row);normals.append((nn[0]+nn[1]).normalized())
            # A tensioned rising tail exits the arm-mounted side anchor. Keep it
            # outside the hips until it reaches the fitted waist section.
            tail=[]
            for x,y,z in [(side*.325,.15,.50),(side*.327,.105,.54),(side*.315,.055,.585),(side*.290,.015,.625)]:tail.append([(x,y,z-.019),(x,y,z+.019)])
            edges=tail+edges;normals=[Vector((side,0,0))]*len(tail)+normals
            attach=[-.036 if side<0 else .055,centre[1],buckle_z]
            edges.append([(attach[0],attach[1],attach[2]-.019),(attach[0],attach[1],attach[2]+.019)]);normals.append(Vector((0,-1,0)))
            _ribbon(a,'B40 worn tensioned lap webbing '+key,edges,normals,trees)
        _female(a,centre);_male(a,centre)
    lid=col(IDS[4])
    # Local origin is the real transverse hinge spindle. Closed leaf covers the
    # receiver throat; opening rotates the whole retained lid, not a fake label.
    outline=a.rr(.067,.039,.007,10);n=len(outline);v=[(x,y,z-.0195) for y in (-.003,.003) for x,z in outline]
    faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    a.mesh('B40 sculpted lift-to-release buckle lid',v,faces,'B40Leather',.0006)
    a.cyl('B40 lid retained transverse hinge sleeve',(0,0,0),.004,.071,'B40Steel',axis='X')
    a.box('B40 lid engraved finger recess',(0,-.0032,-.027),(.035,.0008,.008),'B40Dark',.001)
    metadata['version']=1
    return metadata


def apply(ctx):
    import bpy
    unit=F/'BusinessBelt40_UnitKits.blend';meta=json.loads((F/'BusinessBelt40_Model.json').read_text())
    existing={n:next((c for c in bpy.data.collections if c.get('business_belt40_asset_id')==n and c.get('business_belt40_version')==1),None) for n in IDS}
    requested=tuple(n for n in IDS if not existing[n])
    # Validate the actual saved library before mutating the current assembly.
    # Original-name collisions may append a collection as.001: keep the loaded
    # object mapped to the immutable requested ID, never look it up by its name.
    if requested:
        with bpy.data.libraries.load(str(unit),link=False) as (src,dst):
            missing=set(IDS)-set(src.collections);assert not missing,('Incomplete saved Belt40 library',sorted(missing))
            dst.collections=list(requested)
        loaded=dict(zip(requested,dst.collections))
    else:loaded={}
    cols={n:existing[n] or loaded[n] for n in IDS}
    for aid,c in cols.items():
        ctx.a.ASSETS[aid]=dict(collection=c,collision='complex' if aid==IDS[0] else 'none')
        for ob in c.objects:
            for m in ob.data.materials:
                if m:ctx.a.MATS[m.name]=m
    pm=json.loads((ctx.R.parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];byname={q['name']:q for q in pm['instances']};offset=ctx.D['aircraft38']['offset'];records=[]
    for i,seat in enumerate(SEATS,1):
        pos=[a+b for a,b in zip(byname[seat]['location'],offset)];control='Business belt release '+str(i)+'12'
        occupant=next((q for q in ctx.D['character_placements'] if q.get('animation')=='LuxurySeated' and math.dist(q['location'],pos)<.20),None)
        kind='Crew' if occupant and occupant['character'] in ('PassengerBusiness','PassengerCrew') else 'Generic';worn=meta['worn'][kind]
        hinge=[a+b for a,b in zip(pos,worn['hinge'])];stow=[a+b for a,b in zip(pos,meta['stowed_hinge'])]
        r=dict(seat=seat,control=control,location=pos,occupied_npc=occupant['actor'] if occupant else None,worn_kind=kind,worn_asset=IDS[2] if kind=='Crew' else IDS[3],worn_hinge=hinge,stowed_hinge=stow,initial_state=0 if occupant else 1,
               stowed_actor='B40 stowed '+seat,worn_actor='B40 worn '+seat)
        for name,aid in [(r['stowed_actor'],IDS[1]),(r['worn_actor'],r['worn_asset'])]:
            if any(q['name']==name for q in ctx.D['instances']):ctx.move(name,pos)
            else:ctx.add(aid,name,pos,collision=False,native_individual=True,business_belt40=True)
            ob=ctx.scene.objects.get(name)
            if ob:ob.instance_collection=cols[aid]
        chair=ctx.scene.objects.get(seat)
        if chair:chair.instance_collection=cols[IDS[0]]
        release=ctx.scene.objects.get(control)
        if release:release.instance_collection=cols[IDS[4]];release.location=hinge;release.rotation_euler=(0,0,0)
        for q in ctx.D['instances']:
            if q['name']==seat:q['asset']=IDS[0]
        records.append(r)
    report=dict(version=1,assets=IDS,records=records,old_static_webbing_removed=True,real_webbing_states=True)
    ctx.D.setdefault('repair38',{})['business_belt40']=report;return report


def prepare_plane(P,D):
    """After chair_runtime39/airside translations; before configure/Flight39."""
    if P.DATA.get('business_belt40_prepared'):return
    records=D['repair38']['business_belt40']['records'];byname={q['name']:q for q in P.DATA['instances']}
    for r in records:
        byname[r['seat']]['asset']=IDS[0];byname[r['control']].update(asset=IDS[4],location=r['worn_hinge'])
        q=next(q for q in P.DATA['interactions'] if q.get('actor')==r['control'])
        q.update(title='Fasten / release suite lap belt',states=['Fastened','Released / stowed'],initial_state=r['initial_state'],point=[r['worn_hinge'][0],r['worn_hinge'][1]-.004,r['worn_hinge'][2]-.02],business_belt40=r['seat'])
        q['targets']=[dict(actor=r['control'],axis='x',rotation_states=[0,-155],translation_states=[[0,0,0],[b-a for a,b in zip(r['worn_hinge'],r['stowed_hinge'])]],collision=False),dict(actor=r['worn_actor'],visible_states=[0],collision=False),dict(actor=r['stowed_actor'],visible_states=[1],collision=False)]
    P.DATA['business_belt40_prepared']=True


def apply_native(ctx):
    u=ctx.u;actors=ctx.EA.get_all_level_actors();bytag={str(t)[8:]:a for a in actors for t in a.tags if str(t).startswith('Skyward:')};bylabel={a.get_actor_label():a for a in actors};out=[]
    for r in ctx.D['repair38']['business_belt40']['records']:
        for name,aid in [(r['seat'],IDS[0]),(r['control'],IDS[4]),(r['stowed_actor'],IDS[1]),(r['worn_actor'],r['worn_asset'])]:
            actor=bytag.get(name) or bylabel.get(name);assert actor,('Business belt native actor absent',name)
            c=actor.get_component_by_class(u.StaticMeshComponent);mesh=ctx.mesh(aid);c.set_static_mesh(mesh)
            for index,slot in enumerate(mesh.static_materials):c.set_material(index,slot.material_interface)
            if name==r['control']:actor.set_actor_location(ctx.v(r['worn_hinge']),False,True);actor.set_actor_rotation(u.Rotator(),False);c.set_mobility(u.ComponentMobility.MOVABLE)
            if name in (r['stowed_actor'],r['worn_actor']):
                tags=list(actor.tags)
                for t in ('Skyward:'+name,'Airport38PlaneShift16'):
                    if not any(str(x)==t for x in tags):tags.append(u.Name(t))
                actor.tags=tags;actor.set_actor_enable_collision(False);c.set_mobility(u.ComponentMobility.MOVABLE)
                actor.set_actor_hidden_in_game((name==r['worn_actor'])!=(r['initial_state']==0))
            out.append(dict(actor=name,asset=aid))
    assert len(out)==16;return dict(status='APPLIED_REQUIRES_NATIVE_REVIEW',actors=out)


def install(G):
    """After Flight39; ordinary control targets drive the real belt states."""
    P=G.P
    if P.set_control_state is getattr(P,'_business_belt40_setter',None):return dict(already_installed=True)
    records=G.D['repair38']['business_belt40']['records'];controls={r['control']:r for r in records};seats={r['seat']:r for r in records};base=P.set_control_state;old_stand=P.stand
    def control(actor,index):
        r=controls.get(actor);seated=P.STATE.get('seated')
        if r and index%2==0 and not r['occupied_npc'] and not(seated and seated.get('actor')==r['seat']):
            G.say('Sit in this suite to fasten its lap belt');return P.STATE['controls'][actor]['state']
        return base(actor,index)
    def stand():
        old=P.STATE.get('seated');result=old_stand()
        if old and old.get('actor') in seats and not P.STATE.get('seated'):base(seats[old['actor']]['control'],1)
        return result
    P.set_control_state=control;P._business_belt40_setter=control;P.stand=stand
    return dict(controls=4,default_worn_npcs=sum(bool(r['occupied_npc']) for r in records),actual_webbing_visibility_targets=True,auto_stow_after_player_leaves=True)
