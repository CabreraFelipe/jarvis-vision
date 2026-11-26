"""JARVIS Vision 0.3 — local multicamera and optional voice."""
import argparse
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
import cv2
from PIL import Image,ImageTk
from camera import Capture, MODES, FORMATS, FPS, BACKENDS, load_config, save_config
from vision import ask_vision
import voice
import voice_output
from voice_output_ui import open_voice_output
import speech_input
from speech_input_ui import open_speech_input
from instance_focus import poll_focus
from voice_followup import Followup,stop_phrase
from shutdown import Shutdown
from assistant_core import AssistantCore
from memory import Memory
from memory_ui import open_memory
from windows_launcher import create_shortcut
from diagnostics_ui import open_diagnostics

VERSION='0.5.4'
UPDATE_EXIT=42
BASE=Path(os.environ.get("JARVIS_DATA_DIR",str(Path(__file__).resolve().parent))).resolve()
CONFIG=BASE/'camera_config.json'

def preview_frame(frame,width,height):
    h,w=frame.shape[:2]; scale=min(1.,max(1,width)/w,max(1,height)/h)
    if scale>=1.: return frame,1.
    return cv2.resize(frame,(max(1,int(w*scale)),max(1,int(h*scale))),interpolation=cv2.INTER_AREA),scale

