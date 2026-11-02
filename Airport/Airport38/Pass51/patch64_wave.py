"""Pass64 patch: the A07 wave bench as continuous lofted surfaces, not boxes."""
import ast
from pathlib import Path
p = Path(__file__).resolve().parent / 'lounges62_blender.py'
s = p.read_text(encoding='utf-8')
helper = '''def loft(M, pts, profile, mat, cap=True):
    """Sweep a closed 2-D profile [(n, z), ...] along a polyline pts [(x, y), ...]
    (n = offset along the horizontal normal). Smooth, continuous surfaces."""
    import math as _m
    rings = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = _m.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        rings.append([(x + nx * n, y + ny * n, z) for n, z in profile])
    k = len(profile)
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for j in range(k):
            jj = (j + 1) % k
            M.quad([r0[j], r0[jj], r1[jj], r1[j]], mat)
    if cap:
        M.quad(list(reversed(rings[0])), mat); M.quad(list(rings[-1]), mat)


def rounded(n0, n1, z0, z1, r, seg=4):
    """Rounded-rectangle profile, counter-clockwise in (n, z)."""
    import math as _m
    out = []
    for cn, cz, a0 in ((n1 - r, z0 + r, -90), (n1 - r, z1 - r, 0), (n0 + r, z1 - r, 90), (n0 + r, z0 + r, 180)):
        for t in range(seg + 1):
            a = _m.radians(a0 + 90 * t / seg)
            out.append((cn + r * _m.cos(a), cz + r * _m.sin(a)))
    return out


'''
s = s.replace('def a07(M, F):', helper + 'def a07(M, F):', 1)
i = s.index("    x0, x1, n = -21.7, -15.3, 32")
j = s.index("    names = ['CH12 Waiting passenger 0'")
new = '''    x0, x1, n = -21.7, -15.3, 64
    pts = [(x0 + (x1 - x0) * k / n, c(x0 + (x1 - x0) * k / n)) for k in range(n + 1)]
    loft(M, pts, rounded(-.55, .55, 0, .4, .06), 'oak')                  # plinth
    loft(M, pts, rounded(-.09, .09, .4, 1.02, .08), 'oak')               # spine
    for side in (1, -1):
        lo, hi = (.1, .56) if side > 0 else (-.56, -.1)
        loft(SOFT, pts, rounded(lo, hi, .4, .52, .05), 'teal')            # seat cushion
        bl, bh = (.09, .2) if side > 0 else (-.2, -.09)
        loft(SOFT, pts, rounded(bl, bh, .55, .98, .05), 'cushion')       # back cushion
    for (xe, ye) in (pts[0], pts[-1]):                                    # rounded ends
        M.cylinder((xe, ye, .2), .55, .4, 'oak', seg=28)
        SOFT.cylinder((xe, ye, .46), .5, .12, 'teal', seg=28)
'''
s = s[:i] + new + s[j:]
ast.parse(s)
p.write_text(s, encoding='utf-8')
print('patched')
