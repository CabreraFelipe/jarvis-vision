"""Conservative suggestions from explicit preference statements; no automatic writes."""
import re
from memory import normalize,MAX_NOTE

def candidate(text):
    text=text.strip()
    if not 1<=len(text)<=MAX_NOTE or any(c in text for c in '\n\r?¿!¡'):
        return None
    # A single first-person statement, not an instruction, quote or inference.
    if any(c in text for c in ('"', '«', '»', ';', ':')):return None
    plain=normalize(text).rstrip('.')
    if '.' in plain:return None
    if not re.fullmatch(r'(?:prefiero (?:respuestas|explicaciones|ejemplos|musica|estudiar|trabajar|leer|escuchar)|me gusta (?:escuchar|leer|estudiar|aprender|programar))\s+\S.{0,240}',plain):
        return None
    return text

def suggest(store,text,context_enabled):
    if not context_enabled or not store.suggestions_enabled():return None
    note=candidate(text)
    if note is None:return None
    if any(normalize(t).rstrip('.')==normalize(note).rstrip('.') for _,t in store.items()):return None
    return note
