"""Read-only FBX geometry inventory; no Blender/Unreal process required."""
import array, struct, sys, zlib
from pathlib import Path


def read(path):
    f=Path(path).open('rb');header=f.read(23)
    if not header.startswith(b'Kaydara FBX Binary'):raise ValueError('Binary FBX expected')
    version=struct.unpack('<I',f.read(4))[0];wide=version>=7500
    fmt='<QQQB' if wide else '<IIIB';size=25 if wide else 13
    def prop():
        t=f.read(1).decode('ascii')
        if t in 'YCLFDI':
            code={'Y':'h','C':'?','L':'q','F':'f','D':'d','I':'i'}[t]
            return struct.unpack('<'+code,f.read(struct.calcsize(code)))[0]
        if t in 'SR':
            n=struct.unpack('<I',f.read(4))[0];data=f.read(n)
            return data.decode('utf-8','replace') if t=='S' else data
        if t in 'fdlibc':
            n,encoding,length=struct.unpack('<III',f.read(12));data=f.read(length)
            if encoding:data=zlib.decompress(data)
            code={'f':'f','d':'d','l':'q','i':'i','b':'B','c':'B'}[t]
            values=array.array(code);values.frombytes(data)
            if sys.byteorder!='little':values.byteswap()
            if len(values)!=n:raise ValueError(('array length',n,len(values)))
            return values
        raise ValueError(('Unknown property',t))
    def node():
        row=f.read(size)
        if len(row)<size:return None
        end,count,plen,nlen=struct.unpack(fmt,row)
        if end==0:return None
        name=f.read(nlen).decode('utf-8');props=[prop() for _ in range(count)];children=[]
        while f.tell()<end-size:
            q=node()
            if q:children.append(q)
            else:break
        f.seek(end);return dict(name=name,props=props,children=children)
    roots=[]
    while True:
        q=node()
        if q is None:break
        roots.append(q)
    f.close();return roots


def child(node,name,default=None):
    return next((q for q in node['children'] if q['name']==name),default)


def meshes(path):
    roots=read(path);objects=next(q for q in roots if q['name']=='Objects')
    for q in objects['children']:
        if q['name']!='Geometry' or q['props'][-1]!='Mesh':continue
        verts=child(q,'Vertices')['props'][0];indices=child(q,'PolygonVertexIndex')['props'][0]
        material=child(q,'LayerElementMaterial');mats=child(material,'Materials')['props'][0] if material else None
        poly=[];faces=[]
        for k in indices:
            poly.append(-k-1 if k<0 else k)
            if k<0:faces.append(poly);poly=[]
        yield dict(id=q['props'][0],name=q['props'][1],vertices=[tuple(verts[i:i+3]) for i in range(0,len(verts),3)],faces=faces,materials=mats,node=q)


if __name__=='__main__':
    for path in sys.argv[1:]:
        print(Path(path).name)
        for m in meshes(path):
            p=m['vertices'];print(m['name'],len(p),len(m['faces']),[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]])
