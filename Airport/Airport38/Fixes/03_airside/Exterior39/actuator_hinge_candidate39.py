"""Candidate only: fix geometric hinge estimation; not installed by this module.

For a future approved source actuator rebuild, root can assign
flight39_surfaces._hinge = physical_hinge before its build. Source actor pivots
and mesh recentering must be rebuilt together. Never apply metadata alone to
the existing native meshes, because that would move the closed surfaces.
"""
import math


def hinge_from_points(points,vertical=False):
    unique={tuple(round(float(v),6) for v in p):tuple(float(v) for v in p) for p in points}
    pts=list(unique.values());index=2 if vertical else 0;ends=[min(p[index] for p in pts),max(p[index] for p in pts)]
    if not vertical and abs(ends[0])>abs(ends[1]):ends.reverse()
    hinge=[]
    for edge in ends:
        row=[p for p in pts if abs(p[index]-edge)<.0002];y=min(p[1] for p in row)
        near=[p for p in row if abs(p[1]-y)<.0002]
        hinge.append(tuple(sum(p[i] for p in near)/len(near) for i in range(3)))
    axis=tuple(b-a for a,b in zip(hinge[0],hinge[1]));length=math.sqrt(sum(v*v for v in axis))
    if length<1e-6:raise ValueError('Degenerate physical control-surface hinge')
    return hinge[0],tuple(v/length for v in axis)


def physical_hinge(ob,vertical=False):
    from mathutils import Vector
    pivot,axis=hinge_from_points([ob.matrix_world@v.co for v in ob.data.vertices],vertical)
    return Vector(pivot),Vector(axis)
