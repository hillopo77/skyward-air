"""Native Airport38 lights and fixed warm exposure; invoked by root importer."""
import json
from pathlib import Path
from rendering38 import light_specs, ambient_specs, write_constant_hdr


def _set(obj, **values):
    for key, value in values.items():
        obj.set_editor_property(key, value)


def _indirect_cube(ctx):
    u=ctx.u;name='T_AP38_NeutralIndirect';package=ctx.B+'/Textures/'+name
    tex=u.load_asset(package)
    source=Path(__file__).resolve().parent/(name+'.hdr')
    radiance=write_constant_hdr(source)
    if tex is None:
        factory=u.TextureFactory()
        # Request the documented factory supported class. The internal HDR
        # decision cache is NOT a Python editor property in this engine build.
        # A .hdr long-lat image uses the cube import path; assert actual class
        # below rather than relying on an unavailable transient decision flag.
        _set(factory,supported_class=u.TextureCube,create_material=False)
        task=u.AssetImportTask()
        _set(task,filename=str(source),destination_path=ctx.B+'/Textures',
            destination_name=name,automated=True,save=True,replace_existing=False,factory=factory)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex=u.load_asset(package)
    if tex is None or not isinstance(tex,u.TextureCube):
        raise RuntimeError('Ambient HDR must import as TextureCube: '+package)
    _set(tex,srgb=False,never_stream=True,
        compression_settings=u.TextureCompressionSettings.TC_HDR)
    if not u.EditorAssetLibrary.save_loaded_asset(tex):
        raise RuntimeError('Cannot save Airport38 neutral indirect cubemap')
    return tex,dict(asset=package,source=str(source),**radiance)


