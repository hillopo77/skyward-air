"""Integration test contract, consumed by root's actual native movement runner.

These are normal walk/use/wait actions. No journey flag setup, teleport or
direct bag transform is permitted in the fresh-start scenario.
"""
import math


def specification(D):
    I=D['interactions'];meta=D['repair38']['journey'];queue=meta['queue']
    def target(actor,kind=None,**fields):
        return next(q for q in I if q['actor']==actor and (kind is None or q['kind']==kind)
                    and all(q.get(k)==v for k,v in fields.items()))
    def walk(*points):return dict(action='walk',points=[list(p) for p in points],sweep=True,teleport=False)
    def use(actor,kind=None,**fields):
        q=target(actor,kind,**fields)
        return dict(action='face_and_use',actor=actor,kind=q['kind'],point=q['point'],dispatch='G.nearest then G.use_nearest',require_visible=True)
    y=-13.;belt=next(q for q in D['conveyors'] if q['name']=='Bag drop belt 01')
    t=target('Bag drop belt 01','bagdrop')['point']
    return dict(
        start=D['start'],look_at=D.get('look_at'),
        fresh_start=[
            dict(action='assert',predicate='not any journey flags, no ticket, all WC vacant'),
            walk([-48,-12.5,1.62],[-46.0,-13.6,1.62],[-45.2,-15,1.62],[-42,-15,1.62],[-39,-15,1.62]),
            use(queue['marker']),
            dict(action='wait',until="G.journey38['state']['queue']['called']=='Check-in desk 01'",timeout_s=100,
                 evidence='At call, busy empty, lastNPC more than1.15m from approach; no timer-only call'),
            walk([-39.4,-13.65,1.62],[-32.1,-13.65,1.62],[-32.1,-11.6,1.62]),
            use('Check-in desk 01','checkin'),
            walk([-32.1,-13.65,1.62],[-35.7,-15.5,1.62]),use('Physical luggage 02','pickup'),
            walk([-32.1,-15.8,1.62],[-32.1,-13.0,1.62],[-30.2,-13.0,1.62]),
            use('Bag drop belt 01','bagdrop'),
            dict(action='wait',until="'Physical luggage 02' in G.journey38['state']['registered_bags']",timeout_s=25,
                 evidence='Record real body COM trajectory, through x=-26 aperture, native support receiver, settled .65s; no actor transform'),
            walk([-32.1,-11.6,1.62],[-32.1,-8.8,1.62],[-30,-6,1.62],[-42,-6,1.62],[-42,-3,1.62],[-42,-.4,1.62],[-45.5,-.4,1.62],[-45.5,.5,1.62],[-45.5,2.5,1.62],[-45.5,3.6,1.62]),
            dict(action='assert',predicate="security true only after complete south-to-north traversal; ticket.security_cleared true"),
            walk([-45.5,6.5,1.62],[-36.8,6.5,1.62],[-34.1,6.5,1.62],[-29,6.5,1.62],[-29,4,1.62],[-26,4,1.62],[-22.2,4,1.62],[-19,1.8,1.62],[-18.4,-1.0,1.62]),
            use('Gate A07 boarding desk','boarding'),
            walk([-18.4,.675,1.62],[-15.9,.675,1.62],[-14,.675,1.62],[-12.1,.675,1.62],[-1.5,-3.6,1.62],[10.5,.675,1.62],[13.5,.675,1.62],[14.25,.675,1.62],[15.2,.675,1.62]),
            dict(action='assert',predicate='ticket.aboard true only crossing threshold14.1 via deployed bridge'),
            dict(action='aircraft_walk_and_use',path_key='layout.walk_tests',seat='Economy seat 03E12',
                 evidence='Use translated cabin paths and real occupied-seat guard; walk/sit/stand no teleport'),
        ],
        targeted_negative_tests=[
            dict(id='J01entry',setup='separate fresh launch before checking in',walk=[[-42,-6,1.62],[-42,-4.8,1.62]],
                 expect='bothScreening entry24 fractions0 after proximity; swept walk blocked'),
            dict(id='J01exit',setup='ticket issued but security false',walk=[[-37,6.5,1.62]],
                 expect='bothScreening exit24 fractions0; no1frame opening'),
            dict(id='J03',setup='actual pickup of unscanned cabin bag before traversing',expect='security false; then load bag scanner01 at START target, real physics throughscanner, collect, re-traverse succeeds'),
            dict(id='J04stop',setup='after actual drop before receiver',action='use emergency control for same feed',
                 expect='power false and contact belt brakes; registered_bags unchanged until supported receiving; restart resumes'),
            dict(id='J05',setup='walk into cubicle and use inside close control',target=target('Terminal WC 0','slide',inside_release=True),
                 expect='privacy locked, bothindicatorred; separate outside release refused; inside release alwaysopens/vacant'),
            dict(id='J06',target=target('Gate A08 boarding desk'),expect='information kind / lounge flight status / no scanboarding hint'),
            dict(id='J07',target=next(q for q in I if q['kind']=='vending'),
                 expect='one existing visiblecup on realsaucer, nativepickup,leftmouse decrements sips; repeatedservice no extra actors; hand spring returnrefill'),
            dict(id='J08',setup='joinqueue while standingclear',expect='every servicecall correspondsfree desk; playercall afterfinalNPC clears approach'),
            dict(id='J02',probes=[[-18,18,0],[-15,12,0],[-5,30,0],[0,-50,0]],expect='no0height Current deck; unsupported givesNone or realgradedground'),
            dict(id='J02stairs',setup='naturalwalk galleryup/down thenlowerhold down/up',expect='same eyeheight1.62 aboveeach physicalfloor; no lowerhold pullfromcabin'),
            dict(id='J09',setup='fresh_start above',expect='record controls,baggage,permissions,motion not justwaypoint count'),
        ],
        runtime_api=dict(state="G.journey38['state']",ticket="G.journey38['ticket']()",objective="G.journey38['objective']()",
            floor="G.journey38['floor_at_source'](x,y,feet)",deposit='face real bagdrop/scanner START and G.use_nearest while holding bag'),
        captures=['Receiving bay seen through actualglazing','Bag trajectory through bothapertures','WCoccupied indicatorpair','A08 informationprompt','Coffeecup on saucer and in hand',
                  'Door denied proximity hold','Complete enclosedbridge dock','Gallery/cargostairreturn eyeheight'])


def assert_free_call(G):
    q=G.journey38['state']['queue']
    if not q.get('called'):return True
    assert not q['busy'] and not q['active'] and not q['waiting'],q
    point=G.D['repair38']['journey']['queue']['service_points'][q['called']]
    for name in G.D['repair38']['journey']['queue']['npc_order']:
        actor=G.S['actors'].get(name)
        if actor:assert math.dist(G.source(actor.get_actor_location())[:2],point[:2])>=1.15,name
    return True
