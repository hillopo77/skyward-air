"""Fixes70: small runtime repairs from the player's Pass69 feedback (Airport38 Pass70).

  gate agent   The A07 boarding receptionist ('CH12 Gate pilot') is drawn by the character pack
               (another tool's CharacterPack_Oct30) with its 'Red_Suit' model, whose 1 Nov model
               update broke the skinning: a burgundy sheet of stretched polygons ran from the desk
               across the gate. The pack's files are left alone; once it has installed, this NPC
               alone is re-dressed in the pack's working 'Coat_Character' model and that model's
               own animation set (the player's F7 avatar choices are not touched).
"""
import unreal as u

S = dict(done=False, failed=False)
AGENT = 'CH12 Gate pilot'
BROKEN, GOOD = 'Red_Suit', 'Coat_Character'


def tick(airport, dt):
    if S['done'] or S['failed']:
        return
    try:
        import character_pack_runtime as pack
        if not pack.S.get('installed'):
            return
        S['done'] = True
        npc = pack.S['npcs'].get(AGENT)
        good = next((p for p in pack.S.get('profiles', []) if p['name'] == GOOD), None)
        if not npc or not good or npc['profile']['name'] != BROKEN:
            return
        npc['profile'] = good
        npc['actor'].skeletal_mesh_component.set_skeletal_mesh_asset(good['mesh_obj']) \
            if hasattr(npc['actor'].skeletal_mesh_component, 'set_skeletal_mesh_asset') \
            else npc['actor'].skeletal_mesh_component.set_skeletal_mesh(good['mesh_obj'], True)
        npc['last_clip'] = None                                         # the pack replays the idle on its next tick
        u.log('FIXES70: gate agent re-dressed as ' + GOOD)
    except Exception:
        S['failed'] = True
        import traceback
        u.log_error('Fixes70: ' + traceback.format_exc())
