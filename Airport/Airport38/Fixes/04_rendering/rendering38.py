"""Airport38 rendering specification. Source-only: geometry belongs to its owners."""
PROFILE = {
    'name': 'Airport38 Native Stable', 'requested_viewport': [1920, 1080],
    'cvars': {
        'r.AntiAliasingMethod': 2, 'r.ScreenPercentage': 100,
        'r.DynamicRes.OperationMode': 0, 'r.TemporalAASamples': 16,
        'r.TemporalAACurrentFrameWeight': .10, 'r.TemporalAAFilterSize': 1,
        'r.TemporalAA.Quality': 2, 'r.Tonemapper.Sharpen': .10,
        'r.MotionBlurQuality': 0, 'r.DepthOfFieldQuality': 0,
        'r.SceneColorFringeQuality': 0, 'r.MaxAnisotropy': 16,
        'r.Shadow.MaxResolution': 4096,
    },
    'pixel_budget': '100% of the actual viewport; no supersampling claim',
    'grain': 0, 'motion_blur': 0, 'depth_of_field': 0,
    'reflection_policy': 'preserve SSR pending controlled native A/B; no proven SSR cause',
}


def plan(ctx):
    ctx.D.setdefault('repair38', {})['rendering'] = dict(PROFILE,
        authority='airport_rendering38.install after every legacy initializer',
        shadows='explicit enclosed practical keys; room-bounded neutral-warm indirect IBL floor',
        ceiling_material='MI_AP_P38ACeiling, matte, zero emission',
        geometry_dependencies=['architecture: single ceiling owner',
                               'equipment: dark backed overlapping scanner curtain'],
        baseline={'ceiling_mean_delta_0_255': 10.8162527084,
                  'curtain_mean_delta_0_255': .3276618719,
                  'ceiling_pixel_xy': [900, 300]})


def build(ctx):
    # Architecture builds all real visible fixtures last. Native hook reads the
    # FINAL D.lights, including moving bridge practicals preserved by assembly.
    if 'rendering' not in ctx.D.get('repair38', {}):
        plan(ctx)


def light_specs(D):
    """Pure, testable role policy; no actor-count/index-dependent decisions."""
    zones = {z['id']: z for z in D['zones']}
    result = []
    for i, src in enumerate(D.get('lights', [])):
        q = dict(src)
        zone = zones.get(q.get('zone'))
        moving = bool(q.get('follow_actor'))
        enclosed = bool(zone) or moving
        q.update(name=q.get('name', 'AP38 practical %03d %s' % (i, q.get('role', 'fixture'))),
                 role=q.get('role', 'bridge_practical' if moving else 'practical'),
                 category='practical_key' if enclosed else 'exterior_practical',
                 casts_shadows=enclosed,
                 shadow_intent='physical fixture / walls, people and furniture' if enclosed else 'sheltered exterior wash',
                 temperature=q.get('temperature', 3300 if moving else 3400),
                 lumens=q.get('lumens', q.get('watts', 350)),
                 direction=[0, 0, -1], specular_scale=.16)
        # A source optic can illuminate a normal floor without unbounded reach.
        q['radius_cm'] = 360 if moving else min(680, max(380, q['position'][2] * 145))
        result.append(q)
    return result


def ambient_specs(D):
    """Small global fill, applied to room AND unbound grades alike.

    Pass45: this term used to be the interior's ENTIRE fill light at intensity
    .22, carried only by camera-bound room volumes. Crossing a volume face made
    it appear or vanish in 12 cm, which was the reported white-out, and the
    version without it was the rejected "horror lighting". The fill is now
    applied to the unbound grades too, so it cannot pop, and its intensity is
    reduced because SCREEN_SPACE bounce supplies the gradient it never could.
    The rect is no longer inset, so adjacent room volumes share their face and
    there is no un-graded band at internal doorways.
    """
    specs=[]
    for z in D['zones']:
        x0,x1,y0,y1=z['rect'];height=z['ceiling_m']
        specs.append(dict(zone=z['id'],volume_label='AP38 warm grade '+z['id'],
            rect=[x0,x1,y0,y1],height=height,
            role='room_indirect_ambient',intensity=.10,
            tint=[1.,.98,.94,1.],blend_radius_cm=120.,priority=1538.,
            shadow_intent='preserves direct key occlusion and screen-space contact AO',
            cubemap='T_AP38_NeutralIndirect',
            bounds_kind='camera-local postprocess room region, not world-space light clipping'))
    return specs


def write_constant_hdr(path, rgb=(1.,1.,1.), width=64, height=32):
    """Original neutral low-frequency HDR environment; no image file dependencies.

    Radiance RGBE scanline RLE, angularly constant in every direction/mip. This
    removes the prior local warm pools; brightness comes from bounded PP scalar.
    """
    import math
    from pathlib import Path
    if not (8<=width<=127 and height>0 and min(rgb)>=0):raise ValueError('Unsupported constant HDR dimensions/radiance')
    largest=max(rgb)
    if largest<1e-32:rgbe=[0,0,0,0]
    else:
        mantissa,exponent=math.frexp(largest)
        rgbe=[min(255,int(v*mantissa*256/largest)) for v in rgb]+[exponent+128]
    data=bytearray(('#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n'%(height,width)).encode('ascii'))
    row=bytes([2,2,width>>8,width&255])+b''.join(bytes([128+width,c]) for c in rgbe)
    data.extend(row*height);Path(path).write_bytes(data)
    return dict(width=width,height=height,rgb=list(rgb),rgbe=rgbe,bytes=len(data),angular_variance=0.)
