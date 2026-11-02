"""Pure source/runtime-contract tests. Not native visual or performance proof."""
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from rendering38 import PROFILE,light_specs,ambient_specs,write_constant_hdr
from coplanar38 import find_conflicts,old_conflict_fixture


def face(part,xy,z=3.4,normal=(0,0,-1),asset=None):
    x0,x1,y0,y1=xy
    return dict(actor=part,part=part,asset=asset or part,normal=list(normal),
        vertices=[[x0,y0,z],[x0,y1,z],[x1,y1,z],[x1,y0,z]])


def sample_layout():
    return dict(revision=38,zones=[dict(id='welcome',rect=[-10,0,-6,0],ceiling_m=3.6),
        dict(id='task',rect=[-10,0,0,6],ceiling_m=3.6)],lights=[
        dict(zone='welcome',position=[-7,-3,3.45],lumens=3000,role='welcome',casts_shadows=False),
        dict(zone='task',position=[-7,3,3.45],lumens=3900,role='screening_task'),
        dict(name='Bridge38 warm practical A0',position=[2,0,2.42],watts=350,
             role='bridge_practical',follow_actor='Bridge38 bank A sleeve 00',local_point=[2.45,0,2.42])])


class GeometryTests(unittest.TestCase):
    def test_real_old_caps_fail_cross_asset_check(self):
        inventory=json.loads((HERE.parents[1]/'Audits/SourceInventory38.json').read_text())
        result=find_conflicts(old_conflict_fixture(inventory))
        pairs=[{p['asset'] for p in q['parts']} for q in result['conflicts']]
        self.assertEqual(result['status'],'FAIL')
        self.assertIn({'SM_AP_Roof35','SM_AP_Room37_gate08foyer'},pairs)
        self.assertIn({'SM_AP_Roof35','SM_AP_Room37_cafefoyer'},pairs)
        (HERE/'OldCapRegression38.json').write_text(json.dumps(result,indent=2))

    def test_contact_edges_opposite_faces_and_separation_pass(self):
        surfaces=[face('floorA',(0,2,0,2),0,(0,0,1)),face('floorB',(2,4,0,2),0,(0,0,1)),
            face('ceiling',(0,4,0,2),3.4),face('roof',(0,4,0,2),3.44),
            face('contact',(0,4,0,2),3.4,(0,0,1))]
        self.assertEqual(find_conflicts(surfaces)['status'],'PASS')

    def test_broad_aabb_overlap_without_polygon_overlap_passes(self):
        a=dict(actor='a',part='a',asset='a',normal=[0,0,1],vertices=[[0,0,0],[2,0,0],[0,2,0]])
        b=dict(actor='b',part='b',asset='b',normal=[0,0,1],vertices=[[2,2,0],[2,.5,0],[.5,2,0]])
        self.assertEqual(find_conflicts([a,b])['status'],'PASS')

    def test_depth_tolerance_catches_near_surface_and_area_threshold(self):
        a=face('a',(0,2,0,2));b=face('b',(1,3,1,3),3.4005)
        result=find_conflicts([a,b])
        self.assertEqual(result['status'],'FAIL');self.assertAlmostEqual(result['conflicts'][0]['area_m2'],1)
        b['vertices']=[[x,y,z+.002] for x,y,z in b['vertices']]
        self.assertEqual(find_conflicts([a,b])['status'],'PASS')

    def test_owner_pair_cannot_merge_different_planes_or_normals(self):
        a=face('a',(0,2,0,2),3.4);b=face('b',(1,3,1,3),3.4)
        aa=face('a',(0,2,0,2),4.4);bb=face('b',(1,3,1,3),4.4)
        side_a=dict(a,normal=[1,0,0],vertices=[[0,0,0],[0,2,0],[0,2,2],[0,0,2]])
        side_b=dict(b,normal=[1,0,0],vertices=[[0,1,1],[0,3,1],[0,3,3],[0,1,3]])
        hits=find_conflicts([a,b,aa,bb,side_a,side_b])['conflicts']
        self.assertEqual(len(hits),3)
        self.assertEqual(sorted(q['axis'] for q in hits),['x','z','z'])
        self.assertEqual(sorted(q['area_m2'] for q in hits),[1,1,1])
        self.assertTrue(all('overlap_world_min' in q and q['overlap_sample_points'] for q in hits))


