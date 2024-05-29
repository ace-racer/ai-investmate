from ai_investmate_be.chat_response_handlers import RAGResponse
from ai_investmate_be.models import ChatSession
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat_history(chat_session: ChatSession) -> ChatSession:
    chat_response = RAGResponse()
    return chat_response.get_response(chat_session)
