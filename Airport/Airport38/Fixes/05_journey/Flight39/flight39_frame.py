"""Moving reference frame for the authored plane; one carrier transform per tick.

Manifest points and cached closed poses remain in the parked reference frame.
Only fittings which actually animate are written individually. Static aircraft
actors, proxies, lights and passengers inherit the carrier transform natively.
"""
import math,time,inspect,configparser
from pathlib import Path
from flight39_model import native_basis
from flight39_envelope import pressure_envelope,contains_point,contains_box,bridge_overlap,boarding_threshold_overlap


def occupied_reference(item,placements):
    p=item.get('location',item.get('point',[999,999,999]))
    return any(math.hypot(p[0]-n['location'][0],p[1]-n['location'][1])<.28 and abs(p[2]-n['location'][2]-1.38)<.55
               for n in placements if n.get('animation','').endswith('Seated'))


def inherit_current_carrier(velocity,carrier):
    """A newly carried body may already have inherited the platform speed.

    Choose the interpretation with the smaller local velocity, so a stationary
    carried bag receives90m/s once while a bag already moving90m/s never gets
    doubled to180m/s. Subsequent frames use explicit recorded carrier velocity.
    """
    world_relative=sum((v-c)**2 for v,c in zip(velocity,carrier))
    local_relative=sum(v*v for v in velocity)
    return list(velocity) if world_relative<=local_relative else [v+c for v,c in zip(velocity,carrier)]


def simulated_step_time(world_dt,maximum,minimum=0.):
    """Chaos can integrate less time than the carrier/world during a hitch."""
    if world_dt<minimum:return 0.
    return min(world_dt,maximum) if maximum>0 else world_dt


def physics_clock(G):
    """Read the engine's active cap once, with the saved project as fallback."""
    try:
        settings=G.u.get_default_object(G.u.PhysicsSettings)
        return dict(maximum=float(settings.get_editor_property('max_physics_delta_time')),
                    minimum=float(settings.get_editor_property('min_physics_delta_time')),source='PhysicsSettings CDO')
    except Exception:
        # Installed module lives under Content/Python; isolated source tests
        # live under outputs/Airport. Both resolve the same actual project.
        candidates=[p/'Config/DefaultEngine.ini' for p in Path(__file__).resolve().parents]
        candidates += [p/'SkywardAir/UnrealProject/Config/DefaultEngine.ini' for p in Path(__file__).resolve().parents]
        for path in candidates:
            if not path.is_file():continue
            config=configparser.ConfigParser(strict=False);config.read(path,encoding='utf-8-sig')
            section='/Script/Engine.PhysicsSettings'
            if config.has_option(section,'MaxPhysicsDeltaTime'):
                return dict(maximum=config.getfloat(section,'MaxPhysicsDeltaTime'),
                            minimum=config.getfloat(section,'MinPhysicsDeltaTime',fallback=0.),source=str(path))
        raise RuntimeError('Flight39 cannot resolve the actual native physics timestep cap')


