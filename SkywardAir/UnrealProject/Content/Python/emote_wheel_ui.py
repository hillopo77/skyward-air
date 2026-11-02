"""Runtime restyle of the existing UMG widget; no editor asset rebuild needed."""
import math
import unreal as u
from emote_wheel_model import wheel_geometry,pop_scale,damp_alpha

CREAM=(.98,.91,.76,1.)
INK=(.018,.039,.061,1.)
TEAL=(.065,.27,.31,1.)
GOLD=(1.,.69,.25,1.)
PALE=(.78,.94,.93,1.)


def color(value):return u.LinearColor(*value)
def slate(value):return u.SlateColor(specified_color=color(value))


def brush(fill,radius=38.,outline=(.23,.48,.51,1.),width=1.5):
    edge=u.SlateBrushOutlineSettings(corner_radii=u.Vector4(radius,radius,radius,radius),color=slate(outline),width=width,rounding_type=u.SlateBrushRoundingType.FIXED_RADIUS)
    return u.SlateBrush(draw_as=u.SlateBrushDrawType.ROUNDED_BOX,tint_color=slate(fill),outline_settings=edge)


def style(fill,selected=False):
    normal=brush(fill,38.,GOLD if selected else (.19,.43,.47,1.),2.5 if selected else 1.5)
    return u.ButtonStyle(normal=normal,hovered=brush(GOLD if selected else TEAL,38.,PALE,2.),pressed=brush(GOLD,38.,CREAM,2.),disabled=normal,normal_padding=u.Margin(12,7,12,7),pressed_padding=u.Margin(12,10,12,4))


