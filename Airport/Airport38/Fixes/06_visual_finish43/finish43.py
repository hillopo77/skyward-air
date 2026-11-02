"""Terminal finish43: fitted public wall cassettes and true baggage service portals.

Apply to the current source Context only. No master I/O, launch, baseline reset,
plane, furniture, interactions or collision mutations. Texture scale follows the
existing exporter's metre-projected UV0; native_finish43 binds the same images.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = 'terminal_finish43_v1'
PREFIX = 'P43T'
OWNED = ('SM_AP_TerminalWallFinish43', 'SM_AP_BaggageBackdrop43')
STRUCTURAL = ('SM_AP_Walls38', 'SM_AP_Floors38', 'SM_AP_Ceilings38')
# Filename, sRGB colour, roughness, metallic, tile size in source metres.
MATERIALS = {
 'Plaster': ('Plaster43.png', 'E3DDCF', .82, 0, 4.),
 'PlasterWarm': ('PlasterWarm43.png', 'DDD2BF', .80, 0, 4.),
 'Oak': ('Oak43.png', 'BC976D', .60, 0, 2.),
 'Floor': ('Floor43.png', 'D0CABC', .63, 0, 2.),
 'Carpet': ('Carpet43.png', '526D7E', .94, 0, 2.),
 'WC': ('WC43.png', 'CACEC4', .68, 0, 2.),
 'Ceiling': ('Ceiling43.png', 'D3D5CC', .90, 0, 4.),
 'Dado': (None, '6E8287', .73, 0, 1.),
 'Reveal': (None, '989B91', .83, 0, 1.),
 'Bronze': (None, 'A88C62', .45, .36, 1.),
 'Metal': (None, '889899', .43, .38, 1.),
 'Ink': (None, '304A57', .74, 0, 1.),
 'Text': (None, 'F1E8D4', .76, 0, 1.),
}

def _materials(a):
 import bpy
 for suffix,(file,colour,rough,metal,tile) in MATERIALS.items():
  short=PREFIX+suffix;name='MI_AP_'+short
  m=bpy.data.materials.get(name) or a.mat(short,colour,rough,metal)
  a.MATS[short]=m
  if not file: continue
  path=HERE/'Textures'/file
  assert path.exists(), ('Generate the authored finish textures first',str(path))
  m.use_nodes=True;nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
  for ob in list(nt.nodes):
   if ob.name.startswith('Finish43 '):nt.nodes.remove(ob)
  im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name='sRGB';im.alpha_mode='CHANNEL_PACKED'
  uv=nt.nodes.new('ShaderNodeTexCoord');uv.name='Finish43 metre UV';uv.location=(-650,0)
  scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.name='Finish43 physical tile scale';scale.inputs['Scale'].default_value=1/tile;scale.location=(-430,0)
  tex=nt.nodes.new('ShaderNodeTexImage');tex.name='Finish43 authored colour and roughness';tex.image=im;tex.extension='REPEAT';tex.interpolation='Linear';tex.location=(-210,0)
  nt.links.new(uv.outputs['UV'],scale.inputs[0]);nt.links.new(scale.outputs['Vector'],tex.inputs['Vector']);nt.links.new(tex.outputs['Color'],p.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],p.inputs['Roughness'])
  m['finish43_texture']=file;m['finish43_tile_metres']=tile;m['finish43_no_normal_noise']=True

def _uv(ob):
 """Match airport_export24's dominant-face metre projection exactly."""
 if ob.type!='MESH':return
 me=ob.data;layer=me.uv_layers.active or me.uv_layers.new(name='UV0')
 for face in me.polygons:
  drop=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=drop]
  for j in face.loop_indices:
   co=ob.matrix_world@me.vertices[me.loops[j].vertex_index].co
   layer.data[j].uv=(co[axes[0]],co[axes[1]])
 ob['authored_uv']=True

def _register(ctx,aid,collision):
 import bpy
 c=bpy.data.collections.get(aid)
 assert c,('Missing saved finish collection',aid)
 ctx.a.ASSETS[aid]=dict(collection=c,collision=collision)
 return c

