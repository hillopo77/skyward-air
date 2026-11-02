"""Data-only aircraft annotation adjustment for the modeled luxury module."""
import copy,math
DROP=.080
ASSET='SM_Plane_LuxurySeat_Ergonomic39'

def prepare_data(scene):
    if scene.get('luxury_pose39_prepared'):return dict(already_applied=True)
    seats={q['name'] for q in scene.get('instances',[]) if q.get('asset') in ('SM_Plane_LuxurySeat',ASSET)}
    moved=[];eyes=[]
    for q in scene.get('instances',[]):
        if q.get('asset')=='SM_Plane_LuxurySeat':q['asset']=ASSET
        if q.get('asset')=='SM_Plane_SuiteBuckleLid12' and q['name'].startswith('Business belt release '):
            q['location'][2]-=DROP;moved.append(q['name'])
    for q in scene.get('interactions',[]):
        if q.get('kind')=='seat' and q.get('actor') in seats:
            q['location'][2]-=DROP
            if 'point' in q:q['point'][2]-=DROP
            eyes.append(dict(actor=q['actor'],eye=q['location'],eye_delta_m=-DROP))
        if q.get('actor') in moved:
            for key in ('location','point'):
                if key in q:q[key][2]-=DROP
    scene['luxury_pose39_prepared']=True
    return dict(seated_eye_annotations=eyes,movable_buckle_lids=moved,
        untouched='standing validation approaches, world aircraft origin, screens, suite doors and rails',
        ownership={'static_webbing_and_buckle_frame':ASSET,'interactive_lid':'SM_Plane_SuiteBuckleLid12',
        'runtime_control':'Business belt release 112/212/312/412; original x-axis lid rotation is retained'},
        local_anchors_m={'stowed_buckle_hinge':[0,-.068,.532],
        'left_chassis_webbing_anchor':[-.325,.15,.50],'right_chassis_webbing_anchor':[.325,.15,.50],
        'new_character_hip':[0,-.135,.605],'recommended_worn_lap_buckle':[0,-.20,.66]},
        remaining='Existing controls rotate the separate buckle lid; the fixed chair webbing remains stowed on the pan. A truly wearable fastened loop needs an occupied-state overlay or a skinned belt, and is not represented as complete by this annotation patch.')

def prepare_plane(P,D=None):
    return prepare_data(P.DATA)
