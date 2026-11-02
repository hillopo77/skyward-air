"""Release this game's callbacks before the embedded Python interpreter exits.

Uses the installed engine's public Python shutdown delegate. No engine changes.
"""
import json,sys,time,gc
from pathlib import Path
import unreal as u

G=None
S={}

def cleanup():
    global G
    if S.get('cleaned'):return
    S['cleaned']=True
    root=S['root'];modules=[];handles=[];states=[];seen=set();errors=[]
    python_root=Path(__file__).resolve().parent
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        try:owned=Path(filename).resolve().is_relative_to(python_root)
        except (OSError,ValueError):continue
        if not owned or module is sys.modules[__name__]:continue
        modules.append(module)
        for key in ('S','STATE','ACTORS','CLIPS'):
            state=getattr(module,key,None)
            if isinstance(state,dict) and id(state) not in seen:
                seen.add(id(state));states.append(state)
                handle=state.get('handle')
                if handle is not None and all(handle is not h for h in handles):handles.append(handle)
    for handle in handles:
        try:u.unregister_slate_post_tick_callback(handle)
        except Exception as e:errors.append(str(e))
    # Clearing while Unreal's wrapper modules are alive avoids deferring native
    # wrapper destruction and closure cycles to Py_Finalize's torn-down state.
    for state in states:state.clear()
    for key in ('flight39','airside38','journey38'):
        state=getattr(G,key,None)
        if isinstance(state,dict):state.clear()
    for module in modules:
        if hasattr(module,'G'):module.G=None
    G=None
    gc.collect()
    (root/'ArtBible/Lifecycle43.json').write_text(json.dumps(dict(
        status='CLEANUP_CALLED',time=time.time(),callbacks_released=len(handles),
        state_dictionaries_released=len(states),errors=errors,
        scope='Callback/native-wrapper cleanup only. Process exit is verified separately by the launcher.'),indent=2))

def install(game):
    global G
    if S.get('installed'):return
    G=game;S.update(installed=True,root=game.R)
    S['shutdown']=u.register_python_shutdown_callback(cleanup)

