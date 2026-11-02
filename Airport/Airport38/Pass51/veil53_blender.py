"""Pass53: a shadow-only sun veil behind every clerestory band (headless).

Direct sun through the high windows of the four tall rooms (Hall50.json
'halls') fell as hard orange patches on the wave ceilings, the upper walls and
the floor: light with no visible source. A real hall would use diffusing glass
up there. SM_AP_P53SunVeil is one thin plane per window band, 0.15 m inside the
wall, from just under the glass to the ceiling. lights51_editor.py makes its
actor hidden in game but still casting shadow, so the sky stays visible through
the glass while direct sun stops at the band.
Usage: blender -b --factory-startup -P veil53_blender.py
"""
import bpy, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

SPEC = json.loads((HERE.parent / 'Pass50' / 'Hall50.json').read_text(encoding='utf-8'))
INSET, T = .15, .04


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = Mesh(dict(veil=('MI_AP_P38ANavy', (.02, .05, .06))))
    bands = 0
    for H in SPEC['halls']:
        x0, x1, y0, y1 = H['hall']
        for side in 'WESN':
            z0, z1 = H.get('clerestory_side', {}).get(side, H['clerestory'])
            z0, z1 = z0 - .2, H['ceiling']
            zc, h = (z0 + z1) / 2, z1 - z0
            if side == 'W':
                M.box((x0 + INSET, (y0 + y1) / 2, zc), (T, y1 - y0, h), 'veil')
            elif side == 'E':
                M.box((x1 - INSET, (y0 + y1) / 2, zc), (T, y1 - y0, h), 'veil')
            elif side == 'S':
                M.box(((x0 + x1) / 2, y0 + INSET, zc), (x1 - x0, T, h), 'veil')
            else:
                M.box(((x0 + x1) / 2, y1 - INSET, zc), (x1 - x0, T, h), 'veil')
            bands += 1
    obj = M.finish('SM_AP_P53SunVeil')
    out = HERE / 'VeilBuild'; out.mkdir(exist_ok=True)
    fbx = out / 'SM_AP_P53SunVeil.fbx'
    export(obj, fbx)
    rep = dict(status='SUCCESS', asset=obj.name, fbx=str(fbx.resolve()), materials=['MI_AP_P38ANavy'],
               polygons=len(obj.data.polygons), bands=bands)
    (HERE / 'Veil53Build.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print('VEIL53', bands)


main()
