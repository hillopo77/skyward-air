"""Held-body aim/dispatch regressions against production functions.

The trace adapter resolves the first intersected physical plane, respecting
only the supplied ignore list. It does not grant visibility or interaction.
These bounded Python checks supplement, rather than replace, native QA.
"""
import ast
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch

from flight39_frame import Frame
from test_props39 import V


HERE = Path(__file__).resolve().parent
# Journey38 has a pure policy dependency beside its runtime module. Load the
# actual owned runtime without importing the native Unreal game bootstrap.
with patch.object(sys, 'path', [str(HERE.parent), *sys.path]):
    spec = importlib.util.spec_from_file_location('journey38_interaction_test', HERE.parent / 'airport_journey38.py')
    JOURNEY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(JOURNEY)


def core_use(namespace):
    """Compile the real core dispatcher in an isolated test namespace."""
    source = HERE.parents[4] / 'SkywardAir/UnrealProject/Content/Python/skyward_runtime.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'use_nearest')
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['use_nearest']


class TraceScene:
    def __init__(self):
        self.planes = []
        self.calls = []

    def add(self, name, y, enabled=True):
        actor = N(name=name)
        self.planes.append(dict(actor=actor, y=y, enabled=enabled))
        return actor

    def trace(self, world, start, end, channel, complex_query, ignored, *args):
        self.calls.append(tuple(ignored))
        hits = []
        for plane in self.planes:
            if not plane['enabled'] or any(plane['actor'] is a for a in ignored):
                continue
            dy = end.y - start.y
            if not dy:
                continue
            t = (plane['y'] - start.y) / dy
            if 0 <= t <= 1:
                point = start + (end - start) * t
                if abs(point.x - 1600) <= 80 and abs(point.z - 162) <= 100:
                    hits.append((t, plane['actor'], point))
        if not hits:
            return None
        _, actor, point = min(hits, key=lambda h: h[0])
        values = [None] * 11
        values[0], values[5], values[9] = True, point, actor
        return N(to_tuple=lambda: tuple(values))


def fixture(kind='seat', wall=False, target_collision=True):
    scene = TraceScene()
    pawn = scene.add('Pawn', 0)
    pawn.get_actor_location = lambda: V(1600, 0, 162)
    bag = scene.add('Held suitcase', 45)
    scene.add('Opaque wall', 85, wall)
    target = scene.add('Pilot seat' if kind == 'seat' else 'Battery key', 150, target_collision)
    pressed = [False]
    item = dict(actor=target.name, kind=kind, point=[16, -1.5, 1.62])
    state = dict(pawn=pawn, pc=N(get_control_rotation=lambda: None,
                                was_input_key_just_pressed=lambda key: pressed[0]),
                 world=object(), movables={}, items=[item], seated=None,
                 controls={target.name: dict(state=0)}, door_target=0)
    native = N(MathLibrary=N(get_forward_vector=lambda rotation: V(0, 1, 0)),
               SystemLibrary=N(line_trace_single=scene.trace),
               TraceTypeQuery=N(TRACE_TYPE_QUERY1=1), DrawDebugTrace=N(NONE=0))
    frame = Frame.__new__(Frame)
    p = N(STATE=state, actor_name=lambda actor: actor.name,
          vector=lambda v: V(v[0]*100, -v[1]*100, v[2]*100))
    frame.P, frame.u = p, native
    frame.reference = frame.world = lambda v: v
    p.interaction_visible, p.nearest = frame.visible, frame.nearest
    # A recursive dispatcher call is a failure, never a test fallback.
    p.use_nearest = Mock(side_effect=AssertionError('re-entered wrapped P.use_nearest'))
    g = N(P=p, u=native, S=dict(held='bag', actors={'bag': bag}),
          KEY={'LeftMouseButton': 'mouse'}, nearest=lambda: None, act=Mock())
    frame.G = g
    sit = Mock(side_effect=lambda q: state.update(seated=q))
    control = Mock(side_effect=lambda name, value: state['controls'][name].update(state=value))
    namespace = dict(STATE=state, nearest=p.nearest, sit=sit, set_control_state=control,
                     write=Mock(), stand=Mock(), end_inspect=Mock(),
                     show_screen_page=Mock(), inspect_item=Mock())
    g.S['original_use'] = Mock(wraps=core_use(namespace))
    runtime = dict(coffee=dict(actor='Serving cup', sips=3), base_use=Mock(return_value='base'))
    return N(frame=frame, scene=scene, g=g, p=p, item=item, bag=bag, pawn=pawn,
             state=state, runtime=runtime, pressed=pressed, sit=sit, control=control)


