"""Editable floor-plan proposal. Explicitly a plan, not a game screenshot."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1]
zones=[
 dict(id='checkin',title='01 / CHECK-IN HALL',rect=[-49,-25,-18,-8],fill='#eee4cd',ceiling_m=3.8,description='An enclosed public room: staffed desks, bag-drop recesses, queue lanes and a clear entrance sightline. Counters sit against a service wall; baggage continues behind it.'),
 dict(id='security',title='02 / SECURITY ROOM',rect=[-49,-27,-8,2],fill='#b9d7cb',ceiling_m=3.5,description='Full-height boundaries. Controlled south entry, two screening lanes, separate preparation and recomposure areas, staff station and a controlled north exit. Gates are beyond the exit, not beside the scanners.'),
 dict(id='cafe',title='CAFÉ / TRAVEL SHOP',rect=[-49,-35,4,18],fill='#e8cab6',ceiling_m='3.15 lower / gallery above',description='A furnished destination off the airside route, with its own frontage and doorway. Keep the existing stair and mezzanine inside this area.'),
 dict(id='concourse',title='03 / AIRSIDE CONCOURSE',rect=[-35,-25,2,18],fill='#d9e4ec',ceiling_m=4.0,description='A short connecting space with clear signs at decisions. Café, toilets and separate gate lounges open off it. Its furnishings stay in edge recesses, outside the walking route.'),
 dict(id='gate07',title='04 / GATE A07 LOUNGE',rect=[-25,-14,-3,7.5],fill='#b9c8ec',ceiling_m=3.6,description='A bounded waiting room with a wide concourse portal, seating banks facing the boarding desk, large A07 identity, flight display, charging ledges and a boarding-only exit to the existing jetbridge.'),
 dict(id='gate08',title='GATE A08 LOUNGE',rect=[-25,-14,9,18],fill='#c6c1e3',ceiling_m=3.6,description='A separate adjacent waiting room: its own entry, desk, display and seating. A wall separates the A07/A08 seating areas so each gate reads immediately.'),
 dict(id='amenitylobby',title='WC LOBBY',rect=[-27,-25,-8,2],fill='#e4e3da',ceiling_m=3.0,description='A 2 m wide airside side passage connects the concourse to the lavatories. A solid wall keeps it outside the security room.'),
 dict(id='amenities',title='WC / ASSISTANCE',rect=[-25,-14,-8,-3],fill='#d8d4ca',ceiling_m=2.8,description='Enclosed lavatories and assistance rooms with doors off a short lobby. No lavatory door opens straight into a boarding queue.'),
 dict(id='arrivals',title='ARRIVALS / RECLAIM',rect=[-25,-14,-22,-9.5],fill='#d5d7ca',ceiling_m=3.6,description='A separate landside reclaim room. Its exit joins the public return passage, without crossing the security or gate queues.'),
 dict(id='publicreturn',title='PUBLIC ARRIVALS RETURN / TROLLEYS',rect=[-49,-25,-22,-18],fill='#e3e1d9',ceiling_m=3.2,description='A separate public passage along the forecourt edge. Reclaim passengers leave through their own public exit; trolley bays sit outside the through route.')]
doors=[dict(zone='checkin',point=[-49,-12.5],width_m=2.7,kind='public entrance'),dict(zone='security',point=[-41,-8],width_m=2.4,kind='controlled preparation entry'),dict(zone='security',point=[-33,2],width_m=2.4,kind='controlled screened exit'),dict(zone='cafe',point=[-35,7],width_m=2.4,kind='cafe frontage portal'),dict(zone='gate07',point=[-25,4],width_m=2.6,kind='lounge entry'),dict(zone='gate08',point=[-25,12.5],width_m=2.6,kind='lounge entry'),dict(zone='gate07',point=[-14,.675],width_m=2.7,kind='validated boarding exit'),dict(zone='publicreturn',point=[-49,-20],width_m=2.4,kind='separate public arrivals exit'),dict(zone='arrivals',point=[-25,-20],width_m=2.4,kind='reclaim exit to public return'),dict(zone='amenitylobby',point=[-26,2],width_m=1.8,kind='airside amenities passage'),dict(zone='amenities',point=[-25,-4.5],width_m=1.4,kind='WC lobby entry')]
data=dict(status='PLANNED_NOT_BUILT',units='metres',footprint=[-49,-14,-22,18],zones=zones,doors=doors,principles=['Physical room boundaries and meaningful thresholds','Distinct ceilings and floor fields; simple colors alone are insufficient','A07 and A08 each have a bounded lounge','Keep parked aircraft and jetbridge connection','Recheck circulation after partition construction'],proposed_route=[[-51,-12.5],[-44,-12.5],[-41,-8],[-41,-3.2],[-41,1],[-33,1],[-33,3],[-30,4],[-25,4],[-19,4],[-18,-2],[-14,.675],[-2,.675]])
(R/'Planning/Zoning23.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
sx=lambda x:100+(x+49)*16
sy=lambda y:140+(18-y)*16
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 900"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#d36e2d"/></marker></defs><rect width="1300" height="900" fill="#f4f3ef"/><g font-family="Segoe UI,Arial" fill="#172c3b"><text x="60" y="48" font-size="26" font-weight="700">A sequence of rooms, not one open hall</text><text x="60" y="78" font-size="15">PROPOSED ZONING · Existing 35 × 40 m footprint · Partition construction still to follow</text>']
for z in zones:
 x0,x1,y0,y1=z['rect'];x=sx(x0);y=sy(y1);w=(x1-x0)*16;h=(y1-y0)*16
 label=(f'<text transform="translate({x+w/2+4} {y+h/2}) rotate(-90)" text-anchor="middle" font-size="11">{html.escape(z["title"])}</text>' if w<80 else f'<text x="{x+12}" y="{y+25}" font-size="{12 if w<190 else 14}" font-weight="700">{html.escape(z["title"])}</text>')
 parts.append(f'<g id="{z["id"]}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{z["fill"]}" stroke="#334957" stroke-width="5"/>{label}</g>')
# The same room edges have genuine portal breaks in the diagram.
for d in doors:
 x,y=map(float,[sx(d['point'][0]),sy(d['point'][1])]);h=d['width_m']*8
 vertical=d['point'][0] in [-49,-35,-25,-14]
 parts.append(f'<path d="M{x},{y-h if vertical else y} L{x},{y+h}" stroke="#f4f3ef" stroke-width="9"/>' if vertical else f'<path d="M{x-h},{y} L{x+h},{y}" stroke="#f4f3ef" stroke-width="9"/>')
 # Door jamb marks, wider than a symbolic line so the threshold reads.
 parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#3b7c78"/>')
for x in [-43,-38,-33]:
 parts.append(f'<rect x="{sx(x)-18}" y="{sy(-12)-9}" width="36" height="18" rx="4" fill="#657e92"/><text x="{sx(x)}" y="{sy(-12)+26}" text-anchor="middle" font-size="10">desk</text>')
for x in [-41,-33]:parts.append(f'<rect x="{sx(x)-12}" y="{sy(-3.2)-12}" width="24" height="24" rx="5" fill="#557f73"/><text x="{sx(x)}" y="{sy(-3.2)+29}" text-anchor="middle" font-size="10">screen</text>')
for y0,y1 in [(0,5),(10,15)]:
 for y in [y0,y1]:
  for x in [-22,-18]:parts.append(f'<rect x="{sx(x)-19}" y="{sy(y)-9}" width="38" height="18" rx="5" fill="#506ca4"/>')
parts.append(f'<rect x="{sx(-14)}" y="{sy(2.05)}" width="192" height="44" fill="#c6d7e0" stroke="#334957" stroke-width="4"/><text x="{sx(-14)+13}" y="{sy(2.05)+27}" font-size="13">JETBRIDGE → AIRCRAFT</text>')
points=' '.join(f'{sx(x)},{sy(y)}' for x,y in data['proposed_route'])
parts.append(f'<polyline points="{points}" fill="none" stroke="#fff9eb" stroke-width="10" stroke-linejoin="round"/><polyline points="{points}" fill="none" stroke="#d36e2d" stroke-width="5" stroke-linejoin="round" marker-end="url(#arrow)"/>')
parts.append('<g font-size="14"><text x="870" y="210" font-weight="700">ENCLOSURE RULES</text><text x="870" y="245">Security: continuous solid boundary</text><text x="870" y="273">Gate lounges: walls + framed glazing</text><text x="870" y="301">Doors occur at deliberate thresholds</text><text x="870" y="329">Ceilings: 3.5–4 m in the main rooms</text><text x="870" y="377" font-weight="700">KEEP THE ROUTE LEGIBLE</text><text x="870" y="412">Prepare → screen → collect → depart</text><text x="870" y="440">One distinct flight identity per lounge</text><text x="870" y="468">Arrivals stays outside screened areas</text><text x="870" y="516" font-weight="700">NOT YET IMPLEMENTED</text><text x="870" y="551">This sheet is the construction plan.</text><text x="870" y="579">Visual23 keeps the tested existing route.</text><text x="60" y="838">Orange = outbound passenger journey · Green dots = planned thresholds · North is up</text><text x="60" y="866">Planning dimensions are gameplay targets; this is not an architectural compliance drawing.</text></g></g></svg>')
(R/'Planning/RoomPlan23.svg').write_text(''.join(parts),encoding='utf-8')
print('Zoning23: 10 defined zones, 11 deliberate thresholds; proposal only')
