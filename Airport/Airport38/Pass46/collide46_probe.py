"""Pass46 / P46-015: make the security and queue furniture solid.

Twelve actors are visible and walk-through: two X-ray scanners, six queue posts
and four stanchions. clearance46.py establishes offline that none of them can
obstruct the journey pawn - the posts and stanchions top out at 1.03 and 1.07 m,
below the pawn's collision band of z 1.27..1.97, and the scanners stand at least
1.50 m clear of every walk leg.

This script only changes collision state and records exactly what it changed.
It deliberately makes no claim that the result blocks anything, for two
reasons found the hard way.

Pass45 found that `body_setup` is not reachable as an editor property on
StaticMesh in this engine build, so the mesh-level collision_trace_flag cannot
be set from Python. All that can be set here is the component's
collision_enabled and profile, and whether that blocks depends on collision
data the mesh already carries.

And this mode cannot answer the question anyway. A positive control - a
downward trace onto the check-in hall floor, which is solid, BlockAll and
certainly there - returns nothing under -run=pythonscript -NullRHI. No physics
query answers in this mode at any height, which is the real reason the Pass46
header-mount traces came back empty; it was never about the 2.5 m height.

Verification therefore happens in -game, where the journey's own traces work:
verify46_probe.py behind -Collide46Verify. P46-014 enabled collision on ten
plants and never checked, and that was a claim rather than a result; this is
the correction.

Run standalone under -run=pythonscript; -game has no EditorActorSubsystem.
MUTATES AND SAVES the level.
"""
import unreal as u, json, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = '/Game/Airport38/L_Airport_Repair38'

GROUPS = {
    # The queue furniture. Too short to reach the pawn's collision band, and
    # nowhere near the belt the registered bag travels along.
    'A': ['Queue post31 0', 'Queue post31 1', 'Queue post31 2',
          'Queue post31 3', 'Queue post31 4', 'Queue post31 5',
          'Stanchion24_1725', 'Stanchion24_1726',
          'Stanchion24_1738', 'Stanchion24_1739'],
    # The scanners, kept separate: they are the only two tall enough to reach
    # the pawn, and the only two the scanned bag passes through. The journey
    # run after this group is the real test of that tunnel - it waits for the
    # bag to reach scanned_bags, and a jammed bag times out there.
    'B': ['X-ray scanner 01', 'X-ray scanner 02'],
    # P46-017: the gallery kit (stairs, landing, deck, piers, guards) in one
    # mesh. deck46_probe measured it under -game with collision toggled on:
    # simple and complex both hit the deck at 3.165, nothing is hit under it
    # at 0.6/1.62/2.4 m, and the pawn's sphere sweeps up both flights clear.
    'C': ['Crafted GalleryStair35'],
}

PROFILE = 'BlockAll'

S = dict(status='RUNNING', started=time.time(), group=None,
         changed=[], unchanged=[], rejected=[],
         verification='none in this mode; see verify46_probe.py under -game')


def save(status=None, **extra):
    if status:
        S['status'] = status
    S.update(extra)
    (HERE / 'Collide46.json').write_text(json.dumps(S, indent=1),
                                         encoding='utf-8')


def main():
    # Windows PowerShell's -Encoding utf8 writes a BOM, so strip it.
    group = (HERE / 'Collide46Group.txt').read_text(
        encoding='utf-8-sig').strip().strip('﻿')
    assert group in GROUPS, 'unknown group %r' % group
    S['group'] = group
    names = GROUPS[group]
    save()

    assert u.EditorLoadingAndSavingUtils.load_map(MAP), 'could not load ' + MAP
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    EA = u.get_editor_subsystem(u.EditorActorSubsystem)
    assert EA is not None, 'no EditorActorSubsystem; run under -run=pythonscript'

    actors = {}
    for q in EA.get_all_level_actors():
        try:
            actors[q.get_actor_label()] = q
        except Exception:
            continue

    for n in names:
        a = actors.get(n)
        if a is None:
            S['rejected'].append(dict(actor=n, reason='not in the level'))
            continue
        try:
            c = a.static_mesh_component
            o, e = a.get_actor_bounds(False)
            # The component's reported state is masked by the actor's own
            # switch: with actor collision off, get_collision_enabled reads
            # NO_COLLISION whatever the component is set to. The scanners
            # first came back NO_COLLISION -> NO_COLLISION for exactly this
            # reason, against a layout that declares them collision: True.
            was = dict(enabled=str(c.get_collision_enabled()),
                       profile=str(c.get_collision_profile_name()),
                       actor_collision=bool(a.get_actor_enable_collision()))
            if 'QUERY_AND_PHYSICS' in was['enabled'] and \
                    was['profile'] == PROFILE and was['actor_collision']:
                S['unchanged'].append(dict(actor=n, was=was,
                                           reason='already set to block'))
                continue
            if not was['actor_collision']:
                a.set_actor_enable_collision(True)
            c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
            c.set_collision_profile_name(PROFILE)
            S['changed'].append(dict(
                actor=n, mesh=c.static_mesh.get_name() if c.static_mesh else None,
                was=was,
                now=dict(enabled=str(c.get_collision_enabled()),
                         profile=str(c.get_collision_profile_name()),
                         actor_collision=bool(a.get_actor_enable_collision())),
                centre_m=[round(o.x / 100.0, 3), round(-o.y / 100.0, 3),
                          round(o.z / 100.0, 3)],
                top_m=round((o.z + e.z) / 100.0, 3)))
        except Exception as e:
            S['rejected'].append(dict(actor=n,
                                      reason='could not set collision: %s' % e))
    save()

    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP), 'save_map failed'
    save('SUCCESS', finished=time.time())
    print('COLLIDE46 SUCCESS group=%s changed=%d unchanged=%d rejected=%d'
          % (group, len(S['changed']), len(S['unchanged']),
             len(S['rejected'])), flush=True)


try:
    main()
except Exception:
    S['error'] = traceback.format_exc()
    save('ERROR')
    raise
