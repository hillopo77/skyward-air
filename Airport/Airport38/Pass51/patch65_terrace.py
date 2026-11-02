"""Pass65 patch: the A08 viewing terrace, made a lounge rather than bleachers.

  seats      cushions in 2 m pads with gaps instead of one strip; a lean-back
             cushion against the riser behind every seat row; a few accent
             cushions
  planters   oak planter boxes built into the terrace: the south end of the
             upper two tiers and mid-way along the top tier, spilling greenery
  wall       oak slats behind the terrace up to the datum; above it a large
             'North Coast' artwork: sky, layered coast, sea bands and a gold sun
             in an oak frame
"""
import ast
from pathlib import Path

p = Path(__file__).resolve().parent / 'lounges62_blender.py'
s = p.read_text(encoding='utf-8')
old_start = s.index("    xw, y0, y1 = -31.85, 22.5, 31.3")
old_end = s.index("    for k in range(6):                                                 # steps up the north end")
new = '''    xw, y0, y1 = -31.85, 22.5, 31.3
    L, yc = y1 - y0, (y0 + y1) / 2
    plant_slots = {1: [(22.5, 23.15)], 2: [(22.5, 23.15), (26.6, 27.6)]}   # tier -> planter spans (y)
    for k, top in enumerate((.45, .90, 1.35)):
        xf = -29.15 - k * .9                                           # front edge of tier k
        M.box((xf - .45, yc, top / 2), (.9, L, top), 'oak')
        M.box((xf - .02, yc, top - .03), (.04, L, .02), 'glow')        # light strip under the nosing
        spans, ya = [], y0 + .05
        for a, b in plant_slots.get(k, []) + [(y1 - .05, y1)]:
            if b > ya:
                spans.append((ya, a))
            ya = b
        for a, b in spans:                                             # cushion pads, ~2 m, with gaps
            n = max(1, round((b - a) / 2.0))
            for i in range(n):
                pa = a + (b - a) * i / n + .06
                pb = a + (b - a) * (i + 1) / n - .06
                SOFT.box((xf - .33, (pa + pb) / 2, top + .05), (.58, pb - pa, .1), 'teal')
                if k < 2:                                              # lean cushion against the riser behind
                    SOFT.box((xf - .8, (pa + pb) / 2, top + .26), (.13, pb - pa, .36), 'cushion')
                if i % 2 == 0 and pb - pa > 1.2:
                    SOFT.box((xf - .74, pa + .45, top + .3), (.1, .32, .28), 'accent')
        for a, b in plant_slots.get(k, []):                            # planter boxes built into the tier
            yy = (a + b) / 2
            M.box((xf - .45, yy, top + .2), (.86, b - a, .4), 'oak')
            M.box((xf - .45, yy, top + .405), (.76, b - a - .1, .02), 'black')
            for d in (-.22, .0, .22):
                M.blob((xf - .45 + d, yy + d * .5, top + .55), .26, 'leaf' if d else 'leaf2', squash=.8, subdiv=2)
    SOFT.box((xw + .16, yc, 1.35 + .35), (.16, L - .1, .5), 'teal')    # back cushion against the wall
    slat_wall(M, -31.83, -31.83, y0, y1, 1.42, 3.12, (1, 0))           # oak slats behind the terrace
    # 'North Coast' artwork above the datum
    xa, za0, za1, ya0, ya1 = -31.8, 3.5, 4.85, 23.2, 30.6
    M.box((xa - .02, (ya0 + ya1) / 2, (za0 + za1) / 2), (.05, ya1 - ya0 + .12, za1 - za0 + .12), 'oak')
    M.box((xa + .01, (ya0 + ya1) / 2, (za0 + za1) / 2), (.01, ya1 - ya0, za1 - za0), 'cream')      # sky

    def band(mat, z_of, dx):
        """A filled band on the artwork: from the bottom edge up to z_of(y) (a wavy top)."""
        n = 48
        pts = [(xa + dx, ya0 + (ya1 - ya0) * i / n, za0 + .02) for i in range(n + 1)]
        top = [(xa + dx, ya0 + (ya1 - ya0) * i / n, min(za1 - .02, z_of(ya0 + (ya1 - ya0) * i / n))) for i in range(n + 1)]
        for i in range(n):
            q = [pts[i], pts[i + 1], top[i + 1], top[i]]
            M.quad(q, mat); M.quad(list(reversed(q)), mat)
    band('sage', lambda y: 4.05 + .32 * math.sin((y - ya0) * .55) + .12 * math.sin((y - ya0) * 1.7), .02)   # far hills
    band('fabric', lambda y: 3.85 + .1 * math.sin((y - ya0) * .9 + 1.0), .03)                              # dunes
    band('teal', lambda y: 3.72 + .03 * math.sin((y - ya0) * 3.0), .04)                                    # shallows
    band('navy', lambda y: 3.62 + .02 * math.sin((y - ya0) * 4.0 + .5), .05)                               # sea
    M.cylinder((xa + .06, 28.9, 4.45), .26, .02, 'gold', seg=32, axis='x')                               # sun
    text('NORTH  COAST', (xa + .07, 24.6, 4.62), 0.0, .16, 'navy')
'''
s = s[:old_start] + new + s[old_end:]
ast.parse(s)
p.write_text(s, encoding='utf-8')
print('patched')
