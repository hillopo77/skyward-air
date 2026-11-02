"""Native harness extension after the existing fresh Journey38 route.

Root executes walk and face/use with the normal pawn and nearest visibility.
start_driver requires the actual seated pawn; it does not grant journey flags,
replace the pawn position, set bridge state or directly move the aircraft.
"""
import math,json,time
import flight39_model as M


def specification(P,D):
    items={q['actor']:q for q in P.STATE['items']};dx=D['aircraft38']['offset'][0]
    def p(x,y,z=1.62):return [dx+x,y,z]
    def walk(points):return dict(action='walk',points=points,sweep=True,teleport=False)
    def use(name):return dict(action='plane_face_and_use',actor=name,point=items[name]['point'],dispatch='P.point_at_item / P.nearest then G.use_nearest',require_visible=True)
    return dict(
      continuation=[
        dict(action='assert',predicate='fresh check-in, real bag receiver transfer, security traversal and A07 boarding already passed'),
        dict(action='stand_if_seated',dispatch='P.stand'),
        walk([p(1.1,13.4),p(1.35,12.8),p(1.35,9.2),p(.55,9.2),p(.55,8.65),p(.55,1.2),p(0,.35)]),
        use('Flightdeck door'),dict(action='wait',until='flightdeck leaf completes open animation',timeout_s=3),
        walk([p(0,-1.5),p(-1.3,-2.3),p(-1.3,-3.25)]),
        use('SM_Plane_Seat.016'),dict(action='assert',predicate="G.flight39['pilot']() and P.STATE.seated.actor=='SM_Plane_Seat.016'"),
        dict(action='flight_negative_cases',call='qa_flight39.native_negative(G)',
             evidence='Cold engine, takeoff thrust at stand, gear on ground, unpowered radio all refused; actual controls remain uncommitted'),
        dict(action='flight_driver',call='qa_flight39.start_driver(G,capture)',timeout_s=330,
             evidence='real door animation, real bridge stow and native clearance, engine spool, carrier taxi, full hold, runway entry, roll, rotate, climb, both roll responses'),
        dict(action='flight_verify',call='qa_flight39.verify(G)',
             evidence='actual carrier/pawn/fitting/NPC relative transforms,21+ native actors, floor alignment, physically printed dynamic readout; render frame stats separately'),
        dict(action='flight_walk_begin'),
        walk([p(-1.3,-2.3),p(0,-1.5)]),
        dict(action='flight_drop_bag'),
        dict(action='photo',name='Flight39_WalkingInFlight'),
        walk([p(-1.3,-2.3),p(-1.3,-3.25)]),
        use('SM_Plane_Seat.016'),
        dict(action='flight_target_probe',actor='Cockpit FUEL switch12'),
        dict(action='flight_target_probe',actor='Cockpit quadrant lever 112'),
        dict(action='flight_returned'),
        dict(action='flight_performance'),
      ],
      captures=['crew_close_requested','bridge','engine_spool','taxi','runway_entry','lineup','takeoff_roll','climb','bank_right','bank_left','recover','complete'],
      keys=dict(move_pitch='W / S',steer_bank='A / D',yaw='Left / Right arrows',foot_brake='LeftControl',
        thrust='PageUp / PageDown: Idle, Taxi, Takeoff',parking='P',flaps='F',gear='G',speedbrake='X',radio='C',
        master='M',avionics='N',fuel='U',pumps='J',start_air='K',beacon='L',engine_start='1 / 2',
        crew_close='Home',bridge_stow='End',view='V cockpit / exterior',free_camera='Tab; WASD + Space/Ctrl, Shift fast',stand='Space; finish the takeoff roll first, then walk aboard in flight'),
      no_shortcuts=['No starting aboard flag in the fresh route','No aircraft teleports','No bridge fraction injection','No speed/position/engine state injection','Driver uses actual same command/operate API as modeled controls'],
      native_pending=['Walkability under full plane rotation','Visual/source collision alignment','Actual frame timing with render thread','All attached seated rigs and props','Control aiming and occlusion in motion'])


def native_negative(G):
    api=G.flight39;s=api['state'];results=[]
    for name,value in [('engine1',1),('throttle1',1),('gear',False),('clearance',1)]:
        before=M.snapshot(s);okay,reason=api['command'](name,value,False)
        results.append(dict(case='cold '+name,passed=not okay,reason=reason,
                            engine_unchanged=s['engines']==before['engines'],throttle_unchanged=s['throttle']==before['throttle']))
    return dict(passed=all(q['passed'] and q['engine_unchanged'] and q['throttle_unchanged'] for q in results),cases=results)


def door_open_actual(G):
    d=G.flight39['frame'].door_diagnostics()
    return dict(passed=d['pose_matches_fraction'] and abs(d['fraction']-d['target'])<.1 and abs(d['target'])>80,
                diagnostic=d,evidence='Actual native actor rotation, not merely progress scalar; physical pawn crossing remains required')


def start_driver(G,capture=None):
    from flight39_driver import start
    driver=start(G,capture)
    runtime=G.flight39['runtime'];frame=runtime['frame']
    runtime['qa39_baseline']={a.get_actor_label():dict(actor=a,local=G.u.MathLibrary.inverse_transform_location(frame.carrier.get_actor_transform(),a.get_actor_location())) for a in frame.attached_roots}
    runtime['qa39_begin_frames']=len(G.S['frames']);return driver


