"""Bounded, RAM-only conversational context; no images retained here."""
class Conversation:
    def __init__(self, turns=4):
        self.turns=turns; self.messages=[]; self.epoch=0
    def snapshot(self):
        return [dict(m) for m in self.messages]
    def add(self, question, answer, source, epoch):
        if epoch!=self.epoch: return False
        self.messages.extend([{'role':'user','content':f'[{source}] {question}'[:700]}, {'role':'assistant','content':answer[:1000]}])
        self.messages=self.messages[-2*self.turns:]; return True
    def clear(self):
        self.messages.clear(); self.epoch+=1
