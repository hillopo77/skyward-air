"""Original deterministic, seamless low-contrast colour/roughness maps.
No external media, generative service, photographic scan or normal noise.
"""
import math,struct,zlib
from pathlib import Path
from finish43 import MATERIALS
F=Path(__file__).parent/'Textures';F.mkdir(exist_ok=True)
def png(path,size,pixels):
 def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
 raw=b''.join(b'\0'+pixels[y*size*4:(y+1)*size*4] for y in range(size))
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,7))+chunk(b'IEND',b''))
for suffix,(file,colour,rough,metal,tile) in MATERIALS.items():
 if not file:continue
 n=1024 if suffix in {'Floor','WC'} else 256
 rgb=[int(colour[i:i+2],16) for i in (0,2,4)];pixels=bytearray(n*n*4)
 for y in range(n):
  v=(y+.5)/n
  for x in range(n):
   u=(x+.5)/n
   cloud=(math.sin(math.tau*(u+v))+.5*math.sin(math.tau*(2*u-v)+.8)+.25*math.cos(math.tau*(3*v+u)))/1.75
   shade=1+.014*cloud;rv=rough+.012*cloud
   if suffix=='Oak':
    grain=math.sin(math.tau*(12*u+.15*math.sin(math.tau*v)))+.35*math.sin(math.tau*(23*u+.1*math.sin(2*math.tau*v)))
    shade=1+.034*grain+.012*cloud;rv=rough+.028*grain
   elif suffix in {'Floor','WC'}:
    # 3mm true-world width with a single pixel soft edge. At distance texture
    # mips collapse this almost invisible joint, avoiding thin geometry aliasing.
    distance=min(u,v,1-u,1-v)*tile
    coverage=max(0,min(1,(.0015+tile/(2*n)-distance)/(tile/n)))
    shade=shade*(1-.095*coverage);rv+=.10*coverage
   elif suffix=='Carpet':
    # Broad brushed pile variation, no fine weave/noisy normal detail.
    shade=1+.022*cloud+.009*math.sin(math.tau*(3*u-v));rv=rough+.012*cloud
   i=4*(y*n+x)
   for c in range(3):pixels[i+c]=max(0,min(255,round(rgb[c]*shade)))
   pixels[i+3]=max(0,min(255,round(rv*255)))
 png(F/file,n,pixels)
 print(file,n,'tile',tile,'m',flush=True)
