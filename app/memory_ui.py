"""Memory controls; explicitly authored notes only."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from memory import STYLES

def open_memory(parent,store,on_change):
    win=tk.Toplevel(parent); win.title('JARVIS · Memoria y personalidad'); win.geometry('590x460'); win.transient(parent)
    panel=ttk.Frame(win,padding=14); panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Memoria local y personalidad',font=('Segoe UI',16,'bold')).pack(anchor='w')
    ttk.Label(panel,text='Solo se guardan las notas que agregues. No se graban conversaciones, imágenes ni audio. La base local no está cifrada.',wraplength=540).pack(anchor='w',pady=6)
    enabled,style=store.settings(); use=tk.BooleanVar(value=enabled); tone=tk.StringVar(value=style)
    def guard(fn):
        try: fn()
        except Exception as e: messagebox.showerror('Memoria',str(e),parent=win)
    def settings():
        store.configure(use.get(),tone.get()); on_change()
    ttk.Checkbutton(panel,text='Usar recuerdos en nuevas respuestas',variable=use,command=lambda:guard(settings)).pack(anchor='w')
    ttk.Label(panel,text='Estilo de respuesta').pack(anchor='w',pady=(8,0))
    combo=ttk.Combobox(panel,values=STYLES,textvariable=tone,state='readonly'); combo.pack(fill='x')
    combo.bind('<<ComboboxSelected>>',lambda _:guard(settings))
    box=tk.Listbox(panel,exportselection=False); box.pack(fill='both',expand=True,pady=10)
    entries=[]
    def refresh():
        entries[:]=store.items(); box.delete(0,'end')
        for _,text in entries: box.insert('end',text)
    def add():
        text=simpledialog.askstring('Nuevo recuerdo','¿Qué querés que JARVIS recuerde? (máx. 300 caracteres)',parent=win)
        if text is not None:
            store.add(text); on_change(); refresh()
    def delete():
        selection=box.curselection()
        if selection:
            store.remove(entries[selection[0]][0]); on_change(); refresh()
    def clear():
        if messagebox.askyesno('Borrar recuerdos','¿Eliminar todas las notas guardadas? No se borran otros archivos.',parent=win):
            store.clear(); on_change(); refresh()
    row=ttk.Frame(panel); row.pack(fill='x')
    for label,fn in [('Agregar',add),('Eliminar seleccionado',delete),('Borrar todos',clear)]:
        ttk.Button(row,text=label,command=lambda f=fn:guard(f)).pack(side='left',padx=3)
    ttk.Button(row,text='Cerrar',command=win.destroy).pack(side='right')
    guard(refresh)
    return win
