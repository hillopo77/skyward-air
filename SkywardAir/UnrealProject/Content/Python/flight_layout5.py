"""Deterministic whole-building facade placement; shared by builder and runtime."""
import math
P=101.6;FRONT=3152.92;MECHANICAL={7,8,41,42,75,76,108,109}
def rotate(x,y,side):
 return ((x,y),(y,-x),(-x,-y),(-y,x))[side]
def layout(spec,assets):
 tower=spec['tower'];cx=spec['centre'][0]*100;cy=-spec['centre'][1]*100;pitch=spec['floor_pitch']*100;counts={}
 def row(tag,asset,orientation,x,y,z,kind,**extra):
  i=counts.get(tag,0);counts[tag]=i+1;xx,yy=rotate(x,y,orientation);return dict(tag=tag,index=i,asset=asset,tower=tower,kind=kind,location=[cx+xx,cy+yy,z],yaw=-orientation*90,scale=[1,1,1],**extra)
 for side in range(4):
  for floor in range(104):
   for col in range(59):
    variant=(col*5+floor*3)%6;mechanical=(floor+7) in MECHANICAL
    for segment in range(2):
     aid=f'SM_Q3_{tower}_Tear{variant}_{segment}';tag=f'{"Mechanical" if mechanical else "Normal"}_{variant}_{segment}';yield row(tag,aid,side,(col-29)*P,FRONT,2280+floor*pitch,'facade',side=side,floor=floor,column=col,segment=segment,bent_asset=aid+'_Bent')
  for floor in range(104):
   aid=assets['corners'][tower];yield row('Corner',aid,side,0,0,2280+floor*pitch,'corner',side=side,floor=floor,bent_asset=aid)
  for bay in range(-9,10):
   door=int(abs(bay)<=1)
   for segment in range(3):
    aid=assets['base_cells'][f'{door}_{segment}'];yield row(f'Base_{door}_{segment}',aid,side,bay*3*P,3144.92,0,'base',side=side,floor=-1,bent_asset=aid)
 step=6339.84/7;scale=step/980
 for ix in range(7):
  for iy in range(7):
   q=row('Roof','SM_TT2_Deck',0,(ix-3)*step,(iy-3)*step,spec['height']*100-10,'roof',side=4,floor=104,bent_asset='SM_Q3_Deck_Torn'+str((ix+iy)%3));q['scale']=[scale,scale,1];yield q
