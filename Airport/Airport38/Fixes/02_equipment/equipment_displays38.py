"""Install after journey38: real default UI, state changes and scanner routing."""
import time
S={}
def install(G):
    if S.get('installed'):return
    S.update(installed=True,base_screen=G.screen,base_physics=G.physics,powered={},last=0.,applied={})
    roles=G.D['repair38']['equipment']['screen_roles38'];u=G.u
    def show(actor,key):
        if not G.valid(actor):return
        n=actor.get_actor_label()
        if n.startswith('Security belt '):actor=G.S['actors'].get(n.replace('Security belt ','X-ray scanner '));n=actor.get_actor_label() if G.valid(actor) else n
        if not G.valid(actor):return
        role=roles.get(n,'Checkin')
        key={'Gate':'A07'}.get(key,key)
        if role=='A08' and key in ('A07','Boarding'):key='A08'
        if key not in {'Checkin','CheckedIn','A07','A08','Boarding','Scanner','Scanned','Stopped','Operations','ScreeningControl','Departures','Arrivals'}:return S['base_screen'](actor,key)
        m=u.load_asset('/Game/Airport38/EquipmentScreens/MI_AP_UI38_'+key)
        if not m:return S['base_screen'](actor,key)
        c=actor.static_mesh_component;count=0
        for j,slot in enumerate(c.static_mesh.static_materials):
            if str(slot.material_slot_name).startswith('MI_AP_Screen'):c.set_material(j,m);count+=1
        if count:S['applied'][n]=key
    G.screen=show
    # Pass47: Arrivals is a real role now; the reclaim board used to borrow
    # Departures and told arriving passengers about departures.
    for n,key in roles.items():show(G.S['actors'].get(n),key)
    def physics(dt):
        out=S['base_physics'](dt)
        if time.monotonic()-S['last']<.10:return out
        S['last']=time.monotonic()
        import airport_journey38 as J
        for n,enabled in J.S.get('powered',{}).items():
            if not n.startswith('Security belt '):continue
            old=S['powered'].get(n,True)
            if old!=enabled:show(G.S['actors'].get(n),'Scanner' if enabled else 'Stopped')
            S['powered'][n]=enabled
        return out
    G.physics=physics
