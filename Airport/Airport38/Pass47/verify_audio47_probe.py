"""Pass47: prove the ambience mixer runs and follows the player.

I cannot listen to the game, so this records what the mixer is doing: walks
the pawn to ten places, waits for the volumes to settle, and logs the context
it detected, each loop's volume and whether each component is playing.
Must run WITH sound (no -NoSound), since the mixer disables itself under it.
Read-only.
"""
import unreal as u, json, time, traceback

G = None
S = {}
STOPS = [('forecourt', [-55.0, -12.5]), ('check-in', [-35.0, -13.0]),
         ('security', [-42.0, 4.0]), ('concourse', [-29.0, 5.0]),
         ('cafe', [-40.0, 25.0]), ('gate A07', [-18.0, 4.0]),
         ('toilets', [-18.0, -7.0]), ('arrivals', [-18.0, -17.0]),
         ('apron', [2.0, 2.0]), ('aircraft cabin', None)]
SETTLE = 4.0


def save(status='RUNNING', **kw):
    import ambience47 as A
    (G.R / 'Pass47' / 'VerifyAudio47.json').write_text(json.dumps(dict(
        status=status, mixer_status=A.S.get('status'), stops=S.get('rows', []), **kw),
        indent=1), encoding='utf-8')


def tick(dt):
    try:
        import ambience47 as A
        now = time.monotonic()
        if now < S['next']:
            return
        if S['i'] > 0:
            name, _ = STOPS[S['i'] - 1]
            comps = A.S.get('comps', {})
            S['rows'].append(dict(stop=name, context=A.S.get('context'),
                                  pawn=[round(v, 2) for v in G.source(G.P.STATE['pawn'].get_actor_location())],
                                  volumes={k: round(v, 3) for k, v in A.S.get('volumes', {}).items()},
                                  playing={k: bool(c.is_playing()) for k, c in comps.items()}))
            save()
        if S['i'] >= len(STOPS):
            save('SUCCESS')
            u.unregister_slate_post_tick_callback(S['handle'])
            u.SystemLibrary.quit_game(G.P.STATE['world'], G.P.STATE['pc'], u.QuitPreference.QUIT, False)
            return
        name, xy = STOPS[S['i']]
        p = G.D['aircraft38']['start_aboard'] if xy is None else [xy[0], xy[1], 1.62]
        G.P.STATE['pawn'].set_actor_location(G.v(p), False, True)
        S['i'] += 1
        S['next'] = now + SETTLE
    except Exception:
        save('ERROR', error=traceback.format_exc())
        u.unregister_slate_post_tick_callback(S['handle'])


def start(game):
    global G
    G = game
    S.update(i=0, rows=[], next=time.monotonic() + 3.0)
    S['handle'] = u.register_slate_post_tick_callback(tick)
    save()
