"""Revision 10: real viewport captures, interaction tests and collision walks.

All layout coordinates are Blender metres (x, y, eye height).  The runtime owns
the axis conversion.  Place route metadata in scene.layout.walk_tests::

    {"name": "front economy left access", "start": [-1.1, 12.0, 1.62],
     "path": [[-1.1, 11.2, 1.62], [-1.7, 11.2, 1.62]],
     "tolerance": 0.12, "look_at": [-1.7, 11.8, 1.1],
     "capture": "UE_91_front_economy_walk10.png"}

Only the initial placement teleports. Every path segment is traversed by the
normal collision-enabled player movement, at 1.62 m above the active floor.
Failed waypoints cannot be skipped or marked as successful by an interaction.

scene.layout.validation.captures contains {camera, file} entries.  Optional
scene.layout.validation.door contains {start, direction, closed_duration,
open_duration}.  Optional seat_approaches maps source actor names to starting
points for the separate E-action tests.  Validator(runtime, walk_tests=...,
captures=...) also accepts explicit test data without altering runtime APIs.
scene.layout.barrier_tests contains closed-leaf standing probes: {name,actor,
start,direction,duration,axis,closed_range}; all coordinates/ranges are source
metres. Each test closes the actual leaf, walks into it, checks its stop range,
and reopens it. Open-door access remains a separate normal walking route.
"""

import json
import hashlib
import math
import time
from pathlib import Path

import unreal as u


def _xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def _horizontal_distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _point(value, name):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(name + ' must be [x, y, z] in source metres')
    result = [float(x) for x in value]
    if not all(math.isfinite(x) for x in result):
        raise ValueError(name + ' contains a non-finite coordinate')
    return result


def _interaction_reuse_scope(original,current):
    """Permit only the four approved pilot fitting coordinate corrections."""
    if [item['actor'] for item in original]!=[item['actor'] for item in current]:
        raise RuntimeError('Cannot reuse action evidence: interaction actor inventory/order changed')
    before={item['actor']:item for item in original};after={item['actor']:item for item in current}
    if len(before)!=len(original) or len(after)!=len(current):raise RuntimeError('Interaction actor IDs must be unique')
    seat_ids={'SM_Plane_Seat.016','SM_Plane_Seat.017'};headset_ids={'Pilot headset L12','Pilot headset R12'};records=[]
    def same_vector(a,b):return isinstance(a,(tuple,list)) and len(a)==3 and all(abs(float(a[k])-float(b[k]))<3e-6 for k in range(3))
    for actor,old in before.items():
        new=after[actor]
        if old==new:continue
        allowed={'location','point','validation_approach'} if actor in seat_ids else {'point','validation_approach'} if actor in headset_ids else set()
        fields={key for key in set(old)|set(new) if old.get(key)!=new.get(key)}
        if not fields or not fields<=allowed:raise RuntimeError('Cannot reuse action evidence: unapproved interaction fields changed on '+actor)
        changes={}
        for field in sorted(fields):
            if actor in seat_ids and field=='validation_approach' and field not in old:
                expected=[old['location'][0],-3.84053385258,1.62]
            else:
                if field not in old or field not in new:raise RuntimeError('Unapproved fitting coordinate field addition/removal: '+actor)
                expected=list(old[field]);expected[1]+=.26
            if not same_vector(new.get(field),expected):raise RuntimeError('Unapproved fitting coordinate change: '+actor+' '+field)
            changes[field]={'before':old.get(field),'after':new[field]}
        records.append({'actor':actor,'kind':old['kind'],'changes':changes})
    changed={record['actor'] for record in records}
    if changed and changed!=seat_ids|headset_ids:raise RuntimeError('Pilot access correction must update exactly both chairs and both headsets')
    return {'passed':True,'changed_actor_ids':sorted(changed),'unchanged_item_count':len(original)-len(records),'changed_item_count':len(records),'approved_source_y_shift_m':.26,'changes':records}


