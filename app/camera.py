"""Camera capture: each device is owned and released by its own thread."""
import json
import threading
import time
from pathlib import Path
import cv2

MODES = {'Automática': None, 'Auto fluidez': None, 'Auto calidad': None, 'Compatibilidad': None, 'Inicio rápido': None, '1920x1080': (1920,1080), '1280x720': (1280,720), '640x480': (640,480), 'Predeterminada': None}
FORMATS = ('Automático','MJPG','YUY2')
FPS = (15,30,60)
BACKENDS=('Automático','DirectShow','Media Foundation')
AUTO_MODES=('Automática','Auto fluidez','Auto calidad')

def normalize(raw, default=0):
    raw = raw if isinstance(raw,dict) else {}
    index = raw.get('index',default)
    if type(index) is not int or not 0 <= index <= 31: index=default
    res=raw.get('resolution','Automática'); fmt=raw.get('format','Automático'); fps=raw.get('fps',30)
    return dict(index=index, resolution=res if isinstance(res,str) and res in MODES else 'Automática', format=fmt if fmt in FORMATS else 'Automático', fps=fps if type(fps) is int and fps in FPS else 30, backend=raw.get('backend') if raw.get('backend') in BACKENDS else 'Automático')

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

RECOVERY_MODES=('Compatibilidad','Inicio rápido')

def wait_first_frame(cap,stop=None,seconds=1.5,max_reads=20):
    """Allow slow UVC initialization on the same handle. Cannot bound a native read."""
    deadline=time.monotonic()+seconds
    for _ in range(max_reads):
        if stop is not None and stop.is_set():return None
        ok,frame=cap.read()
        if stop is not None and stop.is_set():return None
        if ok and frame is not None and frame.size:return frame
        remaining=deadline-time.monotonic()
        if remaining<=0:break
        delay=min(.08,remaining)
        if stop is not None:
            if stop.wait(delay):return None
        else:time.sleep(delay)
    return None

def try_mode(cap, mode, fps, fmt, stop=None,*,slow_start=False):
    if fmt!='Automático': cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*fmt))
    if mode:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,mode[0]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,mode[1])
    cap.set(cv2.CAP_PROP_FPS,fps)
    if slow_start:return wait_first_frame(cap,stop)
    frame=None
    for _ in range(3):
        if stop is not None and stop.is_set(): return None
        ok,img=cap.read()
        if ok and img is not None and img.size: frame=img
    return frame

def measure_capture(cap,frame,stop=None,window=.4,max_reads=16):
    start=time.monotonic(); count=0
    for _ in range(max_reads):
        if stop is not None and stop.is_set(): break
        ok,img=cap.read()
        if ok and img is not None and img.size: frame=img; count+=1
        if time.monotonic()-start>=window: break
    return frame,count/max(time.monotonic()-start,1e-6)

def mode_score(frame,rate,target,profile):
    h,w=frame.shape[:2]; pixels=w*h; capped=min(rate,target)
    if profile=='Auto calidad': return (pixels,capped)
    if profile=='Auto fluidez': return (rate>=target*.85,capped,pixels)
    return (rate>=target*.85,pixels if rate>=target*.85 else capped,capped if rate>=target*.85 else pixels)

def open_compatible_camera(config, stop=None):
    """Use the V0.5.0 negotiation without a performance probe, or native defaults."""
    index=config['index']; auto=config['resolution'] in AUTO_MODES or config['resolution']=='Compatibilidad'; explicit=MODES[config['resolution']]
    # Try MJPG first in automatic mode for USB bandwidth, then driver defaults.
    formats=['MJPG','Automático'] if config['format']=='Automático' and auto else [config['format']]
    modes=[(1920,1080),(1280,720),(640,480),None] if auto else [explicit]
    best=None
    def cancelled(): return stop is not None and stop.is_set()
    def attempt(backend,mode,fmt):
        try: cap=cv2.VideoCapture(index,backend)
        except cv2.error: return None
        keep=False
        try:
            if not cap.isOpened(): return None
            if cancelled(): return None
            frame=try_mode(cap,mode,config['fps'],fmt,stop,slow_start=config['resolution'] in RECOVERY_MODES)
            if frame is None: return None
            if cancelled(): return None
            keep=True; return cap,frame
        except cv2.error: return None
        finally:
            if not keep: cap.release()
    # Explicit compatibility mode tries native defaults first, with no property changes.
    if config['resolution']=='Compatibilidad' and config['format']=='Automático':
        drivers={'DirectShow':[cv2.CAP_DSHOW],'Media Foundation':[cv2.CAP_MSMF]}.get(config.get('backend'),[cv2.CAP_DSHOW,cv2.CAP_MSMF])
        for backend in drivers:
            if cancelled(): raise RuntimeError('Captura cancelada')
            try: cap=cv2.VideoCapture(index,backend)
            except cv2.error: continue
            keep=False
            try:
                if not cap.isOpened(): continue
                frame=wait_first_frame(cap,stop)
                if frame is not None and not cancelled():
                    keep=True;return cap,frame
            except cv2.error: pass
            finally:
                if not keep: cap.release()
    # Legacy negotiation; do not probe other indices.
    drivers={'DirectShow':[cv2.CAP_DSHOW],'Media Foundation':[cv2.CAP_MSMF]}.get(config.get('backend'),[cv2.CAP_DSHOW,cv2.CAP_MSMF])
    for backend in drivers:
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


