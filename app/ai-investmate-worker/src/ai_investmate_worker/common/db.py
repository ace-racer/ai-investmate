import os

from faunadb import query as q
from faunadb.client import FaunaClient
import datetime

KNOWLEDGE_GRAPH_COLLECTION_NAME = "knowledge_graphs"

def get_chat_sessions(size:int = 1000):
    fauna_db_client = FaunaClient(secret=os.environ.get("FAUNA_DB_API_KEY"))    
    result = fauna_db_client.query(
            q.map_(
                lambda ref: q.get(ref),
                q.paginate(
                    q.documents(q.collection("chat_sessions")),
                    size=size  # adjust size as needed
                )
            )
        )
    # print(f"result: {result}")
    docs = result['data']
    for doc in docs:
        yield doc['data']

def add_kg(graph: dict, entity_labels: dict):
    fauna_db_client = FaunaClient(secret=os.environ.get("FAUNA_DB_API_KEY"))
    data = {
        "graph": graph,
        "created_on": q.now(),
        "entity_labels": entity_labels
    }
    response = fauna_db_client.query(
            q.create(q.collection(KNOWLEDGE_GRAPH_COLLECTION_NAME), {"data": data})
        )
    return response


if __name__ == "__main__":
    current_chat_sessions = get_chat_sessions()
    total_processed = 0
    all_chat_session_content = []
    for chat_session in current_chat_sessions:
        session_id = chat_session["session_id"]
        # Extract the content from the data
        history_contents = [entry['content'] for entry in chat_session['conversation_history']]
        meta_contents = []
        for message in chat_session['conversation_history']:
            if "meta" in message:
                for metakey in message["meta"]:
                    meta_contents.extend(message["meta"][metakey])

        # Combine the content into a single list of chat_session
        chat_session_content = history_contents + meta_contents
        # Check the resulting chat_session_content
        print(f"len(chat_session_content): {len(chat_session_content)}")
        all_chat_session_content.extend(chat_session_content)


    print(f"len(all_chat_session_content): {len(all_chat_session_content)}")