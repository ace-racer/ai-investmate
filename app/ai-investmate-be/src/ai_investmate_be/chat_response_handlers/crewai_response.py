"""
    Modified from https://mer.vin/2024/02/crewai-rag-using-tools/
"""

import os
from typing import List

from crewai import Agent, Crew, Process, Task
from langchain.memory import ChatMessageHistory, ConversationSummaryMemory
from langchain.tools import tool
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore

from ai_investmate_be.chat_response_handlers.base import ResponseHandler, persist_chat_session
from ai_investmate_be.models import ChatMessage, ChatSession

llm = ChatOpenAI(model="gpt-3.5-turbo")
summary_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# create the open-source embedding function
embedding_function = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cuda"}
)


# Define the tools
# Tool 1 : Get the file content from the vector database
class GetFileContent:
    @tool("Get file content Tool")
    def reference_content(query: str) -> str:
        """Search Pinecone DB for relevant content based on a query."""
        vectorstore = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"), embedding=embedding_function
        )
        retriever = vectorstore.similarity_search(query)
        return retriever


# Tool 2 : Search for details on the web
search_tool = DuckDuckGoSearchRun()

# Tool 3: Yahoo finance

# 2. Create Agents
financial_advisor_agent = Agent(
    role="FinancialAdvisor",
    goal="Provide financial advise based on available information. Use the Get file content tool to get details about a specific financial product. Use the Search tool for detailed results from the internet about the financial product. Provide an analysis for the user on the financial product based on the data points.",
    backstory="Expert in providing unbiased financial advise to users.",
    tools=[GetFileContent().reference_content, search_tool],
    allow_delegation=True,
    verbose=True,
    llm=llm,
)

# 3. Creating Tasks
"""
news_search_task = Task(
    description='Search for AI 2024 and create key points for each news.',
    agent=news_search_agent,
    tools=[SearchNewsDB().news]
)
"""


def get_financial_advise_task(agent, conversation_history: List[ChatMessage]):
    latest_message = conversation_history[-1].content
    history = ChatMessageHistory()
    for message in conversation_history[:-1]:
        if message.role == "user":
            history.add_user_message(message.content)
        elif message.role == "assistant":
            history.add_ai_message(message.content)

    memory = ConversationSummaryMemory.from_messages(
        llm=summary_llm, chat_memory=history, return_messages=True
    )

    print(f"memory.buffer: {memory.buffer}")

    return Task(
        description=f"""
        Given a conversation between a human and an expert unbiased financial advisor with the latest user message: '{latest_message}' and summary of the conversation so far:
        {memory.buffer}
        Based on the latest user message and the conversation summary:
        Step 1: Identify financial products and users queries about these financial products.
        Step 2: Generate appropriate search queries based on the financial products and the user's queries on those products
        Step 3: Use the Get File Content to get relevant content from existing files on the financial product provided by the user that are most likely to answer the user's query.
        Step 4: Use the Search tool to search for further information from internet on the financial product provided by the user that are most likely to answer the user's query.
        Step 5: Go through the data points and write an in-depth analysis about what financial decision the user should take.
        Don't skip any step or any important detail from the conversation.
        """,
        agent=agent,
        tools=[GetFileContent().reference_content, search_tool],
        expected_output="An in-depth analysis about what finncial decision the user should take based on the available information",
    )


class CrewAIResponse(ResponseHandler):
    @persist_chat_session
    def get_response(self, chat_session: ChatSession) -> ChatSession:
        # Get the task with required details
        financial_advise_task = get_financial_advise_task(
            financial_advisor_agent, chat_session.conversation_history
        )

        # 4. Creating Crew
        aiinvestmate_crew = Crew(
            agents=[financial_advisor_agent],
            tasks=[financial_advise_task],
            process=Process.sequential,
            manager_llm=llm,
            verbose=2,
        )
        # Execute the crew
        result = aiinvestmate_crew.kickoff()
        print(result)
        chat_session.conversation_history.append(
            ChatMessage(content=result, role="assistant", meta=None)
        )
        return chat_session
