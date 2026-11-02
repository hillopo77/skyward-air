"""Bounded staged-harness guards. Does not claim native belt input success."""
import importlib.util,json,math,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock,patch
from test_props39 import V

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'SourceAssets/assemblies41_review.py'
spec=importlib.util.spec_from_file_location('assemblies41_review_test',SOURCE)
H=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'unreal':N()}):spec.loader.exec_module(H)
RECORDS=json.loads((HERE.parents[2]/'Exports/airport_layout.json').read_text())['repair38']['business_belt40']['records']


def game():
    setter=lambda *args:None;window=lambda *args:None
    p=N(DATA=dict(window41_prepared=True,business_belt40_prepared=True),set_control_state=setter,_business_belt40_setter=setter,
        _apply_movable=window,_window41_adapter=window)
    return N(D=dict(repair38=dict(business_belt40=dict(records=RECORDS)),aircraft38=dict(offset=[16,0,0])),P=p,flight39=dict(frame=object()))


class HarnessTests(unittest.TestCase):
    def test_requires_real_final_install_order_and_four_records(self):
        g=game();self.assertEqual(H.requirements(g),RECORDS)
        for field in ('window41_prepared','business_belt40_prepared'):
            with self.subTest(field=field),patch.dict(g.P.DATA,{field:False}):
                with self.assertRaises(RuntimeError):H.requirements(g)
        g.P.set_control_state=lambda *args:None
        with self.assertRaises(RuntimeError):H.requirements(g)

    def test_belt_evidence_needs_actual_visibility_hinge_and_native_lid_pose(self):
        r=RECORDS[0];hidden={r['worn_actor']:False,r['stowed_actor']:True};offset=[0.]
        hinge=r['worn_hinge']
        actor=N(get_actor_location=lambda:V((hinge[0]+offset[0])*100,-hinge[1]*100,hinge[2]*100))
        actors={r['control']:actor,**{n:N(get_editor_property=lambda key,name=n:hidden[name]) for n in hidden}}
        snapshot={'passed':True,'targets':[dict(property='rotation',passed=True)]}
        p=N(STATE=dict(controls={r['control']:dict(state=0)},actors=actors),control_snapshot=lambda name:snapshot)
        g=N(P=p,source=lambda q:[q.x/100,-q.y/100,q.z/100],flight39={'frame':N(reference=lambda q:q)})
        self.assertTrue(H.belt_evidence(g,r,0)['passed'])
        hidden[r['worn_actor']]=True;self.assertFalse(H.belt_evidence(g,r,0)['passed']);hidden[r['worn_actor']]=False
        offset[0]=.02;self.assertFalse(H.belt_evidence(g,r,0)['passed']);offset[0]=0
        snapshot['passed']=False;self.assertFalse(H.belt_evidence(g,r,0)['passed'])

    def test_opaque_wall_or_wrong_target_never_dispatches_normal_use(self):
        item=dict(actor='Business belt release 112');control=N(set_control_rotation=Mock())
        pawn=N(get_actor_location=lambda:V());near=[item];visible=[False]
        p=N(STATE=dict(pawn=pawn,pc=control),nearest=lambda:near[0],interaction_visible=lambda q:visible[0],interaction_point=lambda q:V(0,100,0))
        g=N(P=p,use_nearest=Mock(),source=lambda q:q.to_tuple(),flight39={'frame':N(reference=lambda q:q)})
        native=N(MathLibrary=N(find_look_at_rotation=lambda a,b:object()))
        with patch.object(H,'G',g),patch.object(H,'u',native),patch.object(H,'S',dict(actions=[],start=time.monotonic())):
            self.assertFalse(H.aim_use(item));g.use_nearest.assert_not_called()
            visible[0]=True;near[0]=dict(actor='Opaque partition')
            self.assertFalse(H.aim_use(item));g.use_nearest.assert_not_called()
            near[0]=item;self.assertTrue(H.aim_use(item));g.use_nearest.assert_called_once_with(False)

    def test_photo_free_mode_advances_without_creating_fake_capture(self):
        state=dict(screenshots=False,i=0,steps=['photo','next'],checks=[],captures=[],actions=[],setup=[],output='Fixture.json')
        with patch.object(H,'S',state),patch.object(H,'save'):
            H.photo('Fixture',[],[])
        self.assertEqual(state['i'],1);self.assertEqual(state['captures'],[])

    def test_bin_evidence_requires_actual_78degree_native_pose_and_fixed_hinge(self):
        class Quat:
            def __init__(self,x=0.,y=0.,z=0.,w=1.):self.x=x;self.y=y;self.z=z;self.w=w
            def rotator(self):return rotation(math.degrees(2*math.atan2(self.y,self.w)))
        def rotation(degrees):
            return N(pitch=degrees,yaw=0.,roll=0.,quaternion=lambda:Quat(y=math.sin(math.radians(degrees)/2),w=math.cos(math.radians(degrees)/2)))
        angle=[-78.];hinge=[0.]
        a=N(get_actor_rotation=lambda:rotation(angle[0]),get_actor_location=lambda:V(hinge[0],0,0))
        q=dict(actor='Overhead bin L04',motion=dict(axis='y',amount_degrees=-78))
        moving=dict(actor=a,closed_rotation=Quat(),closed_location=V(),progress=1.,target=1.)
        p=N(STATE=dict(movables={q['actor']:moving}),_quat_product=lambda a,b:b,
            _source_quat=lambda axis,d:rotation(d).quaternion())
        g=N(P=p,flight39={'frame':N(rotation=lambda q:q,reference_rotation=lambda q:q,world=lambda p:p)})
        with patch.object(H,'G',g),patch.object(H,'u',N(Quat=Quat)):
            evidence=H.bin_evidence(q,1.);self.assertTrue(evidence['passed']);self.assertAlmostEqual(evidence['measured_relative_angle_degrees'],-78.)
            angle[0]=-30.;self.assertFalse(H.bin_evidence(q,1.)['passed']);angle[0]=-78.
            hinge[0]=1.;self.assertFalse(H.bin_evidence(q,1.)['passed'])

    def test_independent_phase_failure_is_recorded_and_continues(self):
        state=dict(i=0,phase='window_closed',steps=['window_closed','bin_open'],checks=[],actions=[],setup=[],captures=[])
        with patch.object(H,'S',state),patch.object(H,'save'):
            H.phase_error('native fixture failure')
        self.assertEqual(state['phase'],'bin_open');self.assertFalse(state['checks'][0]['passed'])
        self.assertEqual(state['checks'][0]['error'],'native fixture failure')

    def test_start_labels_all_setup_and_does_not_launch_or_install_gameplay(self):
        g=game();r=RECORDS[0]
        window=dict(actor='Window shade fixture L18',kind='movable',point=[13.7,5.2,1.11],window41=True)
        overhead=dict(actor='Overhead bin L04',kind='movable',point=[14.6,4.7,2.3],motion=dict(axis='y',amount_degrees=-78))
        g.P.STATE=dict(items=[dict(actor=r['control'],kind='control'),window,overhead])
        g.S=dict(physics={'Physical luggage 05':object()},actors={'Physical luggage 05':object()},
                 actor_specs={'Physical luggage 05':dict(asset='SM_AP_Bag')})
        g.journey38={'state':dict(registered_bags=set())};g.flight39['runtime']={'chase':object()}
        native=N(register_slate_post_tick_callback=Mock(return_value='test-callback'))
        with tempfile.TemporaryDirectory(dir=HERE,prefix='assemblies41_unit_') as folder:
            self.assertEqual(Path(folder).resolve().parent,HERE.resolve())
            g.R=Path(folder);(g.R/'ArtBible').mkdir()
            (g.R/'ArtBible/InstalledRuntime39.json').write_text(json.dumps(dict(source_sha256='fixture-installed')))
            (g.R/'ArtBible/Assemblies41Source.json').write_text(json.dumps(dict(source_sha256='fixture-source')))
            with patch.object(H,'G',None),patch.object(H,'S',{}),patch.object(H,'u',native),patch.object(H.importlib,'import_module',return_value=N(__file__=str(SOURCE))):
                result=H.start(g,screenshots=False,quit_when_done=False)
                report=json.loads((g.R/'ArtBible/Assemblies41QA.json').read_text())
                self.assertEqual(result['phases'],30)
                self.assertEqual(report['physical_walk_steps'],0)
                self.assertEqual(report['setup'][0]['kind'],'direct_journey_flags_for_independent_staged_cases')
                self.assertEqual(report['captures'],[])
                self.assertEqual(report['context']['assemblies41_source'],'fixture-source')
                self.assertEqual(len(report['context']['live_runtime_sha256']),8)
                native.register_slate_post_tick_callback.assert_called_once()


if __name__=='__main__':unittest.main(verbosity=2)
