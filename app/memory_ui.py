"""Memory controls; explicitly authored notes only."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from memory import STYLES
from personality import OPTIONS,DEFAULT

def open_memory(parent,store,on_change):
    win=tk.Toplevel(parent); win.title('JARVIS · Memoria y personalidad'); win.geometry('640x540'); win.transient(parent)
    panel=ttk.Frame(win,padding=14); panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Memoria local y personalidad',font=('Segoe UI',16,'bold')).pack(anchor='w')
    ttk.Label(panel,text='Solo se guardan las notas que agregues. No se graban conversaciones, imágenes ni audio. La base local no está cifrada.',wraplength=540).pack(anchor='w',pady=6)
    enabled,style=store.settings(); use=tk.BooleanVar(value=enabled); tone=tk.StringVar(value=style)
    semantic=tk.BooleanVar(value=store.semantic_enabled())
    learning=tk.BooleanVar(value=store.suggestions_enabled())
    def guard(fn):
        try: fn()
        except Exception as e: messagebox.showerror('Memoria',str(e),parent=win)
    def settings():
        if not use.get(): semantic.set(False);learning.set(False)
        store.configure(use.get(),tone.get(),semantic.get(),suggestions=learning.get()); on_change()
    ttk.Checkbutton(panel,text='Usar recuerdos en nuevas respuestas',variable=use,command=lambda:guard(settings)).pack(anchor='w')
    def toggle_semantic():
        if semantic.get() and (not use.get() or not messagebox.askyesno('Memoria semántica','¿Permitir que Ollama local compare tu pregunta con todas las notas guardadas? Requiere bge-m3 instalado explícitamente. No se guardan embeddings ni conversaciones. Si falla, se usa búsqueda por palabras.',parent=win)):
            semantic.set(False)
        settings()
    ttk.Checkbutton(panel,text='Recuperación semántica local (experimental)',variable=semantic,command=lambda:guard(toggle_semantic)).pack(anchor='w')
    def toggle_learning():
        if learning.get() and (not use.get() or not messagebox.askyesno('Sugerencias de recuerdos','¿Permitir sugerencias locales al expresar preferencias? Solo se guarda una nota si la revisás y confirmás. No se guardan conversaciones.',parent=win)):
            learning.set(False)
        settings()
    ttk.Checkbutton(panel,text='Sugerir recuerdos de preferencias (opcional)',variable=learning,command=lambda:guard(toggle_learning)).pack(anchor='w')
    ttk.Label(panel,text='Estilo de respuesta').pack(anchor='w',pady=(8,0))
    combo=ttk.Combobox(panel,values=STYLES,textvariable=tone,state='readonly'); combo.pack(fill='x')
    combo.bind('<<ComboboxSelected>>',lambda _:guard(settings))
    def profile_window():
        dialog=tk.Toplevel(win);dialog.title('Personalidad avanzada');dialog.transient(win)
        frame=ttk.Frame(dialog,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Las preferencias modifican las respuestas, no autorizan acciones.').pack(anchor='w',pady=4)
        variables=[]
        for (label,choices),value in zip(OPTIONS,store.personality()):
            ttk.Label(frame,text=label).pack(anchor='w',pady=(6,0))
            var=tk.StringVar(value=value);variables.append(var)
            ttk.Combobox(frame,textvariable=var,values=choices,state='readonly').pack(fill='x')
        def reset():
            for var,value in zip(variables,DEFAULT):var.set(value)
        def save_profile():
            if not messagebox.askyesno('Personalidad','¿Guardar estas preferencias?',parent=dialog):return
            try:store.set_personality(tuple(v.get() for v in variables));on_change();dialog.destroy()
            except Exception as e:messagebox.showerror('Personalidad',str(e),parent=dialog)
        row=ttk.Frame(frame);row.pack(fill='x',pady=(12,0))
        ttk.Button(row,text='Restablecer selección',command=reset).pack(side='left')
        ttk.Button(row,text='Guardar',command=save_profile).pack(side='right')
        dialog.grab_set()
    ttk.Button(panel,text='Personalidad avanzada',command=lambda:guard(profile_window)).pack(fill='x',pady=4)
    query=tk.StringVar(); ttk.Label(panel,text='Buscar recuerdos').pack(anchor='w',pady=(8,0)); ttk.Entry(panel,textvariable=query).pack(fill='x')
    box=tk.Listbox(panel,exportselection=False); box.pack(fill='both',expand=True,pady=10)
    entries=[]
    def refresh():
        entries[:]=store.search(query.get()); box.delete(0,'end')
        for _,text in entries: box.insert('end',text)
    def add():
        text=simpledialog.askstring('Nuevo recuerdo','¿Qué querés que JARVIS recuerde? (máx. 300 caracteres)',parent=win)
        if text is not None:
            store.add(text); on_change(); refresh()
    def edit():
        selection=box.curselection()
        if selection:
            note_id,prior=entries[selection[0]]
            text=simpledialog.askstring('Editar recuerdo','Nuevo texto (máx. 300 caracteres)',initialvalue=prior,parent=win)
            if text is not None: store.edit(note_id,text); on_change(); refresh()
    def delete():
        selection=box.curselection()
        if selection:
            store.remove(entries[selection[0]][0]); on_change(); refresh()
    def clear():
        if messagebox.askyesno('Borrar recuerdos','¿Eliminar todas las notas guardadas? No se borran otros archivos.',parent=win):
            store.clear(); on_change(); refresh()
    row=ttk.Frame(panel); row.pack(fill='x')
    for label,fn in [('Agregar',add),('Editar',edit),('Eliminar',delete),('Borrar todos',clear)]:
        ttk.Button(row,text=label,command=lambda f=fn:guard(f)).pack(side='left',padx=3)
    ttk.Button(row,text='Cerrar',command=win.destroy).pack(side='right')
    query.trace_add('write',lambda *_:guard(refresh))
    guard(refresh)
    return win
