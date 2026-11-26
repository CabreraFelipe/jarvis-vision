"""Bounded, opt-in conversational follow-up; no audio or transcript persistence."""
import re,unicodedata

STOP={'terminar conversacion','fin de la conversacion','jarvis termina la conversacion','deja de escuchar','jarvis deja de escuchar','cancelar microfono'}

def stop_phrase(text):
    clean=''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+',clean)) in STOP

class Followup:
    LIMIT=5
    def __init__(self):
        self.epoch=0;self.remaining=0;self.pending=False
    def reset(self):
        self.epoch+=1;self.remaining=0;self.pending=False
    def initial(self):
        self.reset();self.remaining=self.LIMIT
        return self.epoch
    def accepted(self,epoch):
        if epoch==self.epoch and self.remaining>0:self.pending=True
    def take(self):
        if not self.pending or self.remaining<=0:return False
        self.pending=False;self.remaining-=1;return True