class WheelView:
    HUB=(360.,360.)
    RADIUS=216.

    def __init__(self,pack):
        self.pack=pack;self.ready=False;self.created=[];self.weights=[0.]*8;self.cache={}
        self.geometry=(0.,0.,1.,1.);self.last_selection=object();self.shadows=[]

    def get(self,name):
        if name not in self.cache:
            self.cache[name]=self.pack.find_widget(name)
            if not self.cache[name]:raise RuntimeError('Missing emote widget: '+name)
        return self.cache[name]

    def place(self,widget,x,y,w,h,z=2):
        slot=widget.slot
        slot.set_anchors(u.Anchors());slot.set_alignment(u.Vector2D())
        slot.set_position(u.Vector2D(x,y));slot.set_size(u.Vector2D(w,h));slot.set_z_order(z)
        return slot

    def label(self,name,size,tint=CREAM):
        label=self.get(name)
        label.set_font(u.SlateFontInfo(font_object=u.load_asset('/Engine/EngineFonts/Roboto'),size=size,typeface_font_name='Bold'))
        label.set_color_and_opacity(slate(tint))
        return label

    def image(self,name,x,y,w,h,fill,radius,z):
        panel=self.get('WheelPanel');tree=panel.get_outer()
        image=u.new_object(u.Image,outer=tree,name=name);image.set_brush(brush(fill,radius,fill,0))
        panel.add_child_to_canvas(image);self.place(image,x,y,w,h,z)
        image.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE);self.created.append(image)
        return image

    def build(self):
        main=self.get('WheelPanel');slot=main.slot
        slot.set_anchors(u.Anchors(minimum=u.Vector2D(.5,.5),maximum=u.Vector2D(.5,.5)))
        slot.set_alignment(u.Vector2D(.5,.5));slot.set_position(u.Vector2D());slot.set_size(u.Vector2D(720,800))
        main.set_render_transform_pivot(u.Vector2D(.5,.5));main.set_visibility(u.SlateVisibility.COLLAPSED)
        self.get('WheelRing').set_visibility(u.SlateVisibility.COLLAPSED)
        self.get('WheelShade').set_brush_color(color((.008,.02,.035,.34)))
        self.get('WheelShade').set_visibility(u.SlateVisibility.COLLAPSED)
        self.image('BubbleHubShadow',250,258,220,220,(0.,0.,0.,.24),110,0)
        self.image('BubbleHub',252,250,216,216,(.025,.075,.105,.98),108,1)
        self.place(self.label('WheelTitle',22),268,308,184,45,3)
        self.place(self.label('CharacterName',13,PALE),270,359,180,24,3)
        self.place(self.label('WheelHelp',12,(.80,.86,.86,1)),270,392,180,44,3)
        for i in range(8):
            angle=-math.pi/2+i*math.pi/4;x=self.HUB[0]+self.RADIUS*math.cos(angle)-69;y=self.HUB[1]+self.RADIUS*math.sin(angle)-42
            self.shadows.append(self.image('BubbleShadow'+str(i),x,y+7,138,84,(0.,0.,0.,.25),38,1))
            button=self.get('Emote'+str(i));self.place(button,x,y,138,84,4)
            button.set_render_transform_pivot(u.Vector2D(.5,.5));button.set_background_color(color((1,1,1,1)));button.set_style(style(INK))
            self.label('Emote'+str(i)+'Label',17)
        for name,x,label in [('PreviousPage',249,'<'),('NextPage',425,'>')]:
            button=self.get(name);self.place(button,x,637,46,42,4);button.set_background_color(color((1,1,1,1)));button.set_style(style(INK));self.get(name+'Label').set_text(label)
        self.place(self.label('PageLabel',15,PALE),302,646,116,26,4)
        for i in range(4):
            button=self.get('Character'+str(i));self.place(button,48+i*157,708,150,42,4);button.set_background_color(color((1,1,1,1)));self.label('Character'+str(i)+'Label',13)
        close=self.get('CloseWheel');self.place(close,652,92,38,38,4);close.set_background_color(color((1,1,1,1)));close.set_style(style(INK));self.get('CloseWheelLabel').set_text('X')
        self.get('EmoteHint').set_brush(brush((.02,.055,.075,.94),20));self.get('EmoteHintLabel').set_text('HOLD Z  /  EMOTES')
        self.get('EmoteHint').slot.set_size(u.Vector2D(220,42))
        self.ready=True;self.refresh()

    def refresh(self):
        if not self.ready:return
        items=self.pack.page_items();selected=self.pack.S['emotes'].selection.selected
        for i in range(8):
            visibility=u.SlateVisibility.VISIBLE if i<len(items) else u.SlateVisibility.COLLAPSED
            self.get('Emote'+str(i)).set_visibility(visibility)
            self.shadows[i].set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE if i<len(items) else u.SlateVisibility.COLLAPSED)
            if i<len(items):
                self.get('Emote'+str(i)+'Label').set_text(self.pack.DISPLAY.get(items[i],items[i]))
                self.get('Emote'+str(i)).set_style(style(GOLD if i==selected else INK,i==selected))
                self.get('Emote'+str(i)+'Label').set_color_and_opacity(slate(INK if i==selected else CREAM))
        self.get('PageLabel').set_text(str(self.pack.S['page']+1)+' / '+str(math.ceil(len(self.pack.PREFERRED)/8)))
        self.get('CharacterName').set_text(self.pack.NAMES[self.pack.S['profile']])
        for i in range(4):self.get('Character'+str(i)).set_style(style(TEAL if i==self.pack.S['profile'] else INK,i==self.pack.S['profile']))
        self.get('WheelTitle').set_text(self.pack.DISPLAY.get(items[selected],items[selected]) if selected is not None and selected<len(items) else 'EMOTES')
        self.get('WheelHelp').set_text('Release Z to play' if selected is not None else 'Drag to choose\nRelease here to cancel')
        self.last_selection=selected

    def measure(self):
        size=self.pack.S['pc'].get_viewport_size();dpi=u.WidgetLayoutLibrary.get_viewport_scale(self.pack.S['world'])
        self.geometry=wheel_geometry(size[0],size[1],dpi)
        return self.geometry

    def over_controls(self):
        return any(self.get(name).is_hovered() for name in ['PreviousPage','NextPage','CloseWheel']+['Character'+str(i) for i in range(4)])

    def animate(self,dt,opened_at,now):
        _,_,scale,_=self.measure();main=self.get('WheelPanel');factor=scale*pop_scale(now-opened_at)
        main.set_render_scale(u.Vector2D(factor,factor));main.set_render_opacity(min(1.,max(0.,(now-opened_at)/.10)))
        chosen=self.pack.S['emotes'].selection.selected
        if chosen!=self.last_selection:self.refresh()
        alpha=damp_alpha(dt)
        for i in range(8):
            self.weights[i]+=(float(i==chosen)-self.weights[i])*alpha;weight=self.weights[i];button=self.get('Emote'+str(i));angle=-math.pi/2+i*math.pi/4
            button.set_render_scale(u.Vector2D(1+.11*weight,1+.11*weight));button.set_render_translation(u.Vector2D(math.cos(angle)*8*weight,math.sin(angle)*8*weight));button.set_render_opacity(1. if i==chosen else .90)
