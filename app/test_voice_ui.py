"""GUI and voice state integration with simulated devices and model."""
import tempfile,time,threading,tkinter as tk
from pathlib import Path
from unittest.mock import patch
import jarvis_vision as j
from test_jarvis import FakeCap

def wait(root,condition,seconds=5):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        root.update()
        if condition(): return
        time.sleep(.015)
    raise AssertionError('timeout')

calls=[]; recording=threading.Event(); spoken=[]; requests=[]
def wake(stop,on_state):
    recording.set(); calls.append('listen'); on_state('mic activo simulado')
    try:
        if len(calls)==1: return 'qué ves'
        stop.wait(5); return 'comando cancelado'
    finally: recording.clear()
def answer(frame,question,history):
    requests.append((frame is not None,question,history)); return 'respuesta simulada'
def speak(text):
    assert not recording.is_set(); spoken.append(text)
with tempfile.TemporaryDirectory() as d, patch('camera.cv2.VideoCapture',FakeCap), patch.object(j,'CONFIG',Path(d)/'config.json'), patch.object(j,'ask_vision',side_effect=answer), patch.object(j.voice,'listen_wake',side_effect=wake), patch.object(j.voice,'speak',side_effect=speak):
    root=tk.Tk(); app=j.App(root,0)
    try:
        wait(root,lambda:app.slots[0].frame() is not None)
        assert not calls and not app.wake_enabled
        app.toggle_wake(); wait(root,lambda:len(calls)>=2 and bool(spoken))
        assert requests[0][:2]==(True,'qué ves'); assert len(app.conversation.snapshot())==2
        app.cancel_voice(); wait(root,lambda:not app.listen_busy)
        assert len(requests)==1 and not recording.is_set()
        app.mode.set('Conversación sin cámara'); app.slots[0].disable(); app.question.delete(0,'end'); app.question.insert(0,'seguí explicando'); app.ask(); wait(root,lambda:not app.ask_busy)
        assert requests[-1][0] is False and len(requests[-1][2])==2
        app.clear_context(); assert not app.conversation.snapshot()
        print('UI voz: opt-in, pregunta, respuesta sin micrófono, reactivación, cancelación, texto sin cámara y contexto OK')
    finally:
        sessions=[s.capture for s in app.slots if s.capture]; app.close()
        for s in sessions: s.thread.join(2)
