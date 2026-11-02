"""Engine-independent gesture, animation and camera transition rules."""
from dataclasses import dataclass
import math


def smooth(value):
    t=max(0.,min(1.,value))
    return t*t*(3.-2.*t)


def damp_alpha(dt,rate=18.):
    return 1.-math.exp(-rate*max(0.,dt))


def pop_scale(seconds):
    t=max(0.,min(1.,seconds/.22))-1.
    overshoot=1.+2.70158*t*t*t+1.70158*t*t
    return .78+.22*overshoot


def wheel_geometry(width,height,dpi=1.):
    dpi=max(.25,float(dpi))
    scale=min(1.,max(.2,width/dpi/780.),max(.2,height/dpi/880.))
    return width*.5,height*.5-40.*scale*dpi,scale,dpi


class RadialSelection:
    """Eight fixed compass sectors; unused page sectors remain unselectable."""
    def __init__(self,deadzone=78.,hysteresis_degrees=6.):
        self.deadzone=deadzone;self.hysteresis=hysteresis_degrees
        self.active=False;self.selected=None;self.count=0;self.require_center=False

    def open(self,count):
        self.active=True;self.count=max(0,min(8,count));self.selected=None;self.require_center=False

    def set_page(self,count):
        self.count=max(0,min(8,count));self.selected=None

    def suppress_until_center(self):
        self.selected=None;self.require_center=True

    def update(self,dx,dy,units_to_pixels=1.,blocked=False):
        if not self.active:return None
        if dx is None or dy is None or blocked:
            self.selected=None;return None
        radius=math.hypot(dx,dy)/max(.001,units_to_pixels)
        if radius<self.deadzone:
            self.selected=None;self.require_center=False;return None
        if self.require_center:return None
        # Screen +Y points down: sector0 is up, then proceed clockwise.
        angle=(math.degrees(math.atan2(dy,dx))+90.)%360.
        if self.selected is not None:
            separation=(angle-self.selected*45.+180.)%360.-180.
            if abs(separation)<=22.5+self.hysteresis:return self.selected
        candidate=int((angle+22.5)//45.)%8
        self.selected=candidate if candidate<self.count else None
        return self.selected

    def release(self):
        selected=self.selected if self.active else None
        self.active=False;self.selected=None;return selected

    def cancel(self):
        self.active=False;self.selected=None;self.require_center=False


@dataclass
class OrbitState:
    phase:str='idle'
    body_yaw:float=0.
    returning_at:float=0.
    return_seconds:float=.42

    @property
    def active(self):return self.phase!='idle'

    @property
    def lock_body(self):return self.phase=='orbit'

    def begin(self,body_yaw):
        was_orbit=self.phase=='orbit'
        if not was_orbit:self.body_yaw=float(body_yaw)
        self.phase='orbit'
        return not was_orbit

    def start_return(self,now):
        if self.phase!='orbit':return False
        self.phase='returning';self.returning_at=float(now);return True

    def progress(self,now):
        if self.phase!='returning':return 0.
        return max(0.,min(1.,(now-self.returning_at)/self.return_seconds))

    def update(self,now):
        if self.phase=='returning' and self.progress(now)>=1.:
            self.phase='idle';return True
        return False

    def abort(self):self.phase='idle'
