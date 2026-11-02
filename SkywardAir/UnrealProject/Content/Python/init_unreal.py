import unreal as u
cmd=u.SystemLibrary.get_command_line().lower()
if '-game' in cmd and '-airport' in cmd:
 import airport_runtime
 airport_runtime.start()
elif '-game' in cmd and ('-nullrhi' not in cmd or '-force6headless' in cmd or '-force7headless' in cmd or '-force8headless' in cmd or '-stability9headless' in cmd) and '-twintowers' in cmd:
 if '-twintowersstability9' in cmd:
  import stability9
  stability9.start()
  import perf7_visuals
  perf7_visuals.start(stability9)
  if '-stability9photos' in cmd:
   import stability9_photos
   stability9_photos.start(stability9)
  import flight_readyproof5
  flight_readyproof5.start(stability9)
 elif '-twintowersrigid8' in cmd:
  import perf8
  perf8.start()
  import perf7_visuals
  perf7_visuals.start(perf8)
  if '-force8photos' in cmd:
   import rigid8_photos
   rigid8_photos.start(perf8)
  import flight_readyproof5
  flight_readyproof5.start(perf8)
 elif '-twintowersperf7' in cmd:
  import perf7
  perf7.start()
  import perf7_visuals
  perf7_visuals.start(perf7)
  if '-force7readyproof' in cmd:
   import perf7_readyproof
   perf7_readyproof.start(perf7)
  import flight_readyproof5
  flight_readyproof5.start(perf7)
 elif '-twintowersforce6' in cmd:
  import force6
  force6.start()
  import force6_visuals
  force6_visuals.start(force6)
  if '-force6readyproof' in cmd:
   import force6_readyproof
   force6_readyproof.start(force6)
  import flight_readyproof5
  flight_readyproof5.start(force6)
 elif '-twintowersflight5' in cmd:
  import flight5
  flight5.start()
  import flight_readyproof5
  flight_readyproof5.start(flight5)
 elif '-twintowersquality4' in cmd:
  import penetration4
  penetration4.start()
 elif '-twintowersquality3' in cmd:
  import penetration3
  penetration3.start()
 elif '-twintowerspenetration2' in cmd:
  import penetration2
  penetration2.start()
 elif '-twintowersdamage' in cmd:
  import towers_damage
  towers_damage.start()
 else:
  import towers_runtime
  towers_runtime.start()
elif '-game' in cmd and '-nullrhi' not in cmd:
 import skyward_runtime
 skyward_runtime.start()
 if '-skywardbinshots16' in cmd:
  import bin_capture16
  bin_capture16.start(skyward_runtime)
 if '-skywardexteriorshots15' in cmd:
  import exterior_capture15
  exterior_capture15.start(skyward_runtime)

# BEGIN CHARACTER_PACK_OCT30
if '-game' in cmd and '-airport' in cmd:
 import character_pack_runtime
 character_pack_runtime.start()
# END CHARACTER_PACK_OCT30

# BEGIN FRIEND_ACTION_03
if "-game" in cmd and "-airport" in cmd:
 import friend_action03_runtime
 friend_action03_runtime.start()
# END FRIEND_ACTION_03