class Slot:
    def __init__(self,app,parent,num,config):
        self.app=app; self.num=num; self.config=config; self.capture=None; self.pending=None; self.fallback=None; self.generation=0; self.saved=False; self.boxes=[]; self.box_time=0.; self.photo=None; self.last_render=None; self.preview_fps=0.; self.render_count=0; self.render_start=time.monotonic(); self.last_status=0.
        self.panel=ttk.LabelFrame(parent,text=f'Cámara {num+1}',padding=6)
        self.index=tk.StringVar(value=str(config['index'])); self.res=tk.StringVar(value=config['resolution']); self.fmt=tk.StringVar(value=config['format']); self.fps=tk.StringVar(value=str(config['fps'])); self.status=tk.StringVar(value='Desactivada'); self.backend=tk.StringVar(value=config.get('backend','Automático'))
        self.panel.columnconfigure(0,weight=1); self.panel.rowconfigure(4,weight=1)
        row=ttk.Frame(self.panel); row.grid(row=0,column=0,sticky='ew');
        ttk.Label(row,text='Índice').pack(side='left'); cb=ttk.Combobox(row,textvariable=self.index,values=list(range(32)),width=4,state='readonly'); cb.pack(side='left',padx=3); cb.bind('<<ComboboxSelected>>',self.select_profile)
        ttk.Label(row,text='Resolución').pack(side='left'); ttk.Combobox(row,textvariable=self.res,values=list(MODES),width=14,state='readonly').pack(side='left',padx=3)
        row2=ttk.Frame(self.panel); row2.grid(row=1,column=0,sticky='ew',pady=4)
        ttk.Combobox(row2,textvariable=self.fmt,values=FORMATS,width=11,state='readonly').pack(side='left'); ttk.Combobox(row2,textvariable=self.fps,values=FPS,width=4,state='readonly').pack(side='left',padx=3); ttk.Label(row2,text='FPS').pack(side='left')
        ttk.Button(row2,text='Conectar',command=self.connect).pack(side='left',padx=4); ttk.Button(row2,text='Apagar',command=self.disable).pack(side='left')
        row3=ttk.Frame(self.panel); row3.grid(row=2,column=0,sticky='ew')
        ttk.Label(row3,text='Controlador').pack(side='left'); ttk.Combobox(row3,textvariable=self.backend,values=BACKENDS,state='readonly',width=18).pack(side='left',padx=3)
        ttk.Label(self.panel,textvariable=self.status,wraplength=310).grid(row=3,column=0,sticky='ew',pady=4)
        self.preview=tk.Label(self.panel,bg='#14191f',text='Cámara apagada',fg='white'); self.preview.grid(row=4,column=0,sticky='nsew')
    def select_profile(self,event=None):
        p=self.app.profiles.get(self.index.get())
        if p: self.res.set(p['resolution']); self.fmt.set(p['format']); self.fps.set(str(p['fps'])); self.backend.set(p.get('backend','Automático'))
    def set_controls(self,p):
        self.index.set(str(p['index'])); self.res.set(p['resolution']); self.fmt.set(p['format']); self.fps.set(str(p['fps'])); self.backend.set(p.get('backend','Automático'))
    def connect(self):
        target=dict(index=int(self.index.get()),resolution=self.res.get(),format=self.fmt.get(),fps=int(self.fps.get()),backend=self.backend.get())
        if self.app.in_use(self,target['index']):
            messagebox.showwarning('Cámara','Ese índice está siendo utilizado por la otra cámara. Apagala primero o elegí otro índice.'); return
        self.fallback=dict(self.config) if self.capture and self.capture.snapshot()[5] and target!=self.config else None
        self.request(target)
    def request(self,target):
        self.generation+=1; self.pending=target; self.saved=False; self.boxes=[]; self.box_time=0.; self.clear('Conectando…' if target else 'Cámara apagada')
        if self.capture: self.capture.stop.set()
        self.status.set('Cerrando conexión anterior…' if self.capture else ('Conectando…' if target else 'Desactivada'))
    def clear(self,text):
        self.photo=None; self.last_render=None; self.preview_fps=0.; self.render_count=0; self.render_start=time.monotonic(); self.last_status=0.; self.preview.configure(image='',text=text)
    def disable(self):
        self.fallback=None; self.request(None)
    def frame(self):
        if not self.capture or self.capture.stop.is_set() or self.pending is not None: return None
        frame,stamp,*_=self.capture.snapshot()
        return frame if frame is not None and time.monotonic()-stamp<2 else None
    def poll(self):
        if self.capture and not self.capture.thread.is_alive():
            _,_,_,status,_,_=self.capture.snapshot(); stopped=self.capture.stop.is_set(); self.capture=None
            if not stopped and self.pending is None:
                self.generation+=1; self.clear('Sin imagen'); self.status.set(status)
                if self.fallback:
                    prior=self.fallback; self.fallback=None
                    if not self.app.in_use(self,prior['index']):
                        self.set_controls(prior); self.pending=prior; self.status.set('Restaurando configuración anterior…')
        if self.capture is None and self.pending is not None:
            self.config=self.pending; self.pending=None; self.capture=Capture(self.config); self.status.set('Conectando…')
        if not self.capture or self.capture.stop.is_set():
            if not self.capture and self.pending is None and self.status.get().startswith('Cerrando'): self.status.set('Desactivada')
            return
        frame,stamp,fps,status,fmt,ready=self.capture.snapshot()
        if not ready or frame is None:
            if self.photo is not None:
                self.generation+=1;self.boxes=[];self.box_time=0.;self.clear('Esperando imagen…')
            self.status.set(status);return
        if not self.saved:
            self.saved=True; self.fallback=None; self.app.profiles[str(self.config['index'])]=dict(self.config); self.app.persist()
        now=time.monotonic(); h,w=frame.shape[:2]
        stale=now-stamp>=2
        if now-self.last_status>=.25 or self.last_render is None:
            self.last_status=now
            self.status.set(f'{w} × {h} efectivos | {fps:.1f} FPS captura | {fmt} ({self.capture.backend})\nVista: {self.preview_fps:.1f} FPS | Solicitado: {self.config["fps"]} FPS' + (' | señal demorada' if stale else ''))
        if stale:
            if self.photo is not None: self.clear('Esperando imagen…')
            return
        width=max(1,self.preview.winfo_width()); height=max(1,self.preview.winfo_height())
        overlays=self.app.detection_on and now-self.box_time<1.2
        key=(stamp,width,height,self.box_time if overlays else 0)
        if key==self.last_render: return
        display,scale=preview_frame(frame,width,height)
        if overlays:
            if display is frame: display=frame.copy()
            for (x1,y1,x2,y2),name,conf in self.boxes:
                x1,y1,x2,y2=(int(v*scale) for v in (x1,y1,x2,y2))
                cv2.rectangle(display,(x1,y1),(x2,y2),(90,220,90),2)
                cv2.putText(display,f'{name} {conf:.0%}',(x1,max(15,y1-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,(90,220,90),2)
        im=Image.fromarray(cv2.cvtColor(display,cv2.COLOR_BGR2RGB))
        self.photo=ImageTk.PhotoImage(im); self.preview.configure(image=self.photo,text='')
        self.last_render=key; self.render_count+=1
        if now-self.render_start>=1.:
            self.preview_fps=self.render_count/(now-self.render_start)
            self.render_count=0; self.render_start=now


class App:
    def __init__(self,root,index=None):
        self.root=root; self.closed=False; self.shutdown=Shutdown(); self.exit_guard=False; self.tick_id=None; self.results=queue.Queue(); self.ask_busy=False; self.detect_busy=False; self.detector=None; self.detection_on=False; self.detect_epoch=0; self.last_detection=0; self.listen_busy=False; self.speak_busy=False; self.stop_voice=threading.Event(); self.core=AssistantCore(ask_vision); self.conversation=self.core.conversation; self.wake_enabled=False; self.voice_epoch=0; self.pending_speech=None; self.followup=Followup();self.followup_request=None
        self.memory=Memory(CONFIG.parent/'jarvis_memory.sqlite3'); self.memory_window=None; self.diagnostics_window=None; self.speech_input_window=None; self.voice_output_window=None
        self.voice_settings_path=CONFIG.parent/'voice_preferences.json';self.voice_settings=voice_output.load(self.voice_settings_path)
        self.speech_path=CONFIG.parent/'speech_input.json';self.speech_settings=speech_input.load(self.speech_path)
        a,b,self.profiles=load_config(CONFIG)
        if index is not None: a=dict(self.profiles.get(str(index),a)); a['index']=index
        if b['index']==a['index']: b=dict(b,index=1 if a['index']!=1 else 0)
        self.persisted=[dict(a),dict(b)]
        root.title('JARVIS Vision V'+VERSION); root.geometry('1400x850'); root.minsize(1000,700); root.protocol('WM_DELETE_WINDOW',self.close)
        top=ttk.Frame(root,padding=12); top.pack(fill='x'); ttk.Label(top,text='JARVIS Vision  /  V'+VERSION,font=('Segoe UI',18,'bold')).pack(side='left'); ttk.Label(top,text='Procesamiento local · Micrófono opcional').pack(side='right'); self.update_requested=False
        if os.environ.get('JARVIS_MANAGED')=='1': ttk.Button(top,text='Actualizaciones',command=self.open_updates).pack(side='right',padx=10)
        ttk.Button(top,text='Memoria y personalidad',command=self.show_memory).pack(side='right',padx=6)
        menu=tk.Menu(root); tools=tk.Menu(menu,tearoff=False)
        tools.add_command(label='Diagnóstico de JARVIS',command=self.show_diagnostics)
        tools.add_command(label='Micrófono y reconocimiento',command=self.show_speech_input)
        tools.add_command(label='Configurar voz',command=self.show_voice_output)
        if os.name=='nt' and os.environ.get('JARVIS_MANAGED')=='1':
            tools.add_command(label='Crear acceso directo de JARVIS',command=self.make_shortcut)
        menu.add_cascade(label='Herramientas',menu=tools); root.configure(menu=menu)
        main=ttk.Frame(root,padding=(12,0,12,12)); main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1,uniform='camera'); main.columnconfigure(1,weight=1,uniform='camera'); main.columnconfigure(2,weight=1); main.rowconfigure(0,weight=1)
        self.slots=[Slot(self,main,0,a),Slot(self,main,1,b)]
        for i,s in enumerate(self.slots): s.panel.grid(row=0,column=i,sticky='nsew',padx=(0,8))
        side=ttk.Frame(main); side.grid(row=0,column=2,sticky='nsew');
        ttk.Label(side,text='Asistente visual',font=('Segoe UI',14,'bold')).pack(anchor='w')
        self.source=tk.StringVar(value='Cámara 1'); ttk.Label(side,text='Cámara para IA y foto').pack(anchor='w',pady=(8,0)); cb=ttk.Combobox(side,textvariable=self.source,values=['Cámara 1','Cámara 2'],state='readonly'); cb.pack(fill='x'); cb.bind('<<ComboboxSelected>>',self.source_changed)
        self.dbutton=ttk.Button(side,text='Activar detección YOLO',command=self.toggle); self.dbutton.pack(fill='x',pady=(8,0)); self.dstatus=tk.StringVar(value='Detección desactivada'); ttk.Label(side,textvariable=self.dstatus,wraplength=290).pack(fill='x',pady=4)
        ttk.Button(side,text='Guardar foto local',command=self.save).pack(fill='x'); ttk.Separator(side).pack(fill='x',pady=10)
        self.question=ttk.Entry(side); self.question.pack(fill='x'); self.question.insert(0,'¿Qué ves delante de la cámara?'); self.question.bind('<Return>',lambda _:self.ask())
        self.mode=tk.StringVar(value='Visual'); ttk.Combobox(side,textvariable=self.mode,values=['Visual','Conversación sin cámara'],state='readonly').pack(fill='x',pady=3)
        self.abutton=ttk.Button(side,text='Enviar pregunta',command=self.ask); self.abutton.pack(fill='x',pady=4)
        self.context_on=tk.BooleanVar(value=True); ttk.Checkbutton(side,text='Contexto de esta sesión',variable=self.context_on,command=self.clear_context).pack(anchor='w'); ttk.Button(side,text='Nueva conversación / borrar contexto',command=self.clear_context).pack(fill='x',pady=2)
        self.natural_turn=tk.BooleanVar(value=False)
        ttk.Checkbutton(side,text='Terminar al detectar una pausa',variable=self.natural_turn,command=self.update_voice_button).pack(anchor='w')
        self.vbutton=ttk.Button(side,text='Hablar (6 s)',command=self.listen); self.vbutton.pack(fill='x'); ttk.Button(side,text='Cancelar micrófono',command=self.cancel_voice).pack(fill='x',pady=3)
        self.auto_ask=tk.BooleanVar(value=False); ttk.Checkbutton(side,text='Analizar automáticamente al hablar',variable=self.auto_ask).pack(anchor='w')
        self.bare_wake=tk.BooleanVar(value=False)
        self.bare_check=ttk.Checkbutton(side,text='Permitir también «JARVIS» solo',variable=self.bare_wake); self.bare_check.pack(anchor='w')
        self.wbutton=ttk.Button(side,text='Activar «Hola, JARVIS»',command=self.toggle_wake); self.wbutton.pack(fill='x',pady=3)
        self.followup_on=tk.BooleanVar(value=False)
        ttk.Checkbutton(side,text='Continuar conversación (máx. 5 turnos)',variable=self.followup_on,command=self.change_followup).pack(anchor='w')
        self.auto_speak=tk.BooleanVar(value=False); ttk.Checkbutton(side,text='Leer respuestas en voz alta',variable=self.auto_speak).pack(anchor='w'); self.vstatus=tk.StringVar(value='Voz opcional · sin escucha permanente'); ttk.Label(side,textvariable=self.vstatus,wraplength=290).pack(fill='x',pady=4)
        ttk.Label(side,text='Ollama local · imágenes solo a pedido. Voz continua solo si la activás.',wraplength=290).pack(fill='x')
        self.answer=tk.Text(side,wrap='word',height=8,width=30,font=('Segoe UI',10)); self.answer.pack(fill='both',expand=True); self.write('Conectá una cámara. Para preguntas instalá Ollama y gemma3:4b. Para voz, ver VOZ.txt.')
        self.slots[0].connect(); self.tick_id=self.root.after(15,self.tick)
    def show_voice_output(self):
        if self.voice_output_window is not None and self.voice_output_window.winfo_exists():
            self.voice_output_window.lift();return
        def apply(settings):
            voice_output.save(self.voice_settings_path,settings);self.voice_settings=settings
        self.voice_output_window=open_voice_output(self.root,CONFIG.parent,self.voice_settings,apply,
            lambda settings:self.speak('Hola. Soy JARVIS, tu asistente personal.',settings),
            lambda:self.closed or self.listen_busy or self.speak_busy or self.ask_busy or self.wake_enabled)
    def show_speech_input(self):
        if self.speech_input_window is not None and self.speech_input_window.winfo_exists():
            self.speech_input_window.lift();return
        def apply(settings):
            speech_input.save(self.speech_path,settings);self.speech_settings=settings
        try:self.speech_input_window=open_speech_input(self.root,CONFIG.parent,self.speech_settings,apply,
            lambda settings:self.listen(test_settings=settings),lambda:self.listen_busy or self.speak_busy or self.ask_busy or self.wake_enabled)
        except Exception as e:messagebox.showerror('Micrófono',str(e),parent=self.root)
    def show_diagnostics(self):
        if self.diagnostics_window is not None and self.diagnostics_window.winfo_exists():
            self.diagnostics_window.lift(); return
        def status():
            return [(f'Cámara {s.num+1}',s.status.get().split('\n')[0]) for s in self.slots]+[
                ('Micrófono','En uso' if self.listen_busy else 'Inactivo'),
                ('Activación por voz','Habilitada' if self.wake_enabled else 'Desactivada')]
        self.diagnostics_window=open_diagnostics(self.root,BASE,VERSION,status,start_worker=self.shutdown.start)
    def make_shortcut(self):
        if not messagebox.askyesno('Acceso directo','¿Crear o reemplazar el acceso directo JARVIS en el escritorio? Mantendrá el gestor de actualizaciones.',parent=self.root): return
        try:
            create_shortcut(BASE)
            messagebox.showinfo('Acceso directo','Acceso directo JARVIS creado. Usalo para abrir la aplicación sin una consola permanente.',parent=self.root)
        except Exception as e: messagebox.showerror('Acceso directo',str(e),parent=self.root)
    def show_memory(self):
        if self.memory_window is not None and self.memory_window.winfo_exists():
            self.memory_window.lift(); return
        try: self.memory_window=open_memory(self.root,self.memory,self.clear_context)
        except Exception as e: messagebox.showerror('Memoria',str(e),parent=self.root)
    def in_use(self,slot,index):
        return any(s is not slot and ((s.capture is not None and s.capture.config['index']==index) or (s.pending is not None and s.pending['index']==index)) for s in self.slots)
    def persist(self):
        for i,s in enumerate(self.slots):
            if s.saved: self.persisted[i]=dict(s.config)
        try: save_config(CONFIG,*self.persisted,self.profiles)
        except OSError as e: self.vstatus.set('No se pudieron guardar preferencias: '+str(e))
    def active(self): return self.slots[0 if self.source.get()=='Cámara 1' else 1]
    def source_changed(self,event=None):
        self.detect_epoch+=1
        for s in self.slots: s.boxes=[]; s.box_time=0.
        self.dstatus.set('Esperando detección…' if self.detection_on else 'Detección desactivada')
    def write(self,text):
        self.answer.configure(state='normal'); self.answer.delete('1.0','end'); self.answer.insert('1.0',text); self.answer.configure(state='disabled')
    def toggle(self):
        self.detection_on=not self.detection_on; self.source_changed(); self.dbutton.configure(text='Desactivar detección' if self.detection_on else 'Activar detección YOLO')
    def detect(self,frame,slot,gen,epoch):
        try:
            if self.detector is None:
                from ultralytics import YOLO,settings
                settings.update({'sync':False}); self.detector=YOLO(str(BASE/'yolo11n.pt'))
            result=self.detector.predict(frame,imgsz=416,conf=.45,verbose=False)[0]
            boxes=[(tuple(map(int,b.xyxy[0].tolist())),result.names[int(b.cls.item())],float(b.conf.item())) for b in result.boxes]
            self.results.put(('detect',slot,gen,epoch,boxes,None))
        except Exception as e: self.results.put(('detect',slot,gen,epoch,[],str(e)))
    def change_followup(self):
        self.followup.reset();self.followup_request=None
        if self.listen_busy and getattr(self,'listening_followup',False):
            self.stop_voice.set();self.voice_epoch+=1
    def clear_context(self):
        self.change_followup();self.core.clear(); self.pending_speech=None; self.write('Contexto borrado. Nueva conversación.')
    def ask(self,follow_epoch=None):
        if self.closed or self.ask_busy: return False
        if follow_epoch is None:self.change_followup()
        s=self.active(); visual=self.mode.get()=='Visual'; frame=s.frame() if visual else None; question=self.question.get().strip()
        if visual and frame is None: self.write('Conectá la cámara seleccionada o elegí Conversación sin cámara.'); return False
        if not question: return False
        # Stop recording before inference; defer speech until the stream is closed.
        if self.listen_busy:
            self.stop_voice.set(); self.voice_epoch+=1
        self.ask_busy=True; self.abutton.configure(state='disabled'); source=f'Cámara {s.num+1}' if visual else 'Sin cámara'; self.write(f'{source}: procesando…'); gen=s.generation
        try: style,memories=self.memory.snapshot(question)
        except Exception as e:
            self.ask_busy=False; self.abutton.configure(state='normal'); self.write('No se pudo leer la memoria: '+str(e)); return False
        request=self.core.prepare(question,source,frame,self.context_on.get(),style,memories if self.context_on.get() else ())
        self.followup_request=follow_epoch
        def work():
            try: self.results.put(('ask',s.num if visual else None,gen,self.core.answer(request),None,request))
            except Exception as e: self.results.put(('ask',s.num if visual else None,gen,'',str(e),request))
        self.shutdown.start(work)
        return True
    def cancel_voice(self):
        self.change_followup()
        self.wake_enabled=False; self.bare_check.configure(state='normal'); self.voice_epoch+=1; self.stop_voice.set(); self.pending_speech=None; self.wbutton.configure(text='Activar «Hola, JARVIS»'); self.vstatus.set('Micrófono desactivado; cerrando escucha si estaba activa.')
    def toggle_wake(self):
        if self.wake_enabled: self.cancel_voice(); return
        self.wake_enabled=True; self.bare_check.configure(state='disabled'); self.auto_speak.set(True); self.wbutton.configure(text='Desactivar «Hola, JARVIS»'); self.vstatus.set('Activación habilitada; preparando micrófono…')
    def update_voice_button(self):
        self.vbutton.configure(text='Hablar (hasta 12 s)' if self.natural_turn.get() else 'Hablar (6 s)')
    def listen(self, wake=False, test_settings=None, follow=False):
        if self.closed or self.listen_busy or self.speak_busy or self.ask_busy: return
        if not wake and not follow and self.wake_enabled: return
        if follow and not (self.wake_enabled and self.followup_on.get()):return
        self.listening_followup=follow
        self.listen_busy=True; self.stop_voice.clear(); self.voice_epoch+=1; epoch=self.voice_epoch; self.vbutton.configure(state='disabled'); self.vstatus.set('Preparando micrófono…')
        testing=test_settings is not None
        selected=dict(test_settings if testing else self.speech_settings)
        options={'settings':selected,'base':CONFIG.parent} if selected!=speech_input.DEFAULT or testing else {}
        natural=self.natural_turn.get() and not wake and not testing and selected['model']!='Whisper small'
        if not wake and selected['model']=='Whisper small':options['on_processing']=lambda:self.results.put(('mic_state',epoch,'Whisper local: transcribiendo audio…'))
        bare=self.bare_wake.get() and wake
        def work():
            try:
                if wake:
                    wake_options=dict(options)
                    if bare:wake_options['allow_bare']=True
                    text=voice.listen_wake(self.stop_voice,on_state=lambda state:self.results.put(('mic_state',epoch,state)),**wake_options)
                elif follow:
                    text=voice.listen(self.stop_voice,seconds=8,end_on_phrase=selected['model']!='Whisper small',on_ready=lambda:self.results.put(('mic_state',epoch,'Conversación activa · hablá ahora (hasta 8 s)')),**options)
                elif natural: text=voice.listen(self.stop_voice,seconds=12,end_on_phrase=True,on_ready=lambda:self.results.put(('mic_state',epoch,'Micrófono activo: hablá y hacé una pausa al terminar (máx. 12 s).')),**options)
                else: text=voice.listen(self.stop_voice,on_ready=lambda:self.results.put(('mic_state',epoch,'Micrófono activo: hablá ahora (6 segundos).')),**options)
                self.results.put(('voice_test' if testing else ('voice_followup' if follow else 'voice'),epoch,wake,text,None))
            except Exception as e: self.results.put(('voice_test' if testing else ('voice_followup' if follow else 'voice'),epoch,wake,'',str(e)))
        self.shutdown.start(work)
    def speak(self,text,settings=None):
        if self.closed or self.speak_busy or self.listen_busy: return
        selected=dict(self.voice_settings if settings is None else settings)
        self.speak_busy=True; self.vstatus.set('Leyendo respuesta…')
        def work():
            try: voice_output.speak(CONFIG.parent,selected,text); self.results.put(('spoken',None))
            except Exception as e: self.results.put(('spoken',str(e)))
        self.shutdown.start(work)
    def save(self):
        s=self.active(); frame=s.frame()
        if frame is None: messagebox.showwarning('Cámara','Conectá la cámara seleccionada primero.'); return
        try:
            path=BASE/'capturas'; path.mkdir(exist_ok=True); file=path/f'jarvis_cam{s.config["index"]}_{datetime.now():%Y%m%d_%H%M%S_%f}.jpg'; ok,data=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,95]);
            if not ok: raise RuntimeError('No se pudo codificar la foto.')
            file.write_bytes(data.tobytes()); messagebox.showinfo('Foto guardada',str(file))
        except Exception as e: messagebox.showerror('Error',str(e))
    def tick(self):
        if self.closed: return
        if os.environ.get('JARVIS_MANAGED')=='1':
            now=time.monotonic()
            if now-getattr(self,'last_focus_poll',0.)>=.25:
                self.last_focus_poll=now
                poll_focus(self.root,BASE/'.jarvis')
        for s in self.slots: s.poll()
        while True:
            try: result=self.results.get_nowait()
            except queue.Empty: break
            kind,*r=result
            if kind=='detect':
                self.detect_busy=False; slot,gen,epoch,boxes,error=r; s=self.slots[slot]
                if self.detection_on and s is self.active() and gen==s.generation and epoch==self.detect_epoch:
                    if error: self.toggle(); self.dstatus.set('Error YOLO: '+error)
                    else: s.boxes=boxes; s.box_time=time.monotonic(); self.dstatus.set(', '.join(f'{name} ({conf:.0%})' for _,name,conf in boxes) or 'Sin objetos reconocidos')
            elif kind=='ask':
                self.ask_busy=False; self.abutton.configure(state='normal'); slot,gen,text,error,request=r
                follow_epoch=self.followup_request;self.followup_request=None
                if request.epoch!=self.conversation.epoch: continue
                source=request.source
                if slot is not None and gen!=self.slots[slot].generation: self.write('Captura descartada: cambió o se apagó la cámara.'); continue
                self.write(f'{source}:\n'+(text if not error else 'Error: '+error+'\nComprobá Ollama y gemma3:4b.'))
                if not error:
                    self.core.accept(request,text,self.context_on.get())
                    if self.auto_speak.get(): self.pending_speech=text
                    if self.wake_enabled and self.followup_on.get():self.followup.accepted(follow_epoch)
                else:self.followup.reset()
            elif kind=='mic_state':
                epoch,state=r
                if epoch==self.voice_epoch and not self.stop_voice.is_set(): self.vstatus.set(state)
            elif kind in ('voice','voice_test','voice_followup'):
                self.listen_busy=False; self.listening_followup=False; self.vbutton.configure(state='normal'); epoch,wake,text,error=r
                if epoch!=self.voice_epoch or self.stop_voice.is_set(): continue
                if error:
                    if wake or kind=='voice_followup': self.cancel_voice()
                    self.vstatus.set('Error de voz: '+error)
                elif text:
                    if kind!='voice_test' and (wake or kind=='voice_followup') and stop_phrase(text):
                        self.cancel_voice();self.vstatus.set('Conversación y micrófono desactivados.');continue
                    self.question.delete(0,'end'); self.question.insert(0,text); self.vstatus.set('Pregunta reconocida.')
                    if kind=='voice_test':self.vstatus.set('Prueba de micrófono: transcripción lista, sin consulta a IA.')
                    elif wake or kind=='voice_followup':
                        token=self.followup.initial() if wake and self.followup_on.get() else (self.followup.epoch if kind=='voice_followup' else None)
                        if not self.ask(follow_epoch=token):self.followup.reset()
                    elif self.auto_ask.get():self.ask()
                else:
                    if kind=='voice_followup':self.followup.reset()
                    self.vstatus.set('No se reconoció voz. Probá nuevamente.')
            elif kind=='spoken':
                self.speak_busy=False; self.vstatus.set('Error de voz: '+r[0] if r[0] else 'Respuesta leída')
                if r[0]:self.followup.reset()
        if self.pending_speech is not None and not (self.listen_busy or self.speak_busy):
            text=self.pending_speech; self.pending_speech=None; self.speak(text)
        if self.wake_enabled and not (self.listen_busy or self.ask_busy or self.speak_busy):
            if self.followup_on.get() and self.followup.take():self.listen(follow=True)
            else:self.listen(wake=True)
        s=self.active(); frame=s.frame(); now=time.monotonic()
        if self.detection_on and frame is not None and not self.detect_busy and now-self.last_detection>.65:
            self.detect_busy=True; self.last_detection=now; self.shutdown.start(self.detect,(frame.copy(),s.num,s.generation,self.detect_epoch))
        self.tick_id=self.root.after(15,self.tick)
    def open_updates(self):
        if messagebox.askyesno('Actualizaciones','Se cerrará la sesión actual para abrir el gestor. Las preferencias y archivos locales se conservarán. ¿Continuar?'):
            self.update_requested=True; self.close()
    def close(self):
        if self.closed:return
        self.closed=True; self.wake_enabled=False; self.followup.reset();self.followup_request=None;self.pending_speech=None; self.voice_epoch+=1
        captures=[s.capture for s in self.slots if s.capture]
        self.shutdown.begin([self.stop_voice]+[c.stop for c in captures],[c.thread for c in captures],
                            exit_code=(UPDATE_EXIT if self.update_requested else 0) if self.exit_guard else None)
        if self.tick_id is not None:
            try:self.root.after_cancel(self.tick_id)
            except tk.TclError:pass
        self.root.destroy()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--camera',type=int,default=None,choices=range(32)); args=parser.parse_args(); root=tk.Tk(); app=App(root,args.camera); app.exit_guard=True
    try:root.mainloop()
    finally:
        if not app.closed:app.close()
        app.shutdown.wait(2)
    return UPDATE_EXIT if app.update_requested else 0
if __name__=='__main__':
    # All persistent user writes are synchronous; bounded worker cleanup precedes exit.
    # Avoid native library/interpreter finalization hanging after the GUI is gone.
    os._exit(main())
