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


# Opt-in follow-up, speaker isolation and no reactivation after spoken stop.
follow_calls=[];requests=[];spoken=[];recording.clear()
def first_wake(stop,on_state):
    follow_calls.append('wake')
    return 'primera pregunta'
def follow_listen(stop,**kwargs):
    assert not app.speak_busy
    recording.set();follow_calls.append('follow')
    try:return 'segunda pregunta' if follow_calls.count('follow')==1 else 'terminar conversación'
    finally:recording.clear()
with tempfile.TemporaryDirectory() as d, patch('camera.cv2.VideoCapture',FakeCap), patch.object(j,'CONFIG',Path(d)/'config.json'), patch.object(j,'ask_vision',side_effect=answer), patch.object(j.voice,'listen_wake',side_effect=first_wake), patch.object(j.voice,'listen',side_effect=follow_listen), patch.object(j.voice,'speak',side_effect=speak):
    root=tk.Tk();app=j.App(root,0)
    try:
        app.mode.set('Conversación sin cámara')
        assert not app.followup_on.get()
        app.followup_on.set(True);app.toggle_wake()
        wait(root,lambda:not app.wake_enabled and follow_calls.count('follow')==2)
        assert [r[1] for r in requests]==['primera pregunta','segunda pregunta']
        assert follow_calls==['wake','follow','follow'] and len(spoken)==2
        assert not app.listen_busy and not recording.is_set()
        print('UI seguimiento: dos preguntas con una activación, voz sin escucha, parada local sin consulta OK')
    finally:
        app.close();assert app.shutdown.wait(2)

# Real local command path with simulated wake and explicit confirmation.
def memory_wake(stop,on_state):
    return 'recordá que prefiero el cine'
with tempfile.TemporaryDirectory() as d, patch('camera.cv2.VideoCapture',FakeCap), patch.object(j,'CONFIG',Path(d)/'config.json'), patch.object(j,'ask_vision') as model, patch.object(j.voice,'listen_wake',side_effect=memory_wake), patch.object(j.messagebox,'askyesno',return_value=True) as confirm:
    root=tk.Tk();app=j.App(root,0)
    try:
        app.mode.set('Conversación sin cámara')
        app.toggle_wake()
        wait(root,lambda:bool(app.memory.items()) and not app.wake_enabled)
        assert app.memory.items()[0][1]=='prefiero el cine'
        assert not model.called and confirm.call_count==1
        assert not app.memory.settings()[0]
        app.question.delete(0,'end');app.question.insert(0,'olvidá prefiero el cine')
        confirm.return_value=False
        assert app.ask()
        assert len(app.memory.items())==1 and not model.called
        print('UI comandos de memoria: voz, consentimiento, sin IA y cancelación de borrado OK')
    finally:
        app.close();assert app.shutdown.wait(2)

# Suggestions are opt-in, never written by inference; privacy gate clears pending review.
with tempfile.TemporaryDirectory() as d, patch('camera.cv2.VideoCapture',FakeCap), patch.object(j,'CONFIG',Path(d)/'config.json'), patch.object(j,'ask_vision',return_value='ok'), patch.object(j.messagebox,'askyesno',return_value=False) as confirm:
    root=tk.Tk();app=j.App(root,0)
    try:
        app.mode.set('Conversación sin cámara')
        app.memory.configure(True,'Normal',suggestions=True)
        def ask_pref():
            app.question.delete(0,'end');app.question.insert(0,'Prefiero respuestas cortas.')
            assert app.ask();wait(root,lambda:not app.ask_busy)
        ask_pref()
        assert app.pending_preference=='Prefiero respuestas cortas.' and not app.memory.items()
        app.review_preference();assert not app.memory.items() and app.pending_preference is None
        ask_pref()
        app.context_on.set(False);app.clear_context()
        assert app.pending_preference is None
        app.context_on.set(True);ask_pref()
        confirm.return_value=True;app.review_preference()
        assert app.memory.items()[0][1]=='Prefiero respuestas cortas.'
        ask_pref();assert app.pending_preference is None
        print('UI sugerencias: opt-in, revisión, rechazo, contexto privado y deduplicación OK')
    finally:
        app.close();assert app.shutdown.wait(2)
