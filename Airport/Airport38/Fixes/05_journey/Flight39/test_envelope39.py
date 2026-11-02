"""Actual-metadata interior/bridge safety; no native scene mutation."""
import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock,patch

from flight39_envelope import pressure_envelope,contains_point,contains_box,bridge_overlap
from test_props39 import fixture,V,Body,PLANE_DATA

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'03_airside'))
import airport_airside38 as AIR
LAYOUT=json.loads((HERE.parents[2]/'Exports/airport_layout.json').read_text())


class BoundsBody(Body):
    def __init__(self,point,size=(.5,.5,.8)):
        super().__init__(V(point[0]*100,-point[1]*100,point[2]*100))
        self.extent=V(*(v*50 for v in size));self.bounds_calls=[]
    def get_actor_bounds(self,colliding):self.bounds_calls.append(colliding);return self.p,self.extent
    def get_actor_enable_collision(self):return True


def setup(bodies,held=None):
    frame,_,_=fixture();g=frame.G
    g.D=dict(aircraft38=LAYOUT['aircraft38'],instances=[])
    g.source=lambda p:[p.x/100,-p.y/100,p.z/100]
    g.P=frame.P;g.P.STATE=dict(pawn=N(get_actor_location=lambda:V(-5000,1000,162)),world=object(),
                            movables={AIR.L1:dict(progress=0.,target=0.)})
    g.flight39={'frame':frame};g.S.update(physics=dict(bodies),actors=dict(bodies),held=held,doors={})
    g.u.GameplayStatics=N(get_all_actors_of_class=lambda world,cls:list(bodies.values()));g.u.Actor=object
    g.say=Mock();g.open_door=Mock()
    return frame,g


class EnvelopeTests(unittest.TestCase):
    def setUp(self):self.envelope=pressure_envelope(PLANE_DATA,16.)

    def test_exact_metadata_bounds_and_translated_manifest_agree(self):
        cells={q['name']:q for q in self.envelope['cells']}
        for a,b in zip(cells['Cabin deck']['rect'],[13.62,18.38,0.,35.1]):self.assertAlmostEqual(a,b)
        for a,b in zip(cells['Cockpit deck']['rect'],[14.04,17.96,-5.4,0.]):self.assertAlmostEqual(a,b)
        self.assertEqual(cells['Cabin deck']['ceiling'],2.4)
        self.assertEqual(cells['Forward lower cargo hold']['rect'],[14.6,17.4,1.3,34.65])
        self.assertAlmostEqual(cells['Forward lower cargo hold']['floor'],-2.05)
        self.assertAlmostEqual(cells['Forward lower cargo hold']['ceiling'],-.12)
        translated=AIR.translate_plane_data(PLANE_DATA,16.)
        other=pressure_envelope(translated,16.)
        for a,b in zip(other['cells'],self.envelope['cells']):
            self.assertEqual(a['name'],b['name'])
            for x,y in zip(a['rect'],b['rect']):self.assertAlmostEqual(x,y)
            self.assertEqual(a.get('slope'),b.get('slope'));self.assertEqual(a.get('floor'),b.get('floor'));self.assertEqual(a['ceiling'],b['ceiling'])

    def test_actual_cabin_cockpit_hold_and_stairs_are_covered(self):
        for point in ([16,10,1],[16,-3.8,1.62],[16,20,-1.],[14.2,2.8,-1.1]):
            with self.subTest(point=point):self.assertTrue(contains_point(self.envelope,point))

    def test_docking_cab_outside_side_roof_tail_and_underfloor_are_excluded(self):
        for point in ([12.5,.675,1],[12.5,17,1],[16,10,2.5],[16,40,1],[16,10,-3.2],[14.2,10,-1]):
            with self.subTest(point=point):self.assertFalse(contains_point(self.envelope,point))

    def test_complete_body_cannot_bridge_structural_deck_gap(self):
        # Both top and bottom corners can be in legal volumes while the middle
        # intersects the real deck between hold roof and passenger floor.
        bounds=[[15.8,19.8,-.5],[16.2,20.2,.5]]
        self.assertTrue(contains_point(self.envelope,bounds[0]))
        self.assertTrue(contains_point(self.envelope,bounds[1]))
        self.assertFalse(contains_box(self.envelope,bounds))

    def test_fully_inside_bag_allowed_but_l1_straddling_bag_is_external(self):
        inside=BoundsBody([16,-1.5,1.2]);straddling=BoundsBody([14.15,.675,1.],(.6,.5,.8))
        frame,g=setup({'inside':inside,'straddling':straddling})
        self.assertTrue(frame.body_fully_inside(inside))
        self.assertTrue(frame.body_inside(straddling),'Its COM is aboard, so COM alone is insufficient')
        self.assertTrue(contains_box(frame.envelope,frame.body_source_bounds(straddling)))
        self.assertFalse(frame.body_fully_inside(straddling))
        self.assertTrue(all(inside.bounds_calls+straddling.bounds_calls),'Query actual colliding bounds')

    def test_parked_exit_releases_record_with_zero_carrier_no_pose_or_impulse(self):
        frame,bag,_=fixture();frame.G.S['held']='bag';frame.refresh_props(0,True)
        bag.velocity=V(900,0,0);bag.p=V(2000,-1730,120)
        before=bag.pose_writes;frame.refresh_props(.25)
        self.assertNotIn('bag',frame.prop_records)
        self.assertEqual(bag.velocity.x,900.);self.assertEqual(bag.pose_writes,before)
        frame.refresh_props(.25);self.assertEqual(bag.velocity.x,900.)


