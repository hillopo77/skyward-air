"""Derived Window40 upper-view/hidden-mechanism correction; no shared edits.

The pressure aperture/glass and all48 shade strokes stay unchanged. Six local
kits and one complete, repeat-safe bin/side-PSU mount translation are authored.
"""
import math,json,copy
from pathlib import Path
import window40 as W
F=Path(__file__).parent
LIFT=.150
SHADE_FIT=.008
SWAPS={
 'SM_AP_W40WindowWallL':'SM_AP_W41WindowWallL',
 'SM_AP_W40WindowWallR':'SM_AP_W41WindowWallR',
 'SM_AP_W40ShadeFrameL':'SM_AP_W41ShadeFrameL',
 'SM_AP_W40ShadeFrameR':'SM_AP_W41ShadeFrameR',
 'SM_AP_W40RackL':'SM_AP_W41RackL',
 'SM_AP_W40RackR':'SM_AP_W41RackR',
}


def cover_x(z):return 2.326-.226*W.smooth((z-1.4)/.6)


def _wall(ctx,c,side):
    a=ctx.a;a.ACTIVE=c
    W._remove(c,('W40 continuous pressure-fitted cabin liner','W40 continuous rolled rounded window reveal'))
    # Preserve the central roof junction while forming a real equipment cove
    # above the raised bucket. Every edited shoulder vertex remains inside skin.
    for ob in c.objects:
        if ob.type!='MESH' or not ob.name.startswith('Continuous acoustic ceiling shoulder09'):continue
        T=W._matrix(ob);inv=T.inverted()
        for v in ob.data.vertices:
            p=T@v.co;t=max(0,min(1,(abs(p.x)-1.10)/(2.26-1.10)))
            p.z+=.140*math.sin(math.pi*t)**1.4
            assert abs(p.x)<W.pressure_x(p.z)-.02,(p,W.pressure_x(p.z))
            v.co=inv@p
        ob.data.update()
    path=W._loop(.96,1.28,.24,1.46);rings=[]
    for t in (0,.12,.30,.52,.76,1.):
        row=[]
        for y,z,angle in path:
            dz=z-1.46;scale=min(.675/max(abs(y),1e-9),((2.1923077-1.46) if dz>=0 else 1.46-.2)/max(abs(dz),1e-9));yy=y*(1+(scale-1)*t);zz=1.46+dz*(1+(scale-1)*t)
            row.append((side*(W.pressure_x(zz)-.065),yy,zz))
        rings.append(row)
    W._ringmesh(a,'W41 continuous fitted liner with formed mechanism recess',rings,'W40Liner',-side)
    # A broad molded shoulder, with progressively changing depth, avoids the
    # previous10mm-wide,100mm-deep knife crease reading as exposed guide rods.
    # The inner opening and pressure aperture remain exactly unchanged.
    specs=[(.96,1.28,.24,'root'),(.948,1.272,.236,'roll15'),(.925,1.25,.230,'roll50'),(.889,1.218,.216,'roll86'),(.86,1.19,.207,'front'),(.69,1.11,.175,'front'),(.68,1.10,.170,'inner'),(.704,1.004,.161,'flare'),(.700,1.,.16,'edge')]
    rings=[]
    for width,height,radius,role in specs:
        row=[]
        for y,z,_ in W._loop(width,height,radius,1.46):
            root_x=W.pressure_x(z)-.065
            x=root_x if role=='root' else root_x+(cover_x(z)-root_x)*int(role[4:])/100 if role.startswith('roll') else cover_x(z)+.004 if role=='inner' else cover_x(z) if role=='front' else (cover_x(z)+W.pressure_x(z)-.016)*.5 if role=='flare' else W.pressure_x(z)-.008
            row.append((side*x,y,z))
        rings.append(row)
    W._ringmesh(a,'W41 continuous rolled collar shields actual guide channels',rings,'W40Reveal',-side)
    return dict(complete_pressure_aperture_unchanged=[.70,1.],mechanisms_behind_broad_continuous_collar=True,roof_cove_lift_max=.140,central_roof_junction_unchanged=True)


