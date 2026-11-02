"""Pass64 patch: a wall-mounted departures display on the concourse east wall
(replacing the free-standing information totem whose screen faced the wall)."""
import ast
from pathlib import Path

p = Path(__file__).resolve().parent / 'lounges62_blender.py'
s = p.read_text(encoding='utf-8')
fn = '''def concourse(M):
    """Departures display on the concourse east wall (face x -26.13), facing the
    concourse, where the information totem stood. A navy screen in a slim oak
    frame, gold header, the two departures, and the way to A08."""
    xf, yc, zc, w, h = -26.14, 11.9, 1.85, 2.2, 1.2
    M.box((xf - .03, yc, zc), (.06, w + .08, h + .08), 'oak')              # frame
    M.box((xf - .065, yc, zc), (.01, w, h), 'navy')                        # screen
    face = math.pi                                                          # text faces -x, into the concourse
    x = xf - .07
    text('DEPARTURES', (x, yc, zc + .42), face, .17, 'gold')
    M.box((x - .002, yc, zc + .28), (.004, w - .3, .01), 'gold')
    rows = (('SA107', 'AZURE BAY', 'A07', 'BOARDING'), ('SA208', 'NORTH COAST', 'A08', '10:55'))
    for k, (flt, dest, gate, status) in enumerate(rows):
        z = zc + .1 - k * .26
        for dy, word, mat in ((.82, flt, 'glow'), (.25, dest, 'glow'), (-.3, gate, 'gold'), (-.75, status, 'gold' if k == 0 else 'glow')):
            text(word, (x, yc + dy, z), face, .1, mat)
    text('<   A08  NORTH LOUNGE', (x, yc, zc - .45), face, .09, 'glow')


'''
s = s.replace('\nDECK = 3.17\n', '\n' + fn + 'DECK = 3.17\n', 1)
s = s.replace("    a08(M, F); a07(M, F)\n", "    a08(M, F); a07(M, F); concourse(M)\n", 1)
ast.parse(s)
assert 'concourse(M)\n' in s
p.write_text(s, encoding='utf-8')
print('patched')
