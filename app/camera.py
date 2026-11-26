"""Camera capture: each device is owned and released by its own thread."""
import json
import threading
import time
from pathlib import Path
import cv2

MODES = {'Automática': None, '1920x1080': (1920,1080), '1280x720': (1280,720), '640x480': (640,480), 'Predeterminada': None}
FORMATS = ('Automático','MJPG','YUY2')
FPS = (15,30,60)

def normalize(raw, default=0):
    raw = raw if isinstance(raw,dict) else {}
    index = raw.get('index',default)
    if type(index) is not int or not 0 <= index <= 31: index=default
    res=raw.get('resolution','Automática'); fmt=raw.get('format','Automático'); fps=raw.get('fps',30)
    return dict(index=index, resolution=res if isinstance(res,str) and res in MODES else 'Automática', format=fmt if fmt in FORMATS else 'Automático', fps=fps if type(fps) is int and fps in FPS else 30)

def load_config(path):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict): data={}
    except (OSError,ValueError): data={}
    old=data.get('camera',0)
    a=normalize(data.get('primary'),old if type(old) is int and 0<=old<=31 else 0)
    b=normalize(data.get('secondary'),1 if a['index']!=1 else 0)
    profiles={}
    if isinstance(data.get('profiles'),dict):
        for k,v in data['profiles'].items():
            if k.isdigit() and 0<=int(k)<=31:
                p=normalize(v,int(k)); p['index']=int(k); profiles[k]=p
    return a,b,profiles

def save_config(path,a,b,profiles):
    path=Path(path); tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps({'camera':a['index'],'primary':a,'secondary':b,'profiles':profiles},indent=2,ensure_ascii=False),encoding='utf-8'); tmp.replace(path)

def try_mode(cap, mode, fps, fmt):
    if fmt!='Automático': cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*fmt))
    if mode:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,mode[0]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,mode[1])
    cap.set(cv2.CAP_PROP_FPS,fps)
    frame=None
    for _ in range(3):
        ok,img=cap.read()
        if ok and img is not None and img.size: frame=img
    return frame

def open_camera(config, stop=None):
    """Auto searches common modes, preferring actual pixel count. Explicit mode reports real result."""
    index=config['index']; auto=config['resolution']=='Automática'; explicit=MODES[config['resolution']]
    # Try MJPG first in automatic mode for USB bandwidth, then driver defaults.
    formats=['MJPG','Automático'] if config['format']=='Automático' and auto else [config['format']]
    modes=[(1920,1080),(1280,720),(640,480),None] if auto else [explicit]
    best=None
    def cancelled(): return stop is not None and stop.is_set()
    def attempt(backend,mode,fmt):
        cap=cv2.VideoCapture(index,backend)
        keep=False
        try:
            if not cap.isOpened(): return None
            frame=try_mode(cap,mode,config['fps'],fmt)
            if frame is None: return None
            keep=True; return cap,frame
        finally:
            if not keep: cap.release()
    # Most typical cameras succeed on first or second attempt. Do not probe other indices.
    for backend in (cv2.CAP_DSHOW,cv2.CAP_MSMF):
        for mode in modes:
            for fmt in formats:
                if cancelled(): raise RuntimeError('Captura cancelada')
                result=attempt(backend,mode,fmt)
                if result is None: continue
                cap,frame=result; h,w=frame.shape[:2]
                if not auto or (w>=1920 and h>=1080): return cap,frame
                score=w*h
                if best is None or score>best[0]: best=(score,backend,mode,fmt)
                cap.release()
            # If both 1080 and 720 have been tried and HD was delivered, don't search lower modes.
            if mode==(1280,720) and best and best[0]>=1280*720: break
        if best: break  # retain working backend, avoid disrupting other camera
    if best and not cancelled():
        _,backend,mode,fmt=best; result=attempt(backend,mode,fmt)
        if result is not None: return result
    raise RuntimeError('No se pudo abrir la cámara con estos ajustes. Cerrá Zoom u otras apps; probá Predeterminada / Automático.')

class Capture:
    def __init__(self,config):
        self.config=dict(config); self.stop=threading.Event(); self.lock=threading.Lock()
        self.frame=None; self.stamp=0.; self.fps=0.; self.status='Conectando…'; self.format=''; self.ready=False
        self.thread=threading.Thread(target=self.run,daemon=True); self.thread.start()
    def snapshot(self):
        with self.lock: return self.frame,self.stamp,self.fps,self.status,self.format,self.ready
    def run(self):
        cap=None
        try:
            cap,frame=open_camera(self.config,self.stop)
            try: fourcc=int(cap.get(cv2.CAP_PROP_FOURCC))
            except (ValueError,TypeError,OverflowError): fourcc=0
            fmt=''.join(chr((fourcc >> (8*i)) & 255) for i in range(4)); fmt=fmt if fmt.isprintable() else 'No informado'
            start=time.monotonic(); n=0; failures=0
            while not self.stop.is_set():
                now=time.monotonic(); n+=1
                with self.lock:
                    self.frame=frame; self.stamp=now; self.ready=True; self.status='Conectada'; self.format=fmt
                    if now-start>=1.0: self.fps=n/(now-start); start=now; n=0
                ok,frame=cap.read()
                while not self.stop.is_set() and (not ok or frame is None or not frame.size):
                    failures+=1
                    if failures>=5: raise RuntimeError('Captura interrumpida. Pulsá Conectar.')
                    time.sleep(.05); ok,frame=cap.read()
                failures=0
        except Exception as exc:
            with self.lock: self.status=str(exc)
        finally:
            if cap is not None: cap.release()
            with self.lock:
                self.frame=None; self.ready=False
                if self.stop.is_set(): self.status='Desactivada'
