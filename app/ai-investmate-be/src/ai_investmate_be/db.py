import os

import faunadb
from faunadb import query as q
from faunadb.client import FaunaClient
import faunadb.errors

from ai_investmate_be.models import ChatSession


def upsert_chat_session(chat_session: ChatSession):
    fauna_db_client = FaunaClient(secret=os.environ.get("FAUNA_DB_API_KEY"))
    fauna_db_collection_name = os.environ.get("FAUNA_DB_COLLECTION_NAME")

    try:
        # Check if document with this session_id exists
        existing_doc = fauna_db_client.query(
            q.get(q.match(q.index("docs_by_session_id"), chat_session.session_id))
        )
        doc_ref = existing_doc["ref"]
        print(
            f"Found an existing chat session with id: {chat_session.session_id} so updating the existing chat_session"
        )
        # If exists, update the document
        updated_doc = fauna_db_client.query(q.update(doc_ref, {"data": chat_session.model_dump()}))
        return updated_doc

    except faunadb.errors.NotFound:
        print(
            f"Did not find an existing chat session with id: {chat_session.session_id} so adding a new chat_session"
        )
        # If not found, create the document
        created_doc = fauna_db_client.query(
            q.create(q.collection(fauna_db_collection_name), {"data": chat_session.model_dump()})
        )
        return created_doc

    except Exception as e:
        return str(e)


# Function to get the latest document from the collection
def get_latest_knowledge_graph():
    fauna_db_client = FaunaClient(secret=os.environ.get("FAUNA_DB_API_KEY"))
    try:
        result = fauna_db_client.query(
            q.paginate(
                q.match(q.index("knowledge_graphs_by_created_on_desc")),
                size=1
            )
        )
        # Extract the latest document reference
        latest_doc_ref = result['data'][0][1]  # Document reference is the second element in each value

        # Fetch the actual document data using the reference
        latest_doc = fauna_db_client.query(
            q.get(latest_doc_ref)
        )

        return latest_doc['data']
    except faunadb.errors.NotFound:
        print("No documents found")
        return None