class Frame:
    def __init__(self,G,carrier):
        self.G=G;self.P=G.P;self.u=G.u;self.carrier=carrier
        self.base=carrier.get_actor_transform();self.current=self.base;self.delta=self.u.Quat(x=0.,y=0.,z=0.,w=1.)
        self.attached=False;self.attached_roots=[];self.prop_records={};self.last_velocity=self.u.Vector()
        self.spectator_active=False
        self.last_pose=None
        self.motion_previous=self.base;self.motion_dt=0.;self.prop_scan_clock=0.;self.prop_scan_count=0
        self.physics_clock=physics_clock(G);self.physics_dt=0.
        offset=getattr(G,'D',{}).get('aircraft38',{}).get('offset',[16.])[0]
        self.envelope=pressure_envelope(self.P.DATA,offset)
        self.spectator_movement=None
        self.original={n:getattr(self.P,n) for n in ['_apply_movable','_apply_control','interaction_point','nearest','sit','stand','update_floor','update_door','point_at','inspect_item','end_inspect','control_snapshot']}
        # Airport's parked-X shortcut is invalid after the plane turns west.
        # Unwrap precisely that named closure; retain plane18 seat assistance.
        nearest=self.original['nearest']
        if getattr(nearest,'__name__','')=='aircraft_nearest':self.original['nearest']=inspect.getclosurevars(nearest).nonlocals.get('original_nearest',nearest)
        self.old_floor=G.S.get('original_floor');self.old_spectator=G.toggle_spectator
        # Core flightdeck door uses absolute parked yaw0 / -open_yaw, even
        # when installation happens after the player has already opened it.
        self.door_q=self.u.Quat(x=0.,y=0.,z=0.,w=1.);self.door_fraction=-self.P.STATE['door'].get_actor_rotation().yaw

    def world(self,p):return self.u.MathLibrary.transform_location(self.current,self.u.MathLibrary.inverse_transform_location(self.base,p))
    def reference(self,p):return self.u.MathLibrary.transform_location(self.base,self.u.MathLibrary.inverse_transform_location(self.current,p))
    def rotation(self,q):return self.P._quat_product(self.delta,q)
    def reference_rotation(self,q):
        d=self.delta;return self.P._quat_product(self.u.Quat(x=-d.x,y=-d.y,z=-d.z,w=d.w),q)
    def local_axis(self,v):return self.P._quat_vector(self.delta,v)
    def aboard(self):
        if self.G.S.get('spectator'):return False
        return self.point_inside(self.P.STATE['pawn'].get_actor_location())

    def attach(self,a):
        if a==self.carrier:return
        root=a.root_component
        if not root:return
        root.set_mobility(self.u.ComponentMobility.MOVABLE)
        a.attach_to_actor(self.carrier,self.u.Name(''),self.u.AttachmentRule.KEEP_WORLD,self.u.AttachmentRule.KEEP_WORLD,self.u.AttachmentRule.KEEP_WORLD,False)

    def bind(self):
        u=self.u;P=self.P;G=self.G;allactors=u.GameplayStatics.get_all_actors_of_class(P.STATE['world'],u.Actor)
        self.aircraft_seats={q['actor'] for q in P.STATE['items'] if q['kind']=='seat'}
        explicit={P.STATE['door']}
        for moving in P.STATE['movables'].values():
            explicit.add(moving['actor']);explicit.update(q['actor'] for q in moving.get('links',[]))
        for control in P.STATE['controls'].values():explicit.update(t['actor'] for t in control['targets'] if t.get('actor'))
        self.npc_names=set()
        for q in G.D.get('character_placements',[]):
            p=q.get('location',[0,0,0])
            if 12<p[0]<20 and -7<p[1]<43 and -3.6<p[2]<6.5:
                self.npc_names.update([q['actor'],'CH12COLL '+q['name']])
        selected=[]
        for a in allactors:
            if a in (self.carrier,P.STATE['pawn']):continue
            n=a.get_actor_label();tags=[str(t) for t in a.tags]
            aircraft=any(t.startswith('Skyward:') or t.startswith('SkywardLight:') or t.startswith('SkywardCamera:') for t in tags)
            aircraft|=n.startswith(('COL_','MOTION_PROXY','Flight39 instrument ','Flight39 flap ','Flight39 aileron ','Flight39 elevator ','Flight39 rudder ','Flight39 gear ','Flight39 Status','Flight39 Beacon','Flight39 Chase'))
            aircraft|=n in self.npc_names
            aircraft|=a in explicit
            # Airport-character actors aboard the translated aircraft, selected
            # from the authored placement registry rather than broad world tags.
            if n in G.S.get('actor_specs',{}):
                q=G.S['actor_specs'][n];p=q.get('location',[0,0,0]);aircraft|=('Character' in q.get('asset','') and 12<p[0]<20 and -6<p[1]<40)
            if isinstance(a,u.DirectionalLight) or 'sun' in n.lower():aircraft=False
            if aircraft:selected.append(a)
        selected_set=set(selected)
        # A selected child may already be parented to a selected actor. Its own
        # component still needs MOVABLE before any native parent motion.
        self.mobility_audit=[]
        for a in selected:
            root=a.root_component
            if root:
                before=str(root.get_editor_property('mobility'));root.set_mobility(u.ComponentMobility.MOVABLE)
                if before!=str(root.get_editor_property('mobility')):self.mobility_audit.append(dict(object=a.get_name(),label=a.get_actor_label(),before=before,after=str(root.get_editor_property('mobility'))))
        self.native_warning_actor=[]
        for a in allactors:
            if a.get_name()=='StaticMeshActor_851':
                root=a.root_component;parent=a.get_attach_parent_actor()
                self.native_warning_actor.append(dict(object=a.get_name(),label=a.get_actor_label(),selected=a in selected_set,
                    mobility=str(root.get_editor_property('mobility')) if root else None,parent=parent.get_actor_label() if parent else None))
        for a in selected:
            parent=a.get_attach_parent_actor()
            if parent not in selected_set:self.attach(a);self.attached_roots.append(a)
        # Source-configured closed transforms are deliberately left untouched.
        self.refresh_props(0.,force=True)
        self.original_release=G.release;G.release=self.release
        try:
            import characters12_runtime as CH
            for n in list(CH.S.get('walkers',{})):
                a=G.S['actors'].get(n)
                if a in selected_set:CH.S['walkers'].pop(n,None)
        except ImportError:pass
        P._apply_movable=self.apply_movable;P._apply_control=self.apply_control
        P.interaction_point=self.point;P.interaction_visible=self.visible;P.nearest=self.nearest;P.sit=self.sit;P.stand=self.stand
        P.update_floor=self.floor;G.S['original_floor']=self.floor;P.update_door=self.update_door
        P.inspect_item=self.inspect;P.end_inspect=self.end_inspect;P.control_snapshot=self.control_snapshot
        P.point_at=lambda p:P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(P.STATE['pawn'].get_actor_location(),self.world(P.vector(p))))
        # Configure precedes this installer. If an inherited static component
        # rejected its initial knob/leaf pose, restore that actual declared pose
        # once after mobility promotion; do not trust the state index alone.
        for moving in P.STATE['movables'].values():P._apply_movable(moving)
        for control in P.STATE['controls'].values():P._apply_control(control)
        G.toggle_spectator=self.spectator
        old_point=G.point
        def airport_point(q):
            a=G.S['actors'].get(q['actor'])
            if q['actor'] in self.npc_names and a and q['kind']=='npc':
                return a.get_actor_location()+self.u.MathLibrary.get_right_vector(a.get_actor_rotation())*25+self.local_axis(self.u.Vector(0,0,130))
            return old_point(q)
        G.point=airport_point
        import airport_ext11_runtime as EX
        old_stow=EX.stow
        def stow():
            n=G.S.get('held')
            if n not in self.prop_records or n not in EX.HOMES:return old_stow()
            # A terminal extinguisher carried aboard still belongs to its real
            # terminal bracket; its home must not be treated as a plane point.
            home_source=G.source(EX.HOMES[n].translation)
            if not(12<home_source[0]<20 and -8.5<home_source[1]<43.5):return old_stow()
            a=G.S['actors'][n];home=EX.HOMES[n];position=self.world(home.translation)
            if (a.get_actor_location()-position).length()>300:G.say('Return near the wall bracket to stow');return
            G.release(False);a.static_mesh_component.set_simulate_physics(False)
            a.set_actor_location_and_rotation(position,self.rotation(home.rotation).rotator(),False,True);self.attach(a)
            EX.CHARGE[n]=10.;G.event('Extinguisher stowed',actor=n)
        EX.stow=stow

    def spectator(self):
        G=self.G;P=self.P;u=self.u;pawn=P.STATE['pawn'];pc=P.STATE['pc'];move=pawn.get_component_by_class(u.FloatingPawnMovement)
        if not self.spectator_active:
            if not self.aboard():return self.old_spectator()
            self.spectator_active=True;self.spectator_saved=P.STATE.get('seated');self.spectator_return=self.reference(pawn.get_actor_location())
            P.STATE['seated']=None;P.STATE['review_index']=-1
            if self.attached:self.detach_pawn()
            G.S['spectator']=True;move.activate(True);move.set_plane_constraint_enabled(False);pc.reset_ignore_move_input();pawn.set_actor_enable_collision(False);pc.set_view_target_with_blend(pawn,.1)
            G.say('Free camera / WASD + mouse / Space-Ctrl up-down / Shift fast / Tab returns to your seat')
        else:
            self.spectator_active=False;G.S['spectator']=False;move.stop_movement_immediately();pc.set_view_target_with_blend(pawn,.1)
            if self.spectator_saved:
                saved=self.spectator_saved;self.sit(saved);P.STATE['seated']=saved
            else:
                pawn.set_actor_location(self.world(self.spectator_return),False,True);pawn.set_actor_enable_collision(True);self.attach(pawn);self.attached=True;self.floor(0)
            G.say('Returned aboard / flight controls active')

    def detach_pawn(self):
        p=self.P.STATE['pawn'];p.detach_from_actor(self.u.DetachmentRule.KEEP_WORLD,self.u.DetachmentRule.KEEP_WORLD,self.u.DetachmentRule.KEEP_WORLD)
        self.attached=False;self.G.S['carrier_velocity39']=self.u.Vector()
        move=p.get_component_by_class(self.u.FloatingPawnMovement);move.set_plane_constraint_normal(self.u.Vector(0,0,1))

    def pose(self,position,heading,pitch,bank,dt):
        u=self.u;P=self.P;old=self.current;oldq=self.delta
        # Three clocks differ during a hitch: stability-clamped flight model,
        # world/carrier motion, and the engine's capped Chaos integration.
        native_dt=dt;delta_seconds=getattr(u.GameplayStatics,'get_world_delta_seconds',None)
        if delta_seconds:
            value=float(delta_seconds(P.STATE['world']))
            if value>0:native_dt=value
        f,z=native_basis(heading,pitch,bank);forward=u.Vector(*f);up=u.Vector(*z)
        rot=u.MathLibrary.make_rot_from_yz(forward,up)
        location=P.vector(position);signature=tuple(position)+(heading,pitch,bank);changed=signature!=self.last_pose
        if changed:
            self.carrier.set_actor_location_and_rotation(location,rot,False,True);self.current=self.carrier.get_actor_transform();self.delta=rot.quaternion();self.last_pose=signature
        self.motion_previous=old;self.motion_dt=max(native_dt,.001)
        self.physics_dt=simulated_step_time(native_dt,self.physics_clock['maximum'],self.physics_clock['minimum'])
        # Native physics has already advanced bodies this world frame; compare
        # their actual COM with the corresponding NEW aircraft frame.
        self.refresh_props(native_dt)
        velocity=(location-old.translation)/self.motion_dt;self.last_velocity=velocity
        seat=P.STATE.get('seated');seated_aboard=seat and seat.get('actor') in self.aircraft_seats
        should=(self.aboard() or seated_aboard) and not self.G.S.get('spectator')
        if should and not self.attached:self.attach(P.STATE['pawn']);self.attached=True
        elif not should and self.attached:self.detach_pawn()
        if self.attached:
            inv=u.Quat(x=-oldq.x,y=-oldq.y,z=-oldq.z,w=oldq.w)
            dq=P._quat_product(self.delta,inv);pc=P.STATE['pc']
            pc.set_control_rotation(P._quat_product(dq,pc.get_control_rotation().quaternion()).rotator())
        self.update_spring_frame()
        if changed or self.G.S.get('previous_carrier_velocity39',u.Vector()).length()>.001:self._props(old,oldq,velocity)
        self.spectator_speed()
        return changed

    def body_inside(self,a,transform=None):
        return self.point_inside(a.static_mesh_component.get_center_of_mass(),transform)

    def point_inside(self,p,transform=None):
        q=self.u.MathLibrary.inverse_transform_location(transform or self.current,p)
        reference=self.u.MathLibrary.transform_location(self.base,q)
        return contains_point(self.envelope,[reference.x/100,-reference.y/100,reference.z/100])

    def body_source_bounds(self,actor):
        centre,extent=actor.get_actor_bounds(True)
        points=[]
        for x in (-1,1):
            for y in (-1,1):
                for z in (-1,1):
                    p=centre+self.u.Vector(x*extent.x,y*extent.y,z*extent.z);q=self.reference(p)
                    points.append([q.x/100,-q.y/100,q.z/100])
        return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]

    def body_fully_inside(self,actor):
        """Strict departure exemption: the complete colliding box is aboard."""
        bounds=self.body_source_bounds(actor);aircraft=self.G.D['aircraft38']
        return (contains_box(self.envelope,bounds)
                and not boarding_threshold_overlap(bounds,aircraft['crossing'])
                and not bridge_overlap(bounds,aircraft['bridge']['floor_polygons']))

    def release(self,throw=False):
        G=self.G;name=G.S.get('held');a=G.S.get('actors',{}).get(name)
        if a:
            if self.body_inside(a):self.register_prop(name,a)
            rec=self.prop_records.get(name)
            if rec:
                # Release and the ordinary9m/s throw impulse remain native
                # relative physics while inside the same cabin. Adding the
                # carrier here would simulate its movement a second time.
                rec['released']=True
                if not self.body_inside(a):self._leave_prop(name,rec)
        result=self.original_release(throw);self.update_spring_frame();return result

    def point_velocity(self,p):
        if self.motion_dt<=0:return self.u.Vector()
        local=self.u.MathLibrary.inverse_transform_location(self.current,p)
        before=self.u.MathLibrary.transform_location(self.motion_previous,local)
        return (p-before)/self.motion_dt

    def _prop_component(self,body):
        if isinstance(body,str):body=self.G.S.get('actors',{}).get(body)
        component=getattr(body,'static_mesh_component',body)
        rec=next((q for q in self.prop_records.values() if q['actor']==body or q['actor'].static_mesh_component==component),None)
        return component,rec

    def world_velocity(self,body):
        """Actual reference-space velocity plus the carrier point velocity."""
        c,rec=self._prop_component(body);native=c.get_physics_linear_velocity()
        return native+self.point_velocity(c.get_center_of_mass()) if rec else native

    def relative_velocity(self,body):
        """Registered native velocities are relative; outside velocities are world."""
        c,rec=self._prop_component(body);native=c.get_physics_linear_velocity()
        return native if rec else native-self.point_velocity(c.get_center_of_mass())

    def update_spring_frame(self):
        # Core's real force-based pickup spring must use the body's own
        # velocity space. Aboard bodies are simulated locally, outside bodies
        # retain the original world-space spring and carrier compensation.
        held=self.G.S.get('held')
        local=held in self.prop_records
        self.G.S['carrier_velocity39']=self.u.Vector() if local or not self.attached else self.point_velocity(self.P.STATE['pawn'].get_actor_location())
        self.G.S['held_physics_frame39']='aircraft-relative' if local else 'world'

    def _leave_prop(self,name,rec,carrier=None):
        """Crossing the envelope changes reference space once, without an impulse fake."""
        c=rec['actor'].static_mesh_component
        if c.is_simulating_physics():
            carrier=carrier if carrier is not None else self.point_velocity(c.get_center_of_mass())
            c.set_physics_linear_velocity(c.get_physics_linear_velocity()+carrier,False,self.u.Name(''))
        self.prop_records.pop(name,None)

    def register_prop(self,name,a):
        if not self.body_inside(a):return None
        u=self.u;c=a.static_mesh_component;carrier=self.point_velocity(c.get_center_of_mass())
        simulating=c.is_simulating_physics();rec=self.prop_records.get(name)
        if rec is not None and not(simulating and not rec['simulating']):
            rec['simulating']=simulating;return rec
        if simulating:
            old=c.get_physics_linear_velocity();adopted=u.Vector(*inherit_current_carrier(old.to_tuple(),carrier.to_tuple()))
            # Incoming airport bodies can already carry the world platform
            # speed or only their walking velocity. Convert once on entry.
            c.set_physics_linear_velocity(adopted-carrier,False,u.Name(''))
        rec=dict(actor=a,carrier_velocity=carrier,integrated_carrier=u.Vector(),released=False,simulating=simulating,reference_space='aircraft-relative')
        self.prop_records[name]=rec;return rec

    def refresh_props(self,dt,force=False):
        # Only the small native physics registry, four times per second. A
        # held newcomer is checked immediately; no scene-actor tick scan.
        self.prop_scan_clock+=dt;held=self.G.S.get('held')
        if held:
            a=self.G.S.get('actors',{}).get(held)
            if a:self.register_prop(held,a)
        if not force and self.prop_scan_clock<.25:return
        self.prop_scan_clock=0.;self.prop_scan_count+=1
        for name,a in list(self.G.S.get('physics',{}).items()):
            spec=self.G.S.get('actor_specs',{}).get(name,{});asset=spec.get('asset','').lower()
            if any(n in asset for n in ('tug','dolly','vehicle')) or spec.get('tow_to'):continue
            if self.G.valid(a):self.register_prop(name,a)
        for name,rec in list(self.prop_records.items()):
            if not self.G.valid(rec['actor']):self.prop_records.pop(name,None)
            elif not self.body_inside(rec['actor']) and self.point_velocity(rec['actor'].static_mesh_component.get_center_of_mass()).length()<.001:
                # A parked throw can leave the real volume without any later
                # carrier pose change. Hand it to world physics with zero
                # carrier speed; never wait for takeoff to clean the record.
                self._leave_prop(name,rec,self.u.Vector())
        # Envelope exit is evaluated in _props against the OLD frame before
        # transport, never against a carrier already moved several metres.

    def spectator_speed(self):
        # Core airport tick applies its old6/18m/s before physics. Override it
        # only in free-camera mode, and restore acceleration on return aboard.
        pawn=self.P.STATE['pawn'];move=pawn.get_component_by_class(self.u.FloatingPawnMovement)
        if self.G.S.get('spectator'):
            if self.spectator_movement is None:self.spectator_movement={n:move.get_editor_property(n) for n in ('acceleration','deceleration')}
            boost=self.P.STATE['pc'].is_input_key_down(self.G.KEY['LeftShift'])
            speed=20000. if boost else 3000.;move.set_editor_property('max_speed',speed)
            move.set_editor_property('acceleration',80000.);move.set_editor_property('deceleration',80000.)
            self.G.S['spectator_speed39_m_s']=speed/100
        elif self.spectator_movement is not None:
            for n,v in self.spectator_movement.items():move.set_editor_property(n,v)
            self.spectator_movement=None;self.G.S.pop('spectator_speed39_m_s',None)

    def _props(self,old,oldq,velocity):
        # One reference-frame transform for the small cabin prop registry.
        # Chaos integrates ONLY relative motion. Carrier transport is applied
        # once here, so moving-floor contacts cannot impart90m/s a second time.
        u=self.u;P=self.P;inv=u.Quat(x=-oldq.x,y=-oldq.y,z=-oldq.z,w=oldq.w);dq=P._quat_product(self.delta,inv)
        for name,rec in list(self.prop_records.items()):
            a=rec['actor'];c=a.static_mesh_component
            if not c.is_simulating_physics():
                rec['simulating']=False
                if not self.body_inside(a):self.prop_records.pop(name,None)
                continue
            rel=c.get_physics_linear_velocity();p=a.get_actor_location();com=c.get_center_of_mass()
            inside=self.point_inside(com,old)
            q=u.MathLibrary.inverse_transform_location(old,p)
            com_local=u.MathLibrary.inverse_transform_location(old,com);next_com=u.MathLibrary.transform_location(self.current,com_local)
            carrier=(next_com-com)/self.motion_dt
            a.set_actor_location_and_rotation(u.MathLibrary.transform_location(self.current,q),P._quat_product(dq,a.get_actor_rotation().quaternion()).rotator(),False,True)
            c.set_physics_linear_velocity(P._quat_vector(dq,rel),False,u.Name(''))
            if hasattr(c,'get_physics_angular_velocity_in_radians'):
                c.set_physics_angular_velocity_in_radians(P._quat_vector(dq,c.get_physics_angular_velocity_in_radians()),False,u.Name(''))
            rec['carrier_velocity']=carrier;rec['integrated_carrier']=u.Vector();rec['simulating']=True
            if not inside:self._leave_prop(name,rec,carrier)
        self.G.S['previous_carrier_velocity39']=velocity
        self.update_spring_frame()

    def apply_movable(self,item):
        P=self.P;u=self.u;motion=item['item']['motion'];fraction=item['progress'];position=item['closed_location'];rotation=item['closed_rotation']
        if motion.get('type')=='roller_shade18':
            f=fraction*fraction*(3-2*fraction)
            for part in item['item']['roller_parts']:
                a=P.STATE['actors'][part['actor']];a.set_actor_location(self.world(P.vector(part['closed_location'])+P.vector(part['delta'])*f),False,False)
            return
        for stage in motion['stages'] if motion.get('type')=='compound' else [motion]:
            start=float(stage.get('start',0));end=float(stage.get('end',1));t=max(0,min(1,(fraction-start)/(end-start)));t=t*t*(3-2*t)
            if stage.get('type','rotate')=='rotate':rotation=P._quat_product(rotation,P._source_quat(stage.get('axis','z').lower(),float(stage.get('amount_degrees',stage.get('amount',90)))*t))
            else:position=position+P.vector(stage['delta'])*t
        pos=self.world(position);rot=self.rotation(rotation);a=item['actor'];a.set_actor_location_and_rotation(pos,rot.rotator(),False,False)
        if 'closed_point' in item:item['current_point']=pos+P._quat_vector(rot,item['closed_point'])
        for link in item.get('links',[]):
            spec=link['spec'];start=self.world(P.vector(spec['start']));end=pos+P._quat_vector(rot,P.vector(spec['end_local']));d=end-start;length=d.length()
            if length<.01:continue
            direction=d/length;q=u.MathLibrary.make_rot_from_z(direction);rod=link['actor']
            rod.set_actor_location_and_rotation((start+end)*.5,q,False,False);rod.set_actor_scale3d(u.Vector(link['scale'].x,link['scale'].y,length/100));rod.set_actor_enable_collision(False)
        # Roller shades consist of several physically linked telescoping leaves.
        for leaf in item.get('shade_parts18',[]):
            part=leaf.get('actor');origin=leaf.get('closed_location')
            if part and origin:part.set_actor_location(self.world(origin+P.vector(leaf.get('delta',[0,0,0]))*fraction),False,False)

    def apply_control(self,control):
        # Material/intensity policy is unchanged. Pose targets are converted
        # from their frozen closed reference exactly once, without old writes.
        P=self.P;i=control['state']
        for target in control['targets']:
            spec=target['spec'];a=target.get('actor');c=target.get('component')
            if 'visible_states' in spec:a.set_actor_hidden_in_game(i not in spec['visible_states'])
            if spec.get('collision') is False:a.set_actor_enable_collision(False)
            if 'materials' in target:c.set_material(target['slot'],target['materials'][i])
            if 'intensity_states' in spec:target['light'].light_component.set_intensity(float(spec['intensity_states'][i]))
            if 'rotation_states' in spec:a.set_actor_rotation(self.rotation(P._quat_product(target['rotation'],P._source_quat(spec.get('axis','z'),spec['rotation_states'][i]))).rotator(),False)
            if 'translation_states' in spec:a.set_actor_location(self.world(target['location']+P.vector(spec['translation_states'][i])),False,False)

    def point(self,item):
        P=self.P
        if item.get('inside_point'):
            p=self.G.source(self.reference(P.STATE['pawn'].get_actor_location()));r=item['inside_rect']
            if r[0]<=p[0]<=r[1] and r[2]<=p[1]<=r[3]:return self.world(P.vector(item['inside_point']))
        moving=P.STATE['movables'].get(item['actor']) if item.get('motion') else None
        follows=item.get('point_follows_actor',True)
        if moving and item['actor'] in P.STATE.get('fixed_lever_actors',set()):follows=False
        if follows:
            binding=moving if moving and 'closed_point' in moving else P.STATE.get('point_bindings',{}).get(item['actor'])
            if binding:return binding['actor'].get_actor_location()+P._quat_vector(binding['actor'].get_actor_rotation().quaternion(),binding['closed_point'])
        return self.world(P.vector(item['point']))

    def nearest(self,kind=None):
        P=self.P;u=self.u;pos=P.STATE['pawn'].get_actor_location();reference=self.reference(pos);pc=P.STATE['pc']
        forward=u.MathLibrary.get_forward_vector(pc.get_control_rotation())
        hit=u.SystemLibrary.line_trace_single(P.STATE['world'],pos,pos+forward*300,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,self.aim_ignored(),u.DrawDebugTrace.NONE,True)
        h=hit.to_tuple() if hit else None
        owner,impact=(P.actor_name(h[9]) if h[9] else '',h[5]) if h and h[0] else ('',None)
        choices=[]
        if P.STATE.get('seated') and isinstance(kind,tuple):kind=kind+('movable',)
        kinds=(kind,) if isinstance(kind,str) else kind
        radii={'control':.09,'inspect':.15,'seat':.34,'screen':.29,'movable':.27,'door':.38}
        surfaces={'control':.16,'inspect':.28,'seat':.68,'screen':.55,'movable':1.40,'door':1.40}
        reaches={'control':2.30,'inspect':2.30,'seat':2.50,'screen':2.60,'movable':2.65,'door':2.65}
        for item in P.STATE['items']:
            if item.get('activation')=='inspect_only' or kinds and item['kind'] not in kinds:continue
            if item['kind']=='screen' and P.STATE.get('seated') and item['actor']!=P.STATE['seated'].get('screen_actor'):continue
            required=item.get('requires_open')
            if required and P.STATE['movables'].get(required,{}).get('progress',0)<.95:continue
            source=item['point']
            # One inverse transform for the pawn, then cheap numeric coarse
            # checks. Never transform every fitting through the native bridge.
            if (source[0]*100-reference.x)**2+(-source[1]*100-reference.y)**2+(source[2]*100-reference.z)**2>650**2:continue
            point=self.point(item);d=point-pos;distance=d.length();category=item['kind'];dot=(d.x*forward.x+d.y*forward.y+d.z*forward.z)/max(distance,.001)
            if dot<=0:continue
            lateral=distance*math.sqrt(max(0,1-dot*dot));reach=float(item.get('reach',reaches.get(category,2.3)))*100
            owns=owner==item['actor'] or owner in item.get('visibility_owners',[]) or owner in item.get('linked_actors',[]) or category=='seat' and owner==required
            # Compare a shared pair in the reference frame, not worldX after
            # the carrier turns. The opposite chair remains an occluder.
            if owns and category=='seat' and owner!=item['actor'] and abs(self.reference(impact).x-self.reference(point).x)>=34:owns=False
            surface=owns and (impact-point).length()<=surfaces.get(category,.25)*100 and (impact-pos).length()<reach
            angle=math.degrees(math.acos(max(-1,min(1,dot))))
            assisted=distance<reach and angle<(8. if category=='control' else 12. if category=='inspect' else 14.) and lateral<float(item.get('focus_radius',radii.get(category,.15)))*100+distance*.055
            if not surface and not assisted:continue
            if not surface and not P.interaction_visible(item):continue
            score=angle*(.20 if category=='inspect' else 1.)
            if surface:score=min(score,.10 if category=='control' else .65 if category=='seat' and required else 1.25)
            choices.append((score,distance,item))
        return min(choices,key=lambda q:(q[0],q[1]))[2] if choices else None

    def sit(self,item):
        P=self.P;u=self.u;p=P.STATE['pawn'];pc=P.STATE['pc'];move=p.get_component_by_class(u.FloatingPawnMovement)
        if item.get('actor') not in self.aircraft_seats:return self.original['sit'](item)
        if not self.G.S.get('aboard'):self.G.say('Board through Gate A07 first');return False
        import characters12_runtime as CH
        if occupied_reference(item,CH.S.get('placements',[])):
            self.G.say('This seat is occupied');return False
        P.STATE['seated']={**item,'return':self.reference(p.get_actor_location()),'return_frame39':True}
        if item.get('screen_actor'):P.STATE['seated']['screen_actor']=item['screen_actor']
        move.stop_movement_immediately();move.set_plane_constraint_enabled(False);move.deactivate();pc.set_ignore_move_input(True);p.set_actor_enable_collision(False)
        p.set_actor_location(self.world(P.vector(item['location'])),False,True)
        facing=item.get('facing',[0,-1,0]);yaw=math.degrees(math.atan2(-facing[1],facing[0]));q=u.Rotator(pitch=float(item.get('view_pitch',-5)),yaw=yaw).quaternion()
        pc.set_control_rotation(self.rotation(q).rotator());self.attach(p);self.attached=True;P.write();return True

    def aim_ignored(self):
        ignored=[self.P.STATE['pawn']]
        held=self.G.S.get('actors',{}).get(self.G.S.get('held'))
        if held:ignored.append(held)
        return ignored

    def visible(self,item):
        P=self.P;u=self.u;pos=P.STATE['pawn'].get_actor_location();point=self.point(item)
        hit=u.SystemLibrary.line_trace_single(P.STATE['world'],pos,point,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,self.aim_ignored(),u.DrawDebugTrace.NONE,True)
        if not hit:return True
        h=hit.to_tuple()
        if not h[0]:return True
        owner=P.actor_name(h[9]) if h[9] else ''
        if owner==item['actor']:return True
        if owner in item.get('visibility_owners',[]):return item['kind']!='seat' or abs(self.reference(h[5]).x-self.reference(point).x)<34
        return (h[5]-point).length()<=.2

    def stand(self):
        P=self.P;saved=P.STATE.get('seated')
        if not saved:return
        flight=self.G.S.get('flight39',{})
        if saved.get('actor') in ('SM_Plane_Seat.016','SM_Plane_Seat.017'):
            if flight.get('speed',0)>12 and not flight.get('airborne'):
                self.G.say('Finish the takeoff roll or slow down before leaving the flight controls');return False
            if flight.get('airborne'):
                # The game flight model holds its current trim with neutral
                # controls. Release held axes so a key cannot remain latched
                # while the player walks through the actual moving cabin.
                flight['controls'].update(roll=0.,pitch=0.,rudder=0.,brake=0.)
        saved['return']=self.world(saved['return']) if saved.get('return_frame39') else saved['return']
        result=self.original['stand']();self.floor(0);return result

    def floor(self,dt):
        P=self.P;u=self.u;pawn=P.STATE.get('pawn')
        if not pawn or self.G.S.get('spectator') or self.G.S.get('driving') or P.STATE.get('seated') or P.STATE.get('inspecting'):return
        if not self.aboard():return self.original['update_floor'](dt)
        reference=self.reference(pawn.get_actor_location());x,y,z=self.G.source(reference)
        height,name=self.G.journey38['floor_at_source'](x,y,z-P.EYE_HEIGHT)
        if height is None:return
        desired=self.world(P.vector([x,y,height+P.EYE_HEIGHT]))
        if (desired-pawn.get_actor_location()).length()>.015:pawn.set_actor_location(desired,True,False)
        move=pawn.get_component_by_class(u.FloatingPawnMovement);move.set_plane_constraint_normal(self.local_axis(u.Vector(0,0,1)));move.set_plane_constraint_origin(pawn.get_actor_location());move.set_plane_constraint_enabled(True)
        P.STATE.update(floor_z=height,floor_name=name)

    def update_door(self,dt):
        P=self.P;target=P.STATE['door_target'];change=target-self.door_fraction
        self.door_fraction+=math.copysign(min(abs(change),dt*100),change) if abs(change)>.02 else 0
        if abs(change)>.02:P.STATE['door'].set_actor_rotation(self.rotation(P._quat_product(self.door_q,P._source_quat('z',self.door_fraction))).rotator(),False)
        for item in P.STATE['movables'].values():
            change=item['target']-item['progress']
            if abs(change)>.0001:
                duration=max(.1,float(item['item']['motion'].get('duration',1)));item['progress']+=math.copysign(min(abs(change),dt/duration),change);P._apply_movable(item)
        now=time.monotonic()
        for name,c in P.STATE['controls'].items():
            if c['reset_at'] is not None and now>=c['reset_at']:P.set_control_state(name,int(c['item'].get('initial_state',0)))

    def door_diagnostics(self):
        P=self.P;a=P.STATE['door'];root=a.root_component;parent=a.get_attach_parent_actor();t=a.get_actor_transform();r=a.get_actor_rotation()
        q=P._source_quat('z',self.door_fraction);expected=self.rotation(q).rotator();target=P.STATE['door_target']
        error=max(abs((getattr(r,k)-getattr(expected,k)+180)%360-180) for k in ('pitch','yaw','roll'))
        def rotation(v):return dict(pitch=v.pitch,yaw=v.yaw,roll=v.roll)
        data=dict(label=a.get_actor_label(),object=a.get_name(),fraction=self.door_fraction,target=target,
            location_source=list(self.G.source(a.get_actor_location())),rotation=rotation(r),expected_rotation=rotation(expected),
            error_degrees=error,pose_matches_fraction=error<.1,mobility=str(root.get_editor_property('mobility')),
            transform=dict(translation=list(t.translation.to_tuple()),rotation=[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],scale=list(t.scale3d.to_tuple())),
            parent=parent.get_actor_label() if parent else None,source_quaternion_type=type(q).__name__,source_quaternion=[q.x,q.y,q.z,q.w],
            relative_rotation=rotation(root.get_editor_property('relative_rotation')))
        c=a.get_component_by_class(self.u.StaticMeshComponent)
        if c:data.update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,collision_profile=str(c.get_collision_profile_name()),collision_enabled=str(c.get_collision_enabled()))
        # Duplicate leaves or a forgotten moving proxy can keep the threshold
        # blocked even when the scalar and selected actor agree. Record them.
        data['nearby_door_actors']=[]
        for n,actor in P.STATE['actors'].items():
            if 'door' in n.lower() and (actor.get_actor_location()-a.get_actor_location()).length()<300:
                data['nearby_door_actors'].append(dict(name=n,label=actor.get_actor_label(),object=actor.get_name(),rotation=rotation(actor.get_actor_rotation()),parent=actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None))
        return data

    def inspect(self,item):
        P=self.P;u=self.u;pc=P.STATE['pc'];pawn=P.STATE['pawn'];move=pawn.get_component_by_class(u.FloatingPawnMovement)
        move.stop_movement_immediately();pc.reset_ignore_move_input();pc.set_ignore_move_input(True)
        saved=dict(item=item,view_ref=self.reference_rotation(pc.get_control_rotation().quaternion()),opened={})
        for n in item.get('open_actors',[]):m=P.STATE['movables'][n];saved['opened'][n]=m['target'];m['target']=1.
        camera=P.STATE['cameras'].get(item.get('camera'))
        if not camera:raise RuntimeError('Inspection requires an actual authored camera: '+item['actor'])
        pc.set_view_target_with_blend(camera,.25)
        if item.get('hold'):
            a=P.STATE['actors'][item['actor']];origin=a.get_actor_location();old=a.get_actor_rotation().quaternion();hold=item['hold'];basis=camera.get_actor_rotation().quaternion()
            saved['held']=dict(actor=a,location_ref=self.reference(origin),rotation_ref=self.reference_rotation(old),collision=a.get_actor_enable_collision(),movables={})
            pos=camera.get_actor_location()+P._quat_vector(basis,u.Vector(*[float(v)*100 for v in hold.get('offset',[.38,0,-.06])]))
            angles=hold.get('rotation',[90,0,0]);rot=P._quat_product(basis,u.Rotator(pitch=angles[0],yaw=angles[1],roll=angles[2]).quaternion());dq=P._quat_product(rot,u.Quat(x=-old.x,y=-old.y,z=-old.z,w=old.w))
            a.set_actor_enable_collision(False);a.set_actor_location_and_rotation(pos,rot.rotator(),False,True)
            for n in dict.fromkeys(item.get('open_actors',[])+item.get('hold_actors',[])):
                m=P.STATE['movables'][n];saved['held']['movables'][n]=(m['closed_location'],m['closed_rotation'],m['actor'].get_actor_enable_collision())
                m['closed_location']=self.reference(pos+P._quat_vector(dq,self.world(m['closed_location'])-origin));m['closed_rotation']=self.reference_rotation(P._quat_product(dq,self.rotation(m['closed_rotation'])))
                m['actor'].set_actor_enable_collision(False);P._apply_movable(m)
        P.STATE['inspecting']=saved;P.write()

    def end_inspect(self):
        P=self.P;saved=P.STATE.get('inspecting')
        if not saved:return
        held=saved.get('held')
        if held:
            held['actor'].set_actor_location_and_rotation(self.world(held['location_ref']),self.rotation(held['rotation_ref']).rotator(),False,True);held['actor'].set_actor_enable_collision(held['collision'])
            for n,(pos,rot,collision) in held['movables'].items():
                m=P.STATE['movables'][n];m['closed_location']=pos;m['closed_rotation']=rot;m['actor'].set_actor_enable_collision(collision);P._apply_movable(m)
        for n,target in saved['opened'].items():P.STATE['movables'][n]['target']=target
        P.STATE['pc'].set_view_target_with_blend(P.STATE['pawn'],.25);P.STATE['pc'].set_control_rotation(self.rotation(saved['view_ref']).rotator());P.STATE['pc'].reset_ignore_move_input()
        if P.STATE.get('seated'):P.STATE['pc'].set_ignore_move_input(True)
        P.STATE['inspecting']=None;P.write()

    def control_snapshot(self,actor):
        # The existing validator is retained, with expectations expressed in
        # current world coordinates for this one inspection call only.
        saved=[];P=self.P
        for target in P.STATE['controls'][actor]['targets']:
            old=dict(target);spec=target['spec'];saved.append((target,old))
            if 'rotation' in target:target['rotation']=self.rotation(target['rotation'])
            if 'location' in target:target['location']=self.world(target['location'])
            if 'translation_states' in spec:
                target['spec']=dict(spec,translation_states=[self.G.source(self.local_axis(P.vector(p))) for p in spec['translation_states']])
        try:return self.original['control_snapshot'](actor)
        finally:
            for target,old in saved:target.clear();target.update(old)