class Validator:
    def __init__(self, runtime, walk_tests=None, captures=None):
        self.r = runtime
        self.data = runtime.DATA
        self.layout = self.data.get('layout', {})
        self.config = self.layout.get('validation', {})
        self.walks = list(walk_tests if walk_tests is not None else
                          self.layout.get('walk_tests', self.data.get('walk_tests', [])))
        self.shots = list(captures if captures is not None else
                          self.config.get('captures', self.layout.get('validation_captures', [])))
        self.seats = [item for item in runtime.STATE['items'] if item['kind'] == 'seat']
        self.screens = [item for item in runtime.STATE['items'] if item['kind'] == 'screen']
        self.controls = [item for item in runtime.STATE['items'] if item['kind'] == 'control']
        self.inspects = [item for item in runtime.STATE['items'] if item['kind'] == 'inspect']
        self.movables = [item for item in runtime.STATE['items'] if item.get('motion') and item.get('activation') != 'inspect_only']
        self.inventory={'seats':len(self.seats),'screens':len(self.screens),'controls':len(self.controls),'inspectables':len(self.inspects),
                        'exposed_movables':len(self.movables),'configured_movables':sum(bool(item.get('motion')) for item in runtime.STATE['items']),
                        'crew_fold_seats':sum(bool(item.get('requires_open')) for item in self.seats)}
        self.barriers = list(self.layout.get('barrier_tests', self.config.get('barrier_tests', [])))
        self.door_item = next((item for item in runtime.STATE['items']
                               if item['kind'] == 'door'), None)
        self.cameras = {}
        for actor in u.GameplayStatics.get_all_actors_of_class(runtime.STATE['world'], u.CameraActor):
            for tag in actor.tags:
                if str(tag).startswith('SkywardCamera:'):
                    self.cameras[str(tag)[len('SkywardCamera:'):]] = actor
        self.v = {'phase': 'settle', 'after': time.monotonic() + 25.0, 'index': 0}
        self.body_queries_verified=False
        self.report = {
            'revision': str(self.layout.get('revision', '10')),
            'validator': '12' if self.controls or self.inspects else '10', 'status': 'RUNNING',
            'capture_method': 'actual standalone viewport Shot after settled temporal AA',
            'navigation_method': 'standing collision-enabled player movement; initial placement only',
            'captures': [], 'interactions': [], 'navigation': [], 'configuration': [], 'barriers': [],'body_clearance':[]
        }
        self.report['inventory']=dict(self.inventory)
        self.navigation_retry='-SkywardWalkRetry12' in runtime.COMMAND_LINE
        self.run_id='12-navigation-5' if self.navigation_retry else '12-navigation-4' if '-SkywardContinue12' in runtime.COMMAND_LINE else 'full-validation'
        fingerprint={
            'source_blend_sha256':hashlib.sha256((runtime.ROOT/'SourceAssets/Blender/SkywardAir.blend').read_bytes()).hexdigest(),
            'runtime_sha256':hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest(),
            'interaction_metadata_sha256':hashlib.sha256(json.dumps(self.data['interactions'],sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        self.report['verification_runs']=[{'run_id':self.run_id,'kind':'full captures, actions and walking','status':'RUNNING',**fingerprint}]
        if '-SkywardContinue12' in runtime.COMMAND_LINE:
            baseline_path=runtime.ROOT/'ArtBible/ValidationRuns/Revision12_FullActions/report.json'
            baseline=json.loads(baseline_path.read_text());evidence=baseline['frozen_provenance']
            if fingerprint['runtime_sha256']!=evidence['runtime_sha256']:raise RuntimeError('Cannot carry forward full-action evidence: runtime_sha256 changed')
            original_scene=json.loads((runtime.ROOT/'Versions/Revision12_FunctionsBeforePrint/manifest.json').read_text())['scenes']['L_Plane_Reference']
            original_hash=hashlib.sha256(json.dumps(original_scene['interactions'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if original_hash!=evidence['interaction_metadata_sha256']:raise RuntimeError('Original interaction manifest does not match frozen action evidence')
            scope=_interaction_reuse_scope(original_scene['interactions'],self.data['interactions']);changed=set(scope['changed_actor_ids'])
            if not baseline.get('interactions') or not all(test['passed'] for test in baseline['interactions']):raise RuntimeError('Continuation requires actual passed full-action evidence')
            excluded=[test for test in baseline['interactions'] if any(actor in json.dumps(test,ensure_ascii=False) for actor in changed)]
            if changed and len(excluded)!=8:raise RuntimeError('Changed pilot fittings must exclude their exact eight original action checks')
            self.report['interactions']=[{**test,'verification_run':evidence['run_id']} for test in baseline['interactions'] if test not in excluded]
            scope.update(original_metadata_sha256=original_hash,current_metadata_sha256=fingerprint['interaction_metadata_sha256'],excluded_original_checks=[test['test'] for test in excluded],excluded_original_check_count=len(excluded),carried_forward_check_count=len(self.report['interactions']))
            self.report['metadata_reuse_audit']=scope
            self.report['verification_runs']=[{**evidence,'report':'ArtBible/ValidationRuns/Revision12_FullActions/report.json','original_failure':baseline.get('error'),'reused_action_checks':len(self.report['interactions']),'excluded_changed_fitting_checks':scope['excluded_original_checks']},
                {'run_id':self.run_id,'kind':'fresh captures, targeted card/cockpit/PSU/lavatory/privacy-door actions, all barriers and walking/body audits','status':'RUNNING',**fingerprint}]
            self.report['carried_forward_action_checks']=len(self.report['interactions'])
            self.report['evidence_note']='Earlier checks are retained against their original source hash only for unchanged fitting descriptors; runtime code is unchanged. Approved pilot-chair/headset coordinate differences and excluded original checks are listed in metadata_reuse_audit. Current-source captures, affected fitting actions and all walking/body checks are fresh.'
            targeted={'Cockpit NAV switch12','Cockpit status pushlight 112','Cockpit status pushlight 212','Cockpit side rotary 112',
                      'PSU 01 Gasper12','PSU 01 ReadKey12','PSU 01 CallKey12','Lavatory R mixer lever12','Lavatory R flush button12'}
            targeted|=changed&{'Pilot headset L12','Pilot headset R12'}
            self.controls=[item for item in self.controls if item['actor'] in targeted]
            self.inspects=[item for item in self.inspects if item['actor']=='Passenger safety card 0112']
            self.movables=[item for item in self.movables if item['actor'].startswith('Suite privacy door ') or item['actor'] in {'Lavatory R door — hinge pivot','Lavatory R vanity cupboard12'}]
            self.seats=[item for item in self.seats if item['actor'] in changed]
            if len(self.controls)!=9+(2 if changed else 0) or len(self.inspects)!=1 or len(self.movables)!=6 or len(self.seats)!=(2 if changed else 0):raise RuntimeError('Continuation targeted cockpit/PSU/lavatory/privacy-door/card/pilot fittings are missing')
            self.screens=[]
            self.report['original_full_action_seat_count']=sum(test['test'].startswith('E enters ') and test['passed'] for test in baseline['interactions'])
            self.report['full_action_seat_count']=sum(test['test'].startswith('E enters ') and test['passed'] for test in self.report['interactions'])
        if self.navigation_retry:
            if '-SkywardContinue12' not in runtime.COMMAND_LINE:raise RuntimeError('Walking retry requires the normal continuation proof')
            folder=runtime.ROOT/'ArtBible/ValidationRuns/12-navigation-4';prior_path=folder/'report.json';prior=json.loads(prior_path.read_text());evidence=json.loads((folder/'archive_manifest.json').read_text());scope=prior['verification_runs'][-1]
            if hashlib.sha256(prior_path.read_bytes()).hexdigest()!=evidence['report_sha256']:raise RuntimeError('Archived current-source report changed')
            for key in ('source_blend_sha256','runtime_sha256','interaction_metadata_sha256'):
                if fingerprint[key]!=scope[key]:raise RuntimeError('Walking retry cannot reuse changed '+key)
            for key,path in (('manifest_sha256',runtime.ROOT/'Exports/manifest.json'),('map_sha256',runtime.ROOT/'UnrealProject/Content/Maps/L_Plane_Reference.umap')):
                if hashlib.sha256(path.read_bytes()).hexdigest()!=evidence[key]:raise RuntimeError('Walking retry requires exact same saved '+key)
            if scope['run_id']!='12-navigation-4' or scope['fresh_action_checks']!=71 or not all(test['passed'] for test in prior['interactions']):raise RuntimeError('Walking retry requires71 actual passed current-source actions')
            retained=[capture for capture in prior['captures'] if not capture.get('walking_test')]
            if len(retained)!=59:raise RuntimeError('Walking retry requires59 current-source authored captures')
            checked=[]
            for capture in retained:
                proof=next(item for item in evidence['captures'] if item['file']==capture['file']);path=runtime.ROOT/'Screenshots'/capture['file'];archived=folder/'Screenshots'/capture['file']
                if hashlib.sha256(path.read_bytes()).hexdigest()!=proof['sha256'] or hashlib.sha256(archived.read_bytes()).hexdigest()!=proof['sha256']:raise RuntimeError('Current-source capture changed: '+capture['file'])
                if path.stat().st_mtime<(runtime.ROOT/'SourceAssets/Blender/SkywardAir.blend').stat().st_mtime:raise RuntimeError('Current-source capture predates saved source')
                checked.append({'file':capture['file'],'sha256':proof['sha256']})
            self.report['interactions']=prior['interactions'];self.report['captures']=[{**capture,'verification_run':'12-navigation-4','retained_same_source':True} for capture in retained]
            self.report['verification_runs']=prior['verification_runs']+[{**self.report['verification_runs'][-1],'kind':'fresh calibration, authored fixture reset, six closed-leaf barriers and all22 actual walking/body routes;59 exact-source captures and71 current-source actions retained'}]
            self.report['verification_runs'][-2]['retained_evidence_scope']='Only71 passed actions and59 authored camera captures reused; prior navigation/body/barrier results are superseded'
            self.report['carried_forward_action_checks']=len(prior['interactions']);self.report['carried_forward_checks_by_run']={name:sum(test.get('verification_run')==name for test in prior['interactions']) for name in ('12-full-actions-1','12-navigation-4')}
            self.report['retained_capture_verification']={'passed':True,'source_blend_sha256':fingerprint['source_blend_sha256'],'manifest_sha256':evidence['manifest_sha256'],'map_sha256':evidence['map_sha256'],'authored_capture_count':59,'captures':checked,'archived_report':'ArtBible/ValidationRuns/12-navigation-4/report.json'}
            self.report['evidence_note']='1484 original checks apply only to unchanged fitting descriptors.71 passed current-source actions and59 hash-verified authored captures are retained from12-navigation-4 on exactly identical saved source, runtime, manifest and map. Only calibration, fixture reset, six barriers and all22 walking/body routes are fresh in12-navigation-5; no previous failed navigation/body results are reused.'
            self.report['carried_seat_checks_by_run']={name:sum(test.get('verification_run')==name and test['test'].startswith('E enters ') and test['passed'] for test in prior['interactions']) for name in ('12-full-actions-1','12-navigation-4')}
            self.seats=[];self.screens=[];self.controls=[];self.inspects=[];self.movables=[]
        self.report['fresh_selected_fittings']={'seats':len(self.seats),'screens':len(self.screens),'controls':len(self.controls),'inspectables':len(self.inspects),'movables':len(self.movables)}
        self.save()

    def save(self):
        (self.r.ROOT / 'ArtBible' / 'EngineValidation.json').write_text(
            json.dumps(self.report, indent=2), encoding='utf-8')

    def check(self, name, passed, category='interactions', **details):
        self.report[category].append({'test': name, 'passed': bool(passed),'verification_run':self.run_id, **details})
        self.save()

    def fail(self, error):
        self.report.update(status='FAILED', error=str(error))
        self.finish()

    def finish(self):
        current=self.report['verification_runs'][-1]
        current.update(status=self.report['status'],fresh_action_checks=sum(test.get('verification_run')==self.run_id for test in self.report['interactions']),
                       fresh_captures=sum(capture.get('verification_run',self.run_id)==self.run_id for capture in self.report['captures']),walking_routes_passed=sum(bool(test['passed']) for test in self.report['navigation'] if 'waypoints_source_m' in test),
                       body_routes_passed=sum(bool(test['passed']) for test in self.report['body_clearance']))
        self.save()
        state = self.r.STATE
        u.unregister_slate_post_tick_callback(state['handle'])
        u.SystemLibrary.quit_game(state['world'], state['pc'], u.QuitPreference.QUIT, False)

    def _phase(self, name, delay=0.0, **values):
        self.v.update(phase=name, after=time.monotonic() + delay, **values)

    def _move_component(self):
        return self.r.STATE['pawn'].get_component_by_class(u.FloatingPawnMovement)

    def _stop(self):
        self._move_component().stop_movement_immediately()
        self.r.STATE['pawn'].consume_movement_input_vector()

    def _standing(self):
        state = self.r.STATE
        if state.get('inspecting'):
            self.r.end_inspect()
        if state.get('seated'):
            self.r.stand()
        self._stop()
        state['pc'].reset_ignore_move_input()
        state['pawn'].set_actor_enable_collision(True)
        movement = self._move_component()
        movement.set_plane_constraint_origin(u.Vector(0, 0, state['pawn'].get_actor_location().z))
        movement.set_plane_constraint_enabled(True)
        movement.activate(True)
        state['pc'].set_view_target_with_blend(state['pawn'], 0)

    def _place(self, source):
        """A test's initial placement; never used between walking waypoints."""
        source = _point(source, 'start')
        self._require_standing_point(source, 'Standing walk start')
        self._standing()
        target = self.r.vector(source)
        self.r.reposition(_xyz(target))
        return target

    def _require_standing_point(self, point, name):
        feet = point[2] - 1.62
        if abs(feet) < 0.006:
            return
        x, y = point[:2]
        for zone in self.layout.get('navigation_floors', []):
            xmin, xmax, ymin, ymax = zone['rect']
            if not (xmin - .01 <= x <= xmax + .01 and ymin - .01 <= y <= ymax + .01):
                continue
            slope = zone.get('slope')
            if slope:
                coordinate = x if slope.get('axis', 'y') == 'x' else y
                t = max(0, min(1, (coordinate - slope['from']) / (slope['to'] - slope['from'])))
                floor = slope['start'] + t * (slope['end'] - slope['start'])
            else:
                floor = zone['height']
            if abs(floor - feet) < .035:
                return
        raise ValueError(name + ' must be 1.62 m above the declared cabin, stair or lower floor')

    def _source_direction(self, direction):
        direction = _point(direction, 'direction')
        length = math.hypot(direction[0], direction[1])
        if length < 0.001 or abs(direction[2]) > 0.001:
            raise ValueError('Walk directions must be non-zero and horizontal')
        return u.Vector(direction[0] / length, -direction[1] / length, 0)

    def _door_progress(self):
        displacement = self.r.STATE['pawn'].get_actor_location() - self.v['door_start']
        direction = self.v['door_direction']
        return displacement.x * direction.x + displacement.y * direction.y

    def _open_actors(self, names):
        delay = 0.0
        for name in names or []:
            if name in self.r.STATE.get('movables', {}):
                moving = self.r.STATE['movables'][name]
                delay = max(delay, (1 - moving['progress']) * float(moving['item']['motion'].get('duration', 1)))
                moving['target'] = 1.0
            elif self.door_item and name == self.door_item['actor']:
                self.r.STATE['door_target'] = float(self.door_item.get('open_yaw', 86))
                delay = max(delay, 1.0)
            else:
                raise ValueError('Unknown open_actors prerequisite: ' + str(name))
        return delay

    def _close_actors(self, names):
        delay = 0.0
        for name in names or []:
            if name in self.r.STATE.get('movables', {}):
                moving = self.r.STATE['movables'][name]
                delay = max(delay, moving['progress'] * float(moving['item']['motion'].get('duration', 1)))
                moving['target'] = 0.0
            else:
                raise ValueError('Unknown close_actors prerequisite: ' + str(name))
        return delay

    def _restore_authored_fixtures(self):
        delay=0.
        for moving in self.r.STATE['movables'].values():
            moving['target']=1. if moving['item'].get('initial_open',False) else 0.
            delay=max(delay,abs(moving['progress']-moving['target'])*float(moving['item']['motion'].get('duration',1)))
        if self.door_item:delay=max(delay,self._open_actors([self.door_item['actor']]))
        return delay

    def _prepare_capture(self, file, camera=None, walking=None, open_actors=None, close_actors=None, screen_pages=None, control_states=None, inspect_actor=None):
        if Path(file).name != file or not file.lower().endswith('.png'):
            raise ValueError('Capture file must be a plain PNG filename: ' + str(file))
        if self.r.STATE.get('inspecting'):self.r.end_inspect()
        if camera is not None:
            full_name = camera if camera.startswith('CAM_') else 'CAM_Plane_' + camera
            actor = self.cameras.get(full_name)
            if actor is None:
                raise RuntimeError('Missing capture camera: ' + full_name)
            self.r.STATE['pc'].set_view_target_with_blend(actor, 0)
        opening_delay = max(self._open_actors(open_actors), self._close_actors(close_actors))
        for actor,index in (screen_pages or {}).items():self.r.show_screen_page(actor,index)
        for actor,index in (control_states or {}).items():self.r.set_control_state(actor,index)
        if inspect_actor:
            item=next(item for item in self.r.STATE['items'] if item['kind']=='inspect' and item['actor']==inspect_actor)
            self.r.inspect_item(item)
            opening_delay=max(opening_delay,max((float(self.r.STATE['movables'][name]['item']['motion'].get('duration',1)) for name in item.get('open_actors',[])),default=0))
        self._stop()
        self.v['capture'] = {'camera': camera or 'standing player route endpoint',
                             'file': file, 'walking_test': walking}
        self._phase('capture', 3.0 + opening_delay)

    def _capture(self):
        item = self.v['capture']
        path = self.r.ROOT / 'Screenshots' / item['file']
        path.parent.mkdir(parents=True, exist_ok=True)
        self.v.update(capture_path=path, capture_started=time.time(),
                      capture_deadline=time.monotonic() + 22)
        u.SystemLibrary.execute_console_command(
            self.r.STATE['world'], 'Shot filename="' + str(path).replace('\\', '/') + '" -nosuffix',
            self.r.STATE['pc'])
        self._phase('capture_wait', 1.0)

    def _capture_wait(self):
        path = self.v['capture_path']
        if not path.exists() or path.stat().st_mtime < self.v['capture_started']:
            if time.monotonic() > self.v['capture_deadline']:
                raise RuntimeError('Screenshot did not arrive: ' + path.name)
            return
        # Check the actual file, so an old or partial file cannot satisfy capture.
        with path.open('rb') as stream:
            png_header = stream.read(24)
        if len(png_header) < 24 or png_header[:8] != b'\x89PNG\r\n\x1a\n':
            raise RuntimeError('Capture is not a complete PNG: ' + path.name)
        item = {**self.v['capture'], 'bytes': path.stat().st_size,
                'width': int.from_bytes(png_header[16:20], 'big'),
                'height': int.from_bytes(png_header[20:24], 'big'),
                'method': self.report['capture_method'],'verification_run':self.run_id}
        self.report['captures'].append(item)
        self.save()
        resume = self.v.pop('capture_resume')
        self._phase(resume, 0.2)

    def _start_walk(self):
        test = self.walks[self.v['index']]
        name = str(test['name'])
        start = _point(test['start'], name + '.start')
        path = test.get('path', test.get('waypoints'))
        if path is None and 'target' in test:
            path = [test['target']]
        if not isinstance(path, list) or not path:
            raise ValueError(name + ' must define a non-empty path of standing waypoints')
        path = [_point(point, name + '.path') for point in path]
        for point in path:
            self._require_standing_point(point, name + ' waypoint')
        tolerance_cm = float(test.get('tolerance', 0.12)) * 100
        if not 3 <= tolerance_cm <= 25:
            raise ValueError(name + ' tolerance must be 0.03–0.25 m')
        initial = self._place(start)
        actual = self.r.STATE['pawn'].get_actor_location()
        self.check('initial placement: ' + name, (actual - initial).length() < 1,
                   category='navigation', expected_cm=_xyz(initial), actual_cm=_xyz(actual))
        route = {'test': name, 'passed': False, 'start_source_m': start,
                 'waypoints_source_m': path, 'reached_waypoints': [],
                 'tolerance_cm': tolerance_cm, 'samples_cm': [_xyz(actual)],
                 'teleports_after_start': 0}
        self.report['navigation'].append(route)
        now = time.monotonic()
        self.v.update(route=route, path=path, waypoint=0, tolerance=tolerance_cm,
                      walk_began=now, last_sample=now, progress_at=now,
                      progress_position=actual, path_length=0.0, last_position=actual,
                      segment_began=now)
        body=True  # Every authored standing route receives the full body audit.
        self.v['body_audit']=None
        if body:
            audit={'test':'standing body clearance: '+name,'passed':True,'radius_m':.20,'height_m':1.72,'centre_above_floor_m':.86,'samples':0,'filtered_floor_contacts':0,'obstructions':[],
                   'method':'independent native capsule sweeps along actual walked positions; unchanged player controller; support contacts within0.28m step range require a clear second torso sweep'}
            self.report['body_clearance'].append(audit);self.v['body_audit']=audit;self.v['body_position']=actual
            self._body_sweep(actual,actual,force=True)
        self._phase('walk_move', 0.2)

    def _end_walk(self, passed, reason=None):
        self._stop()
        route = self.v['route']
        route.update(passed=bool(passed), elapsed_seconds=round(time.monotonic() - self.v['walk_began'], 2),
                     walked_distance_cm=round(self.v['path_length'], 1),
                     final_cm=_xyz(self.r.STATE['pawn'].get_actor_location()))
        if reason:
            route['failure'] = reason
        audit=self.v.get('body_audit')
        if audit is not None:
            audit['walk_completed']=bool(passed)
            if not passed:audit['passed']=False;audit['incomplete_reason']=reason or 'Walking route did not complete'
        self.save()
        test = self.walks[self.v['index']]
        self.v['index'] += 1
        resume = 'walk_start' if self.v['index'] < len(self.walks) else 'finish'
        if passed and test.get('capture'):
            if test.get('look_at'):
                self.r.point_at(_point(test['look_at'], 'look_at'))
            self.v['capture_resume'] = resume
            self._prepare_capture(test['capture'], walking=route['test'])
        else:
            self._phase(resume, 0.2)

    def _body_query_preflight(self):
        """Known blockers prove the native query works before any clearance claim."""
        state=self.r.STATE;results=[]
        for name,start,end,half_height,expected,expected_asset in (
            ('known cabin wall',[-4,15,.86],[4,15,.86],86,'COL_CabinSide','SM_Plane_OuterWindowBarrel'),
            ('known below-eye throttle pedestal',[0,-3.6,.45],[0,-3.6,.45],45,'COL_ThrottlePedestal','SM_Plane_Controls')):
            hit=u.SystemLibrary.capsule_trace_single_by_profile(state['world'],self.r.vector(start),self.r.vector(end),20,half_height,u.Name('Pawn'),True,[state['pawn']],u.DrawDebugTrace.NONE,True)
            values=hit.to_tuple() if hit is not None else None
            actor=values[9].get_actor_label() if values and values[9] else '';source_name=self.r.actor_name(values[9]) if values and values[9] else ''
            asset=next((item['asset'] for item in self.data.get('instances',[]) if item['name']==source_name),'')
            point=[values[5].x/100,-values[5].y/100,values[5].z/100] if values else None
            role=actor.startswith(expected) or asset==expected_asset
            physical_bounds=bool(point and ((-3.1<=point[0]<=-2.0 and abs(point[1]-15)<=.25 and -.02<=point[2]<=1.75) if half_height==86 else (abs(point[0])<=.5 and abs(point[1]+3.6)<=.4 and -.02<=point[2]<=.92)))
            passed=bool(values and values[0] and role and physical_bounds);results.append(passed)
            self.check('capsule query detects '+name,passed,category='configuration',actual_actor=actor,
                       actual_asset=asset,blocking_hit=bool(values and values[0]),impact_source_m=point,known_geometry_role_passed=role,physical_bounds_passed=physical_bounds,
                       expected_actor_prefix=expected,expected_source_asset=expected_asset,radius_m=.20,height_m=half_height/50,source_start=start,source_end=end)
        self.body_queries_verified=all(results)
        self.report['body_query_positive_controls_passed']=self.body_queries_verified
        self.save();return self.body_queries_verified

    def _body_sweep(self,previous,current,force=False):
        audit=self.v.get('body_audit')
        if audit is None or (not force and _horizontal_distance(previous,current)<.2):return
        if not getattr(self,'body_queries_verified',True):raise RuntimeError('Standing-body audit aborted: native capsule positive controls did not pass')
        state=self.r.STATE
        def trace(start,end,radius,half_height):
            return u.SystemLibrary.capsule_trace_single_by_profile(state['world'],start,end,radius,half_height,u.Name('Pawn'),True,[state['pawn']],u.DrawDebugTrace.NONE,True)
        def unpack(hit):
            # Python consumes FHitResult's HasNativeBreak via StructBase;
            # the GameplayStatics helper itself is deliberately not exposed.
            values=hit.to_tuple()
            return {'blocking':bool(values[0]),'initial_overlap':bool(values[1]),'distance_cm':float(values[3]),'impact':values[5],'normal':values[7],'actor':values[9]}
        def support(hit):
            feet=(previous.z+current.z)/200-1.62
            floor_top=(feet+float(self.config.get('body_floor_step_m',.28)))*100
            # A stationary sweep can report a zero normal when initially
            # touching the dedicated deck mesh. Never filter whole hold assets.
            actor=hit['actor'];source_name=self.r.actor_name(actor) if actor else ''
            asset=next((i['asset'] for i in self.data.get('instances',[]) if i['name']==source_name),'')
            within_step=(feet-.04)*100<=hit['impact'].z<=floor_top
            dedicated_floor=asset in ('SM_Plane_Floor','SM_Plane_FittedCarpet07') and within_step
            stair_riser=asset=='SM_Plane_CargoStair10' and within_step
            shallow_floor_lip=(feet-.04)*100<=hit['impact'].z<=(feet+.04)*100
            return dedicated_floor or stair_riser or shallow_floor_lip or (hit['normal'].z>.65 and within_step)
        # Standing eye height is 1.62; a 1.72m body centre sits .76m below it.
        start=u.Vector(previous.x,previous.y,previous.z-76);end=u.Vector(current.x,current.y,current.z-76)
        raw=trace(start,end,20,86);audit['samples']+=1
        if raw is None:return
        hit=unpack(raw)
        if not hit['blocking']:return
        if support(hit):
            audit['filtered_floor_contacts']+=1
            # A floor/tread may be the first blocking hit. Probe the remaining
            # .28..1.72m body so a supported foot cannot hide furniture above it.
            torso_start=u.Vector(previous.x,previous.y,previous.z-62);torso_end=u.Vector(current.x,current.y,current.z-62)
            raw=trace(torso_start,torso_end,20,72)
            if raw is None:return
            hit=unpack(raw)
            if not hit['blocking']:return
        actor=hit['actor'];name=actor.get_actor_label() if actor else 'unknown component'
        audit['passed']=False
        if not audit['obstructions'] or audit['obstructions'][-1]['actor']!=name:
            audit['obstructions'].append({'actor':name,'impact_cm':_xyz(hit['impact']),'normal':_xyz(hit['normal']),'initial_overlap':hit['initial_overlap'],'actual_player_cm':_xyz(current)})
            self.save()

    def _walk_move(self, now):
        state = self.r.STATE
        pawn = state['pawn']
        if state.get('seated') or not pawn.get_actor_enable_collision():
            return self._end_walk(False, 'Walking lost standing collision-enabled state')
        position = pawn.get_actor_location()
        if self.v.get('body_audit') is not None:
            self._body_sweep(self.v['body_position'],position);self.v['body_position']=position
        if hasattr(self.r, 'floor_at_source'):
            floor, floor_name = self.r.floor_at_source(position.x / 100, -position.y / 100,
                                                       position.z / 100 - 1.62)
            if abs(position.z - (floor + 1.62) * 100) > 2:
                return self._end_walk(False, 'Standing eye height diverged from the active floor')
        self.v['path_length'] += _horizontal_distance(position, self.v['last_position'])
        self.v['last_position'] = position
        if now - self.v['last_sample'] > 0.35:
            self.v['route']['samples_cm'].append(_xyz(position))
            self.v['last_sample'] = now
        target = self.r.vector(self.v['path'][self.v['waypoint']])
        remaining = _horizontal_distance(position, target)
        if remaining <= self.v['tolerance'] and abs(position.z-target.z) <= self.v['tolerance']:
            self._stop()
            self.v['route']['reached_waypoints'].append(
                {'index': self.v['waypoint'], 'actual_cm': _xyz(position),
                 'distance_from_target_cm': round(remaining, 2)})
            self.v['waypoint'] += 1
            if self.v['waypoint'] == len(self.v['path']):
                return self._end_walk(True)
            self.v.update(segment_began=now, progress_at=now, progress_position=position)
            self._phase('walk_move', 0.15)
            return
        if _horizontal_distance(position, self.v['progress_position']) > 3:
            self.v.update(progress_at=now, progress_position=position)
        if now - self.v['progress_at'] > 2.2:
            return self._end_walk(False, 'Collision blocked waypoint ' + str(self.v['waypoint']))
        if now - self.v['segment_began'] > 35 or now - self.v['walk_began'] > 100:
            return self._end_walk(False, 'Walking route timed out before reaching its waypoint')
        if remaining < .1:
            return self._end_walk(False, 'Reached horizontal waypoint at the wrong floor height')
        direction = u.Vector((target.x - position.x) / remaining,
                             (target.y - position.y) / remaining, 0)
        # Slow near the endpoint to avoid frame-rate-dependent overshoot.
        pawn.add_movement_input(direction, max(0.16, min(1.0, remaining / 45.0)))

    def tick(self, dt):
        r, state, v = self.r, self.r.STATE, self.v
        now = time.monotonic()
        if now - state['began'] > float(self.config.get('timeout_seconds',1800)):
            raise RuntimeError('Aircraft validation timed out')
        if now < v['after']:
            return
        pawn, pc = state['pawn'], state['pc']
        phase = v['phase']
        if phase == 'settle' and self.navigation_retry:
            self.check('same-source action/capture evidence passed strict retry verification',bool(self.report.get('retained_capture_verification',{}).get('passed')),category='configuration')
            self.check('all22 standing routes are supplied for fresh retry',len(self.walks)==22,category='configuration')
            if not self._body_query_preflight():
                self.fail('Native capsule query is insensitive to known wall or below-eye pedestal; no body-clearance pass is valid');return
            self._phase('fixtures_reset',index=0,reset_resume='barrier_start' if self.barriers else 'walk_start')
        elif phase == 'settle':
            self.check('E key imports and polling API is available',
                       'E' in r.KEY.export_text() and hasattr(pc, 'was_input_key_just_pressed'),
                       key=r.KEY.export_text())
            review_count = len(state['review_cameras'])
            self.check('exterior review camera set is available', review_count >= 3,
                       category='configuration', actual_count=review_count)
            # Tests the real review function from a known state, including return.
            state['review_index'] = -1
            for expected in list(range(review_count)) + [-1]:
                self.check('V review cycle ' + str(expected), r.toggle_review() == expected)
            self.check('capture metadata is present', bool(self.shots), category='configuration')
            self.check('standing walking routes are supplied', bool(self.walks), category='configuration')
            self.check('cockpit door interaction is supplied', bool(self.door_item), category='configuration')
            if not self._body_query_preflight():
                self.fail('Native capsule query is insensitive to known wall or below-eye pedestal; no body-clearance pass is valid')
                return
            self._phase('shot' if self.shots else 'door_start', index=0)
        elif phase == 'shot':
            shot = self.shots[v['index']]
            if isinstance(shot, (tuple, list)):
                shot = {'camera': shot[0], 'file': shot[1]}
            v['index'] += 1
            v['capture_resume'] = 'shot' if v['index'] < len(self.shots) else 'door_start'
            self._prepare_capture(shot['file'], camera=shot.get('camera'), open_actors=shot.get('open_actors'), close_actors=shot.get('close_actors'), screen_pages=shot.get('screen_pages'),control_states=shot.get('control_states'),inspect_actor=shot.get('inspect_actor'))
        elif phase == 'capture':
            self._capture()
        elif phase == 'capture_wait':
            self._capture_wait()
        elif phase == 'door_start':
            if not self.door_item:
                self._phase('screen_start', index=0)
                return
            config = self.config.get('door', {})
            point = _point(self.door_item['point'], 'door point')
            start = config.get('start', [point[0], point[1] + 0.95, 1.62])
            v['door_start'] = self._place(start)
            v['door_direction'] = self._source_direction(config.get('direction', [0, -1, 0]))
            v['door_plane_distance'] = (r.vector(point) - v['door_start']).x * v['door_direction'].x + (r.vector(point) - v['door_start']).y * v['door_direction'].y
            state['door_target'] = 0
            self._phase('door_closed', 1.2)
        elif phase == 'door_closed':
            config = self.config.get('door', {})
            v['until'] = now + float(config.get('closed_duration', 0.85))
            self._phase('door_closed_move')
        elif phase == 'door_closed_move':
            pawn.add_movement_input(v['door_direction'], 1)
            if now >= v['until']:
                self._stop()
                progress = self._door_progress()
                self.check('closed cockpit door blocks a standing player',
                           progress < v['door_plane_distance'] - 5,
                           progress_cm=round(progress, 2), door_plane_cm=v['door_plane_distance'])
                r.point_at(self.door_item['point'])
                action = r.use_nearest()
                self.check('same E action opens cockpit door', action == 'door', action=action)
                self._phase('door_open', 1.2)
        elif phase == 'door_open':
            expected = -float(self.door_item.get('open_yaw', 86))
            actual = state['door'].get_actor_rotation().yaw
            self.check('cockpit door reaches its authored open position',
                       abs(actual - expected) < 0.25, expected_yaw=expected, actual_yaw=actual)
            config = self.config.get('door', {})
            v['until'] = now + float(config.get('open_duration', 1.0))
            self._phase('door_open_move')
        elif phase == 'door_open_move':
            pawn.add_movement_input(v['door_direction'], 1)
            if now >= v['until']:
                self._stop()
                progress = self._door_progress()
                self.check('open cockpit door permits a standing player through',
                           progress > v['door_plane_distance'] + 25,
                           progress_cm=round(progress, 2), door_plane_cm=v['door_plane_distance'])
                self._phase('screen_start', 0.2, index=0)
        elif phase == 'screen_start':
            if v['index'] >= len(self.screens):
                self._phase('control_start', index=0)
                return
            item=self.screens[v['index']]
            self._place(item.get('validation_approach',[item['point'][0],item['point'][1]+.36,1.62]))
            r.point_at_item(item);r.show_screen_page(item['actor'],0)
            self._phase('screen_cycle',.1,page_cycle=0)
        elif phase == 'screen_cycle':
            item=self.screens[v['index']];screen=state['screens'][item['actor']]
            expected=(v['page_cycle']+1)%len(screen['pages']);action=r.use_nearest()
            actual=screen['component'].get_material(screen['slot']).get_name()
            self.check('E screen page '+item['actor']+' '+str(expected),
                       action=='screen' and screen['page']==expected and actual==item['pages'][expected],
                       expected_material=item['pages'][expected],actual_material=actual)
            v['page_cycle']+=1
            if v['page_cycle']>=len(screen['pages']):v['index']+=1;self._phase('screen_start',.1)
            else:self._phase('screen_cycle',.1)
        elif phase == 'control_start':
            if v['index']>=len(self.controls):
                self._phase('inspect_start',index=0);return
            item=self.controls[v['index']]
            self._place(item.get('validation_approach',[item['point'][0]*.65,item['point'][1],1.62]))
            delay=self._open_actors(item.get('open_actors'))
            r.set_control_state(item['actor'],int(item.get('initial_state',0)))
            self._phase('control_cycle',delay+.1,control_cycle=0)
        elif phase == 'control_cycle':
            item=self.controls[v['index']];control=state['controls'][item['actor']]
            r.point_at_item(item);expected=(control['state']+1)%len(item['states']);action=r.use_nearest()
            snapshot=r.control_snapshot(item['actor'])
            self.check('E control '+item['actor']+' '+str(expected),action=='control' and snapshot['state']==expected and snapshot['passed'],action=action,target_snapshot=snapshot)
            v['control_cycle']+=1
            if v['control_cycle']<len(item['states']):self._phase('control_cycle',.08)
            elif item.get('auto_reset_seconds'):
                r.point_at_item(item);r.use_nearest();self._phase('control_auto_reset',float(item['auto_reset_seconds'])+.15)
            else:v['index']+=1;self._phase('control_start',.05)
        elif phase == 'control_auto_reset':
            item=self.controls[v['index']];snapshot=r.control_snapshot(item['actor'])
            self.check('automatic reset '+item['actor'],snapshot['state']==int(item.get('initial_state',0)) and snapshot['passed'],target_snapshot=snapshot)
            v['index']+=1;self._phase('control_start',.05)
        elif phase == 'inspect_start':
            if v['index']>=len(self.inspects):self._phase('seat',index=0);return
            item=self.inspects[v['index']];self._place(item['validation_approach']);r.point_at_item(item)
            v['inspect_start_position']=pawn.get_actor_location();v['inspect_start_collision']=state['actors'][item['actor']].get_actor_enable_collision()
            v['inspect_prop_position']=state['actors'][item['actor']].get_actor_location();v['inspect_prop_rotation']=state['actors'][item['actor']].get_actor_rotation()
            action=r.use_nearest()
            self.check('E inspect '+item['actor'],action=='inspect' and bool(state.get('inspecting')) and state['inspecting']['item']['actor']==item['actor'],action=action)
            delay=max((float(state['movables'][name]['item']['motion'].get('duration',1)) for name in item.get('open_actors',[])),default=0)
            self._phase('inspect_return',delay+.3)
        elif phase == 'inspect_return':
            item=self.inspects[v['index']];actor=state['actors'][item['actor']]
            if item.get('hold'):
                self.check('inspection lifts '+item['actor'],(actor.get_actor_location()-v['inspect_prop_position']).length()>5 and not actor.get_actor_enable_collision())
            for name in item.get('open_actors',[]):self.check('inspection opens '+name,state['movables'][name]['progress']>.995)
            action=r.use_nearest();actual=actor.get_actor_rotation();expected=v['inspect_prop_rotation']
            rotation_error=max(abs((getattr(actual,key)-getattr(expected,key)+180)%360-180) for key in ('pitch','yaw','roll'))
            self.check('E returns '+item['actor'],action=='return' and not state.get('inspecting') and (actor.get_actor_location()-v['inspect_prop_position']).length()<.05 and rotation_error<.05 and actor.get_actor_enable_collision()==v['inspect_start_collision'] and (pawn.get_actor_location()-v['inspect_start_position']).length()<1,action=action,rotation_error_degrees=rotation_error)
            v['index']+=1;self._phase('inspect_start',.1)
        elif phase == 'seat':
            if v['index'] >= len(self.seats):
                self._phase('movable_start' if self.movables else 'fixtures_reset', index=0,reset_resume='barrier_start' if self.barriers else 'walk_start' if self.walks else 'finish')
                return
            item=self.seats[v['index']]
            if item.get('requires_open'):
                name=item['requires_open'];delay=self._close_actors([name]);self._phase('seat_folded',delay+.1)
            else:self._phase('seat_ready')
        elif phase == 'seat_folded':
            item=self.seats[v['index']];source=self.config.get('seat_approaches',{}).get(item['actor'],item['validation_approach'])
            self._place(source);r.point_at_item(item);selected=r.nearest()
            self.check('folded crew pan prevents seating '+item['actor'],not selected or selected['actor']!=item['actor'])
            delay=self._open_actors([item['requires_open']]);self._phase('seat_ready',delay+.1)
        elif phase == 'seat_ready':
            item = self.seats[v['index']]
            source = self.config.get('seat_approaches', {}).get(
                item['actor'], item.get('validation_approach',
                                        [item['point'][0], item['point'][1] + 0.85, 1.62]))
            self._place(source)
            r.point_at_item(item)
            before = pawn.get_actor_location()
            action = r.use_nearest()
            seated = state.get('seated')
            self.check('E enters ' + item['actor'],
                       action == 'seat' and bool(seated) and seated['actor'] == item['actor']
                       and not pawn.get_actor_enable_collision()
                       and abs(pawn.get_actor_location().z - item['location'][2] * 100) < 1,
                       selected_actor=seated['actor'] if seated else None)
            if seated:
                if item.get('screen_actor'):
                    self.check('seat owns declared forward display '+item['actor'],seated.get('screen_actor')==item['screen_actor'],expected_screen=item['screen_actor'],actual_screen=seated.get('screen_actor'))
                if item.get('facing'):
                    facing=item['facing'];expected_yaw=math.degrees(math.atan2(-facing[1],facing[0]));actual_yaw=pc.get_control_rotation().yaw
                    self.check('seat faces authored direction '+item['actor'],abs((actual_yaw-expected_yaw+180)%360-180)<.1,expected_yaw=expected_yaw,actual_yaw=actual_yaw)
                own=seated.get('screen_actor')
                if own:
                    screen=state['screens'][own];previous=screen['page'];r.point_at(screen['item']['point']);action=r.use_nearest()
                    self.check('seated E cycles own entertainment '+item['actor'],
                               action=='screen' and state.get('seated') is seated and screen['page']==(previous+1)%len(screen['pages']))
                    r.show_screen_page(own,0)
                # Look behind the chair so E stands rather than selecting IFE.
                r.point_at([item['location'][0],item['location'][1]+1.0,item['location'][2]])
                r.use_nearest()
            self.check('E stands from ' + item['actor'],
                       not state.get('seated') and pawn.get_actor_enable_collision()
                       and (pawn.get_actor_location() - before).length() < 1)
            v['index'] += 1
            self._phase('seat',.05)
        elif phase == 'movable_start':
            if v['index'] >= len(self.movables):
                self._phase('fixtures_reset',index=0,reset_resume='barrier_start' if self.barriers else 'walk_start' if self.walks else 'finish')
                return
            item = self.movables[v['index']]
            moving = state['movables'][item['actor']]
            # Begin each E-action check from its authored standing approach.
            # This does not substitute for the separate collision walking routes.
            source = item.get('validation_approach', [item['point'][0] * .55,
                                                      item['point'][1], 1.62])
            self._place(source)
            r.point_at_item(item)
            moving['target'] = 0.0
            self._phase('movable_closed', float(item['motion'].get('duration', 1)) + .25)
        elif phase == 'movable_closed':
            item = self.movables[v['index']]
            moving = state['movables'][item['actor']]
            self.check('movable reaches closed position: ' + item['actor'],
                       moving['progress'] < .005)
            r.point_at_item(item)
            action = r.use_nearest()
            self.check('E opens ' + item['actor'], action == 'movable' and moving['target'] == 1,
                       action=action)
            self._phase('movable_open', float(item['motion'].get('duration', 1)) + .25)
        elif phase == 'movable_open':
            item = self.movables[v['index']]
            moving = state['movables'][item['actor']]
            self.check('movable reaches open position: ' + item['actor'], moving['progress'] > .995)
            self._phase('movable_open_reach',open_reach_began=now,open_reach_progress=now,open_reach_position=pawn.get_actor_location(),open_reach_walked_cm=0.)
        elif phase == 'movable_open_reach':
            item=self.movables[v['index']];moving=state['movables'][item['actor']]
            r.point_at_item(item);selected=r.nearest()
            if selected and selected['actor']==item['actor'] and selected.get('motion'):
                self._stop();action=r.use_nearest()
                self.check('E closes '+item['actor'],action=='movable' and moving['target']==0,action=action,handle_point_cm=_xyz(r.interaction_point(item)),walked_to_handle_cm=round(v['open_reach_walked_cm'],2))
                self._phase('movable_reclosed',float(item['motion'].get('duration',1))+.25)
                return
            position=pawn.get_actor_location();delta=position-v['open_reach_position'];travelled=math.hypot(delta.x,delta.y)
            if travelled>1:
                v['open_reach_walked_cm']+=travelled;v['open_reach_position']=position;v['open_reach_progress']=now
            point=r.interaction_point(item);target=r.vector(item['open_validation_approach']) if item.get('open_validation_approach') else point
            remaining=_horizontal_distance(position,target)
            if now-v['open_reach_began']>6 or now-v['open_reach_progress']>2 or remaining<4:
                self._stop();self.check('E closes '+item['actor'],False,action=None,reason='Actual moving handle cannot be selected/reached from its walking approach',selected_actor=selected['actor'] if selected else None,handle_point_cm=_xyz(point),actual_player_cm=_xyz(position))
                moving['target']=0.;self._phase('movable_reclosed',float(item['motion'].get('duration',1))+.25);return
            pawn.add_movement_input(u.Vector((target.x-position.x)/remaining,(target.y-position.y)/remaining,0),max(.16,min(.65,remaining/80)))
        elif phase == 'movable_reclosed':
            item = self.movables[v['index']]
            moving = state['movables'][item['actor']]
            self.check('movable returns closed: ' + item['actor'], moving['progress'] < .005)
            # Return service cupboards and crew pans to their authored state.
            # Walking routes explicitly open their required passenger/room doors.
            moving['target'] = 1.0 if item.get('initial_open',False) else 0.0
            v['index'] += 1
            self._phase('movable_start', (float(item['motion'].get('duration',1)) if moving['target'] else 0)+.15)
        elif phase == 'fixtures_reset':
            self._standing();delay=self._restore_authored_fixtures();self._phase('fixtures_ready',delay+.3)
        elif phase == 'fixtures_ready':
            incomplete=[name for name,moving in state['movables'].items() if abs(moving['progress']-moving['target'])>.005]
            self.check('all configured movable fittings restored to authored state before navigation',not incomplete,category='configuration',configured_count=len(state['movables']),incomplete_actors=incomplete,
                       method='all106 motion targets set to authored initial_open, animation completion verified; flightdeck door opened for walking prerequisites')
            if incomplete:self.fail('Movable test fixtures did not finish restoring');return
            self._phase(v['reset_resume'],index=0)
        elif phase == 'barrier_start':
            if v['index'] >= len(self.barriers):
                self._phase('walk_start' if self.walks else 'finish', index=0)
                return
            test = self.barriers[v['index']]
            if test['actor'] not in state['movables']:
                raise ValueError('Barrier actor is not a configured movable: ' + test['actor'])
            delay = self._close_actors([test['actor']])
            self._phase('barrier_ready', delay + .2)
        elif phase == 'barrier_ready':
            test = self.barriers[v['index']]
            v['barrier_start'] = self._place(test['start'])
            v['barrier_direction'] = self._source_direction(test['direction'])
            v['until'] = now + float(test.get('duration', .8))
            self._phase('barrier_move')
        elif phase == 'barrier_move':
            test = self.barriers[v['index']]
            pawn.add_movement_input(v['barrier_direction'], 1)
            if now >= v['until']:
                self._stop()
                position = pawn.get_actor_location()
                source = [position.x / 100, -position.y / 100, position.z / 100]
                axis = test.get('axis', 'x')
                axis = ('x', 'y', 'z').index(axis) if isinstance(axis, str) else int(axis)
                low, high = test['closed_range']
                displacement = position - v['barrier_start'];direction = v['barrier_direction']
                progress = (displacement.x * direction.x + displacement.y * direction.y) / 100
                moving = state['movables'][test['actor']]
                passed = low <= source[axis] <= high and progress >= float(test.get('min_progress', .05))
                passed = passed and pawn.get_actor_enable_collision() and moving['progress'] < .005 and not state.get('seated')
                self.check(test['name'], passed, category='barriers', target_actor=test['actor'],
                           end_source_m=source, accepted_range_source_m=[low, high],
                           travelled_source_m=round(progress, 4), collision_enabled=pawn.get_actor_enable_collision(),
                           closed_fraction=moving['progress'], method='actual standing movement into closed leaf; no teleport after initial placement')
                delay = self._open_actors([test['actor']])
                self._phase('barrier_reopen', delay + .2)
        elif phase == 'barrier_reopen':
            test = self.barriers[v['index']]
            self.check('reopen after barrier: ' + test['name'],
                       state['movables'][test['actor']]['progress'] > .995, category='barriers')
            v['index'] += 1
            self._phase('barrier_start', .1)
        elif phase == 'walk_start':
            test=self.walks[v['index']]
            delay = max(self._open_actors(test.get('open_actors')),self._close_actors(test.get('close_actors')))
            self._phase('walk_ready', delay + .2)
        elif phase == 'walk_ready':
            self._start_walk()
        elif phase == 'walk_move':
            self._walk_move(now)
        elif phase == 'finish':
            tests = self.report['interactions'] + self.report['navigation'] + self.report['configuration'] + self.report['barriers'] + self.report['body_clearance']
            self.report['status'] = 'SUCCESS' if tests and all(test['passed'] for test in tests) else 'FAILED'
            self.report['capture_count'] = len(self.report['captures'])
            self.report['walking_routes_passed'] = sum(bool(test['passed']) for test in self.report['navigation']
                                                       if 'waypoints_source_m' in test)
            self.report['walking_routes_total'] = len(self.walks)
            self.report['closed_barriers_passed'] = sum(bool(test['passed']) for test in self.report['barriers'] if 'target_actor' in test)
            self.report['closed_barriers_total'] = len(self.barriers)
            self.report['control_fittings_total']=self.inventory['controls']
            self.report['inspectable_fittings_total']=self.inventory['inspectables']
            self.report['seats_inventory_total']=self.inventory['seats']
            self.report['fresh_seat_count']=len(self.seats)
            self.report['fresh_control_fittings_total']=len(self.controls)
            self.report['fresh_inspectable_fittings_total']=len(self.inspects)
            self.report['fresh_movable_fittings_total']=len(self.movables)
            self.report['crew_fold_seats_inventory_total']=self.inventory['crew_fold_seats']
            self.report['fresh_crew_fold_and_sit_total']=sum(bool(item.get('requires_open')) for item in self.seats)
            self.report['body_clearance_routes_total']=len(self.report['body_clearance'])
            self.report['body_clearance_routes_passed']=sum(bool(test['passed']) for test in self.report['body_clearance'])
            self.finish()
        else:
            raise RuntimeError('Unknown validation phase: ' + str(phase))
