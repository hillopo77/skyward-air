"""Pass45 lighting repair, native-only, applied to the saved Airport38 map.

Diagnosis this implements (see FINDINGS_LIGHTING.md):

  The interior's entire fill light is an ambient cubemap carried by a
  camera-bound post-process volume. Every practical is a RectLight pitched
  straight down, so the ceiling receives almost no direct light and is lit
  only by that camera-bound term. Crossing the volume face the fill appears
  or vanishes in 12 cm, which is the white-out, and the version without it
  is the "horror lighting" the user rejected earlier.

  Separately, revision 32 ran the room grades with SCREEN_SPACE global
  illumination at indirect intensity 2.0. Revision 33 set them to NONE while
  raising the skylight from 8 to 36, and 34/35/38 kept NONE. That removed all
  bounce, which is why large surfaces read as unshaded blockout however much
  panel detail is added.

Repair, in order of importance:

  1. Put the SAME ambient cubemap on the unbound grades at the same intensity
     the rooms use. The fill then exists everywhere and cannot pop at a
     boundary. This is the actual fix for the white-out.
  2. Restore SCREEN_SPACE GI with indirect intensity 2.0 everywhere, as
     revision 32 had it. Lumen is unavailable (D3D11/SM5), SSGI is already
     configured in DefaultEngine.ini, and it is what gives surfaces gradient.
  3. Match interior exposure to exterior (both EV 6.5) so no exposure step
     remains at any threshold.
  4. Widen blend_radius from 12 cm to 120 cm so any residual difference takes
     about 0.4 s at walking pace instead of 40 ms.
  5. Remove the 2 cm per-side inset so adjacent room volumes share their face,
     eliminating the no-volume band at every internal doorway.

Reversible: the .umap is backed up by the launcher before this runs, and
every value changed is recorded in the report.
"""
import unreal as u, json, time, traceback
from pathlib import Path

R = Path(__file__).resolve().parents[1]
B = '/Game/Airport38'
MAP = B + '/L_Airport_Repair38'
CUBE = B + '/Textures/T_AP38_NeutralIndirect'

AMBIENT_INTENSITY = 0.10
AMBIENT_TINT = (1.0, 0.98, 0.94, 1.0)
INDIRECT_INTENSITY = 2.0
EXPOSURE_EV = 6.5
BLEND_RADIUS_CM = 120.0

report = dict(status='RUNNING', started=time.time(), changed=[], notes=[])


def flush():
    out = R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'LightFix45.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def read(s, name):
    try:
        return s.get_editor_property(name)
    except Exception:
        return None


try:
    D = json.loads((R / 'Exports/airport_layout.json').read_text(encoding='utf-8'))
    zones = {z['id']: z for z in D['zones']}

    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)

    cube = u.load_asset(CUBE)
    if cube is None:
        report['notes'].append('ambient cubemap missing at ' + CUBE)

    volumes = [a for a in EA.get_all_level_actors()
               if isinstance(a, u.PostProcessVolume)]
    report['volumes_found'] = len(volumes)

    for a in volumes:
        label = a.get_actor_label()
        s = a.get_editor_property('settings')
        before = dict(
            unbound=bool(a.get_editor_property('unbound')),
            priority=float(a.get_editor_property('priority')),
            blend_radius=float(a.get_editor_property('blend_radius')),
            exposure_min=read(s, 'auto_exposure_min_brightness'),
            exposure_max=read(s, 'auto_exposure_max_brightness'),
            gi_method=str(read(s, 'dynamic_global_illumination_method')),
            ambient_cubemap_intensity=read(s, 'ambient_cubemap_intensity'),
            indirect_lighting_intensity=read(s, 'indirect_lighting_intensity'),
        )
        after = {}
        is_room = label.startswith('AP38 warm grade ')
        is_base = label in ('Airport clean daylight grade', 'PostProcessVolume')

        if not (is_room or is_base):
            continue

        # 2. real bounce everywhere, as revision 32 had it
        prop(s, override_dynamic_global_illumination_method=True,
             dynamic_global_illumination_method=u.DynamicGlobalIlluminationMethod.SCREEN_SPACE,
             override_indirect_lighting_intensity=True,
             indirect_lighting_intensity=INDIRECT_INTENSITY)
        after['gi_method'] = 'SCREEN_SPACE'
        after['indirect_lighting_intensity'] = INDIRECT_INTENSITY

        # 1. the fill exists everywhere, so it cannot pop at a boundary
        if cube is not None:
            prop(s, ambient_cubemap=cube,
                 override_ambient_cubemap_intensity=True,
                 ambient_cubemap_intensity=AMBIENT_INTENSITY,
                 override_ambient_cubemap_tint=True,
                 ambient_cubemap_tint=u.LinearColor(*AMBIENT_TINT))
            after['ambient_cubemap_intensity'] = AMBIENT_INTENSITY

        # 3. one exposure value across the whole level
        prop(s, override_auto_exposure_min_brightness=True,
             auto_exposure_min_brightness=EXPOSURE_EV,
             override_auto_exposure_max_brightness=True,
             auto_exposure_max_brightness=EXPOSURE_EV)
        after['exposure_min'] = EXPOSURE_EV
        after['exposure_max'] = EXPOSURE_EV

        a.set_editor_property('settings', s)

        if is_room:
            # 4. a transition a walking player can absorb
            prop(a, blend_radius=BLEND_RADIUS_CM)
            after['blend_radius'] = BLEND_RADIUS_CM
            # 5. volumes meet instead of leaving a dead band at every doorway
            zid = label[len('AP38 warm grade '):]
            z = zones.get(zid)
            if z:
                x0, x1, y0, y1 = z['rect']
                H = z['ceiling_m']
                a.set_actor_scale3d(u.Vector((x1 - x0) / 2.0, (y1 - y0) / 2.0, H / 2.0))
                after['inset_removed'] = True
                after['scale'] = [(x1 - x0) / 2.0, (y1 - y0) / 2.0, H / 2.0]

        report['changed'].append(dict(label=label, before=before, after=after))

    assert u.EditorLoadingAndSavingUtils.save_map(
        u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(), MAP), 'save failed'

    report.update(status='SUCCESS', map=MAP, finished=time.time(),
                  summary=dict(rooms=sum(1 for c in report['changed']
                                         if c['label'].startswith('AP38 warm grade ')),
                               base=sum(1 for c in report['changed']
                                        if not c['label'].startswith('AP38 warm grade ')),
                               ambient_intensity=AMBIENT_INTENSITY,
                               indirect_intensity=INDIRECT_INTENSITY,
                               exposure_ev=EXPOSURE_EV,
                               blend_radius_cm=BLEND_RADIUS_CM))
    flush()
    print('LIGHT45 SUCCESS', flush=True)
except Exception:
    report.update(status='FAILED', error=traceback.format_exc())
    flush()
    raise
