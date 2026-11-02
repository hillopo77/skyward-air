"""Map-scoped clean presentation; no image-space sharpening or blur."""
import unreal as u,json,time
from pathlib import Path
SETTINGS=['r.AntiAliasingMethod 2','r.PostProcessAAQuality 6','r.ScreenPercentage 100','r.TemporalAASamples 16','r.TemporalAAFilterSize 1','r.TemporalAACurrentFrameWeight 0.08','r.Tonemapper.Sharpen 0','r.MotionBlurQuality 0','r.DepthOfFieldQuality 0','r.SceneColorFringeQuality 0','r.MaxAnisotropy 16']
def initialize(G):
 for cmd in SETTINGS:u.SystemLibrary.execute_console_command(G.P.STATE['world'],cmd,G.P.STATE['pc'])
 G.P.STATE['pc'].player_camera_manager.set_editor_property('default_fov',82.)
 R=G.R/'ArtBible' if '-AirportRooms24' in G.CMD else Path(__file__).resolve().parents[4]/'Airport/Visual23/ArtBible'
 (R/'RuntimeVisual23.json').write_text(json.dumps(dict(status='READY',settings=SETTINGS,gameplay_fov=82,initialized=time.time()),indent=2),encoding='utf-8')