def open_performance_camera(config, stop=None):
    """Probe selected index sequentially; choose based on actual successful reads."""
    index=config['index']; profile=config['resolution']; auto=profile in AUTO_MODES
    explicit=MODES[profile]; fps=config['fps']
    formats=['MJPG','Automático'] if config['format']=='Automático' else [config['format']]
    modes=([(1280,720),(640,480),(1920,1080),None] if profile=='Auto fluidez' else
           [(1920,1080),(1280,720),(640,480),None]) if auto else [explicit]
    drivers={'DirectShow':[cv2.CAP_DSHOW],'Media Foundation':[cv2.CAP_MSMF]}.get(config.get('backend'),[cv2.CAP_DSHOW,cv2.CAP_MSMF])
    best=None
    def cancelled(): return stop is not None and stop.is_set()
    def attempt(backend,mode,fmt,probe=True):
        try: cap=cv2.VideoCapture(index,backend)
        except cv2.error: return None
        keep=False
        try:
            if not cap.isOpened() or cancelled(): return None
            frame=try_mode(cap,mode,fps,fmt,stop)
            if frame is None or cancelled(): return None
            rate=0.
            if probe: frame,rate=measure_capture(cap,frame,stop)
            if cancelled() or (probe and rate<=0): return None
            keep=True; return cap,frame,rate
        except cv2.error: return None
        finally:
            if not keep: cap.release()
    for mode in modes:
        for backend in drivers:
            for fmt in formats:
                if cancelled(): raise RuntimeError('Captura cancelada')
                result=attempt(backend,mode,fmt)
                if result is None: continue
                cap,frame,rate=result; h,w=frame.shape[:2]
                adequate=rate>=fps*.85
                requested=mode is None or (w>=mode[0] and h>=mode[1])
                score=mode_score(frame,rate,fps,profile) if auto else (requested,min(rate,fps),w*h)
                candidate=(score,backend,mode,fmt)
                if best is None or score>best[0]: best=candidate
                if adequate and requested and (profile!='Auto calidad' or mode==(1920,1080)):
                    # An earlier fallback may already have delivered higher resolution.
                    if best==candidate: return cap,frame
                cap.release()
    if best and not cancelled():
        _,backend,mode,fmt=best; result=attempt(backend,mode,fmt,probe=False)
        if result is not None: return result[0],result[1]
    raise RuntimeError('Captura cancelada' if cancelled() else 'No se pudo abrir la cámara. Probá Predeterminada / Automático u otro controlador.')

def open_camera(config,stop=None):
    """Retain fast webcam negotiation; restore the old path for fragile USB cameras."""
    profile=config['resolution']
    if profile in RECOVERY_MODES:
        return open_compatible_camera(config,stop)
    try: return open_performance_camera(config,stop)
    except RuntimeError:
        if stop is not None and stop.is_set(): raise
        return open_compatible_camera(config,stop)

class Capture:
    def __init__(self,config):
        self.config=dict(config); self.stop=threading.Event(); self.lock=threading.Lock()
        self.frame=None; self.stamp=0.; self.fps=0.; self.status='Midiendo modos de captura…'; self.format=''; self.backend='No informado'; self.ready=False
        self.thread=threading.Thread(target=self.run,daemon=True); self.thread.start()
    def snapshot(self):
        with self.lock: return self.frame,self.stamp,self.fps,self.status,self.format,self.ready
    def run(self):
        # Retry only the explicit USB recovery profiles; never silently change an index.
        attempts=3 if self.config['resolution'] in RECOVERY_MODES else 1
        for attempt in range(attempts):
            if self.stop.is_set():break
            cap=None
            try:
                cap,frame=open_camera(self.config,self.stop)
                self.stream(cap,frame)
                break
            except Exception as exc:
                with self.lock:
                    self.frame=None; self.ready=False; self.fps=0.;self.stamp=0.
                    self.status=str(exc)
                if self.stop.is_set() or attempt+1>=attempts:break
            finally:
                if cap is not None:cap.release()
            with self.lock:
                self.status=f'Reconectando cámara ({attempt+2}/{attempts})…'
            if self.stop.wait(.35*(attempt+1)):break
        with self.lock:
            self.frame=None;self.ready=False
            if self.stop.is_set():self.status='Desactivada'

    def stream(self,cap,frame):
        try:backend=cap.getBackendName()
        except (AttributeError,cv2.error):backend='No informado'
        with self.lock:self.backend=backend
        try:fourcc=int(cap.get(cv2.CAP_PROP_FOURCC))
        except (ValueError,TypeError,OverflowError):fourcc=0
        fmt=''.join(chr((fourcc >> (8*i)) & 255) for i in range(4));fmt=fmt if fmt.isprintable() else 'No informado'
        start=time.monotonic();n=0;failures=0
        while not self.stop.is_set():
            now=time.monotonic();n+=1
            with self.lock:
                self.frame=frame;self.stamp=now;self.ready=True;self.status='Conectada';self.format=fmt
                if now-start>=1.0:self.fps=n/(now-start);start=now;n=0
            ok,frame=cap.read()
            while not self.stop.is_set() and (not ok or frame is None or not frame.size):
                failures+=1
                if failures>=5:raise RuntimeError('Captura interrumpida. Pulsá Conectar.')
                if self.stop.wait(.05):return
                ok,frame=cap.read()
            failures=0
