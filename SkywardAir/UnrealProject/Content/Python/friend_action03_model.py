"""Deterministic paired cartoon prop action, independent of Unreal.

Animation parameters are visual effects; no anatomical model or real-world
concealment mechanism is represented.
"""
from dataclasses import dataclass
import math

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

@dataclass(frozen=True)
class Config:
    cycles:int=1
    bend_degrees:float=24.
    bend_seconds:float=.35
    cycle_seconds:float=1.8
    settle_seconds:float=.2
    restore_seconds:float=.5
    inset_fraction:float=.5
    withdraw_gap_cm:float=9.
    max_distance_cm:float=210.
    min_rear_dot:float=.2

    def __post_init__(self):
        if self.cycles<1 or self.cycle_seconds<=0 or self.bend_seconds<=0 or self.restore_seconds<=0:raise ValueError('Invalid timing')
        if not 0<=self.inset_fraction<=.5:raise ValueError('Visual inset must be in [0,.5]')
    @property
    def pop_time(self):return self.bend_seconds+self.cycles*self.cycle_seconds
    @property
    def duration(self):return self.pop_time+self.settle_seconds+self.restore_seconds

@dataclass(frozen=True)
class Sample:
    elapsed:float
    phase:str
    bend_degrees:float
    approach:float
    cycle:int
    hide_item:bool
    done:bool
    effort:float=0.

# One continuous resisted feed. Travel holds while the arm loads, then advances
# a little as resistance gives. It never resets to a fully withdrawn position.
FEED_KEYS=((0.,0.,0.),(.10,.22,.15),(.18,.30,.4),(.30,.36,.95),
           (.34,.36,1.),(.40,.45,.4),(.55,.56,.95),(.60,.56,1.),
           (.66,.65,.4),(.80,.77,.95),(.84,.77,1.),(.90,.88,.4),
           (.97,1.,.65),(1.,1.,.65))

def resisted_feed(progress):
    t=max(0.,min(1.,float(progress)))
    for a,b in zip(FEED_KEYS,FEED_KEYS[1:]):
        if t<=b[0]:
            w=smooth((t-a[0])/(b[0]-a[0]))
            return a[1]+(b[1]-a[1])*w,a[2]+(b[2]-a[2])*w
    return 1.,.65

@dataclass(frozen=True)
class PressureTremor:
    lateral_cm:float=0.
    vertical_cm:float=0.
    axial_cm:float=0.
    pitch_degrees:float=0.
    roll_degrees:float=0.
    weight:float=0.

def pressure_tremor(elapsed,effort):
    """Bounded, time-based load tremor. Applied only to the grip and prop."""
    t=max(0.,float(elapsed));weight=smooth((float(effort)-.4)/.6)
    a=math.tau*6.3*t;b=math.tau*8.7*t
    return PressureTremor(
        .65*weight*(.72*math.sin(a)+.28*math.sin(b+.4)),
        .35*weight*(.7*math.sin(a+.9)+.3*math.sin(b+1.2)),
        .08*weight*math.sin(a+.3),
        1.1*weight*math.sin(a+.6),
        1.8*weight*(.75*math.sin(a+1.1)+.25*math.sin(b)),weight)

def prop_visibility(elapsed,cfg=Config(),recovering=False):
    """Cartoon inventory handoff: the whole prop vanishes at the handoff gesture."""
    t=max(0.,float(elapsed))
    if recovering:return smooth((t-.85)/.15)
    return 1.-smooth((t-(cfg.pop_time-.12))/.12)

def receiver_wobble(elapsed,effort):
    weight=smooth((float(effort)-.35)/.65);t=float(elapsed)
    return (1.2*weight*math.sin(math.tau*5.3*t+.7),
            2.4*weight*math.sin(math.tau*4.6*t),
            1.6*weight*math.sin(math.tau*4.9*t+1.1))

def sample(elapsed,cfg=Config()):
    t=max(0.,float(elapsed))
    if t<cfg.bend_seconds:
        p=smooth(t/cfg.bend_seconds);return Sample(t,'bend',cfg.bend_degrees*p,0.,0,False,False)
    if t<cfg.pop_time:
        u=(t-cfg.bend_seconds)/cfg.cycle_seconds;i=min(cfg.cycles-1,int(u));phase=u-i
        stroke,effort=resisted_feed(u/cfg.cycles)
        return Sample(t,'motion',cfg.bend_degrees,stroke,i+1,False,False,effort)
    if t<cfg.pop_time+cfg.settle_seconds:return Sample(t,'pop',cfg.bend_degrees,1.,cfg.cycles,True,False)
    if t<cfg.duration:
        p=smooth((t-cfg.pop_time-cfg.settle_seconds)/cfg.restore_seconds)
        return Sample(t,'restore',cfg.bend_degrees*(1-p),1-p,cfg.cycles,True,False)
    return Sample(t,'done',0.,0.,cfg.cycles,True,True)

