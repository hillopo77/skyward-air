"""Fresh targeted native scanner scenario; no state flags or bag teleports.

Root's runner should use its existing normal swept walk / aim-nearest-use /
wait operators. This is a specification, not a claim that native QA passed.
"""
def specification(D):
    def walk(*p):return dict(action='walk',points=[list(q) for q in p],sweep=True,teleport=False)
    def use(actor,kind):
        q=next(q for q in D['interactions'] if q['actor']==actor and q['kind']==kind)
        return dict(action='face_and_use',actor=actor,kind=kind,point=q['point'],
                    dispatch='G.nearest then G.use_nearest',require_visible=True)
    return dict(start=D['start'],scenario='Separate fresh launch: unscanned-held denial, physical scan, collect and valid full traverse',steps=[
        dict(action='assert',predicate="not G.S['checked_in'] and not G.S['security'] and G.S['held'] is None"),
        walk([-48,-12.5,1.62],[-46,-15.8,1.62]),use('Physical luggage 01','pickup'),
        walk([-45.2,-15,1.62],[-42,-15,1.62],[-40.5,-11.8,1.62],[-40.5,-10.2,1.62]),
        use('Self-service kiosk24 0','checkin'),
        walk([-39,-11,1.62],[-32.1,-8.8,1.62],[-30,-8.8,1.62],[-30,-6,1.62],[-42,-6,1.62],[-42,-3,1.62],
             [-45.5,.5,1.62],[-45.5,2.5,1.62],[-45.5,3.6,1.62]),
        dict(action='assert',predicate="G.S['held']=='Physical luggage 01' and not G.S['security'] and 'Physical luggage 01' not in G.journey38['state']['scanned_bags']",
             evidence='Save Security denied unscanned baggage38 event and held-body screenshot'),
        walk([-45.5,2.5,1.62],[-45.5,-.4,1.62],[-42.4,-.4,1.62],[-42.4,.3,1.62]),
        use('Security belt 01','scanner'),
        dict(action='wait',until="G.S['held'] is None",timeout_s=8,
             evidence='Actual spring release COM goal[-43.15,1.4,1.375], safely before front mouth1.925; no bag transform assignment'),
        dict(action='capture',name='Scanner38_InputRelease'),
        dict(action='wait',until="'Physical luggage 01' in G.journey38['state']['scanned_bags']",timeout_s=18,
             evidence='Save COM samples entering fromy<2.1, supported middle2.2..4.1, beyond4.25, elapsed>.75s; native curtains open'),
        dict(action='assert',predicate="not G.S['security']",evidence='Bag transit alone does not clear the person'),
        # Walk around the left of the detector to collect from the output,
        # without traversing its centre before the deliberate final test.
        walk([-42.4,-.4,1.62],[-47.7,-.4,1.62],[-47.7,6.1,1.62],[-43.15,6.1,1.62]),
        use('Physical luggage 01','pickup'),
        dict(action='assert',predicate="G.S['held']=='Physical luggage 01' and not G.S['security']"),
        walk([-47.7,6.1,1.62],[-47.7,-.4,1.62],[-45.5,-.4,1.62],[-45.5,2.5,1.62],[-45.5,3.6,1.62]),
        dict(action='assert',predicate="G.S['security'] and G.journey38['ticket']()['security_cleared']",
             evidence='Full natural traversal succeeds with the genuinely scanned held bag'),
        dict(action='capture',name='Scanner38_CollectedAndCleared'),
    ],requirements=dict(route_teleports=0,direct_bag_transform_assignments=0,scan_state_setup=0,
                        source_geometry_unchanged=True,expected_scanner_centre=[-43.15,3.0],
                        actual_input_approach=[-42.4,.3,1.62]))