class BridgePropTests(unittest.TestCase):
    def occupied(self,bodies,held=None):
        frame,g=setup(bodies,held)
        with patch.object(AIR,'G',g),patch.object(AIR,'S',dict(moving=False)):
            return AIR._bridge_occupied(),AIR.request_bridge(True)[0]

    def test_loose_and_held_props_on_docking_cab_prevent_retraction(self):
        for held in (None,'bag'):
            with self.subTest(held=held):
                occupied,allowed=self.occupied({'bag':BoundsBody([12.5,.675,.7])},held)
                self.assertTrue(occupied);self.assertFalse(allowed)

    def test_body_crossing_bridge_edge_blocks_even_when_com_is_outside(self):
        # Cab's north side is y1.925; the suitcase straddles that real edge.
        occupied,allowed=self.occupied({'bag':BoundsBody([12.5,2.1,.7],(.5,.6,.8))})
        self.assertTrue(occupied);self.assertFalse(allowed)

    def test_fully_aboard_and_under_apron_props_do_not_block_bridge(self):
        for point in ([16,-1.5,1.2],[12.5,.675,-3.3]):
            with self.subTest(point=point):
                occupied,allowed=self.occupied({'bag':BoundsBody(point)},'bag')
                self.assertFalse(occupied);self.assertTrue(allowed)

    def test_bent_bridge_does_not_create_a_phantom_box(self):
        zones=LAYOUT['aircraft38']['bridge']['floor_polygons']
        self.assertFalse(bridge_overlap([[5.9,-3.1,.1],[6.1,-2.9,1.]],zones))

    def test_departure_only_exempts_the_complete_inside_body(self):
        bodies={'inside':BoundsBody([16,-1.5,1.2]),'bridge':BoundsBody([12.5,.675,.7])}
        frame,g=setup(bodies,'bridge');frame.prop_records={n:dict(actor=a) for n,a in bodies.items()}
        def obstacles(u,actors,ignore_names=None):
            return [dict(name=n,bounds=AIR._actor_bounds(a)) for n,a in bodies.items() if n not in ignore_names]
        with patch.object(AIR,'G',g),patch.object(AIR,'collect_airport_obstacles',side_effect=obstacles) as collect:
            result=AIR.departure_clearance()
            self.assertFalse(result['clear']);self.assertEqual([q['name'] for q in result['blocking']],['bridge'])
            self.assertEqual(collect.call_args.kwargs['ignore_names'],{'inside'})


if __name__=='__main__':unittest.main(verbosity=2)
