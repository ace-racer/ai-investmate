from typing import List
import os
import torch

from langchain.memory import ChatMessageHistory, ConversationSummaryMemory
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ai_investmate_be.chat_response_handlers.base import ResponseHandler, persist_chat_session
from ai_investmate_be.chat_response_handlers.utils import get_structured_response, get_chat_completetion_response
from ai_investmate_be.models import ChatMessage, ChatSession

from langchain_pinecone import PineconeVectorStore
from sentence_transformers import util
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain.schema.document import Document
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

summary_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
search_metadata_generation_llm = "gpt-4o"
answer_llm = "gpt-4o"
PROMPTS_DIR = os.path.join(Path(__file__).parent, "prompts")

# create the open-source embedding function
embedding_function = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cuda"}
)

class PineconeSearchConfigs:
    k = 2
    num_search_queries = 3

class TavilySearchConfigs:
    k = 3
    num_search_queries = 2

class RerankerConfigs:
    num_results = 4

class SearchMetadata(BaseModel):
    """Search queries that can be used to find relevant content from the internet and a search index"""

    search_queries: List[str] = Field(
        description="A list of at most 3 unique search queries that captures the required details e.g. Vanguard S&P 500 ETF details, DBS Digiportfolio investor fact sheet, etc. based on the conversation",
        max_length=5,
    )


class RAGResponse(ResponseHandler):
    @persist_chat_session
    def get_response(self, chat_session: ChatSession) -> ChatSession:
        conversation_history = chat_session.conversation_history
        latest_message = conversation_history[-1].content
        history = ChatMessageHistory()
        for message in conversation_history[:-1]:
            if message.content:
                if message.role == "user":
                    history.add_user_message(message.content)
                elif message.role == "assistant":
                    history.add_ai_message(message.content)

        memory = ConversationSummaryMemory.from_messages(
            llm=summary_llm, chat_memory=history, return_messages=True
        )

        print(f"memory.buffer: {memory.buffer}")

        search_queries_request = {
            "model": search_metadata_generation_llm,
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate search queries to search the internet and a search index based on the summarized conversation: {memory.buffer} and the user's latest message: {latest_message}",
                }
            ],
        }

        search_metadata_response: SearchMetadata = get_structured_response(
            SearchMetadata, **search_queries_request
        )

        assert isinstance(search_metadata_response, SearchMetadata)
        print(search_metadata_response.search_queries)
        search_queries = search_metadata_response.search_queries
        meta = {"search_queries": search_queries[:min(PineconeSearchConfigs.num_search_queries, TavilySearchConfigs.num_search_queries)]}
        meta["raw_document_results"] = []
        meta["raw_websearch_results"] = []
        # Query Pinecone using the search queries top X for each query
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        vectorstore = PineconeVectorStore(index_name=pinecone_index_name, embedding=embedding_function)
        
        document_lib_relevant_docs: List[Document] = []
        for search_query in search_queries[:PineconeSearchConfigs.num_search_queries]:
            print(f"Picecone query with search query: {search_query}")
            docs = vectorstore.similarity_search(search_query, k=PineconeSearchConfigs.k)
            document_lib_relevant_docs.extend(docs)
            
        for d in document_lib_relevant_docs:
            meta["raw_document_results"].append(f"[{d.metadata['name']}](Page {int(d.metadata['page'])}): {d.page_content}")

        print(f"len(document_lib_relevant_docs) after Pinecone search: {len(document_lib_relevant_docs)}")

        web_search_relevant_docs: List[Document] = []
        # Query Tavily API using the search queries top Y for each query
        retriever = TavilySearchAPIRetriever(k=3)
        for search_query in search_queries[:TavilySearchConfigs.num_search_queries]:
            print(f"Tavily query with search query: {search_query}")
            docs = retriever.invoke(search_query)
            web_search_relevant_docs.extend(docs)

        for d in web_search_relevant_docs:
            meta["raw_websearch_results"].append(f"[{d.metadata['title']}]({d.metadata['source']}): {d.page_content}")
        print(f"len(web_search_relevant_docs) after Tavily search: {len(web_search_relevant_docs)}")

        all_relevant_docs: List[str] = meta["raw_document_results"] + meta["raw_websearch_results"]
        print(f"len(all_relevant_docs): {len(all_relevant_docs)}")

        # Rerank the results using similariy with the user query
        # https://www.sbert.net/examples/applications/semantic-search/README.html
        query = f"{memory.buffer}\n{latest_message}"

        query_embedding = torch.tensor(embedding_function.embed_documents([query]), device="cuda")
        corpus_embeddings = torch.tensor(embedding_function.embed_documents(all_relevant_docs), device="cuda")
        top_k = min(RerankerConfigs.num_results, len(all_relevant_docs))
        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)
        hits = hits[0]      #Get the hits for the first query
        llm_context_candidates = []
        for hit in hits:
            print(all_relevant_docs[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
            llm_context_candidates.append(all_relevant_docs[hit['corpus_id']])

        # Stuff the reranked results into a RAG prompt to generate the final answer in markdown format
        # Create an environment and set the loader to your template path
        env = Environment(loader=FileSystemLoader(PROMPTS_DIR))

        # Load a specific template by name
        rag_prompt_template_name = "stuffed_rag.jinja2"  # Replace with your template file's name
        template = env.get_template(rag_prompt_template_name)

        # Define the values to populate the template
        data = {
            'context': "\n".join(llm_context_candidates),
            'conversation_history': conversation_history[:-1]
        }

        # Render the template with the data
        rag_system_prompt = template.render(**data)
        answer_generation_request = {
            "model": answer_llm,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "system",
                    "content": rag_system_prompt,
                },
                {
                    "role": "user",
                    "content": latest_message,
                }
            ],
        }
        answer = get_chat_completetion_response(**answer_generation_request)

        chat_session.conversation_history.append(
            ChatMessage(content=answer, role="assistant", meta=meta)
        )
        return chat_session
