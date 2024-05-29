import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# create the open-source embedding function
embedding_function = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cuda"}
)


def process_uploaded_file(original_file_name: str, downloaded_file_path: str, file_details: dict):
    print(f"Processing the file {original_file_name} from downloaded path: {downloaded_file_path}")
    print(f"file_details: {file_details}")
    print(f"file_path: {downloaded_file_path}")
    print(f"PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME')}")

    if not downloaded_file_path.endswith(".pdf"):
        print("No support for non-pdf files for now")
        return

    loader = PyPDFLoader(downloaded_file_path)
    document = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunked_documents = text_splitter.split_documents(document)
    for chunk in chunked_documents:
        print(f"page content: {chunk.page_content}")
        updated_metadata = chunk.metadata
        updated_metadata["source"] = original_file_name
        for k in file_details:
            updated_metadata[k] = file_details[k]
        chunk.metadata = updated_metadata
        print(f"chunk metadata: {chunk.metadata}")

    # https://python.langchain.com/docs/integrations/vectorstores/pinecone/
    PineconeVectorStore.from_documents(
        documents=chunked_documents,
        embedding=embedding_function,
        index_name=os.getenv("PINECONE_INDEX_NAME"),
    )
    print(f"Added {len(chunked_documents)} chunks to Pinecone vector store")
    os.remove(downloaded_file_path)
