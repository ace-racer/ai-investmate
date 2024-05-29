from ai_investmate_be.chat_response_handlers.base import ResponseHandler, persist_chat_session
from ai_investmate_be.models import ChatMessage, ChatSession


class EchoResponse(ResponseHandler):
    @persist_chat_session
    def get_response(self, chat_session: ChatSession) -> ChatSession:
        # Do something with the chat history
        latest_message = chat_session.conversation_history[-1].content
        chat_session.conversation_history.append(
            ChatMessage(content=f"Received {latest_message}", role="assistant", meta=None)
        )
        return chat_session
