from typing import Type

import instructor
from openai import OpenAI
from pydantic import BaseModel


def get_structured_response(
    response_model: Type[BaseModel], **chat_completion_request
) -> BaseModel:
    print("Getting structured response using instructor")

    model = chat_completion_request.get("model")
    messages = chat_completion_request.get("messages")
    chat_completion_request["response_model"] = response_model

    print(f"model: {model} messages: {messages} chat_completion_request: {chat_completion_request}")

    # Enables `response_model`
    client = instructor.patch(OpenAI())
    structured_response_model = client.chat.completions.create(**chat_completion_request)
    print(f"Extracted structured_response_model: {structured_response_model}")
    return structured_response_model


def get_chat_completetion_response(
    **chat_completion_request
) -> str:
    print("Getting chat completion response")

    model = chat_completion_request.get("model")
    messages = chat_completion_request.get("messages")

    print(f"model: {model} messages: {messages} chat_completion_request: {chat_completion_request}")

    client = OpenAI()
    completion = client.chat.completions.create(**chat_completion_request)
    print(f"completion: {completion}")
    return completion.choices[0].message.content
