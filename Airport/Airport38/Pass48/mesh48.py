"""Pass48 shared Blender mesh helper: one bmesh, metre UVs, a material per face.

Boxes get UVs with u across and v along their longest side, so timber grain
runs along every board; everything else is projected by face orientation.
"""
import bpy, bmesh, math, os

# Pass54 'soft' finish (set MESH48_HARD=1 for the old hard-edged output).
SOFT = not os.environ.get('MESH48_HARD')
SOFT_ANGLE = math.radians(40)
SOFT_WIDTH = .012
SOFT_SEGMENTS = 2


class Mesh:
    def __init__(self, mats):
        """mats: {key: (project material name, viewport rgb)} in slot order."""
        self.mats = mats
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.index = {k: i for i, k in enumerate(mats)}
        self.solid = []                       # faces whose winding is recomputed (closed solids)

    def _face(self, verts, mat):
        f = self.bm.faces.new(verts)
        f.material_index = self.index[mat]
        return f

    def box(self, c, s, mat, rot=0.0):
        """Axis box centred at c, size s, optional yaw (radians) about z."""
        bm = self.bm
        cr, sr = math.cos(rot), math.sin(rot)
        vs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    lx, ly = sx * s[0] / 2, sy * s[1] / 2
                    vs.append(bm.verts.new((c[0] + lx * cr - ly * sr, c[1] + lx * sr + ly * cr, c[2] + sz * s[2] / 2)))
        long_ax = max(range(3), key=lambda k: s[k])
        local = [((-1, 1)[i >> 2 & 1] * s[0] / 2, (-1, 1)[i >> 1 & 1] * s[1] / 2, (-1, 1)[i & 1] * s[2] / 2) for i in range(8)]
        for f in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
            face = self._face([vs[i] for i in f], mat)
            # normal axis in the box's own frame
            n_ax = next(k for k in range(3) if len({local[i][k] for i in f}) == 1)
            if n_ax != long_ax:
                ua, va = next(k for k in range(3) if k not in (n_ax, long_ax)), long_ax
            else:
                ua, va = (long_ax + 1) % 3, (long_ax + 2) % 3
            for l, i in zip(face.loops, f):
                l[self.uv].uv = (local[i][ua], local[i][va] + (c[2] if va == 2 else 0))
            face.tag = True

    def quad_uv(self, pts, uvs, mat):
        """A quad with explicit UVs (printed art)."""
        f = self._face([self.bm.verts.new(p) for p in pts], mat)
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = uv
        f.tag = True
        return f

    def quad(self, pts, mat):
        f = self._face([self.bm.verts.new(p) for p in pts], mat)
        return f

    def cylinder(self, c, r, h, mat, seg=16, cap_top=True, cap_bottom=True, mat_bottom=None, axis='z'):
        bm = self.bm

        def P(a, t):
            ca, sa = r * math.cos(a), r * math.sin(a)
            if axis == 'z':
                return (c[0] + ca, c[1] + sa, c[2] + t)
            if axis == 'x':
                return (c[0] + t, c[1] + ca, c[2] + sa)
            return (c[0] + ca, c[1] + t, c[2] + sa)
        lo = [bm.verts.new(P(2 * math.pi * k / seg, -h / 2)) for k in range(seg)]
        hi = [bm.verts.new(P(2 * math.pi * k / seg, h / 2)) for k in range(seg)]
        fs = [self._face([lo[k], lo[(k + 1) % seg], hi[(k + 1) % seg], hi[k]], mat) for k in range(seg)]
        if cap_top:
            fs.append(self._face(hi, mat))
        if cap_bottom:
            fs.append(self._face(list(reversed(lo)), mat_bottom or mat))
        if cap_top and cap_bottom:
            self.solid += fs

    def blob(self, c, r, mat, squash=1.0, subdiv=1):
        """Low-poly foliage blob (icosphere)."""
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=r)
        for v in res['verts']:
            v.co.z *= squash
            v.co.x += c[0]; v.co.y += c[1]; v.co.z += c[2]
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.material_index = self.index[mat]
            self.solid.append(f)

    def finish(self, name):
        bm = self.bm
        # Boxes and quads are wound outward / upward by construction; only
        # closed solids are recomputed (a lone quad could otherwise flip).
        if self.solid:
            bmesh.ops.recalc_face_normals(bm, faces=[f for f in self.solid if f.is_valid])
        for f in bm.faces:
            if f.tag:
                continue
            f.normal_update()
            n = f.normal
            for l in f.loops:
                p = l.vert.co
                if abs(n.z) > .7:
                    l[self.uv].uv = (p.x, p.y)
                elif abs(n.x) > abs(n.y):
                    l[self.uv].uv = (p.y, p.z)
                else:
                    l[self.uv].uv = (p.x, p.z)
        if SOFT:
            # Pass54: no razor edges. Every edge sharper than SOFT_ANGLE between two
            # faces gets a small two-step round-over, so edges catch a highlight
            # like real joinery instead of reading as computer-model creases.
            bm.normal_update()                       # boxes are built without normals
            edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > SOFT_ANGLE]
            if edges:
                bmesh.ops.bevel(bm, geom=edges, offset=SOFT_WIDTH, offset_type='OFFSET', segments=SOFT_SEGMENTS, profile=.5,
                                affect='EDGES', clamp_overlap=True)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me); bm.free()
        for k, (mname, rgb) in self.mats.items():
            m = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
            m.diffuse_color = (*rgb, 1)
            me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = SOFT
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        if SOFT:
            # Face-area weighted normals: flat faces stay flat, the round-overs shade smoothly.
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True); bpy.context.view_layer.objects.active = o
            wn = o.modifiers.new('soft', 'WEIGHTED_NORMAL')
            wn.mode = 'FACE_AREA'; wn.weight = 100; wn.keep_sharp = True
            bpy.ops.object.modifier_apply(modifier=wn.name)
        return o


def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', bake_space_transform=False, axis_forward='Y', axis_up='Z')
