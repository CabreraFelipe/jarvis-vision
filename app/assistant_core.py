"""Device-independent assistant core. No network or disk access of its own."""
from dataclasses import dataclass
from typing import Any, Protocol
from conversation import Conversation

class ChatProvider(Protocol):
    def __call__(self, frame: Any, question: str, history: list[dict]) -> str: ...

@dataclass(frozen=True)
class Request:
    question: str
    source: str
    epoch: int
    use_context: bool
    frame: Any
    history: tuple[tuple[str, str], ...]

class AssistantCore:
    def __init__(self, provider: ChatProvider, turns: int = 4):
        self.provider = provider
        self.conversation = Conversation(turns)

    def prepare(self, question, source, frame=None, use_context=True):
        """Call from UI thread: snapshot the context and frame for a worker."""
        question = question.strip()
        if not question:
            raise ValueError('La pregunta está vacía.')
        messages = self.conversation.snapshot() if use_context else []
        return Request(question, source, self.conversation.epoch, bool(use_context),
                       frame.copy() if frame is not None else None,
                       tuple((m['role'], m['content']) for m in messages))

    def answer(self, request):
        """Call from worker. Only explicit request data reaches the provider."""
        history = [{'role': role, 'content': content} for role, content in request.history]
        return self.provider(request.frame, request.question, history)

    def accept(self, request, answer, context_enabled=True):
        """Call from UI thread after checking the camera generation."""
        if not (request.use_context and context_enabled):
            return False
        return self.conversation.add(request.question, answer, request.source, request.epoch)

    def clear(self):
        self.conversation.clear()