def _line(a,name,s,lo,hi,z0,z1,d0,d1,material):
 if hi-lo<.025 or z1-z0<.012:return None
 k=s['k'];p=((lo+hi)/2,k+(d0+d1)/2,(z0+z1)/2) if s['axis']=='x' else (k+(d0+d1)/2,(lo+hi)/2,(z0+z1)/2)
 size=(hi-lo,abs(d1-d0),z1-z0) if s['axis']=='x' else (abs(d1-d0),hi-lo,z1-z0)
 ob=a.box(name,p,size,PREFIX+material,min(.008,(z1-z0)/4,abs(d1-d0)/4))
 ob['finish43']=True;ob['construction']='Fitted shallow cassette, backed by existing solid shell; real return depth'
 _uv(ob)
 return ob

def _exterior_glazed(s):
 ids=s['members'];ax=s['axis'];k=s['k']
 return s['exterior'] and (
  ('entrancefoyer' in ids and ax=='y' and k==-49) or
  ('cafe' in ids and (k==-49 if ax=='y' else k==34)) or
  ('gate08' in ids and (k==-24 if ax=='y' else k==34)) or
  ('gate07' in ids and (k==-14 if ax=='y' else k==10)) or
  ('arrivals' in ids and ax=='y' and k==-14))

def _cladding(ctx,segments,core):
 a,D=ctx.a,ctx.D
 col=ctx.new_collection('TerminalWallFinish43','none');panels=0;surfaces=[]
 public={z['id'] for z in D['zones'] if z['id'] not in {'operations','baggageservice'}}
 for s in segments:
  opaque,_=core.wall_panels(D,s)
  faces=[(-1,s.get('negative')),(1,s.get('positive'))]
  if s['exterior']:
   if s.get('negative') in public and not s.get('positive'):faces.append((1,'facade'))
   if s.get('positive') in public and not s.get('negative'):faces.append((-1,'facade'))
  for sign,zone in faces:
   if zone not in public and zone!='facade':continue
   baggage=s['axis']=='y' and s['k']==-26 and zone=='checkin'
   for lo,hi,z0,z1 in opaque:
    # Full clear feed aperture and every circulation opening are excluded by
    # the architecture's authoritative opaque occupancy rectangles.
    if _exterior_glazed(s) and z0>=1.005-1e-6:continue
    if baggage:continue
    z0=max(z0,1.075);z1=min(z1,s['H']-.10)
    if z1-z0<.24 or hi-lo<.42:continue
    count=max(1,math.ceil((hi-lo)/2.45));width=(hi-lo)/count
    # Panels have a 1mm backing clearance from masonry, no shared visible face.
    d0,d1=sorted((sign*.091,sign*.105))
    _line(a,'43 recessed plaster mounting bed '+zone,s,lo+.012,hi-.012,z0,z1,d0,d1,'Reveal')
    for i in range(count):
     l=lo+width*i+.009;h=lo+width*(i+1)-.009
     material='PlasterWarm' if zone in {'entrancefoyer','cafe','cafefoyer'} else 'Plaster'
     # Sparse timber pilasters establish hospitality zones; no thin-slat field.
     if zone=='gate08' and i%4==2 and h-l>1.15:material='Oak'
     p0,p1=sorted((sign*.1055,sign*.132))
     ob=_line(a,'43 broad fitted '+zone+' wall panel %02d'%i,s,l,h,z0+.008,z1-.008,p0,p1,material)
     if ob:panels+=1
    # Solid cap return follows the top of the wall, not a floating accent line.
    c0,c1=sorted((sign*.106,sign*.141))
    _line(a,'43 fitted upper panel return '+zone,s,lo+.012,hi-.012,z1-.012,z1+.018,c0,c1,'PlasterWarm')
    surfaces.append(dict(zone=zone,axis=s['axis'],k=s['k'],side=sign,interval=[lo,hi],height=[z0,z1],panel_count=count))
 a.ACTIVE=None
 return dict(panels=panels,surfaces=surfaces,maximum_projection_from_wall_face_m=.051,
             cassette_thickness_m=.0265,shadow_joint_m=.018,largest_panel_width_m=2.45)

