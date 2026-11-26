"""Explicit local preferences and memories; no automatic transcript storage."""
import sqlite3
import json
from personality import DEFAULT as PERSONALITY_DEFAULT,validate as validate_personality
import re
import unicodedata
from contextlib import contextmanager
from pathlib import Path

STYLES=('Normal','Conciso','Detallado','Conversacional')
MAX_ITEMS=100
MAX_NOTE=300
MAX_CONTEXT=1800

STOP_WORDS=set('a al algo como con cual cuando de del donde el en es esta esto la las lo los me mi mis o para por que se si sin su te tu un una y yo jarvis'.split())

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))

def tokens(text):
    return {t for t in re.findall(r'\w+',normalize(text)) if len(t)>1 and t not in STOP_WORDS}

def relevant(rows,question):
    """Rank by exact normalized token overlap, then recency. No unrelated fallback."""
    terms=tokens(question)
    ranked=[(len(terms & tokens(text)),i,text) for i,text in rows]
    return [(i,text) for score,i,text in sorted(ranked,reverse=True) if score]

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
                con.execute('CREATE TABLE IF NOT EXISTS semantic_settings (id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL)')
                con.execute('INSERT OR IGNORE INTO semantic_settings VALUES (1,0)')
                con.execute('CREATE TABLE IF NOT EXISTS learning_settings (id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL)')
                con.execute('INSERT OR IGNORE INTO learning_settings VALUES (1,0)')
                con.execute('CREATE TABLE IF NOT EXISTS personality_settings (id INTEGER PRIMARY KEY CHECK(id=1), profile TEXT NOT NULL)')
                yield con
        finally:
            con.close()
    def settings(self):
        if not self.path.exists(): return False,'Normal'
        with self.db() as con:
            enabled,style=con.execute('SELECT enabled,style FROM settings WHERE id=1').fetchone()
            return bool(enabled),style if style in STYLES else 'Normal'
    def semantic_enabled(self):
        if not self.path.exists(): return False
        with self.db() as con: return bool(con.execute('SELECT enabled FROM semantic_settings WHERE id=1').fetchone()[0])
    def personality(self):
        if not self.path.exists():return PERSONALITY_DEFAULT
        with self.db() as con:
            row=con.execute('SELECT profile FROM personality_settings WHERE id=1').fetchone()
        if row is None:return PERSONALITY_DEFAULT
        try:return validate_personality(json.loads(row[0]))
        except (ValueError,TypeError):return PERSONALITY_DEFAULT
    def set_personality(self,profile):
        profile=validate_personality(profile)
        with self.db() as con:
            con.execute('INSERT INTO personality_settings VALUES (1,?) ON CONFLICT(id) DO UPDATE SET profile=excluded.profile',(json.dumps(profile,ensure_ascii=False),))
    def suggestions_enabled(self):
        if not self.path.exists(): return False
        with self.db() as con:
            enabled=con.execute('SELECT enabled FROM settings WHERE id=1').fetchone()[0]
            learning=con.execute('SELECT enabled FROM learning_settings WHERE id=1').fetchone()[0]
            return bool(enabled and learning)
    def configure(self,enabled,style,semantic=None,*,suggestions=None):
        if style not in STYLES: raise ValueError('Estilo inválido.')
        with self.db() as con:
            con.execute('UPDATE settings SET enabled=?,style=? WHERE id=1',(int(bool(enabled)),style))
            if semantic is not None:
                con.execute('UPDATE semantic_settings SET enabled=? WHERE id=1',(int(bool(semantic) and bool(enabled)),))
            elif not enabled:
                con.execute('UPDATE semantic_settings SET enabled=0 WHERE id=1')
            if suggestions is not None or not enabled:
                con.execute('UPDATE learning_settings SET enabled=? WHERE id=1',(int(bool(suggestions) and bool(enabled)),))
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
    def search(self,query):
        rows=self.items()
        if not query.strip(): return rows
        term=normalize(query.strip())
        return [(i,text) for i,text in rows if term in normalize(text)]
    def edit(self,note_id,text):
        text=text.strip()
        if not text or len(text)>MAX_NOTE: raise ValueError('Escribí una nota de 1 a 300 caracteres.')
        if not self.path.exists(): return False
        with self.db() as con:
            if con.execute('SELECT 1 FROM notes WHERE text=? AND id<>?',(text,note_id)).fetchone():
                raise ValueError('Ya existe ese recuerdo.')
            return con.execute('UPDATE notes SET text=? WHERE id=?',(text,note_id)).rowcount==1
    def remove(self,note_id):
        if not self.path.exists(): return
        with self.db() as con: con.execute('DELETE FROM notes WHERE id=?',(note_id,))
    def clear(self):
        if not self.path.exists(): return
        with self.db() as con: con.execute('DELETE FROM notes')
    def selection(self,question=None,use_context=True):
        """Read one local snapshot; no embedding work or network on the UI thread."""
        if not self.path.exists(): return 'Normal',(),()
        with self.db() as con:
            enabled,style=con.execute('SELECT enabled,style FROM settings WHERE id=1').fetchone()
            semantic=con.execute('SELECT enabled FROM semantic_settings WHERE id=1').fetchone()[0]
            rows=con.execute('SELECT id,text FROM notes ORDER BY id DESC').fetchall() if enabled and use_context else []
            lexical=rows if question is None else relevant(rows,question)
            candidates=tuple(rows) if semantic and question is not None else ()
            notes=[];total=0
            for _,text in lexical:
                if total+len(text)>MAX_CONTEXT: continue
                notes.append(text);total+=len(text)
            return style if style in STYLES else 'Normal',tuple(notes),candidates
    def snapshot(self,question=None):
        style,notes,_=self.selection(question)
        return style,notes