def refine_ceiling_fill(ctx):
    """Idempotent native-only refinement: no AA, geometry or direct-key change.

    Main import calls this automatically. Root can also invoke this once against
    the saved38 map; it removes only obsolete AP38 upward pools and updates the
    existing named room grades. Root owns map saving/captures.
    """
    u,EA=ctx.u,ctx.EA
    cube,cube_report=_indirect_cube(ctx)
    removed=[];actors={a.get_actor_label():a for a in EA.get_all_level_actors()}
    for name,actor in list(actors.items()):
        if name.startswith('AP38 bounded ceiling bounce ') and isinstance(actor,u.RectLight):
            removed.append(name);EA.destroy_actor(actor)
    regions=[]
    for q in ambient_specs(ctx.D):
        actor=actors.get(q['volume_label'])
        if actor is None or not isinstance(actor,u.PostProcessVolume):
            raise RuntimeError('Missing Airport38 local room grade '+q['volume_label'])
        s=actor.get_editor_property('settings')
        _set(s,ambient_cubemap=cube,override_ambient_cubemap_intensity=True,
            ambient_cubemap_intensity=q['intensity'],override_ambient_cubemap_tint=True,
            ambient_cubemap_tint=u.LinearColor(*q['tint']))
        actor.set_editor_property('settings',s)
        # Match exactly the intended spatial grade and preserve fixed exposure.
        _set(actor,unbound=False,priority=q['priority'],blend_radius=q['blend_radius_cm'])
        regions.append(q)
    report=dict(status='APPLIED_REQUIRES_NATIVE_IMAGE_REVIEW',revision='R05b',
        removed_isolated_upward_pools=removed,indirect_cube=cube_report,regions=regions,
        direct_fixture_keys='unchanged',AA='unchanged',geometry='unchanged',
        ceiling_material='unchanged matte lit P38ACeiling, emission0',
        design='angularly constant low-strength neutral-warm indirect, bounded by camera room grades; existing AO and key shadows retain depth',
        boundary_limit='PP bounds apply to the camera/view, not per-surface world-space light clipping',
        native_acceptance='Review actual ceiling/wall luminance and contact depth; no halo or FPS success claim from code')
    out=Path(ctx.R)/'ArtBible';out.mkdir(parents=True,exist_ok=True)
    (out/'CeilingFillRefinement38.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def apply_native(ctx):
    u, EA, D = ctx.u, ctx.EA, ctx.D
    report = {'status': 'APPLYING', 'removed_lights': [], 'removed_grades': [], 'lights': []}
    # Label ownership, not position alone: aircraft, daylight and sky remain.
    for actor in list(EA.get_all_level_actors()):
        name=actor.get_actor_label()
        if isinstance(actor,(u.RectLight,u.PointLight,u.SpotLight)) and name.startswith(('AP24 ','AP25 ','AP27 ','AP33 ','AP34 ','AP35 ','AP36 ','AP37 ','AP38 ','Bridge38 warm practical ')):
            report['removed_lights'].append(name);EA.destroy_actor(actor)
        elif isinstance(actor,u.PostProcessVolume) and (name.startswith(('AP34 warm grade ','AP35 warm grade ','AP38 warm grade '))):
            report['removed_grades'].append(name);EA.destroy_actor(actor)
    actors={a.get_actor_label():a for a in EA.get_all_level_actors()}
    for q in light_specs(D):
        pitch=90 if q['direction'][2]>0 else -90
        actor=EA.spawn_actor_from_class(u.RectLight,ctx.v(q['position']),u.Rotator(pitch=pitch))
        actor.set_actor_label(q['name']);actor.set_folder_path('Airport38/Lighting/'+q['category'])
        c=actor.light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
        _set(c,intensity_units=u.LightUnits.LUMENS,source_width=q.get('width',135.),
             source_height=q.get('height',22.),attenuation_radius=q['radius_cm'],
             cast_shadows=q['casts_shadows'],specular_scale=q['specular_scale'],
             use_temperature=True,temperature=float(q['temperature']))
        c.set_intensity(float(q['lumens']));c.set_light_color(u.LinearColor(1,1,1,1))
        # KEEP_WORLD is essential: source metadata already contains deployed
        # world coordinates. Attaching with relative coordinates would apply
        # a sleeve's translation/rotation twice. Children then follow natively.
        if q.get('follow_actor'):
            parent=actors.get(q['follow_actor'])
            if parent is None:raise RuntimeError('Missing moving bridge light parent '+q['follow_actor'])
            actor.attach_to_actor(parent,u.Name('None'),u.AttachmentRule.KEEP_WORLD,
                                  u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
            report['lights'].append(dict(q,native_parent=parent.get_actor_label()))
        else:report['lights'].append(q)
    # Match the welcoming established exposure throughout the terminal.
    # Only these room-local grades override the aircraft/exterior grade.
    for z in D['zones']:
        x0,x1,y0,y1=z['rect'];H=z['ceiling_m']
        a=EA.spawn_actor_from_class(u.PostProcessVolume,ctx.v([(x0+x1)/2,(y0+y1)/2,H/2]))
        a.set_actor_label('AP38 warm grade '+z['id']);a.set_folder_path('Airport38/Lighting/FixedRoomGrade')
        # Pass45: no inset, so adjacent room volumes share their face and no
        # un-graded band remains at internal doorways. Blend widened from 12 cm
        # to 120 cm so any residual difference takes ~0.4 s at walking pace.
        a.set_actor_scale3d(u.Vector((x1-x0)/2,(y1-y0)/2,H/2))
        _set(a,unbound=False,priority=1538.,blend_radius=120.,blend_weight=1.)
        s=a.get_editor_property('settings')
        # Exposure matches the unbound exterior grade (EV 6.5), so crossing a
        # threshold changes nothing. SCREEN_SPACE bounce restored at the
        # revision 32 intensity; revision 33 set this to NONE and every pass
        # since inherited flat, gradient-free interiors.
        _set(s,override_auto_exposure_min_brightness=True,auto_exposure_min_brightness=6.5,
             override_auto_exposure_max_brightness=True,auto_exposure_max_brightness=6.5,
             override_ambient_occlusion_intensity=True,ambient_occlusion_intensity=.22,
             override_ambient_occlusion_radius=True,ambient_occlusion_radius=38.,
             override_bloom_intensity=True,bloom_intensity=.045,
             override_film_grain_intensity=True,film_grain_intensity=0.,
             override_motion_blur_amount=True,motion_blur_amount=0.,
             override_indirect_lighting_intensity=True,indirect_lighting_intensity=2.,
             override_dynamic_global_illumination_method=True,
             dynamic_global_illumination_method=u.DynamicGlobalIlluminationMethod.SCREEN_SPACE)
        a.set_editor_property('settings',s)
    # Pass45: the unbound grades carry the same fill and bounce, so the fill
    # exists everywhere and cannot pop at a camera-bound boundary. This is the
    # actual repair for the entrance white-out.
    cube=u.load_asset(ctx.B+'/Textures/T_AP38_NeutralIndirect')
    report['base_grades']=[]
    for actor in EA.get_all_level_actors():
        if not isinstance(actor,u.PostProcessVolume) or not actor.get_editor_property('unbound'):continue
        bs=actor.get_editor_property('settings')
        _set(bs,override_dynamic_global_illumination_method=True,
             dynamic_global_illumination_method=u.DynamicGlobalIlluminationMethod.SCREEN_SPACE,
             override_indirect_lighting_intensity=True,indirect_lighting_intensity=2.,
             override_auto_exposure_min_brightness=True,auto_exposure_min_brightness=6.5,
             override_auto_exposure_max_brightness=True,auto_exposure_max_brightness=6.5)
        if cube is not None:
            _set(bs,ambient_cubemap=cube,override_ambient_cubemap_intensity=True,
                 ambient_cubemap_intensity=.10,override_ambient_cubemap_tint=True,
                 ambient_cubemap_tint=u.LinearColor(1.,.98,.94,1.))
        actor.set_editor_property('settings',bs)
        report['base_grades'].append(actor.get_actor_label())
    ambient_report=refine_ceiling_fill(ctx)
    report.update(status='IMPLEMENTED_REQUIRES_NATIVE_IMAGE_REVIEW',
        practical_count=sum(q['category']!='bounded_ambient_fill' for q in report['lights']),
        bounded_fill_count=sum(q['category']=='bounded_ambient_fill' for q in report['lights']),
        indirect_room_regions=len(ambient_report['regions']),
        ambient_design=ambient_report['design'],
        shadow_casters=sum(q['casts_shadows'] for q in report['lights']),
        material_policy='P38ACeiling retained matte and non-emissive; no masking depth defects',
        performance='No FPS claim: capture-free CPU/GPU sample still required',
        reflections='SSR unchanged pending controlled native A/B')
    out=Path(ctx.R)/'ArtBible';out.mkdir(parents=True,exist_ok=True)
    (out/'NativeLighting38.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
