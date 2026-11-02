"""Airport39 character preparation before the preserved12 initializer."""
import json,time,math
from pathlib import Path
import unreal as u
HERE=Path(__file__).resolve().parent
R=HERE if HERE.name=='Revision39' else Path(__file__).resolve().parents[4]/'Characters/Revision39'
S={}


def ready_report():
    path=R/'ArtBible/NativeCharacters39.json'
    if not path.exists():return None
    report=json.loads(path.read_text())
    return report if report.get('status')=='SUCCESS' and report.get('phase')=='APPLIED' else None


def is_ready():return ready_report() is not None


def prepare_before_initialize(game):
    if '-AirportRepair38' not in game.CMD:return
    report=ready_report()
    if report is None:return
    # Native/source alignment is complete before12 builds conversation targets,
    # occupied-seat filters and walking paths. Preserve labels used by gameplay.
    by_actor={q['actor']:q for q in report['placements']}
    for i,q in enumerate(game.D['character_placements']):
        if q['actor'] in by_actor:game.D['character_placements'][i]=dict(by_actor[q['actor']])


def after_initialize(legacy,game):
    report=ready_report()
    if report is None:return
    S.update(game=game,legacy=legacy,base_tick=legacy.tick,report=report,last_blink={},face_tick=0)
    for colour in ('Blue','Yellow','Red','Green','Purple'):
        legacy.S['material_paths']['CH12_'+colour]=report['material_paths']['CH39_'+colour]
    for q in legacy.S['placements']:
        actor=legacy.ACTORS.get(q['actor'])
        if actor:
            c=actor.skeletal_mesh_component
            for name in ('Seated','CafeSeated','CabinSeated','LuxurySeated'):
                c.set_morph_target('SeatFit_'+name,1. if q.get('animation')==name else 0.)
        if q.get('character')=='SecurityGuard':
            for target in game.S.get('targets',[]):
                if target.get('actor')==q['actor'] and target.get('kind')=='npc':target['title']='Talk to security'
    legacy.update_hand_colour();legacy.tick=tick
    game.event('Character39 art ready',characters=len(legacy.ACTORS),skeleton=report['skeleton'],
        source_fit='fixed-length rig plus authored seated contact morphs',native_fit='root capture required')


def tick(dt):
    S['base_tick'](dt);now=time.monotonic();legacy=S['legacy']
    if now-S.get('face_tick',0)<.055:return
    S['face_tick']=now
    for i,(name,actor) in enumerate(legacy.ACTORS.items()):
        phase=(now+i*.47)%(4.6+(i%5)*.17);blink=math.sin(math.pi*phase/.16)**2 if phase<.16 else 0.
        cache=S.setdefault('last_blink',{});previous=cache.get(name)
        if previous is None or abs(blink-previous)>.0001:
            actor.skeletal_mesh_component.set_morph_target('Blink',blink);cache[name]=blink


def patch_legacy_source(source):
    """Root's installer calls this after restoring RecoveryBefore38 source.

    Returns a patched STRING; does not edit a shared file itself. Non38 modes
    keep their original selection and behavior; only ready39 is selected.
    """
    needle="revision=21 if '-Characters21' in G.CMD else 19"
    replacement="revision=39 if '-AirportRepair38' in G.CMD and characters39_runtime.is_ready() else 21 if '-Characters21' in G.CMD else 19"
    if needle not in source:raise RuntimeError('Unknown legacy character revision selector')
    source=source.replace(needle,replacement,1)
    start=' global G,ACTORS,CLIPS;G=game\n'
    if start not in source:raise RuntimeError('Unknown legacy character initializer')
    source=source.replace(start,start+' import characters39_runtime\n characters39_runtime.prepare_before_initialize(G)\n',1)
    end='def update_hand_colour():\n'
    if end not in source:raise RuntimeError('Unknown legacy character initializer end')
    return source.replace(end," if S.get('revision')==39:characters39_runtime.after_initialize(__import__(__name__),G)\n\n"+end,1)
