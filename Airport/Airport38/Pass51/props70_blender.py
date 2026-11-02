"""Pass70: a new fire extinguisher, its stand, and a kids' play plane (headless).

Player feedback: redesign every fire extinguisher and the thing that holds it
(some faced the wall); the A08 play corner's "plane" read as a big green
cylinder. Each mesh is modelled at the origin, base centre at (0, 0, 0), in
metres. FRONT IS -Y (Blender), the face that must look into the room; the
editor step (props70_editor.py) turns each one away from its wall.

  SM_AP_P70Extinguisher   a 6 kg powder extinguisher, 0.56 m: rounded red body,
                          cream label band, black valve head, steel lever and
                          carry handle, a gauge facing front, black hose down the
                          right side to a nozzle clipped at the hip
  SM_AP_P70ExtStand       its floor stand: dark tray, cream backboard with a red
                          border, a steel strap at the extinguisher's waist and a
                          red FIRE sign on top with a white flame mark
  SM_AP_P70PlayPlane      a sit-on play plane, 1.9 m long, 1.6 m span, 0.95 m
                          tall: rounded teal fuselage, cream belly band and nose
                          cone, a gold propeller, cream wings with teal tips and a
                          gold stripe, tail fin and stabiliser, navy windscreen,
                          round portholes, chunky black wheels, an oak step
Usage: blender -b --factory-startup -P props70_blender.py
"""
import bpy, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'Pass48'))
from mesh48 import Mesh, export

MATS = dict(red=('MI_AP_Red', (.7, .05, .04)), cream=('MI_AP_P34Cream', (.8, .75, .6)), black=('MI_AP_P36Black', (.03, .03, .03)),
            steel=('MI_AP_P27Steel', (.5, .52, .54)), rubber=('MI_AP_Rubber', (.05, .05, .05)), white=('MI_AP_WhiteMark', (.9, .9, .9)),
            teal=('MI_AP_P27Teal', (.05, .3, .3)), gold=('MI_AP_P38AGold', (.72, .48, .11)), navy=('MI_AP_P38ANavy', (.02, .05, .06)),
            oak=('MI_AP_P43TOak', (.5, .31, .15)))


def extinguisher(M, z0=0.0):
    r = .075
    M.cylinder((0, 0, z0 + .016), r + .004, .032, 'rubber', seg=24)                       # foot ring
    M.cylinder((0, 0, z0 + .23), r, .40, 'red', seg=28)                                   # body
    M.blob((0, 0, z0 + .43), r, 'red', squash=.62, subdiv=2)                              # domed shoulder
    M.cylinder((0, 0, z0 + .235), r + .0012, .13, 'cream', seg=28, cap_top=False, cap_bottom=False)   # label band
    M.box((0, -(r + .002), z0 + .262), (.07, .004, .018), 'red')                         # label: red bar
    M.box((0, -(r + .002), z0 + .232), (.08, .004, .008), 'black')                        # label: text lines
    M.box((0, -(r + .002), z0 + .214), (.06, .004, .006), 'black')
    M.cylinder((0, 0, z0 + .49), .022, .05, 'steel', seg=16)                              # neck
    M.box((0, 0, z0 + .53), (.05, .07, .045), 'black')                                    # valve head
    M.cylinder((0, -.05, z0 + .53), .018, .006, 'white', seg=18, axis='y')               # gauge face (front)
    M.cylinder((0, -.047, z0 + .53), .021, .006, 'steel', seg=18, axis='y')              # gauge rim
    M.box((0, .02, z0 + .575), (.03, .15, .012), 'steel', rot=0.0)                        # squeeze lever
    M.box((0, .03, z0 + .555), (.026, .13, .01), 'steel')                                 # carry handle
    M.cylinder((0, -.012, z0 + .59), .006, .03, 'red', seg=8)                             # safety pin tag
    M.box((.045, 0, z0 + .51), (.05, .018, .018), 'black')                                # hose leaves the valve sideways
    for zz in (.44, .34, .25):                                                            # and runs down the right side
        M.cylinder((.088, 0, z0 + zz), .009, .1, 'black', seg=10)
    M.cylinder((.088, 0, z0 + .17), .013, .06, 'black', seg=10)                           # nozzle
    M.box((.08, 0, z0 + .2), (.012, .03, .03), 'steel')                                   # nozzle clip


def stand(M):
    M.box((0, 0, .02), (.32, .28, .04), 'black')                                         # tray
    M.box((0, .14, .02), (.32, .02, .07), 'black')                                       # tray lip (back)
    M.box((0, .155, .62), (.34, .025, 1.16), 'cream')                                    # backboard
    for x in (-.165, .165):
        M.box((x, .145, .62), (.012, .01, 1.16), 'red')                                  # red border sides
    M.box((0, .145, .045), (.34, .01, .012), 'red'); M.box((0, .145, 1.195), (.34, .01, .012), 'red')
    M.box((0, .07, .33), (.18, .01, .025), 'steel')                                      # strap round the waist
    M.box((-.09, .11, .33), (.012, .08, .025), 'steel'); M.box((.09, .11, .33), (.012, .08, .025), 'steel')
    M.box((0, .14, 1.33), (.34, .02, .22), 'red')                                        # FIRE sign
    M.box((0, .128, 1.34), (.05, .004, .09), 'white')                                    # flame mark: a white tongue
    M.box((-.02, .128, 1.315), (.03, .004, .05), 'white'); M.box((.022, .128, 1.32), (.026, .004, .06), 'white')
    M.box((0, .128, 1.262), (.24, .004, .016), 'white')                                  # underline


