from typing import Literal, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    content: str
    role: Literal["user", "assistant", "system", "tool"]
    meta: Optional[dict[str, List[str]]] = None


class ProcessingStatus(BaseModel):
    topics_extracted: bool = False
    ner_re_extracted: bool = False

class ChatSession(BaseModel):
    session_id: str
    conversation_history: List[ChatMessage]
    processing_status: ProcessingStatus = ProcessingStatus()

    def __str__(self):
        history_str = ""
        turns = []
        for msg in self.conversation_history:
            metadata = ""
            if msg.meta:
                metadata = "\n".join(f"{k}: {msg.meta[k]}"for k in msg.meta)
            turn = f"{msg.role}: {msg.content}\nmetadata:{metadata}"
            turns.append(turn)

        history_str = "\n".join(turns)
        return f"Session ID: {self.session_id}\nConversation History:\n{history_str}\n"