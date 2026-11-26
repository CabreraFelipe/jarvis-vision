"""Explicit local preferences and memories; no automatic transcript storage."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

STYLES=('Normal','Conciso','Detallado','Conversacional')
MAX_ITEMS=100
MAX_NOTE=300
MAX_CONTEXT=1800

class Memory:
    def __init__(self,path):
        self.path=Path(path)
    @contextmanager
    def db(self):
        con=sqlite3.connect(self.path,timeout=2)
        try:
            with con:
                con.execute('PRAGMA secure_delete=ON')
                con.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL, style TEXT NOT NULL)')
                con.execute("INSERT OR IGNORE INTO settings VALUES (1,0,'Normal')")
                con.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL UNIQUE)')
                yield con
        finally:
            con.close()
    def settings(self):
        if not self.path.exists(): return False,'Normal'
        with self.db() as con:
            enabled,style=con.execute('SELECT enabled,style FROM settings WHERE id=1').fetchone()
            return bool(enabled),style if style in STYLES else 'Normal'
    def configure(self,enabled,style):
        if style not in STYLES: raise ValueError('Estilo inválido.')
        with self.db() as con:
            con.execute('UPDATE settings SET enabled=?,style=? WHERE id=1',(int(bool(enabled)),style))
    def add(self,text):
        text=text.strip()
        if not text or len(text)>MAX_NOTE: raise ValueError('Escribí una nota de 1 a 300 caracteres.')
        with self.db() as con:
            if con.execute('SELECT 1 FROM notes WHERE text=?',(text,)).fetchone(): return False
            if con.execute('SELECT COUNT(*) FROM notes').fetchone()[0]>=MAX_ITEMS: raise ValueError('Límite de 100 recuerdos alcanzado.')
            con.execute('INSERT INTO notes(text) VALUES (?)',(text,))
            return True
    def items(self):
        if not self.path.exists(): return []
        with self.db() as con: return con.execute('SELECT id,text FROM notes ORDER BY id DESC').fetchall()
    def remove(self,note_id):
        if not self.path.exists(): return
        with self.db() as con: con.execute('DELETE FROM notes WHERE id=?',(note_id,))
    def clear(self):
        if not self.path.exists(): return
        with self.db() as con: con.execute('DELETE FROM notes')
    def snapshot(self):
        if not self.path.exists(): return 'Normal',()
        with self.db() as con:
            enabled,style=con.execute('SELECT enabled,style FROM settings WHERE id=1').fetchone()
            notes=[]; total=0
            if enabled:
                for text, in con.execute('SELECT text FROM notes ORDER BY id DESC'):
                    if total+len(text)>MAX_CONTEXT: break
                    notes.append(text); total+=len(text)
            return style if style in STYLES else 'Normal',tuple(notes)