def _frame(ctx,c,side):
    a=ctx.a;a.ACTIVE=c;W._remove(c,('W40 integrated captive shade side channel',))
    def local(x,y,z):return (side*(x-2.3),y,z-.92)
    zvals=[.905,1.30,1.4,1.45,1.55,1.65,1.70,1.76,1.82,1.90,1.975,2.045,2.12,2.20,2.28,2.325]
    for edge in (-1,1):
        rows=[]
        for z in zvals:
            inner=max(2.328 if z<=1.70 else 2.105,W.track_x(z)-.008);outer=min(W.pressure_x(z)-.012,W.track_x(z-.255)+.042);inner=min(inner,outer-.024)
            cross=[(outer,.348),(outer,.398),(inner,.398),(inner,.348),(inner+.005,.348),(inner+.005,.387),(outer-.005,.387),(outer-.005,.348)]
            rows.append([local(x,edge*y,z) for x,y in cross])
        ob=a.loft('W41 captive guide seated behind rolled collar',rows,'W40Pearl',True,True);b=ob.modifiers.new('Small guide edge roll','BEVEL');b.width=.0004;b.segments=3
        # A formed open-backed corner shield, not a solid block in the moving
        # leaf path. Its front is inboard of every stow position; the upper end
        # nests behind the existing cassette mouth.
        vertices=[];levels=[1.91,1.94,1.97,2.,2.025,2.055]
        for z in levels:
            dz=max(0,z-(1.46+1.11/2-.175));boundary=.69/2-.175+math.sqrt(max(0,.175**2-dz**2))
            y0=min(.34,boundary+.009)
            vertices.extend([local(cover_x(z)-.004,edge*y0,z),local(cover_x(z)-.004,edge*.423,z)])
        faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(levels)-1)]
        ob=a.mesh('W41 thin formed upper-corner mechanism shield',vertices,faces,'W40Pearl');solid=ob.modifiers.new('Actual formed shield thickness','SOLIDIFY');solid.thickness=.002;solid.offset=0
    return dict(stroke_geometry_unchanged=True,lower_guide_min_absx=2.328,upper_covers_open_behind=True,controller_face_and_mount_unchanged=True)


def build_units(ctx):
    import bpy
    a=ctx.a;W._aliases(a);active=a.ACTIVE;report=dict(assets=list(SWAPS.values()),details={})
    for old,new in SWAPS.items():
        src=bpy.data.collections.get(old);assert src,old
        c=bpy.data.collections.new(new)
        for ob in src.objects:
            q=ob.copy();q.data=ob.data.copy();c.objects.link(q)
        side=-1 if new.endswith('L') else 1
        if 'WindowWall' in new:detail=_wall(ctx,c,side)
        elif 'ShadeFrame' in new:detail=_frame(ctx,c,side)
        else:
            for ob in c.objects:
                T=W._matrix(ob);inv=T.inverted()
                for v in ob.data.vertices:
                    p=T@v.co;p.z+=LIFT;assert abs(p.x)<W.pressure_x(p.z)-.02,(ob.name,p);v.co=inv@p
                ob.data.update()
            detail=dict(complete_fixed_bucket_and_hinges_lift_m=LIFT,dimensions_unchanged=True)
        c['window41']=True;c['window41_details']=json.dumps(detail);a.ASSETS[new]=dict(collection=c,collision='complex');report['details'][new]=detail
    a.ACTIVE=active;return report


def moving_names(pm):
    names=set()
    for q in pm['instances']:
        if q['asset'].startswith('SM_Plane_OverheadBinDoor10_') or (q['name'].startswith(('Passenger service unit ','PSU ')) and abs(q['location'][0])>1.):names.add(q['name'])
    return names

def shade_names(pm):return {q['name'] for q in pm['instances'] if q['asset'].startswith(('SM_Plane_WindowShadeHandle18_','SM_Plane_WindowShadeSlat18_'))}


