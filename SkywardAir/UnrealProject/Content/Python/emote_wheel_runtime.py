"""Hold/drag/release emotes and an independent third-person orbit camera."""
import math,time
import unreal as u
from emote_wheel_model import RadialSelection,OrbitState,damp_alpha
from emote_wheel_ui import WheelView


def mouse_xy(value):
    if value is None:return None
    values=list(value)
    if len(values)==3 and isinstance(values[0],bool):
        if not values.pop(0):return None
    elif len(values)==3 and isinstance(values[-1],bool):
        if not values.pop():return None
    if len(values)!=2:return None
    return float(values[0]),float(values[1])


class EmoteController:
    OWNER='character_pack_emotes'
    MOVE_KEYS=('W','A','S','D','SpaceBar','Gamepad_FaceButton_Bottom')

    def __init__(self,pack):
        self.pack=pack;self.selection=RadialSelection();self.view=OrbitState();self.ui=WheelView(pack)
        self.camera=None;self.position=None;self.input_locked=False;self.opened_at=0.;self.last_geometry=None;self._warned_trace=False
        self.keys={n:pack.key(n) for n in ['Z','Escape','Left','Right','MouseScrollUp','MouseScrollDown','LeftAlt','RightAlt','Gamepad_LeftX','Gamepad_LeftY',*self.MOVE_KEYS]}

    @property
    def state(self):return self.pack.S
    @property
    def pc(self):return self.state['pc']
    @property
    def game(self):return self.state['game']

    def unavailable(self):
        return bool(self.game.P.STATE.get('seated') or self.game.P.STATE.get('inspecting') or self.game.S.get('driving') or self.game.S.get('spectator') or self.state.get('external_pose'))

    def build_widget(self):self.ui.build()

    def ensure_camera(self):
        if self.pack.valid(self.camera):return self.camera
        library=u.get_default_object(u.GameplayStatics);transform=u.Transform()
        actor=library.call_method('BeginDeferredActorSpawnFromClass',(self.state['world'],u.CameraActor,transform,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        self.camera=library.call_method('FinishSpawningActor',(actor,transform,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        self.camera.set_actor_label('CharacterPack Emote Orbit');self.camera.camera_component.set_field_of_view(72.)
        return self.camera

    def begin_orbit(self):
        if self.unavailable():return False
        entering=self.view.begin(self.state['avatar'].get_actor_rotation().yaw)
        self.state['legacy'].S.update(third=True,camera_owner=self.OWNER)
        if entering:
            self.ensure_camera();self.position=None;self.update_camera(0.)
            self.pc.set_view_target_with_blend(self.camera,.24,u.ViewTargetBlendFunction.VT_BLEND_CUBIC,0.,False)
        return True

    def open(self):
        if self.state['wheel_open'] or self.unavailable():return False
        self.pack.create_wheel()
        # A radial selection replaces an earlier emote without queuing another.
        self.state['emote']=None;self.state['last_clip']=None
        if not self.begin_orbit():return False
        self.prior_cursor=self.pc.get_editor_property('show_mouse_cursor')
        movement=self.state['pawn'].get_component_by_class(u.FloatingPawnMovement)
        if movement:movement.stop_movement_immediately()
        self.pc.set_ignore_move_input(True);self.pc.set_ignore_look_input(True);self.input_locked=True
        self.pc.set_editor_property('show_mouse_cursor',True)
        # Keep keyboard polling on the controller; no UMG button takes focus.
        u.WidgetLibrary.set_input_mode_game_and_ui_ex(self.pc,None,u.MouseLockMode.DO_NOT_LOCK,False,False)
        self.state['wheel_open']=True;self.opened_at=time.monotonic();self.selection.open(len(self.pack.page_items()))
        self.ui.get('WheelPanel').set_visibility(u.SlateVisibility.SELF_HIT_TEST_INVISIBLE)
        self.ui.get('WheelShade').set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE)
        self.ui.get('EmoteHint').set_visibility(u.SlateVisibility.COLLAPSED)
        self.last_geometry=self.ui.measure();cx,cy,_,_=self.last_geometry
        self.pc.set_mouse_location(round(cx),round(cy));self.ui.refresh()
        return True

    def close(self,keep_third=False):
        if not self.state['wheel_open']:return
        self.state['wheel_open']=False;self.selection.cancel()
        self.ui.get('WheelPanel').set_visibility(u.SlateVisibility.COLLAPSED)
        self.ui.get('WheelShade').set_visibility(u.SlateVisibility.COLLAPSED)
        self.ui.get('EmoteHint').set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE)
        pc_valid=self.pack.valid(self.pc)
        if self.input_locked and pc_valid:
            self.pc.set_ignore_move_input(False);self.pc.set_ignore_look_input(False);self.input_locked=False
        self.input_locked=False
        if pc_valid:
            self.pc.set_editor_property('show_mouse_cursor',self.prior_cursor)
            u.WidgetLibrary.set_input_mode_game_only(self.pc,False)
        if not keep_third and pc_valid:self.return_to_first_person(time.monotonic())
        elif not pc_valid:self.view.abort();self.release_ownership()

    def page_changed(self):
        self.selection.set_page(len(self.pack.page_items()));self.ui.refresh()

    def profile_changed(self):
        if self.state['wheel_open']:self.selection.suppress_until_center()
        self.ui.refresh()

    def return_to_first_person(self,now):
        if self.view.start_return(now):
            self.state['emote']=None;self.state['last_clip']=None
            # A single native cubic blend also interpolates FOV back to the pawn.
            self.pc.set_view_target_with_blend(self.state['pawn'],self.view.return_seconds,u.ViewTargetBlendFunction.VT_BLEND_CUBIC,0.,True)

    def release_ownership(self):
        if self.state['legacy'].S.get('camera_owner')==self.OWNER:
            self.state['legacy'].S.pop('camera_owner',None)
        self.state['legacy'].S['third']=False

    def abort_camera(self):
        if self.state['wheel_open']:self.close(True)
        if not self.view.active:return
        self.state['emote']=None;self.state['last_clip']=None;self.view.abort();self.release_ownership()
        # Sitting/inspection/vehicle cameras own their own view target already.
        if self.pack.valid(self.pc) and self.pack.valid(self.camera) and self.pc.get_view_target()==self.camera:
            self.pc.set_view_target_with_blend(self.state['pawn'],.24,u.ViewTargetBlendFunction.VT_BLEND_CUBIC,0.,True)

    def moving(self):
        if any(self.pc.is_input_key_down(self.keys[n]) or self.pc.was_input_key_just_pressed(self.keys[n]) for n in self.MOVE_KEYS):return True
        if any(abs(self.pc.get_input_analog_key_state(self.keys[n]))>.18 for n in ('Gamepad_LeftX','Gamepad_LeftY')):return True
        velocity=self.state['pawn'].get_velocity()
        return math.hypot(velocity.x,velocity.y)>10.

    def process_input(self,dt,now):
        if self.unavailable():
            self.abort_camera();return
        if self.pc.was_input_key_just_pressed(self.keys['Z']):self.pack.open_wheel()
        if self.state['wheel_open']:
            if any(self.pc.was_input_key_just_pressed(self.keys[n]) for n in ['Escape','LeftAlt','RightAlt']):
                self.pack.close_wheel(False);return
            for n,delta in [('Left',-1),('Right',1),('MouseScrollUp',-1),('MouseScrollDown',1)]:
                if self.pc.was_input_key_just_pressed(self.keys[n]):self.pack.change_page(delta)
            geometry=self.ui.measure()
            if geometry!=self.last_geometry:
                self.last_geometry=geometry;self.selection.set_page(len(self.pack.page_items()))
                self.pc.set_mouse_location(round(geometry[0]),round(geometry[1]))
            pointer=mouse_xy(self.pc.get_mouse_position());cx,cy,scale,dpi=geometry
            self.selection.update(pointer[0]-cx if pointer else None,pointer[1]-cy if pointer else None,scale*dpi,self.ui.over_controls())
            self.ui.animate(dt,self.opened_at,now)
            for index,name in enumerate(self.pack.NUMBERS):
                if self.pc.was_input_key_just_pressed(self.pack.KEYS[name]):self.pack.choose_slot(index);return
            if self.pc.was_input_key_just_released(self.keys['Z']) or not self.pc.is_input_key_down(self.keys['Z']):
                index=self.selection.release()
                if index is None:self.pack.close_wheel(False)
                else:self.pack.choose_slot(index)
        elif self.pc.was_input_key_just_pressed(self.keys['Escape']) and self.view.active:
            self.return_to_first_person(now)
        if not self.state['wheel_open'] and self.view.phase=='orbit' and self.moving():self.return_to_first_person(now)
        if self.view.update(now):self.release_ownership()

    def camera_target(self):
        pawn=self.state['pawn'];pivot=pawn.get_actor_location()+u.Vector(0,0,-67.)
        rotation=self.pc.get_control_rotation();raw_pitch=(rotation.pitch+180.)%360.-180.;pitch=max(-55.,min(35.,raw_pitch))
        if abs(pitch-raw_pitch)>.001:self.pc.set_control_rotation(u.Rotator(pitch=pitch,yaw=rotation.yaw,roll=0.))
        direction=u.MathLibrary.get_forward_vector(u.Rotator(pitch=pitch,yaw=rotation.yaw))
        return pivot,pivot-direction*285.+u.Vector(0,0,32.)

    def avoid_walls(self,pivot,target):
        ignored=[self.state['pawn'],self.state['avatar']]
        ignored.extend(a for a in self.state['legacy'].S.get('hands',{}).values() if self.pack.valid(a))
        old=self.state['legacy'].S.get('avatar')
        if self.pack.valid(old):ignored.append(old)
        raw=u.SystemLibrary.sphere_trace_single(self.state['world'],pivot,target,16.,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,u.DrawDebugTrace.NONE,True)
        if not raw:return target
        hit=raw if isinstance(raw,u.HitResult) else next((v for v in raw if isinstance(v,u.HitResult)),None)
        if not hit:return target
        # HitResult's native Python break wrapper is to_tuple(); the C++
        # GameplayStatics BreakHitResult function is not exported to Python.
        result=hit.to_tuple()
        if result[0]:return pivot+(target-pivot)*max(0.,float(result[2])-.025)
        return target

    def update_camera(self,dt):
        if self.view.phase!='orbit':return
        self.ensure_camera();pivot,target=self.camera_target()
        target=self.avoid_walls(pivot,target)
        if self.position is None:self.position=target
        else:
            # Collapse immediately at a wall; ease outward once clear.
            alpha=1. if (target-pivot).length()<(self.position-pivot).length()-1. else damp_alpha(dt,14.)
            self.position+=(target-self.position)*alpha
        self.camera.set_actor_location(self.position,False,True)
        self.camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(self.position,pivot),False)

    def avatar_visible(self,now):
        if not self.view.active:return False
        if self.view.phase=='returning':return self.view.progress(now)<=.68
        pivot=self.state['pawn'].get_actor_location()+u.Vector(0,0,-67.)
        return self.position is None or (self.position-pivot).length()>65.

    def stop(self):
        self.abort_camera()
        if self.pack.valid(self.camera):self.camera.destroy_actor()
        self.camera=None;self.ui.cache.clear()
