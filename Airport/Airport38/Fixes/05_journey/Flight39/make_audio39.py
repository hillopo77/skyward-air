"""Small original PCM recordings; standard library only, no external media."""
import math,wave,struct,random
from pathlib import Path
F=Path(__file__).with_name('Audio');F.mkdir(exist_ok=True);rate=22050;r=random.Random(10739)
def write(name,seconds,sample):
    n=int(rate*seconds)
    with wave.open(str(F/(name+'.wav')),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,sample(i/rate,i,n)))*30000)) for i in range(n)))
# Integer frequency harmonics and a quiet common window make the engine loop
# seamless. The runtime scales this local sound with the actual engine spool.
write('Engine39',2.,lambda t,i,n:.13*math.sin(2*math.pi*54*t)+.075*math.sin(2*math.pi*108*t)+.035*math.sin(2*math.pi*270*t)+.018*math.sin(2*math.pi*864*t))
write('Click39',.055,lambda t,i,n:(r.random()*2-1)*.33*math.exp(-t*95))
write('Caution39',.35,lambda t,i,n:.12*math.sin(2*math.pi*700*t)*math.sin(math.pi*i/n)**2)
write('Radio39',.6,lambda t,i,n:(.065*math.sin(2*math.pi*(950 if t<.24 else 740)*t)+.022*(r.random()*2-1))*math.sin(math.pi*i/n)**2)
print('Original flight audio generated',*[p.name for p in F.glob('*.wav')])
