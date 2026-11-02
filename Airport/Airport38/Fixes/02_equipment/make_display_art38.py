"""Original legible functional UI, not borrowed media or generated screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;T=H/'DisplayArt';T.mkdir(exist_ok=True)
def f(s,b=False):return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if b else 'C:/Windows/Fonts/segoeui.ttf',s)
specs={
 'Checkin':('CHECK IN','SA107 / AZURE BAY',[('1','Join the queue'),('2','Present your travel document'),('3','Collect your boarding pass')],'GATE A07 / ECONOMY 03E'),
 'CheckedIn':('YOU ARE CHECKED IN','SA107 / AZURE BAY',[('PASS','Gate A07 / Economy 03E'),('BAG','Bag drop is optional'),('NEXT','Security screening')],'KEEP YOUR BOARDING PASS READY'),
 'A07':('GATE A07','SA107 / AZURE BAY',[('FLIGHT','Skyward Air SA107'),('CABIN','Economy / Business'),('NEXT','Scan your pass at the desk')],'BOARDING REQUIRES SECURITY CLEARANCE'),
 'Boarding':('BOARDING OPEN','GATE A07 / SA107',[('PASS','Boarding pass accepted'),('WALK','Follow the enclosed jetbridge'),('SEAT','Economy 03E / right aisle')],'WELCOME ABOARD SKYWARD AIR'),
 'A08':('GATE A08','FLIGHT INFORMATION',[('STATUS','No active boarding'),('SA107','Boards at Gate A07'),('HELP','Use the information desk')],'PLEASE CHECK YOUR DEPARTURE GATE'),
 'Scanner':('BAGGAGE SCREENING','CONVEYOR READY',[('1','Place cabin bag on the belt'),('2','Press the green START control'),('3','Collect at the receiving rollers')],'EMERGENCY STOP / RED MUSHROOM'),
 'Scanned':('SCREENING COMPLETE','PROPERTY READY TO COLLECT',[('BAG','Collect from receiving rollers'),('NEXT','Walk through the detector'),('GATE','Continue to A07')],'SCREENING COMPLETE FOR THIS BAG'),
 'Stopped':('CONVEYOR STOPPED','EMERGENCY STOP ACTIVE',[('STOP','Belt motor is disabled'),('CHECK','Keep the rollers clear'),('RESET','Press the red control to restart')],'PROPERTY REMAINS PHYSICALLY SUPPORTED'),
 'ScreeningControl':('SCREENING CONTROL','STAFF OPERATIONS',[('LANE 1','Property screening'),('LANE 2','Property screening'),('SAFETY','Check belt and tunnel before use')],'AUTHORISED STAFF / OPERATIONS'),
 'Operations':('AIRPORT OPERATIONS','TERMINAL SERVICES',[('CHECK','Baggage receiving bay'),('STAFF','Security and flight support'),('FLIGHT','SA107 / Azure Bay / Gate A07')],'AUTHORISED STAFF / OPERATIONS'),
 'Departures':('DEPARTURES','SKYWARD AIR',[('SA107','Azure Bay / Gate A07'),('A07','Check in, screen, then board'),('A08','Flight information only')],'FOLLOW THE GOLD ROUTE TO YOUR GATE')}
for key,(title,sub,rows,footer) in specs.items():
    im=Image.new('RGB',(1024,640),'#102C35');d=ImageDraw.Draw(im)
    d.rounded_rectangle((18,18,1006,622),radius=24,outline='#447B7A',width=3)
    d.text((48,35),'SKYWARD AIR',font=f(27,True),fill='#A3C3BC')
    d.text((48,86),title,font=f(56 if len(title)<22 else 48,True),fill='#F1D69C')
    d.text((50,166),sub,font=f(30),fill='#E5EBE3')
    d.line((48,220,976,220),fill='#4C7776',width=2)
    for j,(tag,body) in enumerate(rows):
        y=258+j*92;d.rounded_rectangle((42,y-8,982,y+65),radius=9,fill='#1C414B')
        d.text((60,y),tag,font=f(29,True),fill='#A1C8B2');d.text((210,y),body,font=f(29),fill='#F1E9D6')
    d.text((49,568),footer,font=f(24,True),fill='#AECCC1')
    im.save(T/('T_AP_UI38_'+key+'.png'))
print('DISPLAY_ART38',len(specs))