def _service_identity(ctx):
 """Raised, physically bearing luggage relief and bay text on each crown."""
 import bpy
 a,D=ctx.a,ctx.D;col=bpy.data.collections['SM_AP_BaggageBackdrop43']
 a.ACTIVE=col;records=[]
 openings=sorted([o for o in D.get('service_openings38',[]) if o['axis']=='y' and o['k']==-26],key=lambda o:-o['centre'])
 for index,o in enumerate(openings,1):
  label='BAY %02d'%index;prefix='43 mounted service identity %02d '%index
  identity=dict(bay=label,centre=o['centre'],front_plane_x=o['k']-.160,glyph_relief_m=.010,
                text_size_m=.26,text_extrusion_m=.006,mount_penetration_m=.001,parts=5)
  old=[ob for ob in col.objects if ob.name.startswith(prefix)]
  if old:
   assert len(old)==5,('Incomplete saved service identity',index,len(old))
   records.append(identity);continue
  s=dict(axis='y',k=o['k']);c=o['centre'];zc=(o['z1']+.20+2.72)/2;glyph=c+.55
  # The crown's front face is x=k-.160. Relief backs penetrate it by1mm;
  # all exposed faces sit8–10mm in front, avoiding a coplanar graphic overlay.
  for name,lo,hi,z0,z1 in [
   ('luggage body',glyph-.145,glyph+.145,zc-.11,zc+.09),
   ('luggage handle left',glyph-.085,glyph-.055,zc+.085,zc+.157),
   ('luggage handle right',glyph+.055,glyph+.085,zc+.085,zc+.157),
   ('luggage handle crown',glyph-.085,glyph+.085,zc+.139,zc+.169)]:
   ob=_line(a,prefix+name,s,lo,hi,z0,z1,-.170,-.159,'Text')
   ob['construction']='Raised solid luggage pictogram bearing1mm into service crown'
  # Editable text is evaluated to actual mesh by the established FBX exporter.
  # Its6mm extrusion also intersects the crown by1mm, rather than hovering.
  font=a.font(label,(o['k']-.162,c-.23,zc-.012),.26,PREFIX+'Text',
              (math.pi/2,0,3*math.pi/2),name=prefix+label)
  font.data.extrude=.003;font.data.bevel_depth=.0004;font.data.bevel_resolution=2
  font['construction']='Raised fitted bay lettering; source-editable font, actual mesh export'
  font['finish43']=True
  records.append(identity)
 a.ACTIVE=None
 return records

def _baggage(ctx,segments,core):
 a,D=ctx.a,ctx.D;ctx.new_collection('BaggageBackdrop43','none')
 sides=[s for s in segments if s['axis']=='y' and s['k']==-26 and 'checkin' in s['members']]
 record=[]
 for s in sides:
  opaque,_=core.wall_panels(D,s)
  # Dado construction bands belong to the shell, not to the new service skin.
  # Merge their contiguous rectangles before paneling to avoid false stripes.
  merged=[]
  for lo,hi,z0,z1 in sorted(opaque,key=lambda q:(q[0],q[1],q[2])):
   if merged and abs(merged[-1][0]-lo)<1e-6 and abs(merged[-1][1]-hi)<1e-6 and abs(merged[-1][3]-z0)<1e-6:
    merged[-1]=(lo,hi,merged[-1][2],z1)
   else:merged.append((lo,hi,z0,z1))
  opaque=merged
  for lo,hi,z0,z1 in opaque:
   z0=max(.10,z0);z1=min(s['H']-.11,z1)
   if z1-z0<.04:continue
   # A quiet cream service wall replaces the broad brown slab. It is cut into
   # actual opaque rectangles; the feed hole has no closure or false backdrop.
   _line(a,'43 baggage fitted cream field',s,lo+.009,hi-.009,z0+.004,z1-.004,-.137,-.091,'PlasterWarm')
  for opening in D.get('service_openings38',[]):
   if opening['axis']!='y' or opening['k']!=-26:continue
   c=opening['centre'];half=opening['width']/2;z0,z1=opening['z0'],opening['z1'];l,r=c-half,c+half
   if not s['l']<c<s['h']:continue
   # Three continuous bearing parts surround each feed opening OUTSIDE its
   # exact 1.45 x 1.40m clear rectangle. Deep sidewalls wrap masonry returns.
   for name,lo,hi,a0,a1 in [('left',l-.18,l,z0,z1+.18),('right',r,r+.18,z0,z1+.18),('head',l,r,z1,z1+.18)]:
    _line(a,'43 service portal '+name,s,lo,hi,a0,a1,-.205,.085,'Oak')
   # Broad inset service-bay crown above the aperture; restrained metal lip.
   _line(a,'43 recessed service bay crown',s,l-.18,r+.18,z1+.20,min(2.72,s['H']-.2),-.160,-.139,'Dado')
   _line(a,'43 service crown solid lip',s,l-.18,r+.18,z1+.18,z1+.207,-.173,-.137,'Metal')
   # Bottom threshold remains wholly below z0 and behind the running rollers.
   _line(a,'43 supported service sill',s,l-.18,r+.18,z0-.055,z0,-.193,.085,'Metal')
   record.append(dict(centre=c,clear_width_m=opening['width'],clear_z=[z0,z1],portal_projection_m=.115,
                      open_rectangle_unchanged=True,deep_return_m=.29))
  # Three substantial wood service piers with actual bearing bases, not slats.
  for c in [-17.77,-14.50,-8.22]:
   if not s['l']+.1<c<s['h']-.1:continue
   if any(abs(c-o['centre'])<o['width']/2+.25 for o in D['service_openings38']):continue
   _line(a,'43 baggage timber service pier',s,c-.09,c+.09,.12,2.77,-.176,-.137,'Oak')
   _line(a,'43 baggage service pier foot',s,c-.09,c+.09,.1,.25,-.188,-.137,'Metal')
 identities=_service_identity(ctx)
 for row in record:row['service_identity']=next(q for q in identities if q['centre']==row['centre'])
 a.ACTIVE=None
 return record

