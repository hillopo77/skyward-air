"""Pass46: measure the real ceiling underside above the check-in headers.

The mount was built to the zone's nominal ceiling_m of 3.80, which is an
authored number, not a measurement. If the real ceiling is lower the shoe
pierces it; if higher the shoe floats below it. Before claiming the headers are
mounted, measure where the ceiling actually is at each hanger position.

Also records which nearby actors block a trace at all, because two of the
things involved - the header boards themselves and the gallery deck - have
collision disabled, which is why earlier traces returned nothing.

Read-only.
"""
import unreal as u, json, time, traceback
from pathlib import Path

R = Path(__file__).resolve().parents[1]
MAP = '/Game/Airport38/L_Airport_Repair38'

POINTS = [
    ('header0 hanger -y', -30.307, -12.80),
    ('header0 hanger +y', -30.307, -10.40),
    ('header0 centre', -30.307, -11.60),
    ('header1 hanger -y', -30.307, -15.80),
    ('header1 hanger +y', -30.307, -13.40),
    ('header1 centre', -30.307, -14.60),
    ('checkin mid-room', -34.00, -13.00),
    ('A07 display (known good, H=3.4)', -14.275, 5.15),
    ('A08 display (known good, H=3.8)', -24.325, 26.15),
]

report = dict(status='RUNNING', started=time.time(), ceiling=[], collision=[])


def flush(status=None):
    if status:
        report['status'] = status
    out = R / 'Pass46'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Measure46.json').write_text(json.dumps(report, indent=1),
                                         encoding='utf-8')


def label_of(hit):
    if not hit:
        return None, None
    t = hit.to_tuple()
    if not t[0]:
        return None, None
    lbl = None
    z = None
    for k in t:
        if lbl is None:
            try:
                lbl = k.get_actor_label()
            except Exception:
                pass
        if z is None and hasattr(k, 'z') and hasattr(k, 'x'):
            z = k.z
    return lbl, z


def main():
    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)

    for name, x, y in POINTS:
        x_cm, y_cm = x * 100.0, -y * 100.0
        # sweep upward from above head height to well past any roof step
        row = dict(point=name, x=x, y=y)
        # Four trace variants. An upward trace found nothing even at the A07
        # and A08 displays, which are mounted and have a passing contact test,
        # so the trace is the suspect rather than the geometry.
        for tag, z0, z1, want_complex in (('up_complex', 250.0, 900.0, True),
                                          ('up_simple', 250.0, 900.0, False),
                                          ('down_complex', 900.0, 250.0, True),
                                          ('down_simple', 900.0, 250.0, False)):
            hit = u.SystemLibrary.line_trace_single(
                world, u.Vector(x_cm, y_cm, z0), u.Vector(x_cm, y_cm, z1),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1, want_complex, [],
                u.DrawDebugTrace.NONE, True)
            lbl, _ = label_of(hit)
            d = None
            if hit:
                t = hit.to_tuple()
                if t[0]:
                    d = float(t[2])
            row[tag] = dict(actor=lbl, hit_z_m=(
                round((z0 + (d if z1 > z0 else -d)) / 100.0, 3)
                if d is not None else None))
        # And a direct question: what does a small box at 3.70 m overlap?
        try:
            found = u.SystemLibrary.box_overlap_actors(
                world, u.Vector(x_cm, y_cm, 370.0), u.Vector(8.0, 8.0, 8.0),
                [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1], u.Actor, [])
            row['box_at_3_70'] = sorted({q.get_actor_label()
                                         for q in (found or [])})[:5]
        except Exception as e:
            row['box_at_3_70'] = ['error: ' + str(e)[:60]]
        report['ceiling'].append(row)
        flush()

    # which of the actors involved can be seen by a trace at all
    for lbl in ('Check-in service header29 0', 'Check-in service header29 1',
                'P46 header mount Header0', 'P46 header mount Header1',
                'Airport38 coherent ceiling union', 'Crafted GalleryStair35',
                'Gate A07 flight display', 'Airport38 verified architectural attachments'):
        a = None
        for q in EA.get_all_level_actors():
            try:
                if q.get_actor_label() == lbl:
                    a = q
                    break
            except Exception:
                continue
        if a is None:
            report['collision'].append(dict(actor=lbl, present=False))
            continue
        try:
            c = a.static_mesh_component
            origin, extent = a.get_actor_bounds(False)
            report['collision'].append(dict(
                actor=lbl, present=True,
                collision_enabled=str(c.get_collision_enabled()),
                profile=str(c.get_collision_profile_name()),
                visible=bool(c.is_visible()),
                centre_m=[round(origin.x / 100.0, 3), round(-origin.y / 100.0, 3),
                          round(origin.z / 100.0, 3)],
                extent_cm=[round(extent.x, 1), round(extent.y, 1),
                           round(extent.z, 1)],
                top_m=round((origin.z + extent.z) / 100.0, 3),
                bottom_m=round((origin.z - extent.z) / 100.0, 3)))
        except Exception as e:
            report['collision'].append(dict(actor=lbl, present=True, error=str(e)))
    flush('SUCCESS')
    print('MEASURE46 SUCCESS', flush=True)


try:
    main()
except Exception:
    report['error'] = traceback.format_exc()
    flush('ERROR')
    raise
