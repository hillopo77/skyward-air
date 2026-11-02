"""Pass45 lighting repair, revision B: keep the look, drop the cost.

Revision A restored SCREEN_SPACE bounce at the revision-32 intensity. It fixed
the white-out and gave surfaces real gradient, but it cost too much on this
laptop: mean median frame time went 16.87 ms (59.3 fps) to 28.53 ms (35.1 fps),
with Check-in at 44.50 ms (22.5 fps). That is not shippable here.

The two gains came from different changes, and only one of them was expensive:

  - the white-out fix is the ambient fill existing on the UNBOUND grades as
    well as the room grades, so it cannot pop at a camera-bound boundary.
    That costs nothing.
  - the gradient came from SSGI, which costs a great deal.

This revision keeps the free half and replaces the expensive half. The reason
the old fill produced no gradient was not that it was an ambient cubemap; it
was that `write_constant_hdr` emitted a single constant value in every
direction, with its own report recording `angular_variance: 0`. An ambient
cubemap with real angular variation gives directional shading for free,
because it is sampled per-normal by the existing lit pipeline.

So: a vertical gradient cubemap, brighter above (ceiling and window bounce),
dimmer at the horizon, warm and moderate below (floor bounce). Surfaces facing
up, sideways and down now receive different light, which is what produces
form. Cost is identical to the constant cubemap: one texture fetch.

SCREEN_SPACE GI is reverted to NONE. The gradient cubemap is applied to every
grade, room and unbound alike, so the boundary pop stays fixed.
"""
import unreal as u, json, math, time, traceback
from pathlib import Path

R = Path(__file__).resolve().parents[1]
B = '/Game/Airport38'
MAP = B + '/L_Airport_Repair38'
TEX_NAME = 'T_AP45_GradientIndirect'
TEX_PATH = B + '/Textures/' + TEX_NAME

AMBIENT_INTENSITY = 0.26
AMBIENT_TINT = (1.0, 0.98, 0.94, 1.0)
EXPOSURE_EV = 6.5
BLEND_RADIUS_CM = 120.0

# Lat-long gradient stops, top of sphere to bottom. Linear radiance.
UP = (1.00, 0.99, 0.96)
HORIZON = (0.72, 0.71, 0.70)
DOWN = (0.62, 0.56, 0.48)

report = dict(status='RUNNING', started=time.time(), changed=[], notes=[])


def flush():
    out = R / 'Pass45'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'LightFix45b.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def prop(o, **kw):
    for k, v in kw.items():
        o.set_editor_property(k, v)


def write_gradient_hdr(path, width=64, height=32):
    """Radiance RGBE lat-long with a real vertical gradient.

    Each row is a constant colour, so the existing per-row RLE encoding is
    exact. Row 0 is the top of the sphere. Returns the sampled stops and the
    measured angular variance, which must not be zero.
    """
    def lerp(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    rows = []
    for j in range(height):
        # theta 0 at top, pi at bottom
        t = (j + 0.5) / height
        if t < 0.5:
            c = lerp(UP, HORIZON, (t / 0.5) ** 0.85)
        else:
            c = lerp(HORIZON, DOWN, ((t - 0.5) / 0.5) ** 1.15)
        rows.append(c)

    data = bytearray(('#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n'
                      % (height, width)).encode('ascii'))
    for c in rows:
        largest = max(c)
        if largest < 1e-32:
            rgbe = [0, 0, 0, 0]
        else:
            mantissa, exponent = math.frexp(largest)
            rgbe = [min(255, int(v * mantissa * 256 / largest)) for v in c] + [exponent + 128]
        data.extend(bytes([2, 2, width >> 8, width & 255]))
        for ch in rgbe:
            data.extend(bytes([128 + width, ch]))
    Path(path).write_bytes(data)

    lum = [0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in rows]
    mean = sum(lum) / len(lum)
    var = sum((q - mean) ** 2 for q in lum) / len(lum)
    return dict(width=width, height=height, up=list(UP), horizon=list(HORIZON),
                down=list(DOWN), bytes=len(data),
                luminance_min=round(min(lum), 4), luminance_max=round(max(lum), 4),
                angular_variance=round(var, 6))


try:
    D = json.loads((R / 'Exports/airport_layout.json').read_text(encoding='utf-8'))
    zones = {z['id']: z for z in D['zones']}

    src = R / 'Pass45' / (TEX_NAME + '.hdr')
    report['gradient'] = write_gradient_hdr(src)
    assert report['gradient']['angular_variance'] > 0, 'gradient must vary'

    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)

    tex = u.load_asset(TEX_PATH)
    factory = u.TextureFactory()
    prop(factory, supported_class=u.TextureCube, create_material=False)
    task = u.AssetImportTask()
    prop(task, filename=str(src), destination_path=B + '/Textures',
         destination_name=TEX_NAME, automated=True, save=True,
         replace_existing=True, factory=factory)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = u.load_asset(TEX_PATH)
    if tex is None or not isinstance(tex, u.TextureCube):
        raise RuntimeError('gradient HDR must import as TextureCube: ' + TEX_PATH)
    prop(tex, srgb=False, never_stream=True,
         compression_settings=u.TextureCompressionSettings.TC_HDR)
    assert u.EditorAssetLibrary.save_loaded_asset(tex), 'cannot save gradient cubemap'
    report['texture'] = TEX_PATH

    for a in EA.get_all_level_actors():
        if not isinstance(a, u.PostProcessVolume):
            continue
        label = a.get_actor_label()
        is_room = label.startswith('AP38 warm grade ')
        is_base = bool(a.get_editor_property('unbound'))
        if not (is_room or is_base):
            continue
        s = a.get_editor_property('settings')

        # Revert the expensive half.
        prop(s, override_dynamic_global_illumination_method=True,
             dynamic_global_illumination_method=u.DynamicGlobalIlluminationMethod.NONE,
             override_indirect_lighting_intensity=False)

        # Keep the free half, now with real angular variation.
        prop(s, ambient_cubemap=tex,
             override_ambient_cubemap_intensity=True,
             ambient_cubemap_intensity=AMBIENT_INTENSITY,
             override_ambient_cubemap_tint=True,
             ambient_cubemap_tint=u.LinearColor(*AMBIENT_TINT),
             override_auto_exposure_min_brightness=True,
             auto_exposure_min_brightness=EXPOSURE_EV,
             override_auto_exposure_max_brightness=True,
             auto_exposure_max_brightness=EXPOSURE_EV)
        a.set_editor_property('settings', s)

        if is_room:
            prop(a, blend_radius=BLEND_RADIUS_CM)
            zid = label[len('AP38 warm grade '):]
            z = zones.get(zid)
            if z:
                x0, x1, y0, y1 = z['rect']
                a.set_actor_scale3d(u.Vector((x1 - x0) / 2.0, (y1 - y0) / 2.0, z['ceiling_m'] / 2.0))
        report['changed'].append(label)

    assert u.EditorLoadingAndSavingUtils.save_map(
        u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(), MAP), 'save failed'

    report.update(status='SUCCESS', map=MAP, finished=time.time(),
                  summary=dict(volumes=len(report['changed']),
                               gi='NONE (SSGI reverted for cost)',
                               ambient_intensity=AMBIENT_INTENSITY,
                               exposure_ev=EXPOSURE_EV,
                               blend_radius_cm=BLEND_RADIUS_CM))
    flush()
    print('LIGHT45B SUCCESS', flush=True)
except Exception:
    report.update(status='FAILED', error=traceback.format_exc())
    flush()
    raise
