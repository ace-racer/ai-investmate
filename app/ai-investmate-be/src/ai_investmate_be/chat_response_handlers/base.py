from abc import abstractmethod

from ai_investmate_be.db import upsert_chat_session
from ai_investmate_be.models import ChatSession


def persist_chat_session(func):
    def wrapper(*args, **kwargs):
        chat_session = func(*args, **kwargs)
        print("Persisting chat session...")
        if not isinstance(chat_session, ChatSession):
            print(f"Unexpected argument type...{type(chat_session)}. Unable to persist!")
        else:
            upsert_result = upsert_chat_session(chat_session)
            print(f"upsert_result: {upsert_result}")

        return chat_session

    return wrapper


class ResponseHandler:
    @abstractmethod
    def get_response(chat_session: ChatSession) -> ChatSession:
        pass
