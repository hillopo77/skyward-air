"""Actual standalone screenshots, interaction checks and collision movement tests."""
import unreal as u,time,json
SHOTS=[('Exterior07','UE_59_airframe09.png'),('Profile08','UE_60_profile09.png'),('FrontOverview07','UE_61_front09.png'),('Wing07','UE_62_wing09.png'),('Business07','UE_63_business09.png'),('SeatDetail09','UE_64_premium_detail09.png'),('Economy07','UE_65_economy09.png'),('Galley07','UE_66_mid_galley09.png'),('IFE07','UE_67_ife09.png'),('Door07','UE_68_door09.png'),('CockpitDoor07','UE_69_cockpit_entry09.png'),('Flightdeck07','UE_70_flightdeck09.png'),('Carpet07','UE_71_carpet09.png')]
TESTS=[
 ('business open centre route',(0,-280,162),(0,-1,0),1.0,1,(-520,-440)),
 ('left route past main mid galley',(-140,-550,162),(0,-1,0),.75,1,(-710,-650)),
 ('right route past main mid galley',(140,-550,162),(0,-1,0),.75,1,(-710,-650)),
 ('left gathered class curtain opening',(-127,-710,162),(0,-1,0),.85,1,(-875,-830)),
 ('right gathered class curtain opening',(127,-710,162),(0,-1,0),.85,1,(-875,-830)),
 ('left economy aisle',(-110,-830,162),(0,-1,0),3.3,1,(-1490,-1400)),
 ('right economy aisle',(110,-830,162),(0,-1,0),3.3,1,(-1490,-1400)),
 ('mid galley cabinet blocks player',(0,-550,162),(0,-1,0),1.0,1,(-610,-580)),
 ('class centre partition blocks player',(0,-710,162),(0,-1,0),.8,1,(-738,-728)),
 # New inner liner is x=231.7cm; the 18cm pawn sphere stops near x=213.7cm.
 ('fitted shell side blocks player',(110,-890,162),(1,0,0),1.4,0,(209,222)),
 ('rear crew utility access',(0,-2135,162),(0,-1,0),.6,1,(-2275,-2215)),
 ('left extended economy aisle',(-110,-1540,162),(0,-1,0),2.6,1,(-2075,-1990)),
 ('right extended economy aisle',(110,-1540,162),(0,-1,0),2.6,1,(-2075,-1990)),
 ('aft service rear bulkhead blocks player',(110,-2350,162),(0,-1,0),1,1,(-2390,-2350)),
 ('front central vestibule portal',(0,-300,162),(0,1,0),.75,1,(-190,-140))]
