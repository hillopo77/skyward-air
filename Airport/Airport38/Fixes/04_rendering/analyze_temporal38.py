"""Compare genuine native sequences at unchanged camera, size and exposure.

Usage: python analyze_temporal38.py capture_dir output.json
Requires Pillow and numpy. Does not manufacture screenshots or diagnose physics.
"""
import json
from pathlib import Path


def analyze(folder):
    import numpy as np
    from PIL import Image
    folder=Path(folder);report={}
    for prefix in ('33_CurtainHold','34_CeilingHold','35_A08Move'):
        files=sorted(folder.glob(prefix+'*.png'))
        if len(files)<4:
            report[prefix]=dict(status='MISSING',files=len(files));continue
        arrays=[np.asarray(Image.open(f).convert('RGB'),dtype=np.float32) for f in files]
        if len({a.shape for a in arrays})!=1:raise ValueError('Changing viewport size invalidates temporal comparison')
        diff=np.stack([np.abs(a-b) for a,b in zip(arrays[2:],arrays[3:])])
        q=dict(status='MEASURED',frames=len(files),viewport=[arrays[0].shape[1],arrays[0].shape[0]],
            warmup_frames=2,mean_absolute_rgb_delta_0_255=float(diff.mean()),
            p99_rgb_delta_0_255=float(np.quantile(diff,.99)),
            interpretation='Moving-camera delta contains genuine scene motion; never an FPS metric or isolated AA diagnosis.')
        if prefix=='34_CeilingHold':
            q['probe_xy']=[900,300]
            q['probe_rgb']=[a[300,900].astype(int).tolist() for a in arrays]
            q['probe_max_range_0_255']=int(np.ptp(np.array(q['probe_rgb']),axis=0).max())
            q['baseline_mean_delta_0_255']=10.8162527084
            q['same_camera_required']=dict(eye=[-28,13.5,1.7],target=[-28,16,3.4],fov=78)
            q['review_required']='Inspect ceiling ROI for alternating materials. Mean improvement alone cannot pass a dark/flat/blurred picture.'
        report[prefix]=q
    return dict(status='MEASURED_REQUIRES_VISUAL_REVIEW',sequences=report,
        caveats=['Use identical native1080p/100%, camera, exposure and settle time.',
                 'Capture-free representative gameplay CPU/GPU timing is a separate acceptance run.',
                 'Run SSR A/B only after geometry and TAA corrections; SSR remains an unproven risk.',
                 'Inspect moving held props and eyes for ghost trails, not just stationary frames.'])


if __name__=='__main__':
    import sys
    result=analyze(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