class HeldAimTests(unittest.TestCase):
    def assert_only_pawn_and_held_ignored(self, f):
        self.assertTrue(f.scene.calls)
        for ignored in f.scene.calls:
            self.assertEqual(len(ignored), 2)
            self.assertIs(ignored[0], f.pawn)
            self.assertIs(ignored[1], f.bag)

    def test_held_bag_is_ignored_for_surface_and_assisted_aim(self):
        for target_collision in (True, False):
            with self.subTest(target_collision=target_collision):
                f = fixture(target_collision=target_collision)
                self.assertIs(f.frame.nearest(), f.item)
                self.assertTrue(f.frame.visible(f.item))
                self.assert_only_pawn_and_held_ignored(f)

    def test_opaque_wall_blocks_surface_and_assisted_target_with_held_bag(self):
        for target_collision in (True, False):
            with self.subTest(target_collision=target_collision):
                f = fixture(wall=True, target_collision=target_collision)
                self.assertFalse(f.frame.visible(f.item))
                self.assertIsNone(f.frame.nearest())
                self.assert_only_pawn_and_held_ignored(f)

    def test_unheld_body_remains_an_occluder(self):
        f = fixture()
        f.scene.add('Other suitcase', 65)
        self.assertFalse(f.frame.visible(f.item))
        self.assertIsNone(f.frame.nearest())
        self.assert_only_pawn_and_held_ignored(f)

    def test_no_held_or_stale_held_reference_ignores_only_pawn(self):
        f = fixture()
        for held in (None, 'missing'):
            with self.subTest(held=held):
                f.g.S['held'] = held
                ignored = f.frame.aim_ignored()
                self.assertEqual(len(ignored), 1)
                self.assertIs(ignored[0], f.pawn)
                self.assertFalse(f.frame.visible(f.item))
                self.assertIsNone(f.frame.nearest())


class HeldUseTests(unittest.TestCase):
    def use(self, f):
        with patch.object(JOURNEY, 'G', f.g), patch.object(JOURNEY, 'S', f.runtime):
            return JOURNEY.use()

    def test_held_e_dispatches_actual_seat_and_control_once_without_recursion(self):
        for kind in ('seat', 'control'):
            with self.subTest(kind=kind):
                f = fixture(kind)
                self.assertEqual(self.use(f), kind)
                f.g.S['original_use'].assert_called_once_with(stand_on_miss=False)
                f.p.use_nearest.assert_not_called()
                f.runtime['base_use'].assert_not_called()
                self.assertEqual(f.g.S['held'], 'bag')
                if kind == 'seat':
                    f.sit.assert_called_once_with(f.item)
                    self.assertIs(f.state['seated'], f.item)
                else:
                    f.control.assert_called_once_with(f.item['actor'], 1)
                    self.assertEqual(f.state['controls'][f.item['actor']]['state'], 1)

    def test_held_use_cannot_dispatch_seat_or_control_through_opaque_wall(self):
        for kind in ('seat', 'control'):
            with self.subTest(kind=kind):
                f = fixture(kind, wall=True)
                self.assertEqual(self.use(f), 'base')
                f.g.S['original_use'].assert_not_called()
                f.p.use_nearest.assert_not_called()
                f.sit.assert_not_called()
                f.control.assert_not_called()
                self.assertIsNone(f.state['seated'])
                self.assertEqual(f.state['controls'][f.item['actor']]['state'], 0)

    def test_held_left_mouse_does_not_activate_plane_fitting(self):
        f = fixture('control')
        f.pressed[0] = True
        self.assertEqual(self.use(f), 'base')
        f.g.S['original_use'].assert_not_called()
        f.p.use_nearest.assert_not_called()
        f.control.assert_not_called()
        f.runtime['base_use'].assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
