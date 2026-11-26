"""Explicit, anchored local commands. No model inference, no automatic storage."""
import re
from dataclasses import dataclass
from memory import normalize,MAX_NOTE,STYLES

@dataclass(frozen=True)
class Command:
    action: str
    value: str = ''

def parse(text):
    text=text.strip()
    text=re.sub(r'^(?:hola\s+)?jarvis\s*[,:\s]+\s*','',text,flags=re.I)
    # Strip only terminal punctuation for exact command recognition.
    plain=normalize(text).strip(' ¿?¡!.')
    if plain in ('que sabes sobre mi','que recordas de mi','mostrar mis recuerdos','mostra mis recuerdos'):
        return Command('list')
    m=re.fullmatch(r'(?:record[aá]|recuerda)\s+que\s+(.+)',text,flags=re.I)
    if m:return Command('add',m.group(1).strip())
    m=re.fullmatch(r'(?:olvid[aá]|olvida)\s+(?:el recuerdo\s+)?(.+)',text,flags=re.I)
    if m:return Command('remove',m.group(1).strip(' .!?'))
    m=re.fullmatch(r'(?:cambi[aá]|cambia)\s+(?:tu |el )?estilo\s+a\s+(normal|conciso|detallado|conversacional)',plain)
    if m:return Command('style',m.group(1).capitalize())
    return None

def execute(store,command,confirm):
    """Confirm each mutation with exact data. Ambiguous removal never deletes."""
    action,value=command.action,command.value
    if action=='add':
        if not value or len(value)>MAX_NOTE:
            return 'El recuerdo debe tener entre 1 y 300 caracteres.'
        if not confirm('Guardar recuerdo',value):return 'Recuerdo no guardado.'
        return 'Recuerdo guardado.' if store.add(value) else 'Ese recuerdo ya existe.'
    if action=='remove':
        target=normalize(value)
        variants={target}
        if target.startswith('que '): variants.add(target[4:])
        matches=[(i,t) for i,t in store.items() if normalize(t).strip(' .!?') in variants]
        if len(matches)!=1:return 'No hay un recuerdo exacto y único. Consultá Memoria y personalidad para elegirlo.'
        i,text=matches[0]
        if not confirm('Eliminar este recuerdo',text):return 'Recuerdo conservado.'
        store.remove(i)
        return 'Recuerdo eliminado.'
    if action=='style' and value in STYLES:
        if not confirm('Cambiar estilo de respuesta',value):return 'Estilo sin cambios.'
        enabled,_=store.settings()
        store.configure(enabled,value)
        return 'Estilo actualizado: '+value+'.'
    raise ValueError('Comando no modificador o inválido.')
