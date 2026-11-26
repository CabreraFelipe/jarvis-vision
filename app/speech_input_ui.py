"""Explicit microphone selection, model selection and speech-only test."""
import tkinter as tk
from tkinter import ttk,messagebox
import speech_input

def open_speech_input(root,base,settings,apply,test,busy):
    import sounddevice as sd
    choices=[None]+speech_input.inputs(sd)
    labels=['Predeterminado de Windows']+[f"{d['index']} · {d['name']} ({d['host']})" for d in choices[1:]]
    win=tk.Toplevel(root);win.title('Micrófono y reconocimiento');win.resizable(False,False)
    panel=ttk.Frame(win,padding=12);panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Micrófono').pack(anchor='w')
    combo=ttk.Combobox(panel,values=labels,state='readonly',width=65);combo.pack(fill='x')
    if settings['device'] in choices:combo.current(choices.index(settings['device']))
    model=tk.StringVar(value=settings['model'])
    ttk.Label(panel,text='Modelo español Vosk').pack(anchor='w',pady=(8,0))
    ttk.Combobox(panel,textvariable=model,values=list(speech_input.MODELS),state='readonly').pack(fill='x')
    ttk.Label(panel,text='Completo: requiere descargar y extraer vosk-model-es-0.42 en modelos. Ligero conserva el modelo actual. La prueba solo transcribe; no envía consultas a la IA.',wraplength=440).pack(pady=8)
    def run(preview=False):
        if busy():
            messagebox.showinfo('Micrófono','Detené la escucha continua y esperá a que termine la respuesta.',parent=win);return
        if combo.current()<0:
            messagebox.showerror('Micrófono','Elegí una entrada disponible.',parent=win);return
        selected=speech_input.normalize({'model':model.get(),'device':choices[combo.current()]})
        if not speech_input.model_path(base,selected['model']).is_dir():
            messagebox.showerror('Modelo','No está instalado el modelo elegido. Consultá VOZ.txt.',parent=win);return
        try:
            if preview:test(selected)
            else:apply(selected)
            win.destroy()
        except Exception as e:messagebox.showerror('Micrófono',str(e),parent=win)
    ttk.Button(panel,text='Probar transcripción (6 s)',command=lambda:run(True)).pack(fill='x')
    ttk.Button(panel,text='Guardar',command=run).pack(fill='x',pady=4)
    return win
