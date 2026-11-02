"""Procedure test pilot: normal controls only, never aircraft/state teleporting."""
import math
import flight39_model as M


class Driver:
    def __init__(self,api,capture=None):
        self.api=api;self.s=api['state'];self.capture=capture;self.stage='doors';self.elapsed=0.;self.events=[];self.done=False;self.failed=None
        self.path=M.taxi_route();self.hold_along=M.closest_path(M.HOLD,self.path)['along'];self.timer=0;self.max_cross_track=0;self.control_responses={};self.next_capture=0
        self.start=self.s['position'][:];self.started=False

    def note(self,label):
        self.events.append(dict(stage=label,time=self.elapsed,position=self.s['position'][:],speed=self.s['speed']))
        if self.capture:self.capture(label)

    def transition(self,stage):self.stage=stage;self.timer=0;self.note(stage)
    def operate(self,actor,index):return self.api['operate'](actor,index)
    def cmd(self,n,v=None):return self.api['command'](n,v,False)
    def inputs(self,**v):return self.api['inputs'](**v)
    def throttle(self,index):
        for i in (1,2):
            n='Cockpit quadrant lever '+str(i)+'12'
            want=[0.,.25,1.][index]
            if self.s['throttle'][i-1]!=want:self.operate(n,index)

    def tick(self,dt):
        if self.done:return
        self.elapsed+=dt;self.timer+=dt;s=self.s;c=self.api['context']()
        if not c['pilot']:self.failed='Pilot seat lost during test';self.done=True;return
        if self.elapsed>400:self.failed='Procedure exceeded400 seconds';self.done=True;return
        if self.stage=='doors':
            if not self.started:self.cmd('close_doors',1);self.started=True;self.note('crew_close_requested')
            if c['doors_closed']:self.transition('bridge')
        elif self.stage=='bridge':
            if self.timer<dt*1.1:self.cmd('stow_bridge',1)
            if c['bridge_stowed']:self.transition('power')
        elif self.stage=='power':
            for n in ['Cockpit AUX switch12','Cockpit NAV switch12','Cockpit FUEL switch12','Cockpit PUMP switch12','Cockpit AIR switch12','Cockpit overhead switch 0212']:self.operate(n,1)
            self.operate('Cockpit quadrant lever 412',1);self.operate('Cockpit quadrant lever 312',0)
            self.operate('Cockpit overhead switch 0112',1);self.operate('Cockpit overhead switch 1012',1);self.transition('engine_spool')
        elif self.stage=='engine_spool':
            if all(e['running'] for e in s['engines']):
                okay,reason=self.cmd('clearance',1)
                if not okay:self.failed=reason;self.done=True;return
                result=self.operate('Cockpit overhead switch 0312',2)
                if s['parking']:self.failed='Departure interlock: '+result['reason'];self.done=True;return
                self.throttle(1);self.transition('taxi')
        elif self.stage in ('taxi','runway_entry'):
            nearest=M.closest_path(s['position'],self.path);self.max_cross_track=max(self.max_cross_track,nearest['distance'])
            if nearest['distance']>10:self.failed='Taxi centreline deviation >10m';self.done=True;return
            # Flight state position is the main-gear/CG frame, about28m aft of
            # the nose. Stop the NOSE before the paint, not the carrier centre.
            stop=self.hold_along-28. if self.stage=='taxi' else M.closest_path([300,150],self.path)['along']
            remaining=stop-nearest['along'];desired=6.0 if nearest['along']<220 else 8.0
            desired=min(desired,math.sqrt(max(0,remaining-1)*2.8))
            if remaining<1.8:desired=0
            look=M.path_at(self.path,min(stop,nearest['along']+max(5,s['speed']*1.7)))
            err=math.radians(M.angle_error(M.heading_to(s['position'],look),s['heading']))
            yaw=math.degrees(2*s['speed']*math.sin(err)/max(5,s['speed']*1.7));rudder=M.clamp(yaw/(24/(1+s['speed']*.075)),-1,1)
            self.inputs(rudder=rudder,roll=0,pitch=0,brake=M.clamp((s['speed']-desired)*.48,0,1))
            self.throttle(0 if desired<.2 or s['speed']>desired+.5 else 1)
            if desired==0 and s['speed']<.08:
                self.inputs(rudder=0,brake=1)
                if self.stage=='taxi':
                    okay,reason=self.cmd('clearance',1)
                    if not okay:self.failed=reason;self.done=True;return
                    self.transition('runway_entry')
                else:
                    if not M.runway_position(s['position'],s['heading']):self.failed='Not aligned at end of real taxi route';self.done=True;return
                    self.transition('lineup')
        elif self.stage=='lineup':
            self.inputs(brake=1,rudder=0,pitch=0)
            if self.timer>1:
                self.throttle(2);self.inputs(brake=0);self.transition('takeoff_roll')
        elif self.stage=='takeoff_roll':
            error=M.angle_error(0,s['heading']);lateral=s['position'][0]-300
            self.inputs(rudder=M.clamp(error*.06+lateral*.03,-.2,.2),pitch=1. if s['speed']>=s['vr'] else 0.,roll=0,brake=0)
            if s['airborne']:self.transition('climb')
            elif s['position'][1]<M.RUNWAY['north']+100:self.failed='Runway overrun without liftoff';self.done=True
        elif self.stage=='climb':
            target=9.;self.inputs(pitch=M.clamp((target-s['pitch'])*.45,-.7,.7),roll=0,rudder=0)
            if s['position'][2]>25 and s['gear_down']:self.operate('Cockpit overhead switch 0812',2)
            if s['position'][2]>100:
                self.transition('bank_right');self.control_responses['start_heading']=s['heading']
        elif self.stage=='bank_right':
            self.inputs(roll=.55,pitch=M.clamp((8-s['pitch'])*.45,-.7,.7),rudder=.15)
            if self.timer>5:
                self.control_responses.update(bank=s['bank'],heading_change=M.angle_error(s['heading'],self.control_responses['start_heading']),pitch=s['pitch'])
                self.transition('bank_left')
        elif self.stage=='bank_left':
            self.inputs(roll=-.55,pitch=-.12,rudder=-.15)
            if self.timer>5:
                self.control_responses['left_bank']=s['bank'];self.control_responses['pitch_after_down']=s['pitch'];self.transition('recover')
        elif self.stage=='recover':
            self.inputs(roll=0,pitch=M.clamp((6-s['pitch'])*.45,-.7,.7),rudder=0,brake=0)
            if self.timer>4:self.transition('complete');self.done=True;self.inputs(roll=0,pitch=0,rudder=0,brake=0)

    def snapshot(self):
        return dict(stage=self.stage,done=self.done,failed=self.failed,elapsed=self.elapsed,max_cross_track=self.max_cross_track,
                    events=self.events,control_responses=self.control_responses,position=self.s['position'][:],airborne=self.s['airborne'])


def start(G,capture=None):
    """Call only after normal journey and real pilot-seat interaction succeed."""
    if not G.flight39['pilot']():raise RuntimeError('Walk to and occupy a pilot seat first')
    runtime=G.flight39['runtime'];driver=Driver(G.flight39,capture);runtime['autoplay']=True;runtime['driver']=driver
    return driver