def apply(ctx):
    import bpy
    needed=[n for n in SWAPS.values() if not bpy.data.collections.get(n)]
    if needed:
        with bpy.data.libraries.load(str(F/'Window41_UnitKits.blend'),link=False) as (src,dst):dst.collections=list(needed)
    for old,new in SWAPS.items():
        c=bpy.data.collections[new];ctx.a.ASSETS[new]=dict(collection=c,collision='complex')
        for ob in c.objects:
            for mat in ob.data.materials:
                if mat:ctx.a.MATS[mat.name]=mat
        for ob in ctx.scene.objects:
            if ob.instance_type=='COLLECTION' and ob.instance_collection and ob.instance_collection.name==old:ob.instance_collection=c
        for q in ctx.D.get('instances',[]):
            if q['asset']==old:q['asset']=new
    pm=json.loads((ctx.R.parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];names=moving_names(pm);shades=shade_names(pm);lifted=[]
    for ob in ctx.scene.objects:
        if ob.name in names or (ob.type=='LIGHT' and ob.name.startswith('PSU ') and abs(ob.location.x-ctx.D['aircraft38']['offset'][0])>1.) or (ob.type=='CAMERA' and 'PSUDetail' in ob.name):
            if not ob.get('window41_lifted'):ob.location.z+=LIFT;ob['window41_lifted']=True
            lifted.append(ob.name)
        if ob.name in shades and not ob.get('window41_shade_fitted'):
            side=-1 if ' L18' in ob.name else 1;ob.location.x+=side*SHADE_FIT;ob['window41_shade_fitted']=True
    report=dict(version=1,assets=list(SWAPS.values()),lift_m=LIFT,shade_fit_m=SHADE_FIT,moving_actor_names=sorted(names),shade_actor_names=sorted(shades),source_lifted=lifted,full_clear_pressure_aperture=[.70,1.],stow_vectors_unchanged=True)
    ctx.D.setdefault('repair38',{})['window41']=report;return report


def prepare_plane(P,D):
    """After Window40 prepare, before Flight39/configure; dimensions/deltas stay."""
    data=P.DATA
    if data.get('window41_prepared'):return
    # Names come from original local source positions before the+16m parked
    # translation, so centralPSUs can never be mistaken for side assemblies.
    names=set(D['repair38']['window41']['moving_actor_names']);offset=D['aircraft38']['offset'][0]
    for q in data['instances']:
        if q['asset'] in SWAPS:q['asset']=SWAPS[q['asset']]
        # DATA still names the original plane families, unlike the current
        # airport master. Bind by original family through Window40's map too.
        mapped=W.SWAPS.get(q['asset'])
        if mapped in SWAPS:q['asset']=SWAPS[mapped]
        if q['name'] in names:q['location'][2]+=LIFT
    for q in data.get('interactions',[]):
        if q['actor'] in names:
            for key in ('point','location'):
                if key in q:q[key][2]+=LIFT
        if q.get('window40'):
            q['window41']=True
            for p in q['roller_parts']:p['closed_location'][0]+=p['window40_side']*SHADE_FIT
    for q in data.get('lights',[]):
        if q['name'].startswith('PSU ') and abs(q['location'][0]-offset)>1.:q['location'][2]+=LIFT
    for q in data.get('labels',[]):
        if q.get('parent') in names:q['location'][2]+=LIFT
    for q in data.get('cameras',[]):
        if 'PSUDetail' in q['name']:q['location'][2]+=LIFT
    data['window41_prepared']=dict(complete_side_psu_and_bin_moving_actors=len(names),lift_m=LIFT,stand_approaches_unchanged=True,shade_stroke_vectors_unchanged=True,parallel_shade_fit_m=SHADE_FIT)


def install(G):
    """After Window40/Flight39 installers; same retained curve,8mm fitting."""
    P=G.P
    if P._apply_movable is getattr(P,'_window41_adapter',None):return dict(already_installed=True)
    base=P._apply_movable
    def apply_movable(m):
        q=m['item']
        if not q.get('window41'):return base(m)
        frame=getattr(G,'flight39',{}).get('frame')
        for part in q['roller_parts']:
            p=W.shade_pose(part,m['progress']);p[0]+=part['window40_side']*SHADE_FIT;position=P.vector(p)
            P.STATE['actors'][part['actor']].set_actor_location(frame.world(position) if frame else position,False,False)
    P._apply_movable=apply_movable;P._window41_adapter=apply_movable
    for m in P.STATE['movables'].values():
        if m['item'].get('window41'):apply_movable(m)
    return dict(mechanisms=48,parallel_fit_m=SHADE_FIT,carrier_aware=True)


def apply_native(ctx):
    u=ctx.u;pm=json.loads((Path(ctx.R).parent.parent/'SkywardAir/Revision18/Exports/manifest.json').read_text())['scenes']['L_Plane_Reference'];targets={q['name']:SWAPS[W.SWAPS[q['asset']]] for q in pm['instances'] if W.SWAPS.get(q['asset']) in SWAPS};names=moving_names(pm);shades=shade_names(pm);changed=[];lifted=[]
    actors=list(ctx.EA.get_all_level_actors());original_positions={a.get_path_name():a.get_actor_location() for a in actors}
    for actor in actors:
        key=next((str(t)[8:] for t in actor.tags if str(t).startswith('Skyward:')),None)
        if key in targets:
            c=actor.get_component_by_class(u.StaticMeshComponent);mesh=ctx.mesh(targets[key]);c.set_static_mesh(mesh)
            for i,slot in enumerate(mesh.static_materials):c.set_material(i,slot.material_interface)
            changed.append(key)
        light=any(str(t).startswith('SkywardLight:PSU ') for t in actor.tags) and abs(actor.get_actor_location().x/100-ctx.D['aircraft38']['offset'][0])>1.
        camera=any('SkywardCamera:CAM_Plane_PSUDetail' in str(t) for t in actor.tags)
        if key in names or light or camera:
            if not any(str(t)=='Window41Lift150' for t in actor.tags):
                p=original_positions[actor.get_path_name()];actor.set_actor_location(p+u.Vector(0,0,LIFT*100),False,True);actor.tags=list(actor.tags)+[u.Name('Window41Lift150')]
            lifted.append(actor.get_actor_label())
        if key in shades and not any(str(t)=='Window41Shade8' for t in actor.tags):
            side=-1 if ' L18' in key else 1;actor.set_actor_location(original_positions[actor.get_path_name()]+u.Vector(side*SHADE_FIT*100,0,0),False,True);actor.tags=list(actor.tags)+[u.Name('Window41Shade8')]
    assert len(changed)==len(targets),(len(changed),len(targets));return dict(status='APPLIED_REQUIRES_NATIVE_REVIEW',swaps=len(changed),complete_assembly_lifted=lifted)
