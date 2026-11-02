from pathlib import Path
from PIL import Image,ImageDraw
R=Path('outputs/Airport/Airport38/Audits'); names=['05_SecurityEntry','06_WestEntryGap','10_StaffDoor','14_A08Marker','15_A08Cubby','16_A08Ceiling','18_WCSign','20_WCEastGap','21_WCInterior']
im=Image.new('RGB',(1920,1152),'#20363d');d=ImageDraw.Draw(im)
for i,n in enumerate(names):
 p=Image.open(R/'BaselineScreenshots'/(n+'.png'));p.thumbnail((640,360));x=i%3*640;y=i//3*384;im.paste(p,(x,y));d.text((x+5,y+363),n,fill='white')
im.save(R/'01_layout/critical_views.jpg',quality=90)
