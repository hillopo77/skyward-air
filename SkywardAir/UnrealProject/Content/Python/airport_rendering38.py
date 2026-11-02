"""One final measured renderer authority for Airport38 only.

Call install AFTER every legacy initializer. Legacy modes never import this.
"""
import json
import sys
import time
from pathlib import Path
import unreal as u
from rendering38 import PROFILE

G=None
S={}


def measured_profile():
    values={k:float(u.SystemLibrary.get_console_variable_float_value(k)) for k in PROFILE['cvars']}
    vp=list(G.P.STATE['pc'].get_viewport_size())
    return dict(name=PROFILE['name'],viewport=vp,settings=values,
        internal_render_extent_approx=[round(v*values['r.ScreenPercentage']/100) for v in vp],
        native_resolution=(values['r.ScreenPercentage']==100),
        grain_policy='zero in AP38 grade; not inferred from a CVar',
        updated=time.time())


def apply_profile(reason='final authority'):
    w,pc=G.P.STATE['world'],G.P.STATE['pc']
    for key,value in PROFILE['cvars'].items():
        u.SystemLibrary.execute_console_command(w,'%s %s'%(key,value),pc)
    S['applications'].append(dict(reason=reason,at=time.monotonic()-S['started']))
    # Legacy diagnostics should report our current profile, too.
    old=sys.modules.get('airport_clarity26')
    if old:old.S['profile']=PROFILE['name']


def _correct_plane_status():
    """Keep the legacy plane's other data, replace its false nominal label."""
    path=Path(G.P.ROOT)/'ArtBible/RuntimeStatus.json'
    if not path.exists():return
    data=json.loads(path.read_text(encoding='utf-8'))
    measured=measured_profile();values=measured['settings'];vp=measured['viewport']
    data['profile']='%sx%s / %s%% native viewport / TAA%s / weight%s / filter%s'%(
        *vp,values['r.ScreenPercentage'],values['r.TemporalAASamples'],
        values['r.TemporalAACurrentFrameWeight'],values['r.TemporalAAFilterSize'])
    data['rendering_measured38']=measured
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')


def _write_plane():
    result=S['old_plane_write']()
    _correct_plane_status()
    return result


def _configure_plane():
    result=S['old_plane_configure']()
    apply_profile('legacy plane configure intercepted')
    return result


def _write_status(measured=None):
    measured=measured or measured_profile()
    out=Path(G.R)/'ArtBible';out.mkdir(parents=True,exist_ok=True)
    drift={k:dict(expected=v,actual=measured['settings'][k]) for k,v in PROFILE['cvars'].items()
           if abs(measured['settings'][k]-v)>1e-4}
    (out/'RenderingSession38.json').write_text(json.dumps(dict(
        status='READY' if not drift else 'PROFILE_DRIFT',actual=measured,
        requested=PROFILE,drift=drift,applications=S['applications'][-30:],
        runtime_viewport_is_measured=True,
        validation='Settings only; visual/temporal/capture-free performance require separate native evidence'),indent=2),encoding='utf-8')


def tick(dt):
    S['base_physics'](dt)
    now=time.monotonic()
    if now-S.get('checked',0)<.75:return
    S['checked']=now
    measured=measured_profile()
    if any(abs(measured['settings'][k]-v)>1e-4 for k,v in PROFILE['cvars'].items()):
        apply_profile('detected later legacy reset')
        measured=measured_profile()
    if now-S.get('written',0)>=2:
        S['written']=now;_write_status(measured)


def install(game):
    global G
    if S.get('installed'):raise RuntimeError('Airport38 rendering installed twice')
    G=game
    if G.D.get('revision')!=38:raise RuntimeError('Rendering38 is only for Airport38')
    S.update(installed=True,started=time.monotonic(),applications=[],base_physics=G.physics)
    G.physics=tick
    old=sys.modules.get('airport_clarity26')
    if old:
        S['old_apply_profile']=old.apply_profile
        old.apply_profile=lambda name:apply_profile('legacy profile request '+str(name))
    S['old_plane_write']=G.P.write;G.P.write=_write_plane
    S['old_plane_configure']=G.P.configure;G.P.configure=_configure_plane
    apply_profile('Airport38 final initialization')
    # Request the native client size once. Every report still uses actual size.
    u.SystemLibrary.execute_console_command(G.P.STATE['world'],'r.SetRes 1920x1080w',G.P.STATE['pc'])
    _write_status();_correct_plane_status()
    G.event('Airport38 measured final rendering',profile=PROFILE['name'],
            resolution='native viewport 100%',settings_measured=True)