SHOTS.extend([('PilotEye09','UE_72_pilot_eye09.png'),('Lavatory','UE_73_lavatory09.png')])
class Validator:
 def __init__(self,r):
  self.r=r;self.v={'phase':'settle','after':time.monotonic()+25,'index':0};self.report={'revision':'09','status':'RUNNING','captures':[],'interactions':[],'navigation':[]};self.save()
 def save(self):(self.r.ROOT/'ArtBible/EngineValidation.json').write_text(json.dumps(self.report,indent=2))
 def check(self,name,passed,**details):self.report['interactions'].append({'test':name,'passed':bool(passed),**details});self.save()
 def fail(self,error):self.report.update(status='FAILED',error=error);self.finish()
 def finish(self):
  self.save();s=self.r.STATE;u.unregister_slate_post_tick_callback(s['handle']);u.SystemLibrary.quit_game(s['world'],s['pc'],u.QuitPreference.QUIT,False)
 def tick(self,dt):
  r=self.r;s=r.STATE;v=self.v;now=time.monotonic()
  if now-s['began']>500:raise RuntimeError('Validation timeout')
  if now<v['after']:return
  w,pc,p=s['world'],s['pc'],s['pawn'];phase=v['phase']
  if phase=='settle':
   self.check('E key imports and polling API is available','E' in r.KEY.export_text() and hasattr(pc,'was_input_key_just_pressed'),key=r.KEY.export_text())
   for expected in (0,1,2,-1):self.check('V exterior review cycle '+str(expected),r.toggle_review()==expected)
   v.update(phase='shot',index=0)
  elif phase=='shot':
   cam,file=SHOTS[v['index']];camera=next(a for a in u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor) if any(str(t)=='SkywardCamera:CAM_Plane_'+cam for t in a.tags))
   pc.set_view_target_with_blend(camera,0);v.update(phase='capture',after=now+3)
  elif phase=='capture':
   cam,file=SHOTS[v['index']];v['fresh']=time.time();u.SystemLibrary.execute_console_command(w,'Shot filename="'+str(r.ROOT/'Screenshots'/file).replace('\\','/')+'" -nosuffix',pc);v.update(phase='capture_wait',after=now+1)
  elif phase=='capture_wait':
   cam,file=SHOTS[v['index']];path=r.ROOT/'Screenshots'/file
   if not path.exists() or path.stat().st_mtime<v['fresh']:
    if now>v['after']+20:raise RuntimeError('Screenshot did not arrive: '+file)
    return
   self.report['captures'].append({'camera':cam,'file':file,'bytes':path.stat().st_size,'method':'actual standalone viewport Shot with settled temporal AA'});self.save();v['index']+=1
   v.update(phase='shot' if v['index']<len(SHOTS) else 'door_closed',after=now+.3)
  elif phase=='door_closed':
   pc.set_view_target_with_blend(p,0);r.reposition((0,-120,162));r.point_at([0,.055,1.15]);v.update(phase='closed_move',until=now+.9)
  elif phase=='closed_move':
   p.add_movement_input(u.Vector(0,1,0),1)
   if now>=v['until']:
    self.check('closed cockpit door blocks entry',p.get_actor_location().y<0,end_y=p.get_actor_location().y)
    r.reposition((0,-105,162));r.point_at([0,.055,1.15]);action=r.use_nearest();self.check('same E action opens cockpit door',action=='door');v.update(phase='door_open',after=now+1.2)
  elif phase=='door_open':
   self.check('cockpit door reaches open position',abs(s['door'].get_actor_rotation().yaw+86)<.2)
   r.reposition((0,-65,162));v.update(phase='open_move',until=now+.8)
  elif phase=='open_move':
   p.add_movement_input(u.Vector(0,1,0),1)
   if now>=v['until']:
    self.check('open cockpit door permits entry',p.get_actor_location().y>50,end_y=p.get_actor_location().y);v.update(phase='seat',index=0,after=now+.2)
  elif phase=='seat':
   seats=[a for a in s['items'] if a['kind']=='seat'];item=seats[v['index']];target=r.vector(item['point']);r.reposition((target.x,target.y-85,162));r.point_at(item['point']);before=p.get_actor_location();action=r.use_nearest()
   self.check('enter '+item['actor'],action=='seat' and s['seated'] and s['seated']['actor']==item['actor'] and not p.get_actor_enable_collision() and abs(p.get_actor_location().z-item['location'][2]*100)<1)
   r.use_nearest();self.check('stand from '+item['actor'],not s['seated'] and p.get_actor_enable_collision() and (p.get_actor_location()-before).length()<1);v['index']+=1
   if v['index']>=len(seats):v.update(phase='nav_start',index=0)
  elif phase=='nav_start':
   name,start,d,duration,axis,limits=TESTS[v['index']];r.reposition(start);actual=p.get_actor_location();self.report['navigation'].append({'test':'reposition '+name,'passed':(actual-u.Vector(*start)).length()<1});v.update(phase='nav_move',until=now+duration)
  elif phase=='nav_move':
   name,start,d,duration,axis,limits=TESTS[v['index']];p.add_movement_input(u.Vector(*d),1)
   if now>=v['until']:
    loc=p.get_actor_location();pos=[loc.x,loc.y,loc.z];self.report['navigation'].append({'test':name,'end_cm':pos,'accepted_range_cm':limits,'passed':limits[0]<pos[axis]<limits[1]});self.save();v['index']+=1;v.update(phase='nav_start' if v['index']<len(TESTS) else 'finish',after=now+.2)
  elif phase=='finish':
   self.report['status']='SUCCESS' if all(x['passed'] for x in self.report['interactions']+self.report['navigation']) else 'FAILED';self.finish()