def verify(G):
    api=G.flight39;s=api['state'];r=api['runtime'];frame=r['frame'];u=G.u;checks=[]
    driver=r.get('driver');checks.append(dict(id='driver_completed',passed=bool(driver and driver.done and not driver.failed),driver=driver.snapshot() if driver else None))
    checks.append(dict(id='airborne_by_integrated_motion',passed=s['airborne'] and s['position'][2]>80 and s['distance']>2000,position=s['position'][:],distance=s['distance']))
    checks.append(dict(id='native_carrier_pose',passed=(frame.carrier.get_actor_location()-G.v(s['position'])).length()<.02,error_cm=(frame.carrier.get_actor_location()-G.v(s['position'])).length()))
    from airport_flight39 import MAP
    animated_targets={t['actor'].get_actor_label() for c in G.P.STATE['controls'].values() for t in c['targets'] if t.get('actor')}
    animated_links={q['actor'].get_actor_label() for m in G.P.STATE['movables'].values() for q in m.get('links',[])}
    for name,rec in r.get('qa39_baseline',{}).items():
        # Animated leaf/controller actors may change their own local pose. The
        # frame audit is for top-level rigid rooms, passengers, proxies, lights.
        if name.startswith(('Flight39 instrument ','Flight39 flap ','Flight39 aileron ','Flight39 elevator ','Flight39 rudder ','Flight39 gear ')):continue
        if name in animated_targets or name in animated_links:continue
        a=rec['actor'];current=G.u.MathLibrary.inverse_transform_location(frame.carrier.get_actor_transform(),a.get_actor_location());error=(current-rec['local']).length()
        if a in [m['actor'] for m in G.P.STATE['movables'].values()] or name=='Flightdeck door':continue
        checks.append(dict(id='rigid_attachment',actor=name,passed=error<.05,error_cm=error))
    for moving in G.P.STATE['movables'].values():
        for link in moving.get('links',[]):
            spec=link['spec'];actor=link['actor'];start=frame.world(G.P.vector(spec['start']));end=moving['actor'].get_actor_location()+G.P._quat_vector(moving['actor'].get_actor_rotation().quaternion(),G.P.vector(spec['end_local']));d=end-start
            error=(actor.get_actor_location()-(start+end)*.5).length();axis=u.MathLibrary.get_up_vector(actor.get_actor_rotation());alignment=(axis.x*d.x+axis.y*d.y+axis.z*d.z)/max(.001,d.length())
            checks.append(dict(id='articulated_door_link_mounts',actor=actor.get_actor_label(),passed=error<.05 and alignment>.999,midpoint_error_cm=error,axis_alignment=alignment))
    for actor in MAP:
        snap=G.P.control_snapshot(actor);checks.append(dict(id='actual_control_pose',actor=actor,passed=snap['passed'],targets=snap['targets']))
        for t in G.P.STATE['controls'][actor]['targets']:
            if 'rotation_states' in t['spec'] and t.get('actor'):
                error=(t['actor'].get_actor_location()-frame.world(t['location'])).length()
                checks.append(dict(id='control_hinge_stays_mounted',actor=t['actor'].get_actor_label(),passed=error<.05,error_cm=error))
    roundtrip=(frame.world(frame.reference(G.P.STATE['pawn'].get_actor_location()))-G.P.STATE['pawn'].get_actor_location()).length()
    checks.append(dict(id='pawn_frame_roundtrip',passed=roundtrip<.001,error_cm=roundtrip))
    item=next(q for q in G.P.STATE['items'] if q['actor']=='Cockpit AUX switch12');binding=G.P.STATE['point_bindings'][item['actor']]
    expected=binding['actor'].get_actor_location()+G.P._quat_vector(binding['actor'].get_actor_rotation().quaternion(),binding['closed_point'])
    error=(G.P.interaction_point(item)-expected).length();checks.append(dict(id='control_target_follows_model',passed=error<.01,error_cm=error))
    checks.append(dict(id='actual_surface_and_needles',passed=len(r['surfaces'])==13 and len(r['needles'])==7,surfaces=len(r['surfaces']),needles=len(r['needles'])))
    checks.append(dict(id='actual_gear_retracted',passed=len(r['gear'])==7 and r['gear_fraction']>.99 and not s['gear_down'],assemblies=len(r['gear']),fraction=r['gear_fraction']))
    checks.append(dict(id='printed_instrument_readout',passed=bool(r.get('status')),text=str(r['status'].get_component_by_class(u.TextRenderComponent).get_editor_property('text')) if r.get('status') else None))
    frames=G.S['frames'][r.get('qa39_begin_frames',0):];ordered=sorted(frames)
    stats=dict(frames=len(frames),average_fps=len(frames)/sum(frames) if frames and sum(frames)>0 else None,
               p95_ms=ordered[int((len(ordered)-1)*.95)]*1000 if ordered else None,
               note='Full elapsed native game frames; includes capture stalls. Collect a separate uncaptured60s manual run for performance approval.')
    context=json.loads((G.R/'ArtBible/InstalledRuntime39.json').read_text())
    out=dict(status='PASS' if all(q['passed'] for q in checks) else 'FAIL',source_sha256=context['source_sha256'],context=context,checks=checks,frame_statistics=stats,
             native=True,state=api['write'](),limitations='Gameplay flight model; not certified aerodynamics or multiplayer moving-platform replication')
    (G.R/'ArtBible/FlightQA39.json').write_text(json.dumps(out,indent=2),encoding='utf-8');return out