def play_plane(M):
    L, R0, Z = 1.9, .32, .55                                                              # length, fuselage radius, axis height
    M.cylinder((0, .05, Z), R0, 1.1, 'teal', seg=40, axis='y')                            # fuselage
    M.blob((0, -.5, Z), R0, 'teal', squash=1.0, subdiv=3)                                 # rounded nose behind the cone
    M.cylinder((0, -.6, Z), R0 * .9, .1, 'cream', seg=40, axis='y')                       # cream nose ring
    M.blob((0, -.7, Z), R0 * .66, 'cream', squash=1.0, subdiv=3)                          # nose cone
    M.cylinder((0, -.93, Z), .05, .06, 'gold', seg=16, axis='y')                          # spinner
    M.box((0, -.965, Z), (.06, .025, .62), 'gold'); M.box((0, -.965, Z), (.62, .025, .06), 'gold')   # propeller
    M.cylinder((0, .66, Z + .04), R0 * .78, .3, 'teal', seg=28, axis='y')                 # tail taper
    M.blob((0, .84, Z + .07), R0 * .58, 'teal', squash=1.0, subdiv=2)
    M.box((0, .86, Z + .43), (.05, .32, .46), 'teal')                                     # fin
    M.box((0, .86, Z + .55), (.055, .3, .07), 'gold')                                     # fin stripe
    M.box((0, .88, Z + .12), (.78, .22, .04), 'cream')                                    # tailplane
    M.cylinder((0, .05, Z - .02), R0 + .004, .5, 'cream', seg=32, axis='y', cap_top=False, cap_bottom=False)   # belly band
    for sx in (-1, 1):                                                                    # wings
        M.box((sx * .55, -.12, Z - .12), (.62, .46, .06), 'cream')
        M.box((sx * .88, -.12, Z - .12), (.08, .47, .065), 'teal')                        # tips
        M.box((sx * .5, -.12, Z - .085), (.4, .06, .012), 'gold')                         # stripe
        M.cylinder((sx * .2, -.32, .11), .11, .08, 'rubber', seg=20, axis='x')            # main wheels
        M.cylinder((sx * .2, -.32, .11), .05, .085, 'steel', seg=12, axis='x')
        M.box((sx * .2, -.32, .3), (.05, .05, .32), 'steel')                              # gear legs
        for k in range(3):                                                                # portholes
            M.cylinder((sx * (R0 + .002), .1 + k * .2, Z + .08), .055, .01, 'cream', seg=16, axis='x')
            M.cylinder((sx * (R0 + .006), .1 + k * .2, Z + .08), .042, .01, 'navy', seg=16, axis='x')
    M.cylinder((0, .78, .07), .06, .06, 'rubber', seg=14, axis='x')                       # tail wheel
    M.blob((0, -.2, Z + .27), .19, 'navy', squash=.62, subdiv=3)                          # rounded canopy
    M.cylinder((0, -.2, Z + .28), .2, .03, 'cream', seg=32)                               # canopy rim
    for k, (dy, h) in enumerate(((.42, .14), (.62, .3))):                                 # two little stairs behind the wing
        M.box((.52, dy, h / 2), (.3, .2, h), 'oak')


PROPS = {'SM_AP_P70Extinguisher': (extinguisher, 6.0), 'SM_AP_P70ExtStand': (stand, 0), 'SM_AP_P70PlayPlane': (play_plane, 0)}


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    out = HERE / 'Props70Build'; out.mkdir(exist_ok=True)
    items = []
    for name, (fn, kg) in PROPS.items():
        probe = Mesh(MATS); fn(probe)
        used = {f.material_index for f in probe.bm.faces}; probe.bm.free()
        M = Mesh({k: v for i, (k, v) in enumerate(MATS.items()) if i in used})
        fn(M)
        obj = M.finish(name)
        fbx = out / (name + '.fbx')
        export(obj, fbx)
        items.append(dict(asset=name, fbx=str(fbx.resolve()), materials=[m.name for m in obj.data.materials], kg=kg,
                          polygons=len(obj.data.polygons), dims=[round(v, 3) for v in obj.dimensions]))
        bpy.data.objects.remove(obj)
    (HERE / 'Props70Build.json').write_text(json.dumps(dict(status='SUCCESS', items=items), indent=1), encoding='utf-8')
    print('PROPS70', [(i['asset'], i['dims'], i['polygons']) for i in items])


if __name__ == "__main__":
    main()
