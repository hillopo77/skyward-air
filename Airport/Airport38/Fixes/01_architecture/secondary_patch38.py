"""Targeted attachment repairs on the current saved38 master, never reset37.

Root calls apply(ctx), exports only returned asset IDs, and updates the one moved
display actor. Does not save a file or start an editor. Prep guide and A08 artwork
are intentionally left to their other owners.
"""
import math

TAG='architecture_attachment_scrutiny38_v1'


def apply(ctx):
    import bpy
    a,D=ctx.a,ctx.D
    state=D.setdefault('repair38',{})
    if state.get(TAG):return state[TAG]
    for material in bpy.data.materials:
        if material.name.startswith('MI_AP_'):a.MATS[material.name[6:]]=material
    changed=[];removed=[]
    retained=bpy.data.collections['SM_AP_RetainedCraft38']
    way=bpy.data.collections['SM_AP_Wayfinding38']
    # Board geometry and lettering formerly crossed the 3.4m concourse ceiling.
    for o in list(way.objects):
        if not o.name.startswith('A08 '):continue
        if o.type=='MESH':
            lo=min(v.co.z for v in o.data.vertices);hi=max(v.co.z for v in o.data.vertices)
            h=.15 if 'navy' in o.name.lower() else .22
            for v in o.data.vertices:v.co.z=3.26+(v.co.z-(lo+hi)/2)*(h/(hi-lo))
        elif o.type=='FONT':o.location.z=3.26;o.data.size=.18
        changed.append(o.name)
    for probe in state.get('marker_probes',[]):
        if probe['id']=='A08':probe['center'][2]=3.26;probe['height']=.22
    # These two unlabelled panels were copied without any display content or
    # supports. They add blank, floating rectangles over the lounge windows.
    for o in list(retained.objects):
        if o.name.startswith('Gate timber feature supported backing35'):
            removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    # It was showing its back to check-in: the visible interface faced -X into
    # the x=-43 wall. The corrected back now meets that wall, front faces +X.
    ctx.move('Compact departures display',[-42.847,-10.2,2.2],rotation=90)
    col=ctx.new_collection('Attachments38','complex')
    def box(name,p,size,material='P38AFrame',bevel=.004):return a.box(name,p,size,material,bevel)
    def rod(name,p0,p1,r=.016):return a.tube(name,[p0,p1],r,'P38AFrame',12)
    # Real ceiling mounts for the two glass-side flight information displays.
    for id_,x,y,top,H in [('A07',-14.3,5.8,2.9386,3.4),('A08',-24.35,26.8,2.9886,3.8)]:
        for yy in (y-.65,y+.65):
            box(id_+' flight display ceiling shoe38',(x+.025,yy,H-.012),(.16,.20,.024))
            rod(id_+' load-bearing display hanger38',(x+.025,yy,top-.025),(x+.025,yy,H-.023),.014)
            box(id_+' display captured lower saddle38',(x+.025,yy,top-.006),(.10,.16,.032))
    # A07 picture clamps bolt to the existing full-height north mullion at x=-18.5.
    # They capture the actual top/bottom frame rails, not the empty picture center.
    for z in (1.52,2.68):
        box('A07 picture mullion clamp38',(-18.5,9.94,z),(.20,.08,.085))
        a.cyl('A07 picture clamp captive bolt38',(-18.5,9.899,z),.014,.015,'P38AFrame','Y')
    # The cafe menu becomes a real fitted service wall between floor and gallery
    # underside, with the original menu face retained in front of it.
    box('Cafe fitted menu support wall38',(-44.30,33.938,1.4325),(4.80,.086,2.875),'P38ANavy',.006)
    for x in (-47.50,-42.00):
        box('Cloud Nine fascia ceiling shoe38',(x,31.35,2.863),(.14,.16,.014))
        rod('Cloud Nine fascia threaded hanger38',(x,31.35,2.727),(x,31.35,2.87),.013)
        box('Cloud Nine fascia captured bracket38',(x,31.35,2.734),(.12,.15,.022))
    # The visible gallery slit was the open side of the 4.4m dining soffit under
    # the taller 6.8m roof. Close that plenum, retaining the gallery's glazing.
    # End heights fit the opaque head at the north facade instead of duplicating it.
    box('Gallery dining soffit closed lower fascia38',(-41,25.045,5.62),(.14,17.91,2.12),'P38ACeiling',.002)
    box('Gallery dining soffit closed upper fascia38',(-41,25,6.74),(.14,17.82,.12),'P38ACeiling',.002)
    # The circular clock rim had a 23mm open mounting gap to the actual new wall.
    a.cyl('Foyer clock actual backing plate38',(-44.15,-17.899,2.53),.195,.030,'P38AFrame','Y')
    # Explicit captive standoffs close the 7.5–17.5mm mounting offsets at all the
    # authored wall plaques. Each pad intersects both wood and its structural wall.
    for p in state.get('marker_probes',[]):
        if not p.get('mounted'):continue
        x,y,z=p['center'];nx,ny=p['normal'];rx,ry=-ny,nx
        us=max(.04,p['width']/2-.075);zs=max(.025,p['height']/2-.065)
        for u in (-us,us):
            for dz in (-zs,zs):
                pos=(x+rx*u-nx*.030,y+ry*u-ny*.030,z+dz)
                a.cyl(p['id']+' captive wall standoff38',pos,.015,.030,'P38AFrame','X' if nx else 'Y')
    ctx.add('SM_AP_Attachments38','Airport38 verified architectural attachments',[0,0,0],collision=True)
    # Register modified derived collections for targeted re-export. Do not restore
    # root's already-replaced preparation board or the other agent's A08 picture.
    for aid,c,collision in [('SM_AP_RetainedCraft38',retained,'complex'),('SM_AP_Wayfinding38',way,'none')]:
        a.ASSETS[aid]=dict(collection=c,collision=collision)
    result=dict(status='IMPLEMENTED_SOURCE_REQUIRES_NATIVE_REVIEW',
        asset_ids=['SM_AP_Attachments38','SM_AP_RetainedCraft38','SM_AP_Wayfinding38'],
        moved_actors=['Compact departures display'],changed_parts=changed,removed_unused_parts=removed,
        new_actor='Airport38 verified architectural attachments',
        findings=['AT02_A08_ceiling_crop','AT03_display_orientation','AT04_flight_display_supports',
                  'AT05_A07_picture_mount','AT06_menu_support','AT07_fascia_hangers',
                  'AT08_gallery_soffit_closure','AT09_clock_backplate','AT10_wall_plaque_standoffs'],
        unresolved=['AT11 shared-boundary roof-step plenum gap requires union repair',
                    'AT12 duplicated glazing mullions require union repair',
                    'AT13 gallery source contact candidates require exposure scrutiny'],
        untouched=['PreparationGuide38 owned by root','A08 rear artwork and Vanity34 owned by equipment agent'])
    state[TAG]=result
    return result