def _assign_structure(ctx):
 """Scoped material replacement only; underlying collision topology untouched."""
 import bpy
 a=ctx.a
 maps={
  'SM_AP_Walls38': {'MI_AP_P38ACream':'Plaster','MI_AP_P38ANavy':'Dado','MI_AP_P38ASage':'Dado','MI_AP_P38AOak':'Oak','MI_AP_P38ACeiling':'Ceiling'},
  'SM_AP_Floors38': {'MI_AP_P38AStone':'Floor','MI_AP_P38ACarpet':'Carpet','MI_AP_P38AWCStone':'WC'},
  'SM_AP_Ceilings38': {'MI_AP_P38ACeiling':'Ceiling'},
 }
 changed=[]
 for aid,mapping in maps.items():
  col=_register(ctx,aid,'complex')
  for ob in col.objects:
   if ob.type!='MESH':continue
   ob.data=ob.data.copy()
   for i,m in enumerate(ob.data.materials):
    if m and m.name in mapping:
     target=a.MATS[PREFIX+mapping[m.name]];ob.data.materials[i]=target
     changed.append(dict(asset=aid,part=ob.name,slot=i,before=m.name,after=target.name))
   _uv(ob)
 return changed

def plan(ctx):
 # Finish-only assignment deliberately leaves final authoritative dimensions,
 # routes, room boundaries, collision, interaction names and portals intact.
 return dict(scope='Terminal public surface finishes only',changes_to_plan=False)

def apply(ctx):
 import bpy
 a,D=ctx.a,ctx.D;state=D.setdefault('repair38',{})
 _materials(a)
 if TAG in state:
  for aid in OWNED:_register(ctx,aid,'none')
  for aid in STRUCTURAL:_register(ctx,aid,'complex')
  identities=_service_identity(ctx)
  for row in state[TAG]['baggage_service_portals']:
   row['service_identity']=next(q for q in identities if q['centre']==row['centre'])
  return dict(state[TAG],repeat_safe_reused=True)
 sys.path.insert(0,str(HERE.parent/'01_architecture'))
 import architecture38 as core
 segments=core.wall_segments(D)
 original_names=[q['name'] for q in D['instances']]
 original_interactions=repr(D['interactions']);original_portals=repr(D['portals'])
 structure=_assign_structure(ctx);panels=_cladding(ctx,segments,core);baggage=_baggage(ctx,segments,core)
 for aid,name in zip(OWNED,['Airport43 fitted public wall finishes','Airport43 baggage service backdrop']):
  ctx.add(aid,name,[0,0,0],collision=False)
 assert all(n in [q['name'] for q in D['instances']] for n in original_names)
 assert repr(D['interactions'])==original_interactions and repr(D['portals'])==original_portals
 result=dict(status='IMPLEMENTED_SOURCE_REQUIRES_NATIVE_VISUAL_VALIDATION',asset_ids=list(OWNED+STRUCTURAL),
             new_assets=list(OWNED),material_changes=structure,wall_panels=panels,baggage_service_portals=baggage,
             texture_tile_metres={PREFIX+k:v[4] for k,v in MATERIALS.items() if v[0]},
             floor_joint_m=.003,collision_topology_unchanged=True,interaction_names_unchanged=True,
             public_room_dimensions_unchanged=True,plane_and_characters_untouched=True,
             native_hook='Fixes/06_visual_finish43/native_finish43.py:apply_native',
             native_validation='Root must bind authored texture graph after fresh asset import and inspect gameplay shots')
 state[TAG]=result
 return result

build=apply
