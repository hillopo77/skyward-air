def initialize(game):
 game.event('Spacious check-in29 ready',queues=1,counters=2,queue_width_m=1.9)
 if '-CheckinPreview29' in game.CMD and '-AirportStartAboard' not in game.CMD:
  import unreal as u
  game.P.STATE['pawn'].set_actor_location(game.v([-41.9,-13,1.62]),False,True);game.P.STATE['pc'].set_control_rotation(u.MathLibrary.find_look_at_rotation(game.v([-41.9,-13,1.62]),game.v([-33.6,-12.8,1.48])))
 if '-Checkin29QA' in game.CMD:
  import checkin29_qa;checkin29_qa.start(game)