class LightTests(unittest.TestCase):
    def test_roles_dont_depend_on_iteration_index(self):
        D=sample_layout();one={q['name']:q for q in light_specs(D) if q.get('follow_actor')}
        D['lights'].reverse();two={q['name']:q for q in light_specs(D) if q.get('follow_actor')}
        self.assertEqual(one,two)
        for q in light_specs(D):
            if q['category']=='practical_key':self.assertTrue(q['casts_shadows'])

    def test_no_isolated_upward_lights_and_bounded_indirect_regions(self):
        D=sample_layout();lights=light_specs(D)
        self.assertTrue(all(q['direction']==[0,0,-1] for q in lights))
        self.assertFalse(any(q['category']=='bounded_ambient_fill' for q in lights))
        ambient=ambient_specs(D);self.assertEqual(len(ambient),len(D['zones']))
        zones={z['id']:z for z in D['zones']}
        for q in ambient:
            x0,x1,y0,y1=zones[q['zone']]['rect'];a,b,c,d=q['rect']
            self.assertGreater(a,x0);self.assertLess(b,x1);self.assertGreater(c,y0);self.assertLess(d,y1)
            self.assertLessEqual(q['intensity'],.26);self.assertGreaterEqual(q['intensity'],.20)
            self.assertEqual(q['cubemap'],'T_AP38_NeutralIndirect')

    def test_hdr_has_zero_spatial_or_angular_variance(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            path=Path(tmp)/'ambient.hdr';r=write_constant_hdr(path)
            data=path.read_bytes();header,body=data.split(b'-Y 32 +X 64\n',1)
            self.assertIn(b'FORMAT=32-bit_rle_rgbe',header)
            self.assertEqual(len(body),32*12)
            rows=[body[i*12:(i+1)*12] for i in range(32)]
            self.assertTrue(all(row==rows[0] for row in rows))
            self.assertEqual(rows[0][:4],bytes([2,2,0,64]))
            channels=[rows[0][i+1] for i in (4,6,8,10)]
            decoded=[v*2**(channels[3]-136) for v in channels[:3]]
            self.assertEqual(decoded,[1.,1.,1.]);self.assertEqual(r['angular_variance'],0)

    def test_no_resolution_escalation(self):
        self.assertEqual(PROFILE['cvars']['r.ScreenPercentage'],100)
        self.assertEqual(PROFILE['cvars']['r.TemporalAASamples'],16)
        self.assertEqual(PROFILE['cvars']['r.TemporalAACurrentFrameWeight'],.1)


class RuntimeTests(unittest.TestCase):
    def test_final_authority_measures_and_intercepts_legacy(self):
        values=dict(PROFILE['cvars']);values.update({'r.TemporalAASamples':8,'r.TemporalAACurrentFrameWeight':.35})
        viewport=[1600,900];commands=[];base_ticks=[]
        def console(world,command,pc):
            commands.append(command)
            k,v=command.split(' ',1)
            if k=='r.SetRes':viewport[:]=[1920,1080]
            else:values[k]=float(v)
        fake=types.SimpleNamespace(SystemLibrary=types.SimpleNamespace(
            execute_console_command=console,get_console_variable_float_value=lambda k:values[k]))
        saved_u=sys.modules.get('unreal');saved_c=sys.modules.get('airport_clarity26')
        sys.modules['unreal']=fake
        legacy=types.SimpleNamespace(S={},apply_profile=lambda n:None)
        sys.modules['airport_clarity26']=legacy
        try:
            sys.modules.pop('airport_rendering38',None)
            runtime=importlib.import_module('airport_rendering38')
            with tempfile.TemporaryDirectory(dir=HERE) as tmp:
                out=Path(tmp);(out/'ArtBible').mkdir()
                path=out/'ArtBible/RuntimeStatus.json'
                def write():path.write_text(json.dumps(dict(profile='FALSE OLD LABEL',seated='Captain',ready=True)))
                P=types.SimpleNamespace(ROOT=out,write=write,configure=lambda:values.update({'r.TemporalAASamples':8}),
                    STATE=dict(world=object(),pc=types.SimpleNamespace(get_viewport_size=lambda:viewport)))
                G=types.SimpleNamespace(D=sample_layout(),R=out,P=P,physics=lambda dt:base_ticks.append(dt),event=lambda *a,**k:None)
                runtime.install(G)
                self.assertEqual(values['r.TemporalAASamples'],16)
                legacy.apply_profile('Calm31')
                self.assertEqual(values['r.TemporalAACurrentFrameWeight'],.1)
                P.configure();self.assertEqual(values['r.TemporalAASamples'],16)
                P.write();status=json.loads(path.read_text())
                self.assertEqual(status['seated'],'Captain')
                self.assertEqual(status['rendering_measured38']['viewport'],[1920,1080])
                self.assertNotIn('FALSE OLD',status['profile'])
                values['r.TemporalAACurrentFrameWeight']=.35;runtime.S['checked']=-1e9
                G.physics(.016)
                self.assertEqual(base_ticks,[.016]);self.assertEqual(values['r.TemporalAACurrentFrameWeight'],.1)
                actual=json.loads((out/'ArtBible/RenderingSession38.json').read_text())
                self.assertEqual(actual['actual']['settings']['r.TemporalAASamples'],16)
                self.assertEqual(actual['status'],'READY')
        finally:
            if saved_u is None:sys.modules.pop('unreal',None)
            else:sys.modules['unreal']=saved_u
            if saved_c is None:sys.modules.pop('airport_clarity26',None)
            else:sys.modules['airport_clarity26']=saved_c


class NativeRefinementContractTests(unittest.TestCase):
    def test_hdr_import_uses_only_documented_reflected_factory_fields(self):
        import native38_rendering as native
        class Properties:
            allowed=None
            def __init__(self):self.props={}
            def set_editor_property(self,k,v):
                if self.allowed is not None and k not in self.allowed:raise ValueError('Unreflected field '+k)
                self.props[k]=v
        class Factory(Properties):allowed={'supported_class','create_material'}
        class Cube(Properties):pass
        class Task(Properties):pass
        cube=Cube();loaded={};tasks=[]
        def importer(xs):
            tasks.extend(xs)
            for t in xs:
                self.assertIs(t.props['factory'].props['supported_class'],Cube)
                self.assertFalse(t.props['factory'].props['create_material'])
                self.assertTrue(t.props['automated'])
                self.assertTrue(t.props['filename'].endswith('.hdr'))
                loaded[t.props['destination_path']+'/'+t.props['destination_name']]=cube
        U=types.SimpleNamespace(load_asset=lambda p:loaded.get(p),TextureFactory=Factory,TextureCube=Cube,
            AssetImportTask=Task,AssetToolsHelpers=types.SimpleNamespace(get_asset_tools=lambda:types.SimpleNamespace(import_asset_tasks=importer)),
            TextureCompressionSettings=types.SimpleNamespace(TC_HDR='HDR'),
            EditorAssetLibrary=types.SimpleNamespace(save_loaded_asset=lambda tex:True))
        ctx=types.SimpleNamespace(u=U,B='/Game/Airport38')
        result,meta=native._indirect_cube(ctx)
        self.assertIs(result,cube);self.assertEqual(len(tasks),1)
        self.assertFalse(cube.props['srgb']);self.assertTrue(cube.props['never_stream'])
        # An already existing wrong-class import must fail, never be silently
        # accepted as a "good" native ambient source or remove old map lights.
        loaded[meta['asset']]=object()
        with self.assertRaises(RuntimeError):native._indirect_cube(ctx)

    def test_targeted_refinement_preserves_direct_keys_exposure_and_bridge(self):
        import native38_rendering as native
        class Settings:
            def __init__(self):self.props={'auto_exposure_min_brightness':6.,'film_grain_intensity':0.}
            def set_editor_property(self,k,v):self.props[k]=v
        class Actor:
            def __init__(self,name):self.name=name;self.props={'settings':Settings()}
            def get_actor_label(self):return self.name
            def get_editor_property(self,k):return self.props[k]
            def set_editor_property(self,k,v):self.props[k]=v
        class Rect(Actor):pass
        class PP(Actor):pass
        D=sample_layout();pool=Rect('AP38 bounded ceiling bounce welcome 0 0')
        direct=Rect('AP38 practical 000 welcome');bridge=Rect('Bridge38 warm practical A0')
        actors=[pool,direct,bridge]+[PP('AP38 warm grade '+z['id']) for z in D['zones']]
        removed=[];cube=object()
        U=types.SimpleNamespace(RectLight=Rect,PostProcessVolume=PP,LinearColor=lambda *args:args)
        EA=types.SimpleNamespace(get_all_level_actors=lambda:list(actors),destroy_actor=lambda a:removed.append(a.name))
        old=native._indirect_cube;native._indirect_cube=lambda ctx:(cube,{'mock':True})
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as tmp:
                report=native.refine_ceiling_fill(types.SimpleNamespace(u=U,EA=EA,D=D,R=Path(tmp)))
                self.assertEqual(removed,[pool.name]);self.assertEqual(len(report['regions']),2)
                for a in actors:
                    if isinstance(a,PP):
                        s=a.props['settings'].props
                        self.assertIs(s['ambient_cubemap'],cube)
                        self.assertEqual(s['ambient_cubemap_intensity'],.22)
                        self.assertEqual(s['auto_exposure_min_brightness'],6.)
                        self.assertEqual(s['film_grain_intensity'],0.)
        finally:native._indirect_cube=old


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    (HERE/'TestResults38.json').write_text(json.dumps(dict(status='PASS' if result.wasSuccessful() else 'FAIL',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        scope='pure math, real old-plane regression, light containment and mocked runtime contracts; native images/performance pending'),indent=2))
    raise SystemExit(not result.wasSuccessful())
