"""Real-manifest coordinate and complete-component clearance acceptance tests."""
import copy,json,math,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import airport_airside38 as runtime
from airside_math38 import *

W=Path(__file__).resolve().parents[5]
MANIFEST=W/'outputs/SkywardAir/Revision18/Exports/manifest.json'

def points_walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('delta','direction','offset','end_local','right','up','size','scale','rotation','translation_states'):yield k,copy.deepcopy(v)
            else:yield from points_walk(v)
    elif isinstance(x,list):
        for v in x:yield from points_walk(v)

class AirsideAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads(MANIFEST.read_text(encoding='utf-8'))['scenes']['L_Plane_Reference']
    def test_real_manifest_translation_preserves_every_local_delta(self):
        before=copy.deepcopy(self.data);out=runtime.translate_plane_data(before)
        self.assertEqual(before,self.data,'No mutation of saved manifest data')
        comparable={k:v for k,v in out.items() if k!='airport38_translation'}
        self.assertEqual(list(points_walk(before)),list(points_walk(comparable)))
        self.assertGreater(out['airport38_translation']['counts']['points'],2500)
        for k in ('instances','cameras','lights','labels','navigation_bounds'):
            for a,b in zip(before[k],out[k]):
                self.assertAlmostEqual(b['location'][0],a['location'][0]+16)
                self.assertEqual(b['location'][1:],a['location'][1:])
        for a,b in zip(before['interactions'],out['interactions']):
            for key in ('point','location','inside_point','validation_approach','open_validation_approach'):
                if key in a:self.assertEqual(b[key],[a[key][0]+16,*a[key][1:]])
            for old,new in zip(a.get('roller_parts',[]),b.get('roller_parts',[])):
                self.assertEqual(new['closed_location'],[old['closed_location'][0]+16,*old['closed_location'][1:]])
            for old,new in zip(a.get('kinematic_links',[]),b.get('kinematic_links',[])):
                self.assertEqual(new['start'],[old['start'][0]+16,*old['start'][1:]])
    def test_layout_absolute_inspection_seats_and_ranges(self):
        out=runtime.translate_plane_data(self.data)
        for a,b in zip(self.data['layout']['walk_tests'],out['layout']['walk_tests']):
            self.assertEqual(b['start'],[a['start'][0]+16,*a['start'][1:]])
            for p,q in zip(a.get('path',[]),b.get('path',[])):self.assertEqual(q,[p[0]+16,*p[1:]])
        for a,b in zip(self.data['layout']['barrier_tests'],out['layout']['barrier_tests']):
            self.assertEqual(b['direction'],a['direction'])
            if a['axis']=='x':self.assertEqual(b['closed_range'],[x+16 for x in a['closed_range']])
        for name,p in self.data['layout']['seat_approaches'].items():self.assertEqual(out['layout']['seat_approaches'][name],[p[0]+16,*p[1:]])
        self.assertEqual(out['layout']['cargo_families'],self.data['layout']['cargo_families'])
        self.assertEqual(out['layout']['crew_room'],self.data['layout']['crew_room'])
        self.assertEqual(out['layout']['lavatory_clear_size_m'],self.data['layout']['lavatory_clear_size_m'])
    def test_vector_conversion_and_idempotence(self):
        class P:DATA=self.data;vector=staticmethod(lambda p:(100*p[0],-100*p[1],100*p[2]))
        convert=P.vector;runtime.prepare_plane(P,{'aircraft38':{'offset':[16,0,0]}})
        self.assertIs(P.vector,convert)
        for a,b in zip(P.vector([-.14,0,.025]),(-14.,0,2.5)):self.assertAlmostEqual(a,b)
        self.assertIs(runtime.translate_plane_data(P.DATA),P.DATA)
    def test_stow_pose_full_bank_and_cab(self):
        d=bridge_pose(0);s=bridge_pose(1)
        for a,b in zip(d['Bridge38 docking cab']['location'][:2],NOSE_CAB):self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(d['Bridge38 bank B sleeve 04']['location'][0]+SLEEVE_LENGTH*math.cos(math.radians(d['Bridge38 bank B sleeve 04']['rotation'])),NOSE_CAB[0])
        for name,p in s.items():
            if 'lift' not in name:self.assertAlmostEqual(p['location'][0],PIVOT[0])
        self.assertEqual(s['Bridge38 docking cab']['rotation'],-90)
        # Conservative sleeve/cab/roof/handrail extents, not only centrelines.
        for name,p in s.items():
            if 'lift' in name:continue
            bounds=([-1.,-.7,0],[1.,.7,.62]) if 'truck' in name else ([-.06,-1.72,-.3],[3.5,1.72,2.95])
            bb=posed_bounds(bounds,p)
            self.assertLess(bb[1][0],-10.3)
            self.assertFalse(intersects(bb,swept_bounds()))
    def test_all_four_carrier_wheels_rest_on_stowed_grade(self):
        for phase in (0,1):
            for name,pose in bridge_pose(phase).items():
                if 'truck' not in name:continue
                for x in (-.68,.68):
                    for y in (-.55,.55):
                        point=[x,y,0]
                        bb=posed_bounds([point,point],pose);p=bb[0]
                        self.assertAlmostEqual(p[2],apron_height(p[0],p[1]),places=5)
    def test_continuous_sweep_catches_between_samples_and_misses_off_route_hangar(self):
        case=[dict(name='thin obstacle between samples',bounds=[[3,-51.001,0],[3.01,-51,1]]),dict(name='hangar behind',bounds=[[19.8,95.96,-3.7],[72.2,158.03,12]])]
        q=validate_sweep(case)
        self.assertFalse(q['clear']);self.assertEqual([b['name'] for b in q['blocking']],['thin obstacle between samples'])
    def test_route_is_bent_and_bounded_without_phantom_rectangle(self):
        zones=floor_polygons()
        for a,b in zip([(-14,.675),PIVOT,ELBOW,NOSE_CAB],[PIVOT,ELBOW,NOSE_CAB,THRESHOLD]):
            for i in range(101):
                p=(lerp(a[0],b[0],i/100),lerp(a[1],b[1],i/100))
                self.assertTrue(any(in_polygon(p,z['polygon']) for z in zones),p)
        self.assertFalse(any(in_polygon((6,-3),z['polygon']) for z in zones))
        self.assertLess(abs(apron_height(-11,56)+3.7),1e-9)
    def test_departure_and_retraction_refuse_unsafe_states(self):
        messages=[];g=SimpleNamespace(P=SimpleNamespace(STATE={'movables':{L1:{'progress':1.,'target':1.}}}),say=messages.append)
        with patch.object(runtime,'G',g),patch.object(runtime,'S',{'fraction':0.,'moving':False}),patch.object(runtime,'_bridge_occupied',return_value=False),patch.object(runtime,'_close_terminal') as close:
            self.assertFalse(runtime.request_bridge(True)[0]);close.assert_not_called()
            g.P.STATE['movables'][L1]={'progress':0.,'target':0.}
            with patch.object(runtime,'_bridge_occupied',return_value=True):self.assertFalse(runtime.request_bridge(True)[0])
            self.assertTrue(runtime.request_bridge(True)[0]);close.assert_called_once()
            self.assertFalse(runtime.can_depart()[0],'A closing terminal door does not mean the long bridge has cleared the wing')
            runtime.S.update(fraction=1.,moving=False,pending_stow=False)
            with patch.object(runtime,'departure_clearance',return_value={'clear':False,'blocking':[{'name':'baggage tug'}]}):self.assertFalse(runtime.can_depart()[0])
            with patch.object(runtime,'departure_clearance',return_value={'clear':True,'blocking':[]}):self.assertTrue(runtime.can_depart()[0])

if __name__=='__main__':unittest.main(verbosity=2)

