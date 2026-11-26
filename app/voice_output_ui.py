"""Configure optional voice engine without starting microphone or downloading files."""
import tkinter as tk
from tkinter import ttk,messagebox
import voice_output

def open_voice_output(root,base,settings,apply,preview,busy):
    win=tk.Toplevel(root);win.title('Voz de JARVIS');win.resizable(False,False)
    frame=ttk.Frame(win,padding=14);frame.pack(fill='both',expand=True)
    engine=tk.StringVar(value=settings['engine']);model=tk.StringVar(value=settings['model'])
    ttk.Label(frame,text='Motor de voz').pack(anchor='w')
    ttk.Combobox(frame,textvariable=engine,values=voice_output.ENGINES,state='readonly').pack(fill='x')
    ttk.Label(frame,text='Modelo neuronal local (opcional)').pack(anchor='w',pady=(10,0))
    choices=ttk.Combobox(frame,textvariable=model,values=voice_output.models(base),state='readonly');choices.pack(fill='x')
    ttk.Button(frame,text='Actualizar lista de modelos',command=lambda:choices.configure(values=voice_output.models(base))).pack(fill='x',pady=4)
    ttk.Label(frame,text='Sistema conserva la voz actual. Piper requiere instalación separada y un modelo ONNX + JSON de origen confiable en modelos/piper. No se descarga nada.',wraplength=360).pack(pady=8)
    def selected():
        settings=voice_output.normalize({'engine':engine.get(),'model':model.get()})
        if settings['engine']=='Piper local':voice_output.model_info(base,settings['model'])
        return settings
    def run(test=False):
        if busy():
            messagebox.showinfo('Voz','Terminá la escucha o reproducción actual antes de cambiar la voz.',parent=win);return
        try:
            choice=selected()
            if test:preview(choice)
            else:apply(choice);win.destroy()
        except Exception as e:messagebox.showerror('Voz',str(e),parent=win)
    ttk.Button(frame,text='Probar voz',command=lambda:run(True)).pack(fill='x')
    ttk.Button(frame,text='Guardar',command=run).pack(fill='x',pady=4)
    return win
