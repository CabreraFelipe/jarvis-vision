import queue
import threading
import tkinter as tk
from tkinter import ttk
from diagnostics import collect

def open_diagnostics(parent,base,version,device_status,start_worker=None):
    win=tk.Toplevel(parent); win.title('JARVIS · Diagnóstico'); win.geometry('650x490'); win.transient(parent)
    panel=ttk.Frame(win,padding=12); panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Diagnóstico local',font=('Segoe UI',16,'bold')).pack(anchor='w')
    ttk.Label(panel,text='Comprobación de instalación y estado actual. No activa cámaras ni micrófono; no envía información fuera del PC.',wraplength=600).pack(anchor='w',pady=6)
    table=ttk.Treeview(panel,columns=('status',),show='tree headings'); table.heading('#0',text='Componente'); table.heading('status',text='Estado'); table.column('#0',width=200); table.column('status',width=330); table.pack(fill='both',expand=True)
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
    button.configure(command=start); button.pack(anchor='w',pady=8)
    start()
    return win
