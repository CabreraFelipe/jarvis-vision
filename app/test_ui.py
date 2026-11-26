"""Smoke test with simulated webcams and local AI; needs a display (Xvfb or Windows)."""
import tempfile,time,tkinter as tk
from pathlib import Path
from unittest.mock import patch
import jarvis_vision as j
from test_jarvis import FakeCap

def wait(root,condition,seconds=6):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        root.update()
        if condition(): return
        time.sleep(.02)
    raise AssertionError('timeout')

with tempfile.TemporaryDirectory() as d, patch('camera.cv2.VideoCapture',FakeCap), patch.object(j,'CONFIG',Path(d)/'config.json'), patch.object(j,'ask_vision',return_value='respuesta simulada'), patch.object(j.messagebox,'showwarning') as warn:
    root=tk.Tk(); app=j.App(root,0); a,b=app.slots
    try:
        wait(root,lambda:a.frame() is not None and a.saved)
        assert '640 × 480' in a.status.get()
        assert 'FPS captura' in a.status.get() and 'Vista:' in a.status.get()
        assert a.backend.get()=='Automático'
        assert b.capture is None
        b.index.set('0'); b.connect(); assert warn.called and b.capture is None
        b.index.set('1'); b.res.set('640x480'); b.connect(); wait(root,lambda:b.frame() is not None and b.saved)
        assert int(a.frame()[0,0,0])==0 and int(b.frame()[0,0,0])==1
        assert not a.capture.config['compatibility_first'] and b.capture.config['compatibility_first']
        b.res.set('Compatibilidad'); b.connect(); wait(root,lambda:b.saved and b.frame() is not None)
        assert b.config['resolution']=='Compatibilidad' and a.frame() is not None
        app.source.set('Cámara 2'); app.source_changed(); app.ask(); wait(root,lambda:not app.ask_busy); assert 'Cámara 2' in app.answer.get('1.0','end')
        b.index.set('3'); b.connect(); wait(root,lambda:b.saved and b.config['index']==1 and b.frame() is not None)
        b.disable(); assert b.frame() is None; wait(root,lambda:b.capture is None); assert a.frame() is not None
        print('UI: inicio, dos cámaras, bloqueo de índice duplicado, selección IA, restauración y apagado OK')
    finally:
        sessions=[s.capture for s in app.slots if s.capture]; app.close()
        for s in sessions: s.thread.join(2)
