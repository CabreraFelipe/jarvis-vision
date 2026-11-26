import queue
import threading
import tkinter as tk
from tkinter import ttk
from diagnostics import collect,voice_install_commands

def open_diagnostics(parent,base,version,device_status,start_worker=None):
    win=tk.Toplevel(parent); win.title('JARVIS · Diagnóstico'); win.geometry('650x490'); win.transient(parent)
    panel=ttk.Frame(win,padding=12); panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Diagnóstico local',font=('Segoe UI',16,'bold')).pack(anchor='w')
    ttk.Label(panel,text='Comprobación de instalación y estado actual. No activa cámaras ni micrófono; no envía información fuera del PC.',wraplength=600).pack(anchor='w',pady=6)
    table=ttk.Treeview(panel,columns=('status',),show='tree headings'); table.heading('#0',text='Componente'); table.heading('status',text='Estado'); table.column('#0',width=200); table.column('status',width=330); table.pack(fill='both',expand=True)
    scroll=ttk.Scrollbar(panel,orient='horizontal',command=table.xview);scroll.pack(fill='x')
    table.configure(xscrollcommand=scroll.set);table.column('status',width=650,stretch=False)
    results=queue.Queue(); button=ttk.Button(panel,text='Comprobar')
    def start():
        button.configure(state='disabled')
        for item in table.get_children(): table.delete(item)
        current=device_status()
        def work():
            try: results.put(current+collect(base,version))
            except Exception: results.put(current+[('Diagnóstico','No se pudo completar')])
        if start_worker is None:threading.Thread(target=work,daemon=True).start()
        else:start_worker(work)
        win.after(50,poll)
    def poll():
        if not win.winfo_exists(): return
        try: rows=results.get_nowait()
        except queue.Empty: win.after(50,poll); return
        for label,status in rows: table.insert('','end',text=label,values=(status,))
        button.configure(state='normal')
    def guide():
        helpwin=tk.Toplevel(win);helpwin.title('Preparar voz local');helpwin.geometry('760x480');helpwin.transient(win)
        frame=ttk.Frame(helpwin,padding=12);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Instalación manual en PowerShell',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(frame,text='No se ejecutan instalaciones desde JARVIS. Python 3.12 de 64 bits en un entorno virtual es la base comprobada. Respaldá tus datos, cerrá JARVIS y ejecutá solo los comandos necesarios, de uno en uno. Si falla, no continúes.',wraplength=700).pack(anchor='w',pady=8)
        commands=voice_install_commands()
        for label,command in commands:
            row=ttk.Frame(frame);row.pack(fill='x',pady=3)
            ttk.Label(row,text=label,width=24).pack(side='left')
            entry=ttk.Entry(row);entry.insert(0,command);entry.configure(state='readonly');entry.pack(side='left',fill='x',expand=True)
            def copy(value=command):
                helpwin.clipboard_clear();helpwin.clipboard_append(value)
                status.set('Comando copiado; no ejecutado.')
            ttk.Button(row,text='Copiar',command=copy).pack(side='left',padx=4)
        status=tk.StringVar(value='Ningún comando ejecutado.')
        ttk.Label(frame,textvariable=status).pack(anchor='w',pady=4)
        ttk.Label(frame,text='Carpeta de datos (conservar): '+str(base),wraplength=700).pack(anchor='w',pady=4)
        ttk.Label(frame,text='Whisper: modelos/faster-whisper-small (Systran, multilingüe). Piper: modelos/piper (ONNX y JSON coincidentes). Vosk: conservar el modelo ligero. Revisá origen y licencia de cada modelo; no reemplaces los existentes. Ver VOZ.txt. Los archivos presentes no garantizan que el motor pueda cargarlos.',wraplength=700).pack(anchor='w',pady=4)
    controls=ttk.Frame(panel);controls.pack(fill='x',pady=8)
    button.configure(command=start); button.pack(anchor='w',in_=controls,side='left')
    ttk.Button(controls,text='Guía de instalación de voz',command=guide).pack(side='left',padx=8)
    start()
    return win