def center_distance(half_length_cm,approach,cfg=Config()):
    """Distance of prop bounds center from the clothed surface, along rear normal."""
    outer=half_length_cm+cfg.withdraw_gap_cm
    inner=half_length_cm*(1-2*cfg.inset_fraction)
    return outer+(inner-outer)*max(0.,min(1.,approach))

class Action:
    """One reserved held item, continuous resisted feed, one commit/pop."""
    def __init__(self,cfg=Config()):self.cfg=cfg;self.state=None
    @property
    def busy(self):return self.state is not None
    def begin(self,initiator,target,item,now,*,held_item,distance_cm,rear_dot,target_ready=True):
        if self.busy:return False,'busy'
        if not item or held_item!=item:return False,'no_held_item'
        if initiator==target:return False,'self_target'
        if not target_ready:return False,'target_unavailable'
        if not math.isfinite(distance_cm) or distance_cm>self.cfg.max_distance_cm:return False,'too_far'
        if rear_dot<self.cfg.min_rear_dot:return False,'approach_from_behind'
        self.state={'initiator':initiator,'target':target,'item':item,'started':float(now),'committed':False,'pop_count':0}
        return True,'started'
    def update(self,now):
        if not self.state:return None,[]
        st=self.state;s=sample(float(now)-st['started'],self.cfg);events=[]
        # A large dt cannot skip the pop, nor can another tick duplicate it.
        if s.hide_item and not st['committed']:
            st['committed']=True;st['pop_count']+=1;events.append({'event':'pop','item':st['item'],'target':st['target']})
        if s.done:
            events.append({'event':'finished','item':st['item'],'target':st['target']});self.state=None
        return s,events
    def cancel(self,reason='cancelled'):
        if not self.state:return None
        st=self.state;self.state=None
        return {'event':'cancelled','reason':reason,'item':st['item'],'target':st['target'],'restore_held_item':not st['committed'],'committed':st['committed']}

@dataclass(frozen=True)
class RecoverySample:
    elapsed:float
    phase:str
    bend_degrees:float
    approach:float
    handoff:float
    reveal:bool
    done:bool

def recovery_sample(elapsed):
    t=max(0.,float(elapsed))
    if t<.6:return RecoverySample(t,'bend',24*smooth(t/.6),1.,0.,False,False)
    if t<.85:return RecoverySample(t,'reach',24.,1.,0.,False,False)
    if t<1.1:return RecoverySample(t,'pull',24.,1.-.08*smooth((t-.85)/.25),0.,True,False)
    if t<1.22:return RecoverySample(t,'pull',24.,.92+.08*smooth((t-1.1)/.12),0.,True,False)
    if t<1.5:return RecoverySample(t,'pull',24.,1.-smooth((t-1.22)/.28),0.,True,False)
    if t<1.85:return RecoverySample(t,'handoff',24.,0.,smooth((t-1.5)/.35),True,False)
    if t<2.4:return RecoverySample(t,'restore',24*(1-smooth((t-1.85)/.55)),0.,1.,True,False)
    return RecoverySample(t,'done',0.,0.,1.,True,True)

class Recovery(Action):
    """Inventory owns the item until the outward pull commits, once."""
    duration=2.4
    def begin(self,initiator,target,item,now,*,stored_item,distance_cm,rear_dot,held_item=None):
        if held_item:return False,'hands_full'
        if stored_item!=item:return False,'not_stored'
        ok,reason=super().begin(initiator,target,item,now,held_item=stored_item,distance_cm=distance_cm,rear_dot=rear_dot)
        if ok:self.state['revealed']=False
        return ok,reason
    def update(self,now):
        if not self.state:return None,[]
        st=self.state;pose=recovery_sample(float(now)-st['started']);events=[]
        if pose.reveal and not st['revealed']:
            st['revealed']=True;events.append({'event':'reveal','item':st['item'],'target':st['target']})
        if pose.elapsed>=1.5 and not st['committed']:
            st['committed']=True;events.append({'event':'recovered','item':st['item'],'target':st['target']})
        if pose.done:events.append({'event':'finished','item':st['item'],'target':st['target']});self.state=None
        return pose,events
    def cancel(self,reason='cancelled'):
        if not self.state:return None
        st=self.state;self.state=None
        return {'event':'cancelled','reason':reason,'item':st['item'],'target':st['target'],'restore_held_item':st['committed'],'restore_stored_item':not st['committed'],'committed':st['committed']}
